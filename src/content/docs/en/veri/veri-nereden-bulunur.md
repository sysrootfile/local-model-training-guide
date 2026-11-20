---
title: "Where to Find Data? (Including Turkish Resources)"
description: "A guide to ready-made datasets, raw text sources and verified Turkish data collections — large pretraining corpora, scraping law and synthetic data notes; where to download, how to use, what to watch out for."
dogrulama: 2026-11-20
---

Data is the fuel of model training. On this page you will see three different source paths and especially strategies for finding **Turkish data**.

:::note
Data is a very broad topic: for types see [Data Types](/en/veri/veri-turleri/), for formatting [Data Formats](/en/veri/veri-formatlari/), for cleaning [Data Cleaning](/en/veri/veri-temizleme/).
:::

## Three Source Paths

```text
A) Ready-made datasets    → Hugging Face, Kaggle ... (fastest start)
B) Generate from raw sources → Wikipedia, Common Crawl, your own scraping job ...
C) Your own data          → FAQs, support records, product docs ...
```

The right strategy for most projects: **start with A, finish with C.** Learn the loop with ready data, then specialize with your own.

## A) Ready-Made Datasets

### The Hugging Face Hub

Today's number-one address for datasets is [Hugging Face Datasets](https://huggingface.co/datasets). Tens of thousands of sets; plus a data viewer for inspecting rows one by one in the browser and one-line-code downloads.

```python title="hf_download_data.py"
from datasets import load_dataset

# Download in one line
ds = load_dataset("username/dataset-name", split="train")
print(ds)             # see the size and fields
print(ds[0])          # peek at the first example

# For large sets: streaming mode, without downloading to disk
ds_stream = load_dataset("username/big-dataset", split="train", streaming=True)
for example in ds_stream.take(3):
    print(example)
```

**Search tips:** when searching on HF, pick the language filter **Turkish (tr)** in the left panel; sort by "Most downloads". On a set's page, check **size and license** first, then **example quality** via the data viewer.

:::tip
Quality check in 30 seconds: read 10-20 rows in the data viewer on the dataset page. Lots of typos, empty fields or irrelevant examples? That set very likely needs extra cleaning.
:::

### Kaggle

