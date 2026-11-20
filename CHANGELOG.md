# Değişiklik Günlüğü

Biçim: [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/); sürümleme
[SemVer](https://semver.org/lang/tr/). Bu depo npm paketi değildir — `package.json`'daki
`private: true` bilinçlidir; sürüm numarası site yayınlarının işaretidir.

## [Yayınlanmamış]

### Ekler
- İlk İngilizce içerik sayfaları: `en/baslangic/giris`, `en/baslangic/kavramlar`,
  `en/baslangic/yol-haritasi`, `en/llm/lora-qlora` — çevrilmemiş `/en/` adresleri Türkçe
  içerik + "çevrilmemiş" uyarısıyla açılmaya devam eder.
- İkinci çeviri serisi: `en/temeller/{transformer,tokenizasyon,egitim-nasil-calisir}`,
  `en/donanim/vram-hesabi` (etkileşimli hesaplayıcı Türkçe arayüzlü olduğu için gömülmedi,
  Türkçe sayfaya yönlendirme notu kondu), `en/kullanim/quantization`.
- Üçüncü çeviri serisi: `en/donanim/{yerel-kurulum,bulut-secenekleri}`, `en/veri/` beşlisi
  (turleri, nereden-bulunur, formatlari, temizleme, kendi-verini-olustur),
  `en/llm/{sft,adim-adim-egitim}` — İngilizce sayfa sayısı 19'a ulaştı.
- Dördüncü çeviri serisi: `en/llm/{pretraining,dpo-rlhf,araclar,hiperparametreler,sorun-giderme}`
  ve `en/degerlendirme/{loss-ve-metrikler,benchmarklar}` — LLM ve değerlendirme bölümleri tam;
  İngilizce sayfa sayısı 26'ya ulaştı.
- Beşinci çeviri serisi: `en/rag/` dörtlüsü (rag-mi-ince-ayar-mi, rag-degerlendirme,
  parcalama-ve-hibrit-arama, gomme-egitimi) ve `en/ajan/` beşlisi (ajan-mi-sabit-hat-mi,
  arac-cagirma-ve-mcp, ajan-olcumu, prompt-enjeksiyonu, enjeksiyon-olcumu) — RAG ve ajan
  bölümleri tam; İngilizce sayfa sayısı 35'e ulaştı.
- Altıncı çeviri serisi: `en/kullanim/`'in kalan 10 sayfası (lora-birlestirme, ollama,
  cikarim-parametreleri, tekrarlanabilirlik, hiz-ve-maliyet, eminlik-ve-kalibrasyon,
  eszamanlilik, sunma-api, huggingface-paylasim, lisans-ve-model-karti) — kullanım bölümü TAM;
  İngilizce sayfa sayısı 45'e ulaştı.

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
