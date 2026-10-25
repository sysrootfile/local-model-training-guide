---
title: "RAG Değerlendirmesi: Arama mı Bozuk, Üretim mi?"
description: "RAG sistemini ölçmenin pratiği — hit@k ve MRR ile getirim ölçümü, parafraz sağlamlığı, kapsam dışı soru eşiği ve sadakat kontrolü. Tüm deneyler bu rehberin Örnek 5 korpusu üzerinde gerçekten çalıştırıldı."
dogrulama: 2026-10-19
---

[RAG karar sayfası](/rag/rag-mi-ince-ayar-mi/) boru hattını kurmayı, [Örnek 5](/ornekler/yerel-rag/) çalıştırmayı öğretti. Bu sayfanın sorusu farklı: **kurduğunuz sistem iyi mi?** Ve bir RAG sisteminde "iyi" tek bir şey değildir — iki ayrı makine var: **arama** (doğru belge bulunuyor mu?) ve **üretim** (bulunan belgeyle doğru cevap yazılıyor mu?). İkisini ayrı ölçmeden iyileştirme, kapalı gözle tamir demektir.

:::note[Bu sayfadaki tüm sayılar gerçek ölçümdür]
Deneyler, Örnek 5'in korpusu (kurgusal Bulut Kargo A.Ş., 8 belge) ve `olc.py` betiğiyle **bu makinede gerçekten çalıştırıldı** (Ollama 0.40.4 — makine 2026-10-19'da 0.40.6, bu sayfadaki sayılar o sürümde yeniden ölçülmedi; bge-m3 ve nomic-embed-text embedding modelleri; tam günlük `ornekler/yerel-rag/cikti/olc-kaydi.txt`). Küçük korpuslu bir deneydir: **kalıbı** gösterir, evrensel rakam vermez.
:::

## İki Katmanı Ayrı Ölçün

Cevap yanlış geldiğinde ilk soru şudur: **arayan mı şaşırdı, yazan mı?**

| Belirti | Getirilen parçalara bakın | Suçlu | İlaç |
| --- | --- | --- | --- |
| Doğru parça hiç gelmemiş | Doğru parça ilk k'ta yok | Arama | Embedding modeli, parçalama, [hibrit arama](/rag/parcalama-ve-hibrit-arama/) |
| Doğru parça var ama cevap yanlış | Doğru parça bağlamda | Üretim | Talimat, model boyutu, bağlam formatı |
| Model "bilmiyor" demesi gerekirken uyduruyor | Alakasız parçalar bağlamda | İkisi birden | Eşik + sistem talimatı |

Pratik kural: hata ayıklamaya **her zaman arama kaydından başlayın** — hangi parçaların getirildiğini log'lamıyorsanız, ilk yapılacak iş onu eklemektir. Örnek 5'in betiği her sorguda `[arama] en iyi benzerlik: 0.709 -> iade, hasar` satırını basar; o satır, bu sayfanın tüm metodolojisinin ham maddesidir.

## Getirim Metrikleri: hit@k ve MRR

Aramayı ölçmek için küçük bir **test seti** kurarsınız: sorular ve her soru için "doğru cevabın olduğu" belge/parça kimliği. Örnek 5'te bu `TEST_SORULARI` listesidir (6 soru). İki temel ölçü:

- **hit@k:** Doğru parça ilk k sonucun içinde mi? k'yi, sistemin bağlama eklediği parça sayısına eşit seçin (Örnek 5'te k=2; test 3'e kadar raporlar). Kullanıcıya gösterilmeyecek sonucu bulmak da hatadır — k'yi büyütmek isabeti yükseltir ama bağlamı kirletir; ölçüm k'yi yansıtmalıdır.
- **MRR (ortalama ters sıra):** Doğru parçanın sırasının tersini (1/rank) sorular boyunca ortalar. Doğru parça hep 1. sıradaysa MRR=1,0; 3. sıradaysa o soruya katkı 0,333'tür. hit@k "girdi mi?" der, MRR "ne kadar üstte?" der — ikisi birlikte okunur.

Ölçümün dürüstlüğü test setinin dürüstlüğüne bağlıdır: her soruyu **cevabını bildiğiniz belgeyle eşleştirin** ve seti sisteme bakarak değil, kullanıcı sorularından kurarak yazın. 20-30 soruluk bir set, yön tayini için yeterlidir; tek haneli farkları bu boyutta okumayın — gürültü o kadar.

