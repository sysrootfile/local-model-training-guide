---
title: "Step by Step: Train Your First Model (End to End)"
description: "From data to a trained, working assistant — a fully coded end-to-end guide on a single page."
dogrulama: 2026-11-20
---

This page is the heart of the guide: we will reach **a trained, tested and working model** starting from scratch. All the steps contain real commands and real code.

**Our scenario:** we want to train a Turkish customer-support assistant.

| Decision | Our choice | Why? |
| --- | --- | --- |
| Model | Qwen3-4B | As of 2026 one of the strongest open models in the 4B class; good at Turkish |
| Method | QLoRA | A low-VRAM, fast and safe start ([why?](/en/llm/lora-qlora/)) |
| Tool | Unsloth | Fast on a single GPU and very simple in code ([tool comparison](/en/llm/araclar/)) |
| Data | 500-5,000 Turkish instruction examples | Quality matters more than quantity ([data types](/en/veri/veri-turleri/)) |

:::note[Prerequisite]
This guide assumes an installed Python environment. If you don't have one, first complete the [Local Setup](/en/donanim/yerel-kurulum/) page, or continue without installing anything with a [free cloud GPU](/en/donanim/bulut-secenekleri/).
:::

## The Journey Map

```text
1. Prepare the data      (30-60 min)  → JSONL, in chat format
2. Set up the environment (10-15 min)  → Python + Unsloth
3. Load the model        (5 min)      → Qwen3-4B, 4-bit
4. Add the LoRA adapter  (2 min)      → Small trainable layers
5. Start the training    (30 min-2 h) → trainer.train()
6. Test it               (5 min)      → Quick inference
7. Save / merge          (5-10 min)   → Adapter or merged model
8. Run it                (10 min)     → GGUF → Ollama
9. Evaluate              (30 min)     → Mini test set, blind comparison
```

## Step 1: Prepare the Data

The training's success depends largely on this step. You have two options:

**Option A — Use a ready Turkish dataset:** download one of the Turkish sets on the [Where to Find Data](/en/veri/veri-nereden-bulunur/) page (e.g. a set from the `atasoglu/turkish-instruction-datasets` collection or the `ogulcanaydogan/Turkish-LLM` training data).

**Option B — Build from your own data:** extract 500-5,000 examples from the support records/FAQs in your hands. For format and quality: [Data Formats](/en/veri/veri-formatlari/) and [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).

Your data must be in this chat format — one JSON per line:

```json title="data.jsonl"
{"messages": [{"role": "system", "content": "You are a customer support assistant."}, {"role": "user", "content": "When will my shipment arrive?"}, {"role": "assistant", "content": "With your tracking number ..."}]}
{"messages": [{"role": "user", "content": "How many days do I have to return an item?"}, {"role": "assistant", "content": "The return period is 14 days..."}]}
```

Short code that loads the data and splits it into training/validation:

```python title="prepare_data.py"
from datasets import load_dataset

# Load from your own JSONL file (Option B)
ds = load_dataset("json", data_files="data.jsonl", split="train")

# If you want to download a ready dataset (Option A) — always check the field names:
# ds = load_dataset("username/dataset-name", split="train")
# print(ds.column_names)

# Set aside 5% for validation
splits = ds.train_test_split(test_size=0.05, seed=42)
train_data = splits["train"]
validation_data = splits["test"]

print(f"Training examples: {len(train_data)} | Validation: {len(validation_data)}")
print(train_data[0])  # eyeball the first example — mandatory!
```

:::caution
Every dataset's field names differ (`instruction/input/output` or `prompt/completion` etc.). After loading, check with `ds.column_names` and, using the conversion examples on the [Data Formats](/en/veri/veri-formatlari/) page, convert into your own `messages` structure.
:::

## Step 2: Set Up the Environment

```bash title="setup.sh"
pip install unsloth
# If your environment already contains PyTorch, the command above suffices.
# On Colab/Kaggle this command works on its own; for CUDA compatibility locally,
# see the current setup notes at https://docs.unsloth.ai
```

:::tip
If you're using Google Colab or Kaggle, don't forget to select the GPU: on Colab **Runtime → Change runtime type → GPU**, on Kaggle **Settings → Accelerator → GPU T4 x2**.
:::

## Step 3: Load the Model

We load the model in 4-bit — VRAM usage drops several-fold this way.

```python title="training.py (1/4)"
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3-4B-bnb-4bit",  # a version prepared for 4-bit
    max_seq_length=2048,                      # the context window: adjust to your data
    load_in_4bit=True,
    dtype=None,                               # automatic: bf16 for Ampere+
)
```

:::note
You can find ready 4-bit repos like `unsloth/Qwen3-4B-bnb-4bit` by searching Hugging Face. If you want to try a different model (Gemma 3, Llama 3.2), only `model_name` changes — the flow is the same. For model choice: [Roadmap](/en/baslangic/yol-haritasi/).
:::

:::note[Unsloth version note]
In newer Unsloth versions, instead of `FastLanguageModel` you may see `FastModel`, the superset that also covers visual models. For language models both do the same job; use whichever your version offers.
:::

