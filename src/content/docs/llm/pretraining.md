---
title: "Sıfırdan Ön Eğitim (Pretraining): Gerçekler ve Alternatifler"
description: "Sıfırdan ön eğitimin gerçek maliyeti, Chinchilla ölçekleme bulgusu ve çoğu proje için doğru yol olan devam ön eğitimi yaklaşımı."
dogrulama: 2026-10-15
---

Bir dil modelinin sohbet edebilmesinden, soruları yanıtlayabilmesinden önce **dilin kendisini** öğrenmesi gerekir. Bu aşamaya **ön eğitim (pretraining)** denir: modele milyonlarca sayfalık ham metin (web sayfaları, kitaplar, kod, makaleler) verilir ve tek bir görev öğretilir — "bir sonraki jetonu (token) tahmin et."

Bunu şöyle düşünün: Bir öğrenciye milyonlarca kitap okutuyorsunuz ama hiç soru sormuyorsunuz. Sadece her cümlenin ortasında durup "sıradaki kelime ne olur?" diye soruyorsunuz. Öğrenci zamanla dil bilgisini, kelime dağarcığını, üslup çeşitliliğini ve dünya hakkında genel bilgileri kendiliğinden öğrenir. Ama henüz "soru sorulduğunda nasıl cevap verilir" kısmını bilmez — o kısım [talimat ayarı (SFT)](/llm/sft/) aşamasının işidir.

:::note
Kısa cevap: Bu sayfa "kendi temel modelimi sıfırdan eğitir miyim?" sorusunu gerçekçi rakamlarla yanıtlamak için var. Çoğu proje için cevap **hayır**; ama küçük ölçekte deney yapmak çok öğreticidir ve gerçekten mümkündür.
:::

## Ön Eğitim Neden Bu Kadar Pahalı?

Ön eğitim, makine öğrenmesindeki en pahalı iştir. Üç şey aynı anda devasa boyuta ulaşır:

1. **Veri:** "Sonraki jetonu tahmin et" görevi çok fazla metin ister. Ciddi modeller trilyonlarca jetonluk metinle eğitilir — bu tek başına yüzlerce GB ile TB arası ham metin demektir.
2. **Hesaplama:** Her örnek, modeldeki her parametre için ayrı bir gradyan hesabı üretir. Hesaplama ihtiyacı hem veri miktarıyla hem model boyutuyla birlikte büyür.
3. **Mühendislik:** Binlerce GPU'yu haftalarca hatasız çalıştırmak (donanım arızaları, veri besleme boru hatları, dağıtık eğitim) başlı başına bir uzmanlık alanıdır.

### Rakamlarla Gerçekler

Aşağıdaki tablo büyüklük mertebelerini göstermek içindir; değerler kesin değil, "yaklaşık" okunmalıdır.

| Ölçek | Veri | Donanım | Süre / Maliyet (yaklaşık) |
| --- | --- | --- | --- |
| Minik deney (TinyStories tarzı) | Birkaç yüz MB hikâye metni | Tek tüketici GPU (ör. RTX 4090) | Birkaç saat ile 1 gün arası |
| ~1B parametre, "ciddi" ön eğitim | Milyarlarca jeton | On binlerce GPU-saati | Ciddi bir bütçe gerektirir |
| 8B+ parametre (Llama sınıfı) | Trilyonlarca jeton | Binlerce GPU × haftalar | Milyonlarca dolar mertebesi |

:::caution
"Hafta sonu kendi GPT'mi eğiteceğim" deneyi ile "Llama seviyesinde bir model üreteceğim" hedefi arasında kabaca on binlerce katlık bir maliyet farkı vardır. İkisi de ön eğitimdir; ama biri öğrenme deneyi, diğeri kurumsal bir projedir.
:::

## Chinchilla: Parametre / Jeton Dengesi

