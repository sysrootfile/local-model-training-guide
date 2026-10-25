---
title: "Loss ve Metrikler: Eğitim Gerçekten İşe Yaradı mı?"
description: "Kayıp eğrilerini okumak, kayıp ve perplexity tuzakları, görev metrikleri, sınıflandırma ve üretim metriklerinde derinleşme, istatistiksel anlamlılık, LLM-as-judge ve eğitim sırasında izlenmesi gereken dört sayı."
dogrulama: 2026-10-15
---

Eğitim döngüsü bitti, model kaydedildi. Peki gerçekten işe yaradı mı? Bu sayfa, "kayıp düştü" ile "model iyileşti" arasındaki farkı anlamanız için gerekli araçları tanıtır. Kaybın ne olduğunu hatırlamak isterseniz: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/).

## İki Sayı: Eğitim ve Doğrulama Kaybı

Kayıp (loss), modelin tahmini ile doğru cevap arasındaki farkı ölçen sayıdır; eğitim onu küçültmeye çalışır. Ama tek bir kayıp değeri yeterli değildir, çünkü iki farklı kayıp izlenir:

- **Eğitim kaybı (training loss):** Modelin *gördüğü* örneklerdeki hatası. Düşmesi öğrenmenin göstergesidir — ama tek başına yeterli değildir.
- **Doğrulama kaybı (validation loss):** Modelin *hiç görmediği*, baştan ayırdığınız örneklerdeki hatası. Modelin gerçekten genelleyip genellemediğini gösterir.

İkisini birden izlememizin nedeni basit: Eğitim kaybı her zaman düşer — model veriyi ezberlese bile. Doğrulama kaybı ise ezberin başladığı anda yükselmeye başlar ve bize "dur" sinyali verir.

:::tip
Eğitimin başında verinizin %5-10'unu `train_test_split` ile ayırın ve `eval_steps` ile düzenli aralıklarla doğrulama kaybını ölçün. Bu, 5 dakikalık bir alışkanlıktır ve sizi en pahalı hatadan (sessiz ezberden) korur.
:::

## Dört Tipik Eğri ve Anlamları

```text title="(1) SAĞLIKLI — ikisi de düşüyor, sonra düzleşiyor"
 loss
 2.4 |*                              * = eğitim kaybı
 2.0 | **                             o = doğrulama kaybı
 1.6 |   ****
 1.2 |       *****o
 0.8 |            oooo****
 0.5 |                oooooooo******____
     +------------------------------------> adım
 Yorum: Öğrenme gerçek; model genelliyor. Kaybın düzleşmesi normaldir; durabilirsiniz.
```

```text title="(2) EZBER (OVERFITTING) — eğitim iniyor, doğrulama yükseliyor"
 loss
 1.8 |*                          
 1.4 | **o
 1.0 |   ** o                    * = eğitim kaybı (düşmeye devam)
 0.7 |     **  o o                o = doğrulama kaybı (yükseliyor!)
 0.5 |       **    o
 0.4 |         ***    o  o
     +------------------------------------> adım
                         ^---- buradan sonrası zarar: eğitimi burada durdurun
 Yorum: Model veriyi ezberliyor. Çözüm: epoch azalt, veri artır, dropout ekle.
```

```text title="(3) HİÇ ÖĞRENMİYOR — ikisi de neredeyse düz"
 loss
 2.3 |* * * * * * * * * * *  o o o o o o
 2.2 |* o * o * o * o * o * o * * * o o
 2.1 |o o o o o o o o o o  * * o o
     +------------------------------------> adım
 Yorum: Kayıp oynamıyor bile. Şüpheliler: lr çok düşük, veri formatı hatalı,
        etiketler bozuk (tümü maskeli). Bakınız: Sorun Giderme bölüm 3.
```

```text title="(4) ZIPLIYOR (KARARSIZ) — testere dişi desen"
 loss
 3.0 |        o
 2.5 |   *   *   o      o
 2.0 |*   *    *    *  *
 1.5 |  o    o   o  o   *   o
     +------------------------------------> adım
 Yorum: lr çok yüksek veya etkin batch çok küçük. Çözüm: lr'ı düşürün,
        gradient_accumulation_steps ile etkin batch'i büyütün.
```

