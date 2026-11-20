---
title: "Sharing on Hugging Face: Opening Your Model to the World"
description: "A guide to uploading your trained model to the Hugging Face Hub, organizing GGUF files, writing an effective model card and choosing a license."
dogrulama: 2026-11-20
---

You trained the model, tested it, liked it. The next step is sharing it. The Hugging Face Hub is a free platform where you can open your model to the world with a single command; on this page we cover uploading, GGUF files, the model card and licensing end to end.

## Why share?

- **Real feedback:** those who download the model report the errors and usage scenarios you can't see; your model improves thanks to the community.
- **A contribution to the Turkish ecosystem:** the number of open Turkish models and datasets is still tiny compared to English. Your modest model trained with 500 examples can save someone doing a similar job days of their time.
- **Portfolio value:** "there's a model I trained in that repo, downloadable and tryable" is one of the strongest résumé lines there is.
- **Convenience:** the HF Hub is free for public models and datasets; downloading, versioning and demos (Spaces) live under one roof.

## Preparation: the account, the token and signing in

1. Open a free account at [huggingface.co](https://huggingface.co).
2. Create an **access token**: `Settings → Access Tokens → Create new token` and choose the **Write** permission. The token is shown only once; copy it somewhere safe. (See `huggingface.co/settings/tokens`)
3. Sign in from the terminal:

```bash title="hf_login.sh"
pip install -U huggingface_hub

# The new-generation command-line tool (recommended as of 2026)
hf auth login

# The equivalent command common in older versions:
# huggingface-cli login
```

Paste your token where asked. At the "Add token as git credential?" question, you can choose Yes if you'll also work with `git`.

The command set's new name is `hf`; `huggingface-cli` is the deprecated old name and has ceded its place to `hf`. The download side's counterpart is `hf download`: `hf download username/model` downloads the whole repo, `hf download username/model config.json` a single file.

## Uploading the model

### With Python: `push_to_hub`

The most used method is sending the folder in your hands straight to the repo:

```python title="upload.py"
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_DIR = "merged-model"               # your local folder
REPO_NAME = "username/qwen3-4b-turkish"  # replace with your own HF username

model = AutoModelForCausalLM.from_pretrained(MODEL_DIR)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

model.push_to_hub(REPO_NAME)       # uploads the weights (splitting into pieces if needed)
tokenizer.push_to_hub(REPO_NAME)   # the tokenizer files + the chat template
```

Notes:

- If the repo doesn't exist, it's created automatically on the first call.
- If there's a `README.md` in the folder, it's uploaded too; that file becomes your model card (described below).
- If a large upload gets cut, re-running the command is safe; missing files are completed.

### From the command line: `hf upload`

```bash title="hf_upload.sh"
# Upload everything in the folder to the repo
hf upload username/qwen3-4b-turkish ./merged-model .

# The equivalent command common in older versions:
# huggingface-cli upload username/qwen3-4b-turkish ./merged-model .
```

## The practice of uploading GGUF files

If you want to share your model's GGUF version too (which raises the download count), there are two built-in methods:

1. **A `gguf/` folder inside the same repo:** the model weights sit at the repo's root, the GGUF files under `gguf/`. The file names should include the level: `qwen3-4b-turkish-Q4_K_M.gguf`, `qwen3-4b-turkish-Q8_0.gguf` etc. Unsloth's `push_to_hub_gguf` output uses this arrangement too.
2. **A separate GGUF repo:** opening a second repo with a "-GGUF" suffix, like `username/qwen3-4b-turkish-GGUF`, is the community standard; tools like LM Studio look for GGUF files in these suffixed repos.

```bash title="upload_gguf.sh"
# Uploading into the gguf/ folder inside the same repo
hf upload username/qwen3-4b-turkish ./model_gguf gguf
```

:::note
GGUF files go through large-file storage; `hf upload` handles that for you automatically. The Hub's backend moved from Git LFS to Xet starting in 2025 (below); you may still see the "LFS" label in old repos and tool interfaces.
:::

## Xet: the Hub's new storage backend

Through 2025, Hugging Face moved the Hub's large-file storage from Git LFS to a chunk-based backend called Xet; the migration announcements were published in March and July 2025. The difference for you produces two practical results:

- **Chunk deduplication:** files are split into chunks and identical chunks are stored only once. When you upload a new version of your model, only the changed chunks go; downloads containing previously downloaded chunks also speed up. In repeated attempts (v2, v3...) this difference is felt.
- **The client side:** `huggingface_hub` versions 0.32.0 and later install the `hf_xet` package by default; older clients keep working through the LFS bridge. The only thing you need to do is keep `huggingface_hub` current.

## safetensors: the weight format becoming standard

Sharing weights in the **safetensors** format instead of `.bin` (pickle) is the standard as of 2026. It has two justifications:

- **Security:** pickle files can run arbitrary Python code while loading; the Hub, for that reason, counts pickle files as risky and scans them. safetensors carries no structure enabling arbitrary code execution.
- **Speed:** safetensors loads tensors zero-copy; model startups are faster than pickle-based files.

The `save_pretrained(..., safe_serialization=True)` call you saw in the PEFT examples explicitly picks the safetensors output. Also fill the `library_name: transformers` and `pipeline_tag` fields on the model card: the Hub uses these fields to serve the right usage snippet and inference options on the model page. An important detail: in repos created after August 2024, the Hub no longer assumes the library automatically; writing `library_name` explicitly is required.

## Repo privacy: private first, then public

Sharing doesn't have to be a one-way door; the recommended flow is publishing hidden first:

1. Create the repo hidden: `create_repo("username/model-name", visibility="private")`. The current `huggingface_hub` doc uses the `visibility` parameter; the `private=True` you saw in older tutorials is the old spelling doing the same job. (`push_to_hub` creates the repo public if it doesn't exist; if you want hidden testing, open the repo in advance.)
2. Download the model from your own account and test it like an outside user; check the card looks right and the files uploaded completely.
3. If there's no problem, open the repo to the public: the visibility option on the repo's **Settings** page in the Hub interface, or programmatically `update_repo_settings(repo_id=..., private=False)`.

:::tip
If you want "share your contact details with me before downloading", the Hub's **gated repo** feature serves exactly that: the user requesting access has to share their username and email with you, and you approve.
:::

## Writing the model card (README.md)

The model card is the first page those downloading the model see; it should be the model's "user manual". A template you can copy and start filling:

````markdown title="README.md"
---
language:
- tr
license: apache-2.0
base_model: Qwen/Qwen3-4B
datasets:
- username/turkish-instruction-data
pipeline_tag: text-generation
library_name: transformers
tags:
- turkish
- lora
- qlora
---

# Qwen3-4B Turkish Instruction Model

This model is a fine-tune of Qwen3-4B with Turkish instruction
data, using QLoRA.

## Training Details

- **Method:** LoRA (QLoRA, a 4-bit NF4 base)
- **Hardware:** T4 16 GB
- **Data:** ~5,000 Turkish instruction examples (source and compilation note here)
- **Hyperparameters:** r=16, alpha=32, lr=2e-4, 1 epoch, cosine schedule

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "username/qwen3-4b-turkish"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

messages = [{"role": "user", "content": "Hello, introduce yourself."}]
inputs = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True, return_tensors="pt"
).to(model.device)
output = model.generate(inputs, max_new_tokens=256)
print(tokenizer.decode(output[0][inputs.shape[1]:], skip_special_tokens=True))
```

## Limitations

- Trained on a narrow dataset, it isn't reliable on every subject.
- It can hallucinate; critical decisions require verification.
- It's optimized for Turkish only.

## License

Apache-2.0 (subject to the base model's license).
````

The must-haves of a good card:

- **Front matter:** `language: tr`, `license`, `base_model`, `datasets` if any, plus `library_name: transformers` and `pipeline_tag`. The Hub derives the relationship (finetune, adapter, quantized or merge) from the `base_model` field itself and shows the derivation chain on the model page; `library_name` and `pipeline_tag` feed the usage snippet, the in-browser widget and the inference options. If you have evaluation results, add them into the text as a table too.
- **Training details:** the method, data, hardware, hyperparameters; someone else should be able to repeat your experiment.
- **A usage example:** working, copy-paste code.
- **Limitations:** be honest; this is the cards' most skipped but most valuable section.
- **License:** clarify according to the table below.

## Licenses: a short guide

| License | Summary | Example models |
|---|---|---|
| **Apache-2.0** | The freest including commercial use; attribution and patent terms | Qwen3, Mistral Small |
| **MIT** | A short, clear license imposing almost no conditions | Phi-4-mini |
| **Llama Community License** | Commercial use free but conditional: a separate agreement at 700 million+ monthly active users; "Llama" in the derivative's name and the "Built with Llama" notice | Llama 3.2, Llama 4 |
| **Gemma Terms of Use** | Commercial use free; compliance with the use policy and keeping the "Gemma" notice are required | Gemma 3 |
| **The Qwen license** | Most of the family is Apache-2.0; **some sizes are under the "Qwen Research License": commercial use closed**, with the "Built with Qwen" notice on distributed derivatives and a `"Notice"` attribution file required | Qwen2.5-3B (measured at this size, see [License, Personal Data and Model Card](/en/kullanim/lisans-ve-model-karti/)) |

:::danger License compliance is mandatory
Your derivative model's license **can't be freer** than the base model's license. For example, you can't publish a model you trained from Llama under an MIT license; the Llama Community License's conditions (naming included) apply to your derivative exactly as they are. Before publishing, be sure to read the license on the base model's card. Likewise, the **dataset's license** you used in training matters; sharing models trained on data that doesn't permit it can constitute rights infringement.
:::

:::note[The table above is a snapshot]
The license rows were written according to the official texts read on October 17, 2026 and the local packages on this machine; models' licenses may change in later versions. Rather than this page's general table, **opening and reading the license field of the package you yourself downloaded and used** is always more reliable. How it was measured — including the local Modelfile check — we show on the [License, Personal Data and Model Card](/en/kullanim/lisans-ve-model-karti/) page.
:::

## A mini demo with Spaces

The most convincing form of sharing a model is people being able to try it without downloading and setting it up. Hugging Face Spaces does exactly that: it's a small application page tied to your profile, and with the Gradio SDK even a chat interface consisting of a single `app.py` file suffices. You can start on the free CPU tier and upgrade to a GPU if it draws interest. Add the Space's link to your model card; the card → live demo → code/data repo trio is your project's showcase. For the setup steps, see the Gradio guide in the [Spaces docs](https://huggingface.co/docs/hub/spaces).

## Sources and Further Reading

- [Hub — Model Cards](https://huggingface.co/docs/hub/model-cards): the official schema of the card metadata fields (license, base_model, pipeline_tag, datasets, library_name).
- [huggingface_hub — CLI](https://huggingface.co/docs/huggingface_hub/guides/cli): the doc of the `hf auth login`, `hf upload`, `hf download` commands.
- [huggingface_hub — Repository management](https://huggingface.co/docs/huggingface_hub/guides/repository): the official guide to creating repos, changing visibility and gated access.
- [Hub — Using Xet Storage](https://huggingface.co/docs/hub/xet/using-xet-storage): the official doc of the `hf_xet` package and chunk deduplication.
- [Hub — the Xet migration announcement](https://huggingface.co/blog/xet-on-the-hub): the blog post announcing storage's move to Xet.
- [safetensors](https://huggingface.co/docs/safetensors/index): the doc of the safe and fast tensor format.
- [Hub — Spaces](https://huggingface.co/docs/hub/spaces): the entry page of the guide to setting up a demo with the Gradio SDK.

## Next Steps

- To see the whole flow from training to sharing once more: [Step-by-Step Training](/en/llm/adim-adim-egitim/)
- Turkish datasets and model repos: [Useful Links and Resources](/en/kaynaklar/faydali-linkler/)
- Frequently asked license/cost questions: [Frequently Asked Questions](/en/kaynaklar/sss/)
- To audit the license chain and personal data before writing the card: [License, Personal Data and Model Card](/en/kullanim/lisans-ve-model-karti/)
