---
title: "Kapsam Haritası: Bu Rehberde Neyi Ölçtük, Neyi Ölçmedik"
description: "Rehberin hangi eksenlerde hangi kanıt kademesinde durduğunu gösteren harita. Ölçüm kafeslerinin birim listesi, on kafesin neyi ölçtüğü, bilerek kapsam dışı bırakılan konular ve yeni bir ölçüm sayfasına girmeden önce kabul edilen koşum kuralları."
dogrulama: 2026-10-26
---

Bu rehberin bir sorunu var ve adı eksiklik değil: **her satır aynı kesinlikle görünüyor.** "LoRA'da
taban model bellekte durur" cümlesi de, "ön-yükleme 43,9-45,9 tok/sn" cümlesi de, "CPU'da flash
attention'ın kazancı sınırlı beklenir" cümlesi de aynı yazı tipinde, aynı sesle duruyor. Oysa
ikincisi bir kafesten, üçüncüsü bir beklentiden geldi.

Bu sayfa o sesi ayıran harita. Bir ölçüm kolunu **koşmadan önce** üç şeyi sabitliyor: hangi eksende
olduğumuz, hangi birimi ölçtüğümüz ve hangi kurala uyduğumuz. Sayfanın altındaki kabul kuralları
bugün bir karar turundan çıktı; yani burası hem envanter hem sözleşme.

## Kanıt Kademesi: Dört Basamak

Sitedeki her sayıyı dört basamaktan birine yazıyoruz. Basamak, sayfanın **iddia gücü**, doğruluk
ölçüsü değil.

| Kademe | Ne demek | Sitede nasıl görünür | Örnek |
| --- | --- | --- | --- |
| **0 — Beklenti** | Koşum yapılmadı, nedeni biliniyor, tahmin açıkça tahmin. | "beklenir", "**ölçülmedi**" | `OLLAMA_FLASH_ATTENTION` ve `OLLAMA_KV_CACHE_TYPE` kazancı ([Hız ve Maliyet](/kullanim/hiz-ve-maliyet/)) |
| **1 — Yukarı akış rakamı** | Üreticinin/belgenin verdiği sayı, bizim makinede doğrulanmamış. | "Ollama'nın varsayılanı", "2026 itibarıyla", son doğrulama tarihi | `OLLAMA_NUM_PARALLEL` varsayılanı 1, `OLLAMA_KEEP_ALIVE` 5 dk |
| **2 — Ölçüldü, tek gözlem** | Bu makinede gerçekten koşuldu; tekrarı yok. | "tek bir gözlem", "bir kez ölçüldü" | `bge-m3` soğuk yükleme 11,92 sn (birinci turda bir kez) |
| **3 — Ölçüldü ve tekrarlandı** | En az iki koşum ya birden çok tekrar; bant olarak verilir. | aralık, "iki tur", "5 tekrar" | karakter/token oranı 2,99 (iki turda aynı), çözme 13,9-14,8 tok/sn |

:::caution[Kademe 2 iken kademe 3 dili kullanmak]
En sık düşülen tuzak bu: tek gözlemi kurala çevirmek. "Soğuk yükleme 9,15 sn" tek bir sayıydı; aynı
makinede yeniden yüklemeler 3,10-3,12 sn çıktı. Sayfa bundan sonra "soğuk çağrı sıcak çağrıdan birkaç
saniye pahalıdır" diyor, sabit sayı demiyor. Bir sayfa kademe 3'e çıkmadan kural cümlesi kuramaz;
kurarsa, o cümle kademe 0'a düşer.
:::

:::note[Kademe ayrımı bizim yazım kuralımız]
Bu dört basamak literatürün standart bir sınıflaması değil, bu sitenin kendi alışkanlığı. O yüzden
başka bir kaynağın "doğrulanmış" etiketiyle karşılaştırılamaz. Karşılaştırılabilir olan tek şey
aynı sitede iki ölçümün yan yana durması.
:::

## Ölçen On Kafes

Sayfalar iddia eder, kafesler ölçer. `ornekler/` altında 14 klasör var; ölçüm üreten onucusu ve
birimleri:

| Kafes | Ne ölçtü | Birim | Ollama'ya bağlanır mı |
| --- | --- | --- | --- |
| `cikarim-olcu` | Gecikmenin dört fazı, `num_ctx` bellek basamakları, `num_thread`, TTFT, isim çözümleme gideri | sn, tok/sn, token, GB | evet, `127.0.0.1:11434` |
| `eszamanli-olcu` | Bariyerle aynı anda salıverilen 1/2/4 isteğin dalga süreleri ve kuyruk merdiveni | sn, p50, p95, tok/sn, bekleyen istek sayısı | evet |
| `tekrarlanabilirlik` | On iki hücre × on tekrar: aynı istek kaç farklı cevap üretiyor | tekrar sayısı, değişen token | evet |
| `eminlik-olcu` | Logprob'un hangi uçta hangi koşulla döndüğü, güven-isabet ilişkisi | logprob, doğru/yanlış sayımı | evet |
| `enjeksiyon-deni` | İki kanal × üç savunma, 31 hücre: sızıntı oldu mu | hücre başına sızıntı sayısı | evet |
| `ajan-dongusu` | Ajan turu, araç çağrısı kataloğunun token gideri | tur, token, sn | evet |
| `yerel-rag` | Getirim kalitesi ve eşik bandı (Örnek 5) | hit@k, MRR, sn | evet |
| `viki-rag` | Canlı korpusla indeksleme ve hibrit arama (Örnek 6) | hit@k, MRR, sn, sıra/sıra başına ms | evet |
| `gomme-egitimi` | CPU'da dokuz gerçek eğitim koşumu, batch tavanı | kayıp, hit@1, MRR, ayrışma, sn, ms | evet (yeniden gömme için) |
| `lisans-ve-gizlilik` | Yerel modellerin lisans metinleri ve kişisel veri taraması | bayt, satır, eşleşme sayısı | evet |

