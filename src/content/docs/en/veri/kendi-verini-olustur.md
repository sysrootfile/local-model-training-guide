---
title: "Create Your Own Dataset: Training Data from FAQs and Documents"
description: "Ways to turn the FAQs, support records and documents in your hands into teachable question-answer data — manual creation, synthetic generation and quality control."
dogrulama: 2026-11-20
---

So far we've used ready-made datasets. But the real value of the job starts here: **your own data.** Every corporate support record you hold, every FAQ you wrote, every product document you prepared — none of these exists in the open sets on the internet. This page describes the path from "I have these materials" to "I have training-ready JSONL".

## Inventory the Materials in Your Hands

Before starting, make a table — decide which source converts into which format:

| Material in your hands | The data it becomes | Suitable method |
| --- | --- | --- |
| FAQ page / frequently asked questions | Question-answer (SFT) | Direct mapping |
| Support emails / live chat records | Question-answer (SFT) | Clean + summarize |
| Product documents, manuals | Question-answer (SFT) or plain text | Generate with an LLM + verify |
| A pile of technical write-ups / articles | Plain text (continued pretraining) | Chunk → plain-text data |
| Workflows, internal processes | Instruction-answer (SFT) | Have an expert dictate or write |

:::note[How is this different from "where to find data"?]
The [Where to Find Data?](/en/veri/veri-nereden-bulunur/) page is the hunt for "ready data"; this page is the manufacture of data from **your own raw material**. The two complement each other: learn the loop with ready data, differentiate with your own.
:::

## Method 0: Interviewing the Expert (The Most Valuable Data)

The highest-quality data is the data written in no document. The **tacit knowledge** in an experienced employee's head — jobs learned by experience like "when a return request comes, check the shipping label first", "if you see this error, open a new account for the customer" — rarely enters FAQ pages and manuals. If you already have written question-answer pairs, skip to [Method 1](#method-1-direct-conversion-highest-quality); the interview extracts what hasn't been written yet. The most direct way is a **structured 30-60 minute interview** with that person.

The mechanics:

1. **Preparation (10 min):** write the questions in advance. Good interview questions: "What are the 10 problems you see most?", "What do customers misunderstand most?", "What are the first three rules you teach a newcomer?", "In which case would you say 'this job doesn't fit the rule'?"
2. **Interview (30-60 min):** record it (with permission). Note the examples and step-by-step flows the expert describes; don't hesitate to ask "why?" — the reasoning behind a rule is valuable for the model's generalization.
3. **Transcription (1-2 hours):** convert the recording into question-answer pairs. Fix the sentences into corporate style but don't change the content.
4. **Expert approval:** have the expert read the pairs you extracted. The "that's what I said" approval catches mis-transfers and ties the expert into the process.

Expectation management: **1 interview ≈ 50-100 examples.** The tidy notes coming out of a 30-60-minute conversation comfortably produce that many pairs.

**The golden set:** set aside a **golden set of 100-200 hand-written examples** (whatever the method, write the first examples yourself). This set does two jobs: (1) it becomes the quality bar for later synthetic generation — if new examples don't reach this level, rewrite them; (2) it is used as reference test questions in model evaluation. Don't contaminate the golden set with synthetic generation; it is the bar itself.

:::tip
Don't try to finish the interview in one sitting: in the first round extract the main flow, in the second round ("last time you said this; what happens in that case?") deepen the detail. Two short rounds are more productive than one long one.
:::

## Method 1: Direct Conversion (Highest Quality)

If you already have FAQs or question-answer pairs, the job is mostly **formatting**:

```text title="conversion example"
RAW (FAQ page)                         →  JSONL (chat format)
                                                      
Question: How many days do I have to return?  →  {"messages": [
Answer: You can return the product                {"role": "user", "content": "How many days do I have to return?"},
within 14 days of delivery.                       {"role": "assistant", "content": "You can return the product
                                                  within 14 days of delivery."}]}
```

Tricks:

- Write the answers **as they are but tidy**: prune unnecessary opening sentences ("Hello, hope you're having a good day...") and go straight to the information.
- Preserve the corporate voice — if that's the style you want the model to learn, reflect it in the data.
- Put the same **system prompt** on every example; consistency is what makes the behavior settle.

