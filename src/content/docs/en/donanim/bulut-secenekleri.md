---
title: "Cloud Options: If You Don't Have Your Own GPU"
description: "Compare the cost of renting GPUs on Google Colab, Kaggle, RunPod and Vast.ai; a free-start recipe, a step-by-step RunPod guide and cost examples."
dogrulama: 2026-11-20
---

Training models on a good graphics card is an expensive start; the cloud opens the door at an hourly rate. This page compares the platforms so you spend your money efficiently; it gives a free-start recipe and a step-by-step rental guide.

:::caution
The prices below are **approximate values as of 2026**, and platforms change their prices often. Check the current value on the platform's own pricing page before renting.
:::

## Buy or Rent?

Simple math:

- The RTX 5090's official list price (MSRP) is **$1,999**; however, as of 2026 its real retail price runs far above MSRP — a band of **~$2,500-5,000** is reported in the US. The RTX 4090 has left production; second-hand prices vary by region and stock. Total budget with the card and peripherals comes to **roughly $2,500 and up** (grows with country, taxes and other components).
- In the cloud, the same class of card (4090) costs **~$0.3-0.5** per hour; a class below, the 3090, is cheaper. So a purchase budget equals **roughly 5,000-8,000 hours** of 4090 use in the cloud; with cheaper cards like the 3090 that duration stretches further.
- Even at one hour of training a day, that spreads over decades; add electricity and hardware obsolescence on top.

Conclusion: for irregular or learning-oriented use, the cloud is clearly smarter. If you will train for tens of hours a week, for years, buying starts to make sense. To see which card suffices for which job: [VRAM Math](/en/donanim/vram-hesabi/).

## Platform Comparison

| Platform | Free tier | Typical GPU | Approx. price (2026) | Suited for |
| --- | --- | --- | --- | --- |
| **Google Colab** | Yes: T4 (limited; limits not guaranteed, notebook lifetime ~12h cap) | T4; higher GPUs with Pro | Free; Pro ~$10/mo; Pro+ ~$50/mo | First experiments, learning |
| **Kaggle** | Yes: ~30 hours/week (sometimes more depending on load) | T4 x2 / P100 | Free | Zero budget, notebook habits |
| **RunPod** | No | RTX 4090, A100, H100, H200 | 4090 from ~$0.34/hr; H100 ~$2.9-4/hr; H200 ~$4-5.5/hr | Planned, serious trainings |
| **Vast.ai** | No | Community GPUs (3090 / 4090 / A100...) | 4090 ~$0.35-0.6/hr (median ~$0.5); interruptible listings cheaper | Price hunting, experienced users |
| **Lambda Labs** | No | A100, H100, H200, B200 | H100 ~$3.3-4.3/hr; A100 ~$2/hr; no egress fee; check the current list | Long-running, corporate work |
| **Modal** | $30/mo free credit on the Starter plan | Serverless: from T4 to B200 | Per use, second-level precision (H100 ~$4/hr) | Code-centric, short and sparse jobs |
| **Hugging Face Jobs / Spaces** | Free CPU tier on Spaces | T4, L4, L40S, A100, H200 | T4 ~$0.4/hr; L4 ~$0.8/hr; A100 ~$2.5/hr; H200 ~$5/hr (per minute) | People living in the HF ecosystem |

A notable 2026 change on the Colab side: from September 2026, Colab perks were integrated into Google AI plans; existing Pro/Pro+ subscriptions remain valid. Check Colab's subscription page for the current packages in your region.

:::note
A reference for the market overall: H100-class cards rent in the **~$2-4/hr** range (in classic hyperscaler clouds $6+), H200-class in the **~$4-5.5/hr** band. The difference between the cheap and expensive ends is often the host's reliability.
:::

A quick selection guide:

- **My budget is zero, I'm learning** → Kaggle (~30 hours weekly) and Colab (T4).
- **I'll run my first serious training** → a rented 4090 on RunPod (simple setup, fast start).
- **I'm hunting the lowest hourly price, I'm experienced** → Vast.ai (but be careful with host selection).
- **I'm planning a days-long, uninterrupted training** → corporate options like Secure Cloud or Lambda.

