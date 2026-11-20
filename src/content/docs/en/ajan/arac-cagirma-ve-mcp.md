---
title: "Tool-Calling Mechanics and MCP"
description: "Ollama's tool-calling request and response format line by line: the tools field, tool_calls, the role tool message, the arguments dictionary, the turn counter, and where MCP standardizes this job."
dogrulama: 2026-11-20
---

The previous page explained whom the agent is choosing; this one explains **how it's written**. We first cover the bare mechanics with Ollama's local API, then the protocol that makes those mechanics portable between applications (MCP). All the sequential code examples come from requests actually sent on this machine; each box notes which run it came from.

**The one-sentence answer:** tool calling means giving the model a function catalog and saying "don't answer — produce the catalog's name and arguments"; the rest of the loop (calling it, putting the result back, asking again) is ordinary software you write.

## The Anatomy of a Turn

There's no new method on the wire for tool calling: it's still `POST /api/chat`. The difference is the `tools` field in the request and the `tool_calls` field in the response.

```jsonc title="The request — a simplified form of Example 7's viki_ara definition"
{
  "model": "qwen2.5:3b-instruct-q4_K_M",
  "messages": [{ "role": "user", "content": "In which year did Marmaray enter service?" }],
  "tools": [{
    "type": "function",
    "function": {
      "name": "viki_ara",
      "description": "Fetches Wikipedia pieces about Istanbul public transit.",
      "parameters": {
        "type": "object",
        "properties": { "question": { "type": "string", "description": "The topic sought, one sentence" } },
        "required": ["question"]
      }
    }
  }],
  "stream": false
}
```

```jsonc title="The response — measured on this machine (the exploration run, cikti/kesif.txt)"
{
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [{
      "id": "call_au6z32fo",
      "function": { "index": 0, "name": "sehir_nufusu", "arguments": { "sehir": "Izmir" } }
    }]
  },
  "done_reason": "stop",
  "prompt_eval_count": 190,
  "eval_count": 26
}
```

Three places to note:

- **`arguments` is a dictionary, not JSON text.** In many OpenAI-compatible APIs this field arrives as an escaped string (`"{\"sehir\": \"Izmir\"}"`); in Ollama's local `/api/chat` it comes as a dictionary. Still, writing a conversion layer accepting both types is cheap insurance — Example 7 does it with `convert_arguments()`.
- **`content` is empty.** In the tool-calling turn the model usually produces no text; if it does, don't count that text as the answer, hold it.
- **The server's `id` and `index` fields.** They're useless in a single tool call; they're needed when two calls arrive in the same turn, to tell which result belongs to which call.

The form for giving the result back is also a message:

```python title="Adding the tool result to the request (Example 7, agent())"
messages.append({"role": "assistant", "content": "", "tool_calls": calls})
messages.append({"role": "tool", "tool_name": "viki_ara", "content": result})
```

`tool_name` or `tool_call_id`? The documented recommendation is `tool_call_id`; on this machine all three forms (with `tool_name`, plain `content`, with `tool_call_id`) produced the same answer and **the same input token count** (240) — see `ornekler/ajan-dongusu/cikti/kesif-dongu.txt`. So in a single-tool, single-call loop these fields don't practically matter. The guarantee against mixing up which result belongs to which when there are two tools and the same tool is called twice, however, is **using `tool_call_id`**; that's not a measured behavior but a defense against the risk of the ordering getting scrambled.

## The Loop: How Many Lines?

The following twelve lines are the entirety of an agent. Simplified from Example 7's `agent()` function:

```python
messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
for turn in range(MAX_TURNS):
    reply = chat(model=MODEL, messages=messages, tools=TOOLS, stream=False)
    calls = reply["message"].get("tool_calls") or []
    if not calls:
        return reply["message"]["content"]          # the loop closes here
    messages.append(reply["message"])
    for c in calls:
        result = APPLY[c["function"]["name"]](c["function"]["arguments"])
        messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
```

