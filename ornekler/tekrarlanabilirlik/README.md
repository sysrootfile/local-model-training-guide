# Tekrarlanabilirlik ve tohum varyansı ölçümü

Sitenin [Tekrarlanabilirlik](../../src/content/docs/kullanim/tekrarlanabilirlik.md)
sayfasındaki tüm sayıların geldiği kafe. İki kola ayrılır: **A/C/D** Ollama
istekleri (aynı istem onar kez), **B** scikit-learn tohum varyansı (aynı veri,
beş tohum, üç senaryo).

## Koşum

```bash
# tam koşum: ~9-10 dk, 123 Ollama isteği + 30 sklearn eğitimi.
# Koşum sırasında başka Ollama isteği GÖNDERMEYİN.
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol hepsi > cikti/tekrar-kaydi.txt 2>&1

# sadece Ollama kolu / sadece sklearn kolu
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol a > cikti/tekrar-kaydi.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol b > cikti/sklearn-kaydi.txt 2>&1

# duman testi: 5 hücre x 2 tekrar + K0 tek istek (~2-3 dk)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --kol a --duman > cikti/duman.txt 2>&1
```

Yönlendirme doğrudan `>` ile yapılır (`| tee` bu projede uzun bir koşumu kaybetti),
`-u` olmadan çıktı tamponda kalır ve koşum sırasında log boş görünür.
Betik yalnızca `http://127.0.0.1:11434` ile konuşur; dışarıya istek atmaz.

## Hücreler

| Kod | Ölçtüğü |
| --- | --- |
| K0 | `num_predict` gönderilmediğinde fiilî tavan: uzun istem, T=0, üç tekrar |
| A1-A6 | Kapalı uçlu soru: T=0 tohumsuz / T=0 tohumlu / T=0,8 tohumsuz / tohum 1234 / aynı ayarın ikinci dizisi / tohum 9999 |
| C1-C3 | Açık uçlu (serbest) istem, `num_predict` 200: tohumsuz çeşitlilik, tohumlu aynılık, ikinci dizi |
| D1-D3 | `format` alanı: `"json"` (300 token) / şema (300) / şema + `num_predict` 48 |
| B1-B3 | scikit-learn: bölme+model tohumu birlikte / yalnız model / yalnız bölme (RF 300 ağaç, lojistik) |

## Kayıtlar

- `cikti/tekrar-kaydi.txt` — **sitedeki tablolar buradan alındı.** Tam koşum,
  2026-10-17 11:04:59 → 11:14:18, 12 hücre × 10 tekrar + K0 + Kol B.
- `cikti/duman1.txt` — ilk duman koşumu (2026-10-17 10:45-10:51). Betiğin önceki
  hâli: D hücreleri yoktu, C hücreleri 48 token tavanıyla koşuyordu. K0'ın ilk
  üçlüsü (1060 / 1460 / 1460 token) burada da var ve tam koşumda doğrulandı.
- `cikti/duman2.txt`, `cikti/duman3.txt` — D hücreleri eklendikten sonraki duman
  koşumları. `duman3` şemanın 48 token tavanında kırılmasını ilk gösteren koşumdur.

Makine: AMD Ryzen 5 2600 (6/12), 15,9 GB RAM, Ollama 0,40,4,
`qwen2.5:3b-instruct-q4_K_M` (CPU'da çalışıyor; `ollama ps` kaydı
`ornekler/cikarim-olcu` tarafında tutuldu). Sklearn tarafı `ornekler/klasik-ml/veri/breast_cancer.csv`,
569 satır / 30 özellik, %20 katmanlı bölme, 114 test satırı.

## Bilinen sınırlar

- Tek model, tek makine, tek Ollama sürümü. Uzun üretimde T=0'ın aynılığı
  kaybetmesinin (K0) nedenini ayırt eden bir kol yok — önbellek durumu ve
  toplama girme biçimi elenmedi.
- On tekrar: oranlar nokta tahmini, güven aralığı hesaplanmadı.
- D hücreleri doğruluğu değil ayrıştırılabilirliği sayar.
