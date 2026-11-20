---
title: "The Scope Map: What We Measured in This Guide, and What We Didn't"
description: "The map showing at which evidence tier the guide stands on which axes. The measurement rigs' unit list, what the ten rigs measured, the topics deliberately left out of scope, and the accepted run rules before entering a new measurement page."
dogrulama: 2026-11-20
---

This guide has a problem, and its name isn't incompleteness: **every line looks equally certain.** The sentence "in LoRA the base model stays in memory", the sentence "pre-fill is 43.9-45.9 tok/s", and the sentence "flash attention's gain on CPU is expected to be limited" all stand in the same typeface, in the same voice. Whereas the second came from a rig and the third from an expectation.

This page is the map separating that voice. It pins three things **before** a measurement arm runs: which axis we're on, which unit we're measuring, and which rule we're following. The acceptance rules at the page's bottom came out of a decision round today; i.e. this place is both an inventory and a contract.

## The Evidence Tier: Four Steps

Every number on the site is written onto one of four steps. The step is the page's **claim strength**, not an accuracy measure.

| Tier | What it means | How it appears on the site | Example |
| --- | --- | --- | --- |
| **0 — Expectation** | No run was made, the reason is known, the guess is openly a guess. | "expected", "**not measured**" | the `OLLAMA_FLASH_ATTENTION` and `OLLAMA_KV_CACHE_TYPE` gain ([Speed and Cost](/en/kullanim/hiz-ve-maliyet/)) |
| **1 — An upstream figure** | A number given by the vendor/the doc, unverified on our machine. | "Ollama's default", "as of 2026", a last-verified date | the `OLLAMA_NUM_PARALLEL` default of 1, `OLLAMA_KEEP_ALIVE` 5 min |
| **2 — Measured, a single observation** | Genuinely ran on this machine; no repeat. | "a single observation", "measured once" | `bge-m3` cold loading 11.92 s (once, in the first round) |
| **3 — Measured and repeated** | At least two runs or multiple repeats; given as a band. | a range, "two rounds", "5 repeats" | the characters/token ratio 2.99 (the same in both rounds), decode 13.9-14.8 tok/s |

:::caution[Using tier-3 language while at tier 2]
This is the most common trap: turning a single observation into a rule. "Cold loading is 9.15 s" was a single number; the reloads on the same machine came out 3.10-3.12 s. The page thereafter says "a cold call costs a few seconds more than a warm one", not a fixed number. A page can't build a rule sentence before rising to tier 3; if it does, that sentence falls to tier 0.
:::

:::note[The tier distinction is our own writing rule]
These four steps aren't the literature's standard classification, they're this site's own habit. That's why they can't be compared with another source's "verified" label. The only comparable thing is two measurements on the same site standing side by side.
:::

## The Ten Measuring Rigs

The pages make claims, the rigs measure. There are 14 folders under `ornekler/`; the ten producing measurements and their units:

| Rig | What it measured | Units | Connects to Ollama |
| --- | --- | --- | --- |
| `cikarim-olcu` | Latency's four phases, the `num_ctx` memory steps, `num_thread`, TTFT, the name-resolution overhead | s, tok/s, tokens, GB | yes, `127.0.0.1:11434` |
| `eszamanli-olcu` | The wave times and queue staircase of 1/2/4 requests released at once with a barrier | s, p50, p95, tok/s, the waiting request count | yes |
| `tekrarlanabilirlik` | Twelve cells × ten repeats: how many different answers the same request produces | the repeat count, changed tokens | yes |
| `eminlik-olcu` | At which end and with which condition the logprob returns, the confidence-hit relation | logprob, the right/wrong count | yes |
| `enjeksiyon-deni` | Two channels × three defenses, 31 cells: did a leak happen | the leak count per cell | yes |
| `ajan-dongusu` | The agent turn, the tool-calling catalog's token expense | turns, tokens, s | yes |
| `yerel-rag` | Retrieval quality and the threshold band (Example 5) | hit@k, MRR, s | yes |
| `viki-rag` | Indexing with a live corpus and hybrid search (Example 6) | hit@k, MRR, s, rank/ms per rank | yes |
| `gomme-egitimi` | Nine real training runs on CPU, the batch ceiling | loss, hit@1, MRR, separation, s, ms | yes (for re-embedding) |
| `lisans-ve-gizlilik` | The local models' license texts and the personal-data scan | bytes, lines, the match count | yes |

