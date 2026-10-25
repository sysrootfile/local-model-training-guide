---
title: "Bulut Seçenekleri: Kendi GPU'n Yoksa"
description: Google Colab, Kaggle, RunPod ve Vast.ai'de GPU kiralamanın maliyetlerini karşılaştırın; ücretsiz başlangıç reçetesi, adım adım RunPod rehberi ve maliyet örnekleri.
dogrulama: 2026-10-15
---

İyi bir ekran kartıyla model eğitmek pahalı bir başlangıçtır; bulut ise kapıyı saatlik ücrete açar. Bu sayfa, paranızı en verimli kullanmanız için platformları karşılaştırır; ücretsiz başlama reçetesi ve adım adım kiralama rehberi verir.

:::caution
Aşağıdaki fiyatlar **2026 itibarıyla** yaklaşık değerlerdir ve platformlar fiyatlarını sık değiştirir. Kiralama yapmadan önce platformun kendi fiyat sayfasındaki güncel değeri kontrol edin.
:::

## Satın Almak mı, Kiralamak mı?

Basit matematik:

- RTX 5090'ın resmî liste fiyatı (MSRP) **$1.999**; ancak 2026 itibarıyla gerçek perakende fiyatı MSRP'nin çok üzerinde seyrediyor — ABD'de **~$2.500-5.000** bandı raporlanıyor. RTX 4090 ise üretimden kalkmış durumda; ikinci elde fiyatlar bölgeye ve stoğa göre değişir. Kart ve çevre birimleriyle toplam bütçe **kabaca $2.500 ve üzeri** (ülke, vergi ve diğer bileşenlere göre artar).
- Bulutta aynı sınıf kart (4090) saatlik **~$0.3-0.5**; bir alt sınıf 3090 daha ucuz. Yani satın alma bütçesi, bulutta **kabaca 5.000-8.000 saat**lik 4090 kullanımına denk gelir; 3090 gibi daha ucuz kartlarla bu süre daha da uzar.
- Günde 1 saat eğitim yapsanız bu on yıllara yayılan bir süre eder; üstüne elektrik ve donanımın eskimesi eklenir.

Sonuç: düzensiz veya öğrenme amaçlı kullanımda bulut açık ara akıllıdır. Haftada onlarca saat, yıllarca eğitim yapacaksanız satın almak anlam kazanır. Hangi iş için hangi kartın yettiğini görmek için: [VRAM Hesabı](/donanim/vram-hesabi/).

## Platform Karşılaştırması

| Platform | Ücretsiz katman | Tipik GPU | Yaklaşık fiyat (2026) | Kime uygun |
| --- | --- | --- | --- | --- |
| **Google Colab** | Var: T4 (limitli; limitler garantili değil, notebook ömrü ~12 saat üst sınır) | T4; üst GPU'lar Pro ile | Ücretsiz; Pro ~$10/ay; Pro+ ~$50/ay | İlk denemeler, öğrenme |
| **Kaggle** | Var: haftada ~30 saat (yoğunluğa göre bazen daha fazla) | T4 x2 / P100 | Ücretsiz | Sıfır bütçe, notebook alışkanlığı |
| **RunPod** | Yok | RTX 4090, A100, H100, H200 | 4090 ~$0.34/sa'dan; H100 ~$2.9-4/sa; H200 ~$4-5.5/sa | Planlı, ciddi eğitimler |
| **Vast.ai** | Yok | Topluluk GPU'ları (3090 / 4090 / A100...) | 4090 ~$0.35-0.6/sa (medyan ~$0.5); kesintili ilanlar daha ucuz | Fiyat avı, tecrübeli kullanıcı |
| **Lambda Labs** | Yok | A100, H100, H200, B200 | H100 ~$3.3-4.3/sa; A100 ~$2/sa; egress ücreti yok; güncel listeyi kontrol edin | Uzun süreli, kurumsal işler |
| **Modal** | Starter planında $30/ay ücretsiz kredi | Serverless: T4'ten B200'e | Kullanım başına, saniye hassasiyetinde (H100 ~$4/sa) | Kod odaklı, kısa ve seyrek işler |
| **Hugging Face Jobs / Spaces** | Spaces'te ücretsiz CPU katmanı | T4, L4, L40S, A100, H200 | T4 ~$0.4/sa; L4 ~$0.8/sa; A100 ~$2.5/sa; H200 ~$5/sa (dakika başı) | HF ekosisteminde yaşayanlar |

