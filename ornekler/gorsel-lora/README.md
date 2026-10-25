# Örnek 4: Görsel Stil LoRA (SDXL + ai-toolkit)

Kendi görsellerinizle bir difüzyon modeline (SDXL) **stil LoRA'sı** eğitme ve
ComfyUI'da kullanma. Dokümantasyon sayfası: `/ornekler/gorsel-lora/`.

```
görseller (1024px+) ──► caption (.txt) ──► veri_kontrol.py ──► ai-toolkit eğitimi ──► LoRA ──► ComfyUI
        veri toplama        etiketleme         denetim (CPU)          eğitim (GPU)      .safetensors
```

Bu klasördeki dosyalar:

| Dosya | Ne yapar | Donanım |
| --- | --- | --- |
| `veri_kontrol.py` | Veri setini eğitimden ÖNCE denetler: boyut, tekrar, caption, tetikleyici | CPU yeterli |
| `sdxl-lora-config.yaml` | ai-toolkit için SDXL LoRA eğitim config'i (Türkçe yorumlu) | — |
| `cikti/` | Denetim raporu ve örnek çalıştırma kaydı | — |

## 1) Veri hazırlığı (GPU gerekmez)

- **Sayı:** 15–30 görsel yeterli; çeşitlilik (açı, ışık, arka plan) sayıdan önemli.
- **Çözünürlük:** hedef 1024px kısa kenar (SDXL standardı).
- **Caption:** her görselin yanına **aynı adlı** `.txt` dosyası; stilde tetikleyici
  kelime (ör. `stilim`) her caption'ın başında. Otomatik etiketleme için WD14
  tagger, Florence-2 veya JoyCaption kullanılabilir; son hâlini yine gözle düzeltin.

Denetim betiği (sanal ortamda bir kez `pip install pillow`):

```bash
cd ornekler/gorsel-lora
python veri_kontrol.py --klasor veri/stilim                  # tetikleyici: stilim
python veri_kontrol.py --klasor veri/stilim --tetikleyici kelimem
```

Betik; 1024px altı görselleri, sha1 ile birebir kopyaları, dHash ile "neredeyse
aynı" kareleri, eksik/fazla caption'ları ve tetikleyicisiz caption'ları listeler;
özeti `cikti/denetim-raporu.json` dosyasına yazar. (Bu klasördeki
`cikti/test-gorseller/` kasten kusurlu ÜRETİLMİŞ sahte görsellerdir; gerçek veri
değildir, yalnızca betiğin uyarıları yakaladığını gösterir.)

## 2) ai-toolkit kurulumu (GPU gerekir)

Resmî depo: <https://github.com/ostris/ai-toolkit> (MIT lisansı). 2026 itibarıyla
resmî kurulum adımları:

```bash
git clone https://github.com/ostris/ai-toolkit.git
cd ai-toolkit
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Linux

# Önce PyTorch (sürüm/CUDA dizini zamanla değişebilir; resmî README'yi kontrol edin):
pip install --no-cache-dir torch==2.13.0 torchvision==0.28.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
```

Alternatif araçlar: OneTrainer (GUI odaklı), SimpleTuner. Windows'ta takılırsanız
topluluk kolay kurulum scripti: <https://github.com/Tavris1/AI-Toolkit-Easy-Install>

## 3) Config'i doldur ve eğitimi başlat

`sdxl-lora-config.yaml` dosyasını ai-toolkit deposundaki `config/` klasörüne
kopyalayın ve iki yeri doldurun: `datasets[0].folder_path` (görsel klasörünüz) ve
`sample.prompts` (test sahneleriniz). Sonra:

```bash
python run.py config/stilim-sdxl-lora.yaml
```

Eğitim çıktısı `output/stilim-sdxl-lora-v1/` altına düşer:

- `*.safetensors` — LoRA ara kayıtları, `save_every: 250` (ComfyUI'ye takılan dosya bunlar)
- `samples/` — eğitim sırasında üretilen örnek görseller (aynı prompt/seed ile karşılaştırın)
- Eğitimi `Ctrl+C` ile durdurup aynı komutla devam edebilirsiniz; kayıt anında
  keserseniz o checkpoint bozulur (resmî README uyarısı).

Kritik değerler (config'te "neden" yorumlarıyla): rank 32, `lr` 1e-4, 1500 adım,
1024px, `noise_scheduler: ddpm` + `sampler: ddpm` eşleşmesi, `train_text_encoder: false`.

## 4) ComfyUI'da kullanım

1. `*.safetensors` dosyasını `ComfyUI/models/loras/` içine kopyalayın.
2. İş akışında Checkpoint Loader (SDXL base) ile KSampler arasına **LoraLoader**
   düğümü ekleyin; model ve clip girişlerini bağlayın.
3. Gücü (strength) 0.6–1.0 arasında tarayın; 0.8 iyi bir başlangıçtır.
4. Prompt: `stilim, watercolor landscape, misty mountains, ...`
5. Ezber testi: eğitimde görülmeyen sahneler isteyin ve tetikleyicisiz de deneyin.

LoRA tek başına çalışmaz; SDXL base ile birlikte kullanılır. Kalıcı birleştirme
isterseniz: `/kullanim/lora-birlestirme/`.

## Donanım gereksinimi (kestirme)

| VRAM | Öneri |
| --- | --- |
| 8 GB | SDXL LoRA **sınırda**: batch 1 + `gradient_checkpointing: true` şart; zorlanırsa buluta geçin |
| 12 GB | SDXL LoRA rahat çalışır (bu projenin varsayılanı) |
| 16 GB+ | Flux LoRA (nicemlenmiş, `is_flux: true` + `quantize: true`); rank 16–32, lr 1e-4, 1000–2500 adım |

Referans süreler (RTX 4090): SDXL LoRA 30–60 dakika; Flux LoRA 1–3 saat.

Bulut alternatifi (2026 itibarıyla yaklaşık): **RunPod** RTX 4090 ~0,34–0,74 $/saat;
**Vast.ai** ~0,14–0,45 $/saat. Ayrıntı: `/donanim/bulut-secenekleri/`.

## Lisans notu

Taban modelin lisansı, eğittiğiniz LoRA'nın kullanımını da bağlar. SDXL
(CreativeML Open RAIL++-M) ticari kullanıma açıktır; **FLUX.2-dev ticari
kullanıma kapalıdır** (non-commercial lisans) — dev varyantıyla eğittiğiniz
LoRA'yı ticari işte kullanamazsınız. Alternatifler için dokümantasyon sayfasına
bakın: `/ornekler/gorsel-lora/`.

## Dürüstlük notu

Bu projede `veri_kontrol.py` bu makinede **gerçekten çalıştırıldı** (CPU);
sayfadaki denetim çıktısı, `cikti/test-gorseller/` içindeki PIL ile üretilmiş
SAHTE ve kasten kusurlu görsellerden alınan gerçek çıktıdır. **ai-toolkit
eğitimi GPU gerektirdiği için çalıştırılmadı**; eğitimle ilgili hiçbir sayı veya
örnek görsel uydurulmadı — config ve anlatım, ai-toolkit'in resmî deposuna göre
yazıldı. Sürüm ve fiyat bilgileri 2026 itibarıyladır.
