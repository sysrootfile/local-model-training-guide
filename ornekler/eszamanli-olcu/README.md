# Eşzamanlı istek ölçümü

Aynı makinede, aynı modelde **aynı anda salıverilen** isteklerin duvar sürelerini ölçen kafes.
Sayfa: `src/content/docs/kullanim/eszamanlilik.md`.

Bu kafes **istemci tarafı** eşzamanlılığı ölçer: K iş parçacığı bir bariyerde bekler, tek seferde
salıverilir. **Sunucu tarafı** ayar olan `OLLAMA_NUM_PARALLEL` betikten okunamaz ve yazılamaz — onu
değiştirmek ve sunucuyu yeniden başlatmak makineyi yöneten kişinin işidir (Kapsam Haritası, kural 3).
Üç koşum bu ayrımı ölçtü: `eszamanli-kaydi-1.txt` sunucunun varsayılanıyla (`-np 1`),
`eszamanli-kaydi-2.txt` makine sahibinin yazdığı `OLLAMA_NUM_PARALLEL=4` ile (`-np 4`),
`eszamanli-kaydi-3.txt` aynı ayarın **`=2`** seviyesiyle (`-np 2`) koşuldu. Seviye **3 ölçülmedi**.
Dördüncü koşum (`eszamanli-kaydi-5.txt`, 2026-10-20) bu ayar ayrımının dışında bir **taşma kolu**:
K=8, kapanıştaki varsayılan sunucuda (`:1`, `-np 1`) yeniden başlatma olmadan koştu; yani sahip işi
gerektirmedi, tek değişen istemci tarafındaki istek sayısıydı.
Ayarın gerçekten okunduğu betikten değil sunucu günlüğünden doğrulanır; tarifi aşağıda.

## Koşum

```bash
cd ornekler/eszamanli-olcu

# duman: K=1 ve K=2, birer tekrar (~40 sn)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --duman > cikti/duman-kaydi.txt 2>&1

# tam koşum: 1, 2, 4 × 5 tekrar = 35 ölçüm isteği (~3 dk)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --kollar 1,2,4 --tekrar 5 > cikti/eszamanli-kaydi-1.txt 2>&1

# aynı koşum, sunucu ayarı elle yazıldıktan ve Ollama yeniden başlatıldıktan sonra
# (etiket kaydın #BASLIK satırına girer; ölçüm değil, künyedir — günlükle doğrulanır)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --duman --sunucu "OLLAMA_NUM_PARALLEL=4" > cikti/duman-kaydi-2.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --kollar 1,2,4 --tekrar 5 --sunucu "OLLAMA_NUM_PARALLEL=4 (server.log 2026-10-19T12:15:11 server config satiri; llama-server -np 4 -c 16384)" > cikti/eszamanli-kaydi-2.txt 2>&1

# üçüncü ayar (=2): aynı komut, yeni etiket ve yeni günlük satırı.
# ÖNCE /api/ps boş mu diye bakılır — üçüncü koşumun ilk denemesi dışarıdan gelen
# istekler yüzünden elendi, tarifi aşağıdaki "kirletme" bölümünde.
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --duman --sunucu "OLLAMA_NUM_PARALLEL=2 (server.log 2026-10-19T13:58:33.133 satiri; -np degeri asagida)" > cikti/duman-kaydi-3.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --kollar 1,2,4 --tekrar 5 --sunucu "OLLAMA_NUM_PARALLEL=2 (server.config 2026-10-19T13:58:33.133 + llama-server -c 8192 -np 2, gunluk 13:59:19.800)" > cikti/eszamanli-kaydi-3.txt 2>&1

# K=8 taşması: kapanıştaki varsayılan sunucuda — DEĞİŞKEN YAZILMADI, RESTART YOK.
# Aynı koşumdan önce /api/ps boş mu diye bakılır; etiket sunucunun son 'server config'
# satırını (2026-10-19T14:39:48, :1) ve o günkü model yüklemesini (-c 4096 -np 1) taşır.
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --duman --sunucu "varsayilan: server.log 2026-10-19T14:39:48 OLLAMA_NUM_PARALLEL:1; 14:41:25 -c 4096 -np 1" > cikti/duman-kaydi-4.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --kollar 8 --tekrar 5 --sunucu "varsayilan: server.log 2026-10-19T14:39:48 OLLAMA_NUM_PARALLEL:1; 14:41:25 -c 4096 -np 1; 2026-10-20 kosumu, yeniden baslatma yok" > cikti/eszamanli-kaydi-5.txt 2>&1

# özeti logdan yeniden hesapla
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u ozetle.py cikti/eszamanli-kaydi-1.txt

# özetleyicinin kendi testi (Ollama'ya hiç bağlanmaz)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u ozetle.py --test
```

