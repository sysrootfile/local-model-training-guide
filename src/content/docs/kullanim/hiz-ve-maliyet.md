---
title: "Yerel Çıkarım Hızı ve Maliyeti: Ölçülmüş Sayılar"
description: "Bir yerel modelin cevabı neden saniyeler sürer. Soğuk yükleme, ön-yükleme, çözme ve ilk token süresinin bu makinede ölçülmüş dağılımı; num_ctx'in bellek basamakları ve sessiz kırpma tuzağı; prompt önbelleğinin sağladığı kazanç; Türkçe metnin karakter/token oranı; ayrıca kodunuzda Ollama'dan bağımsız ödenen iki saniyelik isim çözümleme gideri."
dogrulama: 2026-10-20
---

Örnek 5 ve Örnek 6'da "cevap 52-66 sn sürüyor", "sorgu gömme 0,144 sn" gibi sayılar okudunuz (bu sayfadaki ölçümlerin ilk yayımı bu örneklerin `http://localhost` ile ölçüldüğü günlere, 57-69 sn / 2,168 sn sayılarına dayanıyordu — o giderin ne olduğu bu sayfanın altındadır). Bu sayılar bir yerden gelmek zorunda. Bu sayfa, onların geldiği yerdir: aynı makinede, aynı modellerle, ölçülmüş bir gecikme dökümü.

Burada bir kıyaslama (benchmark) yok. Kıyaslama "şu model en hızlısı" demektir; burası ise başka bir soruyu yanıtlıyor: **bir soru neden bu kadar sürüyor ve parayı nereye ödüyorsunuz.** Sayılar sizin makinenizde farklı olacaktır; önemli olan fazların sırası ve hangisinin baskın olduğu.

:::note[Bu sayfadaki her sayı ölçüldü]
Tümü bu makinede, %100 CPU'da, `ornekler/cikarim-olcu/hiz_olc.py` kafesinden alındı — **"Toplu gömme" bölümü hariç**: o bölümün iki yanı `ornekler/gomme-egitimi/gomme_egit.py --kol e` ile, aynı makinede ve yine %100 CPU'da koşuldu. **İki tur koşuldu:** birinci turda betik `http://localhost:11434` kullanıyordu (`cikti/hiz-kaydi.txt` ile `hiz-kaydi-4.txt`), ikinci turda `http://127.0.0.1:11434` (`cikti/hiz-kaydi-127.txt`, 2026-10-16 01:21-01:39). Aşağıdaki tabloların gövdesi **ikinci turdandır**; yalnızca "Toplu gömme" tablosu 20 Ekim'deki E koşumundandır. İki turu karşılaştırınca iki şey görüldü: (1) duvar süreleri adrese bağlı olarak ~2 sn/istek indi, (2) **sunucunun kendi hızları da koşumdan koşuma oynuyor** — fark yöntemiyle ön-yükleme 39,9-40,5 → 43,9-45,9 tok/sn, çözme 13,8-14,0 → 13,9-14,8 tok/sn; bellek basamakları (`ollama ps`) ise birebir aynı. Oynama tek başına adres gideri kadar büyük: bu sayfada tek bir ölçüme güvenmeyin. Ölçmediğimiz bir şeyi söylediğimiz yerde ayrıca "ölçülmedi" yazıyor.
:::

## Makine ve modeller

| Öğe | Değer |
| --- | --- |
| İşlemci | AMD Ryzen 5 2600, 6 çekirdek / 12 iş parçacığı |
| RAM | 15,9 GB; koşum sırasında 2,0-3,6 GiB boş (sistem %87 dolu) |
| Disk | SATA SSD (ADATA SU650) |
| Sunucu | Ollama 0.40.4 (sayfanın gövdesindeki ölçümler; makine 2026-10-19'da 0.40.6'ya geçti, gövde sayıları o sürümde yeniden ölçülmedi). 2026-10-20'de eklenen "Toplu gömme" bölümü 0.40.6 ile ölçüldü; `ollama ps` çıktısında "100% CPU" |
| Adres | aşağıdaki tablolar `http://127.0.0.1:11434`; birinci tur `http://localhost:11434` |
| Sohbet modeli | `qwen2.5:3b-instruct-q4_K_M`, yerleşik boyutu 2,2 GB |
| Gömme modeli | `bge-m3`, vektör boyutu 1024 |

## Bir isteğin anatomisi: dört faz, dört ayrı fiyat

Ollama her cevabın sonunda size sayılar verir. Kavramak gereken şey, bu sayıların **aynı birim olmadığı**:

```text
total_duration  = yük + ön-yükleme + çözme   (nanosaniye)
load_duration      modelin belleğe yerleşmesi
prompt_eval_count  girdi token sayısı       /  prompt_eval_duration
eval_count         üretilen token sayısı    /  eval_duration
prompt_eval_cached_count  önbellekten gelen, yeniden hesaplanmayan token
```

