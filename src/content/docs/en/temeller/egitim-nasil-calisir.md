---
title: "How Does Training Work? An Intuitive Tour"
description: "Predict, measure loss, find the culprits, update weights: the five-step loop of model training, the optimizer, learning-rate schedules, scaling aids like mixed precision, the difference between memorization and learning, and why data quality is everything."
dogrulama: 2026-11-20
---

"Training a model" sounds mysterious, but at its core it is a single loop repeated millions of times: predict, measure the error, find who is responsible for the error, adjust a little, repeat. This page opens up that loop with everyday analogies — and by the end you will see that the same loop is everywhere, from LLMs to image generation models to classic machine learning.

## The Five-Step Loop of Learning

Think of a student who makes a mistake in an exam and corrects it. Training a model is exactly what that student does:

### Step 1: Predict

The model reads a training example and produces its prediction. In an LLM this prediction is "what should the next token be?"; in classic ML it is "what is the price of this house?". At the start the predictions are nearly random — the weights are initialized with random numbers. **Analogy:** the student walking into their first practice exam without ever studying.

### Step 2: Measure the error

The model's prediction is compared with the true answer, and the difference is condensed into **a single number**: the loss. **Analogy:** the teacher grading the exam. "You got 78" alone is not enough information, but it is the most practical way to measure progress.

### Step 3: Find who is responsible for the error

Of the billions of parameters, which contributed how much to this error? The answer is found with one of mathematics' most elegant tools: **backpropagation**. Using the chain rule, each weight's "share" of the error in the loss is computed. This share, attached to each weight, is called the **gradient**. **Analogy:** the teacher not just saying "wrong" but writing "one third of this error comes from the multiplication table, the rest from carelessness".

A gradient is a direction and a magnitude: it says "if you **increase** this weight a little, the loss **decreases** by that much".

### Step 4: Adjust the weights a little

The model updates every weight with a small step in the direction opposite to what the gradients point: **gradient descent**. The size of the step is set by the **learning rate**:

- Too large: the model oscillates, and instead of dropping, the loss jumps. **Analogy:** a student who radically changes their study method every day after seeing a mistake.
- Too small: progress moves at turtle speed and training takes hours.
- Typical values in LoRA fine-tuning are between 1e-4 and 2e-4; the detailed tuning guide: [Hyperparameters](/en/llm/hiperparametreler/).

### Step 5: Repeat

This loop runs not for a single example but for millions of examples. In the first rounds the loss drops steeply, then keeps decreasing. Training is the sum of millions of "small adjustments".

```text title="The training loop — pseudocode"
for each batch (group of examples) in training_data:
    prediction = model(batch)             # 1. Predict
    loss       = measure_error(prediction, truth)  # 2. Measure the error
    gradients  = backpropagate(loss)      # 3. Find the culprits
    weights   -= learning_rate * gradients  # 4. Adjust a little
# 5. Repeat until all the data is used up
```

## The Optimizer: Who Does "Adjust a Little" Better?

The fourth line of the pseudocode above shows **gradient descent** in its plainest form: every weight is updated by exactly the learning rate. In real training there is a key staff member who does this update more intelligently: the **optimizer**.

Today's de facto standard in LLM training is **AdamW**, a refined form of Adam. Adam (Kingma & Ba, 2014) keeps two "running averages" of the gradients for every parameter: the average of recent gradients (**momentum** — "which direction are we heading?") and the average of their squares (**second moment** — "how big are this weight's gradients generally?"). Combining these two statistics, it computes a **unique** step size per parameter. **Analogy:** a coach who keeps separate notes for each subject — if math errors keep coming in big, it shrinks the steps in that subject on its own; if history errors are small, it boldly enlarges them. Plain gradient descent measures every subject with the same ruler.

AdamW's (Loshchilov & Hutter, 2017) contribution is the correction of **weight decay**. The classic approach (the L2 penalty) mixes the shrinking request into the gradient signal; Adam's adaptive scaling corrupts this mixture and the penalty loses its effect on weights with large gradients. AdamW separates the two: the gradient signal works as is; on top of it, weights are slightly shrunk at every step independently of the optimizer. **Analogy:** instead of attaching "I wish this were shorter" notes to the student's answers, regularly shortening each answer on its own — the feedback channel and the discipline channel are separate. The paper shows in various tasks that this separation improves generalization; PyTorch exposes the class directly as `torch.optim.AdamW`. No code example needed: most tools like Trainer and TRL set this up on your behalf; don't be surprised if you see its name in a log output one day.

One of the reasons for **warmup**, which you will see in the "The Learning Rate Is Not Constant" section below, is right here: the momentum and second-moment statistics have not "warmed up" in the first steps; the steps computed in this period can swing excessively.

## Loss: The Error Expressed in a Single Number

