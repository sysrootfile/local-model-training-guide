---
title: "The End-to-End Single Line: Walking from Data to Ollama"
description: "The page walking a Turkish assistant's five stations on a single line: data collection, cleaning, CPU training, evaluation and running in Ollama. It shows which script ran at every station, which record file the number sits in, what tier it is, and where the line breaks; it doesn't rewrite the numbers."
dogrulama: 2026-11-20
---

The site's other examples advance **topic by topic**: one page tells the data, one the cleaning, one the training, one the evaluation. The reader does the stitching themselves. This page makes that stitching explicit: **one line, five stations, in order.**

This line genuinely walked on this machine — but broke in two places. The page's real job isn't showing the walked part but putting **where and why it broke** into the reader's hands.

## Why There Are No Numbers on This Page

The [Scope Map](/en/kaynaklar/kapsam-haritasi/) rule: if two pages tell the same unit, one is wrong and both are a source. The seconds' address is [Speed and Cost](/en/kullanim/hiz-ve-maliyet/), hit@k/MRR's address [Training an Embedding Model](/en/rag/gomme-egitimi/) and the RAG pages, the concurrent request's address [Concurrency](/en/kullanim/eszamanlilik/). This page **doesn't rewrite** those figures; it carries which record file they stand in and what tier the claim is. This page itself is the single source of three things: **the station order, the tier label, the record file's name.**

## The Line's Five Stations

| # | Station | The script that ran on this machine | The record | Tier |
| --- | --- | --- | --- | --- |
| 1 | Collecting data | `ornekler/turkce-asistan/hazirla.py` | `cikti/rapor.json`, `cikti/egitim.jsonl`, `cikti/test.jsonl` | 2 — a single run |
| 2 | Cleaning the data | `ornekler/veri-temizleme/atolye.py` | `cikti/rapor.json`, `cikti/temiz_veri.jsonl`, `calistirma-log.txt` + the `-old`/`-before` pairs | 2 — a single measurement, a fix pair |
| 3 | Training the model | `ornekler/gomme-egitimi/gomme_egit.py --kol b/c/d`, `kos.py` | `cikti/kol-b.txt` `kol-c.txt` `kol-d.txt`, `kos-trace.txt`, `cikti/lora-adapter/` | 3 — the same configuration on two seeds |
| 4 | Evaluating | the fixed test set inside `gomme_egit.py` + `ornekler/yerel-rag/olc.py`, `ornekler/viki-rag/olc.py` | `kol-*.txt`, `yerel-rag/cikti/olc-log-127.txt`, `viki-rag/cikti/olc-log-127.txt` | 2 — two records but not in the same condition |
| 5 | Running in Ollama | `ornekler/cikarim-olcu/*`, `ornekler/eszamanli-olcu/eszamanli_olcu.py`, `gomme_egit.py`'s `/api/embed` arm | `eszamanli-log-*.txt`, `kol-a.txt` | 3 — three server settings |

:::note[Two ends, not one line]
Station 1 and station 3 **don't carry the same data.** Station 1's output is for chat training, while station 3's input is a separate Turkish corpus written for embedding training. This is the line's first stitching point and sits in the "Where It Breaks" heading below.
:::

## 1) Collecting Data

**What ran:** `hazirla.py`, the script live-downloading a Turkish SFT dataset from Hugging Face and passing it row by row. **What you look at:** `cikti/rapor.json` — the raw record count, the dropped count and the **text of the drop reason**, the train/test split, the seed. The numbers sit on the [Example 3: The Turkish Chat Assistant](/en/ornekler/turkce-asistan/) page; what happens here is those records' existence and why.

**Why rapor.json isn't enough:** because the data you downloaded may have changed today under the same name. Station 1's output isn't a model but a **chain of evidence**: which dataset, which version, which seed, which filter. The [License and Model Card](/en/kullanim/lisans-ve-model-karti/) page's personal-data scan is the same file's second job; if you don't know what went in before cleaning, you won't know after training either.

**The station's other form:** station 3's corpus wasn't downloaded, it was **hand-written into the script** (the pieces, the questions, the training pairs in one file). This isn't a flaw but a deliberate choice: without a fixed small test set, the question "did the training work" can't be asked. The hand-written set's price is this: the result is the behavior on that corpus, not the model's general capacity.

**The trap:** mistaking finding data for collecting data. The page telling where to collect it: [Where to Find Data](/en/veri/veri-nereden-bulunur/), the formats: [Data Formats](/en/veri/veri-formatlari/).

## 2) Cleaning the Data

**What ran:** `atolye.py` — near-duplicate weeding (MinHash + LSH) over Turkish instruction data pulled with streaming, the length/quality filter, field normalization and personal-data masking. **What you look at:** `cikti/rapor.json` plus `calistirma-log.txt` — the script's stdout, i.e. **which filter swallowed how many rows**.

