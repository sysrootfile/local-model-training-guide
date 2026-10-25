---
title: "Yol Haritası: Hangi Yöntemi, Hangi Donanımla Seçmeliyim?"
description: "Donanımınıza, hedefinize ve bütçenize göre hangi model eğitimi yöntemini seçeceğinizi karar ağacı, karşılaştırma tabloları ve gerçek senaryolarla anlatıyoruz."
dogrulama: 2026-10-15
---

Model eğitimi dünyasında en pahalı hata yanlış yöntemle başlamaktır: 4 GB VRAM'li bir kartla 8B modeli tümüyle eğitmeye çalışmak ya da GPU kiralayıp aslında klasik makine öğrenmesiyle çözülecek bir problemi çözmeye uğraşmak gibi. Bu sayfanın amacı, sizi **ilk günden doğru yola** sokmak.

## Doğru Seçim Üç Soruda

Hangi yöntemi seçeceğinizin cevabı üç sorunun kesişiminde:

1. **Elimde ne var?** Donanımınız üst sınırı belirler. GPU yok, 6 GB VRAM, 12 GB, 24 GB, çoklu GPU... Cevabı ölçmenin yolu: [VRAM Hesabı](/donanim/vram-hesabi/).
2. **Ne istiyorum?** Türkçe sohbet botu mu, alan bilgisi mi, üslup mu, görsel üretim mi, tablo verisiyle tahmin mi? Hedef, eğitilecek modelin boyutunu ve veri ihtiyacını belirler.
3. **Ne kadar zaman ve para harcayabilirim?** Yerel eğitim ücretsizdir ama yavaştır; bulut hızlıdır ama saatlik ücretlidir. Karşılaştırma: [Bulut Seçenekleri](/donanim/bulut-secenekleri/).

:::tip[Etkileşimli alternatif]
Ana sayfadaki etkileşimli "yöntem seçici" de aynı soruları sorarak size öneri veriyor: [Ana sayfa](/). Bu sayfa ise gerekçeleriyle birlikte tam karar rehberidir.
:::

## Karar Ağacı

Aşağıdaki diyagram, tipik bir kullanıcının donanımdan yönteme giden yolunu özetler. Kendi durumunuzu bulun ve ok işaretini takip edin:

```text title="Basitleştirilmiş yöntem seçim ağacı"
Başla
│
├── GPU'm var mı?
│   │
│   ├── HAYIR
│   │   ├── Amacım öğrenmek/denemek ───────► Kaggle (~haftada 30 saat ücretsiz GPU)
│   │   │                                     veya Google Colab (ücretsiz T4)
│   │   ├── Amacım tablo verisiyle tahmin ──► Klasik ML — CPU yeterli
│   │   │                                     /klasik-ml/ilk-model/
│   │   └── Amacım ciddi model eğitmek ─────► Bulut GPU kiralama (RunPod, Vast.ai)
│   │                                         /donanim/bulut-secenekleri/
│   │
│   └── EVET — VRAM kaç GB?
│       ├── 4-6 GB   ──► 0,5-2B model + QLoRA (yerel)
│       │                ya da bulutta 4B QLoRA
│       ├── 8-12 GB  ──► 4B QLoRA rahat; 3B LoRA
│       ├── 16-24 GB ──► 7-8B QLoRA; 8B LoRA
│       ├── 24 GB+   ──► 13-14B LoRA (QLoRA ile)
│       └── 48 GB+ / çoklu GPU ──► 13-14B LoRA rahat; daha büyük denemeler
│
└── Hedefim ne?
    ├── Türkçe sohbet asistanı ──────► Talimat verisiyle SFT (LoRA/QLoRA)
    ├── Alan bilgisi (hukuk/tıp/teknik) ► SFT + kaliteli alan verisi (RAG'i de değerlendir)
    ├── Üslup/format öğretmek ────────► Küçük ama tutarlı veriyle LoRA
    ├── Görsel üretim ────────────────► Difüzyon modeli + LoRA
    └── Tablo verisiyle tahmin ───────► Klasik ML (scikit-learn, XGBoost)
```

## Tablo 1 — Donanıma Göre Ne Eğitilir?

