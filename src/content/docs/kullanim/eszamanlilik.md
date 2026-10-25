---
title: "Eşzamanlılık: Aynı Anda Birden Çok Soru Sorduğunuzda Ne Oluyor"
description: "Aynı model, aynı makine, aynı anda salıverilen 1, 2, 4 ve 8 istek — üç sunucu ayarı ve varsayılan sunucuda bir taşma koşumu: varsayılan Ollama'da kuyruk merdiveni, OLLAMA_NUM_PARALLEL=2'de ikişerli çift ve kuyruk, =4'te kilit adımıyla eşzamanlı bitiş; K=8'de merdiven sekiz basamağa çıkıyor ama tek isteğin hızı değişmiyor. Dalga başına duvar, p50 ve p95, sistem token/saniye, bellek bedeli; 2026-10-19 ve 2026-10-20 kayıtları."
dogrulama: 2026-10-20
---

"Sunucum kaç isteğe dayanır" sorusu iki ayrı ayarın karışımından çıkar ve bu ikisi ölçümde birbirinden ayrılmazsa sayı yanlış okunur. Bu sayfada önce o ayrım yapılıyor, sonra **aynı kafes üç sunucu ayarında** koşuluyor: aynı makine, aynı model, bariyerle aynı anda salıverilen 1, 2 ve 4 istek. Sonuç üç cümlede: varsayılan ayarla **dört istek yarışmıyor, sıraya giriyor** — son kullanıcı cevabını 18,50 sn'de alıyor. `OLLAMA_NUM_PARALLEL = 4` verildiğinde sıra kayboluyor (bekleme 14,11 sn'den 0,12 sn'ye iniyor), ama **iş paylaşılıyor**: aynı dalga 13,77 sn sürüyor ve tek bir isteğin hızı 14,97 tok/sn'den 6,38 tok/sn'ye düşüyor. **Ara seviye `=2` ikisinin karışımını veriyor:** dört isteğin ikisi 7,1 sn'de bitiyor, öteki ikisi 14,47 sn'de — çünkü yuvadan çok istek geldiğinde kalanlar yine sıraya giriyor, ama paylaşan taraf da paylaşılıyor. Bu üç desenin üstüne dördüncü bir koşum eklendi: aynı varsayılan sunucuya **sekiz istek** (2026-10-20). Yeni bir desen çıkmadı — merdiven sekiz basamağa çıktı, son kullanıcı cevabını 38,17 sn'de aldı, ama tek isteğin hızı 14,15 tok/sn ve sistem hızı 13,38 tok/sn ile yerinde kaldı. Yani istemci tarafında kalabalığı artırmak, tek yuvalı sunucuda hız değil sıra üretiyor.

## İki Eşzamanlılık, İki Ayrı Ayar

| Ne | Kim belirler | Bu sayfadaki durumu |
| --- | --- | --- |
| **Kaç istek aynı anda salınıyor** (K) | İstemci: betiğiniz, tarayıcı sekmeleriniz, uygulamanız | ölçüldü: K = 1, 2, 4 (üç sunucu ayarında) ve **K = 8** (yalnız varsayılan ayarda, 2026-10-20) |
| **Sunucu aynı anda kaç isteği işlemeye çalışıyor** | `OLLAMA_NUM_PARALLEL` ortam değişkeni, sunucu açılışında okunur | ölçüldü: varsayılan (=1), **=2** ve **=4**. Seviye **3 ölçülmedi** |

:::note[Ayarı betik değil, sunucu günlüğü söyler]
`OLLAMA_NUM_PARALLEL` sunucunun kendi ortam değişkenidir: betik onu okuyamaz, yalnızca makineyi yöneten kişi yazar ve sunucunun yeniden başlatılması gerekir. [Kapsam Haritası](/kaynaklar/kapsam-haritasi/)'nın 3. kabul kuralı bu ayrımı "sunucuya müdahale makine sahibinde" diye sabitlemiştir; ölçülen ikinci ve üçüncü kol de tam olarak böyle koşundu — değişkeni makine sahibi yazdı, sunucuyu o yeniden başlattı.
Ama değer artık "kullanıcının verdiği bilgi" değil, **okunabilir bir ölçüm**: Ollama her açılışta günlüğüne tam ortam haritasını yazıyor. Bugünkü üç sunucu satırı: `12:15:11` → `OLLAMA_NUM_PARALLEL:4`, `13:58:33` → `OLLAMA_NUM_PARALLEL:2`, sabah 08:59'daki (bir önceki günlük dosyası) → `OLLAMA_NUM_PARALLEL:1`. Model ilk yüklendiğinde ayrıca kaldırılan komut satırı görünüyor: `llama-server.exe --model …qwen2.5 blobu… -c 4096 -np 1` (sabah), `-c 16384 -np 4` (öğle) ve `-c 8192 -np 2` (üçüncü kol, 13:59:19 yüklemesi). `-np` = fiilen açılan yuva sayısı; koşumda o yuvaların kullanıldığı da günlükten sayıldı (dört yuvanın dördü de, iki yuvanın ikisi de iş almış — aşağıdaki kirletme denetiminin yan çıktısı). Koşumdan önce bu iki satıra bakmadan ölçüme başlamak yanlış bir kapıdır: değişken yazılmış ama sunucu eski procesle devam ediyor olabilir. Nitekim üçüncü kolün **ilk** koşumu tam bu tuzaktan değil ama komşusundan öldü: ayar doğruydi, pencere kirlendi, kayıt atıldı (aşağıda).
:::

## Dört Koşumun Düzeni

Aynı betik, aynı istek, aynı protokoller; tek fark sunucunun açılışta okuduğu ayar ve istemci tarafında salıverilen istek sayısı. İlk üçü 2026-10-19'da üç sunucu ayarında, dördüncüsü 2026-10-20'de varsayılan sunucuda K = 8 ile koşuldu.

