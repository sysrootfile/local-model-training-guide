---
title: "Agent Measurement: The Turn, Token and Second Counterparts"
description: "The record of running Example 7's agent loop on this machine: per-turn wall time against the fixed line, the cache gain, the tool definition's token expense, and the real behavior of the tool_choice and format fields."
dogrulama: 2026-11-20
---

Every line on this page comes from the `ornekler/ajan-dongusu/cikti/ajan-kaydi.txt` record; the run was made between **2026-10-16, 02:11-02:18**, with a single Python process and no other Ollama request sent. The machine: AMD Ryzen 5 2600 (6 cores/12 threads), 15.9 GB RAM, a SATA SSD, Ollama 0.40.4 (the machine moved to 0.40.6 on 2026-10-19; the numbers on this page weren't re-measured on that version), the chat model `qwen2.5:3b-instruct-q4_K_M`, the embedding model `bge-m3`. The numbers below are that hardware's numbers; on another machine the bands change, the ranking usually doesn't.

The two measured pipelines run on the same Wikipedia corpus (125 pieces) and the same questions. The fixed line does what Example 6 does: embed the question, retrieve pieces, read the context. The agent loop, meanwhile, is the `for` loop itself from the [Mechanics page](/en/ajan/arac-cagirma-ve-mcp/): the model calls the tool, sees the result, and then either answers or calls again. The turn ceiling is 5, `num_predict` 300.

:::note[The first number contains the cold start's count]
When the run started, no model was loaded in Ollama (`ollama ps` was empty). That's why the fixed line's retrieval step took **10.79 s**: that duration is loading `bge-m3` into memory to embed the query. Example 6's warm measurement is **0.09-0.13 s**. Similarly, the fixed line's generation call shows a `load 7.64` s; in all later turns 0.01 s. The cold/warm distinction is the subject of the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page; here we only flag which line is cold.
:::

## The Same Question, Two Pipelines

The question: "In which year did Marmaray enter service?"

| Pipeline | Turns | Wall time | Input tokens | Output tokens | Event |
| --- | --- | --- | --- | --- | --- |
| Fixed line | 1 pass | retrieval 10.79 + generation 68.03 = **78.8 s** | 1,926 | 120 | One read, the answer complete |
| Agent loop | 2 turns | **95.2 s** | 2,623 | 336 | The answer was **cut off** at 300 tokens (`length`) |

The script writes in its own line a "fixed line 68.0 s / agent 95.2 s" comparison; that's a reading that leaves the retrieval step out. Including retrieval, the total is the 78.8 s above. Both readings are valid, but mixing them makes the agent's bill look smaller than it is: compared to the generation step alone, the agent took **27.2 s** longer; compared to the line including retrieval, **16.4 s** longer.

**The difference's source sits in one line:** the agent adds the 4,994-character piece returned by the tool to the second turn's prompt. On the same question the extra input was **697 tokens**. We can't measure the gain from this record: both pipelines gave the same answer, and the agent's answer was cut in half.

## Turn-by-Turn Breakdown: Why Is the Agent's Second Turn Expensive?

| Turn | Wall | Pre-fill | Cache | Decode | `done_reason` |
| --- | --- | --- | --- | --- | --- |
| 1 (tool decision) | 10.82 s | 346 tok / 8.12 s (42.6 tok/s) | 3 tok | 36 tok / 2.65 s (13.6 tok/s) | `stop` |
| 2 (answering with context) | 84.41 s | 2,277 tok / 52.13 s (43.7 tok/s) | **363 tok** | 300 tok / 32.24 s (9.3 tok/s) | **`length`** |

Three readings:

1. **The first turn is cheap but not zero.** The prompt making the tool decision is 346 tokens; 273 of those are the tool catalog and the system instruction (the `E` measurement below). The model produces no answer, it only writes `tool_calls`: 36 tokens.
2. **The second turn re-reads the whole first turn.** 346 → 2,277 tokens. The cache brought 363 of that for free; the remaining ~1,914 tokens were re-read in the 43.7 tok/s band. That band overlaps the 43.9-45.9 tok/s measurement on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page — so the agent's latency isn't the model's quirk, it's the context's growth.
3. **The answer was cut off.** It stuck to the `num_predict: 300` limit (`done_reason=length`), ending mid-sentence. This is the most common silent error when building a local agent: the user gets a "half answer" and there's no error in the log. Any monitoring that doesn't look at the `done_reason` field misses this.

## Five Scenarios, Five Different Failures

| Label | Question | Turns | Wall | Input | Output | What the record shows |
| --- | --- | --- | --- | --- | --- | --- |
| B2 | Compare the opening years of Marmaray and the T1 | 2 | 61.8 s | 2,239 | 210 | The answer came in **English**; the model settled for a single `viki_ara` call |
| C | The T1 line's length, then a unit conversion | 2 | 12.1 s | 794 | 120 | The wrong tool was called, and **"it is 3600 meters"** was fabricated from the result |
| D | Is it raining in Istanbul right now? | 2 | 11.9 s | 774 | 121 | The tool returned the "below threshold" text; the model leaked the 0.496 number to the user |
| D2 | Where is the tunnel funicular line? (`tool_choice="required"`) | 2 | 61.8 s | 2,087 | 207 | The same two turns even with the forcing field; the field's effect wasn't measured separately |
| H | The Marmaray question, no `tool_name` in the tool message | 2 | 84.4 s | 2,623 | 253 | The input tokens were exactly the same as B's; the loop didn't break |

These five rows are here not to say "the agent is bad" but to show that **the agent's failure mode differs from the fixed line's**. On the fixed line, failure comes from one place: the retrieved piece is wrong. In an agent loop, failure can come from four places — tool choice, arguments, the turn count, and answer length. All four appear in different fields: choice and arguments inside `tool_calls`, the turn count in the loop counter, and answer length in `done_reason` and `eval_count`.

## The Tool Definition's Token Expense (E)

The same request, the same system instruction, one difference: how many tools are defined in the `tools` field.

| Catalog | Input tokens | Extra expense | Did the model call a tool? |
| --- | --- | --- | --- |
| 0 tools | 73 | — | No |
| 1 tool (`viki_ara`) | 237 | **+164** | Yes |
| 2 tools (`viki_ara` + `birim_donustur`) | 346 | **+273** | Yes |

The two-tool catalog adds **+109** tokens over the one-tool one, and **+164** over the tool-less base; the script writes its average as "roughly 136 tokens per tool". Look at the two differences, not the average: the expense is proportional to the tool's **description and schema length**, not to the tool count. A tool with a long description is more expensive than two with short ones.

This number has a counterpart seen on both sides: the B/D turns' first-turn input was 345-346 tokens — i.e. the base (73) + the two-tool catalog (273). The tool catalog is a cost paid without producing an answer in a single turn.

:::caution[Cloud pricing and local expense aren't the same thing]
OpenAI and Anthropic describe this expense as **money** ("billed as input tokens"). On local Ollama there's no money; the payment's counterpart is pre-fill time and the context window. Trial E's three rows' pre-fill times were **0.82 / 4.88 / 4.55 s** in order; don't use those three numbers as a speed comparison, because the cache hits differed between the rows (48 / 48 / 171 tokens). The expense's fixed counterpart is in tokens, and it's paid every turn. The real risk is the `num_ctx` window filling up because of the catalog: the silent truncation on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page kicks in much earlier with a ten-tool catalog.
:::

## tool_choice Tried in Four Forms (F)

The field isn't in Ollama's local `/api/chat` doc; the OpenAI and Anthropic compatibility pages say "not supported". We asked the server in four forms — a one-tool catalog, a question expected to call a tool:

| What was sent | The server's reply | Was a tool called? |
| --- | --- | --- |
| no field | HTTP 200 | Yes (`content` empty) |
| `"auto"` | HTTP 200 | Yes (`content` empty) |
| `"required"` | HTTP 200 | Yes (`content` empty) |
| `"bulutmeydan"` (an invalid value) | HTTP 200 | Yes (`content` empty) |

**What it proves:** the server doesn't drop into an error in any form; nor does it reject an invalid value. **What it doesn't prove:** all four coming out the same doesn't prove the field is ignored, because the question we picked was one where the model called a tool anyway — i.e. the test **wasn't discriminating**. The discriminating test would be sending `tool_choice="required"` to a question the model would answer without a tool and looking at whether it's forced to call. That trial wasn't run in this round. The practical conclusion doesn't change: **don't build a design leaning on a forcing field**; don't build on a field whose behavior isn't documented.

## format + tools: The Most Unexpected Finding (G)

`"format": "json"` and `tools` were sent in the same request. The docs don't describe this pair's behavior. On this machine the server **returned HTTP 200** and the answer was:

```json title="From the record, with field names preserved"
{ "role": "assistant", "content": "{\"name\": \"viki_ara\", \"arguments\": {\"question\": \"In which year did Marmaray enter service?\"}}" }
```

So: there's **no** `tool_calls` in the `message`. The model didn't call a tool; it wrote the tool call's **JSON text as plain content**. The structured-output mode appears to have replaced the tool protocol. Its practical counterpart: on a line using `format: "json"`, if you expect `tool_calls` the loop never starts: the call stays as a text blob, and your application either never sees it or has to parse it by hand. If you choose manual parsing, that's no longer tool calling — it becomes a line where **the model produces a text and you interpret it**; type, required-field and name checking falls to you.

:::note[The suggested fix, not measured]
The most prudent path against this behavior is to leave the `format` field empty on requests that use tools, and if the format is needed, do it in a separate pass **after the tool**. This advice rests on a single observation, and we didn't run the alternatives on this machine; repeat trial `G` on your own catalog.
:::

## Is tool_name Required in the Tool Message (H)

B, sent with `tool_name`, and H, with the field removed, produced **exactly the same input token count** (2,623) and the same two turns on the same question; H's output was 253 tokens, B's 336 (B's was longer because it was cut at the limit). In a two-tool catalog, on a single-call turn, the absence of the `tool_name` field didn't break the loop. In the exploration run, all three forms (`tool_name`, plain `content`, `tool_call_id`) had produced the same 240-token input. Still, when the same tool is called **twice**, the guarantee for matching the result to the right call is `tool_call_id`; since that scenario didn't occur in this run, we write it as a defense, not a claim.

## The Measurement's Own Error: Where Did 3600 Meters Come From?

In scenario C the model called `birim_donustur({"amount": 1, "source": "h", "target": "m"})` — a time unit for a length question. The tool should have rejected it; **it didn't**, it returned `1 h = 3600 m`, and on the next turn the model said "the T1 line's length is 3600 meters". The reason is the script's own line:

```python
if UNITS[source] * UNITS[target] <= 0:   # not a dimension check, a product check
```

Since the factors are positive, the condition never fires; time and length units are being converted into each other. This is a flaw in the measuring instrument, not in the measured behavior — and the record's honest reading is this: **half of the number we thought the agent fabricated was our own tool's accepted garbage argument.** If your tools don't reject bad arguments, you're left with no evidence to blame the model. That line in the script stands on the [Example 7 page](/en/ornekler/ajan-dongusu/) with a fix suggestion; the numbers on the page weren't changed because they came from the pre-fix run.

## Practical Conclusions

1. **The turn count doesn't grow latency proportionally; the context size does.** The same two-turn loop ranged from 12.1 s (C) to 95.2 s (B); the difference isn't the turn count but the tokens the second turn read.
2. **An agent log without `done_reason` is incomplete.** A cut-off answer isn't an error; it's silent in the log.
3. **Keep the tool results short.** `viki_ara` returned 3,498-4,994 characters; that directly determined the next turn's pre-fill. Lowering the `k` value from Example 6 works even harder in an agent.
4. **Keep the catalog small, bring the description down to one sentence.** The expense isn't fixed per tool; it scales with length.
5. **Have a tool result over the threshold be told to the model as text, not as a number.** In scenario D the user saw "0.496".
6. **Don't build the agent with a claim of answer quality.** In this run both pipelines gave the same answer; the agent won nothing in exchange for two turns and a cut-off sentence.

## What Wasn't Measured Here

- **The gain.** There's no question in this set where the fixed line was wrong and the agent right; the numbers only tell the cost. For quality, the two pipelines would have to be compared with the set on the [RAG Evaluation](/en/rag/rag-degerlendirme/) page.
- **The discriminating `tool_choice` test** (a tool-free question + `required`) and **third-turn behavior**: `MAX_TURNS` is 5 but no scenario went to a 3rd turn; a loop closed by the counter limit wasn't observed.
- Selection accuracy on a 3+-tool catalog; tool calling with `stream: true`; the effect of a 4,000+-token catalog on `num_ctx` truncation.
- The turn count with bigger/cloud models: the behavior measured here is `qwen2.5:3b` capacity's behavior.
- The cost of the same two tools through an MCP server: there's no documented path of Ollama acting as an MCP client (see the [Mechanics](/en/ajan/arac-cagirma-ve-mcp/) page).

## Repeat This Measurement on Your Own Machine

```bash
cd ornekler/ajan-dongusu
# Ollama must be running; don't send other Ollama requests
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u ajan.py > cikti/ajan-kaydi.txt 2>&1
```

On the first run the script downloads the corpus from Wikipedia and writes it to `cikti/korpus.json` (the second run reads it); it takes the embedding vectors from the `ornekler/viki-rag/cikti/vektor-index.json.gz` cache and re-vectorizes if the signature doesn't match. Do the redirection with `>`, not `| tee`, and use `-u` — in this project, because of buffering, a long run was lost to `tee` costing 20 minutes: [Speed and Cost](/en/kullanim/hiz-ve-maliyet/).

## Sources and further reading

- [Example 7: The Agent Loop](/en/ornekler/ajan-dongusu/) — the script itself, the tool definitions and the line-by-line reading.
- [Tool-Calling Mechanics and MCP](/en/ajan/arac-cagirma-ve-mcp/) — the request/response format, the template requirement, MCP's scope.
- [Agent or a Fixed RAG Pipeline?](/en/ajan/ajan-mi-sabit-hat-mi/) — which decision these numbers justify.
- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — the cache, the pre-fill bands, the cold start and repeating the measurement.
- [Example 6: Turkish RAG from Wikipedia](/en/ornekler/viki-rag/) — the fixed line's warm-measured latency.
- [Ollama Chat API](https://docs.ollama.com/api/chat.md) — the official documentation of `tools`, `tool_calls`, `format` and their fields.
