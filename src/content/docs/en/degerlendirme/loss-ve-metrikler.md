---
title: "Loss and Metrics: Did the Training Actually Work?"
description: "Reading loss curves, the traps of loss and perplexity, task metrics, going deeper on classification and generation metrics, statistical significance, LLM-as-judge and the four numbers to watch during training."
dogrulama: 2026-11-20
---

The training loop finished, the model was saved. But did it actually work? This page introduces the tools you need to understand the difference between "the loss dropped" and "the model improved". If you want a refresher on what loss is: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/)

## Two Numbers: Training and Validation Loss

The loss is the number measuring the gap between the model's prediction and the correct answer; training tries to shrink it. But a single loss value isn't enough, because two different losses are tracked:

- **Training loss:** the model's error on the examples it *sees*. Its drop is the sign of learning — but alone it isn't sufficient.
- **Validation loss:** the model's error on the examples it *has never seen*, set aside at the start. It shows whether the model is really generalizing.

The reason we watch both is simple: the training loss always drops — even if the model memorizes the data. The validation loss, on the other hand, starts rising the moment memorization begins and gives us the "stop" signal.

:::tip
At the start of training, set aside 5-10% of your data with `train_test_split` and measure the validation loss at regular intervals with `eval_steps`. It's a 5-minute habit and protects you from the most expensive error (silent memorization).
:::

## Four Typical Curves and Their Meanings

```text title="(1) HEALTHY — both dropping, then flattening"
 loss
 2.4 |*                              * = training loss
 2.0 | **                             o = validation loss
 1.6 |   ****
 1.2 |       *****o
 0.8 |            oooo****
 0.5 |                oooooooo******____
     +------------------------------------> step
 Read: Learning is real; the model generalizes. The loss flattening is normal; you can stop.
```

```text title="(2) MEMORIZATION (OVERFITTING) — training dropping, validation rising"
 loss
 1.8 |*                          
 1.4 | **o
 1.0 |   ** o                    * = training loss (keeps dropping)
 0.7 |     **  o o                o = validation loss (rising!)
 0.5 |       **    o
 0.4 |         ***    o  o
     +------------------------------------> step
                         ^---- everything past here harms: stop training here
 Read: The model is memorizing the data. Fix: fewer epochs, more data, add dropout.
```

```text title="(3) NOT LEARNING AT ALL — both nearly flat"
 loss
 2.3 |* * * * * * * * * * *  o o o o o o
 2.2 |* o * o * o * o * o * o * * * o o
 2.1 |o o o o o o o o o o  * * o o
     +------------------------------------> step
 Read: The loss isn't even moving. Suspects: lr too low, a broken data format,
        corrupted labels (all masked). See: Troubleshooting section 3.
```

```text title="(4) SPIKING (UNSTABLE) — a sawtooth pattern"
 loss
 3.0 |        o
 2.5 |   *   *   o      o
 2.0 |*   *    *    *  *
 1.5 |  o    o   o  o   *   o
     +------------------------------------> step
 Read: lr too high or the effective batch too small. Fix: lower the lr,
        grow the effective batch with gradient_accumulation_steps.
```

:::note
These drawings are idealized; real curves are noisy. What matters is the **trend**: if the validation loss rises over a 100-step window, the memorization signal should be taken seriously.
:::

## Loss ≠ Quality: When the Loss Number Lies

The loss measures "learning to predict the token"; quality is a completely different thing. Three common situations where the loss number lies:

1. **Masking error (labels marked wrongly):** in SFT, the loss should be computed only on the answer tokens; the prompt tokens are masked with `-100` (the loss computation ignores that value). If masking is done in reverse, the loss drops but the model learns "producing questions" — and talks nonsense in production. The symptom: the loss is low but the outputs look like question sentences. Check: print how many of the labels in a batch are `-100`; if all are masked, the model can learn nothing (the "not learning at all" curve in the [Four Typical Curves](#four-typical-curves-and-their-meanings) section is exactly the result of this).
2. **Format leakage / pattern memorization:** the model learns the answer's template more than its content. The loss drops because pattern tokens like "Sure! Here's your answer:" are the same in every example and easy to predict; the content tokens are still weak. The symptom: every answer starts with the same pattern and the inner substance is thin. Prevention: vary the answer templates in the data and regularly read sample outputs **by eye**.
3. **The preference tuning (DPO) loss is different and read differently:** the "watch the validation loss" habit on this page is for SFT; in DPO, the loss says even less on its own. For details, see the "What Is Measured After DPO?" section on the [DPO and RLHF](/en/llm/dpo-rlhf/) page.

**Loss spikes:** one-step sudden jumps along the curve are usually harmless (an outlier batch). Persistent patterns demand intervention:

| Symptom | Likely cause | Intervention |
| --- | --- | --- |
| A big jump in one step, then descent | An outlier/hard batch | Ignore it; note its frequency |
| The loss settled at a new level after a spike | The weights got damaged | Lower the learning rate; resume from the last good checkpoint |
| Spikes recurring and growing | lr too high / effective batch small | Lower the lr; grow the effective batch with `gradient_accumulation_steps` |
| The validation loss also degraded | Real damage | Stop, roll back the checkpoint, review the data |

Most trainers apply gradient clipping (`max_grad_norm`, the common default 1.0); this already prevents most severe spikes. But if you see clipping at the ceiling value continuously, that's a sign the lr is still too high.

## Perplexity

Perplexity is the exponential of the loss: `perplexity = e^loss`. Its intuitive reading: "on average, how many options is the model torn between when predicting the next token?" Loss 1.0 → perplexity ~2.7; loss 2.3 → perplexity ~10. It's the most standard measure in language modeling because it maps one-to-one with the loss and is more intuitive on an exponential scale.

:::caution
Perplexity is comparable only between models using the **same tokenizer**. The perplexity numbers of two models with different token distributions are an apples-to-oranges comparison. Also, perplexity dropping doesn't mean chat quality improved — it only says "it predicts text better".
:::

### Perplexity Traps: Why Does the Number Mislead?

- **`e^loss` is an amplifier:** perplexity is the exponential of the average loss; small loss differences appear magnified in ppl. Example: loss 0.69 → ppl ≈ 2; loss 2.30 → ppl ≈ 10; loss 4.61 → ppl ≈ 100. So "a 0.7 loss difference" actually means 10x — be clear about which scale you're speaking on.
- **The tokenizer breaks comparison:** the same text produces a different number of tokens in different tokenizers; the per-token loss naturally changes too. The Hugging Face docs warn about this explicitly: the perplexity of models with different tokenizers can't be compared.
- **Naive windowing inflates it in long context:** if the text is longer than the model's context window and is split into plain chunks scored independently, each chunk's beginning is predicted "context-free", so the ppl comes out higher than it is. The fix is Hugging Face's recommended **sliding-window (strided) evaluation**: the window stride is kept smaller than the context length and only the new tokens enter the loss; the context is carried over. The difference isn't to be shrugged off: in the docs' GPT-2 example the same text gives ppl 19.44 with a stride of 1024 and 16.44 with a stride of 512 — i.e. the technique choice looks like a 3-point "improvement".
- **Low ppl ≠ good assistant:** perplexity measures text prediction; not instruction-following, accuracy or style. For chat quality, move to task metrics or LLM-as-judge.

(Details and a code example: the Hugging Face "Perplexity of fixed-length models" doc; linked in the bibliography.)

## "The Loss Dropped but the Answers Are Bad" — Why Does That Happen?

This is the situation that surprises beginners most; the explanation:

1. **Memorization:** if the model learned the training examples word for word, the training loss drops a lot; on new questions it stumbles. The validation loss catches this — again: watch it.
2. **Format obsession:** the model may have learned the answer's *pattern*, not its *content* (e.g. always starting with "Sure! Here's your answer:" but the text coming out is empty). The loss measures token prediction; not whether it produces the right tokens with the right **meaning**.
3. **What you measured is incomplete:** the loss measures "how much the model resembles the training distribution". What you actually seek in real use (helpfulness, accuracy, style) must be measured separately.

Conclusion: the training loss is an **instrument gauge** (like engine temperature), not a destination gauge. Measuring production quality requires the approaches below, and which of them is needed depends on the task.

## A Quick Tour of Task Metrics

| Task type | Metric | What it measures | Where/when it's weak |
| --- | --- | --- | --- |
| Classification | Accuracy | The rate of correct predictions | Misleading when classes are imbalanced (a model saying "no" 99% of the time gets 99% accuracy) |
| Classification | Precision / Recall | Exactness / catch rate | Look at which error is more expensive (spam filter: precision; disease screening: recall) |
| Classification | F1 | The balance of the two | Can still mislead with very rare classes |
| Generation | Exact Match | Verbatim match with the reference | Too strict on free text; even a one-word difference counts as "wrong" |
| Generation | BLEU | n-gram overlap (the translation tradition) | Doesn't measure meaning; punishes a different but correct translation |
| Generation | ROUGE | Word/phrase overlap with the reference (the summarization tradition) | Can be gamed with word play; doesn't measure fluency |
| Ranking | MRR | Where the first correct result ranks | Cares only about the first result |
| Ranking | NDCG | The quality of the whole ranking (graded) | Takes some math to understand; noisy on small sets |

### Going Deeper on Generation Metrics: BLEU's Limit and the Alternatives

The common limit of the generation metrics in the table is this: **a single reference doesn't represent the variety of correct answers.** Let's look closely at the family:

| Metric | What it does | Its limit / caution |
| --- | --- | --- |
| BLEU | Measures n-gram overlap in the "precision" direction (the translation tradition) | Doesn't measure meaning; misses synonyms, punishes a different but correct translation; shouldn't be used alone outside translation |
| ROUGE | Word/phrase overlap with the reference (the summarization tradition) | Favors long summaries; doesn't measure fluency and coherence |
| Exact Match (EM) | Normalizes the answer (lowercase, punctuation) and compares verbatim with the reference | Only meaningful on short-answer tasks (SQuAD-style); too strict on free text |
| BERTScore (arXiv:1904.09675) | Matches tokens with contextualized representations (BERT embeddings); forgives synonyms | Still reference-bound; can't fully catch a "completely different but correct" answer |
| MAUVE (arXiv:2102.01454) | Measures the distribution overlap between the model's text pool and a human text pool | Doesn't require individual references but needs a human text pool; suited for open-ended generation (chat) |
| pass@k (arXiv:2107.03374) | In code: it suffices that at least one of k samples passes the tests | The score rises mechanically as k grows; always report it together with k (pass@1 and pass@10 aren't comparable) |

:::note
The practical selection rule: **if a reference exists** (translation, short answers), BLEU/ROUGE/EM are still a useful start; **if there's no single correct answer** (chat, summarization, style), move to MAUVE, LLM-as-judge or human evaluation. BERTScore is a reasonable bridge between the two.
:::

### Precision / Recall / F1: A Small Calculation

Consider a spam filter over 100 emails: there are really 10 spam emails; the model marked 12 emails as "spam" and 8 of them turned out to be genuine spam.

- **Precision** = correctly marked / total marked = 8/12 ≈ 0.67 → "67% of what I called spam really is spam"
- **Recall** = correctly marked / actual spam count = 8/10 = 0.80 → "I caught 80% of the spam"
- **F1** = harmonic mean = 2 × (0.67 × 0.80) / (0.67 + 0.80) ≈ 0.73

Which metric is "more important" depends on the cost of the error: marking an important email as spam (a precision problem) is usually more annoying than a missed spam (a recall problem). Clarify this cost in your own project first, then decide the metric.

:::tip
A simple principle: **you optimize what you measure.** That's why metric choice should align with your product decision. If you're doing summarization, rather than trusting ROUGE/BLEU alone, include the question "is the summary sufficient when a human reads it?" in the scoring.
:::

### Going Deeper on Classification: The Confusion Matrix, the Threshold and AUC

The table behind the precision/recall calculation is the **confusion matrix**; in binary classification there are four cells:

| Situation | Model said "positive" | Model said "negative" |
| --- | --- | --- |
| Actually positive | True positive (TP) | False negative (FN — missed) |
| Actually negative | False positive (FP — false alarm) | True negative (TN) |

- Precision = TP / (TP + FP); Recall = TP / (TP + FN). In the spam example TP=8, FP=4, FN=2 → precision 8/12, recall 8/10: the table and the calculation match one-to-one.
- **The threshold changes everything:** the model usually produces a probability; if you pick 0.8 instead of 0.5 as the bar for saying "spam", precision rises and recall falls. Threshold choice isn't a "model setting" but a product decision: whichever error costs more, the threshold is chosen accordingly.
- **ROC-AUC and PR-AUC answer different questions:** the ROC curve plots the true-positive rate against the false-positive rate at all thresholds; AUC condenses that into one number. But if the classes are imbalanced (e.g. 1% of the tasks are positive), ROC-AUC can look optimistic; when the positive class is rare, **PR-AUC** (the area under the precision-recall curve) tells the situation more honestly (Saito & Rehmsmeier, PLOS ONE, 2015).
- In multi-class work the matrix widens, and that's where the real benefit appears: seeing which classes confuse each other is far more useful than a single number like "accuracy 85%".

:::tip
When reporting, write the triple instead of one number: "precision 0.92, recall 0.61 (threshold 0.5)". A report that omits the threshold is unreadable; and when comparing two models, make sure both were measured at the same threshold.
:::

## LLM-as-Judge (The Judge Model)

In generation tasks (chat, summarization, style) there is no single correct answer; that's why the method "have another strong model score it" spread: **LLM-as-judge**. The method: take answers from model A and model B to the same question, ask a strong judge model (e.g. a big commercial model or a larger local model than yours) "which is better and why?", or have it score 1-5.

**Advantages:** far faster and cheaper than human evaluation; scalable; can be consistent given a criteria list.

**The traps and precautions:**

- **It likes its own outputs:** the judge model is biased toward outputs from its own family. Prevention: as the judge, pick a **different family** than the models you're comparing.
- **The order effect:** the presentation order (A first or B first) affects the result. Prevention: evaluate every pair in both orders (A-B and B-A) and merge the results.
- **A vague rubric:** instead of "which is good?", give clear criteria: "Score 1-5 on accuracy, grammar, the requested style and compliance with the length constraint."
- **Calibration:** score 20-30 examples yourself by hand and compare them with the judge's scores; if they disagree, fix the rubric.

## Statistical Significance: When Are Score Differences Real?

The sentence "model A scored 71%, model B 69%" says almost nothing on its own; because every measurement contains sampling noise. In a 100-question test **a single question is worth 1 point**, and had your question selection been slightly different, the ranking could have flipped. A rough calibration (assuming ≈70% accuracy and independent sampling):

| Test size | Standard error (approx.) | The "noise band" between two scores |
| --- | --- | --- |
| 100 questions | ≈ 4.6 points | ≈ 6.5 points |
| 500 questions | ≈ 2.0 points | ≈ 2.9 points |
| 1,000 questions | ≈ 1.4 points | ≈ 2.0 points |
| 10,000 questions | ≈ 0.5 points | ≈ 0.7 points |

The logic of the math: standard error ≈ √(p(1−p)/n). At 70% accuracy, for n=100, √(0.7×0.3/100) ≈ 0.046, i.e. ±4.6 points. The standard error of the difference between two independent measurements is about √2 times that; the "noise band" in the table is this value. Conclusion: a 5-point difference on a 100-question set doesn't count as "clear superiority"; a 2-point difference on a 1,000-question set can be taken seriously.

- **Report a confidence interval:** like "70 ± 5". Miller's "Adding Error Bars to Evals" note proposes exactly this: write the standard error alongside the mean, and require the test set to be large enough for a meaningful signal (in that note the "strong signal" criterion is at least ~1,000 questions; arXiv:2411.00640).
- **The same problem in LLM-judging:** if you compared 50 pairs with a judge and found a "58% win rate", that's most likely noise. Increase the pair count or give a range.
- **Don't enter a ranking race on a small set:** some of the "2-point difference" claims on dashboards fall inside this band; that's why we emphasize date, version and setup labeling so much on the [Benchmarks](/en/degerlendirme/benchmarklar/) page.

## A Short Note: Contamination Is the Silent Killer

Test questions (or very similar ones) leaking into the training data is **contamination** (data leakage); such a score is not "success" but the measure of memorization. One of the most talked-about examples is GSM8K → GSM1k: some models scoring very high on GSM8K showed a clear drop on GSM1k, questions **newly written** in the same style (arXiv:2405.00332). The practical consequences for you:

- Prefer cleaned / cross-checked versions (e.g. SWE-bench Verified, GPQA Diamond).
- When building your own mini set, keep a portion "unlooked at" on the side; as you work, you can unknowingly tune toward that set (human-origin leakage).
- If a score looks "too good", ask about leakage first; second, check setup differences ([Benchmarks](/en/degerlendirme/benchmarklar/)).

## In Practice: The 4 Numbers to Watch During Training

Note these four numbers at the start of training; each is the sign of something:

| Number | Ideal behavior | Abnormal pattern and meaning |
| --- | --- | --- |
| `loss` (training) | A steady but noisy descent | If it never drops: an lr/data problem; if it's near zero: memorization |
| `eval_loss` (validation) | Falls in parallel with training, then flattens | If it rises early: memorization, stop |
| `learning_rate` | Follows the planned curve (cosine/linear) | If it stays at zero: the scheduler/warmup setting is broken |
| `grad_norm` | Fluctuates within the same magnitude | If it occasionally explodes: lr high or problematic data; if it's always near 0: no gradient flowing (masked labels?) |

The gradient norm is the measure of the gradients' magnitude. Most training tools log it; if not, it appears in the `logging_steps` output. These four numbers — the training's "health panel" — let you catch most problems before bigger damage forms.

## Wrapping Up

- The loss is a tool, not the goal; watch the training + validation loss together.
- Know the four typical curves: healthy, memorizing, flat, spiky.
- Perplexity is comparable only between models with the same tokenizer.
- In the "loss dropped but answers are bad" case, measure production quality with task-appropriate metrics or LLM-as-judge.
- Watching `loss`, `eval_loss`, `learning_rate` and `grad_norm` during training forms a four-piece health panel.

Continue: compare models with [Benchmarks and Real Evaluation](/en/degerlendirme/benchmarklar/); to fix a bad curve, return to the [Hyperparameters](/en/llm/hiperparametreler/) page.

## Sources and Further Reading

- [Hugging Face — Perplexity of fixed-length models](https://huggingface.co/docs/transformers/en/perplexity) — the e^loss logic, the tokenizer warning and the sliding-window technique (with GPT-2 example code).
- [BERTScore (arXiv:1904.09675)](https://arxiv.org/abs/1904.09675) — evaluating generated text with contextualized representations.
- [MAUVE (arXiv:2102.01454)](https://arxiv.org/abs/2102.01454) — the metric measuring the gap between model-text and human-text distributions.
- [Saito & Rehmsmeier, PLOS ONE (2015)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432) — why the PR curve is more informative than ROC on imbalanced data.
- [Adding Error Bars to Evals (arXiv:2411.00640)](https://arxiv.org/abs/2411.00640) — standard error, confidence intervals and the required question count in evaluations.
- [A Careful Examination of LLM Performance: GSM1k (arXiv:2405.00332)](https://arxiv.org/abs/2405.00332) — a striking example of contamination's effect on scores.
- [The Codex paper (arXiv:2107.03374)](https://arxiv.org/abs/2107.03374) — the origin of the pass@k metric.
- [Judging LLM-as-a-Judge / MT-Bench (arXiv:2306.05685)](https://arxiv.org/abs/2306.05685) — the position, length and self-preference biases of judge models.
