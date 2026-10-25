---
title: "Difüzyon Modelleri: Görsel Üretim Nasıl Çalışır?"
description: Difüzyon modellerinin görsel üretme mantığını; VAE, UNet ve metin kodlayıcı gibi bileşenleri ile LoRA, DreamBooth gibi eğitim türlerini sezgisel olarak anlatıyoruz.
dogrulama: 2026-10-15
---

Bir modele "kırmızı kazaklı bir kedi, suluboya" yazıyorsunuz ve birkaç saniye sonra gerçekten öyle bir görsel geliyor. Peki perde arkasında ne oluyor? Bu sayfa, denklemler yerine sezgiyle, difüzyon (diffusion) modellerinin çalışma mantığını anlatıyor.

Bu rehberin ana odağı LLM'ler (büyük dil modelleri); ama görsel taraf da tanıdık bir akış izliyor: veri → eğitim → değerlendirme. Tek fark, burada "veri"nin görsel + açıklama olması.

## Ana fikir: gürültüyü sökmeyi öğrenmek

Difüzyon modelini anlamanın en kolay yolu iki analojidir:

- **Sisli camı silmek:** Önünüzde buğulanmış bir cam var ve arkasında bir fotoğraf duruyor. Her sildiğiniz hareket camı biraz daha netleştirir; sonunda fotoğraf ortaya çıkar. Difüzyon modeli de tam olarak bu "silme hareketlerini" öğrenir.
- **Kumdan heykel:** Heykeltıraş kuma bir şey eklemez; fazlalığı alır. Model de saf gürültüden yola çıkıp her adımda biraz "fazlalığı" (gürültüyü) atar.

Eğitim sırasında iş aslında tersine yapılır: modele milyonlarca kez "temiz görsel → biraz gürültülü görsel" çifti gösterilir ve model gürültüyü tanımayı öğrenir. Sonra üretim sırasında bu bilgi ters yönde kullanılır:

```text title="difüzyon fikri"
EĞİTİMDE (kolay iş — model bunu binlerce kez görür):
temiz görsel → +biraz gürültü → +biraz daha → ... → saf gürültü
                 (adım 1)          (adım 2)        (son adım)

ÜRETİMDE (zor iş — model eğitimde öğrendiği bilgiyi kullanır):
saf gürültü → gürültüyü tahmin et ve çıkar → ... → temiz görsel
```

:::note
Buradaki "gürültü", görüntüye pikseller düzeyinde eklenen rastgele bozulmadır. Modelin asıl görevi tek bir cümleyle: **"Bu görüntüdeki gürültü tam olarak ne? Söyle, ben çıkarayım."**
:::

## Metinden görsele akış

"Kırmızı kazaklı kedi" yazdığınızda görselin oluşması şu zincirden geçer:

```text
"kırmızı kazaklı kedi, suluboya"     (metin / prompt)
        │
        ▼
Metin kodlayıcı (text encoder — çoğunlukla CLIP)
        │  metni, modelin anlayacağı sayı vektörlerine çevirir
        ▼
Gürültüden arındırma modeli (UNet veya DiT — gürültü giderme/denoising)
        │  saf gürültüden başlar; her adımda "şu an hangi gürültü var?" diye
        │  tahmin edip çıkarır; metin vektörü her adımda yol gösterir
        │  tipik olarak 20-50 küçük adım sonunda ortaya "bulanık ama anlamlı"
        │  bir ara temsil (latent) çıkar
        ▼
VAE çözücü (decoder)
        │  küçük latent temsili, tam boyutlu piksel görsele çözer
        ▼
Görsel
```

Buradaki kilit fikir **latent uzay**: model, milyonlarca piksel üzerinde doğrudan çalışmaz. VAE, görüntüyü çok daha küçük bir sıkıştırılmış temsile indirir; difüzyon işlemi bu küçük "tuval" üzerinde yapılır. Bu, hem hızı hem de bellek kullanımını kat kat iyileştirir. "Latent difüzyon" adı da buradan gelir.

## Ana bileşenler

| Bileşen | Ne işe yarar? |
|---|---|
| **VAE** | Görseli sıkıştırılmış latent temsile çevirir (kodlayıcı) ve üretimin sonunda tekrar piksele çözer (çözücü). Modelin piksel yerine küçük bir temsille çalışmasını sağlar; böylece çok daha az bellekle çok daha hızlı üretim yapılır. |
| **UNet / DiT** (gürültü tahmincisi) | Difüzyonun kalbi ve eğitim sırasında güncellenen asıl parça budur. "Bu görüntüde hangi gürültü var?" sorusuna her adımda cevap verir; yeni bir görseli de bu bilgiyle adım adım temizler. |
| **Metin kodlayıcı** (Text Encoder) | Prompt'unuzu modele anlamlı gelen sayı vektörlerine çevirir; çoğu Stable Diffusion modelinde CLIP ailesinden bir model kullanılır. Yazdığınız kelimeler ile üretilecek görsel arasındaki tercümandır. |
| **Zamanlayıcı** (Scheduler) | Gürültüden arındırma sürecinin adım planını yönetir: kaç adım olacak, her adımda ne kadar gürültü çıkarılacak? Farklı zamanlayıcılar hız-kalite dengesini değiştirir. |

