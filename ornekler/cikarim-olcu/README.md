# Çıkarım hızı ve maliyet ölçümü

Sitedeki gecikme sayılarının (Örnek 5 ve 6 dahil) geldiği kafe. Sayfa:
`src/content/docs/kullanim/hiz-ve-maliyet.md`.

## Koşum

```bash
# tüm deneyler (~20-40 dk, CPU; başka Ollama isteği göndermeyin)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u hiz_olc.py > cikti/hiz-kaydi.txt 2>&1

# seçili deneyler
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u hiz_olc.py --yalniz E12 E13 > cikti/hiz-kaydi-4.txt 2>&1
```

Log'a yönlendirme doğrudan `>` ile yapılır; `| tee` bu projede 20 dakikalık bir
koşumu kaybetti. `-u` olmasa çıktı tamponda kalır ve koşum sırasında log boş görünür.

## Deneyler

| Kod | Ölçtüğü |
| --- | --- |
| E1 | soğuk/sıcak çağrı, `load_duration` |
| E2 | çözme hızı (kusurlu: model 16 token'da kendini kesti, bak E2b) |
| E3 | karakter/token oranı (önbellek kirlimesiyle) |
| E4 | `num_ctx`: bellek, yeniden yükleme, sessiz kırpma |
| E5 | prompt/KV önbelleği: aynı önek ikinci okuma |
| E6 | `num_thread` |
| E7 | TTFT (yeniden yüklemeyi de içerdi, bak E7b) |
| E8 | embedding vs üretim (duvar süresi) |
| E8b | embedding'in sunucu tarafı, sohbet modeli açık/kapalı |
| E9 | takılma avı: 8 sıcak çağrı + boşalt/yeniden yükle karşılaştırması |
| E2b | çözme hızı eğrisi (üretime zorlayan istek) |
| E3b | önbelleksiz ön-yükleme eğrisi + karakter/token |
| E7b | sıcak TTFT (önbellek kurulu) |
| E10 | boşalt/yükle çevrimi ×5 |
| E11 | duvar-sunucu farkı: vekil sunucu hipotezi (elenmedi, bak E12) |
| E12 | `localhost` vs `127.0.0.1` vs `http.client` |
| E13 | 10 parçalık indeksleme A/B'si |

## Kayıtlar

**Birinci tur — betik `http://localhost:11434` kullanıyordu (2026-10-16, 00:21-00:45):**
- `cikti/hiz-kaydi.txt` — E1-E9 tam koşum (bu makine, %100 CPU)
- `cikti/hiz-kaydi-2.txt` — E4 düzeltilmiş hâli + E2b, E3b, E7b, E10, E11
- `cikti/hiz-kaydi-3.txt`, `cikti/hiz-kaydi-3b.txt` — E11, E8b
- `cikti/hiz-kaydi-4.txt` — E12, E13

**İkinci tur — adres `http://127.0.0.1:11434` (2026-10-16 01:21-01:41):**
- `cikti/hiz-kaydi-127.txt` — E1-E13 tek dosyada tam koşum. **Sitedeki tablolar buradan alındı.**

İki tur arasındaki fark sayfa tarafından ölçüldü: duvar süreleri istek başına ~2 sn indi
(isim çözümleme gideri), `ollama ps` bellek basamakları birebir aynı kaldı, sunucu
hızları ise turdan tura ~%10 oynadı. E11/E12/E13'ün `localhost` dizeleri bilerek
değiştirilmedi — A/B deneylerinin karşı kolu onlar.

Makine: AMD Ryzen 5 2600 (6 çekirdek/12 iş parçacığı), 15,9 GB RAM, SATA SSD,
Ollama 0.40.4, `qwen2.5:3b-instruct-q4_K_M` (2,2 GB yerleşik), `bge-m3` (1024 boyut).
Koşum sırasında boş RAM 2,0-3,6 GiB arasındaydı (sistem %87 dolu).
