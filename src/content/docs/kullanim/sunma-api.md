---
title: "Model Sunma: vLLM ve API"
description: "Çok kullanıcılı senaryolarda vLLM ile OpenAI uyumlu API sunma; kurulum, LoRA adaptör sunumu, istemci örnekleri ve sunum motorları karşılaştırması."
dogrulama: 2026-10-17
---

Model hazır ve kalitesi test edildi. Peki bu modeli başka kişiler ya da uygulamalar nasıl kullanacak? Kişisel kullanımda [Ollama](/kullanim/ollama/) bu işi fazlasıyla görür; ama onlarca kullanıcıya hizmet verecekseniz sahneye **vLLM** gibi yüksek verimli bir sunum motoru çıkar.

## Ollama yeterli mi?

Karar oldukça basit:

- **Kişisel kullanım, tek kullanıcı, prototip, demo** → Ollama yeterli ve çok daha pratik.
- **Ürününüzde çok sayıda kullanıcı, yüksek eşzamanlılık (concurrency)** → vLLM sınıfı bir motor gerekir.

Sebep mimaride: Ollama tek/az istek için optimize edilmiştir; vLLM ise sürekli toplu işleme (continuous batching) ile gelen istekleri anlık olarak gruplar ve aynı GPU'dan kat kat daha fazla isteği karşılar. Sohbet eden tek kişiyseniz bu farkı hiç fark etmezsiniz; ama 50 kişilik bir ekip aynı anda soru sorduğunda fark devasa olur.

## vLLM nedir?

vLLM, açık kaynak ve yüksek verimli bir çıkarım motorudur:

- **PagedAttention:** Dikkat önbelleğini (KV cache) sayfa tabanlı yöneterek bellek israfını ciddi ölçüde azaltır.
- **Sürekli toplu işleme:** Yeni istekler bekleyenleri bloke etmeden partilere eklenir; GPU sürekli meşgul kalır.
- **OpenAI uyumlu API:** Aynı `/v1/chat/completions` arayüzü sayesinde istemci kodunuz değişmez.
- Hugging Face ağırlıklarını ve AWQ/GPTQ gibi nicemlenmiş formatları doğrudan destekler.

Proje çok hızlı yayımlanır: Ekim 2026 itibarıyla sürüm hattı v0.31'e ulaşmıştır. Bu sayfadaki komutlar uzun süredir kararlı olan temel bayrakları kullanır; yine de yükseltme yaparken sürüm notlarına göz atın.

:::caution Windows kullanıcıları
vLLM doğrudan Windows'ta çalışmaz; WSL2 (Ubuntu) veya NVIDIA Container Toolkit'li Docker gerekir. Bu sayfadaki komutlar WSL2/Linux ortamı içindir. Kişisel kullanım için bu zahmete girmenize gerek yok, [Ollama](/kullanim/ollama/) aynı işi tek kurulumla görür.
:::

## Kurulum ve başlatma

```bash title="vllm_baslat.sh"
# WSL2 (Ubuntu) veya Linux sunucuda:
pip install vllm

# Modeli OpenAI uyumlu sunucu olarak başlat (güncel komut)
vllm serve Qwen/Qwen3-8B --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.90

# Nicemlenmiş AWQ modeliyle:
vllm serve kullanici/qwen3-4b-turkce-awq --port 8000

# Eski sürümlerde yaygın olan eşdeğer komut:
# python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen3-8B --port 8000
```

Önemli bayraklar:

