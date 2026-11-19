---
title: "Introduction: What Is This Guide, Who Is It For?"
description: "The purpose, target audience, scope and most efficient ways to use the Model Training Guide — written to close a real gap in Turkish-language resources; English translation in progress."
dogrulama: 2026-11-19
---

One of the most common sentences in Turkish-language resources is this: "I want to train my own model but I have no idea where to start." While the English side has thousands of blog posts, videos and open-source repositories, Turkish content usually stays superficial or is limited to a few disconnected examples. The **Model Training Guide** was written precisely to close that gap: it walks through the entire process — from finding data to cleaning it, from training a model to evaluating it and wiring it into an application — from scratch, step by step, in Turkish. This English surface is a growing translation of that guide.

The guide covers a wide range: text models (LLMs), image generation models and classic machine learning. The goal is never to wave a topic through with a "surely everyone knows this" assumption: every concept is explained first through intuition, then with real parameters and numbers, and finally with runnable examples.

:::tip[Three principles of the guide]
1. **Intuition first, detail second, practice last.** Every topic starts with "why does this exist?"
2. **Real numbers.** Instead of saying "a small model", it uses concrete values like "Qwen3-4B weights take roughly 8 GB in fp16".
3. **No fabrication.** For variable information — prices, versions, model lists — you will see "as of 2026" and an encouragement to check the current value.
:::

:::note[Do you need coding experience?]
Most examples are written in Python. Being familiar with variables, loops and functions helps but is **not required**: every section explains from scratch and code blocks are annotated line by line. If you have never touched code, the gentlest starting point is the [Classic Machine Learning](/en/klasik-ml/temeller/) section.
:::

## Who Was This Guide Written For?

The guide assumes no particular prior knowledge. If you recognize yourself in one of these groups, you are in the right place:

- **Curious beginners:** people chasing the question "how are AI models trained?" who have never trained one.
- **Students:** undergraduate and graduate students who need to train a model on their own data for a capstone, thesis or course.
- **Software developers:** developers who know Python, are new to machine learning, and want to add a model to their application.
- **People who want to customize a model:** individuals and small teams who want to adapt an existing model to their own style, domain knowledge or data format.
- **Turkish speakers:** anyone who struggles to follow English resources or works with Turkish data. The data section separately covers Turkish-specific resources and pitfalls.

**Prerequisites:** basic Python helps but is not a hard requirement. Being comfortable with files and folders is enough; the guide builds the rest step by step.

## What Does "Training a Model" Mean? Five Scenarios

Training a model is not one thing. In the industry, the phrase is used for at least five different jobs, and knowing which one you mean is the first step to choosing the right path.

### 1. Customizing an existing model with fine-tuning

**This is the most common scenario.** The large model you have (say Qwen3-8B or Gemma 3) already knows language; you teach it to "do this job in this style" with your own data. With methods like LoRA/QLoRA this can be done on a single consumer GPU with 8-12 GB of VRAM. This scenario is the backbone of the guide: start with [LoRA and QLoRA](/en/llm/lora-qlora/) and [SFT](/en/llm/sft/).

### 2. Pretraining a language model from scratch

Initializing a model with random weights and teaching it language from billions of words. GPT-4-class models are trained this way at a cost of millions of dollars. **We will not do this in the guide** — but seeing a small-scale version of the same process (a few hundred MB of text, one GPU, a few hours) is invaluable for understanding how training works: [Pretraining](/en/llm/pretraining/).

### 3. Training an image model (LoRA)

Teaching a Stable Diffusion-style diffusion model a new style, object or character with your own images. Largely the same logic as LoRA on the text side: the base model freezes, a small extra layer is trained. [Diffusion Fundamentals](/en/gorsel/diffusion-temelleri/) and [Image LoRA Training](/en/gorsel/lora-egitimi/).

### 4. A classic machine learning model

Building a predictive model from tabular data (Excel-like rows and columns): house price prediction, customer churn, classification. It may live in the shadow of LLMs, but most real-world corporate jobs are still solved with these models — and without a GPU, in seconds. [Classic ML Fundamentals](/en/klasik-ml/temeller/) and [Your First Model](/en/klasik-ml/ilk-model/).

