---
title: "License, Personal Data and Model Card"
description: "The license chain, personal-data scanning and model card fields before publishing your trained model — a measured audit, dated 2026-10-17, of this guide's own local stack and its own published texts."
dogrulama: 2026-11-20
---

When training a model finishes, two separate questions begin: **am I permitted to do this** and **does it contain someone else's data**. Neither is answered with "I ran the code, the loss dropped". This page measures those two questions on this machine — what's audited isn't a random repo but **this guide's own example stack and its own published texts**.

:::note[Credentials: what was measured where]
- The license inventory: `ornekler/lisans-ve-gizlilik/lisans_envanter.py` → the record `ornekler/lisans-ve-gizlilik/cikti/lisans-envanter.txt` (the run 2026-10-17 14:22:37 → 14:22:38, Ollama 0.40.4 — the machine's server moved to 0.40.6 on 2026-10-19, the inventory wasn't re-taken on that version, `http://127.0.0.1:11434`).
- The personal-data audit: `ornekler/lisans-ve-gizlilik/pii_denetim.py` → the record `cikti/pii-log.txt` (the run **14:21:44 → 14:22:36**). No inference request, no network access, the seed 20261017.
- The audited masker: the `pii_maskele` and regex constants inside `ornekler/veri-temizleme/atolye.py` — i.e. the tool taught to you in Example 2.
- **This page's own text is inside the scanned set too.** If you re-run the script after pasting the numbers here, the "published pages" row grows as long as this page grows: the table is the snapshot of the run ending at the timestamp below, not a fixed fact. The audit's own folder (`ornekler/lisans-ve-gizlilik/`) was excluded from the count so the scripts wouldn't count their own keywords and their own half-written log.
- Every externally sourced claim (the Hugging Face card fields, the license texts) is given with **last verified: October 17, 2026**. A license may have changed after that date; this page isn't an immutable reference, it's a snapshot.
- This page gives no legal advice. In a use that will become a product, consult a legal expert.
:::

## Saying the First Finding Up Front: This Site's Model Is Research-Licensed

Examples 5, 6, 7 and 8 and all the measurement rigs on the site use the same model: `qwen2.5:3b-instruct-q4_K_M`. The `LICENSE` field in the Modelfile Ollama distributes for this tag carries not Apache-2.0 but the text of the **"Qwen RESEARCH LICENSE AGREEMENT"** — 7,387 bytes, 54 lines. From the record, the text's own sentences:

- The definition clause: `"Non-Commercial" shall mean for research or evaluation purposes only.`
- The granted right: `... to use, reproduce, distribute, copy, create derivative works of, and make modifications to the Materials FOR NON-COMMERCIAL PURPOSES ONLY.`
- The commercial side: `If you are commercially using the Materials, you shall request a license from us.`
- The derivative model condition: `If you use the Materials or any outputs or results therefrom to create, train, fine-tune, or improve an AI model that is distributed or made available, you shall prominently display "Built with Qwen" or "Improved using Qwen" in the related product documentation.`
- The attribution file: you're asked to put a text file named `"Notice"` inside every distributed copy, containing the Alibaba Cloud attribution sentence.
- Also: modified files carrying a "prominent notice", an export-control declaration and an indemnification obligation in third-party claims.

**What this means for you:** running this guide's examples on your own computer for training/measurement purposes is the area the license explicitly permits. If you'll put the output into a product, you must either request a license from Alibaba Cloud or change the base model. If you train and publish a LoRA, clause `4.b` makes you write a notice on the card.

The same model's `license` field on its Hugging Face card is `other`, and the `license_link` field points to the `LICENSE` file inside the repo — i.e. the card and the packaging don't conflict; both point to the same special license.

## It's Not the License Family That's Measured, but the File in the Repo

We looked at the card field in five repos of the Qwen family today (`cardData.license`, the HF API, last verified October 17, 2026):

| Repo | The card field | Meaning |
| --- | --- | --- |
| `Qwen/Qwen2.5-1.5B-Instruct` | `apache-2.0` | free |
| `Qwen/Qwen2.5-3B-Instruct` | `other` + a LICENSE link | Qwen Research, non-commercial |
| `Qwen/Qwen2.5-7B-Instruct` | `apache-2.0` | free |
| `Qwen/Qwen2.5-32B-Instruct` | `apache-2.0` | free |
| `Qwen/Qwen3-8B` | `apache-2.0` | free |

**A single size** in the family has a different license — and that size is the one this guide chose, because it can run on CPU. Family generalizations like "Qwen is Apache" or "Llama is conditional" can come out wrong exactly where the job's edge touches. The rule: **read the license not from the model family but from the repo you'll use and from inside its packaged form.**

