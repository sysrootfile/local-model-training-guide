---
title: "RAG Evaluation: Is Retrieval Broken, or Generation?"
description: "The practice of measuring a RAG system — retrieval measurement with hit@k and MRR, paraphrase robustness, the out-of-scope question margin and faithfulness checking. All experiments were actually run on this guide's Example 5 corpus."
dogrulama: 2026-11-20
---

The [RAG decision page](/en/rag/rag-mi-ince-ayar-mi/) taught you to build the pipeline and [Example 5](/en/ornekler/yerel-rag/) to run it. This page's question is different: **is the system you built good?** And in a RAG system "good" isn't one thing — there are two separate machines: **retrieval** (is the right document found?) and **generation** (is the right answer written with the found document?). Improving without measuring the two separately is repair with your eyes closed.

:::note[Every number on this page is a real measurement]
The experiments were **actually run on this machine** with Example 5's corpus (a fictional Bulut Kargo A.Ş., 8 documents) and the `olc.py` script (Ollama 0.40.4 — the machine moved to 0.40.6 on 2026-10-19; the numbers on this page weren't re-measured on that version; the bge-m3 and nomic-embed-text embedding models; the full log at `ornekler/yerel-rag/cikti/olc-kaydi.txt`). It's a small-corpus experiment: it shows the **pattern**, it gives no universal numbers.
:::

## Measure the Two Layers Separately

When an answer comes back wrong, the first question is: **did the retriever stumble, or the writer?**

| Symptom | Look at the retrieved pieces | The culprit | The medicine |
| --- | --- | --- | --- |
| The right piece never arrived | The right piece isn't in the top k | Retrieval | The embedding model, chunking, [hybrid search](/en/rag/parcalama-ve-hibrit-arama/) |
| The right piece is there but the answer is wrong | The right piece is in the context | Generation | The instruction, model size, context format |
| The model fabricates when it should say "I don't know" | Irrelevant pieces in the context | Both | A threshold + the system instruction |

The practical rule: always **start debugging from the retrieval log** — if you don't log which pieces were retrieved, the first job is adding that. Example 5's script prints a `[retrieval] best similarity: 0.709 -> return, damage` line on every query; that line is the raw material of this entire page's methodology.

## Retrieval Metrics: hit@k and MRR

To measure retrieval you set up a small **test set**: questions and, for each, the document/piece id "where the right answer lives". In Example 5 this is the `TEST_QUESTIONS` list (6 questions). The two basic measures:

- **hit@k:** is the right piece inside the first k results? Choose k equal to the number of pieces the system adds to the context (in Example 5 k=2; the test reports up to 3). Finding a result that will never be shown to the user is also an error — growing k raises hits but pollutes the context; the measurement should reflect k.
- **MRR (mean reciprocal rank):** it averages the reciprocal of the right piece's rank (1/rank) across questions. If the right piece is always 1st, MRR=1.0; if it's 3rd, that question contributes 0.333. hit@k says "did it enter?", MRR says "how high?" — read them together.

The measurement's honesty depends on the test set's honesty: match each question with the document **whose answer you know**, and write the set from user questions, not by looking at the system. A 20-30-question set suffices for direction-finding; don't read single-digit differences at this size — that's noise.

## Paraphrase Robustness: The Same Question, Different Words

The most common measurement mistake: writing test questions that imitate the documents' language. If you ask "how long is the return period?" against a document saying "the return period is 14 days", the keyword already matches — the model passed an easy exam. The user, though, asks "can I send the product back?". That's why for every question you must also measure a **paraphrase** (a different expression of the same information need).

`olc.py` did exactly that: alongside the 6 original questions it wrote 6 paraphrases and passed two embedding models through the same test:

```text title="The real measurement (olc.py, 2026-10-15)"
                          hit@1(orig)   hit@1(para)   MRR(para)
  bge-m3                      1.00          1.00        1.000
  nomic-embed-text            0.83          0.50        0.667
```

Two lessons:

