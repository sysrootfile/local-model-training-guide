---
title: "Step by Step: Train Your Own Image LoRA"
description: "How to train your own character or style LoRA with 15-20 images, step by step, from data collection to testing."
dogrulama: 2026-11-20
---

On this page we'll work a real scenario start to finish: we have a handful of images, and at the end we'll have a single MB-sized file that can generate them. Our example scenario: **"what if I taught my own drawing style?"** or **"what if I could generate my cat in any scene I wanted?"** Both paths are the same.

Prerequisites: roughly knowing what diffusion does ([Diffusion Fundamentals](/en/gorsel/diffusion-temelleri/)) and a computer or a cloud account. A Windows machine with 6-8 GB of VRAM suffices for SD 1.5/SDXL LoRA; if you have no GPU at all, there's the free cloud.

## Step 1 — Collecting the data

A good LoRA's secret is in the data before the model. The rules:

- **Count:** 10-30 images suffice. 15-20 is the sweet spot to start.
- **Resolution:** the short edge at least 512 pixels (aim for 1024 if you'll train SDXL). Pick high-resolution, sharp images; the training scripts crop or shrink if needed.
- **Quality:** don't use blurry, motion-blurred, watermarked, over-compressed images. The model learns from a bad example too.
- **Variety:** angles, lighting, backgrounds and poses should vary. If you teach the same couch every time, the model never leaves the couch.
- **Consistency:** despite the variety, the thing you want to teach (a face, a style, an object) should be clearly visible in every image. Learning the face of a character wearing sunglasses in half the images gets harder.
- **No repeats:** 20 nearly identical frames shot side by side are really 1 image. Weed out the similar frames.

:::danger[Copyright and ethics]
Train your LoRA only with images you shot/drew yourself, with a suitable license, or with explicit consent. Imitating a living artist's style and reproducing their works raises legal and ethical problems even if it's "just training". If you train a character, turning a person's own images into a LoRA depends on their consent.
:::

| | A character LoRA | A style LoRA |
|---|---|---|
| How many images? | 15-30, the subject from every angle | 15-30, the style on different subjects |
| What's critical | Face/subject clarity and consistency | The brush/texture/color palette's consistency |
| Background | Should vary (so it isn't memorized) | The subject should vary (so the style is learned) |

## Step 2 — Labeling (captions)

Captioning is writing a text describing each image. The logic: the model counts **everything in the image the caption doesn't cover** as "general knowledge belonging to the base model"; and separates the thing you caption as the special information it must learn.

- **When teaching a style:** captioning matters a lot. Descriptions like "watercolor, pastel, a misty mountain scene" separate style from content; this way you can apply the style to any scene.
- **When teaching a character:** there are two approaches. (1) **Only a trigger word:** put a rare word at the head of each caption, leave the rest empty. The model memorizes the character bound to that word; simple but low flexibility. (2) **Trigger + a short description:** like "ohwx my cat, sleeping on the couch, daytime". Gives more flexible results, asks for a bit more labor.

:::note[Turkish or English?]
The popular SD models (SD 1.5, SDXL and the other CLIP-based ones) were trained mostly on **English** text. Writing the captions in English and using English prompts at generation markedly raises the model's hit rate in understanding the text. Training with Turkish captions works too, but the results are generally more erratic.
:::

Three example captions (English, trigger included):

```text title="example captions"
ohwx my cat, sitting in the park, sunset light, photo
ohwx my cat, on the kitchen counter, morning, natural light, close-up
sksstyle, a watercolor landscape, misty mountains and a lake, pastel colors
```

The captions are written into a `.txt` file **with the same name as** the image; kohya expects this folder layout:

```text title="the folder structure"
data_folder/
├── mycat_01.jpg
├── mycat_01.txt     →  "ohwx my cat, sleeping on the couch, daytime"
├── mycat_02.jpg
├── mycat_02.txt     →  "ohwx my cat, in the park, sunset"
└── ...
```

If you want to use multiple concept folders, the number at the head of the subfolder's name in kohya means "repeats"; for example the `5_mycharacter/` folder is read 5 times per round. If you're starting with a single set, you needn't think about this detail for now.

**The trigger word** technique: short strings rarely seen in the model's training data are chosen, like "ohwx", "sks". This word gets bound to the character/style in your captions; at generation, writing it brings in what you taught. If you pick real words (like "cat"), the model gets confused — a rare, meaningless string is safest.

## Step 3 — Tool choice

| Option | Setup | Pros | Cons | When? |
|---|---|---|---|---|
| **kohya_ss (local)** | [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) — `git clone` + `setup.bat` | Free, unlimited use, your data stays on your computer | The setup takes effort the first time; as much as your VRAM limit | If you'll train regularly |
| **Colab** | A ready kohya notebook | A T4 GPU, no setup, the free tier | Session times limited, the data must be uploaded | Learning and one-off trials |
| **Kaggle** | A notebook environment | A weekly free GPU quota, dataset hosting | The interface experience differs from Colab's | When you hit the Colab limit |

The simple decision: train your first LoRA **on Colab** (zero risk, fast to learn); move to **local kohya_ss** when you go to regular production. For the Windows local setup steps: [Local Setup](/en/donanim/yerel-kurulum/); if you have no GPU: [Cloud Options](/en/donanim/bulut-secenekleri/).

## Step 4 — The training parameters

You'll see dozens of fields in the kohya_ss interface; for the first training these matter (with typical values for SD 1.5/SDXL):

| Field | Typical value | What does it do? |
|---|---|---|
| `max_train_steps` | 1500-3000 | The total training steps. A rough guide: ~100 steps per image. |
| `learning_rate` | ~1e-4 | The learning speed. Too high = broken results, too low = wasted steps. |
| `network_dim` (rank) | 16-32 | The LoRA's capacity. 16 for a simple character, 32 for a complex style. |
| `network_alpha` | dim/2 (8-16) | The training's "scale"; usually half the dim is a good start. |
| `train_batch_size` | 1-2 | The number of images processed at once. If VRAM is tight, stay at 1. |
| `mixed_precision` | fp16 (SD 1.5), bf16 (SDXL/Flux) | Memory saving + speed; the quality loss is negligible. |
| `save_every_n_steps` | 250-500 | Intermediate saves. Don't tie the final decision to a single file; test the intermediates. |
| Resolution | 512 (SD 1.5), 1024 (SDXL) | The training resolution; the bucketing feature manages different aspect ratios. |

The kohya interface turns these fields into a command at the bottom. For those who want to see what runs behind the scenes, its equivalent (sd-scripts):

```bash title="lora_training.sh (the sd-scripts equivalent, summarized)"
accelerate launch --num_cpu_threads_per_process 4 train_network.py \
  --pretrained_model_name_or_path=model.safetensors \
  --train_data_dir=data \
  --output_dir=output \
  --network_module=networks.lora \
  --network_dim=16 --network_alpha=8 \
  --learning_rate=1e-4 \
  --train_batch_size=1 \
  --max_train_steps=2000 \
  --save_every_n_steps=500 \
  --mixed_precision=fp16 \
  --resolution=512 \
  --caption_extension=.txt
```

:::caution[How do you tell overtraining (overfit)?]
Generate the same test prompt with the intermediate files saved every 250-500 steps and look at three signals: (1) if the result has started being nearly a copy of the training images, (2) if the background doesn't change whatever you write in the prompt, (3) if the character/style forcibly appears in every generation even without the trigger word — the model has moved to memorization. The fix: using an intermediate file from an earlier step, lowering the step count or the learning rate. Generally an "undertrained" LoRA is easier to rescue than an overtrained one.
:::

## Step 5 — Testing and using

When training finishes, you'll have a single file with the `*.safetensors` extension, typically between tens of MB (SD 1.5) and hundreds of MB (SDXL, Flux). This file is a patch applied **on top of** the base model; it doesn't run alone.

**In the AUTOMATIC1111 WebUI:**

1. Copy the file into the `models/Lora/` folder.
2. Add it to the prompt with this syntax: `<lora:file_name:0.8>`

**In ComfyUI:** add the `LoraLoader` node between the model and the sampler, and pick the file and the strength.

```text title="an example test prompt"
<lora:mycat_v1:0.8> ohwx my cat, walking along the shore, golden hour, photo
```

When testing, try these:

- **A strength (weight) sweep:** compare the values 0.6 / 0.8 / 1.0. The 0.6-1.0 range is the sweet spot for most LoRAs; above 1.0 is usually unnecessary and makes the image "gooey".
- **The memorization test:** ask for scenes not in training (a different city, a different season). If the character/style still comes, the model has generalized.
- **The triggerless test:** seeing a slight effect even without the trigger word is normal; if it comes fully triggerless, it may be overtrained.

## Comparison with the LLM LoRA

:::tip[The same idea, different materials]
LoRA/QLoRA [on the LLM side](/en/llm/lora-qlora/) and image LoRA are exactly the same logic: the base model's weights **freeze**, and the small low-rank matrices (A and B) attached to it are trained. The differences are only in the data and the tools.
:::

| | LLM LoRA / QLoRA | Image LoRA |
|---|---|---|
| Data type | Text (instruction-answer pairs) | Image + caption |
| Typical data amount | Hundreds-thousands of examples | 10-30 images |
| Tools | peft / trl / Unsloth | kohya_ss (sd-scripts), diffusers |
| Typical duration | Hours (a 7B model, one GPU) | Minutes-hours (by model) |
| Output | An adapter file (tens-hundreds of MB) | A `safetensors` LoRA (tens-hundreds of MB) |
| Evaluation | Loss, benchmarks, chat output | Inspecting the generated images by eye |

## Cost and time expectations

- **The Colab free T4 + an SD 1.5 LoRA:** about 30-60 minutes. Ideal for a first attempt.
- **An SDXL LoRA:** noticeably longer on the T4; a few hours on a local 12 GB card.
- **A Flux LoRA:** about 1-2 hours in the cloud (with a strong GPU); asks for 16-24 GB VRAM locally. These values are rough; they change considerably by data and step count.
- A privacy note: when training in the cloud, you upload your images to the platform; for sensitive images, consider local training or the rented-GPU routes on the [cloud options](/en/donanim/bulut-secenekleri/) page.

## The checklist

Before starting training:

- [ ] 10-30 images ready; all sharp, the subject consistent, repeated frames weeded out
- [ ] Every image's caption in a same-named `.txt` file
- [ ] A trigger word chosen and added to the captions' heads
- [ ] The base model file (SD 1.5 / SDXL `safetensors`) downloaded
- [ ] `save_every_n_steps` set to 250-500

After training:

- [ ] The intermediate checkpoints were compared with the same test prompt and the same seed
- [ ] The best checkpoint passed the memorization test (scenes not in training were requested)
- [ ] The strength (weight) was swept between 0.6-1.0
- [ ] The file was backed up; if it'll be shared, a model card was written

## Summary and continuation

- Collect 10-30 consistent, quality images; caption them in English if needed.
- Train with kohya_ss (local) or Colab (cloud); start the step count and learning rate with the guide values.
- Test the intermediate saves, catch the overfit, pick the best checkpoint.
- Plug the file into the webui/ComfyUI, set the strength between 0.6-1.0.

To refresh the concepts: [Diffusion Models](/en/gorsel/diffusion-temelleri/). When your LoRA is ready, consider opening it to the community: [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/).
