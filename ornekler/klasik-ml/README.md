# Klasik ML örneği — tablo verisiyle uçtan uca sınıflandırma

GPU'suz, dakikalar içinde çalışan eksiksiz bir scikit-learn iş akışı:

1. **Veri yükleme ve keşif** — Breast Cancer Wisconsin (Diagnostic) veri seti
   (`veri/breast_cancer.csv`, projeye dahil; internet gerekmez)
2. **Baseline** — "hep iyi huylu" sahte modeli; gerçek katkıyı ölçülebilir kılar
3. **5-fold çapraz doğrulama** — Lojistik Regresyon vs Rastgele Orman karşılaştırması
4. **Test değerlendirmesi** — accuracy/precision/recall/F1/ROC-AUC + karışıklık matrisi
5. **Model kaydı** — `Pipeline` (ölçekleyici + model) `joblib` ile saklanır ve geri yüklenir

## Gereksinimler

- Ollama **gerekmez**; yalnızca Python paketleri:

```bash
pip install pandas scikit-learn joblib
```

## Çalıştırma

```bash
cd ornekler/klasik-ml
python tablo_modeli.py
```

Çıktının tam metni `cikti/calistirma-cikti.txt` içinde; özet tablo ve sayıların
dürüst okunması sayfasında: `src/content/docs/ornekler/klasik-ml.mdx`
(İngilizcesi: `src/content/docs/en/ornekler/klasik-ml.mdx`).

## Kendi verinizle

`pd.read_csv(...)` satırını kendi CSV'nizle değiştirin; hedef sütun adını ve
(varsa) sınıf adlarını uyarlayın. Sızıntıya karşı tek satırlık sigorta: ölçekleyici
ve model aynı `Pipeline` içinde — `fit` yalnızca eğitim verisini görür.

Koşum kaydı: `cikti/calistirma-cikti.txt` (2026-10-15; `random_state=42` ile
aynı sürümlerde tekrarlanabilir).
