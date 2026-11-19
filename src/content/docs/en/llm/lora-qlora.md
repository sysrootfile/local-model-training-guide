---
title: "LoRA and QLoRA: Fine-Tuning with Little VRAM"
description: "LoRA's intuition, 4-bit training with QLoRA, rank and layer-selection evidence, rsLoRA and DoRA, the adapter lifecycle, and a complete QLoRA example in the classic Trainer flow."
dogrulama: 2026-11-19
---

**LoRA (low-rank adaptation)** is the most common way to fine-tune a large model. The idea: instead of re-carving a 7-ton marble statue from scratch, you add a **thin layer of plaster** that gives the statue the shape you want. The original statue (the model weights) stays as it is; only the thin top layer (the adapter) is trained.

## How Does LoRA Work?

Consider the weight matrix `W` of a neural network layer (e.g. 4096 × 4096 = ~16.7 million parameters). Training normally updates every element of this `W`. LoRA instead represents the update as the product of two **small** matrices:

```text title="The LoRA idea"
Full update:    W_new = W_original + ΔW          (ΔW: 4096 x 4096 — huge!)

With LoRA:      W_new = W_original + B · A       (A: 16 x 4096, B: 4096 x 16)

  - W_original: FROZEN (not trained) — 16.7 million parameters stay fixed
  - A and B: trained — 131,072 parameters in total (for r=16)
  - Ratio: ~0.8%. You are training one thousandth of the parameters.
```

The small `r` (rank) value limits the "capacity" of the update: the changes expressible with `r=16` are far "lower-dimensional" than a full update. In practice this is usually enough, because the change a model needs in order to learn a new task is much smaller than the original training.

This has three major consequences:

1. **VRAM savings:** the optimizer state is kept only for the adapter.
2. **Small output:** the trained adapter takes a few MB; you do not copy the base model every time.
3. **Multi-use:** you can train different adapters for different tasks on the same base model and switch between them at runtime.

## QLoRA: 4-bit Model + LoRA

Even in normal LoRA, the base model is loaded in fp16 (16-bit). For an 8B-parameter model that alone means `8 billion × 2 bytes = ~16 GB` of VRAM. **QLoRA** steps in here: the base model is **quantized to 4-bit**, and LoRA is trained on top of it.

| | Approximate VRAM for an 8B model |
| --- | --- |
| fp16 loading | ~16 GB (weights only) |
| 4-bit loading | ~4-5 GB (weights) + training overhead |
| QLoRA total (LoRA + gradient checkpointing) | about 5-6 GB |

The QLoRA paper (2305.14314) showed that the quality loss from 4-bit quantization is very small: a well-configured QLoRA run comes very close to fp16 LoRA. As a result, 4B models train comfortably on consumer cards with 8-12 GB VRAM and 8B models on 16-24 GB cards. For the hardware matching table, see [VRAM Math](/en/donanim/vram-hesabi/).

:::note
"NF4" (normal float 4), used in 4-bit quantization, is a special 4-bit format designed on the assumption that weights are close to a normal distribution. The `bitsandbytes` library does this for you; you do not need the details — but keep the table above in mind to understand the settings.
:::

### The triple mechanism: NF4, double quantization, paged optimizer

QLoRA's memory saving is not a single trick but a composition of three mechanisms (QLoRA paper, arXiv:2305.14314):

1. **NF4 (4-bit NormalFloat):** a 4-bit storage format designed for weights close to a normal distribution; it encodes weights most efficiently with respect to that distribution.
2. **Double quantization:** quantizes the quantization constants too, gaining another layer of memory savings.
3. **Paged optimizer:** allows the optimizer state to be paged to CPU memory at memory peaks, helping prevent sudden out-of-memory (OOM) crashes.

The paper's headline result: thanks to this triple, a 65B-parameter model can be fine-tuned **on a single 48 GB GPU**, and the results preserve the task performance of full 16-bit fine-tuning (QLoRA paper, abstract).

### The flow after QLoRA: merge, quantize, serve

When training finishes you hold only the adapter (a few MB). The typical path to production is three steps:

1. **Merge on a 16-bit base:** reload the base model **in 16-bit (bf16/fp16)**, apply the adapter and merge it into a single model with `merge_and_unload()`. In peft, this method returns an independent model of the base model's architecture; you must assign the result to a variable — it is not an in-place operation (peft docs). Step-by-step: [LoRA Merging](/en/kullanim/lora-birlestirme/).
2. **Quantize (optional):** convert the merged 16-bit model to distribution formats like GGUF: [Quantization](/en/kullanim/quantization/).
3. **Serve:** for local use [Ollama](/en/kullanim/ollama/), for APIs [Serving and API](/en/kullanim/sunma-api/).

:::caution
Do **not** merge the adapter directly into a 4-bit quantized base. The correct and recommended flow is to load the base model in 16-bit, merge, and then re-quantize the result if you wish. Direct merging into a 4-bit base risks quality loss; community experience also points to "dequantize first, then merge" (e.g. Hugging Face forum discussions and independent QLoRA write-ups). Do not ship a merged model without comparing it against the pre-merge model on the same fixed test questions.
:::

## Critical Parameters

| Parameter | What it does | Typical value | Selection hint |
| --- | --- | --- | --- |
| `r` (rank) | Adapter capacity | 8 / 16 / 32 / 64 | Simple format task: 8-16. Broad behavior change: 32-64. Little data: 8. |
| `lora_alpha` | Scales the effect of the update | Usually `2 × r` | r=16 → alpha=32. Grow it together with r. |
| `lora_dropout` | Prevents overfitting | 0.0 – 0.05 | 0.05 with little data; can stay 0 with plenty of data. |
| `target_modules` | Which layers the adapter attaches to | `q_proj, k_proj, v_proj, o_proj` + MLP gates | "All linear layers" (`q,k,v,o,gate,up,down`) is a safe, good start. |
| `bias` | Train extra bias terms? | `"none"` | Almost always `"none"`; don't be surprised to see `"all"` in older guides — unnecessary. |
| `use_gradient_checkpointing` | Recomputes activations instead of storing them | On with little VRAM | Lowers VRAM noticeably, slows training by ~20-30%. |

:::tip
For your first attempt use this starting configuration: `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, `target_modules` all linear layers. If you are unhappy with the result and feel "the model isn't changing enough", the first thing to try is raising `r` to 32-64. For other details see [Hyperparameters](/en/llm/hiperparametreler/).
:::

## What Does Rank Selection Depend On? Evidence: "LoRA Learns Less and Forgets Less"

One of the most comprehensive experimental answers to "does growing the rank approach full fine-tuning?" is the study by Biderman et al. (arXiv:2405.09673). Key findings:

- **It lags in the target domain:** in target domains like code, LoRA stays clearly below full fine-tuning; increasing the rank does not close this gap.
- **The gap varies by domain:** in math, LoRA approaches full fine-tuning more closely; however, full fine-tuning is more **sample-efficient** (less data achieves the same performance).
- **Off-target, the advantage is LoRA's:** LoRA preserves the base model's abilities outside the target domain better than full fine-tuning — it forgets less.
- **Why?** Full fine-tuning learns changes with a rank **10-100x higher** than typical LoRA configurations; LoRA's low-rank constraint is a natural ceiling for some targets.

Practical translation: rank selection is not a "make it big, no harm" affair — it depends on **the character of your goal**.

| Your situation | Rank suggestion |
| --- | --- |
| Style/format change, single task | r=8-16 suffices; spend the energy on data |
| Training an intense target domain like code/math | try r=32-64; if the gap persists, consider full fine-tuning |
| Domain adaptation + preserving old abilities as priority | LoRA already forgets less than full fine-tuning; don't overdo the rank |
| Little data (a few thousand examples) | small rank (r=8) is usually safer |

## rsLoRA and DoRA: Two Refinements, When to Consider Them

Classic LoRA scales the update with `alpha / r`. As the rank grows this scale shrinks, and at high ranks the adapter's effect can weaken unexpectedly. Two popular fixes:

| Method | The idea | In peft | When to consider |
| --- | --- | --- | --- |
| **rsLoRA** (arXiv:2312.03732) | Makes the scale `alpha / sqrt(r)` instead of `alpha / r`; balances training at high ranks | `LoraConfig(use_rslora=True)` | If you will use rank 64 and above; if high rank feels like "the model isn't learning" |
| **DoRA** (arXiv:2402.09353) | Splits the weight update into **magnitude** and **direction**: direction is learned by LoRA, magnitude carried by a separate parameter | `LoraConfig(use_dora=True)` | Especially if you want to raise quality at **low ranks** |

The cost difference matters: rsLoRA is almost free (only the scale formula changes, no extra parameters). DoRA slows training and increases memory use; the peft docs recommend merging before inference with DoRA and note that DoRA supports only linear and Conv2D layers. Neither is a "default" — they are options to try when needed: first get a good baseline result with classic LoRA, then compare.

## LoRA on Which Layers? `q,v` or All Linear Layers?

One of the clearest ablation findings comes from the QLoRA paper: to reach full fine-tuning performance, LoRA must be applied to **all linear transformer block layers** (arXiv:2305.14314). Most modern guides therefore do not stop at `q,v`:

| Choice | Coverage | When it makes sense |
| --- | --- | --- |
| `["q_proj", "v_proj"]` | The cheapest option left over from classic recipes | Very simple style tuning; when VRAM is severely limited |
| `["q_proj", "k_proj", "v_proj", "o_proj"]` | All attention projections | The middle way; if the change mostly happens in attention layers |
| `"all-linear"` | All linear layers in the model: attention + MLP (`gate`, `up`, `down`) | The modern default; QLoRA recipes use this coverage |

Shortcut in peft: `LoraConfig(target_modules="all-linear")` selects all linear/Conv1D modules (except the output layer — peft docs). Names vary by model family (Qwen/Llama: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`); if unsure, leave `all-linear`. If you give a wrong name, peft finds no trainable modules and errors out — it does not silently run an empty training.