The remaining four folders (`klasik-ml`, `veri-temizleme`, `turkce-asistan`, `gorsel-lora`) are project scripts; they produce, not measure. The GPU-running steps of `turkce-asistan` and `gorsel-lora` were **not run on this machine**; only the CPU-runnable parts' real outputs are on their pages.

## The Number's Source Is One Place

If two pages tell the same unit, one is wrong and both are a source. On the site every unit has a single verified address:

| Unit | The page carrying it |
| --- | --- |
| inference seconds, tok/s, GB, characters/token | [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) |
| wall per concurrent request, wave time, queue waiting | [Concurrency](/en/kullanim/eszamanlilik/) |
| the old time of sending 24 pieces in one request on `/api/embed` (October 17, 0.40.4) | [Training an Embedding Model](/en/rag/gomme-egitimi/) |
| the `/api/embed` batched-sending comparison: one request vs 24 separate requests (October 20, 0.40.6) | [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — Training an Embedding Model only links to this comparison |
| hit@k, MRR, the threshold band | [Local RAG](/en/ornekler/yerel-rag/), [Wiki RAG](/en/ornekler/viki-rag/), [Training an Embedding Model](/en/rag/gomme-egitimi/) |
| reproducibility, seed variance | [Reproducibility](/en/kullanim/tekrarlanabilirlik/) |
| logprob, confidence, calibration | [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) |
| the leak channel, defense effectiveness | [Injection Measurement](/en/ajan/enjeksiyon-olcumu/) |
| the license text, bytes/lines, personal data | [License and Model Card](/en/kullanim/lisans-ve-model-karti/) |
| "when was this claim reviewed" | [The Verification Mechanism](/en/kaynaklar/dogrulama-mekanizmasi/) |
| "which station genuinely ran on this machine, which file holds the record" | [The End-to-End Single Line](/en/ornekler/ucdan-uca/) |
| "which page's number came from which Ollama version" | this page, the **the measurement's server version** heading |

:::tip[If you saw a number elsewhere]
If a page doesn't link to one of the addresses in this table, that number is either tier 0-1 or a copy. The latter happened on this site and was fixed by measuring when the address changed: the switch from `localhost` to `127.0.0.1` dropped the indexing times on the same machine from 529.3 s to 253.0 s.
:::

## The Measurement's Server Version: the Register

Ollama's version is part of the measurement too. On this machine the measurement arms were taken in **three different server versions**, and the site's prose intertwines those three versions' names. The count below is the snapshot **before** this section was written (October 19, a single grep run): `0.40.4` passed sixteen, `0.40.5` three, `0.40.6` fourteen times. **This table counted itself too:** the same scan, after the section was written, gave 29 passes for `0.40.4`, 6 for `0.40.5`, 18 for `0.40.6` — the whole increase is this register's own lines. A table comparing numbers is written into the set it compares; this is the second example of the [License and Model Card](/en/kullanim/lisans-ve-model-karti/) page's "the audit's result entered the audited set" flaw.

**And the third measurement also surfaced the pattern's own flaw.** After the afternoon arms' acceptance criteria and credential fix were written, the same scan ran again (23:07): the escaped pattern gives 31 passes for `0.40.4`, 7 for `0.40.5`, 20 for `0.40.6`; the **fixed-string pattern** (`grep -F`) gives 30 / 6 / 20. The gap's source is one line — beneath this section itself, the three versions' **comma-written** forms (`0,40,4`, `0,40,5`) match, mistaking the escaped dot for a wildcard. For today, the difference is this much; **whether the noon 29/6/18 count was also inflated isn't recorded** — the order of that scan's writing and this comma sentence's writing wasn't kept in a log, so the old numbers stand as they are and "Corrected" isn't said. This sentence itself was written into the same scan: the 31/7/20 above is now **one snapshot earlier**; the only current thing is the command itself. Two faces of the same flaw as the "the pattern was the dot form" confession above: a pattern both fails to find and fabricates.

**But these numbers aren't version credentials, they're a word count:** nearly all of the fourteen passes of `0.40.6` aren't a measurement but a **confession** ("the machine moved to 0.40.6 on October 19; the numbers on this page weren't re-measured on that version"); the single exception is the [Concurrency](/en/kullanim/eszamanlilik/) page's own credentials, which already stand as the 0.40.6 row in the table below. The register below is the only place separating those two — which page's number came from which server's version:

| The page carrying the measurement | The measurement's version | The run window and record |
| --- | --- | --- |
| [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) | 0.40.4 (body) / **0.40.6** (the "Batched embedding" section) | October 16 01:21-01:39, `hiz-log-127.txt`; October 20 11:45-11:46, `gomme-egitimi/cikti/kol-e.txt` |
| [Agent Measurement](/en/ajan/ajan-olcumu/) | 0.40.4 | October 16 02:11-02:18, `ajan-log.txt` |
| [Example 7: The Agent Loop](/en/ornekler/ajan-dongusu/) | 0.40.4 | the same record's second page |
| [Injection Measurement](/en/ajan/enjeksiyon-olcumu/) | 0.40.4 | October 16 11:36:32-12:12:48, `enjeksiyon-log.txt` |
| [Example 8: Prompt Injection](/en/ornekler/enjeksiyon-deni/) | 0.40.4 | the same record's second page |
| [Example 5: Local RAG](/en/ornekler/yerel-rag/) | 0.40.4 | October 16, `calistirma-log-127.txt` |
| [Example 6: Wiki RAG](/en/ornekler/viki-rag/) | 0.40.4 | October 16, `calistirma-log-127.txt` |
| [RAG Evaluation](/en/rag/rag-degerlendirme/) | 0.40.4 | October 15, `olc-log.txt` (the `localhost` era) |
| [Reproducibility](/en/kullanim/tekrarlanabilirlik/) | 0.40.4 | October 17 11:04:59-11:14:18, 123 requests |
| [Inference Parameters](/en/kullanim/cikarim-parametreleri/) | 0.40.4 | **a carried credential:** the ceiling behavior read from arm K0, i.e. from the record above |
| [License and Model Card](/en/kullanim/lisans-ve-model-karti/) | 0.40.4 | October 17 14:21:44-14:22:38 |
| [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) | **0.40.5** | October 17 22:09:25-23:13:16, four separate records |
| [Concurrency](/en/kullanim/eszamanlilik/) | **0.40.6** (runs A-D) / **0.40.11** (run E, `=3`) | October 19, three server settings; October 20 K = 8; October 26 00:29-00:32, `eszamanli-log-4.txt` |
| [Training an Embedding Model](/en/rag/gomme-egitimi/) | 0.40.4 (A-D) | the version **was written to the rig's README, not the record** (`ornekler/gomme-egitimi/README.md`, the machine line); `kol-a.txt` starts on October 17 15:46:48 but there's no credential line in the log — the script wasn't producing one. The E arm on October 20 wrote the line `Ollama version: 0.40.6` at `kol-e.txt`'s head |

Three things that must be said about the register itself:

- **The version isn't a metric, it's provenance.** This is the only answer to the question "which server did this page's number come from"; but the primary record is still each page's own credential sentence. If a page re-runs, that sentence changes first, then this table — when the two diverge, **this table is the wrong one**, because the table is a summary.
- **The register's rows aren't measurements; they're a scan result.** The 14 rows were listed on October 19 with a single grep run on disk (tier 2 — a single measurement). The same scan's previous state was wrong: when both the disk path (`ornekler/name`) and the page-link form (`/name/`) entered the pattern, `tekrarlanabilirlik` appeared on 13 pages; reducing the pattern to the disk path alone, the real count came out 2. The count pattern is the count's result.
- **The last row also corrected the scan writing this table.** In its first form the `gomme-egitimi` row was **NOT MEASURED**, with my reasoning being "the version is nowhere". It turned out wrong: the version is written in the rig's own `README.md`'s machine line. I had two reasons and both were flaws in my scan pattern: (1) the scan walked only `src/content/docs`, never looking at the `ornekler/*/README.md` files; (2) the pattern was the dot form (`0\.40\.[0-9]`), while those READMEs had written the three versions **with commas** (`0,40,4`, `0,40,5`). Five rig READMEs carry version credentials; three of them in comma form. So before ruling "not on disk", both the scan area and the form pattern should be questioned — an absence of a probe isn't itself a finding, it's the scan's limit.
- **The missing credential line isn't the version itself.** `gomme_egit.py` wasn't writing the server version into the record; on October 19 an `/api/version` read was added to the script, and from now on the `Ollama version: …` line will land inside `kol-a.txt` (the code side, without a run; the proof of these three lines will be written in the next real run). A past number isn't re-verified by re-running — October 17's version stands as it is in the README.

:::note[Why the Verification Mechanism isn't in this table]
[The Verification Mechanism](/en/kaynaklar/dogrulama-mekanizmasi/) names all three versions too, but its own measurement doesn't come from Ollama (the build times and schema trials). It doesn't **measure** the version; it narrates the version's going stale.
:::

## What We Deliberately Didn't Measure

Some gaps stand not from laziness but because no decision came out. The open ones:

- **The server-side concurrency's middle level was filled; the remaining ends are open.** `OLLAMA_NUM_PARALLEL`'s **3** level ran on 2026-10-26 (the closing paragraph below). The side running the measurement can't write that variable (rule 3); on October 19 the machine owner wrote =2 and =4, and against the morning of October 26 =3, restarting the server each time. The default (=1), **=2**, **=3** and =4 ran, on the [Concurrency](/en/kullanim/eszamanlilik/) page: with the default setting four requests released at once queue, `=2` forms pairwise couples and waits on the overflow, `=3` forms a triple lock-step and slides one ~4.3 s, and at `=4` the queue vanishes but the work is shared (a single request's speed 14.97 → 6.38 tok/s). The memory price was also measured from **four points** and **doesn't go in equal steps** (the first extra slot ≈233 MiB, the next three ≈145/144 MiB). On October 20 the **K = 8** arm also ran (on the default server, `-np 1`). K = 5, 6, 7 and **K > 8** still "not measured"; so is K > the slot count on the `=2` / `=3` / `=4` servers (the overflows above 2×2=4, separately). `/api/embed` concurrency also stands as "not measured" on that page — the 24 pieces being measured in one request is a separate thing, a concurrent embedding request another. The recipe of the level runs — the owner's two steps to write, the two lines to read from the log, the runner's single command — sits in the "Seviye 3" heading in `ornekler/eszamanli-olcu/README.md`.
- **The GPU.** There's no GPU measurement at all on this machine. Research (2026-10-25, tier 1): Ollama's Windows ROCm list covers the RDNA3 generation, Polaris (RX 570, gfx803) isn't on the list; the documented path of extra GPU support is Vulkan. The local observation (2026-10-25/26, tier 2, server 0.40.10/0.40.11): the Vulkan backend is installed and active (`OLLAMA_VULKAN:true`), but `llama-server --list-devices` **crashes with 0xc0000005 in all three libraries** (vulkan, cuda, rocm) and the server starts with `inference compute id=cpu` — i.e. on this version the RX 570 can't reach the GPU; the code requiring a GPU stands with the "not run" label. The discovery crash may be a version bug: it can be retried with a single probe on later Ollama versions.
- **Batched embedding — the boundary was drawn, the comparison measured.** `/api/embed` accepts multiple inputs; 24 pieces in one request on October 17 (arm A), and the comparison of the same 24 pieces' **one request vs 24 separate requests** on October 20 (arm E). E's two arms, repeat ranges and verdict are on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page; this map doesn't repeat those seconds. Still unmeasured: a bigger batch (e.g. 125 pieces) in one request, and `/api/embed` concurrency. The old October 17 measurement isn't E's baseline: a different Ollama version, a different session, the warm state not separately recorded. The 125-piece indexing times on the RAG pages were also taken with **one request per piece** and on another corpus; none of them can be put beside E to build the sentence "batching is that cheap".
- **The extra latency of structured output and tool calling.** The `format` and `tools` behavior was measured, their **cost** wasn't.
- **Non-Windows systems.** The per-request 2.03 s name-resolution overhead is a Windows observation; the Linux/macOS repeat isn't on the site.
- **Reader behavior.** That the staleness banner rendered was measured; that it makes the reader more careful wasn't.
- **The rig credential gap was closed and seen for the first time; the old record stands as it is.** `gomme-egitimi`'s `/api/embed` arm fires requests at Ollama but wasn't writing the version into the record; the "the missing credential line" item above explains the `/api/version` read added to the script and why it **doesn't** apply backwards. In the October 20 E run the credential line was genuinely printed: at `kol-e.txt`'s head stands `Ollama version: 0.40.6`. The A-D logs stayed credential-less; their versions in the rig README's machine line.

## Out of Scope: This Guide Will Never Write It

"Training a model from scratch" is a scope promise, not a "everything" promise. The areas this guide deliberately didn't enter:

| Topic | Why it's outside |
| --- | --- |
| Multi-tenant production infrastructure (Kubernetes, autoscaling, queue management) | The site describes one machine; these subjects remain unanswered without that machine's numbers |
| Benchmark rankings / leaderboard scores | Saying "the fastest model" isn't this page's claim; giving a ranking instead of showing the phases' order is buying staleness |
| Live price tracking | Cloud hourly rates change; if there's a price on the site it stands with "as of 2026" + a last-verified date |
| Audio and video model training | Only text (and image diffusion LoRA) |
| The RLHF/DAPO production line, distributed training | Explaining with examples a path unrunnable on a GPU-less machine would produce tier-0 text |
| The security red-team process, a red-team report | The injection section is defense education; not a product's attack testing |
| A code assistant / product integrations | Product engineering, not model training |

:::caution[Leaving out and "not measured" are different things]
"Not measured" = the door is open, it needs money and time. "Out of scope" = the door is, in our view, closed; even if opened, it wouldn't answer this site's question. If you mix the two, the map turns into a list of apologies growing every year.
:::

## A Measurement Page's Acceptance Rules

The contract accepted before entering a new rig run. These aren't changed after the page is written; if they'll be changed, they change here first.

1. **Local only.** No arm spending money runs in this project. The cloud pages stay at tier 1 (a vendor figure).
2. **The time budget.** At most 20 minutes per arm, at most 45 minutes per day, on local CPU. This ceiling exists to keep measurement hygiene: while the run is going, no other CPU job and no other Ollama request.
3. **Intervening in the server is the machine owner's.** Writing Ollama's environment variables and restarting the server is the managing person's job. The side running the measurement only runs the script and writes into the record what happened to that variable during the measurement.
4. **Smoke first, the full run after.** First one arm, one repeat: is it producing a record end to end? The full run doesn't start before the smoke passes.
5. **Numbers only from a finished log.** While the run is going, no number is reported. No half log, no empty log, no "it would probably be like this".
6. **The repeat base.** The measurement arm's repeat count is at least five; the summary is given as **p50 + p95 + total wall time**. A single number is a single observation and is tier 2.
7. **Failure isn't manufactured.** If the server returns 503, if there's memory pressure, if the arm stops midway, what happened is written as it is. Carrying the deficiency to "not measured" is better than guessing the number.
8. **The version credential.** Every new rig writes its own Ollama version at the record's head. Old pages don't change their number unless re-measured; they say on which version it was measured.
9. **The verification pattern.** When a page finishes, the order: `astro build` → `node scripts/link-check.mjs` → `npm run dogrula` → a local preview + a DOM and style probe in the browser → a clean console → the `dogrulama` stamp.
10. **The GPU/ROCm arms want separate approval.** Installing a driver means installing a system component on the machine; that's a permission asked before that arm itself.
11. **The free reading comes first.** A page not requiring measurement (a concept, scope, a decision table) is written each round before the expensive arm; so the round produces something even at no cost.

:::note[These rules' cost]
Of 1-11, the only item requiring measurement is 6: five repeats × three levels, with a 20-minute-per-arm ceiling — not a workday but a work session. The remaining ten items ask not money and time but writing discipline — which is why the most frequently violated ones are those.
:::

## The Run Axis: Concurrency

The acceptance rules' application today. Before the run it stood here so the numbers wouldn't change; on October 19 it ran in three settings, a K = 8 arm was added on October 20, and the last column shows the truth:

| Item | The pinned value | After the run |
| --- | --- | --- |
| The question | On the same machine, the same model, what happens while 1 / 2 / 4 requests **race** | answered, three times: with the default setting no racing, queuing; at the `=2` setting racing up to the slot count with the overflow queuing; at the `=4` setting racing but sharing. The additionally-run K = 8 (October 20) opened no fourth pattern on the same axis: on the default server the staircase grew to eight steps |
| The server setting | `OLLAMA_NUM_PARALLEL` = 1 (default), 2, 4 — the user writes, the user restarts the server | the default, **=2** and **=4** ran (the machine owner wrote both, rule 3 worked as written; the values are now read not from the script label but from the `server config` and `-np 2` / `-np 4` lines in `server.log`). For the K = 8 arm no variable was written, the server wasn't restarted — since the October 19 closure it ran in the same process with `:1` / `-np 1`. **=3 also ran** (2026-10-26, 0.40.11; the closing paragraph below) — all four of the four server settings are now measured |
| The model | `qwen2.5:3b-instruct-q4_K_M`, embedding `bge-m3` | the chat model ran; `bge-m3` was never tried this round — but in the third run's **eliminated** attempt that model loaded itself and broke the measurement (the failure line below) |
| The endpoint | `/api/chat` and `/api/embed`, only `http://127.0.0.1:11434` | `/api/chat` was measured, `/api/embed` **didn't run** |
| The arm | 5 repeats per level | three runs × (5 repeats × 3 arms) = **105 measurement requests**, 45 waves. The K = 8 arm separate: 5 repeats × 1 arm = 40 measurement requests (+1 warm-up) |
| The unit | wall seconds per request, `total_duration` s, tok/s, **p50 and p95**, the round's total wall s | all in the records and on the page |
| Failure | HTTP 503 / memory pressure / an empty answer → goes into the record as it is, isn't deducted from the number | zero errors: 105/105 HTTP 200, `eval_count` 64; 40/40 in the K = 8 arm. **But another failure type was found:** the server setting right, the requests errorless, and the measurement still invalid — the `=2` arm's first run was eliminated because of the 89 foreign requests entering its window, and none of its numbers were published |
| Outside | GPU, multiple machines, a persistent service, network latency | left outside |

:::caution[Confusing with the expected result]
"4 parallel requests give 4x throughput" is an **expectation** (tier 0). The rig measured all three settings: with the default setting no gain (the four requests queue, the single-request speed constant), with the `=4` setting a gain but **1.73x** — four slots don't give four-times speed, because there's a single sharing CPU. The `=2` setting opened a third door: when more requests arrive than slots, **the speed doesn't drop, the queue grows** (9.13 → 9.22 tok/s, a wait median of 3.60 s). That gap between the expected and the measured was this map's reason for writing the rig.
:::

The run's real cost also came out of the record: **168.37 s + 131.78 s + 141.88 s of measured wave time**, the run windows 3 min 46 s (10:54:14 → 10:58:00), 3 min 31 s (12:19:56 → 12:23:27) and 3 min 32 s (14:07:35 → 14:11:07). On top of the second and third runs came the machine owner's job too: writing the variable, restarting Ollama, seeing the `OLLAMA_NUM_PARALLEL:2` / `:4` and `-np 2` / `-np 4` lines in the log. A third cost emerged in the third arm: **the first attempt was discarded**, and its price is the sum of three measured intervals — the eliminated window 3'29" (14:00:46 → 14:04:15) + the probe waiting for memory to empty 1'52" (14:05:43 → 14:07:35) + the published run 3'32" = **≈9 minutes**, on top of the machine owner's second restart. The "these rules' cost" note above carried a work-session estimate; in fact the session's roughly eight minutes rose to over twelve minutes with the third level. Rule 6's (five repeats, p50 + p95) price isn't as much as we thought — the real price is closing the machine to other work for that duration; and what the third run taught is **that closing isn't enough**: a window isn't opened without making sure no other tool is sending requests to the same server.

The fourth run (K = 8, October 20) added no new owner job to this cost register: no variable was written, the server wasn't restarted, because the setting to run was already the closure's default. What it paid was its own measurement window and the contamination audit between the two windows; the times and numbers are on the [Concurrency](/en/kullanim/eszamanlilik/) page.

Rule 3's closing step was also applied on October 19: the variable was deleted from the User registry, `reg query` no longer finds the key, and the machine was left as we found it (`OLLAMA_NUM_PARALLEL` undefined, the server `:1` and `-c 4096 -np 1`). The verification was done with the log, not intuition — and there's one more observation: the tray app appears to have restarted itself in the same minute as the deletion; **its cause wasn't measured**, so no return to the rule saying "no restart needed" is made, and the closure is still counted with the log's `:1` + `-np 1` lines.

The next axis's pinned job **was written on October 19**: [The End-to-End Single Line](/en/ornekler/ucdan-uca/) — a Turkish assistant's data collection, cleaning, training, evaluation and running-in-Ollama steps walked in a single page, in a single order. Two things didn't change while the gap closed. First: that page **rewrites no number**; it carries which record it came from and at what tier, with the figure standing on the relevant page (the single-source table above took one more unit row for that reason). Second: the gap the map saw was "a step-by-step telling", not "an unwalked step" — the new page also hasn't run all five stations on this machine: station 3's **chat arm** (QLoRA) never ran because it wants a GPU, and station 5 ran not the line's own adapter but its model's ready model. The break points sit at the page's top, under the "Where It Breaks" heading.

## The Open Arms' Acceptance Criteria

The axis above shows what pinning the rules **before the run** is good for: whether the overflowing request produced speed or a queue was understood only by looking at that page's numbers. The following three items are pinned the same way — the question, the arm design, the publishing threshold, the record file's name and who the blocker is. The criterion isn't run **permission**; every item additionally awaits a "run" command.

| Item | The question (one sentence) | The arm and request load | The publishing threshold | The blocker | The record |
| --- | --- | --- | --- | --- | --- |
| **The K > 4 overflow** | If **8** requests are released at once while the slot count is 1, how does the waiting grow per wave? | `--kollar 8 --tekrar 5` = 40 measurement requests + 1 warm-up; the server is **untouched** (it runs on the `-np 1` verified at closure) | at least 38 of the 40 records HTTP 200 and `eval_count` 64; in the contamination audit **0** out-of-rig request lines (the rig's own signature: 74-token lines + a single 32-token eviction line at the end) | none — Ollama being up suffices | `eszamanli-log-5.txt` |
| **`/api/embed`'s per-request expense** | Is the gap between sending 24 pieces in one request and in 24 separate requests a per-request fixed expense? | the new arm `--kol e`: `e-batch` 1 request × 5 repeats, `e-teker` 24 requests × 5 repeats → **125 measurement requests** | both arms five repeats each; p50 + p95 + total wall. If the gap is bigger than the spread between repeats a verdict is made, otherwise **"the difference couldn't be measured"** is published — that too is a published result | **code**: a ~25-line new arm branch (the `input` list inside `ollama_embeddings` is turned into a single-addition) | `kol-e.txt` + `kol-e.json` |
| **`OLLAMA_NUM_PARALLEL=3`** | Between the two measured steps (=1→=2 ≈ +233 MiB, =2→=4 ≈ +145 MiB/slot), where does the third slot's price come from? | A/B/C's exact copy: `--kollar 1,2,4 --tekrar 5` = 35 measurement requests + 1 warm-up; the only difference the server setting, with the arm order and hour band preserved | no window opens without reading `OLLAMA_NUM_PARALLEL:3` **and** `-np 3` from the log; `/api/ps` empty; if the signature isn't 37 lines (36 × 74 tokens + 1 × 32) the run isn't published | **rule 3**: the owner's two steps (write the env + restart). The preparation block is in the rig README | `eszamanli-log-4.txt` |

**The items' status today (October 20):** two of the table's three items ran and both passed their threshold. K > 4: 40 of the 40 records HTTP 200 + `eval_count` 64, the contamination audit's signature 41 × 74 + 1 × 32, foreign lines 0, a single `/api/ps` copy; the result is on the [Concurrency](/en/kullanim/eszamanlilik/) page. The `/api/embed` comparison ran on October 20 11:45-11:46: 125 measurement requests, both arms' five repeats each, the pre-registered min-max rule; the repeat ranges didn't overlap and a verdict was made. The two arms' seconds are in the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page's "Batched embedding" section.

**The third item also closed (2026-10-26):** `=3` ran with its own threshold and passed. The machine owner wrote the env twice and restarted the server twice — in the first restart the tray process inherited the old environment and the log read `OLLAMA_NUM_PARALLEL:1`, so no window opened (the closure verification was done with the log; even if `reg query` showed 3, the run didn't start); in the second restart the startup line read `:3`. The run 00:29:18-00:32:39, 35 measurement requests + 1 warm-up, 0 errors; in the log llama-server `-c 12288 -np 3` (the pre-registered 12288 expectation held), the contamination signature 37 lines (36 × 74 + 1 × 32), foreign lines 0, the slot count `id 0: 22, id 1: 10, id 2: 5`. The numbers are on the [Concurrency](/en/kullanim/eszamanlilik/) page; during the window the server was at risk because Docker Desktop's Ollama integration loaded bge-m3 by itself — the contamination audit showed the window was quiet, but **that tool's identity became clear**: the client loading bge-m3 at every Ollama startup is `com.docker.backend.exe`. The identity of the mystery contaminator in the eliminated `=2` run's window also became clear this way.

Other things pre-pinned for the three items:

- **The unit's single address doesn't change.** The K = 8 and (when run) `=3` rows' seconds are published on [Concurrency](/en/kullanim/eszamanlilik/), the `/api/embed` **expense comparison's** seconds on [Speed and Cost](/en/kullanim/hiz-ve-maliyet/). The rig producing the measurement and the page carrying the number can be different; **two pages** can't tell one number. The already-measured 24-piece single request's time stays on its own page by this rule ([Training an Embedding Model](/en/rag/gomme-egitimi/)); the comparison ran, both arms were published in Speed and Cost, and that section additionally writes that it can't be compared with that old page. `rag/parcalama-ve-hibrit-arama/` only links to the batch result, writing no figure in its own sentence.
- **The comparison ban was written in advance.** The 24-piece single request's measured time (`kol-a.txt`, its count on its own page) and the RAG pages' 125-piece indexing times **aren't each other's A/B sides**: a different corpus, a different model, a different request form. The two can't be put side by side to build the sentence "batching is that cheap"; the item makes a verdict only after its own two arms' run.
- **The expected `-c` numbers stand in the register as a derived debt.** The `-c 12288` expectation for `=3` comes from the three measurements' pattern, not from a measurement; if there's a deviation, the deviation itself is the news's headline. The three slots' memory size also isn't pre-estimated — written as an empty cell, filled when run.
- **If the time ceiling is exceeded, the run isn't terminated.** Rule 2 says 20 minutes per arm. Three of the four measured full runs took 3'31" to 3'46" with 35 requests, and the 40-request K = 8 arm also stayed under four minutes (the windows on the Concurrency page); the 125-request arm also ran on October 20 and stayed under the 20-minute ceiling (the duration in the record). If the ceiling fills, no half log is published; "left midway" is written.
- **The out-of-scope neighbors.** Sending the 125 pieces in **one request**, levels above K=8, `/api/embed` concurrency and `OLLAMA_MAX_LOADED_MODELS` aren't in these three items; they don't enter a run without criteria written for themselves.

:::note[The cost of writing the criteria]
For the three items, a total of zero seconds of CPU, zero Ollama requests — the table above was written by reading the records on disk and the script lines. The run itself is separate and expensive: the first three concurrency runs took the machine owner's two restarts and effectively a ≈9-minute window (the eliminated attempt included); the fourth run asked no restart but asked its own window and contamination audit.
:::

## Not Measured

- That this map genuinely helps the reader was **not measured**; as in the banner mechanism, the only thing measured here is that the text rendered.
- The ten-rig / 14-script count was found by grepping with the `127.0.0.1:11434` string (together with the concurrency rig). The whole of the code wasn't audited line by line; the claim "the rigs never went to the internet" **wasn't verified in this run** (no network dump was taken). Examples 6 and 7 download corpora, so those two aren't offline anyway.
- The evidence tiers' (0-3) correct discriminating power was **not measured** — how many lines of a page stand at which tier wasn't counted.
- The measurements' **generalization scope** wasn't measured: this machine is a single Ryzen 5 2600, 15.9 GB RAM, 100% CPU. On another CPU, which number stays at which tier isn't known.

## Related Pages

- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — the source of the tier-3 numbers and the owner of the "what wasn't measured here" list.
- [Concurrency](/en/kullanim/eszamanlilik/) — the output page of the run this map pinned as "the next axis"; the first time the acceptance rules were applied as written to a run.
- [The End-to-End Single Line](/en/ornekler/ucdan-uca/) — the page closing the gap this map pinned as its next axis on October 19; it produced no measurement, only carrying the records' addresses and tiers.
- [The Roadmap](/en/baslangic/yol-haritasi/) — which hardware can do which job; the scope's hardware side.
- [Frequently Asked Questions](/en/kaynaklar/sss/) — the short answer to the question "is this guide sufficient alone".
- [The Verification Mechanism](/en/kaynaklar/dogrulama-mekanizmasi/) — the claims' standing against time; this map's maintenance side.

## Sources and Further Reading

- [Ollama frequently asked questions](https://docs.ollama.com/faq) — the `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_KEEP_ALIVE` defaults; the address of the numbers passing as tier 1 in this map. (Last read: 2026-10.)
- [Starlight — Sidebar](https://starlight.astro.build/guides/sidebar/) — configuring the section and page order. (Last read: 2026-10-19.)
