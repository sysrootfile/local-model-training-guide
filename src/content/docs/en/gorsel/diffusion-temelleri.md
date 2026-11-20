---
title: "Diffusion Models: How Does Image Generation Work?"
description: "The logic of diffusion models' image generation; their components like the VAE, UNet and text encoder, and training types like LoRA and DreamBooth, explained intuitively."
dogrulama: 2026-11-20
---

You type "a cat in a red sweater, watercolor" into a model and a few seconds later an image that really looks like that arrives. But what's happening behind the curtain? This page explains how diffusion models work through intuition rather than equations.

This guide's main focus is LLMs (large language models); but the image side follows a familiar flow too: data → training → evaluation. The only difference is that "data" here is image + caption.

## The core idea: learning to un-noise

The easiest way to understand a diffusion model is two analogies:

- **Wiping the foggy glass:** there's a fogged glass in front of you and a photo behind it. Each wipe makes the glass a little clearer; eventually the photo appears. The diffusion model learns exactly these "wiping motions".
- **The sand sculpture:** a sculptor adds nothing to the sand; they take the excess away. The model likewise starts from pure noise and at every step discards a bit of the "excess" (the noise).

During training the job is actually done in reverse: the model is shown the pair "clean image → a slightly noisier image" millions of times and learns to recognize noise. Then, at generation, this knowledge is used in the opposite direction:

```text title="the diffusion idea"
IN TRAINING (the easy job — the model sees this thousands of times):
clean image → +some noise → +some more → ... → pure noise
               (step 1)         (step 2)       (the last step)

AT GENERATION (the hard job — the model uses what it learned in training):
pure noise → predict and subtract the noise → ... → clean image
```

:::note
The "noise" here is the random corruption added to the image at the pixel level. The model's real job in one sentence: **"What exactly is the noise in this image? Tell me, and I'll subtract it."**
:::

## The text-to-image flow

When you type "a cat in a red sweater", the image's formation passes through this chain:

```text
"a cat in a red sweater, watercolor"   (text / prompt)
        │
        ▼
The text encoder (mostly CLIP)
        │  turns the text into the numeric vectors the model understands
        ▼
The denoising model (UNet or DiT — denoising)
        │  starts from pure noise; at every step predicts and subtracts
        │  "what noise is there now?"; the text vector guides it at every step
        │  typically after 20-50 small steps a "blurry but meaningful"
        │  intermediate representation (a latent) emerges
        ▼
The VAE decoder
        │  decodes the small latent representation into a full-size pixel image
        ▼
The image
```

The key idea here is the **latent space**: the model doesn't work directly on millions of pixels. The VAE reduces the image to a much smaller compressed representation; the diffusion process happens on that small "canvas". This improves both speed and memory use several-fold. The name "latent diffusion" comes from here.

## The main components

| Component | What's it for? |
|---|---|
| **VAE** | Turns the image into a compressed latent representation (the encoder) and at the end of generation decodes it back to pixels (the decoder). It lets the model work with a small representation instead of pixels; this way generation is done much faster with much less memory. |
| **UNet / DiT** (the noise predictor) | This is diffusion's heart and the part actually updated during training. It answers "what noise is in this image?" at every step; and with that information it cleans a new image step by step. |
| **The text encoder** | Turns your prompt into numeric vectors that mean something to the model; most Stable Diffusion models use a model from the CLIP family. It's the interpreter between the words you write and the image to be generated. |
| **The scheduler** | Manages the denoising process's step plan: how many steps, how much noise removed at each step? Different schedulers change the speed-quality balance. |

For the background of how the text encoder works, you can look at [Transformers](/en/temeller/transformer/) and [Tokenization](/en/temeller/tokenizasyon/).

## A typical generation round: 20-30 steps behind the curtain

When generation starts with the "cat in a red sweater" prompt, these happen in order:

1. The text encoder turns the prompt into a vector once.
2. A random starting latent is created from pure noise.
3. The scheduler orders the steps. At every step the UNet/DiT predicts "what noise is in the current image?"; in making that prediction it looks both at the text vector and at what noise level it's at that moment.
4. The predicted noise is subtracted from the latent; the image sharpens a little at every step and "the cat in the red sweater" begins to emerge.
5. After the last step, the VAE decoder turns the latent into a pixel image.

The step count is a simple speed-quality knob: 20 steps are more than enough for most jobs; 40-50 give finer detail but every extra step adds to the time.

## What is the guidance scale (CFG)?

It's the parameter adjusting the prompt's strength over the image; around 7-8 is a reasonable start in most interfaces. At low values the model adheres loosely to the prompt (creative but scattered, "prompt-ignoring" results), and at very high values it clings to the prompt too much (colors saturate, compositions start showing odd distortions). When comparing different checkpoints of a LoRA, keeping CFG and the seed fixed ensures you that the difference you see really comes from the LoRA.

## Training types: which one teaches what?

When you want to teach a model a new character, style or object, there are four basic paths:

| Method | What does it teach? | How many images? | Note |
|---|---|---|---|
| **LoRA** | Teaches a character, style or object by attaching a small "extension" to the base model. | 10-50 | The most practical method; the output is a single MB-sized file, the base model never changes. |
| **DreamBooth** | Teaches a specific subject at the "this is my cat" level. | 5-20 | Heavier than LoRA; touches the UNet more broadly and asks for more VRAM. |
| **Textual Inversion** | Teaches a new concept as an embedding of a few thousand words. | 3-10 | The lightest method; the file is tiny but its effect and flexibility are limited. |
| **Full fine-tune** | Updates the entirety of the base model's weights and produces a new model. | Hundreds to thousands | Rarely preferred; needs big hardware and big data. For most needs LoRA suffices. |

:::tip
If you're undecided, almost always the right start is **LoRA**. The experimentation cost is low, the output is a single file, and it can easily be blended at different strengths (weights) when needed. For its step-by-step application, see the [Train Your Own Image LoRA](/en/gorsel/lora-egitimi/) page.
:::

## Hardware: how much VRAM is needed?

| What are you training? | Local minimum VRAM | Note |
|---|---|---|
| **SD 1.5 LoRA** | 6 GB+ | With batch 1, 512 resolution and mixed precision it trains comfortably on 6-8 GB cards. |
| **SDXL LoRA** | 8-12 GB+ | Wider because of the 1024 resolution; 12 GB and above comfortable, the 8 GB class tryable with optimizations. |
| **Flux LoRA** | 16-24 GB (or cloud) | Flux is a far bigger model than the SD family; most users train it in the cloud. |
| **The alternative to all of them** | Cloud | SD 1.5 LoRA in particular trains without trouble on the free T4 in Colab or Kaggle. |

:::caution[If VRAM is insufficient]
First clarify the numeric expectation: [VRAM math](/en/donanim/vram-hesabi/). If your card isn't enough, the cloud may be the full solution: [Cloud options](/en/donanim/bulut-secenekleri/).
:::

The secret of training on low VRAM is three settings: keeping **batch size 1**, **lowering the resolution** (even on SDXL you can start from 512) and using **mixed precision** (fp16/bf16).

## Commonly confused concepts

| Confused | The difference |
|---|---|
| Diffusion vs GAN | In a GAN, the generator and discriminator, two networks, try to outdo each other; in diffusion a single network is trained toward a far more stable target like "noise prediction". In image generation, diffusion has been dominant since the 2020s. |
| Base model vs LoRA | The base model (e.g. SDXL) is a gigabyte-sized general-purpose image generator; a LoRA is a tens-to-hundreds-of-MB patch attached on top of it and doesn't run alone. |
| Latent vs pixel | The generation loop mostly spins in latent space; converting to pixels is the VAE's job at the very end. That's why "latent resolution" and "output resolution" are different things. |

## The ecosystem: which tool does what?

- **diffusers** ([huggingface.co/docs/diffusers](https://huggingface.co/docs/diffusers)) — Hugging Face's Python library. For those who want to control the code, write their own training scripts or build a production line; it supports all of SD, SDXL and Flux.
- **kohya_ss / sd-scripts** ([github.com/kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts), interface: [github.com/bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss)) — the de facto standard of LoRA training. It offers a Gradio-based interface on Windows; behind the fields you click, sd-scripts commands run.
- **ComfyUI** ([github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)) — a node-based interface. It lets you build complex generation workflows as a visual diagram and make them reproducible.
- **The AUTOMATIC1111 WebUI** ([github.com/AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)) — the classic tabbed interface. Still one of the most common starting points for quick experiments and the rich extension ecosystem.

A simple selection guide: **training** → kohya_ss, **code/pipeline** → diffusers, **production workflow** → ComfyUI, **classic experimentation** → A1111.

## Example model families (as of 2026)

| Family | Standout versions | Short note |
|---|---|---|
| Stable Diffusion | SD 1.5, SDXL, SD3 | Still the most widespread ecosystem in 2026; SD 1.5 is the lightest model with the most LoRA accumulation, and SDXL is accepted as the standard at 1024 resolution. |
| Flux | Black Forest Labs | As of 2026 one of the most popular open image model families; quality high, hardware need also high. |

## This guide's relation to the LLM side

:::tip[If you know LLMs, the logic here will feel familiar]
The same pipeline: **data → training → evaluation**. The same concepts: freezing the base model and training a small layer ([LoRA/QLoRA in LLMs](/en/llm/lora-qlora/), LoRA in images). Only the materials differ.
:::

| | LLM | Image diffusion |
|---|---|---|
| Training data | Text (instruction + answer) | Image + caption |
| What does the base model learn? | Predicting the next token | Predicting the noise in the image |
| The small adaptation method | LoRA / QLoRA ([details](/en/llm/lora-qlora/)) | LoRA |
| Evaluation | Loss, benchmarks, chatting by eye | Sample image generation, inspection by eye |

There's similarity on the from-scratch training side too: what [pretraining](/en/llm/pretraining/) is in LLMs, diffusion pretraining with big data is in images; small adaptations are made on top of it.

## What's next?

You now hold the necessary mental model: a network that learned to un-noise, building the image step by step with the text encoder's accompaniment. And the path you'll use most in practice is clear: training a LoRA with a small dataset.

Continue: [Step by Step: Train Your Own Image LoRA](/en/gorsel/lora-egitimi/)
