---
title: "Roadmap: Which Method, on Which Hardware?"
description: "Choosing the right model training method for your hardware, goal and budget — with a decision tree, comparison tables and real scenarios."
dogrulama: 2026-11-19
---

The most expensive mistake in model training is starting with the wrong method: trying to fully train an 8B model on a 4 GB VRAM card, or renting a GPU to attack a problem that classic machine learning would solve. The goal of this page is to put you **on the right road from day one**.

## The Right Choice in Three Questions

The answer to which method you should pick lies at the intersection of three questions:

1. **What do I have?** Your hardware sets the upper bound. No GPU, 6 GB VRAM, 12 GB, 24 GB, multiple GPUs... The way to measure it: [VRAM Math](/en/donanim/vram-hesabi/).
2. **What do I want?** A Turkish chatbot? Domain knowledge? Style? Image generation? Prediction from tabular data? The goal determines the size of the model to train and the data need.
3. **How much time and money can I spend?** Local training is free but slow; cloud is fast but billed hourly. Comparison: [Cloud Options](/en/donanim/bulut-secenekleri/).

:::tip[Interactive alternative]
The interactive "method selector" on the home page asks the same questions and gives you a suggestion: [Turkish home page](/). This page is the full decision guide, with the reasoning.
:::

## Decision Tree

The diagram below summarizes a typical user's path from hardware to method. Find your own situation and follow the arrows:

```text title="Simplified method-selection tree"
Start
│
├── Do I have a GPU?
│   │
│   ├── NO
│   │   ├── Goal: learn / experiment ───────► Kaggle (~30 free GPU hours/week)
│   │   │                                     or Google Colab (free T4)
│   │   ├── Goal: predict from tables ──────► Classic ML — CPU is enough
│   │   │                                     /en/klasik-ml/ilk-model/
│   │   └── Goal: serious model training ───► Rent a cloud GPU (RunPod, Vast.ai)
│   │                                         /en/donanim/bulut-secenekleri/
│   │
│   └── YES — how many GB of VRAM?
│       ├── 4-6 GB   ──► 0.5-2B model + QLoRA (local)
│       │                or 4B QLoRA in the cloud
│       ├── 8-12 GB  ──► 4B QLoRA comfortably; 3B LoRA
│       ├── 16-24 GB ──► 7-8B QLoRA; 8B LoRA
│       ├── 24 GB+   ──► 13-14B LoRA (with QLoRA)
│       └── 48 GB+ / multi-GPU ──► 13-14B LoRA comfortably; bigger experiments
│
└── What is my goal?
    ├── Turkish chat assistant ──────► SFT on instruction data (LoRA/QLoRA)
    ├── Domain knowledge (law/med/tech) ► SFT + quality domain data (consider RAG too)
    ├── Teach style/format ───────────► LoRA with small but consistent data
    ├── Image generation ─────────────► Diffusion model + LoRA
    └── Predict from tables ──────────► Classic ML (scikit-learn, XGBoost)
```

## Table 1 — What Can You Train, by Hardware?

The table below shows practical ranges: the "locally comfortable" column runs without trouble, while the "borderline" column needs small batches and patience. The full memory math is on [VRAM Math](/en/donanim/vram-hesabi/).

| Hardware (VRAM) | Locally comfortable | Borderline (small batch) | Recommended path |
| --- | --- | --- | --- |
| No GPU | Classic ML (CPU) | — | Free GPU via Kaggle/Colab or hourly cloud rental |
| 4-6 GB | QLoRA on 0.5-2B models | 3B QLoRA | Small local experiments + 4B QLoRA in the cloud |
| 8-12 GB | 3-4B QLoRA, 3B LoRA | 7B QLoRA (very small batch) | Local QLoRA with Unsloth — the sweet spot |
| 16-24 GB | 7-8B QLoRA, 8B LoRA | 13B QLoRA | Serious local projects |
| 24 GB+ | 13-14B LoRA comfortably | 30B+ QLoRA | Production-level work |
| Multi-GPU / cloud | 30B+ LoRA, small full fine-tuning | — | Big experiments on rented H100/H200 |

