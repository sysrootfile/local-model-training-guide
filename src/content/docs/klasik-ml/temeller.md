---
title: "Klasik Makine Öğrenmesi: Temeller"
description: Denetimli ve denetimsiz öğrenme, eğitim-test ayrımı, temel metrikler ve model ailelerini tek sayfada toplayan klasik makine öğrenmesi girişi.
dogrulama: 2026-10-15
---

Bu rehberin büyük bölümü LLM'ler ve görsel modellerle ilgili; ama makine öğrenmesinin tamamı bunlardan ibaret değil. Elinizde bir tablo verisi (Excel'e benzeyen satır-sütun verisi) ve bir tahmin hedefi varsa — müşteri gidecek mi, fiyat ne olur, bu ürün arızalı mı — **klasik makine öğrenmesi** çoğu zaman daha hızlı eğitir, daha az donanım ister, daha kolay açıklanır ve sık sık daha doğru sonuç verir.

Bir de pedagojik nedeni var: eğitim, test, aşırı öğrenme (overfitting), metrikler… Tüm bu kavramlar en net burada öğrenilir. İris gibi küçük bir veri setinde model saniyeler içinde eğitilir; yani "kavramı öğrenmek için günlerce GPU beklemek" gerekmez. Burada öğrendiğiniz her şey LLM eğitiminde birebir karşınıza çıkacak.

## Öğrenme türleri

| Tür | Ne yapar? | Günlük hayattan örnek | Tipik algoritmalar |
|---|---|---|---|
| **Denetimli — sınıflandırma** (supervised, classification) | Etiketli veriden kategori tahmin etmeyi öğrenir | E-postanın spam olup olmadığı | Lojistik regresyon, Rastgele orman (Random Forest), XGBoost |
| **Denetimli — regresyon** (regression) | Etiketli veriden sayı tahmin etmeyi öğrenir | Ev fiyatı, sıcaklık, satış adedi | Doğrusal regresyon, gradyan artırma (gradient boosting) |
| **Denetimsiz** (unsupervised) | Etiketsiz veride gizli yapı/kümeler bulur | Müşterileri benzer davranış gruplarına ayırmak | K-means (k-ortalamalar), hiyerarşik kümeleme |
| **Pekiştirmeli** (reinforcement) | Ödül sinyaliyle deneme-yanılma yoluyla strateji öğrenir | Oyun oynayan bot, robot yürüyüşü | Q-öğrenme, politika gradyanları |

Bu sayfada ağırlıklı olarak **denetimli öğrenmeyle** ilgileneceğiz; çünkü iş dünyasındaki tablo verisi problemlerinin çoğu oraya düşer. LLM İnce ayarı da aslında denetimli öğrenmedir: girdi metni, etiket ise beklenen yanıttır.

## Temel iş akışı

Her klasik ML projesi — kimisi bazı adımları atlar ama — şu hattı izler:

```text
veri toplama → temizleme → özellik mühendisliği → eğitim/test ayrımı
       → model seçimi → eğitim → değerlendirme → yeni veriyle tahmin
```

İki noktayı baştan kabul edin:

1. **İşin büyük kısmı veride geçer.** Gerçek projelerde zamanın %70-80'i veri toplama, temizleme ve özellik hazırlamaya gider. Model satırı nispeten kısadır. Bu rehberdeki [Veri Türleri](/veri/veri-turleri/) ve [Veri Temizleme](/veri/veri-temizleme/) sayfaları bu yüzden model sayfalarından bağımsız okunmalı.
2. **Değerlendirme, eğitimden önce planlanır.** "Başarıyı neye göre ölçeceğim?" sorusu en başta netleşmeli. Yoksa sonuç elinize geçtiğinde metrikler üzerine tartışmaya başlarsınız.

:::tip[Veri ararken]
Klasik ML'de veri çoğu zaman zaten elinizdedir: kurum içi tablolar, Excel dosyaları, açık veri portalları. Nelerin mümkün olduğunu görmek için [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/); hazırladığınız tabloyu hangi biçimde saklayacağınız için [Veri Formatları](/veri/veri-formatlari/) sayfalarına bakabilirsiniz.
:::

### Özellik mühendisliği: veriden bilgi üretmek