2022'de DeepMind'ın **Chinchilla** çalışması önemli bir bulgu paylaştı: Aynı hesaplama bütçesiyle daha iyi sonuç almak için **model boyutu ile eğitim verisi birlikte** büyütülmelidir. O döneme kadar modeller görece "büyük model, az veri" ile eğitilirdi; Chinchilla ekibi daha küçük ama daha çok veri gören modellerin aynı bütçeyle daha iyi olduğunu gösterdi.

Pratikte sık kullanılan kabaca kural şudur:

> "Düzgün" bir ön eğitim için her **parametre başına yaklaşık 20 jeton** eğitim verisi hedefleyin.

Örnek: 1 milyar parametreli bir model için kabaca **20 milyar jeton** metin gerekir. Bir jetona ortalama ~4 karakter dersek, bu onlarca GB'lık ham metne denk gelir.

Hesaplamayı büyüklük mertebesi olarak şöyle ifade edebiliriz:

```text title="Chinchilla hesabı — büyüklük mertebesi"
Gerekli veri      = parametre_sayısı × 20            (jeton cinsinden)
1B model için     = 1.000.000.000 × 20 = 20 milyar jeton
Eğitim hesaplaması ≈ 6 × parametre_sayısı × jeton    (FLOP; kabaca mertebe tahmini)
1B × 20 milyar    ≈ 1,2 × 10^20 FLOP
```

Bu ikinci satır, "eğitim ne kadar hesaplama ister?" sorusunun standart mertebe tahminidir; GPU-saati planı yaparken kabaca kullanılır. Kesin değerler mimariye ve donanıma göre değişir.

:::note[GPU-saati mertebesi: 1B × 20B örneği]
Aynı hesapla somut bir tahmin: 1B parametreli modeli 20 milyar jetonla eğitmek ≈ **1,2 × 10^20 FLOP** demektir. Tek bir RTX 4090'ın bf16 yoğun (dense, FP32 birikimli) tensor gücü NVIDIA kaynaklı karşılaştırma tablolarında ve GPU veri tabanlarında **165,2 TFLOPS** olarak geçer (2026 itibarıyla). Yalnızca bu tepe değere bölerseniz teorik alt sınır ≈ **200 saat** çıkar. Gerçekte bu hızın tamamı kullanılamaz: yayımlanmış büyük ölçekli eğitimlerde tipik verim (MFU) %30-50 bandındadır; %30-50 verim varsayımıyla **400-700 saat** mertebesi elde edilir. Bu bir **mertebe tahminidir; kesin değildir** — mimari, parti boyutu ve yazılım yığını sonucu birkaç kat değiştirebilir.
:::

:::tip
Chinchilla kuralı ön eğitim içindir. Sonraki aşamalarda ([SFT](/llm/sft/), [DPO](/llm/dpo-rlhf/)) çok daha az veriyle çalışırsınız. Asıl veri ihtiyacı ön eğitimde ortaya çıkar; bu yüzden "kaç örnek yeter?" sorusunun cevabı aşamaya göre tamamen değişir.
:::

## Chinchilla ve Sonrası: Neden Güncel Modeller "Aşırı" Eğitiliyor?

Chinchilla sonucu **hesap-optimal** (compute-optimal) dengeyi tanımlar: elinizde sabit bir hesaplama bütçesi varsa, bu bütçeyi model boyutu ile eğitim verisi arasında belirli bir oranda paylaştığınızda kayıp en düşük olur — kabaca **parametre başına ~20 jeton** (arXiv:2203.15556). Ama bu bir "gereklilik" değil, bir **verimlilik** ölçütüdür.

2026 itibarıyla güncel modellere bakınca ilk bakışta tuhaf görünen bir tablo çıkar: Küçük modeller kasıtlı olarak Chinchilla'nın işaret ettiğinden çok daha uzun eğitilir. Örnek: Llama 3 makalesi (arXiv:2407.21783), 8B parametreli modelini **15 trilyon jeton**la eğittiklerini belirtir — bu, parametre başına **~1.900 jeton** eder. Chinchilla kuralıyla 8B için kabaca 160 milyar jeton "yeterli" görünürdü; Llama 3 ekibi kuralın ~90 katı fazlasıyla eğitti.