## Parafraz Sağlamlığı: Aynı Soru, Farklı Kelimeler

En sık yapılan ölçüm hatası: test sorularını, belgelerin dilini taklit ederek yazmak. "İade süresi 14 gündür" belgesine "iade süresi ne kadar?" diye sorarsanız anahtar kelime zaten uyuşmuştur — model kolay sınavdan geçmiştir. Kullanıcı ise "ürünü geri gönderebilir miyim?" diye sorar. Bu yüzden her soru için **parafraz** (aynı bilgi ihtiyacının farklı ifadesi) ölçmelisiniz.

`olc.py` tam olarak bunu yaptı: 6 orijinal sorunun yanına 6 parafraz yazdı ve iki embedding modelini aynı testten geçirdi:

```text title="Gerçek ölçüm (olc.py, 2026-10-15)"
                          hit@1(ory)   hit@1(para)   MRR(para)
  bge-m3                      1.00          1.00        1.000
  nomic-embed-text            0.83          0.50        0.667
```

İki ders:

1. **Parafraz, gizlenen kırılganlığı açığa çıkarır.** nomic-embed-text orijinal sorularda 0,83'lik "iyi görünen" bir isabetle geçti; kelimeler değişince 0,50'ye düştü. Kaçanlar açıklayıcı: "Elimdeki gönderi ne zaman bana ulaşır?" sorusu *teslimat* yerine *hasar* belgesini ilk sıraya koydu — "ulaştı/ulaşır" kelimesinin çağrışımı kelime düzeyinde baskın çıktı.
2. **Test setinizde her bilgi ihtiyacından en az 2 ifade olmalı.** Orijinal + parafraz toplamı 12 soruda bile fark gözle görülürken, 6 soruluk orijinal set tek başına nomic'i "başarılı" diye etiketleyebilirdi.

## Eşik: Kapsam Dışı Sorularla Ayırma Payı

Örnek 5'te "Ankara'da hava nasıl?" sorusunun belgelerle ilgisi düşükken modelin "bilmiyor" demesini gördük. Bu davranış tesadüf değildir: kapsam içi ve kapsam dışı soruların benzerlik dağılımı arasında **boşluk** vardır ve eşik bu boşluğa konur. `olc.py` bu dağılımı sayılarla çıkardı:

```text title="Benzerlik bantları (gerçek ölçüm)"
  bge-m3            kapsam içi: 0.580 - 0.740   kapsam dışı: 0.274 - 0.408
  nomic-embed-text  kapsam içi: 0.660 - 0.784   kapsam dışı: 0.586 - 0.675
```

**ayırma payı = en düşük kapsam içi − en yüksek kapsam dışı:**

