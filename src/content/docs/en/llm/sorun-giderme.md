---
title: "Troubleshooting: Errors Encountered in Training"
description: "From CUDA memory errors to NaN loss, from Windows traps to disk issues and GGUF/version mismatches: a symptom-cause-fix guide to the 11 common problems in training."
dogrulama: 2026-11-20
---

When you hit an error during training, don't panic: 90% of the problems that eat experienced people's days are one of the eleven headings on this page. Each heading follows this structure: **symptom → cause → fix priority order**. Try the fixes in order; after each step restart the training and observe the result.

**Quick index:**

| Your complaint | Section |
| --- | --- |
| "CUDA out of memory" | 1 |
| Loss NaN / inf | 2 |
| The loss never drops | 3 |
| The model talks nonsense | 4 |
| Training is very slow | 5 |
| Windows-specific errors | 6 |
| "input too long" / context overflow | 7 |
| "no space left on device" | 8 |
| "Expected all tensors to be on the same device" | 9 |
| "Broken speech in Ollama/GGUF" | 10 |
| "bitsandbytes / CUDA version error" | 11 |

## 1. CUDA out of memory (The Most Common)

**Symptom:** `torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate ...` — training sometimes drops at the very start, sometimes hours later.

**Cause:** the memory needed has exceeded what's on your GPU. The three most expensive items: model weights, gradients + optimizer state, and activations (sequence length × batch).

**The fix ladder — descend in order:**

| # | Step | Effect | Cost |
| --- | --- | --- | --- |
| 1 | Lower `per_device_train_batch_size` to 1 | High | Slightly slower |
| 2 | Preserve the effective batch with `gradient_accumulation_steps` (e.g. raise to 8) | — | A bit slower |
| 3 | Shorten `max_length` (e.g. 2048 → 1024 → 512) | High | Long examples get truncated |
| 4 | Turn on `gradient_checkpointing=True` | Mid-high | ~20-30% slower |
| 5 | Switch to 4-bit QLoRA (`load_in_4bit=True`) | Very high | A small quality/speed cost |
| 6 | A smaller model (8B → 4B) or a smaller `r` | Very high | Task performance may drop |
| 7 | Move to the cloud (a bigger GPU) | Problem ends | A money cost |