The standard loss measure in language models is **cross-entropy**. The intuition: if the model gave high probability to the correct token, the loss is low; if it gave low probability, the loss is high. A numeric example:

- A model giving 0.9 probability to the correct token has a loss of: −log(0.9) ≈ **0.11** → close to perfect.
- A model giving 0.1 probability has a loss of: −log(0.1) ≈ **2.3** → bad.

You watch the loss curve throughout training. In a typical LoRA run, starting at 3.2 and coming down to around 1.4 is the sign of "going well"; if the loss has stopped decreasing, there is nothing left to learn or something has gone wrong. The detailed reading of loss and metrics — perplexity included — is on the [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) page.

:::note[Reading the loss curve alone misleads]
Loss going down does not mean everything is fine; the model may be memorizing. To understand this you also need to watch the **validation loss** — in a moment.
:::

## Batch, Step and Epoch: Passing Over the Data

Three terms get mixed up; let's clarify once:

- **Batch:** the group of examples processed at once. Why not all at once? Because the entire dataset does not fit in GPU memory at the same time.
- **Step:** **one** weight update made with one batch of data.
- **Epoch:** one pass over the **entirety** of the training set.

Quick math: say 10,000 examples, batch size 8.

```text title="Step and epoch math"
10,000 examples ÷ 8 examples/batch = 1,250 steps/epoch
3 epochs  →  3 × 1,250 = 3,750 total steps
```

:::tip[The 4 GB VRAM trick: gradient accumulation]
If your card can't take more than batch 2, use **gradient accumulation**: accumulate the gradients of 8 small batches and make a single update. The result behaves like an effective batch of 16 — you gain stability without giving up memory. The setting: [Hyperparameters](/en/llm/hiperparametreler/).
:::

In LLM fine-tuning the epoch count is usually 1-3; in classic ML it can go up to hundreds of rounds. Shuffling the data at every epoch makes memorization harder.

## Memorization or Learning? Overfitting and Underfitting

The model's goal is not to **memorize** the training data but to **generalize** the patterns in it. There are two extreme errors:

- **Overfitting:** the model memorizes the training examples together with their answers. The training loss looks magnificent but collapses on new data. **Analogy:** a student who memorized the exact exam and fails on a similar question. The typical symptom in LLM fine-tuning: the model repeats your own training examples verbatim and goes haywire on small variations of the questions.
- **Underfitting:** the model has learned nothing; even the training loss stays high. Usually the sign of insufficient data, a too-low learning rate, or too few epochs.

How do we catch it? We split the data in two: the **training set** and the **validation set** (typically 5-10%). The model never sees the validation set; it is kept aside only for the "exam". In a healthy training run, both losses fall. If the **validation loss stops falling and starts rising** while the training loss is dropping, memorization has begun — early stopping kicks in: the checkpoint at that point is the best one.

:::caution[In LLMs the validation loss is noisy]
In a LoRA run with 1,000 examples the validation set is 30-50 examples; the curve is zigzagged, don't panic at a single rise. To pick the best checkpoint, look at the trend and test output quality by hand: [Evaluation](/en/degerlendirme/loss-ve-metrikler/).
:::

## Loss Curve Shapes: A Quick Diagnosis Table

The most common scenes you'll meet while watching training losses and what they mean:

| Curve appearance | Likely situation | What to do |
| --- | --- | --- |
| Training and validation loss falling together | Healthy training | Continue |
| Training falling, validation rising | Overfitting | Stop early; augment data; reduce the LoRA rank or epochs |
| Validation loss zigzagging but trending downward | Learning rate a bit high, or the validation set too small | Don't panic, watch the trend; try lowering the rate one notch |
| Both high and nearly flat | Underfitting | Raise the learning rate, add epochs, check the data and labels |
| Loss spiking or going NaN | Learning rate way too high | Lower the rate 5-10x; use gradient clipping |
| Loss looks fine but outputs are broken | Data format / chat template mismatch | Check the template and data format: [Tokenization](/en/temeller/tokenizasyon/), [SFT](/en/llm/sft/) |

## The Learning Rate Is Not Constant: Warmup and Decay

In modern training the learning rate is usually not held constant; it follows a **schedule**. The two most common patterns:

- **Warmup + linear decay:** in the first part of training the rate rises from zero to its peak in a straight line, then descends step by step to zero.
- **Warmup + cosine decay:** after warmup the rate falls along a half-cosine curve — fast at first, gently at the end. This pattern comes from the SGDR paper (Loshchilov & Hutter) and is the beloved schedule of the LLM world.

So why is warmup needed? Two reasons:

1. At the beginning the weights are random; the first gradients are both noisy and large. Big steps can shake apart a model that has barely started learning — the transformers docs recommend warmup to "keep the early phase of training balanced".
2. The optimizer statistics from the previous section (momentum and second moment) have not warmed up in the first steps; step sizes computed in this period can swing problematically. The RAdam paper measured this and counted warmup as a "variance reduction technique".

