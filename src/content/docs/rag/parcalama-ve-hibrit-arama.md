---
title: "Parçalama ve Hibrit Arama: Getirimi İyileştirmenin İki Kolu"
description: "RAG'de getirimi belirleyen iki ayar — parça boyutu ve sınırları, ile sözlük ve vektör aramasının birleştirilmesi. BM25 ve RRF'nin nasıl çalıştığı, Türkçede sözcüğe bölme tuzakları ve bu rehberin korpusunda ölçülen sonuçlar."
dogrulama: 2026-11-19
---

[RAG karar sayfası](/rag/rag-mi-ince-ayar-mi/) boru hattının ne zaman gerekli olduğunu, [değerlendirme sayfası](/rag/rag-degerlendirme/) ise getirimin nasıl ölçüleceğini anlattı. Ölçüm size "arama şaşırdı" diyorsa iki kola bakarsınız: **neyi indekslediğinize** (parçalama) ve **nasıl aradığınıza** (arama yöntemi). Bu sayfa ikisini de ele alıyor; sonundaki deney, üç yöntemi aynı 125 parçalık Türkçe korpusta gerçekten yarıştırdı.

## Parçalama Neden Model Seçimi Kadar Önemli?

Gömme modeli bir metne tek bir vektör verir. Bir parçanın içine üç farklı konu koyarsanız, o vektör üç konunun **ortalamasına** çekilir ve hiçbirinin sorusuyla tam uyuşmaz. Parçalama, "bir vektör kaç konu taşısın?" sorusunun cevabıdır; bu yüzden embedding modeli değiştirmek kadar sonuç etkiler.

Üç ayrı baskı aynı anda işin içine girer:

- **Arama tarafı:** bilgi iki parçaya bölünmüşse hiçbir parça tek başına yeterli değildir; ölçümde "doğru parça geldi ama cevap yanlış" görünür. Suç production'a benzer, aslında aramadadır.
- **Bağlam penceresi:** parça sayısı × parça boyutu, üretim modelinin `num_ctx` sınırını doldurur. [Kayıp-ortada](https://arxiv.org/abs/2307.03172) bulgusu tam burada devreye girer: uzun bağlamın ortasındaki bilgi daha az kullanılır — yani "daha çok parça" bedava değildir.
- **Kullanıcı sabrı:** her parça prompt'a girdiği için CPU'da üretimi geciktirir (Örnek 6'da dört parçayla cevap 52-66 sn sürüyor).

## Parçalama Taksonomisi

| Yöntem | Nereye keser | Ne zaman iyi | Bedeli |
| --- | --- | --- | --- |
| **Sabit boy** (karakter veya token penceresi) | Sayıya gelince | Hızlı başlangıç, düzensiz metin | Cümle ortasından keser; anlam bölünür |
| **Özyinelemeli** (paragraf → cümle → kelime önceliğiyle) | Yapı sınırlarına, sığmıyorsa aşağı inerek | En yaygın genel amaç; web/PDF metni | Ayar çok (hedef boy, ayraç listesi) |
| **Yapısal / bölüm tabanlı** | Markdown başlığı, HTML etiketi, PDF sayfası, kod fonksiyonu | Belgede zaten mantıksal bölüm varken | Bölümler eşit büyüklükte değildir |
| **Semantik** | Ardışık cümle vektörleri arası benzerlik düşünce | Konu kayması belirgin uzun metinde | Her cümleyi gömmek = indeks pahalı |
| **İstatistiksel kümeleme** | Küme sınırlarına | Dağınık/not karışık metinde | Sonuç tekrarlanabilir ama açıklaması zor |
| **Geç parçalama** (late chunking) | Parçalamayı gömmeden *sonra* yapar | Parçanın bağlamını korumak istiyorsanız | Modelin uzun girdi sınırı belirleyici |
| **Ebeveyn-çocuk** (small-to-big) | Çocuk parçayı arar, ebeveyni verir | Arama hassas, üretim geniş bağlam isterken | İki indeks/iki temsil gerekir |

Geç parçalama [Günther ve ark. 2024](https://arxiv.org/abs/2409.04701) tarafından tanımlandı: tüm belge modele sokulur, token düzeyindeki vektörler parçaya göre havuzlanır; böylece her parça vektörü çevresindeki bağlamı da taşır. Bu rehberin örneklerinde kullanmadık — tüm belgeyi tek seferde gömmek [bge-m3](https://huggingface.co/BAAI/bge-m3) için bile 8192 token ile sınırlı.

Tavanı büyütmenin bedeli sanıldığı kadar tek yönlü değil: [Gömme Modeli Eğitmek](/rag/gomme-egitimi/) sayfasındaki kesinti deneyinde, aranan cümleyi kuyruğa koyduğumuz bir parça 128 token tavanında **3. sırada** gelirken 512 token tavanında **9. sıraya** düştü — öndeki dolgu metin havuzlamayı seyreltti. "Kesilmesin" diye parçayı uzatmak, getirimi iyileştirmeyebilir.

### Araştırma ne diyor, ne demiyor

Chroma'nın 2024 parçalama değerlendirmesi ([Evaluating chunking strategies for retrieval](https://www.trychroma.com/research/evaluating-chunking)) beş ayrı korpusta farklı bölmeler arasında **geri çağırmada 9 puana varan** fark buldu; 200 token civarı özyinelemeli bölme, örtüşmesiz hâliyle güçlü çıktı; küme-temelli semantik bölmeyse en yüksek hassasiyeti (IoU) verdi. İki uyarı:

1. Çalışma **yalnızca aramayı** ölçtü, üretimi ölçmedi. Parça "doğru" ama okunması kötü olabilir.
2. Yazarların kendi bölmeleriyle karşılaştırma yapıldı; yani "en iyi ayar" korpusa ve gömme modeline bağlı kaldı. Bu sayfanın aşağıdaki deneyi de aynı dersi **kendi korpusunda** sayıyla gösteriyor: **ayar başkasının sayısıyla seçilmez.**

Örtüşme (overlap) konusunda sık verilen "son %10-20'yi tekrar ekle" tavsiyesi iki yüzlüdür: komşu parçanın başını eklemek bilgi kopukluğunu azaltır, ama aynı cümlenin iki vektörde durması getiride **tekrar** üretir — Chroma ölçümünde örtüşme arttıkça IoU düştü. Örnek 6'da örtüşmeyi tek paragrafla sınırlı tuttuk.

### Üç tavanın kesişimi

Parça boyutu tek bir sayıdan değil, üç sınırın kesişiminden çıkar:

- **Gömme modeli:** bge-m3'ün azami girdisi 8192 token (model kartı, son doğrulama 2026-10). Bu, parçanın *sığması* gereken yer; pratikte çok daha küçük tutulur çünkü uzun parçanın vektörü sulanır.
- **Üretim modeli:** Ollama'nın `num_ctx` varsayılanı VRAM'e göre katmanlı (24 GiB altı 4096 token — [belge](/kullanim/ollama/)). k parça × boyut + talimat bu sınırı aşarsa parçalar sessizce kırpılır.
- **Belgenizin kendi yapısı:** ortalama paragraf uzunluğu, hedef boyunuz için doğal tavan.

Örnek 6'nın ölçülmüş hâli (2026-10-15, `ornekler/viki-rag/` içindeki yoklama betiği):

- 8 Vikipedi maddesi 88.861 karakter → **125 parça**; parça metinlerinin toplamı **143.138 karakter**, yani örtüşme ve birleştirme korpusu okunan metnin **1,61 katı** bir indekse çeviriyor.
- Parça başına uzunluk: ortalama **1.145**, en kısa **245**, en uzun **3.274** karakter. `HEDEF_PARCA = 800` bir **tetik**, tavan değil: paragraf hedefi aşınca kesilir, bu yüzden 125 parçanın **91'i** 900 karakterin üstünde.
- Token karşılığı: 1.776 karakterlik bir parça qwen2.5 tokenizer'ında **659 token** (~2,7 karakter/token). Sistem talimatı + soru tabanı **145 token**; ilk dört parça birlikte **2.309 token**. Toplam ≈ 2.454 — 4.096'lık varsayılan pencerenin yaklaşık %60'ı.
- Ama en uzun parça (3.274 karakter ≈ 1.200 token) üst üste dört kez gelirse pencere aşılır ve bağlam **sessizce kırpılır**. `num_ctx`'yi büyütmek ya da parça başına karakter tavanı koymak gerekir; hangisini seçeceğiniz ölçüme bağlı.

Bu sayılar kopyalanacak bir ayar değil, kendi korpusunuz için hesabın **nasıl** yapıldığının örneğidir.

### Türkçede parçalamanın özel tuzakları

- **Nokta kısaltmayı bitirir.** "vb.", "Dr.", "Örn.", "1. Madde" cümle bölen araçları yanıltır; "1." gibi madde numaraları satır başındaysa bölümleme bozulur.
- **Ekler kelimeyi değiştirir.** "Marmaray", "Marmaray'da", "Marmaray'ın" üç ayrı sözcüktür. Parçalama bunu etkilemez ama aşağıdaki sözlük aramasını doğrudan etkiler.
- **Uzun cümleler.** Akademik/kurumsal Türkçe metinlerde virgüllerle uzayan cümleler hedef boyu tek başına aşabilir; "sığmıyorsa cümleyi böl" kuralı (özyinelemeli yöntem) şarttır.
- **Başlık satırları bilgi taşımaz.** Vikipedi'nin `== Başlık ==` satırları kısa ama gömme için verimsizdir; Örnek 6 bilerek attı. Başlık metnini parçanın *başına* yazmak (başlık hiyerarşisini taşımak) ise semantik aramada genelde yardımcı olur.

## Sözlük Araması (BM25) Nedir?

Vektör araması "anlama" benzerliğine bakar; BM25 ise **kelimenin belgede gerçekten geçmesine**. Üç bileşenle puan verir:

```text
score(q, d) = Σ terim  IDF(terim) ·  (tf · (k1 + 1)) / (tf + k1 · (1 − b + b · |d| / ortalama|d|))
```

- **tf doyumu (k1):** terim 5 kez geçiyorsa 50 kez geçmesinden pek fark etmez — artış doyar. `k1` bu doyurma eğrisinin şeklini ayarlar.
- **Boyut normalizasyonu (b):** uzun parça terimi daha çok *içerme* ihtimali taşır; `b` bu cezanın şiddetidir. `b=0` boyutu hiç umursamaz, `b=1` tam orantılı cezalar.
- **IDF:** seyrek terim (ürün kodu, özel ad) sık terimden ("hat", "istasyon") daha çok puan getirir.

Apache Lucene'in `BM25Similarity` sınıfı varsayılan olarak **k1 = 1,2 ve b = 0,75** kullanır ([belge](https://lucene.apache.org/core/9_10_0/core/org/apache/lucene/search/similarities/BM25Similarity.html), son doğrulama 2026-10); ayrıca negatif olmayan bir IDF sürümü vardır. Elasticsearch, OpenSearch ve Solr bu hattın etrafında kuruludur; kuramsal özeti [Robertson & Zaragoza 2009](https://www.nowpublishers.com/article/Details/IPR-017) makalesinden okuyabilirsiniz.

### Hangi soruda hangisi kazanır

| Sorgu türü | Örnek | Vektör | BM25 |
| --- | --- | --- | --- |
| Kelime örtüşmesi yok, anlam var | "paket geri gönderme süresi" → "iade koşulları" | güçlü | zayıf |
| Nadir/kesin terim | `M11`, `P0042`, `TÜVASAŞ`, `2026/14` | bulanık | güçlü |
| Sayı, tarih, kod | "1869 yılında kurulan kurum" | zayıf (sayılar gömmede ayrışmaz) | güçlü |
| Yazım hatası, kısaltma varyantı | "Marmaray", "İst." | bazen kurtarır | kaçırır |
| Çok dilli / kod karışık | Türkçe soru, İngilizce doküman | güçlü (çok dilli modelde) | kaçırır |
| Uzun ve dağınık doküman | 40 sayfalık yönetmelik | güçlü | zayıf |

Bu tablonun **Türkçe için ağır bir yanı** var: ek dili olduğu için kullanıcının yazdığı sözcük, belgedeki sözcükten farklı olabilir ("seferleri" ↔ "sefer"). Sözlük araması bu yüzden Türkçede, İngilizceye göre sistematik olarak daha sık kaçırır; ya gövdeye indirme (stemming/zemberek gibi araçlar) ya da hibrit birleştirme gerekir.

:::note[Tablo beklenti, aşağıdaki ölçüm kanıt]
Aşağıdaki deney bu tabloyu test etti ve **hepsini doğrulamadı**. Leksik kümede vektör ile BM25 hit@1'de başa baş çıktı (3/6 ve 3/6): `M11` ve "İETT hangi yıl kuruldu?" sorularında vektör 1. sırayı alırken (tablonun 2-3. satırlarının beklediğinin tersi), `batırma`, `Ayrılık Çeşmesi` ve `vapur` sorularında BM25 öne çıktı. Yani bu satır direction, kural değil — kendi korpustaki belirteçlerin **başka maddelerde de geçip geçmediği** sonucu çeviriyor (ör. `M11` iki maddede, `batırma` tek maddede geçiyor; ölçüm bunu gösterdi).
:::

## Birleştirme: RRF Neden Puanları Değil, Sıralamayı Kullanır

Vektör benzerliği 0-1 arasında, BM25 puanı ise sınırsız ve korpusa bağlıdır. İkisini ağırlıklı toplamda birleştirmek için önce normalizasyon gerekir (Weaviate'in `relativeScoreFusion` modu bunu yapar); oysa **reciprocal rank fusion** puana bakmaz, sadece sırayı kullanır:

```text
RRF(d) = Σ_listeler  1 / (k + sıra(d, liste))
```

İki listede de üstlerde çıkan belge kazanır. Korelasyon sabiti `k` için standart değer **60**: hem [Cormack, Clarke & Büttcher 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) hem de Elasticsearch'in `rank_constant` varsayılanı 60'tır. Küçük `k` ilk sıraları çok cezalandırır, büyük `k` listeleri eşitler.

Uygulamalarda gördüğünüz adlar aynı fikrin etrafındadır:

| Sistem | Birleştirme adı | Varsayılan |
| --- | --- | --- |
| Elasticsearch | `rrf` retriever | `rank_constant` 60, aday penceresi `rank_window_size` |
| Weaviate | `hybrid` sorgu | `alpha`: 0 = anahtar kelime, 1 = vektör; `rankedFusion`, v1.24+ `relativeScoreFusion` |
| Qdrant | `Query::Hybrid` (dense + sparse) | `fusion` seçenekleri RRF ve DBRF |
| OpenSearch | `hybrid` sorgu + arama hattında `normalization-processor` | normalizasyon: `min_max`, `l2`, `z_score`; birleştirme ağırlıklı |

:::note[Hibrit, "iki aramayı topla" demek değildir]
Sıraları birleştirmek, tek bir eşik koymayı **zorlaştırır**: BM25 puanının mutlak anlamı olmadığı için "0,35 altı = alakasız" tipi bir kontrol hibrit listede çalışmaz. Eşik, vektör benzerliğinde kalmalı; birleştirme sadece sıralamayı düzeltmelidir. Bu sayfanın deneyinde kapsam dışı sorular için ölçtüğümüz davranış bunu gösteriyor.
:::

### Üçüncü kademe: yeniden sıralama (rerank)

Aday havuzunu (ör. 50 parça) geniş tutup sonra küçük bir **cross-encoder** ile yeniden sıralamak, tek aşamalı aramanın ulaşamadığı hassasiyeti verir: cross-encoder soru-parça *çiftini* birlikte okur, ayrı vektörleri karşılaştırmaz. Çok dilli ve yerelde çalıştırılabilir örnek [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) (0,6B). İki uyarı: model kartı çok dilliliği desteklerle belgeler, Türkçe o listede **adı geçen diller arasında değil** — kendi test setinizle ölçmeden güvenmeyin; ve her aday bir ileri geçiş demek olduğu için CPU'da gecikmeyi belirgin artırır.

Benzer bir "üçüncü kademe" de parçanın kendisini zenginleştirmek: Anthropic'ın [contextual retrieval](https://www.anthropic.com/news/contextual-retrieval) yaklaşımı her parçanın başına, parçanın belge içindeki yerini anlatan model üretimi iki cümle ekler. Yayımladıkları sayılar **tedarikçiye ait** (BM25 ile başarısızlık oranında %49, yeniden sıralama ile %67 düşüş) — kendi korpusunuzda doğrulamanız gerekir; ayrıca indeksleme sırasında her parça için bir üretim çağrısı demek, yani para ve süre.

## Deneyin Tasarımı

:::note[Bu bölümün sayıları]
`ornekler/viki-rag/hibrit.py` Örnek 6'nın korpusunu indirir, parçaları hem gömer (bge-m3) hem de saf Python'la BM25 indeksine çevirir; sonra üç yöntemi aynı sorularda, madde başlığına göre sıralar. Betik **bu makinede iki kez çalıştırıldı**, tek fark Ollama adresiydi:

| Koşum | Adres | 125 parçanın vektörleştirilmesi | Tam günlük |
| --- | --- | --- | --- |
| 2026-10-15 | `http://localhost:11434` | **529,3 sn** (toplam 607 sn) | `cikti/hibrit-kaydi.txt` |
| 2026-10-16 | `http://127.0.0.1:11434` | **253,0 sn** | `cikti/hibrit-kaydi-127.txt` |

İki günlüğün **sıralama tabloları satır satır aynı** (rütbeler ve hit@k satırları birebir); değişen tek şey gecikme. Aşağıdaki sayılar 2026-10-16 koşumundan.
:::

Betik üç şeyi sabit tutar ki karşılaştırma anlamlı olsun: aynı 125 parça, aynı sorular, aynı "doğru" tanımı (beklenen madde başlığı). Değişen tek şey sıralama fonksiyonu.

- **Ölçülen rütbe:** beklenen maddenin *ilk* parçasının kaçıncı sırada geldiği. hit@1 ve hit@4 raporlanır; k=4, bağlama gerçek dört parça eklendiği için.
- **Listeye girmemek = rütbe yok.** BM25 yalnızca en az bir sorgu sözcüğü geçen parçaları puanlar; 2 parçalık bir listenin "3. sırası" hit@4 sayılırsa kendinizi alatırsınız. Betik bu yüzden eşleşmeyen maddeye korpus büyüklüğü + 1 rütbe verir ve tabloda `126` görünür.
- **Üç soru kümesi:** orijinal 6 soru (Örnek 6'nın test seti), 6 parafraz, 6 "leksik" soru. Leksik set hedef maddede geçen somut terimlerle kurulur (hat kodu `M11`, özel ad `Seyrantepe`, sayı `1869`, terim `batırma`) ve betik her terimin korpusta **hangi maddelerde** geçtiğini çalıştırma anında doğrular — yani "sözlüğün kazanması beklenen" sorular gerçekten sözlükle kurulmuştur.
- **Sözcüğe bölme naiftir:** küçük harfe indir + regex. Bu, ekleri (`seferleri`) gövdeye indirmez; Türkçe için bilinçli bir eksiklik, sonuçları okurken hatırlayın.

## Ölçülen Sonuç: Üç Kol, Üç Soru Kümesi

Aşağıdaki her sayı aynı anda çalıştırıldı: aynı 125 parça, aynı sorular, yalnızca sıralama fonksiyonu farklı. Hücreler beklenen maddenin **ilk parçasının rütbesi**; `126` = listede hiç yok.

```text title="hit@1 / hit@4 (k=4, 2026-10-16, hibrit-kaydi-127.txt)"
  soru kümesi        vektör        bm25        hibrit
  orijinal (6)       5/6  6/6      3/6  6/6    4/6  6/6
  parafraz (6)       4/6  5/6      2/6  4/6    2/6  5/6
  leksik  (6)        3/6  5/6      3/6  6/6    2/6  5/6

  sorgu gecikmesi (12 deneme ortalaması, CPU, duvar süresi)
  vektör (gömme çağrısı + kosinus) : 0,144 sn
  bm25   (saf Python, bellek içi)  : 0,0001 sn  (≈1.440 kat hızlı; 0,144/0,0001)
```

:::note[İki koşum, iki oran: 10.800 kat değil 1.440 kat]
Aynı betik `http://localhost` ile koştuğunda vektör sorgusu **2,168 sn** ölçülmüştü; adres `127.0.0.1` olunca **0,144 sn**ye indi. Fark modelin işi değil, Windows'un `localhost` adını her istekte ~2 sn'de çözelmesi ([Hız ve Maliyet](/kullanim/hiz-ve-maliyet/)). BM25 kolunun 0,0002 → 0,0001 sn'ye inmesi ise milisaniyenin altındaki bir oynayış: o ölçekte run-to-run gürültü. Ders: **orantıyı duvar süresiyle değil, sunucunun kendi süresiyle kurun** — yayımlanan 10.800 kat, tek kelimelik bir istemci giderinden şişmiş hâliydi; ölçülmüş gerçekte oran 1.440.
:::

### Dört dürüst okuma

**1) Vektör, doğal dil sorularında açık ara önde.** "İETT ne zaman kuruldu?" sorusunda vektör 1. sırada, BM25 4. sırada: soruda İETT maddesinin metniyle örtüşen belirleyici bir sözcük yok ("ne zaman", "kuruldu" her maddede geçiyor). Orijinal + parafraz kümelerinin toplamında vektör 9/12, BM25 5/12.

**2) Leksik sorular vektörün penceresinden düşüyor.** "Vapur seferleri hangi iskeleye uğrar?" sorusunda beklenen madde vektörde **14.** sıraya kadar geriledi — k=4 bağlam penceresinin dışı, yani pratikte **tam kaçırma**. Aynı soru BM25'te 2. sırada. Sonucu BM25'in hit@4'ü taşıyor: leksik kümede 6/6 ile tek tam kapsama ulaşan kol o. `M11`, `Seyrantepe`, `Ayrılık Çeşmesi` gibi biçim-dışı belirteçler, 1024 boyutlu bir vektörde seyrek paragraf bağlamının içinde kayboluyor.

**3) Hibrit, bu korpusta hit@1'de hiç bir kolu geçemedi.** Üç kümede de hibrit hit@1 en yüksek değer değil (4/6, 2/6, 2/6). Günlükte tek tek görünüyor:

| Soru | vektör | bm25 | hibrit |
| --- | --- | --- | --- |
| Marmaray servise ne zaman girdi? | 1 | 9 | 2 |
| Tünel füniküleri hangi iki istasyonu bağlıyor? | 1 | 2 | 3 |
| M11 hattı hangi istasyonlardan geçiyor? | 1 | 4 | 2 |
| Vapur seferleri hangi iskeleye uğrar? | 14 | 2 | 5 |

Sebep aritmetik: `k=60`'ta listenin 1. sırası RRF'de 1/61 = 0,0164 puan alır, 9. sıra 1/69 = 0,0145. Yani BM25'te kötü görünen bir liste, vektörün ilk sırasını devirebilir. Üçüncü satır tam olarak bu: **iki kolu da ilk üçte olan** bir soru, birleştirince 3. sıraya düşüyor. Buna karşılık 4. satırda hibrit, vektörün 14.'sünü 5.'e taşıyıp kurtarmaya en yakın konuma getiriyor.

Dürüst özet: bu ölçümde hibrit **kaliteyi artıran değil, çeşitliliği azaltan** bir kol — ucuz soruları biraz düşürüp pahalı soruları yukarı çekiyor. `k` sabitini küçültmek, listeleri ağırlıklandırmak veya aday havuzunu (20) büyütmek farklı sonuç verir; **bunlar burada ölçülmedi**, sayfa tahmin üretmiyor.

**4) BM25 puanı eşik taşıyamaz — ölçüldü.** Kapsam dışı dört soruda en iyi BM25 puanları: kedi bakımı **1,81**, Ankara müzeleri **4,07**, "Türkiye'nin en uzun nehri" **7,08**; pizza sorusunda ise **eşleşen parça yok**. Aynı soruların vektör benzerlikleri 0,321-0,485 bandında. Dikkat: en yüksek BM25 puanı (7,08) alakasız bir sorudan geldi, çünkü "türkiye / en / uzun / hangisidir" sözcüklerinin dördü korpusta geçiyor — işlev sözcükleri puanı şişiriyor. "0,35 altı alakasız" tipi bir kontrol bu kolda çalışmaz; eşik vektör benzerliğinde kalmalı, birleştirme yalnız sıralamayı düzeltmeli. Yukarıdaki "Hibrit, iki aramayı topla demek değildir" kutusunun ölçülmüş hâli budur.

## Hangi durumda hangisi?

Deneyin sonucuyla birlikte kullanılabilecek karar listesi:

- **Korpusunuzda kod, sayı, madde numarası, ilaç/ürün adı varsa** → tek başına vektör pencereden düşürüyor (ölçülen: bir leksik soruda rütbe 14, yani k=4 bağlamına hiç girmiyor). En azından bir sözlük kolu ekleyin.
- **Kullanıcı tam cümleyle soruyorsa** → sözlük tek başına yetmiyor: orijinal + parafraz kümelerinde hit@1 vektörde 9/12, BM25'te 5/12.
- **Kullanıcı alakasız soru sorabiliyorsa** → eşik vektör kolunda kalsın; birleştirilmiş listede eşik aramayın.
- **GPU'nuz yok ama sağlam bir taban istiyorsanız** → hibrit, sıfır eğitim ve sıfır yeni modelle iki kolun iyi yanlarını tek listeye toplar. Ama ölçüm gösterdi ki bu **her soruda kazanmak demek değil**: hit@1 hiçbir kümede en iyi kolu geçemedi, karşılığında çeşitlilik azaldı. Beklentiniz bu olmalı.
- **Bağlam penceresi kısaysa** → hit@4 karar verdirmemeli: birleştirmenin kurtardığı parça 5. sıradaysa (ölçülen "vapur" vakası: 14 → 5) bağlama yine girmiyor.
- **İndeksleme ucuz, sorgu pahalıysa** → semantik bölmeyi veya geç parçalamayı düşünün; bunlar indeksleme tarafına yazılır, sorgu tarafına değil.
- **Sorgu gecikmesi kritikse** → BM25'i tek kol olarak tutun (sözlük araması milisaniyeler içinde döner), vektörü asenkron/önbellekli kullanın.
- **Hâlâ yetmiyorsa** → yeniden sıralama (cross-encoder) ekleyin; bu en pahalı koldur, en sona saklayın.

## Bu Sayfadaki Deney Nasıl Tekrarlanır?

```bash
cd ornekler/viki-rag
python hibrit.py        # taze indeksleme, 127.0.0.1 -> cikti/hibrit-kaydi-127.txt (253,0 sn vektörleştirme)
python hibrit.py        # ikinci koşum: önbellek gömmeyi atlar, yalnızca sıralama + gecikme
```

Önbelleği sıfırlayıp `localhost` ile ölçmek isterseniz sayı **529,3 sn**'ye çıkar (`cikti/hibrit-kaydi.txt`, 2026-10-15 koşumu); tek fark adres, yani 125 istek × ~2 sn isim çözümleme gideri.

İlk çalıştırma `cikti/vektor-indeks.json.gz` dosyasını yazar; korpus imzası (parça kimlikleri + uzunlukları) değişmezse gömme tekrarlanmaz ve betik `[önbellek] 125 gömme vektörü okundu, vektörleştirme atlandı` satırını basar. Vikipedi maddeleri canlı olduğu için imza birkaç gün sonra değişebilir — bu durumda betik yeniden vektörleştirir.

Önbellekli ikinci koşumda da **üç tablonun tüm rütbeleri ve hit@k satırları birebir aynı** çıktı; farklı olan tek şey sorgu gecikmesiydi (2026-10-15 `localhost`: 2,168 → 2,174 sn vektör; 2026-10-16 `127.0.0.1`: 0,144 → 0,145 sn vektör, 0,0001 sn bm25). Yani deney deterministik: sıralama farkı görürseniz sebep ölçüm gürültüsü değil, kod veya korpus değişimidir.

## Kaynaklar ve İleri Okuma

- [Robertson & Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond" (2009)](https://www.nowpublishers.com/article/Details/IPR-017) — BM25'i kimlerin kullandığı ve `k1`/`b` ayarlarının pratikte ne yaptığı.
- [Apache Lucene `BM25Similarity` sınıf belgesi](https://lucene.apache.org/core/9_10_0/core/org/apache/lucene/search/similarities/BM25Similarity.html) — varsayılan `k1 = 1,2`, `b = 0,75`; Elasticsearch/OpenSearch/Solr'un altındaki parametreler.
- [Cormack, Clarke & Büttcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (SIGIR 2009)](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) — RRF'nin orijinal makalesi; neden puan değil sıra kullandığı.
- [Elasticsearch RRF retriever belgesi](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) — `rank_constant` (varsayılan 60) ve `rank_window_size`.
- [Weaviate hybrid search belgesi](https://docs.weaviate.io/weaviate/search/hybrid) — `alpha` ve `rankedFusion`/`relativeScoreFusion` modları.
- [Qdrant arama belgesi](https://qdrant.tech/documentation/concepts/search/) — `Query::Hybrid` (dense + sparse) ve RRF/DBRF birleştirme modları.
- [Chroma, "Evaluating chunking strategies for retrieval" (2024)](https://www.trychroma.com/research/evaluating-chunking) — beş korpusda böleme stratejilerinin geri çağırma/hassasiyet karşılaştırması.
- [Günther ve ark., "Late Chunking: Improving RAG through Chunk-Aware Context Embeddings" (2024)](https://arxiv.org/abs/2409.04701) — geç parçalama yöntemi ve referans uygulaması.
- [Anthropic, "Contextual Retrieval" (2024)](https://www.anthropic.com/news/contextual-retrieval) — parçaya bağlam ekleyip yeniden sıralamayı birleştiren yaklaşım; sayılar tedarikçi tarafından ölçülmüştür.
- [BAAI/bge-reranker-v2-m3 model kartı](https://huggingface.co/BAAI/bge-reranker-v2-m3) — yerelde çalıştırılabilir çok dilli cross-encoder; desteklenen dil listesi Türkçe için dikkatli okunmalı.
- [Liu ve ark., "Lost in the Middle: How Language Models Use Long Contexts" (2023)](https://arxiv.org/abs/2307.03172) — bağlam uzadıkça ortadaki bilginin neden daha az kullanıldığı.
- [Bu rehberin RAG değerlendirme sayfası](/rag/rag-degerlendirme/) — hit@k, MRR ve eşik ölçümünün adımları; bu sayfadaki deney onun ölçüm dilini kullanır.
- [Örnek 6: Vikipedi'den Türkçe RAG](/ornekler/viki-rag/) — deneyin korpusunu kuran betik ve parçalama kararları.
