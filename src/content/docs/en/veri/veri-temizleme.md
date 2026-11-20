---
title: "Data Cleaning: Quality Data, Good Model"
description: "The steps of making raw data training-ready — normalization, deduplication, quality filtering, personal-data masking and an end-to-end mini cleaning script."
dogrulama: 2026-11-20
---

Most of the time you spend in the training process passes here, and it's worth it: **the model is the mirror of its data.** A model trained on dirty data learns dirty. This page walks through a typical pipeline that turns raw data into training-ready data, step by step.

:::note
The answer to where data is **found** lives on a separate page: [Where to Find Data?](/en/veri/veri-nereden-bulunur/). This page explains what you **do** with the data that lands in your hands.
:::

## The Cleaning Pipeline

```text
Raw data
   ↓ 1. Normalization        (encoding, whitespace, HTML residue)
   ↓ 2. Deduplication        (exact + near duplicates)
   ↓ 3. Quality filtering    (length, meaningless content, spam)
   ↓ 4. Personal data (PII)  (masking name, email, phone)
   ↓ 5. Format conversion    (JSONL / chat format)
   ↓ 6. Verify by eye        (100 examples read by hand — never skipped!)
Training-ready data
```

## 1. Normalization

Reducing the different technical forms of the same text into one form:

- **Unicode normalization (NFC):** merges characters that look the same on screen but differ in bytes. Is `é` one character, or `e` + a combining accent?
- **Whitespace fixes:** multiple spaces, line-ending chaos, leading/trailing whitespace.
- **HTML residue:** cleaning pieces like `<p>`, `&amp;`, `&#39;` (very common in web-sourced data).
- **Encoding errors:** texts that look broken like `Ä°stanbul` ("mojibake"); it comes from reading the source with the wrong encoding.

:::caution[Turkish-specific caution]
In Turkish, the `I→ı` and `İ→i` conversions produce unexpected results in case operations (`"İSTANBUL".lower()` becomes `"i̇stanbul"` in some languages). Remember to test Turkish rules in your normalization script.
:::

```python title="normalize.py"
import re
import unicodedata

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)        # unicode composition
    text = re.sub(r"<[^>]+>", " ", text)             # strip HTML tags
    text = text.replace("&nbsp;", " ").replace("&#39;", "'")
    text = re.sub(r"[ \t]+", " ", text)              # collapse multiple spaces
    text = re.sub(r"\n{3,}", "\n\n", text)           # reduce 3+ empty lines to 2
    return text.strip()
```

## 2. Deduplication

:::note[Why is duplicated data so harmful?]
Three findings point the way. (1) Exact and near-duplicate cleaning reduces the model's verbatim memorization of the training data and improves training ("Deduplicating Training Data Makes Language Models Better", arXiv:2107.06499). (2) This is not a new fad but a classic practice: the C4 corpus was built by dropping extras of repeating three-sentence spans (the T5 paper, arXiv:1910.10683). (3) Repetition isn't unlimited either: with constrained data, repeating the same data for a few rounds (up to ~4 epochs by measurements) gives loss close to training on unique data; beyond that, returns drop fast — repetition is not compensation for missing data ("Scaling Data-Constrained Language Models", arXiv:2305.16264).
:::

Duplicated data pushes the model toward **memorization**: a model that sees the same sentence 50 times assumes it is "valid everywhere". There are two kinds of duplicates:

| Type | What it is | Method |
| --- | --- | --- |
| Exact duplicates | The same text, verbatim copy | Hash comparison (code below) |
| Near duplicates | 90%+ similar, slightly changed | MinHash / LSH (advanced; the `datasets` or `datasketch` library) |

```python title="dedupe.py"
import hashlib

def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

seen = set()
unique = []
for example in examples:                    # examples: a list of dicts
    h = text_hash(example["text"])
    if h not in seen:
        seen.add(h)
        unique.append(example)

print(f"Before: {len(examples)} | After: {len(unique)}")
```

Exact duplicates handled; next comes **near duplication** — examples copied with small changes. A MinHash signature + an LSH index catches likely similar pairs without comparing every example against the whole dataset. We take the signature from 5-word sliding windows (shingles) instead of the full text:

```python title="near_dedupe.py"
from datasketch import MinHash, MinHashLSH

def five_shingles(text: str) -> set[str]:
    """Split the text into 5-word sliding windows (a core robust to small changes)."""
    words = text.split()            # the text must have passed the normalization in section 1
    return {" ".join(words[i : i + 5]) for i in range(len(words) - 4)}

# threshold=0.8: an approximate Jaccard similarity of 80%+ counts as a "duplicate"
lsh = MinHashLSH(threshold=0.8, num_perm=128)
unique_near = []
near_dupes = 0

for i, example in enumerate(unique):        # unique: the list with exact duplicates removed
    shingles = five_shingles(example["text"])
    if len(shingles) < 2:
        unique_near.append(example)        # the signature is meaningless for very short text; pass through
        continue
    mh = MinHash(num_perm=128)
    for s in shingles:
        mh.update(s.encode("utf-8"))
    if lsh.query(mh):                      # if a similar one over the threshold was already added: near duplicate
        near_dupes += 1
        continue
    lsh.insert(f"e{i}", mh)
    unique_near.append(example)

print(f"Removed as near duplicates: {near_dupes} | Remaining: {len(unique_near)}")
```

:::note[Threshold and probability]
With `num_perm=128` you get a balanced precision (as num_perm grows the estimate sharpens and memory grows); these values are verified with datasketch 2.0.0 and current as of 2026. The LSH query is probabilistic: it can miss rare pairs near the threshold. If the decision is critical, verify the exact similarity of suspect pairs with `mh1.jaccard(mh2)`. Calibrate the threshold to your data: if you only want obvious copies, raise it to `threshold=0.9`; 0.80 is balanced for a start.
:::

:::tip
In SFT data, also do the duplicate check **per question**: if the same question has different answers, the model learns contradictions. Adopt the rule "same question → one answer".
:::

## 3. Quality Filtering

Start with rules; when rules aren't enough, continue with your eyes:

- **Length:** drop examples that are very short (<10 characters) or absurdly long.
- **Word variety:** if one word's repetition rate is high (spam/broken collection), drop it.
- **Boilerplate:** patterns repeating on every page like "This site uses cookies", "Comments are closed" — the hidden disease of web data.
- **Language check:** whether the data is really Turkish (matters in mixed sets).

```python title="filter.py"
def is_quality(example: dict) -> bool:
    text = example["text"]
    if len(text) < 20 or len(text) > 8000:
        return False
    words = text.split()
    if len(words) < 5:
        return False
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.3:              # if 70% of the words are the same, suspicious
        return False
    return True

clean = [e for e in unique if is_quality(e)]
```

:::caution[The golden rule]
Look at the filter statistics: **even 1% should be filtered out.** If you see "I dropped 80%", the filter is too aggressive; if you see "0%", the filter isn't working at all. Then always read 100 examples **by eye** — automated checking is never sufficient alone.
:::

## 4. Personal Data (PII) Masking

If the training data contains personal data like names, emails, phone numbers or national IDs, you fall **under KVKK/GDPR**. Detect and mask it (e.g. `[EMAIL]`) before using the data.

```python title="mask_pii.py"
import re

PATTERNS = {
    "[EMAIL]": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "[PHONE]": r"(?:\+90|0)?\s?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}",
    "[TCKN]":  r"\b[1-9]\d{10}\b",
    "[URL]":   r"https?://\S+",
}

def mask(text: str) -> str:
    for label, pattern in PATTERNS.items():
        text = re.sub(pattern, label, text)
    return text
```

:::danger
Simple regexes are only the **first line of defense.** Real names and addresses don't trip regexes. If you're working with sensitive data, use more capable tools (e.g. `presidio`-style PII detection libraries) or, if possible, remove sensitive fields from the dataset entirely.
:::

## 5. Checks Specific to SFT Data

If you're preparing instruction data, additionally look at:

1. **Is the answer correct?** A wrong-answer example teaches the model wrongness. Sample and check by hand.
2. **Are instruction and answer consistent?** If the question asks about "price" and the answer talks about "shipping", the example is garbage.
3. Is there **variety**, or are 500 examples copies of 5 patterns?
4. Is the **system prompt** consistent across examples?
5. Is the **length distribution** natural (are they all 3 lines or all one paragraph)?