## Step 4: Add the LoRA Adapter

The base model's weights freeze; only the small "adapter" layers are trained. The logic of the parameter choices: [LoRA and QLoRA](/en/llm/lora-qlora/).

```python title="training.py (2/4)"
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                 # Rank: 8 is lighter, 32 is more capable
    lora_alpha=32,        # usually r x 2
    lora_dropout=0.0,     # 0 is fast and usually sufficient
    target_modules=[      # apply to all attention + MLP layers
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_gradient_checkpointing="unsloth",  # VRAM saving
    random_state=42,
)
```

## Step 5: Convert the Data to the Chat Template and Start Training

The model must see the data with its own **chat template**. We have the tokenizer do this conversion:

```python title="training.py (3/4)"
from trl import SFTTrainer, SFTConfig

def to_chat(example):
    text = tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False
    )
    return {"text": text}

train_data = train_data.map(to_chat)
validation_data = validation_data.map(to_chat)

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,      # TRL v1: the new name of the tokenizer parameter
    train_dataset=train_data,
    eval_dataset=validation_data,
    args=SFTConfig(
        dataset_text_field="text",
        max_length=2048,                 # TRL v1: max_length (formerly max_seq_length)
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,   # effective batch = 2 x 4 = 8
        warmup_steps=10,
        num_train_epochs=2,
        learning_rate=2e-4,              # a typical value for LoRA
        lr_scheduler_type="cosine",
        optim="adamw_8bit",
        weight_decay=0.01,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_steps=100,
        output_dir="output",
        seed=42,
    ),
)

trainer.train()
```

:::note[Field names changed in TRL v1]
Two names were renewed in TRL v1.x (TRL v1.15 docs, 2026): the `SFTConfig` field is now `max_length` (instead of `max_seq_length` in older versions) and the `SFTTrainer` parameter is now `processing_class` (formerly `tokenizer`; using the old name errors out in new versions). Unsloth's own `FastLanguageModel.from_pretrained(max_seq_length=...)` parameter, however, continues to be used under the same name — they are parameters of two different libraries, don't mix them.
:::

:::tip
You can find what the hyperparameters mean and how to change them per situation on the [Hyperparameters](/en/llm/hiperparametreler/) page. On your first attempt start with the values above and play with them as you see the results.
:::

During training you'll see a flow like this in the console:

```text title="example training output (values are illustrative)"
Step 10/250   | Loss: 2.41
Step 50/250   | Loss: 1.87
Step 100/250  | Loss: 1.52   | Validation loss: 1.61
Step 200/250  | Loss: 1.21   | Validation loss: 1.44
```

If the loss is dropping regularly, things are on track. How to read the curves: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).

## Step 6: Test It

After training, the first job is trying the model with your own hands:

```python title="training.py (4/4)"
from unsloth import FastLanguageModel

FastLanguageModel.for_inference(model)  # Switch to inference mode (faster)

messages = [
    {"role": "system", "content": "You are a customer support assistant."},
    {"role": "user", "content": "My order still hasn't arrived, what should I do?"},
]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

output = model.generate(**inputs, max_new_tokens=256, temperature=0.7, do_sample=True)
answer = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(answer)
```

:::caution[The most classic trap]
When testing you must use **the exact same chat template** you used in training (`apply_chat_template`). If you hand-build text like "User: ... Assistant:", the model may talk nonsense; that doesn't mean the model is bad. Details: [Troubleshooting](/en/llm/sorun-giderme/).
:::

## Step 7: Save

```python title="save.py"
# Save only the adapter (a few MB — recommended)
model.save_pretrained("lora_adapter")
tokenizer.save_pretrained("lora_adapter")

# Save the merged full model (needed for distribution/GGUF — about 8-10 GB for a 4B model)
# model.save_pretrained_merged("merged_model", tokenizer, save_method="merged_16bit")
```

The difference between the adapter and merging: [LoRA Merging](/en/kullanim/lora-birlestirme/).

## Step 8: Run Your Own Model

The most practical way: convert the model to GGUF format and run it with Ollama.

```python title="gguf_export.py"
# Direct GGUF export with Unsloth (about 2-5 GB)
model.save_pretrained_gguf("model-gguf", tokenizer, quantization_method="q4_k_m")
```

Then introduce the GGUF file in the `model-gguf` folder to Ollama. Step by step: the [Ollama Guide](/en/kullanim/ollama/). Alternative: [API serving with vLLM](/en/kullanim/sunma-api/).

## Step 9: Evaluate

Finishing training doesn't finish the job. Prepare your own mini test set of 20-50 questions and probe the model regularly; note on which questions it's good and on which it's bad. Protocol: [Benchmarks and Real Evaluation](/en/degerlendirme/benchmarklar/).

### The Post-Training Checklist

When your first training is done, go through this list start to finish — each item is a few minutes of work, but the most expensive errors are caught here:

- [ ] The adapter (or merged model) was loaded from the right folder; it points to the directory you saved
- [ ] The test used **exactly the same** chat template as in training (`apply_chat_template`)
- [ ] The system prompt is identical to the training one
- [ ] A mini test set of 20-50 questions was prepared and run with both the **pre-training** and **post-training** models
- [ ] The comparison was done "blind": preferences were marked without knowing which answer came from which model
- [ ] Regression check: the model still gives reasonable answers to a few general questions outside the test set
- [ ] Training loss and validation loss were read together (is there a memorization signal?) — [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/)
- [ ] The results were written into a small notes file: which setting, which score, which observation

## The Sneakiest Trap: The Model Works in Python but Talks Broken in GGUF/Ollama

**The symptom:** when you test in Python the model answers properly; when you convert to GGUF and run it in Ollama, it echoes the question ("When will my shipment arrive? When will my shipment arrive?"), keeps writing on its own, or continues the sentence like the untrained base model.

**The cause:** the culprit is almost always the same: **the chat template wasn't carried over**. The model saw the "system / user / assistant" markers in training; if the runtime side doesn't know which template to apply, it uses a different default. Fed the wrong markers, the model can't recognize the pattern it saw in training and its behavior reverts to the base model. The model isn't broken — it's packaged in the wrong format.

**The fix is one of two paths:**

1. **Carry the template in the export:** when you use `save_pretrained_gguf` with Unsloth, Unsloth automatically creates the `Modelfile` Ollama wants, and that file **contains the chat template used in training** (Unsloth documentation, 2026). GGUF files can carry the template in the `tokenizer.chat_template` metadata field; if you convert with other tools, check that this field made it into the file.
2. **Define it manually in the Modelfile:** if the template is missing, define the chat template in the Ollama Modelfile with `TEMPLATE`, and the stop sequences with `PARAMETER stop` (the Ollama modelfile doc; the [Ollama Guide](/en/kullanim/ollama/) on the site illustrates this structure):

```dockerfile title="Modelfile (skeleton)"
FROM ./model-q4_k_m.gguf

# Fill the template exactly as the tokenizer template you used in training
TEMPLATE """{{ .System }}...{{ .Prompt }}"""

# Stop sequences (e.g. <|im_end|> for Qwen3)
PARAMETER stop "<|im_end|>"
```

:::caution[Never write the template "approximately"]
The `TEMPLATE` above is a **skeleton** — don't invent the real value. Take the template from your tokenizer (e.g. the contents of `tokenizer.chat_template`) and make sure it is **identical** to the template you used in training. The Unsloth documentation also emphasizes precisely this: the template used in fine-tuning and the template on the runtime side must be the same; a template mismatch is the most common reason a sound model looks "broken".
:::

For the details of the chat format used in training: [Data Formats](/en/veri/veri-formatlari/).

## Next Steps

Your model is running — what can you do now?

- **Better results:** improve data quality ([Data Cleaning](/en/veri/veri-temizleme/)), increase the example count, play with the [Hyperparameters](/en/llm/hiperparametreler/).
- **Continued training:** add new data to the same adapter.
- **Style/preference:** fine-tune the behavior with [DPO](/en/llm/dpo-rlhf/).
- **Share:** [upload to Hugging Face](/en/kullanim/huggingface-paylasim/) and let the community find you.

## Common Mistakes (A Quick Look)

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `CUDA out of memory` | Batch/sequence size too big | [Troubleshooting: the OOM ladder](/en/llm/sorun-giderme/) |
| Loss not dropping | Format/template error, lr too low | Eyeball the data's `text` field |
| Answers are nonsense | Template mismatch in testing | Use `apply_chat_template` |
| Training very slow | The model isn't fully on the GPU | Check with `nvidia-smi` |
| The model echoes in Ollama / talks like the base model | The chat template wasn't carried into the GGUF/Modelfile | Define `TEMPLATE` and `PARAMETER stop` in the Modelfile (the "Sneakiest Trap" section above) |
| The merged model is worse than expected | Merging directly onto 4-bit weights | Merge in 16-bit; follow the [LoRA Merging](/en/kullanim/lora-birlestirme/) guide |
| Regression on off-domain questions after training | Catastrophic forgetting (no replay, high lr) | Add 5-10% general data to the training mixture, lower the lr; measure with [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) |

:::tip[A closing word]
Your first training won't be perfect — that's normal. What matters is **living the loop once from end to end**: data → training → testing → tuning. The second and third attempts will be much faster and much better.
:::

## Sources and Further Reading

- [TRL — SFT Trainer and SFTConfig reference](https://huggingface.co/docs/trl/sft_trainer) — the current definitions of all SFT parameters like `max_length`, `packing`, `assistant_only_loss` (TRL v1.15, 2026).
- [Unsloth documentation](https://unsloth.ai/docs) — all flows including `FastLanguageModel`, GGUF export and saving for Ollama (the old address `docs.unsloth.ai` redirects here).
- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314) — the foundational paper of the idea of training LoRA on a 4-bit-quantized base model; the source of this guide's method.
- [TRL (GitHub)](https://github.com/huggingface/trl) — the source repo of SFT, DPO and the other training interfaces; release notes and examples.
