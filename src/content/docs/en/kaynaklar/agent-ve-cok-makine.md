---
title: "Replicating This Guide on Another Machine with an Agent"
description: "A step-by-step guide to setting up and running the guide's measurement rigs on a second machine and with a code agent: setup, the smoke-first protocol, window hygiene, the contamination audit, the record discipline and the machine credentials. Which tier your own numbers will stand at."
dogrulama: 2026-11-20
---

Every measurement in this guide came from a single machine and the pages say so openly: the absolute numbers (Ryzen 5 2600, 15.9 GB RAM, CPU) **will come out different** on your hardware; the claim the pages carry is the pattern, not the seconds. There are two honest answers to the question "what happens on my machine?": running the scripts yourself, or having a code agent set them up and run them. Both demand the same discipline — this page is that discipline's setup and run instructions. The contract's site summary is at [The Verification Mechanism](/en/kaynaklar/dogrulama-mekanizmasi/) and the [Scope Map](/en/kaynaklar/kapsam-haritasi/); the full text is the AGENT.md file in the repo.

## The setup (a human and an agent follow the same order)

1. **Take the repo:** `git clone <repo-address>`; the measurement rigs are independent of the site build, and every folder under `ornekler/` comes with its own README.
2. **A single shared virtual environment:** `python -m venv .venv` at the repo root — no per-folder environments; the rigs are called relative to `.venv` (`../../.venv/Scripts/python.exe`, or `../../.venv/bin/python` on Linux/macOS).
3. **The packages:** `pip install pandas scikit-learn joblib` (klasik-ml) and `pip install datasets ftfy datasketch` (veri-temizleme); most measurement rigs ask only for the standard library (each rig's README carries its own list).
4. **Ollama + models:** install [Ollama](https://docs.ollama.com/); `ollama pull qwen2.5:3b-instruct-q4_K_M` and `ollama pull bge-m3`. The server must be listening at `127.0.0.1:11434` — the rigs don't connect to any other address (the `_url_dogrula` guard allows only the permitted hostnames).
5. **Turkish output:** on Windows `PYTHONUTF8=1` is mandatory; the run outputs are written to files with `> cikti/<record>.txt 2>&1`.

## The agent-specific rules (distilled from AGENT.md)

- **Smoke first, the full run after.** One arm, one repeat: is the script producing a record end to end? The full run doesn't start before the smoke passes. In rigs without a smoke mode, the shortest argument combination is used and the record is labeled "smoke".
- **A number comes only from a finished log.** While the run is going, status can be said, results can't; a half log isn't published.
- **Intervening in the server is the machine owner's.** Writing environment variables like `OLLAMA_NUM_PARALLEL` and restarting Ollama aren't the agent's job; the agent only runs the script and reads the value from `server.log` (the `server config` line + the `llama-server … -np N` command line).
- **Window hygiene.** No other request goes to the server during the measurement window. On this machine the most common contaminator class is the embedding requests of IDE/integration tools running in the background — if a second model like bge-m3 loads by itself within a window, there's a contaminator.
- **The contamination audit right after the run.** Every new-prompt line not matching the rig's prompt signature is either foreign or the script's own eviction call; if the distribution doesn't match the signature, the run is eliminated. Command: `python ozetle.py --kirletme "<server.log>" --istem <prompt-tokens> --pencere <start>-<end>`.
- **20 minutes per arm, 45 minutes per day** is the local CPU ceiling — the ceiling's real price isn't the measurement but the machine being closed to other work for that duration.
- **The version credentials.** Ollama updates fast; each record's server version is read from the log and written beside the record. Two versions' numbers aren't put side by side.
- **Script comments ASCII**, the page text Turkish; decimal comma, thousands period.

## What will differ on a new machine

- **The numbers.** All of them. The same script, the same model, a different CPU: a single request's tok/s, the wave walls, the memory steps — all are your hardware's numbers. Make the comparison with this guide's pages at the **pattern level** (is there a staircase? a lock-step? a queue or sharing?); a seconds comparison isn't made.
- **The tier.** The first run on a new machine is tier 2 (a single observation); with 5 repeats + p50/p95 it rises to tier 3. The guide's published numbers don't substitute for yours — they open a new line beside them, with the machine's credentials.
- **The GPU.** If `size_vram` comes out non-zero, the model was running on the GPU; that run is added beside this page's CPU runs, not instead of them. Verify from the log that your Ollama version's GPU discovery works (the `inference compute` line).
- **Contaminators can exist on every machine.** IDE integrations, Docker-like tools, startup applications — if something loads a model by itself whenever the server starts, the contamination audit catches it; silencing that tool before the window is the machine owner's decision.

## The record discipline and retrieval

- Put a machine label in the record's name: `cikti/eszamanli-log-<machine>-<date>.txt`. The same file name doesn't tell the same record on two machines.
- Three credential lines are required with every record: the server version (from the `server config` line), the model load's `-np`/`-c` values, and the machine (the CPU model, RAM, OS).
- The acceptance criteria for the numbers entering the result tables sit in the rigs' READMEs; a window isn't opened before reading that rig's acceptance criteria, without producing a measurement.
- Two machines' numbers aren't put side by side in a single table; the thing to be made to talk is whether you see the same pattern on both hardware. This is the only honest generalization path that carries over from a single machine.

## The smoke commands (setup verification)

The purpose of each rig's README's command summary, here in one line: to prove the setup was installed right. These require Ollama and finish in minutes:

```bash
cd ornekler/tekrarlanabilirlik && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --duman > cikti/duman.txt 2>&1
cd ../enjeksiyon-deni && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u enjeksiyon.py --duman > cikti/duman.txt 2>&1
cd ../cikarim-olcu && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u hiz_olc.py --kisa > cikti/duman.txt 2>&1
cd ../eszamanli-olcu && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --duman > cikti/duman.txt 2>&1
cd ../gomme-egitimi && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u kos.py --duman --kollar a > cikti/duman.txt 2>&1
cd ../yerel-rag && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u rag.py --test > cikti/duman.txt 2>&1
```

:::caution[Two rigs' smoke writes to the canonical record name]
`gomme-egitimi/kos.py --duman` writes its output to `cikti/kol-a.txt`, and `eminlik-olcu/eminlik.py --duman` writes its structured outputs to the `cikti/*.json` evidence files. Before overwriting your own record, check those files' existence or run the smoke output in a separate copy. On this guide's author machine this trap happened once for real and was reverted from git — if you have no git history, back up the evidence files before the smoke run.
:::

The rigs not requiring Ollama (klasik-ml, veri-temizleme, the turkce-asistan data preparation, the gorsel-lora audit) are verified independently with the commands in their READMEs.

## Related Pages

- [The Verification Mechanism](/en/kaynaklar/dogrulama-mekanizmasi/) — how the stamp system and staleness are managed.
- [The Scope Map](/en/kaynaklar/kapsam-haritasi/) — the acceptance rules, the evidence tiers and the measurement's server version register.
- [Concurrency](/en/kullanim/eszamanlilik/) — the most suitable first axis for multi-machine comparison: the question "are the patterns preserved across versions and hardware?" starts there.
- [Local Setup](/en/donanim/yerel-kurulum/) — Ollama setup's own details.
