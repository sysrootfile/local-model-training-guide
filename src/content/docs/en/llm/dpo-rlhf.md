---
title: "DPO and RLHF: Shaping the Model with Preferences"
description: "RLHF's three stages, why DPO is practical, the method landscape in TRL, DPO practice and failure modes, RLAIF and synthetic data, preparing preference data, and an annotated example with TRL DPOTrainer."
dogrulama: 2026-11-20
---

The model coming out of [instruction tuning (SFT)](/en/llm/sft/) often "knows the right thing but its behavior isn't what you want". Let's look at examples:

- It always answers questions at great length (the user wanted a short answer),
- It chats too casually where a formal tone was requested,
- It sometimes hits an unsafe or rude tone,
- It gives unnecessary advice where it should say "I can't help with that".

Although SFT fixes these problems *partially* with examples, teaching every behavior "by writing good examples" is hard. Preference tuning exists precisely for this: instead of "good examples", we teach the model the information **"this answer is better than that one"**.

## RLHF: The Classic Method and Its Three Stages

Reinforcement learning from human feedback (RLHF) consists of three stages:

```text title="The classic RLHF pipeline"
[1] SFT: train the model with good examples  -->  /en/llm/sft/
            |
            v
[2] REWARD MODEL: show humans two answers to the same question and
    ask "which is better?"; train a separate model that learns to
    "score answers" from the given preferences.
            |
            v
[3] PPO: update the main model with reinforcement learning so it
    scores high against the reward model.
      - Four models are held in memory at once: policy, reference, reward, value
      - Unstable and expensive; needs serious engineering and hardware
```

