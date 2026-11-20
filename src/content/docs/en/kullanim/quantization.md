---
title: "Quantization: Shrinking the Model"
description: "The logic of compressing model weights to 4-8 bits; a comparison of GGUF, AWQ, GPTQ and NF4 formats and practical conversion commands."
dogrulama: 2026-11-20
---

Your trained 8B model takes about 16 GB in fp16 and does not fit in your 12 GB graphics card. Or a model you downloaded filled your disk. The fix is called **quantization**: representing the model weights with fewer bits to shrink the size and memory need substantially.

:::note
Quantization does not change the model itself; it changes the model's **number representation**. Its most common use is "post-training quantization", done *after* training; that is what this page covers.
:::

## The Intuition: Not FLAC, MP3

A model's weights are just decimal numbers. To store numbers like `0.00348291...` the computer uses 16 bits in fp16, 32 bits in fp32. Quantization fits these numbers onto a smaller grid: at 4-bit, only 16 possible levels remain for each weight.

The analogy that works: **fp16 is a lossless FLAC file, 4-bit is MP3.** Most ears don't notice the difference, and the file drops to a third of its size. Likewise, at moderate quantization levels the model's ability is preserved in most tasks.

Rough size math (let the model have P billion parameters):

| Level | Approximate size for an 8B model | Rule |
|---|---|---|
| fp16 (unquantized) | ~16 GB | P × 2 GB |
| Q8 | ~8.5 GB | P × 1.1 GB |
| Q5 | ~5.5 GB | P × 0.7 GB |
| Q4 | ~4.7 GB | P × 0.6 GB |
| Q2/Q3 | ~3-4 GB | P × 0.4 GB |

The numbers vary by model and level variant; the goal is to give a sense of magnitude. The same math is useful for estimating the VRAM needed to run a model; see the [VRAM Math](/en/donanim/vram-hesabi/) page for details.

## Formats: which one works where?

| Format | Where it works | Who produces it | Typical use |
|---|---|---|---|
| **GGUF** | llama.cpp, Ollama, LM Studio, llama-cpp-python | llama.cpp tooling, Unsloth | Personal/local running; mixed CPU + GPU |
| **GPTQ** | GPU (vLLM, TGI) | GPTQ toolchain | Legacy GPU serving setups; the AutoGPTQ repo was archived in 2025 and the community has moved to GPTQModel |
| **AWQ** | GPU (vLLM, TGI) | AWQ toolchain | Modern GPU serving, vLLM production |
| **FP8** | vLLM; FP8 compute requires a compute capability 8.9+ GPU (Ada/Hopper, e.g. H100) | Built into vLLM | Fast serving on datacenter-class cards |
| **bitsandbytes NF4** | Training (transformers + PEFT) | bitsandbytes | QLoRA: 4-bit loading during training |

:::tip The takeaway
- Personal use with Ollama / LM Studio → **GGUF**
- Serving with vLLM → **AWQ** (alternatives: GPTQ; FP8 if you have a Hopper-class card)
- VRAM squeeze during training → **bitsandbytes (NF4)**
:::

As of 2026, vLLM can directly serve AWQ, GPTQ, FP8, bitsandbytes and GGUF-quantized models; check the current support list in vLLM's quantization docs. For the serving side's details see [Model Serving: vLLM and API](/en/kullanim/sunma-api/). FP8 is a special case: FP8 *computation* asks for a compute capability 8.9+ card (Ada Lovelace, Hopper; e.g. H100); an FP8-quantized model can run in a weights-only mode on Ampere-class cards.

The last line matters especially: **bitsandbytes 4-bit is not a distribution format.** In QLoRA it is used only to make training possible; when training finishes you [merge](/en/kullanim/lora-birlestirme/) the adapter and, if you wish, quantize separately for distribution.

### NF4 and GGUF are not the same thing

NF4 (NormalFloat4) is the 4-bit data type from the QLoRA paper, applied when the model is loaded into memory with `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")`. It does not produce a file on disk; there is no such thing as sharing an "NF4 model file". GGUF, on the contrary, is exactly a file on disk — llama.cpp's distribution format. The practical result: you trained with QLoRA → merged the adapter → produced a GGUF and distributed it that way.

Two details worth knowing about bitsandbytes: double quantization (`bnb_4bit_use_double_quant=True`) saves an extra ~0.4 bits per weight; NF4/FP4 quantization works on Pascal-class and newer NVIDIA cards. The docs' emphasis matters too: in 8-bit and 4-bit mode only *extra* parameters (i.e. LoRA adapters) can be trained; you cannot update the base weights in 4-bit mode. For the full QLoRA flow see the [LoRA and QLoRA](/en/llm/lora-qlora/) page.

## Decision Tree

```text
How will you run it?
│
├─ Ollama / LM Studio (personal use) ──► GGUF
│     ├─ Balanced start ................ Q4_K_M
│     ├─ Quality first ................. Q5_K_M or Q6_K
│     └─ Plenty of disk, want no loss ... Q8_0
│
├─ vLLM / TGI (server, many users) ─────► AWQ (preferred) or GPTQ
│
└─ Not enough VRAM during training ─────► bitsandbytes NF4 (QLoRA)
      (Not a distribution format; merge + quantize after training)
```

