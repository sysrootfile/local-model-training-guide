---
title: "Ollama ile Kendi Modelini Çalıştırma (Windows)"
description: "Ollama kurulumu, GGUF model ekleme (Modelfile ile veya Hugging Face'ten doğrudan çekme), OpenAI uyumlu API kullanımı ve Open WebUI ile yerel sohbet arayüzü kurulumu."
dogrulama: 2026-10-17
---

Eğitim tamam, model nicemlendi; şimdi sıra onu çalıştırmakta. Ollama, Windows'ta tek kurulumla dil modellerini yerel olarak çalıştırmanın en kolay yolu. Bu sayfada hem hazır modelleri hem kendi eğittiğiniz modeli Ollama'ya ekleyecek, API ve sohbet arayüzünü kuracağız.

## Ollama nedir?

Ollama, llama.cpp üzerine kurulu açık kaynak bir model çalıştırma aracıdır:

- Modelleri indirme, saklama ve çalıştırma işlerini tek komuta indirir (`ollama pull`, `ollama run`).
- Arka planda bir servis olarak çalışır ve `http://localhost:11434` adresinde **OpenAI uyumlu** bir API sunar.
- Windows, macOS ve Linux'ta çalışır; Windows kurulumu sürücü derdi olmadan "indir-kur-çalıştır" seviyesindedir.
- GGUF tabanlıdır: kendi [nicemlenmiş modelinizi](/kullanim/quantization/) de kütüphanesine ekleyebilirsiniz.
- Open WebUI gibi arayüzlerle ve gömme (embedding) modelleriyle uyumludur.

Proje hızlı gelişiyor: Ekim 2026 itibarıyla sürüm hattı v0.40'ı aşmış durumda (güncel sürümü `ollama --version` ya da GitHub yayınlarıyla kontrol edin). 2025-2026 dönemi modele gelen başlıca yetenekler:

- **Akıl yürütme (thinking) çıkışı:** Akıl yürüten modellerde düşünce zinciri cevaptan ayrı gösterilir; CLI'da `--think`, etkileşimli oturumda `/set think`, API'de `"think": true` ile yönetilir.
- **Araç çağırma ve akış:** Modeller fonksiyon çağırabilir; yanıtlar araç çağırırken de akışla (stream) gelir.
- **Yeni motor ve çok modluluk:** 2025'te tanıtılan yeni motor, görsel modelleri ve deneysel görüntü üretimini destekler; Apple Silicon'da MLX arka ucu da eklendi.
- **Yapılandırılmış çıktı:** JSON şeması vererek modelden ayrıştırılabilir, şemaya uyan cevaplar alabilirsiniz.

## Kurulum ve ilk deneme

1. `ollama.com` adresinden Windows kurulum dosyasını indirip çalıştırın. Kurulum sonrası Ollama arka planda başlar (sistem tepsisinde simgesini görürsünüz).
2. Terminali açıp kurulumu doğrulayın:

```bash title="kurulum_dogrula.sh"
ollama --version

# Hazır bir modelle hemen sohbet başlatın (ilk çalıştırmada indirilir)
ollama run qwen3:4b
```

Sohbeti bitirmek için `/bye` yazın.

Deneyebileceğiniz diğer hazır modeller:

```bash title="hazir_modeller.sh"
ollama run gemma3:4b      # Google Gemma 3
ollama run llama3.2:3b    # Meta Llama 3.2
ollama run phi4-mini      # Microsoft Phi-4-mini (küçük ve hızlı)
```

:::tip
İlk indirme boyutları: `qwen3:4b` yaklaşık 2,5 GB. Bağlantınız yavaşsa `llama3.2:1b` (yaklaşık 1,3 GB) ile başlayın. İndirdiğiniz modelleri `ollama list` ile görebilir, `ollama rm <model-adı>` ile silebilirsiniz.
:::

## Bulut modelleri: `-cloud` etiketi

Ollama yalnızca yerel modellerle sınırlı değil. Eylül 2025'te önizlemeye açılan ve sonrasında ürüne dönüşen bulut modelleri, hesabınıza bağlanarak kullanabilirsiniz: model veri merkezindeki GPU'larda çalışır, arayüz ve API tarafındaki yerel özellikler (araç çağırma dahil) aynen geçerlidir.

```bash title="bulut_model.sh"
ollama signin                  # Hesabınıza bağlanın
ollama run gpt-oss:120b-cloud  # Bulutta koşan büyük model
```

