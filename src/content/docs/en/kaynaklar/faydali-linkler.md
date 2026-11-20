---
title: "Useful Links and Resources"
description: "Learning resources, foundational papers, training tools, datasets and communities: a curated, verified link list as of 2026."
dogrulama: 2026-11-20
---

This page is the single, categorized list of the resources we recommend throughout the guide. The sentence next to each link explains why it's useful. The list should be kept alive; **the links were verified as of 2026.**

## Learning and courses

- [The Hugging Face LLM Course](https://huggingface.co/learn) — the official, free and hands-on course stretching from the transformer to fine-tuning; this guide's most natural English complement.
- [The Hugging Face Blog](https://huggingface.co/blog) — regular and reliable posts on new models, techniques and library announcements.
- [DeepLearning.AI](https://www.deeplearning.ai) — Andrew Ng's short, hands-on courses; a quick entry into basic ML and LLM topics.
- [3Blue1Brown — the Neural Networks Series](https://www.3blue1brown.com/topics/neural-networks) — neural networks and backprop intuition with animations; it should be the first stop of those afraid of math.
- [Andrej Karpathy — Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html) — building a language model from scratch with videos; the best answer to "what's happening inside?".
- [MIT 6.S191 — Introduction to Deep Learning](https://introtodeeplearning.com) — MIT's famous intensive course; an academic but accessible entry into deep learning, with slides and labs.

## Foundational papers

- [Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762) — the paper introducing the transformer architecture, the ancestor of all today's LLMs.
- [LoRA (2021)](https://arxiv.org/abs/2106.09685) — the original study of efficient fine-tuning with low-rank adapters.
- [QLoRA (2023)](https://arxiv.org/abs/2305.14314) — training LoRA on 4-bit-quantized base models; the method making big models possible on a single GPU.
- [Chinchilla (2022)](https://arxiv.org/abs/2203.15556) — the study answering "how much data, how many parameters?" with scaling laws.
- [InstructGPT / RLHF (2022)](https://arxiv.org/abs/2203.02155) — the foundational paper explaining how GPT models were aligned with human feedback.
- [DPO (2023)](https://arxiv.org/abs/2305.18290) — a far simpler and more practical alignment alternative to RLHF.
- [LIMA (2023)](https://arxiv.org/abs/2305.11206) — the study showing surprisingly good alignment is possible with 1,000 carefully chosen examples.

## Training and fine-tuning tools

- [unslothai/unsloth](https://github.com/unslothai/unsloth) — faster fine-tuning with less VRAM; one of the easiest starting tools, Windows included.
- [hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) — the ability to train hundreds of models through a single interface or CLI.
- [axolotl-ai-cloud/axolotl](https://github.com/axolotl-ai-cloud/axolotl) — production-quality training flows with YAML configurations.
- [huggingface/trl](https://github.com/huggingface/trl) — Hugging Face's official SFT, DPO and GRPO training library.
- [huggingface/peft](https://github.com/huggingface/peft) — the reference implementation of LoRA and similar efficient fine-tuning methods.
- [huggingface/transformers](https://github.com/huggingface/transformers) — the whole ecosystem's cornerstone; the standard library of model loading, training and inference.
- [UKPLab/sentence-transformers](https://github.com/UKPLab/sentence-transformers) — the reference library of embedding model training; the losses, `mine_hard_negatives` and the [training overview doc](https://sbert.net/docs/sentence_transformer/training_overview.html) are here. The rig on the [Training an Embedding Model](/en/rag/gomme-egitimi/) page was built with this library.

## Running and serving tools

- [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) — the heart of the GGUF ecosystem; the source of the quantization tools and CPU/GPU inference.
- [ollama/ollama](https://github.com/ollama/ollama) — local models on Windows with a single install; the easiest way to start.
- [vllm-project/vllm](https://github.com/vllm-project/vllm) — the GPU serving engine for high concurrency; the standard of production environments.
- [huggingface/text-generation-inference (TGI)](https://github.com/huggingface/text-generation-inference) — Hugging Face's Docker-based production serving engine.
- [open-webui/open-webui](https://github.com/open-webui/open-webui) — a chat interface for Ollama; a local-AI-platform feel with file upload and RAG support.
- [LM Studio](https://lmstudio.ai) — downloading GGUF models and chatting with a graphical interface; for those who want to try without writing code.

## Image model tools

- [kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts) — the industry-standard toolset of LoRA training on image models.
- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) — the most widespread Stable Diffusion interface; with its training extensions.
- [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) — node-based image generation flows; it visualizes complex pipelines.
- [huggingface/diffusers](https://github.com/huggingface/diffusers) — the library for running and training diffusion models from Python.

## Data resources

- [Hugging Face Datasets](https://huggingface.co/datasets) — tens of thousands of ready datasets; you can filter and load them directly with the `datasets` library.
- [FineWeb-2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) — a multilingual, web-scale, cleaned pretraining dataset including Turkish.
- [atasoglu — Turkish Instruction Datasets](https://huggingface.co/collections/atasoglu/turkish-instruction-datasets) — a tidy collection of Turkish instruction datasets; the first place to look for fine-tuning.
- [ogulcanaydogan/Turkish-LLM](https://github.com/ogulcanaydogan/Turkish-LLM) — Turkish LLM work: the open repo gathering data, models and experiments (the Hugging Face profile: [ogulcanaydogan](https://huggingface.co/ogulcanaydogan)).
- [kesimeg/awesome-turkish-language-models](https://github.com/kesimeg/awesome-turkish-language-models) — a curated list of Turkish language models and resources.
- [The Holmeister Turkish Evaluation Collection](https://huggingface.co/collections/Holmeister/turkish-llm-multi-prompt-evaluation-datasets) — a model evaluation package with 17 Turkish datasets and a multi-prompt arrangement.
- [Kaggle Datasets](https://www.kaggle.com/datasets) — competition and community datasets; a rich source for classic ML projects.
- [Common Crawl](https://commoncrawl.org) — web-scale open crawl data; pretraining data's raw material.

## Community and following

- [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA) — the community of running and training local models; the center of hardware, quantization and tool discussions.
- [The Hugging Face Discord](https://huggingface.co/join/discord) — the Hugging Face community's live chat; perfect for quick Q&A.
- [The Hugging Face Forum](https://discuss.huggingface.co) — a searchable Q&A archive about the libraries, models and datasets.
- [r/MachineLearning](https://www.reddit.com/r/MachineLearning) — academic and general machine learning discussions; summaries of new papers.
- Turkish communities: because university AI clubs' Discord/Telegram groups and Turkish ML forums change fast, we're not putting a fixed link here; you can find the current communities from a search engine with terms like "yapay zeka topluluğu Discord".

---

:::tip
The flow we recommend in this list: first determine your order with the [Roadmap](/en/baslangic/yol-haritasi/), keep the [Glossary](/en/kaynaklar/sozluk/) and [FAQ](/en/kaynaklar/sss/) pages beside you while learning, and move to the resources here on the subject you want to go deeper in.
:::