- **Bariyer.** Her dalgada K iş parçacığı `threading.Barrier(K)` noktasında bekletilip tek seferde salıveriliyor. Sabahki koşumda salıverme sapması en fazla **0,015 sn**; öğle ve üçüncü koşumda 35'er kaydın, D'de 40 kaydın tamamı `bariyer_sn` = 0,00 olarak yazıldı (kayıt dört ondalığa yuvarlıyor, yani sapma 0,00005 sn'nin altında). "Aynı anda" iddiası saat okumasıyla değil, ölçülmüş sapmayla duruyor.
- **İstek.** `qwen2.5:3b-instruct-q4_K_M`, `/api/chat`, `http://127.0.0.1:11434`, `temperature: 0,0`, `num_predict: 64`, `keep_alive: "10m"`.
- **Eşit üretim.** Dört koşumun **145 ölçüm isteğinin tamamında** `eval_count` = 64 ve `done_reason` = `length`; istem token sayısı 74'te sabit. Yani dalga süreleri farklı token sayılarının ortalaması değil, aynı işin tekrar sayısı farkı.
- **Isıtma ayrı.** Her koşumdan önce bir istek atılıyor. Sabah: duvar 12,36 sn, yüklenme 5,64 sn. Öğle: duvar 34,09 sn, yüklenme **27,82 sn** — dört yuvanın birden kurulmasının bedeli. Üçüncü kol: duvar 23,83 sn, yüklenme **17,48 sn** — iki yuva, arada bir bedel. D: duvar **27,906 sn**, yüklenme **21,2176 sn** — model bir gün boyunca kullanılmamıştı, ağırlıklar sıcak değildi; bu bedel ölçüm dışı ısıtmada ödendi. Ölçüm kollarının hiçbirinde model yeniden alınmadı: sabah 35 kaydın en büyük `load_duration` 0,022 sn, öğle 0,023 sn, üçüncü kol 0,052 sn, D 0,0639 sn.
- **Dalga arası 3 sn, kol başına 5 tekrar.** İlk üç koşumda kollar `1, 2, 4` sırasıyla, D'de tek kol K = 8 olarak koşuldu; her kolun başında `/api/ps` okundu.
- **`num_thread` gönderilmedi.** Kaydın `secenekler` alanı üç ayar taşıyor (sıcaklık, `num_predict`, `keep_alive`); iş parçacığı sayısı sunucu varsayılanında kaldı. İlk üç koşumun üçer kolu ve D'nin tek kolu kendi içinde aynı varsayılanla koştuğu için **kollar arası** karşılaştırma geçerli — ama mutlak tok/sn bu makinenin varsayılanına bağlıdır ve `num_thread` sabitleyip tekrar koşmak ayrı bir kol demek (ölçülmedi).

:::note[Künye: dört koşum, tek makine]
Betik: `ornekler/eszamanli-olcu/eszamanli_olcu.py`. Özetleyici: `ornekler/eszamanli-olcu/ozetle.py` (aynı logdan yeniden hesaplar; merdiven tablosu dahil, testleri `--test` ile koşulsuz çalışır).
**Koşum A — varsayılan sunucu:** `cikti/eszamanli-kaydi-1.txt`, aralık **10:54:14 → 10:58:00**, ölçülen dalga süresi toplam **168,37 sn**, 35 ölçüm isteği + 1 ısıtma, 0 hata.
**Koşum B — `OLLAMA_NUM_PARALLEL = 4`:** `cikti/eszamanli-kaydi-2.txt`, aralık **12:19:56 → 12:23:27**, ölçülen dalga süresi toplam **131,78 sn**, 35 ölçüm isteği + 1 ısıtma, 0 hata. Bu koşumdan önce kısa bir duman koşumu yapıldı (`cikti/duman-kaydi-2.txt`, 3 istek, 15,19 sn) ve aşağıdaki sayılar **tam koşumdan**.
**Koşum C — `OLLAMA_NUM_PARALLEL = 2`:** `cikti/eszamanli-kaydi-3.txt`, aralık **14:07:35 → 14:11:07**, ölçülen dalga süresi toplam **141,88 sn**, 35 ölçüm isteği + 1 ısıtma, 0 hata; duman koşumu `cikti/duman-kaydi-3.txt` (3 istek, ölçülen dalga 15,28 sn). Aşağıdaki C sayılarının tamamı bu tam koşumdan.
**Koşum D — varsayılan sunucu, K = 8:** `cikti/eszamanli-kaydi-5.txt`, aralık **10:43:35 → 10:47:30** (2026-10-20), ölçülen dalga süresi toplam **191,3 sn**, 40 ölçüm isteği + 1 ısıtma, 0 hata; duman koşumu `cikti/duman-kaydi-4.txt` (8 istek, ölçülen dalga 38,078 sn). Aşağıdaki D sayılarının tamamı tam koşumdan. Sunucu 2026-10-19T14:39:48'deki `server config` satırından beri yeniden başlatılmadı; D de aynı süreçte, `:1` ve `-c 4096 -np 1` ile koştu.
Dördünde de: Ollama **0.40.6**, Python 3.12.10, Windows 11, AMD Ryzen 5 2600 (6 çekirdek/12 iş parçacığı), 15,9 GB RAM; `/api/ps` kaydında `size_vram` **0** — model CPU'da çalıştı. Günlükte sunucunun kendi okuması: `inference compute id=cpu … available="3.2 GiB"`; Vulkan cihaz keşfi bu makinede çöküyor (`llama-server --list-devices failed: exit status 0xc0000005`), yani GPU'ya düşme ihtimali ölçümle elendi.
**Koşullar birebir aynı değil — sayfanın en önemli dikkat noktası bu.** A sabah 10:54'te, B öğle 12:19'da, C 14:07'de (hepsi 2026-10-19); D bir gün sonra, 2026-10-20 10:43'te koşuldu ve ısıtması 21,2 sn'lik yüklenmeyle soğuk bir başlangıç yaptı. A, B ve C üç ayrı sunucu procesinde, D ise 2026-10-19T14:39:48'deki `server config` satırından beri yeniden başlatılmayan varsayılan süreçte koştu; arka plan iş yükü ve bellek durumu bu aralıkta değişebilir. Günlük A'nın ilk yüklemesinde `free="3.8 GiB"`, B'nin sunucu açılışında `available="3.2 GiB"` yazıyor. Bu yüzden **mutlak** sayılar (5,91 vs 5,51 vs 5,66 sn) saat farkına mı ayardan mı geçtiği ayrılamayan sayılardır; sayfa bu karşılaştırmayı yalnız **desen** düzeyinde kesin tutuyor: merdiven var / ikişerli çift var / merdiven yok. D ile A arasındaki karşılaştırma da desen düzeyinde: aynı merdiven, aynı ~4,6 sn'lik adım, aynı ~14 tok/sn istek hızı; K 4'ten 8'e çıkınca dalga 2,08 kat uzuyor. Sayı düzeyinde en sağlam farklar desenlerin kendisinden doğuyor: en kötü kullanıcı süresi (18,50 → 14,47 → 13,77 sn) ve bekleme hanesi (14,11 → 3,60 → 0,12 sn).
**Kirletme denetimi dört pencerede de koşuldu** (tarifi aşağıda): A ve B'nin penceresinde 37 yeni-istem satırı, dağılım birebir aynı — 36 satır 74 token (ısıtma + 35 ölçüm isteği), 1 satır 32 token (betiğin kendi boşaltma çağrısı). D'nin penceresinde 42 satır: 41 satır 74 token (ısıtma + 40 ölçüm isteği), 1 satır 32 token; tamamı `id 0`. C'nin **ilk** koşumu aynı denetimde elendi: pencereye 89 yabancı satır girdi, kayıt `cikti/kirli-eszamanli-kaydi-3.txt` adıyla duruyor ama hiçbir sayısı yayımlanmıyor. Yayımlanan C koşumunda dağılım yine 36 + 1.
:::

## Sonuç Tabloları

**Koşum A — varsayılan sunucu (`-np 1`):**

| Kol | Dalga | Kayıt/beklenen | Hatalı | p50 duvar (sn) | p95 duvar (sn) | En uzun dalga (sn) | Ortalama dalga (sn) | Sistem tok/sn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5,91 | 6,45 | 6,45 | 6,03 | 10,62 |
| K=2 | 5 | 10/10 | 0 | 4,76 | 9,34 | 9,34 | 9,21 | 13,89 |
| K=4 | 5 | 20/20 | 0 | 9,48 | 18,50 | 18,75 | 18,43 | 13,89 |

Oranlar aynı logdan: **bir K=2 dalgası K=1'in 1,53 katı, bir K=4 dalgası 3,06 katı sürüyor.**

**Koşum B — `OLLAMA_NUM_PARALLEL = 4` (`-np 4 -c 16384`):**

| Kol | Dalga | Kayıt/beklenen | Hatalı | p50 duvar (sn) | p95 duvar (sn) | En uzun dalga (sn) | Ortalama dalga (sn) | Sistem tok/sn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5,51 | 5,58 | 5,58 | 5,49 | 11,66 |
| K=2 | 5 | 10/10 | 0 | 8,14 | 8,62 | 8,62 | 8,16 | 15,68 |
| K=4 | 5 | 20/20 | 0 | 12,47 | 13,77 | 13,77 | 12,71 | 20,15 |

Oranlar: **K=2 dalgası K=1'in 1,49 katı, K=4 dalgası 2,32 katı.** A ve B'de hata yok, eksik dalga yok, HTTP 200 dışında kayıt yok.

**Koşum C — `OLLAMA_NUM_PARALLEL = 2` (`-np 2 -c 8192`):**

| Kol | Dalga | Kayıt/beklenen | Hatalı | p50 duvar (sn) | p95 duvar (sn) | En uzun dalga (sn) | Ortalama dalga (sn) | Sistem tok/sn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=1 | 5 | 5/5 | 0 | 5,66 | 5,81 | 5,81 | 5,69 | 11,24 |
| K=2 | 5 | 10/10 | 0 | 8,23 | 8,97 | 8,97 | 8,42 | 15,21 |
| K=4 | 5 | 20/20 | 0 | 7,26 | 14,47 | 14,47 | 14,27 | 17,95 |

Oranlar: **K=2 dalgası K=1'in 1,48 katı, K=4 dalgası 2,51 katı**; üçüncü kol de 0 hata, 0 eksik dalga. K=4 satırındaki **p50 7,26 sn** yanıltmasın ve bunun bir kazanç olduğunu söylemesin: 20 kaydın 10'u hızlı çiftte, 10'u yavaş çiftte, medyan tam sınırda duruyor. Aynı kolun en uzun dalgası 14,47, ortalaması 14,27 sn. Tekrar tekrar bakıldığında beş dalganın beşinde de yapı aynı: iki istek ~7,1 sn, iki istek ~14,2 sn.

**Koşum D — varsayılan sunucu, K = 8 (`-np 1`, 2026-10-20):**

| Kol | Dalga | Kayıt/beklenen | Hatalı | p50 duvar (sn) | p95 duvar (sn) | En uzun dalga (sn) | Ortalama dalga (sn) | Sistem tok/sn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K=8 | 5 | 40/40 | 0 | 20,25 | 38,17 | 38,97 | 38,26 | 13,38 |

Bir K=8 dalgası K=1'in 6,34 katı, A'nın K=4 dalgasının 2,08 katı sürüyor. Oranın 8 değil 6,34 olması önbellek hanesinden: K=1'in her isteği kendi ön-yüklemesini ödüyor, K=8'de sekiz istek tek soğuk ön-yüklemeyi paylaşıp yedisi hazır öneki buluyor (aşağıdaki önbellek tablosu).

Dört tabloyu yan yana okumanın ölçtüğü şey: **K=4 dalgasının son kullanıcısı 18,50 → 14,47 → 13,77 sn'ye iniyor (A'dan C'ye yüzde 22, C'den B'ye yalnız yüzde 5 daha erken), ama K=1 kolundaki tek kullanıcı hiçbir ayarda iyileşmiyor** (5,91 / 5,51 / 5,66 sn — bu üçü saat farkından ayrılamaz, bkz. künye). Kalabalık sırası iki ayar arasında **dağılımla** ayrılıyor: `=4` herkese 12,4-13,8 sn veriyor, `=2` yarısına 7,1 sn verip yarısını 14,2 sn'de bekletiyor. Sistem tok/sn K=4'te 13,89 → 17,95 → 20,15. Dördüncü satır bu resmi bozmuyor: K=8'de tek istek hızı 14,15 tok/sn (A'nın K=1/K=2/K=4 kollarındaki 14,07/14,22/14,14 ile aynı), sistem hızı 13,38 tok/sn (A'nın K=4'ünün 13,89'uyla aynı mertebede) ve son kullanıcı 38,17 sn. Yani istemci sayısı artınca kuyruk uzuyor, hız artmıyor.

## Merdiven, İkişerli Çift ve Kilit Adımı: Üç Ayarın Üç Deseni

Yukarıdaki oranlar tek başına "yarışma var mı" sorusunu cevaplamaz; cevap dalganın **içinde**. K=4 kollarının beş dalgasında, dört isteğin kendi duvar süreleri (kayıt sırası değil, süreye göre dizilmiş):

**Koşum A — varsayılan sunucu:**

| Tekrar | 1. istek | 2. | 3. | 4. | Adımlar |
| --- | --- | --- | --- | --- | --- |
| 1 | 4,70 | 9,48 | 14,03 | 18,50 | 4,78 · 4,55 · 4,47 |
| 2 | 4,63 | 9,22 | 13,94 | 18,47 | 4,59 · 4,72 · 4,53 |
| 3 | 4,67 | 9,38 | 14,11 | 18,75 | 4,70 · 4,74 · 4,64 |
| 4 | 4,73 | 9,23 | 13,73 | 18,38 | 4,50 · 4,50 · 4,64 |
| 5 | 4,59 | 9,08 | 13,69 | 18,08 | 4,48 · 4,61 · 4,39 |

Beş dalganın beşinde de aynı yapı: süreler **eşit aralıklı bir merdiven** diziliyor, adım 4,39–4,78 sn arasında (15 adımın ortalaması 4,59 sn). Yani ikinci istek birincinin bitişinde, üçüncü ikincinin bitişinde başlıyor. K=2'de de aynı şey iki basamaklı hâlde (4,55–4,77 ve 9,02–9,34 sn).

**Koşum B — `OLLAMA_NUM_PARALLEL = 4`:**

| Tekrar | 1. istek | 2. | 3. | 4. | Adımlar |
| --- | --- | --- | --- | --- | --- |
| 1 | 13,64 | 13,64 | 13,77 | 13,77 | 0,00 · 0,12 · 0,00 |
| 2 | 12,47 | 12,47 | 12,47 | 12,47 | 0,00 · 0,00 · 0,00 |
| 3 | 12,50 | 12,50 | 12,50 | 12,50 | 0,00 · 0,00 · 0,00 |
| 4 | 12,39 | 12,39 | 12,39 | 12,39 | 0,00 · 0,00 · 0,00 |
| 5 | 12,41 | 12,41 | 12,41 | 12,41 | 0,00 · 0,00 · 0,00 |

Merdiven yok: 15 adımın 14'ü **0,00 sn**, biri 0,12 sn. Dört istek aynı anda başlıyor ve aynı anda bitiyor. K=2'de de aynı: her iki istek aynı değerde (7,94–8,62 bandında, beş dalganın dördünde birebir aynı). Bu desenin adı **kilit adımı** (lock-step): dört yuva ayrı iş taşıyor ama CPU'da tek bir batch içinde birlikte ilerliyor, dolayısıyla birlikte bitiyor.

**Koşum C — `OLLAMA_NUM_PARALLEL = 2`:**

| Tekrar | 1. istek | 2. | 3. | 4. | Adımlar |
| --- | --- | --- | --- | --- | --- |
| 1 | 7,08 | 7,08 | 14,22 | 14,22 | 0,00 · 7,14 · 0,00 |
| 2 | 7,20 | 7,26 | 14,47 | 14,47 | 0,06 · 7,20 · 0,00 |
| 3 | 7,09 | 7,17 | 14,17 | 14,25 | 0,08 · 7,00 · 0,08 |
| 4 | 7,12 | 7,12 | 14,20 | 14,20 | 0,00 · 7,08 · 0,00 |
| 5 | 7,02 | 7,09 | 14,12 | 14,19 | 0,08 · 7,03 · 0,06 |

Bu tablo A ve B'nin ortasında duruyor ve **ikisinin de saf hâli değil**: 15 adımın 10'u 0,00–0,08 sn (çift içi, kilit adımı), 5'i 7,00–7,20 sn (çiftler arası, merdiven basamağı). Beş dalganın beşinde de aynı yapı: **ikişerli çift**. Yani iki yuvaya dört istek geldiğinde yuvalar dolduğu anda eşzamanlılık baki, taşan kısım sıraya giriyor. K=2 kolunda ise C de B gibi kilit adımı: her iki istek aynı sürede bitiyor (adımlar 0,00–0,08 sn) — yuva sayısıyla istek sayısı eşitlendiğinde sıra tamamen kalkıyor.

**Koşum D — varsayılan sunucu, K = 8:**

| Tekrar | 1. istek | 2. | 3. | 4. | 5. | 6. | 7. | 8. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5,83 | 10,34 | 14,95 | 19,56 | 24,16 | 28,75 | 33,56 | 38,17 |
| 2 | 5,73 | 10,17 | 14,89 | 19,42 | 23,92 | 28,52 | 33,06 | 37,89 |
| 3 | 5,89 | 10,52 | 15,44 | 20,25 | 24,83 | 29,33 | 34,00 | 38,45 |
| 4 | 5,86 | 10,41 | 15,03 | 19,59 | 24,22 | 28,73 | 33,33 | 37,81 |
| 5 | 5,72 | 10,31 | 15,00 | 19,58 | 24,14 | 29,52 | 34,33 | 38,97 |

Beş dalganın beşinde de **sekiz basamaklı merdiven**: 35 adımın tamamı **4,44–5,38 sn**, ortalaması **4,64 sn** — A'nın K=4 merdivenindeki 4,59 sn'lik adımla aynı. D'nin ilk basamağı (~5,8 sn) öteki yedi basamaktan biraz yüksek, çünkü her dalganın ilk isteği 74 token'ın yalnız 28'ini önbellekte buluyor, kalan yedisi 73'ünü. Desen A'nın aynısı: tek yuva, sekiz istek; son istek 38,97 sn'ye kadar sırada. K=8'de ne kilit adımı ne çift var — sunucu `-np 1` olduğu için sekiz istemci tek kuyruğa giriyor.

İkinci ölçüm deseni ayırıyor — tek bir isteğin **kendi çözümleme hızı** (`eval_count / eval_duration`, beş kaydın medyanı):

| | K=1 | K=2 | K=4 | 35 kaydın bandı |
| --- | --- | --- | --- | --- |
| Koşum A (varsayılan) | 14,07 | 14,22 | 14,14 | 12,73–14,81 tok/sn |
| Koşum B (`-np 4`) | 14,97 | 9,54 | 6,38 | 4,74–15,01 tok/sn |
| Koşum C (`-np 2`) | 14,38 | 9,13 | 9,22 | 7,87–14,65 tok/sn |

A'da istek başına hız sabit, toplam duvar K ile çarpılıyor: sıralı kuyruk. B'de hız K ile düşüyor, toplam duvar sabit kalıyor: iş gerçekten paylaşılıyor. Mükemmel paralellikte dört istek tek istekle neredeyse aynı sürede (≈5,5 sn) biter, istek başına hız da 15 tok/sn'de kalırdı. Ölçülen: dalga 12,71 sn (K=1'in 2,32 katı) ve istek başına 6,38 tok/sn (14,97'nin yaklaşık %43'ü). Kazanç 4 / 2,32 = **1,73 kat** — `ozetle.py`'nin "sistem verimi K=1'in 1,73 katı" satırı bu; dört yuva dört kat hız değil, 1,73 kat hız veriyor, çünkü paylaşan tek bir CPU var.

