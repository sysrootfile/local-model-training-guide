---
title: "Inference Parameters: Changing Behavior Without Touching the Weights"
description: "Temperature, top-k, top-p, min-p, seed, num_predict and stop: where these settings come from in Ollama, how they shape the generation distribution, and why the docs' defaults must be verified on your own machine."
dogrulama: 2026-11-20
---

Training is done, the weights are fixed. You ask the same question twice; one answer comes out a crisp sentence, the other a sprawling paragraph. The model didn't change. What changed is **how the next token was picked** from its probability distribution. This page explains the knobs governing that pick, where they come from in Ollama, and what each one cuts in production.

:::note[No new measurement on this page]
The numbers here have two sources: Ollama's official Modelfile and API docs (**last verified 2026-10-17**) and metadata genuinely read from the model file on this machine. This page doesn't measure the knobs' effect on behavior; that measurement now exists: the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page ran the same prompts ten times each and gives the answer, with numbers, to the three places I say "not measured" below. The other measured pages are [Speed and Cost](/en/kullanim/hiz-ve-maliyet/), [Agent Measurement](/en/ajan/ajan-olcumu/) and [Injection Measurement](/en/ajan/enjeksiyon-olcumu/). I also give, line by line, how to check every default I quote from the docs on your own machine — because as you'll see below, **two documents write two different defaults for the same parameter.**
:::

## Where Does a Setting Come From: Four Layers

To understand what a value actually is, four places are looked at in order:

1. **Ollama's own defaults.** The values used if you write nothing; the table below.
2. **The model file's embedded metadata (the GGUF header).** Converters can bake sampling settings into the model.
3. **The `PARAMETER` lines in the Modelfile.** The lines you write when setting up your own model with `ollama create` (the Modelfile example on the [Ollama page](/en/kullanim/ollama/)).
4. **The `options` object in the request body.** The most portable and most temporary layer: whatever your script sends is what counts.

The command for checking the first two layers was actually run on this machine.

```shell
ollama show --modelfile qwen2.5:3b-instruct-q4_K_M
```

The output has `FROM`, `TEMPLATE` and `LICENSE` blocks, and **no `PARAMETER` line**. So this model imposes no sampling setting on Ollama; the effective values are Ollama's own defaults. The same model's GGUF header is a second check: the `scripts/gguf-baslik.py` script prints only the header metadata without loading the file into memory.

```text
GGUF version 3 | tensors 434 | metadata keys 35
  qwen2.context_length                     32768
  qwen2.rope.freq_base                     1000000.0
  tokenizer.ggml.eos_token_id              151645
  tokenizer.ggml.padding_token_id          151643
  tokenizer.ggml.bos_token_id              151643
  tokenizer.ggml.add_bos_token             False
```

Two questions close with two commands: is a sampling setting embedded in the file, and what strings do these three token numbers really correspond to?

```shell
python scripts/gguf-baslik.py "<blob file>" "sampl|penal"
python scripts/gguf-baslik.py "<blob file>" 151643 151644 151645
```

```text
  (no matching key)
  token 151643  ->  (the old marker used as padding and beginning-of-text)
  token 151644  ->  (the template marker opening a chat message)
  token 151645  ->  (the marker ending a chat message; registered as EOS)
```

When the script sees a number it also decodes and prints the token string; the parentheticals here are a summary, the real output is the string itself. None of the 35 keys carries a `general.sampling` or similar sampling field: **no sampling setting is embedded in this model**, the effective values are Ollama's own defaults. The `add_bos_token: False` line is part of the same reading; since no beginning marker is added, the difference between the chat template and `raw` mode stays with the strings you send.

The script reads the blob file shown by the `FROM` line in the `ollama show --modelfile` output and decodes only the header: under a second for a 1.9 GB file. If it prints a sampling key on your own model (e.g. `general.sampling.temperature`), that value is embedded; rather than guessing which layer wins, check with a single request.

## The Documented Defaults