- **Ön-yükleme (prefill):** yazdığınız her şey (sistem istemi, RAG bağlamı, soru) modele bir seferde beslenir. paralel işlenebildiği için *hızlıdır*.
- **Çözme (decode):** model token'ı tek tek üretir. Her adım önceki tüm bağlamı okur, yani *daha yavaştır*.
- **İlk token süresi (TTFT, time to first token):** kullanıcının ekranda bir şey görmeye başlayana kadar beklediği an. Yük + ön-yükleme toplamıdır.

Aynı istekte ölçülen iki hız:

| Faz | Ölçülen hız (2026-10-16, `127.0.0.1`) | Ne anlama geliyor |
| --- | --- | --- |
| Ön-yükleme, önbelleksiz | **36,3-37,4 tok/sn** (E4, 688 token'lık bağlam) · **43,9-45,9 tok/sn** (E3b, fark yöntemiyle; 1.329 token'lık girdi 28,92 sn) | bağlam uzadıkça doğrusal artan maliyet |
| Çözme | **13,9-14,8 tok/sn** (64, 256 ve 412 token üretimde aynı bant) | üretilen her token sabit fiyatlı |

Yani bu makinede bir girdi token'ı, bir çıktı token'ından **2,5-3,3 kat ucuz** (iki bandın uçlarını böldüğünüzde: 36,3/14,8 = 2,5 ile 45,9/13,9 = 3,3). Sayıları deneyin: 700 token'lık cevap ≈ 47-50 sn, 700 token'lık bağlam ≈ 15-19 sn.

:::caution[Uzayan cevap, uzayan bekleme]
Çözme hızı sabit: 64 token 4,42 sn, 256 token 18,48 sn, 412 token 27,90 sn (67,7-72,2 ms/token). Cevabı uzun tutmak, bağlamı uzun tutmaktan bu makinede daha pahalıdır. `num_predict` ile tavan koymanın pratik karşılığı budur.
:::

### İlk token süresi, akış modunda ölçüldüğünde

Kullanıcı `total_duration`'ı değil, ilk harfi bekler. E7 ve E7b'de akış açılıp ilk chunk'ın geliş zamanı ölçüldü:

| İstek | İlk token | Toplam |
| --- | --- | --- |
| Kısa istem (E7b, tur 1) | 4,04 sn | 6,60 sn |
| Kısa istem (E7b, tur 2 — önbellek sıcak) | **0,08 sn** | 2,62 sn |
| Uzun istem, 688 token bağlam (E7b, tur 1) | 10,92 sn | 13,79 sn |
| Uzun istem (E7b, tur 2) | **0,10 sn** | 2,96 sn |
| Aynı iki istem, E7 koşumunda | 8,80 sn / 12,94 sn | 11,7 sn / 16,0 sn |

Üç ders var. (1) TTFT'niz ön-yüklemenin ta kendisi: bağlam 211 tokenden 688 tokene çıkınca ilk token 4,04 sn'den 10,92 sn'ye çıktı. (2) Önbellek onu 0,1 sn'ye düşürüyor — yani **aynı bağlamla sürdürülen ikinci tur, ilk turdan dramatik biçimde daha hızlı başlar.** (3) Çözme bundan bağımsız: 40 token'lık üretim her satırda 2,5-2,9 sn. Not: E7 ile E7b aynı istekleri farklı sayılarla ölçtü, ama E7 kaydı o anki önbellek ve bellek durumunu ayrı satırda raporlamıyor; aradaki farkın nedenini **ölçmedik**, bu yüzden E7'yi ayrı satırda tuttuk.

## Soğuk mu, sıcak mı: bellekte duran modelin değeri

Aynı kısa soru, üç durumda:

| Durum | Duvar (sizin beklediğiniz) | Sunucu | Yük | Ön-yük | Çözme |
| --- | --- | --- | --- | --- | --- |
| `keep_alive: "0"` (çağrı bitince boşalttı) | 2,2 sn | 2,12 sn | 0,01 sn | 37 tok / 1,02 sn | 16 tok / 1,07 sn |
| Soğuk çağrı (az önce boşaldı, yeniden yüklendi) | 11,4 sn | 11,35 sn | **9,15 sn** | 37 tok / 1,07 sn | 16 tok / 1,11 sn |
| Sıcak çağrı (bellekte hazır) | 1,2 sn | 1,22 sn | 0,02 sn | 37 tok / 0,09 sn (430 tok/sn, 36 önb.) | 16 tok / 1,11 sn |

Üç satırda da **duvar ile sunucu üst üste** (fark 0,00-0,08 sn). Birinci turda bu fark hep ~2,0 sn'ydi; adres `localhost`'tan `127.0.0.1`'e geçince kayboldu — yani aşağıdaki rakamlar artık gerçekten modelin işidir.

Soğuk yükleme tek bir sayı değil: bu turda E1'de **9,15 sn**, aynı turun E10 çevriminde beş yeniden yüklemede **3,10-3,12 sn**, birinci turda 3,1-3,4 sn. Aynı makinede, aynı modelde 3-9 sn arası bir bant; neye güveneceğiniz "soğuk çağrı sıcak çağrıdan birkaç saniye pahalıdır" kuralı, sabit değil. Ollama varsayılan olarak modeli **5 dakika** bellekte tutar (`OLLAMA_KEEP_ALIVE`; istek bazında `keep_alive` ile geçersiz kılınır).

