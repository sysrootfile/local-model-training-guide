---
title: "RAG or Fine-Tuning? Choosing the Right Approach"
description: "Do you want to teach the model new knowledge or new behavior? We compare the RAG-vs-fine-tuning decision across cost, freshness, latency, citation and hallucination axes, and map out the hybrid path."
dogrulama: 2026-11-20
---

This is the most important question to answer before investing in model training: will you solve the problem, or make the problem never exist? In most situations that seem to call for "training a model", the actual cure isn't training; **RAG** (retrieval-augmented generation), which works like an open book, solves knowledge-based problems without spending GPU time. This page maps the decision: which tool solves which job, what each costs, and how to build the hybrid path that is most projects' real answer.

**The one-sentence answer:** to teach the model **knowledge**, use RAG; to teach it **behavior**, use fine-tuning; most real projects use both together.

## The Decision Ladder: Start with the Cheapest Tool

Framing the decision as "RAG or fine-tuning?" actually skips two rungs of the ladder. Always start at the bottom rung and justify climbing with a concrete reason:

```text title="The decision ladder — cost and effort grow as you climb"
4. The hybrid path   → RAG (knowledge) + fine-tuning (behavior) together
3. Fine-tuning       → the model's behavior, style or format is wrong
2. RAG               → the model's knowledge is missing, stale or proprietary (your documents)
1. Prompt engineering → does a good instruction + a few examples solve it?
```

:::tip[Take rung 1 seriously]
Clarifying the instruction and giving 2-3 examples (few-shot) solves many format and consistency problems at zero cost. Fine-tuning should be reserved for **permanent** behavior change unreachable by prompting: [SFT](/en/llm/sft/).
:::

## The Main Distinction: Knowledge or Behavior?

You can reduce the decision to a single question: **is the model speaking wrongly, or speaking in the wrong way?**

- **Speaking wrongly** (a knowledge problem): it doesn't know your internal policy, is unaware of your product catalog, speaks with yesterday's data, uses domain terms in the wrong context. The knowledge is **absent** from the model's weights. Fix: retrieve the knowledge externally at query time — RAG.
- **Speaking in the wrong way** (a behavior problem): it has the knowledge but gives in three pages what should take three sentences, uses a chatty tone where a formal one is wanted, dumps plain text when you ask for JSON, talks like an assistant when it should talk like a support agent. The knowledge is there; the **form is wrong**. Fix: teach the behavior with examples — fine-tuning ([SFT](/en/llm/sft/), for preferences [DPO and RLHF](/en/llm/dpo-rlhf/)).

**Analogy:** giving a newly hired expert access to the internal document pool (RAG) is one thing; training them to write in the company's correspondence style (fine-tuning) is another. When you hand someone the documents, their writing style doesn't change; changing style genuinely takes practice (working through examples).

## The Two Approaches Side by Side

| Axis | RAG | Fine-tuning |
| --- | --- | --- |
| What it changes | The knowledge the model **accesses** | The model **itself** (behavior, style, format) |
| Freshness | Knowledge updates when the document does; no retraining | An update = a retraining |
| Citation (sourcing) | Natural: which document the answer came from is traceable | None: the answer's source can't be shown |
| Hallucination risk | Reduces it: the answer leans on supplied documents | Rises if used for knowledge (below) |
| Latency | Adds a retrieval step per query | No extra retrieval; a single pass |
| Data need | Raw documents suffice (no labels) | Thousands of consistent examples needed: [Create your own dataset](/en/veri/kendi-verini-olustur/) |
| Training hardware | Not needed | A GPU or a rented card: [Cloud Options](/en/donanim/bulut-secenekleri/) |
| Maintenance load | A vector database + retrieval quality | A data pipeline + training + evaluation loop |

There's hardly a row where the two don't intersect; but the most commonly skipped row is **citation**. Every scenario where you must show which document an answer came from (law, medicine, internal policies, customer support) effectively makes RAG mandatory — fine-tuning can't do that job.

## Why Is Fine-Tuning a Bad Idea for Teaching Knowledge?

Intuition says "I'll make the model memorize the knowledge too", but practice works against it for three reasons:

1. **Memorization doesn't generalize.** If you make the model memorize a fact with a single example, it recalls it only in that example's formulation; when the question changes slightly, the answer vanishes or gets fabricated. Ovadia et al.'s 2023 comparison from the Microsoft Research team (Fine-Tuning or Retrieval?) showed that in the job of giving a model unseen knowledge, **RAG leaves fine-tuning clearly behind**.
2. **Little data, big damage.** Fine-tuning done on a narrow knowledge pile can degrade the model's existing abilities (forgetting); you need to work with thousands of balanced examples: [Data Cleaning](/en/veri/veri-temizleme/).
3. **The update cost is continuous.** When the inventory, price list or policy changes, retraining is needed; in RAG, changing the document suffices.

:::note[Not the opposite of what LIMA showed]
The LIMA study says "fine-tuning with only 1,000 examples may suffice" — but those examples teach **behavior and format**; the knowledge mostly already exists from pretraining: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/). This doesn't contradict this page's distinction — it confirms it exactly: fine-tuning's job is behavior; it doesn't carry knowledge.
:::

