---
title: "Instruction Tuning (SFT): Training the Model for the Task"
description: "What SFT does, data preparation rules, the data budget (LIMA and s1), loss masking, forgetting and replay, packing, and a fully annotated Qwen3-4B training example with TRL."
dogrulama: 2026-11-20
---

**Instruction tuning (supervised fine-tuning, SFT)** is training a pretrained model with "question-answer" examples to make it task-focused. The model coming out of pretraining knows the language but doesn't know "how to be an assistant"; SFT teaches it how to behave when asked a question.

The intuition: [pretraining](/en/llm/pretraining/) taught the student the language. SFT teaches it **behaviors** like "how to write a reply when a customer asks a question", "in which format to give code when requested", "how short to keep a summary when asked for one". It doesn't build a new capability; it adds a user manual to the existing one.

## What Does SFT Change, and What Doesn't It Change?

| It changes | It doesn't change (or barely changes) |
| --- | --- |
| Answer style (formal/casual, short/long) | The model's core knowledge |
| Output format (JSON, markdown, bullet list) | Language ability (learned with billions of tokens) |
| Task behavior (summarize, translate, classify) | General reasoning capacity |
| Suppression of unwanted outputs | Facts the model never saw in pretraining |

:::caution
SFT is a **weak way to teach the model new knowledge**. You can make the model "memorize" a fact it has never seen via SFT, but that is unreliable: the model can't generalize the memorized fact to new situations, and may even start repeating it in the wrong places. If there's a knowledge gap, the right tools are [continued pretraining](/en/llm/pretraining/) or an external knowledge source (RAG); the full map of the "RAG or fine-tuning?" decision: [RAG or Fine-Tuning?](/en/rag/rag-mi-ince-ayar-mi/)
:::

When is SFT needed?

- If you're producing a chatbot or an assistant model (almost always needed),
- If the model's output will be in a specific format (e.g. JSON, a label list, SQL),
- If domain jargon and style matter (e.g. law, medicine, e-commerce),
- If the general model doesn't turn your request into the right behavior (e.g. always gives very long answers).

## Data Preparation

Most of success in SFT comes from the data. The model becomes the **average** of the examples it sees: if the examples are sloppy the model is sloppy; if the examples are short and clear the model answers short and clear.

### Which data formats exist?

The three common formats (details on the [Data Formats](/en/veri/veri-formatlari/) page):

**Alpaca style** — a simple question-answer pair:

```json title="alpaca_example.json"
{
  "instruction": "Rewrite the following sentence in more formal language: 'I can't come to the meeting tomorrow.'",
  "input": "",
  "output": "I would like to inform you that I will not be able to attend the meeting taking place tomorrow."
}
```

**Chat (messages) style** — for multi-turn conversations:

```json title="chat_example.json"
{
  "messages": [
    { "role": "system", "content": "You are a helpful Turkish assistant." },
    { "role": "user", "content": "What can you do in Istanbul on a rainy day?" },
    { "role": "assistant", "content": "A great day for visiting museums and cafés..." }
  ]
}
```

**ShareGPT style** — a list of human/gpt roles inside a `conversations` field. All modern training libraries can read these three formats; what matters is that **all the data is in one single format**.

### The Data Quality Checklist

Before training, ask your data these 5 questions:

1. **Is it consistent?** Do all examples use the same field names and the same schema? A mixed format breaks the training script or confuses the model.
2. **Are the answers correct?** Examples containing wrong information cause the model to learn wrong information. Fix or delete the suspicious answers.
3. **Is it varied?** Instead of thousands of copies of the same pattern, it should see different tasks, different lengths and different styles. Let the model learn a "skill", not a "pattern".
4. **Are there duplicates?** Verbatim copy examples trigger memorization (overfitting). Simple deduplication makes a big difference.
5. **Is the system prompt aligned?** The system prompt you use in training must be the same as the one you'll use at inference. If you say "You are a French teacher" in training and give no system prompt in production, the model won't behave as you expect.

:::tip
Start with 1,000 examples and see whether the model learns. If the pipeline works, grow the data. Instead of collecting 100,000 examples up front and training for 6 hours, verify "the line works" in 20 minutes with 1,000 examples.
:::

## Loss Masking: Learning Only from Assistant Answers

A chat example contains both the user's question and the assistant's answer. In training, the loss is normally computed over **all** tokens — but we don't want the model to learn "writing questions like a user"; we want it to learn only "writing answers like an assistant".

The fix is the **loss mask**: the labels of the user (and, if present, system) tokens are set to `-100`. The loss function ignores tokens labeled `-100`; the gradient flows only from the assistant's answer tokens.

:::note
This setting's counterparts in the libraries:

