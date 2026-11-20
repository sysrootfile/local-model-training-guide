---
title: "Frequently Asked Questions"
description: "The 15 questions most asked at the beginner level: hardware, cost, data amount, training in Turkish, licenses and the learning order."
dogrulama: 2026-11-20
---

This page gathers the questions newcomers to machine learning ask most, in one place. The answers are kept short; with the links at each answer's end you can move to the relevant page and go deeper.

## 1. I have no GPU, can I still train a model?

Yes, but at small scale. With the LoRA/QLoRA methods, 1-4B-parameter models can be trained on CPU too; however training is orders of magnitude slower compared to a GPU and you need to keep the data small. On CPU the practical limit is usually models around 1B. For serious experiments the free cloud GPUs (the next question) are far more sensible. For hardware planning see [VRAM Math](/en/donanim/vram-hesabi/) and for the methods [LoRA and QLoRA](/en/llm/lora-qlora/).

## 2. Where can I train for free?

Google Colab's free tier offers a T4-class GPU, and Kaggle offers a weekly limited GPU quota for free; both are more than enough for small QLoRA experiments. Shared resources like ZeroGPU on Hugging Face Spaces can also be considered for light experiments. Free GPUs can make you queue at peak hours and the session time is limited; for long trainings a rented GPU is more reliable. The detailed comparison: [Cloud Options](/en/donanim/bulut-secenekleri/).

## 3. How long does a small training take?

On a T4-like GPU, trainings with QLoRA on 1,000-10,000 examples typically take from half an hour to a few hours. Three things determine the duration: the example count, the model size and the sequence length. The most reliable method is running a trial with 100 examples and scaling the total time. For time budget planning, read the [Step-by-Step Training](/en/llm/adim-adim-egitim/) and [Hyperparameters](/en/llm/hiperparametreler/) pages.

## 4. How much data do I need?

Quality comes before quantity: the LIMA experiment showed surprisingly good results with 1,000 carefully chosen examples. For most personal projects 500-5,000 clean and consistent examples suffice; a million bad examples is worse than a thousand good ones. For a narrow task (e.g. writing email drafts) even a few hundred examples can do the job. For data generation and cleaning, see the [Create Your Own Dataset](/en/veri/kendi-verini-olustur/) and [Data Cleaning](/en/veri/veri-temizleme/) pages.

## 5. Which model should I start with?

For Turkish, Qwen3 (4B/8B), Gemma 3 (4B/12B) and Llama 3.2 (1B/3B) are good starts; all were trained with multilingual data and their Turkish abilities are reasonable. At 8-16 GB VRAM, 4B models train comfortably with QLoRA; on a very small card start with 1B. When choosing, also check the license's fit to your intended use (there are Turkish model collections in the [Useful Links](/en/kaynaklar/faydali-linkler/) list). For the tool and model ecosystem, the [Tools](/en/llm/araclar/) page guides you.

## 6. Full fine-tuning or LoRA?

For almost everyone the answer is LoRA/QLoRA: full fine-tuning updates the model's every parameter and typically requires A100-class GPUs. With LoRA you do the same job with far more modest hardware; the quality gap is small in most tasks. Full training makes sense only if you have a big dataset and a big GPU budget. For the comparison, see [LoRA and QLoRA](/en/llm/lora-qlora/) and [SFT (Supervised Fine-Tuning)](/en/llm/sft/).

## 7. My trained model answers badly, why?

The first suspect is always **the data**: inconsistent, noisy or too few examples is the most common problem. The second suspect is chat template mismatch; if the template used in training isn't the same as the one used at inference, the model behaves "bewildered". Overtraining also locks the model to the training data; the validation loss starting to rise on the loss curve is the typical sign. For systematic diagnosis follow the [Troubleshooting](/en/llm/sorun-giderme/) page and for metric reading [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).

## 8. Is anything special needed to train in Turkish?

