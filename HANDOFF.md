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
- İkinci dil altyapısı: Starlight i18n ile `en` yereli eklendi (Türkçe kök kaldı, URL'ler değişmedi).
  `src/content/i18n/en.json` arayüz metinleri + İngilizce açılış sayfası (`en/index.mdx`) hazır;
  çevrilmemiş `/en/...` adresleri Türkçe içerik + Starlight "çevrilmemiş" uyarısıyla açılıyor.
  Çeviri politikası README "Çok dillilik" bölümünde.
- Makine yolu sızıntısı 0 (2026-11-06'daki 2 dosya o tarihten beri temizlenmişti); gizli anahtar
  taraması temiz.
- Yayın kuruldu (2026-11-19 kararı: GitHub Pages + depo public): `site: https://sysrootfile.github.io`
  + `base: /local-model-training-guide`; canonical/sitemap/robots.txt üretimi açık. Base kuplingi
  çözüldü: Starlight içerik linklerini otomatik önekliyor (rehype gerekmedi), banner linki
  `BASE_URL`'den okuyor (`src/starlightRouteData.ts`), `scripts/link-check.mjs` base-önekli
  Pages düzenini denetliyor. Deploy: `.github/workflows/yayin.yml`, Pages API ile
  `build_type=workflow` olarak açıldı.
- Norm dosyaları: `CHANGELOG.md` (Keep a Changelog, 0.1.0), `CONTRIBUTING.md`,
  `public/robots.txt`.
- Damga takvimi: `.github/workflows/damga-takvimi.yml` — her ayın 1'inde `dogrula --strict`
  koşar; bayat sayfa varsa depoya issue açar/günceller.
- Sürüm kararı kaydı: `package.json` `0.1.0` + `private: true` bilinçli — bu depo npm paketi
  değil; `private: true` yanlışlıkla publish'i engeller, sürüm numarası site yayınlarının
  işaretidir (CHANGELOG taşır).

## Sıradaki işler
1. İngilizce çeviri: 45 sayfa canlı (önceki 35 + `kullanim/`'in kalan 10 sayfası — bölüm TAM;
   damgalar 2026-11-19/20). Kalan ~19 sayfa aynı kuralla çevrilir: `gorsel/` ikilisi +
   `klasik-ml/` ikilisi + `ornekler/` onlusu + `kaynaklar/` altılısı (18) + EN index güncellemesi.
   Not: `VramCalculator` bileşeni Türkçe arayüzlü; EN `vram-hesabi` sayfası gömmedi, Türkçe
   sayfaya notla yönlendiriyor.
2. İsteğe bağlı: `ornekler/klasik-ml` ve `ornekler/veri-temizleme` için README. README satır 70-73
   bilinçli tercih diyor, karar sana ait.

## Ölçülmemiş kapılar
- GPU isteyen eğitim betiklerinin (turkce-asistan, gorsel-lora) fiilen koşumu.
- Pages canlı adresinin ilk dış doğrulaması (push sonrası `yayin` iş akışı + curl).
- `damga-takvimi`'nin ilk ay turu (ilk tetik: 2026-12-01).
