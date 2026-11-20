---
title: "Hyperparameters: The Right Settings Guide"
description: "Every knob of training from learning rate to packing, evidence from a QLoRA sweep, library defaults, copy-paste starting configs and a symptom-fix table."
dogrulama: 2026-11-20
---

Model weights are learned from data; **hyperparameters are the knobs you turn by hand**. The same data and the same model can fail to learn at all with wrong knob settings, yet give perfectly good results with the right ones. This page introduces the knobs one by one; at the end you'll find three ready-made config sets and a symptom-fix table.

:::tip
Don't panic: in reality, **two knobs** are decisive in most projects — the learning rate and the data amount. Leaving the others at a reasonable default and only fiddling when a problem arises is completely normal.
:::

## Learning Rate: The Most Critical Knob

It determines how "big a step" the model takes at each update. Too small and the model doesn't learn (the loss stubbornly stays the same); too large and the model lurches all over the place, the loss can even go NaN.

| Scenario | Typical learning rate |
| --- | --- |
| LoRA / QLoRA | 1e-4 – 2e-4 |
| Full fine-tuning | 1e-5 – 2e-5 |
| DPO | 5e-7 – 1e-6 |
| Pretraining from scratch | 1e-4 – 6e-4 (usually smaller for bigger models) |

Why bigger for LoRA? Because the number of trained parameters is small; bigger steps are needed for the adapter to have an effect. In full fine-tuning all the weights move, so small steps suffice and are safe.

:::caution
When copying a setting, pay attention to **which method it belongs to**: take `2e-4` from a LoRA example and put it into full fine-tuning and the model will most likely break. In DPO, `2e-4` is a disaster; don't start above `5e-7`.
:::

### Evidence: the QLoRA paper's hyperparameter sweep

The bands above come from experience; one of the best-known supports is the QLoRA paper's own sweep (arXiv:2305.14314, Table 9). The paper reports the best LoRA learning rate by model size as follows:

| Model size | Best LoRA learning rate |
| --- | --- |
| 7B and 13B | 2e-4 |
| 33B and 65B | 1e-4 (the learning rate is halved while the batch size is doubled) |

The trend is clear: **as the model grows, the best learning rate drops.** Take these values not as a "law" but as the starting point of a sweep for your own model size. A second note: the "LoRA Learns Less and Forgets Less" study reports that LoRA is **more sensitive** to the learning rate compared to full fine-tuning and benefits from the highest rate that doesn't break stability (arXiv:2405.09673). So an overly conservative lr in LoRA creates a more visible loss than it would in full fine-tuning.

## Learning Rate Timing: Scheduler and Warmup

- **`lr_scheduler_type`:** how the learning rate changes over training. `cosine` is almost always a good default (starts high, descends gently to zero). On short jobs (under half an hour) `linear` is also common. `constant` is simple but usually a notch worse.
- **Warmup (`warmup_steps` in v5, `warmup_ratio` in older versions):** in the first steps of training the learning rate ramps up gradually from zero to its target. The typical value is **0.03 – 0.1** (3-10% of steps). Warmup prevents the early instability of training (loss spikes); if you're getting NaN, this is the first place to look.

### What's a default, what's a tradition?

A commonly confused distinction: `cosine + warmup` appears in almost every guide, but that is a **community tradition**; not the libraries' default.

| Setting | HF Trainer / TRL default | Common tradition |
| --- | --- | --- |
| `lr_scheduler_type` | `"linear"` | `"cosine"` |
| Warmup | None — the default warmup step is 0 | ~3% of steps |
| `learning_rate` | Trainer: 5e-5; TRL SFTConfig: 2e-5 | By method: LoRA 1e-4-2e-4, full fine-tuning 1e-5-2e-5 |

(As of 2026, the transformers and TRL v1.15 defaults. TRL's SFTConfig deliberately keeps a few values different: learning rate 2e-5, gradient checkpointing on, `logging_steps` 10, bf16 on if fp16 isn't set.)

