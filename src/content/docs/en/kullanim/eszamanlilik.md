---
title: "Concurrency: What Happens When You Ask Several Questions at Once"
description: "The same model, the same machine, 1, 2, 4 and 8 requests released at once — across four server settings and one overflow run on the default server: the default Ollama's queue staircase, OLLAMA_NUM_PARALLEL=2's pairwise couples and queue, =3's triple lock-step with a single straggler, =4's simultaneous finish with lock-step; at K=8 the staircase grows to eight steps but a single request's speed doesn't change. Wall, p50 and p95 per wave, system tokens/second, the memory price; the 2026-10-19, 2026-10-20 and 2026-10-26 records."
dogrulama: 2026-11-20
---

The question "how many requests can my server take" comes out of a mix of two separate settings, and if the two aren't separated in the measurement, the number is misread. On this page the separation is made first, then **the same rig runs in three server settings**: the same machine, the same model, 1, 2 and 4 requests released at once with a barrier. The result in three sentences: with the default setting, **four requests don't race, they queue** — the last user gets their answer at 18.50 s. With `OLLAMA_NUM_PARALLEL = 4` the queue vanishes (the wait drops from 14.11 s to 0.12 s), but **the work is shared**: the same wave takes 13.77 s and a single request's speed drops from 14.97 tok/s to 6.38 tok/s. **The middle level `=2` gives a mix of the two:** two of the four requests finish at 7.1 s, the other two at 14.47 s — because when more requests arrive than slots, the overflow queues again, but the sharing side is shared too. A fourth run was added on top of these three patterns: **eight requests** to the same default server (2026-10-20). No new pattern emerged — the staircase grew to eight steps, the last user got their answer at 38.17 s, but a single request's speed stayed in place at 14.15 tok/s and the system speed at 13.38 tok/s. So growing the crowd on the client side produces not speed but queue, on a single-slot server. A fifth run filled the missing middle level: on the **`=3` server** (2026-10-26, 0.40.11), **three of the four requests** finish with a lock-step at ~10.1 s and **the fourth arrives ~4.3 s later at its own full speed** — three slots absorb three of four requests, the overflow waits alone.

## Two Concurrency, Two Separate Settings

| What | Who decides | The status on this page |
| --- | --- | --- |
| **How many requests are released at once** (K) | The client: your script, your browser tabs, your application | measured: K = 1, 2, 4 (in three server settings) and **K = 8** (only on the default setting, 2026-10-20) |
| **How many requests the server tries to process at once** | The `OLLAMA_NUM_PARALLEL` environment variable, read at server startup | measured: default (=1), **=2**, **=3** (2026-10-26) and **=4** |