Aşağıdaki tablo, "yerel olarak rahat" kolonundakilerin sorunsuz çalıştığı, "sınırda" kolonundakilerin ise küçük batch ve sabır gerektirdiği pratik aralıkları gösterir. Bellek hesabının ayrıntısı [VRAM Hesabı](/donanim/vram-hesabi/) sayfasında.

| Donanım (VRAM) | Yerel olarak rahat | Sınırda (küçük batch) | Önerilen yol |
| --- | --- | --- | --- |
| GPU yok | Klasik ML (CPU) | — | Kaggle/Colab ile ücretsiz GPU ya da saatlik bulut kiralama |
| 4-6 GB | 0,5-2B modelde QLoRA | 3B QLoRA | Yerelde küçük deneyler + bulutta 4B QLoRA |
| 8-12 GB | 3-4B QLoRA, 3B LoRA | 7B QLoRA (çok küçük batch) | Unsloth ile yerel QLoRA — en tatlı nokta |
| 16-24 GB | 7-8B QLoRA, 8B LoRA | 13B QLoRA | Yerel ciddi projeler |
| 24 GB+ | 13-14B LoRA rahat | 30B+ QLoRA | Üretim seviyesi işler |
| Çoklu GPU / bulut | 30B+ LoRA, küçük full fine-tuning | — | Kiralık H100/H200 ile büyük denemeler |

:::caution["Rahat" ne demek?]
Tablodaki "rahat", eğitimin çökmeyecek kadar bellek bulduğu anlamına gelir; hız garanti değildir. 12 GB bir kartta 4B QLoRA modeli saatler sürebilirken bulutta aynı iş dakikalar sürebilir. Hız, kartın nesline (ör. RTX 3060 ile 4090 arasında büyük fark vardır) ve eğitim yazılımına bağlıdır.
:::

## Tablo 2 — Hedefe Göre Hangi Yöntem?

| Hedef | Önerilen yaklaşım | Başlangıç sayfası |
| --- | --- | --- |
| Türkçe sohbet asistanı | Talimat verisiyle SFT + QLoRA (Qwen3-4B/8B ile başlayın) | [SFT](/llm/sft/) |
| Alan bilgisi öğretme (hukuk, tıp, teknik) | Alan verisiyle SFT; güncel bilgi için RAG ile birlikte düşünün: [RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/) | [Kendi verini oluştur](/veri/kendi-verini-olustur/) |
| Üslup ve format öğretme | 100-1.000 tutarlı örnekle LoRA; en kolay ve en başarılı senaryo | [LoRA ve QLoRA](/llm/lora-qlora/) |
| Görsel üretim (stil, karakter, nesne) | Difüzyon modeline LoRA eğitimi | [Görsel LoRA Eğitimi](/gorsel/lora-egitimi/) |
| Tablo verisiyle tahmin | Klasik ML — çoğu durumda LLM'den daha isabetli ve hızlı | [İlk Model](/klasik-ml/ilk-model/) |
| Araştırma / merak | Küçük ölçekli ön eğitim denemesi (tek GPU, birkaç saat) | [Ön Eğitim](/llm/pretraining/) |

## Araç Seçimi: Hangi İş İçin Hangi Araç?

Yönteme karar verdikten sonra sıra araca gelir. 2026 itibarıyla öne çıkan seçenekler ve uygun oldukları durumlar:

| Araç | Kimin için? | Karakteri |
| --- | --- | --- |
| Unsloth | Tek GPU'lu bireysel kullanıcılar | Hız ve kolaylık odaklı; ilk QLoRA deneyimi için en pratik başlangıç |
| Axolotl | Üretim işleri, çoklu GPU, tekrarlanabilirlik isteyenler | YAML konfigürasyon dosyasıyla yönetim; sürüm kontrolüne uygun |
| LLaMA-Factory | Kod yazmak istemeyenler, GUI arayanlar | Web arayüzü + komut satırı; 100'den fazla model desteği |
| HF TRL | Kod içinde tam kontrol isteyenler | Hugging Face'in SFT/DPO/GRPO eğitimcileri; kütüphane düzeyinde esneklik |
| PEFT + bitsandbytes | Altyapıyı elle kurmak isteyen ileri seviye | LoRA ve 4-bit katmanların çekirdeği; diğer araçların çoğu bunun üstüne kurulu |