Kalan dört klasör (`klasik-ml`, `veri-temizleme`, `turkce-asistan`, `gorsel-lora`) proje
betiği; ölçüm değil üretim yapıyor. `turkce-asistan` ve `gorsel-lora`'nın GPU'da çalışan adımları
**bu makinede çalıştırılmadı**, yalnız CPU'da koşabilen kısımlarının gerçek çıktıları sayfalarında.

## Sayının Kaynağı Tek Yer

Aynı birimi iki sayfa söylüyorsa biri yanlış, ikisi de kaynaktır. Sitede her birimin tek bir
doğrulmuş adresi var:

| Birim | Taşıyan sayfa |
| --- | --- |
| çıkarım saniyeleri, tok/sn, GB, karakter/token | [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) |
| eşzamanlı istek başına duvar, dalga süresi, kuyruk bekleme | [Eşzamanlılık](/kullanim/eszamanlilik/) |
| `/api/embed`-de tek istekte 24 parça göndermenin eski süresi (17 Ekim, 0.40.4) | [Gömme Modeli Eğitimi](/rag/gomme-egitimi/) |
| `/api/embed` toplu gönderme karşılaştırması: tek istek vs 24 ayrı istek (20 Ekim, 0.40.6) | [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — Gömme Modeli Eğitimi bu karşılaştırmaya yalnız bağlanır |
| hit@k, MRR, eşik bandı | [Yerel RAG](/ornekler/yerel-rag/), [Viki RAG](/ornekler/viki-rag/), [Gömme Modeli Eğitimi](/rag/gomme-egitimi/) |
| tekrarlanabilirlik, tohum varyansı | [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) |
| logprob, eminlik, kalibrasyon | [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) |
| sızıntı kanalı, savunma etkinliği | [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/) |
| lisans metni, bayt/satır, kişisel veri | [Lisans ve Model Kartı](/kullanim/lisans-ve-model-karti/) |
| "bu iddia ne zaman gözden geçirildi" | [Doğrulama Mekaniği](/kaynaklar/dogrulama-mekanizmasi/) |
| "hangi istasyon bu makinede gerçekten koştu, kaydı hangi dosyada" | [Uçtan Uca Tek Hat](/ornekler/ucdan-uca/) |
| "hangi sayfanın sayısı hangi Ollama sürümünden geldi" | bu sayfa, **Ölçümün Sunucu Sürümü** başlığı |

:::tip[Başka bir yerde sayı gördüyseniz]
Bir sayfa bu tablodaki adreslerden birine bağlanmıyorsa, o sayı ya kademe 0-1'dir ya da bir
kopyalama. İkinci durum bu sitede oldu ve adres değişince ölçülerek düzeltildi: `localhost` yerine
`127.0.0.1` geçişi, aynı makinede indeks sürelerini 529,3 sn'den 253,0 sn'ye indirdi.
:::

## Ölçümün Sunucu Sürümü: Defter

Ollama'nın sürümü de ölçümün bir parçası. Bu makinede ölçüm kolları **üç farklı sunucu sürümünde**
alındı, ve sitenin düzyazısında o üç sürümün adı iç içe geçiyor. Aşağıdaki sayım bu bölüm yazılmadan
**önceki** anlık görüntüdür (19 Ekim, tek grep koşumu): `0.40.4` on altı, `0.40.5` üç, `0.40.6` on dört
kez geçiyordu. **Bu tablo kendini de saydı:** aynı tarama bölüm yazıldıktan sonra `0.40.4` için 29,
`0.40.5` için 6, `0.40.6` için 18 geçiş verdi — artışın tamamı bu defterin kendi satırları. Sayıları
karşılaştıran bir tablo, karşılaştırdığı kümenin içine yazılıyor; [Lisans ve Model Kartı](/kullanim/lisans-ve-model-karti/)
sayfasının "denetimin sonucu denetlenen kümenin içine girdi" kusurunun ikinci örneği budur.

**Ve üçüncü ölçüm, desenin kendi kusurunu da çıkardı.** Akşamüstü kalemlerin kabul kriterleri ve künye
düzeltmesi yazıldıktan sonra aynı tarama yeniden koşuldu (23:07): kaçışsız desen `0.40.4` için 31,
`0.40.5` için 7, `0.40.6` için 20 geçiş veriyor; **sabit-dizi deseni** (`grep -F`) ise 30 / 6 / 20.
Farkın kaynağı tek satır — bu bölümün kendi altında, üç sürümün **virgülle** yazılmış hâlleri
(`0,40,4`, `0,40,5`) kaçışsız noktayı joker sanıp eşleşiyor. Bugün için fark bu kadar; **öğlen alınan
29/6/18 sayısının da şişkin olup olmadığı kayıtlı değil** — o tarama ile bu virgüllü cümlenin
yazımı hangi sırayla olduğu bir logda tutulmadı, o yüzden eski sayılar olduğu gibi duruyor ve
"Düzeltildi" denmiyor. Bu cümlenin kendisi de aynı taramanın içine yazıldı: yukarıdaki 31/7/20 artık
bir **önceki** anlık görüntüdür, güncel olan tek şey komutun kendisi. Yukarıdaki "desen nokta
biçimiydi" itirafı ile aynı kusurun iki yüzü: bir desen hem bulamaz hem uydurur.

**Ama bu sayılar sürüm künyesi değil, sözcük sayısıdır:** `0.40.6` geçen on dört geçişin neredeyse
tamamı bir ölçüm değil bir **itiraftır** ("makine 19 Ekim'de 0.40.6; bu sayfadaki sayılar o sürümde
yeniden ölçülmedi"); tek istisna [Eşzamanlılık](/kullanim/eszamanlilik/) sayfasının kendi künyesi, o
zaten aşağıdaki tabloda 0.40.6 satırı olarak duruyor. Aşağıdaki defter o ikisini ayıran tek yer — hangi
sayfanın sayısı hangi sunucunun sürümünden geldi:

| Ölçümü taşıyan sayfa | Ölçüm sürümü | Koşum penceresi ve kayıt |
| --- | --- | --- |
| [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) | 0.40.4 (gövde) / **0.40.6** ("Toplu gömme" bölümü) | 16 Ekim 01:21-01:39, `hiz-kaydi-127.txt`; 20 Ekim 11:45-11:46, `gomme-egitimi/cikti/kol-e.txt` |
| [Ajan Ölçümü](/ajan/ajan-olcumu/) | 0.40.4 | 16 Ekim 02:11-02:18, `ajan-kaydi.txt` |
| [Örnek 7: Ajan Döngüsü](/ornekler/ajan-dongusu/) | 0.40.4 | aynı kaydın ikinci sayfası |
| [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/) | 0.40.4 | 16 Ekim 11:36:32-12:12:48, `enjeksiyon-kaydi.txt` |
| [Örnek 8: Prompt Enjeksiyonu](/ornekler/enjeksiyon-deni/) | 0.40.4 | aynı kaydın ikinci sayfası |
| [Örnek 5: Yerel RAG](/ornekler/yerel-rag/) | 0.40.4 | 16 Ekim, `calistirma-kaydi-127.txt` |
| [Örnek 6: Viki RAG](/ornekler/viki-rag/) | 0.40.4 | 16 Ekim, `calistirma-kaydi-127.txt` |
| [RAG Değerlendirme](/rag/rag-degerlendirme/) | 0.40.4 | 15 Ekim, `olc-kaydi.txt` (`localhost` dönemi) |
| [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) | 0.40.4 | 17 Ekim 11:04:59-11:14:18, 123 istek |
| [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) | 0.40.4 | **aktarma künye:** tavan davranışı K0 kolundan, yani yukarıdaki kayıttan okundu |
| [Lisans ve Model Kartı](/kullanim/lisans-ve-model-karti/) | 0.40.4 | 17 Ekim 14:21:44-14:22:38 |
| [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) | **0.40.5** | 17 Ekim 22:09:25-23:13:16, dört ayrı kayıt |
| [Eşzamanlılık](/kullanim/eszamanlilik/) | **0.40.6** (A-D koşumları) / **0.40.11** (E koşumu, `=3`) | 19 Ekim, üç sunucu ayarı; 20 Ekim K = 8; 26 Ekim 00:29-00:32, `eszamanli-kaydi-4.txt` |
| [Gömme Modeli Eğitimi](/rag/gomme-egitimi/) | 0.40.4 (A-D) | sürüm **kayda değil kafes README'sine yazılmış** (`ornekler/gomme-egitimi/README.md`, makine satırı); `kol-a.txt` 17 Ekim 15:46:48'de başlıyor ama logda künye satırı yok — betik üretmiyordu. 20 Ekim'deki E kolu `kol-e.txt` başında `Ollama sürümü: 0.40.6` satırını yazdı |

Üç şey bu defterin kendisi için söylenmesi gereken:

- **Sürüm bir metrik değil, provenans.** "Bu sayfanın sayısı hangi sunucudan geldi" sorusunun tek
  yanıtı burası; fakat birincil kayıt hâlâ her sayfanın kendi künye cümlesidir. Sayfa yeniden koşarsa
  önce o cümle değişir, sonra bu tablo — ikisi ayrıştığında hatalı olan **bu tablodur**, çünkü tablo
  bir özet.
- **Defterin satırları ölçüm değildir; tarama sonucudur.** 14 satır, 19 Ekim'de diskte tek bir grep
  koşumuyla listelendi (kademe 2 — tek ölçüm). Aynı taramanın bir önceki hali yanlıştı: desene disk
  yolu (`ornekler/ad`) ile sayfa bağlantısı biçimi (`/ad/`) **birlikte** girince `tekrarlanabilirlik`
  13 sayfada görünüyordu; deseni yalnız disk yoluna indirince gerçek sayı 2 çıktı. Sayım deseni,
  sayımın sonucudur.
- **Son satır bu tabloyu yazan taramayı da düzeltti.** İlk halinde `gomme-egitimi` satırı
  **ÖLÇÜLMEDİ** idi, gerekçem "sürüm hiçbir yerde yok"tu. Yanlışmış: sürüm kafesin kendi
  `README.md`sinin makine satırında yazıyor. İki sebebim vardı ve ikisi de tarama desenimin
  kusuruydu: (1) tarama yalnız `src/content/docs`'ta dolaştı, `ornekler/*/README.md` dosyalarına
  hiç bakmadı; (2) desen nokta biçimiydi (`0\.40\.[0-9]`), o README'ler ise üç sürümü **virgülle**
  yazmış (`0,40,4`, `0,40,5`). Beş kafes README'sinde sürüm künyesi var; üçü virgül biçiminde. Yani
  "diskte yok" hüküm vermeden önce hem tarama alanı hem biçim deseni sorgulanmalı — yoklama
  yokluğun kendisi bir bulgu değil, taramanın sınırıdır.
- **Eksik olan künye satırı, sürümün kendisi değil.** `gomme_egit.py` sunucu sürümünü kayda
  yazmıyordu; 19 Ekim'de betiğe `/api/version` okuması eklendi ve artık `Ollama sürümü: …` satırı
  `kol-a.txt`nin içine düşecek (kod tarafı, koşumsuz; bu üç satırın kanıtı bir sonraki gerçek
  koşumda yazılacak). Geçmiş bir sayıyı doğrulamak için koşum yeniden alınmaz — 17 Ekim'in sürümü
  README'de olduğu gibi duruyor.

:::note[Doğrulama Mekaniği neden bu tabloda yok]
[Doğrulama Mekaniği](/kaynaklar/dogrulama-mekanizmasi/) üç sürümün adını da anıyor ama kendi ölçümü
Ollama'dan gelmiyor (build süreleri ve şema denemeleri). Sürümü **ölçmüyor**, sürümün bayatlamasını
anlatıyor.
:::

## Bilerek Ölçmediklerimiz

Bazı boşluklar tembellikten değil, karar çıkmadığı için duruyor. Açık olanlar:

- **Sunucu tarafı eşzamanlılık ara seviyesi dolduruldu; kalan uçlar açık.** `OLLAMA_NUM_PARALLEL`'ın **3** seviyesi 2026-10-26'da koşuldu (aşağıdaki kapanış paragrafı). Ölçümü koşan taraf o değişkeni yazamaz (kural 3); 19 Ekim'de makine sahibi =2 ve =4'ü, 26 Ekim sabahına karşı =3'ü yazdı ve sunucuyu her seferinde o yeniden başlattı. Varsayılan (=1), **=2**, **=3** ve =4 koşundu, [Eşzamanlılık](/kullanim/eszamanlilik/) sayfasında: varsayılan ayarla aynı anda salıverilen dört istek sıraya giriyor, `=2` ikişerli çift kurup taşanı bekletiyor, `=3` üçlü kilit adımı kurup tekini ~4,3 sn kaydırıyor, `=4`'de sıra kalkıyor ama iş paylaşılıyor (tek isteğin hızı 14,97 → 6,38 tok/sn). Bellek bedeli de **dört noktadan** ölçüldü ve **eşit adımlarla gitmiyor** (ilk ek yuva ≈233 MiB, sonraki üçü ≈145/144 MiB). 20 Ekim'de **K = 8** kolu da koşuldu (varsayılan sunucuda, `-np 1`). K = 5, 6, 7 ve **K > 8** hâlâ "ölçülmedi"; `=2` / `=3` / `=4` sunucularında K > yuva sayısının ikisi (K=2×2=4 üstü taşmalar ayrı ayrı) de öyle. `/api/embed` eşzamanlılığı da o sayfada "ölçülmedi" olarak duruyor — 24 parçanın tek istekte ölçülmüş olması ayrı bir şey, eşzamanlı gömme isteği ayrı. Seviye koşumlarının tarifi — sahibin yazacağı iki adım, günlükten okunacak iki satır, koşanın tek komutu — `ornekler/eszamanli-olcu/README.md` içindeki "Seviye 3" başlığında duruyor.
- **GPU.** Bu makinede hiçbir GPU ölçümü yok. Araştırma (2026-10-25, kademe 1): Ollama'nın Windows ROCm listesi RDNA3 kuşağını kapsıyor, Polaris (RX 570, gfx803) listede yok; ek GPU desteğinin belgelenmiş yolu Vulkan. Yerel gözlem (2026-10-25/26, kademe 2, sunucu 0.40.10/0.40.11): Vulkan backend kurulu ve etkin (`OLLAMA_VULKAN:true`), ama `llama-server --list-devices` **üç kütüphanede de (vulkan, cuda, rocm) 0xc0000005 ile çakılıyor** ve sunucu `inference compute id=cpu` ile açılıyor — yani bu sürümde RX 570 GPU'ya çıkamıyor; GPU gerektiren kod "çalıştırılmadı" etiketiyle duruyor. Keşif çökmesi sürüm hatası olabilir: ilerleyen Ollama sürümlerinde tek yoklamayla yeniden denenebilir.
- **Toplu (batch) gömme — sınır çizildi, karşılaştırma ölçüldü.** `/api/embed` çok girdi kabul ediyor;
  tek istekte 24 parça 17 Ekim'de (kol A), aynı 24 parçanın **tek istekte vs 24 ayrı istekte**
  karşılaştırması 20 Ekim'de (E kolu) ölçüldü. E'nin iki yanı, tekrar aralıkları ve hükmü
  [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasında; bu harita o saniyeleri tekrarlamıyor. Hâlâ
  ölçülmeyen: daha büyük bir parti (ör. 125 parça) tek istekte ve `/api/embed` eşzamanlılığı. Eski
  17 Ekim ölçümü E'nin tabanı değildir: farklı Ollama sürümü, farklı oturum, ısınma durumu ayrıca
  kayıtlı değil. RAG sayfalarındaki 125'lik indeks süreleri de **parça başına tek istek** atılarak ve
  başka bir korpusta alındı; hiçbiri E ile yan yana konup "batch şu kadar ucuz" cümlesi kuramaz.
- **Yapılandırılmış çıktı ve araç çağırmanın ek gecikmesi.** `format` ve `tools` davranışı ölçüldü,
  **maliyeti** ölçülmedi.
- **Windows dışı sistemler.** İstek başına 2,03 sn'lik isim çözümleme gideri bir Windows görgüsü;
  Linux/macOS tekrarı sitede yok.
- **Okuyucu davranışı.** Bayatlık banner'ının render edildiği ölçüldü, okuyucuyu daha dikkatli
  yaptığı ölçülmedi.
- **Kafes künyesi eksiği giderildi ve ilk kez görüldü, eski kayıt olduğu gibi duruyor.** `gomme-egitimi`'nin
  `/api/embed` kolu Ollama'ya istek atıyor ama sürümü kayda yazmıyordu; yukarıdaki "Eksik olan künye
  satırı" maddesi betiğe eklenen `/api/version` okumasını ve neden **geriye doğru** geçerli olmadığını
  anlatıyor. 20 Ekim'deki E koşumunda künye satırı gerçekten basıldı: `kol-e.txt` başında `Ollama
  sürümü: 0.40.6` yazıyor. A-D logları künyesiz kaldı; sürümleri kafes README'sinin makine satırında.

## Kapsam Dışı: Bu Rehber Onu Hiç Yazmayacak

"Sıfırdan model eğitimi" bir kapsam sözüdür, "her şey" sözü değil. Bu rehberin bilerek girmediği
alanlar:

| Konu | Neden dışarıda |
| --- | --- |
| Çok kiracılı üretim altyapısı (Kubernetes, autoscaling, kuyruk yönetimi) | Site tek makineyi anlatıyor; bu konular o makinenin sayısı olmadan cevapsız kalır |
| Kıyaslama sıralaması / leaderboard puanı | "En hızlı model" demek bu sayfanın iddiası değil; fazların sırasını göstermek yerine sıralama vermek, bayatlamayı satın almaktır |
| Canlı fiyat takibi | Bulut saat ücretleri değişir; sitede fiyat varsa "2026 itibarıyla" + son doğrulama tarihiyle durur |
| Ses ve video modeli eğitimi | Yalnız metin (ve görsel difüzyon LoRA) |
| RLHF/DAPO üretim hattı, dağıtık eğitim | Tek GPU'suz bir makinede koşulamayan bir yolu örneklerle anlatmak, kademe 0 metin üretmek olur |
| Güvenlik kırmızı hat süreci, red-team raporu | Enjeksiyon bölümü savunma eğitimi; bir ürünün saldırı testi değil |
| Kod asistanı / ürün entegrasyonları | Ürün mühendisliği, model eğitimi değil |

:::caution[Dışarıda bırakmak ile "ölçülmedi" farklı şeyler]
"Ölçülmedi" = kapı açık, para ve zaman gerektiriyor. "Kapsam dışı" = kapı bizce kapalı; açılsa bile
bu sitenin sorusuna cevap olmaz. İkisini karıştırırsanız harita her yıl büyüyen bir özür listesine
döner.
:::

## Bir Ölçüm Sayfasının Kabul Kuralları

Yeni kafes koşumuna girmeden önce kabul edilen sözleşme. Bunlar sayfa yazıldıktan sonra
değiştirilmez; değiştirilecekse önce burada değişir.

1. **Yalnız yerel.** Bu projede para harcayan hiçbir kol koşulmaz. Bulut sayfaları kademe 1
   (üretici rakamı) olarak kalır.
2. **Zaman bütçesi.** Kol başına en fazla 20 dakika, gün başına en fazla 45 dakika yerel CPU.
   Bu tavan, ölçüm higienini korumak için var: koşum sürerken başka CPU işi ve başka Ollama isteği
   yok.
3. **Sunucuya müdahale makine sahibinde.** Ollama'nın ortam değişkenlerini yazmak ve sunucuyu
   yeniden başlatmak makineyi yöneten kişinin işi. Ölçümü koşan taraf yalnızca betiği çalıştırır ve
   o değişkenin ölçüm sırasında ne olduğunu kayda yazar.
4. **Duman önce, tam koşum sonra.** Önce tek kol, tek tekrar: uçtan uca bir kayıt üretiyor mu?
   Duman geçmeden tam koşum başlamaz.
5. **Sayılar yalnız bitmiş günlükten.** Koşum sürerken sayı raporlanmaz. Yarım log, boş log,
   "muhtemelen şöyle olur" yok.
6. **Tekrar tabanı.** Ölçüm kolunun tekrar sayısı en az beş; özet **p50 + p95 + toplam duvar
   süresi** olarak verilir. Tek sayı tek gözlemdir ve kademe 2'dir.
7. **Başarısızlık üretilmez.** Sunucu 503 dönerse, bellek baskısı olursa, kol yarıda kalırsa olan
   aynen yazılır. Eksiği "ölçülmedi"ye taşımak, sayıyı tahmin etmekten iyidir.
8. **Sürüm künyesi.** Her yeni kafes kendi Ollama sürümünü kaydın başına yazar. Eski sayfalar
   yeniden ölçülmedikçe sayısını değiştirmez; hangi sürümde ölçüldüğünü söyler.
9. **Doğrulama kalıbı.** Sayfa bitince sırası: `astro build` → `node scripts/link-check.mjs` →
   `npm run dogrula` → yerelde önizleme + tarayıcıda DOM ve stil yoklaması → konsol temizliği →
   `dogrulama` damgası.
10. **GPU/ROCm kolları ayrı onay ister.** Sürücü kurulumu demek makineye sistem bileşeni kurmak
    demek; bu, o kolun kendisinden önce sorulan bir izin.
11. **Bedava okum önce.** Ölçüm gerektirmeyen bir sayfa (kavram, kapsam, karar tablosu) her turda
    pahalı koldan önce yazılır; tur bedavaya da bir şey üretsin diye.

:::note[Bu kuralların maliyeti]
1-11 arasında ölçüm gerektiren tek madde 6: beş tekrar × üç seviye, kol başına 20 dakika tavanıyla
yaklaşık bir iş günü değil, bir iş oturumu. Kalan on madde para ve zaman değil, yazım disiplini
ister — bu yüzden en sık ihlal edilenleri de onlardır.
:::

## Koşulan Eksen: Eşzamanlılık

Kabul kurallarının bugünkü uygulaması. Koşumdan önce, sayılar değişmesin diye burada duruyordu;
19 Ekim'de üç ayarla koşuldu, 20 Ekim'de bir K = 8 kolu eklendi ve son sütun gerçeği gösteriyor:

| Öğe | Sabitlenen değer | Koşumdan sonra |
| --- | --- | --- |
| Soru | Aynı makinede, aynı modelde 1 / 2 / 4 istek **yarışırken** neler oluyor | cevaplandı, üç kez: varsayılan ayarla yarışmıyor sıraya giriyor; `=2` ayarında yuva kadarı yarışıyor taşan sıraya giriyor; `=4` ayarında yarışıyor ama paylaşarak. Üstüne ayrı kalem olarak koşulan K = 8 (20 Ekim) aynı eksende dördüncü bir desen açmadı: varsayılan sunucuda merdiven sekiz basamağa çıktı |
| Sunucu ayarı | `OLLAMA_NUM_PARALLEL` = 1 (varsayılan), 2, 4 — kullanıcı yazar, sunucuyu kullanıcı yeniden başlatır | varsayılan, **=2** ve **=4** koşuldu (ikisini de makine sahibi yazdı, kural 3 olduğu gibi işledi; değerler artık betik etiketi değil `server.log`'daki `server config` ve `-np 2` / `-np 4` satırlarından okundu). K = 8 kolu için değişken yazılmadı, sunucu yeniden başlatılmadı — 19 Ekim'deki kapanıştan beri aynı süreçte `:1` / `-np 1` ile koştu. **=3 de koşuldu** (2026-10-26, 0.40.11; aşağıdaki kapanış paragrafı) — dört sunucu ayarının dördü de artık ölçümlü |
| Model | `qwen2.5:3b-instruct-q4_K_M`, gömme `bge-m3` | sohbet modeli koştu; `bge-m3` bu turda hiç denenmedi — ama üçüncü koşumun **elenen** denemesinde o model kendi kendine yüklendi ve ölçümü bozdu (aşağıdaki başarısızlık satırı) |
| Uç | `/api/chat` ve `/api/embed`, yalnız `http://127.0.0.1:11434` | `/api/chat` ölçüldü, `/api/embed` **koşulmadı** |
| Kol | seviye başına 5 tekrar | üç koşum × (5 tekrar × 3 kol) = **105 ölçüm isteği**, 45 dalga. K = 8 kolu ayrı: 5 tekrar × 1 kol = 40 ölçüm isteği (+1 ısıtma) |
| Birim | istek başına duvar sn, `total_duration` sn, tok/sn, **p50 ve p95**, tur toplam duvar sn | hepsi kayıtlarda ve sayfada |
| Başarısızlık | HTTP 503 / bellek baskısı / boş cevap → kayda aynen geçer, sayıdan düşülmez | sıfır hata: 105/105 HTTP 200, `eval_count` 64; K = 8 kolunda 40/40. **Ama başka bir başarısızlık türü bulundu:** sunucu ayarı doğru, istekler hatasız, ölçüm yine de geçersiz — `=2` kolunun ilk koşumu pencereye giren 89 yabancı istek yüzünden elendi ve hiçbir sayısı yayımlanmadı |
| Dışarıda | GPU, çok makine, kalıcı servis, ağ gecikmesi | dışarıda kaldı |

:::caution[Tahmini sonuçla karıştırmak]
"4 paralel istek, 4 kat verim verir" bir **beklenti**dir (kademe 0). Kafes üç ayarı da ölçtü: varsayılan
ayarla kazanç yok (dört istek sıraya giriyor, tek istek hızı sabit), `=4` ayarıyla kazanç var ama
**1,73 kat** — dört yuva dört kat hız vermiyor, çünkü paylaşan tek bir CPU var. `=2` ayarı üçüncü bir
kapı açtı: yuvadan çok istek geldiğinde **hız düşmüyor, kuyruk uzuyor** (9,13 → 9,22 tok/sn, bekleme
medyanı 3,60 sn). Beklenenle ölçülen arasındaki o fark, bu haritanın kafesi yazma sebebiydi.
:::

Koşumun gerçek maliyeti de kayıttan çıktı: **168,37 sn + 131,78 sn + 141,88 sn ölçülen dalga süresi**,
koşum aralıkları 3 dakika 46 saniye (10:54:14 → 10:58:00), 3 dakika 31 saniye (12:19:56 → 12:23:27) ve
3 dakika 32 saniye (14:07:35 → 14:11:07). İkinci ve üçüncü koşumun üstüne bir de makine sahibinin işi
bindi: değişkeni yazmak, Ollama'yı yeniden başlatmak, günlükte `OLLAMA_NUM_PARALLEL:2` / `:4` ve
`-np 2` / `-np 4` satırlarını görmek. Üçüncü kolda bir maliyet daha çıktı: **ilk deneme atıldı** ve bedeli üç ölçülmüş aralığın toplamı — elenen
pencere 3' 29'' (14:00:46 → 14:04:15) + bellek boşalmasını bekleyen yoklama 1' 52'' (14:05:43 → 14:07:35)
+ yayımlanan koşum 3' 32'' = **≈9 dakika**, üstüne makine sahibinin ikinci bir restart'ı. Yukarıdaki "bu
kuralların maliyeti" notu bir iş oturumu tahmini taşıyordu; fiilen oturumun yaklaşık sekiz dakikası,
üçüncü seviyeyle birlikte on ikiden fazla dakikaya çıktı. Kural 6'nın
(beş tekrar, p50 + p95) bedeli sandığımız kadar değil — asıl bedel, o süre boyunca makineyi başka işe
kapatmak; üçüncü koşuldan öğrenilen ise **kapatmanın yetmediği**: başka bir aracın aynı sunucuya
istek göndermediğinden emin olmadan pencere açılmıyor.

Dördüncü koşum (K = 8, 20 Ekim) bu maliyet defterine yeni bir sahip işi eklemedi: değişken yazılmadı,
sunucu yeniden başlatılmadı, çünkü koşulacak ayar zaten kapanıştaki varsayılandı. Ödediği tek şey
kendi ölçüm penceresi ve iki pencere arasındaki kirletme denetimi; süreler ve sayılar
[Eşzamanlılık](/kullanim/eszamanlilik/) sayfasında.

Kural 3'ün kapanış adımı da 19 Ekim'de uygulandı: değişken User kaydından silindi, `reg query` artık anahtarı
bulmuyor, makine bulduğumuz gibi (`OLLAMA_NUM_PARALLEL` tanımsız, sunucu `:1` ve `-c 4096 -np 1`) bırakıldı.
Doğrulama günlükle yapıldı, sezgiyle değil — ve tek bir gözlem daha var: tray uygulaması silmeyle aynı
dakikada kendini yeniden başlatmış görünüyor; **bunun nedeni ölçülmedi**, o yüzden "restart gerekmez"
diye kurala dönmez, kapanış yine günlükteki `:1` + `-np 1` satırlarıyla sayılır.

Sıradaki eksen olarak sabitlenen iş **19 Ekim'de yazıldı**: [Uçtan Uca Tek Hat](/ornekler/ucdan-uca/) —
sıfırdan bir Türkçe asistanın veri toplama, temizleme, eğitim, değerlendirme ve Ollama'da çalıştırma
adımalarının tek bir sayfada, tek bir sıra halinde yürünmesi. Boşluk kapanırken iki şey değişmedi.
Birincisi: o sayfa **hiçbir sayıyı yeniden yazmıyor**; hangi kayıttan geldiğini ve kademe kaç olduğunu
taşıyor, rakam ilgili sayfada duruyor (yukarıdaki tek-kaynak tablosu bu yüzden yeni bir birim satırı
daha aldı). İkincisi: haritanın gördüğü boşluk "adım adım anlatım"dı, "yürünmemiş adım" değil — yeni
sayfa da beş istasyonun tamamını bu makinede koşmuş değil: istasyon 3'ün **sohbete ait kolu** (QLoRA)
GPU istediği için hiç çalışmadı, istasyon 5 ise hattın kendi ürettiği adaptörü değil emsalinin hazır
modelini çalıştırdı. Kopma noktaları sayfanın üstünde, "Nerede Kırılır" başlığında duruyor.

## Açık Kalemlerin Kabul Kriterleri

Yukarıdaki eksen, kuralların **koşumdan önce** bağlandığında ne işe yaradığını gösteriyor: taşan isteğin
hız mı yoksa kuyruk mu ürettiği ancak o sayfa sayısına bakınca anlaşıldı. Aşağıdaki üç kalem de aynı
şekilde sabitleniyor — soru, kol tasarımı, yayımlama eşiği, kayıt dosyasının adı ve engel kimde. Kriter
koşum izni **değildir**; her kalem ayrıca "koş" demeyi bekler.

| Kalem | Soru (tek cümle) | Kol ve istek yükü | Yayımlama eşiği | Engel | Kayıt |
| --- | --- | --- | --- | --- | --- |
| **K > 4 taşması** | Yuva sayısı 1 iken **8** istek aynı anda salınırsa bekleme dalga başına nasıl büyüyor? | `--kollar 8 --tekrar 5` = 40 ölçüm isteği + 1 ısıtma; sunucuya **dokunulmaz** (kapanışta doğrulanan `-np 1` üzerinde koşar) | 40 kayıttan en az 38'i HTTP 200 ve `eval_count` 64; kirletme denetiminde kafes dışı istek satırı **0** (kafesin kendi imzası: 74 token'lık satırlar + sonda tek 32 token'lık tahliye satırı) | yok — Ollama'nın ayakta olması yeterli | `eszamanli-kaydi-5.txt` |
| **`/api/embed` isteğin başına düşen gider** | 24 parçayı tek istekte göndermekle 24 ayrı istekte göndermek arasındaki fark, istek başına sabit bir gider mi? | yeni kol `--kol e`: `e-batch` 1 istek × 5 tekrar, `e-teker` 24 istek × 5 tekrar → **125 ölçüm isteği** | iki yan da beşer tekrar; p50 + p95 + toplam duvar. Fark tekrarlar arası yayılımdan büyükse hüküm kurulur, değilse **"fark ölçülemedi"** yayımlanır — o da yayımlanmış sonuçtur | **kod**: ~25 satırlık yeni kol şubesi (`ollama_gommeler` içindeki `input` listesi tek-ilaveye çevrilir) | `kol-e.txt` + `kol-e.json` |
| **`OLLAMA_NUM_PARALLEL=3`** | Ölçülen iki adım (=1→=2 ≈ +233 MiB, =2→=4 ≈ +145 MiB/yuva) arasında üçüncü yuva bedeli nereden geliyor? | A/B/C'nin aynısı: `--kollar 1,2,4 --tekrar 5` = 35 ölçüm isteği + 1 ısıtma; tek fark sunucu ayarı, kol sırası ve saat bandı korunur | günlükle `OLLAMA_NUM_PARALLEL:3` **ve** `-np 3` okunmadan pencere açılmaz; `/api/ps` boş; imza 37 satır (36 × 74 token + 1 × 32) değilse koşum yayımlanmaz | **kural 3**: sahibin iki adımı (env yaz + restart). Hazırlık bloğu kafes README'sinde | `eszamanli-kaydi-4.txt` |

**Kalemlerin bugünkü durumu (20 Ekim):** tablodaki üç kalemden ikisi koşuldu ve ikisi de eşiğini
geçti. K > 4: 40 kaydın 40'ı HTTP 200 + `eval_count` 64, kirletme denetiminin imzası 41 × 74 + 1 × 32,
yabancı satır 0, `/api/ps` tek kopya; sonuç [Eşzamanlılık](/kullanim/eszamanlilik/) sayfasında.
`/api/embed` karşılaştırması 20 Ekim 11:45-11:46'da koşuldu: 125 ölçüm isteği, iki yanın beşer
tekrarı, ön kayıtlı min–maks kuralı; tekrar aralıkları çakışmadı ve hüküm verildi. İki yanın
saniyeleri [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasının "Toplu gömme" bölümünde.

**Üçüncü kalem de kapandı (2026-10-26):** `=3`, kendi eşiğiyle koşuldu ve geçti. Makine sahibi
iki kez env yazıp sunucuyu iki kez restart etti — ilk restart'ta tray süreci eski ortamı miras
aldı ve günlük `OLLAMA_NUM_PARALLEL:1` okuduğu için pencere açılmadı (kapanış doğrulaması
günlükle yapıldı; `reg query` 3 gösterse bile koşum başlamadı); ikinci restart'ta açılış satırı
`:3` okundu. Koşum 00:29:18-00:32:39, 35 ölçüm isteği + 1 ısıtma, 0 hata; günlükte llama-server
`-c 12288 -np 3` (önceden kaydedilen 12288 beklentisi tuttu), kirletme imzası 37 satır
(36 × 74 + 1 × 32), yabancı satır 0, yuva sayımı `id 0: 22, id 1: 10, id 2: 5`. Sayılar
[Eşzamanlılık](/kullanim/eszamanlilik/) sayfasında; pencere sırasında sunucu Docker Desktop'ın
Ollama entegrasyonu bge-m3'ü kendi kendine yüklediği için risk altındaydı — kirletme denetimi
pencere içinde sessiz olduğunu gösterdi, ama **bu aracın kimliği netleşti**: her Ollama açılışında
bge-m3'ü yükleyen istemci `com.docker.backend.exe`. =2 koşumunun elenen penceresindeki faili
meçhul kirleticinin kimliği de böylece belli oldu.

Üç kalem için de önceden bağlanan başka şeyler:

- **Birimin tek adresi değişmiyor.** K = 8 ve (koşulduğunda) `=3` satırlarının saniyeleri
  [Eşzamanlılık](/kullanim/eszamanlilik/), `/api/embed` **gider karşılaştırmasının** saniyeleri
  [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasında yayımlanır. Ölçümü üreten kafes başka, sayıyı
  taşıyan sayfa başka olabilir; sayıyı **iki sayfa** söyleyemez. Zaten ölçülmüş olan 24 parçalık tek
  isteğin süresi bu kural gereği kendi sayfasında ([Gömme Modeli Eğitimi](/rag/gomme-egitimi/)) kalır;
  karşılaştırma koşuldu, iki yanı Hız ve Maliyet'te yayımlandı ve oradaki bölüm o eski sayıyla
  karşılaştırma yapılamayacağını ayrıca yazıyor.
  `rag/parcalama-ve-hibrit-arama/` batch sonucuna yalnız bağlanır, kendi cümlesinde rakam yazmaz.
- **Karşılaştırma yasağı önceden yazıldı.** 24 parçalık tek isteğin ölçülmüş süresi (`kol-a.txt`, sayısı
  kendi sayfasında) ile RAG sayfalarındaki 125'lik indeks süreleri **birbirinin A/B tarafı değildir**:
  farklı korpus, farklı model, farklı istek biçimi. İkisini yan yana koyup "batch şu kadar ucuz" cümlesi
  kurulamaz; kalem ancak kendi iki yanı koşulundan sonra hüküm verir.
- **Beklenen `-c` sayıları defterde türetilmiş borç olarak duruyor.** `=3` için `-c 12288` beklentisi
  üç ölçümün örüntüsünden geliyor, ölçümden değil; sapma olursa sapmanın kendisi haberin başlığı olur.
  Üç yuvanın bellek boyutu da önceden tahmin edilmez — boş hane olarak yazılır, koşulunca dolar.
- **Zaman tavanı aşılırsa koşum bitirilmez.** Kural 2 kol başına 20 dakika diyor. Ölçülmüş dört tam
  koşumdan üçü 35 istekle 3'31'' ile 3'46'' arasında sürdü, 40 istekli K = 8 kolu da dört dakikanın
  altında kaldı (pencereler Eşzamanlılık sayfasında); 125 istekli kol da 20 Ekim'de koşuldu ve 20
  dakikalık tavanın altında kaldı (süre kayıtta). Tavan dolarsa yarım log yayımlanmaz, "yarıda
  bırakıldı" yazılır.
- **Kapsam dışı kalan komşular.** 125 parçayı **tek istekte** göndermek, K=8'den yüksek seviyeler,
  `/api/embed` eşzamanlılığı ve `OLLAMA_MAX_LOADED_MODELS` bu üç kalemde değil; kendilerine kriter
  yazılmadan koşuma girmezler.

:::note[Kriter yazmanın maliyeti]
Üç kalem için toplam sıfır saniye CPU, sıfır Ollama isteği — yukarıdaki tablo diskteki kayıtlar ve betik
satırları okunarak yazıldı. Koşumun kendisi ayrıca ve pahalıdır: ilk üç eşzamanlılık koşumu
makine sahibinin iki restart'ını ve fiilen ≈9 dakikalık bir pencereyi (elenen deneme dahil) götürdü;
dördüncü koşum restart istemedi ama kendi penceresini ve kirletme denetimini istedi.
:::

## Ölçülmedi

- Bu haritanın okuyucuya gerçekten yardımcı olduğu **ölçülmedi**; banner mekaniğinde olduğu gibi,
  burada da ölçülmüş olan tek şey metnin render edildiği.
- On kafes / 14 betik sayımı `127.0.0.1:11434` dizgesiyle grep'lenerek bulundu (eşzamanlılık kafesiyle
  birlikte). Kodun tamamı
  satır satır denetlenmedi; "kafeslerin internete hiç çıkmadığı" iddiası **bu koşumda doğrulanmadı**
  (ağ dökümü alınmadı). Örnek 6 ve 7 korpus indirdiği için o ikisi zaten çevrimdışı değil.
- Kanıt kademelerinin (0-3) doğru ayırma gücü **ölçülmedi** — bir sayfanın kaç satırı hangi
  kademede, sayılmadı.
- Ölçümlerin **genelleme kapsamı** ölçülmedi: bu makine tek bir Ryzen 5 2600, 15,9 GB RAM,
  %100 CPU. Başka bir CPU'da hangi sayının hangi kademede kalacağı bilinmiyor.

## İlgili Sayfalar

- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — kademe 3 sayıların kaynağı ve "Burada ölçülmeyenler" listesinin sahibi.
- [Eşzamanlılık](/kullanim/eszamanlilik/) — bu haritanın "sıradaki eksen" diye sabitlediği koşumun çıktı sayfası; kabul kuralları yazıldıktan sonra ilk kez bir koşuma olduğu gibi uygulandı.
- [Uçtan Uca Tek Hat](/ornekler/ucdan-uca/) — bu haritanın sıradaki ekseni olarak sabitlediği boşluğu 19 Ekim'de kapatan sayfa; ölçüm üretmedi, yalnızca kayıtların adresini ve kademesini taşıyor.
- [Yol Haritası](/baslangic/yol-haritasi/) — hangi donanımın hangi işi yapabildiği; kapsamın donanım tarafı.
- [Sıkça Sorulan Sorular](/kaynaklar/sss/) — "bu rehber tek başına yeter mi" sorusunun kısa cevabı.
- [Doğrulama Mekaniği](/kaynaklar/dogrulama-mekanizmasi/) — iddiaların zamana karşı durumu; bu haritanın bakım tarafı.

## Kaynaklar ve İleri Okuma

- [Ollama sıklıkla sorulanlar](https://docs.ollama.com/faq) — `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_KEEP_ALIVE` varsayılanları; bu haritada kademe 1 olarak geçen sayıların adresi. (Son okuma: 2026-10.)
- [Starlight — Sidebar](https://starlight.astro.build/guides/sidebar/) — bölüm ve sayfa sırasının yapılandırılması. (Son okuma: 2026-10-19.)