## Ayarı doğrula, sonra kirletmeyi denetle

Koşumdan **önce** sunucunun gerçekten o ayarla açıldığı günlükten okunur (`server config` satırı
ortam haritasını, `-np` bayrağı fiilen açılan yuva sayısını taşır; ikinci satır model ilk
yüklendiğinde görünür, o yüzden önce tek bir istek atılır):

```powershell
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern 'OLLAMA_NUM_PARALLEL' | Select-Object -Last 1
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern '-np' | Select-Object -Last 1
```

Günlük dolmuşsa aynı arama `server-1.log`, `server-2.log` … dosyalarında yinelenir (sabah koşumunun
`-np 1` satırı rotasyon sonrası `server-1.log`'da bulundu). Üç koşumun üçü de bu iki satırla
doğrulandı: `12:15:11` → `OLLAMA_NUM_PARALLEL:4` + `-np 4 -c 16384`, `13:58:33` → `:2` +
`-c 8192 -np 2` (ikincisi `13:59:19.800`'da), sabahki ise `-np 1 -c 4096`. Dördüncü koşum (K=8) yeni
bir satır üretmedi: sunucu kapanıştan beri yeniden başlamadığı için etiket 19 Ekim'in kapanış
satırlarını (`14:39:48` → `:1`, `14:41:25` → `-c 4096 -np 1`) taşıyor; 20 Ekim'in iki
`starting llama-server` satırı da (10:42:06 duman, 10:43:35 tam koşum) `-c 4096 -np 1` diyor.
Kapanışta geri alma:
değişkeni silmek + yeniden başlatma, sonra aynı iki satırın `1` / `-np 1` döndüğünün okunması.
`setx`'in silme bayrağı **yoktur** (`setx OLLAMA_NUM_PARALLEL /D` → `ERROR: Invalid syntax. Value expected for '/D'`); doğrusu
`[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", $null, "User")` ya da `reg delete
"HKCU\Environment" /v OLLAMA_NUM_PARALLEL /f`, doğrulaması `reg query "HKCU\Environment" /v
OLLAMA_NUM_PARALLEL` (anahtar bulunamadı hatası beklenir).

Kapanış 2026-10-19'da birinci yazımla uygulandı ve dört izi bıraktı: HKCU'da anahtar yok (HKLM'de hiç
yoktu), `server.log 14:39:48` → `OLLAMA_NUM_PARALLEL:1`, `14:41:25` model yüklenmesi → `-c 4096 -np 1`
(sabahki A koşumuyla aynı satır), o yüklemede `/api/ps` → 2 168 371 280 bayt = A'nın varsayılan boyutu.
`-np` satırını görmek için tek bir 1 token'lık yoklama isteği atıldı (ölçüm değil; `keep_alive: 30s`,
14:42:33'te `/api/ps` boş). Gözlem, nedeni kanıtsız: `ollama app.exe` silmeyle aynı dakikada (14:39:44)
yeniden başlamış görünüyor — ortam-değişimi bildirimi tray'i yeniliyor olabilir ya da restart elle
yapılmıştır; kural bu yüzden değişmiyor, günlükteki `:1` + `-np 1` okunmadan kapanmış sayılmaz.

Koşumdan **sonra** pencereye dışarıdan istek girip girmediği `--kirletme` ile sayılır. Kafesin
istemlerinin token boyutu biliniyor (74), llama.cpp satırlarında ise zaman damgası yok; denetim
satır sırasını tarayarak son görülen `time=` etiketini yeni-istem satırlarına taşır:

```powershell
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 12:19:50-12:23:35
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 14:07:30-14:11:20
python -X utf8 ozetle.py --kirletme "$env:LOCALAPPDATA\Ollama\server.log" --istem 74 --pencere 10:43:30-10:47:35
```

Çıktı: toplam satır, istem token boyutlarının dağılımı, yuva id dağılımı ve 74'ten sapan satırların
saat/id/boyut dökümü. 32 token'lık satır betiğin kendi model boşaltma çağrısıdır (pencerenin en
sonunda çıkar), yani "beklenmeyen" listesi otomatik hüküm değil, ayrılacak bir listedir. Yayımlanan
dört tam koşumun dördü de aynı imzayı verdi: üçünde **37 yeni-istem satırı, 36'sı 74 token, 1'i 32
token**; K=8 koşumunda **42 satır, 41'i 74 token, 1'i 32 token** (sekiz yerine bir ısıtma + 40 ölçüm).
Yan çıktı olarak yuva id dağılımı da kanıt taşır: `-np 1` penceresinde A'nın 37 satırının tamamı
`id 0`, D'nin 42 satırının tamamı yine `id 0`; `-np 4` penceresinde `id 0: 17, id 1: 10, id 2: 5,
id 3: 5`, `-np 2` penceresinde `id 0: 22, id 1: 15`.

Bu denetim bir koşumu gerçekten el etti: `=2` ayarının **ilk** tam koşumu (`kirli-eszamanli-kaydi-3.txt`,
pencere 14:00:46 → 14:04:15) 126 yeni-istem satırı verdi — 37'si kafese ait, **89'u yabancı** (10–22
token, tek dalga hâlinde 14:02:15-14:02:19). Yabancılar ikinci bir model de bıraktı: `bge-m3`,
1 244 166 879 bayt, 14:07:33'e kadar bellekte. Kayıt atıldı, tek bir sayısı bile yayımlanmadı;
yeniden koşmadan önce `/api/ps` 10 sn aralıkla yoklandı (14:05:43'te model hâlâ yüklü → 14:07:35'te
boş) ve kafes ancak o zaman salıverildi. Elenen koşumdan çıkan ders: kirlenmiş bir pencerede yuva
sayımı da okunamaz olur (`id 0: 111, id 1: 15` — yabancı satırlar kendi proceslerinin yuva
numaralarını taşır), yani "yuvalar fiilen kullanıldı" kanıtı ancak temiz pencerede kanıttır.

Yönlendirme doğrudan `>` ile; `| tee` bu projede bir koşumun çıktısını yok etti. `-u` olmadan çıktı
tamponda kalır, koşum sürerken log boş görünür. Üçüncü koşumda başka bir kaza daha oldu: arka planda
koşan blok, yönlendirmeyi kendi yakaladığı dosyaya aldığı için `eszamanli-kaydi-3.txt` boş kaldı;
kayıt `grep '^#'` ile o yakalardan yeniden kuruldu ve `ozetle.py` çıktısının ham dosyayla birebir
aynı olduğu `diff` ile doğrulandı — yani yayımlanan C logu **filtrelenmiş bir kopyadır**, betiğin
doğrudan yazdığı bir dosya değil. Koşum sırasında **başka Ollama isteği göndermeyin**
ve makineye ağır bir iş bindirmeyin: bu kafes tam olarak yarışan isteğin etkisini ölçüyor, sizin
yarışınız ölçümü bozar.

## Seviye 3: sahip tarafının hazırlık bloğu

Ayarı **yazmak ve sunucuyu yeniden başlatmak makine sahibinin işidir** (kural 3); bu depo o iki adımı
hiç koşmadı. Aşağıdaki blok, o iki adımı tek yapıştırmaya indirmek için yazıldı — betik tarafında
yapılacak tek şey son komut satırı.

**Bu blokta satırların nereden geldikleri:** `Select-String` satırları,
`[Environment]::SetEnvironmentVariable(…)` ve `reg query` satırı bu dosyada **daha önce koşuldu** — üç
kapanış da onlarla doğrulandı. Son koşum satırı B ve C koşumlarının biçimi, yalnız etiketi ve dosya adı
yeni. `setx OLLAMA_NUM_PARALLEL 3` ise bu depoda önceki koşumlarda yazılmamış bir komuttur: `setx`'in
**yazma** biçimi Windows'un kendi yardımıyla sabit, silme biçimi değil (aşağıdaki not). Yani bu blok
yayımlanmış bir koşum değil, koşulmamış bir hazırlıktır; satırların kanıtı ilk gerçek koşumda yazılacak.

```powershell
# 1) SAHİP: ayarı yaz (setx yeni pencereye değil, oturum kaydına yazar)
setx OLLAMA_NUM_PARALLEL 3

# 2) SAHİP: Ollama'yı tamamen kapatıp yeniden başlat. Bu makinede Ollama bir tray uygulaması,
#    Windows servisi yok; yani restart tray'den çık + yeniden aç demektir. Eski süreç ayakta
#    kalırsa ayar okunmaz: env yalnız sunucu AÇILIŞINDA okunur.

# 3) SAHİP/koşan: ayarın gerçekten okunduğunu günlükten doğrula (ikinci satır model ilk
#    yüklendiğinde görünür; 1 token'lık tek bir yoklama isteği atmadan -np satırı gelmez)
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern 'OLLAMA_NUM_PARALLEL' | Select-Object -Last 1
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern '-np' | Select-Object -Last 1
```

Beklenti iki satır: `OLLAMA_NUM_PARALLEL:3` ve `-np 3`. Bağlam boyutu için tahmini bir sayı söylemiyoruz:
açılışların üçü `-c` = 4096 × yuva sayısı kurdu (4096 / 8192 / 16384), yani `=3`'te `-c 12288` **beklenir**
— bu türetilmiş bir sayıdır, ölçüm değil; saparsa sapmanın kendisi yazılır. Üç yuvanın bellek bedeli
hiç ölçülmedi, o yüzden burada boş bir hane olarak duruyor.

Doğrulama satırları okunmadan koşum açılmaz; açılırken de bir kapı daha var: `GET /api/ps` boş olmalı
(`POST` deneme, `JSONDecodeError` verir). C koşumu tam bu kapıdan geçti: elenen denemeden sonra
`/api/ps` 10 sn aralıkla yoklandı, 14:05:43'te model hâlâ yüklüydü, 14:07:35'te boşaldı ve kafes ancak
o zaman salıverildi. Yani boş `/api/ps` **gerekli ama tek başına yeterli değil** — kapanıştaki
`--kirletme` sayımı şart, çünkü C'nin ilk denemesi kapıyı geçtikten sonra pencereye giren yabancı
istekler yüzünden elendi. Açıldıktan sonra koşan tarafın tek komutu:

```bash
cd ornekler/eszamanli-olcu
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --kollar 1,2,4 --tekrar 5 --sunucu "OLLAMA_NUM_PARALLEL=3 (server.log <ZAMAN DAMGASI> server config satiri; llama-server -c <okunan> -np 3)" > cikti/eszamanli-kaydi-4.txt 2>&1
```

Etiketteki `<...>` yer tutucuları **günlükten okunan gerçek değerlerle** doldurulur; önce duman koşumu
(`--duman --sunucu "…"`, ~40 sn) yapılır. Koşum ~3,5 dk sürer: 35 istekli üç tam koşum 3 dk 46 sn (A),
3 dk 31 sn (B), 3 dk 32 sn (C) — ve o süre boyunca makineye ağır bir iş bindirilemez, başka Ollama
isteği gönderilemez. Kirletme denetimi kapanıştan önce koşular; `=2`'nin ilk tam koşumu tam bu
denetimle elenmişti (`kirli-eszamanli-kaydi-3.txt`).

Kapanış aynı iki adımla geri alınır ve **üç iz** ister: `[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", $null, "User")`
(silme bayrağı olmadığı için `setx … /D` kullanılmaz), yeniden başlatma, sonra aynı iki `Select-String`
satırının `:1` + `-np 1` döndüğünün okunması. `reg query "HKCU\Environment" /v OLLAMA_NUM_PARALLEL`
"anahtar bulunamadı" hatası vermeli ve zaten açık olan terminallerde kalan kopya için `Remove-Item Env:OLLAMA_NUM_PARALLEL`
(günlükte `:1` + `-np 1` okunmadan seviye 3 kapatılmış sayılmaz).

## Kollar

| Kol | Ne | Not |
| --- | --- | --- |
| Isıtma | 1 istek, ölçüm dışı | model belleğe alınır; kollar o modelin üstünde başlar |
| K=1 | 5 dalga × 1 istek | taban; tek isteğin kendi süresi |
| K=2 | 5 dalga × 2 istek | bariyerle aynı anda |
| K=4 | 5 dalga × 4 istek | bariyerle aynı anda |
| K=8 | 5 dalga × 8 istek | yalnız varsayılan sunucuda (`-np 1`) koşuldu; taşma kolu |

Sabitler: `qwen2.5:3b-instruct-q4_K_M`, `/api/chat`, `http://127.0.0.1:11434`,
`temperature: 0.0`, `num_predict: 64`, `keep_alive: "10m"`, dalga arası 3 sn, bariyer tavanı 30 sn,
istek zaman aşımı 900 sn. Bir dalga içindeki K istek **birbirinin aynı metindir** (denek numarası
tekrar numarasından gelir) — tekrarlar arasında önbellek kirlenmesin diye istem önekle ayrılır. Bu
tercih ön-yüklemeyi kol içinde neredeyse bedava yapar; sayfa o karıştırmayı ayrı bir başlıkta
açıklıyor.

İlk üç kol (K=1/2/4) üç sunucu ayarında da aynı koşuldular; K=8 yalnız varsayılanda koştu. Taşma iki
yerde ölçüldü: `-np 2` ayarında K=4 (dört istek iki yuvaya) ve `-np 1` ayarında K=8 (sekiz istek tek
yuvaya). İlki sıraya girmeyle paylaşmanın karışımını, ikincisi saf merdiveni veriyor.

## Kayıt Biçimi

Tek dosya; her satır `#ETİKET {json}` biçiminde:

| Satır | İçerik |
| --- | --- |
| `#BASLIK` | sürüm, model, kollar, seçenekler, `sunucu_etiketi` + o etiketin ölçüm olmadığı uyarısı |
| `#ISITMA` | ısıtma isteğinin kaydı (özet dışı) |
| `#KAYIT` | istek başına: `k`, `tekrar`, `no`, `bariyer_sn`, `duvar_sn`, `total_sn`, `load_sn`, `prefill_sn`, `decode_sn`, `prompt_eval_count`, `prompt_eval_cached_count`, `eval_count`, `done_reason`, `http_kod`, `hata`, `cevap_uzunluk` |
| `#DALGA` | dalga başına: `yapilan_sn` (makespan), `beklenen`, `tamamlanan`, `hata_sayisi` |
| `#PS_KOL` | her koldan önce `/api/ps` dökümü (model tek kopya mı, `size_vram` kaç) |
| `#BOSALT`, `#PS_BITIS` | koşum sonunda model tahliyesi ve tahliye sonrası doğrulama |
| `#BITIS` | zaman, toplam kayıt, ölçülen dalga süresi toplamı |

`ozetle.py` yalnız `#KAYIT` ve `#DALGA` satırlarını okur. p50/p95 **en yakın mertebe** yöntemiyle
hesaplanır (`indeks = tavan(p·n) − 1`), yani n=5'te p95 = maksimum. Hatalı sayılan kayıt: HTTP 200
dışı, `hata` dolu **ya da** `eval_count` 0 — üçü de özetten düşer, `hatali` ve `eksik dalga`
sütunlarında görünür. Kayıttaki `#DALGA.tamamlanan` ile `#KAYIT` sayısının farkı `eksik dalga`dır.

## Kayıtlar

- `cikti/duman-kaydi.txt` — duman koşumu: kollar 1 ve 2, tek tekrar, 3 kayıt; bittiği an **10:53:39**,
  ölçülen dalga süresi 14,88 sn. Amacı uçtan uca bir kayıt ürettiğini görmekti; sayfadaki hiçbir sayı
  bu dosyadan alınmadı.
- `cikti/eszamanli-kaydi-1.txt` — **Koşum A, varsayılan sunucu (`-np 1`).** 2026-10-19
  10:54:14 → 10:58:00, Ollama 0.40.6, 35 ölçüm isteği + 1 ısıtma, ölçülen dalga süresi 168,37 sn,
  sıfır hatalı kayıt, koşum sonunda model tahliye edildi (`#PS_BITIS` boş).
- `cikti/duman-kaydi-2.txt` — `OLLAMA_NUM_PARALLEL=4` sunucusunun duman koşumu: 3 ölçüm isteği,
  15,19 sn; sayfadaki sayılar bu dosyadan alınmadı.
- `cikti/eszamanli-kaydi-2.txt` — **Koşum B, `-np 4` sunucusu.** 2026-10-19 12:19:56 → 12:23:27,
  35 ölçüm isteği + 1 ısıtma, ölçülen dalga süresi 131,78 sn, sıfır hatalı kayıt, model tahliye edildi.
  Isıtmanın `load_sn` değeri 27,8168 sn: dört yuvanın kurulma bedeli ölçümden önce burada görünüyor.
- `cikti/duman-kaydi-3.txt` — `OLLAMA_NUM_PARALLEL=2` sunucusunun duman koşumu: 3 ölçüm isteği,
  15,28 sn; sayfadaki sayılar bu dosyadan alınmadı.
- `cikti/eszamanli-kaydi-3.txt` — **Koşum C, `-np 2` sunucusu.** 2026-10-19 14:07:35 → 14:11:07,
  35 ölçüm isteği + 1 ısıtma, ölçülen dalga süresi 141,88 sn, sıfır hatalı kayıt, model tahliye edildi.
  Isıtma duvar 23,828 sn / yüklenme 17,4792 sn. `/api/ps` üç kolda da 2 412 794 346 bayt,
  `size_vram` 0. Yukarıda anlatıldığı gibi bu dosya ham yakalardan `grep '^#'` ile kuruldu.
- `cikti/kirli-eszamanli-kaydi-3.txt` — **elendi, yayımlanmadı.** Aynı ayarın ilk tam koşumu
  (14:00:46 → 14:04:15, ölçülen dalga süresi 153,52 sn). Kirletme denetimi pencereye 89 yabancı istek
  girdiğini ve `bge-m3`'ün 14:07:33'e kadar bellekte kaldığını gösterdi. Kanıt olarak duruyor;
  hiçbir sayısı sayfaya girmedi.
- `cikti/duman-kaydi-4.txt` — K=8 duman koşumu: 8 ölçüm isteği, ölçülen dalga süresi 38,078 sn;
  ısıtma duvar 36,609 sn / yüklenme 29,8475 sn. Sayfadaki sayılar bu dosyadan alınmadı.
- `cikti/eszamanli-kaydi-5.txt` — **Koşum D, varsayılan sunucu, K = 8.** 2026-10-20 10:43:35 →
  10:47:30, Ollama 0.40.6, 40 ölçüm isteği + 1 ısıtma (duvar 27,906 sn / yüklenme 21,2176 sn),
  ölçülen dalga süresi 191,3 sn, sıfır hatalı kayıt, `/api/ps` 2 168 371 280 bayt ve `size_vram` 0,
  koşum sonunda model tahliye edildi (`#PS_BITIS` boş). Sunucu 19 Ekim kapanışından (14:39:48) beri
  yeniden başlatılmadı, aynı süreçte `:1` ve `-c 4096 -np 1` ile koştu; dumanı `duman-kaydi-4.txt`.

Makine: AMD Ryzen 5 2600 (6 çekirdek/12 iş parçacığı), 15,9 GB RAM, SATA SSD, %100 CPU
(`size_vram` = 0). Radeon RX 570 bu kafeste kullanılmadı; GPU kolları ayrı onay ister.

## Bekleme hanesi (aritmetik, yeni ölçüm değil)

Sayfadaki "sıra bekleyen saniye" tablosu `duvar − (load + prefill + decode)` farkıdır. Girdilerin
üçü de sunucudan gelen ölçülmüş alanlar, ama sonuç **hesap**, o yüzden kaynağı ayrı tutmak gerekir:

```bash
python - cikti/eszamanli-kaydi-1.txt cikti/eszamanli-kaydi-2.txt cikti/eszamanli-kaydi-3.txt cikti/eszamanli-kaydi-5.txt <<'PY'
import json, statistics, sys
from collections import defaultdict
for dosya in sys.argv[1:]:
    k = defaultdict(list)
    for c in open(dosya, encoding="utf-8"):
        c = c.strip()
        if not c.startswith("#KAYIT "):
            continue
        r = json.loads(c[len("#KAYIT "):])
        if r.get("hata") or r.get("http_kod") != 200 or not (r.get("eval_count") or 0):
            continue
        k[int(r["k"])].append(float(r["duvar_sn"]) - float(r["load_sn"])
                              - float(r["prefill_sn"]) - float(r["decode_sn"]))
    print(dosya)
    for s in sorted(k):
        v = sorted(k[s])
        print("  K={0} n={1} min={2:.3f} medyan={3:.3f} maks={4:.3f} 0.5sn uzeri={5}".format(
            s, len(v), v[0], statistics.median(v), v[-1], sum(1 for x in v if x > 0.5)))
PY
```

Dört kayıtta da koşuldu ve sayfadaki tabloları birebir verdi: A'da `K=4 → 0,009 / 6,891 / 14,110` ve
0,5 sn üstü 15 kayıt, B'de `K=4 → 0,009 / 0,021 / 0,122` ve 0 kayıt, C'de `K=4 → 0,008 / 3,598 /
7,236` ve 10 kayıt, D'de `K=8 → 0,001 / 17,405 / 34,291` ve 35 kayıt. `min` sütununda eksi görünen
değerler (−0,000, −0,002) sıfırdan kısa sürmüş bir
şeyi anlatmaz: fark, dört ondalığa yuvarlanmış dört alanın toplamından çıktığı için taşıdığı yuvarlama
gideridir.

## Ölçülmeyenler

- `OLLAMA_NUM_PARALLEL` = **3**. İki uç ve orta seviye ölçüldü (varsayılan, `=2`, `=4`); seviye 3
  hiç koşulmadı. Koşum tarifi (sahip tarafının iki adımı + koşan tarafın tek komutu) yukarıdaki
  **Seviye 3: sahip tarafının hazırlık bloğu** başlığında duruyor. Bellek bedelinin yuva sayısıyla büyümesi üç noktadan çıktı ama **eşit adım değil**
  (1→2 ≈ +233 MiB, 2→4 ≈ +145 MiB/yuva) ve hangi yuva aralığının neden farklı olduğu ayrılmadı.
- **K = 5, 6, 7 ve K > 8 salınmadı.** Taşma iki yerde ölçüldü: `-np 2` üzerine dört istek ve `-np 1`
  üzerine sekiz istek. Dört yuvaya beşinci isteğin gelişi, K=8'in üstü ve `=2` / `=4` sunucularında
  K > 4 hâlâ görülmedi.
- Bağlam boyutu ayrı bir kol olarak koşmadı: sunucu üç açılışta toplam `-c 4096 / 8192 / 16384` kurdu
  (yuva başına 4096 token üçünde de aynı), yani bağlam yuvalar arasında bölünmüyor, toplanıyor. Başı
  ve sonu dolu bir bağlamla yarışan isteklerin süresi ölçülmedi.
- Farklı istemlerle gelen karışık trafik, `/api/embed` eşzamanlılığı, çok model, `OLLAMA_MAX_LOADED_MODELS`.
  (`bge-m3` bu kafeste ölçüm objesi olarak değil, elenen koşuma sızmış kirletici olarak görüldü.)
- Bellek baskısı ve tahliyesi: dört koşumda da model bellekte kaldı, `keep_alive` hiç dolmadı.
- Koşumlar farklı saatlerde (D bir gün sonra sabah) koşuldu ve kol sırası sabit tutuldu: gün içi arka
  plan yükü ile ayar etkisi **ayrıştırmalı** değil.
- Önbellek hediyesi ile yuva kazancı ayrıştırmalı değil: C'deki "1,60 kat" sistem sayısının bir
  bölümü A'daki önbellek kârına benziyor; önbellek sıcaklığının yuva sayısıyla neden-sonuç ilişkisi
  ölçülmedi.