:::caution[What does "comfortable" mean?]
"Comfortable" in the table means training finds enough memory not to crash; speed is not guaranteed. A 4B QLoRA model can take hours on a 12 GB card while the same job takes minutes in the cloud. Speed depends on the card's generation (e.g. there is a large gap between an RTX 3060 and a 4090) and on the training software.
:::

## Table 2 — Which Method, by Goal?

| Goal | Recommended approach | Starting page |
| --- | --- | --- |
| Turkish chat assistant | SFT on instruction data + QLoRA (start with Qwen3-4B/8B) | [SFT](/en/llm/sft/) |
| Teaching domain knowledge (law, medicine, technical) | SFT on domain data; consider RAG for current knowledge: [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/) | [Create your own dataset](/en/veri/kendi-verini-olustur/) |
| Teaching style and format | LoRA with 100-1,000 consistent examples; the easiest and most successful scenario | [LoRA and QLoRA](/en/llm/lora-qlora/) |
| Image generation (style, character, object) | Train a LoRA on a diffusion model | [Image LoRA Training](/en/gorsel/lora-egitimi/) |
| Prediction from tabular data | Classic ML — often more accurate and much faster than an LLM | [Your First Model](/en/klasik-ml/ilk-model/) |
| Research / curiosity | A small-scale pretraining experiment (one GPU, a few hours) | [Pretraining](/en/llm/pretraining/) |

## Tool Choice: Which Tool for Which Job?

Once the method is decided, the tool comes next. As of 2026, the leading options and where they fit:

| Tool | For whom? | Character |
| --- | --- | --- |
| Unsloth | Individual users with a single GPU | Speed and ease focused; the most practical start for a first QLoRA experience |
| Axolotl | Production work, multi-GPU, those who want reproducibility | Managed via a YAML config file; fits version control |
| LLaMA-Factory | Those who do not want to write code, seekers of a GUI | Web UI + command line; supports 100+ models |
| HF TRL | Those who want full control in code | Hugging Face's SFT/DPO/GRPO trainers; library-level flexibility |
| PEFT + bitsandbytes | Advanced users who want to wire the infrastructure themselves | The core of LoRA and 4-bit layers; most other tools are built on top of it |

:::tip[Which one to start with?]
For your first training, Unsloth (fast results) or LLaMA-Factory (interface) are the gentlest options. If you will build a reproducible, scripted production pipeline, move to Axolotl. Tool comparison: [Tools](/en/llm/araclar/).
:::

## Real Scenarios: Four Typical Paths

Instead of abstract tables, let's look at four typical user profiles. You can follow the steps of the one closest to you.

### Scenario A — "I have a GTX 1650 with 4 GB, I want a Turkish chatbot"

4 GB of VRAM allows QLoRA only on 0.5-2B models locally; that is a bit tight for a quality Turkish chat assistant. The most practical solution: train in the cloud. Google Colab's free T4 or an hourly RTX 4090 on RunPod comfortably trains Qwen3-4B with QLoRA (as of 2026, a RunPod 4090 starts around $0.34/hour; check the current price).

1. [Core Concepts](/en/baslangic/kavramlar/) — learn what QLoRA and SFT mean.
2. [Turkish data sources](/en/veri/veri-nereden-bulunur/) — review the ready Turkish instruction sets (e.g. the `atasoglu/turkish-instruction-datasets` collection on Hugging Face).
3. [Data Cleaning](/en/veri/veri-temizleme/) — even ready datasets want cleaning.
4. [Cloud Options](/en/donanim/bulut-secenekleri/) — Colab or a rented GPU?
5. [LoRA and QLoRA](/en/llm/lora-qlora/) and [Step-by-Step Training](/en/llm/adim-adim-egitim/) — run the training.
6. [Benchmarks](/en/degerlendirme/benchmarklar/) — measure the result.
7. [LoRA Merging](/en/kullanim/lora-birlestirme/) and [Ollama](/en/kullanim/ollama/) — run the model on your own computer.

### Scenario B — "With an RTX 3060 12 GB, I want to teach my model my own style"

12 GB is the local sweet spot for this job: 4B QLoRA is comfortable with Unsloth, 7-8B QLoRA is borderline but possible. Style teaching needs little data (100-1,000 examples), so you can get results in a single session.

