# HANDOFF — local-model-training-guide

Son güncelleme: 2026-11-19 · Kaynak: 12 projelik kapsamlı yayın denetimi (2026-11-06) +
sektör normu denetimi (2026-11-18/19)

## Bu proje ne
Astro 7 + Starlight tabanlı, Türkçe model eğitimi rehberi sitesinin kaynağı.
`src/content/docs/` altında 13 bölümde 66 sayfa ve 14 klasörlük `ornekler/` laboratuvarı.

## Ölçülen durum (2026-11-06 denetimi)
- 67 içerik dosyası; sidebar'daki tüm slug'lar gerçek dosyalara karşılık geliyor, eksik/fazla yok.
  (2026-11-19 düzeltmesi: içerik sayfası 66 — 65 alt dizin + `index.mdx`; "67" sayım hatasıydı.)
- Gerçek TODO/draft → 0. grep'in 3 eşi Türkçe kelime alt-dizisi ("yakından", "devam edecekseniz"),
  yanlış pozitif. `draft:` frontmatter → 0.
- Kanıt mekanizması çalışıyor: tüm sayfalarda `dogrulama:` damgası. 90 günlük bayatlık banner'ı
  `src/starlightRouteData.ts`'te kurulu.
- `npm run build` BAŞARILI → Pagefind indeksi tamam. `site:` tanımsızken tek uyarı:
  `[@astrojs/sitemap] The Sitemap integration requires the site option. Skipping.`
- Teknik doğruluk: MDX sayfaları betikleri `?raw` ile gerçek dosyadan gösteriyor; `ornekler/*/cikti/`
  koşum kayıtları commit'lenmiş; betiklerdeki model adları metinle tutarlı.
- Lisans iki katmanlı ve doğru: içerik CC BY-SA 4.0, kod MIT; Vikipedi atfı belgelenmiş.
- Git hijyeni temiz: 239 izlenen dosya, en büyüğü ~845 KB (hero.png). Diskteki `.hfcache` ve
  `egitim.jsonl` ignore dışında.

## Tamamlanan (2026-11-19)
- Remote kuruldu: github.com/sysrootfile/local-model-training-guide (private), `main` push'landı;
  HANDOFF.md commit'lenerek dahil edildi.
- `scripts/link-check.mjs` çıkış kodu kusuru giderildi: kırık iç link artık çıkış 1 döner.
- Dış linkler ilk kez uçtan uca tarandı (308 URL): 3 gerçek 404 onarıldı —
  Epoch AI panosu → `epoch.ai/benchmarks`; NeurIPS atfı yanlış makaleydi, doğru kaynak
  Kumar/Liang/Ma 2019 (`arXiv:1909.10155`); Chroma parçalama değerlendirmesi →
  `trychroma.com/research/evaluating-chunking` (2 yer). Üç sayfanın damgası 2026-11-19'a çekildi.
  Kalan 6 sorunlu URL false positive (bot engelleme 403, `cuXXX` yer tutucu, parametresiz API,
  dahili host).
- Üç kapı koşuldu: build ✅ (66 sayfa), link-check ✅ (66 sayfa), `dogrula` ✅ (65 damga, 0 bayat).
- CI kuruldu: `.github/workflows/denetim.yml` — push/PR'da `npm ci` → build → link-check → dogrula.
- Makine yolu sızıntısı 0 (2026-11-06'daki 2 dosya o tarihten beri temizlenmişti); gizli anahtar
  taraması temiz.

## Sıradaki işler
1. `astro.config.mjs` içine `site:` tanımla. Dikkat: GitHub Pages
   (`sysrootfile.github.io/local-model-training-guide`) seçilirse `base: '/local-model-training-guide'`
   de gerekir; o zaman `src/starlightRouteData.ts`'deki `/kaynaklar/dogrulama-mekanizmasi/` mutlak
   linki ve `scripts/link-check.mjs`'in `/`-köklü href varsayımı da base'e uyarlanmalı. Kök alan
   adı (özel domain / Vercel) seçilirse yalnız `site:` yeter.
2. Alan adı + hosting kararı; yayın ilk kez fiilen yapılacak. İsteyen `gh repo edit
   sysrootfile/local-model-training-guide --visibility public` ile depoyu açabilir.
3. `package.json` sürümü `0.1.0` ve `private: true`; yayın kararıyla uyumla.
4. Damga tazeliği takvimi: damgaların çoğu 2026-10-15/19, 90 gün Ocak 2027'de doluyor. CI şu an
   `dogrula`yı strict olmayan kipte koşuyor (bayat kırmez, eksik damga kırar); zorlayıcı istenirse
   iş akışına `npm run dogrula -- --strict` yazılır.
5. İsteğe bağlı: `ornekler/klasik-ml` ve `ornekler/veri-temizleme` için README. README satır 70-73
   bilinçli tercih diyor, karar sana ait.

## Ölçülmemiş kapılar
- GPU isteyen eğitim betiklerinin (turkce-asistan, gorsel-lora) fiilen koşumu.
- CI'ın GitHub tarafında ilk yeşil koşumu (bu push'ın Actions sayfasından doğrulanacak).
