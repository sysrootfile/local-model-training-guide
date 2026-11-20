---
title: "Pretraining from Scratch: The Realities and the Alternatives"
description: "The real cost of pretraining from scratch, the Chinchilla scaling finding, and continued pretraining — the approach that is the right path for most projects."
dogrulama: 2026-11-20
---

Before a language model can chat or answer questions, it must learn **the language itself**. This stage is called **pretraining**: the model is given millions of pages of raw text (web pages, books, code, articles) and taught a single task — "predict the next token."

Think of it like this: you make a student read millions of books but never ask them a question. You just stop in the middle of each sentence and ask "what's the next word?". Over time the student picks up grammar, vocabulary, stylistic variety and general world knowledge on their own. But they still don't know the "how to answer when asked" part — that part is the job of the [instruction tuning (SFT)](/en/llm/sft/) stage.

:::note
The short answer: this page exists to answer the question "should I train my own base model from scratch?" with realistic numbers. For most projects the answer is **no**; but experimenting at small scale is very instructive and genuinely possible.
:::

## Why Is Pretraining So Expensive?

Pretraining is the most expensive job in machine learning. Three things reach enormous size at the same time:

1. **Data:** the "predict the next token" task demands a lot of text. Serious models are trained on trillions of tokens — that alone means raw text from hundreds of GB up to TBs.
2. **Computation:** every example produces a separate gradient computation for every parameter in the model. The compute need grows with both the data amount and the model size.
3. **Engineering:** running thousands of GPUs faultlessly for weeks (hardware failures, data feeding pipelines, distributed training) is a discipline of its own.

### The Realities in Numbers

The table below is for showing orders of magnitude; the values aren't exact and should be read as "approximate".

| Scale | Data | Hardware | Duration / Cost (approx.) |
| --- | --- | --- | --- |
| Tiny experiment (TinyStories-style) | A few hundred MB of story text | A single consumer GPU (e.g. RTX 4090) | From a few hours to 1 day |
| ~1B parameters, "serious" pretraining | Billions of tokens | Tens of thousands of GPU-hours | Requires a serious budget |
| 8B+ parameters (Llama class) | Trillions of tokens | Thousands of GPUs × weeks | On the order of millions of dollars |

:::caution
Between the "I'll train my own GPT over the weekend" experiment and the "I'll produce a Llama-level model" goal, there is a cost difference of roughly tens of thousands of times. Both are pretraining; but one is a learning experiment and the other is a corporate project.
:::

## Chinchilla: The Parameter / Token Balance

In 2022, DeepMind's **Chinchilla** study shared an important finding: to get better results with the same compute budget, **model size and training data must grow together**. Until then, models were trained with relatively "big model, little data"; the Chinchilla team showed that smaller models seeing more data do better with the same budget.

The rough rule of thumb commonly used is:

> For a "proper" pretraining, aim for approximately **20 tokens of training data per parameter**.

Example: for a 1-billion-parameter model you need roughly **20 billion tokens** of text. If we count an average of ~4 characters per token, that corresponds to tens of GB of raw text.

We can express the calculation as an order of magnitude like this:

```text title="The Chinchilla math — order of magnitude"
Required data      = parameter_count × 20            (in tokens)
For a 1B model     = 1,000,000,000 × 20 = 20 billion tokens
Training compute   ≈ 6 × parameter_count × tokens    (FLOPs; a rough magnitude estimate)
1B × 20 billion    ≈ 1.2 × 10^20 FLOPs
```

That second line is the standard magnitude estimate for the question "how much compute does training want?"; it's used roughly when planning GPU-hours. Exact values vary by architecture and hardware.

:::note[The GPU-hour magnitude: the 1B × 20B example]
A concrete estimate with the same math: training a 1B-parameter model on 20 billion tokens ≈ **1.2 × 10^20 FLOPs**. The bf16 dense (FP32-accumulated) tensor power of a single RTX 4090 passes as **165.2 TFLOPS** in NVIDIA-sourced comparison tables and GPU databases (as of 2026). If you divide by that peak value only, the theoretical lower bound ≈ **200 hours**. In reality you can't use all of that speed: the typical efficiency (MFU) in published large-scale trainings is in the 30-50% band; assuming 30-50% efficiency you get a magnitude of **400-700 hours**. This is a **magnitude estimate; not an exact value** — architecture, batch size and the software stack can change the result several-fold.
:::