Neden? Çünkü iki maliyetin ömrü farklıdır:

- **Eğitim bir kerelik bir masraftır:** Bir kez ödenir.
- **Çıkarım (inference) ömür boyu süren bir masraftır:** Model her sorguda çalıştıkça tekrar tekrar ödenir.

Aynı hedef performansa, daha küçük ama daha uzun eğitilmiş bir modelle ulaşabiliyorsanız üretimde her sorgu daha az parametre işler ve uzun vadeli GPU maliyeti düşer. Llama 3 makalesindeki ifadeyle: küçük modeller hesap-optimalin çok ötesinde eğitildiğinde "aynı çıkarım bütçesinde" hesap-optimal modellerden **daha iyi** performans verir. Yani hesap-optimal olmak, yaşam-döngüsü-optimal olmak demek değildir.

Sizin için pratik anlamı: "20 jeton kuralı"nı bir tavan ya da endüstri standardı gibi okumayın; kendi durumunuzda eğitim bütçeniz ile çıkarım maliyetiniz arasında bir denge kurun.

:::caution[En sık yapılan yanlış okuma]
"20 jeton/parametre" **hesap-optimal bir eğitim bütçesidir**; bir kalite tavanı ya da zorunlu asgari değildir. İki yanlış okuma sık görülür: (1) "20 jetonu geçersem model bozulur" — hayır; veri arttıkça kayıp genellikle düşmeye devam eder, yalnızca *aynı hesaplama bütçesiyle* kıyaslarsanız verimsiz kalırsınız. (2) "Kuralı uyguladım, artık Chinchilla seviyesindeyim" — hayır; kural bir denge tarifidir; veri kalitesini veya eğitim başarısını tek başına garanti etmez.
:::

## Ön Eğitim Ne Zaman Mantıklı? 3 Senaryo

Çoğu kişi için değildir; ama şu üç durumda gerçekten gerekli olabilir.

### 1. Yeni bir dil için temel model

Elinizdeki açık modellerin iyi bilmediği, kaynakları kısıtlı bir dil için temel model eğitmek mantıklı olabilir. Türkçe için örnek: akademik ekipler ve topluluk projeleri, yüzlerce GB'lık Türkçe korpuslarla modeller eğitmiştir; **Turkish Data Depository** (turkish-nlp-suite topluluğunun veri deposu) Türkçe ön eğitim verisi sağlar. Yine de önce mevcut çok dilli bir modelle (ör. Qwen3, Gemma 3) devam ön eğitimi denemek neredeyse her zaman daha ucuzdur.

### 2. Çok özel bir alan için temel model

Bazı alanların verisi doğal dilden tamamen farklıdır: moleküler veri, protein dizileri, genom, zaman serileri, finansal akışlar... Bu alanlarda genel amaçlı dil modellerinin öğrendiği "gramer" işe yaramaz; amaç diline özel bir model sıfırdan eğitilir. Gerçek dünya örneği: Protein dizileri üzerine eğitilen **ESM** serisi modeller, "protein dilini" öğrenmek için milyonlarca amino asit dizisiyle ön eğitilmiştir; bu model daha sonra protein yapısı tahmini gibi görevlerde kullanılmıştır.

### 3. Öğrenme ve araştırma amaçlı küçük ölçek

Bazen amaç üretim modeli değil, **anlamaktır**. Küçük bir veri kümesi ve tek GPU ile birkaç on milyon parametreli minik bir modeli sıfırdan eğitip davranışını izlemek, ön eğitimin nasıl çalıştığını en iyi anlatan yöntemdir. Bunu aşağıda ayrıca ele alıyoruz.

### Türkçe ekosistemden örnekler

- **Turkish Data Depository:** Türkçe ham metin kaynaklarını bir araya getiren topluluk deposu; ön eğitim ve devam ön eğitimi için başlangıç noktası.
- **FineWeb-2 Türkçe:** Hugging Face'in çok dilli web veri kümesinin Türkçe dilim. Web ölçeğinde ham metin arayanlar için uygun.
- **ogulcanaydogan/Turkish-LLM:** Qwen2.5 üzerinde QLoRA ile talimat ayarı yapan açık bir topluluk projesi (173K–242K arası Türkçe örnek). Sıfırdan eğitim yerine "mevcut model + veri" yaklaşımının somut örneği.