1. [Local Setup](/en/donanim/yerel-kurulum/) — set up the environment.
2. [Create Your Own Dataset](/en/veri/kendi-verini-olustur/) — collect your style examples (your existing writing is a great source).
3. [Tools](/en/llm/araclar/) — get to know Unsloth.
4. [LoRA and QLoRA](/en/llm/lora-qlora/) → [Hyperparameters](/en/llm/hiperparametreler/) → [Step-by-Step Training](/en/llm/adim-adim-egitim/).
5. [Troubleshooting](/en/llm/sorun-giderme/) — if training behaves unexpectedly (and it will), come back here.
6. [Serving and API](/en/kullanim/sunma-api/) — connect the model to your own application.

### Scenario C — "I have no GPU, I just want to learn"

You can proceed without buying anything. Follow a two-legged plan: learn classic machine learning on CPU, and experiment with the LLM side using Kaggle's ~30 free GPU hours per week.

1. [Classic ML Fundamentals](/en/klasik-ml/temeller/) → [Your First Model](/en/klasik-ml/ilk-model/) — train a real model without a GPU.
2. [Tokenization](/en/temeller/tokenizasyon/) — your entry into the LLM world.
3. [Cloud Options](/en/donanim/bulut-secenekleri/) — learn the rules of Kaggle and Colab.
4. [Step-by-Step Training](/en/llm/adim-adim-egitim/) — run a small QLoRA experiment in a Kaggle notebook (1,000 examples, small model).
5. [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) — learn to read the training curves.

### Scenario D — "I need to train a domain model on company data"

In this scenario you deal with **data** more than code; realistically, 70-80% of the job is data preparation. On the model side, SFT on instruction data (with LoRA) is enough to start; evaluation must be planned from the beginning.

1. [Data Types](/en/veri/veri-turleri/) — which category does your data fall into?
2. [Create Your Own Dataset](/en/veri/kendi-verini-olustur/) + [Data Cleaning](/en/veri/veri-temizleme/) + [Data Formats](/en/veri/veri-formatlari/).
3. [SFT](/en/llm/sft/) — designing instruction-data training.
4. [Hyperparameters](/en/llm/hiperparametreler/) — tuned to your company GPU.
5. [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) and [Benchmarks](/en/degerlendirme/benchmarklar/) — measure your definition of "good".
6. [Serving and API](/en/kullanim/sunma-api/) and [Hugging Face Sharing](/en/kullanim/huggingface-paylasim/) (or an in-company repository).

## Time and Cost Expectations

:::note[Typical runtimes]
- **QLoRA training:** with 1,000-5,000 examples, **30 minutes to 6 hours** depending on hardware. The same job can take hours on free Colab but drop under 1 hour on a rented 4090.
- **Data preparation:** in most projects this takes **longer** than the training itself. Days if you collect data from scratch; hours if you adapt a ready dataset.
- **Evaluation and iteration:** the first training is usually not the last; 2-4 rounds of trial is normal.
- **Cost example (as of 2026, subject to change):** an RTX 4090 on Vast.ai costs roughly $0.14-0.45/hour; a 4090 on RunPod starts around $0.34. A 4-hour training rental comes to roughly $1-2. Always check current prices.
:::

Also, do not underestimate the free options: Google Colab offers a T4 on the free tier (Pro is about $10/month), and Kaggle gives about 30 free GPU hours per week. With that quota you can run real experiments on small models: [Cloud Options](/en/donanim/bulut-secenekleri/).

## Do Not Forget Classic ML

If your goal is prediction from tabular data (sales forecasting, churn, classification), you do not need to enter the LLM side at all. Classical models are often more accurate for these jobs, an order of magnitude faster, and free. Start here: [Classic ML Fundamentals](/en/klasik-ml/temeller/) and [Your First Model](/en/klasik-ml/ilk-model/).

:::tip[Next step]
Have you made your decision? To clarify cloud vs. local, [Cloud Options](/en/donanim/bulut-secenekleri/); for the memory math, [VRAM Math](/en/donanim/vram-hesabi/); for your first training, [Step-by-Step Training](/en/llm/adim-adim-egitim/). Still undecided? Try the interactive selector on the [Turkish home page](/).
:::