1. **Paraphrase exposes hidden fragility.** nomic-embed-text passed the original questions with a "good-looking" hit of 0.83; when the words changed it fell to 0.50. The misses are explanatory: to the question "when will the shipment I have reach me?", it put the *damage* document in first place instead of *delivery* — the association of the word "reach" dominated at the word level.
2. **Your test set should have at least 2 expressions of every information need.** The difference was visible even in 12 original+paraphrase questions; the 6-question original set alone could have labeled nomic "successful".

## The Threshold: The Separation Margin with Out-of-Scope Questions

In Example 5 we saw the model say "I don't know" for the question "How's the weather in Ankara?" even though its similarity to the documents was low. This behavior isn't luck: there's a **gap** between the similarity distributions of in-scope and out-of-scope questions, and the threshold sits in that gap. `olc.py` printed this distribution with numbers:

```text title="Similarity bands (real measurement)"
  bge-m3            in-scope: 0.580 - 0.740   out-of-scope: 0.274 - 0.408
  nomic-embed-text  in-scope: 0.660 - 0.784   out-of-scope: 0.586 - 0.675
```

**separation margin = lowest in-scope − highest out-of-scope:**

- bge-m3: 0.580 − 0.408 = **+0.172** → a line can be drawn between them (Example 5's `WEAK_THRESHOLD = 0.35` sits exactly in this gap)
- nomic-embed-text: **−0.015** → the bands **overlap**; no threshold can produce the "I don't know" behavior in this system

The second lesson matters even more: nomic gave 0.59-0.68 similarity even to irrelevant Turkish questions — that is, it **confidently retrieved irrelevant documents**. An English-focused embedding model's "everything looks alike" problem in the Turkish space also kills the silence behavior: the system either produces irrelevant answers or fabricates.

:::caution[The threshold is the model's fingerprint]
Example 5's 0.35 threshold came out of bge-m3's distribution. The moment you change the embedding model, the threshold is **invalid** — you re-measure the new model's in-scope/out-of-scope bands and set the threshold again. Rule: the threshold comes after the measurement; it isn't copied before it. The same shift happens when the model is **fine-tuned**, even with a prefix added to the query: in the prefix experiment on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page, the rankings stayed exactly the same while the right pieces' band dropped ~0.08.
:::

### The same threshold, a second corpus: why carrying it is dangerous

The same `olc.py` logic was repeated with [Example 6](/en/ornekler/viki-rag/), i.e. on a live 125-piece Wikipedia corpus (bge-m3, 2026-10-15; log at `ornekler/viki-rag/cikti/olc-kaydi.txt`). The result showed that the rule above holds not only when the model changes but also when the **corpus changes**:

```text title="Bands measured on the 125-piece corpus (bge-m3)"
  in-scope (12 questions) : 0.598 - 0.714   hit@1 original 0.83 / paraphrase 0.67
  out-of-scope (8 questions) : 0.321 - 0.485
  separation margin       : +0.113          threshold suggestion: 0.541
  the inherited 0.35      : OUTSIDE THE BANDS — invalid on this corpus
```

The same script ran the second model too — the same 125 pieces, the same 20 questions:

```text title="The same corpus, the second model (nomic-embed-text, size=768)"
  in-scope (12 questions) : 0.624 - 0.808   hit@1 original 0.83 / paraphrase 1.00
  out-of-scope (8 questions) : 0.642 - 0.737
  separation margin       : -0.112
  threshold suggestion    : NONE — the bands overlap
```

Three new lessons:

1. **A small corpus makes for an optimistic threshold.** In Example 5's 8 documents the out-of-scope band stopped at 0.41; on a real 125-piece corpus it rose to 0.485. As the piece count grows, the chance of finding "a piece resembling even an irrelevant question" grows — the gap **shrinks**, the margin drops (+0.172 → +0.113).
2. **The out-of-scope set shouldn't be built from obvious irrelevancies.** In Example 6, "How do I make pizza dough at home?" got 0.344 while irrelevant questions containing the word "Istanbul" went up to 0.45-0.48 (cheap hotels, the stock exchange, Galatasaray). Real users ask questions that touch the corpus's topic but have no answer in it; if you set the threshold only with pizza recipes, you miss this class.
3. **Band overlap is a measurement result, not an error.** nomic-embed-text's retrieval itself isn't bad: the paraphrase hit@1 is **1.00** (bge-m3 stayed at 0.67). But the same model gives 0.642-0.737 to out-of-scope questions, i.e. the irrelevant question sits *inside* the relevant question's band. Building the "I don't know" branch with this model is impossible: whatever threshold you set, you either silence in-scope questions too or never catch the out-of-scope ones. Retrieval quality and threshold-worthiness are separate properties — measuring one doesn't guarantee the other.

Example 6's code's `WEAK_THRESHOLD` was moved to 0.54 after this measurement (`olc.py` keeps testing 0.35 so as not to break the comparison). The page itself now says so too: [Chunking and Hybrid Search](/en/rag/parcalama-ve-hibrit-arama/) narrates the measurement's repeat, along with the decision list.

## What Does Changing the Embedding Model Change?

The complete set of both experiments in one table — all on the same corpus, the same questions, only the embedding model differs:

| Measure | bge-m3 (multilingual) | nomic-embed-text (English-focused) |
| --- | --- | --- |
| hit@1 (original), 8 documents | 1.00 | 0.83 |
| hit@1 (paraphrase), 8 documents | 1.00 | 0.50 |
| MRR (paraphrase), 8 documents | 1.000 | 0.667 |
| Out-of-scope band, 8 documents | 0.27-0.41 | 0.59-0.68 |
| Separation margin, 8 documents | +0.172 | −0.015 |
| hit@1 (original), 125 pieces | 0.83 | 0.83 |
| hit@1 (paraphrase), 125 pieces | 0.67 | 1.00 |
| MRR (paraphrase), 125 pieces | 0.767 | 1.000 |
| Out-of-scope band, 125 pieces | 0.321-0.485 | 0.642-0.737 |
| Separation margin, 125 pieces | +0.113 | −0.112 |

The last two rows reverse the model interpretation: on the big corpus, **nomic** measured paraphrase retrieval better (1.00 / 0.67), but the separation needed for the threshold was given not by it but by **bge-m3**. A single table trusting a single model can lead to the wrong conclusion — that's why the measurement must be repeated across both corpus and model dimensions.

The conclusion is the numerical proof of the advice on the [RAG decision page](/en/rag/rag-mi-ince-ayar-mi/), "measure the embedding choice with your own data": with Turkish content, model choice can be not a "small efficiency difference" but a question of **whether the system works at all**. The measurement routine is cheap — the same test set runs against every model; the only caveat is that a 125-piece corpus on CPU takes minutes per model. Measured (2026-10-16, `127.0.0.1`): bge-m3 **259.2 s**, nomic-embed-text **158.6 s**. The same scripts had come out at 495.7 and 503.7 s on 2026-10-15 with the `localhost` address; nearly all of the difference was the ~2 s per-request Windows name-resolution overhead, and the scores stayed identical across both runs.

One operational note: when you change the embedding model you **must rebuild the whole index** (the vectors live in the model's space; the two models' vectors don't mix). Changing the generator model carries no such cost — the practical consequence of the "three models, three jobs" box in [Example 5](/en/ornekler/yerel-rag/).

## Measuring the Generation Side: Faithfulness and Relevance

Once retrieval is measured, the answer's turn comes. The three basic measures of the generation side:

- **Faithfulness:** is the answer consistent with the information in the retrieved documents? A number not in the documents is an claim of unclear origin.
- **Answer relevance:** does the answer actually answer the question asked? (Relevant but answerless responses are the classic error.)
- **Citation accuracy:** is the shown source really the document used? In Example 5's out-of-scope test, the small model had attached a **fabricated source** to the correct "I don't know" answer — verifying citations programmatically (does the shown id match the retrieved ids?) is a one-line check and must be done.
- **Latency:** a quality RAG answer taking 65 seconds is unusable in practice. This is measurable too: retrieval **0.09-0.13 s** (embedding the query, the 2026-10-16 run; 0.10-0.16 s in the previous run), generation **52-66 s** (reading Example 6's 4-piece context) — the phase-by-phase CPU breakdown is on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page. The most unexpected finding there: part of the latency has nothing to do with the model: on Windows, the `localhost` address adds ~2 s per request. When the scripts were switched to `127.0.0.1` on 2026-10-16, Example 6's 125-piece index went from **501.8 → 246.6 s**, and the similarity scores and hit@k lines **didn't change at all**. When measuring latency, separate wall time from the server's work; otherwise you'll mistake a name-resolution overhead for a slow model.

The common approach for automating the first three measures is the **LLM judge**: you ask a strong model "is this answer faithful to the documents?". The open-source framework designed for this job is **RAGAS** (Es et al., 2023): it computes the faithfulness, answer-relevance and context-relevance measures over the question-answer-document triple. Two cautions: the judge model errs too (especially in Turkish) — balance RAGAS output with periodic manual sampling; and the judge model's API cost is proportional to the question count.

:::tip[The three-question manual faithfulness check]
Even before building an automatic framework, read 5-10 random answers every week with three questions: (1) does every factual claim in the answer exist in a document piece? (2) does the answer fully answer the question? (3) is the shown source correct? This half-hour routine is usually the first thing to notice that the automatic measurements have broken.
:::

## The Practical Measurement Routine

In your RAG system, after every meaningful change (chunk size, embedding model, k, the instruction):

1. **Run the test set:** original + paraphrase questions → hit@k, MRR.
2. **Run the out-of-scope set:** similarity bands → separation margin → is the threshold still valid?
3. **Read 5-10 answers by eye:** faithfulness, relevance, citation accuracy.
4. **Keep the record:** which setting gave which number? An unmeasured experiment is an unrepeatable experiment — Example 5's and this page's outputs are all kept as logs in the `cikti/` folder.

If the measures came back bad, the medicine order is usually: fix **retrieval** first (chunking, embedding, hybrid search), then the **instruction**, and the **model size** last — that's the cost order: [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/)

## How Is the Experiment on This Page Repeated?

`olc.py` lives in the Example 5 folder and uses the same corpus as `rag.py` (the single source of truth):

```bash
cd ornekler/yerel-rag
python olc.py                    # compare the two models (bge-m3 + nomic-embed-text)
python olc.py --model bge-m3     # one model only
```

To use it on your own corpus, just change the `DOCUMENTS` and `TEST_QUESTIONS` lists in `rag.py` — the paraphrase and out-of-scope lists live in `olc.py`. No external packages are needed; only Ollama.

The same measurement logic carried to a bigger corpus is [Example 6: Turkish RAG from Wikipedia](/en/ornekler/viki-rag/) — `ornekler/viki-rag/olc.py` produced both hit@1/hit@4 and the second band table above on a 125-piece real-text corpus. If you want the measured path to improving the retrieval arm, there's a separate page: [Chunking and Hybrid Search](/en/rag/parcalama-ve-hibrit-arama/).

## Sources and Further Reading

- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al. 2020, arXiv:2005.11401)](https://arxiv.org/abs/2005.11401) — RAG's original paper; the pipeline's academic source.
- [RAGAS: Automated Evaluation of Retrieval Augmented Generation (Es et al. 2023, arXiv:2309.15217)](https://arxiv.org/abs/2309.15217) — the paper of the framework defining the faithfulness/answer-relevance/context-relevance measures.
- [RAGAS docs](https://docs.ragas.io/) — the framework's official guide to setup and metrics.
- [Example 5: The Local RAG Assistant](/en/ornekler/yerel-rag/) — the corpus, script and threshold discussion of this page's experiments.
- [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) — not a similarity threshold but a **generation probability** threshold: the same lesson repeats there too — the separation margin is a one-off number, and the threshold must be re-scanned on another model or dataset.
- [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/) — the decision map; the chunking and local stack sections.
- [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) — reading the training-side loss curves; RAG evaluation's training counterpart.
- [Benchmarks and Evaluation](/en/degerlendirme/benchmarklar/) — the difference between model-level and system-level measurements.