:::note[A Filled License Field Doesn't Mean the License Is Right]
The Modelfile license fields of the three local models entering the inventory:

| Model | The license heading | The text | Template residue |
| --- | --- | --- | --- |
| `qwen2.5:3b-instruct-q4_K_M` (3.1B, Q4\_K\_M, 1,930 MB) | Qwen RESEARCH LICENSE AGREEMENT | 7,387 bytes / 54 lines | none |
| `bge-m3` (566.7M, F16, 1,158 MB) | MIT License | 1,068 bytes / 21 lines | **`[year]` and `[fullname]` sitting as they are** |
| `nomic-embed-text` (137M, F16, 274 MB) | Apache License | 11,357 bytes / 201 lines | Apache's appendix's template parenthesis (by design) |

Note the `bge-m3` row: in the copyright line, where the year and copyright holder should be, a bracketed template sits. An MIT text with no rights holder written is, legally, "tried to say MIT but didn't declare it" — in the table above BAAI's own card says `mit`, i.e. the problem is the distribution package's copying sloppiness. The lesson to draw: **the existence of a license text and the license being defined are different things.** In quantized/GGUF derivatives the license field is mostly filled automatically, and mostly filled incompletely.
:::

## The Derivative's License: Fine-Tuning, Merging, Quantization

Three rules, all three direct readings of the texts above:

1. **The derivative can't be freer than the base model.** Publishing an Apache-2.0-based LoRA under MIT promises more than the text permits; publishing a Qwen Research-based fine-tune as Apache-2.0 is an outright violation. The compliance box on the [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/) page explains this rule; what's measured here is which text the rule comes from.
2. **Quantization doesn't lower the license.** A Q4\_K\_M is a copy, not a new work — the `qwen2.5:3b-instruct-q4_K_M` row entering the inventory shows this itself: the Q4\_K\_M package carries the Research license as it is. That's the legal consequence of the technical steps on the [Quantization](/en/kullanim/quantization/) and [LoRA Merging](/en/kullanim/lora-birlestirme/) pages.
3. **Merging takes the most restrictive one.** A model produced by weight-averaging two base models must comply with both's conditions at the same time; if you combine Apache-2.0 with the Research license, commercial use stays under the Research side's prohibition.

The Hugging Face card fields exist to carry this chain structurally (today's doc, last verified October 17, 2026): `base_model` and `base_model_relation` (the Hub derives the relation as `adapter` / `merge` / `quantized` / `finetune` itself; it can also be written by hand), `license`, for a special license `license: other` + `license_name` + `license_link`, `datasets`, `pipeline_tag`, `library_name`, `tags`.

## Personal Data: We Audited the Scanner

The masker in `ornekler/veri-temizleme/atolye.py` looks at four patterns: email, phone, IBAN and an 11-digit TCKN candidate. Today we distinguished two things: **does the tool find the data within its scope** and **does the tool know its own scope**.

### The calibration set: 30 cases, three kinds of labels

Thirty hand-written synthetic Turkish sentences. Each case is either POSITIVE (personal data, the tool should see it), or TAIL (not personal data, the tool shouldn't mark it), or a BLIND SPOT (personal data, but outside the tool's scope).

| Result | Count | Reading |
| --- | --- | --- |
| In-scope data caught | 12 / 12 | all the positive cases: a hold rate of 1.00 |
| In-scope data missed | 0 | no loss in this slice |
| False positive (tail) | 1 / 9 | the only marked case: `TR` + 24 identical digits |
| Correct rejections | 8 / 9 | an uns checksummed TCKN, a version number, a short TR code... |
| Blind spots (personal data, unseen) | 9 / 9 | name-surname + address, a birth date, GPS coordinates, a plate, a health sentence, an obfuscated email, delimiter-grouped TCKNs (2 forms), pairwise-grouped phones |

The two numbers say the same thing: the tool succeeds on **formal** data and is absent on **semantic** data. The 12/12 hold rate doesn't mean "our mass is clean" — because the 9 missed cases are personal data itself.

### Form or validity?

| What was tried | A plain regex | With checksum/math |
| --- | --- | --- |
| `12345678901` (11 digits, an order no) | counts as TCKN | the checksum fails → rejected |
| `TR111111111111111111111111` | counts as IBAN | mod-97 fails |
| `TR680001234567890123456789` (a computed check digit) | counts as IBAN | mod-97 passes |

The checksum steps are already inside the masker (the TCKN side), and **absent** on the IBAN side. Of the seven IBAN-shaped hits found in the repo scan, **one** passes mod-97; and that hit is the synthetic value I quoted in the calibration table above. So the thing contaminating the scan is precisely the audit's own report. There's no real IBAN; but the scanner would count both a formally shaped string like `TR111…` and the mod-97-failing `TR00 0000 0000 0000 0000 0000 01` (occurring in Example 3's training mass) as an IBAN and mask them.

### The bill of deleting delimiters

Three of the blind spots (two TCKN forms and one phone) were "space/dot entered between the digits" cases. Deleting the delimiters and joining the digits: in calibration **3 blind spots turned into catches, 6 blind spots stayed where they were** (name, address, birth date, coordinates, plate, health, an email written in words).

Across the whole repo the same move changes the bill: TCKN candidates **34 → 57**, checksum-passing ones **8 → 8**, phone hits **78 → 107**, IBANs **7 → 7**. No new genuine identity number was found; 23 new candidates and 29 new phone hits were added. The checksum filter can silence the candidate growth, but can't silence the phone/IBAN growth. **Conclusion: deleting delimiters isn't a cleverness raising the catch rate; it's a trade-off producing wrong masks; on real personal data alone (identity numbers written in groups) it wins 3/9 by itself.**

### Our own repo's scan

| Group | Files | Characters | TCKN candidates | Checksummed TCKN | Email | Phone | IBAN | mod-97 passing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Published pages (md + mdx) | 58 | 862,300 | 4 | 3 | 4 | 1 | 3 | 1 |
| Example datasets (jsonl) | 3 | 47,049,122 | 20 | 0 | 149 | 68 | 1 | 0 |
| Run logs (txt) | 33 | 192,645 | 4 | 4 | 4 | 4 | 0 | 0 |
| Scripts and README | 28 | 274,187 | 6 | 1 | 6 | 5 | 3 | 0 |
| **TOTAL** | **122** | **48,378,254** | **34** | **8** | **163** | **78** | **7** | **1** |

The run took 12.68 s, a single process, CPU. The four rows' readings:

- **Had we used plain `\d{11}`:** since 8 of the 34 candidates pass the checksum (a rate of 0.235), we'd have produced **26 wrong masks**. All **eight** of the checksum-passing hits are this site's deliberately placed demo value `10000000146`: 3 in two published pages (this page + the Example 2 page), 4 in Example 2's run logs (two in the pre-fix backup, two in the new run), 1 in the masker's own test line (`atolye.py:234`). So there's no genuine identity number in this repo — but the regex doesn't know that, the checksum algorithm does.
- **Example 3's training mass** forms the scan's body: `egitim.jsonl` alone is 43.42 M characters with **130 email and 61 phone** hits; `test.jsonl` 2.31 M characters, 19 emails and 7 phones. These are contact details arriving via `AlicanKiraz0/Turkish-SFT-Dataset-v1.0`, **synthetic-looking**, mostly in the `@example.com` / `+90 555 ...` pattern. Example 3's preparation pipeline (`hazirla.py`) **contains no masking step** — because that example teaches the transition to SFT format, not cleaning. If you work with your own data, the same mass should be passed through Example 2's pipeline.
- **Example 2's own output is clean:** in `temiz_veri.jsonl` email and phone hits are **zero**; there are four TCKN candidates, none passing the checksum. Also, **2 ready mask tokens** (like `[E-POSTA]`) sit in the file — i.e. the masker sees its own trace; there are 4 of those tokens in the training mass.
- **56 of the 58 pages have zero formal hits**; the two pages with hits are pages *explaining* the personal-data subject: the Example 2 page (4 hits, 2 checksummed TCKNs) and this page. The audit's result entered the audited set — since this page carries the very patterns it quotes, the hits count in the scan.
- Of the 83 scanned files (py/md/mdx; `__pycache__`, `cikti/` and the audit's own folder excluded), **32 files** carry at least one license word; the full word count is in the log. Example 6's script carries Wikipedia's CC BY-SA attribution requirement in the `VIKI_LICENSE` constant and prints it at the end of every run.

## The Real Error We Found in Our Own Pipeline

What the audit found wasn't the scanner's error but the **pipeline's**, and it was fixed. `atolye.py` applies normalization to the three fields `instruction`, `input`, `output`; but it applied PII masking to only `instruction` and `output`. Since the SFT writer embedded the `input` field into the user message as "Context: ", an unmasked email remained in a masked line's **published output**. The fix (`atolye.py:263-270`) is one line: adding the `input` field to the masking loop.

| Run | `rapor.json` → `pii_masking` | Email hits remaining in the published output | Other numbers |
| --- | --- | --- | --- |
| 2026-10-15 (pre-fix) | 1 | 1 | 3,000 → 2,747, 5,732 fields corrected |
| 2026-10-17 (post-fix) | **2** | **0** | 3,000 → 2,747, 5,732 fields corrected (exactly the same) |

The same record's line, before and after:

```text
Context: Name: John Doe Phone: (123) 456-7890 Email: jdoe@email.com Current role: ...
Context: Name: John Doe Phone: (123) 456-7890 Email: [E-POSTA] Current role: ...
```

:::caution[These two lines aren't a masking success, they're masking's limit]
The line's masked form still carries personal data. **Name: John Doe** is no regex's job. **(123) 456-7890**, written in US format, falls outside the Turkish phone rule's `5xx` / `2xx-4xx` pattern's scope. The mask counter went from 1 to 2, the line wasn't cleaned. In your own project, don't make the mask count the success measure; the measure is the **scope list**: document which data types you scanned and which you didn't.
:::

:::note[The same name, two meanings]
"John Doe" appears in the output in two records: in one as part of a contact block, in the other as a story character. The latter isn't personal data, the former looks like it; there's no rule making that distinction automatically. That's precisely why the blind-spot class on the scale needs to be *reported in writing* as "out of scope".
:::

## The Legal Framework on the Personal-Data Side: What Should Be Known

In Turkey, the job's name is KVKK (Law No. 6698). On this page I don't quote the law's articles' text as if verified — the authority's site returned only a navigation menu today, and the article text was **not verified** in this audit. The structure you should know is this (its verified form is handled on this site's [Where to Find Data](/en/veri/veri-nereden-bulunur/) page):

- Name, national ID number, phone, email, address, location and health information are **personal data**; types like health, belief and biometrics count as **special-category** with stricter criteria.
- Purpose limitation and data minimization: don't collect from the start the fields you don't need for training. Masking is a secondary cleaning done after collecting.
- The personal data in the data you trained the model on can also leak into the model's *weights* — from the angle of deletion/handling requests, saying "we masked the data, done" may not suffice. Machine unlearning isn't **offered on this guide as a verified method**; keeping your training data small and clean is the real control in our hands today.
- Read the authority's and the law's current text yourself: [kvkk.gov.tr](https://www.kvkk.gov.tr/). This page is general information.

## Writing the Model Card: The Reading List's Other Side

The "model card reading checklist" on the [evaluation pages](/en/degerlendirme/benchmarklar/) was the buyer's side. This is the seller's side — from Hugging Face's model card doc, read today (last verified October 17, 2026): the card is the `README.md` file inside the repo; YAML metadata at the top, text below. The doc expects the card to explain: the model, **the intended use and limitations** (bias and ethical dimensions included — citation: Mitchell et al., arXiv:1810.03993), the training parameters and experimental information, **the datasets used**, the evaluation results. The measurable/fillable metadata fields: `license` (for a special license `other` + `license_name` + `license_link`), `base_model` + `base_model_relation`, `datasets`, `language`, `pipeline_tag`, `library_name`, `tags` (`not-for-all-audiences` if needed), evaluation results structured with `model-index` and a CO2 emissions section.

Two small but critical details: **in repos opened after August 2024 the `library_name: transformers` field isn't assumed automatically** — if you don't write it, the card looks incomplete — and if the `datasets` field is filled, the model page prints the "Datasets used to train:" line itself; i.e. the second link of your license chain becomes visible inside the card.

A filled card heading for a fine-tune going over the base model whose license we measured above — `Qwen/Qwen2.5-3B-Instruct`. Clause 1's rule in its applied form: **the card can't say `apache-2.0`**, because the base is Research-licensed.

```yaml
---
language: tr
license: other                       # can't be freer than the base model's license
license_name: qwen-research-license  # not a family generalization, the measured text
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
base_model: Qwen/Qwen2.5-3B-Instruct
base_model_relation: finetune
datasets:
  - AlicanKiraz0/Turkish-SFT-Dataset-v1.0
library_name: transformers           # must be written by hand for post-2024-08 repos
pipeline_tag: text-generation
tags: [sft, turkish]
---
```

Three things to write on the card's text side come straight out of this page's measurements: (1) the personal-data scan's **scope list** — which types you scanned, which you didn't; (2) the scanner's **calibration result** — your own numbers like 12/12 hold, 9/9 blind spots; (3) the license chain — the base model, every dataset and the attribution file (`Notice`, CC BY-SA source citation). In this example there's also clause `4.b`'s notice: for the distributed derivative, in the documentation **"Built with Qwen" / "Improved using Qwen"**.

## The Pre-Publication Checklist

- [ ] I read the base model's **license text**; I noted the commercial use, naming and attribution conditions.
- [ ] I wrote the license of **every dataset** I used one by one; if any have NC and SA conditions, I reflected them in my output.
- [ ] I didn't define my derivative's license **freer** than the base model's.
- [ ] I opened and looked at the license field inside the quantized/merged files; I checked whether there's template residue (`[year] [fullname]`).
- [ ] I know that if I'm going to a product with a research-licensed base, I need to write to the license holder.
- [ ] I ran the personal-data scan over **all the fields** (instruction + input + output + metadata).
- [ ] I wrote the scanner's scope list: what it scans, what it doesn't.
- [ ] I used a checksum/math filter for TCKN/IBAN; I didn't trust the plain digit pattern.
- [ ] The model card's `license`, `base_model`, `datasets`, `library_name`, `pipeline_tag` and evaluation results are filled.
- [ ] The card's limitations section is honest: how much, in which language, on which task, in which measurement.
- [ ] It's written **with which settings** the evaluation results, if any, were taken (temperature, `num_predict`, seed) — see [Reproducibility](/en/kullanim/tekrarlanabilirlik/).
- [ ] If attribution is mandatory (like CC BY-SA), the source citation exists both on the card and in the output files.
- [ ] If I worked with a mass that could contain personal data: my legal basis, my storage location and my deletion path are written.

## What This Audit Doesn't Show

:::caution[Limits — how to read the numbers]
- **The calibration set was hand-written, a small 30-case sample.** The blind-spot counts show the scanner's *scope*, not its real frequency in Turkish text; no confidence interval was computed (NOT MEASURED).
- **The POSITIVE cases' identity numbers were produced with the checksum function.** So the 12/12 hold rate measures the behavior between the regex and the checksum, not the verifier's own accuracy.
- **The repo scan is specific to this project.** Most of the 48.4 M characters is synthetic/generated text; on a real customer mass the numbers wouldn't come out this clean.
- **The license inventory covers the three models on this machine.** Another tag, another version, another distribution channel may carry a different license field.
- **The external claims are a snapshot.** The HF card fields and license texts were read on October 17, 2026; licenses can change.
- **No legal evaluation was done.** The KVKK article texts weren't verified in this audit; a commercial use plan needs expert opinion.
:::

## Run It on Your Own Machine

```bash
# the license inventory (Ollama must be running; no inference request goes out, only /api/tags + ollama show)
cd ornekler/lisans-ve-gizlilik
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py > cikti/lisans-envanter.txt 2>&1

# the same section's Ollama-less form (only the repo count)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py --depo > cikti/repo-count.txt 2>&1

# the personal-data audit: a=calibration, b=repo scan, c=delimiter deletion
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u pii_denetim.py --kol hepsi > cikti/pii-log.txt 2>&1
```

Both scripts exclude their own folder from the scan: `lisans_envanter.py` because it sees the count keywords in its own list, and `pii_denetim.py` so it doesn't read its own log (half-written at the time of writing) containing synthetic identity numbers. With your own data: add your data directory to the `HEDEF_GRUPLARI` (TARGET_GROUPS) dictionary in `pii_denetim.py`; write your own tail and blind-spot cases into the `--kol a` part. What works as a scope list is which types appear in your own data.

## Sources and further reading

- [The Ollama Modelfile reference](https://docs.ollama.com/modelfile) — how the `LICENSE` field is carried in the package.
- [The Qwen2.5-3B-Instruct card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) and the [LICENSE file](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE) in its repo — the source of the research license we measured.
- [Hugging Face Hub — Model Cards](https://huggingface.co/docs/hub/model-cards) — the official list of the card fields (`license`, `base_model`, `datasets`, `model-index`).
- [Meta Llama 3 Community License](https://github.com/meta-llama/llama3/blob/main/LICENSE) — the 700-million monthly active user threshold, derivative naming and attribution sentence conditions.
- [Gemma Terms of Use](https://ai.google.dev/gemma/terms) — commercial use free, the prohibited-use policy and the agreement being distributed with the copy.
- [Mitchell et al., Model Cards for Model Reporting (arXiv:1810.03993)](https://arxiv.org/abs/1810.03993) — the paper where the card idea emerged.
- [Gebru et al., Datasheets for Datasets (arXiv:1803.09010)](https://arxiv.org/abs/1803.09010) — the dataset card's counterpart: the template for documenting a dataset.
- [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) — Example 6's Wikipedia mass's attribution/derivative condition.
- [The KVKK Authority](https://www.kvkk.gov.tr/) — the official address of personal data legislation.
