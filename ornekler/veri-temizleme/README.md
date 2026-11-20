# Veri temizleme örneği — HF veri setinden SFT formatına

İnternetteki gerçek bir Türkçe talimat veri setini indirip temizleyen uçtan uca
hat (CPU, Ollama gerekmez):

1. **Streaming indirme** — Hugging Face `datasets` ile
2. **Alan eşleme** — sütun adları → `messages` şeması (SFT formatı)
3. **Normalizasyon** — Unicode (NFC), HTML kalıntıları, mojibake (`ftfy`)
4. **PII maskeleme** — e-posta, telefon, IBAN, TCKN (sağlama kontrollü)
5. **Kalite filtreleri** — uzunluk, alfanümerik oran
6. **Tekrar temizliği** — birebir (sha256) + yakın (MinHash/LSH, eşik 0.8)

## Gereksinimler

- Ollama **gerekmez**; internet bağlantısı gerekir (ilk indirme):

```bash
pip install datasets ftfy datasketch
```

## Çalıştırma

```bash
cd ornekler/veri-temizleme
python atolye.py                     # varsayılan: 3000 örnek (merve/turkish_instructions)
python atolye.py --ornek 500         # hızlı deneme
python atolye.py --veri-seti AlicanKiraz0/Turkish-SFT-Dataset-v1.0   # başka set
```

## Çıktılar (`cikti/`)

- `temiz_veri.jsonl` — SFT eğitimine hazır temiz kayıtlar (`messages` dizisi)
- `rapor.json` — tüm sayılar yapılandırılmış (öncesi/sonrası, filtre kırılımı)
- `calistirma-kaydi.txt` — stdout'un tamamı; `-eski`/`-oncesi` sonekli çiftler
  2026-10-17 PII düzeltmesinin öncesi/sonrasını tutar (maskeleme alan listesine
  `input` alanı eklendi; ayrıntı sayfada §6d)

Sayfası: `src/content/docs/ornekler/veri-temizleme.mdx`
(İngilizcesi: `src/content/docs/en/ornekler/veri-temizleme.mdx`); kavram tarafı:
`src/content/docs/veri/veri-temizleme.md`
