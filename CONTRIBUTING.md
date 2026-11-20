# Katkı Rehberi

## Kurulum

```bash
npm install     # Node 26 önerilir (CI ile aynı)
npm run dev     # http://localhost:4321
```

Örnek betikler için kökteki tek ortak `.venv` kurulumu: README "Örnek projeleri
çalıştırma" bölümünde.

## İçerik katkısı

1. Sayfayı oluştur: `src/content/docs/<bölüm>/<sayfa>.md` (Türkçe kök) ya da
   `src/content/docs/en/<bölüm>/<sayfa>.md` (İngilizce; çevrilmemiş adresler Türkçe
   fallback + uyarıyla açılır).
2. `dogrulama:` damgası **zorunlu** — ne söylediğini ve ne söylemediğini
   `src/content/docs/kaynaklar/dogrulama-mekanizmasi.md` anlatır.
3. Sayfayı `astro.config.mjs` içindeki `sidebar` listesine ekle.
4. Üç kapıyı koş:

   ```bash
   npm run build                # dist/ üretilir
   node scripts/link-check.mjs  # "TÜM İÇ LİNKLER TAMAM" beklenir
   npm run dogrula              # damga denetimi
   ```

## Yazım sözleşmesi

Kanıt kademeleri (0 beklenti → 3 tekrarlandı), "sayı yalnız bitmiş günlükten gelir"
kuralı, koşum hijyeni ve bilinen tuzaklar: [AGENT.md](AGENT.md). Kısa hâli: ölçmediğin
sayıyı yazma, ölçtüğünün kaydını koşum günlüğünden taşı.

- Betik içi yorumlar ASCII Türkçe; sayfa metni tam Türkçe (ondalık virgül: `141,88 sn`).
- Sayfa metnini değiştirdiysen `dogrulama:` tarihini bugüne çek; değişmediyse çekme.

## Gönderim

- Commit konu satırı Türkçe ve kısa; birden çok konu `;` ile ayrılır.
- PR'lar küçük tutulur: bir sayfa = bir PR. CI (`denetim`) yeşil olmadan merge edilmez.
- Bağımlılık eklerken `package-lock.json` commit'e girer.

## Lisans

Katkın, dosya türüne göre çift lisansa girer: sayfa metni ve belgeler **CC BY-SA 4.0**,
çalışan her şey (betikler, site kodu, yapılandırma) **MIT**. Sınır çizgisi:
[LICENSE.md](LICENSE.md).
