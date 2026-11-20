---
title: "Running Your Own Model with Ollama (Windows)"
description: "Ollama setup, adding a GGUF model (with a Modelfile or pulled straight from Hugging Face), using the OpenAI-compatible API, and setting up a local chat interface with Open WebUI."
dogrulama: 2026-11-20
---

Training is done, the model is quantized; now it's time to run it. Ollama is the easiest way to run language models locally on Windows with a single install. On this page you'll add both ready models and the model you trained to Ollama, and set up the API and chat interface.

## What is Ollama?

Ollama is an open-source model-running tool built on llama.cpp:

- It reduces downloading, storing and running models to a single command (`ollama pull`, `ollama run`).
- It runs as a background service and serves an **OpenAI-compatible** API at `http://localhost:11434`.
- It runs on Windows, macOS and Linux; the Windows install is "download-install-run" level, with no driver drama.
- It's GGUF-based: you can add your own [quantized model](/en/kullanim/quantization/) to its library too.
- It's compatible with interfaces like Open WebUI and with embedding models.

The project moves fast: as of October 2026 the release line has passed v0.40 (check the current version with `ollama --version` or the GitHub releases). The major capabilities that arrived in 2025-2026:

- **Reasoning (thinking) output:** in reasoning models the chain of thought is shown separately from the answer; controlled with `--think` in the CLI, `/set think` in the interactive session, and `"think": true` in the API.
- **Tool calling and streaming:** models can call functions; responses stream even while calling tools.
- **The new engine and multimodality:** the engine introduced in 2025 supports vision models and experimental image generation; an MLX backend was also added on Apple Silicon.
- **Structured output:** by giving a JSON schema you can get parseable, schema-compliant answers from the model.

## Setup and the First Try

