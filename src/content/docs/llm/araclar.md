---
title: "Araçlar Karşılaştırması: Unsloth, Axolotl, LLaMA-Factory, TRL"
description: "2026 itibarıyla öne çıkan dört ince ayar aracının karşılaştırması, karar rehberi ve her biri için mini başlangıç örnekleri."
dogrulama: 2026-10-15
---

Model ince ayarı yapmak için kod yazmanın birden çok yolu var: birinden hızlı sonuç alırsınız, diğeri tekrarlanabilir üretim işleri için tasarlanmıştır, bir diğeri hiç kod yazmadan tıklamayla eğitim yapmanızı sağlar. Bu sayfa, 2026 itibarıyla ekosistemde öne çıkan dört seçeneği karşılaştırır:

- **Unsloth** — tek GPU'da hız ve VRAM odaklı Python kütüphanesi
- **Axolotl** — YAML dosyasıyla yapılandırılan, üretim odaklı eğitim aracı
- **LLaMA-Factory** — web arayüzü + komut satırı, yüzden fazla model desteği
- **HF TRL + PEFT** — kod tabanlı referans kütüphaneler

:::note
Önemli gerçek: Bu araçların hepsi alt katmanda aynı şeyleri kullanır — `transformers`, `peft`, `bitsandbytes`, `accelerate`. Yani araç seçimi öğrendiklerinizi değiştirmez: LoRA, öğrenme oranı, kayıp maskesi gibi kavramlar her araçta aynıdır. Araç yalnızca kolaylıktır. Kavramları bir kez öğrenin, araçları istediğiniz gibi değiştirin.
:::

## Büyük Karşılaştırma Tablosu

Tablodaki değerlendirmeler 2026 itibarıyla geçerli eğilimleri yansıtır; her araç hızla geliştiği için güncel sürümlere göz atmayı ihmal etmeyin.

| | Unsloth | Axolotl | LLaMA-Factory | HF TRL + PEFT |
| --- | --- | --- | --- | --- |
| **Arayüz** | Python kodu (fonksiyonlar) | YAML yapılandırma dosyası | Web UI + CLI | Python kütüphanesi |
| **Ayırt edici özellik** | Tek GPU'da yaklaşık 2 kat hız + belirgin VRAM tasarrufu; QLoRA'da çok iyi | Üretim işleri için kapsamlı seçenekler; tekrarlanabilir deneyler | 100+ model desteği; tıklamayla eğitim; config paylaşımı | Referans uygulamalar; SFT/DPO/GRPO eğiticileri |
| **Çoklu GPU** | Destekleniyor: DDP (torchrun ile Unsloth CLI), Accelerate ve DeepSpeed; çoklu GPU deneyimi hâlâ sadeleştiriliyor | Evet, DeepSpeed ile güçlü | Evet | Evet (accelerate/DeepSpeed ile) |
| **Model desteği** | Popüler modeller yayınlandıktan kısa süre sonra desteklenir | Geniş; yeni modeller hızlı eklenir | Çok geniş (100+) | transformers'ta olan her model |
| **Tercih eğitimi desteği** | DPO, GRPO, ORPO, KTO | DPO, IPO, ORPO, KTO, GRPO, SimPO (ayrıca GDPO, EBFT) | DPO, KTO, ORPO, SimPO, PPO (+ ödül modelleme) | DPO, KTO, GRPO, RLOO (ORPO ve CPO deneysel) |
| **GGUF dışa aktarma** | `save_pretrained_gguf` | `axolotl export` (önce birleştirme) | — (llama.cpp ile çevrilir) | — (llama.cpp ile çevrilir) |
| **Lisans** | Apache-2.0 | Apache-2.0 | Apache-2.0 | Apache-2.0 |
| **Kime uygun** | Tek GPU'da hızlı deneme yapan bireyler | Config ile üretim işi yürüten ekipler | Kod yazmak istemeyenler, hızlı denemeciler | Kavramları öğrenmek ve özel akış kurmak isteyenler |

## Karar Rehberi

