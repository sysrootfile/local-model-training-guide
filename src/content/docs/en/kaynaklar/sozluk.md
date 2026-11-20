---
title: "Glossary: Turkish-English Terms"
description: "The Turkish equivalents, pronunciations and one-sentence explanations of machine learning's and the LLM world's most used terms."
dogrulama: 2026-11-20
---

A quick reference for the terms you'll constantly meet in machine learning texts. The original guide's glossary pairs each English term with its Turkish equivalent — useful when reading Turkish pages, papers or datasets. Here the terms are sorted alphabetically by their English names; the first column is the term itself, the second its Turkish equivalent or common pronunciation, the third a one-sentence explanation.

:::tip
This page is a glossary, not a lesson. The page that explains the concepts with their stories is [Core Concepts](/en/baslangic/kavramlar/); the terms here meet you there with their context.
:::

| Term (English) | Turkish equivalent / pronunciation | Explanation |
|---|---|---|
| Activation | aktivasyon | The function transforming a neural network layer's output (e.g. ReLU); it adds non-linearity to the network. |
| Abstention | kaçınma | The model choosing not to answer (or the "I don't know" option); the desired behavior for questions below the confidence threshold. Its measurement: [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/). |
| AdamW | "adam-dablyu" | The most used optimizer; it adaptively scales the gradients and applies weight decay. |
| Adapter | adaptör | A small module added to the base model later, containing few trainable parameters (the A and B matrices in LoRA). |
| Attention | "dikkat" (attention) | The transformer component computing which other tokens in the sequence each token "looks at" and how much. |
| AWQ | "ey-dablyu-kyu" | A hardware-friendly 4-bit quantization method for GPUs; common in serving engines like vLLM. |
| Backpropagation | geri yayılım (backpropagation) | The fundamental algorithm of neural network learning, computing backwards how much the loss depends on each weight. |
| Batch size | yığın boyutu (batch size) | The number of examples the model processes together in a single step; it directly affects VRAM consumption. |
| Benchmark | kıyas testi (benchmark) | Standard tasks and test sets enabling comparing models under the same conditions. |
| bf16 / fp16 | "b-f-16", "f-p-16" | 16-bit number formats: fp16 more precise, bf16 wider-ranged; bf16 is preferred for training on modern GPUs. |
| bitsandbytes | "bits end bayts" | The library loading models in 8/4-bit; it provides QLoRA's NF4 support. |
| BPE | "bi-pi-i" | Byte-Pair Encoding: the tokenization algorithm splitting text into pieces by merging the most frequent character pairs. |
| Calibration | kalibrasyon | The model's reported probability matching the accuracy rate: "are 90% of the questions I said 0.9 about correct?" |
| Catastrophic forgetting | felaket unutma | The model largely losing its previous general abilities after fine-tuning. |
| Chain-of-thought (CoT) | düşünce zinciri (chain-of-thought) | The prompting technique encouraging the model to write intermediate steps before reaching the answer; it raises accuracy on reasoning tasks. |
| Chat template | sohbet şablonu | The template turning messages into the special control-tokened text format the model expects. |
| Checkpoint | kontrol noktası (checkpoint) | The weight snapshot saved periodically during training. |
| Concurrency | eşzamanlılık | The number of requests arriving at the server at once. The client side (how many requests you release at once) and the server side (`OLLAMA_NUM_PARALLEL`) are separate things; with the server at its default setting, growing client concurrency on CPU doesn't split the latency — every user waits for the entirety of those before them. When slots open, the queue vanishes but the work is shared: a single request's decode speed drops. If more requests arrive than slots, the two mix — the speed drops by the slot count, and the overflow requests queue. Its measurement: [Concurrency](/en/kullanim/eszamanlilik/). |
| Confidence, verbalized | sözlü güven | The statement the model gives when asked numerically how sure it is out of how much; it produces hard-to-parse outputs. Its measurement: [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/). |
| Context window | bağlam penceresi | The maximum number of tokens the model can process at once. |
| Cosine schedule | kosinüs programı | The schedule reducing the learning rate along a cosine curve over training. |
| Cross-entropy | çapraz entropi | The fundamental language-modeling loss penalizing the probability the model gives the correct token. |
| Data collator | veri toplayıcı | The helper component turning different-length examples into regular training batches. |
| Dataset | veri kümesi | The collection of examples used for training and validation. |
| Diffusion model | difüzyon modeli | The model family used in image and audio generation, learning to produce clean data from noise. |
| Distillation | damıtma (distillation) | Carrying a large "teacher" model's behavior into a small "student" model. |
| DPO | "di-pi-o" | Direct Preference Optimization: the method aligning the model with "good answer / bad answer" preference pairs. |
| Dropout | "dırap-aut" | The technique reducing memorization by randomly disabling a portion of the neurons during training. |
| ECE (Expected Calibration Error) | beklenen kalibrasyon hatası | The single number binning the model's given probabilities and weighting the gap, in each bin, between the number it reported and the real hit rate. |
| Embedding | gömme (embedding) | Turning text into meaning-carrying numeric vectors; the foundation of search and RAG systems. |
| Epoch | tur (epoch) | One full pass over the training data, start to finish. |
| Evaluation | değerlendirme | Measuring the model's quality with test sets, metrics and human review. |
| Few-shot | az örnekli (few-shot) | Describing the task to the model by showing a few examples inside the prompt. |
| Fine-tuning | ince ayar (fine-tuning) | Adapting a pretrained model to a new task with your own data. |
| Flash Attention | "flaş ıtenşın" | The acceleration kernel making the attention computation efficient in GPU memory. |
| FP8 | "ef-pi-sekiz" | An 8-bit floating-point number format; it speeds training and inference on new-generation GPUs. |
| GGUF | "ci-ci-yu-ef" | The llama.cpp family's quantized model file format; the standard of Ollama and LM Studio. |
| GPTQ | "ci-pi-ti-kyu" | An older but widespread quantization method for 4-bit inference on GPU. |
| Gradient | gradyan (eğim) | The derivative saying in which direction each weight should be updated to reduce the loss. |
| Gradient accumulation | gradyan biriktirme | Creating a big-batch effect by accumulating small batches' gradients. |
| Gradient checkpointing | gradyan kontrol noktalaması | Saving VRAM by recomputing intermediate activations when needed instead of storing them. |
| GRPO | "ci-ar-pi-o" | Group Relative Policy Optimization: the reinforcement learning method comparing answer groups with each other. |
| Hallucination | halüsinasyon | The model producing false or fabricated information with a confident tone on a subject it doesn't know. |
| Hard negative | zor negatif | The wrong match the model believes is right; in embedding training the most instructive but most dangerous negative type, because it's the model itself that picks the miner's wrong answer as validating. |
| Hyperparameter | hiperparametre | The settings training itself doesn't learn: the learning rate, batch size, LoRA rank etc. |
| In-batch negatives | batch içi negatifler | The other examples in the same batch counting as free negatives for each row; that's `MultipleNegativesRankingLoss`'s logic. |
| Inference | çıkarım (inference) | The trained model producing an answer for a new input; the "usage" stage. |
| Instruction tuning | talimat ayarı | Fine-tuning the model with examples in the "request → response" form. |
| JSONL | "cey-son-el" | The file format with an independent JSON object on every line; common in datasets. |
| KL divergence | KL ayrışması (KL divergence) | The metric measuring how different two probability distributions are; used in alignment training to keep the model from straying too far from the base. |
| KV cache | "kı-vi" önbellek | The memory area gaining speed by storing prior tokens' attention computations during generation. |
| Learning rate | öğrenme oranı (learning rate) | The most critical hyperparameter, determining how much the weights change at each update. |
| LLM | büyük dil modeli (LLM) | A language model with hundreds of millions to trillions of parameters, trained on huge texts. |
| Logprob | log olasılığı (logprob) | A token's natural logarithmic probability; as it approaches zero, certainty rises. Requested in Ollama with `logprobs: true`, the `top_logprobs` ceiling is 20. |
| LoRA | "lora" | Low-Rank Adaptation: the efficient fine-tuning method freezing the base model and training small low-rank matrices. |
| LoRA alpha (alpha) | "lora alfa" | The scale coefficient adjusting the adapter's strength over the base model; in practice often twice the rank is chosen. |
| Loss | kayıp | The number measuring how far the model's prediction is from the correct answer; in training it's tried to be lowered. |
| Merge | birleştirme (merge) | Permanently fusing the LoRA adapter weights into the base model. |
| Mixture of Experts | uzmanlar karışımı (MoE) | The efficient architecture activating only a small portion of the expert sub-networks per token. |
| Model card | model kartı | The page published with the model, containing its introduction, training and license information. |
| Multimodal | çok modlu (multimodal) | A model able to process multiple data types together, like text, image and audio. |
| Multiple Negatives Ranking Loss (MNRL) | çoklu negatif sıralama kaybı | The most common loss in embedding training: it teaches each row to separate its right match from the others in the batch; you don't label the negatives. |
| NF4 | "en-ef-dört" | The 4-bit NormalFloat number format QLoRA uses. |
| Overfitting | aşırı öğrenme, ezberleme | The model memorizing the training data and getting worse on new data. |
| Packing | paketleme | The technique merging short examples into a single sequence to reduce padding waste. |
| P(True) | doğru şıkkın olasılığı | The confidence measure found by dividing the mass of the tokens giving the correct answer by the mass of all the answer candidates. |
| Padding | doldurma (padding) | The filler tokens added to equalize sequences of different lengths; wasteful if unnecessary. |
| Parameter | parametre | Each of the numeric weights the model learned from data; the model's size is measured with this number. |
| PEFT | "peft" | Parameter-Efficient Fine-Tuning: the family of methods training a small portion of the parameters (LoRA etc.). |
| Perplexity | şaşkınlık (perplexity) | The model's degree of "surprise" at a text; a lower value means a better language model. |
| Pipeline | akış hattı (pipeline) | The end-to-end chain of data collection, cleaning, training and evaluation steps. |
| Position bias | konum yanlılığı | The model looking at the option's letter or place rather than its content; if the choices pile onto a single letter, the probability threshold stops being a discriminator. |
| Precision | hassasiyet | How many bits the numbers are held in: fp32, fp16, bf16, int8, int4 etc. |
| Pretraining | ön eğitim (pretraining) | Training the model from scratch with huge texts on the "predict the next token" task. |
| Prompt | istem | The instruction or text given to the model. |
| Prompt engineering | istem mühendisliği | Carefully designing the prompt to steer model behavior without training. |
| QLoRA | "kyu-lora" | The method loading the base model in 4-bit (NF4) and training LoRA on top; the key to training a big model on a single consumer GPU. |
| Quantization | nicemleme (quantization) | Shrinking and speeding the model by representing the weights in fewer bits. |
| Rank (r) | rütbe, derece | The size of the low-rank matrices LoRA adds; as it grows, capacity rises and training gets heavier. |
| RAG | "rag" | Retrieval-Augmented Generation: adding information retrieved from external documents into the model's prompt. |
| Reinforcement Learning | pekiştirmeli öğrenme | Learning through trial and error with a reward signal. |
| RLHF | "er-el-eyç-ef" | Reinforcement Learning from Human Feedback: reinforcement learning through a reward model trained on human preferences. |
| RoPE | "rope" (rotary position embedding) | The method letting the model understand the token order; today's most common position encoding. |
| Safetensors | "seyf-tensırs" | The fast, code-not-executing safe weight file format widespread in the Hugging Face ecosystem. |
| Sampling | örnekleme | Picking from the next token's probability distribution; adjusted with temperature and top-p. |
| Seed | tohum (seed) | The number pinning the randomness; the same seed makes the same experiment reproducible. What it does and doesn't pin in a language model was measured: [Reproducibility](/en/kullanim/tekrarlanabilirlik/). |
| Self-consistency | öz-tutarlılık | Sampling the same question a few times with temperature and taking the majority answer; if the samples pile onto one answer, variety is read; if they spread, uncertainty. |
| Semantic entropy | anlamsal entropi | The sampled answers cluster at the **meaning** level and entropy is drawn from the cluster weights; it measures conceptual difference, not word difference. |
| SFT | "es-ef-ti" | Supervised Fine-Tuning: supervised fine-tuning with labeled input-output examples. |
| Small Language Model | küçük dil modeli | Language models of roughly 0.5-15 billion parameters, able to run on local hardware. |
| Slot | yuva (slot) | A request bucket the server processes at once: the context and KV cache are allocated per slot, i.e. the slot count is a memory price — but the price isn't **equal steps per slot** (measured: the first extra slot ≈233 MiB, each of the next two ≈145 MiB). In Ollama its count is set by `OLLAMA_NUM_PARALLEL`, read at server startup, and asks for a restart. Its measurement: [Concurrency](/en/kullanim/eszamanlilik/). |
| Step | adım (step) | A weight update made over a single batch; the epoch's subunit. |
| System prompt | sistem istemi | The instruction given at the chat's start, defining the model's personality and rules. |
| Temperature | sıcaklık | The sampling's degree of randomness; values near 0 produce consistent, high values creative output. |
| Test set | test seti | The dataset set aside for the final measurement, used for no tuning. |
| Throughput | verim (throughput) | The number of tokens the server produces per second; evaluated together with the concurrent user count. |
| Token | "token" (jeton) | The smallest unit the tokenizer splits text into; it can be smaller than a word, bigger than a character. |
| Tokenizer | "tokenizer" (jetonlaştırıcı) | The component turning text into tokens and their numeric identities. |
| Top-p | "top-p", çekirdek örnekleme | Sampling from the set of the most likely tokens until their total probability reaches p. |
| Training | eğitim | The process of the model's weights being updated with data. |
| Transformer | "transformer" | The attention-based fundamental architecture of today's LLMs. |
| Truncated entropy | kırpılmış entropi | Entropy computed by re-normalizing only the first k returned candidates; since the tail isn't seen, it's a **lower bound**, never exceeding the real entropy. |
| Underfitting | eksik öğrenme | The model failing to learn even the training data enough; it happens from insufficient capacity, data or time. |
| Validation | doğrulama | Watching the model's performance on data it didn't see in training. |
| Vocabulary | sözlük (vocabulary) | The set of all tokens the tokenizer knows; its size affects the model's cross-lingual efficiency. |
| VRAM | "vi-ram" | The graphics card (GPU) memory; the main constraint determining the model size and quantization choice. |
| Warmup | ısınma | Gradually ramping the learning rate from zero to its target at training's start. |
| Weight decay | ağırlık sönümü | The regularization reducing memorization by preventing the weights from growing. |
| Weights | ağırlıklar (weights) | The model's learned parameters; the numbers that quantization and merging operate on. |
| Zero-shot | sıfır örnekli | Asking the model the task directly, giving no examples. |

