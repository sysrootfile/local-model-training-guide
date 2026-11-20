---
title: "Data Formats: JSONL, Alpaca, ShareGPT and Others"
description: "Learn the data formats training tools expect (JSONL, Alpaca, ShareGPT, ChatML/messages) with examples; the chat template difference, conversion code and common mistakes."
dogrulama: 2026-11-20
---

Training tools expect your data in specific formats. **The wrong format is the most common source of errors in this field**: your code is right, the model is right, but the tool either can't read your data or pretends to read it and runs an empty training. On this page you will see the common formats, the difference between them and the conversion paths.

## JSONL: One JSON per Line

JSONL (JSON Lines) is a text file where each line holds **a single independent JSON object**. The extension is usually `.jsonl` (sometimes `.ndjson`).

```json title="data.jsonl"
{"instruction": "Say hello.", "output": "Hello! How can I help you?"}
{"instruction": "Say thanks.", "output": "You're welcome, have a good day."}
```

Why JSONL?

- **Readable line by line:** huge files are processed as a stream without loading fully into memory.
- **Errors are isolated:** a broken line doesn't make the whole file unreadable; you fix only that line.
- **Appendable:** adding a new example is writing one more line at the end of the file.

For comparison, the same data as a "single array" JSON: `[ {...}, {...} ]`. That works for tiny files but is not stream-friendly as it grows, and a single error drops the entire file.

## The Alpaca Format: instruction / input / output

The most common format for SFT (instruction tuning). Three fields:

- **instruction:** the task/question (required).
- **input:** extra text provided along with the task (optional).
- **output:** the answer the model should learn.

A complete, realistic example:

```json title="alpaca_example.jsonl"
{
  "instruction": "Summarize the following paragraph in at most three bullets.",
  "input": "Photosynthesis is the process by which plants use sunlight to produce glucose from water and carbon dioxide. This process takes place in chloroplasts and releases oxygen as a by-product. Photosynthesis forms the basis of Earth's oxygen balance and the food chain.",
  "output": "- Plants produce glucose from water and carbon dioxide using sunlight.\n- The process takes place in chloroplasts and releases oxygen as a by-product.\n- Photosynthesis is the basis of the oxygen balance and the food chain."
}
```

:::tip
**When is input left empty?** When the instruction is self-sufficient — e.g. `"instruction": "What is the capital of Turkey?"`. In such cases writing `"input": ""` is the safest; some tools expect an empty string rather than `null`. Verify the field names (instruction/input/output) against your tool's docs: in the Alpaca family, variants using a `prompt`/`response` pair are also common.
:::

## ShareGPT / conversations: Multi-Turn Chat

If you will train the model for multi-turn chat, the ShareGPT format comes in: a single example is a `conversations` list of ordered messages.

```json title="sharegpt_example.jsonl"
{
  "conversations": [
    {"from": "human", "value": "How do I reverse a list in Python?"},
    {"from": "gpt", "value": "The shortest way is reverse slicing: my_list[::-1]. This expression returns a reversed copy of the list."},
    {"from": "human", "value": "What if I want it sorted in reverse without mutating the original list?"},
    {"from": "gpt", "value": "You can use sorted(my_list, reverse=True); it returns a new list and the original list stays unchanged."}
  ]
}
```

A variant is the version that uses `role`/`content` names instead of `from`/`value`:

```json
{"conversations": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Which names are expected varies by tool: Unsloth, LLaMA-Factory and Axolotl support the traditional `from`/`value` form; many tools also accept the `role`/`content` variant. If unsure, download the tool's example dataset and look at the field names.

## ChatML / messages: Roles and the System Prompt

The most modern approach: a role-based message list. There are three roles:

- **system:** the model's general behavior frame (tone, language, limits).
- **user:** the user's message.
- **assistant:** the model's answer.

```json title="messages_example.jsonl"
{
  "messages": [
    {"role": "system", "content": "You are the customer service assistant of an online store. You answer in Turkish, briefly and politely."},
    {"role": "user", "content": "My order has been in transit for three days, what should I do?"},
    {"role": "assistant", "content": "If you share your order number, I can check the shipping status right away and inform you."}
  ]
}
```

**What is the system prompt and why does it matter?** It is the first message carrying the model's "personality and rules". The system prompts in your training data must be **consistent**: if one example says "speak like a formal lawyer" and another has no system message at all, the model learns to ignore the system prompt rather than follow it. Decide: either every example has the same/similar system prompt or none does. At deployment (inference) use the same or a very similar prompt as in training.

The name "ChatML" comes from the template that translates the `messages` structure into special tokens (`<|im_start|>`, `<|im_end|>` etc.) behind the scenes; we'll see that translation shortly.

## Summary Table: Which Format, Which Situation?

| Format | Fields | Multi-turn? | Tools that like it |
| --- | --- | --- | --- |
| Alpaca | instruction, input, output | No (single turn) | Unsloth, TRL (SFT), LLaMA-Factory, Axolotl |
| ShareGPT | conversations: from/value | Yes | Unsloth, LLaMA-Factory, Axolotl |
| ChatML / messages | messages: role/content | Yes | Unsloth, TRL, LLaMA-Factory, Axolotl |
| Plain text | — | No | Pretraining / continued training (TRL, Axolotl) |
| prompt-completion | prompt, completion | No | TRL (completion training) |

:::note
Tools change the formats they support over time; the table reflects the typical situation as of 2026. The definitive information is in the tool's own docs: [Tools](/en/llm/araclar/).
:::

## Format ≠ Template: Chat Templates

The most critical distinction: the **format** is how the data looks in the file; the **template (chat template)** is the rule by which the tokenizer turns that structure into the special-token plain text the model expects. Every model family uses a different template (Qwen, Llama, Mistral... all different).

```python title="template.py"
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B")  # put the HF name of the model you use

messages = [
    {"role": "system", "content": "Answer briefly and clearly."},
    {"role": "user", "content": "Hello!"},
]

text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print(text)
```

The output is the messages as plain text wrapped in the special tokens the model wants (in ChatML-like models, the `<|im_start|>system ... <|im_end|>` pattern). Training tools often do this transformation for you; in cases where they don't, skipping this step creates one of the sneakiest errors:

:::caution
**The same-template rule:** if you query a model you trained with `apply_chat_template` (say the ChatML pattern) at inference with a different template (say the `[INST]` pattern), the model doesn't recognize the "instruction format": instead of answering it tries to complete the input, echoes the question or talks nonsense. The model isn't broken; your input format doesn't match the training pattern. Behind most "I did SFT but the model doesn't talk properly" questions, this is what lies. Make sure the template is chosen correctly in local deployment: [Ollama Guide](/en/kullanim/ollama/), [Troubleshooting](/en/llm/sorun-giderme/).
:::

## Converting Formats with Python

Converting Alpaca-format data in your hands to ShareGPT is very simple. There are two subtleties here: `ensure_ascii=False` (so Turkish characters don't turn into escape sequences like `\u0130`) and writing line by line (the JSONL rule):

```python title="alpaca_to_sharegpt.py"
import json

def alpaca_to_sharegpt(example: dict) -> dict:
    question = example["instruction"]
    if example.get("input"):
        question = f"{question}\n\n{example['input']}"
    return {
        "conversations": [
            {"from": "human", "value": question},
            {"from": "gpt", "value": example["output"]},
        ]
    }

with open("alpaca.jsonl", encoding="utf-8") as f:
    examples = [json.loads(line) for line in f if line.strip()]

with open("sharegpt.jsonl", "w", encoding="utf-8") as f:
    for example in examples:
        f.write(json.dumps(alpaca_to_sharegpt(example), ensure_ascii=False) + "\n")

print(f"{len(examples)} examples converted")
```

:::tip
After conversion, always eyeball the first 5 lines. Even if the file is "valid JSON", only your eyes catch the semantic error (an answer written into the wrong field, an empty conversations list).
:::

Converting to the modern default `messages` format follows the same pattern; this time take the system prompt as a parameter so trying the same data with different prompts becomes easy:

```python title="alpaca_to_messages.py"
import json

def alpaca_to_messages(example: dict, system_prompt: str | None = None) -> dict:
    question = example["instruction"]
    if example.get("input"):
        question = f"{question}\n\n{example['input']}"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": example["output"]})
    return {"messages": messages}


SYSTEM_PROMPT = "You are an assistant that answers briefly and clearly."

with open("alpaca.jsonl", encoding="utf-8") as f:
    examples = [json.loads(line) for line in f if line.strip()]