Model, ham sütunları değil sizin sunduğunuz temsilleri öğrenir. Özellik mühendisliği (feature engineering), ham veriden modelin işine yarayacak yeni sütunlar üretmektir:

- Tarih sütunundan "haftanın günü", "ay", "tatil mi?" sütunları çıkarmak.
- Serbest metin adres sütunundan "şehir" ve "posta kodu" ayırmak.
- Toplam fiyattan birim fiyat, gelirden borç/gelir oranı gibi türetilmiş değerler hesaplamak.
- Kategorik sütunları (renk: kırmızı/mavi/yeşil) modele sayı olarak tanıtmak; en yaygını her kategori için 0/1 sütunu üreten "one-hot kodlama"dır.

Aynı sütuna uygulanan farklı bir mühendislik, aynı modelden çok farklı sonuç almanızı sağlayabilir. Klasik ML'de "modeli değiştirmeden önce özellikleri iyileştir" neredeyse her zaman kazandırır. LLM tarafında bunun karşılığı veri kalitesi ve etiketlemedir: aynı mantık, farklı malzeme.

### Çapraz doğrulama ve referans model (baseline)

Tek bir eğitim/test bölmesi şansa açıktır: bölme değişince skor zıplayabilir. **Çapraz doğrulama (cross-validation)**, veriyi k parçaya bölüp sırayla her parçayı doğrulama olarak kullanır ve k skorun ortalamasını raporlar (k=5 tipiktir). Hem ölçüm daha güvenilir olur hem de her örnek birden fazla kez "sınavda" görülür. scikit-learn'de tek satır: `cross_val_score(model, X, y, cv=5)`.

Ayrıca her projede basit bir **referans model (baseline)** kurun: "herkese en yaygın sınıfı söyle" diyen sahte bir model bile karşılaştırma tabanı sağlar. Örneğin müşterilerin %60'ı gidiyorsa, "herkes gider" diyen modelin doğruluğu %60'tır; gerçek modeliniz bunu anlamlı biçimde geçemiyorsa mimariyi büyütmeden önce veriye ve özelliklere dönmek gerekir.

## Eğitim/test ayrımı neden kutsal?

Modelin eğitildiği veride iyi olması bir şey kanıtlamaz: sınav sorularını önceden gören öğrencinin o sorulardan yüksek alması gibi. Asıl sınav, **hiç görülmemiş veridir**. Bu yüzden veri daha eğitim başlamadan ikiye (hatta üçe) ayrılır:

| Küme | Ne işe yarar? | Tipik oran |
|---|---|---|
| Eğitim (train) | Model buradan öğrenir | %70-80 |
| Doğrulama (validation) | Ayar denemeleri, model seçimi | %10-15 |
| Test | Dokunulmaz; son karne burada ölçülür | %10-20 |

**Aşırı öğrenme (overfitting)**, modelin veriyi "genellemek" yerine "ezberlemesidir": Eğitim verisinde hatasız, yeni veride kötü. Belirtileri: eğitim skoru mükemmele yakınken test skoru belirgin düşük; eğitim verisindeki gürültüye bile uyum sağlanmış. Çözüm yolları: daha fazla veri, daha basit model, düzenlileştirme (regularization) ve erken durdurma (early stopping, doğrulama skoru artmayı bırakınca eğitimi kesmek).

LLM tarafında bu kavramların kayıp (loss) eğrileriyle aynısını göreceksiniz: eğitim kaybı düşerken doğrulama kaybı artmaya başladıysa overfit başlamıştır. Detaylar: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/) ve [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).

## Temel metrikler (ve tuzakları)