The one big difference is **in tokenization**: Turkish spends markedly more tokens than English for the same content (often 1.5-2x). This fills the context window quickly and inflates the training/cost math; we explain why on the [Tokenization](/en/temeller/tokenizasyon/) page. Adding extra Turkish tokens (vocabulary extension) is an advanced solution; not needed to start. Quality Turkish datasets and multilingual models suffice in most cases: [Where to Find Data](/en/veri/veri-nereden-bulunur/).

## 9. I want to train a model from scratch, is that possible?

Technically possible, let's be realistic about budget: modern LLM pretraining requires millions of dollars and thousands of GPU hours. If the goal is learning, the answer is different: training 10-100M-parameter small models from scratch with small datasets is a great experience and genuinely teaches how language models work. If the "from scratch" goal is understanding rather than a production model, start from the [Pretraining](/en/llm/pretraining/) and [Classic ML Fundamentals](/en/klasik-ml/temeller/) pages.

## 10. Is DPO/RLHF a must?

No. SFT (supervised fine-tuning on instruction data) suffices for most projects; DPO is a second improvement stage. DPO makes sense when you can collect preference data in the form "this answer is good, that one bad"; RLHF is a heavier pipeline and definitely not needed to start. To see the ordering, see the [SFT](/en/llm/sft/) and [DPO and RLHF](/en/llm/dpo-rlhf/) pages.

## 11. What will the training cost?

On local hardware the cost is electricity and time; zero on the free cloud tiers. On rented GPUs a T4-class is on the order of roughly half a dollar an hour, an A100-class a few dollars, and training an 8B QLoRA typically takes a few GPU hours. So your first experiments are mostly possible on a "coffee" budget. For current prices and options, see the [Cloud Options](/en/donanim/bulut-secenekleri/) page.

## 12. How do I test the model I trained?

Prepare a fixed test set of at least 20-30 questions and score the answers by eye; if possible, also have a few people who don't know you test it. Loss and validation metrics are indicative but not sufficient alone; the real measure is human evaluation. To compare with Turkish evaluation sets and know the standard benchmarks, read the [Benchmarks and Evaluation](/en/degerlendirme/benchmarklar/) and [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) pages.

## 13. Will I have trouble on Windows?

The general flow works on Windows: Python, PyTorch/CUDA, Unsloth and Ollama support Windows. The problems usually come from two places: packages compiled only for Linux (e.g. flash-attention) and serving tools requiring Linux (e.g. vLLM). In those cases WSL2 is the practical fix; you don't need it to start. For setup steps and the commonly hit driver/CUDA problems, see the [Local Setup](/en/donanim/yerel-kurulum/) page.

## 14. In what order should I learn?

The recommended order: concepts → the transformer's logic → tokenization → data preparation → the first fine-tune with LoRA/QLoRA → evaluation → quantization and sharing. The [Roadmap](/en/baslangic/yol-haritasi/) page gives this order split into weeks, with links. The [Concepts](/en/baslangic/kavramlar/) page serves as the basic glossary; on terms whose meaning you forgot, the [Glossary](/en/kaynaklar/sozluk/) is your quick reference.

## 15. Can I use the model I trained commercially?

Largely it depends on the base model's license: derivatives you produce with Apache-2.0 and MIT licensed models are open to commercial use. The Llama and Gemma models also permit commercial use but with conditions (naming, a user count threshold, use policies). Your derivative model's license can't be freer than the base model's; your dataset's license also matters separately. For the detailed table, see the license section on the [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/) page.

One warning: **a license isn't a model family's name, it's the file in the repo.** We have a measured example — while most sizes of the Qwen family are Apache-2.0, the `Qwen2.5-3B-Instruct` size is under the "Qwen Research License" with commercial use explicitly closed; and that size is the most chosen one, since it runs on CPU. The audit of the license fields in your local packages and the personal-data scan: [License, Personal Data and Model Card](/en/kullanim/lisans-ve-model-karti/).

---

If you couldn't find your question's answer, for community resources and Turkish data/model repos see the [Useful Links and Resources](/en/kaynaklar/faydali-linkler/) page, and for the basic concepts' definitions the [Glossary](/en/kaynaklar/sozluk/) page.
