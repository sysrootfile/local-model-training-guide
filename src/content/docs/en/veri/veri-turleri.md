---
title: "Data Types: Which Training Wants Which Data?"
description: "From pretraining to instruction tuning, from DPO to image model training: learn which data type each method wants, in which format and how much, with examples."
dogrulama: 2026-11-20
---

> **"The model is the mirror of its data."**

Whatever you give a model, it learns: give it crude data and you get crude results; give it careful data and you get careful results. But "data" is not one thing; raw text, question-answer pairs, "good/bad answer" comparisons, a table row and a photo don't go in the same basket. **Which training you want to do determines which data you will collect.** This page is a map for setting up that match.

## Which Training, Which Data?

| Training type | Data it wants | Typical format | Typical amount |
| --- | --- | --- | --- |
| Pretraining | Raw text: books, web, code | Plain text / parquet | Billions of tokens |
| Continued pretraining | Domain text: law, medicine, company documents | Plain text | 1-100 million tokens |
| Instruction tuning (SFT) | Question-answer / task-solution pairs | JSONL (Alpaca etc.) | 1K-100K examples |
| Preference optimization (DPO/RLHF) | Preference pairs: good + bad answer to the same question | JSONL | 1K-50K examples |
| Image model training | Image + caption(s) | Folder + mapping file (json/csv) | 10-10,000 images |
| Classic machine learning | Row = example, column = feature table | CSV / parquet | Hundreds to millions of rows |
| Evaluation (eval) | Held-out question set: exam questions you write yourself | JSONL / list | 20-200+ questions; never mixed into training |

### Pretraining

The stage where the model learns language itself; the rawest and largest data. Pretraining from scratch rarely makes sense in your own project — "continuing" an existing model with 1-100 million tokens of domain data is almost always smarter. Details: [Pretraining](/en/llm/pretraining/).

### Instruction Tuning (SFT)

It gives the model the behavior "answer when asked"; the type you will use most on this site. The data is question-answer pairs reflecting your real usage scenarios. Training: the [SFT Guide](/en/llm/sft/). Format examples: [Data Formats](/en/veri/veri-formatlari/).

### Preference Optimization (DPO/RLHF)

You give "good answer / bad answer" pairs for the same question and train the model's sense of preference. Example:

```json title="preference_example.jsonl"
{
  "prompt": "How should I handle a customer's return request?",
  "chosen": "I've received your return request; if you share your order number I can start the process right away.",
  "rejected": "You can review our return conditions on our website."
}
```

Details: [DPO and RLHF](/en/llm/dpo-rlhf/).

### Image Model Training

Diffusion models and vision-language models need image-caption mapping; usually a folder of images plus a mapping file:

```csv title="image_mapping.csv"
file, caption
product_001.jpg, "red leather women's bag, front view, white background"
product_002.jpg, "navy men's shirt, straight cut, mannequin"
```

Target pages: [Diffusion Fundamentals](/en/gorsel/diffusion-temelleri/), [Image LoRA Training](/en/gorsel/lora-egitimi/).

### Classic Machine Learning

Here the data is a table with one example per row and one feature per column: "square meters, room count, location, price" for real estate price prediction. No text/image processing; jobs like imputing missing values and scaling start here: [Classic ML Fundamentals](/en/klasik-ml/temeller/), [Your First Model](/en/klasik-ml/ilk-model/).

:::note
The "typical amount" values in the table are a realistic **starting range**, not a threshold. The unit of the amounts is "tokens" or "examples"; for a token refresher: [Tokenization](/en/temeller/tokenizasyon/). Turkish text generally spends **more tokens** than English for the same content; measure "1 GB of text is this many tokens" guesses with your own tokenizer.
:::

### Roughly Estimating the Data Amount

An "epoch" is seeing all the examples once. The total workload comes out of this simple formula:

```text
total tokens ≈ number of examples × average tokens per example × number of epochs
```

Example: you have 2,000 question-answer examples with an average of ~500 tokens per example → 1 epoch ≈ 1 million tokens; 3 epochs ≈ 3 million tokens. This number is your fuel gauge: training time, cloud cost and the "is this data enough?" decision all come out of here.

## How Much Repetition Is Acceptable?

When data is scarce, the first idea is to show the same data over more epochs. There is a region where repetition works; but it is not unlimited.