with open("messages.jsonl", "w", encoding="utf-8") as f:
    for example in examples:
        f.write(json.dumps(alpaca_to_messages(example, SYSTEM_PROMPT), ensure_ascii=False) + "\n")

print(f"{len(examples)} examples converted")
```

Remember to keep the system prompt **the same across the entire set** (see the "What is the system prompt and why does it matter?" section above); lifting the prompt into a parameter lets you trial only the prompt text without touching the conversion code.

## Loading and Splitting with Hugging Face Datasets

```python title="load.py"
from datasets import load_dataset

ds = load_dataset("json", data_files="data.jsonl", split="train")

# A 10% validation split — keep the seed fixed so it's reproducible
splits = ds.train_test_split(test_size=0.1, seed=42)
train_ds, val_ds = splits["train"], splits["test"]

print(train_ds)
print(val_ds)
```

:::note
On imbalanced datasets like classification, use `train_test_split(stratify_by_column="label")` so balanced examples fall into each class. Choosing a fixed `seed` for the train/validation split lets you compare different runs fairly. Sharing the model after training: [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/).
:::

## Common Format Errors

| Problem | Symptom | Fix |
| --- | --- | --- |
| Missing/extra comma, unterminated quote | `JSONDecodeError` (with line number) | Fix the line; write a tiny script passing the file through `json.loads` line by line |
| Wrong key name | The tool says "field not found" or loads 0 examples | Alpaca: instruction/input/output; ShareGPT: conversations + from/value; messages: role/content |
| All data on one line | Example count shows 1 | Make sure lines are separated with line breaks (LF); don't write the file as one JSON array |
| BOM / encoding issue | Turkish characters break; "utf-8 codec can't decode" | Save the file as UTF-8 (without BOM); give `encoding="utf-8"` to every read/write in Python |
| Extremely long single lines | Loading very slow / memory blowup | Filter out overly long examples; split long documents into pieces |
| Loss not dropping in training | "Training runs but the model doesn't learn" | Is the template the same in training and inference? Are the tokens the loss is computed on (masking) right? → [Troubleshooting](/en/llm/sorun-giderme/) |

## The Pre-Training Validation Script

Format errors are the most expensive errors: usually unnoticed, they get baked into a training that runs for hours. The following single-file script does three checks together before you hand the data to training: a line-by-line linter, required-field validation and tokenizer verification. The script loads the tokenizer of the model you will train, needs no GPU, and can be re-run after every change to the dataset.

```python title="validate_data.py"
import json
import math

from transformers import AutoTokenizer

PATH = "data.jsonl"           # the file to validate
MODEL = "Qwen/Qwen3-4B"       # the HF name of the model you will train
FIRST_N = None                # if the file is huge: check only the first N lines


def check_fields(example: dict) -> str | None:
    """Returns None if valid, an explanatory error message otherwise."""
    if "messages" in example:
        messages = example["messages"]
        if not isinstance(messages, list) or not messages:
            return "'messages' is empty or not a list"
        for i, message in enumerate(messages):
            if "role" not in message or "content" not in message:
                return f"messages[{i}] is missing 'role'/'content'"
        return None
    if "instruction" in example and "output" in example:
        return None
    return "no 'messages' or 'instruction' + 'output' fields"


def to_messages(example: dict) -> list:
    """Converts both formats into a message list (for template rendering)."""
    if "messages" in example:
        return example["messages"]
    question = example["instruction"]
    if example.get("input"):
        question = f"{question}\n\n{example['input']}"
    return [
        {"role": "user", "content": question},
        {"role": "assistant", "content": example["output"]},
    ]


def percentile(sorted_list: list, p: int) -> int:
    """Pure-Python percentile (nearest-rank); no numpy needed."""
    if not sorted_list:
        return 0
    k = math.ceil(p / 100 * len(sorted_list))
    return sorted_list[min(k, len(sorted_list)) - 1]


# 1) Linter: line-by-line JSON + required-field check
valid = []
with open(PATH, encoding="utf-8") as f:
    for number, line in enumerate(f, start=1):
        if FIRST_N and number > FIRST_N:
            break
        if not line.strip():
            continue
        try:
            example = json.loads(line)
        except json.JSONDecodeError as err:
            print(f"ERROR line {number}: broken JSON ({err.msg})")
            continue
        problem = check_fields(example)
        if problem:
            print(f"ERROR line {number}: {problem}")
            continue
        valid.append(example)