### 5. Just using a model (inference)

Downloading and running a model without training it: chatting, summarizing, generating code. Outside the guide's main scope, but you will need exactly these skills to run the model you train: [Ollama](/en/kullanim/ollama/) and [Serving and API](/en/kullanim/sunma-api/).

:::note[One-sentence summary]
This guide teaches scenarios 1-4 from scratch; for scenario 5 it provides the practical pages.
:::

## How Should You Use This Guide? Three Paths

You do not have to read it cover to cover like a book. Pick the path that fits you:

### Path 1 — Quick Start (first training in 1-2 days)

If your goal is to see a working training run as soon as possible, follow this order:

1. [VRAM Math](/en/donanim/vram-hesabi/) — which model can your hardware train?
2. [Cloud Options](/en/donanim/bulut-secenekleri/) — hourly rentals if you have no GPU.
3. [Data Formats](/en/veri/veri-formatlari/) — what should a training data file look like?
4. [LoRA and QLoRA](/en/llm/lora-qlora/) — why train a small add-on instead of the whole model?
5. [Step-by-Step Training](/en/llm/adim-adim-egitim/) — we run your first training together.
6. [Ollama](/en/kullanim/ollama/) — make your trained model talk on your own computer.

:::caution[The price of the fast path]
On this path you skip fundamentals like attention, tokenizer details and loss functions. When training behaves unexpectedly (and it will), you will need to return to the [Fundamentals](/en/temeller/transformer/) section to understand why.
:::

### Path 2 — Solid Foundation (in order, front to back)

If you want to understand machine learning properly, read the pages in the site menu's order: Getting Started → Fundamentals → Hardware → Data → LLM Training → Image Models → Classic ML → Evaluation → Usage and Publishing. This path takes longer but takes you from the "copy-paste" level to the "able to make your own decisions" level. Your starting point: [Core Concepts](/en/baslangic/kavramlar/).

### Path 3 — Jump by Need

If you have a single goal, go straight to it:

| My goal | What I should read |
| --- | --- |
| Train a Turkish chat assistant | [SFT](/en/llm/sft/), [LoRA and QLoRA](/en/llm/lora-qlora/), [Turkish data sources](/en/veri/veri-nereden-bulunur/) |
| Customize a model with my own data | [Create your own dataset](/en/veri/kendi-verini-olustur/), [Data cleaning](/en/veri/veri-temizleme/), [Step-by-step training](/en/llm/adim-adim-egitim/) |
| My own style in image generation | [Image LoRA Training](/en/gorsel/lora-egitimi/) |
| Predictions from tabular data | [Classic ML Fundamentals](/en/klasik-ml/temeller/), [Your First Model](/en/klasik-ml/ilk-model/) |
| Understand model training concepts | [Core Concepts](/en/baslangic/kavramlar/), [How Does Training Work?](/en/temeller/egitim-nasil-calisir/) |

If you are not sure which method suits you, the [Roadmap](/en/baslangic/yol-haritasi/) page makes this decision based on your hardware and goal.

## What Is in Each Section?

| Section | What it covers | First page |
| --- | --- | --- |
| Getting Started | Guide tour, core concepts, method choice | [Introduction](/en/baslangic/giris/) |
| Fundamentals | Transformer architecture, tokenization, the training loop | [Transformer](/en/temeller/transformer/) |
| Hardware | VRAM math, local setup, cloud options | [VRAM Math](/en/donanim/vram-hesabi/) |
| Data | Data types, where to find it, formats, cleaning, your own data | [Data Types](/en/veri/veri-turleri/) |
| LLM Training | Pretraining, SFT, LoRA/QLoRA, DPO, tools, troubleshooting | [Pretraining](/en/llm/pretraining/) |
| Image Models | Diffusion fundamentals, image LoRA training | [Diffusion Fundamentals](/en/gorsel/diffusion-temelleri/) |
| Classic ML | Machine learning basics, first model on tabular data | [Classic ML Fundamentals](/en/klasik-ml/temeller/) |
| Evaluation | Loss and metrics, benchmarks | [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) |
| Usage and Publishing | LoRA merging, quantization, Ollama, API, Hugging Face | [LoRA Merging](/en/kullanim/lora-birlestirme/) |
| Resources | FAQ, glossary, useful links | [FAQ](/en/kaynaklar/sss/) |

