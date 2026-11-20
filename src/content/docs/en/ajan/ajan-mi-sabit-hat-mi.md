---
title: "Agent or a Fixed RAG Pipeline?"
description: "We compare when turning your RAG pipeline into an agent loop adds value and when it adds latency and uncertainty — with a decision ladder, four questions and measured cost bands."
dogrulama: 2026-11-20
---

The [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/) page solves the question "is fine-tuning needed?". This page solves a sub-question: **should the RAG pipeline you built be smart or fixed?** Example 6's pipeline is fixed: on every question it embeds, retrieves pieces, reads the context to the model, and answers. The decision isn't made by the model; it's made by the order of the code you wrote. An **agent loop** leaves the decision to the model: will it call a tool, with which arguments, for how many turns? That difference looks like a capability gain at first glance; when measured locally, part of it turns out to be a payment in latency and uncertainty. This page explains when that payment is worth making.

**The one-sentence answer:** if the tool sequence is known and the same on every query, a fixed pipeline; if the model needs to decide which resource to call or whether a second pass is needed, an agent loop — and until then, measure the agent's bill.

## The Decision Ladder: The Agent Is the Top Rung

If we open the part of the ladder on the [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/) page that sits above RAG:

```text title="The same principle, finer rungs"
5. Agent loop         → the model decides how many times and in what order to call tools
4. Fixed multi-tool   → you order the two tools, the sequence is query-independent
3. Fixed single line  → one retrieval, one generation (Examples 5 and 6)
2. Routing            → you classify the query and pick the PIPELINE (code, not a model)
1. Prompt only        → no tools at all
```

The ladder's rule is the same as the previous page's: show a concrete reason to climb. Rung 2 fills most "should I build an agent?" plans — a single classifier separates whether the query wants RAG or a tool-less answer, at the cost of one extra pass.

## The Four Questions

Leaving a pipeline fixed when the answer is "yes" to all four is a loss; if even one is "no", the agent is justified.

| Question | The answer saying "a fixed line suffices" | The answer saying "an agent is needed" |
| --- | --- | --- |
| **Is the tool sequence fixed?** | Retrieval first, then the answer, on every query | The resource changes with the query (sometimes retrieval, sometimes calculation, sometimes both) |
| **Is the number of passes known in advance?** | One pass | The "search again if needed" decision depends on the data |
| **Does the tool result need interpreting?** | The result goes straight into the context | If the result is insufficient, it needs trying again with different arguments |
| **What's the latency budget in seconds?** | Tolerance of seconds | The user doesn't know the wait time in turns |

The third question is the agent's real justification and the least talked about: the fixed line must read the context it retrieved even if it's bad. The agent, on a sub-threshold tool result, can re-formulate the question and search again. This is the dynamic form of the "what's done below the threshold" discussion on the [Chunking and Hybrid Search](/en/rag/parcalama-ve-hibrit-arama/) page.

## The Agent's Bill: All Three Items Measured

An agent loop doesn't get smart for free. Three expense items measured on this machine (AMD Ryzen 5 2600, CPU, `qwen2.5:3b-instruct-q4_K_M`):

**1. The tool definition is paid as input tokens on every turn.** Tool schemas are embedded in the request and count as input tokens. OpenAI's official doc says it plainly: *"callable function definitions count against the model's context limit and are billed as input tokens"*, and recommends reducing the tools' number/length as the first measure. Anthropic's doc advises "at least 3-4 sentences" for a single tool definition's description — that's text added per request. Measured on this machine: a base 73-token prompt rises to 237 with one tool and 346 with two (**+273 tokens**), and those 273 tokens are paid from scratch on every turn of the loop (trial `E`: [Agent Measurement](/en/ajan/ajan-olcumu/)).

**2. Every turn reads the growing message list from the start.** The loop's second turn carries the first turn's messages and the tool result again. The only consolation here is prompt caching: on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page, the same prefix's second read was measured at **18.96 s → 0.08 s** (687 tokens came from cache). Caching makes reading the unchanged prefix cheap per turn; but the new tokens the tool result adds are paid again every turn. How many tokens per turn escaped from cache in the loop was dumped line by line in Example 7's record: [Agent Measurement](/en/ajan/ajan-olcumu/).

