---
title: "Tokenization: How Does the Model See Text?"
description: "What a token is, how BPE works, why Turkish consumes more tokens than English and why chat templates are critical — all explained with examples."
dogrulama: 2026-11-20
---

A language model sees neither letters nor words. The only thing it sees is **numbers**: when you type "hello world", the model actually processes a list of numbers like `[15339, 1917]`. The bridge that turns text into those numbers is called **tokenization**. This page explains how that bridge works and why it matters so much for Turkish in particular.

## What Is a Token?

A token is the smallest piece of text the model sees. Sometimes a word, sometimes part of a word, sometimes a punctuation mark. The process runs in two steps:

1. The tokenizer splits the text into pieces: `"hello world"` → `["hello", " world"]` (for Turkish, `"Merhaba dünya"` → `["Mer", "haba", " dünya"]`).
2. Each piece is mapped to an **id** (a number) in the vocabulary: `["hello", " world"]` → `[15339, 1917]`.

**Analogy:** Lego. The model works with ready-made Lego pieces; frequently used pieces (like "the", "and") sit in the box as single pieces, while rare and long ones are assembled from smaller pieces.

## Why Not Letters or Words?

Both extreme approaches have serious flaws:

- **Character-based:** the vocabulary becomes tiny (the alphabet), but sentences grow 3-4x longer. Since single letters carry no meaning, the model's job gets needlessly harder, and the context window drains away.
- **Word-based:** in agglutinative languages like Turkish, "ev, evler, evlerimizden, evlerimizdekiler..." produces millions of word forms. The vocabulary explodes, and words never seen in training (unknown / OOV) are papered over with `<unk>` — information is lost.

The solution is in between: the **subword** logic. Frequent pieces become single tokens; rare words are split into meaningful pieces. The model can read even a word it has "never seen" from its familiar pieces.

## BPE (Byte-Pair Encoding), Intuitively

BPE rests on a simple idea: **merge the symbol pair that appears most frequently side by side in the data, and repeat this thousands of times.**

Let's follow a representative example:

```text title="Representative BPE merge steps"
Start: words split into characters
  e v,  e v l e r,  e v d e n        (ev = house, evler = houses, evden = from the house)

Step 1: most frequent pair "e v" → new symbol: "ev"
  ev,  ev l e r,  ev d e n

Step 2: now the most frequent pair "l e" → new symbol: "le"
  ev,  ev le r,  ev d e n

Step 3: "le r" appears often → new symbol: "ler"
  ev,  ev ler,  ev d e n
...
Result: "ev" and "ler" are now single tokens; the rarer "evden" is split
into pieces like "ev" + "d" + "en".
```

In real training this is repeated thousands of times over a corpus of hundreds of thousands of words, and a model-specific **vocabulary** is born. The size varies by model and is written explicitly in the model's config file: 128,256 in Llama 3, 151,936 in Qwen3, 262,208 in Gemma 3; OpenAI's GPT-4o tokenizer is about 200k. (Exact figures taken from model cards; last verified 2026-10.)

Modern models also have a safety net: **byte-level BPE**. It builds the vocabulary not on Unicode characters but on the 256 **byte** values; so whatever language and whatever characters you write (İ, ğ, ş, emoji, any symbol you can think of), the text can always be represented as a chain of bytes. This solves the word-based approach's `<unk>` (unknown token) problem at its root: no text can ever fall into "unknown". Since GPT-2, most widespread models including Llama, Qwen and Gemma use this approach.

## Algorithm Families: BPE, WordPiece, Unigram

BPE is not the only player; distinguishing the three main algorithm families is enough to understand what you read on model cards:

- **BPE:** merges the most frequent adjacent pair; builds bottom-up (from letters). Deterministic: the same text always splits the same way. Most generative models today, including Llama, Qwen and Gemma, use BPE.
- **WordPiece:** BERT's method. It picks the merge candidate not from the most frequent pair but from the pair that most increases the training likelihood — it tries to find the most "informative" merge.
- **Unigram:** works in reverse: it first builds a large subword pool, then progressively discards the candidates that contribute least to the training loss. T5 belongs to this family.

Separate from these, a note: **SentencePiece** is not an algorithm but a library that runs BPE or Unigram on raw text. Since it includes the whitespace (▁) as a token in the vocabulary, it is preferred for space-less languages (Chinese, Japanese) and multilingual models; you will also meet it often in Turkish-focused projects.

## Turkish's Crisis: An Agglutinative Language, Expensive Tokens

Attention here: **Turkish is a disadvantaged language in model training compared to English — and the reason is linguistic.**

Turkish derives words by adding suffixes — it is **agglutinative**. Let's break down the word "yapabileceklerimizden":

```text title="One word, seven morphemes"
yap - abil - ecek - ler - imiz - den
root   ability  future  plural  our-possession  ablative case

English equivalent: "from the things that we will be able to do"
```