The exit condition is one line: **end when the model doesn't call a tool.** If you don't write it, you produce not a loop but an infinity. `MAX_TURNS` is the second safety nut; on the [Agent Measurement](/en/ajan/ajan-olcumu/) page there's a case that stuck to the counter limit (`done_reason=length`).

## The Requirement: The Model's Template Must Know Tools

Tool calling lives not in the model's weights but in its **chat template**. If the model's template doesn't know to produce a block like `<tool_call>`, sending `tools` to the API does nothing; Ollama refuses to call such a model with a tool list (documented behavior — HTTP 400). The check is a one-command job:

```bash
ollama show qwen2.5:3b-instruct-q4_K_M
# capabilities: completion, tools      <- the output seen on this machine
```

:::note[A small model, fragile choice]
Listing the `tools` capability doesn't guarantee the model will **choose the tool correctly**. In Example 7's record, despite a length question the model called the unit-conversion tool with the arguments `{"amount": 1, "source": "h", "target": "m"}`; our tool didn't reject that garbage request (it returned "1 h = 3600 m") and on the next turn the model said "the T1 line's length is 3600 meters". Two flaws stacked: first the 3-billion-parameter model's catalog-reading limit, second our tool code's missing validation. The way to shrink the error locally is to keep the tool count low, the descriptions one sentence, and enforce the arguments **server-side**.
:::

## tool_choice: The Undocumented Field

