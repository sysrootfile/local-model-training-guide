---
title: "Local Inference Speed and Cost: Measured Numbers"
description: "Why a local model's answer takes seconds. The measured distribution of cold loading, pre-fill, decode and time-to-first-token on this machine; num_ctx's memory steps and the silent truncation trap; the gain from the prompt cache; Turkish text's characters/token ratio; plus the two-second name-resolution expense paid in your code, independent of Ollama."
dogrulama: 2026-11-20
---

In Examples 5 and 6 you read numbers like "the answer takes 52-66 s", "query embedding 0.144 s" (the first publication of this page's measurements rests on those examples' days measured with `http://localhost` — the 57-69 s / 2.168 s figures; what that overhead was sits at the bottom of this page). Those numbers have to come from somewhere. This page is where they come from: a measured latency breakdown on the same machine, with the same models.

There's no benchmark here. A benchmark says "such-and-such model is the fastest"; this answers another question: **why does a question take this long, and where are you paying.** The numbers will differ on your machine; what matters is the phases' order and which dominates.

:::note[Every number on this page was measured]
All of it on this machine, at 100% CPU, from the `ornekler/cikarim-olcu/hiz_olc.py` rig — **except the "Batched embedding" section**: that section's two arms ran with `ornekler/gomme-egitimi/gomme_egit.py --kol e`, on the same machine, also at 100% CPU. **Two rounds were run:** in the first the script used `http://localhost:11434` (`cikti/hiz-log.txt` and `hiz-log-4.txt`), in the second `http://127.0.0.1:11434` (`cikti/hiz-log-127.txt`, 2026-10-16 01:21-01:39). The tables below's body is **from the second round**; only the "Batched embedding" table is from the E run on October 20. Comparing the two rounds showed two things: (1) wall times dropped ~2 s/request depending on the address, (2) **the server's own speeds also wobble run to run** — pre-fill by the difference method 39.9-40.5 → 43.9-45.9 tok/s, decode 13.8-14.0 → 13.9-14.8 tok/s; the memory steps (`ollama ps`) matched exactly. The wobble is as big as the address overhead alone: don't trust a single measurement on this page. Where we say something we didn't measure, it says "not measured" separately.
:::

## The machine and the models

| Item | Value |
| --- | --- |
| CPU | AMD Ryzen 5 2600, 6 cores / 12 threads |
| RAM | 15.9 GB; 2.0-3.6 GiB free during the run (the system 87% full) |
| Disk | SATA SSD (ADATA SU650) |
| Server | Ollama 0.40.4 (the page body's measurements; the machine moved to 0.40.6 on 2026-10-19, the body numbers weren't re-measured on that version). The "Batched embedding" section added on 2026-10-20 was measured on 0.40.6; `ollama ps` output says "100% CPU" |
| Address | the tables below use `http://127.0.0.1:11434`; the first round used `http://localhost:11434` |
| Chat model | `qwen2.5:3b-instruct-q4_K_M`, resident size 2.2 GB |
| Embedding model | `bge-m3`, vector size 1024 |

## The anatomy of a request: four phases, four separate prices

Ollama hands you numbers at the end of every answer. The thing to grasp is that those numbers **aren't the same unit**:

```text
total_duration  = load + pre-fill + decode   (nanoseconds)
load_duration      the model settling into memory
prompt_eval_count  input token count         /  prompt_eval_duration
eval_count         generated token count     /  eval_duration
prompt_eval_cached_count  tokens from cache, not recomputed
```

- **Pre-fill:** everything you wrote (the system prompt, the RAG context, the question) is fed to the model in one go. Since it can be processed in parallel, it's *fast*.
- **Decode:** the model produces the token one by one. Every step reads all the prior context, so it's *slower*.
- **Time to first token (TTFT):** the moment the user waits until something starts appearing on screen. It's the sum of load + pre-fill.

The two speeds measured on the same request:

| Phase | Measured speed (2026-10-16, `127.0.0.1`) | What it means |
| --- | --- | --- |
| Pre-fill, uncached | **36.3-37.4 tok/s** (E4, a 688-token context) · **43.9-45.9 tok/s** (E3b, by the difference method; a 1,329-token input in 28.92 s) | a cost rising linearly as the context grows |
| Decode | **13.9-14.8 tok/s** (the same band at 64, 256 and 412-token generations) | every generated token is fixed-price |

