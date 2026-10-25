---
title: "Nicemleme (Quantization): Modeli Küçültmek"
description: "Model ağırlıklarını 4-8 bite sıkıştırmanın mantığı; GGUF, AWQ, GPTQ ve NF4 formatlarının karşılaştırması ve pratik dönüşüm komutları."
dogrulama: 2026-10-18
---

Eğittiğiniz 8B'lik model, fp16 haliyle yaklaşık 16 GB tutuyor ve 12 GB'lık ekran kartınıza sığmıyor. Ya da indirdiğiniz bir model diskinizi doldurdu. Çözümün adı **nicemleme (quantization)**: model ağırlıklarını daha az bit ile temsil ederek boyutu ve bellek ihtiyacını büyük ölçüde küçültmek.

:::note
Nicemleme modelin kendisini değil, modelin **sayı temsilini** değiştirir. En yaygın kullanımı eğitim *sonrası* yapılan "eğitim sonrası nicemleme"dir (post-training quantization); bu sayfada onu anlatıyoruz.
:::

## Sezgi: FLAC değil, MP3

Bir modelin ağırlıkları aslında sadece ondalık sayılardır. `0.00348291...` gibi sayıları saklamak için bilgisayar fp16'da 16 bit, fp32'de 32 bit kullanır. Nicemleme, bu sayıları daha küçük bir ızgaraya oturtur: 4-bit'te her ağırlık için geriye yalnızca 16 olası seviye kalır.

İşe yarayan benzetme: **fp16 kayıpsız FLAC dosyası, 4-bit ise MP3'tür.** Kulakların çoğu farkı fark etmez, dosya ise üçte birine iner. Aynı şekilde, ılımlı nicemleme seviyelerinde modelin yeteneği çoğu görevde korunur.

Kaba boyut hesabı (model parametresi P milyar olsun):

| Seviye | 8B model için yaklaşık boyut | Kural |
|---|---|---|
| fp16 (nicemlenmemiş) | ~16 GB | P × 2 GB |
| Q8 | ~8,5 GB | P × 1,1 GB |
| Q5 | ~5,5 GB | P × 0,7 GB |
| Q4 | ~4,7 GB | P × 0,6 GB |
| Q2/Q3 | ~3-4 GB | P × 0,4 GB |

Sayılar modele ve seviye varyantına göre değişir; amaç büyüklük hissi vermek. Aynı hesap bir modeli çalıştırmak için gereken VRAM tahmininde işinize yarar; ayrıntılar için [VRAM Hesabı](/donanim/vram-hesabi/) sayfasına bakın.

## Formatlar: hangisi nerede çalışır?

| Format | Nerede çalışır | Kim üretir | Tipik kullanım |
|---|---|---|---|
| **GGUF** | llama.cpp, Ollama, LM Studio, llama-cpp-python | llama.cpp araçları, Unsloth | Kişisel/yerel çalıştırma; CPU + GPU karışık |
| **GPTQ** | GPU (vLLM, TGI) | GPTQ araç zinciri | Eski GPU sunum kurulumları; AutoGPTQ deposu 2025'te arşivlendi, topluluk GPTQModel'e yönelmiş durumda |
| **AWQ** | GPU (vLLM, TGI) | AWQ araç zinciri | Modern GPU sunumu, vLLM üretimi |
| **FP8** | vLLM; FP8 hesaplaması için compute capability 8.9+ GPU (Ada/Hopper, ör. H100) | vLLM yerleşik | Veri merkezi sınıfı kartlarda hızlı sunum |
| **bitsandbytes NF4** | Eğitim (transformers + PEFT) | bitsandbytes | QLoRA: eğitim sırasında 4-bit yükleme |

:::tip Ezberden çıkarın
- Ollama / LM Studio ile kişisel kullanım → **GGUF**
- vLLM ile sunucu → **AWQ** (alternatif: GPTQ; Hopper sınıfı kart varsa FP8)
- Eğitim sırasında VRAM darlığı → **bitsandbytes (NF4)**
:::

