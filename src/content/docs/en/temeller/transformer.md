---
title: "Transformer Architecture: What Is Inside the Model?"
description: "From neural networks to the attention mechanism, from the encoder-decoder split to what parameter counts mean: the architecture inside LLMs, explained intuitively."
dogrulama: 2026-11-20
---

You can use a language model without ever opening the box; most people do. But to understand why the model eats so much VRAM, why the context window is limited, and what exactly you change during fine-tuning, you need to look inside the box once. This page explains the transformer architecture without boring you and without dumbing it down.

## A Short Journey from Neural Networks to the Transformer

### What is a neural network?

The smallest building block is the **neuron**: it takes a group of inputs, multiplies each by a weight, sums them, and passes the result through an activation function. A single neuron is a simple decision maker; when thousands of them are arranged in layers, they can capture incredibly complex patterns. The classic example: a network that predicts which digit (10 outputs) a 28×28-pixel digit image (784 numbers) shows. How the training process works is on [How Does Training Work?](/en/temeller/egitim-nasil-calisir/); here our subject is the network's **shape**.

The problem for language is this: text is not a fixed-size list of numbers. Sentences have variable length, and meaning **depends on order**: "the cat ate the fish" and "the fish ate the cat" consist of the same words but their meanings are opposite.

### Why weren't sequential models (RNNs) enough?

Before the transformer, text was processed with RNN (recurrent neural network) derivatives. An RNN processes words **one by one, in order**: at each step a "memory" (hidden state) is updated. Two fundamental problems emerged:

1. **Forgetting over long dependencies:** information from the beginning of a 500-word text has badly faded in memory by the time you reach the end.
2. **No parallelization:** every word must wait for the previous one; the GPU's thousands of cores sit largely idle.

The 2017 paper "Attention Is All You Need" solved both problems by abandoning sequentiality altogether — and the current LLM era began.

## Attention: The Model's "What Should I Look At?" Mechanism

Look at this sentence: *"I fed the cat because **it** was very hungry."* Who is "it"? As a human you find the cat in a split second because you pay **attention** to the other words in the sentence. The attention mechanism does exactly this: every word looks at all the other words and takes its meaning from them.

### The query/key/value (Q/K/V) analogy

Think of attention as a library search:

- **Query:** your search request — "what is there about the cat?"
- **Key:** each book's label — "about books", "about cats"...
- **Value:** the book's content.

For each word, the model produces a query, compares it against all the keys (a similarity score), gives the highest weights to the most similar keys, and sums the values with those weights. Result: the vector of the word "it" is filled mostly with the information from the word "cat".

In reality these are three separate **learned matrix** multiplications (W_q, W_k, W_v) and the weights are normalized with softmax; the whole system is just a few matrix multiplications. And that is exactly what GPUs love: one big parallel computation.

:::note[Multi-head attention]
A single attention gives a single "point of view". The transformer does this 8-64 times in parallel: one head can focus on grammar, another on semantic similarity, another on position. The results are combined. This is called **multi-head attention** and it is one reason models capture grammatical structure so well.
:::

### Why was it revolutionary?

Attention's three practical advantages made the current LLM era possible:

- **Full parallelism:** all tokens are processed at once; none of the GPU's power goes to waste. RNN's "wait in line" bottleneck disappears.
- **Short path, long memory:** no matter how far apart two words are, the computation between them is one step. Information 5,000 words away is as accessible as information 5 words away.
- **Scalability:** the structure works better as the model grows. Copying the same block design scales from 1B to 400B with the same recipe.

## The Anatomy of a Transformer Block

An LLM consists of dozens of copies of the same structure stacked on top of each other. Each block has four components:

1. **Attention layer:** the "looking at other words" job described above. It builds relationships between tokens.
2. **Feed-forward network (FFN):** a small two-layer neural network that processes each vector coming out of attention independently. A significant share of the model's parameters live here; it is thought to work like an "information vault".
3. **Residual connections:** each layer's output is added to its input. **Analogy:** notes added on top of every correction so that nothing is lost. Without these connections, 30+ layer models cannot be trained.
4. **Layer normalization (RMSNorm/LayerNorm):** a scaling that keeps values in a balanced range at every step. It keeps training from collapsing.