The `tool_choice: "required"` field (must call a tool) we know from OpenAI's interface is **absent** from Ollama's local `/api/chat` documentation; both the OpenAI and Anthropic compatibility-layer pages mark `tool_choice` as "not supported". Earlier versions are reported to have silently ignored the field (ollama/ollama#11171).

We didn't assume that claim on this page: we sent it to the server and measured the result (trial `F`). The four forms of the `tool_choice` field — not sending it, `"auto"`, `"required"` and an invalid value (`"bulutmeydan"`) — produced **HTTP 200 and the same behavior in all four** on this machine: the model called a tool, `content` stayed empty. So the server neither rejects the field nor notices an invalid value.

The honest limit: this test **wasn't discriminating.** The question we picked was one where the model calls a tool even without the field; the "forced it" vs "ignored it" distinction can only be run with a query the model would answer without calling a tool. That trial wasn't done. The practical conclusion doesn't change: **don't build design on an undocumented field**; if forcing is needed, pin the sequence in your own code or trigger the tool yourself with the structured-output mode.

## format + tools: What the Docs Don't Say

What happens when structured output (`"format": "json"`) and tools meet in the same request? Ollama's documentation doesn't describe this pair's interaction. Trial `G` returned HTTP 200 on this machine and the answer had **no `tool_calls` field at all**: the model wrote the tool call as JSON *text* into `content` (`{"name": "viki_ara", "arguments": {...}}`). So the protocol didn't win — it was replaced: a loop expecting `tool_calls` never starts on this request. The raw record is on the [Agent Measurement](/en/ajan/ajan-olcumu/) page; against this one-trial behavior, the most prudent path is not sending `format` on requests that use tools.

## The Token Price of Tools

The catalog isn't free. Both vendors say it in writing:

- OpenAI, Function calling → Token Usage: *"callable function definitions count against the model's context limit and are billed as input tokens"*; recommending fewer/shorter tools as the measure.
- Anthropic, Define tools: recommends "at least 3-4 sentences" for each tool's description — text added to the request.

The only official text giving an open number is Anthropic's `input_examples` band: simple examples **~20-50**, deeply nested complex objects **~100-200 tokens**. There's no official figure for a general function schema's token count; so we measured. On this machine there are two separate runs: in a bare trial the request's base was **54** tokens, rising to **190** (+136) when a single tool definition was added; in the trial running Example 7's real system instruction the base was **73** tokens, `viki_ara` added **+164**, and the second tool `birim_donustur` added **+109** tokens. The table and commentary: [Agent Measurement](/en/ajan/ajan-olcumu/).

The claim that tool count breaks selection (the docs' "dozens of tools" warning) is qualitative; no official source gives a numeric threshold.

## MCP: Carrying the Same Catalog to More Than One Application

The `tools` field above is **application-specific**: if you want the same tool in your own script, in an editor and in a chat interface, you write a separate integration for each. **MCP (Model Context Protocol)** is the open protocol standardizing that bridge.

The specification's own definition (rev 2026-07-28): *"MCP is an open protocol that enables seamless integration between LLM applications and external data sources and tools."* The protocol was written by **David Soria Parra** and **Justin Spahr-Summers**, and Anthropic announced it on **2024-11-25** (the date from the vendor's own page). Today its governance sits under "Model Context Protocol a Series of LF Projects, LLC"; the Linux Foundation announced on **December 9, 2025** that it founded the Agentic AI Foundation, with the first contributions being **Anthropic's MCP, Block's goose and OpenAI's AGENTS.md**.

:::caution[Two texts conflict on the license]
The spec repo's `LICENSE` file says **MIT**; the community governance page asks contributions for **Apache-2.0** (docs CC BY 4.0). Stating both separately is the right thing — writing either one as "MCP's license" is a claim without a source.
:::

### Three Parties, Three Capabilities

MCP's vocabulary (rev 2026-07-28):

| Party | Who | What it does |
| --- | --- | --- |
| Host | Your application (an editor, a chat interface) | The side calling the models and talking to the user |
| Client | The bridge inside the host | Connects to the server, relays notifications (one per server in the application) |
| Server | The small service wrapping the tools | Serves **Tools**, **Resources**, **Prompts** |

The server's three offerings don't substitute for each other: **Tools** are for the model to call (the counterpart of our `tools` field), **Resources** are data the application reads, **Prompts** are ready templates the user picks. The request-side capabilities (Elicitation, Sampling, Roots) and the utilities (progress, cancellation, completion, logging) are named separately too.

As the transport layer there are **stdio** (same machine, as a subprocess) and **Streamable HTTP**; the spec permits "custom transports". JSON-RPC 2.0 and UTF-8 are mandatory bases.

### The Version Timeline: This Part of the Job Is Moving

Revisions: **2024-11-05 → 2025-03-26 → 2025-06-18 → 2025-11-25 → 2026-07-28** (current). This isn't showcase information but a distinction that affects code:

- **The HTTP+SSE transport was deprecated on 2025-03-26**; the migration path is Streamable HTTP. If you copy old examples you'll hit this error.
- **Roots, Sampling and Logging were deprecated in the 2026-07-28 revision** (SEP-2577). The recommended migrations: tool parameters / resource URIs / server settings, working directly with the model provider's API, and stderr or OpenTelemetry for logs. The earliest removal date is "the first revision published after 2027-07-28".
- The 2026-07-28 is a **stateless rewrite**: the session and `Mcp-Session-Id` were removed, the `initialize` / `notifications/initialized` handshake was removed; version, capabilities and client info now travel per-request in `_meta`, and servers must answer `server/discover`. The spec splits this into "Modern" and "Legacy" eras; a "Dual-era" supporting both is also defined.

Official SDKs (2026-07-28 doc): Tier 1 TypeScript, Python, C#, Go, Rust, Ruby; Tier 2 Java; Tier 3 Swift, PHP, Kotlin. For finding servers there's the **Official MCP Registry**, but it's still in **preview**: its own doc says "breaking changes or data resets may occur before general availability" — don't treat it as a permanent dependency.

## Ollama and MCP: Today's Actual State

:::caution[The doc is squeezed into one place, and there's no measurement]
Ollama doesn't document itself as an **MCP host or client**. Across the whole page index of docs.ollama.com (`llms.txt`), the only place MCP appears is the "## MCP Server" heading on the Web search page: Ollama exposes its **cloud** web search/fetch service as an **MCP stdio server** via `examples/web-search-mcp.py` in the ollama-python repo (using it requires `OLLAMA_API_KEY`), with documented client examples Cline, Codex and Goose. The PRs adding "MCP support" to the repo (#13562, #13700) were **closed unmerged**.
:::

If you're building a local loop, two paths make sense today:

1. **`/api/chat` + `tools`** (Example 7's path). The only dependency is Ollama; zero extra processes. Your tools live in a Python script.
2. **Write a separate MCP server and call it from your own script.** The protocol's gain is that the same server can also be used by a second application like an editor or Cline; the cost is a subprocess, JSON-RPC communication and tracking MCP versions. The `tool` message format and MCP's `tools/call` format are not the same thing; the translation layer stays with you.

Since this guide measures locally, it settles for path 1; the latency and token cost of path 2 was **not measured on this machine**.

:::note[If you want to try your own server]
The smallest MCP server is a Python script with the Tier 1 Python SDK; the server's `tools/list` response must be deterministically ordered and `inputSchema` must be a valid JSON Schema (2026-07-28 requirements). Example 7's two tools (`viki_ara`, `birim_donustur`) are perfectly portable jobs for MCP — how much local latency changed after the port wasn't measured here, so the page gives no numbers.
:::

## The Practical Checklist

1. Is there `tools` in the `ollama show <model>` output? If not, don't build a loop with this model.
2. Keep the catalog **small**: one tool, one job. Two tools doing the same job are the first agent of broken selection.
3. Check the `arguments` type: a dictionary or JSON text? Write a converter accepting both.
4. Don't call a loop an "agent" without writing the exit condition and the `MAX_TURNS` counter.
5. If the tool result is insufficient, return **a text the model will interpret** ("below threshold", "unknown unit") — silent failure is the fuel of fabricated answers.
6. Log the per-turn `prompt_eval_count` and `done_reason` fields; no other field shows the cost and the cut-off answer.
7. Don't build a design relying on undocumented fields like `tool_choice`: measure its behavior on this machine first.

## What Wasn't Measured Here

- The effect of the tool count (3, 10, 30) on selection accuracy: worked with a two-tool catalog.
- The MCP server's local latency/token cost; Ollama behaving as an MCP client (not documented).
- Tool calling with `stream: true`: merging the fragmented (delta) `tool_calls` wasn't tried here.
- With a stronger model than the small one, how many turns the same catalog closes in.

## Sources and further reading

- [Agent Measurement](/en/ajan/ajan-olcumu/) — this mechanism's second, turn and token counterparts; the result of the `tool_choice` and `format` trials on this machine.
- [Agent or a Fixed RAG Pipeline?](/en/ajan/ajan-mi-sabit-hat-mi/) — the decision page, not the mechanics.
- [Example 7: The Agent Loop](/en/ornekler/ajan-dongusu/) — the script in full, explained line by line.
- [Ollama Chat API](https://docs.ollama.com/api/chat.md) — the local documentation of `tools`, `tool_calls` and their fields.
- [Ollama Tool Calling](https://docs.ollama.com/capabilities/tool-calling.md) — the documented example section of the multi-turn tool loop.
- [The MCP specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) — the current protocol; terminology, requirements and transports.
- [MCP deprecations](https://modelcontextprotocol.io/specification/2026-07-28/deprecated.md) — dates and migration paths for HTTP+SSE, Roots, Sampling and Logging.
- [OpenAI Function calling](https://developers.openai.com/api/docs/guides/function-calling) — the official text on tool definitions counting as input tokens.
- ReAct, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) — producing reasoning and action in sequence; this loop's academic name.
- Toolformer, [arXiv:2302.04761](https://arxiv.org/abs/2302.04761) — the model learning itself which API to call, when and with what arguments.
