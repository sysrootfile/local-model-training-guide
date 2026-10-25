---
title: "Eğitim Nasıl Çalışır? Sezgisel Bir Tur"
description: "Tahmin, kayıp, gradyan ve ağırlık güncellemesi: model eğitiminin beş adımlı döngüsünü, optimizatörü, öğrenme oranı çizelgesini, karışık hassasiyet gibi ölçekleme kolaylıklarını, ezber ile öğrenme arasındaki farkı ve veri kalitesinin neden her şey olduğunu anlatıyoruz."
dogrulama: 2026-10-15
---

"Model eğitmek" kulağa gizemli gelir ama özünde tek bir döngünün milyonlarca kez tekrarıdır: tahmin et, hatayı ölç, hatanın sorumlusunu bul, azıcık düzelt, tekrarla. Bu sayfa, o döngüyü günlük hayattan analojilerle açıyor — ve sonunda göreceksiniz ki aynı döngü, LLM'den görsel üretim modeline, klasik makine öğrenmesine kadar her yerde aynıdır.

## Öğrenmenin Beş Adımlı Döngüsü

Sınavda hata yapıp düzelten bir öğrenci düşünün. Modelin eğitimi tam olarak bu öğrencinin yaptığı şeydir:

### 1. Adım: Tahmin et

Model, bir eğitim örneğini okur ve tahminini üretir. LLM'de bu tahmin "sıradaki token ne olmalı?"dır; klasik ML'de "bu evin fiyatı ne?"dir. Başlangıçta tahminler neredeyse rastgeledir — ağırlıklar rastgele sayılarla başlatılmıştır. **Analoji:** Öğrencinin derse hiç çalışmadan ilk deneme sınavına girmesi.

### 2. Adım: Hatayı ölç

Modelin tahmini ile gerçek cevap karşılaştırılır ve aradaki fark **tek bir sayıya** indirgenir: kayıp (loss). **Analoji:** Öğretmenin sınavı puanlaması. "78 aldın" bilgisi tek başına yeterli değildir ama ilerlemeyi ölçmenin en pratik yoludur.

### 3. Adım: Hatanın sorumlularını bul

Milyarlarca parametreden hangisi bu hataya ne kadar katkıda bulundu? Cevap, matematiğin en zarif araçlarından biriyle bulunur: **geri yayılım (backpropagation)**. Zincir kuralıyla, kayıptaki hatanın her bir ağırlığa düşen "payı" hesaplanır. Her ağırlığa iliştirilen bu paya **gradyan (gradient)** denir. **Analoji:** Öğretmenin yalnızca "yanlış" demekle kalmayıp "bu hatanın üçte biri çarpım tablosundan, kalanı dikkatsizlikten" diye geri bildirim yazması.

Gradyan bir yön ve büyüklüktür: "Bu ağırlığı azıcık **artırırsan** kayıp şu kadar **azalır**" der.

### 4. Adım: Ağırlıkları azıcık düzelt

Model, gradyanların işaret ettiği yönün tersine doğru her ağırlığı küçük bir adımla günceller: **gradyan inişi (gradient descent)**. Adımın büyüklüğünü **öğrenme oranı (learning rate)** belirler:

- Çok büyükse: model savrulur, kayıp düşmek yerine zıplar. **Analoji:** Hatasını görüp ders çalışma yöntemini her gün kökten değiştiren öğrenci.
- Çok küçükse: ilerleme kaplumbağa hızında olur, eğitim saatler sürer.
- LoRA ince ayarında tipik değerler 1e-4 – 2e-4 arasıdır; ayrıntılı ayar rehberi: [Hiperparametreler](/llm/hiperparametreler/).

### 5. Adım: Tekrarla

Bu döngü tek bir örnek için değil, milyonlarca örnek için tekrarlanır. İlk turda kayıp dik düşer, sonra azalarak iner. Eğitim, milyonlarca "azıcık düzeltme"nin toplamıdır.

