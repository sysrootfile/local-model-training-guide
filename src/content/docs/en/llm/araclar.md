---
title: "Tools Comparison: Unsloth, Axolotl, LLaMA-Factory, TRL"
description: "A comparison of the four standout fine-tuning tools as of 2026, a decision guide and mini getting-started examples for each."
dogrulama: 2026-11-20
---

There is more than one way to write code for model fine-tuning: one gets you quick results, another is designed for reproducible production jobs, and yet another lets you train by clicking without writing any code. This page compares the four standout options in the ecosystem as of 2026:

- **Unsloth** — a speed- and VRAM-focused Python library on a single GPU
- **Axolotl** — a production-oriented training tool configured with a YAML file
- **LLaMA-Factory** — web UI + command line, 100+ model support
- **HF TRL + PEFT** — code-based reference libraries

:::note
An important truth: all these tools use the same things underneath — `transformers`, `peft`, `bitsandbytes`, `accelerate`. So tool choice doesn't change what you've learned: concepts like LoRA, learning rate and loss masking are the same in every tool. The tool is only convenience. Learn the concepts once and swap the tools as you please.
:::

## The Big Comparison Table

The assessments in the table reflect trends valid as of 2026; since every tool evolves fast, don't skip checking the current versions.

| | Unsloth | Axolotl | LLaMA-Factory | HF TRL + PEFT |
| --- | --- | --- | --- | --- |
| **Interface** | Python code (functions) | YAML config file | Web UI + CLI | Python library |
| **Distinguishing feature** | ~2x speed on a single GPU + clear VRAM saving; very good for QLoRA | Comprehensive options for production jobs; reproducible experiments | 100+ model support; click-to-train; config sharing | Reference implementations; SFT/DPO/GRPO trainers |
| **Multi-GPU** | Supported: DDP (Unsloth CLI with torchrun), Accelerate and DeepSpeed; the multi-GPU experience is still being simplified | Yes, strong with DeepSpeed | Yes | Yes (with accelerate/DeepSpeed) |
| **Model support** | Popular models supported shortly after release | Broad; new models added fast | Very broad (100+) | Every model in transformers |
| **Preference training support** | DPO, GRPO, ORPO, KTO | DPO, IPO, ORPO, KTO, GRPO, SimPO (plus GDPO, EBFT) | DPO, KTO, ORPO, SimPO, PPO (+ reward modeling) | DPO, KTO, GRPO, RLOO (ORPO and CPO experimental) |
| **GGUF export** | `save_pretrained_gguf` | `axolotl export` (merge first) | — (converted with llama.cpp) | — (converted with llama.cpp) |
| **License** | Apache-2.0 | Apache-2.0 | Apache-2.0 | Apache-2.0 |
| **Suited for** | Individuals doing quick experiments on a single GPU | Teams running production jobs from a config | Those who don't want to write code, quick experimenters | Those who want to learn the concepts and build a custom flow |

## The Decision Guide

- **"I don't want to write code, let me train by clicking"** → **LLaMA-Factory** (the web UI lets you pick model, data and parameters with forms)
- **"Quick results on a single GPU + Python"** → **Unsloth** (does the same job faster and with less VRAM)
- **"Reproducible production job from a config file"** → **Axolotl** (you put the YAML into version control, the result becomes reproducible)
- **"I'll learn the libraries and build my own custom flow"** → **TRL + PEFT** (everything is exposed; the most control, the most code)

## Mini Starters

### Unsloth