Metin kodlayıcının nasıl çalıştığına dair altyapı için [Transformer'lar](/temeller/transformer/) ve [Tokenizasyon](/temeller/tokenizasyon/) sayfalarına göz atabilirsiniz.

## Tipik bir üretim turu: perde arkasında 20-30 adım

"Kırmızı kazaklı kedi" prompt'uyla üretim başladığında sırasıyla şunlar olur:

1. Metin kodlayıcı, prompt'u bir kez vektöre çevirir.
2. Saf gürültüden rastgele bir başlangıç latenti oluşturulur.
3. Zamanlayıcı adımları sıralar. Her adımda UNet/DiT, "şu anki görüntüde hangi gürültü var?" diye tahmin eder; bu tahmini yaparken hem metin vektörüne hem de o anda hangi gürültü seviyesinde olduğuna bakar.
4. Tahmin edilen gürültü latentten çıkarılır; görüntü her adımda biraz daha netleşir ve "kırmızı kazaklı kedi" belirmeye başlar.
5. Son adımın ardından VAE çözücü, latenti piksel görsele çevirir.

Adım sayısı basit bir hız-kalite düğmesidir: 20 adım çoğu iş için fazlasıyla yeterlidir; 40-50 adım daha ince ayrıntı verir ama her ek adım süreye eklenir.

## Yönlendirme ölçeği (CFG) nedir?

Prompt'un görsel üzerindeki etki gücünü ayarlayan parametredir; çoğu arayüzde 7-8 civarı makul bir başlangıçtır. Düşük değerlerde model prompt'a gevşek uyar (yaratıcı ama dağınık, "prompt'u dinlemeyen" sonuçlar), çok yüksek değerlerde ise prompt'a aşırı yapışır (renkler doygunlaşır, kompozisyonlar tuhaf bozulmalar göstermeye başlar). Bir LoRA'nın farklı checkpoint'lerini karşılaştırırken CFG'yi ve tohum (seed) değerini sabit tutmak, gördüğünüz farkın gerçekten LoRA'dan geldiğinden emin olmanızı sağlar.

## Eğitim türleri: hangisi ne öğretir?

Bir modele yeni bir karakter, üslup veya nesne öğretmek istediğinizde dört temel yol vardır:

| Yöntem | Ne öğretir? | Kaç görsel? | Not |
|---|---|---|---|
| **LoRA** | Taban modele küçük bir "uzantı" ekleyerek karakter, üslup veya nesne öğretir. | 10-50 | En pratik yöntem; çıktı MB boyutunda tek bir dosya, taban model hiç değişmez. |
| **DreamBooth** | Belirli bir özneyi "bu benim kedim" düzeyinde öğretir. | 5-20 | LoRA'dan daha ağır; UNet'e daha geniş dokunuş yapar ve daha fazla VRAM ister. |
| **Textual Inversion** | Yeni bir kavramı birkaç bin kelimeden oluşan bir embedding olarak öğretir. | 3-10 | En hafif yöntem; dosya minicik ama etkisi ve esnekliği sınırlıdır. |
| **Tam ince ayar** (full fine-tune) | Taban modelin ağırlıklarının tamamını güncelleyip yeni bir model üretir. | Yüzler-den binler | Nadiren tercih edilir; büyük donanım ve büyük veri ister. Çoğu ihtiyaç için LoRA yeterlidir. |

:::tip
Kararsızsanız neredeyse her zaman doğru başlangıç **LoRA**'dır. Deneme maliyeti düşük, çıktısı tek dosya ve gerektiğinde farklı güçlerle (weight) kolayca karıştırılabilir. Adım adım uygulaması için [Kendi Görsel LoRA'nı Eğit](/gorsel/lora-egitimi/) sayfasına bakın.
:::

## Donanım: ne kadar VRAM gerekiyor?

| Ne eğitiyorsunuz? | Yerel minimum VRAM | Not |
|---|---|---|
| **SD 1.5 LoRA** | 6 GB+ | Batch 1, 512 çözünürlük ve mixed precision ile 6-8 GB'lı kartlarda rahatça eğitilir. |
| **SDXL LoRA** | 8-12 GB+ | 1024 çözünürlük nedeniyle daha aç; 12 GB ve üzeri rahat, 8 GB sınıfı optimizasyonlarla denenebilir. |
| **Flux LoRA** | 16-24 GB (veya bulut) | Flux, SD ailesinden çok daha büyük bir model; çoğu kullanıcı bulutta eğitir. |
| **Hepsinin alternatifi** | Bulut | Colab veya Kaggle'daki ücretsiz T4 ile özellikle SD 1.5 LoRA sorunsuzca eğitilebilir. |