There is one exception: a **completely absent language or a very narrow domain language** (like intensive use of medical jargon) may require continued pretraining (DAPT) — and that too is not fine-tuning but a scaled training job: [Pretraining](/en/llm/pretraining/).

## Why Is RAG Insufficient for Teaching Behavior?

RAG adds **content** to the model's context; it cannot change **how the model produces**. A student taking an open-book exam doesn't change their answer-writing style by reading the book. These requests can't be met with RAG:

- "Give every answer in three bullets and formal language." (format)
- "Never tell the customer 'I don't know'; propose a solution." (policy behavior)
- "Speak in the company's voice." (style)
- "Answer the question in a JSON schema." (structure)

All of these are permanent behaviors taught with examples; the right tool is SFT, which is why in most product scenarios the order is: if RAG solves the problem, don't train; if it doesn't, teach the behavior to a model now fed RAG-backed examples (the hybrid path below).

## The Hybrid Path: Most Projects' Real Answer

The typical production setup is two-layered:

1. **The RAG layer** provides the right knowledge: documents live in a vector database, the most relevant pieces per query are added to the context, the answer leans on the document and can cite its source.
2. **The fine-tuning layer** pins the answer's format: the model is taught the behavior "with the retrieved context, in this style, in this format, answer".

The practical order: run the RAG pipeline first; then **collect the good answers the system gives** and convert them into your fine-tuning data. That way your training data reflects the real distribution, and the two layers support each other. For a comprehensive resource on the naive → advanced → modular evolution of RAG architectures, see the Gao survey below.

