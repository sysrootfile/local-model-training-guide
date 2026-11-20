---
title: "Local Setup (Windows): A Ready Environment from Scratch"
description: "Set up Python, a virtual environment, the NVIDIA driver and PyTorch on Windows step by step; CUDA verification, when WSL2 is needed and fixes for common setup errors."
dogrulama: 2026-11-20
---

This page is the shortest path from a Windows computer with nothing installed to the "I can train a model" point. At each step we first give the **what** and **why**, then the copy-paste commands.

:::tip
All commands are for PowerShell (or Windows Terminal) and require no administrator rights.
:::

## The Big Picture: Python, PyTorch, CUDA, Driver

Setting the relationship between these four names straight once lets you diagnose later errors on your own:

```text title="Layered structure"
  ┌────────────────────────────────────────────────────┐
  │  Your code and libraries                           │
  │  (transformers, datasets, peft, trl, ...)          │
  ├────────────────────────────────────────────────────┤
  │  PyTorch   →  tensor math and automatic gradients  │
  ├────────────────────────────────────────────────────┤
  │  CUDA      →  running the math on the GPU          │
  ├────────────────────────────────────────────────────┤
  │  NVIDIA driver  →  Windows talking to the card     │
  ├────────────────────────────────────────────────────┤
  │  GPU hardware                                      │
  └────────────────────────────────────────────────────┘
```

- **Python:** the language you write code in; libraries live here.
- **PyTorch:** the framework doing weight, gradient and matrix operations.
- **CUDA:** the interface through which PyTorch talks to the GPU ("the card's calculator language").
- **Driver:** the interpreter between hardware and operating system; `nvidia-smi` is this layer's live report.

:::note
**What if you have no GPU?** Everything still installs; PyTorch runs in CPU mode. You can do short experiments with small models (0.5-1B), but real fine-tuning is unbearably slow on CPU. In that case the journey continues on the [Cloud Options](/en/donanim/bulut-secenekleri/) page; the setup steps are nearly identical in the cloud.
:::

## Step 1: Installing Python