**Layer count** is the model's "depth"; **hidden size** is the length of the vector each token travels with. An 8B-class model typically has 30-40 layers and a hidden size between 3,000 and 4,000. Why does it matter? Memory and compute needs grow almost proportionally with these two numbers: [VRAM Math](/en/donanim/vram-hesabi/).

## Encoder or Decoder? Why Is Everyone Decoder-Only?

In the transformer's early years two different usages came to the fore:

| Architecture | Representative | Training task | Strong at |
| --- | --- | --- | --- |
| Encoder-only | BERT | Masked language modeling: some words in the sentence are hidden and the model fills them in | Understanding: classification, sentiment analysis, search |
| Encoder-decoder | T5 | Read the input and produce a different text | Translation, summarization |
| Decoder-only | GPT, Llama, Qwen, Gemma, Mistral | Predicting **the next token** at each step | Generation: chat, code, general purpose |

Between 2018-2020 the three architectures competed; today almost all large models are **decoder-only**. The reason is the power of simplicity at scale: a single training objective (predict the next token) lets you generate labels automatically from every text at internet scale. Encoder models are still used for understanding tasks (e.g. similarity search), but general-purpose assistants are all decoder-only. This table is as valid as of 2026; the change you will notice is that multimodal models attach a **separate vision encoder** to the model for processing images — that component is the input reader, while the text-generating core remains decoder-only.

:::note[How does "predicting the next token" turn into a chat?]
The model actually does one thing: it looks at the text up to that moment and produces a probability distribution for the next token. Chat is the steering of the same mechanism with instruction and role markers (the chat template). Details: [Tokenization](/en/temeller/tokenizasyon/) and [SFT](/en/llm/sft/).
:::

## What Does the Parameter Count Determine?

The "B" in model names stands for **billion** parameters. The parameter count affects three things at once:

- **Capacity:** more parameters means the potential to learn more complex patterns — if data and training budget are sufficient.
- **Memory:** each parameter takes 2 bytes in fp16. So a 1B model needs ~2 GB, an 8B model ~16 GB, a 70B model ~140 GB (weights only). With 4-bit quantization these values drop roughly to a quarter: [Quantization](/en/kullanim/quantization/).
- **Speed:** inference speed is mostly inversely proportional to parameter count; a model twice as large runs nearly twice as slow.

As of 2026, typical examples: the Qwen3 family 0.6B / 1.7B / 4B / 8B; the Gemma 3 family 1B / 4B / 12B; the Llama 3.2 family 1B / 3B. These sizes are not random — they are "local-friendly" versions designed to fit on a single consumer GPU.

| Model size | Weights only (fp16) | Weights only (4-bit, approximate) |
| --- | --- | --- |
| 1B | ~2 GB | ~0.6 GB |
| 8B | ~16 GB | ~4-5 GB |
| 70B | ~140 GB | ~35-40 GB |

:::note[So what does a 0.5B model give up?]
The capacity difference is felt most in: long-chain reasoning, obscure domain knowledge and multilingual inference. In return, 0.5-2B models can be surprisingly good at jobs narrowed to a single task (e.g. classification, style transfer, format conversion) and they fit in 4 GB of VRAM. That is why the guide keeps saying "define the task first, then pick the model size": [Roadmap](/en/baslangic/yol-haritasi/).
:::

## Two Short Notes

### Mixture-of-Experts (MoE)

Some modern models activate only a part of the parameters **per token**, not all of them: a few of the sub-networks called experts are selected. To see the difference clearly, three official examples (total → active per token):