:::caution[Don't reverse the order]
Fine-tuning first and adding RAG later is the most common wrong setup: if the fine-tuning was trained on answers given without RAG, it isn't used to the context format it sees in real RAG-backed use, and the behavior it gained is lost. Prepare your training data in the same template as the production context format (document pieces + question): [Data Formats](/en/veri/veri-formatlari/).
:::

## Did Long Context Kill RAG?

In the small context windows of the 2010s RAG was a necessity; today 128K-token windows gave birth to the option "throw all documents into the context, skip building retrieval infrastructure". This option works in three situations:

- If the corpus is small (a few dozen documents, below the window in total),
- If the query count is low and cost/latency are irrelevant,
- If you can accept the quality loss.

It has three serious prices:

1. **The cost is paid per query.** Every token thrown into the context is billed on every request — and Turkish inflates this math 1.5-2.5x: [Tokenization](/en/temeller/tokenizasyon/). In RAG, only the relevant pieces are paid for.
2. **Memory and speed.** Long context grows the KV cache memory linearly at inference: [Transformer Architecture](/en/temeller/transformer/). 128K context on a local card is mostly a fantasy.
3. **Quality drops in the middle.** Liu et al.'s "Lost in the Middle" study showed that in long contexts the model trusts the information at the beginning and end more than the middle. A short, relevant context selected by retrieval naturally reduces this risk.

Conclusion: long context doesn't replace RAG; it replaces RAG in the **small corpus + low traffic** combination.

## The Cost and Effort Comparison

**The RAG side:** the main cost is one-time indexing and it's surprisingly cheap. Local embedding models (below) are free; if you use an API, as of 2026 OpenAI text-embedding-3-small is **$0.02** and text-embedding-3-large is **$0.13** per 1M tokens — so indexing half a million tokens of documents with the small model costs about **$0.01**. The continuous cost is the context tokens added per query and running the vector database.

**The fine-tuning side:** there are two expense items: data labor (preparing consistent examples is most projects' longest step: [Data](/en/veri/kendi-verini-olustur/)) and training time (a typical QLoRA run takes from 30 minutes to 6 hours depending on hardware: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/)). Serving the trained model adds the [merging](/en/kullanim/lora-birlestirme/) and [quantization](/en/kullanim/quantization/) steps to the chain.

The rule: for your knowledge problem, RAG is almost always cheaper **and** more accurate; reserve the fine-tuning budget for behavior.

## The Local RAG Stack (As of 2026)

Running all components locally is possible; the flow has four parts:

```text title="The local RAG pipeline"
1. Chunk the documents      → 256-1024-token chunks (10-20% overlap at the edges)
2. Vectorize the chunks     → an embedding model (local, free)
3. Write to a vector DB     → an index for similarity search
4. The query flow           → vectorize the question → fetch the k nearest chunks → add to context → generate
```

- **The embedding model:** Ollama runs embedding models directly (the `/api/embeddings` endpoint): the common choices are `nomic-embed-text` and BAAI's multilingual `bge-m3`. Setup and an example flow: [Ollama](/en/kullanim/ollama/).
- **The vector database:** for simple projects [Chroma](https://docs.trychroma.com/) (installs with pip, runs embedded); for larger scale and filtering [Qdrant](https://qdrant.tech/documentation/); for a single-file lightweight solution, `sqlite-vec`.
- **Orchestration:** if you don't want to hand-write the document loading → chunking → indexing → query chain, [LlamaIndex](https://docs.llamaindex.ai/) or LangChain provides it ready.
- **A zero-code solution:** [Open WebUI](/en/kullanim/ollama/) lets you upload documents and ask questions over them from the interface; at the decision stage it's the fastest way to feel the concepts.

:::tip[Run end to end first, then improve]
On the first night aim for a "working answer", not a "great answer". If your problem is retrieval quality (the right document isn't found), the fix isn't fine-tuning but changing the chunk size, the embedding model or the [hybrid search](/en/rag/parcalama-ve-hibrit-arama/) (keyword + vector) choice — measurement decides which to change: [RAG Evaluation](/en/rag/rag-degerlendirme/). This pipeline has **two versions actually run on this machine**: the [Local RAG Assistant example](/en/ornekler/yerel-rag/) (with supplied documents) and the [Turkish RAG from Wikipedia example](/en/ornekler/viki-rag/) (live data + chunking).
:::

## Practical Notes for Turkish

- **Measure the embedding choice with your own data.** Multilingual models (bge-m3, multilingual-e5) generally work well in Turkish, but that's a general observation; prepare 20-30 question-answer pairs from your own documents and measure "does the right piece arrive in the top k?" — half a day's work that determines the whole system's quality. Fill the numbers with your own measurement; someone else's table doesn't represent your corpus.
- **The token multiplier sets the budget.** Turkish's 1.5-2.5x token consumption fits fewer chunks in the same window; don't plan the context budget with English assumptions: [Tokenization](/en/temeller/tokenizasyon/).
- **Chunk boundaries shouldn't split words.** In an agglutinative language, splitting inside a word hurts embedding quality more than in English; forcing the chunker to cut at sentence boundaries is usually the right choice.

## The Mini Decision Table

| Scenario | Recommendation |
| --- | --- |
| Q&A over internal documents, with sources shown | RAG |
| Answer style/format inconsistent, knowledge correct | Fine-tuning (SFT) |
| The model has both problems: knowledge missing, format broken | The hybrid path (RAG + SFT) |
| Product catalog / prices / policies updated often | RAG (no retraining) |
| It doesn't answer in Turkish or speaks broken Turkish | Fine-tuning — with Turkish behavior data: the [turkce-asistan example](/en/ornekler/turkce-asistan/) |
| Small corpus, low traffic, quick prototype | Directly stuffing the context (without RAG) |
| A new language or very narrow domain language is needed | Continued pretraining (DAPT): [Pretraining](/en/llm/pretraining/) |
| Which sources the wrong answers came from will be audited | RAG (citation traceability) |

## Next Steps

- If the decision favored fine-tuning: [SFT](/en/llm/sft/) and [LoRA and QLoRA](/en/llm/lora-qlora/)
- If it favored RAG: the [Local RAG Assistant example](/en/ornekler/yerel-rag/) (a working script), [Turkish RAG from Wikipedia](/en/ornekler/viki-rag/) (live data + chunking) and local embedding setup with [Ollama](/en/kullanim/ollama/)
- The infrastructure both paths presuppose: [VRAM Math](/en/donanim/vram-hesabi/), [Roadmap](/en/baslangic/yol-haritasi/)
- A quick look at the concepts: [Concepts](/en/baslangic/kavramlar/), [FAQ](/en/kaynaklar/sss/)

## Sources and Further Reading

- [Agent or a Fixed RAG Pipeline?](/en/ajan/ajan-mi-sabit-hat-mi/) — the rung after building your RAG pipeline: do you or the model decide the tool sequence? The cost was measured.
- [Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs (Ovadia et al. 2023, arXiv:2312.05934)](https://arxiv.org/abs/2312.05934) — the study directly comparing RAG and fine-tuning in knowledge injection; shows RAG's clear superiority.
- [Retrieval-Augmented Generation for LLMs: A Survey (Gao et al. 2023, arXiv:2312.10997)](https://arxiv.org/abs/2312.10997) — a comprehensive survey mapping the naive/advanced/modular RAG evolution.
- [Lost in the Middle (Liu et al. 2023, arXiv:2307.03172)](https://arxiv.org/abs/2307.03172) — the study showing performance drops when information sits in the middle of long contexts.
- [OpenAI — API pricing](https://developers.openai.com/api/docs/pricing) — the official page for text-embedding-3-small/large prices (verified as of 2026; check the current value).
- [Ollama — API docs](https://docs.ollama.com/api) — the official doc of the `/api/embeddings` endpoint.
- [BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3) — a multilingual embedding model supporting dense+sparse retrieval.
- [nomic-embed-text (the Ollama library)](https://ollama.com/library/nomic-embed-text) — a common embedding model for local RAG.
- [Chroma docs](https://docs.trychroma.com/) — an embedded vector database installable with pip.
- [Qdrant docs](https://qdrant.tech/documentation/) — a filtering- and scale-focused vector search engine.
- [LlamaIndex docs](https://docs.llamaindex.ai/) — the orchestration framework that builds the RAG chain from document loading to query.
