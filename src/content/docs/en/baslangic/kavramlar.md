---
title: "Core Concepts: A Vocabulary for Model Training"
description: "From AI to LoRA, from the training loop to quantization: the 30 core concepts of model training explained in four layers, with analogies and examples. Turkish equivalents included."
dogrulama: 2026-11-19
---

Everything written about model training seems full of terms: loss, epoch, gradient, embedding. This page explains those terms in **four layers**, from the most basic to the most specific. The goal is not memorization; it is to tie every concept to an analogy and, where possible, a concrete number. Where the Turkish original uses a specific term, the Turkish equivalent appears in parentheses — useful when reading Turkish pages, papers or datasets.

:::note[Looking for a quick reference?]
This page is the narrative version. If you do not want a long read, see the [Glossary](/en/kaynaklar/sozluk/) page with one-line definitions. Both cover the same terms, but the narrative here also answers the "why" question.
:::

## Layer 1: The Most Basic Concepts

### Artificial intelligence

The umbrella name for the effort of making computers do tasks that look human. Chess programs, recommendation systems, chatbots — all count as AI. **Analogy:** if AI is a toolbox, the concepts below are the different tools inside it.

### Machine learning (makine öğrenmesi)

An approach that teaches the model to **extract rules from examples** instead of writing rules by hand. Instead of writing your email filter a rule like "mark as suspicious anything containing 'free' and a link", you show it 10,000 spam and 10,000 normal emails and let it find the pattern. Nearly all of AI's current success comes from this approach.

### Deep learning (derin öğrenme)

The branch of machine learning that uses **multi-layer artificial neural networks**. "Deep" refers to the number of layers. On complex data like images, audio and text it beats classical methods by a wide margin. Today's LLMs and diffusion models are all deep learning models. For how layers work, see [Transformer Architecture](/en/temeller/transformer/).

### Model

The mathematical structure that emerges from the learning process, made of parameters (numbers). Think of it as a function: text in, text out; image in, label out. The model itself consists of a few `.safetensors` files and its size is measured in gigabytes.

### Dataset (veri seti)

The collection of examples used for the model to learn from. Usually split into three: the **training set** (what the model sees), the **validation set** (what we check during training to detect memorization) and the **test set** (the final exam at the very end, on data never touched). Why this split is critical is explained on [How Does Training Work?](/en/temeller/egitim-nasil-calisir/)

### Feature and label (özellik / hedef)

In tabular data, columns split into two: the columns the model **sees as input** are features; the column we **want it to predict** is the label. Example: in house price prediction, "square meters, room count, location" are features; "price" is the label. In practice: [Your First Model](/en/klasik-ml/ilk-model/).

## Layer 2: The Training Process

### Parameter and weight (parametre / ağırlık)

The **numbers the model learns** during training. "A 7B model" means "a model with 7 billion parameters". Parameter count determines both the model's capacity and its memory need: each parameter takes 2 bytes in fp16 precision, so a 7B model asks for roughly **14 GB** of VRAM for its weights alone. The full math: [VRAM Math](/en/donanim/vram-hesabi/).

### Training (eğitim)

The process of updating parameters step by step over the examples in the data. Numbers that start random get a little closer to reality with every step. **Analogy:** a long calibration process with continuous small corrections.

### Inference (çıkarım)

A trained model producing an answer for a new input. Unlike training, parameters **do not change** here; only a forward pass is computed. That is why inference is orders of magnitude cheaper than training, but its speed depends on model size and hardware. In practice: [Ollama](/en/kullanim/ollama/).

### Loss (kayıp)

The difference between the model's prediction and the true answer, condensed into **a single number**. It is the compass of training: our goal is to make this number smaller. Example: if loss dropped from 3.2 to 1.4, training is going well; how to read the curves is on [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).

### Epoch

**One full pass** over the entire training set. If you train on 10,000 examples and the model has seen each once, you completed 1 epoch. Since models start memorizing on very small datasets, 1-3 epochs are usually enough.

### Batch and step

A **batch** is the group of examples processed at once (say 8 examples). A **step** is one parameter update made with one batch of data. Quick math: 10,000 examples ÷ batch 8 = **1,250 steps per epoch**. If GPU memory is small, the batch is reduced; for stability, the effective batch is enlarged with gradient accumulation.