:::caution[VRAM yetersizse]
Önce sayısal beklentiyi netleştirin: [VRAM hesabı](/donanim/vram-hesabi/). Kartınız yetmiyorsa bulut tam çözüm olabilir: [Bulut seçenekleri](/donanim/bulut-secenekleri/).
:::

Düşük VRAM'de eğitimin sırrı üç ayardır: **batch size 1** tutmak, **çözünürlüğü düşürmek** (SDXL'de bile 512'den başlanabilir) ve **mixed precision** (fp16/bf16) kullanmak.

## Sık karıştırılan kavramlar

| Karıştırılan | Fark |
|---|---|
| Difüzyon vs GAN | GAN'de üretici ve ayırt edici iki ağ birbirini yenmeye çalışır; difüzyonda tek bir ağ, "gürültü tahmini" gibi çok daha kararlı bir hedefe eğitilir. Görsel üretimde 2020'lerden itibaren difüzyon baskın hale gelmiştir. |
| Taban model vs LoRA | Taban model (ör. SDXL) gigabaytlar büyüklüğünde, genel amaçlı bir görsel üreticidir; LoRA onun üstüne takılan onlarca-yüzlerce MB'lık bir yamadır ve tek başına çalışmaz. |
| Latent vs piksel | Üretim döngüsü çoğunlukla latent uzayda döner; piksele çevirme işi en sonda VAE'nin görevidir. Bu yüzden "latent çözünürlüğü" ile "çıktı çözünürlüğü" farklı şeylerdir. |

## Ekosistem: hangi araç ne işe yarar?

- **diffusers** ([huggingface.co/docs/diffusers](https://huggingface.co/docs/diffusers)) — Hugging Face'in Python kütüphanesi. Kodu kontrol etmek, kendi eğitim betiklerini yazmak veya üretim hattı kurmak isteyenler için; SD, SDXL ve Flux'un tamamını destekler.
- **kohya_ss / sd-scripts** ([github.com/kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts), arayüz: [github.com/bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss)) — LoRA eğitiminin fiili standardı. Windows'ta Gradio tabanlı bir arayüz sunar; tıkladığınız alanların arkasında sd-scripts komutları çalışır.
- **ComfyUI** ([github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)) — Düğüm tabanlı arayüz. Karmaşık üretim iş akışlarını görsel bir şema olarak kurmayı ve tekrarlanabilir hâle getirmeyi sağlar.
- **AUTOMATIC1111 WebUI** ([github.com/AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)) — Klasik sekmeli arayüz. Hızlı denemeler ve zengin uzantı ekosistemi için hâlâ en yaygın başlangıç noktalarından.

Basit seçim kılavuzu: **eğitim** için kohya_ss, **kod/pipeline** için diffusers, **üretim iş akışı** için ComfyUI, **klasik deneme** için A1111.

## Örnek model aileleri (2026 itibarıyla)

| Aile | Öne çıkan sürümler | Kısa not |
|---|---|---|
| Stable Diffusion | SD 1.5, SDXL, SD3 | 2026'da hâlâ en yaygın ekosistem; SD 1.5 en hafif ve en çok LoRA birikimi olan model, SDXL 1024 çözünürlükte standart kabul ediliyor. |
| Flux | Black Forest Labs | 2026 itibarıyla en popüler açık görsel model ailelerinden biri; kalite yüksek, donanım ihtiyacı da yüksek. |

## Bu rehberin LLM tarafıyla ilişkisi

:::tip[LLM biliyorsanız buradaki mantık tanıdık gelecek]
Aynı boru hattı: **veri → eğitim → değerlendirme**. Aynı kavramlar: taban modelin dondurulup küçük bir katmanın eğitilmesi ([LLM'de LoRA/QLoRA](/llm/lora-qlora/), görselde LoRA). Sadece malzemeler farklı.
:::

| | LLM | Görsel difüzyon |
|---|---|---|
| Eğitim verisi | Metin (talimat + yanıt) | Görsel + açıklama (caption) |
| Taban model ne öğrenir? | Sıradaki tokenı tahmin etmeyi | Görüntüdeki gürültüyü tahmin etmeyi |
| Küçük uyarlama yöntemi | LoRA / QLoRA ([detay](/llm/lora-qlora/)) | LoRA |
| Değerlendirme | Kayıp (loss), benchmarklar, gözle sohbet | Örnek görsel üretimi, gözle inceleme |

Sıfırdan eğitim tarafında da benzerlik var: LLM'de [ön eğitim](/llm/pretraining/) neyse, görselde de büyük veriyle difüzyon ön eğitimi odur; küçük uyarlamalar onun üzerine yapılır.

## Sırada ne var?

Artık elinizde gerekli zihinsel model var: gürültüyü sökmesini öğrenmiş bir ağ, metin kodlayıcı eşliğinde adım adım görseli inşa ediyor. Pratikte en çok kullanacağınız yol ise belli: küçük bir veri setiyle LoRA eğitmek.

Devam: [Adım Adım: Kendi Görsel LoRA'nı Eğit](/gorsel/lora-egitimi/)
