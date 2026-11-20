---
title: "LoRA Merging: Fusing the Adapter into the Base Model"
description: "Learn when it's necessary to make your trained LoRA adapter one piece with the base model, and how it's done step by step."
dogrulama: 2026-11-20
---

When LoRA fine-tuning finishes, you're left with two separate pieces: the huge **base model** and the small **adapter** fitted on top of it. On this page we clarify the question "should I keep the adapter separate, or merge it with the base model into one model?" and apply merging step by step.

:::note
If you're new to the LoRA, adapter and QLoRA concepts, first glance at the [LoRA and QLoRA](/en/llm/lora-qlora/) page. To see the whole training flow, the [Step-by-Step Training](/en/llm/adim-adim-egitim/) guide awaits you.
:::

## The adapter can't run alone

The scene on your disk at the end of a typical LoRA training is this:

| Piece | Example | Typical size |
|---|---|---|
| Base model | `Qwen/Qwen3-4B` weights | ~8 GB (fp16) |
| Adapter | `adapter_model.safetensors` + `adapter_config.json` | 50-200 MB |

The adapter isn't an independent model; it's like a "patch" fitted onto the base model. With `PeftModel.from_pretrained(base, adapter)` it doesn't run without being fitted onto the base model. That's why everyone (and every tool) using the adapter also needs the base model.

## Two paths: keeping separate and merging

| | Keep the adapter separate | Merge |
|---|---|---|
| Disk size | Base + a few hundred MB | One model at base size |
| Running | Base + adapter loaded together | Runs standalone, like a standard model |
| Multiple variants | One base + dozens of plug-in adapters | Each variant a full-size separate copy |
| Sharing | Both pieces must be sent together | One folder, one repo |
| GGUF conversion | Not supported (see below) | Required |

The short rule: **keep the adapter separate in the experimentation phase, merge in the distribution phase.**

## Why is merging necessary?

The most practical reason is [quantization](/en/kullanim/quantization/) and GGUF conversion. Tools like Ollama, LM Studio and llama.cpp expect a GGUF file; llama.cpp's conversion tools take a standard Hugging Face model folder as input. You can't hand adapters directly to these tools. The practical flow is:

**Training → merging (this page) → GGUF conversion → quantization → running in Ollama**

Merging's other benefits:

- The person downloading the model doesn't wrestle with "first download the base, then attach the adapter like so" steps; a single `from_pretrained` call suffices.
- Tools and serving engines that don't support adapters work flawlessly with the merged model.

:::tip
llama.cpp has limited support for loading a separate LoRA; but Ollama doesn't support that flow and the toolchain is a chore. At the beginner level, "merge first, then quantize" is almost always the right choice.
:::

## Merging: step by step

:::danger Never do the merge on a 4-bit model!
During QLoRA training the base model was loaded in 4-bit; but merging is always done on a **clean base model in fp16/bf16 precision**. If you merge a 4-bit model, the quantization error gets baked into the weights permanently and quality drops noticeably. So: training may be 4-bit, merging never.
:::

First the required libraries:

```bash title="setup.sh"
pip install -U torch transformers peft accelerate
```

Then the merge script:

```python title="merge.py"
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE    = "Qwen/Qwen3-4B"                    # the base model you used in training
ADAPTER = "username/qwen3-4b-turkish-lora"   # the adapter repo (on HF or a local folder)
OUTPUT  = "merged-model"                     # the folder the result will be saved to

# 1) Load the base model as fp16. NEVER load it in 4-bit/8-bit!
base = AutoModelForCausalLM.from_pretrained(
    BASE,
    torch_dtype=torch.float16,
    device_map="cpu",       # CPU is enough for merging; "auto" also works if you have a GPU
)

# 2) Fit the adapter onto the base model
model = PeftModel.from_pretrained(base, ADAPTER)

# 3) Fuse the adapter weights into the main model
model = model.merge_and_unload()

# 4) Save the single-piece model and the tokenizer
model.save_pretrained(OUTPUT)

# We take the tokenizer from the adapter folder; it was saved there during training.
# (If unsure, you can also use the BASE model's tokenizer.)
tokenizer = AutoTokenizer.from_pretrained(ADAPTER)
tokenizer.save_pretrained(OUTPUT)

print("Merging complete:", OUTPUT)
```

