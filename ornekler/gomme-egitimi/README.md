# Gömme modeli eğitimi ölçüm kafesi

Sitenin [Gömme Modeli Eğitmek](../../src/content/docs/rag/gomme-egitimi.md)
sayfasındaki tüm sayıların geldiği kafe. GPU yok: eğitim, değerlendirme ve
LoRA CPU'da koşar. Karşılaştırma için yerel Ollama'daki `bge-m3` yalnız
**gömme üretmek** için çağrılır (üretim modeliyle konuşulmaz).

## Ne Ölçülür?

| Kol | İçerik |
| --- | --- |
| **A** | Sıradan atış: MiniLM (118M) ve bge-m3 (566M) aynı 8 soru / 24 parça kümesinde; dört puanlama biçimi (normalize kosinüs / negatif Öklid, ham nokta / negatif Öklid); sorgu öneki etkisi; `max_seq_length` 128 vs 512 kesinti hücresi; yükleme süresi, RSS, encode hızı |
| **B** | Altı eğitim kolu: 30 / 120 / 240 adım, `lr` 2e-5, zor negatif madenciliği (`mine_hard_negatives`) 240 adım, `lr` 1e-4 240 adım, tohum 5678 240 adım. Her kolda ÖNCE/SONRA hit@1, hit@3, MRR, doğru bandı, en iyi yanlış, ayrışma, eğitim çiftlerinin kosinüs değişimi (ezber), adım süresi, RSS |
| **C** | LoRA: `r=16, alpha=32, dropout=0,05`, hedef modüller `query`+`value`; eğitilebilir parametre sayısı ve oranı, eşleşen modül sayısı, adım süresi, diske yazılan adaptör vs indirilen taban ağırlık MB |
| **D** | Batch 8 vs 32: aynı 240 adımda süre, adım başına saniye, sıra başına ms ve aynı test metrikleri (in-batch negatif sayısı etkisi) |
| **E** | `/api/embed` gideri: aynı 24 parçayı tek istekte vs 24 ayrı istekte gönderme; beşer tekrar, dönüşümlü sıra; yan başına p50/p95/min-maks/toplam duvar, istek başına p50/p95, sunucu süreleri; ön kayıtlı min-maks aralık kuralı |

## Koşum

```bash
# tam koşum: 42,4 dk, dört kol sırayla (kol a 40 sn, kol b 1628 sn, kol c 155 sn, kol d 723 sn)
# not: --kol hepsi A-D'yi koşar; E ayrı çağrılır (42 dk'lık eğitim koşumu değişmesin)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u kos.py > cikti/kos-iz.txt 2> cikti/kos-iz-err.txt

# tek kol
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol a  > cikti/kol-a.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol b  > cikti/kol-b.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol c  > cikti/kol-c.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol d  > cikti/kol-d.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol e  > cikti/kol-e.txt 2>&1

# duman: her kolda 8 adım, iki kol (B'de ilk iki kol) — ~2 dk
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol b --duman > cikti/duman.txt 2>&1

# kol e duman: tek tekrar, 25 ölçüm isteği — hüküm kurmaz
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol e --duman > cikti/duman-e.txt 2>&1
```

Yönlendirme doğrudan `>` ile yapılır (`| tee` bu projede uzun bir koşumun
kaydını kaybetti), `-u` olmadan çıktı tamponda kalır. Betik ağırlıkları
`../../.hfcache` içine indirir (`HF_HOME` betiğin kendisinde kuruludur);
Ollama'ya yalnız `http://127.0.0.1:11434/api/embed` ile gider, dışarıya
istek atmaz.

## Kol E ön kaydı (2026-10-20, koşumdan önce)

Kapsam Haritası'ndaki "`/api/embed` isteğin başına düşen gider" satırının
kabul kriteri koşumdan önce şu hâle getirildi:

- **Yanlar.** Aynı 24 parça (`GEVDE`), aynı `bge-m3`, aynı süreç. `batch`: 24
  metin tek `/api/embed` isteğinde. `teker`: her metin ayrı istekte, toplam 24
  istek. İki yan da beşer kez ölçülür; sıra tekrarlar arasında dönüşümlü
  (1/3/5: batch→teker, 2/4: teker→batch).