## Commonly confused concepts

- **Fine-tuning vs pretraining:** pretraining is from scratch, with huge data, and expensive; fine-tuning is with an existing model, small data, and relatively cheap.
- **LoRA vs QLoRA:** in LoRA the base model stays at normal precision (fp16); in QLoRA it's loaded in 4-bit. QLoRA asks for less VRAM, LoRA offers somewhat higher fidelity.
- **Epoch vs step:** a step is a single batch's weight update; an epoch is one pass over all the data. For example with 10,000 examples and a batch size of 8, one epoch = 1,250 steps.
- **Parameter vs hyperparameter:** a parameter is a weight the model learned from data; a hyperparameter is the setting you choose (like the learning rate).
- **Precision vs quantization:** precision is the general name of the question "how many bits are the numbers?"; quantization is the operation of deliberately lowering that bit count.
- **Loss vs perplexity:** loss is the error measure used in training; perplexity is its easier-to-interpret derivative, often used with language models.
- **Validation vs test set:** the validation set is looked at during development (model choice, early stopping); the test set is reserved for the final measurement.
- **Temperature vs top-p:** both are sampling settings; temperature changes the distribution's shape, top-p the breadth of the set of tokens that can be picked. A third truncation form, min-p, keeps those with a probability of a fraction of the most likely candidate; the three's behavior and their Ollama defaults: [Inference Parameters](/en/kullanim/cikarim-parametreleri/).
- **Temperature vs calibration:** temperature changes **which** token is picked; whether the probability the model reports to you matches accuracy (calibration) is a separate question. It was measured on this machine that the logprob Ollama reports isn't affected by temperature: [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/).
- **Logprob vs accuracy:** a sequence's logprob measures how **confident the model looks**, not whether the answer is right. The measured example: an answer given an average logprob of −0.0028 (i.e. near certainty) coming out wrong.
- **P(chosen) vs P(golden):** the chosen option's probability is available at inference time and used to set thresholds; the golden option's probability is an analysis-only number, since it knows the label.

## Related pages

- The concepts' story-told telling: [Core Concepts](/en/baslangic/kavramlar/)
- The practical meaning of the hyperparameters used in training: [Hyperparameters](/en/llm/hiperparametreler/)
- More Turkish and English resources: [Useful Links and Resources](/en/kaynaklar/faydali-linkler/)