:::note[It's the server log that tells the setting, not the script]
`OLLAMA_NUM_PARALLEL` is the server's own environment variable: the script can't read it, only the person managing the machine writes it, and the server needs restarting. The [Scope Map](/en/kaynaklar/kapsam-haritasi/)'s third acceptance rule fixed this separation as "intervening in the server is the machine owner's"; the measured second and third arms ran exactly like that — the machine owner wrote the variable, they restarted the server.
But the value is no longer "information given by the user"; it's a **readable measurement**: Ollama writes the whole environment map into its log at every startup. Today's three server lines: `12:15:11` → `OLLAMA_NUM_PARALLEL:4`, `13:58:33` → `OLLAMA_NUM_PARALLEL:2`, and the morning one at 08:59 (a previous log file) → `OLLAMA_NUM_PARALLEL:1`. When the model first loads, the lifted command line also appears: `llama-server.exe --model …qwen2.5 blob… -c 4096 -np 1` (morning), `-c 16384 -np 4` (noon) and `-c 8192 -np 2` (the third arm, loaded 13:59:19). `-np` = the slots actually opened; that those slots were used in the run was also counted from the log (all four of the four slots, both of the two slots took work — a side output of the contamination audit below). Starting a measurement without looking at these two lines is a wrong door: the variable may be written while the server continues on the old process. Indeed the third arm's **first** run died not from that trap but from its neighbor: the setting was right, the window was contaminated, the record was discarded (below).
:::

## The Order of the Five Runs

The same script, the same request, the same protocols; the only difference is the setting the server read at startup and the number of requests released client-side. The first three ran on 2026-10-19 in three server settings, the fourth on 2026-10-20 on the default server with K = 8, the fifth on 2026-10-26 on the `=3` server.

- **The barrier.** In every wave, K threads wait at a `threading.Barrier(K)` point and are released in one shot. In the morning run the release spread was at most **0.015 s**; in the noon and third runs all 35 records, and in D all 40 records, were written as `barrier_s` = 0.00 (the record rounds to four decimals, so the spread is under 0.00005 s). The "at the same time" claim rests on the measured spread, not a clock reading.
- **The request.** `qwen2.5:3b-instruct-q4_K_M`, `/api/chat`, `http://127.0.0.1:11434`, `temperature: 0.0`, `num_predict: 64`, `keep_alive: "10m"`.
- **Identical generation.** In **all 180 measurement requests of the five runs**, `eval_count` = 64 and `done_reason` = `length`; the prompt token count was fixed at 74. So the wave times aren't an average of different token counts, but a repeat-count difference of the same job.
- **Warming is separate.** One request is sent before each run. Morning: wall 12.36 s, loading 5.64 s. Noon: wall 34.09 s, loading **27.82 s** — the price of setting up four slots at once. Third arm: wall 23.83 s, loading **17.48 s** — two slots, a middle price. D: wall **27.906 s**, loading **21.2176 s** — the model hadn't been used for a day, the weights weren't warm; that price was paid in the off-measurement warm-up. E: the server had just been restarted, `/api/ps` was empty; the model loaded in warm-up and the first measurement record's `load_s` came out 0.0092. The model was never re-dropped in any of the measurement arms: the biggest `load_duration` of the morning's 35 records was 0.022 s, noon's 0.023 s, the third arm's 0.052 s, D's 0.0639 s, E's 0.0092 s.
- **3 s between waves, 5 repeats per arm.** In the first three runs the arms ran in the order `1, 2, 4`, and D ran as a single arm with K = 8; `/api/ps` was read at the head of every arm.
- **`num_thread` wasn't sent.** The record's `options` field carries three settings (temperature, `num_predict`, `keep_alive`); the thread count stayed at the server default. Since the first three runs' three arms each and D's single arm ran under the same default internally, the **between-arms** comparison is valid — but the absolute tok/s depends on this machine's default, and pinning `num_thread` and re-running would be a separate arm (not measured).

:::note[Credentials: four runs, one machine]
The script: `ornekler/eszamanli-olcu/eszamanli_olcu.py`. The summarizer: `ornekler/eszamanli-olcu/ozetle.py` (recomputes from the same log, the staircase table included; runs its tests with `--test` without touching Ollama).
**Run A — the default server:** `cikti/eszamanli-log-1.txt`, the window **10:54:14 → 10:58:00**, the measured wave times totaling **168.37 s**, 35 measurement requests + 1 warm-up, 0 errors.
**Run B — `OLLAMA_NUM_PARALLEL = 4`:** `cikti/eszamanli-log-2.txt`, the window **12:19:56 → 12:23:27**, the measured wave times totaling **131.78 s**, 35 measurement requests + 1 warm-up, 0 errors. Before this run a short smoke run was made (`cikti/duman-log-2.txt`, 3 requests, 15.19 s) and the numbers below are **from the full run**.
**Run C — `OLLAMA_NUM_PARALLEL = 2`:** `cikti/eszamanli-log-3.txt`, the window **14:07:35 → 14:11:07**, the measured wave times totaling **141.88 s**, 35 measurement requests + 1 warm-up, 0 errors; the smoke run `cikti/duman-log-3.txt` (3 requests, the measured wave 15.28 s). All the C numbers below are from this full run.
**Run D — the default server, K = 8:** `cikti/eszamanli-log-5.txt`, the window **10:43:35 → 10:47:30** (2026-10-20), the measured wave times totaling **191.3 s**, 40 measurement requests + 1 warm-up, 0 errors; the smoke run `cikti/duman-log-4.txt` (8 requests, the measured wave 38.078 s). All the D numbers below are from the full run. The server hadn't been restarted since the `server config` line of 2026-10-19T14:39:48; D also ran in that same process, with `:1` and `-c 4096 -np 1`.
**Run E — `OLLAMA_NUM_PARALLEL = 3` (`-np 3 -c 12288`):** `cikti/eszamanli-log-4.txt`, the window **00:29:18 → 00:32:39** (2026-10-26), the measured wave times totaling **140.5 s**, 35 measurement requests + 1 warm-up, 0 errors. All the E numbers below are from the full run. The server's `server config` line at 22:13:22 read `OLLAMA_NUM_PARALLEL:3`; the model load `llama-server … -c 12288 -np 3` — the [Scope Map](/en/kaynaklar/kapsam-haritasi/)'s pre-registered `-c 12288` expectation was written before the measurement and held. The contamination audit found 37 new-prompt lines (36 × 74 + 1 × 32), foreign lines 0. The audit's side output, the slot count: `id 0: 22, id 1: 10, id 2: 5` — all three slots took work (the same method as A-D's counts).
In A-D: Ollama **0.40.6**, Python 3.12.10, Windows 11, AMD Ryzen 5 2600 (6 cores/12 threads), 15.9 GB RAM; in the `/api/ps` record `size_vram` was **0** — the model ran on CPU. The log carries the server's own reading: `inference compute id=cpu … available="3.2 GiB"`; Vulkan device discovery crashes on this machine (`llama-server --list-devices failed: exit status 0xc0000005`), so any GPU fallback was eliminated by measurement. **In E the version credentials differ:** the server had been updated in between, and E ran on **0.40.11**; in the same log GPU discovery crashed with the same error in all three libraries (vulkan, cuda, rocm) and `inference compute` again read `id=cpu` — so E also ran on CPU on this machine, but not on the same version as A-D.
**The conditions aren't identical — this is the page's most important caution.** A ran at 10:54 in the morning, B at 12:19 noon, C at 14:07 (all 2026-10-19); D ran a day later, on 2026-10-20 at 10:43, and made a cold start with a 21.2 s loading warm-up. A, B and C ran in three separate server processes, while D ran in the default process, not restarted since the `server config` line of 2026-10-19T14:39:48; the background workload and memory state can change in that interval. The log writes `free="3.8 GiB"` at A's first load and `available="3.2 GiB"` at B's server startup. That's why the **absolute** numbers (5.91 vs 5.51 vs 5.66 s) are numbers that can't be separated into clock difference vs setting difference; the page holds this comparison strictly at the **pattern** level: a staircase exists / pairwise couples exist / no staircase. The D-vs-A comparison is also at pattern level: the same staircase, the same ~4.6 s step, the same ~14 tok/s request speed; as K went from 4 to 8, the wave grew 2.08x. The most robust number-level differences come from the patterns themselves: the worst user time (18.50 → 14.47 → 13.77 s) and the wait component (14.11 → 3.60 → 0.12 s). **E adds one more threshold to all this:** a week later, on the updated server (0.40.11), it ran in a third new server process — comparing E's numbers with A-D's is valid only at pattern level; the version difference is also on the table.
**The contamination audit ran in all four windows** (the recipe below): A's and B's windows had 37 new-prompt lines, the distribution exactly the same — 36 lines of 74 tokens (warm-up + 35 measurement requests), 1 line of 32 tokens (the script's own eviction call). D's window had 42 lines: 41 lines of 74 tokens (warm-up + 40 measurement requests), 1 line of 32 tokens; all on `id 0`. C's **first** run was eliminated in the same audit: 89 foreign lines entered the window; the record sits as `cikti/kirli-eszamanli-log-3.txt` but none of its numbers are published. In the published C run the distribution was again 36 + 1.
:::

## The Result Tables

**Run A — the default server (`-np 1`):**

| Arm | Waves | Recorded/expected | Failed | p50 wall (s) | p95 wall (s) | Longest wave (s) | Average wave (s) | System tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5.91 | 6.45 | 6.45 | 6.03 | 10.62 |
| K=2 | 5 | 10/10 | 0 | 4.76 | 9.34 | 9.34 | 9.21 | 13.89 |
| K=4 | 5 | 20/20 | 0 | 9.48 | 18.50 | 18.75 | 18.43 | 13.89 |

The ratios from the same log: **a K=2 wave takes 1.53x K=1, a K=4 wave 3.06x.**

**Run B — `OLLAMA_NUM_PARALLEL = 4` (`-np 4 -c 16384`):**

| Arm | Waves | Recorded/expected | Failed | p50 wall (s) | p95 wall (s) | Longest wave (s) | Average wave (s) | System tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5.51 | 5.58 | 5.58 | 5.49 | 11.66 |
| K=2 | 5 | 10/10 | 0 | 8.14 | 8.62 | 8.62 | 8.16 | 15.68 |
| K=4 | 5 | 20/20 | 0 | 12.47 | 13.77 | 13.77 | 12.71 | 20.15 |

The ratios: **the K=2 wave is 1.49x K=1, the K=4 wave 2.32x.** In A and B there were no errors, no missing waves, no record outside HTTP 200.

**Run C — `OLLAMA_NUM_PARALLEL = 2` (`-np 2 -c 8192`):**

| Arm | Waves | Recorded/expected | Failed | p50 wall (s) | p95 wall (s) | Longest wave (s) | Average wave (s) | System tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5.66 | 5.81 | 5.81 | 5.69 | 11.24 |
| K=2 | 5 | 10/10 | 0 | 8.23 | 8.97 | 8.97 | 8.42 | 15.21 |
| K=4 | 5 | 20/20 | 0 | 7.26 | 14.47 | 14.47 | 14.27 | 17.95 |

The ratios: **the K=2 wave is 1.48x K=1, the K=4 wave 2.51x**; the third arm also had 0 errors, 0 missing waves. Don't be misled by the **p50 of 7.26 s** in the K=4 row, and don't call it a gain: 10 of the 20 records were in the fast couple, 10 in the slow couple, the median standing exactly on the boundary. The same arm's longest wave is 14.47 and its average 14.27 s. Looked at over and over, all five waves had the same structure: two requests at ~7.1 s, two at ~14.2 s.

**Run D — the default server, K = 8 (`-np 1`, 2026-10-20):**

| Arm | Waves | Recorded/expected | Failed | p50 wall (s) | p95 wall (s) | Longest wave (s) | Average wave (s) | System tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=8 | 5 | 40/40 | 0 | 20.25 | 38.17 | 38.97 | 38.26 | 13.38 |

A K=8 wave takes 6.34x K=1 and 2.08x A's K=4 wave. The ratio being 6.34 rather than 8 comes from the cache component: each of K=1's requests pays its own pre-fill, while in K=8 the eight requests share one cold pre-fill and the seven others find a ready prefix (the cache table below).

**Run E — `OLLAMA_NUM_PARALLEL = 3` (`-np 3 -c 12288`, 2026-10-26):**

| Arm | Waves | Recorded/expected | Failed | p50 wall (s) | p95 wall (s) | Longest wave (s) | Average wave (s) | System tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5.36 | 5.45 | 5.45 | 5.33 | 12.0 |
| K=2 | 5 | 10/10 | 0 | 8.0 | 8.77 | 8.77 | 8.03 | 15.93 |
| K=4 | 5 | 20/20 | 0 | 10.56 | 15.05 | 15.22 | 14.73 | 17.38 |

The ratios: **the K=2 wave is 1.51x K=1, the K=4 wave 2.76x.** E had no errors, no missing waves.

What reading the four tables side by side measures: **the K=4 wave's last user drops from 18.50 → 14.47 → 13.77 s (22% from A to C, only 5% more from C to B), but the single user in the K=1 arm improves in no setting** (5.91 / 5.51 / 5.66 s — these three can't be separated from clock difference, see credentials). The crowd's order separates between the two settings by **distribution**: `=4` gives everyone 12.4-13.8 s, `=2` gives half 7.1 s and makes the other half wait 14.2 s. The system tok/s in K=4 goes 13.89 → 17.95 → 20.15. The fourth row doesn't spoil this picture: at K=8 the single-request speed is 14.15 tok/s (the same as A's K=1/K=2/K=4 arms' 14.07/14.22/14.14), the system speed 13.38 tok/s (the same magnitude as A's K=4's 13.89), and the last user 38.17 s. So as the client count grows, the queue grows, not the speed. E measured this staircase's middle: with the K=4 wave's longest at 15.22 s and the system speed at 17.38 tok/s, it sits **between `=2` and `=4`** — the expected order, claimed only at ranking level since it ran on a different version, not at absolute-number level.