- `--max-model-len`: Maksimum bağlam uzunluğu; VRAM tüketimini doğrudan etkiler (Ollama'daki `num_ctx` karşılığı).
- `--gpu-memory-utilization`: vLLM'in GPU belleğinin ne kadarını kullanacağı (ör. 0.90).
- `--api-key`: Basit API anahtarı koruması.
- `--max-num-seqs`: Aynı anda işlenecek istek sayısı sınırı.

:::note GGUF ve vLLM
vLLM ağırlıklı olarak AWQ/GPTQ ve saf Hugging Face ağırlıklarıyla çalışır; GGUF desteği sınırlıdır. Elinizdeki GGUF modeliyle sunucu kurmak istiyorsanız ya AWQ/GPTQ'ya geçin ya da llama.cpp sunucusunu (`llama-server`) değerlendirin. Format karar ağacı için [Nicemleme](/kullanim/quantization/) sayfasına bakın.
:::

## LoRA adaptörlerini birleştirmeden sunma

vLLM'in pratik bir yanı da eğitilmiş LoRA adaptörlerini taban modeli kopyalamadan sunabilmesidir. Sunucuyu adaptör desteğiyle başlatır, her adaptöre bir ad verirsiniz:

```bash title="vllm_lora.sh"
vllm serve Qwen/Qwen3-8B \
  --enable-lora \
  --lora-modules turkce-asistan=/yol/turkce-asistan-lora \
  --max-lora-rank 64 \
  --port 8000
```

İstemci tarafındaki tek değişiklik model adıdır: `"model": "turkce-asistan"` yazan istekler adaptörle, `"model": "Qwen/Qwen3-8B"` yazanlar taban modelle karşılanır. Böylece aynı GPU üzerinde birden fazla ince ayarlı varyantı tek taban modelden sunarsınız. Adaptörü kalıcı olarak birleştirme kararı için [LoRA Birleştirme](/kullanim/lora-birlestirme/) sayfasındaki akışa bakın.

:::note
`--max-lora-rank` değeri, eğittiğiniz adaptörün rank'ına (ör. 16, 32, 64) eşit ya da büyük olmalıdır; aksi hâlde sunucu adaptörü yüklemeyi reddeder.
:::

## İstemci: OpenAI kütüphanesiyle bağlanma

vLLM sunucusu OpenAI API'siyle uyumludur; Ollama örneğindeki kodun neredeyse aynısı çalışır. Tek değişen `base_url`:

```bash
pip install openai
```

```python title="vllm_istemci.py"
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",   # --api-key vermediyseniz yer tutucu yeterli
)

# 1) Normal istek
yanit = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Merhaba, kendini bir cümleyle tanıt."}],
)
print(yanit.choices[0].message.content)

# 2) Akışlı (stream) istek: cevaplar üretildikçe parça parça gelir
akim = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Türkçe 4 satırlık kısa bir şiir yaz."}],
    stream=True,
)
for parca in akim:
    icerik = parca.choices[0].delta.content
    if icerik:
        print(icerik, end="", flush=True)
```

:::tip
`base_url` dışında hiçbir şeyi değiştirmek zorunda kalmamak, OpenAI uyumlu arayüzlerin en büyük avantajıdır. Aynı istemci kodu hem Ollama (11434) hem vLLM (8000) hem de bulut sağlayıcılarla çalışır.
:::

## Yapılandırılmış çıktı ve araç çağırma

Uygulamaların çoğu modelden serbest metin değil, ayrıştırılabilir veri ister; vLLM her iki ihtiyacı için de sunucu tarafı seçenekleri sunar:

- **Yapılandırılmış çıktı:** İstemci, `response_format` alanına koyduğu JSON şemasıyla şemaya uymayan üretimi engeller. Şemayı zorlayan arka uç (2026 itibarıyla xgrammar, guidance, outlines) `--structured-outputs-config.backend` bayrağıyla seçilir; eski adı `--guided-decoding-backend` olan bayrak terk edilmektedir. Ollama tarafında bunun karşılığı istekteki `format` alanı; neyi garanti edip neyi etmediği [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) sayfasında.
- **Araç çağırma:** Sunucuyu `--enable-auto-tool-choice --tool-call-parser hermes` gibi bir bayrak çiftiyle başlatırsınız; ayrıştırıcı adı modele göre değişir (ör. `hermes`, `llama3_json`) ve bazı modellerde uygun bir `--chat-template` gerekir. İstemci tarafı yine OpenAI standardıdır: araçlar istekteki `tools` parametresiyle tanıtılır.

## Karşılaştırma: hangi sunucu, kime uygun?

| | Ollama | llama.cpp server | vLLM | SGLang | TGI | TensorRT-LLM |
|---|---|---|---|---|---|---|
| Kurulum kolaylığı | Çok kolay (Windows) | Orta | Orta (Linux/WSL2 şart) | Orta (Linux) | Orta (Docker) | Zor (NVIDIA araç zinciri) |
| Eşzamanlı istek verimi | Tek/az kullanıcı | Düşük-orta | Çok yüksek | Çok yüksek | Yüksek | Çok yüksek (NVIDIA'ya özel) |
| Format desteği | GGUF | GGUF | HF ağırlıkları, AWQ, GPTQ (GGUF sınırlı) | HF ağırlıkları, yaygın nicemlemeler | HF ağırlıkları, AWQ, GPTQ | Derlenmiş TensorRT motorları |
| 2026 durumu | Yerel kullanımın standardı; `-cloud` ile buluta da açıldı | Aktif geliştirme; `llama-server` OpenAI uyumlu | Çok kullanıcılı sunumun fiilî standardı | Ajan iş yükleri ve büyük ölçekli sunumda güçlü | Bakım modunda (Aralık 2025'ten beri) | NVIDIA NIM/Triton ile kurumsal dağıtımlarda |

Sahnenin son birkaç yılda nasıl değiştiğini özetleyelim:

- **Ollama**, kişisel kullanımın standardı olmaya devam ediyor; bulut modelleriyle yerel donanımın ötesine de uzandı.
- **llama.cpp server** (`llama-server`) OpenAI uyumlu API sunar; CPU ve düşük VRAM senaryolarının doğal seçimidir.
- **vLLM**, çok kullanıcılı sunumun fiilî standardıdır; Hugging Face Inference Endpoints başta olmak üzere pek çok barındırma platformu motor seçenekleri arasında onu sunar.
- **SGLang**, RadixAttention temelli tasarımıyla özellikle çok adımlı ajan iş yüklerinde ve büyük ölçekli sunumda tercih edilir.
- **TGI** (Text Generation Inference), Hugging Face'in uzun süre ana sunum motoruydu; Aralık 2025'te bakım moduna alındı ve Hugging Face, Inference Endpoints kullanıcılarına vLLM ya da SGLang'e geçmeyi öneriyor. Mevcut kurulumlar çalışmaya devam eder ama yeni projeler için önerilmez.
- **TensorRT-LLM**, NVIDIA'nın en yüksek performans hedefli çıkarım kütüphanesidir; Triton Inference Server ve NVIDIA NIM ile kurumsal ölçekte dağıtılır. Modeli hedef donanıma derleme gerektirdiğinden bireysel kullanıcı için kurduğu karmaşıklığa değer etmez; tabloda bütünlüğü tamamlamak için yer alır.

## Donanım notu

- vLLM'in asıl avantajı (yüksek eşzamanlılık) ciddi VRAM ister; pratikte 16 GB ve üzeri VRAM'li GPU'larda parlıyor. Daha küçük kartlarda `--max-model-len` ve `--gpu-memory-utilization` değerlerini düşürmeniz gerekir.
- Tek kullanıcı ve 8-12 GB VRAM'li bir kartta Ollama genellikle daha pratik ve tamamen yeterlidir.
- Eğitim ve sunumu aynı makinede yapacaksanız, eğitim bitince süreçleri kapatıp VRAM'i boşaltmak şarttır; ayrıntılar için [VRAM Hesabı](/donanim/vram-hesabi/) ve [Bulut Seçenekleri](/donanim/bulut-secenekleri/) sayfalarına bakın.

## Üretim notları

- **Kimlik doğrulama:** `--api-key GIZLI_ANAHTAR` ile temel koruma sağlanır; sunucuyu internete açacaksanız mutlaka bir ters vekil (reverse proxy) arkasında ve hız sınırı (rate limit) ile çalıştırın.
- **Gözlemlenebilirlik:** Sunucu ayakta mı diye `/health` uç noktasına bakılır; Prometheus metrikleri `/metrics` adresinden çekilir (istek gecikmesi, kuyruk, önbellek kullanımı). Konteynerle çalıştıracaksanız resmî imaj Docker Hub'da `vllm/vllm-openai` adıyla yayımlanır.
- **Çoklu GPU:** Tek kart yetmezse `--tensor-parallel-size 2` (modeli kartlara bölerek paralelleştirme) ve `--data-parallel-size 2` (istekleri model kopyaları arasına dağıtma) ile ölçeklersiniz; her ikisi birlikte de kullanılabilir.
- **Eşzamanlılık:** `--max-num-seqs` ile aynı anda işlenecek istek sayısını, `--gpu-memory-utilization` ile bellek payını ayarlayın; yük arttıkça gecikme-verim dengesini test edin.
- **Maliyet/ölçek:** Kiralık GPU maliyeti saatlik ücret × çalışma süresidir; talep düşükken sunucuyu kapatmak ya da uykuya alma en basit tasarruftur. Uygun GPU kiralamak için [Bulut Seçenekleri](/donanim/bulut-secenekleri/) sayfasını okuyun.

## Kaynaklar ve İleri Okuma

- [vLLM Belgeleri](https://docs.vllm.ai/en/latest/) — Kurulumdan sunuma güncel resmî referans.
- [vLLM: LoRA](https://docs.vllm.ai/en/latest/features/lora.html) — `--enable-lora` ve `--lora-modules` bayraklarının resmî kılavuzu.
- [vLLM: Yapılandırılmış Çıktılar](https://docs.vllm.ai/en/latest/features/structured_outputs.html) — JSON şemasıyla kısıtlı üretim ve arka uç seçimi.
- [vLLM: Araç Çağırma](https://docs.vllm.ai/en/latest/features/tool_calling.html) — `--enable-auto-tool-choice` ve ayrıştırıcı (parser) seçimi.
- [vLLM: Üretim Metrikleri](https://docs.vllm.ai/en/stable/usage/metrics/) — Prometheus `/metrics` uç noktasının sunduğu metrikler.
- [vLLM: Docker Dağıtımı](https://docs.vllm.ai/en/stable/deployment/docker/) — Resmî `vllm/vllm-openai` imajının kullanımı.
- [TGI: Inference Endpoints sayfası](https://huggingface.co/docs/inference-endpoints/engines/tgi) — TGI'nin bakım modu duyurusu ve vLLM/SGLang'e geçiş kılavuzu.
- [SGLang](https://github.com/sgl-project/sglang/) — Ajan iş yükleri ve büyük ölçekli sunuma odaklı alternatif çatı.
- [llama.cpp](https://github.com/ggml-org/llama.cpp/) — `llama-server` ve OpenAI uyumlu yerel sunumun resmî deposu.
- [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/) — NVIDIA'nın yüksek performanslı çıkarım kütüphanesi.

## Sonraki adımlar

- Sunuma açmadan önce kalite testleri: [Benchmarklar ve Değerlendirme](/degerlendirme/benchmarklar/)
- Modeli toplulukla paylaşmak için: [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/)
- Aklınıza takılanlar: [Sıkça Sorulan Sorular](/kaynaklar/sss/)