Boşalt/yükle çevrimi beş kez tekrarlandı: yeniden yükleme çağrıları duvar **4,9-5,0 sn** (birinci turda 7,3 sn'ydi — fark yine isim çözümleme gideri).

`ollama ps` çıktısı bu kararın kontrol noktasıdır; "4 minutes from now" yazıyorsa bir sonraki soru sıcak gidecek demektir.

## num_ctx: bellek basamakları ve sessiz kırpma

Bağlam penceresi (`num_ctx`) "modelin kaç token'ı birlikte görebileceği". Ölçülen etki:

| `num_ctx` | `ollama ps` boyutu | Değerlendirilen token | Sonuç |
| --- | --- | --- | --- |
| 512 | 2,0 GB | **258** | 688 token'lık istekten 430 token **sessizce düştü** |
| 2048 | 2,1 GB | 688 | sığdı |
| 4096 (varsayılan) | 2,2 GB | 688 | sığdı |
| 8192 | 2,4 GB | 688 | sığdı |

:::caution[Kırpma size bir şey söylemez]
512 satırında hata almadık, uyarı almadık, HTTP 200 döndü. Tek kanıt, cevaplandığını sandığınız metnin yarısının gerçekten okunmamış olması. RAG'de bu şu anlama gelir: **parçaları bağlama doldururken toplam token sayısını kontrol etmezseniz, model getirdiği belgelerin bir kısmını görmemiştir ve siz kalite düşüklüğünü modelin aptallığına yorarsınız.**
:::

İki ek gözlem: her `num_ctx` değişimi modeli yeniden yükletti (satır başına 3,48-6,79 sn `yük`; birinci turda 3,2-3,5 sn). Ve bağlamı büyütmek üretim hızını değiştirmedi (çözme 12,6-13,1 tok/sn bandında) — ölçeklenen şey bellek ve ön-yükleme süresidir. Bellek hesabının yöntemi ve GPU tarafı için [VRAM/RAM sayfasına](/donanim/vram-hesabi/), Ollama'nın bellek katmanları için [Ollama sayfasına](/kullanim/ollama/) bakabilirsiniz; buradakiler CPU'da ölçülmüş değerler.

## Prompt önbelleği: aynı bağlamı ikinci kez okumak

688 token'lık aynı istek tekrar gönderildiğinde:

| Okuma | Token | Önbellekten | Ön-yükleme süresi |
| --- | --- | --- | --- |
| İlk okuma (E4, `num_ctx=8192`) | 688 | 0 | 18,96 sn |
| Aynı önek, sonraki okumalar (E5) | 688 | **687** | **0,08 sn** |
| Sonundaki soru değiştirilmiş (E5) | 679 | **661** | 0,75 sn |

Önbellek, bağlamın *ön ekini* eşler. Bu RAG ve ajan döngüleri için doğrudan bir tasarım kuralına dönüşür: **bağlamı başa koyun, soruyu sona ekleyin.** Son cümleyi değiştirmek 679 − 661 = 18 token'lık yeniden hesaplamaya mal oldu; baştan yazmak 688 token'ın tamamına mal olurdu.

:::note[Kazanç gerçek, ama sınırsız değil]
Önbellek RAM'de tutulur ve boyutu yapılandırılabilir değil; Ollama'yı çalıştıran kişilerin bu konudaki şikâyeti açık bir issue'da duruyor (ollama/ollama #17351, "Make prompt cache size configurable", 2026-07). Birinci turun günlüğünde en büyük önbellek durumu 4 prompt / 334 MiB olarak görülmüştü; ikinci turun sonunda günlükte 0 prompt / 0,000 MiB kayıtlıydı — yani model boşaldığında önbellek de sıfırlanmıştı (E9 faz B'de ikinci çağrıya kadar 0 önbellek token'ı görülmesi bundan).
:::

## num_thread: CPU'da daha çok iş parçacığı daha çok hız mı?

| `num_thread` | Ön-yükleme | Çözme |
| --- | --- | --- |
| 2 | 16,9 tok/sn | 9,0 tok/sn |
| 6 (fiziksel çekirdek sayısı) | 32,8 tok/sn | **14,5 tok/sn** |
| 12 (mantıksal iş parçacığı) | **44,6 tok/sn** | 13,3 tok/sn |

İki ayrı eğri: ön-yükleme paralelleştirmeye açık, 12 iş parçacığında hâlâ kazanıyor; çözme 6'da tepede, sonrası **kazanç yok** (13,3 vs 14,5). Sebep tek token'lık işin çekirdekler arasında bölünememesi; bellek bant genişliği dar boğaz oluyor. Kural: uzun girdili işlerde iş parçacığını yükseltin, sohbet hissi için varsayılan bırakın.

Birinci turda aynı test 17,4 / 36,6 / 44,9 tok/sn ön-yükleme, 9,0 / 13,9 / 12,8 tok/sn çözme vermişti. Şekil aynı, rakamlar kayıyor — 12 iş parçacığının çözmeye zararı bir turda 1,1 tok/sn, diğerinde 0,6 tok/sn. Tek ölçüme dayanıp "6 ideali" demiyoruz; "12'de çözme kazancı yok" diyoruz.

## Türkçe metnin token fiyatı

İngilizce için dolaşan "1 token ≈ 4 karakter" kuralının Türkçe karşılığı ölçüldü. Yöntem: aynı metnin iki kat büyüklüğünü gönderip **token farkını karakter farkına bölmek** — böylece sohbet şablonunun sabit gideri hesabın dışına çıkıyor.

| Karakter farkı | Token farkı | Oran | Süre farkı | Ön-yükleme hızı |
| --- | --- | --- | --- | --- |
| 476 | 159 | 2,99 karakter/token | 3,62 sn | 43,9 tok/sn |
| 952 | 318 | 2,99 | 6,92 sn | 45,9 tok/sn |
| 1904 | 636 | 2,99 | 14,32 sn | 44,4 tok/sn |

Son iki sütun E3b'den: her satırın başına benzersiz bir numara konularak önbellek eşleşmesi bozuldu, böylece süre gerçekten baştan sona önbelleksiz ön-yükleme oluyor. Oran birinci turda da aynıydı (2,99); süre sütunları turdan tura ~%10 oynuyor — **karakter/token oranı deterministik, hız deterministik değil.**

**Türkçe metin ~3 karakter/token** üretiyor (4 değil). Bir paragraf için oran 2,94-2,99 bandında sabit kaldı. Sonucu iki yerde kullanın: (1) bağlamınızı token cinsinden tahmin ederken karakter sayısını 3'e bölün, 4'e değil; (2) bulut API fiyatlandırmasında Türkçe içerik aynı kelime sayısı için daha pahalıdır. [Tokenizasyon sayfasında](/temeller/tokenizasyon/) bu oranın dilbilgisel nedeni var.

## RAG sorgusunun gerçek maliyet dökümü

Bir soruyu yanıtlayana kadar geçen sürenin dağılımı (sunucu tarafı; istemci gideri sonraki bölümde):

| İş | Ölçülen |
| --- | --- |
| Sorguyu gömmek (11 token, `bge-m3`) | **0,09-0,13 sn** |
| 1.904 karakterlik (450 token) parçayı gömmek | **2,47-3,04 sn** |
| `bge-m3`'ün soğuk yükleme maliyeti | 11,92 sn — **yalnız birinci turda, bir kez** ölçüldü; ikinci turda model bellekteydi, tekrarlanmadı |
| 683 token bağlamı sohbete ön-yüklemek | 17,62 sn (38,8 tok/sn, 3 önbellek token'ı) |
| 49 token cevap üretmek | 3,89 sn |
| Toplam cevap süresi (duvar) | 21,5 sn |

Orantı şaşırtıcı: **arama 0,1 sn, üretim 21,5 sn.** RAG'in pahalı kısmı vektör indeksi değil, bulduğunuz metni dil modeline okutmak. Örnek 6'nın 52-66 sn'lik cevapları da buradan hesaplanabilir: 4 parça ≈ 2.450 token, 2.450 ÷ ~40 tok/sn ≈ 61 sn.

:::note[İki model aynı anda bellekteyken yavaşlama ölçülmedi]
Sohbet modeli bellekteyken sorgu gömme 0,10 sn, boşaltıldıktan sonra 0,09 sn; uzun parça 2,55 sn vs 2,47 sn. 15,9 GB'lık makinede, %87 dolulukta, ikinci modelin varlığı ölçülebilir bir ceza üretmedi. (Bu, bellek baskısının hiç ceza üretmediği demek değil — şu koşullarda üretmediği demek. E8b'de sohbet modeli 2,2 GB yerken bile gömme süreleri değişmedi.)
:::

## Toplu gömme: 24 parça tek istekte mi, 24 ayrı istekte mi?

Bir RAG indeksi kurarken parçaları gömmek zorundasınız. `/api/embed` tek istekte bir **liste** kabul ediyor; aynı 24 parçayı 24 ayrı istekte de gönderebilirsiniz. Soru şu: aradaki fark, istek başına sabit bir gider mi, yoksa hesaplamanın kendisi mi?

Bu karşılaştırma 2026-10-20'de, Ollama **0.40.6**'da, tek oturumda ve model ısıtıldıktan sonra ölçüldü. İki yan da aynı 24 kurgusal cümleyi (`bge-m3`, toplam 583 token) aynı sunucuya gönderiyor; tek fark isteklerin bölünmesi. Her yan beş kez koşuldu, sıra tekrarlar arasında dönüşümlüydü (1/3/5: tek→ayrı, 2/4: ayrı→tek). Süreler duvar saatidir; sayılan toplam 125 ölçüm isteği, bir ısıtma ve bir tahliye isteği sayılmadı.

| Yan | Beş tekrar (sn) | p50 | p95 | Min–maks | Beş tekrar toplamı |
| --- | --- | --- | --- | --- | --- |
| 24 parça tek istekte | 4,58 · 4,57 · 4,73 · 4,44 · 4,64 | **4,58** | 4,71 | 4,44–4,73 | 22,97 sn |
| 24 ayrı istekte | 4,90 · 4,96 · 4,86 · 5,01 · 4,97 | **4,96** | 5,00 | 4,86–5,01 | 24,69 sn |

İki yanın tekrar aralıkları çakışmıyor (4,73 < 4,86). Önceden yazılan kural buydu: aralıklar çakışırsa "fark ölçülemedi" denecekti, çakışmazsa p50'si düşük olan yan kazanacaktı. **Tek istek daha ucuz:** p50 farkı 0,38 sn, yani 24 ayrı istek tek isteğin 1,08 katı.

Ama büyüklüğe bakın. 24 ayrı istekte istek başına p50 **0,204 sn** (p95 0,254); aynı işin tek istekte parça başına payı 4,58 / 24 = **0,191 sn**. Toplam 0,38 sn'lik farkı 24 isteğe bölerseniz istek başına ≈0,016 sn kalır. Gömme işinin kendisi 4,4-5,0 sn sürdüğü için bu korpusta toplulaştırmanın kazancı **yaklaşık %8**; pahalı olan istek sayısı değil, hesaplamanın kendisi. İstemci tarafında da anlamlı bir ek gider yok: 24 ayrı istekte duvar ile sunucunun toplam süresi arasındaki fark 0,05-0,09 sn, tek istekte 0,01-0,03 sn.

Token sayıları iki yanda da 583. Yani 24 istek, aynı metni 24 kez yeniden hesaplamıyor; her istek yalnız kendi cümlesini görüyor ve toplam iş aynı kalıyor. Sunucunun kendi `total_duration` toplamı da aynı resmi veriyor: p50 tek istekte 4,57 sn, 24 ayrı istekte 4,87 sn (duvardan farkı istemci tarafıdır).

:::caution[Bu sayı, Gömme Modeli Eğitimi sayfasındaki 24 parçalık ölçümle karşılaştırılamaz]
[Gömme Modeli Eğitimi](/rag/gomme-egitimi/) sayfasındaki 24 parçalık tek istek ölçümü 0.40.4'te, farklı bir koşumda ve modelin ısınma durumu ayrıca kaydedilmeden alındı. Buradaki iki yan ise 0.40.6'da, aynı oturumda, ısıtma isteği sayılmadan ölçüldü. İki sayı bir A/B'nin iki tarafı değildir; yan yana konup "toplu gömme şu kadar hızlandırdı" denemez. Toplulaştırmanın kazancı yalnızca bu tablodaki iki yan arasında okunur.
:::

Sınırlar: 24 parça / 583 token küçük bir iştir; daha büyük partide sabit giderin payı daha da düşer, ama 24'ten büyük parti **ölçülmedi**. `/api/embed` isteklerini eşzamanlı çalıştırmak da bu koşumun dışında. Beş tekrarın dağılımı verildi, güven aralığı çıkarılmadı.

## İsteminizin içindeki iki saniye

Ölçümlerin ilk turunda inatçı bir tutarlılık vardı: sunucu 1,2 sn derken duvar 3,2 sn. Fark hep ~2,0 sn. Kaynağını aradık (E11, birinci tur):

| Hipotez | Test | Sonuç |
| --- | --- | --- |
| Vekil sunucu (proxy) algılama | `ProxyHandler({})` ile kapatarak çağrı | **elenmedi**: 2,05 sn → 2,08 sn |
| TCP bağlantısı kurma gideri | `http.client` ile doğrudan bağlantı | **elendi**: 0,00 sn fark |
| `localhost` adının çözülmesi | aynı istek `http://127.0.0.1:11434` ile | **bulundu**: 2,03 sn → **0,00 sn** |

İkinci tur (2026-10-16) aynı testi betik `127.0.0.1` kullanırken tekrarladı — ve ortada elenecek bir 2 saniye kalmamıştı: varsayılan ortamda 4 denemenin medyan farkı **0,00 sn**, vekil sunucu kapalıyken **0,03 sn**. Yani vekil sunucuyu birinci tur eledi; ikinci tur adres değişikliğinin kendisini doğruladı.

Kanıt olarak tek bir çağrının iki adresle ölçümü (E12, ikinci tur; her satır 4 deneme):

| Adres ve istemci | Duvar − sunucu farkı (medyan) | Denemeler |
| --- | --- | --- |
| `http://localhost:11434` (urllib) | **2,04 sn** | 2,05 / 2,05 / 2,04 / 2,03 |
| `http://127.0.0.1:11434` (urllib) | **0,00 sn** | 0,00 / 0,00 / 0,00 / 0,00 |
| `http://127.0.0.1:11434` (`http.client`) | 0,00 sn | 0,00 / 0,00 / 0,00 / 0,00 |

Windows'ta `localhost` adını çözmek her istekte ~2 sn sürüyor; sayısal adres aynı işi anında yapıyor. Modelle, CPU ile, RAM ile ilgisi yok — kodunuzda bir kelime.

Etkinin boyutu, döngü başına çağrı sayısına bağlı. 10 parçalık bir indeksleme A/B'si (E13, ikinci tur):

| Adres | 10 parça toplam | Parça başına | Sunucunun işi | İstemci gideri |
| --- | --- | --- | --- | --- |
| `localhost` | 32,5 sn | 3,25 sn | 12,2 sn | **20,4 sn (%63)** |
| `127.0.0.1` | **12,5 sn** | 1,25 sn | 12,4 sn | 0,0 sn (%0) |

Birinci turda aynı A/B **35,6 sn / 16,1 sn** çıkmıştı. İki turu yan yana koyunca kararlı olan şey istemci gideri: 10 istekte 20,3 sn, sonra 20,4 sn (başına 2,03-2,04 sn). Kararsız olan sunucunun işi: `localhost` tarafında 15,3 → 12,2 sn, `127.0.0.1` tarafında 16,1 → 12,4 sn. Yani oran (%57 → %63) tek başına değişiyor; bu makinede hız ölçümü bir kez yapılmaz.

:::caution[Bu gider, sitedeki indeks sürelerinin yarısıydı — şimdi ölçüldü]
Bu sayfa yazılırken Örnek 5-6 ve RAG betiklerinin tümü `http://localhost:11434` kullanıyordu; yani okuduğunuz indeks süreleri istek başına ~2 sn'lik isim çözümlemesini de içeriyordu ve "125 parça × 2,03 sn ≈ 254 sn" ayrımı yalnızca **ölçülmüş iki bileşenin aritmetiğiydi**. 2026-10-16'da adres `http://127.0.0.1:11434`'e çevrilip aynı betikler yeniden koşuldu: aynı 125 parça, aynı makine, aynı sıralama sonuçları — `hibrit.py` vektörleştirmesi **529,3 → 253,0 sn**, `olc.py` bge-m3 **495,7 → 259,2 sn**, nomic-embed-text **503,7 → 158,6 sn**. Tahmin tuttu; hatta ikinci modelde düşüş 345 sn'ye çıktı, ki bu da o eski koşumda makine yükünün (RAM doluluğu) DNS giderine eklenmiş olabileceğini gösteriyor. Sayfalardaki güncel indeks/cevap süreleri bu yeniden koşumlardan geldi.
:::

## Takılma avı: bir hipotezin ölümü

Bu sayfanın yazılış hikâyesi dürüstçe şudur: birinci turun ölçümleri sırasında kısa bir istek **42,7 sn** sürmüştü; oysa aynı çağrının model işi 1-2 sn. Günlükte (Windows'ta `%LOCALAPPDATA%\Ollama\server.log`) biriken satırlar suçlu gibi görünüyordu:

```text
srv  get_availabl: prompt cache update took 92.7 ms
srv        update:  - cache state: 4 prompts, 334.237 MiB (limits: 8192.000 MiB, 4096 tokens, ...)
```

"Önbellek büyüdükçe istekler kilitleniyor" hipotezi kuruldu. Sonra ölçüldü ve üç yerde kırıldı:

1. **Birim kontrolü.** Son 2 MB günlükte birinci turda 126, ikinci turda 118 "prompt cache update" satırı var; en büyükleri sırasıyla **92,7 ms** ve **68,5 ms**. Milisaniye. 60 saniyelik bir takılmayı açıklayamaz — hipotezin çökmesi için tek bir birim harfi yetti. İkinci turun sonunda günlükte yazan son önbellek durumu ayrıca **0 prompt / 0,000 MiB**'di: ortada büyümüş bir önbellek bile yoktu.
2. **Tekrarlanabilirlik.** Özdeş sıcak çağrılar 8 kez koşuldu. Birinci tur: duvar 3,3-3,5 sn, `total_duration` ile faz toplamı arasındaki en büyük fark 0,07 sn. İkinci tur (`127.0.0.1`): duvar **1,3-1,5 sn**, en büyük fark **0,02 sn**. Boşalt/yeniden yükle çevrimi 5 kez tekrarlandı: birinci turda beşinde de 7,3 sn, ikinci turda **4,9-5,0 sn**. Aykırı değer ikinci turda çıkmadı — E10'daki boşaltma çağrılarının en yavaşı 5,3 sn. İkinci turda 15 sn'yi aşan tek çağrı, boşaltmadan hemen sonraki ilk çağrıydı (23,3 sn) ve o da hesaba sığıyor: 3,11 sn yeniden yükleme + önbelleği boş 688 token'lık ön-yükleme; faz toplamıyla duvar arasındaki fark 0,01 sn.
3. **Log'un kendi hesabı.** Günlükteki 20-59 sn süren istek satırlarının yanındaki `print_timing` kayıtları sürenin tamamını veriyor. Örnek (2026-10-14 tarihli bir kayıt, bu koşumdan değil): 49,34 sn'lik `POST /api/chat` = 46,59 sn ön-yükleme (2.046 token, 43,9 tok/sn) + 2,60 sn çözme (27 token, 10,0 tok/sn). İkinci turun penceresinde 907 `POST` isteğinin 36'sı 20 sn'nin üzerindeydi (en büyüğü 59,9 sn); E10 penceresinde 1.427 isteğin 67'si — hepsi uzun bağlamlı gerçek iş.

Yani "takılma" yoktu; **uzun bağlamlı gerçek iş** vardı ve biz ona yanlış isim vermiştik. Kalan tek aykırı gözlem (n=1) açıklanamadı; ölçüm tekrarında çıkmadı.

:::note[Bu bölümü neden siliyoruz]
Çünkü sayfanın en öğretici kısmı bu. Biraz yavaş hissedilen her şey "sunucu takılması" değildir; önce fazlara ayırın, sonra birimlere bakın. Ollama'nın dört süre alanı bunu bedava yaptırıyor.
:::

## Pratik karar listesi

Ölçümlere dayanan, bu makinedeki sırayla:

1. **Adresi `127.0.0.1` yaz.** Çağrı başına ~2 sn kazanç; RAG döngülerinde en büyük tek kalem.
2. **Bağlamı başa, soruyu sona koy.** Önbellek ön ekten eşleşiyor: 687/688 token bedava.
3. **Bağlama aldığın parça sayısını azalt.** Ön-yükleme ~40 tok/sn; 2.450 token'lık bağlam 61 sn. Üç parça yerine bir parça, bekleme süresini üçe bölüyor.
4. **`num_ctx`'i toplam token'ınıza göre kurun ve kontrol edin.** 512'de 688 token'lık isteğin 430'u sessizce düştü.
5. **Uzun cevap istiyorsanız fiyatını bilin.** Çözme 14 tok/sn'de sabit; 400 token ≈ 29 sn.
6. **Sıcak tutun.** `keep_alive` varsayılanı 5 dk; soğuk yükleme tek sayı değil, bu makinede ölçülen bant **3,1-9,2 sn** (ve `num_ctx` değişimi her seferinde yeniden yükletir: 3,5-6,8 sn).
7. **İş parçacığını işe göre ayarlayın.** Toplu indeksleme/ön-yükleme için 12, sohbet için 6.
8. **Aynı ölçümü en az iki kez koşun.** Bu sayfadaki iki tur, ön-yükleme hızını 39,9-40,5'ten 43,9-45,9 tok/sn'ye, çözme hızını 13,8-14,0'tan 13,9-14,8'e taşıdı. Bandın kendisi bulgu; tek sayı değil.
9. **Gömmeyi toplulaştırın.** Aynı 24 parça tek istekte p50 4,58 sn, 24 ayrı istekte 4,96 sn; kazanç yaklaşık %8. İstek başına sabit gider bu makinede milisaniyelerde, asıl maliyet hesaplamanın kendisi.

## Bu ölçümü kendi makinenizde tekrar edin

Kafes tek dosya, yalnızca Python standard kütüphanesini kullanıyor (Ollama dışında bağımlılık yok):

```bash
cd ornekler/cikarim-olcu
PYTHONUTF8=1 python -u hiz_olc.py > cikti/benim-kaydim.txt 2>&1
```

Koşum 20-40 dakika sürer ve **boyun eğdirici bir kuralı var:** bittiği ana kadar başka hiçbir Ollama isteği göndermeyin (sohbet arayüzü, editör eklentisi, başka bir betik). Sunucu varsayılan ayarla tek kullanıcıya göre sıralıyor — ki bu artık beklenti değil ölçüm: [Eşzamanlılık](/kullanim/eszamanlilik/) sayfasındaki K=4 dalgasında dört isteğin duvar süreleri 4,7 / 9,4 / 14,0 / 18,5 sn merdiveni gibi dizildi, istek başına çözümleme hızı ise hiç değişmedi. (Aynı sayfa `OLLAMA_NUM_PARALLEL=4` ile ikinci bir koşum da taşıyor: orada merdiven yok, ama tek isteğin hızı düşüyor. Yani kuralın sebebi ayar, kader değil.) Yarışan bir istek duvar sürelerinizi şişirir. İsterseniz `--yalnız E4 E5` gibi tek deney seçebilirsiniz; `--kisa` yalnızca E1, E2, E3, E7'yi koşar. Ham logların nasıl okunduğu (her satırın hangi `duration` alanından geldiği) `ornekler/cikarim-olcu/README.md`'de.

:::caution[Çıktıyı doğrudan dosyaya yazdırın]
`... | tee log.txt` kullanmayın: bu projede `tee` erken çıkıp 20 dakikalık bir koşumun çıktısını yok etti. `python -u` da şart — bayraksız çalıştırınca çıktı tamponda kalıyor, koşum sürerken log boş görünüyor.
:::

## Burada ölçülmeyenler

- GPU ile hiçbir ölçüm (bu makinede torch yok, ekran kartı kullanılmadı). Sayılar %100 CPU içindir.
- Başka model boyutları, başka nicemleme düzeyleri, başka CPU'lar. Bu kafes tek makineyi anlatır.
- `bge-m3`'ün soğuk yüklemesi: 11,92 sn **tek bir gözlem** (birinci tur). İkinci turda model bellekteydi, yeniden ölçülmedi.
- E7 ile E7b arasındaki TTFT farkının nedeni **ölçülmedi** (koşum sırası, makine doluluğu ve önbellek ısısı birlikte değişti).
- Eşzamanlılık artık üç sunucu ayarında, dört koşumda ölçüldü ve [Eşzamanlılık](/kullanim/eszamanlilik/) sayfasında: varsayılan ayarla aynı anda salıverilen dört istek **yarışmıyor, sıraya giriyor** (K=4 dalgasının son isteği 18,50 sn, bekleme hanesi 14,11 sn); `OLLAMA_NUM_PARALLEL=4` verildiğinde sıra kalkıyor (bekleme 0,12 sn) ama tek isteğin hızı 14,97 → 6,38 tok/sn'ye düşüyor; `=2` ayarında yuvadan çok istek geldiği için hız **düşmüyor, kuyruk uzuyor** (9,13 → 9,22 tok/sn; ilk çift 7,1 sn'de, ikinci çift 14,2 sn'de bitiyor). Bu sayfadaki tüm süreler **tek isteğin** süreleridir ve `-np 1` varsayılanıyla koşuldu. `OLLAMA_NUM_PARALLEL`'ın **3** seviyesi ve çok kullanıcılı kalıcı servis davranışı hâlâ **ölçülmedi** — sunucu ortamı betikten yazılamaz, değişkeni yazmak ve yeniden başlatmak makine sahibinin onayıdır. K > 4'ün ise tek bir noktası ölçülü: **K = 8**, varsayılan sunucuda 20 Ekim'de koşuldu ve desen merdiveni aynı kaldı; sayılar [Eşzamanlılık](/kullanim/eszamanlilik/) sayfasında. K = 5–7, K > 8 ve `=2` / `=4` sunucularında K > 4 hâlâ görülmedi.
- Toplu (batch) gömme: aynı 24 parçanın **tek istekte** ve **24 ayrı istekte** süresi 20 Ekim'de birlikte ölçüldü; sonuç yukarıdaki "Toplu gömme" bölümünde. Daha büyük bir partinin (ör. 125 parça) tek istekte gönderilmesi ve `/api/embed` isteklerinin eşzamanlı çalıştırılması **ölçülmedi**. 0.40.4'teki eski 24 parçalık ölçüm [Gömme Modeli Eğitimi](/rag/gomme-egitimi/) sayfasında durur ve bu karşılaştırmanın tabanı değildir; ayrımın kriteri [Kapsam Haritası](/kaynaklar/kapsam-haritasi/) sayfasında.
- `OLLAMA_FLASH_ATTENTION` ve `OLLAMA_KV_CACHE_TYPE` (varsayılan `f16`) etkisi bu makinede **ölçülmedi** — CPU'da ikisinin de kazancı sınırlı beklenir, ama bu bir beklenti, ölçüm değil.
- Yapılandırılmış çıktı (`format`) ve araç çağırmanın (`tools`) ek maliyeti **ölçülmedi**; araç çağırma davranışı ve gecikmesi ayrı bir bölüm olarak planlanıyor.
- Windows dışı işletim sistemlerinde isim çözümleme gideri **ölçülmedi**. Bu sayfadaki 2,03 sn'lik `localhost` gideri bir Windows görgüsüdür; Linux/macOS'ta aynı testin tekrarı sitede yok.

## Kaynaklar ve ileri okuma

- [Ollama sıklıkla sorulanlar](https://docs.ollama.com/faq) — ortam değişkenleri ve varsayılanlar: `OLLAMA_KEEP_ALIVE` (5 dk), `OLLAMA_MAX_LOADED_MODELS` (GPU sayısının 3 katı, CPU'da 3), `OLLAMA_NUM_PARALLEL` (varsayılan 1), `OLLAMA_CONTEXT_LENGTH` (varsayılan 4096 token), `OLLAMA_KV_CACHE_TYPE` (varsayılan `f16`). Son doğrulama 2026-10.
- [Ollama sohbet API'si](https://docs.ollama.com/api/chat) — `total_duration`, `load_duration`, `prompt_eval_duration`, `eval_duration`, `prompt_eval_cached_count` alanlarının tanımı; bu sayfanın tüm faz ayrımı bu alanlardan geldi.
- [Ollama bellek konuları (issue #17351)](https://github.com/ollama/ollama/issues/17351) — prompt önbellek boyutunun yapılandırılabilir olmaması; 2026-07 tarihli, açık.
- [llama.cpp ölçüm alanları](https://github.com/ggml-org/llama.cpp) — günlükteki `print_timing` satırlarının ("prompt eval time", "eval time") kaynağı; CPU'da iş parçacığı ölçeklemesinin asıl adresi.
- [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) — bu sayfanın faz tablosuna bir satır daha: `num_predict=1` + `top_logprobs=20` isteği taze (~100 tokenlık) istemle 2,1–2,9 sn sürüyor, aynı istem önbelleği sıcakken 0,10–0,15 sn'ye düşüyor.
- [Eşzamanlılık](/kullanim/eszamanlilik/) — bu sayfanın tüm süreleri tek istek içindir; aynı makinede 1/2/4 ve 8 isteğin aynı anda salıverildiği dört koşum, sıralı kuyruğun merdiven kanıtı, `=2` ayarında ikişerli çiftin kuyrukla karışımı ve `OLLAMA_NUM_PARALLEL=4` açıldığında iş paylaşımının imzası orada.
