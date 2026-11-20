---
title: "Confidence and Calibration: How Sure Is the Model of Itself?"
description: "What logprobs and top_logprobs actually produce in Ollama, why the record count differs from the generated token count, whether the P(True) pattern falls into positional bias on Turkish multiple choice, whether temperature changes the reported probability, how many questions verbal confidence is readable from — numbers measured from the 2026-10-17 records."
dogrulama: 2026-11-20
---

Asking a model to say "I don't know" is a separate job from the quality of the text it produces. The only way to do it isn't asking the model for its internal state; there are three separate confidence sources: **generation probability** (how likely the model sees the correct option, token by token), **self-consistency** (does sampling the same question land on the same answer) and **verbal statement** (how many points the model gives itself). This page ran all three sources on this machine, and measured a fourth thing: **does Ollama's `logprobs` field behave according to the doc, or differently from what we assumed reading the doc?**

:::note[The credentials: four runs, one machine]
The script: `ornekler/eminlik-olcu/eminlik.py`. The records: under `ornekler/eminlik-olcu/cikti/`,
`prob.txt` (the A + H contract prob, **2026-10-17 22:09:25 → 22:09:59**, 27 inference requests),
`olcum.txt` (the B-F full run, **23:05:00 → 23:10:02**, 5 minutes 2 seconds, 176 chat + 100 embedding requests),
`g2.txt` (arm G with the fixed parser, **23:12:27 → 23:13:16**, 10 chat requests) and
`kontrol-b.txt` (the B digit check, 23:04:00 → 23:04:33).
Ollama **0.40.5**, the models `qwen2.5:3b-instruct-q4_K_M` and `bge-m3`, on CPU; the address `http://127.0.0.1:11434`. The [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page's run was taken with 0.40.4; this page's records are from 0.40.5. The machine's server moved to 0.40.6 on 2026-10-19; the numbers on this page weren't re-measured on that version.
The golden answers were written by hand from pages already documented on this site, not from the model's memorization. No other Ollama request was sent during the runs.
:::

## What Does `logprobs` Actually Produce

When you add `"logprobs": true` to the `/api/chat` body, a `logprobs` field comes in the response; each record has `token`, `logprob`, `bytes` fields (prob.txt A1). If you also send the `top_logprobs` count, a fourth field, `top_logprobs`, is added, carrying that position's candidate list (A2). The measured limits:

| Request | Result |
| --- | --- |
| `top_logprobs` not sent | no candidate list (`min 0 / max 0`), `token`/`logprob`/`bytes` arrived |
| `top_logprobs = 1` … `20` | the requested candidate count returned exactly (5 → 5, 10 → 10, 20 → 20) |
| `top_logprobs = 0` | the candidate field came but the list was empty |
| `top_logprobs = 100` | **HTTP 400**, body: `{"error":"top_logprobs must be between 0 and 20"}` |
| `top_logprobs = 5` but `logprobs: false` | **the `logprobs` field never came** — `top_logprobs` was silently ignored |

The last row is this page's most useful finding: sending the field and the field arriving aren't the same thing. If the measurement code assumes "I asked for it, so it's there", it silently holds an empty list; the thing to check isn't the request's body but **whether the `logprobs` key exists in the response**.

**The record count and the token count differ.** Between the generated token count (`eval_count`) and the logprob records there was always a gap of 1 on this machine:

```text
A1 | out 18 | logprob records 17      (free generation)
A3 | out  1 | logprob records  1      (num_predict=1)
A7 | out 36 | logprob records 35      (format=json)
```

The gap alone doesn't mean "the model produced one more token"; whether the trailing stop token's logprob record was produced, or whether `eval_count` counted one too many, **wasn't distinguished in this rig**. The practical result: when taking a sequence's average logprob, the denominator should be not `eval_count` but **the record count**. On this page all averages were taken by dividing by the record count.

## The Same Prompt, the Same Logprob — Until the Model Reloads

Three repeats at temperature zero, three separate settings (prob.txt H1-H3): seeded, seedless and single token. In all three, the token sequence and the logprob values returned **bit-identical**. The "verbatim identity at T=0" measured in arm A of the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page holds here too; moreover the identity exists not just in text but in the fractional numbers.

But when the model was dropped with `keep_alive: 0` and the same prompt resent (H4):

- the cold first request took **6.68 s**, the next two warm ones 1.38 and 1.37 s;
- the generated tokens were again verbatim identical;
- the logprobs weren't the same: **the biggest absolute gap 0.2286**, the first gap on the `i` token.

A numerically different gap was also seen between two separate runs on the same question: on the same question `P(C)` was 0.9634 in the `kontrol-b.txt` run, 0.9613 in the `olcum.txt` run. No discriminating arm was written for the shift's cause (the summation path, the cache state, machine load); **the cause wasn't measured**. Two conclusions: do the threshold calibration in a fixed loading state, and don't compare logprobs taken from different sessions to their decimal place.

## Turkish, the Schema and the Twenty-Candidate Ceiling: Three Situations That Break Reading the Probability

**Sub-word splitting.** The Qwen interface chops Turkish syllable by syllable: "Marmaray" enters the logprob as `M` `arm` `ar` `ay`, "2013" as `2` `0` `1` `3`. The first token's candidates are `M` 0.9668 / `1` 0.0113 / `İ` 0.0075 / `I` 0.0044 — i.e. the model decides whether it will say "Marmaray", "1913" or "Istanbul" in the first syllable. The standalone probability of a Turkish letter was also measured (A9): `I` 0.5014, `İ` 0.1418, `H` 0.0525. Together with the punctuation marks, this makes **a single-token golden answer impossible in Turkish**; this rig's multiple-choice design asks for a letter for that reason.

**Constrained generation shapes the distribution.** In the `format: "json"` and JSON schema conditions the first position's top candidate is nearly fixed: `'{\n'` 0.9969 (A7) and 0.9975 (A8). While the same question in free style says "2013", in the two-field JSON form the model produced `"yil": 2022`. **We're not writing this to the `format` field alone**: the two prompts' words also differed, so the variable wasn't single. Still, the reading is this — the schema puts nearly all the first token's probability on the structure character; in this case "the structure's probability" and "the content's accuracy" are separate things.

**The tail isn't visible.** Since `top_logprobs` is capped at 20, entropy can only be computed by re-normalizing those 20 candidates; a tail longer than 20 is never seen. That's why every entropy number on this page is a **lower bound** and was labeled so in the records: `[ALT SINIR]` ([LOWER BOUND]) in `prob.txt`, `kirpik ent` (trimmed entropy) in `olcum.txt`.

## `P(chosen)`: Not the Correct Option's Probability, the Chosen Option's Probability

20 knowledge + 6 "unknowable" questions, four options, the golden option's position rotated by question order, asked for a single letter (`num_predict=1`, T=0, `top_logprobs=20`). Option A's mass was found by collecting the candidates exactly matching `A`, `A)` and `A:`, and re-normalized over the four letters' masses (the P(True) pattern).

This run itself produced a finding about the instrument being broken (`olcum.txt`, the B summary):

| Measured | Value |
| --- | --- |
| The correct option | 6/20 (0.30) |
| The chosen-letter distribution | A 0, B 3, **C 16**, D 1 |
| `P(chosen)` on the correct ones | avg 0.8885 (range 0.6043-1.0000) |
| `P(chosen)` on the wrong ones | avg 0.9253 (range 0.6399-1.0000) |
| The separation margin (worst correct − best wrong) | **−0.3957** |

The model said **C** on 16 of the twenty questions. In this state `P(chosen)` measures not knowledge but positional bias; the script therefore built an invalidity gate, writing into the log that when a single letter takes more than half the votes, the threshold/risk table shouldn't count as a discriminator. We still scanned the threshold, because the number itself is a finding:

| Threshold τ (answer if `P(chosen) ≥ τ`) | Coverage | Risk (error among the covered) |
| --- | --- | --- |
| 0.30 – 0.60 | 1.00 (20/20) | 0.700 |
| 0.70 | 0.85 (17/20) | 0.706 |
| 0.80 – 0.90 | 0.80 (16/20) | 0.750 |
| 0.95 | 0.65 (13/20) | 0.692 |
| 0.99 | 0.45 (9/20) | 0.556 |

Pulling the threshold to 0.99 brings the risk down from 0.700 to 0.556, but coverage falls to nearly half; i.e. on this model, on this question set, the probability threshold **reduces the error only if you're willing to give fewer than half the answers**.

:::caution[Don't build the threshold on the golden label]
The log's `P(golden)` lines were written separately with the `[analysis]` tag: on the correct ones avg 0.8885, on the wrong ones avg 0.0044. That means "the model sees the probability of the option it got wrong as nearly zero" — but since you don't know the golden label at inference time, that number can't set a threshold. The threshold is **always scanned over the chosen answer's probability**; scanning over the golden leaks the label and produces a self-serving result.
:::

**The unknowable questions.** Six questions' golden option was "None / I don't know". In two the model really chose that option; in four it chose a known thing and the mass wasn't bad: 0.5367, 0.8617, 0.9707, 0.8087. So abstention behavior doesn't come spontaneously in this model, in this form.

## Temperature Doesn't Change the Reported Probability

The same questions were sent three times each at T = 0 / 0.7 / 1.0 with a fixed seed (1234). **The chosen letter didn't change in all ten of the ten questions**; the range of the `P` value across the three temperatures was 0.00000 in nine questions and 0.00001 in one. So the logprob Ollama reports is independent of temperature on this machine: you can't "sharpen" the probabilities by cooling.

:::tip[Don't confuse]
This isn't the inverse of the calibration literature's *temperature scaling* technique — there, temperature is a transformation applied afterwards on the logits and genuinely changes the distribution. What's measured here is: the number Ollama **reports to you** isn't affected by the inference temperature. This measurement doesn't explain at which step it's computed; only that the reporting isn't affected.
:::

## The Average Logprob in Free Answers: The Most Confident Line Was the Wrong Output

The same ten questions' answers were this time requested as the option's text (a 64-token ceiling, T=0). The average logprob spread between −0.4680 and −0.0018; content accuracy was **3/10** (counted from the log: D2, D3, D10). The order was odd:

| Row | Average logprob | Answer | Golden |
| --- | --- | --- | --- |
| D10 | −0.0018 | `B) $0.07/GB-month` | `$0.07/GB-month` — correct |
| D9 | −0.0028 | `C) 88.838` | `37` — **wrong** |
| D4 | −0.0706 | "bge-m3 produces a 768-dimensional vector" | `1024` — **wrong** |

−0.0028 means roughly **0.997**; the model gave the wrong answer with near certainty. In D4 too it said the wrong size with the same certainty. On the other hand, the trimmed entropy worked here: while D9's entropy average was 0.0173 (max 0.0792), the long and rambling D3's was 0.8391 (max 2.7541). The sequence's logprob measures **self-confidence**, not accuracy.

## Self-Consistency and Semantic Entropy: When No Variety Comes Out, No Entropy Comes Out Either

Ten samples per question, T=0.8 (`olcum.txt`, arm E's summary; the 100-line raw choice dump sits in the log): **agreement was 1.00 in all ten of the ten questions** — 80 of the hundred choices were C, 20 were B, none A or D. The majority option was correct in three questions. So sampling noise produced no variety on this task; the literature's remedy of "sample the same question ten times" didn't work on a task squeezed into a single letter with a letter bias.

The hundred answers collected in the free-text arm were clustered with bge-m3 vectors. At a cosine threshold of 0.70 the cluster count averaged 1.90 (at most 5), the semantic entropy averaged 0.3290; at 0.80, 2.20 (at most 7) and 0.4426. **In six of the ten questions a single cluster** came out, i.e. the semantic entropy was zero. The method deviates from the original recipe in two places, and the deviation sits in the record: the original definition wants bidirectional entailment (NLI), cosine was used here; greedy clustering compares against the cluster's **first** example, not the average. When the threshold changed 0.70→0.80, the cluster count in the same answer set went 2→3 and 5→7 — the cluster count itself is a threshold-sensitive number.

:::caution[Noise inflates the cluster count]
Two examples were the "instruction echo" texts coming from the model repeating the prompt. On that question (F2) there were 5 clusters at 0.70 and 7 at 0.80; the echo wasn't cleaned, was counted in the log as `instruction echo 2`, and left. When building automatic abstention thresholds, this artifact looks like real variety.
:::

## The Verbally Stated Confidence: With No Label, the Number Is Meaningless

In the first run we asked the model for a number between 0-100 under the answer. The model mostly produced the number by **echoing the instruction**; and the parser took the first number on the last empty line. The result looks like this in the record (`olcum.txt`, block G):

```text
G2  |  3.97 s | confidence 1  | answer right? NO | 'A) 128.256 /  / a single whole number between 1 and 100: 50'
G9  |  4.25 s | confidence 88 | answer right? NO | 'C) 88.838 /  / This corpus's Turkish part is 88.838-message Turkish'
```

The number the model **meant** was 50, but the "1" at the line's start was read by the parser as the confidence. G9 has a similar ambiguity: the read 88 collides with the `88.838` number in the answer text; which number it came from can't be told from this log. That's why arm G's parser was fixed to read only the number arriving with the `CONFIDENCE:` tag and the arm was re-run (`g2.txt`). The new measurement:

- In **7/10 questions** the label arrived; in 3 it didn't and **didn't enter** the averages (fail-closed).
- The read confidences averaged 53.7 (a 0-88 range).
- On the wrong answers the confidences were 26, 85, 85, 0, 88, 7 (avg 48.5); **on the single correct answer 85** (n=1).

In this state, verbal confidence is unusable on this machine: 3 of 10 questions unreadable, and among the readable ones the model gives 85-88 to wrong answers, and the correct answer's single example is also 85. So wrong and right don't separate in the stated number either — the measurement of the behavior the literature calls "overconfidence" on this model. The "average 16.2" figure obtained with the first (broken) tool **is invalid and was used nowhere**.

## What's Done Today

- **If you want a confidence signal, start with `P(chosen)`**, not `P(golden)`; scan the threshold on your own data. This rig's τ scan was measured on 20 questions, one model, a set with hand-written goldens — the number coming out of that isn't your application's threshold.
- Ask for the **option's text** rather than its letter, and match the text with digit/period boundaries (`8` as a golden produces a false positive inside `128`); in the letter design measure and report positional bias separately.
- **Divide the average logprob by the record count**, not `eval_count`.
- **Report entropy as a lower bound**; `top_logprobs` is capped at 20.
- **Build abstention with behavior**, not probability: show the model the "I don't know" option explicitly and measure the rate of choosing it (here 2/6).
- Do the measurement **in the same loading state**; the cold/warm difference can shift the logprob by 0.2286.

## Not Measured

- The full vocabulary entropy (unreachable, since the `top_logprobs` ceiling is 20).
- Confidence behavior on a quantized model: the Q4 vs Q8/Q16 comparison needs a new download, absent from this footprint; see [Quantization](/en/kullanim/quantization/).
- **ECE, confidence intervals and the temperature-scaling fit.** No confidence interval was computed for N=20 and N=6; every ratio on this page is a point estimate. The study showing the ECE estimator misleads on small samples sits in the records (Sources below).
- How calibration changes when context (RAG) is given, the `P` comparison in the chain-of-thought condition, using a confidence threshold in the agent loop. How the threshold **invalidates when carried to another dataset** is measured on the similarity side: [RAG Evaluation](/en/rag/rag-degerlendirme/).
- Which side the gap of 1 between `eval_count` and the logprob record comes from.

## Sources and further reading

- [The Ollama Chat API reference](https://docs.ollama.com/api/chat/) — the body shape of the `logprobs`, `top_logprobs`, `format` fields (last verified 2026-10-17).
- [On Calibration of Modern Neural Networks (arXiv:1706.04599)](https://arxiv.org/abs/1706.04599) — Guo et al., ICML 2017; the ECE definition and the later temperature scaling.
- [Language Models (Mostly) Know What They Know (arXiv:2207.05221)](https://arxiv.org/abs/2207.05221) — Kadavath et al.; the source of the P(True) pattern normalizing the correct option's probability over the others.
- [Self-Consistency Improves Chain of Thought Reasoning (arXiv:2203.11171)](https://arxiv.org/abs/2203.11171) — Wang et al.; sampling the same question many times and taking the majority, arm E on this page.
- [Semantic Uncertainty (arXiv:2302.09664)](https://arxiv.org/abs/2302.09664) — Kuhn et al.; meaning-level entropy. Published in Nature 2024, vol 630, pages 625-630.
- [Just Ask for Calibration (arXiv:2305.14975)](https://arxiv.org/abs/2305.14975) — Tian et al., EMNLP 2023; asking aligned models for verbal confidence halving the ECE. Arm G here tests its "ask" part, not its ECE part.
- [Can LLMs Express Their Uncertainty? (arXiv:2306.13063)](https://arxiv.org/abs/2306.13063) — Xiong et al.; overconfidence in verbal statements and scale traps.
- [Know Your Limits: A Survey of Abstention in Large Language Models (arXiv:2407.18418)](https://arxiv.org/abs/2407.18418) — Wen et al., TACL 2025; the classification of the routes by which abstention is achieved.
- [When Quantization Affects Confidence of Large Language Models? (arXiv:2405.00632)](https://arxiv.org/abs/2405.00632) — Proskurina et al.; quantization shifting the confidence distribution — **not measured** on this page.
- [Verified Uncertainty Calibration (arXiv:1909.10155)](https://arxiv.org/abs/1909.10155) — Kumar, Liang and Ma, NeurIPS 2019; why the ECE estimator misleads (measures biasedly) on small samples.
- [Inference Parameters](/en/kullanim/cikarim-parametreleri/) — the doc side of the `logprobs` field and the "not tried" note this page closed.
- [Reproducibility](/en/kullanim/tekrarlanabilirlik/) — T=0 identity, the `num_predict` ceiling and the schema/content split; the complement of this page's H and A7-A8 rows.
- [Tokenization](/en/temeller/tokenizasyon/) — the language of Turkish's sub-word splitting.
- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — this rig's unit cost: a `num_predict=1` + `top_logprobs=20` request with a fresh ~100-token prompt takes 2.1-2.9 s, and 0.10-0.15 s with the cache warm on the same prompt.