1. Download **Python 3.11 or 3.12** from [python.org/downloads](https://www.python.org/downloads/).
2. On the setup screen, make sure to tick **"Add python.exe to PATH"**. (Fixing it later is a hassle.)
3. Finish the setup, then **close and reopen** the terminal.

:::caution
As of 2026 PyTorch officially supports the Python 3.10-3.14 band on Windows; there is no Windows package for 3.15 yet. 3.13 is generally fine too, but if you get "package could not be built" style errors with third-party packages at the extreme end of the band (3.14/3.15), Python is the first suspect; going back to 3.12 is the most practical fix.
:::

Verify:

```bash title="PowerShell"
python --version
# Example output: Python 3.12.8
```

If `python` is not found, try Windows' `py` launcher: `py --version`.

:::tip
A machine can have multiple Python versions. `where python` shows which one is active; the permanent solution is a virtual environment (Step 2).
:::

## Step 2: Virtual Environment (venv or uv)

A virtual environment (venv) is a project-scoped isolated Python installation: project A's packages don't affect project B.

- **venv:** comes with Python, needs no extra setup.
- **uv:** a modern package manager written in Rust; installation and package resolution are very fast, and it can manage Python versions too. As of 2026 it is mature and widespread.

:::caution
**Why is a virtual environment mandatory?** Packages installed system-wide gradually break each other ("package A wants a newer X, package B wants an older X"). A virtual environment gives each project its own boxed world; to get rid of it you just delete the folder.
:::

### Installing uv (recommended)

```powershell title="PowerShell — installing uv"
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Reopen the terminal and verify:

```powershell title="PowerShell"
uv --version
```

:::note
The command above is uv's official install script (`irm` = Invoke-RestMethod). The current command is always in the [uv docs](https://docs.astral.sh/uv/); when copying one-liner scripts, verifying the source is a good habit.
:::

### Creating the project and the environment

```powershell title="PowerShell"
mkdir C:\ml\projelerim
cd C:\ml\projelerim
uv venv --python 3.12
```

The short path (`C:\ml\...`) is a deliberate choice: Windows' long-path limit (260 characters) causes unexpected errors in deep folders.

With `uv` you can run `uv pip install ...` directly without activating the environment. If you prefer classic `venv`:

```powershell title="PowerShell — classic venv"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

:::tip
If PowerShell complains "running scripts is disabled on this system", run this once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
:::

## Step 3: NVIDIA Driver Check

```bash title="PowerShell / CMD"
nvidia-smi
```

Three lines in the output matter:

```text
+-------------------------------------------------------------+
| NVIDIA-SMI 5xx.xx    Driver Version: 5xx.xx                 |
| CUDA Version: 12.x                                          |
+-------------------------------------------------------------+
|   0  NVIDIA GeForce RTX 4070        Mem: 1234MiB / 12282MiB |
+-------------------------------------------------------------+
```

- **Driver Version:** the installed driver's version.
- **CUDA Version:** the *highest* CUDA version the driver supports — not what's installed, but the upper bound. The CUDA runtime PyTorch brings must be below this value.
- **Memory-Usage (Mem):** used / total VRAM on the card.

If the command isn't found, the NVIDIA driver isn't installed (or the card isn't NVIDIA). Current drivers: [the official NVIDIA driver download page](https://www.nvidia.com/Download/index.aspx).

For a sense of driver bands: as of 2026 the CUDA 13 runtime requires a driver from the **r580 driver family**; for the CUDA 12 family, 525.60.13 on Linux and 527.41 and later on Windows suffice (NVIDIA CUDA Toolkit release notes). If the CUDA version of the PyTorch build you will install exceeds the "CUDA Version" upper bound in the output (e.g. you see 12.x while installing cu130), update the driver; a driver update does not break an installed PyTorch.

:::note
"It says CUDA Version 12.x — do I also need to install CUDA manually?" — No. PyTorch ships the CUDA runtime with its package. The only thing asked of you is a new enough **driver**.
:::

## Step 4: Installing PyTorch

CPU (no-GPU) install — only for small experiments:

```bash title="PowerShell — CPU"
pip install torch
```

GPU (CUDA) install — the typical form as of 2026 (current stable: PyTorch 2.13):

```bash title="PowerShell — template; copy the current tag from the site"
pip install torch --index-url https://download.pytorch.org/whl/cuXXX
```

:::caution
The `cuXXX` above is a **placeholder**. As of 2026 the current example tags are `cu126` and `cu130`; CUDA 13.0 is the default build and older tags get retired periodically (with PyTorch 2.13 the `cu128`/`cu129` wheels were removed — commands from old guides may therefore no longer work). Always generate the full command from the selector on the [PyTorch: Get Started](https://pytorch.org/get-started/locally/) page: Platform **Windows**, Package **pip**, Compute Platform **CUDA XX**.
:::

:::danger
On Windows, plain `pip install torch` usually installs the **CPU version**. This is the number-one cause of "I installed it but the GPU isn't used". If in doubt, run the verification in Step 5.
:::

## Step 5: Verification

```python title="verify.py"
import torch

print("PyTorch version     :", torch.__version__)
print("CUDA available?     :", torch.cuda.is_available())
print("CUDA runtime        :", torch.version.cuda)

if torch.cuda.is_available():
    print("Device              :", torch.cuda.get_device_name(0))
    total_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print("Total VRAM          :", round(total_gb, 1), "GB")
    print("BF16 support        :", torch.cuda.is_bf16_supported())
```

Run it: `python verify.py`. Expected: `CUDA available? True`, your card's name, and a value like `13.0` on the `CUDA runtime` line. Read the output like this:

- If `CUDA runtime` shows **None**, the CPU wheel is installed — reinstall with the CUDA command from Step 4.
- If `CUDA available?` is **False**, the GPU isn't visible even at the driver level: check the driver first (Step 3), then go back to Step 4.
- If `CUDA runtime` is higher than the "CUDA Version" upper bound in `nvidia-smi`, the driver is old; update the driver first.
- If `BF16 support` is **False**, your card doesn't know bf16 in hardware; you must use fp16 instead of `bf16=True` in recipes.
- If setup is complete but you hit a version-related error, compare the same three outputs with the diagnosis steps in the "Version Mismatches" (heading 11) section of the [Troubleshooting](/en/llm/sorun-giderme/) page; that flow uses the same information as this script.

## Step 6: The First Libraries

The core library stack in one line:

```bash title="PowerShell"
pip install -U pip
pip install transformers datasets peft trl accelerate bitsandbytes
```

(If you work with uv, type `uv pip` instead of `pip`.)

- **transformers:** loading models and tokenizers.
- **datasets:** loading, transforming, splitting data.
- **peft:** adapter methods like LoRA.
- **trl:** SFT / DPO / GRPO training loops.
- **accelerate:** device, mixed precision and distribution management.
- **bitsandbytes:** 4-bit / 8-bit quantization (QLoRA's engine).

:::note
As of 2026 bitsandbytes officially supports Windows: the install doc lists prebuilt wheels for Windows x86-64 in tables and recommends plain `pip install bitsandbytes` (system requirements: Python 3.10+, PyTorch 2.4+). Still, it is the fussiest package in this stack: if you get an `ImportError` or DLL error, first move to the current version; if the problem persists, see the version headings on the [Troubleshooting](/en/llm/sorun-giderme/) page and the WSL2 section below.
:::

## The HF Cache: Where It Piles Up, How to Move It

The libraries in Step 6 accumulate every model and dataset you download in your user folder by default: `C:\Users\<user>\.cache\huggingface` (models live in the `hub` subfolder, one folder per model). Since models are on the order of GBs, this folder grows silently; when the disk fills, this is the first place to look.

Two practical habits:

- **Freeing space:** you can delete the folders of models you don't use; they are re-downloaded on next use. For the general disk strategy combined with checkpoints, see the "Disk Full" (heading 8) section of the [Troubleshooting](/en/llm/sorun-giderme/) page.
- **Moving to another drive:** the `HF_HOME` environment variable sets the cache root. To set it permanently on Windows:

```powershell title="PowerShell — set HF_HOME permanently"
[Environment]::SetEnvironmentVariable("HF_HOME", "D:\hf-cache", "User")
```

Reopen the terminal; transformers, datasets and the hub libraries do their downloads and reads from this root. If you moved the existing cache to the new location, you can delete the old folder.

## Pinning Versions: The Same Environment Three Months Later

Recording the versions of the stack you install today is the cheapest way to recreate the exact same environment three months later (or on another machine); it closes the "it worked in one experiment, but how?" era. After setup completes:

```bash title="PowerShell — save the current versions"
pip freeze > requirements.txt
```

With uv the equivalent is `uv pip compile`:

```bash title="PowerShell — locking with uv"
uv pip compile pyproject.toml -o requirements.txt
```

Keep `requirements.txt` next to your project. To recreate the same environment:

```bash title="PowerShell — recreate the same environment"
pip install -r requirements.txt
```

:::caution
The PyTorch line carries a version tag naming the CUDA build (+cu130-like); this tag may not exist on default PyPI. When reinstalling, install torch with the Step 4 command (same index-url) and pass the rest through `requirements.txt` — that's the safest order.
:::

## The End-of-Setup Smoke Test (No GPU)

The verification script says "packages are installed"; it does not show the end-to-end flow works. A one-minute smoke test closes that gap: download a genuinely tiny model with transformers and run it on CPU. `sshleifer/tiny-gpt2` (a miniature GPT-2 for testing, long popular on HF) fits the job:

```python title="smoke_test.py"
from transformers import pipeline

pipe = pipeline("text-generation", model="sshleifer/tiny-gpt2")
output = pipe("Hello", max_new_tokens=8)
print(output[0]["generated_text"])
```

On first run the model lands in the HF cache from the previous section; afterwards it answers on CPU within seconds. The output is not meaningful: tiny-gpt2 is a test model, no sense is expected from its text; the point is that the "download → load → inference" chain returns without error. If the script finished without error, your environment works end to end; the GPU side is confirmed separately with the Step 5 script.

## WSL2: When Is It Needed?

WSL2 (Windows Subsystem for Linux 2) runs a real Linux kernel inside Windows. Most trainings work fine on Windows; however, speed packages compiled for Linux like `flash-attn`, the smoothest installs of some tools like Unsloth, and the `bash` scripts in READMEs are more comfortable on the Linux side. Setup: `wsl --install` in an **administrator** PowerShell, a reboot and creating an Ubuntu account. Current steps: [the Microsoft WSL install doc](https://learn.microsoft.com/en-us/windows/wsl/install). After installation you repeat Steps 2-6 in the Ubuntu terminal; the only difference is command names (`python3`, `source .venv/bin/activate`).

:::note
**Two practical notes on WSL2.** (1) The driver stays on the Windows side: NVIDIA's CUDA-on-WSL guide explicitly says not to install a Linux GPU driver inside WSL; you keep the driver current only on Windows, and `nvidia-smi` inside WSL sees it. Installing a separate CUDA Toolkit into WSL is also unnecessary — PyTorch's pip wheels bring the CUDA runtime themselves; the toolkit is only needed if you compile your own CUDA code. (2) Keep project files in WSL's own file system (e.g. `~/projects`): Microsoft's WSL docs state that this is how you get the fastest performance when working with Linux tools; working via `/mnt/c` is noticeably slower especially with many small files (datasets, checkpoints).
:::

:::note
**Is Git Bash enough?** No. Git Bash only provides a shell; it brings no Linux environment, no Linux packages, no different CUDA behavior. It's great for conveniently running `bash` commands, but it doesn't solve "Linux-specific tool" problems — for that you need WSL2. If your tools aren't Linux-specific, staying on Windows is entirely valid.
:::

## Common Setup Errors

| Error message | Meaning | Fix |
| --- | --- | --- |
| `'pip' is not recognized...` | Python not on PATH or wrong terminal | Reopen the terminal; try `python -m pip --version`; reinstall Python with "Add to PATH" |
| `torch not compiled with CUDA enabled` | CPU version installed | Reinstall with the CUDA command from Step 4 (current index-url) |
| `ImportError: DLL load failed while importing torch` | Missing system component or broken install | Install the [Microsoft Visual C++ Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe); `pip install --force-reinstall torch` |
| `UnicodeEncodeError` / broken Turkish characters | Console code page or file encoding | `chcp 65001` in the terminal; save files as UTF-8 (without BOM) |
| "Long path" / "path too long" warnings | The 260-character limit | Move the project to a short path (`C:\ml\...`); enable Long Paths (gpedit → Computer Configuration → Administrative Templates → System → File System) |
| `No module named 'torch'` | Virtual environment not active | `.\.venv\Scripts\Activate.ps1`; check with `where python` |
| `CUDA out of memory` | Not a setup issue but a VRAM issue | [VRAM Math](/en/donanim/vram-hesabi/) |

## Sources and Further Reading

- [Python Downloads](https://www.python.org/downloads/) — the official source of the Windows install; current versions and release notes.
- [uv Documentation](https://docs.astral.sh/uv/) — the official reference for the install script, `uv venv` and `uv pip` commands.
- [PyTorch: Get Started Locally](https://pytorch.org/get-started/locally/) — the current stable version; the selector that generates the Windows + pip + CUDA install command.
- [NVIDIA Driver Download](https://www.nvidia.com/Download/index.aspx) — the current driver matching your card model and Windows version.
- [Microsoft WSL Install](https://learn.microsoft.com/en-us/windows/wsl/install) — the official WSL2 setup steps; for dev environment recommendations see the [environment setup guide](https://learn.microsoft.com/en-us/windows/wsl/setup/environment).
- [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) — the official download page of the system component that is the first suspect for "DLL load failed" errors.
- [bitsandbytes Installation Docs](https://huggingface.co/docs/bitsandbytes/installation) — platform support, system requirements and per-OS wheel tables.

## What's Next?

- If your GPU is weak or absent: [Cloud Options](/en/donanim/bulut-secenekleri/)
- Tool choice and the training flow: [Step-by-Step Training](/en/llm/adim-adim-egitim/)
- An overview of training tools: [Tools](/en/llm/araclar/)
- Your first dataset: [Where to Find Data?](/en/veri/veri-nereden-bulunur/)