```text title="Eğitim döngüsü — sözde kod"
for her batch (örnek grubu) in eğitim_verisi:
    tahmin = model(batch)              # 1. Tahmin et
    kayip  = hata_olc(tahmin, gercek)  # 2. Hatayı ölç
    gradyanlar = geri_yayilim(kayip)   # 3. Sorumluları bul
    agirliklar -= ogrenme_orani * gradyanlar  # 4. Azıcık düzelt
# 5. Tüm veri bitene kadar tekrarla
```

## Optimizatör: "Azıcık Düzelt"i Kim Daha İyi Yapar?

Yukarıdaki sözde kodun dördüncü satırı, en yalın hâliyle **gradyan inişini** gösterir: her ağırlık, öğrenme oranı kadar aynı ölçüde güncellenir. Gerçek eğitimde bu güncellemeyi daha akıllıca yapan bir kilit personel vardır: **optimizatör**.

Bugün LLM eğitiminde fiilî standart **Adam**'ın rafine hâli **AdamW**'dir. Adam (Kingma ve Ba, 2014) her parametre için gradyanların iki "akan ortalamasını" (running average) tutar: son gradyanların ortalaması (**momentum** — "hangi yönde ilerliyoruz?") ve karelerinin ortalaması (**ikinci moment** — "bu ağırlığın gradyanları genelde ne kadar büyük?"). Bu iki istatistiği birleştirip her parametre için **kendine özgü** bir adım boyu hesaplar. **Analoji:** Her ders için ayrı not tutan koç — matematik hataları hep büyük geliyorsa o dersteki adımları kendi içinde küçültür, tarih hataları küçükse cesurca büyütür. Düz gradyan inişi ise her dersi aynı cetvelle ölçer.

AdamW'nin (Loshchilov ve Hutter, 2017) katkısı **weight decay**'in düzeltilmesidir. Klasik yöntem (L2 cezası), küçülme istekini gradyan bildiriminin içine karıştırır; Adam'ın adaptif ölçeklemesi bu karışımı bozar ve ceza, gradyanları büyük olan ağırlıklarda etkisini yitirir. AdamW ikisini ayırır: gradyan bildirimi olduğu gibi işler; ağırlıklar her adımda buna ek olarak, optimize ediciden bağımsız biçimde hafifçe küçültülür. **Analoji:** Öğrencinin cevaplarına "keşke daha kısa olsaydı" notu iliştirmek yerine, her cevabı kendi başına düzenli kısaltmak — geri bildirim kanalı ile disiplin kanalı ayrıdır. Bu ayırmanın genelleme kalitesini iyileştirdiğini makale çeşitli görevlerde göstermiştir; PyTorch, sınıfı doğrudan `torch.optim.AdamW` olarak sunar. Kod örneğine gerek yok: Trainer ve TRL gibi araçların çoğu bunu sizin adınıza kurar; ismini bir gün log çıktısında görürseniz şaşırmayın.

Aşağıda, "Öğrenme Oranı Sabit Değildir" bölümünde göreceğiniz **warmup**'ın bir sebebi de buradadır: momentum ve ikinci moment istatistikleri ilk adımlarda henüz "ısınmamıştır"; bu dönemde hesaplanan adımlar aşırı büyük oynayabilir.

## Kayıp (Loss): Hatanın Tek Sayıyla İfadesi

Dil modellerinde standart kayıp ölçüsü **çapraz entropi (cross-entropy)**'dir. Sezgi şöyle: model, doğru token'a yüksek olasılık verdiyse kayıp düşük; düşük olasılık verdiyse kayıp yüksektir. Sayısal örnek:

- Doğru token'a 0,9 olasılık veren modelin kaybı: −log(0,9) ≈ **0,11** → mükemmele yakın.
- Doğru token'a 0,1 olasılık veren modelin kaybı: −log(0,1) ≈ **2,3** → kötü.

Eğitim boyunca kayıp eğrisini izlersiniz. Tipik bir LoRA eğitiminde 3,2'den başlayıp 1,4 civarına inmek "iyi gidiyor" işaretidir; kayıp düşmeyi bıraktıysa öğrenilecek şey kalmamış ya da bir şey ters gitmiştir. Kayıp ve metriklerin ayrıntılı okunması — perplexity dahil — [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfasında.

