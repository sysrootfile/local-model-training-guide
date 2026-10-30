# Model Eğitimi Rehberi

Türkçe, sıfırdan ileri seviyeye **model eğitimi** rehberi. Veri bulmaktan kendi modelini çalıştırmaya kadar tüm adımları kapsayan, tamamen Türkçe bir dokümantasyon sitesi.

## Kapsam

- **Başlangıç ve Temeller:** Kavramlar, transformer mimarisi, tokenizasyon, eğitim döngüsü
- **Donanım ve Ortam:** VRAM hesabı (etkileşimli hesaplayıcı dahil), Windows'ta yerel kurulum, bulut seçenekleri
- **Veri:** Veri türleri, Türkçe veri kaynakları, formatlar (JSONL/Alpaca/ShareGPT), temizleme, kendi verini oluşturma
- **LLM Eğitimi:** Ön eğitim, SFT, LoRA/QLoRA, DPO/RLHF, araç karşılaştırması, uçtan uca eğitim rehberi, hiperparametreler, sorun giderme
- **Görsel Model Eğitimi:** Difüzyon temelleri, görsel LoRA eğitimi
- **Klasik Makine Öğrenmesi:** Temeller ve scikit-learn ile ilk model
- **Değerlendirme:** Loss eğrileri, metrikler, benchmark'lar
- **Kullanım ve Yayınlama:** LoRA birleştirme, nicemleme (GGUF), Ollama, vLLM API, Hugging Face paylaşımı
- **Örnek Projeler:** Numaralanmış sekiz örnek — dördü proje betiği (Örnek 1 tablo verisiyle ML, 2 veri temizleme, 3 Türkçe sohbet asistanı, 4 görsel stil LoRA), dördü ölçüm örneği (5 yerel RAG, 6 Vikipedi RAG, 7 ajan döngüsü, 8 prompt enjeksiyonu deneyi). Örnekleri tek hatta dikişleyen sayfa ayrıca var: "Uçtan Uca Tek Hat" (`ornekler/ucdan-uca`).
- **Kaynaklar:** SSS, Türkçe-İngilizce sözlük, faydalı linkler

Ana sayfada ayrıca etkileşimli bir **yöntem seçici** ve VRAM sayfasında bir **VRAM hesaplayıcı** bulunur.

## Teknoloji