In English, pieces like "will", "be", "able", "to", "do" are separate and very frequent words; in BPE nearly all of them become single tokens. In Turkish, the same meaning is packed into **one word** and word forms are extremely varied, so the tokenizer splits the word into 6-8 pieces. Result: the same content consumes roughly **1.5-2.5x more tokens in Turkish compared to English** (a ratio; it varies by text type and tokenizer). This is not an observation unique to Turkish either: research shows commercial tokenizers produce systematic efficiency gaps between languages, and English is privileged in this game.

| Text (Turkish) | Approx. tokens | English equivalent | Approx. tokens |
| --- | --- | --- | --- |
| merhaba | 1-2 | hello | 1 |
| kitaplar | 2-3 | books | 1 |
| evlerimizden | 4-5 | from our houses | 3 |
| yapabileceklerimizden | 6-8 | what we can do | 3-4 |
| yapay zeka | 2-3 | artificial intelligence | 2 |

:::caution[The numbers in the table are representative]
Token counts vary by the tokenizer you use; the values above are the approximate ranges seen in common models as of 2026. To measure the exact number with your own text, run the [Python example](#practical-counting-tokens-with-python) at the end of this page.
:::

This has three concrete consequences:

1. **The context window narrows:** while a 128k-token window holds tens of thousands of words in English, it effectively holds roughly half as much text in Turkish.
2. **Cost rises:** most APIs and cloud services bill per token; the same job can come 1.5-2.5x more expensive in Turkish.
3. **Training and inference slow down:** since per-token processing time is fixed, the same sentence takes longer to process.

:::tip[Practical tips for Turkish]
- If possible, choose models **trained on Turkish data** or that have seen multilingual data (the Qwen and Gemma families are relatively good at this).
- When planning context, calculate the token budget **measured on your own data**, not with English assumptions.
- Do not needlessly lengthen your system instructions; every extra sentence steals from the budget.
:::

## Tokenizer Choice and Vocabulary Extension

**A model's tokenizer cannot be swapped.** The reason is simple: the model's embedding table is learned according to the ids the tokenizer produces; nobody can "re-tell" what id 9707 means. The tokenizer is like the alphabet the model was born with.

**When does vocabulary extension come up?** Some projects want to add Turkish-specific new tokens (e.g. very frequent suffixes) to reduce token counts. Tempting as it looks, the risks are large:

- **New embeddings are born from scratch:** with `resize_token_embeddings` the table grows, but the new rows start random; the model cannot learn the meaning of these tokens without seeing hundreds of thousands of examples.
- **Forgetting risk:** when the vocabulary grows, the whole embedding layer is affected; degradation (forgetting) in existing abilities can be observed.
- **Extra VRAM and compatibility issues:** a larger embedding table asks for more memory; community tools (Ollama, llama.cpp) can have trouble with custom vocabularies.

As of 2026 the practical advice: for most Turkish projects, **staying with the existing tokenizer** is smarter; the model-side gains now come from data quality, not from expanding the vocabulary. Consider extension only for pretraining from scratch or a very special domain (e.g. medical terms).

## Special Tokens and Chat Templates

The tokenizer has a hidden job too: telling the model "who is speaking?". For this, **special tokens** that never occur in natural text are reserved in the vocabulary:

- Qwen/ChatML: `<|im_start|>`, `<|im_end|>`
- Llama 2: `[INST]`, `[/INST]`; Llama 3: `<|begin_of_text|>`, `<|start_header_id|>`, `<|eot_id|>`
- Generic: `<|user|>`, `<|assistant|>`, `<|system|>`

When these tokens combine into a sequence and pattern, the **chat template** emerges:

```text title="A ChatML-like chat template"
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Recommend three books to me.<|im_end|>
<|im_start|>assistant
Sure! Here are three suggestions: ...<|im_end|>
```

In the template of reasoning models like Qwen3 there is also a thinking area: before giving its answer, the model produces its reasoning inside a `<think>...</think>` block. You can turn this mode off with `enable_thinking=False` in the `apply_chat_template` call.

The model sees this pattern during the instruction-tuning stage and learns the boundaries of the roles. Two critical points:

1. **The template used in training and the template used at inference must be the same.** Mismatch is the most common cause of a model "talking nonsense"; if your own model's behavior is broken, check the template first. The training side: [SFT](/en/llm/sft/).
2. **For which tokens is the loss computed?** In SFT, loss is usually computed only for the assistant's answer tokens; the user message is not memorized. Details: [SFT](/en/llm/sft/).

## Practical: Counting Tokens with Python

Now let's measure how many tokens your own text consumes. With the `transformers` library you can download the model's own tokenizer and count in three lines:

```python title="token_count.py"
from transformers import AutoTokenizer

# The model's own tokenizer — nobody else's!
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

text = "Yapabileceklerimizden bahsedelim."  # Turkish: "Let's talk about what we can do."
ids = tokenizer.encode(text)

print("Token count:", len(ids))
print("Pieces:", tokenizer.convert_ids_to_tokens(ids))
# Example output (varies by tokenizer version; a single word
# can split into multiple pieces):
# Pieces: ['Yap', 'abile', 'cek', 'ler', 'imiz', 'den', ' bahs', 'edelim', '.']
```

:::note[If you are counting OpenAI models: tiktoken]
If you are counting the tokens of OpenAI's own models, the right tool is the `tiktoken` library (it works with OpenAI-specific encodings like `o200k_base`, `cl100k_base`). For any other model you trained or run locally, your counter is always the model's own tokenizer — i.e. the `AutoTokenizer` method above. Applying the OpenAI counter to another model's text diverges from the count made with that model's vocabulary and misleads your cost calculations.
:::

Passing the same text through the chat template to see the final input is just as easy:

```python title="chat_template.py"
messages = [{"role": "user", "content": "Hello, how are you?"}]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,             # show as raw text
    add_generation_prompt=True, # add the "assistant:" part
)
print(prompt)
```

Finally, let's model simply how the token difference reflects onto cost:

```python title="cost.py"
# Assumption: the API you use charges $0.50 per 1M tokens.
# Say the same content takes 1,000 tokens in English, 2,000 in Turkish:

english = 1_000 / 1_000_000 * 0.50
turkish = 2_000 / 1_000_000 * 0.50

print(f"English: ${english:.4f}  Turkish: ${turkish:.4f}")
print(f"Turkish is roughly {turkish / english:.1f}x more expensive")
```

:::note[Why does this ratio matter?]
In an application making 100,000 calls a day, 2x tokens means a 2x bill. If you are building a Turkish product, this difference must definitely be accounted for in budget planning.
:::

## Token Economics and Cost

Converting token counts into money and capacity is two simple calculations.

**Spending math:** on API or cloud inference, the bill forms roughly like this:

```text
cost = (input tokens + generated tokens) × price per 1M tokens / 1,000,000
```

Turkish consuming 1.5-2.5x more tokens means the bill swells by the same ratio; the cost.py in the previous section computes exactly this multiplication.

**Budget math:** the context window is a budget with four shares: the system instruction, fixed texts (few-shot examples, reference document pieces), the user's current input, and the space you reserve for the model's answer. The system instruction is **a fixed expense re-paid on every request** — an unnecessarily long system instruction is like a rent paid out of the budget on every call. The context window's counterpart in the architecture is on the [Transformer Architecture](/en/temeller/transformer/) page; the `max_length` setting where this budget takes effect in training is on the [Hyperparameters](/en/llm/hiperparametreler/) page.

The rule is simple: think of your design decisions in tokens. Shortening the prompt is direct saving; long context is both expensive and slow; Turkish's extra load is real but measurable cost.

## Token Budget While Preparing Data

Understanding tokenization is the foundation of data preparation: how many examples you can fit, how you split the context window, and what your cost will be — all are computed with token counts. How to plan this budget is on the [Data Types](/en/veri/veri-turleri/) page; how to convert your data into chat format is on the [Data Formats](/en/veri/veri-formatlari/) page.

:::tip[Next step]
Tokens turned into numbers; now how are these numbers processed inside the model? Move on to the [Transformer Architecture](/en/temeller/transformer/) page. Or jump straight to how training works: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/).
:::