:::note
Bulut modeller adlarının sonundaki `-cloud` etiketiyle ayrılır (ör. `qwen3-coder:480b-cloud`, `deepseek-v3.1:671b-cloud`); etiketi olmayan her model bilgisayarınızda çalışır. Bulut tarafı bazı modellerde ücretli olabilir; güncel liste ve koşullar için ollama.com adresine bakın.
:::

## Kendi modelini Ollama'ya ekleme

Elinizde GGUF dosyanız varsa (nasıl üretileceği için [Nicemleme](/kullanim/quantization/) sayfasına bakın) dört adımda Ollama modeline dönüştürürsünüz.

### Adım 1: GGUF dosyanı hazırla

Birleştirilmiş ve nicemlenmiş modeliniz örneğin `qwen3-4b-turkce-Q4_K_M.gguf` olsun. Çalışmayı bu klasörde yapalım.

### Adım 2: Modelfile yaz

**Modelfile**, Ollama'ya "bu modeli nasıl çalıştıracağını" anlatan basit bir metin dosyasıdır:

```dockerfile title="Modelfile"
# Kullanılacak GGUF dosyası (Modelfile ile aynı klasördeyse göreli yol yeterli)
FROM ./qwen3-4b-turkce-Q4_K_M.gguf

# Üretim ayarları
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

# Modelin durma token'ı (GGUF'tan otomatik gelmezse ekleyin)
PARAMETER stop "<|im_end|>"

# Türkçe sistem istemi
SYSTEM """Sen Türkçe konuşan yardımcı bir asistansın. Sorulara kısa, net ve doğru cevaplar verirsin. Bilmediğin bir konuda emin olmadığını açıkça söylersin."""
```

:::note
`stop` token'ı modele göre değişir (ör. Qwen ailesinde `<|im_end|>`, Llama 3'te `<|eot_id|>`). Cevap kesme sorunları görürseniz modelinizin sohbet şablonuna bakın; Ollama çoğu modelde gerekli token'ları GGUF metadata'sından zaten okur.
:::

### Adım 3: Modeli oluştur

```bash title="model_ekle.sh"
ollama create benim-model -f Modelfile
```

Komut, GGUF dosyanızı Ollama'nın yerel kütüphanesine bir model olarak ekler. `ollama list` çıktısında `benim-model` görünür.

### Adım 4: Çalıştır

```bash
ollama run benim-model
```

Test için "Merhaba, kendini tanıt." gibi Türkçe bir mesaj yazmanız yeterli; modelin eğitim verinizin üslubuna uygun cevaplar vermesi gerekiyor.

:::tip Adaptörlü modeliniz mi var?
LoRA adaptörünüzü doğrudan Ollama'ya veremezsiniz. Önce adaptörü taban modelle [birleştirip](/kullanim/lora-birlestirme/), sonra [GGUF'a çevirmeniz](/kullanim/quantization/) gerekir. Eğitimi Unsloth ile yaptıysanız tek satırlık GGUF çıktısı bu akışı otomatikleştirir.
:::

## Hugging Face'ten doğrudan GGUF çekme

Modelfile yazmak zorunda da değilsiniz: Ollama, Hugging Face Hub'daki GGUF depolarını doğrudan çekebilir. Depoda `Q4_K_M` nicemlemesi varsa varsayılan olarak onu indirir; başka bir nicemleme isterseniz etiketle belirtirsiniz:

```bash title="hf_gguf.sh"
# Biçim: ollama run hf.co/KULLANICI/DEPO[:NICEMLEME]
ollama run hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF        # varsayılan: Q4_K_M
ollama run hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0   # açık nicemleme seçimi
```

Kendi eğittiğiniz model için de bu yol geçerlidir: GGUF dosyanızı Hugging Face'a yükledikten sonra kullanıcı adınız ve deponuzla tek komutla çekebilirsiniz. Özel (private) depolar için Ollama'nın SSH anahtarını Hugging Face hesabınıza tanıtmanız yeterli. Yükleme adımları için [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/) sayfasına bakın.

### Eğitimden sohbete uçtan uca akış

Kendi modelinizin Ollama'ya ulaşma yolunun tamamı şöyle özetlenir:

1. **Eğitin:** [Adım adım eğitim](/llm/adim-adim-egitim/) akışıyla LoRA eğitin.
2. **Birleştirin:** Adaptörü taban modelle [birleştirin](/kullanim/lora-birlestirme/).
3. **GGUF üretin:** Birleşik modeli [nicemleyip](/kullanim/quantization/) GGUF'a çevirin.
4. **Yükleyin:** GGUF'u Hugging Face'a [yükleyin](/kullanim/huggingface-paylasim/).
5. **Çekin ve çalıştırın:** `ollama run hf.co/KULLANICI/DEPO:Q4_K_M` ile herhangi bir makinede çalıştırın; sistem istemi ve üretim ayarlarını sabitlemek isterseniz yukarıdaki Modelfile akışını uygulayın.

