---
title: "Model Serving: vLLM and API"
description: "Serving an OpenAI-compatible API with vLLM in multi-user scenarios; setup, LoRA adapter serving, client examples and a comparison of serving engines."
dogrulama: 2026-11-20
---

The model is ready and its quality tested. But how will other people or applications use this model? For personal use, [Ollama](/en/kullanim/ollama/) does this job more than well; but if you'll serve dozens of users, a high-throughput serving engine like **vLLM** takes the stage.

## Is Ollama enough?

The decision is quite simple:

- **Personal use, a single user, a prototype, a demo** → Ollama suffices and is far more practical.
- **Many users in your product, high concurrency** → an engine of the vLLM class is needed.

The reason is in the architecture: Ollama is optimized for one/few requests; vLLM, with continuous batching, groups arriving requests on the fly and serves many times more requests from the same GPU. If you're a single person chatting, you'll never notice this difference; but when a 50-person team asks questions at the same time, the difference is enormous.

## What is vLLM?

vLLM is an open-source, high-throughput inference engine:

- **PagedAttention:** by managing the attention cache (KV cache) page-based, it reduces memory waste considerably.
- **Continuous batching:** new requests are added to batches without blocking the waiting ones; the GPU stays busy constantly.
- **An OpenAI-compatible API:** thanks to the same `/v1/chat/completions` interface, your client code doesn't change.
- It supports Hugging Face weights and quantized formats like AWQ/GPTQ directly.

The project releases fast: as of October 2026 the release line has reached v0.31. The commands on this page use the base flags that have been stable for a long time; still, glance at the release notes when upgrading.

:::caution Windows users
vLLM doesn't run directly on Windows; WSL2 (Ubuntu) or Docker with the NVIDIA Container Toolkit is required. The commands on this page are for a WSL2/Linux environment. For personal use you needn't go to that trouble; [Ollama](/en/kullanim/ollama/) does the same job with a single install.
:::

## Setup and starting

```bash title="start_vllm.sh"
# On WSL2 (Ubuntu) or a Linux server:
pip install vllm

# Start the model as an OpenAI-compatible server (the current command)
vllm serve Qwen/Qwen3-8B --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.90

# With a quantized AWQ model:
vllm serve username/qwen3-4b-turkish-awq --port 8000

# The equivalent command common in older versions:
# python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen3-8B --port 8000
```

The important flags:

- `--max-model-len`: the maximum context length; directly affects VRAM consumption (the counterpart of `num_ctx` in Ollama).
- `--gpu-memory-utilization`: how much of GPU memory vLLM will use (e.g. 0.90).
- `--api-key`: simple API key protection.
- `--max-num-seqs`: the limit on requests processed at once.

:::note GGUF and vLLM
vLLM works mainly with AWQ/GPTQ and plain Hugging Face weights; GGUF support is limited. If you want to set up a server with the GGUF model in your hands, either switch to AWQ/GPTQ or consider the llama.cpp server (`llama-server`). For the format decision tree, see the [Quantization](/en/kullanim/quantization/) page.
:::

## Serving LoRA adapters without merging

One practical side of vLLM is being able to serve trained LoRA adapters without copying the base model. You start the server with adapter support and give each adapter a name:

```bash title="vllm_lora.sh"
vllm serve Qwen/Qwen3-8B \
  --enable-lora \
  --lora-modules turkish-assistant=/path/turkish-assistant-lora \
  --max-lora-rank 64 \
  --port 8000
```

The only change on the client side is the model name: requests writing `"model": "turkish-assistant"` are served with the adapter, those writing `"model": "Qwen/Qwen3-8B"` with the base model. This way you serve several fine-tuned variants from a single base model on the same GPU. For the decision of merging the adapter permanently, see the flow on the [LoRA Merging](/en/kullanim/lora-birlestirme/) page.

:::note
The `--max-lora-rank` value must be equal to or greater than the rank of the adapter you trained (e.g. 16, 32, 64); otherwise the server refuses to load the adapter.
:::

## The client: connecting with the OpenAI library

The vLLM server is compatible with the OpenAI API; almost the exact copy of the code in the Ollama example works. The only thing changing is the `base_url`:

```bash
pip install openai
```

