---
title: "Gömme Modeli Eğitmek: Kendi Korpusta Aramayı İyileştirmek"
description="Hazır bir embedding modelini kendi metinleriniz üzerinde eğitmenin mekanizması: çoklu negatif sıralama kaybı, zor negatif madenciliği, LoRA hedef katmanları ve GPU'suz bir makinede ölçülmüş adım süreleri. Aynı 24 parçalık Türkçe korpusta dört eğitim kolu gerçekten çalıştırıldı."
dogrulama: 2026-10-20
---

[RAG karar sayfası](/rag/rag-mi-ince-ayar-mi/) hangi sorunun ince ayarı haklı çıkardığını, [değerlendirme sayfası](/rag/rag-degerlendirme/) getirimin nasıl ölçüleceğini anlattı. İkisinin arasında bir boşluk kalıyor: **indeksi kuran gömme modelinin kendisi.** Vektörler kötüyse parçalamayı da prompt'u da üretim modelini de değiştirirsiniz, arama yine şaşırır. Bu sayfa o katmanı eğitmeyi anlatıyor — ve GPU'suz tek makinede çalıştırılmış sayılarla yapıyor.

Ölçüm kafesi `ornekler/gomme-egitimi/gomme_egit.py`, koşucu `kos.py`, kayıtlar `ornekler/gomme-egitimi/cikti/kol-*.txt`. Beş kol var: sıradan atış (A), eğitim (B), LoRA (C), batch tavanı (D) ve `/api/embed` istek gideri (E). A-D'nin sayıları bu sayfada; E'nin iki yanı, tekrar aralıkları ve hükmü [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasında yayımlandı, bu sayfa o sayıları tekrarlamaz. Aşağıdaki sayıların tamamı koşum bittikten sonra o kayıtlardan kopyalandı.

## Hangi Model, Hangi Makine?

Tabandaki model [`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2): kartın söylediği 384 boyutlu çıkış, `max_seq_length` 128, apache-2.0 lisansı, 50 dil. Karşılaştırma için yereldeki [`BAAI/bge-m3`](https://huggingface.co/BAAI/bge-m3) kullanıldı (Ollama `/api/embed` üzerinden): 1024 boyut, 8192 token girdi tavanı, MIT lisansı, kartın iddiası 100'den fazla çalışma dili.

Koşum **ekran kartı olmadan** yapıldı: Ryzen 5 2600, 15,9 GB RAM, `torch 2.6.0+cpu`, `sentence-transformers 6.1.0`, `peft 0.21.2`. İki Windows tuzağı yolda ortaya çıktı:

1. torch'ın 2.7 ve sonrası CPU wheel'ları bu makinede `OSError: [WinError 1114]` ile (`c10.dll` yüklenemiyor) kuruldu ama çalışmadı; kurulu VC++ çalışma zamanı 14.29. Sistem DLL'lerini güncellemek yerine `torch==2.6.0+cpu` sabitlendi ve eğitim bu sürümle koştu.
2. `sentence-transformers==3.0.1` kurmak `huggingface-hub`'ı düşürüp `datasets 5.1.0`'ı `BucketNotFoundError` ile kırdı. İkisi birlikte ancak 6.x hattında çalıştı.

:::note[Bu sayfa neyi iddia etmiyor]
Test kümesi 8 soru / 24 parça ve tamamı kurgusal bir mahalle için elle yazıldı. Bu tablo "MiniLM kötü, bge-m3 iyi" demez; **bu korpustaki davranışı** ölçer. Güven aralığı hesaplanmadı. GPU, dağıtık eğitim ve yüz binlerce çiftlik gerçek bir veri seti bu makinede **çalıştırılmadı**.
:::

## Sıradan Atış: Eğitim Öncesinde Neredesiniz?

Kol A hiçbir şey eğitmez; eğitimsiz taban modeli sabit bir test kümesine sokar. Gövde 24 parça, sorgu 8 tane; eğitim çiftleriyle **bilerek ayrık** — aynı cümle iki tarafta geçmiyor.

| Ölçüm | Değer |
| --- | --- |
| Önbellekten model yükleme | 12,70 sn (aynı oturumda ikinci yükleme 4,51 sn) |
| Parametre / çıkış boyutu | 117.653.760 / 384 |
| İndirilen ağırlık klasörü | 457,5 MB |
| Süreç belleği (RSS) | 179 MB → 1170 MB (+991 MB) |
| Encode hızı | 24 parça 0,25 sn (97,4 parça/sn) · 8 sorgu 0,07 sn (117,3 sorgu/sn) |
| Gövde parça token sayıları | en kısa 18, ortalama 22,3, en uzun 30 |
| bge-m3 indeksleme (Ollama) | 15,77 sn → 1,5 parça/sn, 8 sorgu 1,03 sn |

İki katmanlı bir maliyet tablosu çıkıyor: **eğitim** (bir defa) ve **yeniden indeks** (model her değişince). 24 parçalık mahalle bülteni MiniLM ile saniyenin dörtte birinde indeksleniyor; aynı işi 566 milyon parametreli bge-m3'e yaptırmak 16 sn sürüyor. Kol B'de her eğitimin ardından yeniden indeks 0,33–0,40 sn — küçük korpusta bedava. Kurumsal ölçekte (yüz binlerce parça) tablonun tersine dönmesi beklenir: orada indeksi yeniden kurmak, modeli eğitmekten pahalı olabilir. Bu cümle burada **ölçülmedi** — elimizdeki tek veri, küçüğün küçüğü bir kümede yeniden indekslemenin saniyenin altında sürdüğü.

## Puanlama Biçimi Bir Hiperparametredir

Aynı model, aynı sorular, aynı gövde; yalnızca mesafe tanımı değişiyor:

| Puanlama | hit@1 | hit@3 | MRR | Doğru parçaların bandı (ort.) | En iyi yanlış | Ayrışma |
| --- | --- | --- | --- | --- | --- | --- |
| normalize + kosinüs | 7/8 | 8/8 | 0,938 | 0,305–0,718 (0,609) | 0,541 | **−0,236** |
| normalize + negatif Öklid | 7/8 | 8/8 | 0,938 | −1,390 – −0,565 (−0,782) | −0,918 | −0,472 |
| ham + nokta çarpımı | 7/8 | 8/8 | 0,917 | 4,377–12,345 (9,252) | 8,935 | −4,558 |
| ham + negatif Öklid | **6/8** | 8/8 | 0,875 | −21,140 – −9,066 (−12,223) | −12,181 | −8,959 |

**Ayrışma** = doğru parçanın en düşük skoru − en iyi yanlış parçanın skoru. Dört satırın dördü de negatif, yani hiçbir koşutta "doğruyu yanlışlardan ayıran temiz bir eşik" yok. Üçüncü satır normalize edilmemiş nokta çarpımı: uzun parçalar kayrılıyor (MRR 0,938 → 0,917, bir soru 1. sıradan 3. sıraya düşüyor). Dördüncü satır ham + Öklid: hit@1 **7/8'den 6/8'e** iniyor.

:::caution[Mesafe seçimi sonuç değiştirir]
"Kosinüs mü, Öklid mi?" estetik bir tercih değil. Vektörler normalize edildiyse üç ölçüm de **aynı sıralamayı** verir; yukarıdaki ilk iki satırın rütbeleri zaten birebir aynı. Fark, normalize etmeyi **unuttuğunuz** anda ortaya çıkıyor: ham + negatif Öklid satırında iki soru daha ilk sıradan düştü ve hit@1 7/8'den 6/8'e indi. Vektörleri kaydederken normalize edip etmediğinizi de kaydedin — [lisans/model kartı sayfasında](/kullanim/lisans-ve-model-karti/) anlatılan "indeksi neyin kurduğunu yazmak" tam olarak budur.
:::

## Sorgu Öneki: Sıra Değişmiyor, Skor Değişiyor

Bazı gömme modelleri sorguya İngilizce bir talimat öneki eklenerek eğitilir. bge-m3'e aynı 8 sorguyu `Represent this sentence for searching relevant passages: ` önekiyle verdik:

| Koşul | hit@1 | hit@3 | MRR | Doğru bandı (ort.) | En iyi yanlış | Ayrışma |
| --- | --- | --- | --- | --- | --- | --- |
| bge-m3, öneksiz | 8/8 | 8/8 | 1,000 | 0,570–0,717 (0,670) | 0,528 | +0,042 |
| bge-m3, önekli | 8/8 | 8/8 | 1,000 | 0,522–0,641 (0,586) | 0,480 | +0,042 |

**Sıralar birebir aynı, mutlak skorlar ~0,08 aşağı kaydı.** Eşiği modelin kalitesinin bir göstergesi sanan biri, burada boşuna eşiği indirir. Pratik sonuç: **eşik; modele, sorgu şablonuna ve normalize biçimine birlikte bağlıdır.** [Tekrarlanabilirlik sayfasındaki](/kullanim/tekrarlanabilirlik/) tohum bulgusunun arama tarafındaki karşılığı bu.

Aynı tabloda daha rahatsız edici bir şey var: bge-m3 8/8 buldu — sıralama kusursuz — ve yine de doğru parçanın en düşük kosinüsü (0,570) ile en iyi yanlış eşleşme (0,528) arasında yalnız 0,042 var. **Kusursuz sıralama, ayrılabilir bant demek değildir.** Eşiği 0,55'e kurarsanız doğru parçayı atarsınız, 0,50'ye kurarsanız yanlış parçayı alırsınız.

## Bağlam Tavanı: Daha Fazla Metin Her Zaman Daha Fazla Bilgi Değil

`max_seq_length` kesinti demektir. Kesinti hücresi bilerek sinsice kuruldu: kuyrukta **aranan bilgiyi taşıyan** bir cümle var (`Kreş kayıtları kontenjan doluysa yedek listeden ...`), önüne 160 token'lık dolgu kondu; birleşik parça 180 token.

| Tavan | Görünen token | Kuyruk cümlesinin soruyla kosinüsü | Uzun parçanın aday sırası |
| --- | --- | --- | --- |
| 128 | ~126 | **0,280** | **3 / 25** |
| 512 | ~180 | 0,234 | 9 / 25 |

Aynı parçanın iki tavanla üretilen vektörleri birbirine yalnız **0,882** benziyor. Tavanı yükseltmek kesintiyi kaldırır ama bu kümede **getirimi bozdu**: dolgu metin havuzlamayı seyreltiyor, kuyruktaki tek cümlenin sinyali ortalamaya karışıyor. Kesinti "bilginin kaybı" demek değildir; bazen gürültünün de içeri girmesidir. Çözüm tavanı büyütmek değil, parçayı doğru yere kesmek — [parçalama sayfası](/rag/parcalama-ve-hibrit-arama/).

## Kayıp Fonksiyonu: MultipleNegativesRankingLoss Neden Varsayılan?

Eğitimin çekirdeği `MultipleNegativesRankingLoss` (MNRL). Batch'te `anchor` ve `positive` sütunları verirsiniz; **negatifleri siz yazmazsınız** — aynı batch'teki diğer `positive`'ler o satırın negatifleri olur. Hedef, doğru çiftin skorunu batch'teki 15 yanlış çifte karşı softmax üzerinden öne çıkarmak; `scale=20.0` sıcaklık katsayısı bu yarışı ne kadar acımasız puanladığını belirler. İki sonuç:

- **Batch = negatif sayısı.** Kol D bu yüzden batch 8 ile 32'yi yarıştırıyor: daha büyük batch, sıfır etiket maliyetiyle daha çok negatif demek.
- **Negatifleri elle etiketlemek zorunda değilsiniz.** Elimizde yalnız 40 paraphrase çifti var; ayrı bir olumsuz listesi kurmak yerine batch'ten çıkarıyoruz. CPU'da eğitimin mümkün olmasının asıl sebebi bu.

Kullanılabilecek diğer kayıplar ve bu kafeste ölçülüp ölçülmedikleri:

| Kayıp | Ne ister | Ne zaman | Bu ölçümde |
| --- | --- | --- | --- |
| `MultipleNegativesRankingLoss` | anchor + positive çifti | Çift var, negatif yokken | **Çalıştırıldı (A/B/C/D)** |
| `CachedMultipleNegativesRankingLoss` | aynı, negatif havuzu önbellekte | Veri batch'e sığmıyorken | Ölçülmedi |
| `MatryoshkaLoss` | birkaç boyutta birden kayıp | Vektörü kısaltıp saklamak isterken | Ölçülmedi |
| `CoSENTLoss` | çift + göreli sıralama etiketi | "şu şu'dan daha iyi" diyebiliyorsanız | Ölçülmedi |
| `TripletLoss` | anchor/positive/negative üçgeni | Negatifleri elle seçtiniz | Ölçülmedi |

:::tip[Sütun sırası sözleşmedir, adı değil]
Kütüphanenin [eğitim genel bakış belgesi](https://sbert.net/docs/sentence_transformer/training_overview.html) açık söylüyor: veri setindeki **sütun adları önemli değildir, sıra önemlidir** — kaybın `forward` imzası birinci sütunu demir, ikincini olumlu, üçüncüyü olumsuz sayar. Biz yine de `anchor` / `positive` adlarını kullandık, çünkü `mine_hard_negatives(...)` bu adları **parametre olarak ister** (`anchor_column_name`, `positive_column_name`). Bu hatta kafa karışıklığının çoğu metinden değil, sütun sırasını kaydetmemekten çıkar.
:::

## Zor Negatif Madenciliği

Model kendi gövdesini tarayıp "en çok karıştırdığı" yanlış parçayı negatif olarak seçebilir; kütüphanenin kendi fonksiyonu var: `mine_hard_negatives(...)`. `zor-240` kolu bunu `num_negatives=1`, `sampling_strategy="top"` ile çağırıyor. Literatürün iddiası güçlü: iyi seçilmiş zor negatif, rastgele negatife göre belirgin iyileştirir. Tehlikeli tarafı da gerçek: **madenci modelin kendisi olduğu için**, modelin yanlış inandığı bir eşleşmeyi eğitim hedefi olarak yedirebilirsiniz. Bu kafeste `zor-240` kolunun ölçtüğü şey, tam olarak bu iddianın küçük bir kümede tutup tutmadığı.

## LoRA: Hangi Katmanlar Eğitilebilir?

[LLM ince ayarı sayfasında](/llm/lora-qlora/) kullanılan `q_proj` / `v_proj` hedef adları **LLM ailelerine** ait. MiniLM ise BERT ailesinden: dikkat hatları `...attention.self.query` / `.key` / `.value` olarak adlandırılıyor. Llama adlarıyla giderseniz eğitim başlamadan patlıyor:

```text
NoMatchingPeftModuleError: Target modules {'q_proj', 'v_proj'} not found
```

Doğrusu `target_modules=["query", "value"]`. Kol C bunu `r=16, lora_alpha=32, lora_dropout=0,05` ile kuruyor ve üç sayıyı birden yazıyor: eğitilebilir parametre oranı, adım süresi, diske yazılan adaptörün taban ağırlığa karşı boyutu.

## Eğitim Kolunu Okuma Bilgisi

Kol B aynı sabit test kümesi üzerinde altı kolu yarıştırıyor: 30/120/240 adım, 2e-5 ve 1e-4 öğrenme hızı, iki farklı tohum, bir zor negatif kolu. Her kol taban modeli **sıfırdan yeniden yükleyerek** başlıyor — bir önceki kolun ağırlıkları sızmaması için. Üç sayı birlikte okunur:

1. **Getiri:** hit@1 / hit@3 / MRR — kullanıcıya dokunan.
2. **Ayrışma:** doğru bandı ile en iyi yanlışın arasındaki boşluk — eşik koyabiliyor musunuz.
3. **Ezber:** eğitim çiftlerinin ortalama kosinüsünün eğitim sonrası artışı — model gerçekten *bir şey öğrendi mi*.

Üçü farklı şeylerdir ve aynı yöne gitmek zorunda değildir. Bu yüzden "kayıp düştü, demek ki iyileşti" çıkarımı yanlıştır: **kayıp fonksiyonu, eğitim çiftleri üzerindeki ayrıma bakar; test kümesindeki sıralamaya değil.** [Değerlendirme sayfasında](/rag/rag-degerlendirme/) kurulan "ayar değiştir → aynı sabit test kümesinde ölç" döngüsü burada da geçerli.

## Kol B Sonuçları: Altı Eğitim Koşumu, Tek Sonuç Satırı

Altı kol da aynı taban modelden başladı (her kol modeli sıfırdan yükledi), aynı 40 çift üzerinde MNRL ile eğitildi ve aynı 8 soru / 24 parça kümesinde ölçüldü. Maliyet tarafı:

| Kol | Veri | Adım | Öğrenme hızı | Tohum | Eğitim süresi | Adım başına | Ezber artışı |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cift-30` | çift | 30 | 2e-5 | 1234 | 42,94 sn | 1,43 sn | +0,182 |
| `cift-120` | çift | 120 | 2e-5 | 1234 | 169,45 sn | 1,41 sn | +0,273 |
| `cift-240` | çift | 240 | 2e-5 | 1234 | 319,70 sn | 1,33 sn | +0,295 |
| `zor-240` | zor negatif | 240 | 2e-5 | 1234 | 399,03 sn | 1,66 sn | +0,257 |
| `cift-240-lr4` | çift | 240 | 1e-4 | 1234 | 319,76 sn | 1,33 sn | +0,363 |
| `cift-240-t5678` | çift | 240 | 2e-5 | 5678 | 323,12 sn | 1,35 sn | +0,299 |

Sonuç tarafı — **hit@1 altı kolda da 7/8'de kaldı, hit@3 8/8'de kaldı:**

| Kol | MRR önce → sonra | Ayrışma önce → sonra | Doğru bandı ort. önce → sonra |
| --- | --- | --- | --- |
| `cift-30` | 0,938 → 0,938 | −0,236 → −0,241 | 0,609 → **0,641** |
| `cift-120` | 0,938 → 0,938 | −0,236 → −0,258 | 0,609 → **0,548** |
| `cift-240` | 0,938 → 0,938 | −0,236 → −0,236 | 0,609 → **0,515** |
| `zor-240` | 0,938 → 0,938 | −0,236 → **−0,305** | 0,609 → 0,571 |
| `cift-240-lr4` | 0,938 → **0,917** | −0,236 → **−0,328** | 0,609 → **0,468** |
| `cift-240-t5678` | 0,938 → 0,938 | −0,236 → **−0,173** | 0,609 → 0,553 |

Altı şey ölçüldü:

1. **Model öğrendi.** Eğitim çiftlerinin ortalama kosinüsü her kolda 0,503'ten 0,68-0,87 aralığına çıktı. MNRL işini yaptı.
2. **Getiri kıpırdamadı.** 8 soruluk sabit test kümesinde hit@1 altı kolda da 7/8 kaldı. Kayıp 1,16'dan 0,001'in altına inerken sıralama aynı.
3. **Bantlar aşağı kaydı.** 120 ve 240 adımda doğru parçaların ortalama skoru 0,609'dan 0,548'e ve 0,515'e düştü — model çiftleri ayırmayı öğrenirken **mutlak benzerlikleri** alçalttı. 30 adımda tam tersi oldu (0,641). Adım sayısı arttıkça bant aynı yöne gitmiyor.
4. **5 kat öğrenme hızı zarar verdi.** `lr=1e-4` kolunda MRR 0,917'ye indi (bir soru 1. sıradan 3. sıraya düştü), ayrışma −0,328'e açıldı, bant 0,468'e çöktü. Küçük model + küçük veri + yüksek öğrenme hızı = daha çok ezber (+0,363) ve daha kötü arama.
5. **Zor negatif madenciliği burada işe yaramadı.** Kayıp eğrisi `cift-240`'ta 240. adımda 0,000 iken `zor-240`'ta hâlâ 0,276'da dalgalanıyordu — madencinin seçtiği negatif kaybı gerçekten zorlaştırdı. Ama ayrışma −0,236'dan −0,305'e **kötüleşti**, hit@1 değişmedi.
6. **Tohum burada fark yaratmadı.** 1234 ile 5678: hit@1 aynı, MRR aynı, adım süresi 1,33 vs 1,35 sn. Ama rütbeler kaydı: eğitim öncesinde 7. soru 2. sıradayken, çift verisiyle eğitilen beş kolda 6. soru 2. sıraya indi; `cift-240-lr4` kolunda ise 7. soru 3. sıraya düştü ve MRR'ı bozan bu oldu. Yani "7/8" aynı sayı, **farklı 7/8**.

Sebep 5. maddede logda duruyor — madencinin seçtiği üçgen:

```text
anchor:   Randevular MHRS üzerinden alınıyor.
positive: Aile Sağlığı Merkezi randevuları MHRS'den yapılıyor.
negative: Zabıta tutanağının numarası sonraki başvurularda isteniyor.
```

MHRS cümlesinin "en zorlayıcı yanlış eşi" olarak zabıta tutanağı seçilmiş. 40 pozitiflik bir havuzda, zayıf bir modelin "en çok benzeyen ama pozitif olmayan"ı bulması **anlamlı bir zorluk üretmiyor**; eğitime yalnız gürültü ekliyor. Zor negatif, gerçek bir gövdeyle (binlerce parça) ve güçlü bir taban modelle başka bir şeydir — burada ölçülen, küçük kümedeki hâli.

:::danger[Küçük veride uzun eğitim getiri getirmez]
40 çiftlik bir veriyle, batch 16'da 240 adım (120 epoch; `dataloader_drop_last` ile bir epoch iki adımdır) koşmak, yine batch 16'da 30 adım koşmaktan daha iyi sonuç vermedi; yalnızca ezberleme arttı ve bant aşağı kaydı. Bu, "MNRL kötüdür" demek değil — **veriniz bu kadar küçükken, adım sayısını artırmadan önce parçalama/eşik/mesafe seçeneklerine dönün** demek. Aşağıdaki Kol D bölümü kafesteki tek istisnayı gösteriyor: aynı 240 adım batch **8** ile koşulunca sıralama 8/8'e çıktı. Ama o karşılaştırmada satır başına negatif sayısı da, görülen epoch sayısı da birlikte değiştiği için "kazanç şundan geldi" diye tek bir sebep yazılamaz. Aynı mesajı [parçalama sayfası](/rag/parcalama-ve-hibrit-arama/) farklı bir eksende veriyordu: en iyi ayar, başkasının sayısıyla seçilmez.
:::

Peki eğitim maliyeti pratikte ne? `cift-240` kolu 5,3 dakika sürdü; altı kolun tamamı 27,1 dakika (kayıtta 1628 sn). Adım başına süre 1,33-1,66 sn arasındaydı ve batch 16 sabit kaldığı için veri boyutuyla değişmedi: adım süresini **batch büyüklüğü ve modelin boyutu** belirler. Küçük korpusta asıl ucuz olan şey ise yeniden indeksleme: her kolun ardından 24 parçayı tekrar gömmek 0,33-0,40 sn.

## Kol C: LoRA Ne Kadar Ucuzlar, Ne Kadar Öğrenir?

Aynı taban model, aynı 40 çift, aynı 240 adım; bu sefer ağırlıkların tamamı değil, dikkat hatlarına eklenen iki düşük rütbeli matris eğitiliyor (`r=16`, `alpha=32`, `dropout=0,05`, `lr=1e-4`). Ölçülenler:

| Ölçüm | Değer |
| --- | --- |
| Tüm ağırlıklar | 117.653.760 parametre |
| Eğitilebilir parametre | 294.912 (**0,251%**) — hedef `["query", "value"]`, eşleşen modül 24 |
| Adım süresi | 0,54 sn (tam ince ayar: 1,33 sn) → **2,5 kat hızlı** |
| 240 adım toplam | 130,67 sn (tam ince ayar: 319,70 sn) |
| Süreç belleği | 1426 MB |
| Diske yazılan adaptör | **17,4 MB** |
| İndirilen taban ağırlık | 457,5 MB (adaptör/taban = %3,8) |

Davranış tarafı ise karışık:

| | hit@1 | hit@3 | MRR | Doğru bandı (ort.) | Ayrışma |
| --- | --- | --- | --- | --- | --- |
| lora ÖNCE | 7/8 | 8/8 | 0,938 | 0,305–0,718 (0,609) | −0,236 |
| lora SONRA | 7/8 | 8/8 | 0,938 | 0,308–0,777 (0,632) | −0,253 |

Üç okuma:

- **Hız ve disk gerçek.** 2,5 kat daha kısa süre, %0,25 eğitilebilir parametre ve 457,5 MB yerine 17,4 MB'lık çıktı. Başka bir makineye taşınacak şey bu kadar küçük.
- **Kayıp eğrisi tam ince ayar gibi davranmadı.** `cift-240` 0,000'e inerken LoRA kolu 0,182'de dolaştı ve ilk 30 adımda kayıp **yükseldi** (1,235 → 1,476). Kapasite küçük olduğu için model çiftleri aynı kesinlikle ayıramıyor; gürültü daha yüksek görünüyor.
- **Yine de testte bir şey değişmedi.** hit@1 ve MRR aynı, bant ortalaması hafif yükseldi (0,609 → 0,632), ayrışma hafif açıldı (−0,236 → −0,253). Aynı `lr=1e-4` ile **tam** ince ayar yapmak MRR'ı 0,917'ye düşürmüştü — LoRA'nın kısıtlı kapasitesi burada hatayı yumuşattı.

:::tip[Adaptörü mü, tüm modeli mi kaydet?]
Dağıtım için adaptör (17,4 MB) açık ara ucuz; ama adaptörü yüklemek taban modelin **aynı revizyonunu** gerektirir. Taban model güncellenirse adaptörün davranışı ölçülmemiş bir şey olur. [Model kartı sayfasındaki](/kullanim/lisans-ve-model-karti/) "temel modelin adı **ve revizyonu**" kuralı burada da geçerli. Bir de pratik fark var: merge edilmiş (birleştirilmiş) tam model daha basit bir yükleme yoludur, 457 MB disk ve tek dosya seti demektir.
:::

## Batch Tavanı: Satır Başına Kaç Negatif?

Yukarıdaki kayıp fonksiyonu bölümü, batch boyutunun sıradan bir hız ayarı değil **hiperparametrenin kendisi** olduğunu söylemişti: MNRL'de bir satır, aynı batch'teki diğer bütün olumlulara karşı yarışır. Batch 8 demek satır başına 7 negatif, batch 32 demek 31 negatif demek. Kafesteki tek batch denemesi bu bölüm: iki kol de aynı 40 çift, aynı `lr=2e-5`, aynı tohum 1234 ve **aynı 240 optimizer adımı** ile koştu.

Maliyet tarafı:

| Batch | Satır başına negatif | 240 adım süresi | Adım başına | Sıra başına | Kayıp: ilk → son okuma |
| --- | --- | --- | --- | --- | --- |
| 8 | 7 | 255,22 sn | 1,06 sn | 133 ms | 0,883 → 0,0026 |
| 32 | 31 | 446,97 sn | 1,86 sn | 58 ms | 1,701 → 0,0001 |

Sonuç tarafı — kafesteki dokuz eğitim koşumunun **tek getiri hareketi** burada:

| Batch | hit@1 önce → sonra | MRR önce → sonra | Ayrışma önce → sonra | Doğru bandı ort. önce → sonra |
| --- | --- | --- | --- | --- |
| 8 | 7/8 → **8/8** | 0,938 → **1,000** | −0,236 → −0,206 | 0,609 → 0,573 |
| 32 | 7/8 → 7/8 | 0,938 → 0,938 | −0,236 → **−0,200** | 0,609 → **0,509** |

Dört okuma:

1. **Küçük batch kazandı, ve literatürün tersi.** Batch 8 kolu 7/8'i 8/8'e taşıdı: `[1, 1, 1, 1, 1, 1, 2, 1]` rütbeleri `[1, 1, 1, 1, 1, 1, 1, 1]` oldu — yani tek başarısız sorgu 2. sıradan 1. sıraya çıktı. Batch 32 kolunda rütbe toplamı değişmedi, ama **başarısız sorgu yer değiştirdi**: 7. sıradaki sorgu düzelip 6. sıradaki bozuldu. Kol B'deki tohum kolu da aynısını yapmıştı — sıfır net değişim, iki rütbe hareketi.
2. **Adım sayısı sabitken batch'i büyütmek tur sayısını büyütür.** 40 çift ve `dataloader_drop_last=True`: batch 8'de bir epoch beş adımdır (40 ÷ 8), yani 240 adım **48 epoch** eder; batch 32'de bir epoch tek adımdır (40 ÷ 32'nin tam kısmı 1, kalan 8 çift düşer), yani 240 adım **240 epoch** eder. Yani batch 32 kolu her çifti kabaca dört kez daha fazla görerek çalıştı ve yine de sıralamada bir şey kazanamadı. Batch tavanı ile tur sayısı bu kurulumda birbirine bağlıdır; **tek değişken olarak batch büyütüldü denilemez.**
3. **Kayıp daha da düştü, iyileşme gelmedi.** Batch 32'nin son kayıp okuması 0,0001, batch 8'inki 0,0026 — yani sıralamada hiçbir şey kazanamayan kolun kaybı yaklaşık yirmi kat daha derine indi. Daha derin kayıp, daha iyi sıralama demek değil — Kol B bölümünde kurulan ayrımın en temiz örneği bu: **kayıp, eğitim çiftleri üzerindeki ayrıma bakar; test sıralamasına değil.**
4. **En iyi ikinci ayrışma, sıfır getiri.** Batch 32'nin son ayrışması (−0,200) dokuz koşumun en iyi ikinci değeri; yalnızca tohum kolu `cift-240-t5678` (−0,173) daha iyi. Ama bu kolun doğru bandı 0,10 aşağı kaydı (0,609 → 0,509, en düşük doğru kosinüs 0,249) ve bandın tepesi 0,661'de kaldı. Eski eşik yeni modele taşınırsa doğru parçalar atılmaya başlar — **ayrışma düzelmesi, eski eşiğin hâlâ geçerli olduğu anlamına gelmez.**

Zamanlama tarafı da tek başına karar verdirmez: batch 32, dört kat çok satırı 1,75 kat daha uzun sürede işledi (sıra başına 133 ms → 58 ms). Yani **daha büyük batch gerçekten daha verimli** — birim iş başına. Yalnız aynı 240 adımda bu, daha çok epoch'a sahip olmak demek olduğu için sonuç değişiyor; verimlilik ile kalite aynı tuşta değil.

:::caution[İki koşum, bir sayı]
Bu bölüm iki rakam üzerine yazıldı; her biri tek tekrar. Rütbe hareketlerinin (hangi sorgunun düştüğü) tohumla değiştiği Kol B'de ölçüldü, batch tavanında ölçülmedi. Yani "batch 8 daha iyidir" genellemesi **bu kafeste desteklenmiyor** — desteklenen tek cümle, 40 çiftli bu kümede 240 adımda batch 8'in sıralamayı kıpırdatıp batch 32'nin kıpırdatmadığı.
:::

## Eğitimden Sonra Ne Kaydedilir?

Yeni vektörler eski vektörlerle **aynı uzayda değil.** Modeli eğittiğiniz an, dün indekslediğiniz her parça geçersiz hale gelir. Kaydedilecek üç şey var:

1. **Modelin kendisi veya adaptörü.** Tam ağırlık mı, LoRA adaptörü mü — ikisi farklı depolama, farklı yükleme yolu ister. Kol C'nin ölçtüğü tam olarak bu ayrım.
2. **Yeniden indekslenmiş gövde.** Bunu otomatikleştirmezseniz, bir kısmı eski modelle üretilmiş bir indeksle arama yaparsınız; skorlar karşılaştırılamaz hâle gelir. [Örnek 6](/ornekler/viki-rag/) vektör indeksini korpus imzasına (parça kimlikleri + uzunlukları) bağladı; model değişince imzanın bir **model kimliği** de içermesi gerekir.
3. **Yeniden kalibre edilmiş eşik.** Ayrışma ve bantlar her kolda değişti (aşağıdaki tablolar). Eski eşik yeni modelde rastgele bir sayıdır.

:::caution[Ezber, başarı değildir]
Eğitim çiftlerinin ortalama kosinüsü her kolda arttı — model çiftleri ayırmayı **öğrendi.** Aynı kolun test sıralaması yerinde sayabilir. Kayıp eğrisinin düşmesi ve kosinüsün artması, iyileşmenin değil **öğrenmenin** kanıtıdır. [Öz-denetim sayfasında](/kullanim/lisans-ve-model-karti/) anlatılan "rapor ettiğiniz şeyle ölçtüğünüz şey aynı mı" sorusu burada da sorulur.
:::

## Karar Listesi

- **Önce eşik, sonra model.** [Örnek 6'nın ölçüm betiği](/ornekler/viki-rag/) gibi kendi sabit test kümenizde doğru/en iyi yanlış bandınızı çıkarın. Bantlar ayrışmıyorsa eğitim muhtemelen gereksiz, parçalama ve eşik daha ucuz.
- **Eğitime girmeden önce taban modelin dil desteğini doğrulayın.** Küçük çok dilli modeller Türkçede "çalışır" ama eşikleri İngilizce modellere benzemez; bu sayfada MiniLM ile bge-m3 arasındaki 8 soruluk fark ölçüldü — genelleme değil, tek korpus gözlemi.
- **Veri şekli kaybı belirler.** Elinizde yalnız "(soru, doğru parça)" çiftleri varsa `MultipleNegativesRankingLoss` başlar; "(a, b, c)" üçgenleri veya göreli sıralama etiketleri varsa sırasıyla triplet/CoSENT.
- **Kendi kendine yeten boru hattı ucuzdur.** Batch'ten çıkan negatifler ekstra etiket gerektirmez; bu, CPU'da eğitimin mümkün olmasının asıl sebebidir.
- **Batch boyutunu ayar sanmayın, hiperparametre sayın.** Aynı 240 adımda batch 8 sıralamayı 8/8'e taşıdı, batch 32 yerinde saydı — ama adım sayısı sabitken batch'i büyütmek epoch sayısını da dört katına çıkarıyor. İkisini birlikte değiştirip tek bir sayıya bakmak, hangi değişkenin kazandırdığını göstermez.
- **Zor negatif madenciliğini küçük kümede test edin.** Kol B bunu 40 çift üzerinde ölçüyor ve sonucu sayılarla yazıyor.
- **BERT ailesinde LoRA hedeflerini modelin modül adlarından bulun.** `q_proj` diye ısrar ederseniz hata alırsınız.
- **Yeniden indeks maliyetini hesaba katın.** Model her değiştiğinde tüm gövdeyi yeniden gömersiniz; bu kafeste saniyenin altında sürdü, büyük gövdelerde eğitimden pahalı **olabilir** (ölçülmedi).
- **Eşiği her model ve sorgu şablonu için tekrar kurun.** Önek eklemek sıralamayı bozmadı ama bantları 0,08 aşağı taşıdı.
- **GPU'lu bir makinede eğitiyorsanız, bu sayfadaki süreler size rehber olmasın.** Hepsi CPU'da ölçüldü.

## Kaynaklar ve İleri Okuma

- [Reimers & Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" (2019)](https://arxiv.org/abs/1908.10084) — çift/Siyam yapısıyla gömme eğitiminin orijinali; bu sayfadaki MNRL onun pratik torunudur.
- [Gao, Yao & Chen, "SimCSE: Simple Contrastive Learning of Sentence Embeddings" (2021)](https://arxiv.org/abs/2104.08821) — tekniğin "batch içindeki diğer örnekler negatiftir" damarı; dropout'u ucuz bir negatif üreticisi olarak kullanır.
- [Wang ve ark., "Text Embeddings by Weakly-Supervised Contrastive Pre-training" (E5, 2022)](https://arxiv.org/abs/2212.03533) — milyonlarca otomatik çiftle eğitilen gömme modelinin tarifi; neden "hazır model yeterli olabilir" sorusunu doğurur.
- [Li ve ark., "Towards General Text Embeddings with Multi-stage Contrastive Learning" (GTE, 2023)](https://arxiv.org/abs/2308.03281) — çok aşamalı eğitimin (genel → sıralama → damıtma) endüstriyel örneği.
- [Chen ve ark., "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation" (2024)](https://arxiv.org/abs/2402.03216) — bu sayfada kıyaslama için kullanılan bge-m3'ün makalesi; çok dillilik ve 8192 token çoklu-tanelilik iddiaları burada.
- [Kusupati ve ark., "Matryoshka Representation Learning" (2022)](https://arxiv.org/abs/2205.13147) — tek vektörün ilk `d` boyutunu kullanarak indeksi küçültmenin yöntemi; `MatryoshkaLoss` buradan gelir.
- [Muennighoff ve ark., "MTEB: Massive Text Embedding Benchmark" (2022)](https://arxiv.org/abs/2210.07316) — 8 görev türü, 58 veri seti, 112 dil; kendi bulgusu: **hiçbir yöntem tüm görevlerde üstün değil.** Sıralama listelerine bu gözle bakın.
- [Thakur ve ark., "BEIR: A Heterogeneous Benchmark for Zero-shot IR" (2021)](https://arxiv.org/abs/2104.08663) — dağıtım dışı veride BM25'in hâlâ güçlü taban çizgi olması; "eğitim şart" demeden önce denenecek bedava alternatif.
- [sentence-transformers eğitim genel bakışı](https://sbert.net/docs/sentence_transformer/training_overview.html) — kayıp/veri seti/öğretici (trainer) üçlüsü ve sütun sırası sözleşmesi.
- [paraphrase-multilingual-MiniLM-L12-v2 model kartı](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) — 384 boyut, 128 tavan, apache-2.0.
- [BAAI/bge-m3 model kartı](https://huggingface.co/BAAI/bge-m3) — 1024 boyut, 8192 tavan, MIT lisansı.
- [Bu rehberin RAG değerlendirme sayfası](/rag/rag-degerlendirme/) — hit@k, MRR ve eşik ölçümünün nasıl kurulacağı; bu sayfadaki sayılar o dili kullanır.
- [Parçalama ve hibrit arama](/rag/parcalama-ve-hibrit-arama/) — bağlam tavanı bulgusunun diğer yarısı: kesinti yerine doğru yere kesmek.
- [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) — tohum varyansının çıkarım tarafındaki ölçümü; Kol B'nin tohum kolu onun eğitim tarafı.
- [Lisans, kişisel veri ve model kartı](/kullanim/lisans-ve-model-karti/) — eğittiğiniz modeli yayınlarken yazılması gerekenler; burada indirilen ağırlıkların lisansı da orada ölçüldü.