**Analogy:** don't tell a student whose practice-exam results haven't arrived yet to "radically change your method" in the first week; start with small trials, enlarge the steps once you see where things are going — and as the exam (the end of training) approaches, shrink the changes and let things settle. The reason for decay is also at the end: while the loss wanders around the minimum, large steps keep "jumping"; as the rate falls, the model settles gently into the minimum.

:::caution[transformers v5 has no `warmup_ratio`]
The `warmup_ratio` parameter was removed in v5; TrainingArguments now also accepts a decimal ratio in the `warmup_steps` field — a float between 0 and 1, interpreted as a ratio of total steps. The `warmup_ratio=0.03` from old examples is written today as:

```python title="Learning rate schedule (transformers v5)"
args = TrainingArguments(
    learning_rate=2e-4,          # with a schedule, this is the "peak" value
    lr_scheduler_type="cosine",  # decay with cosine after warmup
    warmup_steps=0.03,           # warmup for 3% of total steps
)
```
:::

At the PyTorch level the same schedules live in the `torch.optim.lr_scheduler` module (`LambdaLR`, `OneCycleLR` and friends); if you use the Trainer you don't need to wire them by hand. In small LoRA jobs most tools apply a cosine schedule with a short warmup by default; a constant rate is also common. All schedule options: [Hyperparameters](/en/llm/hiperparametreler/).

## Three Aids That Kick In as Scale Grows

The loop we've described so far is a single weight update. In real training you need to run this loop thousands of times on limited VRAM; three standard aids make your life easier exactly at that point — each saves on a different resource: compute precision, memory and step size.

### Mixed precision

Weights and computations run in 32-bit floating point (fp32) by default. Mixed precision brings most of the computation down to 16 bits: you gain speed and memory, and the result stays largely the same. There are two 16-bit formats and the difference between them matters:

- **fp16:** the exponent range is narrow; the small gradients of backpropagation can fall below this range and vanish. The fix is **loss scaling**: the loss is multiplied by a large coefficient so the gradients stay in a measurable range; when the operation finishes, the scale is removed. In fp16 this scaling is mandatory — PyTorch's `GradScaler` does exactly this.
- **bf16:** preserves fp32's exponent range; small gradients are not lost and no scaling is needed. The transformers docs explicitly state they prefer bf16 over fp16 for "better numerical stability and no scaling requirement". The price: your card must support this format in hardware — on the NVIDIA side, the Ampere generation and later (RTX 30 series and up).

**Analogy:** reducing your calculator's digit count from 32 to 16: ordinary multiplications don't care, but very small numbers show up as zero on the screen. That's why with fp16 you must carry a "magnifying glass" (scaling) with you; bf16's lower range is wide enough that no magnifying glass is needed.

The Trainer equivalent is a single field: `bf16=True`.

### Gradient accumulation

The official counterpart of the "4 GB VRAM trick" box above. The idea: process micro-batches back to back, accumulate the gradients in memory, and update the weights only after a certain number of examples. The formula:

```text title="Effective batch"
effective batch = micro batch × accumulation steps   (multi-GPU: × GPU count)
```

For example 4 micro-batch × 8 accumulation steps = effective batch 32; but no more than the 4-example micro-batch is held in GPU memory. Nothing changes in the five-step loop; only step 4 (the update) comes less often and is made with the average of the accumulated gradients. Trainer equivalent: `gradient_accumulation_steps`.

### Gradient checkpointing

Backpropagation needs the intermediate results (activations) of the forward pass, and storing every layer's activations is one of VRAM's biggest consumers. The checkpointing idea: instead of storing them all, store only a few checkpoints and recompute the in-betweens during the backward pass. You give up memory and pay in compute: the transformers docs document this with a "slowdown of up to ~20%" note. **Analogy:** instead of carrying the complete lecture notes in your bag, carry only the section headings; during the backward pass you re-read the section and rewrite the notes — the bag gets lighter, the time gets longer. Trainer equivalent: `gradient_checkpointing=True`.

The three aids in TrainingArguments at a glance:

```python title="Three aids, three fields"
args = TrainingArguments(
    bf16=True,                      # mixed precision (bf16 must be supported by hardware)
    gradient_accumulation_steps=8,  # update once per 8 micro-batches
    gradient_checkpointing=True,    # skip activations, recompute in the backward pass
)
```

These three aids work together with model-side quantization (QLoRA): [LoRA and QLoRA](/en/llm/lora-qlora/).

## What Determines Training Time?

Time is proportional to the product of three quantities: **total tokens processed × model size × hardware speed**. Practical inferences:

- 2,000 examples × average 500 tokens = about 1 million tokens processed; with batch 8 that's ~250 steps/epoch.
- On the same data a 4B model is clearly faster than an 8B; LoRA is an order of magnitude faster than training all parameters, because gradients are computed only for the small adapter.
- General expectation: with 1,000-5,000 examples a typical QLoRA run takes **30 minutes to 6 hours** depending on hardware (upper end on local 6-12 GB cards, lower end on a rented 4090-class card).

The screws you turn by hand — batch size, accumulation steps, epochs, schedule — directly change the step count; the full list of these screws and recommended values: [Hyperparameters](/en/llm/hiperparametreler/).

:::tip[Set up a fast trial loop]
In the first round use a small slice of the data (e.g. 10%) and 1 epoch; confirm everything works. Test setting changes this way quickly, and save the full training for last.
:::

## Why Is Data Quality Everything?

Classically put: "garbage in, garbage out": if the training data is full of inconsistent labels, typos or duplicate examples, the model learns that inconsistency. Meta's 2023 **LIMA** study is the proof: the researchers showed that fine-tuning done with only **1,000 carefully selected** instruction-answer examples could compete with trainings done on much larger but noisier datasets. The interpretation: most of the knowledge is already there from pretraining; fine-tuning's job is to teach **behavior and format**, and that happens through example quality.

What does this mean in practice?

- 1,000 clean, consistent examples can beat 100,000 noisy ones.
- Contradictory answers to the same question confuse the model. Above all: **consistency**.
- Duplicate examples inflate the memorization risk; clean up repeats.
- Answers should be in the style and length you want — the model imitates what it sees.

Data preparation processes: [Data Cleaning](/en/veri/veri-temizleme/) and [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).

:::tip[Start small, then scale]
Do your first training with 30-50 examples and confirm the pipeline works end to end; then go to 1,000-5,000 examples. Starting directly with 50,000 examples is the surest way to notice the error hours later.
:::

## The Same Loop Everywhere

The five-step loop described on this page is universal:

- **In LLM fine-tuning:** the next token is predicted at every batch, the cross-entropy loss is computed; in LoRA only the small adapter matrices are updated: [SFT](/en/llm/sft/), [LoRA and QLoRA](/en/llm/lora-qlora/).
- **In image models:** diffusion models learn to predict the noise added to an image — again predict, measure, correct. The concepts hiding underneath: [Diffusion Fundamentals](/en/gorsel/diffusion-temelleri/).
- **In classic machine learning:** `model.fit(X, y)` is one line, but the same gradient descent runs underneath; the loss curves tell the same story here too: [Classic ML Fundamentals](/en/klasik-ml/temeller/), [Your First Model](/en/klasik-ml/ilk-model/).
- **In preference training:** DPO and RLHF are also derivatives of the same loop — which of two answers the model prefers is turned into a loss and processed with predict, measure, correct: [DPO and RLHF](/en/llm/dpo-rlhf/).
- **In pretraining from scratch:** the same loop, this time with billions of tokens: [Pretraining](/en/llm/pretraining/).

:::tip[Next step]
To learn to read loss curves professionally, move to the [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) page; to dig into the details of training settings (learning rate, batch, LoRA rank), [Hyperparameters](/en/llm/hiperparametreler/). Enough theory; [Step-by-Step Training](/en/llm/adim-adim-egitim/) awaits you for the first real run.
:::

## Sources and Further Reading

Primary sources used while writing this page:

- [Adam: A Method for Stochastic optimization (arXiv:1412.6980)](https://arxiv.org/abs/1412.6980) — Kingma & Ba's 2014 paper; the origin of the per-parameter adaptive step idea.
- [Decoupled Weight Decay Regularization (arXiv:1711.05101)](https://arxiv.org/abs/1711.05101) — the AdamW paper; shows that separating weight decay from the gradient improves generalization.
- [SGDR: Stochastic Gradient Descent with Warm Restarts (arXiv:1608.03983)](https://arxiv.org/abs/1608.03983) — the paper proposing the cosine schedule and warm restarts.
- [On the Variance of the Adaptive Learning Rate and Beyond (arXiv:1908.03265)](https://arxiv.org/abs/1908.03265) — the RAdam paper; initial variance in adaptive optimizers and why warmup works.
- [Transformers Trainer and TrainingArguments docs](https://huggingface.co/docs/transformers/main_classes/trainer) — the official reference for every field on this page (`warmup_steps`, `bf16`, `gradient_accumulation_steps`, `gradient_checkpointing`).
- [PyTorch torch.optim.AdamW docs](https://docs.pytorch.org/docs/stable/generated/torch.optim.AdamW.html) — AdamW's "decoupled weight decay" implementation itself.
- [PyTorch OneCycleLR docs](https://docs.pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.OneCycleLR.html) — an example of schedules at the PyTorch level.