vLLM 2026 itibarıyla AWQ, GPTQ, FP8, bitsandbytes ve GGUF nicemlenmiş modelleri doğrudan sunabiliyor; güncel destek listesini vLLM'in quantization dokümanından kontrol edin. Sunum tarafının ayrıntıları için [Model Sunma: vLLM ve API](/kullanim/sunma-api/) sayfasına bakın. FP8 özel bir durumdur: FP8 *hesaplaması* compute capability 8.9 ve üzeri (Ada Lovelace, Hopper; ör. H100) kart ister; FP8 nicemli bir model Ampere sınıfı kartlarda ağırlık-only kipte çalışabilir.

Son satır özellikle önemli: **bitsandbytes 4-bit bir dağıtım formatı değildir.** QLoRA'da yalnızca eğitimi mümkün kılmak için kullanılır; eğitim bitince adaptörü [birleştirirsiniz](/kullanim/lora-birlestirme/) ve dağıtım için isterseniz ayrıca nicemlersiniz.

### NF4 ile GGUF aynı şey değildir

NF4 (NormalFloat4), QLoRA makalesinden gelen 4-bit veri tipidir ve model belleğe yüklenirken `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")` ile uygulanır. Diskte duran bir dosya üretmez; "NF4 model dosyası" diye paylaşılacak bir şey yoktur. GGUF ise tam tersine diskte duran, llama.cpp ekosisteminin dağıtım formatıdır. Pratik sonuç: QLoRA ile eğittiniz → adaptörü birleştirdiniz → GGUF üretip öyle dağıttınız.

bitsandbytes'tan bilmeye değer iki ayrıntı: çift nicemleme (`bnb_4bit_use_double_quant=True`) ağırlık başına yaklaşık 0,4 bit ekstra tasarruf sağlar; NF4/FP4 nicemlemesi Pascal sınıfı ve üzeri NVIDIA kartlarda çalışır. Belgelerin vurgusu da önemlidir: 8-bit ve 4-bit kipte yalnızca *ekstra* parametreler (yani LoRA adaptörleri) eğitilebilir; taban ağırlıkları 4-bit kipte güncelleyemezsiniz. QLoRA akışının tamamı için [LoRA ve QLoRA](/llm/lora-qlora/) sayfasına bakın.

## Karar ağacı

```text
Nasıl çalıştıracaksın?
│
├─ Ollama / LM Studio (kişisel kullanım) ──► GGUF
│     ├─ Dengeli başlangıç ................ Q4_K_M
│     ├─ Kalite öncelikli ................. Q5_K_M veya Q6_K
│     └─ Yer bol, kayıp istemiyorum ...... Q8_0
│
├─ vLLM / TGI (sunucu, çok kullanıcı) ─────► AWQ (tercih) veya GPTQ
│
└─ Eğitim sırasında VRAM yetmiyor ─────────► bitsandbytes NF4 (QLoRA)
      (Dağıtım formatı değil; eğitim sonrası birleştir + nicemle)
```

Aynı kararın tablo hali:

| Format | Ne zaman seçin | Kalite / hız dengesi | Araç uyumu |
|---|---|---|---|
| **GGUF** | Kişisel kullanım, Ollama/LM Studio, CPU+GPU karışık | Q4_K_M/Q5_K_M'de dengeli; CPU'da en geniş destek | llama.cpp ekosistemi, Unsloth |
| **NF4 + bitsandbytes** | Yalnızca eğitim sırasında VRAM açmak için | Eğitim amaçlı; dağıtıma uygun değil | transformers + PEFT |
| **AWQ / GPTQ** | GPU sunum, çok kullanıcılı servis | 4-bit sunum için olgun çözümler | vLLM, TGI |
| **FP8** | Hopper/Ada sınıfı kartlarda yüksek verimli sunum | 8-bit; FP8 hızlandırması donanım ister | vLLM |

Kural basit: **eğitimde NF4, yerelde GGUF, sunucuda AWQ/GPTQ/FP8.**

## GGUF seviyeleri: Q4_K_M'deki harfler ne demek?