## Alternatifler: Çoğu Kişi İçin Doğru Yol

Sıfırdan ön eğitim yerine, mevcut güçlü bir açık modelle başlayıp onu kendi verinizle şekillendirmek neredeyse her zaman daha hızlı ve daha ucuzdur:

```text title="Çoğu proje için önerilen akış"
[Ham verinizi toplayın]  -->  /veri/veri-nereden-bulunur/
        |
        v
[Mevcut açık temel modeli seçin]   (ör. Qwen3-8B, Gemma 3, Llama 3.2)
        |
        v
[Devam ön eğitimi (continued pretraining)]  -- isteğe bağlı, alan/dil bilgisi için
  - Model zaten dili biliyor; siz ona kendi alanınızın metinlerini okutursunuz
  - Full fine-tuning veya LoRA/QLoRA ile yapılabilir
        |
        v
[Talimat ayarı (SFT)]  -->  /llm/sft/
  - "Soruya nasıl cevap verilir" burada öğretilir
        |
        v
[Tercih ayarı (DPO)]  -- isteğe bağlı  -->  /llm/dpo-rlhf/
```

**Devam ön eğitimi** şu demektir: Elinizdeki modelin ağırlıklarıyla başlarsınız, üzerine kendi ham metninizle (ör. şirket dokümanları, hukuk metinleri, forum arşivi) birkaç epoch daha "sonraki jetonu tahmin et" eğitimi yaparsınız. Modelin genel dil yeteneği korunur, üzerine alan bilgisi eklenir. Ardından SFT ile görev davranışını öğretirsiniz.

:::tip
Sıralama önemlidir: **devam ön eğitimi → SFT → (isteğe bağlı) DPO**. Devam ön eğitimi verisi ham metin, SFT verisi ise soru-cevap ikilileridir; iki aşamanın verisini karıştırmayın. SFT verisini devam ön eğitimine karıştırmak modelin davranışını bozabilir.
:::

## Devam Ön Eğitiminin Zorlukları: Unutma ve Replay

Devam ön eğitimi basit görünür — "model zaten dili biliyor, üzerine birkaç doküman okutalım" — ama bilinmesi gereken iki yönü vardır.

**Birincisi, işe yaradığı kanıtlı:** "Don't Stop Pretraining" çalışması, bir modeli hedef alanın ham metniyle ön eğitime devam etmenin (alan uyarlamalı ön eğitim, DAPT) o alandaki görevlerde belirgin kazanç sağladığını göstermiştir (arXiv:2004.10964). Yani yaklaşım sağlamdır; kazanç yalnızca SFT'den değil, ham alan metninden de gelir.

**İkincisi, bedeli olabilir:** Modele kendi alanınızı öğretirken genel yeteneklerini silebilirsiniz. Buna **felaket unutması (catastrophic forgetting)** denir; belirtisi tanıdıktır: alan sorularında iyileşme olurken genel sohbet, akıl yürütme veya diğer dillerde gerileme görülür.

Pratik refleksler:

- **Replay (genel veri karışımı):** Eğitim karışımınıza genel amaçlı ham metinden bir miktar geri koyun. Tipik bir başlangıç, verinin **%5-10**'unu genel metne ayırmaktır; bu bir kanun değil, toplulukta yaygın bir pratiktir. En iyi oranı kendi doğrulama sonuçlarınızla bulun.
- **Küçük öğrenme oranı, az epoch:** Tam ince ayarla (full fine-tuning) devam ön eğitimi yapıyorsanız öğrenme oranını çok küçük tutun — **1e-5 mertebesi** yaygın bir başlangıçtır ve 1-2 epoch genellikle yeterlidir. Yüksek öğrenme oranı ve çok epoch, unutmayı hızlandırır.
- **LoRA/QLoRA daha nazik olabilir:** Tüm ağırlıkları güncellemek yerine [LoRA ve QLoRA](/llm/lora-qlora/) ile yapılan devam ön eğitimi, genel yetenekleri daha iyi koruyabilir; küçük veri setlerinde ilk denenecek yol budur.