## The Staircase, the Pairwise Couples and the Lock-Step: Three Settings' Three Patterns

The ratios above alone don't answer the question "is there racing"; the answer is **inside** the wave. In the K=4 arms' five waves, the four requests' own wall times (not the record order, sorted by duration):

**Run A — the default server:**

| Repeat | 1st request | 2nd | 3rd | 4th | Steps |
| --- | --- | --- | --- | --- | --- |
| 1 | 4.70 | 9.48 | 14.03 | 18.50 | 4.78 · 4.55 · 4.47 |
| 2 | 4.63 | 9.22 | 13.94 | 18.47 | 4.59 · 4.72 · 4.53 |
| 3 | 4.67 | 9.38 | 14.11 | 18.75 | 4.70 · 4.74 · 4.64 |
| 4 | 4.73 | 9.23 | 13.73 | 18.38 | 4.50 · 4.50 · 4.64 |
| 5 | 4.59 | 9.08 | 13.69 | 18.08 | 4.48 · 4.61 · 4.39 |

All five waves have the same structure: the times line up as an **equally spaced staircase**, the step between 4.39-4.78 s (the 15 steps' average 4.59 s). So the second request starts when the first ends, the third when the second ends. The same holds two-stepped in K=2 (4.55-4.77 and 9.02-9.34 s).

**Run B — `OLLAMA_NUM_PARALLEL = 4`:**

| Repeat | 1st request | 2nd | 3rd | 4th | Steps |
| --- | --- | --- | --- | --- | --- |
| 1 | 13.64 | 13.64 | 13.77 | 13.77 | 0.00 · 0.12 · 0.00 |
| 2 | 12.47 | 12.47 | 12.47 | 12.47 | 0.00 · 0.00 · 0.00 |
| 3 | 12.50 | 12.50 | 12.50 | 12.50 | 0.00 · 0.00 · 0.00 |
| 4 | 12.39 | 12.39 | 12.39 | 12.39 | 0.00 · 0.00 · 0.00 |
| 5 | 12.41 | 12.41 | 12.41 | 12.41 | 0.00 · 0.00 · 0.00 |

No staircase: 14 of the 15 steps are **0.00 s**, one is 0.12 s. The four requests start at the same time and end at the same time. The same in K=2: both requests at the same value (in the 7.94-8.62 band, exactly the same in four of the five waves). This pattern's name is **lock-step**: the four slots carry separate jobs but advance together inside a single batch on the CPU, so they finish together.

**Run C — `OLLAMA_NUM_PARALLEL = 2`:**

| Repeat | 1st request | 2nd | 3rd | 4th | Steps |
| --- | --- | --- | --- | --- | --- |
| 1 | 7.08 | 7.08 | 14.22 | 14.22 | 0.00 · 7.14 · 0.00 |
| 2 | 7.20 | 7.26 | 14.47 | 14.47 | 0.06 · 7.20 · 0.00 |
| 3 | 7.09 | 7.17 | 14.17 | 14.25 | 0.08 · 7.00 · 0.08 |
| 4 | 7.12 | 7.12 | 14.20 | 14.20 | 0.00 · 7.08 · 0.00 |
| 5 | 7.02 | 7.09 | 14.12 | 14.19 | 0.08 · 7.03 · 0.06 |

This table sits between A and B and is **neither's pure form**: 10 of the 15 steps are 0.00-0.08 s (within the couple, lock-step), 5 are 7.00-7.20 s (between couples, a staircase step). All five waves have the same structure: **pairwise couples**. So when four requests arrive at two slots, the moment the slots fill, concurrency is spent and the overflow queues. In the K=2 arm, C, like B, is lock-step: both requests finish in the same time (steps 0.00-0.08 s) — when the slot count matches the request count, the queue vanishes entirely.

**Run D — the default server, K = 8:**

| Repeat | 1st request | 2nd | 3rd | 4th | 5th | 6th | 7th | 8th |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5.83 | 10.34 | 14.95 | 19.56 | 24.16 | 28.75 | 33.56 | 38.17 |
| 2 | 5.73 | 10.17 | 14.89 | 19.42 | 23.92 | 28.52 | 33.06 | 37.89 |
| 3 | 5.89 | 10.52 | 15.44 | 20.25 | 24.83 | 29.33 | 34.00 | 38.45 |
| 4 | 5.86 | 10.41 | 15.03 | 19.59 | 24.22 | 28.73 | 33.33 | 37.81 |
| 5 | 5.72 | 10.31 | 15.00 | 19.58 | 24.14 | 29.52 | 34.33 | 38.97 |

All five waves have the **eight-step staircase**: all 35 steps are **4.44-5.38 s**, averaging **4.64 s** — the same as A's K=4 staircase's 4.59 s steps. D's first step (~5.8 s) is a bit higher than the other seven because each wave's first request finds only 28 of the 74 tokens in cache, the other seven find 73. The pattern is A's exact copy: one slot, eight requests; the last request queued until 38.97 s. At K=8 there's neither lock-step nor couples — since the server is `-np 1`, the eight clients enter a single queue.

**Run E — `OLLAMA_NUM_PARALLEL = 3`:**

| Repeat | 1st request | 2nd | 3rd | 4th | Steps |
| --- | --- | --- | --- | --- | --- |
| 1 | 10.89 | 10.89 | 10.89 | 15.22 | 0.00 · 0.00 · 4.33 |
| 2 | 10.09 | 10.09 | 10.16 | 14.48 | 0.00 · 0.06 · 4.33 |
| 3 | 9.97 | 10.09 | 10.09 | 14.52 | 0.12 · 0.00 · 4.42 |
| 4 | 10.03 | 10.14 | 10.14 | 14.38 | 0.11 · 0.00 · 4.24 |
| 5 | 10.56 | 10.67 | 10.67 | 15.05 | 0.11 · 0.00 · 4.38 |

E's K=4 arm gives not all three patterns but **the triple's and the single's mixture**, and the same in all five waves: 10 of the 15 steps are **0.00-0.12 s** (within the triple, lock-step — three slots carrying three requests together), 5 are **4.24-4.42 s** (average 4.34 — the fourth request's single staircase step). In the four-slot B, four requests finished together at 12.4-13.8 s; in the three-slot E, three requests finish at ~10.1 s and the fourth at ~14.5-15.2 s — as the work per slot drops, the shared wave shortens, and the overflowing request builds the staircase's last step. In the K=2 arm, E gives full lock-step (the step 0.00 in all five waves; the walls in the 7.66-8.77 s band): two slots, two requests — no queue.