:::note
**Research finding:** "Scaling Data-Constrained Language Models" (Muennighoff et al., 2023) showed in pretraining experiments that **repetition up to ~4 epochs** gave nearly the same loss as fresh data; past that point, the value of a repeated token decreases a little every round — diminishing returns kick in. Source: [arXiv:2305.16264](https://arxiv.org/abs/2305.16264).
:::

- **For pretraining and continued pretraining:** repeating your corpus for a few epochs is normal; in practice the "acceptable" region goes up to ~4 epochs. Beyond that isn't forbidden, but each extra round's contribution shrinks; the "more repetition = more knowledge" assumption becomes invalid.
- **In SFT the threshold drops noticeably:** because instruction data is small and the examples resemble each other, repetition quickly turns into memorization; the typical safe range is **1-3 epochs**, and 5+ epochs carries memorization risk (details: the [SFT Guide](/en/llm/sft/), [Hyperparameters](/en/llm/hiperparametreler/)). The way to raise quality in SFT is not raising epochs but improving example quality and variety.
- **Invisible repetition:** besides exact copies, "nearly identical" examples also count as effective repetition; even in 1 epoch, if the set contains twin examples, the model sees some content several times. Pick out near-duplicates before training: [Data Cleaning](/en/veri/veri-temizleme/).
- **Relation to the "typical amount" ranges in the table above:** if your amount is inside the table's range, you generally don't need to re-read the data; if you're below the range, some compensation with repetition is possible. But repetition never fully substitutes for fresh data: showing a small number of examples dozens of times doesn't teach, it memorizes.

## Mixture: Combining Multiple Data Types

In real projects a single data type is rarely enough; what the model must learn at the same time is varied: question-answering behavior, domain knowledge, desired format, style. That's why the training set is usually set up as a **mixture**, and two things become hyperparameters:

1. **Task variety:** which task types will be represented in the set?
2. **Ratios:** how many examples of each task type will go in?

An open recipe example: the **TÜLU 3** post-training recipe combines curated (carefully selected) data, synthetic data, preference (DPO) data and verifiable-reward reinforcement learning (RLVR) data in a single mixture, and explains in detail how the mixture is built and refined ([arXiv:2411.15124](https://arxiv.org/abs/2411.15124)). So "how much of which task?" is not an intuitive list but a design decision measured with experiments.

A practical starting guide (there is no universal ratio; ratio choice is validated with experiments on your own data):

- **Mirror the real usage distribution:** the mixture weights should resemble how often the model will meet each task in deployment; the most frequently used task gets the most examples.
- **Deliberately weight the under-represented task:** a rare but important task, left to its natural frequency, stays in the shadow of dominant tasks and its behavior doesn't get learned.
- **Choose the ratios by measuring:** the "right mixture" isn't known in advance; run comparison runs with differently-ratios small versions and don't decide without measuring on a held-out set. The measurement side: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/), [Benchmarks](/en/degerlendirme/benchmarklar/).

Where to find the components: [Where to Find Data?](/en/veri/veri-nereden-bulunur/). If you want to fill a gap in the mixture with synthetic generation, see the "Synthetic Data" section above and the [Create Your Own Dataset](/en/veri/kendi-verini-olustur/) page.

## Quality or Quantity? (Short answer: Quality)

- **The LIMA finding:** Meta's [LIMA study](https://arxiv.org/abs/2305.11206) showed that instruction tuning done with only ~1,000 carefully chosen examples could compete with tens of thousands of haphazardly collected ones. Few but good is often better than many but careless.
- **Garbage in, garbage out:** the model learns the data's average and its errors. If your dataset contains wrong information, the model repeats it with confidence.
- **Repetition teaches memorization:** if you repeat the same example 100 times, the model memorizes it instead of generalizing; performance drops on a similar but different question. Excessive repetition also shadows the effect of the other examples.
- **Variety:** if everything comes from a single source, the model's perspective is single too; a mix of different sources and styles increases generalization.

:::tip
Rough intuitions (assuming quality, consistent data): a few hundred examples may be enough to teach a **format/behavior**; 500-2,000 to copy a **style**; 2,000-10,000 to process a narrow **knowledge domain**. These are not exact thresholds; observation and evaluation always come first.
:::

## What Does Domain Data Look Like? Three Mini Examples

**1) Customer support FAQs → SFT.** You have three years of support correspondence. From them you extract 300-2,000 real question-answers; each is written to JSONL in the `{"instruction": "...", "output": "..."}` form. In cleaning, copy-paste template answers and "hello/thanks" filler are picked out. The result: a small model answering in your company's style with correct information.

**2) Legal texts → continued pretraining.** 5-50 million tokens of plain text (.txt) from legislation, case law and internal documents. There are two obligations: copyright/license checking and personal data scrubbing. At this stage the model learns the domain's language and style; legal correctness additionally requires careful evaluation.

**3) Product photos → image model.** 100-1,000 product photos and consistent captions for each ("red leather women's bag, front view, white background"). Captions should be written in the same language and a similar template; starting with few photos and growing while observing the result is the healthiest path.

## Getting to Know the Data: 30 Minutes Before Training

Before handing the dataset to training, always walk through it "by hand". Statistics can mislead you; your eyes don't:

1. **Read 20-30 random examples.** Are answers truncated? Did code or template residue get mixed in? Is the tone consistent?
2. **Look at the length distribution.** One giant example makes the average look high and misplans your activation budget.
3. **Encoding check:** are Turkish characters (ş, ğ, ı) correct? Don't use a set showing corruption like "Ã¼nlÃ¼" (mojibake) before fixing it.
4. **Duplication rate:** how many times does the same example appear? A few percent is normal; at percentages of tens, absolutely deduplicate.
5. **Balance:** in classification, how many examples per class; in SFT, which task types dominate?
6. **Source and license trail:** keep which source each example came from in a field; during publishing/demonstration this record becomes priceless.

Tools and practical methods: [Data Cleaning](/en/veri/veri-temizleme/).

## Synthetic Data: When to Use It?

Synthetic data is training examples generated by a strong model; if a small model is being trained to imitate a large one, this is called **distillation**.

**When it makes sense:**

- To multiply real data when it is scarce but representative.
- While converting data to another format/task (e.g. turning FAQs into preference pairs).
- To produce hard and negative examples (the model's typical wrong answers).

**The risks:**

- The teacher model's errors are inherited by the student.
- Data generated with a single prompt style narrows variety; the model learns the generation template, not the real world.
- Bad filtering lays noise over what was learned from real data.

The golden rule: don't add generated data to training without sampling and verifying it by hand. Detailed guide: [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).

:::note
**The Turkish data landscape:** open Turkish data is markedly scarcer than English. That's why for a Turkish model, usually three paths are used together: (1) existing open sets, (2) translating English data, (3) generating your own data. Starting points: the `atasoglu/turkish-instruction-datasets` collection on Hugging Face, `ogulcanaydogan/Turkish-LLM` (a Turkish model trained with QLoRA on Qwen2.5, plus its data), FineWeb-2's Turkish subset, the Turkish Data Depository (a large corpus based on OSCAR + mC4) and `hasankursun/turkish-corpus-100b`. On the evaluation side, the Holmeister Turkish evaluation sets (17 sets for 11 tasks) will do the job. The tidy list: [Where to Find Data?](/en/veri/veri-nereden-bulunur/).
:::

:::danger
**Do not use the same data for both training and testing!** It is expected for the model to score high on the examples it has seen — that is not success, that's memorization. Data leakage makes your evaluation meaningless: you effectively "asked the same questions on the exam". Set the test set aside from the very beginning and don't use it in any training stage (SFT, DPO...). The measurement side: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/), [Benchmarks](/en/degerlendirme/benchmarklar/).
:::

## Which Data Type Do the Common Sources Map To?

- **Hugging Face Datasets:** the first address for all types on this page; thousands of options from SFT sets to image data.
- **Kaggle:** tabular data (classic ML) and ready competition/SFT sets.
- **Wikipedia dumps (trwiki):** clean, license-compatible plain text for continued pretraining.
- **OPUS / Tatoeba:** translation pairs; the raw material for carrying English data into Turkish (can be converted to SFT).
- **The Stack:** a large code corpus for code pretraining (use with a license filter).
- **Common Crawl / FineWeb-2:** web text at pretraining scale; here filtering quality is everything.

Turkish-specific collections and download methods: [Where to Find Data?](/en/veri/veri-nereden-bulunur/).

## Checklist: Before Starting with Data

1. **Which training am I doing?** → Pick the data type from the table above.
2. **What format should it be?** → [Data Formats](/en/veri/veri-formatlari/).
3. **Is it clean enough?** → [Data Cleaning](/en/veri/veri-temizleme/).
4. **Did I set aside the test set?** → Prevent leakage from the very start.
5. **Are license and privacy checks done?** → Copyright in text and images, personal data law (in Turkey, KVKK) for personal data.

## Sources and Further Reading

- [The Chinchilla study: Training Compute-Optimal Large Language Models (arXiv:2203.15556)](https://arxiv.org/abs/2203.15556) — the study showing model size and training token count should scale together, at equal rates; the basic reference for the "how much data is enough?" question.
- [LIMA: Less Is More for Alignment (arXiv:2305.11206)](https://arxiv.org/abs/2305.11206) — the "less is more" study showing a strong instruction follower can be trained with only 1,000 carefully chosen examples.
- [Scaling Data-Constrained Language Models (arXiv:2305.16264)](https://arxiv.org/abs/2305.16264) — the finding that under data constraint, repetition up to ~4 epochs gives results close to fresh data, with diminishing returns beyond.
- [TÜLU 3: Pushing Frontiers in Open Language Model Post-Training (arXiv:2411.15124)](https://arxiv.org/abs/2411.15124) — an open post-training recipe mixing curated, synthetic, preference and verifiable-reward data.

Next up: download your first dataset with the [Where to Find Data?](/en/veri/veri-nereden-bulunur/) page.