- **TRL:** `SFTConfig(assistant_only_loss=True)` — the data must be in the `messages` format and the tokenizer must have a chat template.
- **Unsloth:** the mask with `train_on_responses_only(...)`; the comparison is on the [Tools](/en/llm/araclar/) page.
- **Axolotl:** `train_on_inputs: false`.
:::

What happens without masking? The model tries to produce the user's question too; sometimes it starts inventing questions and answering them itself (imitating the "user: ... assistant: ..." pattern). With small data, this behavior surfaces quickly.

### How is the mask extracted technically?

TRL extracts the mask match from the chat data **automatically**; but for that to work, the tokenizer's chat template must mark the assistant section with the `{% generation %}` and `{% endgeneration %}` tags (TRL v1.15 docs, 2026). For well-known model families like Qwen3, TRL fixes the template itself; for other models, check the template yourself. If the template isn't suitable, TRL errors out — it doesn't silently mask wrongly.

You can test that the mask is correct on your data like this:

```python
messages = [
    {"role": "user", "content": "What is the capital of Turkey?"},
    {"role": "assistant", "content": "Ankara."},
]
out = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_assistant_tokens_mask=True,  # assistant tokens 1, others 0
)
print(sum(out["assistant_masks"]), "assistant tokens /",
      len(out["assistant_masks"]), "total tokens")
```

If the number is sensible (for a small assistant answer, a mask sum greater than zero and smaller than the total), masking works as expected. If the mask comes back entirely 0 (seen in some templates), your tokenizer isn't marking the assistant section; you need to change the training template or build the mask by hand.

:::note
Don't confuse two similar parameters: `assistant_only_loss` is for **conversational** data and the mask is extracted from the template. `completion_only_loss` is for **prompt-completion** data; in that format TRL already computes the loss only from the "completion" part by default, and with `completion_only_loss=False` you can force it to compute over the whole sequence. So they are sibling parameters aimed at different data formats (TRL v1.15 docs) — one is not the old name of the other.
:::

## Full Example: Qwen3-4B Instruction Tuning with TRL

The example below shows a classic SFT flow using Hugging Face tools directly (transformers + peft + trl), without facilitators like Unsloth. The 4B model was chosen because it can be tried comfortably on a single consumer GPU:

- with 4-bit loading (QLoRA) it runs at around ~5-6 GB of VRAM,
- thanks to LoRA the trainable-parameter ratio is around 1%.

```python title="sft_training.py"
# Instruction tuning (SFT) — a simple, annotated example with TRL SFTTrainer
# Setup:
#   pip install "trl" "peft" "datasets" "transformers" "accelerate" "bitsandbytes"

import torch
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

MODEL_NAME = "Qwen/Qwen3-4B"  # a 4-billion-parameter small model that also works well in Turkish

# ---------------------------------------------------------------------------
# 1) Data: our target is the chat format with a "messages" field.
#    (For Turkish instruction datasets, see the /en/veri/veri-nereden-bulunur/ page.)
#    In the example below we assume we have Alpaca-style data and convert it
#    into the chat format. When using it, check your dataset's field names in
#    the "Data Studio" section of its page.
# ---------------------------------------------------------------------------

data = load_dataset("atasoglu/instruction-turkish", split="train")
data = data.select(range(min(5000, len(data))))  # start small: 5,000 examples

SYSTEM_PROMPT = "You are a helpful, honest and polite Turkish assistant."

def to_chat(example):
    user = example.get("instruction", "") or example.get("prompt", "")
    answer = example.get("output", "") or example.get("response", "")
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": answer},
        ]
    }

data = data.map(to_chat)
splits = data.train_test_split(test_size=0.05, seed=42)  # 5% reserved for validation

# ---------------------------------------------------------------------------
# 2) LoRA configuration: instead of all weights, small "adapter" matrices
#    are trained. (Details: /en/llm/lora-qlora/)
# ---------------------------------------------------------------------------

lora_config = LoraConfig(
    r=16,                          # the adapter's capacity
    lora_alpha=32,                 # usually 2x the rank
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],  # attention + MLP layers
    bias="none",
    task_type="CAUSAL_LM",
)

# ---------------------------------------------------------------------------
# 3) Training settings: for the meaning of every knob, /en/llm/hiperparametreler/
# ---------------------------------------------------------------------------

training_args = SFTConfig(
    output_dir="./qwen3-4b-turkish-sft",
    num_train_epochs=1,               # 1-3 epochs typical; more risks memorization
    per_device_train_batch_size=2,    # keep between 1-4 depending on VRAM
    gradient_accumulation_steps=4,    # effective batch = 2 x 4 = 8 examples
    learning_rate=2e-4,               # the typical learning rate for LoRA
    lr_scheduler_type="cosine",
    warmup_steps=0.03,                # a ratio: 3% of steps (v5; formerly warmup_ratio)
    max_length=1024,                  # the maximum tokens per example
    bf16=torch.cuda.is_bf16_supported(),  # returns False on older GPUs (use fp16)
    logging_steps=10,
    save_strategy="epoch",
    eval_strategy="steps",
    eval_steps=50,                    # measure the validation loss every 50 steps
    report_to="none",                 # if you don't want wandb/tensorboard
    assistant_only_loss=True,         # learn only from the assistant's answer (masking)
)

# ---------------------------------------------------------------------------
# 4) Create the trainer and train
# ---------------------------------------------------------------------------

trainer = SFTTrainer(
    model=MODEL_NAME,
    args=training_args,
    train_dataset=splits["train"],
    eval_dataset=splits["test"],
    peft_config=lora_config,          # LoRA kicks in here
)
trainer.train()

# ---------------------------------------------------------------------------
# 5) Save: only the adapter is saved — it takes just a few MB!
# ---------------------------------------------------------------------------

trainer.save_model("./qwen3-4b-turkish-sft/adapter")
trainer.push_to_hub("YOUR-USERNAME/qwen3-4b-turkish-sft")  # optional
```