:::tip
The Chinchilla rule is for pretraining. In later stages ([SFT](/en/llm/sft/), [DPO](/en/llm/dpo-rlhf/)) you work with far less data. The real data need arises in pretraining; that's why the answer to "how many examples suffice?" changes completely by stage.
:::

## Chinchilla and Beyond: Why Do Current Models "Overtrain"?

The Chinchilla result defines the **compute-optimal** balance: if you have a fixed compute budget, distributing that budget between model size and training data in a certain ratio gives the lowest loss — roughly **~20 tokens per parameter** (arXiv:2203.15556). But that is not a "requirement"; it is an **efficiency** criterion.

As of 2026, looking at current models produces a picture that looks odd at first: small models are deliberately trained far longer than Chinchilla points to. Example: the Llama 3 paper (arXiv:2407.21783) states they trained their 8B-parameter model on **15 trillion tokens** — that is **~1,900 tokens per parameter**. With the Chinchilla rule, roughly 160 billion tokens would have seemed "enough" for 8B; the Llama 3 team trained with ~90x more than the rule.

Why? Because the two costs have different lifetimes:

- **Training is a one-time expense:** paid once.
- **Inference is an expense that lasts a lifetime:** paid again and again as the model runs on every query.

If you can reach the same target performance with a smaller but longer-trained model, each query in production processes fewer parameters and the long-term GPU cost drops. In the words of the Llama 3 paper: when small models are trained far beyond compute-optimal, they perform **better** than compute-optimal models "at the same inference budget". So being compute-optimal is not the same as being lifecycle-optimal.

The practical meaning for you: don't read the "20-token rule" as a ceiling or an industry standard; in your own situation strike a balance between your training budget and your inference cost.

:::caution[The most common misreading]
"20 tokens/parameter" is a **compute-optimal training budget**; it is not a quality ceiling or a mandatory minimum. Two misreadings are common: (1) "if I exceed 20 tokens the model breaks" — no; as data grows the loss generally keeps dropping, you only become *inefficient relative to the same compute budget*. (2) "I applied the rule, now I'm at Chinchilla level" — no; the rule is a recipe for balance; it doesn't by itself guarantee data quality or training success.
:::

## When Does Pretraining Make Sense? 3 Scenarios

For most people it doesn't; but in these three cases it can genuinely be necessary.

### 1. A base model for a new language

Training a base model for a low-resource language that the open models in your hands don't know well can make sense. For Turkish, an example: academic teams and community projects have trained models on hundreds of GB of Turkish corpora; the **Turkish Data Depository** (the turkish-nlp-suite community's data repository) provides Turkish pretraining data. Even so, trying continued pretraining with an existing multilingual model (e.g. Qwen3, Gemma 3) first is almost always cheaper.

### 2. A base model for a very specific domain

Some domains' data is completely different from natural language: molecular data, protein sequences, genomes, time series, financial streams... In these domains the "grammar" that general-purpose language models learned is of no use; a model specific to the target language is trained from scratch. A real-world example: the **ESM** series of models, trained on protein sequences, was pretrained with millions of amino acid sequences to learn "the language of proteins"; that model was later used in tasks like protein structure prediction.

### 3. Small scale for learning and research

Sometimes the goal isn't a production model but **understanding**. Training a tiny model of a few tens of millions of parameters from scratch on a small dataset and a single GPU, and watching its behavior, is the method that best explains how pretraining works. We cover this below.

### Examples from the Turkish ecosystem

- **Turkish Data Depository:** a community repository gathering Turkish raw text sources; a starting point for pretraining and continued pretraining.
- **FineWeb-2 Turkish:** the Turkish slice of Hugging Face's multilingual web dataset. Suited for those seeking web-scale raw text.
- **ogulcanaydogan/Turkish-LLM:** an open community project doing instruction tuning with QLoRA on Qwen2.5 (173K-242K Turkish examples). A concrete example of the "existing model + data" approach instead of training from scratch.

