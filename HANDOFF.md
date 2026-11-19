# HANDOFF — local-model-training-guide

Son güncelleme: 2026-11-06 · Kaynak: 12 projelik kapsamlı yayın denetimi

## Bu proje ne
Astro 7 + Starlight tabanlı, Türkçe model eğitimi rehberi sitesinin kaynağı.
`src/content/docs/` altında 13 bölümde 66 sayfa ve 14 klasörlük `ornekler/` laboratuvarı.

## Ölçülen durum
- 67 içerik dosyası; sidebar'daki tüm slug'lar gerçek dosyalara karşılık geliyor, eksik/fazla yok.
- Gerçek TODO/draft → 0. grep'in 3 eşi Türkçe kelime alt-dizisi ("yakından", "devam edecekseniz"),
  yanlış pozitif. `draft:` frontmatter → 0.
- Kanıt mekanizması çalışıyor: 67 dosyanın tamamında `dogrulama:` damgası, en yenisi 2026-10-30,
  gelecek tarihli yok. 90 günlük bayatlık banner'ı `src/starlightRouteData.ts`'te kurulu.
- `npm run build` BAŞARILI → "66 page(s) built in 18.25s", Pagefind indeksi tamam.
  Tek uyarı: `[@astrojs/sitemap] The Sitemap integration requires the site option. Skipping.`
- Teknik doğruluk: MDX sayfaları betikleri `?raw` ile gerçek dosyadan gösteriyor (11 import, hepsi var);
  `ornekler/*/cikti/` koşum kayıtları commit'lenmiş; betiklerdeki model adları metinle tutarlı.
- Lisans iki katmanlı ve doğru: içerik CC BY-SA 4.0 (`LICENSE-CC-BY-SA-4.0.txt` repoda), kod MIT;
  Vikipedi atfı belgelenmiş.
- Git hijyeni temiz: 238 izlenen dosya, en büyüğü ~120 KB. Diskteki 458 MB `.hfcache` ve 46 MB
  `egitim.jsonl` ignore dışında. 7 commit, remote YOK.
- Durum özeti: KISMEN, ve 12 proje içinde yayına en yakın olanı.

## Sıradaki işler
1. `astro.config.mjs` içine `site:` tanımla (şu an tanımsız). Bu tek satır olmadan sitemap
   üretilmiyor ve canonical adres yok; README satır 154 bunu kendisi de itiraf ediyor.
2. Alan adı + hosting kararını ver ve remote tanımla. Yayın fiilen hiç yapılmamış.
3. İki izlenen dosyada makine yolu geçiyor; `git grep -l 'sys\.root\.file'` ile bul ve temizle.
   (Sayı: 2 dosya — içerik veya betik içindeki mutlak yol.)
4. `package.json` sürümü `0.1.0` ve `private: true`; yayın kararıyla uyumla.
5. Damga tazeliği takvimi kur: damgaların çoğu 2026-10-15/19, 90 gün Ocak 2027'de doluyor ve
   siteler "bayat" banner'ı göstermeye başlayacak. Periyodik yenileme tarihi yok.
6. `npm run dogrula` ve `node scripts/link-check.mjs` bir kez koş ve sonuçlarını buraya yaz
   (denetimde yalnız build koşuldu).
7. İsteğe bağlı: `ornekler/klasik-ml` ve `ornekler/veri-temizleme` için README. README satır 70-73
   bilinçli tercih diyor, karar sana ait.

## Ölçülmemiş kapılar
- `npm run dogrula`, `node scripts/link-check.mjs`, harici (http) linklerin canlılığı,
  GPU isteyen eğitim betiklerinin (turkce-asistan, gorsel-lora) fiilen koşumu.
