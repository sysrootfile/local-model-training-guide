# Değişiklik Günlüğü

Biçim: [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/); sürümleme
[SemVer](https://semver.org/lang/tr/). Bu depo npm paketi değildir — `package.json`'daki
`private: true` bilinçlidir; sürüm numarası site yayınlarının işaretidir.

## [Yayınlanmamış]

## [0.1.0] — 2026-11-19

İlk sürüm: 13 bölümde 66 sayfalık Türkçe model eğitimi rehberi + İngilizce ikinci dil
altyapısı, GitHub Pages'te yayında.

### Ekler
- Türkçe içerik: veri bulmadan yayınlamaya kadar 13 bölüm; VRAM hesaplayıcı ve yöntem
  seçici etkileşimli bileşenleri.
- `ornekler/` altında 10 ölçüm kafesi + 4 proje betiği; koşum kayıtları `cikti/` altında
  commit'li.
- `dogrulama:` damga sistemi: sayfa başına zorunlu gözden geçirme tarihi, 90/180 gün
  bayatlık banner'ı (`src/starlightRouteData.ts`), denetim betiği
  (`scripts/dogrulama-kontrol.mjs`, `--strict` kipi).
- İç link yoklaması (`scripts/link-check.mjs`, kırıkta çıkış 1) ve base-önekli Pages
  düzeni denetimi.
- Starlight i18n: Türkçe kök yerel (URL'ler öneksiz) + İngilizce `/en/` — çevrilmemiş
  sayfalar Türkçe içerik + "çevrilmemiş" uyarısıyla açılır.
- Çift lisans: içerik CC BY-SA 4.0, kod MIT (`LICENSE.md`).

### Düzeltilenler
- Üç kırık dış link onarıldı: Epoch AI panosu güncel adresine; NeurIPS atfı uydurma
  başlık+hash'ti, doğru kaynakla (Kumar/Liang/Ma 2019, arXiv:1909.10155) değiştirildi;
  Chroma parçalama değerlendirmesi yeni adresine (2 yer).

### Altyapı
- GitHub Actions: `denetim` (push/PR: build + link-check + damga), `yayin` (GitHub Pages
  deploy), `damga-takvimi` (aylık strict damga turu → issue).
- Yayın adresi: <https://sysrootfile.github.io/local-model-training-guide/> — `site:` +
  `base: /local-model-training-guide`; canonical, sitemap ve robots.txt üretimi açık.