C satırı bu sayfanın en az tahmin edilen bulgusu: **K=2 ve K=4 hızları aynı** (9,13 ve 9,22 tok/sn). Sebep desende: iki yuva dolu kaldığı sürece batch'te her zaman **iki** iş var, dördüncü istek geldiğinde batch büyümüyor, kuyruk uzuyor. Yani yuvadan çok istek gelirse istek başına hız **yuva sayısı kadar iş varmış gibi** kalmaya devam ediyor — düşen şey hız değil, sıradaki isteğin beklemesi (medyan 3,60 sn, aşağıdaki bekleme tablosu). Sistem hızı da bu yüzden 17,95 tok/sn: B'nin 20,15'inin %89'u, ama dört yuva yerine iki yuva ve 300 MB daha az bellekle.

D bu hız tablosuna dördüncü satır eklemiyor (K=1/2/4 kolları koşulmadı); tek sayı yeterli: K=8'de istek başına hız medyanı **14,15 tok/sn** (40 kaydın bandı 12,18–14,69), A'nın üç kolundaki 14,07/14,22/14,14 ile aynı. Sistem hızı 13,38 tok/sn — istemci sayısı 4'ten 8'e çıkarken toplam verimin artmadığını, yalnız kuyruğun uzadığını söylüyor.