GGUF dosya adlarındaki kodlar kısaca şöyledir:

- **Q4 / Q5 / Q8**: ağırlık başına bit sayısı (4 bit, 5 bit, 8 bit...).
- **K**: "k-quant" — hassas katmanlara daha çok, dayanıklı katmanlara daha az bit veren akıllı dağıtım şeması.
- **\_M / \_S**: aynı seviyedeki kalite/boyut varyantları (M = medium, S = small).

Sık görülen seviyeler:

| Seviye | Kalite | Tavsiye |
|---|---|---|
| Q2_K, Q3_K | Belirgin kayıp | Zorunlu kalmadıkça kullanmayın |
| **Q4_K_M** | Çok iyi denge | **Varsayılan öneri**; çoğu kişi burada durur (llama.cpp nicemleyicisinin de varsayılanı budur) |
| Q5_K_M | fp16'ya çok yakın | Bellek elveriyorsa tercih edin |
| Q6_K | Neredeyse kayıpsız | Kalite odaklıysanız |
| Q8_0 | Fark edilemez | Yer bolsa; pratikte kayıpsız sayılır |

Şema ailelerini ayırt etmek dosya adlarını okumayı kolaylaştırır. llama.cpp dokümanı üç aileden söz eder:

- **Klasik (legacy) şemalar** (`Q4_0`, `Q5_0` gibi): ilk nesil; blok başına tek ölçek kullanan basit şema.
- **K-quant'lar** (`Q2_K` ... `Q6_K`): katman türüne göre farklı blok ve ölçek düzeni kullanan şema; bugün dengeli seviyelerin ana ailesi.
- **i-quant'lar** (`IQ2_XXS`, `IQ3_XXS`, `IQ4_XS` gibi): "importance" kavramı etrafında kurgulanan aile; özellikle 2-4 bit gibi agresif aralıkta, düşük boyutta kaliteyi korumayı hedefler.

:::caution
İki ileri seviye önerinin karışmaması için: Q4_K_M gibi **K-quant** seviyeleri her modele uyar ve ekstra adım istemez; i-quant seviyeleri ise en iyi değerine önem matrisiyle (aşağıda) ulaşır. Yeni başlıyorsanız Q4_K_M ile kalın.
:::

### imatrix: önem matrisiyle nicemleme

llama.cpp'nin `llama-imatrix` aracı, modeli bir örnek metin derleminden geçirip ağırlıkların çıktıya katkısını ölçen bir **önem matrisi (importance matrix)** üretir. `llama-quantize` bu matrisi `--imatrix` bayrağıyla aldığında, hangi ağırlıkları hangi hassasiyette bırakacağını kabaca değil bu ölçüme dayanarak seçer. i-quant seviyeleri bu matrisle birlikte tasarlandı; K-quant'larla da kullanılabilir. Tipik akış:

```bash title="imatrix_ornegi.sh"
# 1) Önem matrisini hesapla (Türkçe kullanım için derlem Türkçe olsun)
./llama-imatrix -m model-f16.gguf -f ornek-metin.txt -o imatrix.gguf

# 2) Matrisi kullanarak i-quant seviyesinde nicemle
./llama-quantize --imatrix imatrix.gguf model-f16.gguf model-IQ4_XS.gguf IQ4_XS
```

Bayrak adları sürüme göre değişebilir; araçların `--help` çıktısına bakın. Nicemlemenin güncel resmi dokümanı depoda `tools/quantize/README.md` altındadır. Topluluk pratiğinde matris için eğitim verinize benzeyen ya da hedef dili kapsayan bir derlem kullanılır; model Türkçe için eğitildiyse Türkçe metin vermek mantıklıdır.

### Dinamik (UD) nicemlemeler: haber düzeyinde