- **Sayılan istekler.** 5 × (1 + 24) = 125. Baştaki tek ısıtma ve sondaki
  `keep_alive: 0` tahliye isteği sayılmaz; ikisi de logda ayrı satırdır.
- **Ölçülen birim.** Her yan için tekrar toplamlarının p50 / p95 / min / maks /
  ortalaması ve toplam duvar süresi; teker yanında ayrıca istek başına
  p50 / p95. Sunucunun `total_duration` ve `load_duration` alanları ayrı
  yazılır, duvar saatiyle karıştırılmaz.
- **Ön kayıtlı hüküm.** İki yanın beş tekrar toplamının **min–maks aralıkları
  çakışıyorsa** "fark ölçülemedi" yayımlanır — o da yayımlanmış sonuçtur.
  Çakışmıyorsa p50'si düşük olan yan kazanır. Kural koşumdan önce burada ve
  Kapsam Haritası'nda yazılı; koşumdan sonra değiştirilmez.
- **Eski 15,77 sn taban değildir.** O sayı 0.40.4'te, ilk (soğuk) çağrıda,
  farklı bir istek biçiminde alındı; bu karşılaştırmanın iki yanı da aynı
  oturumda 0.40.6'da birlikte ölçülür.
- **Duman.** `--duman` tek tekrar koşar (25 ölçüm isteği) ve hüküm kurmaz;
  yalnız boru hattını sınar.

## Bağımlılıklar

`torch` 2.7+ CPU wheel'ları bu makinede `WinError 1114` verir (VC++ çalışma
zamanı 14.29); `2.6.0+cpu` sabitlendi. `sentence-transformers` 3.x hattı
`huggingface-hub`'ı düşürüp `datasets 5.1.0`'ı kırdığı için 6.x kullanıldı.

```bash
../../.venv/Scripts/python.exe -m pip install "torch==2.6.0+cpu" --index-url https://download.pytorch.org/whl/cpu
../../.venv/Scripts/python.exe -m pip install "sentence-transformers==6.1.0" transformers==5.20.1 peft==0.21.2 psutil
```

Koşumda kullanılan sürümler: `torch 2.6.0+cpu`, `transformers 5.20.1`,
`sentence-transformers 6.1.0`, `peft 0.21.2`, `datasets 5.1.0`,
`accelerate 1.15.0`, `numpy 2.4.6`, `psutil 7.2.2`, `huggingface-hub 1.33.0`.

## Kayıtlar

2026-10-17 koşumu: A → B → C tek `kos.py` koşumunda (başlangıç 15:03:25, satır
satırı `kos-iz.txt`), D ayrı çağrıyla koşuldu (15:33:49 → 15:45:52). Kol A, betik
yamalandıktan sonra **yeniden** koşuldu (15:46:48 → 15:47:28) ve `kol-a.txt`'i
ezdi; `kos-iz.txt`'teki "kol a: 40 sn" satırı ilk (silinen) koşuma ait.

- `cikti/kol-a.txt` (15:46:48 → 15:47:28, 40,47 sn), `kol-b.txt` (15:04:06 → 15:31:12,
  1628 sn), `kol-c.txt` (15:31:14 → 15:33:47, 155 sn), `kol-d.txt` (15:33:49 →
  15:45:52, 723 sn) — **sitedeki tablolar buradan alındı.** Ham tqdm ilerleme
  satırları logun içindedir; ölçüm satırları iki boşlukla başlar.