:::note[Kayıp eğrisini tek başına okumak yanıltır]
Kayıp düşüyor diye her şey yolunda demek değildir; model ezberliyor olabilir. Bunu anlamak için yanında **doğrulama kaybını** da izlemek gerekir — birazdan.
:::

## Batch, Step ve Epoch: Veri Üzerinden Geçiş

Üç terim birbirine karışır; bir kez netleştirelim:

- **Batch (yığın):** Aynı anda işlenen örnek grubu. Neden hepsi birden değil? Çünkü tüm veri seti aynı anda GPU belleğine sığmaz.
- **Step (adım):** Bir batch'lik veriyle yapılan **bir** ağırlık güncellemesi.
- **Epoch (tur):** Eğitim setinin **tamamı** üzerinden bir geçiş.

Basit hesap: 10.000 örneklik veri, batch boyutu 8 olsun.

```text title="Step ve epoch hesabı"
10.000 örnek ÷ 8 örnek/batch = 1.250 step/epoch
3 epoch  →  3 × 1.250 = 3.750 toplam step
```

:::tip[4 GB VRAM hilesi: gradyan birikimi]
Kartınız batch 2'den fazlasını kaldırmıyorsa **gradyan birikimi (gradient accumulation)** kullanın: 8 küçük batch'in gradyanını biriktirip tek güncelleme yapın. Sonuç, etkin batch 16 gibi davranır — bellekten feragat etmeden kararlılık kazanırsınız. Ayarı: [Hiperparametreler](/llm/hiperparametreler/).
:::

LLM ince ayarında epoch sayısı genelde 1-3'tür; klasik ML'de yüzlerce tura kadar çıkabilir. Verinin her epoch'ta karıştırılması (shuffle) ezberlemeyi zorlaştırır.

## Ezber mi Öğrenme mi? Overfitting ve Underfitting

Modelin amacı, eğitim verisini **ezberlemek** değil, oradaki örüntüyü **genellemek**tir. İki uç hata vardır:

- **Aşırı öğrenme (overfitting):** Model, eğitim örneklerini cevaplarıyla birlikte ezberler. Eğitim kaybı muhteşem görünür ama yeni veride çöker. **Analoji:** Sınavın aynısını ezberleyen, benzer soruda sınıfta kalan öğrenci. LLM ince ayarında tipik belirtisi: model kendi eğitim örneklerinizi birebir tekrarlar, sorulara küçük varyasyonlarda sapıtır.
- **Yetersiz öğrenme (underfitting):** Model hiçbir şey öğrenememiştir; eğitim kaybı bile yüksek kalır. Genellikle yetersiz veri, fazla düşük öğrenme oranı veya çok az epoch'un işaretidir.

Nasıl yakalarız? Veriyi ikiye ayırırız: **eğitim seti** ve **doğrulama seti** (tipik olarak %5-10). Model doğrulama setini hiç görmez; yalnızca "sınav" için saklanır. Sağlıklı bir eğitimde iki kayıp da düşer. Eğitim kaybı düşerken **doğrulama kaybı düşmeyi bırakıp yükselmeye başladıysa** ezber başlamıştır — erken durdurma (early stopping) devreye girer: o noktadaki checkpoint en iyisidir.

