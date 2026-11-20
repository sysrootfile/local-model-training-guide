---
title: "Chunking and Hybrid Search: The Two Arms of Improving Retrieval"
description: "The two settings that determine retrieval in RAG — chunk size and boundaries, and combining lexical with vector search. How BM25 and RRF work, the word-splitting traps of Turkish, and results measured on this guide's corpus."
dogrulama: 2026-11-20
---

The [RAG decision page](/en/rag/rag-mi-ince-ayar-mi/) explained when the pipeline is needed, and the [evaluation page](/en/rag/rag-degerlendirme/) how retrieval is measured. If the measurement tells you "the retrieval stumbled", you look at two arms: **what you indexed** (chunking) and **how you searched** (the search method). This page covers both; the experiment at the end actually raced three methods on the same 125-piece Turkish corpus.

## Why Is Chunking as Important as Model Choice?

An embedding model gives a text a single vector. If you put three different topics inside one chunk, that vector is pulled toward the **average** of the three topics and matches none of their questions perfectly. Chunking is the answer to "how many topics should one vector carry?"; that's why it affects the result as much as changing the embedding model.

Three separate pressures enter the job at once:

- **The retrieval side:** if the knowledge is split across two chunks, neither alone suffices; the measurement shows "the right chunk arrived but the answer is wrong". The culprit looks like generation, but it's actually in retrieval.
- **The context window:** chunk count × chunk size fills the generator model's `num_ctx` limit. The [lost-in-the-middle](https://arxiv.org/abs/2307.03172) finding kicks in exactly here: information in the middle of a long context is used less — so "more chunks" isn't free.
- **User patience:** every chunk goes into the prompt, so it delays generation on CPU (in Example 6 an answer with four chunks takes 52-66 s).

## The Chunking Taxonomy

| Method | Where it cuts | When it's good | The price |
| --- | --- | --- | --- |
| **Fixed size** (character or token window) | When the number is reached | A quick start, irregular text | Cuts mid-sentence; meaning is split |
| **Recursive** (paragraph → sentence → word priority) | At structural boundaries, descending if it doesn't fit | The most common general-purpose choice; web/PDF text | Many settings (target size, separator list) |
| **Structural / section-based** | Markdown heading, HTML tag, PDF page, code function | When the document already has logical sections | Sections aren't equally sized |
| **Semantic** | Where similarity between consecutive sentence vectors drops | Clearly topic-shifting long text | Embedding every sentence = expensive indexing |
| **Statistical clustering** | At cluster boundaries | Scattered/notes-like mixed text | The result is repeatable but hard to explain |
| **Late chunking** | Does the chunking *after* embedding | If you want to preserve the chunk's context | The model's long-input limit is decisive |
| **Parent-child** (small-to-big) | Searches the child chunk, returns the parent | When retrieval should be precise but generation wants broad context | Two indexes/two representations needed |

