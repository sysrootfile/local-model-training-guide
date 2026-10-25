---
title: "Tekrarlanabilirlik: Aynı Soruyu On Kez Sormak"
description: "Aynı istem, aynı model, aynı makine: sıcaklık sıfırda ve tohum sabitken cevap birebir aynı mı, num_predict gönderilmezse tavan kaç token, JSON şeması hangi alan adlarını zorluyor, scikit-learn'de tohum varyansı ne kadar — 2026-10-17 kaydından ölçülmüş sayılar."
dogrulama: 2026-10-19
---

"Repeatable" kelimesi iki ayrı iddia taşır: **aynı isteği tekrar gönderirsem aynı cevabı alır mıyım** ve **bugünkü sonucumu yarınki koşumla karşılaştırabilir miyim**. İkincisi birincisine bağlı, ama ikisi aynı şey değil. Bu sayfa dört soruyu bu makinede gerçekten koşarak cevaplıyor: Ollama'da sıcaklık ve tohumun fiili etkisi, `num_predict` gönderilmediğinde yürürlükteki tavan, `format` alanının gerçekten neyi zorladığı, ve bir kontrol kolu olarak scikit-learn'de tohum varyansının büyüklüğü.

:::note[Künye: tek koşum, tek makine]
Betik: `ornekler/tekrarlanabilirlik/tekrar.py`. Kayıt: `ornekler/tekrarlanabilirlik/cikti/tekrar-kaydi.txt`.
Koşum aralığı **2026-10-17 11:04:59 → 11:14:18** (9 dakika 19 saniye), Ollama 0.40.4 (makine 2026-10-19'da 0.40.6; bu sayfadaki sayılar o sürümde yeniden ölçülmedi), model `qwen2.5:3b-instruct-q4_K_M`, adres `http://127.0.0.1:11434`. Ollama'ya **123 istek** (3 tanesi tavan araması, 120 tanesi onar tekrarlı 12 hücre), scikit-learn tarafında 30 eğitim-doğruluk çifti. Bu makinede model CPU'da çalışıyor; bu satır yeni bir ölçüm değil, [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasındaki `ollama ps` "100% CPU" kaydından aktarıldı. Koşum boyunca başka Ollama isteği gönderilmedi.
Aşağıdaki her sayı o dosyadan alındı; alıntıladığım her hücrenin etiketi (A1, D3, B2 gibi) kayıtta da aynı.
:::

## Aynı İstem, Sıcaklık Sıfır, Tohum Yok: Kısa Cevap Birebir Aynı

Kapalı uçlu bir soru ve tek kelime istemi: "Marmaray hangi yılında hizmete açıldı? Yanıtınız tek kelime olsun." On tekrar, altı ayar kombinasyonu. Her cevap 5 token; farklar metnin kendisinde.

| Hücre | Ayar | 10 tekrarda benzersiz cevap | En sık cevabın oranı | Üretilen yıllar |
| --- | --- | --- | --- | --- |
| `A1` | T=0, tohum yok | 1 | 10/10 | 2020 |
| `A2` | T=0, tohum 1234 | 1 | 10/10 | 2020 |
| `A3` | T=0,8, tohum yok | 5 | 3/10 | 2021 üç, 2020 üç, 2011 iki, 2013 bir, 2015 bir |
| `A4` | T=0,8, tohum 1234 | 1 | 10/10 | 2020 |
| `A5` | A4'ün ayrı diz tekrarı | 1 | 10/10 | 2020 |
| `A6` | T=0,8, tohum 9999 | 1 | 10/10 | 2020 |

Üç şey ölçüldü:

- **Sıcaklık sıfır, beş token'lık üretimde birebir aynılık verdi** — tohum gönderilmeden bile (A1, A2). [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) sayfasında "ölçülmedi" diye bıraktığım iddia buydu; kısa çıktıda bu makinede tutuyor.
- **Tohum, sıfır olmayan sıcaklıkta aynılığı geri getiriyor**: A3 örnekledikçe beş farklı yıla dağıldı; A4 ve A5 aynı tohumla iki ayrı diz halinde koşuldu ve yirmi isteğin yirmisi de aynı dizgiyi verdi.
- **Tohumun *değeri* cevabı belirlemiyor**: 1234 ve 9999 (A4, A6) aynı cevaba düştü. Tohum örnekleme zincirini sabitler; hangi zincirin hangi cevaba düşeceği sabitlenmez. İki farklı tohumun aynı sonucu vermesi sürpriz değil, dağılımın A3'te görüldüğü gibi tepeli olmasının doğal sonucu.

Bir uyarı: bu tablo **doğruluğu ölçmedi.** On istekte beş farklı yıl çıktı; hangisinin doğru olduğunu bu kafes test etmiyor. Ölçtüğümüz şey tekrarlanabilirlik.

## Açık Uçlu İstem: Tohum 68 Token'lık Cevabı da Sabitliyor

Aynı kafesin ikinci kolu, serbest üretim isteyen bir istem: "Kadıköy'de bir kahve dükkânı için üç slogan öner." `num_predict` 200.

| Hücre | Ayar | Benzersiz | En sık | Çıktı token (ort.) | Karakter aralığı | Duvar (10 istek) |
| --- | --- | --- | --- | --- | --- | --- |
| `C1` | T=0,8, tohum yok | 10/10 | 1/10 | 54,7 | 91-142 | 37,0 sn |
| `C2` | T=0,8, tohum 1234 | 1/10 | 10/10 | 68,0 | 146 | 45,4 sn |
| `C3` | C2'nin ayrı diz tekrarı | 1/10 | 10/10 | 68,0 | 146 | 45,0 sn |

Tohum burada da çalıştı: 68 token'lık, 146 karakterlik bir üretim on isteğin onunda karakter karakter aynı; ikinci diz (C3) de aynı imzayı verdi. Tohumsuz kolda (C1) ise **on cevabın biri diğer dokuzundan farklı** — tek tekrar bile çıkmadı, ortalama uzunluk 54,7 token'a otururken.

:::note[Örneklem gürültüsü dilin kendisini de vuruyor]
C1'in dördüncü isteğinde üç maddeden biri Türkçe değil, **Çince** geldi ("每一杯都是对生活的敬意"). İstem tamamen Türkçe, model aynı, ayar aynı; on denemenin birinde dil kaymış. Bu, "yanıt hep istemin diliyle gelir" varsayımının sıcaklık 0,8'de tutmadığının bu makinedeki ölçümü. Sıcaklık sıfırda veya tohum sabitken böyle bir kayma bu kafeste görülmedi — ama bu, onu engelleyen bir garanti değil, yalnızca gözlem.
:::

## `num_predict` Göndermezseniz Tavan Ne: 128 Değil

[Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) sayfasında iki Ollama belgesinin aynı parametre için iki farklı varsayılan yazdığını görmüştük: `docs.ollama.com` **-1**, readthedocs aynası **128**. Kapama yöntemi olarak "bir istek atın" demiştim. Koşumda `options = {temperature: 0}` gönderildi, `num_predict` **hiç gönderilmedi**, uzun yazması istenen aynı istem üç kez yinelendi:

```text
K0.1: duvar  80,58 sn | çıktı token 1060 | bitis stop
K0.2: duvar 111,88 sn | çıktı token 1460 | bitis stop
K0.3: duvar 111,79 sn | çıktı token 1460 | bitis stop
```

Sonuç iki yönlü:

1. **128 yürürlükte değil.** 1060 ve 1460 token üretildi, üçünde de `done_reason: stop` var, yani kesme değil modelin kendi bitişi. Bu sürümde (Ollama 0.40.4) `num_predict` göndermemek üretimi fiilen durdurmuyor; üretim, model EOS üretilene kadar sürüyor. Uygulamanızda bir tavan istiyorsanız **siz göndermelisiniz.**
## `format`: "json" ile Şemanın Farkı Ölçüldü

Aynı soru, aynı sıcaklık, tohum yok; tek değişen istekteki `format` alanı. Şema iki alan istiyor: `yil` (sayı) ve `gerekce` (metin). Onar tekrar:

| Hücre | `format` | `num_predict` | Ayrıştırılabilen | İkinci alanın adı kaç çeşitli çıktı | `yil` değerleri |
| --- | --- | --- | --- | --- | --- |
| `D1` | `"json"` | 300 | 10/10 | **4** (`gercekce`, `gereken`, `gereke`, `gerekce`) | 2011, 2020, 2022, 2023 |
| `D2` | JSON şeması | 300 | 10/10 | **1** (`gerekce`) | 2017, 2019, 2020, 2022 |
| `D3` | JSON şeması | 48 | **2/10** | 8 istek cümlenin ortasında kesildi | 2022 ve kesikler |

Bu üç satır, [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) sayfasında çalıştırılmadan bırakılmış iki iddiayı sayıyla kapatıyor:

- **`"json"` yalnızca geçerli JSON garanti ediyor, sizin alanlarınızı etmiyor.** On isteğin onu ayrıştırıldı; ama model ikinci alanı dört farklı adla yazdı. `veri["gerekce"]` ile okumaya çalışan kod, on cevabın dördünde `KeyError` alırdı. Şema (D2) alan adlarını tam tuttu: on/on `gerekce` + `yil`.
- **Şema biçimi garanti eder, içeriği garanti etmez.** D2'de alan adları kusursuzken `yil` değeri on istekte dört farklı yıla dağıldı, üstelik D1'den tamamen başka bir dört yıla. Biçim denetimi (şema) ile olgu denetimi (doğrulama katmanı) ayrı işler; şema ikincisini yapmıyor.
- **Token tavanı JSON'u kırar.** D3'te tek değişiklik `num_predict`'i 48'e indirmekti: on isteğin sekizi `done_reason: length` ile kesildi ve kesik JSON `json.loads`'tan geçmedi. Sunucu tarafında şema zorlaması, çıktıyı geçersiz kılan bu kesmeyi **engellemiyor**; HTTP 200, alanlar doğru, cevap ayrıştırılamıyor. Yapılandırılmış çıktı istiyorsanız tavanı şemanın gerçek uzunluğuna göre açın ve `done_reason` alanını kontrol edin.

:::caution[Kesik JSON sessiz bir arızadır]
D3'ün sekiz bozuk cevabının hiçbirinde hata yoktu: durum kodu 200, içerik alanı dolu, `done_reason` kesme diyor. Ayırt etmenin tek yolu `done_reason` alanına bakmak — ya da ayrıştırmayı deneyip düşünce "cevap eksik" kolunu çalıştırmak. [Ajan Ölçümü](/ajan/ajan-olcumu/) sayfasındaki kesik cevap ve [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/) kaydındaki `length` bitişleri aynı arızanın başka bağlamlardaki hâli.
:::

## Kontrol Kolu: scikit-learn'de Tohum Varyansı

Üretim tarafındaki oynama tek başına "doğal gürültü mü" sorusunu cevaplamıyor. Aynı kafesin ikinci kolunda, deterministik sayılan klasik makine öğrenmesi akışında (breast-cancer verisi, 569 satır, %20 katmanlı bölme, 114 test satırı) beş tohumla 30 eğitim-doğruluk çifti koşuldu. Üç senaryo: neyin tohumu oynatıldığı bilinçli olarak değiştirildi.

| Kol | Ne değişti | Rastgele orman doğruluğu | Aralık | Lojistik regresyon | Aralık |
| --- | --- | --- | --- | --- | --- |
| `B1` | bölme + model tohumu birlikte | 0,9474-0,9825 | **0,0351** | 0,9649-0,9912 | 0,0263 |
| `B2` | bölme sabit (42), yalnız model tohumu | 0,9474-0,9561 | **0,0088** | 0,9825 (beşte beş aynı) | **0,0000** |
| `B3` | model tohumu sabit (42), yalnız bölme | 0,9386-0,9825 | **0,0439** | 0,9649-0,9912 | 0,0263 |

Ölçülen sıralama net: **test bölmesinin seçimi, model tohumundan daha çok oynatıyor** (B3'ün açığı 0,0439, B2'ninki 0,0088). B2'deki 0,0088 tam olarak bir test örneğine denk: 1/114 = 0,00877. Lojistik regresyon ise bölme sabitken beş tohumda dört ondalık basamakla aynı kaldı (0,9825); bu veride model tohumu onu hiç oynatmıyor — nitekim B1 ve B3'un lojistik satırları birebir aynı.

Buradaki ders LLM tarafına taşınıyor: **kaynağı bilinmeyen bir oynama, boyutu bilinen bir oynamaya dönüşür.** Tohum varyansının klasik bir makine öğrenmesi akışında bile 0,04 doğruluğa çıkabildiği bir ortamda, sıcaklığı açıkça sabitlenmemiş bir dil modelinin iki koşumunu karşılaştırmak ölçüm sayılmaz. [Hiperparametreler](/llm/hiperparametreler/) sayfasının "tek koşuya güvenmeyin" maddesi bu hesabın gerekçesini, [Benchmarklar](/degerlendirme/benchmarklar/) sayfasının beşinci maddesi de raporlama tarafını anlatıyor.

## Bu Ölçüm Neyi Göstermiyor

:::caution[Sınırlar — sayıların okuma biçimi]
- **Tek makine, tek model, tek sürüm.** Ollama 0.40.4 ve `qwen2.5:3b-instruct-q4_K_M`, CPU'da. GPU'lu bir kurulumda, toplama (batching) gerçekten devreye girdiğinde aynılık davranışı değişebilir; burada test edilmedi.
- **Kısa çıktıda aynılık, uzun çıktıda aynısızlık gözlemidir; kural değildir.** K0'daki 1060/1460 farkının nedenini ayırt eden bir kol kurmadım. "Sıcaklık 0 + sabit istem = garanti aynı çıktı" iddiası bu sayfada **doğrulanmadı**, yalnızca 5 token'lık ve 68 token'lık iki durumda gözlendi.
- **On tekrar küçük bir örneklem.** A3'teki "5 benzersiz" oranı dağılımın doğru ölçüsü değil; kesinlik aralığı hesaplanmadı (ÖLÇÜLMEDİ).
- **Doğruluk ölçülmedi.** Yılların hangisi doğru, oradaki tartışma konusu değil; bu sayfa sadece aynı soruya kaç farklı cevap verildiğini saydı.
- **Scikit-learn kolu tek bir veri setinde.** 569 satır, 30 özellik, tek bölme oranı; başka bir veri setinde sıralama değişebilir.
:::

## Pratik Karar Listesi

- Karşılaştırma/ölçüm yapıyorsanız: `temperature: 0`, açık `num_predict` ve sabit `seed` birlikte. Uzun üretimde sıcaklık sıfır tek başına aynılığı korumadı (K0), `num_predict` gönderilmeyince üretim 1460 token'a kadar çıktı; bu üçlü, ölçüm sayfalarının hepsinde birlikte kullanılıyor.
- Uygulamanız aynı soruyu tekrar tekrar soruyor ve cevap çeşitliliği istemiyorsanız: tohum gönderin. İstem bir token bile değişirse tohumun bir şeyi sabitlemediğini unutmayın; RAG'da bağlam parçası değişiyorsa karşılaştırma yapmıyorsunuz demektir.
- Yapılandırılmış çıktı istiyorsanız: `"json"` değil **şema** gönderin, tavanı şemanın gerçek uzunluğuna göre açın, `done_reason` kontrol edin ve alan değerlerini ayrıca doğrulayın.
- Tek sayfalık bir iyileşme iddiası için: en az beş tekrar, mümkünse iki ayrı diz. Bu kafeste A4/A5 ve C2/C3 çiftleri bunun için kuruldu; aynı ayarla ikinci dizin ilk dizle birebir aynı imzayı vermesi, tekrarlanabilirlik kanıtının "bir diz" değil "iki diz" olması gerektiğini gösteriyor.
- Kaynağı belirsiz oynama şüphesinde: oynayan şeyin boyutunu ölçün. B2/B3 ayrımı bunun klasik makine öğrenmesindeki hâli.

## Kendi Makinenizde Koşun

Kafes tek dosya; `--duman` iki tekrarlı hızlı doğrulama, onar tekrarlı tam koşum ~9 dakika (Ollama kolu CPU'da yavaşsa daha uzun sürer).

```bash
cd ornekler/tekrarlanabilirlik
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol a --duman > cikti/duman.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol hepsi > cikti/tekrar-kaydi.txt 2>&1
```

Koşum bittiği ana kadar başka hiçbir Ollama isteği göndermeyin — sohbet arayüzü, editör eklentisi, ikinci bir betik. Hücre eşleşmeleri (A4/A5 gibi iki ayrı diz) bu kurala bağlı. Betik yalnızca `127.0.0.1:11434` ile konuşur; model adını, istemleri ve `--kol` seçimini değiştirerek kendi sorularınızla aynı tabloyu kurabilirsiniz.

## Kaynaklar ve ileri okuma

- `ornekler/tekrarlanabilirlik/cikti/tekrar-kaydi.txt` — bu sayfadaki tüm sayıların ham kaydı (123 istek, 30 sklearn koşumu, 2026-10-17 11:04-11:14).
- [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) — sıcaklık, top-k, top-p, min-p, tohum ve `format` alanlarının belgeye dayalı açıklaması; bu sayfa onun çalıştırılmadan bıraktığı üç iddiayı ölçüyor.
- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — aynı makinede ölçülmüş faz süreleri, `num_ctx` kırpması ve iki koşum arasındaki %10'luk hız oynaması.
- [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) — aynılığı metin yerine **sayılarda** arayan koşum: sıcaklık sıfırda logprobitelerin bit bit aynı döndüğü, ama model `keep_alive: 0` ile düşürülüp yeniden yüklenince aynı tokenların olasılıklarının 0,2286 kayabildiği ölçüm.
- [Ajan Ölçümü](/ajan/ajan-olcumu/) ile [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/) — `done_reason: length` ile kesilen cevapların gerçek kayıtları.
- [Hiperparametreler](/llm/hiperparametreler/) — tohum varyansının ince ayar üzerinde klasik referansı (Dodge vd., arXiv:2002.06305).
- [Klasik Makine Öğrenmesi: İlk Model](/klasik-ml/ilk-model/) — `random_state` kullanımının örnek akışı; B kolu aynı veri ve boru hattı üzerinde kuruldu.
- [Gömme Modeli Eğitmek](/rag/gomme-egitimi/) — aynı tohum sorusunun **eğitim** tarafı: iki farklı tohumla koşulan 240 adımlık iki kolda hit@1 ve MRR birebir aynı kaldı, adım süresi yalnız 1,33 vs 1,35 sn oynadı.