The `merge_and_unload()` call adds the adapter's low-rank matrix product to the base weights and removes the PeftModel wrapper. The result is an ordinary Hugging Face model: `AutoModelForCausalLM.from_pretrained("merged-model")` now suffices. Two details should be noted from the PEFT docs: `merge_and_unload()` doesn't work in-place, assigning the returned model to a variable is mandatory (the script above does this); and merging is irreversible — to try different adapters you must reload the base model. If you want to pick the output format explicitly, write `model.save_pretrained(OUTPUT, safe_serialization=True)`; safetensors is the recommended safe format instead of pickle-based `.bin`.

:::caution Don't lose the tokenizer and chat template
The merged folder must contain not just the weights but also the **tokenizer files and the chat template**. If these aren't saved, the model loads but `apply_chat_template` errors out; the chat ability "evaporates". If you didn't change the template in training, the base tokenizer suffices; if you did (you added special tokens), be sure to save the tokenizer from the adapter folder.
:::

### One-line merging with Unsloth

If you trained with Unsloth, you don't need to hand-write the flow above; Unsloth does the same job in one call:

```python title="unsloth_merge.py"
# Merges the adapter into the base model and saves it as a single-piece fp16 model
model.save_pretrained_merged("output", tokenizer, save_method = "merged_16bit")
```

See the Unsloth docs for the `save_method` parameter's other options. The same tool also handles GGUF export (`save_pretrained_gguf`); that whole flow is described on the [Quantization](/en/kullanim/quantization/) page.

### Merging after QLoRA

If you trained with QLoRA, watch two points:

1. **Training 4-bit, merging fp16:** 4-bit was only for VRAM saving during training; you do the merging on a clean fp16 base model.
2. **The disk expectation:** the merged model is the base model's fp16 size (e.g. ~8 GB for 4B). Don't confuse it with the 100 MB adapter file that appears on disk when training finishes; the real model is formed at this step.

### Verification: did it really merge?

```python title="verify.py"
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("merged-model", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("merged-model")

messages = [{"role": "user", "content": "Hello! Introduce yourself in one sentence."}]
inputs = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True, return_tensors="pt"
).to(model.device)

output = model.generate(inputs, max_new_tokens=100)
print(tokenizer.decode(output[0][inputs.shape[1]:], skip_special_tokens=True))
```

If you're getting proper answers in the style of your training data, the merge succeeded. To see the chat template works, test specifically with a simple chat message like "Hello".

## Unifying multiple adapters: add_weighted_adapter

If you have several adapters trained on the same base (one for Turkish chat, one for code, say), PEFT can blend them into a single new adapter; then you permanently merge that single adapter as above:

```python title="merge_adapters.py"
import torch
from transformers import AutoModelForCausalLM
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(
    BASE,  # the same base model as in the script above
    torch_dtype=torch.float16, device_map="cpu"
)

# Load the two adapters under different names
model = PeftModel.from_pretrained(base, "username/turkish-lora", adapter_name="turkish")
model.load_adapter("username/code-lora", adapter_name="code")

# Weighted blending: one new adapter
model.add_weighted_adapter(
    adapters=["turkish", "code"],   # the adapters to blend
    weights=[0.7, 0.3],             # the weights (can be negative)
    adapter_name="combined",
    combination_type="linear",      # the blending strategy
)
model.set_adapter("combined")

# Now there's a single adapter: permanent merging
model = model.merge_and_unload()
model.save_pretrained("merged-model", safe_serialization=True)
```