## API: Ollama'yı programdan kullanma

Ollama, arka planda çalışan servisi üzerinden **OpenAI uyumlu** bir API sunar. Bu sayede `openai` kütüphanesini kullanan mevcut kodunuzu neredeyse hiç değiştirmeden Ollama'ya yönlendirebilirsiniz.

Kök API de belgelenmiştir: `http://localhost:11434` üzerinde `/api/generate` (ham tamamlama), `/api/chat` (sohbet), `/api/embeddings` (gömme) ve `/api/ps` (yüklenen modeller) gibi uç noktalar bulunur; `"think": true` gibi Ollama'ya özgü seçenekler bu yerel API'de geçerlidir. Yaygın sohbet kullanımı için aşağıdaki OpenAI uyumlu `/v1/chat/completions` yolu yeterlidir:

### curl ile hızlı test

```bash title="api_test.sh"
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "benim-model",
    "messages": [
      {"role": "user", "content": "Türkçe iki cümlelik bir doğa betimlemesi yaz."}
    ]
  }'
```

:::note
Windows'ta JSON gövdesini tırnak kaçışlarıyla uğraşmadan göndermenin en kolay yolu Git Bash kullanmaktır (PowerShell'de `curl` bir takma ad olarak farklı davranır).
:::

### Python istemcisi

```bash title="kurulum.sh"
pip install openai
```

```python title="ollama_istemci.py"
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",   # Ollama anahtar istemez; istemci boş değer kabul etmez
)

yanit = client.chat.completions.create(
    model="benim-model",
    messages=[
        {"role": "system", "content": "Türkçe konuşan, kısa ve net bir asistansın."},
        {"role": "user", "content": "LoRA nedir? İki cümleyle anlat."},
    ],
)

print(yanit.choices[0].message.content)
```

### Gömmeler (embedding) ve RAG

Ollama, gömme modellerini de çalıştırır; bu, RAG (belgeye dayalı soru-cevap) sistemlerinin temelidir:

```bash title="embedding_modeli.sh"
ollama pull nomic-embed-text
```

```python title="embedding_ornek.py"
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

g = client.embeddings.create(
    model="nomic-embed-text",
    input=["İlk belge parçası", "İkinci belge parçası"],
)
print(len(g.data[0].embedding))   # vektör boyutu: 768
```

Metinleri bu şekilde vektörlere çevirip bir vektör veritabanında saklar, soruya en benzer belge parçalarını bulup modelin istemine eklerseniz basit bir RAG sistemi kurmuş olursunuz. Open WebUI bu akışı arayüzden sunar; boru hattının uçtan uca, gerçek çalıştırma çıktılı hâli için [Yerel RAG Asistanı örneğine](/ornekler/yerel-rag/) bakın.

## Open WebUI: Yerel yapay zeka platformunuz

Open WebUI, başlangıçtaki "Ollama arayüzü" kimliğinin ötesine geçip yerel modelleri ve OpenAI uyumlu API'leri tek panelden bağlayan bir yerel yapay zeka platformuna dönüştü: sohbet geçmişi, dosya yükleme, belgeler üzerinden soru sorma (RAG) ve çok kullanıcı desteği sunar. Windows'ta en zahmetsiz yol pip ile kurmaktır; Docker Desktop kuruluysa konteynerle de çalıştırabilirsiniz:

```bash title="open-webui-pip.sh"
pip install open-webui
open-webui serve   # http://localhost:8080 adresinde çalışır
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

Ardından tarayıcıdan arayüzü açın (pip kurulumunda `http://localhost:8080`, Docker kurulumunda `http://localhost:3000`); ilk kayıt olan hesap yönetici olur. Ollama'daki modelleriniz (benim-model dahil) üstteki model menüsünde görünür. Dosya yükleme düğmesiyle PDF veya metin yükleyip "bu belgeyi özetle" gibi sorular sorabilirsiniz.

:::caution
Docker'daki arayüz Windows ana makinesindeki Ollama'ya ulaşamazsa güvenlik duvarında 11434 portuna izin vermeniz gerekebilir. Ollama'yı da konteyner içinde çalıştırmak isterseniz Open WebUI'nin Ollama'yı gömülü getiren `ghcr.io/open-webui/open-webui:ollama` imajı tek başına yeterlidir; bu durumda GPU erişimi için komuta `--gpus all` ekleyin.
:::

## Performans ipuçları