## Hidden Costs: Budget Discipline

Bad surprises in cloud bills always come from the same places:

- **Pods left running:** the most expensive server is the one you forgot to shut down. Check the "Pods" list at the end of every session.
- **Stop ≠ shutdown:** a stopped pod stops the GPU charge but the persistent volume keeps being billed. On RunPod the container disk becomes free when stopped; a network volume is billed even while the pod is off ($0.07/GB/mo under 1 TB, as of 2026). Example: a forgotten 100 GB volume on a stopped pod comes to **~$7** a month; left unattended for three months, **~$21** accumulates — equal to roughly 60 hours of GPU time on a ~$0.35/hr 4090.
- **Disk and volume extras:** the hourly price is only for the GPU. On RunPod the container disk is $0.10/GB/mo while running (the container disk isn't billed when the pod is stopped), a network volume $0.07/GB/mo under 1 TB (as of 2026); on Vast.ai storage varies by host and keeps being billed even if the instance is stopped. Check current rates on the platform's page.
- **Wrong card choice:** renting an H100 for a 4B QLoRA is driving a Ferrari to the grocery store. First clarify the need with [VRAM Math](/en/donanim/vram-hesabi/).

## The Free-Start Recipe: Kaggle

1. Create an account on kaggle.com (Google or email).
2. Start a notebook with **Create → New Notebook**.
3. In the right panel, under **Settings → Accelerator**, pick the GPU: **T4 x2 or P100**. Your weekly quota is about 30 hours (sometimes a bit more depending on load); if it's used up, you wait for next week.
4. Install the libraries in the first cell:

```python title="Kaggle cell"
!pip install -q transformers datasets peft trl bitsandbytes
```

5. Try QLoRA with a small model: [LoRA and QLoRA](/en/llm/lora-qlora/) and [Step-by-Step Training](/en/llm/adim-adim-egitim/).
6. Save the output: write the model files under `/kaggle/working` and persist them with **Save Version**; for large models [upload to Hugging Face](/en/kullanim/huggingface-paylasim/).

:::caution
**Colab note:** on the free tier, the session drops during long trainings or when idle, and everything on the machine is wiped. The fix: mount Google Drive and save checkpoints there:

```python title="Colab — mounting Drive"
from google.colab import drive
drive.mount("/content/drive")
```

Keep the Trainer's `save_steps` small (e.g. save every 200 steps) so a drop loses at most a few minutes of work.
:::

## RunPod: Step by Step

1. **Account:** create an account on runpod.io, verify your email.
2. **Balance:** load balance with your card under Billing. Setting a spending limit/alert prevents a forgotten pod from blowing up the bill.
3. **GPU choice:** choose the GPU via Pods → Deploy. "Community Cloud" is cheaper, "Secure Cloud" is more reliable and pricier. A single RTX 4090 is more than enough for most QLoRA jobs.
4. **Template:** pick the "PyTorch" image — it comes with CUDA and PyTorch installed, so you don't wrestle with building the environment from scratch.
5. **Disk:** a container disk (e.g. 30-50 GB) is enough for model downloads and data; if you want your data to persist, add a volume.
6. **Connection:** when the pod is up, enter via **Connect → JupyterLab** (or SSH).
7. **Data:** the most practical path is to keep the data on Hugging Face (in a private repo if needed) and pull it from inside the pod with `hf download username/my-dataset`. For small files, drag-and-drop into Jupyter also works.
8. **SSH + tmux for long jobs:** if you'll connect over SSH, start the training inside `tmux` or `screen`; the training keeps running even if the terminal or browser closes.
9. **Shutting down:** when the job is done, **Terminate** the pod. The forgotten pod is the classic killer of cloud bills.

:::danger
On RunPod, **Stop** halts the GPU charge but disk billing continues; **Terminate** deletes everything (except volumes). If you keep persistent data in a volume (volumes are priced separately), you can terminate the pod with peace of mind. Make it a habit to check the "Pods" list after every job.
:::

### Data Upload Options

There are three common ways to bring data to a pod; choose by file size:

- **Pulling from the Hugging Face Hub (recommended):** keep the data in an HF repo (private if needed) and download it from inside the pod. The `hf_transfer` package parallelizes downloads, giving serious speed on large repos:

```bash title="Fast HF download (inside the pod)"
pip install -q hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1
hf download username/my-dataset --repo-type dataset --local-dir /workspace/data
```

- **Drag-and-drop:** the JupyterLab interface suffices for files up to a few hundred MB; but if the browser connection drops, the upload is cut short.
- **rclone / S3:** use rclone to pull large archives from your own object storage. Watch egress: in classic clouds like AWS S3, outbound traffic is billed separately; some GPU clouds like Lambda charge no egress, while Vast.ai bills bandwidth per GB. Check whose budget the data-direction traffic is paid from before renting.

## A Note on Vast.ai

Vast.ai is an **auction** marketplace: individual hosts rent out their idle GPUs by naming a price. That's why the market's cheapest 4090s are usually found here: as of 2026, on-demand listings sit in the ~$0.35-0.6/hr band and interruptible listings are priced lower. Check the live list for current prices.

- **For whom:** it suits cost-sensitive, experimental jobs with checkpoints (interrupt-tolerant). For short tests it is one of the most economical options.
- **Choosing a reliable host:** pick machines with high star ratings, a **reliability score of 95%+** and the "verified" tag; extremely cheap listings can have hardware/VRAM inconsistencies — make verifying the card with `nvidia-smi` your first job.
- **Interruption risk:** the host can power off the machine; don't use Vast.ai for long trainings without regular checkpoints.
- **When it's preferred:** perfect for a few hours of experiments, price-comparison benchmarks and practice jobs like "what is 48 GB of VRAM like?".

## Spot and Interruptible Instances

Both RunPod and Vast.ai sell "reclaimable at any moment" capacity well below the on-demand price; but their logics differ:

- **RunPod spot:** usually drops to **around 50%** of the on-demand price; in exchange, the pod can be stopped **without notice** when capacity is reclaimed. Suited for short experiments and users disciplined about checkpoints.
- **Vast.ai interruptible (auction):** you set the hourly bid; if the spot price rises above your bid, the instance is stopped (files remain on disk, storage billing continues). "On-demand" listings are exempt from the bidding race but are pricier.

In both models the rule is the same: **interruption is not an exception, it's part of the design.** The checkpoint discipline from the "Tips for Long Trainings" section below becomes mandatory here: shrink `save_steps`, write the saves to a persistent volume, and verify with a short trial that your training code can resume from the last checkpoint.

:::caution
As tempting as spot/interruptible discounts are, starting a long, uninterrupted training on spot without checkpoints can lose all progress at the moment of interruption. For critical jobs, on-demand / Secure Cloud remains the safest path.
:::

## Tips for Long Trainings

- **Always run training under a supervisor:** `tmux` over SSH, or a `nohup`/log file instead of "Run All" in Jupyter; let the job continue even if the connection drops.
- **Shrink the checkpoint interval:** in the cloud, interruption is a surprise; keep `save_steps` small and write the saves to a volume.
- **Don't reload data over and over:** keep the data in a volume; downloading it from HF at every session wastes both time and bandwidth.
- **Overnight training budget:** an 8-hour training on a $0.34/hr 4090 comes to roughly **$2.7**. Before sleeping, verify with `nvidia-smi` that the job is actually progressing.
- **Save the logs:** output streaming in the terminal is lost; use redirection like `> training.log 2>&1` or the tool's own log file.
- **One training per pod:** starting a second job on the same GPU splits the VRAM in two; if you get OOM, queue the jobs.

## When Should You Switch to Paid?

- **If the weekly free quota isn't enough:** if Kaggle's 30 hours/full week is used up and experiments are being delayed.
- **If you need over 16 GB of VRAM:** the free tiers' T4s are 16 GB; if you want 8B LoRA or 14B+ QLoRA, a paid GPU is a must.
- **If continuity is critical:** if Colab/Kaggle sessions drop and you lose work, hourly rental pays for itself immediately.
- **If you're doing a hyperparameter sweep:** trying 5-6 variants on the same day stretches into weeks on free tiers; a paid day is often cheaper.

## Kaggle or Colab?

Both are free, but their characters differ:

- **Kaggle:** a fixed ~30-hour weekly quota, persistent notebooks, output versioning. Phone verification may be requested at account creation. Highly predictable. A fine detail: if you have a Colab Pro/Pro+ subscription, Kaggle grants +15/+30 extra GPU hours per week respectively when you link the accounts.
- **Colab:** starts instantly with zero setup; but sessions can drop and free GPU access can be restricted at peak hours. On the free tier, a single notebook's lifetime is at most ~12 hours and limits are not guaranteed. GitHub integration is practical.

Practical plan: first experiments on Colab, regular quota-bound work on Kaggle, serious jobs on RunPod/Vast.ai.

## Cost Examples

:::tip
Back-of-the-envelope math (assuming an RTX 4090 rental at ~$0.3-0.4/hr; durations vary by your data and settings):

- **4B model, 5,000-example QLoRA:** ~1-2 hours → **about $0.5-1**
- **8B model, 10-20k-example QLoRA:** ~2-4 hours → **about $1-2**
- **14B model, 20k-example QLoRA:** ~4-8 hours → **about $2-5**
- **Free-tier trial (Kaggle/Colab): QLoRA up to 4B → $0** (within quota and session limits)

Model download and environment setup are included in these durations. The important thing: you can finish a job your own card can't handle for a few dollars. For bigger models (32B+) and long sequences, durations multiply several times; clarify the need on paper first: [VRAM Math](/en/donanim/vram-hesabi/).
:::

## Data Privacy

:::caution
When using cloud GPUs with sensitive data (personal information, customer records, health/finance data), the data leaves your machine and passes through the host's disk; on community platforms there is a possibility of the host accessing the container's file system. What to do: anonymize the data, prefer local hardware if possible, get legal counsel for data covered by personal-data-protection law (in Turkey, KVKK) and evaluate cross-border transfer rules. In fields like health and finance, cloud training is unsuitable in most scenarios.

Small but effective habits for key and token hygiene:

- **Don't paste the token into a cell:** put the HF token in the template's environment-variable section when opening the pod, or define it in the shell with `export HF_TOKEN=...`; a key hardcoded into the code leaks into error logs and saved notebooks.
- **Extra care on shared platforms:** Kaggle and Colab notebooks are easily shared; provide secret values via the platform's own secret feature, never in a plain cell.
- **Revoke the token when the job ends:** revoke the token in HF settings (Settings → Access Tokens) when your job closes; a token's lifetime shouldn't outlive the pod's.
- **Leave no residue:** if you copied sensitive data, delete that copy from the persistent volume at the end; terminating the pod cleans the container but the volume keeps living separately.
:::

## Sources and Further Reading

- [RunPod Documentation](https://docs.runpod.io/) — the official reference for pods, spot instances and disk/volume pricing.
- [RunPod Pricing Page](https://www.runpod.io/pricing) — the current list of per-second on-demand and spot GPU prices.
- [Vast.ai Documentation](https://docs.vast.ai/) — the auction/interruptible logic, storage and bandwidth charges.
- [Colab FAQ](https://research.google.com/colaboratory/faq.html) — the official statement that free-tier limits are "not guaranteed and can fluctuate".
- [Kaggle: Efficient GPU Usage](https://www.kaggle.com/docs/efficient-gpu-usage) — the weekly GPU quota and session rules.
- [Google Blog: Colab is now part of your Google AI plan](https://developers.googleblog.com/colab-is-now-part-of-your-google-ai-plan/) — the September 2026 integration announcement.
- [Modal Pricing](https://modal.com/pricing) — per-second GPU prices and the Starter plan's monthly free credit.
- [Hugging Face Jobs Pricing](https://huggingface.co/docs/hub/jobs-pricing) — Jobs hardware options and the per-minute price table.
- [Lambda Pricing](https://lambda.ai/pricing) — on-demand H100/H200/B200 prices and the egress policy.

## What's Next?

- Setup on your own machine: [Local Setup (Windows)](/en/donanim/yerel-kurulum/)
- Data to feed the training: [Where to Find Data?](/en/veri/veri-nereden-bulunur/)
- Do your first training end to end: [Step-by-Step Training](/en/llm/adim-adim-egitim/)