`combination_type` picks the blending's math. `linear` is a weighted simple sum; `svd` re-decomposes the combined result to low rank (unsupported on models loaded in fp16/bf16, fp32 needed); `ties`, `dare_ties`, `dare_linear` and `magnitude_prune` are methods that prune conflicting updates; and `cat` concatenates the adapters, growing the rank (memory use rises). Which strategy is better varies by model and task; don't ship without comparing the result on your own evaluation set: [Benchmarks and Evaluation](/en/degerlendirme/benchmarklar/).

## mergekit's place: full-model merging, not a LoRA merge

[mergekit](https://github.com/arcee-ai/mergekit), often heard when the community says "model merge", is not the tool that fuses your LoRA adapter; the confusion is common. mergekit is the tool that merges **two or more fully trained models** (e.g. different fine-tunes of the same base) into one new model: the merge strategy is defined in a YAML file, and it offers methods like SLERP (spherical interpolation of two models), TIES and DARE (merging while pruning conflicting task updates), linear and Model Stock.

mergekit has a second face that may serve you: the `mergekit-extract-lora` tool takes the difference between a fine-tuned model and its base and extracts a PEFT-compatible LoRA adapter from it. In the scenario "I want to reduce the big model's delta to a small adapter", it's a practical exploration tool.

:::note
Summary: preparing your own QLoRA/LoRA adapter for distribution needs no mergekit; PEFT's `merge_and_unload()` flow (or Unsloth) suffices. mergekit is for model-model merging, a separate problem.
:::

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Merging a 4-bit-loaded model | Quality drops, answers become inconsistent | Load the clean base in fp16 and merge again |
| Forgetting to save the tokenizer | `apply_chat_template` errors, odd outputs | Add `tokenizer.save_pretrained(OUTPUT)` |
| The chat template getting lost | The model behaves like it "doesn't know how to chat" | Save the tokenizer from the adapter; check the template files |
| Merging the same adapter twice | The adapter's effect doubles, the model breaks | Always start every merge with a **clean** (adapter-free) base model |
| Merging with the wrong base model | A size mismatch or meaningless outputs | Check the `base_model` field in the adapter |

## When shouldn't you merge?

- **If you're still experimenting:** adapters are 50-200 MB; storing dozens of experiments' adapters is an order of magnitude easier than dozens of full models. Leave merging to the very end of the job.
- **If you'll use different abilities on the same base:** if you keep the "Turkish", "law" and "code" adapters separate, the base model sits on disk once and you switch between them.
- **If you'll swap adapters dynamically on the server:** engines like [vLLM](/en/kullanim/sunma-api/) can serve adapters directly with the `--enable-lora` and `--lora-modules` flags without merging them into the base model; a new adapter can even be loaded at runtime. No merging is needed in that scenario.

## Sources and Further Reading

- [PEFT — the LoRA developer guide](https://huggingface.co/docs/peft/developer_guides/lora): the official doc of the `merge_and_unload()` flow and the `add_weighted_adapter`/`combination_type` options.
- [mergekit](https://github.com/arcee-ai/mergekit): the repo of full-model merging methods like SLERP, TIES, DARE and of the `mergekit-extract-lora` tool.
- [Unsloth — Saving to GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf): the official doc of `save_pretrained_merged` and GGUF export.
- [vLLM — LoRA support](https://docs.vllm.ai/en/latest/features/lora.html): the doc of serving adapters without merging, with `--enable-lora`.
- [safetensors](https://huggingface.co/docs/safetensors/index): the doc of the safe tensor format used when sharing the merged model.

## Next Steps

- To shrink the merged model: [Quantization](/en/kullanim/quantization/)
- To run it locally: the [Ollama Guide](/en/kullanim/ollama/)
- To share with the community: [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/)
- To see the flow start to finish: [Step-by-Step Training](/en/llm/adim-adim-egitim/)