The second measurement separates the patterns — a single request's **own decode speed** (`eval_count / eval_duration`, the median of the five records):

| | K=1 | K=2 | K=4 | The 35 records' band |
| --- | --- | --- | --- | --- |
| Run A (default) | 14.07 | 14.22 | 14.14 | 12.73-14.81 tok/s |
| Run B (`-np 4`) | 14.97 | 9.54 | 6.38 | 4.74-15.01 tok/s |
| Run C (`-np 2`) | 14.38 | 9.13 | 9.22 | 7.87-14.65 tok/s |
| Run E (`-np 3`) | 15.43 | 9.51 | 7.23 | 6.12-15.39 tok/s |

In A the per-request speed is constant and the total wall multiplies with K: a sequential queue. In B the speed drops with K and the total wall stays constant: the work is genuinely shared. In perfect parallelism four requests would finish in nearly the same time as one (≈5.5 s) and the per-request speed would stay at 15 tok/s. Measured: the wave is 12.71 s (2.32x K=1) and per-request 6.38 tok/s (about 43% of 14.97). The gain is 4 / 2.32 = **1.73x** — that's `ozetle.py`'s "system throughput is 1.73x K=1" line; four slots don't give four-times speed, they give 1.73x, because there's a single sharing CPU.

C's row is this page's least-anticipated finding: **the K=2 and K=4 speeds are the same** (9.13 and 9.22 tok/s). The reason is in the pattern: as long as the two slots stay full, there are always **two** jobs in the batch; when the fourth request arrives the batch doesn't grow, the queue grows. So if more requests arrive than slots, the per-request speed keeps staying as if there were **as much work as the slot count** — what drops isn't the speed, but the next request's waiting (a median of 3.60 s, the wait table below). The system speed is 17.95 tok/s for the same reason: 89% of B's 20.15, but with two slots instead of four and 300 MB less memory.

D adds no fourth row to this speed table (the K=1/2/4 arms weren't run); a single number suffices: at K=8 the per-request speed median is **14.15 tok/s** (the 40 records' band 12.18-14.69), the same as A's three arms' 14.07/14.22/14.14. The system speed is 13.38 tok/s — saying that as the client count grows from 4 to 8, total throughput doesn't grow, only the queue lengthens.

E's K=4 row sits numerically between B and C (7.23; B 6.38, C 9.22) but the band **carries two populations**: 6.12-15.39. The five waves' triples run at the shared speed (~6.8-7.3 tok/s — 15 records, which is why the median is also 7.23), while the fourth request, running **alone** after the triple, decodes at its own full speed (~15.4 tok/s — 5 records). So with four requests on three slots: both speed and queue split in two; if the median is read alone, the fourth request being twice as fast isn't visible. The K=1 cell (15.43) sits a bit above A-D's 14.07-14.97 band — one request, one slot, the different version's difference resting in the band without breaking the pattern.

:::tip[The single column separating the patterns]
Wave time growing + single-request speed **constant** = no racing, a queue (Run A). Wave time growing near-flat + single-request speed **dropping** = sharing (Run B). Wave time growing + speed **dropping but staying equal to K=2 at K=4**, with the staircase giving **pairwise couples** = sharing up to the slot count, queuing beyond (Run C). These three signatures are independent of cache state; that's the way to tell them apart without falling into the "the multiple that seems like a gain" trap below. The fourth run (K=8, default) produced no new signature: while the wave stretched 18.43 → 38.26 s, the single-request speed stayed at 14.14 → 14.15 tok/s — A's "there's a queue, no race" signature, longer. The fifth run (`=3`) added a fourth signature: **a triple lock-step + a single straggler** — inside the wave the first three requests finish together (steps 0.00-0.12 s), the fourth arrives in a single step (4.24-4.42 s); the gap between the slot count and the request count reduces to a single staircase step.
:::

## The Waiting Time: Subtracted from the Measured Total

For every record I took the gap `wall − (load + prefill + decode)`. This is **arithmetic**, not a new measurement; but all three of its inputs are measured fields from the server. The command sits in `ornekler/eszamanli-olcu/README.md`, i.e. it's reproducible from the four runs' logs.

**Run A — the default server:**

| Arm | Least waiting | Median | Most waiting | Records over 0.5 s |
| --- | --- | --- | --- | --- |
| K=1 | 0.006 s | 0.014 s | 0.017 s | 0 / 5 |
| K=2 | −0.000 s | 2.270 s | 4.766 s | 5 / 10 |
| K=4 | 0.009 s | 6.891 s | **14.110 s** | 15 / 20 |