## The Alternatives: The Right Path for Most People

Instead of pretraining from scratch, starting from an existing strong open model and shaping it with your own data is almost always faster and cheaper:

```text title="The recommended flow for most projects"
[Collect your raw data]  -->  /en/veri/veri-nereden-bulunur/
        |
        v
[Pick an existing open base model]   (e.g. Qwen3-8B, Gemma 3, Llama 3.2)
        |
        v
[Continued pretraining]  -- optional, for domain/language knowledge
  - The model already knows the language; you feed it your domain's texts
  - Can be done with full fine-tuning or LoRA/QLoRA
        |
        v
[Instruction tuning (SFT)]  -->  /en/llm/sft/
  - "How to answer a question" is taught here
        |
        v
[Preference tuning (DPO)]  -- optional  -->  /en/llm/dpo-rlhf/
```

**Continued pretraining** means this: you start from the weights of the model in your hands, and on top of it do a few more epochs of "predict the next token" training with your own raw text (e.g. company documents, legal texts, a forum archive). The model's general language ability is preserved, and domain knowledge is added on top. Then you teach the task behavior with SFT.

:::tip
The order matters: **continued pretraining → SFT → (optional) DPO**. Continued pretraining data is raw text; SFT data is question-answer pairs; don't mix the two stages' data. Mixing SFT data into continued pretraining can break the model's behavior.
:::

## The Challenges of Continued Pretraining: Forgetting and Replay

Continued pretraining looks simple — "the model already knows the language, let's feed it a few documents" — but it has two aspects worth knowing.

**First, it's proven to work:** the "Don't Stop Pretraining" study showed that continuing to pretrain a model on the target domain's raw text (domain-adaptive pretraining, DAPT) gives a clear gain on that domain's tasks (arXiv:2004.10964). So the approach is solid; the gain comes not only from SFT but from raw domain text too.

**Second, it can cost you:** while teaching the model your domain, you can erase its general abilities. This is called **catastrophic forgetting**; the symptom is familiar: while domain questions improve, general chat, reasoning or other languages regress.

Practical reflexes:

- **Replay (a general-data mix):** put some general-purpose raw text back into your training mixture. A typical start is reserving **5-10%** of the data for general text; that's not a law, but a widespread community practice. Find the best ratio with your own validation results.
- **Small learning rate, few epochs:** if you do continued pretraining with full fine-tuning, keep the learning rate very small — **the 1e-5 magnitude** is a common start, and 1-2 epochs usually suffice. A high learning rate and many epochs accelerate forgetting.
- **LoRA/QLoRA may be gentler:** continued pretraining done with [LoRA and QLoRA](/en/llm/lora-qlora/) instead of updating all weights can preserve general abilities better; on small datasets this is the first path to try.