Late chunking was defined by [Günther et al. 2024](https://arxiv.org/abs/2409.04701): the whole document goes into the model, token-level vectors are pooled per chunk; so each chunk vector also carries its surrounding context. We didn't use it in this guide's examples — embedding the whole document in one shot is limited to 8192 tokens even for [bge-m3](https://huggingface.co/BAAI/bge-m3).

The price of raising the ceiling isn't as one-directional as thought: in the truncation experiment on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page, a chunk in which we had put the target sentence at the tail came **3rd** at a 128-token ceiling but fell to **9th** at a 512-token ceiling — the leading filler text diluted the pooling. Lengthening the chunk so it "doesn't get cut" may not improve retrieval.

### What the research says, and what it doesn't

Chroma's 2024 chunking evaluation ([Evaluating chunking strategies for retrieval](https://www.trychroma.com/research/evaluating-chunking)) found differences of **up to 9 points in recall** between splitters across five separate corpora; recursive splitting around 200 tokens was strong without overlap, and cluster-based semantic splitting gave the highest precision (IoU). Two caveats:

1. The study measured **only retrieval**, not generation. A chunk can be "right" but unpleasant to read.
2. The comparison was made against the authors' own splitters; i.e. the "best setting" stayed bound to the corpus and the embedding model. The experiment below on this page shows the same lesson **on its own corpus** with numbers: **the setting isn't chosen with someone else's number.**

The frequently given overlap advice "re-add the last 10-20%" is two-faced: prepending the neighbor chunk's beginning reduces information breakage, but the same sentence living in two vectors produces **duplicates** in retrieval — in Chroma's measurement, IoU fell as overlap grew. In Example 6 we kept the overlap to a single paragraph.

### The intersection of three ceilings

Chunk size comes not from a single number but from the intersection of three limits:

- **The embedding model:** bge-m3's maximum input is 8192 tokens (model card, last verified 2026-10). This is where the chunk must *fit*; in practice it's kept much smaller, because a long chunk's vector gets diluted.
- **The generator model:** Ollama's `num_ctx` default is tiered by VRAM (4096 tokens under 24 GiB — [doc](/en/kullanim/ollama/)). If k chunks × size + the instruction exceeds this limit, chunks are silently truncated.
- **Your document's own structure:** the average paragraph length is the natural ceiling for your target size.

Example 6's measured state (2026-10-15, the probing script in `ornekler/viki-rag/`):

- 8 Wikipedia articles were 88,861 characters → **125 chunks**; the chunk texts total **143,138 characters**, i.e. overlap and merging turn the corpus into an index **1.61x** the text read.
- Length per chunk: average **1,145**, shortest **245**, longest **3,274** characters. `TARGET_CHUNK = 800` is a **trigger**, not a ceiling: the paragraph is cut when it exceeds the target, which is why **91** of the 125 chunks are over 900 characters.
- The token counterpart: a 1,776-character chunk is **659 tokens** in the qwen2.5 tokenizer (~2.7 characters/token). The system instruction + question base is **145 tokens**; the first four chunks together are **2,309 tokens**. Total ≈ 2,454 — about 60% of the 4,096 default window.
- But if the longest chunk (3,274 characters ≈ 1,200 tokens) arrives four times stacked, the window overflows and the context is **silently truncated**. You need to grow `num_ctx` or put a per-chunk character ceiling; which one you choose depends on measurement.

These numbers are not a setting to copy, but an example of **how** the math is done for your own corpus.

### Turkish's special chunking traps

- **A period ends an abbreviation.** "vb.", "Dr.", "Örn.", "1. Madde" (Item 1.) fool sentence splitters; item numbers like "1." at line starts break sectioning.
- **Suffixes transform the word.** "Marmaray", "Marmaray'da", "Marmaray'ın" are three different word forms. Chunking doesn't affect this, but it directly affects the lexical search below.
- **Long sentences.** In academic/corporate Turkish, sentences stretched with commas can exceed the target size alone; the "split the sentence if it doesn't fit" rule (the recursive method) is mandatory.
- **Heading lines carry no information.** Wikipedia's `== Heading ==` lines are short but inefficient for embedding; Example 6 deliberately dropped them. Writing the heading text at the *start* of the chunk (carrying the heading hierarchy), however, generally helps semantic search.

## What Is Lexical Search (BM25)?

Vector search looks at "meaning" similarity; BM25 looks at **whether the word actually occurs in the document**. It scores with three components:

```text
score(q, d) = Σ terms  IDF(term) ·  (tf · (k1 + 1)) / (tf + k1 · (1 − b + b · |d| / avg|d|))
```

- **tf saturation (k1):** if a term occurs 5 times, occurring 50 times barely matters — the increase saturates. `k1` shapes this saturation curve.
- **Length normalization (b):** a long chunk is more *likely* to contain the term; `b` is the strength of this penalty. `b=0` ignores length entirely, `b=1` penalizes fully proportionally.
- **IDF:** a rare term (product code, proper name) earns more points than a frequent one ("line", "station").

Apache Lucene's `BM25Similarity` class uses **k1 = 1.2 and b = 0.75** by default ([doc](https://lucene.apache.org/core/9_10_0/core/org/apache/lucene/search/similarities/BM25Similarity.html), last verified 2026-10); it also has a non-negative IDF variant. Elasticsearch, OpenSearch and Solr are built around this line; you can read the theoretical summary from the [Robertson & Zaragoza 2009](https://www.nowpublishers.com/article/Details/IPR-017) paper.

### Which one wins on which question

| Query type | Example | Vector | BM25 |
| --- | --- | --- | --- |
| No word overlap, meaning present | "package return duration" → "return conditions" | strong | weak |
| Rare/exact term | `M11`, `P0042`, `TÜVASAŞ`, `2026/14` | fuzzy | strong |
| Numbers, dates, codes | "the institution founded in 1869" | weak (numbers don't separate in embeddings) | strong |
| Typo, abbreviation variant | "Marmaray", "İst." | sometimes rescues | misses |
| Multilingual / mixed with code | A Turkish question, an English document | strong (with a multilingual model) | misses |
| Long and sprawling document | A 40-page regulation | strong | weak |

This table has a **heavy side for Turkish**: because it's a suffixing language, the word the user types may differ from the word in the document ("seferleri" ↔ "sefer"). That's why lexical search systematically misses more in Turkish than in English; you need stemming down (tools like stemming/zemberek) or a hybrid merge.

:::note[The table is the expectation; the measurement below is the evidence]
The experiment below tested this table and **did not confirm all of it**. In the lexical set, vector and BM25 came out even on hit@1 (3/6 and 3/6): on the `M11` and "what year was İETT founded?" questions the vector took 1st place (the opposite of what rows 2-3 of the table expect), while BM25 led on the `batırma`, `Ayrılık Çeşmesi` and `vapur` questions. So this row is a direction, not a rule — it's flipped by whether the tokens in your corpus **also appear in other articles** (e.g. `M11` appears in two articles, `batırma` in one; the measurement showed this).
:::

## Merging: Why RRF Uses Ranks, Not Scores

Vector similarity is between 0-1, while the BM25 score is unbounded and corpus-dependent. Combining them in a weighted sum requires normalization first (Weaviate's `relativeScoreFusion` mode does this); **reciprocal rank fusion**, however, doesn't look at the score, only the rank:

```text
RRF(d) = Σ_over_lists  1 / (k + rank(d, list))
```

A document high in both lists wins. The standard value for the correlation constant `k` is **60**: both [Cormack, Clarke & Büttcher 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) and Elasticsearch's `rank_constant` default are 60. A small `k` heavily punishes the top ranks, a large `k` equalizes the lists.

The names you see in products circle the same idea:

| System | Merge name | Default |
| --- | --- | --- |
| Elasticsearch | the `rrf` retriever | `rank_constant` 60, candidate window `rank_window_size` |
| Weaviate | the `hybrid` query | `alpha`: 0 = keyword, 1 = vector; `rankedFusion`, `relativeScoreFusion` from v1.24+ |
| Qdrant | `Query::Hybrid` (dense + sparse) | `fusion` options RRF and DBRF |
| OpenSearch | the `hybrid` query + a `normalization-processor` in the search pipeline | normalization: `min_max`, `l2`, `z_score`; weighted merging |

:::note[Hybrid doesn't mean "add the two searches up"]
Merging ranks makes setting a single threshold **harder**: since the BM25 score has no absolute meaning, a check like "below 0.35 = irrelevant" doesn't work on the hybrid list. The threshold should stay on the vector similarity; the merge should only fix the ranking. The behavior we measured for out-of-scope questions in this page's experiment shows this.
:::

### The third tier: reranking

Keeping the candidate pool wide (e.g. 50 pieces) and then reranking with a small **cross-encoder** gives the precision that single-stage retrieval can't reach: a cross-encoder reads the question-piece *pair* together, it doesn't compare separate vectors. A multilingual, locally runnable example is [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) (0.6B). Two cautions: the model card documents multilinguality with support claims, and Turkish is **not among the named languages** in that list — don't trust it without measuring with your own test set; and since every candidate means a forward pass, it noticeably increases latency on CPU.

A similar "third tier" is enriching the chunk itself: Anthropic's [contextual retrieval](https://www.anthropic.com/news/contextual-retrieval) approach prepends to each chunk two model-generated sentences describing the chunk's place within the document. The published numbers are **the vendor's** (a 49% drop in failure rate with BM25, 67% with reranking) — you must verify on your own corpus; also, one generation call per chunk during indexing means money and time.

## The Experiment's Design

:::note[This section's numbers]
`ornekler/viki-rag/hibrit.py` downloads Example 6's corpus, both embeds the chunks (bge-m3) and converts them into a BM25 index in pure Python; then it races the three methods on the same questions, ranked by article title. The script **was run twice on this machine**, the only difference being the Ollama address:

| Run | Address | Vectorizing the 125 chunks | Full log |
| --- | --- | --- | --- |
| 2026-10-15 | `http://localhost:11434` | **529.3 s** (603 s total) | `cikti/hibrit-log.txt` |
| 2026-10-16 | `http://127.0.0.1:11434` | **253.0 s** | `cikti/hibrit-log-127.txt` |

The two logs' **ranking tables are identical line by line** (the ranks and hit@k lines match exactly); the only thing that changed is latency. The numbers below are from the 2026-10-16 run.
:::

The script holds three things constant so the comparison is meaningful: the same 125 chunks, the same questions, the same definition of "correct" (the expected article title). The only thing that changes is the ranking function.

- **The measured rank:** which position the expected article's *first* piece came in. hit@1 and hit@4 are reported; k=4, because four real pieces are added to the context.
- **Not making the list = no rank.** BM25 scores only the chunks passing at least one query word; if a 2-piece list's "3rd place" counted as hit@4, you'd fool yourself. That's why the script gives a non-matching article the rank of corpus size + 1, and `126` appears in the table.
- **Three question sets:** the original 6 questions (Example 6's test set), 6 paraphrases, 6 "lexical" questions. The lexical set is built with concrete terms occurring in the target article (the line code `M11`, the proper name `Seyrantepe`, the number `1869`, the term `batırma`), and the script verifies at runtime **which articles** each term occurs in across the corpus — i.e. the questions "expected to be won by the lexicon" really were built with the lexicon.
- **Word splitting is naive:** lowercase + regex. This doesn't stem the suffixes (`seferleri`); a deliberate shortcoming for Turkish, remember it while reading the results.

## The Measured Result: Three Arms, Three Question Sets

Every number below ran at the same time: the same 125 chunks, the same questions, only the ranking function differs. The cells are the **rank of the expected article's first piece**; `126` = not in the list at all.

```text title="hit@1 / hit@4 (k=4, 2026-10-16, hibrit-log-127.txt)"
  question set       vector        bm25        hybrid
  original (6)       5/6  6/6      3/6  6/6    4/6  6/6
  paraphrase (6)     4/6  5/6      2/6  4/6    2/6  5/6
  lexical  (6)       3/6  5/6      3/6  6/6    2/6  5/6

  query latency (average of 12 trials, CPU, wall time)
  vector (embedding call + cosine) : 0.144 s
  bm25   (pure Python, in-memory)  : 0.0001 s  (≈1,440x faster; 0.144/0.0001)
```

:::note[Two runs, two ratios: not 10,800x but 1,440x]
When the same script ran with `http://localhost`, the vector query measured **2.168 s**; with the address `127.0.0.1` it fell to **0.144 s**. The difference isn't the model's work but Windows resolving the `localhost` name in ~2 s on every request ([Speed and Cost](/en/kullanim/hiz-ve-maliyet/)). The BM25 arm's drop from 0.0002 → 0.0001 s, meanwhile, is a sub-millisecond wobble: run-to-run noise at that scale. The lesson: **build the ratio from the server's own time, not wall time** — the published 10,800x was the inflated form of a one-word client expense; the measured real ratio is 1,440.
:::

### Four honest readings

**1) The vector is clearly ahead on natural-language questions.** On the question "When was İETT founded?", the vector ranks 1st and BM25 4th: there is no decisive word in the question overlapping the İETT article's text ("when", "founded" appear in every article). Across the original + paraphrase sets combined, the vector is 9/12 and BM25 5/12.

**2) Lexical questions fall out of the vector's window.** On the question "Which pier do the ferry services call at?", the expected article slipped all the way to **14th** in the vector — outside the k=4 context window, i.e. practically a **total miss**. The same question is 2nd in BM25. The result is carried by BM25's hit@4: it's the only arm reaching full coverage in the lexical set with 6/6. Form-less tokens like `M11`, `Seyrantepe`, `Ayrılık Çeşmesi` get lost inside sparse paragraph context in a 1,024-dimensional vector.

**3) Hybrid couldn't beat either arm on hit@1 in this corpus.** In all three sets, hybrid's hit@1 isn't the highest value (4/6, 2/6, 2/6). It's visible one by one in the log:

| Question | vector | bm25 | hybrid |
| --- | --- | --- | --- |
| When did Marmaray enter service? | 1 | 9 | 2 |
| Which two stations does the tunnel funicular connect? | 1 | 2 | 3 |
| Which stations does the M11 line pass through? | 1 | 4 | 2 |
| Which pier do the ferry services call at? | 14 | 2 | 5 |

The reason is arithmetic: at `k=60`, the list's 1st rank gets 1/61 = 0.0164 points in RRF, the 9th rank 1/69 = 0.0145. So a list looking bad in BM25 can overturn the vector's first rank. The third row is exactly this: a question that had **both arms in the top three** falls to 3rd place after merging. In contrast, in the 4th row hybrid carries the vector's 14th to 5th, bringing it closest to rescue.

The honest summary: in this measurement, hybrid is an arm that **reduces variety rather than raising quality** — it drops the easy questions a little and pulls the expensive ones up. Shrinking the `k` constant, weighting the lists, or growing the candidate pool (20) gives different results; **these weren't measured here**, the page produces no guesses.

**4) The BM25 score can't carry a threshold — measured.** In the four out-of-scope questions the best BM25 scores: cat care **1.81**, Ankara museums **4.07**, "Turkey's longest river" **7.08**; on the pizza question there was **no matching piece**. The same questions' vector similarities are in the 0.321-0.485 band. Note: the highest BM25 score (7.08) came from an irrelevant question, because four of the words "turkiye / longest / river / which" occur in the corpus — function words inflate the score. A check like "below 0.35 = irrelevant" doesn't work on this arm; the threshold should stay on vector similarity, and the merge should only fix the ranking. This is the measured form of the "Hybrid doesn't mean adding the two searches" box above.

## Which One, in Which Case?

A decision list usable together with the experiment's result:

- **If your corpus has codes, numbers, item numbers, drug/product names** → the vector alone drops them from the window (measured: rank 14 on one lexical question, i.e. it never enters the k=4 context). Add at least one lexical arm.
- **If the user asks in a full sentence** → the lexicon alone isn't enough: in the original + paraphrase sets, hit@1 is 9/12 for the vector and 5/12 for BM25.
- **If the user can ask irrelevant questions** → keep the threshold on the vector arm; don't look for a threshold on the merged list.
- **If you have no GPU but want a solid baseline** → hybrid gathers the good sides of both arms into one list with zero training and zero new models. But the measurement showed this doesn't mean **winning on every question**: hit@1 couldn't beat the best arm in any set, in exchange for reduced variety. That should be your expectation.
- **If the context window is short** → don't let hit@4 decide: if the piece the merge rescued is in 5th place (the measured "ferry" case: 14 → 5), it still doesn't enter the context.
- **If indexing is cheap and queries are expensive** → consider semantic splitting or late chunking; these are written onto the indexing side, not the query side.
- **If query latency is critical** → keep BM25 as the single arm (lexical search returns within milliseconds), and use the vector asynchronously/cached.
- **If it's still not enough** → add reranking (a cross-encoder); this is the most expensive arm, save it for last.

## How Is the Experiment on This Page Repeated?

```bash
cd ornekler/viki-rag
python hibrit.py        # fresh indexing, 127.0.0.1 -> cikti/hibrit-log-127.txt (253.0 s vectorizing)
python hibrit.py        # second run: skips cached embedding, only ranking + latency
```

If you want to reset the cache and measure with `localhost`, the number rises to **529.3 s** (`cikti/hibrit-log.txt`, the 2026-10-15 run); the only difference is the address, i.e. 125 requests × ~2 s of name-resolution overhead.

The first run writes the `cikti/vektor-index.json.gz` file; if the corpus signature (piece ids + lengths) doesn't change, the embedding isn't repeated and the script prints the line `[cache] read 125 embedding vectors, vectorization skipped`. Since Wikipedia articles are live, the signature may change after a few days — in that case the script re-vectorizes.

Even in the cached second run, **all ranks and hit@k lines of the three tables came out exactly the same**; the only thing that differed was the query latency (2026-10-15 `localhost`: 2.168 → 2.174 s vector; 2026-10-16 `127.0.0.1`: 0.144 → 0.145 s vector, 0.0001 s bm25). So the experiment is deterministic: if you see a ranking difference, the cause isn't measurement noise but a code or corpus change.

## Sources and Further Reading

- [Robertson & Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond" (2009)](https://www.nowpublishers.com/article/Details/IPR-017) — who uses BM25 and what the `k1`/`b` settings do in practice.
- [Apache Lucene `BM25Similarity` class doc](https://lucene.apache.org/core/9_10_0/core/org/apache/lucene/search/similarities/BM25Similarity.html) — the default `k1 = 1.2`, `b = 0.75`; the parameters beneath Elasticsearch/OpenSearch/Solr.
- [Cormack, Clarke & Büttcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (SIGIR 2009)](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) — RRF's original paper; why it uses rank, not scores.
- [Elasticsearch RRF retriever doc](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) — `rank_constant` (default 60) and `rank_window_size`.
- [Weaviate hybrid search doc](https://docs.weaviate.io/weaviate/search/hybrid) — the `alpha` and `rankedFusion`/`relativeScoreFusion` modes.
- [Qdrant search doc](https://qdrant.tech/documentation/concepts/search/) — `Query::Hybrid` (dense + sparse) and the RRF/DBRF merge modes.
- [Chroma, "Evaluating chunking strategies for retrieval" (2024)](https://www.trychroma.com/research/evaluating-chunking) — the recall/precision comparison of splitting strategies across five corpora.
- [Günther et al., "Late Chunking: Improving RAG through Chunk-Aware Context Embeddings" (2024)](https://arxiv.org/abs/2409.04701) — the late chunking method and reference implementation.
- [Anthropic, "Contextual Retrieval" (2024)](https://www.anthropic.com/news/contextual-retrieval) — the approach combining adding context to the chunk with reranking; the numbers were measured by the vendor.
- [BAAI/bge-reranker-v2-m3 model card](https://huggingface.co/BAAI/bge-reranker-v2-m3) — a locally runnable multilingual cross-encoder; the supported-language list must be read carefully for Turkish.
- [Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" (2023)](https://arxiv.org/abs/2307.03172) — why information in the middle is used less as context grows.
- [This guide's RAG evaluation page](/en/rag/rag-degerlendirme/) — the steps of hit@k, MRR and threshold measurement; this page's experiment uses its measurement language.
- [Example 6: Turkish RAG from Wikipedia](/en/ornekler/viki-rag/) — the script that builds the experiment's corpus and the chunking decisions.