:::tip
Before running this script, do your VRAM planning on the [VRAM Math](/en/donanim/vram-hesabi/) page. With 4-bit loading off, a 4B model asks for ~8 GB VRAM in fp16; with 4-bit mode and LoRA it can come down to 5-6 GB.
:::

## How Much Data, How Many Epochs?

| Data amount | What do you expect? |
| --- | --- |
| 500 – 1,000 examples | A weak start. Enough to verify the pipeline works; not for production. |
| 5,000 – 20,000 examples | A serious start for a narrow task (e.g. classification in a specific style). |
| 50,000+ examples | Broad behavior change, a multi-task assistant. |

For epochs (the number of passes over the data):

- **1-3 epochs** is the typical, safe range.
- **5+ epochs** on the same data means memorization risk: the training loss drops, but the model starts "remembering" the data instead of "understanding" it; it produces odd answers to new questions.
- For early stopping, set aside part of the training data (5-10%) as **validation** and watch the validation loss. When the validation loss stops dropping and starts rising, stop. Details: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).

:::caution
The training loss dropping is not always good news. If you don't split the data and watch the validation loss, you can't see whether you're holding a model that has "memorized". Little data + many epochs is the most classic trap.
:::

## Is Little Data Enough? What LIMA and s1 Showed

The sentence "quality comes before quantity" sounds like a slogan, but there is experimental backing behind it. The two most talked-about studies:

- **LIMA (arXiv:2305.11206):** LIMA, trained with only **1,000 carefully selected prompt-response pairs** without any preference training like RLHF, was found **equivalent to or better than GPT-4 in 43%** of human preference comparisons.
- **s1 (arXiv:2501.19393):** the **1,000 questions and solution traces** called `s1K` were curated on three criteria: difficulty, variety and quality. On top of training came test-time scaling too: "budget forcing", which force-terminates the thinking process or extends it by adding "Wait". s1-32B beat o1-preview by up to 27% in competition math (MATH and AIME24).

| Study | Data size | What it showed |
| --- | --- | --- |
| LIMA (arXiv:2305.11206) | 1,000 careful examples | Near-GPT-4 results in preference comparisons, trained without RLHF |
| s1 (arXiv:2501.19393) | 1,000 questions + solution traces | Strong math performance with little data + test-time scaling |

:::caution
Don't over-generalize these results. Both are controlled experiments on a single training recipe with evaluation sets that could be called narrow; they don't mean "1,000 examples suffice for every project". Today's strong open assistants are trained not with a one-off small set but with multi-stage and broad open-data mixtures (e.g. TÜLU 3, arXiv:2411.15124). The "quality > quantity" proposition is true; but quality's measure is not an abstract "good" — it is these three concrete things:

1. **Consistency:** do the examples use the same schema and the same style norms?
2. **Variety:** are different tasks, different lengths and different difficulty levels covered? (In s1, difficulty was a deliberate curation criterion.)
3. **Format correctness:** do the outputs match exactly the format you expect in production?
:::

:::tip
A practical start: do the first training with **1,000-5,000 examples**. If behavior on the validation set is improving, grow the data gradually; if not, first fix the consistency and format of the existing examples — collecting new data is better than multiplying broken data.
:::

## Forgetting, Replay and the "Alignment Tax"

An overlooked risk in SFT is **catastrophic forgetting**: as the model specializes on the new task data, it loses part of the general abilities it brought from pretraining. The symptoms are typical: success on your narrow task rises, but the model starts answering irrelevant questions worse than before.