```bash title="monitor_vram.sh"
# Linux / WSL2: live VRAM tracking
watch -n 1 nvidia-smi

# A one-off summary query
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

If you want to measure peak memory from inside Python: `torch.cuda.max_memory_allocated() / 1024**3` gives the highest allocation so far in GB; the counter resets with `torch.cuda.reset_peak_memory_stats()`. This value can be a bit lower than what `nvidia-smi` shows — the difference is PyTorch's cache pool, not a leak.

:::caution
**"VRAM looks idle but I'm getting OOM" note (Windows):** on Windows, browser tabs, game clients and even the desktop hold GPU memory; Task Manager may show it as "shared memory". Closing the browser before training sometimes gains 1-2 GB. Also `torch.cuda.empty_cache()` only releases idle cache; don't expect miracles during an active training.
:::

:::danger
Environment-variable tricks like `max_split_size_mb` sometimes help, but while the root problem is obvious (model + batch + sequence), don't waste time with them; take one more step down the ladder.
:::

Related pages: [VRAM Math](/en/donanim/vram-hesabi/), [LoRA and QLoRA](/en/llm/lora-qlora/), [Cloud Options](/en/donanim/bulut-secenekleri/).

## 2. The Loss Goes NaN or inf

**Symptom:** `nan` or `inf` in the loss table; afterwards all gradients corrupt and the model becomes garbage.

**Causes and fixes (in order):**

1. **The learning rate is too high** — the model lurches at the start. Halve the lr; if you started at 2e-4 for LoRA, try 1e-4. Details: [Hyperparameters](/en/llm/hiperparametreler/).
2. **fp16 instability** — fp16's numeric range is narrow; overflow produces NaN. If possible use `bf16=True` (RTX 30xx and later support it). If you must stay on an old card, keep loss scaling on (the Trainer does it by default).
3. **Broken data** — an example may contain a numeric field with NaN or a broken character sequence. Refresh the data: write a small check script that verifies text fields are strings and numbers are finite.
4. **Missing warmup** — jumping straight to the target lr at the very start of training causes spikes; add `warmup_steps=0.03` (v5; formerly `warmup_ratio` — the old name errors out on current transformers versions).

:::tip
A simple way to find which example NaN came from: split the training data into small chunks of 100 examples and narrow down by experiment which chunk produced the NaN. Usually the culprit is a few broken examples in a thousandth slice of the data.
:::

Related page: [Hyperparameters](/en/llm/hiperparametreler/).

## 3. The Loss Isn't Dropping / The Model Isn't Learning

**Symptom:** the loss is nearly flat throughout training; the model's output is identical to before training.

**The checklist (look in order):**

1. **Data format and chat template** — the most common cause! If you didn't use `apply_chat_template` in training, or the data's field names differ from what's expected, the model may actually be seeing "irrelevant text". Pass one example through the tokenizer and read it **with human eyes**.
2. **The learning rate is too low** — doing LoRA with a full fine-tuning lr (2e-5) is the classic mistake; LoRA wants 1e-4 – 2e-4.
3. **No layer may be training at all** — if you use PEFT, check the `model.print_trainable_parameters()` output; if you see "0%", LoRA was applied to the wrong place (e.g. `target_modules` matches no layer name).
4. **Labels entirely masked** — if you use `assistant_only_loss` and the data template is broken, all labels may be `-100` and the loss becomes meaningless. Be suspicious if the loss value is exactly 0 or a fixed odd value.
5. **Tokenizer mismatch** — if the model and tokenizer were loaded from different versions (e.g. base vs. instruct), tokens don't match. Load both from the same model identity.

Related pages: [Instruction Tuning (SFT)](/en/llm/sft/), [Data Formats](/en/veri/veri-formatlari/).

## 4. Training Finished but the Model Talks Nonsense

**Symptom:** "the loss dropped, everything looked fine, but the model either repeats the same sentence, doesn't answer the question, or produces meaningless text."

This is the most misleading scenario of the training process. Check in order:

1. **Wrong chat template (the classic):** if the template used in training differs from the one used at inference, the model "falls apart". If your training data has the Qwen template, the same template must be used at inference too: `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)`.
2. **Over-memorization (overfitting):** many epochs + little data = the model repeats the training examples word for word and stumbles on new questions. Fix: reduce epochs, watch the validation loss ([Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/)).
3. **The adapter was never loaded:** if you loaded only the base model instead of `PeftModel.from_pretrained(base_model, "./adapter")`, of course you see no change. Verify that your inference script loads the adapter.
4. **Data quality:** if some of the examples are translation residue, half sentences or wrong answers, the model becomes their average. Read 200 examples by hand — how many are really of example-worthy quality?
5. **Generation settings:** if generation parameters like `temperature`, `top_p`, `repetition_penalty` are broken, the model is innocent. Try with defaults (around `temperature=0.7, top_p=0.9`).

Related pages: [Instruction Tuning (SFT)](/en/llm/sft/), quick generation testing with [Ollama](/en/kullanim/ollama/).

## 5. Training Is Progressing Very Slowly

**Symptom:** seconds per step; GPU usage hovers below 100% in `nvidia-smi`.

**Causes and fixes:**

- **A data-loading bottleneck** — the GPU is waiting for data. Raise `dataloader_num_workers` (e.g. 4-8); tokenize the data in advance and save it to disk (don't repeat the map operation on every run; use `dataset.map(..., num_proc=4)` and `save_to_disk`).
- **Packing off** — on short examples half the GPU idles; `packing=True` gains noticeable speed ([Hyperparameters](/en/llm/hiperparametreler/)).
- **Running with batch 1** — if forced, raise gradient accumulation; but if possible raise the batch to 2-4.
- **No Flash Attention** — when on, it provides a notable speedup; but installing it (especially on Windows) is a chore. Run everything without it first, then add it as an optimization.

:::note
**Expectation management:** on a single RTX 4090, one epoch of QLoRA training of a 4B model on 5,000 examples takes roughly **1-2 hours**. If you say "it finished in 10 minutes", something is wrong (probably the data isn't being read); if you say "it's been 3 days", packing is off or there's a data bottleneck.
:::

Related pages: [Hyperparameters](/en/llm/hiperparametreler/), [VRAM Math](/en/donanim/vram-hesabi/).

## 6. Windows-Specific Problems

Training directly on Windows is possible, but the ecosystem mostly assumes Linux. The most practical fix: **WSL2** (a real Linux environment inside Windows) — GPU drivers are supported directly and packages like `bitsandbytes`, `flash-attn`, `triton` install without trouble.

- **bitsandbytes version issues:** in a native Windows install some versions error; move to WSL2 or use the current `bitsandbytes` version. 90% of the "4-bit training won't turn on" error relates to this. Setup details: [Local Setup](/en/donanim/yerel-kurulum/).
- **The long file path error:** on Windows, paths exceeding 260 characters (deep `site-packages` + cache folders) produce errors. Fix: turn on the "enable long paths" setting (administrator PowerShell: `Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name LongPathsEnabled -Value 1`) and keep projects under a short path (e.g. `C:\ml\`).
- **triton / flash-attn setup:** on native Windows it may need compiling and can take hours. Use WSL2; if you don't need flash-attn, don't install it.

Related page: [Local Setup](/en/donanim/yerel-kurulum/).

## 7. Token / Context Overflow Errors

**Symptom:** the `Token indices sequence length is longer than the specified maximum...` warning, an `input too long` error, or oddly truncated examples.

**What to do:**

1. Look at the data's token-length distribution: measure with `dataset.map(lambda x: {"n": len(tokenizer(x["text"])["input_ids"])})` and look at the percentiles. Choose `max_length` to cover 95%.
2. Make the truncation strategy deliberate: in chat, **never** truncate the system prompt; in long conversations keep the last N turns.
3. Don't exceed the model's architectural ceiling (e.g. 8,192 or 32,768 tokens) — exceeding it gives silent corruption or an error.

Related pages: [Tokenization](/en/temeller/tokenizasyon/), [Hyperparameters](/en/llm/hiperparametreler/).

## 8. The Disk Filled Up

**Symptom:** "no space left on device" mid-training, or an error while saving a checkpoint. Model trainings inflate the disk fast: each checkpoint takes the full size of the model (and more, with the optimizer state).

**Fixes:**

- **Checkpoint strategy:** thin out the save frequency with `save_strategy` and `save_steps`; with `save_total_limit=2` everything but the newest 2 checkpoints is deleted automatically.
- **Clean old experiments:** regularly delete the old `checkpoint-*` folders under `output_dir`.
- **The Hugging Face cache:** every downloaded model accumulates under `~/.cache/huggingface` (Windows: `C:\Users\<user>\.cache\huggingface`). Delete the models you don't use; you can move the cache to another drive with the `HF_HOME` environment variable.
- **The LoRA advantage:** if you're training an adapter, the results are already MB-sized; the real load is in the checkpoints — that's why `save_total_limit` is the most effective fix.

## 9. Device Mismatch: "Expected all tensors to be on the same device"

**Symptom:** `RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!`

**Cause:** part of the model or the inputs stayed on the GPU, part on the CPU. This is especially common in 4-bit models loaded with `device_map="auto"`: some layers are deliberately kept on the CPU, and intervening in the model by hand upsets the balance.

**Fixes (in order):**

1. If there's a `model.to("cuda")` or `model.cuda()` call in the code, **remove it** — it's forbidden on models using `device_map`.
2. Move the input tensors to the model's device: `inputs = {k: v.to(model.device) for k, v in inputs.items()}`.
3. If you use the `Trainer` for training, leave device placement to the Trainer; don't intervene by hand.
4. If the problem persists, try explicit single-GPU placement instead of `device_map="auto"`: `device_map={"": 0}`.

Related page: [Local Setup](/en/donanim/yerel-kurulum/).

## 10. The Model Trained but Talks Broken in Ollama/GGUF

**Symptom:** the same model answers properly in Python (with transformers/PEFT), but when converted to GGUF and run in Ollama it shows one of three classic behaviors: echoing the question, producing continuation text like the base model, or writing the chat-template tokens (e.g. `<|im_start|>` / `<|im_end|>`) as plain text.

**Cause:** during training the model saw examples tokenized with a specific chat template; if that template isn't applied at inference, it starts doing "text completion" instead of "question answering". The Unsloth documentation names "a chat template that isn't the same as the one used in training" as the most common cause of such broken outputs. If the template wasn't carried into the GGUF/Modelfile layer, Ollama feeds the model raw text; the result is the familiar "broken speech" picture.

**Fixes (in order):**

1. **Isolate the suspicion:** before GGUF, test the model with transformers/PEFT using `tokenizer.apply_chat_template(..., add_generation_prompt=True)` (the inference examples on the [SFT](/en/llm/sft/) page). If it answers properly in Python, the fault is in the export / template-carrying layer.
2. **Include the template in the export flow:** produce the GGUF while the tokenizer has the training chat template set (e.g. Unsloth's `save_pretrained_gguf` flow — Unsloth emphasizes the "same template in training and inference" rule and recommends conversational notebooks to enforce the template). Verify with a small test that your converter actually embedded the template into the GGUF file; if it didn't, go to step 3.
3. **Define the template in the Ollama Modelfile:** if the template isn't in the GGUF, supply it externally with a `TEMPLATE` block and `PARAMETER stop`; the closing token varies by model (e.g. `<|im_end|>` in Qwen/ChatML, `<|eot_id|>` in Llama 3). A ready Modelfile example is on the [Ollama Guide](/en/kullanim/ollama/) page.
4. **Check the data side too:** if the fields in the training data were mapped wrongly, the model may never have learned the template; compare your data against the [Data Formats](/en/veri/veri-formatlari/) page.

:::note
The summary of Unsloth's official FAQ: the most common fix for these behaviors is to enforce the chat template used in training at inference too. When you suspect, the first test is this question: "Does the same prompt work in Python on the pre-GGUF model?"
:::

Related pages: the [Ollama Guide](/en/kullanim/ollama/), [Data Formats](/en/veri/veri-formatlari/), [SFT](/en/llm/sft/).

## 11. Version Mismatches: bitsandbytes / CUDA / PyTorch

**Symptom:** classic version-related errors at setup or training start: `ImportError: libbitsandbytes_cuda...so: cannot open shared object file`, `CUDA error: no kernel image is available for execution on the device`, or the system driver not matching the CUDA version PyTorch expects.

**Cause:** these three components are a chain: the GPU driver → the CUDA version PyTorch was compiled with → the CUDA version bitsandbytes was compiled with. If one link in the chain mismatches, the package won't install (an import error), the compiled kernel can't be found, or training silently drops before starting.

**Diagnosis steps (in order):**

```bash title="version_diagnosis.sh"
# 1) The driver version and the highest supported CUDA version ("CUDA Version" is the driver's ceiling)
nvidia-smi