| Setting | Documented default | What it does |
| --- | --- | --- |
| `temperature` | 0.8 | Divides the logits; softens or sharpens the distribution |
| `top_k` | 40 | Keeps only the 40 most likely candidates |
| `top_p` | 0.9 | Holds candidates in descending order until probabilities sum to 0.9 |
| `min_p` | 0.0 | Eliminates candidates lighter than a tenth of the most likely one |
| `seed` | 0 | Pins the sampling chain |
| `num_predict` | -1 | The most tokens to generate; -1 means "let the model finish itself" |
| `num_ctx` | 2048 | The context window; the server sets this dynamically per your machine's memory |
| `repeat_last_n` | 64 | The number of trailing tokens the repeat penalty looks at |
| `repeat_penalty` | 1.0 | The penalty on a token repeating in that window |
| `stop` | undefined | Stops when one of these strings is generated |

:::caution[Two documents, two different defaults]
The table above comes from the docs.ollama.com/modelfile page. The readthedocs copy, the English mirror of the Ollama docs, writes other values on the same two lines: `repeat_penalty` **1.1**, `num_predict` **128**; its table also has `mirostat` (0), `mirostat_tau` (5.0), `mirostat_eta` (0.1), `tfs_z` (1) rows — none of which appear in the docs.ollama.com table. This conflict was closed by measuring on this machine: in the K0 arm on the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page `num_predict` was **never sent**, and generation ran between 1060 and 1460 tokens, with all three requests ending in `stop`. So on Ollama 0.40.4 (the machine's server moved to 0.40.6 on 2026-10-19; this behavior wasn't re-tested on that version) neither document is in force; the ceiling effectively doesn't exist. The cost of the check on your own version is again a single request.
:::

The `num_ctx` row is a separate confusion: the Modelfile doc writes 2048, but Ollama's runtime raises it automatically if your memory is big (thresholds and measurements on the [Ollama page](/en/kullanim/ollama/) and [Speed and Cost](/en/kullanim/hiz-ve-maliyet/)). The measured proof of silently truncating the context is there: with `num_ctx` 512, 430 of a 688-token prompt were never read, and there was no warning in the response.

## Five Truncation Knobs, One Distribution

Say the six candidates' logits for the next token are 6, 5, 4, 3, 2, 1. The probabilities below were computed **by hand** from softmax; not a real model's distribution, an illustration.

| `temperature` | most likely candidate | how many candidates `top_p` 0.9 keeps | how many candidates `min_p` 0.1 keeps |
| --- | --- | --- | --- |
| 0.3 | 0.964 | 1 | 1 |
| 0.8 | 0.714 | 2 | 2 |
| 1.5 | 0.496 | 4 | 4 |

What the three cuts cut is different, and this table exists for that:

- **`top_k` fixes the count.** It says "the 40 most likely candidates" without looking at the probability sum. While the distribution is sharp (low temperature), 39 of those 40 are already negligible probability and the cut has no effect; while the distribution is flat, the 40 fill with real candidates and the chance of a wrong pick rises.
- **`top_p` fixes the sum.** It lines up candidates in descending order and discards the rest once the cumulative sum reaches 0.9. The set's size varies with the distribution: 1, 2, 4 candidates in the rows above.
- **`min_p` sets a relative threshold.** "Have at least a tenth of the most likely candidate's probability." The tail is **affected** by temperature in shape — so `min_p` doesn't suppress `temperature`'s effect; at low temperature the cut hardens by itself, which is what the table shows.

Ollama's docs don't define the order these three apply in; this page makes no order claim. The practical result: their effects alone matter more than their order.

## Where Generation Ends: `num_predict`, `stop`, EOS

Generation has three ways of ending, and all three look different in the response.

| Ending | What shows in the response | Meaning |
| --- | --- | --- |
| The model ends itself | `done_reason: stop` | EOS or a `stop` string was generated; the answer is complete |
| It hits the length limit | `done_reason: length` | `num_predict` ran out; the answer is **cut mid-sentence** |
| The answer comes back empty | `done_reason: stop`, empty content | a template/application mismatch; filter empty content before showing it to the user |