- `cikti/kol-a.json` … `kol-d.json` — aynı sayıların makine okunur hâli.
- `cikti/lora-adapter/` — Kol C'nin diske yazdığı LoRA adaptörü.
- `cikti/chk-*` — eğitim öğreticisinin (trainer) boş ara klasörleri; silinebilir
  (bu depoda 2026-10-17'de silindi).

2026-10-20 koşumu (yalnız E): duman 11:45:23 → 11:45:50 (26,24 sn, tek tekrar,
25 ölçüm isteği), tam koşum 11:45:59 → 11:46:56 (57,74 sn, 125 ölçüm isteği).
İkisi de varsayılan sunucuda (`-np 1`), model sıcakken; `/api/ps` koşum öncesi
ve tahliye sonrası boş.

- `cikti/duman-e.txt` — tek tekrar; hüküm kurmaz, yalnız boru hattını sınar.
  `kol-e.json`'u da bu yazdı, tam koşum üzerine yazdı.
- `cikti/kol-e.txt` + `cikti/kol-e.json` — **sitedeki "Toplu gömme" tablosu
  buradan alındı.** Her yan 5 tekrar, dönüşümlü sıra (1/3/5: batch→teker,
  2/4: teker→batch). Batch (24 parça tek istek) tekrarları 4,58 / 4,57 / 4,73 /
  4,44 / 4,64 sn → p50 4,58, p95 4,71, min–maks 4,44–4,73, toplam 22,97 sn.
  Teker (24 ayrı istek) 4,90 / 4,96 / 4,86 / 5,01 / 4,97 sn → p50 4,96,
  p95 5,00, min–maks 4,86–5,01, toplam 24,69 sn. İstek başına p50 0,204 sn;
  fark p50 +0,38 sn (1,08×). Aralıklar çakışmıyor (4,73 < 4,86) → ön kayıtlı
  hüküm: **tek istek daha ucuz**. 583 token iki yanda da aynı; ısıtma 9,89 sn
  (5,11 sn yükleme) sayılmadı; tahliye 0,07 sn. Sıcak batch isteklerinde
  `load_duration` 0,01 sn.
- `cikti/kol-e.json` ayrıca yan başına ham tekrar listesini, 24 ayrı isteğin
  her birinin duvar süresini, sunucu `total_duration` toplamlarını ve hükmü
  taşır.

**Sürüm künyesi.** `gomme_egit.py` 2026-10-19'da log başına `GET /api/version`
ekledi; 2026-10-20'deki E koşumu bu değişikliğin ilk gerçek kullanımıdır ve
`kol-e.txt` satır 9'da `Ollama sürümü: 0.40.6` yazar. 17 Ekim'deki A-D
kayıtları hâlâ künyesizdir; onların sürümünü diskte tek söyleyen yer aşağıdaki
"Makine" satırıdır. Eski sayılar bu değişiklik için yeniden koşulmadı.

Makine: AMD Ryzen 5 2600 (6/12), 15,9 GB RAM, ekran kartı yok, Ollama 0,40,4
(A-D, 17 Ekim) ve 0,40,6 (E, 20 Ekim; log kendi künyesini taşıyor), `bge-m3`
yerel, Windows 11 26300. Model ağırlıkları
`D:\projects\...\model-egitimi-rehberi\.hfcache` içinde.

## Bilinen sınırlar

- **8 soru / 24 parça.** Tablolar modellerin genel kapasitesini değil, bu
  korpustaki davranışını ölçer. Güven aralığı hesaplanmadı.
- Eğitim verisi 40 elle yazılmış paraphrase çifti; tamamı kurgusal "Yıldıztepe"
  mahallesinin kurgusal metinleri. Gerçek kurum verisi yok, kişisel veri yok.
- Tek tekrar: bir eğitim koşumu = bir sayı. Tohum varyansına yalnız B kolunun iki
  koluyla (1234 vs 5678) dokunuldu, dağılım çıkarılmadı.
- Windows'ta sembolik bağ kurulamadığı için HF önbelleği kopyalarla dolu; disk
  boyutu okunurken bu fark edilir.
- Matryoshka, CachedMNRL, CoSENT ve triplet kaybı **çalıştırılmadı** — sayfadaki
  "Ölçülmedi" satırları bundan.
- Kol E yalnız 24 parça / 583 token'da, tek modelle (`bge-m3`) ve `-np 1`
  varsayılanıyla koştu. 24'ten büyük parti, `/api/embed` eşzamanlılığı ve başka
  gömme modelleri **ölçülmedi**. Beş tekrarın dağılımı verildi, güven aralığı
  çıkarılmadı.
- GPU, çok iş parçacıklı dağıtık eğitim ve büyük veri bu kafeste yok.