- bge-m3: 0,580 − 0,408 = **+0,172** → aralarına çizgi çekmek mümkün (Örnek 5'in `ZAYIF_ESIK = 0.35` eşiği tam bu boşluğa konmuş)
- nomic-embed-text: **−0,015** → bantlar **çakışıyor**; hiçbir eşik bu sistemde "bilmiyor" davranışını üretemez

İkinci ders daha da önemli: nomic, alakasız Türkçe sorulara bile 0,59-0,68 benzerlik verdi — yani **kendinden emin bir şekilde alakasız belge getirdi.** İngilizce odaklı bir embedding modelinin Türkçe uzayında "her şey birbirine benziyor" sorunu, sessiz kalma davranışını da öldürür: sistem ya alakasız cevap üretir ya uydurur.

:::caution[Eşik, modelin parmak izidir]
Örnek 5'teki 0,35 eşiği bge-m3'ün dağılımından çıktı. Embedding modelini değiştirdiğiniz an eşik **geçersizdir** — yeni modelin kapsam içi/kapsam dışı bantlarını yeniden ölçüp eşiği yeniden koyarsınız. Kural: eşik, ölçümden sonra gelir; ölçümden önce kopyalanmaz. Aynı kayma model **eğitildiğinde** de olur, hatta sorguya eklenen bir önekle de olur: [Gömme Modeli Eğitmek](/rag/gomme-egitimi/) sayfasındaki önek deneyinde sıralar birebir aynı kalırken doğru parçaların bandı ~0,08 aşağı indi.
:::

### Aynı eşik, ikinci korpus: taşımak neden tehlikeli

Aynı `olc.py` mantığı [Örnek 6](/ornekler/viki-rag/) ile, yani 125 parçalık canlı Vikipedi korpusunda tekrarlandı (bge-m3, 2026-10-15; günlük `ornekler/viki-rag/cikti/olc-kaydi.txt`). Sonuç, yukarıdaki kuralın sadece model değişince değil **korpus değişince** de işlediğini gösterdi:

```text title="125 parçalık korpusda ölçülen bantlar (bge-m3)"
  kapsam içi (12 soru) : 0.598 - 0.714   hit@1 orijinal 0.83 / parafraz 0.67
  kapsam dışı (8 soru) : 0.321 - 0.485
  ayırma payı          : +0.113          eşik önerisi: 0.541
  devralınan 0.35      : BANTLARIN DIŞINDA — bu korpusta geçersiz
```

Aynı betik ikinci modeli de koştu — aynı 125 parça, aynı 20 soru:

```text title="Aynı korpus, ikinci model (nomic-embed-text, boyut=768)"
  kapsam içi (12 soru) : 0.624 - 0.808   hit@1 orijinal 0.83 / parafraz 1.00
  kapsam dışı (8 soru) : 0.642 - 0.737
  ayırma payı          : -0.112
  eşik önerisi         : YOK — bantlar çakışıyor
```

Üç yeni ders:

1. **Küçük korpus, iyimser eşik.** 8 belgelik Örnek 5'te kapsam dışı bant 0,41'de duruyordu; 125 parçalık gerçek bir korpusda 0,485'e çıktı. Parça sayısı arttıkça "alakasız soruya bile benzeyen bir parça" bulunma olasılığı artar — boşluk **küçülür**, pay düşer (+0,172 → +0,113).
2. **Kapsam dışı set bariz alakasızlıklardan kurulmamalı.** Örnek 6'da "Evde pizza hamuru nasıl yapılır?" 0,344 alırken, "İstanbul" kelimesini içeren alakasız sorular 0,45-0,48'e çıktı (ucuz otel, Borsa İstanbul, Galatasaray). Gerçek kullanıcılar korpusun konusuna değen ama cevabı olmayan sorular sorar; eşiği yalnız pizza tarifleriyle ayarlarsanız bu sınıfı kaçırırsınız.
3. **Bant çakışması bir ölçüm sonucudur, hata değil.** nomic-embed-text'te getirimin kendisi fena değil: parafraz hit@1 **1,00** (bge-m3 0,67'de kaldı). Ama aynı model kapsam dışı sorulara 0,642-0,737 veriyor, yani alakasız soru, alakalı sorunun bandının *içinde*. Bu modelle "bilmiyorum" dalı kurmak imkânsız: hangi eşiği koyarsanız koyun ya kapsam içi soruları da susturursunuz ya kapsam dışını hiç yakalamazsınız. Getiri kalitesi ile eşe-uygunluk ayrı özelliklerdir — birini ölçmek diğerini garanti etmez.