## Sources and Further Reading

- [HF Transformers: Tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary) — the official comparison of BPE, WordPiece, Unigram and byte-level BPE; includes a note specific to Turkish's agglutinative structure.
- [Sennrich et al. 2015: Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — the original paper that brought BPE to NLP.
- [Kudo 2018: Subword Regularization](https://arxiv.org/abs/1804.10959) — the Unigram tokenization paper (the family T5 uses).
- [Kudo & Richardson 2018: SentencePiece](https://arxiv.org/abs/1808.06226) — raw-text tokenization for space-less languages.
- [HF Tokenizers](https://huggingface.co/docs/tokenizers) — a fast, Rust-based library if you want to train your own tokenizer.
- [HF LLM Course, Chapter 6](https://huggingface.co/learn/llm-course/chapter6/1) — a hands-on chapter on tokenizer algorithms and training from scratch.
- [tiktoken (GitHub)](https://github.com/openai/tiktoken) — fast BPE token counter for OpenAI models.
- [Ahia et al. 2023: Do All Languages Cost the Same?](https://aclanthology.org/2023.emnlp-main.614/) — the study measuring cross-lingual cost inequality in commercial tokenizers.
- [Qwen3-8B model card](https://huggingface.co/Qwen/Qwen3-8B) — official details of the chat template, the `<think>` block and context extension with YaRN.