:::caution[Don't continue without measuring]
Run a short general-ability test **before and after** continued pretraining (20-50 questions is a good start): read the gain in domain performance together with the drop in the general score. If the general score drops clearly, raise the replay ratio, lower the learning rate, or reduce the epoch count. For loss-reading practice see the [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) page; for a more comprehensive comparison, [Benchmarks](/en/degerlendirme/benchmarklar/).
:::

## A Small-Scale Pretraining Experiment: TinyStories in 5 Steps

If you truly want to understand pretraining, the best way is to train a tiny model from scratch on one GPU over a weekend. There's a perfect toy dataset for it: **TinyStories**. This dataset, compiled by researchers, consists of simple English stories suitable for very young children. The idea: just as a child learns language first through simple stories, a small language model can learn a surprisingly fluent "children's story language" from simple stories. A model of a few tens of millions of parameters starts producing nonsense but grammatically consistent stories within hours.

**The 5-step recipe:**

1. **Get the code:** use [nanoGPT](https://github.com/karpathy/nanoGPT) (Andrej Karpathy's minimal educational GPT implementation) or one of the community-made training scripts for TinyStories.
2. **Download the data:** download the [TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories) dataset from Hugging Face; a few-hundred-MB subset is more than enough to start.
3. **Shrink the model:** define a GPT with a few layers and a few million parameters. The goal isn't a good model; it's a working pretraining loop.
4. **Train and watch:** watch the training loss drop and the generated text turn from nonsense into coherent stories over time. This takes a few hours on a single RTX 4090.
5. **Play with the parameters:** change the model size, the learning rate and the data amount. Seeing which change affects the loss how will make the Chinchilla idea "click" for you.

:::note
Even at small scale, pretraining confronts you with data cleaning, tokenization, learning-rate planning and loss monitoring. That's why it's so instructive; this knowledge also serves you in your professional [SFT](/en/llm/sft/) and [LoRA](/en/llm/lora-qlora/) work.
:::

## The Decision Table

| Your situation | The recommended approach |
| --- | --- |
| Chatbot, task model, style/tone change | SFT only (+ optional DPO). Don't enter training from scratch at all. |
| Dense domain jargon (law, medicine, corporate documents) and you have data | **Continued pretraining** with an existing model, then SFT. |
| A base model is needed in a very low-resource language | First try continued pretraining with multilingual open models; from-scratch training is realistic only for research teams. |
| The goal is learning / curiosity | From-scratch training at tiny scale on one GPU with TinyStories or nanoGPT. |
| Big budget + expert team + a new base model goal | The full line: pretraining from scratch + continued pretraining + SFT + DPO. |

## Mini FAQ

**"Should I train my own tokenizer?"**
If you're pretraining from scratch, yes — training a separate tokenizer (e.g. with BPE) for the target language and domain significantly improves token efficiency. If you're doing continued pretraining you **must keep** the existing tokenizer; changing it makes the model's learned weights meaningless.

**"Is Turkish pretraining data enough?"**
Turkish is far below English at web scale but doesn't count as "low-resource" on its own: sets like FineWeb-2 Turkish and community repositories have reached reasonable volume. In return, "seriously" training an 8B+ model still needs predominantly English data; that's why multilingual models are advantageous in practice.

**"What's the most I can do with a single RTX 4090?"**
A small-scale experiment: a 10-50-million-parameter model with a few hundred MB of text, from a few hours to 1 day. At this scale no "production model" comes out; but the whole line (data collection → tokenizer → training → sampling) passes through your hands and what you learn carries directly into your SFT/LoRA work.

## Wrapping Up

- Pretraining is the stage that teaches the model the language; it's the most expensive stage and demands serious data/compute/engineering resources.
- Keep the Chinchilla finding in mind: the balance of roughly 20 tokens per parameter.
- The right order for most projects: [collect your data](/en/veri/veri-nereden-bulunur/), start from an existing open model, do continued pretraining if needed, then apply [SFT](/en/llm/sft/) and optionally [DPO](/en/llm/dpo-rlhf/).
- If you want to learn, experiment from scratch — but at small scale and as an experiment whose goal is learning.

The next step: to give your model task behavior, move on to the [instruction tuning (SFT)](/en/llm/sft/) page.

## Sources and Further Reading

- [Chinchilla: Training Compute-Optimal Large Language Models (arXiv:2203.15556)](https://arxiv.org/abs/2203.15556) — the source of the model-size/data balance under a fixed compute budget and the "~20 tokens/parameter" finding.
- [Llama 3: The Llama 3 Herd of Models (arXiv:2407.21783)](https://arxiv.org/abs/2407.21783) — the 8B model's "overtraining" with 15T tokens and its justification via the inference budget.
- [DAPT: Don't Stop Pretraining (arXiv:2004.10964)](https://arxiv.org/abs/2004.10964) — the foundational study showing the benefit of domain-adaptive pretraining.
- [nanoGPT (GitHub)](https://github.com/karpathy/nanoGPT) — minimal, readable GPT training code for trying small-scale pretraining from scratch.
- [TinyStories (Hugging Face)](https://huggingface.co/datasets/roneneldan/TinyStories) — the dataset showing tiny models learn a surprisingly fluent language from simple stories.
