---
title: "Reproducibility: Asking the Same Question Ten Times"
description: "Same prompt, same model, same machine: is the answer verbatim identical at temperature zero and a fixed seed, how many tokens is the ceiling if num_predict isn't sent, which field names the JSON schema enforces, how big seed variance is in scikit-learn — numbers measured from the 2026-10-17 record."
dogrulama: 2026-11-20
---

The word "repeatable" carries two separate claims: **if I resend the same request, do I get the same answer** and **can I compare today's result with tomorrow's run**. The second depends on the first, but the two aren't the same thing. This page answers four questions by genuinely running them on this machine: the actual effect of temperature and seed in Ollama, the ceiling in force when `num_predict` isn't sent, what the `format` field really enforces, and — as a control arm — the magnitude of seed variance in scikit-learn.

:::note[The credentials: one run, one machine]
The script: `ornekler/tekrarlanabilirlik/tekrar.py`. The record: `ornekler/tekrarlanabilirlik/cikti/tekrar-log.txt`.
The run window was **2026-10-17 11:04:59 → 11:14:18** (9 minutes 19 seconds), Ollama 0.40.4 (the machine moved to 0.40.6 on 2026-10-19; the numbers on this page weren't re-measured on that version), the model `qwen2.5:3b-instruct-q4_K_M`, the address `http://127.0.0.1:11434`. **123 requests** to Ollama (3 of them ceiling probes, 120 of them 12 cells with ten repeats each), and 30 training-accuracy pairs on the scikit-learn side. The model runs on CPU on this machine; that line isn't a new measurement, it's carried over from the `ollama ps` "100% CPU" record on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page. No other Ollama request was sent during the run.
Every number below was taken from that file; every cell I quote (A1, D3, B2 etc.) has the same label in the record.
:::

## The Same Prompt, Temperature Zero, No Seed: The Short Answer Is Verbatim Identical

A closed-ended question and a one-word instruction: "In which year did Marmaray enter service? Your answer must be one word." Ten repeats, six setting combinations. Every answer is 5 tokens; the differences are in the text itself.

| Cell | Setting | Unique answers in 10 repeats | The most common answer's rate | Years produced |
| --- | --- | --- | --- | --- |
| `A1` | T=0, no seed | 1 | 10/10 | 2020 |
| `A2` | T=0, seed 1234 | 1 | 10/10 | 2020 |
| `A3` | T=0.8, no seed | 5 | 3/10 | 2021 three, 2020 three, 2011 two, 2013 one, 2015 one |
| `A4` | T=0.8, seed 1234 | 1 | 10/10 | 2020 |
| `A5` | A4's repeat on a separate day | 1 | 10/10 | 2020 |
| `A6` | T=0.8, seed 9999 | 1 | 10/10 | 2020 |

Three things were measured:

- **Temperature zero gave verbatim identity on five-token generation** — even without a seed sent (A1, A2). That was the claim I left as "not measured" on the [Inference Parameters](/en/kullanim/cikarim-parametreleri/) page; on short output it holds on this machine.
- **The seed brings identity back at a non-zero temperature**: A3 spread across five different years as it sampled; A4 and A5 ran with the same seed on two separate days, and all twenty of twenty requests gave the same string.
- **The seed's *value* doesn't determine the answer**: 1234 and 9999 (A4, A6) landed on the same answer. The seed pins the sampling chain; which chain lands on which answer isn't pinned. Two different seeds giving the same result is no surprise — it's the natural consequence of the distribution being peaked, as seen in A3.

One caveat: this table **didn't measure accuracy.** Five different years came out of ten requests; which is correct, this rig doesn't test. What we measured is reproducibility.

## The Open-Ended Prompt: The Seed Pins Even a 68-Token Answer

The same rig's second arm, a prompt asking for free generation: "Suggest three slogans for a coffee shop in Kadıköy." `num_predict` 200.

| Cell | Setting | Unique | Most common | Output tokens (avg.) | Character range | Wall (10 requests) |
| --- | --- | --- | --- | --- | --- | --- |
| `C1` | T=0.8, no seed | 10/10 | 1/10 | 54.7 | 91-142 | 37.0 s |
| `C2` | T=0.8, seed 1234 | 1/10 | 10/10 | 68.0 | 146 | 45.4 s |
| `C3` | C2's repeat on a separate day | 1/10 | 10/10 | 68.0 | 146 | 45.0 s |

The seed worked here too: a 68-token, 146-character generation was character-identical in ten of ten requests; the second day (C3) gave the same signature. In the seedless arm (C1), **one of the ten answers differed from the other nine** — not even a single repeat came out, while the average length settled at 54.7 tokens.

:::note[Sampling noise hits the language itself]
In C1's fourth request, one of the three slogans came not in Turkish but in **Chinese** ("每一杯都是对生活的敬意"). The prompt is entirely Turkish, the model the same, the settings the same; in one of ten trials the language slipped. This is this machine's measurement that the assumption "the answer always comes in the prompt's language" doesn't hold at temperature 0.8. No such slip was seen in this rig at temperature zero or with a fixed seed — but that's not a guarantee preventing it, only an observation.
:::

## If You Don't Send `num_predict`, What's the Ceiling: Not 128

On the [Inference Parameters](/en/kullanim/cikarim-parametreleri/) page we saw the two Ollama docs writing two different defaults for the same parameter: `docs.ollama.com` says **-1**, the readthedocs mirror says **128**. I'd said the closure method is "fire one request". The run sent `options = {temperature: 0}`, **never sent `num_predict`**, and repeated the same long-writing prompt three times:

```text
K0.1: wall  80.58 s | output tokens 1060 | ending stop
K0.2: wall 111.88 s | output tokens 1460 | ending stop
K0.3: wall 111.79 s | output tokens 1460 | ending stop
```

The result is two-sided:

1. **128 isn't in force.** 1060 and 1460 tokens were generated, all three have `done_reason: stop`, i.e. it isn't a truncation but the model's own ending. On this version (Ollama 0.40.4), not sending `num_predict` doesn't stop generation at all; generation continues until the model produces EOS. If you want a ceiling in your application, **you must send it.**
## `format`: The Difference Between "json" and the Schema, Measured

The same question, the same temperature, no seed; the only thing changing is the `format` field in the request. The schema wants two fields: `year` (a number) and `reason` (text). Ten repeats each:

| Cell | `format` | `num_predict` | Parseable | How many variants the second field's name had | `year` values |
| --- | --- | --- | --- | --- | --- |
| `D1` | `"json"` | 300 | 10/10 | **4** (`gercekce`, `gereken`, `gereke`, `gerekce`) | 2011, 2020, 2022, 2023 |
| `D2` | JSON schema | 300 | 10/10 | **1** (`reason`) | 2017, 2019, 2020, 2022 |
| `D3` | JSON schema | 48 | **2/10** | 8 requests cut mid-sentence | 2022 and the cut ones |

These three rows close, with numbers, the two claims left unrun on the [Inference Parameters](/en/kullanim/cikarim-parametreleri/) page:

- **`"json"` only guarantees valid JSON, not your fields.** All ten of the ten requests parsed; but the model wrote the second field under four different names. Code trying to read it with `data["reason"]` would get a `KeyError` on four of the ten answers. The schema (D2) held the field names fully: ten out of ten `reason` + `year`.
- **The schema guarantees the shape, not the content.** In D2 the field names were flawless while the `year` value spread across four different years in ten requests — and a completely different four years than D1's. Shape checking (the schema) and fact checking (a validation layer) are separate jobs; the schema doesn't do the latter.
- **The token ceiling breaks the JSON.** The only change in D3 was lowering `num_predict` to 48: eight of ten requests were cut with `done_reason: length`, and the cut JSON didn't pass `json.loads`. Server-side schema enforcement **doesn't prevent** this truncation that invalidates the output: HTTP 200, fields right, answer unparsable. If you want structured output, open the ceiling according to the schema's real length and check the `done_reason` field.

:::caution[Cut JSON is a silent failure]
None of D3's eight broken answers had an error: status code 200, the content field full, `done_reason` saying truncation. The only way to tell is looking at the `done_reason` field — or trying to parse and running the "answer incomplete" branch on failure. The cut answer on the [Agent Measurement](/en/ajan/ajan-olcumu/) page and the `length` endings in the [Injection Measurement](/en/ajan/enjeksiyon-olcumu/) record are other contexts of the same failure.
:::

## The Control Arm: Seed Variance in scikit-learn

The wobbling on the generation side alone doesn't answer the question "is it natural noise?". In the same rig's second arm, in a classic machine-learning flow considered deterministic (the breast-cancer data, 569 rows, a 20% stratified split, 114 test rows), 30 training-accuracy pairs ran with five seeds. Three scenarios: what was seeded was deliberately varied.

| Arm | What changed | Random forest accuracy | Range | Logistic regression | Range |
| --- | --- | --- | --- | --- | --- |
| `B1` | split + model seed together | 0.9474-0.9825 | **0.0351** | 0.9649-0.9912 | 0.0263 |
| `B2` | split fixed (42), only the model seed | 0.9474-0.9561 | **0.0088** | 0.9825 (five of five identical) | **0.0000** |
| `B3` | model seed fixed (42), only the split | 0.9386-0.9825 | **0.0439** | 0.9649-0.9912 | 0.0263 |

The measured ranking is clear: **the test split's choice wobbles more than the model seed** (B3's spread 0.0439 vs B2's 0.0088). B2's 0.0088 is exactly one test example: 1/114 = 0.00877. Logistic regression, meanwhile, stayed the same to four decimal places across five seeds with the split fixed (0.9825); on this data the model seed doesn't wobble it at all — indeed B1 and B3's logistic rows are identical.

The lesson here carries to the LLM side: **an unknown-source wobble becomes a known-size wobble.** In an environment where seed variance can reach 0.04 accuracy even in a classic machine-learning flow, comparing two runs of a language model whose temperature isn't explicitly pinned isn't a measurement. The "don't trust a single run" item on the [Hyperparameters](/en/llm/hiperparametreler/) page gives the justification of this math, and the fifth item on the [Benchmarks](/en/degerlendirme/benchmarklar/) page the reporting side.

## What This Measurement Doesn't Show

:::caution[Limits — how to read the numbers]
- **One machine, one model, one version.** Ollama 0.40.4 and `qwen2.5:3b-instruct-q4_K_M`, on CPU. In a GPU setup, when batching genuinely kicks in, the identity behavior may change; not tested here.
- **Identity on short output, non-identity on long output is an observation; not a rule.** I didn't build an arm that would distinguish the cause of the 1060/1460 difference in K0. The claim "temperature 0 + fixed prompt = guaranteed identical output" was **not verified** on this page; it was only observed in the two cases of 5 tokens and 68 tokens.
- **Ten repeats is a small sample.** The "5 unique" rate in A3 isn't the distribution's true measure; no confidence interval was computed (NOT MEASURED).
- **Accuracy wasn't measured.** Which of the years is right isn't the discussion here; this page only counted how many different answers were given to the same question.
- **The scikit-learn arm is on one dataset.** 569 rows, 30 features, one split ratio; the ranking may change on another dataset.
:::

## The Practical Decision List

- If you're measuring/comparing: `temperature: 0`, an explicit `num_predict` and a fixed `seed` together. On long generation, temperature zero alone didn't preserve identity (K0), and without `num_predict` sent, generation ran up to 1460 tokens; this trio is used together on all the measurement pages.
- If your application asks the same question over and over and you don't want answer variety: send a seed. Remember the seed pins nothing if the prompt changes by even one token; if the context piece changes in RAG, you're not making a comparison.
- If you want structured output: send a **schema**, not `"json"`, open the ceiling according to the schema's real length, check `done_reason`, and validate the field values separately.
- For a one-page improvement claim: at least five repeats, two separate days if possible. The A4/A5 and C2/C3 pairs in this rig were built for that; a second day giving the same signature as the first under the same setting shows the reproducibility proof should be "two days", not "one day".
- On suspicion of an unknown-source wobble: measure the wobble's size. The B2/B3 distinction is its classic machine-learning form.

## Run It on Your Own Machine

The rig is a single file; `--duman` (smoke) is a quick two-repeat verification, the full ten-repeat run ~9 minutes (longer if the Ollama arm is slow on CPU).

```bash
cd ornekler/tekrarlanabilirlik
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol a --duman > cikti/duman.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol hepsi > cikti/tekrar-log.txt 2>&1
```

Until the run finishes, send no other Ollama request — no chat interface, no editor extension, no second script. The cell pairings (two separate days like A4/A5) depend on this rule. The script talks only to `127.0.0.1:11434`; by changing the model name, the prompts and the `--kol` (arm) choice you can build the same table with your own questions.

## Sources and further reading

- `ornekler/tekrarlanabilirlik/cikti/tekrar-log.txt` — the raw record of all the numbers on this page (123 requests, 30 sklearn runs, 2026-10-17 11:04-11:14).
- [Inference Parameters](/en/kullanim/cikarim-parametreleri/) — the doc-based explanation of temperature, top-k, top-p, min-p, seed and the `format` fields; this page measures the three claims it left unrun.
- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — the phase times measured on the same machine, the `num_ctx` truncation and the 10% speed wobble between two runs.
- [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) — the run seeking identity in **numbers** rather than text: the measurement that at temperature zero the logprobs came back bit-identical, but when the model was dropped with `keep_alive: 0` and reloaded, the same tokens' probabilities could shift by 0.2286.
- [Agent Measurement](/en/ajan/ajan-olcumu/) and [Injection Measurement](/en/ajan/enjeksiyon-olcumu/) — the real records of answers cut with `done_reason: length`.
- [Hyperparameters](/en/llm/hiperparametreler/) — the classic reference on seed variance in fine-tuning (Dodge et al., arXiv:2002.06305).
- [Classic Machine Learning: Your First Model](/en/klasik-ml/ilk-model/) — the example flow of using `random_state`; arm B was built on the same data and pipeline.
- [Training an Embedding Model](/en/rag/gomme-egitimi/) — the **training** side of the same seed question: in two 240-step arms run with two different seeds, hit@1 and MRR stayed exactly the same, with the step time only wobbling 1.33 vs 1.35 s.