- **Llama 4 Scout:** 109B total, 17B active; selected from 16 experts (Meta's announcement).
- **Qwen3-30B-A3B:** 30.5B total, 3.3B active; there are 128 experts, 8 are selected per token.
- **DeepSeek-V3:** 671B total, 37B active.

This approaches "big-model knowledge at small-model cost". But note: **there is no discount on the VRAM side.** The model decides token by token which expert will be selected; you cannot know in advance which experts will be needed, so **the weights of all experts still sit fully in memory.** A 30B MoE model behaves like a 3B model in compute but demands the full memory of a 30B model: [VRAM Math](/en/donanim/vram-hesabi/).

### Positional encoding

Attention does not inherently know the **order** of words — "the cat ate the fish" and "the fish ate the cat" look the same to it. Therefore position information is added to each token's vector. While the first models used learned position vectors, the dominant method as of 2026 is **RoPE** (rotary position embedding; the [RoFormer paper](https://arxiv.org/abs/2104.09864)): position is encoded by rotating the vectors; it carries absolute position and lets the relative distance between two words naturally blend into the attention score. When you go beyond the contexts seen in training, scaling techniques come in: YaRN ([paper](https://arxiv.org/abs/2309.00071)) carefully rescales RoPE frequencies to enlarge the window. A concrete example: Qwen3-8B ships with a native window of 32,768 tokens; according to its model card it has been verified up to 131,072 tokens with YaRN.

## The 2026 Architecture Glossary: Terms You Will See in Config Files

A mini glossary of the terms you will encounter when you open modern model cards. None of it is magic; they are the updated forms of the block components we just described.

- **GQA (grouped-query attention) and MQA:** in attention there are many query heads but few key/value (KV) heads: Llama 3 has 8 KV heads against 32 query heads, Qwen3-8B again 32 to 8, Gemma 3 8 to 4. It directly shrinks the KV cache and memory traffic without giving up much quality. The extreme form is **MQA**: a single KV head. Seeing `num_key_value_heads` smaller than `num_attention_heads` in a config is the sign of this.
- **RMSNorm:** a slimmed-down form of layer normalization ([paper](https://arxiv.org/abs/1910.07467)): it skips the mean-subtraction step and scales values only by the square root of the mean of squares. It provides similar training stability with less computation, and has become the standard choice of modern models including Llama and Qwen.
- **SwiGLU:** the activation function family of the FFN ([paper](https://arxiv.org/abs/2002.05202)); it appears in configs as the "SiLU" activation. Thanks to its gated structure it usually learns better within the same parameter budget.
- **RoPE:** today's dominant answer to position encoding; the details and the story of extending it with YaRN are in the previous section.

When you see these terms, know this: the backbone has not changed; every component of the 2017 block has been renewed with best practices tested over the years for scale and stability.

## A Token's Journey: Summary from Start to Finish

When you type "hello", the following path is followed inside the model:

1. **Tokenization:** the text is turned into tokens and ids (e.g. "hello" → `[9707]`).
2. **Embedding:** each id is converted into a hidden-size vector.
3. **Position injection:** the order information (RoPE) is applied to each vector.
4. **Block tour:** the vector passes through N transformer blocks in sequence; in each block, attention and FFN operations are applied.
5. **Output layer:** the final vector is converted into a list of scores (logits) the size of the vocabulary.
6. **Conversion to probability and sampling:** probabilities are computed with softmax; the model "picks" a token and the process repeats with it.

Note: the choice in step 6 is not always the most probable token; sampling settings like `temperature` and `top_p` control the creativity and variety of the generation. These are not training parameters but **inference** settings.

## The Memory Limit at Inference: KV Cache

As the model produces each new token, it stores the attention information (key and value vectors) of all previous tokens so it does not recompute them. This memory is called the **KV cache**. Consequence: as the context window grows, inference memory grows quickly, and in long conversations the model slows down and asks for more VRAM. The main reason the "128K context" promise hits hardware limits in practice is the KV cache.

You compute it roughly like this: cache size ≈ 2 (key + value) × layer count × KV head count × head size × context length × bytes. An example over Qwen3-8B (fp16, i.e. 2 bytes): 2 × 36 layers × 8 KV heads × 128 size × 2 bytes ≈ 0.14 MB per token. Over a 32,768-token context that is ~4.5 GB; if you raise it to 131K with YaRN, ~18 GB — for the cache alone. GQA's share here is large: if there were 32 KV heads (no GQA), you would pay four times the memory. Remember this extra memory stacks on top of the model's own weights (~16 GB in fp16).

## The Speed Trick: FlashAttention

The KV cache inflates memory; attention itself also gets expensive quickly as the context grows: in a naive implementation a score is computed for every token pair, and writing that huge intermediate matrix to memory and reading it back can take longer than the computation itself. **FlashAttention**'s idea is engineering, not mathematics: it computes the attention without ever writing the matrix to memory, keeping the computation in small tiles inside the GPU's fast on-chip memory ([paper](https://arxiv.org/abs/2205.14135)). The result is bit-for-bit the same; only memory traffic is reduced, so it is both faster and makes long context possible with less memory.

You do not write this technique by hand; you use it ready-made:

- In HF transformers it is enough to say `attn_implementation="flash_attention_2"` while loading the model. Even if you say nothing, **SDPA** (PyTorch's built-in, optimized attention implementation) kicks in by default; most local users do perfectly well with SDPA.
- Inference tools like vLLM and Ollama use these optimizations on their own; you do not need to do anything.

:::caution[If you are on Windows]
The FlashAttention library targets Linux; the note in its repository openly says the Windows build is still not sufficiently tested. If you need it on a Windows machine, the smoothest path is working through WSL2: see the WSL2 section on the [Local Setup](/en/donanim/yerel-kurulum/#wsl2-ne-zaman-gerekir) page.
:::

## Common Misconceptions

:::caution[These three beliefs are common but wrong]
- **"Parameters are a memorized text store."** No; knowledge is woven **distributed** across billions of weights. A single neuron does not represent "Ankara".
- **"Attention works like human attention."** The analogy is useful, but the mechanism is not emotional — it is pure matrix multiplication and softmax.
- **"More parameters are always better."** Capacity turns into value only with enough data and training budget; an 8B model trained on good data can surpass a 70B in a specific domain.
:::

## Where Does Fine-Tuning Enter This Picture?

The answer to "which layers does the adapter attach to?", which you will meet on the LoRA and QLoRA pages, lies exactly in this architecture. Adapters are usually attached to the attention's query/key/value and output projections (q_proj, k_proj, v_proj, o_proj) and, in some tools, to the feed-forward matrices. These matrices are a small fraction of all the model's parameters; that is the secret of being able to train an 8B model with "less than 1% of the parameters".

The next stop: on the [LoRA and QLoRA](/en/llm/lora-qlora/) page you will see how these adapters are configured with settings like rank and alpha. To understand the training loop itself: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/).

## We Will Not Change the Architecture in This Guide

Good news: when you fine-tune, you do not touch the architecture. The model keeps consisting of the same blocks; you only update a part of the weights with your own data. Bad news: since the architecture stays the same, the memory need stays the same too — and now you know why it eats that much VRAM.

Attention computing for every token means memory consumption rises quickly as the context window grows; the layers and hidden size determine the weight file's size. With this knowledge, VRAM planning is no longer a guessing game: [VRAM Math](/en/donanim/vram-hesabi/).

:::tip[Next step]
Learn tokenization, the first stop where text turns into numbers: [Tokenization](/en/temeller/tokenizasyon/). If the architecture has settled, move to the training loop: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/). If you want to train your own small model from scratch: [Pretraining](/en/llm/pretraining/).
:::

## Sources and Further Reading

- [Attention Is All You Need (Vaswani et al. 2017)](https://arxiv.org/abs/1706.03762) — the original paper introducing the transformer architecture.
- [RoFormer / RoPE (Su et al. 2021)](https://arxiv.org/abs/2104.09864) — the rotary position embedding paper.
- [YaRN (Peng et al. 2023)](https://arxiv.org/abs/2309.00071) — efficient RoPE-based context window extension.
- [GQA (Ainslie et al. 2023)](https://arxiv.org/abs/2305.13245) — the grouped-query attention paper that shrinks the KV cache.
- [RMSNorm (Zhang & Sennrich 2019)](https://arxiv.org/abs/1910.07467) — the slimmed-down form of layer normalization.
- [GLU Variants Improve Transformer (Shazeer 2020)](https://arxiv.org/abs/2002.05202) — the source paper of the SwiGLU activation.
- [FlashAttention (Dao et al. 2022)](https://arxiv.org/abs/2205.14135) and [GitHub repository](https://github.com/Dao-AILab/flash-attention) — IO-efficient attention with bit-identical results.
- [DeepSeek-V3 technical report](https://arxiv.org/abs/2412.19437) — the report of the MoE architecture with 671B total / 37B active parameters.
- [HF Transformers: Attention backends](https://huggingface.co/docs/transformers/attention_interface) — the guide to choosing attention implementations like SDPA and FlashAttention-2.
- [Meta Llama 4 announcement](https://ai.meta.com/blog/llama-4-multimodal-intelligence/) — Llama 4 Scout's 109B total / 17B active MoE numbers.
- [Qwen3-30B-A3B model card](https://huggingface.co/Qwen/Qwen3-30B-A3B) — 30.5B total / 3.3B active; 8 selected from 128 experts.