The second row is local setups' most common silent failure. It genuinely happened on the [Agent Measurement](/en/ajan/ajan-olcumu/) page: an answer stuck at the `num_predict: 300` limit ended mid-sentence, returned HTTP 200, and there was no error in the log. The [Injection Measurement](/en/ajan/enjeksiyon-olcumu/) record also shows cut (`length`) and complete (`stop`) endings together. If your monitoring doesn't look at the `done_reason` field, the "half answer" comes back as a user complaint.

The third row's scale matters: `num_predict` counts **tokens**, not words. Turkish text produces ~2.99 characters/token — [a ratio measured on the Speed and Cost page](/en/kullanim/hiz-ve-maliyet/). Back-of-envelope: `num_predict: 40` in Turkish is roughly 24 words, a sentence or two. If you want long answers, raise the limit; if you want them shorter, account for the limit working in tokens, not words.

:::tip[Structure instead of cutting the long answer]
Rather than saying "write long", say "write three bullets" and do the enforcement in the prompt; then open `num_predict` with a buffer for that form (e.g. twice the expectation). The only thing distinguishing a cut answer from a complete one is `done_reason`.
:::

## Temperature 0: Is "Same Input, Same Output" a Guarantee?

`temperature: 0` doesn't sample the distribution; it picks the most likely candidate at every step (greedy generation). That's the justification for comparison pages keeping the temperature at zero: the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/), [Agent Measurement](/en/ajan/ajan-olcumu/) and [Injection Measurement](/en/ajan/enjeksiyon-olcumu/) runs all ran with `temperature: 0` and an explicit `num_predict`; that's the way to separate the difference between two measurements from sampling noise.

A guarantee? There's now a measured answer, and the answer varies by generation length. On the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page the same prompt ran ten times each: on the 5-token short answer, temperature zero, **without a seed sent**, all twenty of twenty requests produced a character-identical string; and in the 68-token free generation the seed-pinned answer stayed verbatim identical across two separate days. But in three 1,000+-token long generations made without sending `num_predict`, the same temperature zero and same prompt gave **different lengths** (1060, 1460, 1460 tokens). So the "temperature 0 suffices" rule held on this machine for short output, and didn't hold for long output; the arm that would distinguish the cause wasn't measured. That's the reason every measurement page sends an **explicit** `num_predict` alongside `temperature: 0`.

## Structured Output: the `format` Field

In Ollama's API docs the `format` field accepts two things: `"json"` or directly a **JSON schema**. The second serves you better than the first, because "valid JSON" and "your fields" aren't the same thing.

```python
request = {
    "model": "qwen2.5:3b-instruct-q4_K_M",
    "messages": [{"role": "user", "content": question}],
    "format": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "has_source": {"type": "boolean"},
        },
        "required": ["answer", "has_source"],
        "additionalProperties": False,
    },
    "stream": False,
    "options": {"temperature": 0, "num_predict": 200},
}
```

This page didn't run the schema itself; the body shape is from the [Ollama API docs](https://docs.ollama.com/api/chat), the field names taken from there. The same body shape was genuinely run, ten repeats, in arm D of the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page: the difference between `"json"` and the schema was measured, and it was seen how the token ceiling breaks the JSON. On an OpenAI-compatible server the same intent lands in the `response_format` field, and server-side in the parser that truly enforces the schema — the comparison is on the [API Serving page](/en/kullanim/sunma-api/).

:::caution[The schema guarantees the shape, not the content]
`format` protects you from malformed output — unparsable output, a missing field; it doesn't protect you from a fabricated value. Two measured examples: in arm D of the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page the ten schema-generated answers' field names were identical in all ten (`year`, `reason`), but the `year` value spread across **four different years** in ten requests. Second, in scenario C on the [Agent Measurement](/en/ajan/ajan-olcumu/) page the wrong tool was called and the model produced the **"3600 meters"** number that exists nowhere in the result. The shape was right, the content wrong. For the same reason, a validation layer for tool arguments is separate from the schema; the reaction to a malicious document is on the [Prompt Injection page](/en/ajan/prompt-enjeksiyonu/).
:::