:::caution[Ölçmeden devam etmeyin]
Devam ön eğitiminden **önce ve sonra** kısa bir genel yetenek testi koşun (20-50 soru iyi bir başlangıçtır): alan performansındaki artışı, genel puandaki düşüşle birlikte okuyun. Genel puan belirgin düşüyorsa replay oranını artırın, öğrenme oranını düşürün veya epoch sayısını azaltın. Kayıp okuma pratiği için [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfasına, daha kapsamlı karşılaştırma için [Benchmark'lar](/degerlendirme/benchmarklar/) sayfasına bakın.
:::

## Küçük Ölçekte Ön Eğitim Deneyi: 5 Adımda TinyStories

Ön eğitimi gerçekten anlamak istiyorsanız en iyi yol, bir hafta sonunda tek GPU'da minik bir modeli sıfırdan eğitmektir. Bunun için mükemmel bir oyuncak veri kümesi var: **TinyStories**. Araştırmacıların derlediği bu veri kümesi, çok küçük çocuklara uygun basit İngilizce hikâyelerden oluşur. Fikir şudur: Bir çocuk nasıl önce basit hikâyelerle dil öğreniyorsa, küçük bir dil modeli de basit hikâyelerle şaşırtıcı derecede akıcı bir "çocuk hikâyesi dili" öğrenebilir. Birkaç on milyon parametreli bir model, saatler içinde saçma ama gramatik olarak tutarlı hikâyeler üretmeye başlar.

**5 adımlık tarif:**

1. **Kodu alın:** [nanoGPT](https://github.com/karpathy/nanoGPT) (Andrej Karpathy'nin eğitim amaçlı minimal GPT uygulaması) veya TinyStories için topluluk tarafından hazırlanmış eğitim betiklerinden birini kullanın.
2. **Veriyi indirin:** [TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories) veri kümesini Hugging Face'ten indirin; birkaç yüz MB'lık bir alt küme başlangıç için fazlasıyla yeterli.
3. **Modeli küçültün:** Birkaç katmanlı, birkaç milyon parametreli bir GPT tanımlayın. Amaç iyi bir model değil; çalışan bir ön eğitim döngüsü kurmak.
4. **Eğitin ve izleyin:** Eğitim kaybının düştüğünü ve üretilen metnin başta saçmalarken zamanla tutarlı hikâyelere dönüştüğünü izleyin. Bu, tek bir RTX 4090'da birkaç saat sürer.
5. **Parametrelerle oynayın:** Model boyutunu, öğrenme oranını ve veri miktarını değiştirin. Hangi değişikliğin kaybı nasıl etkilediğini görmek, Chinchilla fikrini size "hissettirecektir".

:::note
Küçük ölçekte bile ön eğitim sizi veri temizleme, jetonlaştırma (tokenization), öğrenme oranı planlaması ve kayıp izleme konularıyla yüzleştirir. Bu yüzden çok öğreticidir; bu bilgiler profesyonel işlerinizdeki [SFT](/llm/sft/) ve [LoRA](/llm/lora-qlora/) çalışmalarında da işinize yarar.
:::

## Karar Tablosu

| Durumunuz | Önerilen yaklaşım |
| --- | --- |
| Sohbet botu, görev modeli, üslup/ton değiştirme | Sadece SFT (+ isteğe bağlı DPO). Sıfırdan eğitime hiç girmeyin. |
| Alan jargonu yoğun (hukuk, tıp, kurumsal dokümanlar) ve veriniz var | Mevcut modelle **devam ön eğitimi**, ardından SFT. |
| Çok az kaynaklı bir dilde temel model gerekiyor | Önce çok dilli açık modellerle devam ön eğitimini deneyin; sıfırdan eğitim ancak araştırma ekipleri için gerçekçidir. |
| Amaç öğrenmek / merak | TinyStories veya nanoGPT ile tek GPU'da minik ölçekte sıfırdan eğitim. |
| Büyük bütçe + uzman ekip + yeni bir temel model hedefi | Sıfırdan ön eğitim + devam ön eğitimi + SFT + DPO tam hattı. |

## Mini SSS

**"Kendi tokenizer'ımı eğitmeli miyim?"**
Sıfırdan ön eğitim yapıyorsanız evet — hedef dil ve alan için ayrı bir tokenizer (ör. BPE ile) eğitmek jeton verimliliğini ciddi artırır. Devam ön eğitimi yapıyorsanız mevcut tokenizer'ı **korumak zorundasınız**; değiştirmek, modelin öğrenilmiş ağırlıklarını anlamsızlaştırır.

**"Türkçe ön eğitim verisi yeterli mi?"**
Türkçe, web ölçeğinde İngilizce'nin çok altındadır ama tek başına "az kaynaklı" (low-resource) sayılmaz: FineWeb-2 Türkçe gibi setler ve topluluk depoları makul hacme ulaşmıştır. Buna karşılık 8B+ bir modeli "ciddi" eğitmek için hâlâ ağırlıklı olarak İngilizce veri gerekir; bu yüzden çok dilli modeller pratikte avantajlıdır.

**"Tek bir RTX 4090 ile en fazla ne yapabilirim?"**
Küçük ölçekli bir deney: birkaç yüz MB metinle 10-50 milyon parametreli bir model, birkaç saat ile 1 gün arasında. Bu ölçekte "üretim modeli" çıkmaz; ama tüm hat (veri toplama → tokenizer → eğitim → örnekleme) elinizden geçer ve öğrendikleriniz doğrudan SFT/LoRA işlerinize taşınır.

## Toparlarsak

- Ön eğitim, modele dili öğreten aşamadır; en pahalı aşamadır ve veri/hesaplama/mühendislik açısından ciddi kaynak ister.
- Chinchilla bulgusu akılda tutulmalı: parametre başına yaklaşık 20 jeton dengesi.
- Çoğu proje için doğru sıralama: [verinizi toplayın](/veri/veri-nereden-bulunur/), mevcut bir açık modelle başlayın, gerekirse devam ön eğitimi yapın, sonra [SFT](/llm/sft/) ve isteğe bağlı [DPO](/llm/dpo-rlhf/) uygulayın.
- Öğrenmek istiyorsanız sıfırdan deney yapın — ama küçük ölçekte ve amacı öğrenmek olan bir deney olarak.

Bir sonraki adım: Modelinize görev davranışı kazandırmak için [talimat ayarı (SFT)](/llm/sft/) sayfasına geçin.

## Kaynaklar ve İleri Okuma

- [Chinchilla: Training Compute-Optimal Large Language Models (arXiv:2203.15556)](https://arxiv.org/abs/2203.15556) — Sabit hesaplama bütçesinde model boyutu/veri dengesi ve "~20 jeton/parametre" bulgusunun kaynağı.
- [Llama 3: The Llama 3 Herd of Models (arXiv:2407.21783)](https://arxiv.org/abs/2407.21783) — 8B modelin 15T jetonla "aşırı" eğitimi ve bunun çıkarım bütçesiyle gerekçelendirilmesi.
- [DAPT: Don't Stop Pretraining (arXiv:2004.10964)](https://arxiv.org/abs/2004.10964) — Alan uyarlamalı ön eğitimin (DAPT) faydasını gösteren temel çalışma.
- [nanoGPT (GitHub)](https://github.com/karpathy/nanoGPT) — Sıfırdan, küçük ölçekli ön eğitim denemek için minimal ve okunabilir GPT eğitim kodu.
- [TinyStories (Hugging Face)](https://huggingface.co/datasets/roneneldan/TinyStories) — Minik modellerin basit hikâyelerle şaşırtıcı derecede akıcı bir dil öğrendiğini gösteren veri kümesi.