Sabit seviyelerin (her katmana aynı bit) dışında bir de "dinamik" yaklaşım vardır: Unsloth'un Dynamic (UD) nicemlemeleri her katmana ayrı nicemleme tipi seçer; şirket bunu "seçici olarak katmanları nicemler, her katmanın nicemleme tipini dinamik ayarlar" diye tanıtır ve aynı disk boyutunda daha yüksek doğruluk iddia eder (satıcının kendi ölçümüdür). Haberin değeri şurada: Ocak 2025'te Unsloth, 671B parametreli DeepSeek-R1'in 1,58-bit (UD-IQ1_S) ve 1,78-bit (UD-IQ1_M) GGUF varyantlarını yayımladı; amaç, tam haliyle terabayt ölçeğinde bellek isteyen bu modeli yüksek RAM'li iş istasyonlarında, büyük ölçüde CPU yüküyle de olsa çalıştırılabilir kılmaktı. Bu uç seviyeler kalite açısından denge noktası değildir; yeni başlayan biri için Q4_K_M / Q5_K_M hâlâ doğru tercihtir.

## Dönüştürme: Hugging Face modelinden GGUF'a

Ön koşul: Elinizde **birleştirilmiş** bir HF modeli olmalı (modeliniz adaptörlüyse önce [LoRA Birleştirme](/kullanim/lora-birlestirme/)). Akış: HF modeli → ara GGUF (fp16) → nicemlenmiş GGUF.

```bash title="gguf_donustur.sh"
# 1) llama.cpp deposunu klonla (dönüştürme betikleri ve nicemleyici için)
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# 2) Dönüştürme betiğinin Python bağımlılıklarını kur
pip install -r requirements.txt

# 3) HF modelini fp16 ara GGUF'a çevir
python convert_hf_to_gguf.py ../birlestirilmis-model \
    --outfile model-f16.gguf \
    --outtype f16

# 4) Ara dosyayı Q4_K_M seviyesine nicemle
./llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

Birkaç not:

- Dönüştürme betiğinin `--outtype` seçenekleri `f32`, `f16`, `bf16` ve `q8_0` (ve bazı teraryal tipler) ile sınırlıdır; K-quant ve i-quant seviyeleri için `llama-quantize` adımı gerekir.
- Birden çok varyant üretmek isterseniz 3. ve 4. adımı farklı seviyelerle tekrarlamanız yeterli (Q4_K_M, Q5_K_M, Q8_0...).
- Tek seferlik dönüşüm için tüm depoyu derlemeniz şart değil; ama nicemleyici aracı asıl işi yapan parçadır.

:::tip Windows kullanıyorsanız
llama.cpp'yi derlemek zorunda değilsiniz: GitHub Releases sayfasındaki hazır Windows paketlerinden (CPU ya da CUDA sürümü) birini indirip açın; içindeki `llama-quantize.exe` doğrudan çalışır. Kendiniz derlemek isterseniz çalıştırılabilirler `build\bin\Release` altına çıkar.
:::

### Unsloth ile tek satırda GGUF

Eğitimi Unsloth ile yaptıysanız dönüşümü de o halleder:

```python title="unsloth_gguf.py"
# Unsloth, adaptörü otomatik birleştirip GGUF üretir (arka planda llama.cpp kullanır)
model.save_pretrained_gguf(
    "model_gguf",            # çıktı klasörü
    tokenizer,
    quantization_method = "q4_k_m",
)
```

Unsloth bazı ortamlarda llama.cpp yolunu kendisi ayarlar; "llama.cpp bulunamadı" türü bir hatayla karşılaşırsanız Unsloth belgelerindeki GGUF bölümüne bakın. Modeli doğrudan Hugging Face'e GGUF olarak göndermek de mümkündür (`push_to_hub_gguf`); bunu [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/) sayfasında ele alıyoruz.

### GGUF'u Python'dan çalıştırma

Dönüşen dosyayı hemen denemek isterseniz:

```bash
pip install llama-cpp-python
```

```python title="gguf_calistir.py"
from llama_cpp import Llama

llm = Llama(
    model_path="model-Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,   # tüm katmanları GPU'ya taşı; CPU'da 0 bırakın
)