### Learning rate (öğrenme oranı)

The coefficient that determines **how fast** parameters change with each update. Too large and the model oscillates and fails to learn; too small and training takes forever. Typical values in LoRA fine-tuning are between 1e-4 and 2e-4; for tuning guidance, [Hyperparameters](/en/llm/hiperparametreler/).

### Checkpoint

A **snapshot of the model** saved to disk at intervals during training. If training crashes, you resume from the last checkpoint; the best checkpoint (lowest validation loss) is also kept for later stages. **Analogy:** a save point in a video game.

## Layer 3: Language Models

### Token

The smallest piece of text the model sees. For example, the Turkish word `yapabileceklerimizden` splits into roughly 6-8 tokens in a typical tokenizer for Turkish. The sentence is first split into tokens, then each token is mapped to a numeric identity (id). Full story: [Tokenization](/en/temeller/tokenizasyon/).

### Tokenizer (tokenizasyon)

The tool that splits text into tokens and maps each token to an id. Every model family has its own tokenizer and it is **not interchangeable**; the ids a model learned are only meaningful with its own tokenizer. Vocabulary size varies by model: about 128k tokens in Llama 3, about 151k in the Qwen family.

### Embedding (gömme)

The token id converted into a **numeric vector** representing meaning. Vectors of semantically similar words land close together; the famous "king - man + woman ≈ queen" example works for this reason. In 8B-class models the vector size is around 4,000. For the image counterpart, see the latent space discussion on [Diffusion Fundamentals](/en/gorsel/diffusion-temelleri/).

### Transformer

The architecture introduced by the 2017 paper "Attention Is All You Need"; the foundation of all large language models today. Its essence is the **attention** mechanism: every word in the sentence takes its meaning from context by "looking at" the other words. Details: [Transformer Architecture](/en/temeller/transformer/).

### LLM (large language model)

A language model with billions of parameters, pretrained on a massive text corpus. At its core it does exactly one thing: predict the probability of "the most likely continuation of the given text". Chatting, translating, writing code — all are byproducts of that single skill. Example families (as of 2026): Llama 4, Mistral Small, Phi-4.

### SLM (small language model)

Models in the range of roughly 0.5-8 billion parameters: Qwen3 (0.6B/1.7B/4B/8B), Gemma 3 (1B/4B/12B), Llama 3.2 (1B/3B), SmolLM3, Phi-4-mini. These are the **true heroes of this guide**: they fit on a single GPU and allow fine-tuning. In independent comparisons, Qwen3-8B gives the best overall fine-tuning results.

### Context window (bağlam penceresi)

The number of tokens the model can "see" at once. 128k tokens in Llama 3.2; natively 32k in Qwen3 (expandable to about 131k with the YaRN technique). How much Turkish text the window corresponds to depends on your token efficiency — for Turkish the window effectively shrinks by roughly half; the calculation is on [Tokenization](/en/temeller/tokenizasyon/). Check the model card for current values.

### Chat template (sohbet şablonu)

The special token pattern that tells the model "who is speaking?". In ChatML, used by Qwen, messages are framed with `<|im_start|>` and `<|im_end|>` markers; in Llama 2 you see `[INST]`. The model learns this pattern in the instruction stage after pretraining. **Critical rule:** whatever template was used in training must also be used at inference; otherwise the model breaks. Its role in training: [SFT](/en/llm/sft/).

## Layer 4: Customization

### Fine-tuning (ince ayar)

Updating the weights of a pretrained model with **additional training** on your own data. **Analogy:** giving on-the-job training to a university graduate; not teaching from scratch, but adding expertise on top of existing knowledge. The order of its types: [Pretraining](/en/llm/pretraining/) → [SFT](/en/llm/sft/) → [DPO and RLHF](/en/llm/dpo-rlhf/).

### LoRA (Low-Rank Adaptation)

Instead of training the whole model, attaching **small extra matrices** to the model and training only those. The base model freezes; less than 1% of the original parameters are trained. The result is an **adapter** file, tens to hundreds of megabytes, independent of the base model. This is the standard way to fine-tune an 8B model on a single consumer GPU: [LoRA and QLoRA](/en/llm/lora-qlora/).