An update note (as of 2026): `warmup_ratio` was deprecated in transformers v5 and fully removed in v5.2; current versions no longer accept it. Its place was taken by `warmup_steps`, and this parameter interprets decimal values below 1 as "a ratio of total steps": for 3% of steps, just write `warmup_steps=0.03` (the same effect as `warmup_ratio=0.03` in pre-v5 code; examples that keep writing the old name error out on the current version).

So why are cosine + 3% warmup so widespread? Because they work well: the learning rate shrinking gently toward the end calms the loss curve, and a small warmup prevents the early instability (loss spikes). So the tradition isn't "wrong", just not the default. Leaving the defaults (linear + no warmup) as they are and trying is also perfectly valid.

## Epochs: How Many Passes Over the Data?

- **1 – 3 epochs** is the typical, safe range.
- 5+ epochs on the same data = memorization (overfitting) risk: while the training loss keeps dropping, the validation loss starts to rise. Details: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).
- As data grows, reducing the epoch count is usually better: 1 epoch with 20,000 examples is often better than 3 epochs with 5,000.

### The step budget and early stopping

Thinking in terms of **optimization steps** instead of epochs makes it easy to compare different data sizes:

```text title="The step budget"
total_steps ≈ epochs × example_count ÷ effective_batch

Example: 5,000 examples, effective batch 8, 2 epochs  →  ~1,250 steps
The same ~1,250 steps equal 1 epoch on 10,000 examples.
```

Early stopping: watch the validation loss with `eval_strategy="steps"`; when the loss stops dropping and starts rising, the best point has passed. To automate it, use `EarlyStoppingCallback(early_stopping_patience=2)` in transformers: together with `metric_for_best_model`, training stops if the tracked metric worsens for the stated number of evaluations. Overfitting (overfitting) symptoms: the **validation loss rising** while the training loss keeps dropping, and the model's answers starting to resemble the memorized examples.

## Batch Size and Gradient Accumulation

- **`per_device_train_batch_size`:** the number of examples each GPU sees in one step. It's VRAM's main enemy; the first knob to turn down when you get OOM (out of memory).
- **`gradient_accumulation_steps`:** gradients are accumulated over this many steps, then a single update is made. It's the way to preserve the **effective batch** when you're forced to shrink the batch.

**Effective batch math:**

```text title="Effective batch size"
effective_batch = per_device_train_batch_size × gradient_accumulation_steps × GPU_count

Example 1:  batch 2, accum 4, 1 GPU  →  effective batch = 2 × 4 × 1 = 8
Example 2:  batch 1, accum 8, 1 GPU  →  effective batch = 8    (same; less VRAM, a bit slower)
Example 3:  batch 2, accum 4, 2 GPU  →  effective batch = 16   (double with two cards)
```

Rule: keeping the effective batch in the 8-32 range is a good balance for most fine-tuning jobs. If the loss is very jumpy (zigzag), the first remedy is growing the effective batch.

:::note
The learning rate does **not scale automatically** with gradient accumulation. Raising `gradient_accumulation_steps` from 4 to 8 grows the effective batch but the LR and scheduler math stay the same. If you grow the effective batch substantially, revisit the LR too: "if you double the effective batch, roughly double the LR" is a common starting hypothesis but not a law — don't move to a full-scale training without verifying with a short run.
:::

### Variance and the seed: don't trust a single run

Same model, same data, same settings; only the randomness differs (seed, data order). Will the result be the same? No — and that should be expected. The classic reference on this shows that different random seeds can change fine-tuning results **markedly**, and that weight initialization and data order contribute comparably to the variance (Dodge et al., arXiv:2002.06305).

The practical consequences:

- Don't count a small difference between two runs as an "improvement"; make decisions with **2-3-seed repeats**.
- In an important comparison (config A vs config B), run both a few times and look at the mean and the spread.
- For reproducibility, set the `seed` explicitly (the trainer default is 42); but remember a fixed seed doesn't pin everything — kernel-level parallelism and library versions can create small differences.
- For comparison and evaluation practice: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).
- The production side of the same distinction was measured: when the same prompt was sent ten times, temperature 0 preserved identity on short answers but not on 1,000+-token long generations. The numbers and the run manifest are on the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page.

## Maximum Sequence Length (max_length)

`max_length` (formerly `max_seq_length`; `sequence_len` in some tools) determines the maximum number of tokens each example is truncated to. As length grows, VRAM and time grow **not quadratically but fast** — since the attention factor grows quadratically with length, a 2,048-token example asks for a bit more than twice the memory of a 1,024-token one.

- Pick the smallest value that **won't throw away 95%** of your data. Chat data usually sits between 512-2048.
- Don't immediately fill the real context (the model's supported ceiling); if your data is short, choosing 4096 just burns money/electricity.

### Packing

It merges short examples (e.g. 200-token Q&As) into a single `max_length` window. The gain: the GPU doesn't idle, training speeds up noticeably.

- **On (packing=True):** it's great for datasets with short, homogeneous examples; it boosts speed significantly.
- **Off:** turn it off when example boundaries must be exact (e.g. evaluation, delicate masking experiments) or when examples are already long.

:::note
Packing causes the loss to be interpreted "per token" rather than "per example"; loss values can't be compared one-to-one with those you got with packing off. Compare experiments under the same setting.
:::

## The Other Knobs

| Knob | What it does | Typical value | When to change it? |
| --- | --- | --- | --- |
| `lora r / alpha / dropout` | The adapter's capacity, scale, regularization | r=16, alpha=32, dropout=0.05 | If the model isn't changing enough, raise r to 32-64; if data is scarce, raise dropout. Details: [LoRA and QLoRA](/en/llm/lora-qlora/) |
| `weight_decay` | Reduces memorization by keeping weights small | 0.0 – 0.1 (usually 0.01) | Raise it if the validation loss rises early (memorization); 0 is also common in LoRA |
| `optim` | The optimization algorithm | `adamw_torch`; `paged_adamw_8bit` with little VRAM | If memory is tight, switch to the paged version; in QLoRA the paged version saves VRAM |
| `bf16 / fp16` | Compute precision | bf16 preferred | If you hit NaN/loss spikes, move from fp16 to bf16; if an old GPU doesn't support bf16, fp16 + loss scaling |
| `gradient_checkpointing` | Recomputes intermediate activations instead of storing them | On by default in TRL SFTConfig; off in the classic Trainer | Turn it on if you get OOM; turn it off if speed is the priority and VRAM is plentiful (training speeds up noticeably) |
| `max_grad_norm` | Clips the gradient norm; prevents explosions | 1.0 (default) | Lower it (e.g. 0.3) if sudden loss jumps persist; a too-low value slows learning |
| `seed` | Pinning the randomness | 42 (default) | In comparative experiments deliberately try a few values (see the variance section above) |

## Copy-Paste Starting Configs

Three ready sets — take the one that fits your need and play with your own values:

```python title="ready_configs.py"
# A) QLoRA — a 4B/8B model, single GPU. The starting point for most individual projects.
qlora_4b_8b = {
    "learning_rate": 2e-4,
    "num_train_epochs": 2,          # you can try between 1-3
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,   # effective batch = 8
    "lr_scheduler_type": "cosine",
    "warmup_steps": 0.03,           # a ratio: 3% of steps (v5; formerly warmup_ratio)
    "max_length": 1024,
    "bf16": True,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "packing": True,
}

# B) Full fine-tuning — a small model (1B-3B), if you have enough VRAM (e.g. 24 GB+)
full_fine_tune = {
    "learning_rate": 2e-5,          # NOTE: ~10x SMALLER than the LoRA value
    "num_train_epochs": 2,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 2,
    "lr_scheduler_type": "cosine",
    "warmup_steps": 0.05,           # a ratio: 5% of steps (v5)
    "max_length": 1024,
    "bf16": True,
    "weight_decay": 0.01,
}

# C) DPO — preference tuning (after SFT, optional)
dpo = {
    "learning_rate": 5e-7,          # NOTE: much much smaller than SFT
    "num_train_epochs": 1,
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 8,
    "beta": 0.1,
    "warmup_steps": 0.03,           # a ratio (v5)
    "bf16": True,
}
```

