---
title: "Training an Embedding Model: Improving Retrieval on Your Own Corpus"
description="The mechanics of training a ready embedding model on your own texts: the multiple-negatives ranking loss, hard negative mining, LoRA target layers and step times measured on a GPU-less machine. Four training arms were actually run on the same 24-piece Turkish corpus."
dogrulama: 2026-11-20
---

The [RAG decision page](/en/rag/rag-mi-ince-ayar-mi/) explained which problem justifies fine-tuning, and the [evaluation page](/en/rag/rag-degerlendirme/) how retrieval is measured. A gap remains between them: **the embedding model that builds the index itself.** If the vectors are bad, you'll change the chunking, the prompt and the generator model, and retrieval will still stumble. This page explains training that layer — and does it with numbers run on a single GPU-less machine.

The measurement rig is `ornekler/gomme-egitimi/gomme_egit.py`, the runner `kos.py`, the logs `ornekler/gomme-egitimi/cikti/kol-*.txt`. There are five arms: the plain shot (A), training (B), LoRA (C), the batch ceiling (D), and the `/api/embed` request overhead (E). A-D's numbers are on this page; E's two answers, repeat ranges and verdict were published on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page, and this page doesn't repeat those numbers. All of the numbers below were copied from those logs after the run finished.

## Which Model, Which Machine?