| Metrik | Ne ölçer? | Nerede kritiktir? | Tuzağı |
|---|---|---|---|
| **Doğruluk** (accuracy) | Doğru tahminlerin oranı | Sınıflar dengeliyse | **Dengesiz veride yanıltır:** verinin %95'i "negatif" ise, hep "negatif" diyen bir model %95 doğruluk alır — ama hiçbir işe yaramaz. |
| **Kesinlik** (precision) | "Pozitif" dediklerinin kaçı gerçekten pozitif? | Yanlış alarmın pahalı olduğu yerler (spam filtresi: meşru e-postayı spam saymak ağır bedeldir) | Çekingen model kesinliği şişirir ama pozitiflerin çoğunu kaçırır; tek başına okumayın. |
| **Duyarlılık** (recall) | Gerçek pozitiflerin kaçı yakalandı? | Kaçırmanın pahalı olduğu yerler (hastalık taraması: hastayı "sağlıklı" demek kabul edilemez) | Her şeye "pozitif" diyen model duyarlılığı %100 yapar; kesinlikle birlikte değerlendirin. |
| **F1** | Kesinlik ve duyarlılığın harmonik ortalaması | İki hatanın da önemli olduğu durumlar | Hangi bileşenin düşürdüğünü göstermez; iki metriği ayrı da izleyin. |
| **MSE / MAE** | Regresyonda tahmin hatasının büyüklüğü | Fiyat, süre, sıcaklık gibi sayı tahminleri | MSE aykırı değerlere (outlier) aşırı duyarlıdır; MAE daha dayanıklı ama türevlenemez olduğundan optimizasyonda tercih edilmez. |

Kesinlik ve duyarlılığın formülleri, karışıklık matrisi (confusion matrix) tanımından gelir — modelin neyi neyle karıştırdığını gösteren 2x2 tablo:

| | Tahmin: pozitif | Tahmin: negatif |
|---|---|---|
| **Gerçek: pozitif** | Doğru pozitif (TP) | Yanlış negatif (FN) |
| **Gerçek: negatif** | Yanlış pozitif (FP) | Doğru negatif (TN) |

Buradan: `kesinlik = TP / (TP + FP)`, `duyarlılık = TP / (TP + FN)`. Yani kesinlik "pozitif dediklerim ne kadar sağlam", duyarlılık "pozitiflerin ne kadarını buldum" sorusudur. İkisini de asla tek başına okumayın; hangisinin kritik olduğu **uygulamaya** bağlıdır: spam filtresinde kesinlik, hastalık taramasında duyarlılık öne çıkar.

## Model aileleri: hızlı tur

- **Doğrusal modeller** (linear/lojistik regresyon): Girdi özelliklerinin ağırlıklı toplamıyla tahmin yapar. Hızlı, az veriyle çalışır ve katsayıları sayesinde yorumlanabilir; "hangi özellik ne kadar etkiliyor?" sorusunun en net cevabı buradadır. İlişki doğrusala yakınsa şaşırtıcı derecede iyi bir ilk modeldir.
- **Karar ağaçları ve rastgele orman (Random Forest):** Karar ağacı, "eğer yaş > 30 ve gelir < X ise…" gibi if-else zinciridir; tek başına ezberlemeye (overfit) meyillidir. Rastgele orman, yüzlerce farklı ağacı eğitip çoğunluk oyuyla karar verir — bu "kalabalık bilgeliği" ezberi ciddi şekilde dengeler. Az ayar gerektirmesiyle tablo verisinin güvenilir işçisidir.
- **Gradyan artırma (XGBoost / LightGBM):** Ağaçları sırayla eğitir; her yeni ağaç, öncekilerin hatalarını düzeltmeye odaklanır. Tablo verisi yarışmalarında yıllardır en sık kazanan ailedir; ince ayar gerektirir ama tavan başarısı yüksektir. Sayısal tablo veriniz varsa mutlaka deneyin.
- **KNN (k-en yakın komşu):** Tahmin için en benzer k örneğe bakar ve çoğunluğa uyar. Kavramsal olarak en sezgisel yöntemdir; ölçekleme zorunludur ve büyük veride tahmin yavaşlar. Küçük veri setlerinde iyi bir referanstır.
- **SVM (destek vektör makineleri):** Sınıfları ayıran en geniş "marjı" bulur; orta boy, yüksek boyutlu veride klasik bir araçtır. Çekirdek hileleri (kernel) güçlüdür ama büyük veride eğitimi ağırlaşır.
- **K-means (k-ortalamalar):** Etiketsiz veriyi k kümeye ayırır. Müşteri segmentasyonu gibi "keşfetme" problemlerinin standart aracıdır; kaç küme olduğunu (k) siz söylersiniz, bu da hem güç hem zahmet demektir.

Hızla karar vermek için:

| Durum | İlk denenecek | Sonraki adım |
|---|---|---|
| Küçük veri, hızlı sonuç isteniyor | Lojistik regresyon | Rastgele orman |
| Tablo verisi, en iyi skor hedefi | Rastgele orman | XGBoost / LightGBM |
| Açıklanabilirlik şart ("neden bu karar?") | Lojistik regresyon, karar ağacı | Katsayı ve dallanma analizi |
| Etiketsiz veri, grupları keşfetmek | K-means | Hiyerarşik kümeleme |