- **GPU'ya katman taşıma:** Ollama, VRAM elverdiğince katmanları GPU'ya otomatik taşır; kalan katmanlar RAM'de çalışır. Yani model VRAM'den büyükse de çalışır, sadece yavaşlar. Zorlamak veya sınırlamak için Modelfile'a `PARAMETER num_gpu 99` (tümü) ya da daha düşük bir katman sayısı ekleyin.
- **Bağlam boyutu:** Varsayılan bağlam penceresi modelden değil, makinenizin belleğinden gelir: 2026 itibarıyla Ollama, 24 GB altı VRAM'de 4096, 24-48 GB aralığında 32 bin, 48 GB ve üzerinde 256 bin token varsayılanı kullanır. Servis genelindeki varsayılanı `OLLAMA_CONTEXT_LENGTH` ortam değişkeniyle değiştirebilir, Modelfile'da `PARAMETER num_ctx 8192` gibi bir değerle model bazlı sabitleyebilirsiniz; her artış bellek tüketimini yükseltir.
- **İzleme ve tanı:** `ollama ps` komutu, yüklü modelin GPU'da mı yoksa kısmen CPU'da mı çalıştığını ve ne kadar bellek kullandığını gösterir; `ollama run benim-model --verbose` ile saniyedeki token hızını görebilirsiniz. Modelde beklenmeyen davranışlar görürseniz `ollama show benim-model --modelfile` çıktısı, etkin Modelfile'ı (parametreler, sohbet şablonu, sistem istemi) yazdırır ve teşhise doğrudan yol gösterir. Windows'ta Görev Yöneticisi ve `nvidia-smi` VRAM takibi için işe yarar.
- **Hız sorularını ölçerek yanıtlayın:** Cevabın neden 3-60 saniye sürdüğünü fazlara ayıran ölçüm (soğuk yükleme 3,1 sn, ön-yükleme ~40 tok/sn, çözme ~14 tok/sn, `num_ctx` bellek basamakları, önbellek kazancı) [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasında. Aynı sayfadaki bir bulgu buradaki örnekleri de ilgilendiriyor: Windows'ta `http://localhost:11434` adresi **her istekte ~2,03 sn** isim çözümleme gideri ekliyor; `http://127.0.0.1:11434` ile bu **0,00 sn**. Çok çağrılı döngülerde (RAG indeksleme gibi) tek kelimelik değişiklik ölçülebilir fark yaratıyor.
- **Örnekleme ve bitiş ayarları:** `temperature`, `top_k`, `top_p`, `min_p`, `num_predict`, `stop` ve `format` alanlarının ne yaptığı, belge varsayılanlarının nerede yazdığı ve kendi modelinize gömülü bir örnekleme ayarı olup olmadığını nasıl okuyacağınız: [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/).

## Kaynaklar ve İleri Okuma

- [Ollama Blog](https://ollama.com/blog/) — Yeni motor, bulut modelleri ve MLX gibi özelliklerin birincil duyuru kanalı.
- [Ollama Sürüm Notları](https://github.com/ollama/ollama/releases/) — Sürüm sürüm değişiklik listesi; Ekim 2026 itibarıyla v0.40 hattı.
- [Ollama Belgeleri: Bağlam Uzunluğu](https://docs.ollama.com/context-length/) — VRAM'e göre varsayılan bağlam değerleri ve `OLLAMA_CONTEXT_LENGTH` kullanımı.
- [Ollama API Referansı](https://docs.ollama.com/api/) — `/api/chat`, `/api/generate`, `/api/embeddings` uç noktaları ve OpenAI uyumluluk tablosu.
- [Hugging Face: Use Ollama with any GGUF Model](https://huggingface.co/docs/hub/ollama/) — `ollama run hf.co/...` sözdizimi, nicemleme seçimi ve özel (private) depo erişimi.
- [Ollama Bulut Modelleri Duyurusu](https://ollama.com/blog/cloud-models/) — `-cloud` etiketi ve oturum açma akışının tanıtıldığı yazı.
- [Ollama Thinking Duyurusu](https://ollama.com/blog/thinking/) — `--think` bayrağı ve API'deki `"think"` parametresi.
- [Open WebUI Deposu](https://github.com/open-webui/open-webui/) — pip ve Docker kurulum komutlarının resmî kaynağı.

## Sonraki adımlar

- Modelinizi profesyonel biçimde sunmak için: [Model Sunma: vLLM ve API](/kullanim/sunma-api/)
- Nicemlenmiş modelin kalitesini ölçmek için: [Benchmarklar ve Değerlendirme](/degerlendirme/benchmarklar/)
- Modeli toplulukla paylaşmak için: [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/)