print(f"\n{len(valid)} valid examples found.")
if not valid:
    raise SystemExit("No valid examples; fix the file and re-run the script.")

# 2) Template render: eyeball the first example
tok = AutoTokenizer.from_pretrained(MODEL)
print("\n--- The first example rendered through the template ---")
print(tok.apply_chat_template(to_messages(valid[0]), tokenize=False, add_generation_prompt=False))
print("--- Are the role tokens, ordering and whitespace right? ---\n")

# 3) Token statistics: p50 / p95 and a max_length suggestion
lengths = sorted(
    len(tok.apply_chat_template(to_messages(example), tokenize=True, add_generation_prompt=False))
    for example in valid
)
p50 = percentile(lengths, 50)
p95 = percentile(lengths, 95)
suggested = max(128, math.ceil(p95 / 128) * 128)  # round up to a multiple of 128
print(f"Token length: min={lengths[0]}  p50={p50}  p95={p95}  max={lengths[-1]}")
print(f"max_length suggestion: {suggested} (covers p95; the minority above it gets truncated)")
```

**Don't skip any of the three steps:**

1. The **linter** tells you the broken JSON and the missing field with a line number; you don't need to scan the file by eye.
2. The **template render** shows the first example turned into the exact text the model will see; wrong role order, a missing system prompt or empty content is only caught this way.
3. The **token statistics** is the input for your `max_length` and memory plan; if the gap between p95 and max is large, the long tail gets truncated at the suggested `max_length` — consider splitting long examples or raising `max_length`.

## Tool-Calling Data: A Quick Look

If you want to give the model the behavior of calling defined tools when needed, in your SFT data the assistant's answer is not plain text but a **structured call**. The mechanics are roughly: the model is first given tool definitions (tool name, description and parameter schema — usually JSON Schema); when the model wants to make a call, instead of a free sentence it writes a call made of the defined fields. After the tool runs, you feed the result back to the model; the model reads the result and produces the final answer.

As of 2026 the common shape is the OpenAI Chat Completions style: the assistant message returns a `tool_calls` list; each call has `id`, `type` and `function` (tool name + arguments) fields. The critical detail: the `function.arguments` field is a **JSON-encoded string** (nested JSON text); to use it you must parse it with `json.loads`.

```json title="tool_calls_example.json"
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_example123",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"Ankara\"}"
      }
    }
  ]
}
```

You give the tool result to the model with a `{"role": "tool", "tool_call_id": "...", "content": "..."}` message. In your training data this whole loop must be exemplified: the tool list (`tools`) → `tool_calls` → the tool result → the final answer.

Not every ecosystem uses the same shape: for example, Hermes-style models produce the call embedded in ChatML with `<tool_call>...</tool_call>` tags; OpenAI's newer Responses API uses a different structure. So when preparing the dataset, confirm the shape your training tool expects: [Tools](/en/llm/araclar/) and the OpenAI [function calling guide](https://developers.openai.com/api/docs/guides/function-calling).

:::note
**Often unnecessary for your first project.** If you're not targeting an assistant that reaches into the outside world (search, calculation, API calls), you can leave tool-calling data for later; starting with a simple question-answer set moves you faster.
:::

## Sources and Further Reading

- [Hugging Face — Chat templates](https://huggingface.co/docs/transformers/chat_templating) — the official explanation of `apply_chat_template` and the templates that vary by model family; the source of the "format ≠ template" distinction.
- [TRL — Dataset formats](https://huggingface.co/docs/trl/dataset_formats) — the full list of formats and types TRL trainers expect (including language modeling, prompt-completion, preference and tool calling).
- [Unsloth — Chat Templates](https://unsloth.ai/docs/basics/chat-templates) — the templates Unsloth supports (Conversational, ChatML, ShareGPT, Alpaca) and usage notes.

## What's Next?

- Format is done, now cleaning: [Data Cleaning](/en/veri/veri-temizleme/)
- Generate your data from scratch: [Create Your Own Dataset](/en/veri/kendi-verini-olustur/)
- Move on to training: the [SFT Guide](/en/llm/sft/) and [Step-by-Step Training](/en/llm/adim-adim-egitim/)