## Two Notes on Terminology and Freshness

- **English terms:** The original guide is in Turkish and introduces every important English term with its Turkish equivalent at first use — "ince ayar (fine-tuning)" — then uses it consistently. This English translation keeps the original Turkish term in parentheses where the Turkish-specific context matters. The guide's preferred term pairs are always available on the [Glossary](/en/kaynaklar/sozluk/) page.
- **Freshness:** The guide reflects the ecosystem as of 2026. Model versions, cloud prices and tool versions change fast; you will see "as of 2026" notes next to variable information. We recommend verifying against official sources before critical decisions (model choice, cloud purchases).

## Realistic Expectations

### What will you learn?

- **Customizing** an existing model with your own data (fine-tuning with LoRA/QLoRA).
- Collecting, cleaning and formatting data, and calculating a **token budget**.
- **Monitoring and evaluating** training: loss curves, early stopping, benchmarks.
- **Quantizing** the model you trained, running it on your own computer, serving it as an API and sharing it on Hugging Face.
- Building classic machine learning models on tabular data and training LoRAs for image models.

### What is out of scope

- **Distributed training:** megatron-style infrastructures coordinating dozens of GPUs. We focus on one GPU and one node.
- **Training a frontier model from scratch:** pretraining GPT-4-class models needs a budget of millions of dollars and thousands of GPUs; apart from small-scale learning experiments, we stay away.
- **Research-level mathematics:** topics like attention derivatives and optimization theory are explained conceptually, not at academic depth.
- **Data labeling operations:** we cover the engineering side of data collection; running large labeling teams is a separate discipline.

### How long does it take?

Reading the whole guide takes from a few hours to a few weeks (depending on your intensity). You can usually run your first LoRA training **on day one**; however, preparing a good dataset — trial and error included — often takes longer than the training itself. Be patient: the most valuable skill in this guide is data preparation.

## The 5 Most Common Mistakes While Learning

All of these mistakes are emphasized repeatedly throughout the guide; it helps to know them up front:

1. **Starting from the model, not from the data.** Everyone asks "which model should I train?"; yet data decides a project's fate. Understand the [Data](/en/veri/veri-turleri/) section first.
2. **Setting a giant goal in one shot.** Instead of "I'll build a ChatGPT rival", start with small, measurable goals like "I'll train a small model that imitates my style"; each success is the infrastructure for the next.
3. **Thinking about hardware later.** Model choice cannot be made independently of hardware; the first step should always be [VRAM Math](/en/donanim/vram-hesabi/).
4. **Skipping evaluation.** "The outputs look nice" is not a measurement. Without benchmarks and loss metrics you cannot see improvement or regression: [Evaluation](/en/degerlendirme/loss-ve-metrikler/).
5. **Running code you do not understand.** Ready-made notebooks are a great start, but if you do not know what each line does you are helpless when an error appears. Code blocks in this guide are annotated for that reason.

## When You Need Help

When you hit an error message during training, do not panic: the [Troubleshooting](/en/llm/sorun-giderme/) page lists the most common errors and their fixes. For concept tangles there is the [Glossary](/en/kaynaklar/sozluk/), for frequent questions the [FAQ](/en/kaynaklar/sss/), and for tool hunting [Useful Links](/en/kaynaklar/faydali-linkler/).

If you are ready, two routes await: to learn concepts in order, [Core Concepts](/en/baslangic/kavramlar/); to decide directly, [Roadmap](/en/baslangic/yol-haritasi/). The interactive method selector on the [Turkish home page](/) is currently Turkish-only.