Setup and quick loading (for detailed examples see the [Unsloth documentation](https://unsloth.ai/docs)):

```bash title="unsloth_setup.sh"
# A virtual environment is recommended (venv or conda), then:
pip install unsloth
```

```python title="unsloth_quick_start.py"
from unsloth import FastModel  # FastModel in newer versions; FastLanguageModel in older guides

model, tokenizer = FastModel.from_pretrained(
    model_name="Qwen/Qwen3-4B",   # Unsloth's ready 4-bit versions also exist (unsloth/...)
    max_seq_length=1024,
    load_in_4bit=True,            # the key to VRAM saving
)

# Add LoRA
model = FastModel.get_peft_model(
    model,
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
)

# From here on it's the classic TRL flow: hand it to SFTTrainer and train.
# (For the loss mask: train_on_responses_only — see the /en/llm/sft/ page.)
```

### Axolotl

```bash title="axolotl_setup.sh"
git clone https://github.com/axolotl-ai-cloud/axolotl.git
cd axolotl
pip install -e .
# Alternative: use the ready Docker image (axolotlai/axolotl)
```

```yaml title="config.yml"
# Axolotl defines the whole job through this YAML file: put it in version control,
# and repeat the same experiment with the same config whenever you want.
base_model: Qwen/Qwen3-4B
load_in_4bit: true          # QLoRA
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj

datasets:
  - path: data.jsonl       # your Alpaca/ShareGPT-style data file
    type: alpaca

sequence_len: 1024
micro_batch_size: 2
gradient_accumulation_steps: 4
num_epochs: 2
learning_rate: 0.0002
lr_scheduler: cosine
warmup_ratio: 0.03          # valid in Axolotl's schema; converted to warmup_steps internally
bf16: auto
```

```bash title="start_training.sh"
axolotl train config.yml
```

### LLaMA-Factory

```bash title="llamafactory_setup.sh"
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e ".[torch,metrics]"
```

```bash title="llamafactory_usage.sh"
# Option 1 — Web UI: pick model/data/parameters in the browser and start training
llamafactory-cli webui

# Option 2 — CLI: training with a ready config
# (many example configs live under examples/; you can write your own YAML too)
llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml
```

Since the interface turns training parameters into form fields, it's a perfect playground for learning "which knob does what?" — and after learning the same concepts, carrying the [Hyperparameters](/en/llm/hiperparametreler/) knowledge from this page over is easy.

### HF TRL + PEFT

Code-based, the lowest-level but most flexible option. The full example is on the [SFT page](/en/llm/sft/):

```bash title="trl_setup.sh"
pip install "trl" "peft" "datasets" "transformers" "accelerate" "bitsandbytes"
```

```python title="trl_quick_start.py"
from trl import SFTTrainer

trainer = SFTTrainer(
    model="Qwen/Qwen3-4B",
    train_dataset=data,          # data in the messages format
)
trainer.train()
```

:::tip
The biggest advantage of learning TRL: when the other tools run into a problem (e.g. a weird error message, unexpected behavior), you can understand "which layer" the problem is in. A person who knows TRL reads Unsloth and Axolotl easily too, because both use concepts and parameters familiar from TRL.
:::

## Which One Should I Start With?

:::tip
- **A beginner wanting to see results immediately:** Unsloth (single GPU, fast) or LLaMA-Factory (no code at all).
- **Learning-oriented, wanting to understand the fundamentals:** see TRL first — the examples on the [SFT](/en/llm/sft/) and [LoRA/QLoRA](/en/llm/lora-qlora/) pages already use TRL + PEFT. Once the concepts settle, you'll better appreciate Unsloth's speed gain and what Axolotl solves in production.
- **Production/reproducibility within a team:** Axolotl's YAML config exists precisely for that.
:::

## Moving Between Tools

Switching from one tool to another is easier than you think: the concepts (LoRA, learning rate, loss masking, warmup) stay the same; only the key names and the interface change. The mapping below shows the most commonly confused names; for the meanings, the explanations on the [Hyperparameters](/en/llm/hiperparametreler/) page apply.

| Concept | TRL + PEFT | Unsloth | Axolotl | LLaMA-Factory |
| --- | --- | --- | --- | --- |
| Max sequence length | `max_length` | `max_seq_length` | `sequence_len` | `cutoff_len` |
| Effective batch | `per_device_train_batch_size` + `gradient_accumulation_steps` | same | `micro_batch_size` + `gradient_accumulation_steps` | `per_device_train_batch_size` + `gradient_accumulation_steps` |
| Epoch count | `num_train_epochs` | `num_train_epochs` | `num_epochs` | `num_train_epochs` |
| LoRA rank | `r` | `r` | `lora_r` | `lora_rank` |
| LoRA target modules | `target_modules` | `target_modules` | `lora_target_modules` | `lora_target` |
| Warmup | `warmup_steps` (decimal = ratio; v5) | `warmup_steps` | `warmup_ratio` (converted to `warmup_steps` internally) | `warmup_ratio` (in official example configs) |

The checklist when carrying over:

1. **Data format** — most tools read the same JSONL, but field names and mapping settings vary by tool (`datasets[].type` in Axolotl, `template` in LLaMA-Factory). In the target tool, read and verify the first 5-10 examples in their processed form; details: [Data Formats](/en/veri/veri-formatlari/).
2. **Chat template** — the template you used in training must also be the same in the target tool; if the template changes, the model behaves "scattered".
3. **Hyperparameters don't change, names do** — keep lr, epochs and effective batch the same; translate the names from the table above. Warmup note: on the TRL/Unsloth side the current name is `warmup_steps` (a decimal value = a ratio), while Axolotl's schema accepts `warmup_ratio` and converts it internally.
4. **Loss masking** — the "learn only from the assistant's answer" option has a different name in every tool; if set up wrongly, the model also memorizes the system prompt and output quality drops.
5. **Smoke test** — after carrying over, before starting a long run, run a few steps with 100-200 examples and see that the loss curve starts similarly to the previous tool.

## Wrapping Up

- All four tools use the same underlying layer; moving between them is far easier than learning from scratch.
- Unsloth for speed + VRAM, Axolotl for production + reproducibility, LLaMA-Factory for convenience, TRL for flexibility + learning.
- Whichever tool you start with, data quality and evaluation are more decisive than the tool.

Continue: fill in your chosen tool's settings correctly with [Hyperparameters](/en/llm/hiperparametreler/), and follow the end-to-end flow with [Step-by-Step Training](/en/llm/adim-adim-egitim/).

## Sources and Further Reading

- [Unsloth documentation](https://unsloth.ai/docs) — setup, quick start, DPO/GRPO guides and saving to GGUF.
- [Axolotl documentation](https://docs.axolotl.ai/) — the YAML config reference, RLHF methods (DPO/ORPO/KTO/GRPO) and GGUF export.
- [LLaMA-Factory (GitHub)](https://github.com/hiyouga/LLaMA-Factory) — 100+ model support, the web UI and ready example configurations.
- [TRL documentation](https://huggingface.co/docs/trl/) — the trainer taxonomy, data formats and reinforcement learning guides.