In the BERT family (including embedding models), attention lines are named `query` / `key` / `value` / `dense`; you get an error if you pass `q_proj`. We measured this trap by actually running it on an embedding model: in the LoRA arm on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page, the targets are `["query", "value"]` and the trainable-parameter ratio is given as a number.

:::tip
Widening layer coverage (e.g. `all-linear` instead of just `q,v`) typically gains more task performance at the same rank, in exchange for slightly more trainable parameters and VRAM. Recommended order: widen layer coverage first, then grow the rank.
:::

## LoRA or Full Fine-Tuning?

| | LoRA / QLoRA | Full fine-tuning |
| --- | --- | --- |
| VRAM need | Low (4-8x saving) | High |
| Training speed | Fast | Slow |
| Output size | Adapter: a few MB | The whole model: GBs |
| Depth of behavior change | Enough for most format/style tasks | If very deep behavior change is needed |
| Multiple tasks | Same base model + different adapters | A separate full model per task |
| Difficulty | Easy | Harder (stability, resource management) |
| When chosen | **Almost always the first choice** | Sufficient hardware + cases LoRA can't cover |

:::caution
"LoRA is not real fine-tuning" is a common but wrong belief. Most format, style, domain-jargon and task-behavior changes are learned perfectly well with LoRA. Full fine-tuning enters the picture only when you saturate LoRA (usually in very specific cases).
:::

## Full Example: QLoRA with peft + transformers

The example on the [SFT page](/en/llm/sft/) used `SFTTrainer`. Here we see the **classic `Trainer` flow**, so you can see the mechanism underneath (data processing, collator, loss) more clearly:

```python title="qlora_training.py"
# QLoRA: quantize the base model to 4-bit + train a LoRA adapter on top
# Setup:
#   pip install transformers peft bitsandbytes datasets accelerate

import torch
from datasets import load_dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, TrainingArguments, Trainer,
                          DataCollatorForLanguageModeling)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

MODEL_NAME = "Qwen/Qwen3-4B"

# ---------------------------------------------------------------------------
# 1) 4-bit quantization settings — this is where the VRAM saving happens
# ---------------------------------------------------------------------------

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                      # load the weights in 4-bit
    bnb_4bit_quant_type="nf4",              # "normal float 4": the recommended type
    bnb_4bit_use_double_quant=True,         # a second quantization layer: a bit more saving
    bnb_4bit_compute_dtype=torch.bfloat16,  # matrix multiplications run in bf16
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",                      # place layers onto the GPU automatically
)

# ---------------------------------------------------------------------------
# 2) Prepare for 4-bit training:
#    - gradient checkpointing is enabled (VRAM saving)
#    - layernorm layers are cast to fp32 for numerical stability
# ---------------------------------------------------------------------------

model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

# ---------------------------------------------------------------------------
# 3) LoRA configuration
# ---------------------------------------------------------------------------

lora_config = LoraConfig(
    r=16,                                   # rank: adapter capacity
    lora_alpha=32,                          # scale: usually 2x the rank
    lora_dropout=0.05,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],  # all linear layers
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # you will see "trainable: ~0.5-1%"

# ---------------------------------------------------------------------------
# 4) Data: a simple pretraining-style "predict the next token" example.
#    (For instruction data, see the example on the /en/llm/sft/ page.)
# ---------------------------------------------------------------------------

data = load_dataset("atasoglu/instruction-turkish", split="train[:3000]")

def prepare(example):
    # merge the "prompt + completion" fields into one text;
    # adapt the dataset's field names to your own data.
    text = example.get("prompt", "") + "\n" + example.get("completion", "")
    encoded = tokenizer(text, truncation=True, max_length=1024)
    encoded["labels"] = encoded["input_ids"].copy()  # language modeling: target = the input itself
    return encoded

data = data.map(prepare, remove_columns=data.column_names)

# ---------------------------------------------------------------------------
# 5) Training settings and the classic Trainer flow
# ---------------------------------------------------------------------------

training_args = TrainingArguments(
    output_dir="./qlora-output",
    num_train_epochs=2,
    per_device_train_batch_size=2,          # set to 1 if VRAM is not enough
    gradient_accumulation_steps=4,          # effective batch = 8
    learning_rate=2e-4,                     # typical value for LoRA/QLoRA
    lr_scheduler_type="cosine",
    warmup_steps=0.03,                      # a ratio: 3% of steps (v5; formerly warmup_ratio)
    bf16=torch.cuda.is_bf16_supported(),
    gradient_checkpointing=True,
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=data,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
)
trainer.train()

# ---------------------------------------------------------------------------
# 6) Save only the adapter (not the base model — just a few MB):
# ---------------------------------------------------------------------------

model.save_pretrained("./qlora-adapter")
tokenizer.save_pretrained("./qlora-adapter")
```

:::note
Note: in this classic flow the loss is computed over **all** tokens (there is no loss mask). If you want a loss mask while working with instruction data, prefer the [SFT](/en/llm/sft/) example using `SFTTrainer(assistant_only_loss=True)`. The concept itself is explained on the [SFT page](/en/llm/sft/).
:::

## Frequently Asked Questions

:::tip
**"What should I pick for r?"**
First attempt: `r=16`. If the model's behavior isn't changing enough, try `r=32` or `64` (and set alpha to 2×r). With little data and a memorization risk, `r=8` may be safer. Raising `r` increases VRAM very little; its only costs are some speed and a lot of memorization potential.

**"How do I save and reload the adapter?"**

```python
# Saving (at the end of training):
model.save_pretrained("./adapter")

# Reloading (for inference):
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-4B")
model = PeftModel.from_pretrained(base, "./adapter")
```

The adapter does not work alone; it is always loaded together with a **base model**. If you want to carry it in a single file, merge the adapter into the base model: [LoRA Merging](/en/kullanim/lora-birlestirme/).

**"How do I run the model?"**
For quick local use see [Ollama](/en/kullanim/ollama/), for serving as an API [Serving and API](/en/kullanim/sunma-api/), for sharing on Hugging Face [Hugging Face Sharing](/en/kullanim/huggingface-paylasim/).

**"Can I train multiple adapters?"**
Yes — one of LoRA's nicest sides: train separate adapters for different tasks on the same base model and switch adapters at runtime as needed. The disk cost is only a few MB per adapter.
:::

## Adapter Lifecycle: Version, Serve, Verify

The adapter is not a "side file"; it is an **artifact** that must be managed:

- **Version it:** whenever you save an adapter, note alongside it: the base model's name **and revision**, the training data's version/summary, `r`, `alpha`, `target_modules`, epoch count and learning rate. Adapters trained with different revisions of the same base model can be incompatible; the question "which run is this from?" will definitely come back.
- **Serve multiple adapters:** several adapters can run on the same base model. In peft, adapters are loaded with `model.load_adapter("...", adapter_name="task_a")` and the active one is chosen with `set_adapter`. Serving engines like vLLM serve multiple LoRAs at once with the `--enable-lora` and `--lora-modules` flags (limits set with `max_loras` and `max_lora_rank`).
- **Verify after merging:** merging should be mathematically equivalent, but "should be" and "is" differ: define 10-20 fixed test questions and compare outputs before/after the merge. Most silent regressions are caught at this step.
- **Keep the raw adapter:** archive the original adapter (a few MB) next to the merged model; when moving to a new base model version, re-merging + verification may be enough instead of training from scratch.