Colab tarafında 2026'nın önemli değişikliği: Eylül 2026'dan itibaren Colab ayrıcalıkları Google AI planlarına entegre edildi; mevcut Pro/Pro+ abonelikleri geçerliliğini koruyor. Bölgenizdeki güncel paketler için Colab'ın abonelik sayfasını kontrol edin.

:::note
Piyasa geneli için referans: H100 sınıfı kartlar **yaklaşık $2-4/sa** (klasik hiperscaler bulutlarda $6+), H200 sınıfı **yaklaşık $4-5.5/sa** bandında kiralanır. Ucuz ve pahalı uç arasındaki fark çoğu zaman barındırıcının güvenilirliğidir.
:::

Hızlı seçim rehberi:

- **Bütçem sıfır, öğreniyorum** → Kaggle (haftalık ~30 saat) ve Colab (T4).
- **İlk ciddi eğitimimi yapacağım** → RunPod'da kiralık 4090 (kurulumu basit, hızlı başlar).
- **En düşük saatlik fiyatı arıyorum, tecrübeliyim** → Vast.ai (ama barındırıcı seçimine dikkat).
- **Günler sürecek, kesintisiz bir eğitim planlıyorum** → Secure Cloud veya Lambda gibi kurumsal seçenekler.

## Görünmeyen Maliyetler: Bütçe Disiplini

Bulut faturalarının kötü sürprizleri hep aynı yerlerden gelir:

- **Açık unutulan pod'lar:** En pahalı sunucu, kapatmayı unuttuğunuz sunucudur. Her oturum sonunda "Pods" listesini kontrol edin.
- **Stop ≠ kapatma:** Durdurulan pod'da GPU ücreti durur ama kalıcı volume ücreti ödenmeye devam eder. RunPod'da konteyner diski durdurulunca ücretsizleşir; ağ volume'ü ise pod kapalıyken de faturalanır (1 TB altında $0.07/GB/ay, 2026 itibarıyla). Örnek: durdurulmuş pod'da unutulan 100 GB'lık volume ayda **~$7** eder; üç ay gözetimsiz kalırsa **~$21** birikir — bu, ~$0.35/sa'lik bir 4090'da kabaca 60 saatlik GPU süresine denk düşer.
- **Disk ve volume ekstraları:** Saatlik fiyat yalnızca GPU içindir. RunPod'da konteyner diski çalışırken $0.10/GB/ay'dır (pod durdurulunca konteyner diski ücretlenmez), ağ volume'ü 1 TB altında $0.07/GB/ay'dır (2026 itibarıyla); Vast.ai'de depolama barındırıcıya göre değişir ve instance durdurulsa da ödenmeye devam eder. Güncel oranları platformun sayfasından kontrol edin.
- **Yanlış kart seçimi:** 4B QLoRA için H100 kiralamak, Ferrari ile markete gitmektir. Önce [VRAM Hesabı](/donanim/vram-hesabi/) ile ihtiyacı netleştirin.

## Ücretsiz Başlangıç Reçetesi: Kaggle

1. kaggle.com'da hesap açın (Google veya e-posta ile).
2. **Create → New Notebook** ile bir notebook başlatın.
3. Sağ panelde **Settings → Accelerator** bölümünden GPU'yu seçin: **T4 x2 veya P100**. Haftalık kotanız yaklaşık 30 saattir (yoğunluğa göre bazen biraz daha fazla); dolduysa gelecek haftayı beklersiniz.
4. İlk hücrede kütüphaneleri kurun:

```python title="Kaggle hücresi"
!pip install -q transformers datasets peft trl bitsandbytes
```

5. Küçük bir modelle QLoRA deneyin: [LoRA ve QLoRA](/llm/lora-qlora/) ve [Adım Adım Eğitim](/llm/adim-adim-egitim/).
6. Çıktıyı kaydedin: model dosyalarını `/kaggle/working` altına yazın ve **Save Version** ile kalıcılaştırın; büyük modellerde [Hugging Face'e yükleyin](/kullanim/huggingface-paylasim/).

:::caution
**Colab notu:** Ücretsiz katmanda oturum, uzun eğitimlerde veya boşta kalınca kopar ve makinedeki her şey silinir. Çözüm: Google Drive'ı bağlayıp kontrol noktalarını (checkpoint) oraya kaydetmek:

```python title="Colab — Drive bağlama"
from google.colab import drive
drive.mount("/content/drive")
```

Trainer'da `save_steps` ayarını küçük tutun (ör. her 200 adımda kayıt) ki kopmada en fazla birkaç dakikalık iş kaybetsiniz.
:::

## RunPod: Adım Adım

1. **Hesap:** runpod.io'da hesap açın, e-postayı doğrulayın.
2. **Bakiye:** Billing bölümünden kartınızla bakiye yükleyin. Harcama limiti/uyarısı kurmak, unutulan bir pod'un faturayı uçurmasını engeller.
3. **GPU seçimi:** Pods → Deploy ile GPU seçin. "Community Cloud" daha ucuz, "Secure Cloud" daha güvenilir ve pahalıdır. Tek RTX 4090, çoğu QLoRA işi için fazlasıyla yeter.
4. **Şablon:** "PyTorch" imajını seçin — CUDA ve PyTorch kurulu gelir, sıfırdan ortam kurmakla uğraşmazsınız.
5. **Disk:** Konteyner diski (ör. 30-50 GB) model indirme ve veri için yeter; veriniz kalıcı olsun istiyorsanız volume ekleyin.
6. **Bağlantı:** Pod açılınca **Connect → JupyterLab** (veya SSH) ile içeri girin.
7. **Veri:** En pratik yol, veriyi Hugging Face'te (gerekirse gizli bir depoda) tutup pod içinden `hf download kullanici/veri-setim` komutuyla çekmektir. Küçük dosyalar için Jupyter'e sürükle-bırak da çalışır.
8. **Uzun işler için SSH + tmux:** SSH ile bağlanacaksanız eğitimi `tmux` veya `screen` içinde başlatın; terminal veya tarayıcı kapansa da eğitim sürer.
9. **Kapatma:** İş bitince pod'u **Terminate** edin. Unutulan pod, bulut faturalarının en klasik katilidir.

:::danger
RunPod'da **Stop**, GPU ücretini durdurur ama disk ücreti işlemeye devam eder; **Terminate** her şeyi siler (volume hariç). Kalıcı veriyi volume'da tutuyorsanız (volume ayrıca fiyatlandırılır) pod'u gönül rahatlığıyla terminate edebilirsiniz. Her iş sonrası "Pods" listesini kontrol etmeyi alışkanlık yapın.
:::

### Veri Yükleme Seçenekleri

Pod'a veri götürmenin üç yaygın yolu var; dosya büyüklüğüne göre seçin:

- **Hugging Face Hub'dan çekme (önerilen):** Veriyi bir HF deposunda (gerekirse gizli depoda) tutup pod içinden indirin. `hf_transfer` paketi indirmeyi paralelleştirerek büyük depolarda ciddi hız kazandırır:

```bash title="HF hızlı indirme (pod içi)"
pip install -q hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1
hf download kullanici/veri-setim --repo-type dataset --local-dir /workspace/veri
```

- **Sürükle-bırak:** Birkaç yüz MB'a kadar dosyalar için JupyterLab arayüzü yeterlidir; ama tarayıcı bağlantısı koparsa yükleme yarıda kalır.
- **rclone / S3:** Büyük arşivleri kendi object storage'ınızdan çekmek için rclone kullanın. Egress'e dikkat: AWS S3 gibi klasik bulutlarda çıkış trafiği ayrıca ücretlendirilir; Lambda gibi bazı GPU bulutları egress ücreti almaz, Vast.ai ise bant genişliğini GB başına faturalar. Yönü veri olan trafiğin kimin bütçesinden ödendiğini kiralama öncesi kontrol edin.

## Vast.ai Notu

Vast.ai bir **açık artırma (auction)** pazarıdır: bireysel barındırıcılar boştaki GPU'larını fiyat vererek kiralar. Bu yüzden piyasadaki en ucuz 4090'lar genelde burada bulunur: on-demand ilanlar 2026 itibarıyla ~$0.35-0.6/sa bandında, kesintiye uğrayan (interruptible) ilanlar ise daha aşağıda fiyatlanır. Güncel canlı listeyi kontrol edin.

- **Kimin için:** Maliyet hassasiyeti yüksek, deney niteliğinde ve kontrol noktalı (kesintiye dayanıklı) işler için uygundur. Kısa süreli testlerde en ekonomik seçeneklerden biridir.
- **Güvenilir sunucu seçimi:** Yıldız puanı yüksek, **reliability (güvenilirlik) skoru %95+** ve "verified" etiketli makineleri seçin; aşırı ucuz ilanlarda donanım/VRAM tutarsızlığı olabilir — ilk iş olarak `nvidia-smi` ile kartı doğrulayın.
- **Kesinti riski:** Barındırıcı makineyi kapatabilir; uzun eğitimlerde düzenli kontrol noktası almadan Vast.ai kullanmayın.
- **Ne zaman tercih edilir:** Birkaç saatlik denemeler, fiyat karşılaştırmalı benchmark'lar ve "acaba 48 GB VRAM nasıl bir şey?" gibi alıştırma işleri için birebir.

## Spot ve Kesintiye Uğrayan Instance'lar

Hem RunPod hem Vast.ai, on-demand fiyatın belirgin altında "her an geri alınabilir" kapasite satar; ama mantıkları farklıdır:

- **RunPod spot:** On-demand fiyatın genelde **~%50 civarına** düşer; karşılığında kapasite geri istendiğinde pod **uyarı yapılmadan** durdurulabilir. Kısa denemeler ve checkpoint disiplinine alışmış kullanıcılar için uygundur.
- **Vast.ai interruptible (açık artırma):** Saatlik teklifi (bid) siz belirlersiniz; anlık fiyat teklifinizin üzerine çıkarsa instance durdurulur (dosyalar diskte kalır, depolama ücreti sürer). "On-demand" ilanlar ise teklif yarışından muaf, ama daha pahalıdır.

İki modelde de kural aynıdır: **kesinti bir istisna değil, tasarımın parçasıdır.** Yukarıdaki "Uzun Eğitimler İçin Püf Noktaları" bölümündeki checkpoint disiplini burada zorunluluk kazanır: `save_steps`'i küçültün, kayıtları kalıcı volume'a yazın ve eğitim kodunuzun son kontrol noktasından devam edebildiğini kısa bir denemeyle doğrulayın.

:::caution
Spot/interruptible indirimleri cazip görünse de, uzun ve kesintisiz bir eğitimi checkpoint'siz şekilde spot'ta başlatmak, kesinti anında tüm ilerlemeyi kaybettirebilir. Kritik işlerde on-demand / Secure Cloud seçeneği hâlâ en güvenli yoludur.
:::

## Uzun Eğitimler İçin Püf Noktaları

- **Eğitimi her zaman bir yönetici altında çalıştırın:** SSH'de `tmux`, Jupyter'de "Run All" yerine bir `nohup`/log dosyası; bağlantı kopsa da iş devam etsin.
- **Kontrol noktası (checkpoint) aralığını küçültün:** Bulutta kesinti sürprizdir; `save_steps` küçük olsun ve kayıtları volume'a yazın.
- **Veriyi tekrar tekrar yüklemeyin:** Veriyi volume'da tutun; her oturumda HF'ten indirmek hem zaman hem trafik israfıdır.
- **Gece eğitimi bütçesi:** 8 saatlik bir eğitim, $0.34/sa'lık 4090'da kabaca **$2.7** eder. Uyumadan önce `nvidia-smi` ile işin gerçekten ilerlediğini doğrulayın.
- **Logları kaydedin:** Terminalde akan çıktı kaybolur; `> egitim.log 2>&1` tarzı yönlendirme ya da aracın kendi log dosyasını kullanın.
- **Tek pod'da tek eğitim:** Aynı GPU'da ikinci bir iş başlatmak VRAM'i ikiye böler; OOM alırsanız işleri sıraya alın.

## Ne Zaman Ücretliye Geçmeli?

- **Haftalık ücretsiz kota yetmiyorsa:** Kaggle'da 30 saat/tam hafta dolduysa ve denemeler erteleniyorsa.
- **16 GB üstü VRAM gerekiyorsa:** Ücretsiz katmanların T4'leri 16 GB'dır; 8B LoRA veya 14B+ QLoRA istiyorsanız ücretli GPU şart.
- **Kesintisizlik kritikse:** Colab/Kaggle oturumları koparda iş kaybediyorsanız, saatlik kiralama kendini hemen amorti eder.
- **Hiperparametre taraması yapıyorsanız:** Aynı gün 5-6 varyant denemek, ücretsiz katmanlarda haftalara yayılır; ücretli bir gün çoğu zaman daha ucuzdur.

## Kaggle mı, Colab mı?

İkisi de ücretsizdir ama karakterleri farklı:

- **Kaggle:** Haftalık ~30 saat sabit kota, kalıcı notebook'lar, çıktı sürümleme. Hesap açılışında telefon doğrulaması istenebilir. Öngörülebilirliği yüksektir. İnce ayrıntı: Colab Pro/Pro+ aboneliğiniz varsa Kaggle, hesapları bağlamanız hâlinde haftada sırasıyla +15/+30 ek GPU saati tanır.
- **Colab:** Sıfır kurulumla anında başlar; ancak oturumlar kopabilir ve ücretsiz GPU erişimi yoğun saatlerde kısıtlanabilir. Ücretsiz katmanda tek notebook ömrü en fazla ~12 saattir ve limitler garanti edilmez. GitHub entegrasyonu pratiktir.

Pratik plan: ilk denemeler Colab'da, düzenli ve kotası belli çalışmalar Kaggle'da, ciddi işler RunPod/Vast.ai'de.

## Maliyet Örnekleri

:::tip
Kaba hesap (RTX 4090 kiralama ~$0.3-0.4/sa varsayımıyla; süreler verinize ve ayarlarınıza göre değişir):

- **4B model, 5.000 örnek QLoRA:** ~1-2 saat → **yaklaşık $0.5-1**
- **8B model, 10-20 bin örnek QLoRA:** ~2-4 saat → **yaklaşık $1-2**
- **14B model, 20 bin örnek QLoRA:** ~4-8 saat → **yaklaşık $2-5**
- **Ücretsiz katman denemesi (Kaggle/Colab): 4B'ye kadar QLoRA → $0** (kota ve oturum sınırları dahilinde)

Model indirme ve ortam kurulumu bu sürelere dahildir. Önemli olan şu: kendi kartınızın yetmediği bir işi birkaç dolar karşılığında bitirebilirsiniz. Daha büyük modeller (32B+) ve uzun dizilerde süreler birkaç katına çıkar; ihtiyacı önce kağıt üzerinde netleştirin: [VRAM Hesabı](/donanim/vram-hesabi/).
:::

## Veri Gizliliği

:::caution
Hassas veriyle (kişisel bilgiler, müşteri kayıtları, sağlık/finans verisi) bulut GPU kullanırken veri makinenizden çıkar ve barındırıcının diskinden geçer; topluluk platformlarında barındırıcının container dosya sistemine erişebilme ihtimali vardır. Yapılması gerekenler: veriyi anonimleştirin, mümkünse yerel donanımı tercih edin, KVKK (Kişisel Verilerin Korunması Kanunu) kapsamındaki verilerde hukuki danışmanlık alın ve yurt dışına aktarım kurallarını değerlendirin. Sağlık ve finans gibi alanlarda bulutta eğitim, çoğu senaryoda uygun değildir.

Anahtar ve token hijyeni için küçük ama etkili alışkanlıklar:

- **Token'ı hücreye yazmayın:** HF token'ını pod'u açarken şablonun ortam değişkeni bölümüne koyun veya kabukta `export HF_TOKEN=...` ile tanımlayın; kodun içine sabitlenmiş anahtar hata loglarına ve kaydedilen notebook'lara sızar.
- **Paylaşılan platformlarda ekstra dikkat:** Kaggle ve Colab notebook'ları kolayca paylaşılabilir; gizli değerleri platformun kendi secret özelliğiyle verin, düz hücreyle asla.
- **İş bitince token'ı iptal edin:** HF ayarlarındaki (Settings → Access Tokens) token'ı işiniz kapanınca iptal edin; bir token'ın ömrü pod'un ömründen uzun olmasın.
- **Kalıntı bırakmayın:** Hassas veri kopyaladıysanız iş sonunda kalıcı volume'daki kopyayı da silin; pod'u terminate etmek konteyneri temizler ama volume ayrıca yaşamaya devam eder.
:::

## Kaynaklar ve İleri Okuma

- [RunPod Dokümantasyonu](https://docs.runpod.io/) — pod'lar, spot instance'lar ve disk/volume fiyatlandırmasının resmî referansı.
- [RunPod Fiyat Sayfası](https://www.runpod.io/pricing) — saniye başı on-demand ve spot GPU fiyatlarının güncel listesi.
- [Vast.ai Dokümantasyonu](https://docs.vast.ai/) — açık artırma/interruptible mantığı, depolama ve bant genişliği ücretleri.
- [Colab SSS](https://research.google.com/colaboratory/faq.html) — ücretsiz katman limitlerinin "garanti edilmediği, dalgalanabildiği" resmî açıklaması.
- [Kaggle: Verimli GPU Kullanımı](https://www.kaggle.com/docs/efficient-gpu-usage) — haftalık GPU kotası ve oturum kuralları.
- [Google Blog: Colab artık Google AI planlarının parçası](https://developers.googleblog.com/colab-is-now-part-of-your-google-ai-plan/) — Eylül 2026 entegrasyon duyurusu.
- [Modal Fiyatlandırma](https://modal.com/pricing) — saniye başı GPU fiyatları ve Starter planının aylık ücretsiz kredisi.
- [Hugging Face Jobs Fiyatlandırması](https://huggingface.co/docs/hub/jobs-pricing) — Jobs donanım seçenekleri ve dakika başına fiyat tablosu.
- [Lambda Fiyatlandırma](https://lambda.ai/pricing) — on-demand H100/H200/B200 fiyatları ve egress politikası.

## Sırada Ne Var?

- Kendi makinenizde kurulum: [Yerel Kurulum (Windows)](/donanim/yerel-kurulum/)
- Eğitimi besleyecek veri: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/)
- İlk eğitiminizi uçtan uca yapın: [Adım Adım Eğitim](/llm/adim-adim-egitim/)