This station has two records on disk, but they're **not a repeat**: the files with the `-old`/`-before` suffixes hold before and after the fix. A leak was found in the script's own output — normalization was applied to three fields while personal-data masking was applied to only two; since the SFT writer embedded the unmasked field into the user message, an unmasked email remained in a line **published by a masked pipeline**. The before/after line and the row number sit on the [Example 2](/en/ornekler/veri-temizleme/) page.

The line's lesson here is about the tier: a cleaning step's second record doesn't make that step **repeatable** — it makes it **provable**. If the two numbers come out the same you rise to tier 3; if one corrects the other, what's left in your hands is which record the fix lives in.

**Why a separate station:** because station 1's filter and station 2's filter do different jobs. One looks at "is this row enough for training", the other at "is this row right". In a project stacking both into a single script, nobody can say which rule killed how much data.

**Going deeper:** the [Data Cleaning](/en/veri/veri-temizleme/) concept page, its walked form [Example 2: The Data Cleaning Workshop](/en/ornekler/veri-temizleme/).

## 3) Training the Model — The Only Training That Ran on This Machine

:::caution[The choice: why an embedding model and not chat?]
Chat training (LoRA/QLoRA) wants a GPU; it wasn't run on this machine and that arm sits in the box below. The training path that could **genuinely run** on a GPU-less machine is training an embedding model: a small base model, a CPU-measurable step-time loop, and a measurable test set for the result. The line walks from that arm.
:::

**What ran:** `gomme_egit.py` — four arms: the plain shot (A), full training (B), LoRA (C), the batch ceiling (D).
**What you look at:** `kol-b.txt`, `kol-c.txt`, `kol-d.txt` and the trace of `kos.py`, which runs A→B→C in one shot, `kos-trace.txt`; the trained adapter itself under `cikti/lora-adapter/`.

The line's most instructive row is here: LoRA **genuinely won on the speed and disk side** (the trainable-parameter ratio, the step time, the written adapter's size against the base weights) but **didn't budge the ranking** — hit@1 stayed the same before and after training on the fixed test set. The loss curve dropping while the rank doesn't move is the main reason this site looks cautiously at the sentence "the training worked". All the numbers and the six training arms' breakdown on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page.

This station is tier 3, but not because of the six arms' repetition: the arm differences are each a **comparison**, not a repeat. The same configuration's repetition comes only from the arm run with a second seed, and that repeat didn't change a hit ratio — what it changed was **which questions** sat inside that ratio.

**The reading wisdom:** when reading a training arm, the three layers to look at are defined there — retrieval (hit@1/hit@3/MRR), separation (the gap between the right piece's lowest score and the best wrong one's), the cost (the step time, RSS, the MB written to disk). A result table writing one and not the others is an incomplete table.

**The lost record:** in this rig direct `>` redirection is used instead of `| tee`; in an intermediate attempt the `tee` line dropped a long run's output, and without the `-u` flag the script's output also stayed in the buffer. That the scripts' READMEs state this isn't a preference but an accident.

## 4) Evaluating

**What ran:** station 3's own fixed test set (the training's BEFORE/AFTER written with the same measurement), plus `yerel-rag/olc.py` and `viki-rag/olc.py` for the threshold band and ranking metrics.

**What you look at:** in every `olc-log-127.txt` line, **which address** was used. On this site, the switch from `localhost` to `127.0.0.1` alone changed the measurement result; that's why the evaluation records' both versions sit on disk (the old address and the new address). That's what verifying an evaluation page by itself means.

**Two measurement limits:**
1. The fixed test set is **small** and no confidence interval was computed. That the same hit ratio is produced by **different questions** on two different seeds is a measured state: the ratio the same, the right-wrong pattern inside it different. The seed/repeat side: [Reproducibility](/en/kullanim/tekrarlanabilirlik/).
2. Evaluation can catch the retrieval **breaking**: if the piece you're looking for fell outside the indexing limit, it isn't the model but the line itself that loses. Chunking and truncation: [Chunking and Hybrid Search](/en/rag/parcalama-ve-hibrit-arama/).

The third note belongs to the station's tier: the two records on disk don't form a **band**. The gap between them comes not from a repeat but from the address change, i.e. they aren't the same condition's two measurements but the same line's two different runs. That's why tier 2 is written in the table.

The metrics' definitions: [RAG Evaluation](/en/rag/rag-degerlendirme/), [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).

## 5) Running in Ollama

**What ran:** here the line compares the embedding models it trained with **Ollama's own model** (`/api/embed`, only `127.0.0.1`), then latency and concurrency are measured with the chat model on the same server. **What you look at:** `kol-a.txt` (embedding generation through Ollama), `eszamanli-log-*.txt` (three server settings), the `ornekler/cikarim-olcu/` outputs (the phase breakdown: loading, pre-fill, decode).