cikti = llm.create_chat_completion(
    messages=[{"role": "user", "content": "Nicemleme nedir, bir cümleyle anlat."}]
)
print(cikti["choices"][0]["message"]["content"])
```

Günlük kullanım için en pratik yol ise [Ollama](/kullanim/ollama/) olacaktır.

## Kalite ne kadar düşer?

Merak edilen iki soru:

**1. Aynı modelin Q4'ü ile Q8'i arasında ne fark var?** Çoğu sohbet görevinde fark küçüktür; fark, çok adımlı akıl yürütme, matematik, kod ve az temsil edilen dillerde büyümeye başlar. Türkçe gibi İngilizce'ye kıyasla daha az veriye sahip dillerde nicemleme etkisi bazen daha görünür olabilir; kritik testlerde Q5_K_M'ye çıkmayı deneyin.

**2. "4-bit 8B mi, fp16 3B mi?"** Topluluk deneyimleri ve ölçümler genellikle nicemlenmiş **büyük** modelin, fp16 **küçük** modelden daha yetenekli kaldığını gösterir: bilgi büyük ölçüde parametre sayısıyla gelir ve Q4_K_M ılımlı bir sıkıştırmadır. İstisna, Q2/Q3 gibi agresif seviyelerdir; orada kalite kaybı bu farkı kapatabilir. Son kararı kendi görevlerinizde verin: [Benchmarklar ve Değerlendirme](/degerlendirme/benchmarklar/).

:::caution Son bir uyarı
Nicemleme, birleştirilmiş (fp16) model üzerinde yapılır. QLoRA adaptörünüzü nicemlenmiş bir taban modele merge etmeye çalışmak sık yapılan ve pahalıya patlayan bir hatadır; ayrıntılar [LoRA Birleştirme](/kullanim/lora-birlestirme/) sayfasında.
:::

## Kaynaklar ve İleri Okuma

- [llama.cpp — tools/quantize README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md): `llama-quantize` kullanımı, K-quant/i-quant ayrımı ve imatrix bayrağının resmi dokümanı.
- [llama.cpp deposu](https://github.com/ggml-org/llama.cpp): `convert_hf_to_gguf.py` dahil dönüştürme araçlarının ana kaynağı.
- [Transformers — bitsandbytes dokümanı](https://huggingface.co/docs/transformers/quantization/bitsandbytes): NF4, çift nicemleme ve 4-bit yükleme ayarlarının resmi açıklaması.
- [vLLM — Quantization](https://docs.vllm.ai/en/latest/features/quantization/index.html): vLLM'in doğrudan sunduğu nicemlenmiş formatların güncel listesi.
- [vLLM — FP8 W8A8](https://docs.vllm.ai/en/v0.6.4/quantization/fp8.html): FP8 için donanım (compute capability) koşullarını belirleyen doküman.
- [AWQ makalesi](https://arxiv.org/abs/2306.00978) ve [GPTQ makalesi](https://arxiv.org/abs/2210.17323): Aktivasyon duyarlı ve GPU sunum odaklı nicemleme yöntemlerinin özgün makaleleri.
- [QLoRA makalesi](https://arxiv.org/abs/2305.14314): NF4 veri tipini tanıtan özgün makale.
- [Unsloth — DeepSeek-R1 Dynamic 1.58-bit](https://unsloth.ai/blog/deepseekr1-dynamic): Dinamik (UD) düşük bit nicemlemelerin duyurulduğu blog yazısı.
- [Unsloth — Saving to GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf): Unsloth ile GGUF dışa aktarma adımlarının resmi belgesi.
- [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/): aynı modelin Q4'ü ile daha yüksek bitli bir sürümünün **güven dağılımları** karşılaştırması bu sitede ölçülmedi; o sayfanın "Ölçülmedi" listesinde duran kalemlerden biri, çünkü ikinci bir model indirmesi gerekiyor.

## Sonraki adımlar

- GGUF modelinizi Ollama'ya ekleyip sohbet etmek için: [Ollama ile Kendi Modelini Çalıştırma](/kullanim/ollama/)
- Çok kullanıcılı sunum için: [Model Sunma: vLLM ve API](/kullanim/sunma-api/)
- Modeli toplulukla paylaşmak için: [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/)