## İki klasik tuzak: ölçekleme ve sızıntı

- **Ölçekleme (scaling):** Yaş (0-100) ile gelir (0-1.000.000) aynı tablodaysa, mesafe ve iç çarpım tabanlı modeller (KNN, SVM, doğrusal modeller) ikinci sütuna gereğinden fazla ağırlık verir. Çözümü `StandardScaler` gibi araçlarla her sütunu ortalama 0, standart sapma 1 olacak şekilde dönüştürmektir. İnce ayrıntı: ölçekleyici yalnızca **eğitim verisiyle** `fit` edilmeli, test verisine yalnızca `transform` uygulanmalıdır; ağaç tabanlı modeller ise ölçekten genelde etkilenmez.
- **Veri sızıntısı (leakage):** Test kümesinin bilgisi eğitime karışırsa skorlar olduğundan yüksek görünür. En yaygın örneği ölçekleme sızıntısıdır; bir başkası da hedef oluşurken meydana gelen sütunları özellik olarak kullanmaktır (ör. "işten ayrılma tarihi" sütunuyla "ayrıldı mı?" hedefini tahmin etmeye çalışmak). Kural nettir: tahmin anında **elinizde olmayacak** hiçbir bilgi özellik olamaz.

## scikit-learn: standart araç kutusu

Python'da klasik ML denince akla gelen çatı [scikit-learn](https://scikit-learn.org)'dir. Neden standart?

- Aynı API her modelde: eğit, tahmin et, puanla.
- Veri ön işleme, bölme, ölçekleme, metrikler, çapraz doğrulama — hepsi aynı pakette.
- Yüzden fazla algoritma; geçiş yapmak için model adını değiştirmek yeterli.

Tüm kütüphanenin özü şu üç satırdır:

```python title="scikit-learn API deseni"
model.fit(X_train, y_train)        # öğren
tahmin = model.predict(X_test)     # tahmin et
skor = model.score(X_test, y_test) # değerlendir
```

Her sınıflandırma/regresyon modeli bu desene uyar; farkları sadece kurucu parametrelerdir (`RandomForestClassifier(n_estimators=100)` gibi). Bu desen, Hugging Face tarafındaki `trainer.train()` / `model.generate()` akışıyla aynı felsefedir: kütüphane ayrıntıyı gizler, siz akışa odaklanırsınız.

:::tip
Bu deseni ilk kez uygulayacaksanız hazır veriyle uçtan uca bir örneğe geçin: [İlk Modelin: Uçtan Uca scikit-learn Örneği](/klasik-ml/ilk-model/) — 40 satırlık bir betikte tüm iş akışını çalıştıracaksınız.
:::

## Karar: ne zaman klasik ML, ne zaman LLM/derin öğrenme?

| Durum | Doğru araç |
|---|---|
| Tablo/sayısal veride tahmin (fiyat, sınıf, skor) | **Klasik ML** — özellikle XGBoost/rastgele orman |
| Az veri + tablo (yüzlerce satır) | **Klasik ML** — derin öğrenme bu ölçekte ezberler |
| Metin, görsel, ses, sohbet üretimi | **Derin öğrenme / LLM** ([Adım Adım Eğitim](/llm/adim-adim-egitim/)) |
| "Neden bu karar?" açıklaması şart | **Klasik ML** (doğrusal modeller, ağaçlar) |
| Metinden özellik çıkarıp tabloyla birleştirme | **Hibrit:** LLM çıkarır, klasik ML karar verir |

Pratik kural: elinizde sütunlar ve satırlar varsa önce klasik ML deneyin. Metin/görsel işin içindeyse veya üretim (generation) istiyorsanız derin öğrenme tarafına geçin. Çoğu gerçek sistem ikisini karıştırır.

## Sırada ne var?

Artık kavram haritanız hazır: öğrenme türleri, iş akışı, eğitim/test ayrımı, metrikler ve model aileleri. Sırada bunların hepsini gerçek kodla çalıştırmak var.

Devam: [İlk Modelin: Uçtan Uca scikit-learn Örneği](/klasik-ml/ilk-model/)