Örnek 6'nın kodundaki `ZAYIF_ESIK` bu ölçümden sonra 0,54'e çekildi (`olc.py` ise karşılaştırmayı bozmamak için 0,35'i test etmeye devam eder). Sayfanın kendisi de artık bunu yazıyor: [Parçalama ve Hibrit Arama](/rag/parcalama-ve-hibrit-arama/) ölçümün tekrarını, karar listesiyle birlikte anlatıyor.

## Embedding Modelini Değiştirmek Ne Değiştirir?

İki deneyin tamamı tek tabloda — hepsi aynı korpus, aynı sorular, yalnızca embedding modeli farklı:

| Ölçü | bge-m3 (çok dilli) | nomic-embed-text (İngilizce odaklı) |
| --- | --- | --- |
| hit@1 (orijinal), 8 belge | 1,00 | 0,83 |
| hit@1 (parafraz), 8 belge | 1,00 | 0,50 |
| MRR (parafraz), 8 belge | 1,000 | 0,667 |
| Kapsam dışı bandı, 8 belge | 0,27-0,41 | 0,59-0,68 |
| Ayırma payı, 8 belge | +0,172 | −0,015 |
| hit@1 (orijinal), 125 parça | 0,83 | 0,83 |
| hit@1 (parafraz), 125 parça | 0,67 | 1,00 |
| MRR (parafraz), 125 parça | 0,767 | 1,000 |
| Kapsam dışı bandı, 125 parça | 0,321-0,485 | 0,642-0,737 |
| Ayırma payı, 125 parça | +0,113 | −0,112 |

Son iki satır model yorumunu tersine çevirir: büyük korpustan parafraz getirimi **nomic** daha iyi ölçtü (1,00 / 0,67), ama eşik için gereken ayrımı o değil **bge-m3** verdi. Tek modele güvenen tek bir tablo, yanlış sonuca götürebilir — bu yüzden ölçümü hem korpus hem model boyutunda tekrarlamak gerekir.

Sonuç, [RAG karar sayfasındaki](/rag/rag-mi-ince-ayar-mi/) "embedding seçimini kendi verinizle ölçün" tavsiyesinin sayısal kanıtıdır: Türkçe içerikte model seçimi "ufak verim farkı" değil, **sistemin çalışıp çalışmaması** sorunu olabilir. Ölçüm rutini ucuzdur — aynı test seti her modele koşar; tek uyarı, CPU'da 125 parçalık bir korpusun model başına dakikalar tutmasıdır. Ölçülen (2026-10-16, `127.0.0.1`): bge-m3 **259,2 sn**, nomic-embed-text **158,6 sn**. Aynı betikler 2026-10-15'te `localhost` adresiyle 495,7 ve 503,7 sn çıkmıştı; farkın neredeyse tamamı istek başına ~2 sn'lik Windows isim çözümleme gideriydi, skorlar iki koşumda da aynı kaldı.

Bir işlem notu: embedding modelini değiştirdiğinizde **tüm indeksi yeniden oluşturmanız gerekir** (vektörler modelin uzayındadır; iki modelin vektörleri karışmaz). Üretici modeli değiştirmek böyle bir maliyet doğurmaz — [Örnek 5'teki](/ornekler/yerel-rag/) "üç model, üç iş" kutusunun pratik sonucu.

## Üretim Tarafını Ölçmek: Sadakat ve İlgi

Getirim ölçüldükten sonra sıra cevaba gelir. Üretim tarafının üç temel ölçüsü:

- **Sadakat (faithfulness):** Cevap, getirilen belgelerdeki bilgiyle tutarlı mı? Belgelerde olmayan bir sayı, cevabın nereden geldiği belirsiz bir iddiadır.
- **Cevap ilgisi:** Cevap, sorulan soruyu gerçekten yanıtlıyor mu? (Alakalı ama sorusuz cevaplar klasik hatadır.)
- **Alıntı doğruluğu:** Gösterilen kaynak gerçekten kullanılan belge mi? Örnek 5'in kapsam dışı testinde küçük model doğru "bilmiyorum" cevabına **uydurma bir kaynak** eklemişti — alıntıyı programatik doğrulamak (gösterilen kimlik, getirilen kimliklerle eşleşiyor mu?) tek satırlık bir kontroldür ve mutlaka yapılır.
- **Gecikme:** Kaliteli ama 65 saniye süren bir RAG cevabı, pratikte kullanılmaz. Bu ölçü de ölçülebilir: arama **0,09-0,13 sn** (sorguyu gömmek, 2026-10-16 koşumu; bir önceki koşumda 0,10-0,16 sn), üretim **52-66 sn** (Örnek 6'nın 4 parçalık bağlamını okutmak) — CPU'da faz faz dökümü [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasında. Oradaki en beklenmedik bulgu, gecikmenin bir kısmının modelle hiç ilgisi olmaması: Windows'ta `localhost` adresi istek başına ~2 sn ekliyor. Betikler 2026-10-16'da `127.0.0.1`'e geçirilince Örnek 6'nın 125 parçalık indeksi **501,8 → 246,6 sn**'ye indi, benzerlik skorları ve hit@k satırları **hiç değişmedi**. Gecikmeyi ölçerken duvar süresi ile sunucunun işini ayrıştırın; aksi hâlde bir isim çözümleme giderini modelin yavaşlığı sanırsınız.

İlk üç ölçünün otomatik ölçümü için yaygın yaklaşım **LLM-yargıç**tir: güçlü bir modele "bu cevap belgelere sadakatli mi?" diye sorarsınız. Bu iş için tasarlanmış açık kaynak çerçeve **RAGAS**'tır (Es ve arkadaşları, 2023): sadakat, cevap ilgisi ve bağlam ilgisi ölçülerini soru-cevap-belge üçlüsü üzerinden hesaplar. İki dikkat: yargıç modeli de hata yapar (özellikle Türkçe'de) — RAGAS çıktısını periyodik elle örneklemeyle dengeleyin; ve yargıç olarak kullanacağınız modelin API maliyeti, soru sayısıyla doğru orantılıdır.

:::tip[Üç soruluk elle sadakat kontrolü]
Otomatik çerçeve kurmadan önce bile her hafta 5-10 rastgele cevabı üç soruyla elle okuyun: (1) Cevaptaki her olgusal iddia bir belge parçasında var mı? (2) Cevap soruyu tam yanıtlıyor mu? (3) Gösterilen kaynak doğru mu? Bu yarım saatlik rutin, otomatik ölçümlerin çöktüğünü ilk fark eden şey genellikle olur.
:::

## Pratik Ölçüm Rutini

RAG sisteminizde her anlamlı değişiklikten (parçalama boyutu, embedding modeli, k, talimat) sonra:

1. **Test setini çalıştırın:** orijinal + parafraz sorular → hit@k, MRR.
2. **Kapsam dışı seti çalıştırın:** benzerlik bantları → ayırma payı → eşik hâlâ geçerli mi?
3. **5-10 cevabı elle okuyun:** sadakat, ilgi, alıntı doğruluğu.
4. **Kaydı tutun:** hangi ayarla hangi sayı? Ölçüsü tutulmamış deney, tekrarlanmamış deneydir — Örnek 5 ve bu sayfanın tüm çıktıları `cikti/` klasöründe günlük olarak saklanıyor.

Ölçüler kötü geldiyse ilaç sırası genellikle şudur: önce **aramayı** düzeltin (parçalama, embedding, hibrit arama), sonra **talimatı**, en sonda **model boyutunu** — maliyet sırası budur: [RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/)

## Bu Sayfadaki Deney Nasıl Tekrarlanır?

`olc.py`, Örnek 5 klasöründedir ve `rag.py` ile aynı korpusu kullanır (tek doğruluk kaynağı):

```bash
cd ornekler/yerel-rag
python olc.py                    # iki modeli karşılaştır (bge-m3 + nomic-embed-text)
python olc.py --model bge-m3     # yalnızca bir model
```

Kendi korpusunuzda kullanmak için `rag.py`'deki `BELGELER` ve `TEST_SORULARI` listelerini değiştirmeniz yeterli — parafraz ve kapsam dışı listeleri `olc.py`'dedir. Harici paket gerekmez; yalnızca Ollama.

Aynı ölçü mantığının daha büyük bir korpusa taşınmış hâli [Örnek 6: Vikipedi'den Türkçe RAG](/ornekler/viki-rag/) — `ornekler/viki-rag/olc.py` 125 parçalık gerçek metin korpusunda hem hit@1/hit@4 hem de yukarıdaki ikinci bant tablosunu üretti. Arama kolunu iyileştirmenin ölçülmüş yoluysa ayrı bir sayfa: [Parçalama ve Hibrit Arama](/rag/parcalama-ve-hibrit-arama/).

## Kaynaklar ve İleri Okuma

- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis vd. 2020, arXiv:2005.11401)](https://arxiv.org/abs/2005.11401) — RAG'ın orijinal makalesi; boru hattının akademik kaynağı.
- [RAGAS: Automated Evaluation of Retrieval Augmented Generation (Es vd. 2023, arXiv:2309.15217)](https://arxiv.org/abs/2309.15217) — sadakat/cevap ilgisi/bağlam ilgisi ölçülerini tanımlayan çerçevenin makalesi.
- [RAGAS dokümanları](https://docs.ragas.io/) — çerçevenin kurulumu ve metriklerinin resmî rehberi.
- [Örnek 5: Yerel RAG Asistanı](/ornekler/yerel-rag/) — bu sayfanın deneylerinin korpusu, betiği ve eşik tartışması.
- [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) — benzerlik eşiği değil **üretim olasılığı** eşiği: aynı ders orada da tekrarlanıyor, ayırma payı tek seferlik bir sayıdır ve eşik başka bir modelde veya veri setinde yeniden taranmalıdır.
- [RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/) — karar haritası; parçalama ve yerel yığın bölümleri.
- [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) — eğitim tarafındaki kayıp eğrilerini okuma; RAG değerlendirmesinin eğitim karşılığı.
- [Benchmarklar ve Değerlendirme](/degerlendirme/benchmarklar/) — model düzeyi ölçümler ile sistem düzeyi ölçümlerin farkı.