**3. Unanswerable questions burn turns.** A query of the type "Is it raining in Istanbul right now?", which no tool can answer, burns as many passes as the turn counter if the model keeps calling tools. On the fixed line this is a single threshold check ([Example 5's](/en/ornekler/yerel-rag/) out-of-scope test); in an agent loop it's a multi-turn ordeal.

The per-turn wall time, how many turns got burned, and whether the `tool_choice` field constrains this were measured on this machine with Example 7's script: [Agent Measurement](/en/ajan/ajan-olcumu/).

## The Hybrid Path: Most Projects' Real Answer

Fixed line vs. agent is a false dilemma; most shipped solutions mix the two:

- **Fixed outside, free inside.** The user's first question passes through the fixed RAG pipeline (known latency, guaranteed citation). If the model says "a second source is needed", the agent kicks in. That way the worst-case latency starts from the single-turn line.
- **A turn counter.** Put an upper bound on the loop (Example 7 uses `MAX_TURNS = 5`). A loop without a counter is a cost without an end when the model won't stop calling tools.
- **Structured output instead of forced tools.** Ask the model for structured output of the "fill these fields" form and trigger the tool call yourself; the freedom stays only in the argument text. This is the cheapest way of keeping the sequence fixed while leaving the interpretation to the model.

:::caution[A local small model isn't the same as a closed model]
Agent behavior depends on model capacity. The list of models that can call tools sits separately in the Ollama docs and separately on model cards, and the `qwen2.5:3b-instruct-q4_K_M` we measured in this guide is a small model. On a cloud model that makes fewer tool-choice errors, how many turns the same loop closes in — not measured here. Read this page's "turn-burning" behaviors not as a flaw but as an expense that scales with capacity.
:::

## Common Decisions

| Situation | Recommendation | Reason |
| --- | --- | --- |
| Corporate document Q&A, a single source | Fixed line (Examples 5/6) | Latency and citation auditing stay with you |
| You have retrieval + a calculator + a database, and the query's choice is unclear | An agent, with a turn counter | The sequence can't be written independently of the query |
| Multi-step report generation, the user can wait | Agent | Turn cost is second to the accuracy gained |
| An instant search box with a 1 s budget | A fixed single line or no tools | The turn count grows latency linearly |
| The model might not know the answer | A fixed line + a threshold | The out-of-scope check is a one-line programmatic job |

## What Wasn't Measured Here

- The ratio of cases where the agent answers **more accurately** than the fixed line: this page measures the cost, not the benefit. For the benefit measurement, the question-answer set on the [RAG Evaluation](/en/rag/rag-degerlendirme/) page would have to be run on both pipelines.
- Realistic multi-tool scenarios (10+ tools): two tools are defined here. How the tool count harms selection accuracy passes in the literature as "too many tools", but OpenAI's "dozens of tools → high cost and latency" warning is qualitative; there's no numeric threshold.
- Agent features like persistent memory, planning and feedback (Reflexion-style self-critique); this page covers only the tool-calling loop.

## Sources and further reading

- [Agent Measurement](/en/ajan/ajan-olcumu/) — Example 7's turn, token and second numbers; the result of the `tool_choice` and `format` trials on this machine.
- [Tool-Calling Mechanics and MCP](/en/ajan/arac-cagirma-ve-mcp/) — the loop's request/response format and where MCP standardizes this job.
- [Example 7: The Agent Loop](/en/ornekler/ajan-dongusu/) — the script producing the measurement itself, explained line by line.
- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — the cache, the per-turn server work and how to repeat the measurement.
- ReAct: Synergizing Reasoning and Acting in Language Models, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) — the pattern of producing reasoning and action in sequence; the agent loop's academic name.
- Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity, [arXiv:2403.14403](https://arxiv.org/abs/2403.14403) — the controller that classifies the query and picks the retrieval step as none/one/repeated; the trained form of this page's rung 2.