The base model is [`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2): a 384-dimensional output as the card says, `max_seq_length` 128, the apache-2.0 license, 50 languages. For comparison, the local [`BAAI/bge-m3`](https://huggingface.co/BAAI/bge-m3) was used (through Ollama's `/api/embed`): 1024 dimensions, an 8192-token input ceiling, the MIT license, and the card's claim of 100+ working languages.

The run was made **without a graphics card**: Ryzen 5 2600, 15.9 GB RAM, `torch 2.6.0+cpu`, `sentence-transformers 6.1.0`, `peft 0.21.2`. Two Windows traps appeared along the way:

1. torch's CPU wheels from 2.7 onward installed on this machine but didn't run, with `OSError: [WinError 1114]` (`c10.dll` fails to load); the installed VC++ runtime is 14.29. Rather than updating system DLLs, `torch==2.6.0+cpu` was pinned and the training ran with that version.
2. Installing `sentence-transformers==3.0.1` downgraded `huggingface-hub` and broke `datasets 5.1.0` with `BucketNotFoundError`. The two only work together on the 6.x line.

:::note[What this page doesn't claim]
The test set is 8 questions / 24 chunks, all hand-written for a fictional neighborhood. This table doesn't say "MiniLM is bad, bge-m3 is good"; it measures **the behavior on this corpus**. No confidence interval was computed. GPU, distributed training and a real dataset with hundreds of thousands of pairs were **not run** on this machine.
:::

## The Plain Shot: Where Are You Before Training?

Arm A trains nothing; it throws the untrained base model at a fixed test set. The body is 24 chunks, the queries 8; **deliberately disjoint** from the training pairs — the same sentence doesn't appear on both sides.

| Measure | Value |
| --- | --- |
| Model loading from cache | 12.70 s (a second load in the same session 4.51 s) |
| Parameters / output size | 117,653,760 / 384 |
| Downloaded weights folder | 457.5 MB |
| Process memory (RSS) | 179 MB → 1170 MB (+991 MB) |
| Encode speed | 24 chunks in 0.25 s (97.4 chunks/s) · 8 queries in 0.07 s (117.3 queries/s) |
| Body chunk token counts | shortest 18, average 22.3, longest 30 |
| bge-m3 indexing (Ollama) | 15.77 s → 1.5 chunks/s, 8 queries in 1.03 s |

A two-layer cost table emerges: **training** (once) and **re-indexing** (every time the model changes). The 24-chunk neighborhood bulletin is indexed by MiniLM in a quarter of a second; having 566-million-parameter bge-m3 do the same job takes 16 s. In arm B, after each training the re-index is 0.33-0.40 s — free on a small corpus. At enterprise scale (hundreds of thousands of chunks) the table is expected to flip: there, rebuilding the index can be more expensive than training the model. That sentence was **not measured here** — the only data we hold is that re-indexing the tiniest of tiny sets on this cluster ran in under a second.

## The Scoring Form Is a Hyperparameter

Same model, same questions, same body; only the distance definition changes:

| Scoring | hit@1 | hit@3 | MRR | Right pieces' band (avg.) | Best wrong | Separation |
| --- | --- | --- | --- | --- | --- | --- |
| normalize + cosine | 7/8 | 8/8 | 0.938 | 0.305-0.718 (0.609) | 0.541 | **−0.236** |
| normalize + negative Euclidean | 7/8 | 8/8 | 0.938 | −1.390 – −0.565 (−0.782) | −0.918 | −0.472 |
| raw + dot product | 7/8 | 8/8 | 0.917 | 4.377-12.345 (9.252) | 8.935 | −4.558 |
| raw + negative Euclidean | **6/8** | 8/8 | 0.875 | −21.140 – −9.066 (−12.223) | −12.181 | −8.959 |

**Separation** = the right piece's lowest score − the best wrong piece's score. All four rows are negative, i.e. in no run is there a "clean threshold separating right from wrong". The third row is the unnormalized dot product: long pieces get favored (MRR 0.938 → 0.917, one question fell from 1st to 3rd). The fourth row, raw + Euclidean: hit@1 falls **from 7/8 to 6/8**.

:::caution[The distance choice changes the result]
"Cosine or Euclidean?" isn't an aesthetic choice. If the vectors were normalized, all three measures give the **same ranking**; the first two rows' ranks above are already identical. The difference appears the moment you **forget** to normalize: in the raw + negative Euclidean row two more questions fell from first place and hit@1 dropped from 7/8 to 6/8. Also record whether you normalized when saving the vectors — "writing down what built the index" as described on the [license/model card page](/en/kullanim/lisans-ve-model-karti/) is exactly this.
:::

## The Query Prefix: Ranks Don't Change, Scores Do

Some embedding models are trained with an English instruction prefix added to the query. We gave bge-m3 the same 8 queries with the prefix `Represent this sentence for searching relevant passages: `:

| Condition | hit@1 | hit@3 | MRR | Right band (avg.) | Best wrong | Separation |
| --- | --- | --- | --- | --- | --- | --- |
| bge-m3, no prefix | 8/8 | 8/8 | 1.000 | 0.570-0.717 (0.670) | 0.528 | +0.042 |
| bge-m3, prefixed | 8/8 | 8/8 | 1.000 | 0.522-0.641 (0.586) | 0.480 | +0.042 |

**The ranks are exactly the same, the absolute scores shifted ~0.08 down.** Someone who thinks the threshold is an indicator of the model's quality lowers it here in vain. The practical result: **the threshold depends jointly on the model, the query template and the normalization form.** This is the retrieval-side counterpart of the seed finding on the [Reproducibility page](/en/kullanim/tekrarlanabilirlik/).

There's something more troubling in the same table: bge-m3 found 8/8 — the ranking is perfect — and yet there is only 0.042 between the right piece's lowest cosine (0.570) and the best wrong match (0.528). **A perfect ranking doesn't mean a separable band.** If you set the threshold at 0.55 you discard the right piece; at 0.50 you take in the wrong one.

## The Context Ceiling: More Text Isn't Always More Information

`max_seq_length` means truncation. The truncation cell was deliberately set up sneakily: at the tail there's a sentence **carrying the sought information** (`If the daycare quota is full, from the waiting list ...`), with 160 tokens of filler placed in front of it; the combined chunk is 180 tokens.

| Ceiling | Visible tokens | The tail sentence's cosine with the question | The long chunk's candidate rank |
| --- | --- | --- | --- |
| 128 | ~126 | **0.280** | **3 / 25** |
| 512 | ~180 | 0.234 | 9 / 25 |

The vectors the same chunk produced under the two ceilings resemble each other only **0.882**. Raising the ceiling removes the truncation, but on this set it **broke retrieval**: the filler text dilutes the pooling, and the single tail sentence's signal blends into the average. Truncation doesn't mean "loss of information"; sometimes it's noise getting in too. The fix isn't growing the ceiling but cutting the chunk in the right place — the [chunking page](/en/rag/parcalama-ve-hibrit-arama/).

## The Loss Function: Why MultipleNegativesRankingLoss Is the Default?

The core of training is `MultipleNegativesRankingLoss` (MNRL). You supply `anchor` and `positive` columns in the batch; **you don't write the negatives** — the other `positive`s in the same batch become that row's negatives. The goal is to push the correct pair's score ahead of the batch's 15 wrong pairs through softmax; the `scale=20.0` temperature coefficient determines how ruthlessly that race is scored. Two consequences:

- **Batch = negative count.** That's why arm D races batch 8 against 32: a bigger batch means more negatives at zero labeling cost.
- **You don't have to label negatives by hand.** We have only 40 paraphrase pairs; instead of building a separate negative list, we draw them from the batch. This is the main reason training on CPU is possible.

Other usable losses and whether they were measured in this rig:

| Loss | What it wants | When | In this measurement |
| --- | --- | --- | --- |
| `MultipleNegativesRankingLoss` | an anchor + positive pair | When you have pairs but no negatives | **Run (A/B/C/D)** |
| `CachedMultipleNegativesRankingLoss` | same, negative pool cached | When the data doesn't fit the batch | Not measured |
| `MatryoshkaLoss` | loss at several sizes at once | When you want to shrink and store the vector | Not measured |
| `CoSENTLoss` | a pair + a relative ranking label | When you can say "this is better than that" | Not measured |
| `TripletLoss` | an anchor/positive/negative triangle | When you picked negatives by hand | Not measured |

:::tip[The column order is the contract, not the name]
The library's [training overview doc](https://sbert.net/docs/sentence_transformer/training_overview.html) says it plainly: the **column names in the dataset don't matter, the order does** — the loss's `forward` signature treats the first column as the anchor, the second as positive, the third as negative. We still used the names `anchor` / `positive`, because `mine_hard_negatives(...)` asks for those names **as parameters** (`anchor_column_name`, `positive_column_name`). Most of the confusion on this line comes not from the text but from not recording the column order.
:::

## Hard Negative Mining

The model can scan its own body and pick the wrong piece it "confuses most" as a negative; the library has its own function: `mine_hard_negatives(...)`. The `hard-240` arm calls it with `num_negatives=1`, `sampling_strategy="top"`. The literature's claim is strong: a well-chosen hard negative improves markedly over a random one. The dangerous side is real too: **since the miner is the model itself**, you can feed the model a match it wrongly believes in as a training target. What the `hard-240` arm measures in this rig is exactly whether that claim holds on a small set.

## LoRA: Which Layers Are Trainable?

The `q_proj` / `v_proj` target names used on the [LLM fine-tuning page](/en/llm/lora-qlora/) belong to **LLM families**. MiniLM is from the BERT family: the attention lines are named `...attention.self.query` / `.key` / `.value`. If you go with the Llama names, it explodes before training starts:

```text
NoMatchingPeftModuleError: Target modules {'q_proj', 'v_proj'} not found
```

The right one is `target_modules=["query", "value"]`. Arm C sets it up with `r=16, lora_alpha=32, lora_dropout=0.05` and writes three numbers at once: the trainable-parameter ratio, the step time, and the adapter's size on disk against the base weights.

## How to Read the Training Arm

Arm B races six runs on the same fixed test set: 30/120/240 steps, 2e-5 and 1e-4 learning rates, two different seeds, one hard-negative arm. Every arm starts by **reloading the base model from scratch** — so the previous arm's weights don't leak in. Three numbers are read together:

1. **Retrieval:** hit@1 / hit@3 / MRR — what touches the user.
2. **Separation:** the gap between the right band and the best wrong — can you set a threshold.
3. **Memorization:** the rise in the training pairs' average cosine after training — did the model really *learn something*.

The three are different things and don't have to move in the same direction. That's why the inference "the loss dropped, so it improved" is wrong: **the loss function looks at the separation on the training pairs; not at the ranking on the test set.** The "change a setting → measure on the same fixed test set" loop set up on the [evaluation page](/en/rag/rag-degerlendirme/) applies here too.

## Arm B Results: Six Training Runs, One Result Line

All six arms started from the same base model (each arm loaded the model from scratch), were trained with MNRL on the same 40 pairs, and were measured on the same 8-question / 24-chunk set. The cost side:

| Arm | Data | Steps | Learning rate | Seed | Training time | Per step | Memorization gain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pair-30` | pairs | 30 | 2e-5 | 1234 | 42.94 s | 1.43 s | +0.182 |
| `pair-120` | pairs | 120 | 2e-5 | 1234 | 169.45 s | 1.41 s | +0.273 |
| `pair-240` | pairs | 240 | 2e-5 | 1234 | 319.70 s | 1.33 s | +0.295 |
| `hard-240` | hard negatives | 240 | 2e-5 | 1234 | 399.03 s | 1.66 s | +0.257 |
| `pair-240-lr4` | pairs | 240 | 1e-4 | 1234 | 319.76 s | 1.33 s | +0.363 |
| `pair-240-s5678` | pairs | 240 | 2e-5 | 5678 | 323.12 s | 1.35 s | +0.299 |

The result side — **hit@1 stayed at 7/8 in all six arms, hit@3 stayed at 8/8:**

| Arm | MRR before → after | Separation before → after | Right band avg. before → after |
| --- | --- | --- | --- |
| `pair-30` | 0.938 → 0.938 | −0.236 → −0.241 | 0.609 → **0.641** |
| `pair-120` | 0.938 → 0.938 | −0.236 → −0.258 | 0.609 → **0.548** |
| `pair-240` | 0.938 → 0.938 | −0.236 → −0.236 | 0.609 → **0.515** |
| `hard-240` | 0.938 → 0.938 | −0.236 → **−0.305** | 0.609 → 0.571 |
| `pair-240-lr4` | 0.938 → **0.917** | −0.236 → **−0.328** | 0.609 → **0.468** |
| `pair-240-s5678` | 0.938 → 0.938 | −0.236 → **−0.173** | 0.609 → 0.553 |

Six things were measured:

1. **The model learned.** The training pairs' average cosine rose from 0.503 into the 0.68-0.87 range in every arm. MNRL did its job.
2. **Retrieval didn't budge.** On the 8-question fixed test set, hit@1 stayed at 7/8 in all six arms. While the loss fell from 1.16 to below 0.001, the ranking stayed the same.
3. **The bands shifted down.** At 120 and 240 steps the right pieces' average score fell from 0.609 to 0.548 and 0.515 — while learning to separate the pairs, the model **lowered the absolute similarities**. At 30 steps the opposite happened (0.641). As the step count grows, the band doesn't move in one direction.
4. **A 5x learning rate did harm.** In the `lr=1e-4` arm MRR fell to 0.917 (one question dropped from 1st to 3rd), the separation opened to −0.328, and the band collapsed to 0.468. Small model + small data + high learning rate = more memorization (+0.363) and worse retrieval.
5. **Hard negative mining didn't help here.** While `pair-240`'s loss curve hit 0.000 at step 240, `hard-240`'s was still oscillating at 0.276 — the miner's chosen negatives genuinely made the loss harder. But the separation **worsened** from −0.236 to −0.305, and hit@1 didn't change.
6. **The seed made no difference here.** 1234 vs 5678: hit@1 the same, MRR the same, step time 1.33 vs 1.35 s. But the ranks did shift: before training question 7 was in 2nd place, while in the five arms trained on pair data question 6 moved to 2nd; in the `pair-240-lr4` arm question 7 fell to 3rd, and that's what broke the MRR. So "7/8" is the same number, a **different 7/8**.

The reason for item 5 sits in the log — the miner's chosen triangle:

```text
anchor:   Appointments are taken through MHRS.
positive: Family Health Center appointments are made through MHRS.
negative: The municipal guard report's number is requested in later applications.
```

The municipal guard report was chosen as the MHRS sentence's "most challenging wrong partner". In a pool of 40 positives, a weak model finding "the most similar but non-positive" **doesn't produce a meaningful challenge**; it only adds noise to training. Hard negatives are a different thing with a real body (thousands of chunks) and a strong base model — what's measured here is the small-set version.

:::danger[Long training on small data doesn't buy retrieval]
Running 240 steps (120 epochs; with `dataloader_drop_last` an epoch is two steps) at batch 16 with 40 pairs of data did not produce better results than running 30 steps at the same batch 16; only memorization rose and the band shifted down. This isn't saying "MNRL is bad" — it's saying **while your data is this small, before raising the step count go back to the chunking/threshold/distance options**. The Arm D section below shows the rig's single exception: when the same 240 steps ran at batch **8**, the ranking rose to 8/8. But in that comparison both the negatives per row and the epochs seen changed together, so a single cause can't be written for "the gain came from this". The [chunking page](/en/rag/parcalama-ve-hibrit-arama/) was giving the same message on another axis: the best setting isn't chosen with someone else's number.
:::

So what does training cost in practice? The `pair-240` arm took 5.3 minutes; all six arms together 27.1 minutes (1628 s in the record). The per-step time was between 1.33-1.66 s and didn't change with data size, since batch 16 stayed fixed: the **batch size and the model's size** determine the step time. What's really cheap on a small corpus is re-indexing: after each arm, re-embedding the 24 chunks took 0.33-0.40 s.

## Arm C: How Much Does LoRA Cheapen, How Much Does It Learn?

Same base model, same 40 pairs, same 240 steps; this time not all weights but two low-rank matrices attached to the attention lines are trained (`r=16`, `alpha=32`, `dropout=0.05`, `lr=1e-4`). What was measured:

| Measure | Value |
| --- | --- |
| All weights | 117,653,760 parameters |
| Trainable parameters | 294,912 (**0.251%**) — targets `["query", "value"]`, 24 matching modules |
| Step time | 0.54 s (full fine-tuning: 1.33 s) → **2.5x faster** |
| 240 steps total | 130.67 s (full fine-tuning: 319.70 s) |
| Process memory | 1426 MB |
| Adapter written to disk | **17.4 MB** |
| Downloaded base weights | 457.5 MB (adapter/base = 3.8%) |

The behavior side is mixed:

| | hit@1 | hit@3 | MRR | Right band (avg.) | Separation |
| --- | --- | --- | --- | --- | --- |
| lora BEFORE | 7/8 | 8/8 | 0.938 | 0.305-0.718 (0.609) | −0.236 |
| lora AFTER | 7/8 | 8/8 | 0.938 | 0.308-0.777 (0.632) | −0.253 |

Three readings:

- **Speed and disk are real.** 2.5x shorter time, 0.25% trainable parameters, and a 17.4 MB output instead of 457.5 MB. That's how small the thing to carry to another machine is.
- **The loss curve didn't behave like full fine-tuning.** While `pair-240` fell to 0.000, the LoRA arm hovered at 0.182 and the loss **rose** in the first 30 steps (1.235 → 1.476). Because the capacity is small, the model can't separate the pairs with the same certainty; the noise looks higher.
- **Still, nothing changed on the test.** hit@1 and MRR the same, the band average rose slightly (0.609 → 0.632), the separation opened slightly (−0.236 → −0.253). Doing **full** fine-tuning with the same `lr=1e-4` had dropped the MRR to 0.917 — LoRA's constrained capacity softened the error here.

:::tip[Save the adapter, or the whole model?]
For distribution the adapter (17.4 MB) is clearly cheaper; but loading the adapter requires the base model's **same revision**. If the base model is updated, the adapter's behavior becomes something unmeasured. The "the base model's name **and revision**" rule from the [model card page](/en/kullanim/lisans-ve-model-karti/) applies here too. And there's a practical difference: the merged full model is a simpler loading path, meaning 457 MB of disk and a single file set.
:::

## The Batch Ceiling: How Many Negatives per Row?

The loss function section above said the batch size isn't an ordinary speed setting but **the hyperparameter itself**: in MNRL, a row races against all the other positives in the same batch. Batch 8 means 7 negatives per row, batch 32 means 31. The rig's only batch trial is this section: the two arms ran with the same 40 pairs, the same `lr=2e-5`, the same seed 1234 and **the same 240 optimizer steps**.

The cost side:

| Batch | Negatives per row | 240-step time | Per step | Per row | Loss: first → last reading |
| --- | --- | --- | --- | --- | --- |
| 8 | 7 | 255.22 s | 1.06 s | 133 ms | 0.883 → 0.0026 |
| 32 | 31 | 446.97 s | 1.86 s | 58 ms | 1.701 → 0.0001 |

The result side — the rig's nine training runs' **only retrieval movement** is here:

| Batch | hit@1 before → after | MRR before → after | Separation before → after | Right band avg. before → after |
| --- | --- | --- | --- | --- |
| 8 | 7/8 → **8/8** | 0.938 → **1.000** | −0.236 → −0.206 | 0.609 → 0.573 |
| 32 | 7/8 → 7/8 | 0.938 → 0.938 | −0.236 → **−0.200** | 0.609 → **0.509** |

Four readings:

1. **The small batch won — the opposite of the literature.** The batch 8 arm carried 7/8 to 8/8: the ranks `[1, 1, 1, 1, 1, 1, 2, 1]` became `[1, 1, 1, 1, 1, 1, 1, 1]` — the single failing query rose from 2nd to 1st. In the batch 32 arm the rank total didn't change, but **the failing query changed places**: the 7th-ranked query fixed itself while the 6th-ranked one broke. The seed arm in Arm B had done the same — zero net change, two rank movements.
2. **With the step count fixed, growing the batch grows the round count.** 40 pairs and `dataloader_drop_last=True`: at batch 8 an epoch is five steps (40 ÷ 8), so 240 steps **= 48 epochs**; at batch 32 an epoch is a single step (the whole part of 40 ÷ 32 is 1, the remaining 8 pairs drop), so 240 steps **= 240 epochs**. So the batch 32 arm ran seeing each pair roughly four times more and still won nothing in the ranking. The batch ceiling and the round count are coupled in this setup; you can't say "the batch was grown as a single variable."
3. **The loss fell even deeper, no improvement came.** Batch 32's final loss reading is 0.0001, batch 8's is 0.0026 — i.e. the arm that won nothing in the ranking went roughly twenty times deeper in loss. A deeper loss isn't a better ranking — this is the cleanest example of the distinction set up in the Arm B section: **the loss looks at the separation on the training pairs; not at the test ranking.**
4. **The second-best separation, zero retrieval.** Batch 32's final separation (−0.200) is the second-best value of the nine runs; only the seed arm `pair-240-s5678` (−0.173) is better. But this arm's right band shifted down 0.10 (0.609 → 0.509, the lowest right cosine 0.249) and the band's peak stayed at 0.661. If the old threshold is carried to the new model, the right pieces start getting discarded — **a separation improvement doesn't mean the old threshold is still valid.**

The timing side alone isn't decisive either: batch 32 processed four times more rows in 1.75x the time (per row 133 ms → 58 ms). So **a bigger batch really is more efficient** — per unit of work. Only, at the same 240 steps, that means having more epochs, so the outcome changes; efficiency and quality aren't on the same key.

:::caution[Two runs, one number]
This section was written over two figures; each is a single repeat. That the rank movements (which query dropped) change with the seed was measured in Arm B, not in the batch ceiling. So the generalization "batch 8 is better" **isn't supported in this rig** — the only supported sentence is that on this 40-pair set, at 240 steps, batch 8 moved the ranking and batch 32 didn't.
:::

## What Is Recorded After Training?

The new vectors are **not in the same space as the old ones.** The moment you train the model, every piece you indexed yesterday becomes invalid. There are three things to record:

1. **The model itself or the adapter.** Full weights or a LoRA adapter — the two want different storage, different loading paths. Arm C measured exactly this distinction.
2. **The re-indexed body.** If you don't automate this, you'll search with an index partly produced by the old model; the scores become incomparable. [Example 6](/en/ornekler/viki-rag/) tied its vector index to the corpus signature (piece ids + lengths); when the model changes, the signature needs to include a **model id** too.
3. **The recalibrated threshold.** The separation and bands changed in every arm (the tables above). The old threshold is a random number on the new model.

:::caution[Memorization isn't success]
The training pairs' average cosine rose in every arm — the model **learned** to separate the pairs. The same arm's test ranking may stand still. The loss curve falling and the cosine rising are the proof of **learning**, not of improvement. The "is what you're reporting the same as what you're measuring" question described on the [self-audit page](/en/kullanim/lisans-ve-model-karti/) is asked here too.
:::

## The Decision List

- **Threshold first, model later.** On your own fixed test set, like [Example 6's measurement script](/en/ornekler/viki-rag/), extract your right/best-wrong band. If the bands don't separate, training is probably unnecessary; chunking and the threshold are cheaper.
- **Verify the base model's language support before entering training.** Small multilingual models "work" in Turkish but their thresholds don't resemble English models'; the 8-question difference between MiniLM and bge-m3 was measured on this page — not a generalization, a single-corpus observation.
- **The data shape determines the loss.** If you only have "(question, right chunk)" pairs, `MultipleNegativesRankingLoss` starts; if you have "(a, b, c)" triangles or relative-ranking labels, triplet/CoSENT respectively.
- **A self-contained pipeline is cheap.** Negatives drawn from the batch need no extra labeling; that's the real reason training on CPU is possible.
- **Don't think of batch size as a setting, count it as a hyperparameter.** At the same 240 steps, batch 8 moved the ranking to 8/8 while batch 32 stood still — but with the step count fixed, growing the batch also quadruples the epoch count. Changing both together and looking at a single number doesn't show which variable won.
- **Test hard negative mining on the small set.** Arm B measures it on 40 pairs and writes the result with numbers.
- **In the BERT family, find the LoRA targets from the model's module names.** If you insist on `q_proj`, you get an error.
- **Factor in the re-index cost.** Every time the model changes you re-embed the whole body; in this rig it ran in under a second, on large bodies it **may** be more expensive than training (not measured).
- **Re-set the threshold for every model and query template.** Adding a prefix didn't break the ranking but carried the bands down 0.08.
- **If you're training on a machine with a GPU, don't take this page's durations as your guide.** They were all measured on CPU.

## Sources and Further Reading

- [Reimers & Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" (2019)](https://arxiv.org/abs/1908.10084) — the original of embedding training with pairs/Siamese structure; this page's MNRL is its practical descendant.
- [Gao, Yao & Chen, "SimCSE: Simple Contrastive Learning of Sentence Embeddings" (2021)](https://arxiv.org/abs/2104.08821) — the "the other examples in the batch are negatives" vein of the technique; it uses dropout as a cheap negative generator.
- [Wang et al., "Text Embeddings by Weakly-Supervised Contrastive Pre-training" (E5, 2022)](https://arxiv.org/abs/2212.03533) — the recipe of an embedding model trained with millions of automatic pairs; why it raises the question "maybe a ready model suffices".
- [Li et al., "Towards General Text Embeddings with Multi-stage Contrastive Learning" (GTE, 2023)](https://arxiv.org/abs/2308.03281) — the industrial example of multi-stage training (general → ranking → distillation).
- [Chen et al., "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation" (2024)](https://arxiv.org/abs/2402.03216) — the paper of bge-m3, used for comparison on this page; the multilinguality and 8192-token multi-granularity claims live here.
- [Kusupati et al., "Matryoshka Representation Learning" (2022)](https://arxiv.org/abs/2205.13147) — the method of shrinking the index using the first `d` dimensions of one vector; `MatryoshkaLoss` comes from here.
- [Muennighoff et al., "MTEB: Massive Text Embedding Benchmark" (2022)](https://arxiv.org/abs/2210.07316) — 8 task types, 58 datasets, 112 languages; its own finding: **no method is superior on all tasks.** Look at the leaderboards with that eye.
- [Thakur et al., "BEIR: A Heterogeneous Benchmark for Zero-shot IR" (2021)](https://arxiv.org/abs/2104.08663) — BM25 still being a strong baseline on out-of-distribution data; the free alternative to try before saying "training is a must".
- [the sentence-transformers training overview](https://sbert.net/docs/sentence_transformer/training_overview.html) — the loss/dataset/trainer trio and the column-order contract.
- [the paraphrase-multilingual-MiniLM-L12-v2 model card](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) — 384 dimensions, a 128 ceiling, apache-2.0.
- [the BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3) — 1024 dimensions, an 8192 ceiling, the MIT license.
- [This guide's RAG evaluation page](/en/rag/rag-degerlendirme/) — how to set up hit@k, MRR and threshold measurement; this page's numbers use that language.
- [Chunking and hybrid search](/en/rag/parcalama-ve-hibrit-arama/) — the other half of the context-ceiling finding: cutting in the right place instead of truncating.
- [Reproducibility](/en/kullanim/tekrarlanabilirlik/) — the measurement of seed variance on the inference side; Arm B's seed arm is its training side.
- [License, personal data and model card](/en/kullanim/lisans-ve-model-karti/) — what must be written when publishing the model you trained; the downloaded weights' license was also measured there.