[Kaggle Datasets](https://www.kaggle.com/datasets) is strong especially for tabular data and competition sets. In Kaggle notebooks you can reach data with `pip install kagglehub` + `kagglehub.dataset_download("username/set-name")`. You can also make training attempts with the weekly free GPU quota ([cloud options](/en/donanim/bulut-secenekleri/)).

## Turkish Datasets

Open Turkish data is markedly scarcer than English — which is why this section is gold for people working in Turkish. The standout sets as of 2026:

| Dataset | Type | Scale / Note | For what? |
| --- | --- | --- | --- |
| `atasoglu/turkish-instruction-datasets` | HF collection | Instruction sets together (many sets) | First stop for fine-tuning (SFT) |
| `ogulcanaydogan/Turkish-LLM` (HF + GitHub) | Instruction + training data | ~173K-242K examples; used with QLoRA on Qwen2.5 | Turkish instruction tuning — a real project example |
| `HuggingFaceFW/fineweb-2` (tr) | Web corpus | ~95.1M documents / ~41.9B words / 125.53 GB on disk (verified from the HF card's language table) | Continued pretraining, pretraining |
| Turkish Data Depository (TDD) | Academic corpus | OSCAR + mC4 Turkish, ~240 GB / 82M documents | Pretraining, language modeling research |
| `hasankursun/turkish-corpus-100b` | Web + reasoning mix | Targeting 100B tokens | Continued pretraining |
| Holmeister Turkish evaluation sets | Evaluation | Multi-task, multi-prompt (17 sets) | Eval — not for training! |
| `kesimeg/awesome-turkish-language-models` | Catalog (GitHub) | A list of Turkish models + data + papers | Discovery and keeping current |

If you want to pull FineWeb-2's Turkish section in streaming mode only:

```python title="fineweb_tr.py"
from datasets import load_dataset

# Note: the language config name ("tur_Latn") can change between versions — check the HF page
ds = load_dataset(
    "HuggingFaceFW/fineweb-2", "tur_Latn",
    split="train", streaming=True,
)
for example in ds.take(2):
    print(example["text"][:300])
```

:::caution
Turkish web corpora (OSCAR, mC4, fineweb etc.) contain raw web text: broken sentences, spam and ad text can be plentiful. Filtering is a must before direct use: [Data Cleaning](/en/veri/veri-temizleme/).
:::

### Verified Turkish datasets (last verified: October 2026)

Each line below was verified one by one from the HF dataset page and the data viewer: row counts come from the actual files, licenses were read from the data card's `license` field. The ones marked "not stated on card" were deliberately left that way — do not assume an unverified license.

| Dataset | Size / rows (as of 2026) | License | Task type | HF page |
| --- | --- | --- | --- | --- |
| `TFLai/Turkish-Alpaca` | 51,914 rows | Apache-2.0 | Instruction (SFT) | [HF](https://huggingface.co/datasets/TFLai/Turkish-Alpaca) |
| `merve/turkish_instructions` | 51,563 rows | Apache-2.0 | Instruction (SFT) | [HF](https://huggingface.co/datasets/merve/turkish_instructions) |
| `AlicanKiraz0/Turkish-SFT-Dataset-v1.0` | 5,579 rows | MIT | Instruction (SFT) | [HF](https://huggingface.co/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0) |
| `OpenAssistant/oasst1` (Turkish part) | 37 messages (whole corpus 88,838 rows) | Apache-2.0 | Dialogue / preference data | [HF](https://huggingface.co/datasets/OpenAssistant/oasst1) |
| `winvoker/turkish-sentiment-analysis-dataset` | 489,644 examples (440,679 + 48,965) | CC-BY-SA-4.0 | Sentiment analysis | [HF](https://huggingface.co/datasets/winvoker/turkish-sentiment-analysis-dataset) |
| `savasy/ttc4900` | 4,900 examples / 7 news categories | Not stated on card | Text classification | [HF](https://huggingface.co/datasets/savasy/ttc4900) |
| `reciTAL/mlsum` (tr) | 273,617 rows (249,277 + 11,565 + 12,775) | Non-commercial research only | News summarization | [HF](https://huggingface.co/datasets/reciTAL/mlsum) |
| `facebook/xnli` (tr) | 400,202 rows (392,702 + 2,490 + 5,010) | Not stated on card | NLI (evaluation-oriented) | [HF](https://huggingface.co/datasets/facebook/xnli) |
| `GoktugD/turkish-nli-constructed-1.5m` | 1,500,000 pairs (synthetic generation) | CC0-1.0 | NLI | [HF](https://huggingface.co/datasets/GoktugD/turkish-nli-constructed-1.5m) |
| `hcsolakoglu/turkish-wikipedia-qa-4-million` | 449,844 rows (~4M Q&A; model-generated) | CC-BY-NC-SA-4.0 | Question answering | [HF](https://huggingface.co/datasets/hcsolakoglu/turkish-wikipedia-qa-4-million) |
| `tascib/turkish-llm-dataset` | 100M-1B tokens (HF size label) | CC-BY-SA-4.0 | Pretraining / continued training | [HF](https://huggingface.co/datasets/tascib/turkish-llm-dataset) |

:::note
`oasst1` says it contains 35 languages but is English-heavy: the Turkish message count across the whole corpus is only 37 (October 2026, data viewer filter). It isn't enough alone for Turkish alignment — mix it with English preference data and measure with a Turkish evaluation set: [DPO and RLHF](/en/llm/dpo-rlhf/).
:::

:::caution
Before using the sets marked "not stated on card" in the license column (`savasy/ttc4900`, `facebook/xnli`) in a commercial product, ask the source. `mlsum` is open to non-commercial research only; the Turkish Wikipedia QA set is CC-BY-NC-SA — both are closed to commercial use.
:::

## Large Pretraining Corpora (Turkish)

If you're looking for pretraining-scale data there are three big options; the decision comes down almost entirely to license and access conditions (scales as of 2026 from HF data cards, last verified: October 2026):

| Corpus (config) | Scale (as of 2026) | License / access | When preferred? |
| --- | --- | --- | --- |
| FineWeb-2 (`tur_Latn`) | 95,129,129 documents; 41,933,799,420 words; 125.53 GB on disk (284.52 GB UTF-8) | ODC-By — attribution required | If you'll do continued pretraining with filtered text that has passed through one pipeline: today's most balanced start. |
| CulturaX (`tr`) | 94,207,460 documents; 64,292,787,164 tokens | Subject to the mC4 and OSCAR licenses (the mC4 side ODC-By) | If you want a cleaned corpus with high source variety, merged from mC4 + OSCAR — but you must examine both sources' conditions separately. |
| OSCAR-2301 | Gated: access only with manual approval; **temporarily suspended** until usage rights are clarified (October 2026) | No copyright claim on the raw data; metadata and descriptions CC0-1.0; download requires a declaration of compliance with national law | Don't prefer it until the legal situation is clear; FineWeb-2 and CulturaX cover the same need comfortably. |

## B) Generating Data from Raw Sources

| Source | Content | Typical use |
| --- | --- | --- |
| Wikipedia dumps (trwiki) | Encyclopedia text, CC BY-SA licensed | Continued pretraining, knowledge base |
| Common Crawl | Periodic archives of the whole web | Pretraining (needs serious filtering) |
| OPUS | Parallel translation corpora | Translation/multilingual training |
| Tatoeba | Example sentence pairs | Small-scale language experiments |
| The Stack | Open-licensed source code | Code models |
| Open government data (e.g. data.gov.tr) | Official documents, statistics | Domain models (law, public sector) |

:::danger[Legal and ethical boundaries]
- **Copyright:** books, news texts and closed-platform content cannot be used without permission. Prefer open licenses (CC, MIT, Apache) and public-domain sources.
- **Personal data:** if texts contain personal data like names, national IDs, addresses, health information, you fall under **KVKK/GDPR**; don't use without cleaning ([cleaning steps](/en/veri/veri-temizleme/)).
- **Platform rules:** before scraping a site, look at its terms of use and `robots.txt` rules.
- **The safest path:** data you produced yourself, openly licensed sets and public-domain sources.
:::

## The Status of Official and Public Sources

Official sources may look "open" but their access models differ a lot. The status as of 2026:

| Source | Status | Access and conditions |
| --- | --- | --- |
| Turkish Wikipedia dumps (trwiki) | Open and regular: monthly dumps are published (the current version as of October 2026: 20261001) | [dumps.wikimedia.org/trwiki](https://dumps.wikimedia.org/trwiki/) — content CC BY-SA; attribution required when publishing |
| TTC4900 (a text classification classic) | Available on HF: `savasy/ttc4900` (4,900 examples, 7 categories); no license on the card | [HF page](https://huggingface.co/datasets/savasy/ttc4900) — confirm the license from the source before commercial use |
| TBMM (Turkish Parliament) transcripts | An official web interface exists (per term and legislative year, with "raw text" links); no official bulk-download API | [Transcript Texts](https://www.tbmm.gov.tr/Tutanaklar/TutanakMetinleri) — examine the terms of use before automated scraping |
| YÖK National Thesis Center | No bulk download; search with membership, full text only for permitted theses | [tez.yok.gov.tr](https://tez.yok.gov.tr/UlusalTezMerkezi) — measured, attribution-carrying access; try official request routes instead of bulk scraping |

## Scraping and the Law: What to Watch Out For?

Scraping is technically easy, legally demanding work. In Turkey, three layers are evaluated together:

:::caution
- **KVKK (personal data):** name, national ID number, phone, email, address, location and health information are personal data. Due to purpose limitation and data minimization, collect only the fields you need; mask identifiers before training ([Data Cleaning](/en/veri/veri-temizleme/)). The bar is stricter for special-category data like health, belief and biometrics.
- **robots.txt and terms of use:** before scraping, look at the site's `robots.txt` file and terms; don't crawl forbidden paths, limit the request rate so the site isn't strained, and never touch login/membership areas.
- **License compatibility:** CC-BY-NC (e.g. `mlsum`, the Turkish Wikipedia QA set) is closed to commercial use; ODC-By (e.g. FineWeb-2, mC4) requires attribution; CC-BY-SA (e.g. Wikipedia, the `winvoker` sentiment set) requires the same license for derivative works; MIT / Apache-2.0 are open to commercial use.
- **This section is general information, not legal advice.** If you plan a use that will become a product, consult a legal expert — legislation and case law change over time ([the KVKK Authority](https://www.kvkk.gov.tr/)).
:::

## C) Preparing Your Own Data

The most valuable data is usually already in your hands: support emails, FAQ pages, product docs, internal correspondence... To teach these to a model you must convert them into a structured question-answer format. Step-by-step recipe: [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).

## Synthetic Data: Generating Instructions from a Model

Synthetic data is a training example generated by a model. Two common tools:

- **Self-instruct generation (Magpie):** you give an aligned chat model only the part of the template up to the user's turn; the model generates the instruction and the response from its own distribution — quality alignment data without human-written instructions ([Xu et al., 2024](https://arxiv.org/abs/2406.08464)).
- **Pipeline tool (distilabel):** combines generation, filtering and judge-model evaluation in one pipeline ([GitHub](https://github.com/argilla-io/distilabel)); the tool started by the Argilla team is now community-maintained.

Synthetic data shines especially in: under-represented domains (law, medicine, games), multi-turn scenarios with a `system` field, and tasks where labeled data is expensive.

:::caution
Training in a loop on synthetic data only carries a **model collapse** risk: as the model is trained repeatedly on its own generated distribution, the tails of the real distribution are erased and variety decreases across generations (Shumailov et al., Nature 631, 755-759, 2024 — [link](https://www.nature.com/articles/s41586-024-07566-y)). A balanced mixture: always include human-written real data alongside (a common starting point is half and half), don't stay dependent on a single model's output, and filter the generated data. For the preference-data side, [DPO and RLHF](/en/llm/dpo-rlhf/); for turning your own material into data, [Create Your Own Dataset](/en/veri/kendi-verini-olustur/).
:::

## Where Do You Find Evaluation Data?

The training + evaluation split is sacred — don't use the same data for both. For Turkish evaluation, the [Holmeister sets](https://huggingface.co/collections/Holmeister/turkish-llm-multi-prompt-evaluation-datasets) (17 sets for 11 tasks; last verified 2026-10), the eval sets in the `atasoglu` collection, or your own 20-50-question mini test set (the most practical way): [Benchmarks](/en/degerlendirme/benchmarklar/).

## A Strategy for Finding the Right Dataset

Searching is the job of quickly pulling the right box from a crowded shelf — the most efficient flow as of 2026:

1. **Filter:** in the [HF Datasets](https://huggingface.co/datasets) search, pick **Turkish (tr)** in the left panel, narrow the task category (instruction, summarization, QA...) and sort first by **Most downloads**, then **Trending**.
2. **Read the data card (5 minutes):** the license (commercially usable? attribution required?), size and row count (consistent with the data viewer?), splits (is an evaluation set separated?), language quality (mixed languages, translation smell, repetition?), the contamination note (overlap-with-benchmarks warning) and the last update date (a set frozen in 2023 may not meet current needs).
3. **Preview before downloading:** pull the first rows with the `datasets-server` API without taking the file to disk:

```python title="preview.py"
import requests

r = requests.get(
    "https://datasets-server.huggingface.co/rows",
    params={
        "dataset": "TFLai/Turkish-Alpaca",
        "config": "default",  # differs in some sets: see the Configs list on the data card
        "split": "train",
        "offset": 0,
        "length": 5,
    },
    timeout=30,
)
data = r.json()
print("Total rows:", data["num_rows_total"])
for row in data["rows"]:
    print(row["row"])
```

4. **Streaming mode for giant corpora:** process with `streaming=True` without downloading to disk; don't feed raw web text straight into training, pass it through the [Data Cleaning](/en/veri/veri-temizleme/) pipeline.

## The Quick Quality Checklist

For every set you download, run these 6 checks:

1. Is the **license** compatible (especially if you'll use it commercially)?
2. Is the **language** really Turkish (mixed sets exist)?
3. What is the rate of **empty/broken rows**?
4. Are there **duplicates** (the same example many times)?
5. Is there **personal data** (name, phone, email)?
6. Is the **format** right for your tool ([conversion](/en/veri/veri-formatlari/))?

:::tip
You don't have to do these checks by hand; a mini script scanning the first 1,000 rows with `datasets` + pandas takes 10 minutes to write — see the [Data Cleaning](/en/veri/veri-temizleme/) page for ideas.
:::

## Sources and Further Reading

- [FineWeb-2 data card (Hugging Face)](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) — a filtered web corpus with over a thousand language subsets; the Turkish statistics are in the card's language table.
- [FineWeb2 paper (arXiv:2506.20920)](https://arxiv.org/abs/2506.20920) — the technical details of the corpus and filtering pipeline.
- [CulturaX data card (Hugging Face)](https://huggingface.co/datasets/uonlp/CulturaX) — a multilingual corpus cleaned from the mC4 and OSCAR merge; document and token counts per language.
- [OSCAR-2301 data card (Hugging Face)](https://huggingface.co/datasets/oscar-corpus/OSCAR-2301) — gated access, copyright status and terms of use.
- [Magpie: Alignment Data Synthesis from Scratch (arXiv:2406.08464)](https://arxiv.org/abs/2406.08464) — the method for generating instructions from an aligned model on its own.
- [distilabel (GitHub)](https://github.com/argilla-io/distilabel) — the pipeline tool for synthetic data and judge-model evaluation.
- [AI models collapse when trained on recursively generated data (Nature 631, 755-759, 2024)](https://www.nature.com/articles/s41586-024-07566-y) — the experimental demonstration of model collapse.
- [Wikimedia dumps: trwiki](https://dumps.wikimedia.org/trwiki/) — the Turkish Wikipedia's regular dumps (CC BY-SA).
- [TBMM Transcript Texts](https://www.tbmm.gov.tr/Tutanaklar/TutanakMetinleri) — the official transcript archive; no official bulk-download API.
- [YÖK National Thesis Center](https://tez.yok.gov.tr/UlusalTezMerkezi) — thesis search and permitted full texts; bulk download is restricted.
- [The KVKK Authority](https://www.kvkk.gov.tr/) — the official source of personal data protection legislation.