## Unsloth: The Fast Alternative (Status in 2026)

Unsloth is a training framework that speeds up the same peft/TRL workflow and is compatible with the Hugging Face ecosystem; the TRL docs cite its claim of "up to 2x faster, up to 70% less VRAM" (TRL docs, 2026). An honest status report:

- As of 2026 the project moves at a very fast release tempo and publishes its releases with a "beta" label (the most recent tag as of October 13, 2026: `v0.1.907-beta`, GitHub releases).
- The beta label does not mean "unusable"; but read the release notes and run your own tests before updating your production pipeline.
- Before switching, get a baseline result with the classic TRL/peft flow; measure the speed gain on your own data.

For the comparison table and setup: [Tools Comparison](/en/llm/araclar/).

## Turkish Token Efficiency: Why Model Choice Changes Cost

Turkish is an agglutinative language: a single word may correspond to several words in another language. Since different models' vocabularies were trained on different data, **the same Turkish text can split into a different number of tokens depending on the model**. This directly affects two things:

- **Training and inference cost:** pricing is mostly per token; if the same text splits into more tokens, the same job costs more.
- **Effective context window:** an 8,192-token context can mean "less text" in Turkish; in long-document or RAG jobs you feel that limit early.

We could not find a public, reliable and comparable measurement on this — rather than fabricating rates, here is how to measure it. Compare your own candidates like this:

```python
from transformers import AutoTokenizer

text = ("Model training is a long journey that takes patience; data quality "
        "comes before hyperparameters.")
word_count = len(text.split())

candidates = ["Qwen/Qwen3-4B", "PUT-YOUR-OWN-CANDIDATE-HERE"]

for name in candidates:
    tok = AutoTokenizer.from_pretrained(name)
    tokens = len(tok.encode(text))
    print(f"{name}: {tokens} tokens  (tokens/word = {tokens / word_count:.2f})")
```

Method: a single sentence misleads — take a 20-50 sentence sample **from your real data** and compute the tokens/word ratio for each candidate tokenizer. A low ratio is the sign of a tokenizer that represents the same data with fewer tokens (more efficient for Turkish); the final decision is still given by task performance. Tokenization fundamentals: [Tokenization](/en/temeller/tokenizasyon/).

## Wrapping Up

- LoRA: original weights freeze, small adapter matrices are trained. The output is a few MB.
- QLoRA: the base model is quantized to 4-bit; even an 8B model fits in ~5-6 GB of VRAM with little quality loss.
- Starting configuration: `r=16`, `alpha=32`, `dropout=0.05`, all linear layers, `bias="none"`.
- Always make LoRA/QLoRA the first choice; full fine-tuning is the next step.

Next stops: [Step-by-Step Training](/en/llm/adim-adim-egitim/), [Hyperparameters](/en/llm/hiperparametreler/) and, after training, [LoRA Merging](/en/kullanim/lora-birlestirme/).

## Sources and Further Reading

- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314) — NF4, double quantization and the paged optimizer; 65B model trained on a single 48 GB GPU.
- [LoRA: Low-Rank Adaptation of Large Language Models (arXiv:2106.09685)](https://arxiv.org/abs/2106.09685) — the original LoRA paper.
- [LoRA Learns Less and Forgets Less (arXiv:2405.09673)](https://arxiv.org/abs/2405.09673) — target/off-target domain split, rank effects and the forgetting comparison.
- [A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA (arXiv:2312.03732)](https://arxiv.org/abs/2312.03732) — rsLoRA.
- [DoRA: Weight-Decomposed Low-Rank Adaptation (arXiv:2402.09353)](https://arxiv.org/abs/2402.09353) — DoRA.
- [peft — LoRA reference](https://huggingface.co/docs/peft/package_reference/lora) — current definitions of `use_rslora`, `use_dora` and `all-linear`.
- [TRL — SFT Trainer docs](https://huggingface.co/docs/trl/sft_trainer) — Unsloth integration and training defaults.
- [vLLM — LoRA support](https://docs.vllm.ai/en/latest/features/lora.html) — multi-adapter serving (`--enable-lora`, `--lora-modules`).