- **"Kod yazmak istemiyorum, tıklayarak eğiteyim"** → **LLaMA-Factory** (web arayüzü model, veri, parametre seçimini formlarla yaptırır)
- **"Tek GPU'da hızlı sonuç + Python"** → **Unsloth** (aynı işi daha hızlı ve daha az VRAM'le yapar)
- **"Config dosyasıyla tekrarlanabilir üretim işi"** → **Axolotl** (YAML'ı sürüm kontrolüne koyarsınız, sonuç tekrarlanabilir olur)
- **"Kütüphaneleri öğrenip kendi özel akışımı kuracağım"** → **TRL + PEFT** (her şey açıkta; en yüksek kontrol, en çok kod)

## Mini Başlangıçlar

### Unsloth

Kurulum ve hızlı yükleme (ayrıntılı örnekler için [Unsloth dokümantasyonuna](https://unsloth.ai/docs) bakabilirsiniz):

```bash title="unsloth_kurulum.sh"
# Sanal ortam önerilir (venv veya conda), sonra:
pip install unsloth
```

```python title="unsloth_hizli_baslangic.py"
from unsloth import FastModel  # Yeni sürümlerde FastModel; eski rehberlerde FastLanguageModel

model, tokenizer = FastModel.from_pretrained(
    model_name="Qwen/Qwen3-4B",   # Unsloth'un hazır 4-bit sürümleri de mevcut (unsloth/...)
    max_seq_length=1024,
    load_in_4bit=True,            # VRAM tasarrufunun anahtarı
)

# LoRA ekle
model = FastModel.get_peft_model(
    model,
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
)

# Buradan sonrası klasik TRL akışıdır: SFTTrainer'a verip eğitin.
# (Kayıp maskesi için: train_on_responses_only — /llm/sft/ sayfasına bakın.)
```

### Axolotl

```bash title="axolotl_kurulum.sh"
git clone https://github.com/axolotl-ai-cloud/axolotl.git
cd axolotl
pip install -e .
# Alternatif: hazır Docker imajı kullanın (axolotlai/axolotl)
```

```yaml title="config.yml"
# Axolotl işi tamamen bu YAML dosyasıyla tanımlanır: sürüm kontrolüne koyun,
# aynı config ile aynı deneyi istediğiniz zaman tekrarlayın.
base_model: Qwen/Qwen3-4B
load_in_4bit: true          # QLoRA
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj

datasets:
  - path: veri.jsonl       # Alpaca/ShareGPT tarzı veri dosyanız
    type: alpaca

sequence_len: 1024
micro_batch_size: 2
gradient_accumulation_steps: 4
num_epochs: 2
learning_rate: 0.0002
lr_scheduler: cosine
warmup_ratio: 0.03          # Axolotl şemasında geçerli; içeride warmup_steps'e çevrilir
bf16: auto
```

```bash title="egitimi_baslat.sh"
axolotl train config.yml
```

### LLaMA-Factory

```bash title="llamafactory_kurulum.sh"
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e ".[torch,metrics]"
```

```bash title="llamafactory_kullanim.sh"
# Seçenek 1 — Web arayüzü: tarayıcıda model/veri/parametre seçip eğitimi başlatın
llamafactory-cli webui

# Seçenek 2 — CLI: hazır bir config ile eğitim
# (examples/ altında çok sayıda örnek config bulunur; kendi YAML'ınızı da yazabilirsiniz)
llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml
```

Arayüz, eğitim parametrelerini form alanlarına dönüştürdüğü için "hangi düğme ne yapıyor?" öğrenmek için mükemmel bir oyuncak alanıdır — ama aynı kavramları öğrendikten sonra bu sayfadaki [Hiperparametreler](/llm/hiperparametreler/) bilgisini taşımak kolaydır.

### HF TRL + PEFT

Kod tabanlı, en düşük seviyeli ama en esnek seçenek. Tam örnek [SFT sayfasında](/llm/sft/):

```bash title="trl_kurulum.sh"
pip install "trl" "peft" "datasets" "transformers" "accelerate" "bitsandbytes"
```

```python title="trl_hizli_baslangic.py"
from trl import SFTTrainer

egitici = SFTTrainer(
    model="Qwen/Qwen3-4B",
    train_dataset=veri,          # messages formatlı veri
)
egitici.train()
```

:::tip
TRL'i öğrenmenin en büyük avantajı: Diğer araçlar bir sorun çıkardığında (ör. tuhaf bir hata mesajı, beklenmeyen davranış), sorunun "hangi katmanda" olduğunu anlayabilmenizdir. TRL öğrenen kişi, Unsloth ve Axolotl'u da kolayca okur; çünkü ikisi de TRL'den tanıdık kavramlar ve parametreler kullanır.
:::

## Hangisiyle Başlamalıyım?

:::tip
- **Yeni başlayan, hemen sonuç görmek isteyen:** Unsloth (tek GPU, hızlı) veya LLaMA-Factory (hiç kod yazmadan).
- **Öğrenme amaçlı, temelleri anlamak isteyen:** Önce TRL'i görün — [SFT](/llm/sft/) ve [LoRA/QLoRA](/llm/lora-qlora/) sayfalarındaki örnekler zaten TRL + PEFT kullanıyor. Kavramlar oturunca Unsloth'un hız kazandırdığını, Axolotl'un üretimde ne çözdüğünü daha iyi anlarsınız.
- **Ekip içinde üretim/tekrarlanabilirlik:** Axolotl'un YAML config'i tam bunun içindir.
:::

## Araçlar Arasında Geçiş

Bir araçtan diğerine geçmek sandığınızdan kolaydır: kavramlar (LoRA, öğrenme oranı, kayıp maskesi, warmup) aynı kalır; yalnızca anahtar adları ve arayüz değişir. Aşağıdaki eşleme en sık karışan adları gösterir; anlamlar için [Hiperparametreler](/llm/hiperparametreler/) sayfasındaki açıklamalar geçerlidir.

| Kavram | TRL + PEFT | Unsloth | Axolotl | LLaMA-Factory |
| --- | --- | --- | --- | --- |
| Maksimum dizi uzunluğu | `max_length` | `max_seq_length` | `sequence_len` | `cutoff_len` |
| Etkin batch | `per_device_train_batch_size` + `gradient_accumulation_steps` | aynı | `micro_batch_size` + `gradient_accumulation_steps` | `per_device_train_batch_size` + `gradient_accumulation_steps` |
| Epoch sayısı | `num_train_epochs` | `num_train_epochs` | `num_epochs` | `num_train_epochs` |
| LoRA rank | `r` | `r` | `lora_r` | `lora_rank` |
| LoRA hedef modülleri | `target_modules` | `target_modules` | `lora_target_modules` | `lora_target` |
| Warmup | `warmup_steps` (ondalık = oran; v5) | `warmup_steps` | `warmup_ratio` (içeride `warmup_steps`'e çevrilir) | `warmup_ratio` (resmî örnek config'lerde) |

Taşırken kontrol listesi:

1. **Veri formatı** — Çoğu araç aynı JSONL'i okur ama alan adları ve eşleme ayarları araçtan araca değişir (Axolotl'da `datasets[].type`, LLaMA-Factory'de `template`). Hedef araçta ilk 5-10 örneği işlenmiş haliyle okuyup doğrulayın; ayrıntı: [Veri Formatları](/veri/veri-formatlari/).
2. **Sohbet şablonu (chat template)** — Eğitimde kullandığınız şablon hedef araçta da aynı olmalı; şablon değişirse model "dağılmış" gibi davranır.
3. **Hiperparametreler değişmez, isimler değişir** — lr, epoch ve etkin batch'i aynı tutun; adları yukarıdaki tablodan çevirin. Warmup notu: TRL/Unsloth tarafında güncel ad `warmup_steps` (ondalık değer = oran), Axolotl şeması ise `warmup_ratio`'yu kabul edip içeride dönüştürür.
4. **Kayıp maskesi** — "yalnızca asistan yanıtından öğren" seçeneğinin adı her araçta farklıdır; yanlış kurulursa model sistem istemini de ezberler ve çıktı kalitesi düşer.
5. **Duman testi** — Taşıma sonrası uzun koşuya başlamadan önce 100-200 örnekle birkaç adım koşup kayıp eğrisinin önceki araçtakiyle benzer başladığını görün.

## Toparlarsak

- Dört araç da aynı alt katmanı kullanır; aralarında geçiş yapmak, sıfırdan öğrenmekten çok kolaydır.
- Unsloth hız + VRAM, Axolotl üretim + tekrarlanabilirlik, LLaMA-Factory kolaylık, TRL esneklik + öğrenme içindir.
- Hangi araçla başlarsanız başlayın, veri kalitesi ve değerlendirme araçtan daha belirleyicidir.

Devam: [Hiperparametreler](/llm/hiperparametreler/) ile seçtiğiniz aracın ayarlarını doğru doldurun, [Adım Adım Eğitim](/llm/adim-adim-egitim/) ile uçtan uca akışı izleyin.

## Kaynaklar ve İleri Okuma

- [Unsloth dokümantasyonu](https://unsloth.ai/docs) — kurulum, hızlı başlangıç, DPO/GRPO kılavuzları ve GGUF'a kaydetme.
- [Axolotl dokümantasyonu](https://docs.axolotl.ai/) — YAML yapılandırma referansı, RLHF yöntemleri (DPO/ORPO/KTO/GRPO) ve GGUF dışa aktarma.
- [LLaMA-Factory (GitHub)](https://github.com/hiyouga/LLaMA-Factory) — 100+ model desteği, web arayüzü ve hazır örnek konfigürasyonlar.
- [TRL dokümantasyonu](https://huggingface.co/docs/trl/) — eğitici (trainer) taksonomisi, veri formatları ve pekiştirmeli öğrenme rehberleri.