:::tip[Üç deseni ayıran tek sütun]
Dalga süresi artıyor + tek istek hızı **sabit** = yarışma yok, sıra var (Koşum A). Dalga süresi sabite yakın artıyor + tek istek hızı **düşüyor** = paylaşım var (Koşum B). Dalga süresi artıyor + hız **düşüyor ama K=4'te K=2 ile aynı kalıyor** ve merdiven **ikişerli çift** veriyor = yuva sayısına kadar paylaşım, fazlası kuyruk (Koşum C). Bu üç imza önbellek durumundan bağımsızdır; aşağıdaki "kazanç sanılan kat" tuzağına düşmeden ayırt etmenin yolu budur. Dördüncü koşum (K=8, varsayılan) yeni bir imza üretmedi: dalga 18,43 → 38,26 sn'ye uzarken tek istek hızı 14,14 → 14,15 tok/sn'de kaldı — A'nın "sıra var, yarış yok" imzasının daha uzun hâli.
:::

## Bekleme Süresi: Ölçülenin Toplamından Çıkarılan

Her kayıt için `duvar − (load + prefill + decode)` farkını aldım. Bu **aritmetik**, yeni bir ölçüm değil; ama girdilerinin üçü de sunucudan gelen ölçülmüş alanlar. Komut `ornekler/eszamanli-olcu/README.md`'de duruyor, yani dört koşumun logundan yeniden üretilebilir.

**Koşum A — varsayılan sunucu:**

| Kol | En az bekleyen | Medyan | En çok bekleyen | 0,5 sn üzeri kayıt |
| --- | --- | --- | --- | --- |
| K=1 | 0,006 sn | 0,014 sn | 0,017 sn | 0 / 5 |
| K=2 | −0,000 sn | 2,270 sn | 4,766 sn | 5 / 10 |
| K=4 | 0,009 sn | 6,891 sn | **14,110 sn** | 15 / 20 |

K=1'de fark sıfıra iniyor (ölçüm gideri kadar), K=4'te son istek 14,11 sn **sıra bekliyor**. 35 kaydın 20'sinde bekleme 0,5 sn üzerinde — ki bu, K=2'nin beş ikinci isteği ile K=4'ün on beş sıradaki isteğinin tam sayısı. Kullanıcı diliyle: dört kişi aynı anda sorarsa son kişi cevabını **en kötü 18,75 sn**'de alıyor (p95 18,50); tek başına soran bir kullanıcı için en kötü süre 6,45 sn. Yani sıraya girmek gecikmeyi bölmez: her yeni kullanıcı, önündekilerin tamamını bekliyor.

**Koşum B — `OLLAMA_NUM_PARALLEL = 4`:**

| Kol | En az bekleyen | Medyan | En çok bekleyen | 0,5 sn üzeri kayıt |
| --- | --- | --- | --- | --- |
| K=1 | −0,002 sn | 0,019 sn | 0,022 sn | 0 / 5 |
| K=2 | 0,008 sn | 0,013 sn | 0,023 sn | 0 / 10 |
| K=4 | 0,009 sn | 0,021 sn | **0,122 sn** | 0 / 20 |

Sıra tümüyle kalkıyor: 35 kaydın **hiçbirinde** bekleme 0,5 sn'yi geçmiyor, en kötü bekleme 0,122 sn. Ama bedel başka yere taşınıyor — K=4'te her istek 12,4 sn'lik dalgayı baştan sona yaşıyor, oysa A'da ilk istek 4,7 sn'de bitiyordu. Yani: **A'da ilk kişi hızlı, son kişi yavaş; B'de herkes eşit ve aradaki kişi A'dan yavaş.** K=2'nin ilk isteği A'da 4,55–4,77 sn'de bitiyor, B'de 7,94–8,62 sn'de.

**Koşum C — `OLLAMA_NUM_PARALLEL = 2`:**

| Kol | En az bekleyen | Medyan | En çok bekleyen | 0,5 sn üzeri kayıt |
| --- | --- | --- | --- | --- |
| K=1 | 0,004 sn | 0,006 sn | 0,021 sn | 0 / 5 |
| K=2 | −0,000 sn | 0,008 sn | 0,089 sn | 0 / 10 |
| K=4 | 0,008 sn | **3,598 sn** | **7,236 sn** | 10 / 20 |

Bu tablo C'nin "yarı sıralı" olduğunu saysal olarak söylüyor: K=2 kolunda sıra yok (en kötü 0,089 sn), K=4 kolunda 20 kaydın **tam yarısı** 0,5 sn üzerine çıkıyor ve en uzun bekleme 7,24 sn — ki bu, merdiven tablosundaki çiftler arası adımın (7,00–7,20 sn) kendisi. İki ölçüm aynı şeyi iki yerden söylüyor: hızlı çift bitince yuva boşalıyor, sıradaki ikili o anda başlıyor. Medyan 3,60 sn, sınırda duran 20 kayıt için beklenen yer.