## Method 2: Generating Q&A from Documents

You have a 40-page product manual but no question-answers. Two paths:

### A) Manual writing (highest quality, slowest)

Read the document and write by imagining real user questions. Start with a 500-example goal; if you write the first 50-100 yourself, you also learn the quality bar.

### B) Generation from a large model (synthetic data)

Asking a strong model (a cloud model via API or a large local model) to generate question-answers from a document piece:

```python title="synthetic_generation_skeleton.py"
# A representative skeleton — the logic is the same whichever provider you use
PROMPT = """Based on the following text, produce {count} question-answer pairs.
Rules:
- The questions should be the kind real customers would ask.
- The answers must rely ONLY on the information in the text; add no made-up information.
- Give the output as a JSON list: [{{"question": "...", "answer": "..."}}]

TEXT:
{text}
"""

generated = []
for chunk in document_chunks:            # split the document into 1000-1500-character chunks
    raw_output = call_llm(PROMPT.format(count=5, text=chunk))
    for pair in load_json_safely(raw_output):
        generated.append({
            "messages": [
                {"role": "system", "content": "You are the company's product assistant."},
                {"role": "user", "content": pair["question"]},
                {"role": "assistant", "content": pair["answer"]},
            ]
        })
```

The origin of this generation logic is **Self-Instruct**: a model can be aligned with instruction-answer examples it generated itself ([arXiv:2212.10560](https://arxiv.org/abs/2212.10560)). But not every generated example is equal — the proof is **AlpaGasus**: filtering Alpaca's 52k instructions by having an LLM judge score them leaves ~9k high-quality examples behind, and **the model trained on 9k examples clearly beats the one trained on all 52k** ([arXiv:2307.08701](https://arxiv.org/abs/2307.08701)). The lesson: in synthetic generation, invest in the **filter**, not the volume — where the "rely only on the text" prompt isn't enough, add a quality-scoring step and drop the low-scored examples.

Prompt variation for variety: WizardLM's **Evol-Instruct** approach artificially evolves instructions into more complex and varied forms ([arXiv:2304.12244](https://arxiv.org/abs/2304.12244)) — instead of generating in the same pattern with the same prompt, you can enrich the set by making the questions harder and more varied.

:::danger[The three traps of synthetic data]
1. **Fabrication:** the model "completes" information that isn't in the text. That's why the "rely only on the text" rule in the prompt is a must, and the examples must also be verified **against the source** after generation.
2. **Reinforcing its own errors:** training a model with the data it generated teaches it its errors too. Use synthetic data with a small human verification (a sampling check).
3. **Pattern repetition:** data generated with the same prompt takes on a "robotic" pattern. Ask for variety in the prompt; request different question types (why/how/isn't it).
:::

## Method 3: Continued-Pretraining Data from Plain Text

The path that doesn't require you to generate answers: using the long texts in your hands (articles, internal notes) as **plain text**.

```python title="chunk_text.py"
def chunk(text: str, chunk_size: int = 1500, overlap: int = 150):
    """Split a long text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap      # leave overlap so the context doesn't break
    return chunks
```

:::caution
Don't confuse continued pretraining with SFT: with plain text you do "knowledge infusion" but you don't teach "instruction following". Usually the two are used together — for the flow see [Pretraining from Scratch](/en/llm/pretraining/) and [Instruction Tuning](/en/llm/sft/).
:::

## An End-to-End Mini Case: 200 Examples from a 40-Page Manual

Let's combine the methods in one scenario. You have a 40-page product manual; the goal is a domain-specific SFT set of ~200 examples:

1. **Chunk (Method 3 code):** split the manual into 1,500-character chunks → **~60 chunks**. Cut the chunks at sentence boundaries where possible so questions don't lose context.
2. **Generate (Method 2B):** generate 3-5 question-answers per chunk → **~250 candidates**.
3. **Dedupe ([Data Cleaning](/en/veri/veri-temizleme/)):** similar questions from different chunks — it's typical for the manual to explain the same information in two places — trip the exact and near-duplicate filters → **~200 remain**. The remaining difference comes from pruning broken/disjointed generations.
4. **Verify by eye:** randomly pick 10% of the examples (20 examples) and read them against the source.
5. **Split:** ~180 examples for training, 20 for test. Verify with a leakage scan that the test examples don't overlap with training.

| Step | Count | Note |
| --- | --- | --- |
| Raw manual | ~40 pages | |
| Chunking (1,500 characters) | ~60 chunks | cut at sentence boundaries |
| Synthetic generation | ~250 candidates | 3-5 questions per chunk |
| Exact + near-duplicate filter | ~200 remaining | repeated questions are removed |
| 10% eye verification | 20 examples | read against the source |
| Training / test set | ~180 / 20 | leakage scan done |

The numbers belong to this example scenario; the ratios change in your material. What matters is the flow: **chunk → generate → filter → verify → split**.

## A Realistic Plan with a 500-Example Goal

| Step | Target | Time (approx.) |
| --- | --- | --- |
| Inventory + raw material collection | 1 stack of documents | 1-2 hours |
| Hand-writing (golden set) | 150-200 examples | 3-5 hours |
| Synthetic generation | 300-500 examples | 1-2 hours |
| Cleaning + duplicate filter | A deduplicated set | 1 hour |
| Verifying the generated ones (sampling) | 10% eye check | 1 hour |
| Training/validation split | 95% / 5% | 5 minutes |

Total: **1-2 days of effort** for a dataset specific to your domain that nobody else can access. The training itself may take 1-3 hours — that is, **the weight of the job is in the data**, just as this guide said from the start.

## Quality Control and Ethics

The last check before training:

1. **Source robustness:** pick 20 random answers, verify them against the source document.
2. **Contradiction scan:** are there examples giving two different answers to the same question?
3. **Distribution:** the balance of easy/medium/hard questions and short/long answers.
4. **Personal data:** are there leftover names, emails, customer records? ([Data Cleaning](/en/veri/veri-temizleme/))
5. **Permission and license:** do you have the right to use customer data and internal documents? Check the company policy and the personal-data-law framework (in Turkey, KVKK).

:::danger[The ethical boundary]
Don't build training data from other people's private correspondence, customer data or content collected without permission. Work with data you produced, data you have permission for, or openly licensed data.
:::

## The Post-Deployment Loop: Updating the Data

When the model goes live, the data work isn't over; **the real data source just opens up**: real user questions. The loop goes:

1. **Collect:** record the questions the model fails at — chat logs if you run the model locally with the [Ollama Guide](/en/kullanim/ollama/), request logs if you're on an API. "I didn't like it" feedback is the most valuable signal.
2. **Label:** write the correct answer for each failed question (consult an expert if needed) and add the question-answer pair to the golden set.
3. **Retrain:** retrain the model with the updated set; measure progress with [Benchmarks](/en/degerlendirme/benchmarklar/) and your own test set.
4. **Version:** store every dataset with a date/number (`data_v2_2026-10.jsonl` etc.). The question "which data was this model trained on?" will definitely be asked days later.

Two rules:

- **Never touch the test set.** Failed questions go into the training/golden set; the test set stays fixed so progress can be measured honestly. If you must update the test set, create a new version and report the scores from scratch.
- **Update little and often.** Instead of collecting 500 questions for one giant round, run a small training round every 50-100 new examples; measure at every round whether things improved.

## Sources and Further Reading

- [AlpaGasus (arXiv:2307.08701)](https://arxiv.org/abs/2307.08701) — the study showing that reducing 52k Alpaca instructions to ~9k with a quality filter improved model quality (Chen et al., 2023).
- [Self-Instruct (arXiv:2212.10560)](https://arxiv.org/abs/2212.10560) — the origin paper of the idea that a model can be aligned with its own generated instructions (Wang et al., 2023).
- [LIMA (arXiv:2305.11206)](https://arxiv.org/abs/2305.11206) — the study showing the power of little but carefully chosen data; strong alignment results with 1,000 selected examples (Zhou et al., 2023).
- [distilabel (GitHub)](https://github.com/argilla-io/distilabel) — a framework for synthetic data generation and AI feedback; community-maintained as of 2026.

## Next Step

You have a clean JSONL in hand. Now you can train your model with [Instruction Tuning (SFT)](/en/llm/sft/) or return to the [Step-by-Step Training](/en/llm/adim-adim-egitim/) guide to complete the loop.