RLHF is powerful (it was used in the GPT series' alignment) but costly for an individual project: you need to train an extra reward model, manage PPO's stability, and have serious VRAM.

## DPO: The Same Idea, Far Simpler

**DPO (direct preference optimization)** became popular in 2023 with the paper "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (2305.18290). The finding, briefly: you can skip the reward model + PPO complexity and update the model **directly from "chosen vs rejected" answer pairs**.

```text title="The DPO pipeline"
[Preference data: (question, chosen answer, rejected answer)]
            |
            v
[DPO loss: the 'chosen' answer's probability rises while
 the 'rejected' answer's probability falls; both at once, in one training]
            |
            v
[One training loop — no reward model, no PPO]
  - A fixed 'reference model' is kept only as a comparison yardstick
  - Works with a training script as simple as SFT's
```

DPO's practical advantages:

- It uses the **same data type** as RLHF (human preferences), but with a far simpler pipeline.
- It can be combined with [LoRA/QLoRA](/en/llm/lora-qlora/); it can be tried even on a single consumer GPU.
- The training loop resembles SFT: load data, train, save.

## Preference Data: Format and Production

For DPO, the most common data format is a JSONL file with `prompt`, `chosen`, `rejected` fields:

```json title="preference_data.jsonl"
{"prompt": "A customer wrote an angry email because their shipment is 3 days late. Draft a polite, solution-focused reply of no more than 150 words.", "chosen": "Hello, we are very sorry about the delay you experienced. I've looked into it right away: your shipment was held at the distribution center and goes out today. You can follow its movements through your tracking number; if the delay exceeds 48 hours we will refund the shipping fee. Thank you for your understanding — we'll keep you posted.", "rejected": "Shipping delays aren't something under our control, ask the courier company. There's always rush, just wait a bit."}
{"prompt": "A user says they forgot their password. Help them.", "chosen": "Of course, let me help. You can click the 'Forgot my password' link and use the reset link sent to your registered email. If the email doesn't arrive, check the spam folder; if the problem persists, try verification with the phone number registered to your account.", "rejected": "If you don't know your password there's nothing I can do, I suggest you open a new account."}
```

:::note
Where will you get the data?

- For open preference datasets and Turkish sources, see the [Where to Find Data](/en/veri/veri-nereden-bulunur/) page. (Most open preference sets are English; Turkish sets are growing as of 2026 but are not yet as rich as English.)
- Producing it yourself is also a perfectly valid path: write two different answers to the same question (or take them from two different models) and label which is better.
- For speed: generating two answers from a strong model (e.g. with different temperature settings) and marking the better one is also a common approach. Auto-labeling brings noise; in a small set, always check by eye.
:::

The golden rule in data preparation: `chosen` must be genuinely good, `rejected` genuinely bad — but they must both be **answers to the same question**. If they answer entirely different questions, the model learns "topic" instead of "preference".

## A Short Example: TRL DPOTrainer

```python title="dpo_training.py"
# Preference tuning with DPO — on a model that passed SFT (or a base model)
# Setup: pip install "trl" "peft" "datasets" "transformers" "accelerate"

from datasets import load_dataset
from peft import LoraConfig
from trl import DPOConfig, DPOTrainer

# Preference data: a JSONL with prompt / chosen / rejected fields
data = load_dataset("json", data_files="preference_data.jsonl", split="train")
splits = data.train_test_split(test_size=0.1, seed=42)

lora_config = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    task_type="CAUSAL_LM",
)

training_args = DPOConfig(
    output_dir="./dpo-output",
    beta=0.1,                        # how far the model may stray from the reference (0.01-0.5)
    num_train_epochs=1,              # in DPO, 1 epoch usually suffices
    learning_rate=5e-7,              # NOTE: in DPO the lr is far smaller than SFT (5e-7 - 1e-6)
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    lr_scheduler_type="cosine",
    warmup_steps=0.03,               # a ratio: 3% of steps (v5; formerly warmup_ratio)
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
)

trainer = DPOTrainer(
    model="Qwen/Qwen3-4B",           # ideally give the path of your SFT-trained model
    args=training_args,
    train_dataset=splits["train"],
    eval_dataset=splits["test"],
    peft_config=lora_config,         # to combine with QLoRA, load the model in 4-bit and pass it
)
trainer.train()
trainer.save_model("./dpo-adapter")  # again only an adapter of a few MB
```

:::caution
Leaving the learning rate as high as SFT's (e.g. 2e-4) in DPO training is the most common mistake; the model breaks quickly (it "collapses"). For DPO stay in the `5e-7 – 1e-6` range. To understand `beta`: a small beta (0.01-0.05) lets the model change more freely, a large beta (0.2-0.5) keeps it more tied to the reference model.
:::

## Quick Notes: ORPO, SimPO and GRPO

- **ORPO and SimPO:** DPO's newer relatives. ORPO aims to skip the SFT stage entirely and learn from preference data in a single stage; SimPO is a DPO variant that removes the reference-model need. If you're doing straightforward SFT+DPO, you don't have to try these for now; note them as an interesting research area.
- **GRPO:** the reinforcement learning method popular in deep reasoning models; strong on tasks where **the correct answer can be automatically verified**, like math and code. It's available in TRL as `GRPOTrainer`. For small projects with custom data it's usually more than even DPO; keep it in the back of your mind as an advanced topic.

## The Method Landscape in TRL as of 2026

TRL v1 (2026) sorts its trainers by maturity: some are core (used in production for years and listed in the official docs' main flow), some experimental. The status as of 2026:

| Method | Trainer | Status (TRL v1.x) | When preferred |
| --- | --- | --- | --- |
| DPO | `DPOTrainer` | Core | If you have `chosen`/`rejected` pairs; the first preference method to try |
| KTO | `KTOTrainer` | Core | If you can't collect preference pairs: a single answer + a "good/bad" (binary) label suffices |
| GRPO | `GRPOTrainer` | Core (online) | If you can verify the reward automatically with a function (math, code) |
| RLOO | `RLOOTrainer` | Core (online) | Online reinforcement learning; a lighter alternative in reward-function flows |
| ORPO | `ORPOTrainer` | Experimental | If you want to skip the SFT stage and learn from preference data in one step |
| CPO | `CPOTrainer` | Experimental | Similar to ORPO; another single-stage relative without SFT |

(Source: the "Taxonomy" section of the TRL docs — the core/experimental split is made officially there.)

If you stay with DPO, there are loss variants too; they're chosen with the `loss_type` parameter in TRL. The default is `sigmoid`; a few standout options:

| `loss_type` | The idea | Source |
| --- | --- | --- |
| `sigmoid` (default) | The classic DPO objective: grow the probability gap between chosen and rejected | The DPO paper, arXiv:2305.18290 |
| `ipo` | Identity transformation instead of logit transformation; against overfitting | IPO, arXiv:2310.12036 |
| `sigmoid_norm` | The sigmoid loss normalized by answer length (SimPO) | SimPO, arXiv:2405.14734 |
| `hinge` | A margin-based loss | RSO, arXiv:2309.06657 |
| `bco_pair` | Treats the preference as a binary classification problem | BCO, arXiv:2404.04656 |
| `robust` | Resilient to noisy/flipped preference labels | Robust DPO, arXiv:2403.00409 |

:::tip
If you're starting out, stay with the default `sigmoid`. Changing `loss_type` is no substitute for fixing data quality; the real lever is the data. If you're bothered by length exploitation, `sigmoid_norm` (SimPO-style length normalization) can be tried — we dig into that problem in the "Known Failure Modes" section.
:::

## DPO Practice: beta, ref_model and the Learning Rate

Let's open the four critical knobs of the example config, based on the TRL docs:

- **`beta` (default 0.1):** it penalizes the model's deviation from the reference model. With the TRL docs' wording: "higher beta, less deviation from the reference model". If the model barely changes (stayed too conservative), lower beta a notch; if the model breaks away from the reference and starts behaving oddly, raise it.
- **`ref_model=None` (memory saving):** if you don't want to keep a separate reference model, leave it `None`; in that case the trainer treats the model's state before training began as the reference. With LoRA/QLoRA (PEFT) this becomes even more practical — in the TRL docs' words: "when using PEFT in DPO you don't need to provide a separate reference model; the trainer automatically uses the frozen base model as the reference." This way you needn't load a second model copy into memory.
- **Epochs:** if the preference data is small, 1-2 rounds usually suffice; before raising it, look at the validation loss ([Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/)).
- **Learning rate:** the recommendations from TRL's PEFT integration doc (for LoRA, roughly 10x the full fine-tuning value):

| Training type | TRL recommendation (DPO) |
| --- | --- |
| Full fine-tuning | `5.0e-7` |
| LoRA | `5.0e-6` (roughly 10x) |

TRL's DPO trainer page notes that a magnitude of `≈1e-5` can also be used when training an adapter. There's no single "right" number; decide on your own data by watching the validation loss and sample outputs.

On the data side, TRL accepts both plain text and chat forms. If your data carries role labels (user/assistant), the chat form makes things easier:

```json title="chat_form_preference.jsonl"
{"prompt": [{"role": "user", "content": "My shipment is 3 days late, what should I do?"}], "chosen": [{"role": "assistant", "content": "We're sorry for the delay; we're looking into it right away and will update you through your tracking number."}], "rejected": [{"role": "assistant", "content": "Ask the courier company, there's nothing we can do."}]}
```

## Known Failure Modes and Precautions

DPO is powerful but not free; the literature documents three traps well:

1. **Likelihood displacement:** DPO should normally suppress only the rejected answer; but in some cases the "chosen" answer's probability also falls — while moving away from the preferred answer, the model lurches in a different direction. The "Unintentional Unalignment" study shows this happens especially with preference pairs that have similar representations (embeddings), and that filtering such examples reduces the problem markedly (arXiv:2410.08847).
2. **Length exploitation:** humans (and judge models) tend to favor long answers; DPO can learn this and start inflating every answer. Park et al. relate this exploitation to the length bias in DPO's implicit reward and propose a simple length regularization (arXiv:2403.19159); length-normalized losses like TRL's `sigmoid_norm` (SimPO) also aim to reduce this bias.
3. **Regression in reasoning:** DPO is effective on chat benchmarks but its gain remains marginal in long-horizon reasoning; the Step-DPO study reports that plain DPO provides almost no benefit on math problems (arXiv:2406.18629). Comprehensive studies comparing DPO with PPO also show DPO can lag behind PPO on some tasks (arXiv:2404.10719).

:::caution
That's why after DPO, looking only at "did the preference improve?" isn't enough: run regression tests on the tasks the model was already good at (knowledge questions, JSON generation, math). Precautions: (1) the quality and length balance of the preference data, (2) a cautious setup of beta and the learning rate, (3) a blind before/after comparison with your own mini test set ([Benchmarks](/en/degerlendirme/benchmarklar/)).
:::

## RLAIF and Synthetic Preference Data

The preference label doesn't have to come from a human: **RLAIF** (reinforcement learning from AI feedback) is having a model do the labeling. The best-known application of this idea is Anthropic's **Constitutional AI** study: the model is given a written list of principles (a "constitution"), evaluates and corrects its own outputs against those principles, and most of the human harmlessness labeling is delegated to the model (arXiv:2212.08073).

Two practical approaches for generating synthetic preference/data:

- **Magpie:** give an aligned model a nearly empty chat template to have it generate a "user question", then have the same model answer it; this synthesizes large-scale instruction data from the model's own distribution (arXiv:2406.08464).
- **distilabel (Argilla):** an open-source Python library that lets you wire generator and judge models into sequential steps and build a pipeline producing synthetic data and preference pairs ([argilla-io/distilabel](https://github.com/argilla-io/distilabel)).

:::caution
Loop-training on only your own model's outputs carries a **model collapse** risk: models trained over and over on synthetic data gradually lose the tails of the distribution and variety drops (Shumailov et al., Nature, 631, 755-759, 2024). The balance: mix synthetic data with human-written or human-approved data, don't rely on a single model's output, and check examples by eye. Starting points: [Where to Find Data](/en/veri/veri-nereden-bulunur/) and [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).
:::

## SFT and DPO Side by Side

| | SFT | DPO |
| --- | --- | --- |
| Data type | (input, good answer) pairs | (input, good answer, bad answer) triples |
| What it teaches | "Answer like this" | "Answer like this, not like that" |
| Learning rate (with LoRA) | 1e-4 – 2e-4 | 5e-7 – 1e-6 |
| Typical epochs | 1 – 3 | 1 |
| Typical data need | Thousands of question-answer examples | Thousands of preference pairs |
| Training time | Hours | Hours (similar to SFT) |
| When used | Always the first step | The second step if style/safety/preference is critical |

:::note
A post-DPO evaluation tip: looking only at the training loss isn't enough; check **by eye** whether it produces outputs resembling the "chosen" answers. For details, [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).
:::

## Do You Need It? The Decision Box

:::tip
- **Individual project / single-task model:** [SFT](/en/llm/sft/) is almost certainly enough. Do SFT first, [evaluate](/en/degerlendirme/loss-ve-metrikler/) the results; think about DPO only if behavior is genuinely problematic.
- **Style, safety or "preference" is critical:** DPO makes sense. It gives good results if you have (or can collect) thousands of quality preference pairs.
- **Experimenting with 200-300 preference pairs:** not enough; the model memorizes or polarizes. Invest in growing the data.
- **DPO out of pure curiosity:** not categorically harmful, but spend the time and GPU cost consciously. Over-engineering is beginners' most common trap; "SFT + good data + good evaluation" usually gets you to the goal.
:::

## What Is Measured After DPO?

DPO is a "preference" training; measurement is done in three layers:

1. **Preference measurement (the actual goal):** are the model's answers genuinely preferred more than before DPO? The most reliable way is to produce before/after answers to the same questions and compare them blind (without knowing which model is which). If you want to scale this, there are LLM-judged tools like AlpacaEval ([tatsu-lab/alpaca_eval](https://github.com/tatsu-lab/alpaca_eval)) — but remember judge models have their own biases; details on the [Benchmarks](/en/degerlendirme/benchmarklar/) page.
2. **Regression tests (silent damage insurance):** DPO can break the abilities the model was already good at (see the "Known Failure Modes" section). Run your mini test set before and after DPO and compare success per task; if there's a drop, raise beta or review the data.
3. **Behavior tests:** was the desired behavior genuinely gained? For target behaviors like "answer briefly", "be polite", "say you can't help when needed", 20-30 hand-written examples suffice; put the two models' outputs side by side and read blind.

:::tip
Don't lean on a single number ("a 67% win rate"): in small sets, a few examples flipping swings the result. Account for the possibility that differences are statistical noise when the sample size is small ([Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/)).
:::

## Wrapping Up

- RLHF = SFT + reward model + PPO. Powerful but a heavy pipeline.
- DPO = a simple alternative using the same preference data, requiring no reward model or PPO.
- Data: `prompt / chosen / rejected` pairs; scarce and low-quality data breaks DPO.
- The learning rate is far smaller than SFT's (5e-7 – 1e-6); 1 epoch is typical.
- In most projects, SFT first, and DPO only if needed.

Related pages: [Tools Comparison](/en/llm/araclar/), [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/), [Benchmarks](/en/degerlendirme/benchmarklar/), [Hyperparameters](/en/llm/hiperparametreler/).

## Sources and Further Reading

- [TRL — DPO Trainer documentation](https://huggingface.co/docs/trl/main/en/dpo_trainer) — the official reference for `loss_type` options, the `beta` default and data formats.
- [TRL — PEFT Integration](https://huggingface.co/docs/trl/main/en/peft_integration) — where the no-separate-reference-model note and the recommended learning rates live.
- [TRL — Main Page (Taxonomy section)](https://huggingface.co/docs/trl/en/index) — which trainer is core and which experimental: the official split.
- [Direct Preference Optimization (arXiv:2305.18290)](https://arxiv.org/abs/2305.18290) — DPO's original paper (Rafailov et al., 2023).
- [Unintentional Unalignment: Likelihood Displacement (arXiv:2410.08847)](https://arxiv.org/abs/2410.08847) — why the "chosen" answer's probability can drop, and the filtering fix.
- [Disentangling Length from Quality in DPO (arXiv:2403.19159)](https://arxiv.org/abs/2403.19159) — the mechanism of length exploitation and the regularization proposal.
- [Is DPO Superior to PPO for LLM Alignment? (arXiv:2404.10719)](https://arxiv.org/abs/2404.10719) — the comprehensive comparison of DPO and PPO.
- [STEP-DPO (arXiv:2406.18629)](https://arxiv.org/abs/2406.18629) — plain DPO's limits in reasoning and the step-based alternative.
- [Constitutional AI (arXiv:2212.08073)](https://arxiv.org/abs/2212.08073) — the foundational study of the RLAIF idea (Anthropic).
- [Magpie (arXiv:2406.08464)](https://arxiv.org/abs/2406.08464) — the method for synthesizing instruction data from an aligned model.
- [distilabel (GitHub)](https://github.com/argilla-io/distilabel) — the open-source library for building synthetic-data and preference-pair pipelines.
- [Model collapse (Nature 631, 755-759, 2024)](https://www.nature.com/articles/s41586-024-07566-y) — how loop-training on synthetic data narrows the distribution.
- [SimPO (arXiv:2405.14734)](https://arxiv.org/abs/2405.14734) — the reference-model-free, length-normalized DPO variant.
- [AlpacaEval (GitHub)](https://github.com/tatsu-lab/alpaca_eval) — an open tool doing automatic preference comparison with an LLM judge.