:::note
Bu çizimler idealleştirilmiştir; gerçek eğriler gürültülüdür. Önemli olan **eğilimdir**: 100 adımlık pencerede doğrulama kaybı üst üste artıyorsa ezber sinyali ciddiye alınmalıdır.
:::

## Kayıp ≠ Kalite: Kayıp Sayısı Yanıltınca

Kayıp, "jeton tahminini öğrenme"nin ölçüsüdür; kalite ise bambaşka bir şeydir. Kayıp sayısının yalan söylediği üç yaygın durum:

1. **Maskeleme hatası (etiketler yanlış işaretlenmiş):** SFT'de kayıp yalnızca cevap jetonlarında hesaplanmalıdır; prompt jetonları `-100` ile maskelenir (kayıp hesabı bu değeri yok sayar). Maskeleme ters yapılırsa kayıp düşer ama model "soru üretmeyi" öğrenir — üretimde saçmalar. Belirti: kayıp düşük ama çıktılar soru cümlesi gibi. Kontrol: bir batch'te etiketlerin kaç tanesinin `-100` olduğunu yazdırın; tümü maskeliyse model hiçbir şey öğrenemez ([Dört Tipik Eğri](#dört-tipik-eğri-ve-anlamları) bölümündeki "hiç öğrenmiyor" eğrisi tam bunun sonucudur).
2. **Format sızıntısı / kalıp ezberi:** Model, cevabın içeriğinden çok şablonunu öğrenir. Kayıp düşer çünkü "Elbette! İşte cevabınız:" gibi kalıp jetonları her örnekte aynıdır ve kolayca tahmin edilir; içerik jetonları ise hâlâ zayıftır. Belirti: tüm cevaplar aynı kalıpla başlar, iç doluluk azdır. Önlem: cevap kalıplarını veride çeşitlendirin ve örnek çıktıları düzenli olarak **gözle** okuyun.
3. **Tercih ayarı (DPO) kaybı farklı ve farklı okunur:** Bu sayfadaki "doğrulama kaybı izle" alışkanlığı SFT içindir; DPO'da kayıp tek başına daha da az şey söyler. Ayrıntı için [DPO ve RLHF](/llm/dpo-rlhf/) sayfasındaki "DPO Sonrası Ne Ölçülür?" bölümüne bakın.

**Kayıp sıçramaları (spike):** Eğri boyunca tek adımlık ani zıplamalar genellikle zararsızdır (aykırı bir batch). Kalıcılaşan örüntüler ise müdahale ister:

| Belirti | Olası neden | Müdahale |
| --- | --- | --- |
| Tek adımda büyük sıçrama, sonra iniş | Aykırı/zor bir batch | Yok sayın; sıklığını not edin |
| Sıçrama sonrası kayıp yeni bir seviyede düzleşti | Ağırlıklar hasar gördü | Öğrenme oranını düşürün; son iyi checkpoint'ten devam edin |
| Sıçramalar tekrarlı ve büyüyor | lr çok yüksek / etkin batch küçük | lr'ı düşürün; `gradient_accumulation_steps` ile etkin batch'i büyütün |
| Doğrulama kaybı da bozuldu | Gerçek hasar | Durdurun, checkpoint geri alın, veriyi gözden geçirin |

Çoğu eğitimci gradyan kırpma (clipping) uygular (`max_grad_norm`, yaygın varsayılan 1.0); bu, vahim sıçramaların çoğunu zaten engeller. Ama sürekli tavan değerinde kırpma görüyorsanız bu, lr'ın hâlâ yüksek olduğunun işaretidir.

## Perplexity (Şaşkınlık)

Perplexity, kaybın üstel hâlidir: `perplexity = e^loss`. Sezgisel okuması: "Model, bir sonraki jetonu tahmin ederken ortalama kaç seçenek arasında bocalıyor?" Loss 1.0 → perplexity ~2.7; loss 2.3 → perplexity ~10. Dil modellemesinde en standart ölçüdür çünkü kayıpla birebir ilişkilidir ve üssel ölçekte daha sezgiseldir.

:::caution
Perplexity yalnızca **aynı tokenizer** kullanan modeller arasında karşılaştırılabilir. Jeton dağılımı farklı iki modelin perplexity sayıları elma-armut kıyaslamasıdır. Ayrıca perplexity düşmesi, sohbet kalitesinin arttığı anlamına gelmez — sadece "metni daha iyi tahmin ediyor" der.
:::

### Perplexity Tuzakları: Sayı Neden Yanıltır?

- **`e^loss` büyütücüdür:** Perplexity, ortalama kaybın üstel hâlidir; kayıptaki küçük farklar ppl'de büyütülerek görünür. Örnek: loss 0,69 → ppl ≈ 2; loss 2,30 → ppl ≈ 10; loss 4,61 → ppl ≈ 100. Yani "0,7 kayıp farkı" aslında 10 kat demektir — hangi ölçekte konuştuğunuzu netleştirin.
- **Tokenizer karşılaştırmayı bozar:** Aynı metin, farklı tokenizer'da farklı sayıda jeton üretir; jeton başına kayıp da doğal olarak değişir. Hugging Face dokümanı bunu açıkça uyarır: farklı tokenizer'lı modellerin perplexity'si karşılaştırılamaz.
- **Uzun bağlamda naif pencereleme şişirir:** Metin modelin bağlam penceresinden uzunsa ve düz parçalara (chunk) bölünüp her parça bağımsız puanlanırsa, her parçanın başı "bağlamsız" tahmin edildiği için ppL olduğundan yüksek çıkar. Çözüm, Hugging Face'in önerdiği **kaydırmalı pencere (sliding window / strided) değerlendirmedir**: pencere adımı bağlam uzunluğundan küçük tutulur ve yalnızca yeni jetonlar kayba girer; bağlam taşınır. Fark küçümsenmez: dokümandaki GPT-2 örneğinde aynı metin, adım 1024 iken ppl 19,44; adım 512 iken 16,44 çıkıyor — yani teknik seçimi 3 puanlık "iyileşme" gibi görünür.
- **Düşük ppl ≠ iyi asistan:** Perplexity metin tahminini ölçer; talimat takibi, doğruluk ve üslup değil. Sohbet kalitesi için görev metrikleri veya LLM-as-judge'a geçin.

(Ayrıntı ve kod örneği: Hugging Face "Perplexity of fixed-length models" dokümanı; kaynakçada bağlantısı var.)

## "Loss Düştü Ama Cevaplar Kötü" — Neden Olur?

Bu, yeni başlayanların en çok şaşırdığı durumdur; açıklaması şudur:

1. **Ezber:** Model eğitim örneklerini kelime kelime öğrenmişse eğitim kaybı çok düşer; yeni sorularda ise tökezler. Doğrulama kaybı bunu yakalar — tekrar: onu izleyin.
2. **Format takıntısı:** Model, cevabın *içeriğini* değil *kalıbını* öğrenmiş olabilir (ör. hep "Elbette! İşte cevabınız:" diye başlıyor ama çıkan metin boş). Kayıp, jeton tahminini ölçer; doğru jetonları doğru **anlamla** üretip üretmediğini değil.
3. **Ölçtüğünüz şey eksik:** Kayıp, "model eğitim dağılımına ne kadar benzedi"nin ölçüsüdür. Sizin gerçek kullanımda aradığınız şey (yardımcılık, doğruluk, üslup) ayrıca ölçülmelidir.

Sonuç: Eğitim kaybı bir **araç göstergesidir** (motor sıcaklığı gibi), varış göstergesi değildir. Üretim kalitesini ölçmek için aşağıdaki yaklaşımlar gerekir ve hangisinin gerekli olduğu göreve bağlıdır.

## Görev Metrikleri Hızlı Turu

| Görev türü | Metrik | Ne ölçer | Ne zaman/nerede zayıf |
| --- | --- | --- | --- |
| Sınıflandırma | Accuracy | Doğru tahmin oranı | Sınıflar dengesizse yanıltıcı ("%99 hayır" diyen model %99 accuracy alır) |
| Sınıflandırma | Precision / Recall | Kesinlik / yakalama oranı | Hangi hata daha pahalıysa ona bakın (spam filtresi: precision; hastalık taraması: recall) |
| Sınıflandırma | F1 | İkisinin dengesi | Çok nadir sınıflarda hâlâ yanıltıcı olabilir |
| Üretim | Exact Match | Referansla birebir eşleşme | Serbest metinde aşırı sert; tek kelime farkı bile "yanlış" sayar |
| Üretim | BLEU | n-gram örtüşmesi (çeviri geleneği) | Anlamı ölçmez; farklı ama doğru çeviriyi cezalandırır |
| Üretim | ROUGE | Referansla kelime/ifade örtüşmesi (özetleme geleneği) | Kelime oyunlarıyla kandırılabilir; akıcılığı ölçmez |
| Sıralama | MRR | İlk doğru sonucun kaçıncı sırada olduğu | Yalnızca ilk sonuçla ilgilenir |
| Sıralama | NDCG | Tüm sıralamanın kalitesi (kademeli) | Anlamak için biraz matematik ister; küçük setlerde oynak |

### Üretim Metriklerinde Derinleşme: BLEU'nun Sınırı ve Alternatifler

Tablodaki üretim metriklerinin ortak sınırı şudur: **tek bir referans, doğru cevapların çeşitliliğini temsil etmez.** Aileye yakından bakalım:

| Metrik | Ne yapar | Sınırı / dikkat |
| --- | --- | --- |
| BLEU | n-gram örtüşmesini "kesinlik" yönünden ölçer (çeviri geleneği) | Anlamı ölçmez; eşanlamlıyı kaçırır, farklı ama doğru çeviriyi cezalandırır; çeviri dışında tek başına kullanılmamalı |
| ROUGE | Referansla kelime/ifade örtüşmesi (özetleme geleneği) | Uzun özetleri kayırır; akıcılık ve tutarlılığı ölçmez |
| Exact Match (EM) | Cevabı normalleştirip (küçük harf, noktalama) referansla birebir karşılaştırır | Yalnızca kısa cevaplı görevlerde (SQuAD tarzı) anlamlıdır; serbest metinde aşırı serttir |
| BERTScore (arXiv:1904.09675) | Jetonları bağlamlı gösterimlerle (BERT embedding) eşleştirir; eşanlamlıyı affeder | Yine de referansa bağlıdır; "tamamen farklı ama doğru" cevabı tam yakalayamaz |
| MAUVE (arXiv:2102.01454) | Modelin metin havuzu ile insan metni havuzunun dağılım örtüşmesini ölçer | Tek tek referans gerekmez ama insan metni havuzu gerektirir; açık uçlu üretim (sohbet) için uygundur |
| pass@k (arXiv:2107.03374) | Kodda: k örneğin en az birinin testleri geçmesi yeterlidir | k büyüdükçe skor mekanik yükselir; her zaman k ile birlikte raporlayın (pass@1 ile pass@10 karşılaştırılamaz) |

:::note
Pratik seçim kuralı: **referans varsa** (çeviri, kısa cevap) BLEU/ROUGE/EM hâlâ kullanışlı bir başlangıçtır; **tek doğru cevap yoksa** (sohbet, özet, üslup) MAUVE, LLM-as-judge veya insan değerlendirmesine geçin. BERTScore ikisinin arasında makul bir köprüdür.
:::

### Precision / Recall / F1: Küçük Bir Hesap

100 e-postalık bir spam filtresi düşünün: gerçekte 10 spam var; model 12 e-postayı "spam" işaretledi ve bunların 8'i gerçekten spam çıktı.

- **Precision** = doğru işaretlenen / işaretlenen toplam = 8/12 ≈ 0,67 → "spam dediklerimin %67'si gerçekten spam"
- **Recall** = doğru işaretlenen / gerçek spam sayısı = 8/10 = 0,80 → "spamlerin %80'ini yakaladım"
- **F1** = harmonik ortalama = 2 × (0,67 × 0,80) / (0,67 + 0,80) ≈ 0,73

Hangi metriğin "daha önemli" olduğu hatanın maliyetine bağlıdır: önemli bir e-postayı spam saymak (precision sorunu), kaçırılan bir spamdan (recall sorunu) genelde daha can sıkıcıdır. Kendi projenizde bu maliyeti önce netleştirin, sonra metriğe karar verin.

:::tip
Basit bir ilke: **Ölçtüğünüz şeye optimize edersiniz.** Bu yüzden metrik seçimi, ürün kararınızla hizalı olmalı. Özetleme yapıyorsanız ROUGE/BLEU'ya tek başına güvenmek yerine "insan okuyunca özet yeterli mi?" sorusunu puanlamaya dahil edin.
:::

### Sınıflandırmada Derinleşme: Karışıklık Matrisi, Eşik ve AUC

Precision/recall hesabının arkasındaki tablo **karışıklık matrisidir** (confusion matrix); ikili sınıflandırmada dört hücre vardır:

| Durum | Model: "pozitif" dedi | Model: "negatif" dedi |
| --- | --- | --- |
| Gerçek: pozitif | Doğru pozitif (TP) | Yanlış negatif (FN — kaçırılan) |
| Gerçek: negatif | Yanlış pozitif (FP — yanlış alarm) | Doğru negatif (TN) |

- Precision = TP / (TP + FP); Recall = TP / (TP + FN). Spam örneğinde TP=8, FP=4, FN=2 → precision 8/12, recall 8/10: tablo ile hesap birebir örtüşür.
- **Eşik (threshold) her şeyi değiştirir:** Model genelde bir olasılık üretir; "spam" demek için 0,5 yerine 0,8 eşiğini seçerseniz precision artar, recall düşer. Eşik seçimi bir "model ayarı" değil, ürün kararıdır: hangi hatanın maliyeti yüksekse eşik ona göre seçilir.
- **ROC-AUC ile PR-AUC farklı sorulara cevap verir:** ROC eğrisi tüm eşiklerde doğru pozitif oranına karşı yanlış pozitif oranını çizer; AUC bunu tek sayıya indirger. Ama sınıflar dengesizse (ör. görevlerin %1'i pozitif) ROC-AUC iyimser görünebilir; asıl sınıfın nadir olduğu durumlarda **PR-AUC** (precision-recall eğrisinin altında kalan alan) durumu daha dürüst anlatır (Saito & Rehmsmeier, PLOS ONE, 2015).
- Çok sınıflı işlerde matris genişler ve asıl fayda orada ortaya çıkar: hangi sınıfların birbiriyle karıştığını görmek, "accuracy %85" gibi tek sayıdan çok daha kullanışlıdır.

:::tip
Raporlarken tek sayı yerine üçlüyü yazın: "precision 0,92, recall 0,61 (eşik 0,5)". Eşiği yazmayan rapor okunamaz; iki modeli karşılaştırırken de aynı eşikte ölçüldüğünden emin olun.
:::

## LLM-as-Judge (Yargıç Model)

Üretim görevlerinde (sohbet, özetleme, üslup) tek doğru cevap yoktur; bu yüzden "başka bir güçlü modele puanlatma" yöntemi yaygınlaştı: **LLM-as-judge**. Yöntem: A modelinden ve B modelinden aynı soruya cevap alın, güçlü bir yargıç modele (ör. büyük bir ticari model veya sizden büyük bir yerel model) "hangisi daha iyi ve neden?" diye sorun ya da 1-5 arası puanlatın.

**Avantajları:** İnsan değerlendirmesinden çok daha hızlı ve ucuz; ölçeklenebilir; kriter listesi verildiğinde tutarlı olabilir.

**Tuzakları ve önlemler:**

- **Kendi çıktısını sever:** Yargıç model kendi ailesinden çıktılara önyargılıdır. Önlem: yargıç olarak, karşılaştırdığınız modellerden **farklı bir aile** seçin.
- **Sıra etkisi:** Sunum sırası (A önce mi B önce mi) sonucu etkiler. Önlem: her çifti iki sırayla da değerlendirin (A-B ve B-A) ve sonuçları birleştirin.
- **Belirsiz rubrik:** "Hangisi iyi?" yerine net kriterler verin: "Doğruluk, dil bilgisi, istenen üslup ve uzunluk kısıtına uyum açısından 1-5 puanla."
- **Kalibrasyon:** 20-30 örneği kendiniz elle puanlayıp yargıcın puanlarıyla karşılaştırın; uyuşmuyorsa rubriği düzeltin.

## İstatistiksel Anlamlılık: Skor Farkları Ne Zaman Gerçek?

"Model A %71 aldı, model B %69" cümlesi tek başına neredeyse hiçbir şey söylemez; çünkü her ölçüm örnekleme gürültüsü içerir. 100 soruluk bir testte **tek bir soru 1 puan eder** ve soru seçiminiz biraz farklı olsaydı sıralama değişebilirdi. Kaba bir kalibrasyon (≈ %70 doğruluk ve bağımsız örnekleme varsayımıyla):

| Test boyutu | Standart hata (yaklaşık) | İki skor arası "gürültü bandı" |
| --- | --- | --- |
| 100 soru | ≈ 4,6 puan | ≈ 6,5 puan |
| 500 soru | ≈ 2,0 puan | ≈ 2,9 puan |
| 1.000 soru | ≈ 1,4 puan | ≈ 2,0 puan |
| 10.000 soru | ≈ 0,5 puan | ≈ 0,7 puan |

Hesabın mantığı: standart hata ≈ √(p(1−p)/n). %70 doğrulukta n=100 için √(0,7×0,3/100) ≈ 0,046, yani ±4,6 puan. İki bağımsız ölçümün farkının standart hatası bunun yaklaşık √2 katıdır; tablodaki "gürültü bandı" bu değerdir. Sonuç: 100 soruluk sette 5 puanlık fark "kesin üstünlük" sayılmaz; 1.000 soruluk sette 2 puanlık fark ciddiye alınabilir.

- **Güven aralığı raporlayın:** "70 ± 5" gibi. Miller'ın "Adding Error Bars to Evals" notu tam bunu önerir: ortalama ile birlikte standart hatayı yazın ve anlamlı sinyal için test setinin yeterince büyük olmasını şart koşun (bu notta "güçlü sinyal" ölçütü en az ~1.000 sorudur; arXiv:2411.00640).
- **LLM-yargıçta da aynı sorun:** Yargıçla 50 çift karşılaştırıp "kazanma oranı %58" bulduysanız bu büyük olasılıkla gürültüdür. Çift sayısını artırın veya aralık verin.
- **Küçük sette sıralama yarışına girmeyin:** Panolardaki "2 puan fark" iddialarının bir kısmı bu bandın içindedir; bu yüzden [Benchmark'lar](/degerlendirme/benchmarklar/) sayfasında tarih, sürüm ve kurulum etiketlemesini o kadar vurguluyoruz.

## Kısa Not: Kontaminasyon Sessiz Katildir

Test sorularının (veya çok benzerlerinin) eğitim verisine sızması **kontaminasyondur** (veri sızıntısı); böyle bir skor "başarı" değil, ezberin ölçüsüdür. En çok konuşulan örneklerden biri GSM8K → GSM1k'tir: GSM8K'da çok yüksek skor alan bazı modeller, aynı tarzda **yeni yazılmış** GSM1k sorularında belirgin düşüş gösterdi (arXiv:2405.00332). Sizin için pratik sonuçları:

- Temizlenmiş / çapraz kontrol edilmiş sürümleri tercih edin (ör. SWE-bench Verified, GPQA Diamond).
- Kendi mini setinizi kurarken bir bölümünü "hiç bakmadan" kenarda tutun; üzerinde çalıştıkça farkında olmadan o sete göre ayar yapabilirsiniz (insan kaynaklı sızıntı).
- Bir skor "fazla iyi" görünüyorsa önce sızıntıyı sorun; ikinci olarak kurulum farklarını kontrol edin ([Benchmark'lar](/degerlendirme/benchmarklar/)).

## Pratik: Eğitim Sırasında İzlenecek 4 Sayı

Eğitimin başında bu dört sayıyı not edin; her biri bir şeyin göstergesidir:

| Sayı | İdeal davranış | Anormal örüntü ve anlamı |
| --- | --- | --- |
| `loss` (eğitim) | Düzenli ama gürültülü şekilde iniş | Hiç düşmüyorsa: lr/veri sorunu; sıfıra yakınsa: ezber |
| `eval_loss` (doğrulama) | Eğitimle paralel iner, sonra düzleşir | Erken yükselirse: ezber, durdurun |
| `learning_rate` | Planlanan eğriyi izler (cosine/linear) | Sıfır kalıyorsa: scheduler/warmup ayarı bozuk |
| `grad_norm` | Aynı mertebede dalgalanır | Ara ara patlıyorsa: lr yüksek veya veri sorunlu; hep 0'a yakınsa: gradyan akmıyor (maskeli etiketler?) |

Gradyan normu (gradient norm), gradyanların büyüklüğünün ölçüsüdür. Eğitim araçlarının çoğu bunu günlüğe kaydeder; kaydetmiyorsa `logging_steps` çıktısında görünür. Eğitimin "sağlık paneli" diyebileceğiniz bu dört sayı, çoğu sorunu daha büyük hasar oluşmadan yakalamanızı sağlar.

## Toparlarsak

- Kayıp bir araçtır, hedef değildir; eğitim + doğrulama kaybını birlikte izleyin.
- Dört tipik eğriyi tanıyın: sağlıklı, ezber, sabit, zıplayan.
- Perplexity yalnızca aynı tokenizer'lı modeller arası karşılaştırılabilir.
- "Kayıp düştü ama cevaplar kötü" durumunda üretim kalitesini göreve uygun metriklerle veya LLM-as-judge ile ölçün.
- Eğitim sırasında `loss`, `eval_loss`, `learning_rate` ve `grad_norm` değerlerini izlemek dörtlü bir sağlık paneli oluşturur.

Devam: [Benchmark'lar ve Gerçek Değerlendirme](/degerlendirme/benchmarklar/) ile modelleri karşılaştırın; kötü eğriyi düzeltmek için [Hiperparametreler](/llm/hiperparametreler/) sayfasına dönün.

## Kaynaklar ve İleri Okuma

- [Hugging Face — Perplexity of fixed-length models](https://huggingface.co/docs/transformers/en/perplexity) — e^loss mantığı, tokenizer uyarısı ve kaydırmalı pencere tekniği (GPT-2 örnekli kodla).
- [BERTScore (arXiv:1904.09675)](https://arxiv.org/abs/1904.09675) — bağlamlı gösterimlerle üretim metni değerlendirme.
- [MAUVE (arXiv:2102.01454)](https://arxiv.org/abs/2102.01454) — model metni ile insan metni dağılımları arasındaki boşluğu ölçen metrik.
- [Saito & Rehmsmeier, PLOS ONE (2015)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432) — dengesiz veride PR eğrisinin ROC'tan neden daha bilgilendirici olduğu.
- [Adding Error Bars to Evals (arXiv:2411.00640)](https://arxiv.org/abs/2411.00640) — değerlendirmelerde standart hata, güven aralığı ve gereken soru sayısı.
- [LLM Performansı Üzerine Dikkatli Bir İnceleme: GSM1k (arXiv:2405.00332)](https://arxiv.org/abs/2405.00332) — kontaminasyonun skorlara etkisinin çarpıcı örneği.
- [Codex makalesi (arXiv:2107.03374)](https://arxiv.org/abs/2107.03374) — pass@k metriğinin çıkış noktası.
- [Judging LLM-as-a-Judge / MT-Bench (arXiv:2306.05685)](https://arxiv.org/abs/2306.05685) — yargıç modellerin konum, uzunluk ve öz-kayırma yanlılıkları.