The `think` field, in the same docs, is the on/off control of the "reasoning" section on supporting models; not measured on this site, because the Qwen2.5 model running here has no thinking mode. `logprobs` and `top_logprobs`, meanwhile, are now measured: the [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) page showed, run by run, what these two fields actually return in Ollama, that the `top_logprobs` ceiling is 20, and that when `logprobs` isn't sent, `top_logprobs` is **silently ignored**.

## The Seed: `seed`

`seed` pins the sampling chain's start; in every run where the temperature is **other than zero**, this is the only cure for reproducibility. The documented default is 0. Two cautions:

- The same seed is meaningful together with the same **prompt**. If the prompt changes by even one token (if a different piece entered the context in RAG), the sampling chain continues from another step even though the seed is the same; assuming a fixed seed means "the same result" is the most common mistake made when comparing two runs. How much the context itself wobbles is a measured subject: on the [Chunking and Hybrid Search](/en/rag/parcalama-ve-hibrit-arama/) page vector retrieval dropped the expected piece to **14th place** on one question, i.e. outside the `k=4` context window.
- The seed's **value** and its **effect** are different things. Its measured form: on the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page at temperature 0.8, seed 1234 and seed 9999 gave the same answer (all twenty of twenty requests the same string), while the same setting seedless spread across five different answers in ten requests. The seed pins the chain; which answer you land on stays with the distribution itself.
- Give the seed alongside the result when reporting. The fifth item on the [Benchmarks](/en/degerlendirme/benchmarklar/) page touches the same point: if sampling settings aren't pinned, the same model looks like two.

## The Practical Decision List

- If you're measuring/comparing: `temperature: 0`, an explicit `num_predict`, a fixed `seed`, a fixed model tag, a fixed `num_ctx`. Why all of them: on the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page temperature zero alone didn't preserve identity on long generation, and without an explicit ceiling sent, generation ran up to 1460 tokens.
- If you want creativity: keep the temperature in the 0.8-1.1 band and play with `top_p`; if your candidate set is already cut below 40, growing `top_k` has no benefit.
- Machine-to-machine portability: don't trust the `PARAMETER` lines, send the value in the request.
- Application outputs: a JSON schema **and** field validation; a `done_reason` check; an empty-content warning.
- Learning your own machine's effective default: `ollama show --modelfile`, and if needed `scripts/gguf-baslik.py`.

## Sources and further reading

- [The Ollama Modelfile reference](https://docs.ollama.com/modelfile/) — the `PARAMETER` names and default table; the 0.8 / 40 / 0.9 / 0.0 values here were taken from it (last verified 2026-10-17).
- [The Ollama Modelfile mirror (readthedocs)](https://ollama.readthedocs.io/en/modelfile/) — the copy of the same table writing `repeat_penalty` 1.1, `num_predict` 128 and containing `mirostat`/`tfs_z` rows; the proof of where the two docs disagree.
- [The Ollama API reference](https://docs.ollama.com/api/chat/) — the shape of the `format`, `think`, `keep_alive`, `logprobs` fields.
- [Confidence and Calibration](/en/kullanim/eminlik-ve-kalibrasyon/) — the measured behavior of the `logprobs` and `top_logprobs` fields on this machine; where the debt this page left as "not measured" was paid off.
- [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) — the `num_ctx` truncation, the Turkish characters/token ratio and the phase times; the measured source of this page's citations.
- [Reproducibility](/en/kullanim/tekrarlanabilirlik/) — the ten-repeat measurement of the three claims this page left as "not measured" (the default `num_predict`, the temperature-0 guarantee, the `"json"` vs schema difference).
- [Agent Measurement](/en/ajan/ajan-olcumu/) — the real record of the answer cut with `done_reason: length` and of the fabricated tool argument.
- [Tokenization](/en/temeller/tokenizasyon/) — the linguistic reason Turkish text eats more tokens.