We covered the quality-quantity balance on the [Data Types](/en/veri/veri-turleri/) page with the LIMA finding: 1,000 selected examples can beat 100,000 noisy ones.

## The Leakage Check: Training and Test Overlap

**Contamination (leakage)** is test or benchmark examples — or near copies of them — being present in the training data. The result: the model "knows" the answer because it memorized it; the scores you see through [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/) and [Benchmarks](/en/degerlendirme/benchmarklar/) inflate, and the model looks better than it really is. Leakage enters through two doors: benchmark questions may have accidentally mixed into the data you collected from the web; in your own set, synthetic generation may have written a variant of a test-set question into the training side.

The practical check: split test examples into 8-13-word n-grams and see whether these n-grams appear in the training set. n-grams shorter than 8 produce false matches because of common patterns; that's why you shouldn't take the lower bound below 8. Pick out the overlapping test examples — if your test set is small, removing the example from the test rather than from training is more practical.

```python title="leakage_check.py"
def ngram_set(text: str, n: int) -> set[str]:
    words = text.split()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}

def training_ngrams(train_set, n: int = 13) -> set[str]:
    all_ngrams: set[str] = set()
    for example in train_set:
        all_ngrams |= ngram_set(example["question"], n)
        all_ngrams |= ngram_set(example["answer"], n)     # scan both fields
    return all_ngrams

TRAIN_NGRAMS = training_ngrams(train_set, n=13)

clean_test = []
for example in test_set:
    if ngram_set(example["question"], 13) & TRAIN_NGRAMS:
        continue          # overlaps with training: drop from test
    clean_test.append(example)

print(f"Test examples removed due to overlap: {len(test_set) - len(clean_test)}")
```

:::caution[Order matters]
Clean duplicates **first**, then make the train/validation/test split; if two copies of the same example fall one into training and one into test, leakage forms by itself. After splitting too, run this script and scan for overlap — saying "I split it, done" is not enough.
:::

## Language Detection and Mixed Language

In web scrapes and translation-derived sets, even a single example can consist of mixed languages: an English menu residue in the middle of a Turkish page, or machine translation producing "translation-smelling" sentences. Mixed language escapes the quality filter's eye but distorts the model's language distribution. Two practical tools: `langdetect` (easy to install, downloads no model file) and fastText's `lid.176` model (supports 176 languages; the small version `lid.176.ftz` is 917 KB — more accurate, needs a separate download).

:::note[Short-text warning]
Language detection tools misjudge short texts: for inputs like "Yes." or "2026", the result is not trustworthy. Don't run detection standalone on short pieces like titles and table cells; append them to the main text or leave them outside detection.
:::

Practical threshold: split the example into sentences, detect language per sentence and **flag examples where the Turkish-sentence ratio falls below ~90%**; inspect the flagged ones by eye. This ratio is a starting threshold — calibrate it by reading a few dozen examples from your own data.

```python title="lang_detect.py"
import re
from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0      # mandatory for reproducibility: same text, same result

def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"[.!?]+", text)
    return [p.strip() for p in pieces if len(p.strip()) >= 30]   # detection is unreliable on very short sentences

def turkish_ratio(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 1.0            # if there aren't enough sentences to measure, don't touch it
    turkish = 0
    for sentence in sentences:
        try:
            if detect(sentence) == "tr":
                turkish += 1
        except LangDetectException:
            pass              # number/punctuation-heavy sentences can't be detected
    return turkish / len(sentences)

suspects = [e for e in examples if turkish_ratio(e["text"]) < 0.90]
print(f"Mixed-language suspects to inspect by eye: {len(suspects)}")
```

Translation smell is a separate signal: machine translation leaves a verbatim copy of English syntax, overly literal patterns and term inconsistencies; tool signatures like "Powered by ... translation" can also remain in web scrapes. If you can't filter these as rules, at least flag them and read a sample by eye — polished but unnatural translation language teaches the model an unnatural style.

## The End-to-End Mini Pipeline

Let's put the pieces together — a single-file script that reads and cleans JSONL, discards duplicates, filters and prints a summary:

```python title="cleaning_pipeline.py"
import json, hashlib, re, unicodedata

INPUT, OUTPUT = "raw_data.jsonl", "clean_data.jsonl"

def normalize(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def mask(text):
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]", text)
    text = re.sub(r"(?:\+90|0)?\s?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}", "[PHONE]", text)
    return text

counter = {"read": 0, "duplicate": 0, "filtered": 0, "written": 0}
seen = set()

with open(INPUT, encoding="utf-8") as f_in, open(OUTPUT, "w", encoding="utf-8") as f_out:
    for line in f_in:
        counter["read"] += 1
        example = json.loads(line)
        for message in example["messages"]:
            message["content"] = mask(normalize(message["content"]))
        key = hashlib.sha256(
            json.dumps(example, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        if key in seen:
            counter["duplicate"] += 1
            continue
        seen.add(key)
        total_length = sum(len(m["content"]) for m in example["messages"])
        if total_length < 30 or total_length > 12000:
            counter["filtered"] += 1
            continue
        f_out.write(json.dumps(example, ensure_ascii=False) + "\n")
        counter["written"] += 1

print(counter)
```

Read the output: can you explain the **reason** for the gap between `read` and `written`? If there's a drop you can't explain, one of the filters is too aggressive.

## The Cleaning Report Card: Don't Say "Done" Without Measuring

The `counter` dictionary in the end-to-end script holds the core of the job: `read`, `duplicate`, `filtered`, `written`. But to say "done" you must pour these numbers into a **report card**. Fill in and attach this table to your training report — three months later, the answer to "where did this data come from, what did I filter?" is in the archive:

| Stage | Example count | Reason (short note) |
| --- | --- | --- |
| Read (raw) | — | number of lines in the raw file |
| Exact duplicates (removed) | — | hash matches |
| Near duplicates (removed) | — | MinHash/LSH, threshold 0.80 |
| Quality filter (removed) | — | write the per-rule breakdown too |
| PII-masked examples | — | masking doesn't remove; don't expect a drop on this line |
| Training set | — | |
| Validation + test set | — | overlap scan against training was done |

Fill the table by hand (replace "—" with your own numbers); if you like, add each line's ratio to the line above. The critical question on the report card is this: **can you explain, line by line, the gap between `read` and the number entering training?** Every gap you can't explain may be the sign of an invisible filter — or an invisible error.

## The Cleaning Checklist

- [ ] Encoding and Turkish characters look correct
- [ ] Exact duplicates removed
- [ ] Length and word-variety filters applied
- [ ] Personal data masked (or removed)
- [ ] Format compatible with the schema the tool expects ([Data Formats](/en/veri/veri-formatlari/))
- [ ] Train/validation split made, no leakage
- [ ] 100 examples read by eye and noted

:::tip[The last step]
When cleaning is done, you should be able to answer one "why" question: **"What is this data for teaching my model?"** If the answer is clear, it's training-ready; if it's murky, go back to the [Create Your Own Dataset](/en/veri/kendi-verini-olustur/) page and clarify the scope.
:::

## Sources and Further Reading

- [Deduplicating Training Data Makes Language Models Better (arXiv:2107.06499)](https://arxiv.org/abs/2107.06499) — the foundational study showing exact and near-duplicate cleaning reduces memorization and improves training (Lee et al., ACL 2022).
- [Exploring the Limits of Transfer Learning (T5/C4, arXiv:1910.10683)](https://arxiv.org/abs/1910.10683) — the classic source on how the C4 corpus cleaned repeating three-sentence spans (Raffel et al., 2019).
- [Scaling Data-Constrained Language Models (arXiv:2305.16264)](https://arxiv.org/abs/2305.16264) — the study measuring the limit of repetition under data constraint: repetition up to ~4 epochs is harmless, returns drop beyond (Muennighoff et al., 2023).
- [datasketch (GitHub)](https://github.com/ekzhu/datasketch) — a Python library for MinHash, LSH and similar probabilistic data structures; the example on this page is compatible with version 2.0.0 as of 2026.
- [Presidio (GitHub)](https://github.com/data-privacy-stack/presidio) — a PII detection and masking framework; as of 2026 it is maintained by the data-privacy-stack community (the old `microsoft/presidio` address redirects here).