:::caution[LLM'de doğrulama kaybı gürültülüdür]
1.000 örneklik bir LoRA eğitiminde doğrulama seti 30-50 örnektir; eğri zikzaklı olur, tek bir yükselmeye bakıp paniklemeyin. En iyi checkpoint'i seçmek için eğilime bakın ve çıktı kalitesini elle test edin: [Değerlendirme](/degerlendirme/loss-ve-metrikler/).
:::

## Kayıp Eğrisi Şekilleri: Hızlı Teşhis Tablosu

Eğitim kayıplarını izlerken en sık karşılaşacağınız manzaralar ve anlamları:

| Eğri görünümü | Muhtemel durum | Ne yapmalı? |
| --- | --- | --- |
| Eğitim ve doğrulama kaybı birlikte düşüyor | Sağlıklı eğitim | Devam edin |
| Eğitim düşüyor, doğrulama yükseliyor | Aşırı öğrenme (overfitting) | Erken durdurun; veri çoğaltın; LoRA rütbesini (rank) veya epoch'u azaltın |
| Doğrulama kaybı zikzak çiziyor ama eğilimi aşağı doğru | Öğrenme oranı biraz yüksek ya da doğrulama seti çok küçük | Paniklemeyin, eğilime bakın; oranı bir kademe düşürmeyi deneyin |
| İkisi de yüksek ve neredeyse düz | Yetersiz öğrenme | Öğrenme oranını artırın, epoch ekleyin, veriyi ve etiketleri kontrol edin |
| Kayıp zıplıyor veya NaN oluyor | Öğrenme oranı çok yüksek | Oranı 5-10 kat düşürün; gradyan kırpma (gradient clipping) kullanın |
| Kayıp iyi ama çıktılar bozuk | Veri formatı / sohbet şablonu uyumsuzluğu | Şablonu ve veri formatını kontrol edin: [Tokenizasyon](/temeller/tokenizasyon/), [SFT](/llm/sft/) |

## Öğrenme Oranı Sabit Değildir: Isınma ve Azaltma

Modern eğitimde öğrenme oranı genellikle sabit tutulmaz; bir **çizelge (schedule)** izler. En yaygın iki desen:

- **Isınma + doğrusal azalma (warmup + linear decay):** Eğitimin ilk kısmında oran sıfırdan tepe değere düz bir çizgiyle çıkar, sonra adım adım sıfıra iner.
- **Isınma + kosinüs azalması (warmup + cosine decay):** Isınmadan sonra oran bir yarım kosinüs eğrisi boyunca önce hızlı, sonda yumuşakça düşer. Bu desen SGDR makalesinden (Loshchilov ve Hutter) gelir ve LLM dünyasında en sevilen çizelgedir.

Peki ısınma neden gerekiyor? İki sebep var:

1. Başta ağırlıklar rastgeledir; ilk gradyanlar hem gürültülü hem büyüktür. Büyük adımlar, öğrenmeye daha yeni başlamış modeli baştan savurabilir — transformers dokümanı warmup'ı "eğitimin ilk evresini dengede tutmak" için önerir.
2. Bir önceki bölümdeki optimizatör istatistikleri (momentum ve ikinci moment) ilk adımlarda henüz ısınmamıştır; bu dönemde hesaplanan adım boyları sorunlu ölçüde oynayabilir. RAdam makalesi bunu ölçmüş ve warmup'ı bir "varyans azaltma tekniği" saymıştır.

**Analoji:** Deneme sınavı sonuçları daha gelmemiş bir öğrenciye ilk hafta "yöntemini kökten değiştir" demeyin; küçük denemelerle başlatın, gidiyatı görünce adımları büyütün — sınav (eğitimin sonu) yaklaştıkça da değişiklikleri küçültüp oturtun. Azaltmanın sebebi de sondadır: kayıp minimumun çevresinde dolaşırken büyük adımlar "zıplamaya" devam eder; oran düştükçe model minimuma yumuşakça oturur.

:::caution[transformers v5'te `warmup_ratio` yok]
v5'te `warmup_ratio` parametresi kaldırıldı; TrainingArguments artık `warmup_steps` alanına ondalık oran da kabul ediyor — 0 ile 1 arası bir float, toplam adımın oranı olarak yorumlanır. Eski örneklerdeki `warmup_ratio=0.03` bugün şöyle yazılır:

```python title="Öğrenme oranı çizelgesi (transformers v5)"
args = TrainingArguments(
    learning_rate=2e-4,          # çizelgeyle kullanılınca "tepe" (peak) değerdir
    lr_scheduler_type="cosine",  # ısınmadan sonra kosinüsle azalt
    warmup_steps=0.03,           # toplam adımın %3'ü kadar ısınma
)
```
:::

PyTorch düzeyinde aynı çizelgeler `torch.optim.lr_scheduler` modülünde yaşar (`LambdaLR`, `OneCycleLR` gibi); Trainer kullanıyorsanız bunları elle kurmanız gerekmez. Küçük LoRA işlerinde çoğu araç varsayılan olarak kosinüs çizelgesi ve kısa bir ısınma uygular; sabit oran da sık kullanılır. Tüm çizelge seçenekleri: [Hiperparametreler](/llm/hiperparametreler/).

## Ölçek Büyüdükçe Devreye Giren Üç Kolaylık

Şimdiye kadar anlattığımız döngü tek bir ağırlık güncellemesiydi. Gerçek eğitimde bu döngüyü sınırlı VRAM'de binlerce kez döndürmeniz gerekir; üç standart kolaylık tam bu noktada işinizi kolaylaştırır — her biri farklı bir kaynakta tasarruf ettirir: hesap hassasiyeti, bellek ve adım büyüklüğü.

### Karışık hassasiyet (mixed precision)

Ağırlıklar ve hesaplar varsayılan olarak 32 bit kayan nokta sayılarla (fp32) yürür. Karışık hassasiyet, hesabın çoğunu 16 bite indirir: hız ve bellek kazanırsınız, sonuç büyük ölçüde aynı kalır. İki 16 bit biçim vardır ve aralarındaki fark önemlidir:

- **fp16:** üs aralığı dardır; geri yayılımdaki küçük gradyanlar bu aralığın altına düşüp yok olabilir. Çözüm **kayıp ölçekleme (loss scaling)**: kayıp büyük bir katsayıyla çarpılır, gradyanlar böylece ölçülebilir aralıkta kalır; işlem bitince ölçek geri alınır. fp16'da bu ölçekleme şarttır — PyTorch'un `GradScaler`'ı tam bu işi yapar.
- **bf16:** fp32'nin üs aralığını korur; küçük gradyanlar kaybolmaz ve ölçekleme gerekmez. transformers dokümanı bf16'yı "daha iyi numerik stabilite ve ölçekleme gerektirmemesi" nedeniyle fp16'ya tercih ettiğini açıkça yazar. Bedeli: kartınızın bu formatı donanımsal desteklemesi gerekir — NVIDIA tarafında Ampere kuşağı ve sonrası (RTX 30 serisi ve üstü).

**Analoji:** Hesap makinenizin hane sayısını 32'den 16'ya indirmek: sıradan çarpımlar için fark etmez ama çok küçük sayılar ekranda sıfır görünür. fp16'da bu yüzden yanınızda bir "büyüteç" (ölçekleme) taşımak zorundasınız; bf16'nın alt aralığı geniş olduğu için büyütece gerek kalmaz.

Trainer karşılığı tek alandır: `bf16=True`.

### Gradyan birikimi (gradient accumulation)

Yukarıdaki "4 GB VRAM hilesi" kutusunun resmî karşılığı. Fikir: mikro batch'leri arka arkaya işleyin, gradyanları bellekte biriktirin ve ancak belirli sayıda örnekten sonra ağırlıkları güncelleyin. Formül:

```text title="Etkin batch"
etkin batch = mikro batch × birikim adımı   (çok GPU'da: × GPU sayısı)
```

Örneğin 4 mikro batch × 8 birikim adımı = etkin batch 32; ama GPU belleğinde 4'lük mikro batch'ten fazlası tutulmaz. Beş adımlı döngüde hiçbir şey değişmez; yalnızca 4. adım (güncelleme) daha seyrek gelir ve biriken gradyanların ortalamasıyla yapılır. Trainer karşılığı: `gradient_accumulation_steps`.

### Gradyan checkpointing (gradient checkpointing)

Geri yayılım, ileri geçişteki ara sonuçlara (aktivasyonlara) ihtiyaç duyar ve tüm katmanların aktivasyonlarını saklamak VRAM'in baş tüketicilerinden biridir. Checkpointing fikri: hepsini saklamak yerine yalnızca birkaç kontrol noktası saklayın, geri geçişte aradakileri yeniden hesaplayın. Bellekten feragat edip hesaptan ödersiniz: transformers dokümanı bunu "~%20'ye varan yavaşlama" notuyla belgeler. **Analoji:** Ders notlarının tamamını çantada taşımak yerine yalnızca bölüm başlıklarını taşımak; geri geçişte bölümü baştan okuyup notları yeniden yazarsınız — çanta hafifler, süre uzar. Trainer karşılığı: `gradient_checkpointing=True`.

Üç kolaylığın TrainingArguments'taki karşılıkları tek bakışta:

```python title="Üç kolaylık, üç alan"
args = TrainingArguments(
    bf16=True,                      # karışık hassasiyet (bf16 donanımı desteklemeli)
    gradient_accumulation_steps=8,  # 8 mikro batch'te bir güncelle
    gradient_checkpointing=True,    # aktivasyonları at, geri geçişte yeniden hesapla
)
```

Bu üç kolaylık, model tarafındaki nicemleme ile (QLoRA) birlikte çalışır: [LoRA ve QLoRA](/llm/lora-qlora/).

## Eğitim Süresini Ne Belirler?

Süre, üç büyüklüğün çarpımıyla orantılıdır: **işlenen toplam token sayısı × model boyutu × donanım hızı**. Pratik çıkarımlar:

- 2.000 örnek × ortalama 500 token = yaklaşık 1 milyon token işlenir; batch 8 ile ~250 step/epoch.
- Aynı veriyle 4B model, 8B modelden belirgin hızlıdır; LoRA, tüm parametreleri eğitmekten kat kat hızlıdır çünkü gradyanlar yalnızca küçük adaptör için hesaplanır.
- Genel beklenti: 1.000-5.000 örnekle tipik bir QLoRA eğitimi, donanıma göre **30 dakika ile 6 saat** arası sürer (yerel 6-12 GB kartlarda üst uç, kiralık 4090 sınıfı bir kartta alt uç).

Süreyi eliyle çevirdiğiniz vidalar — batch boyutu, birikim adımı, epoch, çizelge — doğrudan adım sayısını değiştirir; bu vidaların tam listesi ve önerilen değerler: [Hiperparametreler](/llm/hiperparametreler/).

:::tip[Hızlı deneme döngüsü kurun]
İlk turda verinin küçük bir dilimini (ör. %10) ve 1 epoch kullanın; her şeyin çalıştığını görün. Ayar değişikliklerini böyle hızlı test edin, tam eğitimi en sona saklayın.
:::

## Neden Veri Kalitesi Her Şeydir?

Klasik deyişle "çöp girer, çöp çıkar": eğitim verisi tutarsız etiketler, yazım hataları veya kopya örneklerle doluysa model bu tutarsızlığı öğrenir. 2023'te Meta'nın yayımladığı **LIMA** çalışması bunun kanıtıdır: araştırmacılar yalnızca **1.000 özenle seçilmiş** talimat-cevap örneğiyle yapılan ince ayarın, çok daha büyük ama gürültülü veri setleriyle yapılan eğitimlerle yarışabildiğini gösterdi. Yorum şu: bilginin çoğu zaten ön eğitimde vardır; ince ayarın işi **davranış ve format** öğretmektir, bu da örnek kalitesiyle olur.

Pratikte bu ne demek?

- 1.000 temiz, tutarlı örnek; 100.000 gürültülü örnekten iyi olabilir.
- Aynı sorunun çelişkili cevapları, modelin kafasını karıştırır. Her şeyden önce **tutarlılık**.
- Kopya örnekler ezber riskini şişirir; tekrarları temizleyin.
- Cevaplar, istediğiniz üslup ve uzunlukta olmalı — model gördüğünü taklit eder.

Veri hazırlama süreçleri: [Veri Temizleme](/veri/veri-temizleme/) ve [Kendi Verini Oluştur](/veri/kendi-verini-olustur/).

:::tip[Küçük başla, sonra ölçekle]
İlk eğitiminizi 30-50 örnekle yapıp boru hattının baştan sona çalıştığından emin olun; sonra 1.000-5.000 örneğe çıkın. Doğrudan 50.000 örnekle başlamak, hatayı saatler sonra fark etmenin en garantili yoludur.
:::

## Aynı Döngü Her Yerde

Bu sayfada anlatılan beş adımlı döngü, evrenseldir:

- **LLM ince ayarında:** Her batch'te sıradaki token tahmin edilir, çapraz entropi kaybı hesaplanır; LoRA'da yalnızca küçük adaptör matrisleri güncellenir: [SFT](/llm/sft/), [LoRA ve QLoRA](/llm/lora-qlora/).
- **Görsel modellerde:** Difüzyon (diffusion) modelleri, görüntüye eklenen gürültüyü tahmin etmeyi öğrenir — yine tahmin, hata, düzelt. Gizli kalan kavramlar: [Difüzyon Temelleri](/gorsel/diffusion-temelleri/).
- **Klasik makine öğrenmesinde:** `model.fit(X, y)` tek satırdır ama altında aynı gradyan inişi çalışır; kayıp eğrileri burada da aynı hikâyeyi anlatır: [Klasik ML Temelleri](/klasik-ml/temeller/), [İlk Model](/klasik-ml/ilk-model/).
- **Preferans eğitiminde:** DPO ve RLHF de aynı döngünün türevidir — modelin iki cevaptan hangisini tercih ettiği bir kayba çevrilir ve yine tahmin, hata, düzelt ile işlenir: [DPO ve RLHF](/llm/dpo-rlhf/).
- **Sıfırdan ön eğitimde:** Aynı döngü, bu kez milyarlarca token'la: [Ön Eğitim](/llm/pretraining/).

:::tip[Sıradaki adım]
Kayıp eğrilerini profesyonelce okumayı öğrenmek için [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfasına, eğitim ayarlarının (öğrenme oranı, batch, LoRA rütbesi) detayına inmek için [Hiperparametreler](/llm/hiperparametreler/) sayfasına geçin. Artık teori yeter; ilk gerçek eğitim için [Adım Adım Eğitim](/llm/adim-adim-egitim/) sizi bekliyor.
:::

## Kaynaklar ve İleri Okuma

Bu sayfayı yazarken yararlandığımız birincil kaynaklar:

- [Adam: A Method for Stochastic Optimization (arXiv:1412.6980)](https://arxiv.org/abs/1412.6980) — Kingma ve Ba'nın 2014 makalesi; parametre başına uyarlanabilir adım fikrinin kaynağı.
- [Decoupled Weight Decay Regularization (arXiv:1711.05101)](https://arxiv.org/abs/1711.05101) — AdamW makalesi; weight decay'in gradyandan ayrılmasının genellemeyi iyileştirdiğini gösterir.
- [SGDR: Stochastic Gradient Descent with Warm Restarts (arXiv:1608.03983)](https://arxiv.org/abs/1608.03983) — Kosinüs çizelgesi ve ısınmış yeniden başlatmaların önerildiği makale.
- [On the Variance of the Adaptive Learning Rate and Beyond (arXiv:1908.03265)](https://arxiv.org/abs/1908.03265) — RAdam makalesi; adaptif optimizatörlerde başlangıç varyansı ve warmup'ın neden işe yaradığı.
- [Transformers Trainer ve TrainingArguments dokümanı](https://huggingface.co/docs/transformers/main_classes/trainer) — Bu sayfadaki tüm alanların (`warmup_steps`, `bf16`, `gradient_accumulation_steps`, `gradient_checkpointing`) resmî referansı.
- [PyTorch torch.optim.AdamW dokümanı](https://docs.pytorch.org/docs/stable/generated/torch.optim.AdamW.html) — AdamW'nin "ayrık weight decay" uygulamasının kendisi.
- [PyTorch OneCycleLR dokümanı](https://docs.pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.OneCycleLR.html) — Çizelgelerin PyTorch düzeyindeki karşılığına bir örnek.