Two practical reflexes:

- **Replay (data mixing):** into your training data, mix **5-10% general instruction data** alongside your task data. The aim is to give the model a "spring of life" reminding it of its general behavior. Not a law, but a widespread community practice; measure the exactly right mixture ratio with your own validation set.
- **Alignment tax measurement:** run a small general-ability test **before and after** training (e.g. a short 20-50-question knowledge/reasoning checklist). Read the gain in task score together with the drop in the general score. If the general score drops clearly, raise the replay ratio or lower the learning rate.

:::note
The forgetting risk depends not only on whether you do SFT but also on **which method** you do it with. The "LoRA Learns Less and Forgets Less" study shows that low-rank LoRA training preserves out-of-target-domain abilities better than full fine-tuning (arXiv:2405.09673) — for the comparison, see the [LoRA and QLoRA](/en/llm/lora-qlora/) page.
:::

## Packing: Filling the GPU on Short Examples

Chat data is often short (a few hundred tokens). If you run with `max_length=1024`, each example fills only a small part of the window and the GPU's compute power flows away unused. **Packing** places multiple short examples into the same fixed-length block; training speeds up noticeably.

The one-line switch in TRL:

```python
training_args = SFTConfig(packing=True, packing_strategy="bfd", ...)
```

- `packing=True` turns packing on; the block length becomes `max_length`.
- `packing_strategy="bfd"` is the **best-fit decreasing** strategy and TRL's default: long examples are placed first, leftover tokens are truncated. Alternatives: `"bfd_split"` (splits the overflowing example) and `"wrapped"` (aggressive wrapping that can cut an example mid-way) (TRL v1.x docs).
- The fastest packing path (padding-free) requires FlashAttention 2 or 3; check against your setup.

Risks and things to watch:

- **Example boundaries:** if the attention layer doesn't properly separate the boundaries of the packed examples, the model may think the adjacent example is a continuation of the same context; you can see oddities like answers continuing with the next example's content instead of `EOS`. Modern TRL versions keep the boundaries separate; still, check outputs by eye after turning packing on.
- **Loss comparison:** since the loss in packing is computed "per token", the values can't be compared one-to-one with unpadded runs; compare experiments with the same setting (this note is also on the [Hyperparameters](/en/llm/hiperparametreler/) page).
- **Long examples:** if most of your data is already close to `max_length`, packing's gain shrinks.

## What Is Measured After SFT?

When training finishes, you should have answers to three questions:

1. **Did it learn?** Prepare a "task test" of 30-100 questions matching your task definition; put the pre- and post-training answers side by side. If you chose a measurable task (classification, format compliance), turn the result into a number.
2. **What do the metrics say?** For loss curves, token accuracy and signals to watch: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).
3. **Are the general abilities intact?** A short general test for the forgetting check; for a more comprehensive comparison, [Benchmarks](/en/degerlendirme/benchmarklar/).

## Wrapping Up

- SFT teaches behavior; it doesn't teach knowledge. Format, style and task behavior are gained here.
- Data quality comes before data quantity: collect consistent, correct, varied and deduplicated examples.
- Learn only from the assistant's answers with the loss mask (`assistant_only_loss=True`).
- Avoid memorization with 1-3 epochs, a low-to-mid learning rate and validation tracking.

Next steps:

- Combine this flow with [LoRA and QLoRA](/en/llm/lora-qlora/) for a bigger model or less VRAM.
- Measure that the training actually worked with the [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) page.
- For the end-to-end command flow, follow the [Step-by-Step Training](/en/llm/adim-adim-egitim/) guide.

## Sources and Further Reading

- [LIMA: Less Is More for Alignment (arXiv:2305.11206)](https://arxiv.org/abs/2305.11206) — strong instruction-following results with 1,000 carefully selected examples, without RLHF.
- [s1: Simple test-time scaling (arXiv:2501.19393)](https://arxiv.org/abs/2501.19393) — test-time scaling with 1,000 examples + "budget forcing".
- [TÜLU 3: Pushing Frontiers in Open Language Model Post-Training (arXiv:2411.15124)](https://arxiv.org/abs/2411.15124) — open, multi-stage post-training recipes.
- [TRL — SFT Trainer docs](https://huggingface.co/docs/trl/sft_trainer) — current definitions of the `assistant_only_loss`, `completion_only_loss`, `packing` and `packing_strategy` parameters.
- [LoRA Learns Less and Forgets Less (arXiv:2405.09673)](https://arxiv.org/abs/2405.09673) — the experimental comparison on forgetting and off-target performance.
- [transformers — Chat templating](https://huggingface.co/docs/transformers/chat_templating) — chat templates and the assistant mask (`return_assistant_tokens_mask`).