```python title="vllm_client.py"
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",   # if you gave no --api-key, a placeholder suffices
)

# 1) A normal request
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Hello, introduce yourself in one sentence."}],
)
print(response.choices[0].message.content)

# 2) A streaming request: the answers arrive piece by piece as they're generated
stream = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Write a short 4-line poem in Turkish."}],
    stream=True,
)
for piece in stream:
    content = piece.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

:::tip
Not having to change anything but the `base_url` is the OpenAI-compatible interfaces' biggest advantage. The same client code works with Ollama (11434), vLLM (8000) and cloud providers alike.
:::

## Structured output and tool calling

Most applications want parseable data from the model, not free text; vLLM offers server-side options for both needs:

- **Structured output:** the client, with the JSON schema it puts in the `response_format` field, blocks generation not complying with the schema. The backend enforcing the schema (as of 2026 xgrammar, guidance, outlines) is chosen with the `--structured-outputs-config.backend` flag; the flag, formerly `--guided-decoding-backend`, is being deprecated. Its counterpart on the Ollama side is the `format` field in the request; what it guarantees and what it doesn't is on the [Inference Parameters](/en/kullanim/cikarim-parametreleri/) page.
- **Tool calling:** you start the server with a flag pair like `--enable-auto-tool-choice --tool-call-parser hermes`; the parser name varies by model (e.g. `hermes`, `llama3_json`) and some models need a suitable `--chat-template`. The client side is again the OpenAI standard: tools are introduced with the `tools` parameter in the request.

## The comparison: which server, for whom?

| | Ollama | llama.cpp server | vLLM | SGLang | TGI | TensorRT-LLM |
|---|---|---|---|---|---|---|
| Ease of setup | Very easy (Windows) | Medium | Medium (Linux/WSL2 required) | Medium (Linux) | Medium (Docker) | Hard (the NVIDIA toolchain) |
| Concurrent request throughput | Single/few users | Low-mid | Very high | Very high | High | Very high (NVIDIA-only) |
| Format support | GGUF | GGUF | HF weights, AWQ, GPTQ (GGUF limited) | HF weights, common quantizations | HF weights, AWQ, GPTQ | Compiled TensorRT engines |
| The 2026 status | The standard of local use; also opened to the cloud with `-cloud` | Active development; `llama-server` OpenAI-compatible | The de facto standard of multi-user serving | Strong in agent workloads and large-scale serving | In maintenance mode (since December 2025) | In corporate deployments with NVIDIA NIM/Triton |

Let's summarize how the stage has changed in the last few years:

- **Ollama** remains the standard of personal use; with its cloud models it also reached beyond local hardware.
- **llama.cpp server** (`llama-server`) serves an OpenAI-compatible API; it's the natural choice of CPU and low-VRAM scenarios.
- **vLLM** is the de facto standard of multi-user serving; many hosting platforms, Hugging Face Inference Endpoints first among them, offer it among their engine options.
- **SGLang**, with its RadixAttention-based design, is preferred especially in multi-step agent workloads and large-scale serving.
- **TGI** (Text Generation Inference) was Hugging Face's main serving engine for a long time; it entered maintenance mode in December 2025, and Hugging Face recommends Inference Endpoints users move to vLLM or SGLang. Existing setups keep working but aren't recommended for new projects.
- **TensorRT-LLM** is NVIDIA's highest-performance-targeting inference library; it's distributed at corporate scale with Triton Inference Server and NVIDIA NIM. Since it requires compiling the model to the target hardware, for the individual user it isn't worth the complexity it sets up; it's in the table to complete the picture.

## A hardware note

- vLLM's real advantage (high concurrency) asks for serious VRAM; in practice it shines on GPUs with 16 GB and above VRAM. On smaller cards you'll need to lower `--max-model-len` and `--gpu-memory-utilization`.
- For a single user and a card with 8-12 GB VRAM, Ollama is usually more practical and entirely sufficient.
- If you'll do training and serving on the same machine, closing the processes and freeing the VRAM when training finishes is a must; for details see the [VRAM Math](/en/donanim/vram-hesabi/) and [Cloud Options](/en/donanim/bulut-secenekleri/) pages.

## Production notes

- **Authentication:** `--api-key SECRET_KEY` gives basic protection; if you'll open the server to the internet, run it definitely behind a reverse proxy and with rate limiting.
- **Observability:** whether the server is up is checked at the `/health` endpoint; Prometheus metrics are pulled from `/metrics` (request latency, the queue, cache usage). If you'll run it in a container, the official image is published on Docker Hub as `vllm/vllm-openai`.
- **Multi-GPU:** if a single card isn't enough, you scale with `--tensor-parallel-size 2` (parallelizing by splitting the model across cards) and `--data-parallel-size 2` (distributing requests across model copies); both can be used together too.
- **Concurrency:** set the number of requests processed at once with `--max-num-seqs` and the memory share with `--gpu-memory-utilization`; test the latency-throughput balance as the load grows.
- **Cost/scale:** rented GPU cost is the hourly rate × running time; shutting the server down or putting it to sleep when demand is low is the simplest saving. To rent a suitable GPU, read the [Cloud Options](/en/donanim/bulut-secenekleri/) page.

## Sources and Further Reading

- [vLLM Documentation](https://docs.vllm.ai/en/latest/) — the current official reference from setup to serving.
- [vLLM: LoRA](https://docs.vllm.ai/en/latest/features/lora.html) — the official guide of the `--enable-lora` and `--lora-modules` flags.
- [vLLM: Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html) — schema-constrained generation and backend choice.
- [vLLM: Tool Calling](https://docs.vllm.ai/en/latest/features/tool_calling.html) — `--enable-auto-tool-choice` and parser choice.
- [vLLM: Production Metrics](https://docs.vllm.ai/en/stable/usage/metrics/) — the metrics the Prometheus `/metrics` endpoint offers.
- [vLLM: Docker Deployment](https://docs.vllm.ai/en/stable/deployment/docker/) — the use of the official `vllm/vllm-openai` image.
- [TGI: the Inference Endpoints page](https://huggingface.co/docs/inference-endpoints/engines/tgi) — TGI's maintenance-mode announcement and the migration guide to vLLM/SGLang.
- [SGLang](https://github.com/sgl-project/sglang/) — the alternative framework focused on agent workloads and large-scale serving.
- [llama.cpp](https://github.com/ggml-org/llama.cpp/) — the official repo of `llama-server` and OpenAI-compatible local serving.
- [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/) — NVIDIA's high-performance inference library.

## Next Steps

- Quality tests before opening to serving: [Benchmarks and Evaluation](/en/degerlendirme/benchmarklar/)
- To share the model with the community: [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/)
- Things on your mind: [Frequently Asked Questions](/en/kaynaklar/sss/)