**Koşum D — varsayılan sunucu, K = 8:**

| Kol | En az bekleyen | Medyan | En çok bekleyen | 0,5 sn üzeri kayıt |
| --- | --- | --- | --- | --- |
| K=8 | 0,001 sn | 17,405 sn | **34,291 sn** | 35 / 40 |

40 kaydın 35'inde bekleme 0,5 sn'nin üzerinde; altında kalan beş kayıt her dalganın ilk isteği ve duvarları ~5,7–5,9 sn. En uzun bekleyen istek 34,29 sn — 38,97 sn'lik son isteğin kendisi. K=4'te bu hane 6,891 / 14,110 sn idi; K 4'ten 8'e çıkınca medyan bekleme 2,53 kat, en kötü bekleme 2,43 kat büyüdü. Sekiz kişi aynı anda sorduğunda cevaplar 5,7–39,0 sn aralığında sırayla geliyor; ilk kişi tek başına soranla aynı sürede bitiyor, sonuncusu yedisini bekliyor.

:::note[Eksi gördüğünüz yer ölçüm gideridir]
A'nın K=2 satırında −0,000, B'nin K=1 satırında −0,002, C'nin K=2 satırında −0,000 sn var: faz toplamları duvar süresini çok küçük bir farkla aşıyor, çünkü alanlar sunucunun ve betiğin farklı saat okumalarından geliyor. "Negatif bekleme" gerçek bir şey değil; bu hane o giderin büyüklüğünü gösteriyor.
:::

## Kazanç Sanılan Katlar: Önbellek ile Paralelliği Ayırmak

A tablosunda `sistem tok/sn` K=1'de 10,62, K=2 ve K=4'te 13,89: özet çıktısı bunu "K=2, K=1'in 1,31 katı verim" diye basıyor. **Bu sayı bir kazanç değil, bir karıştırmadır** ve bu sayfada onunla dolaşmaması için burada duruyor.

Sebep kayıtta ölçülü: ön-yüklemenin kendisi. Betik bir dalga içindeki K isteği **birbirinin aynı** metinle salıyor (denek numarası tekrar numarasından geliyor); aynı istem üst üste gidince ön-ek önbelleği hazır parça buluyor.

| Koşum | Kol | Toplam istem token'ı | Önbellekten gelen | İstek başına önbellek | `prompt_eval_duration` medyan |
| --- | --- | --- | --- | --- | --- |
| A (varsayılan) | K=1 | 370 | 140 | 28 / 74 | 1,335 sn |
| A | K=2 | 740 | 730 | 73 / 74 | 0,076 sn |
| A | K=4 | 1480 | 1460 | 73 / 74 | 0,073 sn |
| B (`-np 4`) | K=1 | 370 | 140 | 28 / 74 | 1,159 sn |
| B | K=2 | 740 | 477 | 0–73 / 74 | 1,241 sn |
| B | K=4 | 1480 | 954 | 0–73 / 74 | 2,378 sn |
| C (`-np 2`) | K=1 | 370 | 140 | 28 / 74 | 1,263 sn |
| C | K=2 | 740 | 477 | 0–73 / 74 | 1,302 sn |
| C | K=4 | 1480 | 1460 | 73 / 74 | 0,114 sn |
| D (varsayılan, K=8) | K=8 | 2960 | 2695 | 28 ya da 73 / 74 | 0,074 sn |

A'da K=1 kolu her tekrarında farklı önekle (`[denek 1]`, `[denek 2]`…) geliyor, önbellek 74 token'ın ancak 28'ini karşılıyor ve her isteğe ~1,3 sn'lik gerçek ön-yüklenme biniyor. K=2 ve K=4 kollarında tek yuva olduğu için aynı metin defalarca aynı yuvadan geçiyor: 74'ün 73'ü hazır. A'daki "1,31 kat", işte o ~1,3 sn'lik giderin iki kollarda ödenmemiş olması — çözümleme hızının üç kolda da aynı kalması (14,07/14,22/14,14) başka bir şeyin kazanmadığını söylüyor.

B'de tablo tersine dönüyor: **dört yuva dört ayrı önbellek demek.** İstekler yuvalara dağılınca bazıları soğuk yuvaya düşüyor (istek başına önbellek 0 ile 73 arasında), K=4 kolu ön-yüklemeye istek başına 2,38 sn ödüyor. Yani B'nin +45%'lik sistem hızı, önbellek avantajıyla değil, ona **rağmen** kazanılmış hız. A ile B'nin "kat" sayılarını aynı cümleye koymak bu yüzden yanlış: A'nın kâtı önbellekten, B'nin kâtı (`1,73`) yuvalardan geliyor.

C ise A ile aynı önbellek hanesini ödüyor: K=4 kolundaki **20 kaydın 20'si de** 74 token'ın 73'ünü hazır buldu, ön-yükleme medyanı 0,114 sn. Yani C'nin "sistem verimi K=1'in 1,60 katı" satırı B'nin 1,73'üyle aynı cinsten değil — bir kısmı A'daki önbellek armağanı. **Yuva sayısı ile önbellek isabeti arasındaki neden-sonuç burada ayrılmadı (ölçülmedi); görünen iki olgu: iki yuvada her istek sıcak yuvaya düşüyor, dört yuvada düşmüyor.** C'nin yuva-kazanımını tek başına anlatan sayı önbellek hanesi değil, 9,13 → 9,22 tok/sn hızının K=2'de K=4 ile aynı kalması ve bekleme medyanının 3,60 sn'ye çıkması.

D satırı bu tuzağın en büyük hâli: 40 istekte 2960 istem token'ının 2695'i önbellekten geldi; istek başına 28 (her dalganın ilk isteği) ya da 73 (kalan yedisi). Yine de K=8'in sistem hızı 13,38 tok/sn — A'nın 13,89'undan **yüksek değil**. İstemci sayısını iki katına çıkarmak tek yuvalı sunucuda sistem verimi üretmiyor; K=8 için "kazanç katı" diye yazılacak bir sayı yok, çünkü tek yuva işi paylaşmıyor, sırayla yapıyor.

:::caution[Bir dalga içindeki istekler aynı olmak zorunda değil]
Aynı soruyu K kişiye birden göndermek gerçek bir senaryo (yeniden deneme, çoğullukla örnekleme, sıcak bir sorunun yankısı). Ama gerçek çok kullanıcılı trafik birbirinden farklı istemlerle gelir; orada önbellek bu kadar cömert davranmaz, yani A'da K=1 ile K=4 arasındaki duvar farkı bu koşumdan daha **küçük** çıkar. Bu sayfanın ölçtüğü üç desen —sıralı merdiven, paylaşarak yarışı ve ikişerli kilit— önbellekten bağımsız bulgulardır; 1,31 ve 1,60 kat sayıları ise değildir.
:::

## Bellek Tarafı: Dört Yuva Kaça Mal Oluyor

Her kolun başında okunan `/api/ps`:

| | Model kopyası | Bağlam | `size` | `size_vram` |
| --- | --- | --- | --- | --- |
| Koşum A (`-np 1`) | 1 | `-c 4096` | 2 168 371 280 bayt (üç kolda da aynı) | 0 |
| Koşum D (`-np 1`, K = 8) | 1 | `-c 4096` | 2 168 371 280 bayt | 0 |
| Koşum C (`-np 2`) | 1 | `-c 8192` | 2 412 794 346 bayt (üç kolda da aynı) | 0 |
| Koşum B (`-np 4`) | 1 | `-c 16384` | 2 716 000 582 bayt (üç kolda da aynı) | 0 |