At K=1 the gap goes to zero (the measurement overhead), at K=4 the last request **queues** for 14.11 s. 20 of the 35 records wait over 0.5 s — which is exactly the count of K=2's five second requests plus K=4's fifteen queued requests. In user language: if four people ask at once, the last gets their answer at **worst in 18.75 s** (p95 18.50); for someone asking alone the worst time is 6.45 s. So queuing doesn't split the latency: every new user waits for the entirety of those before them.

**Run B — `OLLAMA_NUM_PARALLEL = 4`:**

| Arm | Least waiting | Median | Most waiting | Records over 0.5 s |
| --- | --- | --- | --- | --- |
| K=1 | −0.002 s | 0.019 s | 0.022 s | 0 / 5 |
| K=2 | 0.008 s | 0.013 s | 0.023 s | 0 / 10 |
| K=4 | 0.009 s | 0.021 s | **0.122 s** | 0 / 20 |

The queue vanishes entirely: in **none** of the 35 records does the wait exceed 0.5 s, the worst wait 0.122 s. But the price moves elsewhere — at K=4 every request lives the 12.4 s wave start to finish, whereas in A the first request finished in 4.7 s. So: **in A the first person is fast, the last slow; in B everyone is equal and the middle person is slower than A's.** K=2's first request finishes in 4.55-4.77 s in A, in 7.94-8.62 s in B.

**Run C — `OLLAMA_NUM_PARALLEL = 2`:**

| Arm | Least waiting | Median | Most waiting | Records over 0.5 s |
| --- | --- | --- | --- | --- |
| K=1 | 0.004 s | 0.006 s | 0.021 s | 0 / 5 |
| K=2 | −0.000 s | 0.008 s | 0.089 s | 0 / 10 |
| K=4 | 0.008 s | **3.598 s** | **7.236 s** | 10 / 20 |

This table says numerically that C is "half queued": in the K=2 arm there's no queue (worst 0.089 s), while in the K=4 arm **exactly half** of the 20 records goes over 0.5 s and the longest wait is 7.24 s — which is the between-couples step of the staircase table itself (7.00-7.20 s). The two measurements say the same thing from two places: when the fast couple finishes, the slot empties, and the next couple starts at that moment. The median of 3.60 s is the expected place for the 20 records sitting on the boundary.

**Run D — the default server, K = 8:**

| Arm | Least waiting | Median | Most waiting | Records over 0.5 s |
| --- | --- | --- | --- | --- |
| K=8 | 0.001 s | 17.405 s | **34.291 s** | 35 / 40 |

In 35 of the 40 records the wait is over 0.5 s; the five under it are each wave's first request, with walls of ~5.7-5.9 s. The longest-waiting request is 34.29 s — the 38.97 s last request itself. At K=4 this cell was 6.891 / 14.110 s; as K went from 4 to 8, the median wait grew 2.53x and the worst wait 2.43x. When eight people ask at once, the answers arrive in sequence across a 5.7-39.0 s range; the first person finishes in the same time as someone asking alone, the last waits for seven.

**Run E — `OLLAMA_NUM_PARALLEL = 3`:**

| Arm | Least waiting | Median | Most waiting | Records over 0.5 s |
| --- | --- | --- | --- | --- |
| K=1 | 0.007 s | 0.010 s | 0.023 s | 0 / 5 |
| K=2 | 0.005 s | 0.010 s | 0.014 s | 0 / 10 |
| K=4 | 0.012 s | 0.087 s | **10.883 s** | 5 / 20 |

E's waiting tells the staircase's same story from two places: of K=4's 20 records exactly **5** wait — the five waves' fourth request (median 0.087 s, the triple doesn't wait; worst 10.88 s, the staircase's 4.34 s step + the shared wave). In C this cell was 10/20 (two slots, two couples), in B 0/20 (four slots, no queue); since three slots absorb three of four requests, E sits exactly in the middle. In K=2 the queue vanished entirely — the same signature as B's K=2.