:::tip[Hangisiyle başlamalı?]
İlk eğitiminiz için Unsloth (hızlı sonuç) ya da LLaMA-Factory (arayüz) en yumuşak seçeneklerdir. Tekrarlanabilir, senaryolaştırılmış üretim hattı kuracaksanız Axolotl'a geçin. Araçların karşılaştırması: [Araçlar](/llm/araclar/).
:::

## Gerçek Senaryolar: Dört Tipik Yol

Soyut tablolar yerine dört tipik kullanıcı profiline bakalım. Kendinize en yakın olanın adımlarını izleyebilirsiniz.

### Senaryo A — "GTX 1650 4 GB kartım var, Türkçe sohbet botu istiyorum"

4 GB VRAM yerelde yalnızca 0,5-2B modellerde QLoRA'ya izin verir; kaliteli bir Türkçe sohbet asistanı için biraz dar. En pratik çözüm: eğitimi bulutta yapmak. Google Colab'in ücretsiz T4'ü veya RunPod'da saatlik bir RTX 4090, Qwen3-4B'yi QLoRA ile rahatça eğitir (2026 itibarıyla RunPod 4090 yaklaşık $0,34/saat'ten başlıyor; güncel fiyatı kontrol edin).

1. [Temel Kavramlar](/baslangic/kavramlar/) — QLoRA ve SFT ne demek, öğrenin.
2. [Türkçe veri kaynakları](/veri/veri-nereden-bulunur/) — hazır Türkçe talimat setlerini inceleyin (ör. Hugging Face'teki `atasoglu/turkish-instruction-datasets` koleksiyonu).
3. [Veri Temizleme](/veri/veri-temizleme/) — hazır setler bile temizlik ister.
4. [Bulut Seçenekleri](/donanim/bulut-secenekleri/) — Colab mi, kiralık GPU mu?
5. [LoRA ve QLoRA](/llm/lora-qlora/) ve [Adım Adım Eğitim](/llm/adim-adim-egitim/) — eğitimi çalıştırın.
6. [Benchmarklar](/degerlendirme/benchmarklar/) — sonucu ölçün.
7. [LoRA Birleştirme](/kullanim/lora-birlestirme/) ve [Ollama](/kullanim/ollama/) — modeli kendi bilgisayarınızda çalıştırın.

### Senaryo B — "RTX 3060 12 GB ile modelime kendi üslubumu öğretmek istiyorum"

12 GB, bu işin yerel tatlı noktasıdır: Unsloth ile 4B QLoRA rahat, 7-8B QLoRA sınırda ama mümkün. Üslup öğretmek için gereken veri azdır (100-1.000 örnek), bu yüzden tek oturumda sonuç alabilirsiniz.

1. [Yerel Kurulum](/donanim/yerel-kurulum/) — ortamı kurun.
2. [Kendi Verini Oluştur](/veri/kendi-verini-olustur/) — üslup örneklerinizi toplayın (mevcut yazılarınız harika bir kaynaktır).
3. [Araçlar](/llm/araclar/) — Unsloth'u tanıyın.
4. [LoRA ve QLoRA](/llm/lora-qlora/) → [Hiperparametreler](/llm/hiperparametreler/) → [Adım Adım Eğitim](/llm/adim-adim-egitim/).
5. [Sorun Giderme](/llm/sorun-giderme/) — eğitim beklenmedik davranırsa (mutlaka olacak) buraya dönün.
6. [Sunma ve API](/kullanim/sunma-api/) — modeli kendi uygulamanıza bağlayın.

### Senaryo C — "GPU'm yok, sadece öğrenmek istiyorum"

Hiçbir şey satın almadan ilerleyebilirsiniz. İki ayaklı bir plan izleyin: klasik makine öğrenmesini CPU'da öğrenin, LLM tarafını ise Kaggle'ın haftada yaklaşık 30 saatlik ücretsiz GPU kotasıyla deneyin.

1. [Klasik ML Temelleri](/klasik-ml/temeller/) → [İlk Model](/klasik-ml/ilk-model/) — GPU'suz, gerçek bir model eğitin.
2. [Tokenizasyon](/temeller/tokenizasyon/) — LLM'lerin dünyasına giriş.
3. [Bulut Seçenekleri](/donanim/bulut-secenekleri/) — Kaggle ve Colab'in kurallarını öğrenin.
4. [Adım Adım Eğitim](/llm/adim-adim-egitim/) — Kaggle notebook'unda küçük bir QLoRA deneyi yapın (1.000 örnek, küçük model).
5. [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) — eğitim eğrilerini okumayı öğrenin.

### Senaryo D — "Şirket verisiyle alan modeli eğitmem gerekiyor"

Bu senaryoda kod yazmaktan çok **veriyle** uğraşırsınız; gerçekçi olmak gerekirse işin %70-80'i veri hazırlığıdır. Model tarafında talimat verisiyle SFT (LoRA ile) başlangıç için yeterlidir; değerlendirme baştan planlanmalıdır.

1. [Veri Türleri](/veri/veri-turleri/) — elinizdeki veri hangi kategoriye giriyor?
2. [Kendi Verini Oluştur](/veri/kendi-verini-olustur/) + [Veri Temizleme](/veri/veri-temizleme/) + [Veri Formatları](/veri/veri-formatlari/).
3. [SFT](/llm/sft/) — talimat verisiyle eğitim kurgusu.
4. [Hiperparametreler](/llm/hiperparametreler/) — şirket GPU'suna göre ayar.
5. [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) ve [Benchmarklar](/degerlendirme/benchmarklar/) — "iyi" tanımınızı ölçün.
6. [Sunma ve API](/kullanim/sunma-api/) ve [Hugging Face Paylaşımı](/kullanim/huggingface-paylasim/) (şirket içi depo da olabilir).

## Zaman ve Maliyet Beklentileri

:::note[Tipik çalışma süreleri]
- **QLoRA eğitimi:** 1.000-5.000 örnekle, donanıma göre **30 dakika ile 6 saat** arası. Aynı iş ücretsiz Colab'de saatler sürerken, kiralık bir 4090'da 1 saatin altına inebilir.
- **Veri hazırlığı:** Çoğu projede eğitimin kendisinden **uzun sürer**. Sıfırdan veri topluyorsanız günler, hazır seti uyarlıyorsanız saatler.
- **Değerlendirme ve iterasyon:** İlk eğitim genellikle son eğitim değildir; 2-4 tur deneme-normaldir.
- **Maliyet örneği (2026 itibarıyla, değişebilir):** Vast.ai'de RTX 4090 saatlik yaklaşık $0,14-0,45; RunPod'ta 4090 yaklaşık $0,34'ten başlar. 4 saatlik bir eğitim kirası kabaca 1-2 dolara denk gelir. Güncel fiyatları mutlaka kontrol edin.
:::

Ayrıca ücretsiz seçenekleri küçümsemeyin: Google Colab ücretsiz sürümde T4 sunar (Pro yaklaşık $10/ay), Kaggle ise haftada yaklaşık 30 saat ücretsiz GPU verir. Bu kotayla küçük modellerde gerçek deneyler yapabilirsiniz: [Bulut Seçenekleri](/donanim/bulut-secenekleri/).

## Klasik ML'i Unutmayın

Hedefiniz tablo verisiyle tahminse (satış tahmini, müşteri kaybı, sınıflandırma), LLM tarafına hiç girmenize gerek yok. Klasik modeller bu işlerde çoğu zaman daha isabetli, kat kat hızlı ve bedavadır. Başlangıç: [Klasik ML Temelleri](/klasik-ml/temeller/) ve [İlk Model](/klasik-ml/ilk-model/).

:::tip[Sıradaki adım]
Kararınızı verdiniz mi? Bulut mu yerel mi kararınızı netleştirmek için [Bulut Seçenekleri](/donanim/bulut-secenekleri/), bellek hesabı için [VRAM Hesabı](/donanim/vram-hesabi/), ilk eğitiminiz için [Adım Adım Eğitim](/llm/adim-adim-egitim/) sayfasına geçin. Hâlâ kararsızsanız ana sayfadaki etkileşimli seçiciyi deneyin: [Ana sayfa](/).
:::