This station has three measured lessons, all on the relevant page: a single request's phases aren't independent of each other; on the server, as many requests as slots genuinely race, and the overflow waits in the queue; and the memory price doesn't rise in **equal steps** per slot. The numbers: [Speed and Cost](/en/kullanim/hiz-ve-maliyet/), [Concurrency](/en/kullanim/eszamanlilik/). Reading the server-side settings: [Inference Parameters](/en/kullanim/cikarim-parametreleri/).

## The Unwalked Arm: The Chat Assistant's GPU Steps

:::danger[This arm never ran on this machine]
`hazirla.py` genuinely ran; `egitim.py` (QLoRA) and `sor.py` (the before/after comparison) **didn't run** because they want a GPU. On this page and the relevant example page, not a single loss curve, answer text or comparison row belonging to those steps is presented as a **real run**; `sor.py`'s example output is *illustrative*, as the page itself says. The scripts were written against the current Unsloth/TRL APIs as of 2026 (tier 1) and may need version-difference fixes on the first real run.
:::

By the rule, this project runs no money-spending arm: the [Scope Map](/en/kaynaklar/kapsam-haritasi/) rule 1. So that arm is walked either on your own GPU or with a rented card; the plan and hourly rates sit as tier 1 on the [Cloud GPU Options](/en/donanim/bulut-secenekleri/) page. Including carrying a trained LoRA to GGUF and from there to Ollama: [LoRA Merging](/en/kullanim/lora-birlestirme/), [Quantization](/en/kullanim/quantization/), [Ollama](/en/kullanim/ollama/).

## The Order of Walking the Line on Your Own Machine

The two blocks below are **taken verbatim from the relevant rig's own README** and ran in this form on this machine; no new command was produced here.

```bash
# source: ornekler/gomme-egitimi/README.md — a single-arm run
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol c  > cikti/kol-c.txt 2>&1
```

```bash
# source: ornekler/turkce-asistan/README.md — the data preparation's quick trial (CPU)
python hazirla.py --limit 200
```

The order matters: **smoke first, the full run after.** After seeing a single arm, a single repeat, produce a record end to end, move to the full run. During the run send no other request to the same server; if you think you might have, probe with `GET /api/ps` before and after the run what's in memory. This rule had a price: in the concurrency rig, **while the server setting was right and all requests errorless**, a run was eliminated because of foreign requests entering its window, and not a single one of its numbers was published.

## Where It Breaks

- **The data stitch:** the chat line's data was downloaded, the embedding line's data hand-written. A single dataset didn't pass through the five stations end to end; had it, this page would be much shorter.
- **The training stitch:** the training that ran on this machine is only the embedding model's. Language model training stands at tier 0-1 (the box above).
- **The evaluation stitch:** a fixed and small test set; no confidence interval. The measured "the behavior on this corpus" isn't a generalization.
- **The running stitch:** the Ollama measurements were made with **ready models**. The adapter this line produced wasn't converted to GGUF and taken to the server with `ollama create`; i.e. station 5 runs not station 3's product but its model's product.

## Not Measured

- Whether this page actually makes the reader walk the line was **not measured**; the only thing measured is that the text rendered.
- The line's **total local cost** isn't on this page. The stations' own durations are measured on the relevant pages, but the five's sum would be a **sum**; a sum isn't a measurement.
- Whether the embedding LoRA's not moving the ranking also **holds on big corpora** wasn't measured.
- How many questions/pieces the hand-written test set has isn't written here (the single-source rule); that number is on the rig's own page.
- The `bge-m3` concurrent behavior measured at station 5: it **didn't run** on this axis; the concurrency measurement was made with the chat model.

## Related Pages

- [The Scope Map](/en/kaynaklar/kapsam-haritasi/) — the source of the tiers and acceptance rules; this page is that map's "next axis" row's walked form.
- [Training an Embedding Model](/en/rag/gomme-egitimi/) — stations 3 and 4's number source.
- [Example 3: The Turkish Chat Assistant](/en/ornekler/turkce-asistan/) — the unwalked arm's scripts.
- [Step-by-Step Training](/en/llm/adim-adim-egitim/) — the line's conceptual counterpart.
- [Local RAG](/en/ornekler/yerel-rag/) and [Wiki RAG](/en/ornekler/viki-rag/) — another line, untrained but measured end to end.

## Sources and Further Reading

- [Sentence Transformers — Training Overview](https://sbert.net/docs/sentence_transformer/training_overview.html) — the official telling of loss choice and the training loop. (Last read: 2026-10.)
- [Sentence-BERT (arXiv 1908.10084)](https://arxiv.org/abs/1908.10084) — the original definition of the pair/sentence ranking loss. (Last read: 2026-10.)
- [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) — the card of the base model trained on this line. (Last read: 2026-10.)