:::note[Where you see a minus, it's the measurement overhead]
A's K=2 row has −0.000, B's K=1 row −0.002, C's K=2 row −0.000 s: the phase sums exceed the wall time by a tiny margin, because the fields come from the server's and the script's different clock readings. "Negative waiting" isn't a real thing; this cell shows that overhead's size.
:::

## The Multiples That Seem Like Gains: Separating the Cache from Parallelism

In A's table the `system tok/s` is 10.62 at K=1 and 13.89 at K=2 and K=4: the summary output prints this as "K=2 is 1.31x K=1's throughput". **That number isn't a gain, it's a confusion**, and it sits here so it isn't carried around on this page.

The cause is measured in the record: the pre-fill itself. The script fires the K requests in a wave with **identical** text (the subject number comes from the repeat number); when the same prompt goes repeatedly, the prefix cache finds ready pieces.

| Run | Arm | Total prompt tokens | From cache | Cache per request | `prompt_eval_duration` median |
| --- | --- | --- | --- | --- | --- |
| A (default) | K=1 | 370 | 140 | 28 / 74 | 1.335 s |
| A | K=2 | 740 | 730 | 73 / 74 | 0.076 s |
| A | K=4 | 1480 | 1460 | 73 / 74 | 0.073 s |
| B (`-np 4`) | K=1 | 370 | 140 | 28 / 74 | 1.159 s |
| B | K=2 | 740 | 477 | 0-73 / 74 | 1.241 s |
| B | K=4 | 1480 | 954 | 0-73 / 74 | 2.378 s |
| C (`-np 2`) | K=1 | 370 | 140 | 28 / 74 | 1.263 s |
| C | K=2 | 740 | 477 | 0-73 / 74 | 1.302 s |
| C | K=4 | 1480 | 1460 | 73 / 74 | 0.114 s |
| E (`-np 3`) | K=1 | 370 | 140 | 28 / 74 | 1.118 s |
| E | K=2 | 740 | 477 | 0-73 / 74 | 1.245 s |
| E | K=4 | 1480 | 1207 | 0-73 / 74 | 0.650 s |
| D (default, K=8) | K=8 | 2960 | 2695 | 28 or 73 / 74 | 0.074 s |

In A the K=1 arm arrives with a different prefix on every repeat (`[subject 1]`, `[subject 2]`...), so the cache covers only 28 of the 74 tokens and every request carries ~1.3 s of genuine pre-fill. In the K=2 and K=4 arms there's a single slot, so the same text passes through the same slot repeatedly: 73 of 74 ready. A's "1.31x" is exactly that ~1.3 s expense not being paid in the other arms — the decode speed staying the same across the three arms (14.07/14.22/14.14) says nothing else won.

In B the table turns over: **four slots mean four caches.** As the requests spread across slots, some fall on a cold slot (cache per request between 0 and 73), and the K=4 arm pays 2.38 s per request in pre-fill. So B's +45% system speed is a speed won **despite** the cache, not because of it. Putting A's and B's "multiple" numbers in the same sentence is therefore wrong: A's multiple comes from the cache, B's (1.73) from the slots.

C pays the same cache cell as A: in the K=4 arm **all 20 of the 20 records** found 73 of 74 tokens ready, the pre-fill median 0.114 s. So C's "system throughput is 1.60x K=1" line isn't the same kind as B's 1.73 — part of it is A's cache gift. **The causality between slot count and cache hit wasn't separated here (not measured); the two visible facts: on two slots every request lands on a warm slot, on four it doesn't.** The number telling C's slot-gain alone isn't the cache cell, but the 9.13 → 9.22 tok/s speed staying equal to K=4 at K=2 and the wait median rising to 3.60 s.

D's row is this trap's biggest form: of the 2,960 prompt tokens in 40 requests, 2,695 came from cache; 28 per request (each wave's first request) or 73 (the remaining seven). Yet K=8's system speed is 13.38 tok/s — **not higher** than A's 13.89. Doubling the client count doesn't produce system throughput on a single-slot server; there's no "gain multiple" to write for K=8, because the single slot doesn't share the work, it does it in sequence.

E carries B's cache pattern: at K=2 and K=4 the cache per request is **0-73/74** — as the slots distribute the requests, cold slots catch some; although 1,207 of E's K=4's 1,480 prompt tokens came from cache, 273 paid genuine pre-fill (median 0.650 s). So E's "system throughput is 1.45x K=1" number is also won **despite the cache**, like B's 1.73 — unlike the two-slot C's 1.60, not a warm-slot gift. The number telling E's slot-gain is again speed and waiting: 7.23 tok/s of sharing speed at K=4 with a single 4.34 s staircase step.

:::caution[The requests within a wave don't have to be identical]
Sending the same question to K people at once is a real scenario (retries, majority sampling, the echo of a hot question). But real multi-user traffic arrives with prompts different from each other; there the cache won't be this generous, i.e. the wall gap between K=1 and K=4 in A would come out **smaller** than this run. The three patterns this page measured — the sequential staircase, racing while sharing and the pairwise lock — are findings independent of the cache; the 1.31 and 1.60x numbers aren't.
:::

## The Memory Side: What Four Slots Cost

The `/api/ps` read at the head of every arm:

| | Model copy | Context | `size` | `size_vram` |
| --- | --- | --- | --- | --- |
| Run A (`-np 1`) | 1 | `-c 4096` | 2,168,371,280 bytes (the same in all three arms) | 0 |
| Run D (`-np 1`, K = 8) | 1 | `-c 4096` | 2,168,371,280 bytes | 0 |
| Run C (`-np 2`) | 1 | `-c 8192` | 2,412,794,346 bytes (the same in all three arms) | 0 |
| Run E (`-np 3`) | 1 | `-c 12288` | 2,564,753,979 bytes (the same in all three arms) | 0 |
| Run B (`-np 4`) | 1 | `-c 16384` | 2,716,000,582 bytes (the same in all three arms) | 0 |

In none of the five is there a second model copy — all eight of the eight requests share the same weights. D's row isn't a new memory point but a repeat of the same setting: the model copy, the context and the byte count are exactly the same as A's. E's row filled the staircase's missing step: memory depends on the slot count, not the concurrent client count — as the client count grew from 4 to 8, `/api/ps` didn't change by a single byte. The four points now answer the **linearity question**: the 1→2 slot transition is **+244,423,066 bytes ≈ +233 MiB**, the 2→3 transition **+151,959,633 bytes ≈ +145 MiB**, the 3→4 transition **+151,246,603 bytes ≈ +144 MiB** — i.e. the first extra slot opens about **1.6x** the room of the next three, and the next three are very close to each other. E's gap from its two neighbors also carries the version gap (A-D 0.40.6, E 0.40.11): the size reading was assumed constant across versions, a single observation. The three measurements' total for 1→4 is +522 MiB. Every setting sets up 4096 tokens of context per slot (`-c 4096 / 8192 / 12288 / 16384`), i.e. the comparison is equalized per context — the context isn't **split** across slots, it's summed. (Run B's loading price is the same reason: 27.82 s; C 17.48 s; A 5.64 s.)

How much of the increase is the KV cache, how much a per-slot compute buffer, and how much structures opened **once** when moving to multiple slots, the log doesn't write separately — that **split wasn't measured**. The first extra slot being more expensive brings that third possibility to mind, but a cause isn't picked from three points; the page carries only the claim that "it doesn't go in equal steps". The practical result: on this 15.9 GB machine the B server read `available="3.2 GiB"` at startup and the model took 2.5 GiB; enough models or long contexts to fill four slots multiply the same bill. The [VRAM Math](/en/donanim/vram-hesabi/) page explains that the item growing with the concurrent request count is the KV cache; that growth's **CPU counterpart** is now measured — and the measured counterpart isn't a fixed unit price.

## What It Means in Practice

- **Opening two tabs doesn't speed the server up with the default setting.** The second request seeing its first byte depends on the first finishing. No difference for a single user; a wait added for the second. At the `=2` setting, though, two tabs really do run side by side (C's K=2 arm, worst wait 0.089 s).
- **If eight people ask at once, the default setting queues all eight.** In the K=8 wave the answers arrived across a 5.7-39.0 s range; the system speed stayed at 13.38 tok/s — not higher than K=4's 13.89. The single slot isn't divided among eight clients, it only works in sequence.
- **`OLLAMA_NUM_PARALLEL = 4` removes the crowd's queue, doesn't raise one person's speed.** Nothing measured in the K=1 arm improved (5.91 → 5.51 s; this gap could be a clock difference, see credentials). The gain is in the crowd: the last user's worst time 18.50 → 13.77 s, the system speed 13.89 → 20.15 tok/s. The price: +522 MiB of memory, a 27.8 s first load, and **the middle user slowing down** (K=2's first request rises from 4.6 s to 8.1 s).
- **If more requests arrive than slots, the queue grows, not the speed — the measurement of four requests on `=2` and above.** Four requests to two slots: the speed stays constant at 9.13 → 9.22 tok/s (always two jobs in the batch), the first couple finishing at 7.1 s, the second at 14.2 s. Four requests to four slots: the speed drops to 6.38 tok/s, everyone finishing in 12.4-13.8 s. **The worst user's time differs by only 0.7 s between the two settings** (14.47 vs 13.77), but the distribution differs: `=2` answers half of them about twice as fast as `=4`, and makes the other half wait.
- **A waiting queue or equal latency — that's a product decision.** If it's a one-person chat app, the sequential queue feels better: the first answer comes earlier. If there's a crowd or bulk jobs (summarization, data cleaning), opening slots shortens the total time. The middle levels are now measured: `=2` is concurrent for two people and queues the third-fourth (memory price +233 MiB); `=3` lock-step latency for three of four people and a single ~4.3 s queue for the fourth (memory price +145 MiB more). `=4` equal for everyone but slows the middle user.
- **Writing the variable isn't enough, the server must be restarted; don't start without looking at the startup line.** This page's second and third arms ran only after seeing the `OLLAMA_NUM_PARALLEL:4` / `:2` and `llama-server … -np 4` / `-np 2` lines in `server.log`.
- **If concurrency is genuinely needed, the address isn't the CPU but the serving engine.** The [Serving APIs](/en/kullanim/sunma-api/) page's continuous-batching comparison therefore looks at the vLLM side; that table's throughput numbers are produced in the vendor's and separate hardware's context, not on this machine.

:::danger[The measured decision and the unmeasured decision aren't the same thing]
This page doesn't say "concurrency good/bad". What it says: **on this machine, on CPU, with a single model, with 64 tokens of generation, with K copies of the same text** — the default setting does a sequential queue (up to eight steps at K=8), `=2` forms pairwise couples and waits on the overflow, `=3` forms a triple lock-step and slides one over, `=4` runs simultaneously with lock-step. Which setting is better in a persistent service, with users arriving with different prompts, on long contexts, or on a GPU is **again** not data; the numbers there don't carry over from these five runs.
:::

## What Wasn't Measured on This Page

- `OLLAMA_NUM_PARALLEL` = **3**: **measured** (Run E, 2026-10-26, 0.40.11 — the tables above). The two things E kept separate: the version gap (A-D 0.40.6), and the share of the increase between the KV cache and the per-slot buffer not being separable at **any of the four points** — a cause isn't picked from four points. Every level is measurable with this run's cost (~3 min) and a restart; writing the variable and restarting the server is the machine owner's approval (rule 3).
- **K = 5, 6, 7 and K > 8**: not measured. **K = 8 was measured** (Run D, 2026-10-20, the default server): on a single slot eight clients queue; the staircase grows to eight steps, the per-request speed stays at 14.15 tok/s, the last user waits 38.17 s. That the staircase would extend with the same step at five, six and seven is an **expectation**, not a measurement; nine and above were never tried. **K > 4 on the `=2` and `=4` servers also wasn't measured:** since the slot count there is 2 or 4, whether the fifth request would queue or hit a ceiling like `OLLAMA_MAX_QUEUE` isn't known from this run.
- **The runs weren't aligned to the same hour or grid.** A at 10:54 in the morning, B at 12:19 noon, C at 14:07 (all 2026-10-19), D on 2026-10-20 at 10:43. In the first three runs the arms ran in the same `1, 2, 4` order; D was single-armed. So the within-day background load, the memory state, the between-days difference and a possible thermal difference sit **together with** the setting difference; a randomized ordered grid (A-B-A-B, the arm order shuffled) wasn't measured. The claim this page can carry is the pattern difference, not an absolute second difference (see credentials).
- `/api/embed` concurrency: the scope axis table had this endpoint too, and it wasn't **run** in any of the four runs. Only `/api/chat` was measured. (That embedding requests can leak into a measurement window, though, is proven: the eliminated C run below.)
- Real multi-user traffic arriving with different prompts (the caution above's subject) wasn't measured.
- `OLLAMA_MAX_LOADED_MODELS`, a request arriving while the model loads, cache eviction (`keep_alive` expiring) weren't measured. At K=8 the eight requests entered the same queue; the `OLLAMA_MAX_QUEUE` limit (default 512) was never approached, no ceiling behavior was seen.
- The GPU side: Vulkan discovery crashes on this machine, `size_vram` was 0 in all four runs. So "what the `=2` or `=4` setting costs on a GPU" wasn't measurable here.
- Network latency, multiple machines, a persistent service: out of scope (the [Scope Map](/en/kaynaklar/kapsam-haritasi/)).

## Run Your Own Measurement

```bash
cd ornekler/eszamanli-olcu
PYTHONUTF8=1 python -u eszamanli_olcu.py --duman > cikti/my-duman-log.txt 2>&1
PYTHONUTF8=1 python -u eszamanli_olcu.py --kollar 1,2,4 --tekrar 5 > cikti/my-log.txt 2>&1
# the overflow arm: eight requests on a single slot × 5 repeats = 40 measurement requests (~4 min)
PYTHONUTF8=1 python -u eszamanli_olcu.py --kollar 8 --tekrar 5 > cikti/my-log-8.txt 2>&1
PYTHONUTF8=1 python -u ozetle.py cikti/my-log.txt
```

The summarizer prints the arm tables plus the **staircase** block: each wave's sorted times and steps — the raw form of this page's pattern tables. The parsing, percentiles and step math are tested without touching Ollama: `PYTHONUTF8=1 python -u ozetle.py --test`.

The script doesn't try to produce through failure: if `/api/version` can't be read the exit is 2, if the warm-up request fails the exit is 3 and the measurement arms never start. Every request landing in the record has its HTTP code, `eval_count` and error field written; a record with `eval_count` 0 or not returning 200 **doesn't enter** the summary but appears as an outlier (the `failed` and `missing wave` columns). If you have a GPU, `size_vram` will come out non-zero and the table will say something else — that run doesn't replace this page, it adds a line next to it.

### Verify the server setting in the log before the run

The prerequisite of running the second and third arms is two lines. Writing the variable and restarting the server is the managing person's job (rule 3); but **whether the value was genuinely read** is told by the log, not the script. On Windows the permanent write: `setx OLLAMA_NUM_PARALLEL 4` (or `2`), then closing and reopening Ollama completely.

```powershell
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern 'OLLAMA_NUM_PARALLEL' | Select-Object -Last 1
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern '-np' | Select-Object -Last 1
```

The first line is the environment map the server read at startup (`…OLLAMA_NUM_PARALLEL:4…`), the second the real command line lifted when the model first loaded (`… -c 16384 -np 4 …`). In the third arm the same two lines were `…OLLAMA_NUM_PARALLEL:2…` (13:58:33) and `… -c 8192 -np 2 …` (13:59:19). Run D required writing no new setting: the log's last `server config` line was 2026-10-19T14:39:48 → `OLLAMA_NUM_PARALLEL:1`, and D's model load was `-c 4096 -np 1`; i.e. D was the repeat of A's default setting in the same process. The `-np` line isn't visible until the model loads, so the order: write the variable → restart → fire a single request (the script's warm-up suffices) → look at the two lines. If both show the value you expect and you ran the run with the `--server "OLLAMA_NUM_PARALLEL=4 (server.log <date and time> line; llama-server -np 4 -c 16384)"` label, the numbers in the record are that setting's measurement. If the log has rotated, the same search should be repeated in the `server-1.log`, `server-2.log` ... files: this page's morning run's `-np 1` line was found there after rotation.

### After the run: the contamination audit

If another request reaches the same Ollama instance during the run, the wave times are no longer yours. On this machine that possibility is real: in the log, **outside** the measurement windows, short prompts of 10-22 tokens appear; they're **believed** to be editor/agent tools' embedding requests — which tool sent which wasn't proven one by one, but the size distribution matches embedding calls. There's no timestamp on the llama.cpp lines alone, so the audit is done by line order: the last seen `time=` value is carried over, and since the rig's prompt is 74 tokens, every new-prompt line deviating from that size is either foreign or the script's own eviction call. The command is ready:

```powershell
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 12:19:50-12:23:35
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 10:43:30-10:47:35
```

All four published full runs gave the same signature: in A, B and C **37 new-prompt lines** (36 × 74 + 1 × 32; warm-up + 35 measurement + eviction), in D **42 lines** (41 × 74 + 1 × 32; warm-up + 40 measurement + eviction). No foreign lines. If you see a size other than 74, throw away that wave's times or re-run the window.

:::danger[This audit genuinely eliminated a run]
The sentence above, "outside the windows", was wrong once on the afternoon of 2026-10-19, because we fell **inside** one. The `=2` setting's first full run (`cikti/kirli-eszamanli-log-3.txt`, the window **14:00:46 → 14:04:15**) was eliminated despite the server setting being right: the audit found **126 new-prompt lines** — 37 belonged to the rig, **89 were foreign** (10-22 tokens). The foreigners arrived in a single wave at 14:02:15-14:02:19 and left a second model behind: `bge-m3`, 1,244,166,879 bytes, **staying in memory until 14:07:33**. So the K=4 arm ran while a 1.2 GB other model was loaded, on this machine with a single CPU; one of K2's waves also coincided with the same seconds. None of this record's numbers are on this page — no wave time, no memory, no tok/s. The eliminated run's one measurable contribution was showing that the slot count was corrupted too: the distribution came out `id 0: 111, id 1: 15`, because the foreign lines carry their own server processes' slot numbers; i.e. in a contaminated window even the "slots were genuinely used" proof becomes unreadable.
When the re-run started: the script doesn't wait on its own. First it was seen that no model remained in the `/api/ps` response (polling at 10 s intervals: a model loaded at 14:05:43 → **empty at 14:07:35**), and the rig was released at exactly that moment. The published C run's window is **14:07:35 → 14:11:07**, with an audit of 37 lines and the 36 + 1 signature. As a rule: **if another tool can send requests to the same Ollama, the measurement window runs not at a random hour but in an interval where that tool is silent** — and the only way to know that is to audit the window not before the run but immediately after it.
:::

The audit has one more free side output: the slot id distribution. In Run A all **37 lines** passed through **`id 0`** — one queue, one slot. In Run B the distribution was `id 0: 17, id 1: 10, id 2: 5, id 3: 5`; all four of the four opened slots took work. In Run C `id 0: 22, id 1: 15`; both of the two slots took work — the wait table saying the third and fourth requests queued also says the slots weren't idle. In Run D all **42 lines again through `id 0`**: even as the client count grew to eight, `-np 1` used the single slot's queue. Which slot worked in which arm wasn't parsed arm by arm (in the unmeasured list), but the proof of the "slots were genuinely used" claim is this count.

### After measuring, leave the machine as you found it

Closing the setting is also two steps: deleting the variable and restarting Ollama. **`setx` has no delete option** — `setx OLLAMA_NUM_PARALLEL /D` was tried and gave `ERROR: Invalid syntax. Value expected for '/D'`; `/D` is `reg delete`'s switch. The two correct spellings for deleting the persistent user variable:

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", $null, "User")
# or from the command line:
reg delete "HKCU\Environment" /v OLLAMA_NUM_PARALLEL /f
```

To know the deletion worked, ask back with the same tool: `reg query "HKCU\Environment" /v OLLAMA_NUM_PARALLEL` should now give `ERROR: The system was unable to find the specified registry key or value`. The closing verification is done with the server log's same two lines: in the `…OLLAMA_NUM_PARALLEL:…` field the value must be empty or 1, and at the next model load `-np 1` must be visible. The script drops the model itself (the `evict()` call, `keep_alive: 0`), but the slot count is the server's startup choice: it won't come back without deleting the variable and restarting the server. One more difference — the deletion cleans the registry and the running server, but doesn't clean the copies in the PowerShell/cmd windows **opened that morning**; if you'll continue in those windows, `Remove-Item Env:OLLAMA_NUM_PARALLEL` (PowerShell) or `set OLLAMA_NUM_PARALLEL=` (cmd) is needed.

:::note[The closing record: 2026-10-19, after three settings the machine was left as found]
When the third arm's job was done, the deletion command was run with the first spelling above and four traces were taken: (1) `reg query` **couldn't find** the key in HKCU, and it never existed in HKLM; (2) the log's last `server config` line `14:39:48` → `OLLAMA_NUM_PARALLEL:1`; (3) the next model load `14:41:25` → `-c 4096 -np 1`, i.e. the same as morning Run A's command line; (4) at that load the `/api/ps` size came out **2,168,371,280 bytes** — bit-identical to A's default size, verifying the closure's memory side too. Two honest notes: to see the `-np` line a single 1-token request was fired (not a measurement, a probe; the model dropped itself with `keep_alive: 30s`, and at 14:42:33 `/api/ps` was empty). And the `ollama app.exe` process appears to have restarted **in the same minute** as the deletion (14:39:44) — we didn't prove the cause: Windows' environment-change notification refreshing the tray, or the restart was done by hand. That's why the rule doesn't change: **it doesn't count as closed until `:1` and `-np 1` are read in the log.** The D run on October 20 didn't break this closure: no new environment variable was written, the server stayed in the same process with `:1` + `-np 1`, and the model was evicted again at the run's end (`#PS_BITIS` empty).
:::

## Related Pages

- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — a single request's phase breakdown (`load`, `prefill`, `decode`) and the main source of the tok/s numbers.
- [Reproducibility](/en/kullanim/tekrarlanabilirlik/) — the same prompt ten times: the cache behavior and the `num_predict` ceiling.
- [Inference Parameters](/en/kullanim/cikarim-parametreleri/) — the definition of the `keep_alive`, `num_predict`, `temperature` options.
- [Serving APIs](/en/kullanim/sunma-api/) — the continuous queue and multi-user throughput comparison.
- [VRAM Math](/en/donanim/vram-hesabi/) — the context of the claim that the KV cache grows with concurrency.
- [The Scope Map](/en/kaynaklar/kapsam-haritasi/) — the acceptance rules and how this measurement's axes were pinned.

## Sources and Further Reading

- [Ollama frequently asked questions](https://docs.ollama.com/faq) — the `OLLAMA_NUM_PARALLEL` default being 1, the server partitioning by memory and CPU cores; last verified 2026-10.
- [The Ollama chat API](https://docs.ollama.com/api/chat) — the `total_duration`, `prompt_eval_duration`, `eval_duration`, `prompt_eval_cached_count`, `done_reason` fields; every phase on this page came from these fields.
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — thread scaling on CPU and the prefix cache; the address of the question of why a single request's speed stays at 14 tok/s.
- [vLLM docs](https://docs.vllm.ai/) — continuous batching and the serving pattern that genuinely races concurrent requests.