Dördünde de ikinci bir model kopyası yok — sekiz isteğin sekizi de aynı ağırlıkları paylaşıyor. D satırı yeni bir bellek noktası değil, aynı ayarın tekrarı: model kopyası, bağlam ve bayt sayısı A ile birebir aynı. Ölçünün söylediği şu: **bellek yuva sayısına bağlı, eşzamanlı istemci sayısına değil** — istemci sayısı 4'ten 8'e çıkarken `/api/ps` tek bayt değişmedi. Üç nokta artık **doğrusallık sorusunu** cevaplıyor: 1→2 yuva geçişi **+244 423 066 bayt ≈ +233 MiB**, 2→4 geçişi (iki yuva daha) **+303 206 236 bayt ≈ +289 MiB**, yani son iki yuvanın başına ≈ **145 MiB**. Bedel yuva başına eşit **değil**: ilk ek yuva, sonrakilerin yaklaşık **1,6 katı** kadar yer açıyor. Üç ölçümün toplamı 1→4 için +522 MiB. Her üç ayar da yuva başına 4096 token bağlam kuruyor (`-c 4096 / 8192 / 16384`), yani karşılaştırma bağlam başına eşitlenmiş durumda — bağlam yuvalar arasında **bölünmüyor**, toplanıyor. (Koşum B'nin yüklenme bedeli de aynı sebepten: 27,82 sn; C 17,48 sn; A 5,64 sn.)

Artışın ne kadarının KV önbelleği, ne kadarının yuva başına hesap tamponu, ne kadarının **birden çok yuvaya geçişte bir kez** açılan yapılar olduğu günlükte ayrı yazmıyor — o **ayrım ölçülmedi**. İlk ek yuvanın daha pahalı olması bu üçüncü ihtimali akla getiriyor, ama üç noktayla bir neden seçilmez; sayfa yalnız "eşit adımlarla gitmiyor" iddiasını taşıyor. Pratik sonuç: 15,9 GB'lık bu makinede B sunucusu açılışta `available="3.2 GiB"` okudu ve model 2,5 GiB yer tuttu; dört yuvayı dolduracak kadar çok model ya da uzun bağlam aynı faturayı katlar. [VRAM Hesabı](/donanim/vram-hesabi/) sayfası eşzamanlı istek sayısıyla büyüyen kalemin KV önbelleği olduğunu anlatır; artık o büyümenin **CPU'daki karşılığı da ölçülmüş** durumda — ve ölçülen karşılık sabit birim fiyat değil.

## Pratikte Ne Anlama Geliyor

- **İki sekme açmak varsayılan ayarla sunucuyu hızlandırmaz.** İkinci isteğin ilk baytını görmesi, birincinin bitişine bağlı. Tek kullanıcı için fark yok; ikinci kullanıcı için bekleme eklenir. `=2` ayarında ise iki sekme gerçekten yan yana koşuyor (C'nin K=2 kolunda bekleme en kötü 0,089 sn).
- **Sekiz kişi aynı anda sorarsa varsayılan ayar sekizini de sıraya koyar.** K=8 dalgasında cevaplar 5,7–39,0 sn aralığında geldi; sistem hızı 13,38 tok/sn'de kaldı — K=4'ün 13,89'undan yüksek değil. Tek yuva sekiz istemciye bölünmüyor, yalnız sırayla çalışıyor.
- **`OLLAMA_NUM_PARALLEL = 4` kalabalığın sırasını kaldırır, tek kişinin hızını artırmez.** K=1 kolunda ölçülen hiçbir şey iyileşmedi (5,91 → 5,51 sn; bu fark saat farkı olabilir, bkz. künye). Kazanç kalabalıkta: son kullanıcının en kötü süresi 18,50 → 13,77 sn, sistem hızı 13,89 → 20,15 tok/sn. Bedel: +522 MiB bellek, 27,8 sn'lik ilk yükleme, ve **ara kullanıcının yavaşlaması** (K=2'nin ilk isteği 4,6 sn'den 8,1 sn'ye çıkıyor).
- **Yuvadan çok istek gelirse hız değil sıra büyür — `=2` üzeri dört isteğin ölçümü.** İki yuvaya dört istek: hız 9,13 → 9,22 tok/sn sabit kalıyor (batch'te her zaman iki iş var), ilk çift 7,1 sn'de bitiyor, ikinci çift 14,2 sn'de. Dört yuvaya dört istek: hız 6,38 tok/sn'ye düşüyor, herkes 12,4-13,8 sn'de bitiyor. **En kötü kullanıcı süresi iki ayar arasında yalnız 0,7 sn farklı** (14,47 vs 13,77), ama dağılım farklı: `=2` yarısına `=4`'ten yarı yarıya hızlı cevap veriyor, öbür yarısını bekletiyor.
- **Bekleme kuyruğu mu, eşit gecikme mi — bu bir ürün kararı.** Bir kişilik sohbet uygulamasıysanız sıralı kuyruk daha iyi hissettirir: ilk cevap daha erken gelir. Kalabalık ya da toplu iş (özet çıkarma, veri temizleme) varsa yuva açmak toplam süreyi kısaltıyor. Ara seviye `=2` artık ölçümlü: iki kişiye eşzamanlı, üçüncü-dördüncü kişiye kuyruk; bellek bedeli `=4`'ün yarısından az (+233 MiB). `=3` bu makinede **ölçülmedi**.
- **Değişkeni yazmak yetmez, sunucunun yeniden başlatılması gerekir; açılış satırına bakmadan başlamayın.** Bu sayfanın ikinci ve üçüncü kolu ancak `server.log`'daki `OLLAMA_NUM_PARALLEL:4` / `:2` ve `llama-server … -np 4` / `-np 2` satırları görüldükten sonra koşuldu.
- **Eşzamanlılık gerçekten gerekirse adres CPU değil, sunum motorudur.** [Sunum API'leri](/kullanim/sunma-api/) sayfasının sürekli-kuyruk (continuous batching) karşılaştırması bu yüzden vLLM tarafına bakar; o tablodaki verim sayıları bu makinede değil, üretici ve ayrı donanım bağlamında üretilmiş sayılardır.

:::danger[Ölçülen karar ile ölçülmeyen karar aynı şey değil]
Bu sayfa "eşzamanlılık iyi/kötü" demiyor. Dediği: **bu makinede, CPU'da, tek modelle, 64 token üretimle, aynı metnin K kopyasıyla** — varsayılan ayar sıralı kuyruk yapıyor (K=8'de sekiz basamağa kadar), `=2` ikişerli çift kurup taşanı bekletiyor, `=4` kilit adımıyla eşzamanlı çalıştırıyor. Kalıcı bir serviste, farklı istemlerle gelen kullanıcılarla, uzun bağlamlarda ya da GPU'da hangi ayarın daha iyi olduğu **yine** veri değil; oradaki sayılar bu dört koşumdan taşınmaz.
:::

## Bu Sayfada Ölçülmeyenler

- `OLLAMA_NUM_PARALLEL` = **3**: ölçülmedi. Ölçülen üç nokta var (varsayılan = 1, = 2, = 4); bellek bedelinin yuva sayısıyla **eşit adımlarla** gitmediği üç noktadan görüldü (ilk ek yuva ≈ 233 MiB, sonrakiler ≈ 145 MiB), ama üç yuvanın kendi bedeli ve üçüncü desen noktası bilinmiyor. Artışın KV önbelleği ile yuva başına tampon arasındaki payı da ayrılmadı — üç noktadan bir neden seçilmez. Her seviye bu koşumun maliyetiyle (~3 dk) ve bir yeniden başlatmayla ölçülebilir; değişkeni yazmak ve sunucuyu restart etmek makine sahibinin onayıdır (kural 3).
- **K = 5, 6, 7 ve K > 8**: ölçülmedi. **K = 8 ölçüldü** (Koşum D, 2026-10-20, varsayılan sunucu): tek yuvada sekiz istemci sıraya giriyor; merdiven sekiz basamağa çıkıyor, istek başına hız 14,15 tok/sn'de kalıyor, son kullanıcı 38,17 sn bekliyor. Beş, altı ve yedide merdivenin aynı adımla uzayacağı bir **beklenti**, ölçüm değil; dokuz ve üzeri hiç denenmedi. **`=2` ve `=4` sunucularında K > 4 de ölçülmedi:** orada yuva sayısı 2 ya da 4 olduğu için beşinci isteğin sıraya mı gireceği, yoksa `OLLAMA_MAX_QUEUE` gibi bir tavanla mı karşılaşacağı bu koşumdan bilinmiyor.
- **Koşumlar aynı saate ya da ızgaraya oturtulmadı.** A sabah 10:54, B öğle 12:19, C 14:07 (hepsi 2026-10-19), D 2026-10-20 10:43. İlk üç koşumda kollar aynı `1, 2, 4` sırasıyla koşuldu; D tek kollu. Yani gün içi arka plan yükü, bellek durumu, günler arası fark ve olası termal fark, ayar farkıyla **birlikte** duruyor; rasgele sıralı bir ızgara (A-B-A-B, kol sırası karıştırılmış) ölçülmedi. Bu sayfanın taşıyabileceği iddia desen farkıdır, mutlak saniye farkı değil (bkz. künye).
- `/api/embed` eşzamanlılığı: kapsam ekseni tablosunda bu uç da vardı, dört koşumda da **koşulmadı**. Yalnız `/api/chat` ölçüldü. (Gömme isteklerinin ölçüm penceresine sızabildiği ise kanıtlı: aşağıdaki elenen C koşumu.)
- Farklı istemlerle gelen gerçek çok kullanıcılı trafik (yukarıdaki caution'ın konusu) ölçülmedi.
- `OLLAMA_MAX_LOADED_MODELS`, model yüklenirken gelen istek, önbellek tahliyesi (`keep_alive` dolması) ölçülmedi. K=8'de sekiz istek aynı kuyruğa girdi; `OLLAMA_MAX_QUEUE` sınırına (varsayılan 512) yaklaşılmadı, tavan davranışı görülmedi.
- GPU tarafı: bu makinede Vulkan keşfi çöküyor, `size_vram` dört koşumda da 0. Yani "`=2` ya da `=4` ayarı GPU'da neye mal olur" burada ölçülebilir değildi.
- Ağ gecikmesi, çok makine, kalıcı servis: kapsam dışı ([Kapsam Haritası](/kaynaklar/kapsam-haritasi/)).

## Kendi Ölçümünüzü Koşun

```bash
cd ornekler/eszamanli-olcu
PYTHONUTF8=1 python -u eszamanli_olcu.py --duman > cikti/duman-kaydim.txt 2>&1
PYTHONUTF8=1 python -u eszamanli_olcu.py --kollar 1,2,4 --tekrar 5 > cikti/benim-kaydim.txt 2>&1
# taşma kolu: tek yuvada sekiz istek × 5 tekrar = 40 ölçüm isteği (~4 dk)
PYTHONUTF8=1 python -u eszamanli_olcu.py --kollar 8 --tekrar 5 > cikti/benim-kaydim-8.txt 2>&1
PYTHONUTF8=1 python -u ozetle.py cikti/benim-kaydim.txt
```

Özetleyici kol tablolarının yanısıra **merdiven** bloğunu da basar: her dalganın sıralanmış süreleri ve adımları — bu sayfadaki desen tablolarının ham hâli. Ayrıştırma, yüzdelik ve adım hesabı Ollama'ya dokunmadan test edilir: `PYTHONUTF8=1 python -u ozetle.py --test`.

Betik başarısızlığı üretmeye çalışmaz: `/api/version` okunamazsa çıkış 2, ısıtma isteği başarısızsa çıkış 3 ve ölçüm kolları hiç başlamaz. Kayda düşen her isteğin HTTP kodu, `eval_count`'u ve hata alanı yazılır; `eval_count` 0 olan ya da 200 dönmeyen kayıt özete **girmez** ama aykırı sayı olarak görünür (`hatali` ve `eksik dalga` sütunları). GPU'nuz varsa `size_vram` sıfırdan farklı çıkacak ve tablo başka bir şey söyleyecek — o koşum bu sayfanın yerine geçmez, yanına bir satır daha ekler.

### Sunucu ayarını koşumdan önce günlükle doğrulayın

İkinci ve üçüncü kolü koşmanın ön koşulu iki satır. Değişkeni yazmak ve sunucuyu yeniden başlatmak makineyi yöneten kişinin işi (kural 3); ama **değerin gerçekten okunup okunmadığını** betik değil günlük söyler. Windows'ta kalıcı yazım: `setx OLLAMA_NUM_PARALLEL 4` (ya da `2`), ardından Ollama'yı tamamen kapatıp açmak.

```powershell
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern 'OLLAMA_NUM_PARALLEL' | Select-Object -Last 1
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern '-np' | Select-Object -Last 1
```

Birinci satır sunucunun açılışta okuduğu ortam haritası (`…OLLAMA_NUM_PARALLEL:4…`), ikinci satır model ilk yüklendiğinde kaldırılan gerçek komut satırı (`… -c 16384 -np 4 …`). Üçüncü kolda aynı iki satır `…OLLAMA_NUM_PARALLEL:2…` (13:58:33) ve `… -c 8192 -np 2 …` (13:59:19) idi. D koşumu yeni bir ayar yazmayı gerektirmedi: günlükteki son `server config` satırı 2026-10-19T14:39:48 → `OLLAMA_NUM_PARALLEL:1`, D'nin model yüklemesi de `-c 4096 -np 1`; yani D, A'nın varsayılan ayarının aynı süreçteki tekrarı. `-np` satırı model yüklenmeden görünmez, o yüzden sıra: değişkeni yaz → yeniden başlat → tek bir istek at (betiğin ısıtması yeter) → iki satıra bak. İkisi de beklediğiniz değeri gösteriyorsa ve koşumu `--sunucu "OLLAMA_NUM_PARALLEL=4 (server.log <tarih ve saat> satırı; llama-server -np 4 -c 16384)"` etiketiyle koştuysanız, kayıttaki sayılar o ayarın ölçümüdür. Günlük dolmuşsa aynı arama `server-1.log`, `server-2.log` … dosyalarında da yinelenmeli: bu sayfadaki sabah koşumunun `-np 1` satırı rotasyon sonrası orada bulundu.

### Koşumdan sonra: kirletme denetimi

Aynı Ollama örneğine koşum sırasında başka bir istek gelirse dalga süreleri artık sizin değildir. Bu makinede o ihtimal gerçek: günlükte ölçüm pencerelerinin **dışında**, 10–22 token'lık kısa istemler görünüyor; editör/ajan araçlarının gömme istekleri oldukları **düşünülüyor** — hangi aracın gönderdiği tek tek kanıtlanmadı, ama boyut dağılımı gömme çağrılarıyla uyuyor. Yalnız llama.cpp satırlarında zaman damgası yok, o yüzden denetim satır sırasıyla yapılıyor: son görülen `time=` değeri taşınır, kafesin istemi 74 token olduğu için o boyuttan sapan her yeni-istem satırı ya yabancıdır ya da betiğin kendi boşaltma çağrısı. Komut hazır:

```powershell
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 12:19:50-12:23:35
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 10:43:30-10:47:35
```

Yayımlanan dört tam koşumda da aynı imza çıktı: A, B ve C'de **37 yeni-istem satırı** (36 × 74 + 1 × 32; ısıtma + 35 ölçüm + boşaltma), D'de **42 satır** (41 × 74 + 1 × 32; ısıtma + 40 ölçüm + boşaltma). Yabancı satır yok. 74 dışında bir boyut daha görürseniz o dalganın sürelerini atın ya da pencereyi yeniden koşun.

:::danger[Bu denetim bir koşumu gerçekten el etti]
Yukarıdaki "pencerelerin dışında" cümlesi 2026-10-19 öğleden sonra bir kez yanlış oldu, çünkü **içine** düştü. `=2` ayarının ilk tam koşumu (`cikti/kirli-eszamanli-kaydi-3.txt`, pencere **14:00:46 → 14:04:15**) sunucu ayarı doğru olduğu hâlde elendi: denetim **126 yeni-istem satırı** buldu — 37'si kafese ait, **89'u yabancı** (10–22 token). Yabancılar tek bir dalga hâlinde 14:02:15-14:02:19'da geldi ve arkasında ikinci bir model bıraktı: `bge-m3`, 1 244 166 879 bayt, **14:07:33'e kadar bellekte kaldı**. Yani K=4 kolu, CPU'su tek olan bu makinede 1,2 GB'lık başka bir model yükliyken koştu; K2'nin bir dalgası da aynı saniyelere denk düştü. Bu kaydın hiçbir sayısı bu sayfada yok — ne dalga süresi, ne bellek, ne tok/sn. Elenen koşumun tek ölçülebilir katkısı, yuva sayımının da bozulduğunu göstermesi: dağılım `id 0: 111, id 1: 15` çıkmıştı, çünkü yabancı satırlar kendi sunucu proceslerinin yuva numaralarını taşıyor; yani kirlenmiş bir pencerede "yuvalar fiilen kullanıldı" kanıtı da okunamaz olur.
Yeniden koşum ne zaman başladı: betik kendi kendine beklemez. Önce `/api/ps` yanıtında model kalmadığı görüldü (10 sn aralıklı yoklama, 14:05:43'te bir model yüklü → **14:07:35'te boş**), kafes tam o anda salıverildi. Yayımlanan C koşumunun penceresi **14:07:35 → 14:11:07**, denetimi 37 satır ve 36 + 1 imzasında. Kural olarak: **başka bir araç aynı Ollama'ya istek gönderebiliyorsa ölçüm penceresi rastgele bir saatte değil, o aracın sessiz olduğu bir aralıkta koşulur** — ve bunu anlamanın tek yolu pencereyi koşumdan sonra değil, koşumdan hemen sonra denetlemek.
:::

Denetimin bedava bir yan çıktısı daha var: yuva id dağılımı. Koşum A'da 37 satırın **tamamı `id 0`** üzerinden geçmiş — tek kuyruk, tek yuva. Koşum B'de dağılım `id 0: 17, id 1: 10, id 2: 5, id 3: 5`; açılan dört yuvanın dördü de iş almış. Koşum C'de `id 0: 22, id 1: 15`; iki yuvanın ikisi de iş almış — üçüncü ve dördüncü isteğin sıraya girdiğini söyleyen bekleme tablosu, yuvaların boş durmadığını söylüyor. Koşum D'de 42 satırın **tamamı yine `id 0`**: istemci sayısı sekize çıksa da `-np 1` tek yuvanın kuyruğunu kullandı. Hangi yuvanın hangi kolda çalıştığı kol kol ayrıştırılmadı (ölçülmeyenler listesinde), ama "yuvalar fiilen kullanıldı" iddiasının kanıtı bu sayım.

### Ölçtükten sonra makineyi bulduğunuz gibi bırakın

Ayarı kapatmak da iki adım: değişkeni silmek ve Ollama'yı yeniden başlatmak. **`setx`'in silme seçeneği yok** — `setx OLLAMA_NUM_PARALLEL /D` denendi ve `ERROR: Invalid syntax. Value expected for '/D'` verdi; `/D` `reg delete`'in anahtarı. Kalıcı kullanıcı değişkenini silen iki doğru yazım:

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", $null, "User")
# ya da komut satırından:
reg delete "HKCU\Environment" /v OLLAMA_NUM_PARALLEL /f
```

Silme işi bitti mi anlamak için aynı araçla geri sorun: `reg query "HKCU\Environment" /v OLLAMA_NUM_PARALLEL` artık `ERROR: The system was unable to find the specified registry key or value` vermeli. Kapanış doğrulaması ise sunucu günlüğünün aynı iki satırıyla yapılır: `…OLLAMA_NUM_PARALLEL:…` alanında değer boş ya da 1 olmalı, bir sonraki model yüklenmesinde `-np 1` görünüyor olmalı. Betik modeli kendisi düşürüyor (`boşalt()` çağrısı, `keep_alive: 0`), ama yuva sayısı sunucunun açılış tercihi: değişkeni silip sunucuyu yeniden başlatmadan geri gelmez. Bir fark daha var — silme kaydı ve çalışan sunucuyu temizler, o **sabah açılmış olan** PowerShell/cmd pencerelerindeki kopyayı temizlemez; o pencerelerde devam edecekseniz `Remove-Item Env:OLLAMA_NUM_PARALLEL` (PowerShell) ya da `set OLLAMA_NUM_PARALLEL=` (cmd) gerekir.

:::note[Kapanış kaydı: 2026-10-19, üç ayar sonrası makine bulunduğu gibi bırakıldı]
Üçüncü kolun işi bittiğinde silme komutu yukarıdaki birinci yazımla çalıştırıldı ve dört iz alındı: (1) `reg query` HKCU'da anahtarı **bulamadı**, HKLM'de zaten hiç yoktu; (2) günlüğün son `server config` satırı `14:39:48` → `OLLAMA_NUM_PARALLEL:1`; (3) sonraki model yüklenmesi `14:41:25` → `-c 4096 -np 1`, yani sabahki Koşum A'nın komut satırıyla aynı; (4) o yüklemede `/api/ps` boyutu **2 168 371 280 bayt** çıktı — A'nın varsayılan boyutuyla bit bit aynı, kapanışın bellek tarafı da doğrulanıyor. İki dürüst not: `-np` satırını görmek için tek bir 1 token'lık istek atıldı (ölçüm değil, yoklama; model `keep_alive: 30s` ile kendi düştü, 14:42:33'te `/api/ps` boş). Ve `ollama app.exe` süreci silmeyle **aynı dakikada** (14:39:44) yeniden başlamış görünüyor — nedenini kanıtlamadık: Windows'un ortam-değişimi bildirimi tray'i yeniliyor olabilir ya da restart elle yapılmıştır. Bu yüzden kural değişmiyor: **günlükte `:1` ve `-np 1` okunmadan kapanmış sayılmaz.** 20 Ekim'deki D koşumu bu kapanışı bozmadı: yeni bir ortam değişkeni yazılmadı, sunucu aynı süreçte `:1` + `-np 1` ile kaldı ve koşum sonunda model yine tahliye edildi (`#PS_BITIS` boş).
:::

## İlgili Sayfalar

- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — tek isteğin faz dökümü (`load`, `prefill`, `decode`) ve tok/sn sayılarının asıl kaynağı.
- [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) — aynı istem on kez: önbellek davranışı ve `num_predict` tavanı.
- [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) — `keep_alive`, `num_predict`, `temperature` seçeneklerinin tanımı.
- [Sunum API'leri](/kullanim/sunma-api/) — sürekli kuyruk ve çok kullanıcılı verim karşılaştırması.
- [VRAM Hesabı](/donanim/vram-hesabi/) — KV önbelleğinin eşzamanlılıkla büyüdüğü iddiasının bağlamı.
- [Kapsam Haritası](/kaynaklar/kapsam-haritasi/) — kabul kuralları ve bu ölçümün eksen olarak nasıl sabitlendiği.

## Kaynaklar ve İleri Okuma

- [Ollama sıkça sorulanlar](https://docs.ollama.com/faq) — `OLLAMA_NUM_PARALLEL` varsayılanının 1 olduğu, sunucunun bellek ve CPU çekirdeğine göre bölüm yaptığı; son doğrulama 2026-10.
- [Ollama sohbet API'si](https://docs.ollama.com/api/chat) — `total_duration`, `prompt_eval_duration`, `eval_duration`, `prompt_eval_cached_count`, `done_reason` alanları; bu sayfadaki her faz bu alanlardan geldi.
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — CPU'da iş parçacığı ölçeklemesi ve ön-ek önbelleği; tek isteğin hız neden 14 tok/sn'de kalıyor sorusunun adresi.
- [vLLM belgeleri](https://docs.vllm.ai/) — sürekli kuyruk (continuous batching) ve eşzamanlı isteği gerçekten yarıştıran sunum deseni.