# 2) The CUDA version PyTorch sees and GPU access
python -c "import torch; print(torch.version.cuda, torch.cuda.is_available())"

# 3) The bitsandbytes version and install form
pip show bitsandbytes
```

If `torch.version.cuda` returns `None`, the CPU wheel was installed; if `torch.cuda.is_available()` returns `False`, the GPU isn't visible even at the driver level.

**Fix directions:**

- **Pick a compatible wheel:** install PyTorch with the command matching your OS and CUDA version from the official install selector; prefer the bitsandbytes version matching PyTorch's CUDA major version. Since version numbers change fast, we give no fixed numbers here — the selector and the bitsandbytes release notes are authoritative for the current match.
- **A clean virtual environment:** half-finished installs are the most common cause of these errors; delete the venv and install in the right order in one go (PyTorch first, then bitsandbytes).
- **WSL2 on Windows:** bitsandbytes/CUDA wheels mostly assume Linux; if the problem persists on a native Windows install, WSL2 is the smoothest path.

:::tip
Don't type the install command by hand: PyTorch's "Get Started Locally" selector produces the right `pip install` line for your OS + CUDA version; the link is in the sources at the end of the page.
:::

Related page: [Local Setup](/en/donanim/yerel-kurulum/).

## Still Not Solved?

Copy and search the **full** error message: most error messages are ones hundreds of people hit before you. For that:

- The project/library's GitHub issues and discussions (e.g. the TRL, Unsloth, transformers repos),
- The Hugging Face forums and Discord communities,
- For Turkish communities and generally useful links, see the [Useful Links](/en/kaynaklar/faydali-linkler/) page.

When sharing a problem, adding the following multiplies your chance of an answer: the full error text, the tool and versions you use, the GPU model and VRAM, the command/script you ran, and the fixes you've tried.

## Sources and Further Reading

- [PyTorch CUDA memory management](https://docs.pytorch.org/docs/stable/notes/cuda.html) — the official explanation of allocation/cache behavior and memory APIs like `max_memory_allocated`.
- [PyTorch: the local setup selector](https://pytorch.org/get-started/locally/) — generates the install command matching your OS and CUDA version.
- [bitsandbytes (GitHub)](https://github.com/bitsandbytes-foundation/bitsandbytes) — CUDA wheels, install docs and release notes.
- [Unsloth: Troubleshooting and FAQs](https://unsloth.ai/docs/basics/troubleshooting-and-faqs) — the most common causes of GGUF/Ollama and chat-template-related broken outputs.
- [Transformers: Troubleshooting](https://huggingface.co/docs/transformers/en/troubleshooting) — the library's official error guide, including CUDA out of memory.