So on this machine an input token is **2.5-3.3x cheaper** than an output token (dividing the two bands' ends: 36.3/14.8 = 2.5 to 45.9/13.9 = 3.3). Try the numbers: a 700-token answer ≈ 47-50 s, a 700-token context ≈ 15-19 s.

:::caution[The longer the answer, the longer the wait]
The decode speed is fixed: 64 tokens in 4.42 s, 256 in 18.48 s, 412 in 27.90 s (67.7-72.2 ms/token). On this machine, keeping the answer long is more expensive than keeping the context long. That's the practical counterpart of setting a ceiling with `num_predict`.
:::

### Time to first token, measured in streaming mode

The user doesn't wait for `total_duration`; they wait for the first letter. In E7 and E7b streaming was turned on and the first chunk's arrival time measured:

| Request | First token | Total |
| --- | --- | --- |
| Short prompt (E7b, turn 1) | 4.04 s | 6.60 s |
| Short prompt (E7b, turn 2 — cache warm) | **0.08 s** | 2.62 s |
| Long prompt, 688-token context (E7b, turn 1) | 10.92 s | 13.79 s |
| Long prompt (E7b, turn 2) | **0.10 s** | 2.96 s |
| The same two requests, the E7 run | 8.80 s / 12.94 s | 11.7 s / 16.0 s |

Three lessons. (1) Your TTFT is the pre-fill itself: as the context went from 211 to 688 tokens, the first token rose from 4.04 s to 10.92 s. (2) The cache drops it to 0.1 s — meaning **a second turn continuing with the same context starts dramatically faster than the first.** (3) Decode is independent of this: 40-token generation takes 2.5-2.9 s in every row. Note: E7 and E7b measured the same requests with different figures, but the E7 record doesn't report that moment's cache and memory state on a separate line; we **didn't measure** the cause of the gap, so we kept E7 on a separate row.

## Cold or warm: the value of the model sitting in memory

The same short question, in three states:

| State | Wall (what you wait) | Server | Load | Pre-fill | Decode |
| --- | --- | --- | --- | --- | --- |
| `keep_alive: "0"` (it unloaded after the call) | 2.2 s | 2.12 s | 0.01 s | 37 tok / 1.02 s | 16 tok / 1.07 s |
| Cold call (just unloaded, reloaded) | 11.4 s | 11.35 s | **9.15 s** | 37 tok / 1.07 s | 16 tok / 1.11 s |
| Warm call (ready in memory) | 1.2 s | 1.22 s | 0.02 s | 37 tok / 0.09 s (430 tok/s, 36 cached) | 16 tok / 1.11 s |

In all three rows **wall and server overlap** (the gap 0.00-0.08 s). In the first round this gap was always ~2.0 s; when the address moved from `localhost` to `127.0.0.1` it vanished — i.e. the figures below are now genuinely the model's work.

Cold loading isn't one number: in this round it was **9.15 s** in E1, **3.10-3.12 s** across five reloads in the same round's E10 cycle, and 3.1-3.4 s in the first round. A band of 3-9 s on the same machine, the same model; the rule you can lean on, "a cold call costs a few seconds more than a warm one", isn't fixed. Ollama keeps the model in memory for **5 minutes** by default (`OLLAMA_KEEP_ALIVE`; overridden per-request with `keep_alive`).

The unload/load cycle was repeated five times: the reload calls' wall time was **4.9-5.0 s** (7.3 s in the first round — the gap again the name-resolution overhead).

The `ollama ps` output is the checkpoint of this decision; if it says "4 minutes from now", the next question will go warm.

## num_ctx: memory steps and silent truncation

The context window (`num_ctx`) is "how many tokens the model can see together". The measured effect:

| `num_ctx` | `ollama ps` size | Tokens evaluated | Result |
| --- | --- | --- | --- |
| 512 | 2.0 GB | **258** | 430 of a 688-token request **silently dropped** |
| 2048 | 2.1 GB | 688 | fit |
| 4096 (default) | 2.2 GB | 688 | fit |
| 8192 | 2.4 GB | 688 | fit |

:::caution[Truncation tells you nothing]
In the 512 row we got no error, no warning, HTTP 200. The only proof is that half the text you thought was answered was genuinely never read. In RAG this means: **if you don't check the total token count while stuffing pieces into the context, the model hasn't seen part of the documents it retrieved, and you'll attribute the quality drop to the model being dumb.**
:::

Two more observations: every `num_ctx` change reloaded the model (3.48-6.79 s `load` per row; 3.2-3.5 s in the first round). And growing the context didn't change the generation speed (decode in the 12.6-13.1 tok/s band) — what scales is memory and pre-fill time. For the method of the memory math and the GPU side see the [VRAM/RAM page](/en/donanim/vram-hesabi/), for Ollama's memory tiers the [Ollama page](/en/kullanim/ollama/); these are CPU-measured values.

## The prompt cache: reading the same context a second time

When the same 688-token request was sent again:

| Read | Tokens | From cache | Pre-fill time |
| --- | --- | --- | --- |
| The first read (E4, `num_ctx=8192`) | 688 | 0 | 18.96 s |
| The same prefix, later reads (E5) | 688 | **687** | **0.08 s** |
| The trailing question changed (E5) | 679 | **661** | 0.75 s |

The cache matches the context's *prefix*. This turns into a direct design rule for RAG and agent loops: **put the context first, append the question last.** Changing the final sentence cost a recomputation of 679 − 661 = 18 tokens; rewriting from the start would have cost all 688.

:::note[The gain is real, but not unlimited]
The cache is held in RAM and its size isn't configurable; the complaints of people running Ollama about this sit in an open issue (ollama/ollama #17351, "Make prompt cache size configurable", 2026-07). The first round's log showed the biggest cache state as 4 prompts / 334 MiB; at the end of the second round the log recorded 0 prompts / 0.000 MiB — i.e. when the model was unloaded, the cache reset too (that's why E9 phase B showed 0 cached tokens until the second call).
:::

## num_thread: on CPU, do more threads mean more speed?

| `num_thread` | Pre-fill | Decode |
| --- | --- | --- |
| 2 | 16.9 tok/s | 9.0 tok/s |
| 6 (the physical core count) | 32.8 tok/s | **14.5 tok/s** |
| 12 (logical threads) | **44.6 tok/s** | 13.3 tok/s |

Two separate curves: pre-fill is parallelizable and still wins at 12 threads; decode peaks at 6, with **no gain** after (13.3 vs 14.5). The reason is that a single token's job can't be split across cores; memory bandwidth becomes the bottleneck. The rule: raise the thread count for long-input jobs, leave it default for chat feel.

The first round's same test had given 17.4 / 36.6 / 44.9 tok/s pre-fill and 9.0 / 13.9 / 12.8 tok/s decode. The shape is the same, the figures shift — 12 threads' harm to decode was 1.1 tok/s in one round, 0.6 in the other. We're not saying "6 is the ideal" off one measurement; we're saying "there's no decode gain at 12".

## The token price of Turkish text

The Turkish counterpart of the circulating "1 token ≈ 4 characters" rule for English was measured. Method: send twice the size of the same text and **divide the token difference by the character difference** — that way the chat template's fixed expense leaves the calculation.

| Character difference | Token difference | Ratio | Time difference | Pre-fill speed |
| --- | --- | --- | --- | --- |
| 476 | 159 | 2.99 characters/token | 3.62 s | 43.9 tok/s |
| 952 | 318 | 2.99 | 6.92 s | 45.9 tok/s |
| 1,904 | 636 | 2.99 | 14.32 s | 44.4 tok/s |

The last two columns are from E3b: a unique number was prepended to each row's start to break the cache match, so the time is genuinely an uncached pre-fill start to finish. The ratio was the same in the first round too (2.99); the time columns wobble ~10% round to round — **the characters/token ratio is deterministic, the speed isn't.**

**Turkish text produces ~3 characters/token** (not 4). For a paragraph the ratio stayed fixed in the 2.94-2.99 band. Use the result in two places: (1) when estimating your context in tokens, divide the character count by 3, not 4; (2) in cloud API pricing, Turkish content is more expensive for the same word count. The [Tokenization page](/en/temeller/tokenizasyon/) has the linguistic reason for this ratio.

## A RAG query's real cost breakdown

The distribution of the time until a question is answered (server side; the client overhead is the next section):

| Job | Measured |
| --- | --- |
| Embedding the query (11 tokens, `bge-m3`) | **0.09-0.13 s** |
| Embedding a 1,904-character (450-token) piece | **2.47-3.04 s** |
| `bge-m3`'s cold-load cost | 11.92 s — measured **only in the first round, once**; in the second round the model was in memory, not repeated |
| Pre-filling a 683-token context into the chat | 17.62 s (38.8 tok/s, 3 cached tokens) |
| Producing a 49-token answer | 3.89 s |
| Total answer time (wall) | 21.5 s |

The proportion is surprising: **retrieval 0.1 s, generation 21.5 s.** RAG's expensive part isn't the vector index, it's reading the text you found to the language model. Example 6's 52-66 s answers are computable from here too: 4 pieces ≈ 2,450 tokens, 2,450 ÷ ~40 tok/s ≈ 61 s.

:::note[The slowdown while both models are in memory wasn't measured]
With the chat model in memory, query embedding was 0.10 s, and 0.09 s after unloading; the long piece 2.55 s vs 2.47 s. On the 15.9 GB machine, at 87% fullness, the second model's presence produced no measurable penalty. (That doesn't mean memory pressure never penalizes — it means it didn't under these conditions. In E8b the embedding times didn't change even while the chat model sat at 2.2 GB.)
:::

## Batched embedding: 24 pieces in one request, or 24 separate requests?

Building a RAG index, you have to embed the pieces. `/api/embed` accepts a **list** in one request; you could also send the same 24 pieces in 24 separate requests. The question: is the difference a per-request fixed expense, or the computation itself?

This comparison was measured on 2026-10-20, on Ollama **0.40.6**, in a single session and after the model was warmed. Both arms send the same 24 fictional sentences (`bge-m3`, 583 tokens total) to the same server; the only difference is how the requests are split. Each arm ran five times, the order alternating between repeats (1/3/5: single→separate, 2/4: separate→single). The times are wall-clock; the counted total is 125 measurement requests, excluding one warm-up and one eviction request.

| Arm | Five repeats (s) | p50 | p95 | Min-max | Five repeats total |
| --- | --- | --- | --- | --- | --- |
| 24 pieces in one request | 4.58 · 4.57 · 4.73 · 4.44 · 4.64 | **4.58** | 4.71 | 4.44-4.73 | 22.97 s |
| 24 separate requests | 4.90 · 4.96 · 4.86 · 5.01 · 4.97 | **4.96** | 5.00 | 4.86-5.01 | 24.69 s |

The two arms' repeat ranges don't overlap (4.73 < 4.86). That was the pre-written rule: if the ranges overlapped we'd say "the difference couldn't be measured", and if they didn't, the arm with the lower p50 would win. **The single request is cheaper:** the p50 gap is 0.38 s, i.e. 24 separate requests are 1.08x the single request.

But look at the magnitude. In 24 separate requests the per-request p50 is **0.204 s** (p95 0.254); the same job's per-piece share in the single request is 4.58 / 24 = **0.191 s**. If you divide the total 0.38 s gap across 24 requests, ≈0.016 s per request remains. Since the embedding job itself took 4.4-5.0 s, batching's gain on this corpus is **about 8%**; the expensive thing isn't the request count, it's the computation itself. There's no meaningful extra client-side overhead either: in the 24 separate requests the gap between wall and the server's total time was 0.05-0.09 s, in the single request 0.01-0.03 s.

The token counts were 583 in both arms. So the 24 requests aren't recomputing the same text 24 times; each request sees only its own sentence and the total work stays the same. The server's own `total_duration` total gives the same picture: p50 4.57 s for the single request, 4.87 s for the 24 separate ones (the gap from wall is the client side).

:::caution[This number isn't comparable with the 24-piece measurement on the Training an Embedding Model page]
The 24-piece single-request measurement on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page was taken on 0.40.4, in a different run, without separately recording the model's warm state. The two arms here were measured on 0.40.6, in the same session, with the warm-up request excluded. The two numbers aren't the two sides of an A/B; don't put them side by side and say "batching sped it up by that much". Batching's gain is read only between the two arms in this table.
:::

Limits: 24 pieces / 583 tokens is a small job; in a bigger batch the fixed expense's share falls further, but a batch larger than 24 was **not measured**. Running the `/api/embed` requests concurrently is also outside this run. The five repeats' distribution is given, no confidence interval was derived.

## The two seconds inside your prompt

In the measurements' first round there was a stubborn consistency: the server said 1.2 s while the wall said 3.2 s. The gap was always ~2.0 s. We hunted the source (E11, first round):

| Hypothesis | Test | Result |
| --- | --- | --- |
| Proxy detection | calling with `ProxyHandler({})` disabling it | **eliminated**: 2.05 s → 2.08 s |
| The TCP connection setup overhead | a direct connection with `http.client` | **eliminated**: a 0.00 s gap |
| Resolving the `localhost` name | the same request with `http://127.0.0.1:11434` | **found**: 2.03 s → **0.00 s** |

The second round (2026-10-16) repeated the same test while the script used `127.0.0.1` — and there was no 2-second gap left to eliminate: in the default environment the median gap of 4 trials was **0.00 s**, and **0.03 s** with the proxy disabled. So the first round eliminated the proxy; the second round verified the address change itself.

The single-call proof with both addresses (E12, second round; each row 4 trials):

| Address and client | Wall − server gap (median) | Trials |
| --- | --- | --- |
| `http://localhost:11434` (urllib) | **2.04 s** | 2.05 / 2.05 / 2.04 / 2.03 |
| `http://127.0.0.1:11434` (urllib) | **0.00 s** | 0.00 / 0.00 / 0.00 / 0.00 |
| `http://127.0.0.1:11434` (`http.client`) | 0.00 s | 0.00 / 0.00 / 0.00 / 0.00 |

On Windows, resolving the `localhost` name takes ~2 s per request; the numeric address does the same job instantly. It has nothing to do with the model, the CPU or the RAM — one word in your code.

The effect's size depends on the call count per loop. A 10-piece indexing A/B (E13, second round):

| Address | 10 pieces total | Per piece | The server's work | Client overhead |
| --- | --- | --- | --- | --- |
| `localhost` | 32.5 s | 3.25 s | 12.2 s | **20.4 s (63%)** |
| `127.0.0.1` | **12.5 s** | 1.25 s | 12.4 s | 0.0 s (0%) |

The first round's same A/B had come out **35.6 s / 16.1 s**. Putting the two rounds side by side, what's stable is the client overhead: 20.3 s over 10 requests, then 20.4 s (2.03-2.04 s each). What's unstable is the server's work: on the `localhost` side 15.3 → 12.2 s, on the `127.0.0.1` side 16.1 → 12.4 s. So the ratio (57% → 63%) changes on its own; on this machine a speed measurement isn't done once.

:::caution[This overhead was half the site's indexing times — now measured]
When this page was written, all of Examples 5-6 and the RAG scripts used `http://localhost:11434`; i.e. the indexing times you read included the ~2 s per-request name resolution, and the "125 pieces × 2.03 s ≈ 254 s" split was only the arithmetic of **two measured components**. On 2026-10-16 the address was switched to `http://127.0.0.1:11434` and the same scripts re-run: the same 125 pieces, the same machine, the same ranking results — `hibrit.py`'s vectorization **529.3 → 253.0 s**, `olc.py` bge-m3 **495.7 → 259.2 s**, nomic-embed-text **503.7 → 158.6 s**. The prediction held; in fact the second model's drop reached 345 s, suggesting that machine load (RAM fullness) may have been added to the DNS overhead in that old run. The pages' current indexing/answer times come from these re-runs.
:::

## The stall hunt: the death of a hypothesis

The story of this page's writing is honestly this: during the first round's measurements, a short request took **42.7 s**; whereas the same call's model work was 1-2 s. The lines accumulating in the log (on Windows, `%LOCALAPPDATA%\Ollama\server.log`) looked guilty:

```text
srv  get_availabl: prompt cache update took 92.7 ms
srv        update:  - cache state: 4 prompts, 334.237 MiB (limits: 8192.000 MiB, 4096 tokens, ...)
```

The hypothesis "as the cache grows, requests lock up" was formed. Then it was measured and broke in three places:

1. **The unit check.** The last 2 MB of log had 126 "prompt cache update" lines in the first round, 118 in the second; their largest were **92.7 ms** and **68.5 ms** respectively. Milliseconds. That can't explain a 60-second stall — a single unit letter sufficed for the hypothesis's collapse. The last cache state written in the second round's log was also **0 prompts / 0.000 MiB**: there wasn't even a grown cache around.
2. **Reproducibility.** Identical warm calls ran 8 times. First round: wall 3.3-3.5 s, the biggest gap between `total_duration` and the phase sum 0.07 s. Second round (`127.0.0.1`): wall **1.3-1.5 s**, the biggest gap **0.02 s**. The unload/reload cycle repeated 5 times: 7.3 s in all five in the first round, **4.9-5.0 s** in the second. The outlier didn't appear in the second round — the slowest of E10's eviction calls was 5.3 s. The only call exceeding 15 s in the second round was the first call right after eviction (23.3 s), and even that fits the math: 3.11 s reload + an uncached 688-token pre-fill; the gap between the phase sum and the wall was 0.01 s.
3. **The log's own accounting.** The `print_timing` records next to the log's 20-59 s request lines give the whole duration. Example (a record dated 2026-10-14, not from this run): a 49.34 s `POST /api/chat` = 46.59 s pre-fill (2,046 tokens, 43.9 tok/s) + 2.60 s decode (27 tokens, 10.0 tok/s). In the second round's window, 36 of 907 `POST` requests were over 20 s (the biggest 59.9 s); in the E10 window, 67 of 1,427 — all of them real work with long contexts.

So there was no "stall"; there was **real work with long contexts**, and we'd named it wrongly. The one remaining outlier observation (n=1) went unexplained; it didn't appear in the measurement repeat.

:::note[Why we're keeping this section]
Because it's the page's most instructive part. Everything that feels a bit slow isn't "the server stalling"; phase it first, then look at the units. Ollama's four duration fields let you do this for free.
:::

## The practical decision list

Based on the measurements, in this machine's order:

1. **Write the address as `127.0.0.1`.** A ~2 s gain per call; the biggest single item in RAG loops.
2. **Put the context first, the question last.** The cache matches on the prefix: 687/688 tokens for free.
3. **Reduce the pieces you put in the context.** Pre-fill ~40 tok/s; a 2,450-token context is 61 s. One piece instead of three cuts the wait into thirds.
4. **Set `num_ctx` according to your total tokens and check it.** At 512, 430 of a 688-token request silently dropped.
5. **If you want a long answer, know its price.** Decode is fixed at 14 tok/s; 400 tokens ≈ 29 s.
6. **Keep it warm.** The `keep_alive` default is 5 min; cold loading isn't one number, the band measured on this machine is **3.1-9.2 s** (and a `num_ctx` change reloads it every time: 3.5-6.8 s).
7. **Set the thread count to the job.** 12 for bulk indexing/pre-fill, 6 for chat.
8. **Run the same measurement at least twice.** This page's two rounds moved the pre-fill speed from 39.9-40.5 to 43.9-45.9 tok/s and the decode speed from 13.8-14.0 to 13.9-14.8 tok/s. The band itself is the finding; not a single number.
9. **Batch the embedding.** The same 24 pieces: p50 4.58 s in one request, 4.96 s in 24 separate ones; the gain about 8%. The per-request fixed expense on this machine is milliseconds, the real cost is the computation itself.

## Repeat this measurement on your own machine

The rig is a single file, using only the Python standard library (no dependency beyond Ollama):

```bash
cd ornekler/cikarim-olcu
PYTHONUTF8=1 python -u hiz_olc.py > cikti/my-record.txt 2>&1
```

The run takes 20-40 minutes and has **one submissive rule:** send no other Ollama request until it finishes (no chat interface, no editor extension, no other script). The server with default settings schedules for a single user — which is now a measurement, not an expectation: in the [Concurrency](/en/kullanim/eszamanlilik/) page's K=4 wave, the four requests' wall times lined up like a 4.7 / 9.4 / 14.0 / 18.5 s staircase, and the per-request decode speed never changed. (The same page also carries a second run with `OLLAMA_NUM_PARALLEL=4`: there the staircase is gone, but a single request's speed drops. So the rule's cause is the setting, not fate.) A competing request inflates your wall times. If you like, pick a single experiment with `--yalniz E4 E5`; `--kisa` runs only E1, E2, E3, E7. How the raw logs are read (which `duration` field each line comes from) is in `ornekler/cikarim-olcu/README.md`.

:::caution[Write the output straight to a file]
Don't use `... | tee log.txt`: in this project `tee` exited early and destroyed a 20-minute run's output. `python -u` is also mandatory — run without the flag, the output stays in the buffer and the log looks empty while the run is going.
:::

## What wasn't measured here

- No GPU measurement at all (no torch on this machine, no graphics card used). The numbers are for 100% CPU.
- Other model sizes, other quantization levels, other CPUs. This rig describes one machine.
- `bge-m3`'s cold load: 11.92 s is a **single observation** (the first round). In the second round the model was in memory, not re-measured.
- The cause of the TTFT gap between E7 and E7b was **not measured** (run order, machine fullness and cache warmth changed together).
- Concurrency is now measured across three server settings and four runs, on the [Concurrency](/en/kullanim/eszamanlilik/) page: with the default setting, four requests released at once **don't race, they queue** (the K=4 wave's last request 18.50 s, a wait component of 14.11 s); with `OLLAMA_NUM_PARALLEL=4` the queue vanishes (a wait of 0.12 s) but a single request's speed drops 14.97 → 6.38 tok/s; at the `=2` setting, since more requests arrive than slots, the speed **doesn't drop, the queue grows** (9.13 → 9.22 tok/s; the first pair finishing in 7.1 s, the second in 14.2 s). All the times on this page are **a single request's** times, run with the `-np 1` default. `OLLAMA_NUM_PARALLEL`'s **3** level and multi-user persistent service behavior remain **unmeasured** — the server environment can't be written by a script; writing the variable and restarting is the machine owner's approval. Of K > 4, a single point is measured: **K = 8**, run on the default server on October 20, and the staircase pattern stayed the same; the numbers are on the [Concurrency](/en/kullanim/eszamanlilik/) page. K = 5-7, K > 8, and K > 4 on the `=2` / `=4` servers remain unseen.
- Batch embedding: the same 24 pieces' duration **in one request** and **in 24 separate requests** was measured together on October 20; the result is the "Batched embedding" section above. Sending a bigger batch (e.g. 125 pieces) in one request, and running the `/api/embed` requests concurrently, were **not measured**. The old 24-piece measurement on 0.40.4 sits on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page and isn't this comparison's baseline; the split's criterion is on the [Scope Map](/en/kaynaklar/kapsam-haritasi/) page.
- The effect of `OLLAMA_FLASH_ATTENTION` and `OLLAMA_KV_CACHE_TYPE` (default `f16`) was **not measured** on this machine — on CPU both gains are expected to be limited, but that's an expectation, not a measurement.
- The extra cost of structured output (`format`) and tool calling (`tools`) was **not measured**; tool-calling behavior and latency are planned as a separate section.
- The name-resolution overhead on non-Windows operating systems was **not measured**. This page's 2.03 s `localhost` overhead is a Windows observation; the same test's repeat on Linux/macOS isn't on the site.

## Sources and further reading

- [Ollama frequently asked questions](https://docs.ollama.com/faq) — the environment variables and defaults: `OLLAMA_KEEP_ALIVE` (5 min), `OLLAMA_MAX_LOADED_MODELS` (3x the GPU count, 3 on CPU), `OLLAMA_NUM_PARALLEL` (default 1), `OLLAMA_CONTEXT_LENGTH` (default 4096 tokens), `OLLAMA_KV_CACHE_TYPE` (default `f16`). Last verified 2026-10.
- [The Ollama chat API](https://docs.ollama.com/api/chat) — the definition of the `total_duration`, `load_duration`, `prompt_eval_duration`, `eval_duration`, `prompt_eval_cached_count` fields; this page's whole phase split came from these fields.
- [Ollama memory matters (issue #17351)](https://github.com/ollama/ollama/issues/17351) — the prompt cache size not being configurable; dated 2026-07, open.
- [llama.cpp measurement fields](https://github.com/ggml-org/llama.cpp) — the source of the log's `print_timing` lines ("prompt eval time", "eval time"); the real address for thread scaling on CPU.
- [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) — one more row for this page's phase table: a `num_predict=1` + `top_logprobs=20` request takes 2.1-2.9 s with a fresh (~100-token) prompt, and drops to 0.10-0.15 s when the same prompt's cache is warm.
- [Concurrency](/en/kullanim/eszamanlilik/) — all this page's times are for a single request; on the same machine, the four runs where 1/2/4 and 8 requests were released at once, the sequential queue's staircase proof, the `=2` setting's pairwise mix with queuing, and the signature of work-sharing when `OLLAMA_NUM_PARALLEL=4` is turned on are there.