## The Symptom → Fix Table

If things go wrong during training, use this table; for detailed debugging move to the [Troubleshooting](/en/llm/sorun-giderme/) page.

| Symptom | Likely cause | Try first |
| --- | --- | --- |
| The loss never drops | lr too low; a data format error | Raise the lr 2-5x; eyeball the data on one example (chat template!) |
| Loss NaN / inf | lr too high; fp16 instability; a broken example | Halve the lr; switch to bf16; clean out NaN-containing examples; add warmup |
| Loss very jumpy (zigzag) | Effective batch small; lr high | Raise `gradient_accumulation_steps`; lower the lr a bit |
| Validation loss rising early (memorization) | Too many epochs; little data | Reduce epochs; add `lora_dropout`/`weight_decay`; add data |
| Training very slow | Packing off; sequence too long; a data-loading bottleneck | Turn packing on; shorten `max_length`; raise `dataloader_num_workers` |
| The model is broken after training | Wrong chat template; too many epochs; the adapter wasn't loaded | [Troubleshooting](/en/llm/sorun-giderme/) section 4 |

## Which Name in Which Tool?

The concepts are the same, the names vary a little by tool:

| Concept | TRL (SFTConfig) | Axolotl (YAML) | Unsloth |
| --- | --- | --- | --- |
| Learning rate | `learning_rate` | `learning_rate` | `learning_rate` |
| Epochs | `num_train_epochs` | `num_epochs` | `num_train_epochs` |
| Micro batch | `per_device_train_batch_size` | `micro_batch_size` | `per_device_train_batch_size` |
| Gradient accumulation | `gradient_accumulation_steps` | `gradient_accumulation_steps` | `gradient_accumulation_steps` |
| Sequence length | `max_length` | `sequence_len` | `max_seq_length` |
| LoRA rank | `r` (LoraConfig) | `lora_r` | `r` (LoraConfig) |

For tool choice and setups, see the [Tools Comparison](/en/llm/araclar/) page.

## Wrapping Up

- Set the **learning rate** and the data right first; the other knobs are secondary.
- Effective batch = micro batch × accumulation × GPU count; aim for the 8-32 range.
- Choose `max_length` according to your data, not the model's ceiling.
- To watch the curve: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/); for error messages: [Troubleshooting](/en/llm/sorun-giderme/).

## Sources and Further Reading

- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314) — the learning-rate sweep by model size in Table 9.
- [LoRA Learns Less and Forgets Less (arXiv:2405.09673)](https://arxiv.org/abs/2405.09673) — LoRA's learning-rate sensitivity and the target-domain comparison.
- [Fine-Tuning Pretrained Language Models: Weight Initializations, Data Orders, and Early Stopping (arXiv:2002.06305)](https://arxiv.org/abs/2002.06305) — the classic study on seed variance and early stopping.
- [transformers — Trainer and TrainingArguments](https://huggingface.co/docs/transformers/main_classes/trainer) — default values and EarlyStoppingCallback.
- [transformers — the "Deprecate warmup_ratio" change](https://github.com/huggingface/transformers/pull/41326) — the switch from `warmup_ratio` to `warmup_steps` (decimal = ratio); removal completed in v5.2.
- [TRL — SFTConfig reference](https://huggingface.co/docs/trl/sft_trainer) — the SFT-specific defaults (`packing`, `gradient_checkpointing`, learning rate etc.).