The same decision as a table:

| Format | When to choose | Quality / speed balance | Tool compatibility |
|---|---|---|---|
| **GGUF** | Personal use, Ollama/LM Studio, mixed CPU+GPU | Balanced at Q4_K_M/Q5_K_M; widest support on CPU | llama.cpp ecosystem, Unsloth |
| **NF4 + bitsandbytes** | Only to free VRAM during training | Training-oriented; not suitable for distribution | transformers + PEFT |
| **AWQ / GPTQ** | GPU serving, multi-user service | Mature solutions for 4-bit serving | vLLM, TGI |
| **FP8** | High-throughput serving on Hopper/Ada-class cards | 8-bit; FP8 acceleration wants hardware | vLLM |

The rule is simple: **NF4 in training, GGUF locally, AWQ/GPTQ/FP8 on the server.**

## GGUF levels: what do the letters in Q4_K_M mean?

The codes in GGUF file names are briefly:

- **Q4 / Q5 / Q8**: bits per weight (4-bit, 5-bit, 8-bit...).
- **K**: "k-quant" — a smart distribution scheme giving more bits to sensitive layers and fewer to robust ones.
- **\_M / \_S**: quality/size variants within the same level (M = medium, S = small).

Commonly seen levels:

| Level | Quality | Advice |
|---|---|---|
| Q2_K, Q3_K | Noticeable loss | Don't use unless forced |
| **Q4_K_M** | Very good balance | **The default recommendation**; most people stop here (it is also llama.cpp's quantizer default) |
| Q5_K_M | Very close to fp16 | Prefer it if memory allows |
| Q6_K | Nearly lossless | If you are quality-focused |
| Q8_0 | Indistinguishable | If you have the space; practically considered lossless |

Distinguishing the scheme families makes file names easier to read. The llama.cpp docs speak of three families:

- **Legacy schemes** (`Q4_0`, `Q5_0` etc.): the first generation; a simple scheme using a single scale per block.
- **K-quants** (`Q2_K` ... `Q6_K`): a scheme using different block and scale layouts per layer type; today the main family of balanced levels.
- **i-quants** (`IQ2_XXS`, `IQ3_XXS`, `IQ4_XS` etc.): a family built around the "importance" concept; it aims to preserve quality at low sizes especially in the aggressive 2-4-bit range.

:::caution
So two advanced recommendations don't get mixed up: **K-quant** levels like Q4_K_M fit every model and want no extra steps; i-quant levels reach their best value with an importance matrix (below). If you are just starting, stay with Q4_K_M.
:::

### imatrix: quantization with an importance matrix

llama.cpp's `llama-imatrix` tool runs the model through a sample text corpus and produces an **importance matrix** measuring how much the weights contribute to the output. When `llama-quantize` receives this matrix with the `--imatrix` flag, it picks which weights to leave at which precision based on this measurement rather than roughly. The i-quant levels were designed together with this matrix; they can also be used with K-quants. Typical flow:

```bash title="imatrix_example.sh"
# 1) Compute the importance matrix (for Turkish use, the corpus should be Turkish)
./llama-imatrix -m model-f16.gguf -f sample-text.txt -o imatrix.gguf

# 2) Quantize to an i-quant level using the matrix
./llama-quantize --imatrix imatrix.gguf model-f16.gguf model-IQ4_XS.gguf IQ4_XS
```

Flag names can change between versions; check the tools' `--help` output. The current official quantization doc lives in the repo under `tools/quantize/README.md`. Community practice is to use a corpus resembling your training data or covering the target language; if the model was trained for Turkish, feeding Turkish text makes sense.

### Dynamic (UD) quantizations: news-level

Beyond the fixed levels (the same bits for every layer) there is also a "dynamic" approach: Unsloth's Dynamic (UD) quantizations pick a separate quantization type per layer; the company markets it as "selectively quantizes layers, dynamically setting each layer's quantization type" and claims higher accuracy at the same disk size (the vendor's own measurement). The news value is here: in January 2025, Unsloth published 1.58-bit (UD-IQ1_S) and 1.78-bit (UD-IQ1_M) GGUF variants of the 671B-parameter DeepSeek-R1; the aim was to make this model — which wants terabyte-scale memory in its full form — runnable on high-RAM workstations, largely on CPU load. These extreme levels are not the quality sweet spot; for a beginner Q4_K_M / Q5_K_M is still the right choice.

## Converting: from a Hugging Face model to GGUF

Prerequisite: you must have a **merged** HF model (if your model has an adapter, first [LoRA Merging](/en/kullanim/lora-birlestirme/)). The flow: HF model → intermediate GGUF (fp16) → quantized GGUF.

```bash title="gguf_convert.sh"
# 1) Clone the llama.cpp repo (for the conversion scripts and the quantizer)
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# 2) Install the conversion script's Python dependencies
pip install -r requirements.txt

# 3) Convert the HF model to an fp16 intermediate GGUF
python convert_hf_to_gguf.py ../merged-model \
    --outfile model-f16.gguf \
    --outtype f16

# 4) Quantize the intermediate file to the Q4_K_M level
./llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

A few notes:

- The conversion script's `--outtype` options are limited to `f32`, `f16`, `bf16` and `q8_0` (and some exotic types); the K-quant and i-quant levels need the `llama-quantize` step.
- To produce multiple variants, just repeat steps 3 and 4 with different levels (Q4_K_M, Q5_K_M, Q8_0...).
- For a one-off conversion you don't have to compile the whole repo; but the quantizer tool is the part doing the real work.

:::tip If you're on Windows
You don't have to compile llama.cpp: download and extract one of the ready Windows packages (CPU or CUDA version) from the GitHub Releases page; the `llama-quantize.exe` inside runs directly. If you want to compile it yourself, the executables land under `build\bin\Release`.
:::

### One-line GGUF with Unsloth

If you trained with Unsloth, it also handles the conversion:

```python title="unsloth_gguf.py"
# Unsloth merges the adapter automatically and produces the GGUF (it uses llama.cpp under the hood)
model.save_pretrained_gguf(
    "model_gguf",            # output folder
    tokenizer,
    quantization_method = "q4_k_m",
)
```

Unsloth sets the llama.cpp path itself in some environments; if you hit an error like "llama.cpp not found", see the GGUF section of the Unsloth docs. Pushing the model to Hugging Face directly as GGUF is also possible (`push_to_hub_gguf`); we cover that on the [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/) page.

### Running the GGUF from Python

If you want to try the converted file right away:

```bash
pip install llama-cpp-python
```

```python title="run_gguf.py"
from llama_cpp import Llama

llm = Llama(
    model_path="model-Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,   # move all layers to the GPU; leave at 0 for CPU
)

output = llm.create_chat_completion(
    messages=[{"role": "user", "content": "Explain quantization in one sentence."}]
)
print(output["choices"][0]["message"]["content"])
```

For daily use the most practical path is [Ollama](/en/kullanim/ollama/).

## How Much Does Quality Drop?

Two questions everyone asks:

**1. What's the difference between Q4 and Q8 of the same model?** In most chat tasks the difference is small; it starts growing in multi-step reasoning, math, code and under-represented languages. In languages with less data than English — like Turkish — the quantization effect can sometimes be more visible; in critical tests, try stepping up to Q5_K_M.

**2. "A 4-bit 8B, or an fp16 3B?"** Community experience and measurements generally show the quantized **large** model remaining more capable than the fp16 **small** one: knowledge comes mostly from the parameter count and Q4_K_M is a moderate compression. The exception is aggressive levels like Q2/Q3; there, the quality loss can flip this difference. Make the final call on your own tasks: [Benchmarks and Evaluation](/en/degerlendirme/benchmarklar/).

:::caution One final warning
Quantization is done on the merged (fp16) model. Trying to merge your QLoRA adapter into a quantized base model is a common and costly mistake; details on the [LoRA Merging](/en/kullanim/lora-birlestirme/) page.
:::

## Sources and Further Reading

- [llama.cpp — tools/quantize README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md): the official doc for `llama-quantize` usage, the K-quant/i-quant split and the imatrix flag.
- [llama.cpp repo](https://github.com/ggml-org/llama.cpp): the main source of the conversion tools, including `convert_hf_to_gguf.py`.
- [Transformers — bitsandbytes docs](https://huggingface.co/docs/transformers/quantization/bitsandbytes): the official explanation of NF4, double quantization and 4-bit loading settings.
- [vLLM — Quantization](https://docs.vllm.ai/en/latest/features/quantization/index.html): the current list of quantized formats vLLM serves directly.
- [vLLM — FP8 W8A8](https://docs.vllm.ai/en/v0.6.4/quantization/fp8.html): the doc defining the hardware (compute capability) conditions for FP8.
- [AWQ paper](https://arxiv.org/abs/2306.00978) and [GPTQ paper](https://arxiv.org/abs/2210.17323): the original papers of activation-aware and GPU-serving-oriented quantization methods.
- [QLoRA paper](https://arxiv.org/abs/2305.14314): the original paper introducing the NF4 data type.
- [Unsloth — DeepSeek-R1 Dynamic 1.58-bit](https://unsloth.ai/blog/deepseekr1-dynamic): the blog post announcing the dynamic (UD) low-bit quantizations.
- [Unsloth — Saving to GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf): the official doc of GGUF export steps with Unsloth.
- [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/): a comparison of the **confidence distributions** of the same model's Q4 vs a higher-bit version was not measured on this site; it stands on that page's "Not Measured" list, since it requires downloading a second model.

## Next Steps

- To add your GGUF model to Ollama and chat with it: [Run Your Own Model with Ollama](/en/kullanim/ollama/)
- For multi-user serving: [Model Serving: vLLM and API](/en/kullanim/sunma-api/)
- To share the model with the community: [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/)