### QLoRA

LoRA's memory-friendly sibling: the base model is first **quantized** (compressed) to 4-bit, and the LoRA adapter is trained on top of that compressed model. A 7B model's memory need drops from ~14 GB to around 5 GB; this way even 4-6 GB VRAM GPUs can train 0.5-2B models. The most common fine-tuning method of 2026.

### Instruction tuning (talimat ayarı)

Teaching the model the behavior "when asked a question, answer it". A raw pretrained model continues text; an instruction-tuned model follows patterns like question-answering and task completion. The technical name of this stage is **supervised fine-tuning (SFT)** and its data always consists of the same triple: instruction, input (if any), answer. Details: [SFT](/en/llm/sft/).

### RLHF and DPO

Methods for aligning the model with **human preferences**. In RLHF (reinforcement learning from human feedback), a reward model that scores "good answers" is trained first, then the language model is updated with reinforcement learning (PPO) toward that reward. DPO does the same job more simply: direct training on pairs like "I preferred answer A over B". As of 2026, DPO is the clear community favorite: [DPO and RLHF](/en/llm/dpo-rlhf/).

### Quantization (nicemleme)

The art of representing numbers with fewer bits: going from fp16 to 8-bit or 4-bit. **Analogy:** converting a photo from high quality to JPEG; the file shrinks 4x, quality drops slightly. An 8B model drops to about 5 GB at 4-bit and runs on an ordinary laptop. You meet it both in training (QLoRA) and in deployment (GGUF): [Quantization](/en/kullanim/quantization/).

### Distillation (damıtma)

Training a small "student" model that imitates the outputs of a large "teacher" model. The student learns not only the teacher's answer but its answer distribution (which wrong answer is "less wrong"). Example: the R1-Distill family, trained on DeepSeek-R1 outputs, carries that behavior to small models. The most practical use at your scale: generating data with a large model and training a small one: [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).

### RAG (retrieval-augmented generation)

Instead of embedding knowledge in the model's weights, **retrieving** relevant documents from a database when a question arrives and adding them to the context. **Analogy:** an open-book exam instead of a memorization exam. It needs no training and is perfect for current and proprietary knowledge; however, it does not change the model's style or behavior — which is why most projects use it together with fine-tuning. Decision guide: [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/) · The serving side: [Serving and API](/en/kullanim/sunma-api/).

## Where Do These Terms Go Deeper?

| Concept | Page that goes deeper |
| --- | --- |
| Token, tokenizer, chat template | [Tokenization](/en/temeller/tokenizasyon/) |
| Transformer, embedding, attention, layers | [Transformer Architecture](/en/temeller/transformer/) |
| Loss, epoch, batch, step, learning rate | [How Does Training Work?](/en/temeller/egitim-nasil-calisir/) |
| Learning rate and other training settings | [Hyperparameters](/en/llm/hiperparametreler/) |
| Parameters, VRAM, fp16/4-bit memory | [VRAM Math](/en/donanim/vram-hesabi/) |
| Fine-tuning, instruction tuning, SFT data | [SFT](/en/llm/sft/) |
| LoRA, QLoRA, adapter | [LoRA and QLoRA](/en/llm/lora-qlora/) |
| RLHF, DPO, alignment | [DPO and RLHF](/en/llm/dpo-rlhf/) |
| Quantization, GGUF, 4-bit | [Quantization](/en/kullanim/quantization/) |
| Pretraining from scratch, small scale | [Pretraining](/en/llm/pretraining/) |
| Inference, running locally | [Ollama](/en/kullanim/ollama/) |
| Distillation, data synthesis | [Create Your Own Dataset](/en/veri/kendi-verini-olustur/) |
| Classic ML: feature, label, model | [Classic ML Fundamentals](/en/klasik-ml/temeller/) |

:::tip[How to proceed?]
If the concepts have settled, the next stop is the [Roadmap](/en/baslangic/yol-haritasi/), which draws the path that fits your hardware. For technical depth, move to the [Fundamentals](/en/temeller/transformer/) section. Come back to this page whenever a term bothers you — every term is explained in place, with its context.
:::