1. Download and run the Windows installer from `ollama.com`. After setup, Ollama starts in the background (you'll see its icon in the system tray).
2. Open a terminal and verify the install:

```bash title="verify_setup.sh"
ollama --version

# Start a chat with a ready model right away (downloaded on first run)
ollama run qwen3:4b
```

Type `/bye` to end the chat.

Other ready models you can try:

```bash title="ready_models.sh"
ollama run gemma3:4b      # Google Gemma 3
ollama run llama3.2:3b    # Meta Llama 3.2
ollama run phi4-mini      # Microsoft Phi-4-mini (small and fast)
```

:::tip
First-download sizes: `qwen3:4b` is about 2.5 GB. If your connection is slow, start with `llama3.2:1b` (about 1.3 GB). You can see your downloaded models with `ollama list` and delete them with `ollama rm <model-name>`.
:::

## Cloud models: the `-cloud` tag

Ollama isn't limited to local models. The cloud models that opened in preview in September 2025 and later became a product can be used by signing into your account: the model runs on GPUs in a data center, and the local features on the interface and API side (tool calling included) apply as they are.

```bash title="cloud_model.sh"
ollama signin                  # Sign into your account
ollama run gpt-oss:120b-cloud  # The big model running in the cloud
```

:::note
Cloud models are distinguished by the `-cloud` tag at the end of their names (e.g. `qwen3-coder:480b-cloud`, `deepseek-v3.1:671b-cloud`); every model without the tag runs on your computer. The cloud side may be paid for some models; see ollama.com for the current list and terms.
:::

## Adding your own model to Ollama

If you have your GGUF file (for how to produce it, see the [Quantization](/en/kullanim/quantization/) page), you turn it into an Ollama model in four steps.

### Step 1: Prepare your GGUF file

Let your merged and quantized model be, say, `qwen3-4b-turkish-Q4_K_M.gguf`. Let's work in that folder.

### Step 2: Write the Modelfile

The **Modelfile** is a simple text file telling Ollama "how to run this model":

```dockerfile title="Modelfile"
# The GGUF file to use (a relative path suffices if it's in the same folder as the Modelfile)
FROM ./qwen3-4b-turkish-Q4_K_M.gguf

# Generation settings
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

# The model's stop token (add it if it doesn't come automatically from the GGUF)
PARAMETER stop "<|im_end|>"

# The Turkish system prompt
SYSTEM """You are a helpful assistant speaking Turkish. You answer questions briefly, clearly and correctly. On a topic you don't know, you say openly that you're unsure."""
```

:::note
The `stop` token varies by model (e.g. `<|im_end|>` in the Qwen family, `<|eot_id|>` in Llama 3). If you see answer-truncation problems, look at your model's chat template; Ollama already reads the needed tokens from the GGUF metadata in most models.
:::

### Step 3: Create the model

```bash title="add_model.sh"
ollama create my-model -f Modelfile
```

The command adds your GGUF file into Ollama's local library as a model. `my-model` appears in the `ollama list` output.

### Step 4: Run it

```bash
ollama run my-model
```

For testing, writing a Turkish message like "Hello, introduce yourself." suffices; the model should answer in the style of your training data.

:::tip Do you have an adapter-based model?
You can't hand your LoRA adapter to Ollama directly. You first need to [merge](/en/kullanim/lora-birlestirme/) the adapter with the base model, then [convert it to GGUF](/en/kullanim/quantization/). If you trained with Unsloth, the one-line GGUF output automates this flow.
:::

## Pulling GGUF straight from Hugging Face

You don't have to write a Modelfile either: Ollama can pull GGUF repos from the Hugging Face Hub directly. If the repo has a `Q4_K_M` quantization it downloads that by default; for another quantization you specify it with the tag:

```bash title="hf_gguf.sh"
# Format: ollama run hf.co/USER/REPO[:QUANTIZATION]
ollama run hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF        # default: Q4_K_M
ollama run hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0   # explicit quantization choice
```

This path also holds for your own trained model: after uploading your GGUF file to Hugging Face, you can pull it with one command using your username and repo. For private repos it suffices to introduce Ollama's SSH key to your Hugging Face account. For the upload steps, see the [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/) page.

### The end-to-end flow from training to chat

The whole path of your own model reaching Ollama summarizes like this:

1. **Train:** train a LoRA with the [step-by-step training](/en/llm/adim-adim-egitim/) flow.
2. **Merge:** [merge](/en/kullanim/lora-birlestirme/) the adapter with the base model.
3. **Produce the GGUF:** [quantize](/en/kullanim/quantization/) the merged model and convert it to GGUF.
4. **Upload:** [upload](/en/kullanim/huggingface-paylasim/) the GGUF to Hugging Face.
5. **Pull and run:** run it on any machine with `ollama run hf.co/USER/REPO:Q4_K_M`; if you want to pin the system prompt and generation settings, apply the Modelfile flow above.

## The API: using Ollama from a program

Ollama serves an **OpenAI-compatible** API through its background service. This lets you redirect your existing code using the `openai` library to Ollama with almost no changes.

The root API is documented too: on `http://localhost:11434` there are endpoints like `/api/generate` (raw completion), `/api/chat` (chat), `/api/embeddings` (embeddings) and `/api/ps` (loaded models); Ollama-specific options like `"think": true` apply on this local API. For common chat use, the OpenAI-compatible `/v1/chat/completions` path below suffices:

### A quick test with curl

```bash title="api_test.sh"
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-model",
    "messages": [
      {"role": "user", "content": "Write a two-sentence nature description in Turkish."}
    ]
  }'
```

:::note
On Windows, the easiest way to send a JSON body without wrestling with quote escapes is to use Git Bash (in PowerShell, `curl` behaves differently as an alias).
:::

### The Python client

```bash title="setup.sh"
pip install openai
```

```python title="ollama_client.py"
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",   # Ollama asks for no key; the client won't accept an empty value
)

response = client.chat.completions.create(
    model="my-model",
    messages=[
        {"role": "system", "content": "You are a Turkish-speaking, brief and clear assistant."},
        {"role": "user", "content": "What is LoRA? Explain in two sentences."},
    ],
)

print(response.choices[0].message.content)
```

### Embeddings and RAG

Ollama runs embedding models too; that's the foundation of RAG (document-grounded Q&A) systems:

```bash title="embedding_model.sh"
ollama pull nomic-embed-text
```

```python title="embedding_example.py"
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

e = client.embeddings.create(
    model="nomic-embed-text",
    input=["First document piece", "Second document piece"],
)
print(len(e.data[0].embedding))   # the vector size: 768
```

If you convert texts to vectors this way, store them in a vector database, find the document pieces most similar to the question and add them to the model's prompt, you've built a simple RAG system. Open WebUI serves this flow from the interface; for the pipeline's end-to-end form with real run outputs, see the [Local RAG Assistant example](/en/ornekler/yerel-rag/).

## Open WebUI: your local AI platform

Open WebUI has moved past its initial "Ollama interface" identity into a local AI platform connecting local models and OpenAI-compatible APIs from one panel: it offers chat history, file upload, asking questions over documents (RAG) and multi-user support. On Windows the least-effort path is installing with pip; if you have Docker Desktop you can also run it in a container:

```bash title="open-webui-pip.sh"
pip install open-webui
open-webui serve   # runs at http://localhost:8080
```

```bash title="open-webui-docker.sh"
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

Then open the interface from the browser (`http://localhost:8080` on a pip install, `http://localhost:3000` on Docker); the first registered account becomes the admin. Your Ollama models (my-model included) appear in the model menu at the top. With the file-upload button you can upload a PDF or text and ask questions like "summarize this document".

:::caution
If the containerized interface can't reach the Ollama on the Windows host, you may need to allow port 11434 in the firewall. If you want to run Ollama inside a container too, Open WebUI's `ghcr.io/open-webui/open-webui:ollama` image, which bundles Ollama, suffices on its own; in that case add `--gpus all` to the command for GPU access.
:::

## Performance Tips

- **Moving layers to the GPU:** Ollama moves layers to the GPU automatically as VRAM allows; the remaining layers run in RAM. So the model runs even if it's bigger than VRAM — it's just slower. To force or limit it, add `PARAMETER num_gpu 99` (all) or a lower layer count to the Modelfile.
- **Context size:** the default context window comes not from the model but from your machine's memory: as of 2026, Ollama uses a 4096 default under 24 GB of VRAM, 32k in the 24-48 GB range, and 256k tokens at 48 GB and above. You can change the service-wide default with the `OLLAMA_CONTEXT_LENGTH` environment variable, or pin it per model with a value like `PARAMETER num_ctx 8192` in the Modelfile; every increase raises memory consumption.
- **Monitoring and diagnosis:** the `ollama ps` command shows whether the loaded model is running on the GPU or partly on the CPU and how much memory it uses; with `ollama run my-model --verbose` you can see the tokens-per-second speed. If you see unexpected model behavior, the `ollama show my-model --modelfile` output prints the effective Modelfile (parameters, chat template, system prompt) and points the diagnosis straight at it. On Windows, Task Manager and `nvidia-smi` work for VRAM tracking.
- **Answer speed questions by measuring:** the measurement that phases why an answer took 3-60 seconds (cold load 3.1 s, pre-fill ~40 tok/s, decode ~14 tok/s, the `num_ctx` memory steps, the cache gain) is on the [Speed and Cost](/en/kullanim/hiz-ve-maliyet/) page. One finding on that page also concerns the examples here: on Windows, `http://localhost:11434` adds a **~2.03 s per request** name-resolution overhead; with `http://127.0.0.1:11434` it's **0.00 s**. In multi-call loops (like RAG indexing), a one-word change makes a measurable difference.
- **Sampling and stop settings:** what the `temperature`, `top_k`, `top_p`, `min_p`, `num_predict`, `stop` and `format` fields do, where the docs' defaults are written, and how to read whether your own model has a baked-in sampling setting: [Inference Parameters](/en/kullanim/cikarim-parametreleri/).

## Sources and Further Reading

- [The Ollama Blog](https://ollama.com/blog/) — the primary announcement channel for features like the new engine, cloud models and MLX.
- [Ollama Release Notes](https://github.com/ollama/ollama/releases/) — the release-by-release change list; the v0.40 line as of October 2026.
- [Ollama Docs: Context Length](https://docs.ollama.com/context-length/) — the default context values by VRAM and using `OLLAMA_CONTEXT_LENGTH`.
- [Ollama API Reference](https://docs.ollama.com/api/) — the `/api/chat`, `/api/generate`, `/api/embeddings` endpoints and the OpenAI compatibility table.
- [Hugging Face: Use Ollama with any GGUF Model](https://huggingface.co/docs/hub/ollama/) — the `ollama run hf.co/...` syntax, quantization choice and private repo access.
- [Ollama Cloud Models Announcement](https://ollama.com/blog/cloud-models/) — the post introducing the `-cloud` tag and the sign-in flow.
- [Ollama Thinking Announcement](https://ollama.com/blog/thinking/) — the `--think` flag and the `"think"` API parameter.
- [The Open WebUI Repo](https://github.com/open-webui/open-webui/) — the official source of the pip and Docker install commands.

## Next Steps

- To serve your model professionally: [Model Serving: vLLM and API](/en/kullanim/sunma-api/)
- To measure the quantized model's quality: [Benchmarks and Evaluation](/en/degerlendirme/benchmarklar/)
- To share the model with the community: [Sharing on Hugging Face](/en/kullanim/huggingface-paylasim/)