- [Astro](https://astro.build) 7 + [Starlight](https://starlight.astro.build) 0.42
- İçerik: Markdown / MDX (`src/content/docs/`)
- Arama: Pagefind (Starlight ile gelir, `build` sonrası çalışır)
- Tema: `src/styles/custom.css` (indigo-mor aksan paleti, açık/koyu tema)

## Çalıştırma

```bash
npm install     # bağımlılıkları kur
npm run dev     # geliştirme sunucusu → http://localhost:4321
npm run build   # üretim derlemesi → dist/
npm run preview # derlenmiş siteyi önizle (arama burada çalışır)
```

## Proje Yapısı

```text
src/
├── assets/hero.png              # Ana sayfa hero görseli
├── components/
│   ├── MethodWizard.astro       # "Hangi yol bana uygun?" etkileşimli seçici
│   └── VramCalculator.astro     # VRAM tahmin hesaplayıcı
├── content.config.ts            # içerik koleksiyonları (docs + i18n)
├── content/
│   ├── i18n/tr.json             # arayüz metinleri (Türkçe)
│   └── docs/                    # TÜM SAYFALAR (bölüm klasörleri halinde)
│       ├── index.mdx            # ana sayfa (splash)
│       ├── baslangic/ temeller/ donanim/ veri/
│       ├── llm/ gorsel/ klasik-ml/ degerlendirme/
│       ├── kullanim/ ornekler/ ajan/ rag/ kaynaklar/
└── styles/custom.css            # tema
astro.config.mjs                 # site başlığı, sidebar, yerel ayarlar
QODER.md                         # yazım ve ölçüm sözleşmesi (kademeler, koşum kuralları, tuzaklar)

ornekler/                        # 14 klasör: 10 ÖLÇÜM KAFESİ + 4 PROJE BETİĞİ
├── <kafes>/                     # 10 kafes, hepsi http://127.0.0.1:11434'e bağlanır:
│                                #   cikarim-olcu, eszamanli-olcu, tekrarlanabilirlik, eminlik-olcu,
│                                #   enjeksiyon-deni, ajan-dongusu, yerel-rag, viki-rag,
│                                #   gomme-egitimi, lisans-ve-gizlilik
├── klasik-ml/                   # betik + veri + cikti (tamamı bu makinede çalıştırıldı)
├── veri-temizleme/              # betik + cikti (bu makinede çalıştırıldı)
├── turkce-asistan/              # 3 betik + README (veri hazırlama çalıştırıldı; eğitim GPU ister)
└── gorsel-lora/                 # denetim betiği + ai-toolkit config + README (denetim çalıştırıldı; eğitim GPU ister)

.venv/                           # TEK ORTAK sanal ortam (kökte); klasör başına ayrı ortam yok
.hfcache/                        # kafeslerin indirdiği ağırlıklar (HF_HOME betiklerin içinde kurulu)
```

Her `ornekler/<klasör>/` altında `cikti/` var. 12 klasörde ayrıca `README.md` var — **koşum komutları,
bağımlılıklar ve kayıt dosyası adları orada durur**; `klasik-ml` ve `veri-temizleme`de README yok,
koşum kayıtları doğrudan `cikti/` içinde. Bu dosya o komutları yeniden yazmaz (yazsaydı bayatlayan bir
kopya olurdu).

### Örnek projeleri çalıştırma

Örnek betikler ve kafesler site derlemesinden **bağımsızdır**; hepsi depo kökündeki **tek ortak**
`.venv` içinde çalışır (klasör başına ayrı ortam yok). Kökte `.venv` zaten varsa yeniden kurma:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install pandas scikit-learn joblib          # klasik-ml için
pip install datasets ftfy datasketch            # veri-temizleme için
```

Kafesler `.venv`'e göreli çağrılır ve Türkçe çıktı için `PYTHONUTF8=1` ister; örnek biçim (olduğu
kaynak: `ornekler/gomme-egitimi/README.md`):

```bash
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u <betik>.py > cikti/<kayit>.txt 2>&1
```

Ölçüm kafesi koşacaksan Ollama'nın `127.0.0.1:11434`te açık olması gerekir; hangi komutla hangi
kaydın üretildiği her kafesin kendi `README.md`sinde yazar. Koşum hijyeni (sunucuya dokunma, tek kol
zamanı, yabancı istek yoklaması) [QODER.md](QODER.md) dosyasında.

Windows'ta bazı paketlerin en yeni sürümleri kurumsal "Application Control" ilkelerine takılabilir; bu projede çalışan sürümler: `pyarrow 24.0.0`, `scipy 1.15.3` (detaylar ilgili sayfalarda). GPU gerektiren iki proje (turkce-asistan eğitimi, gorsel-lora eğitimi) WSL2/Linux veya bulut GPU önerir.

## Yeni Sayfa Ekleme

Yazım ve ölçüm kuralları (kanıt kademeleri, "sayı yalnız bitmiş günlükten", koşum hijyeni, tuzaklar)
[QODER.md](QODER.md) dosyasında; yeni bir sayfaya sayı taşıyorsan önce oraya bak.

1. `src/content/docs/<bölüm>/<sayfa>.md` dosyasını oluştur:

   ```markdown
   ---
   title: Sayfa Başlığı
   description: Tek cümlelik açıklama.
   dogrulama: 2026-01-01
   ---

   İçerik...
   ```

   `dogrulama:` **zorunludur**: o sayfanın iddialarının en son ne zaman gözden geçirildiği. Damgasız,
   biçimi bozuk ya da gelecek tarihli sayfa `npm run dogrula`yı kırar (çıktı 1). Metin değiştiyse
   tarihi bugüne çek; değişmediyse çekme.

2. Sayfayı `astro.config.mjs` içindeki `sidebar` listesine ekle:

   ```js
   { slug: '<bölüm>/<sayfa>' }
   ```

3. Sırayı bozmadan doğrula:

   ```bash
   npm run build                # dist/ üretilir; link yoklaması dist üzerinden konuşur
   node scripts/link-check.mjs  # kırık iç link yoksa "TÜM İÇ LİNKLER TAMAM"
   npm run dogrula              # damga denetimi
   ```

Starlight ek özellikleri: `:::note`, `:::tip`, `:::caution`, `:::danger` uyarı blokları, başlıklı kod blokları, `Card`/`CardGrid` bileşenleri.

**Örnek betiği sayfaya gömme:** `ornekler/` altındaki gerçek bir dosyayı kopyalamadan sayfada göstermek için `.mdx` sayfasında `?raw` importu + `Code` bileşeni kullanılır (tek doğruluk kaynağı betiğin kendisidir):

```mdx
import kod from '../../../../ornekler/klasik-ml/tablo_modeli.py?raw';
import { Code } from 'astro-expressive-code/components';

<Code code={kod} lang="python" title="ornekler/klasik-ml/tablo_modeli.py" />
```

## Lisans

İçerik (sayfalar ve belgeler) **CC BY-SA 4.0**, çalışan kod (betikler, denetim araçları, site kodu)
**MIT** lisansıyla yayımlanır; ayrımın sınır çizgisi, Vikipedi atfı ve lisans metinleri
[LICENSE.md](LICENSE.md) dosyasındadır.

## Notlar

- Site şu an **yalnızca yerel** kullanım için yapılandırıldı (herhangi bir yayın adresi tanımlı değil). Yayınlamak istediğinde `astro.config.mjs` içine `site:` eklenmesi önerilir.
- Fiyat/sürüm gibi değişken bilgiler "2026 itibarıyla" notuyla verilmiştir; güncel değerleri ilgili resmî kaynaktan doğrulayın.
- İçerikler öğretici amaçlıdır; üretim ortamına almadan önce test edin.
