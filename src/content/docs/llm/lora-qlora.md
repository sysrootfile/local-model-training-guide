---
title: "LoRA ve QLoRA: Az VRAM'le İnce Ayar"
description: "LoRA'nın sezgisi, QLoRA ile 4-bit eğitim, rank ve katman seçimi kanıtları, rsLoRA ve DoRA, adaptör yaşam döngüsü ve peft ile klasik Trainer akışında tam bir QLoRA örneği."
dogrulama: 2026-10-17
---

**LoRA (low-rank adaptation)**, büyük bir modeli ince ayarlamanın (fine-tuning) en yaygın yoludur. Fikir şudur: 7 tonluk dev bir mermer heykeli baştan yontmak yerine, heykelin üzerine istediğiniz şekli veren **ince bir sıva tabakası** eklersiniz. Orijinal heykel (model ağırlıkları) olduğu gibi kalır; yalnızca üstteki ince tabaka (adaptör) eğitilir.

## LoRA Nasıl Çalışır?

Bir sinir ağı katmanının ağırlık matrisini `W` düşünün (ör. 4096 × 4096 = ~16,7 milyon parametre). Eğitim normalde bu `W`'nun her elemanını günceller. LoRA ise güncellemeyi iki **küçük** matrisin çarpımı olarak temsil eder:

```text title="LoRA fikri"
Tam güncelleme:    W_guncel = W_orijinal + ΔW          (ΔW: 4096 x 4096 — devasa!)

LoRA ile:          W_guncel = W_orijinal + B · A       (A: 16 x 4096, B: 4096 x 16)

  - W_orijinal: DONAR (eğitilmez) — 16,7 milyon parametre sabit
  - A ve B: eğitilir — toplam 131.072 parametre (r=16 için)
  - Oran: ~%0,8. Yani parametrelerin binde biri kadarını eğitiyorsunuz.
```

Küçük `r` (rank) değeri, güncellemenin "kapasitesini" sınırlar: `r=16` ile ifade edilebilen değişiklikler, tam güncellemeden çok daha "düşük boyutlu"dur. Pratikte bu genellikle yeterlidir; çünkü modelin yeni bir görev öğrenmesi için gereken değişiklik, orijinal eğitimden çok daha küçüktür.

Bunun üç büyük sonucu vardır:

1. **VRAM tasarrufu:** Optimizasyon durumu (optimizer state) yalnızca adaptör için tutulur.
2. **Küçük çıktı:** Eğitilmiş adaptör birkaç MB tutar; temel modeli her seferinde kopyalamanız gerekmez.
3. **Çoklu kullanım:** Aynı temel model üzerine farklı görevler için farklı adaptörler eğitip, çalışma anında aralarında geçiş yapabilirsiniz.

## QLoRA: 4-bit Model + LoRA

Normal LoRA'da bile temel model fp16 (16-bit) olarak yüklenir. 8B parametreli bir model için bu tek başına `8 milyar × 2 bayt = ~16 GB` VRAM demektir. **QLoRA** burada devreye girer: temel model **4-bit** olarak nicemlenir (quantization), üzerine LoRA eğitilir.

| | 8B modelin yaklaşık VRAM'i |
| --- | --- |
| fp16 yükleme | ~16 GB (yalnızca ağırlıklar) |
| 4-bit yükleme | ~4-5 GB (ağırlıklar) + eğitim ek yükü |
| QLoRA toplam (LoRA + gradyan checkpointing ile) | yaklaşık 5-6 GB |

QLoRA makalesi (2305.14314), 4-bit nicemlemenin kalite kaybının çok küçük olduğunu gösterdi: iyi ayarlanmış bir QLoRA eğitimi, fp16 LoRA'ya çok yakın sonuç verir. Bu sayede 8-12 GB VRAM'li tüketici kartlarında 4B modeller, 16-24 GB kartlarda 8B modeller rahatça eğitilebilir. Donanım eşleştirme tablosu için [VRAM Hesaplama](/donanim/vram-hesabi/) sayfasına bakın.

:::note
4-bit nicemlemede kullanılan "nf4" (normal float 4), ağırlıkların normal dağılıma yakın olduğu varsayımıyla tasarlanmış özel bir 4-bit formattır. `bitsandbytes` kütüphanesi bunu sizin için yapar; detayları bilmeniz gerekmez — ama ayarları tanımak için yukarıdaki tabloyu aklınızda tutun.
:::

### Üçlü mekanizma: NF4, çift niceleme, paged optimizer

QLoRA'nın bellek tasarrufu tek bir numara değil, üç mekanizmanın bileşimidir (QLoRA makalesi, arXiv:2305.14314):

1. **NF4 (4-bit NormalFloat):** Normal dağılıma yakın ağırlıklar için tasarlanmış 4-bit depolama formatı; ağırlıkları bu dağılıma göre en verimli biçimde kodlar.
2. **Çift niceleme (double quantization):** Niceleme sabitlerini de niceleyerek bellek kazancını bir kat daha artırır.
3. **Paged optimizer:** Bellek zirvelerinde optimizasyon durumunun CPU belleğine sayfalanmasına izin verir; ani taşmaları (OOM) önlemeye yardımcı olur.

Makalenin öne çıkan sonucu: bu üçlü sayesinde 65B parametreli bir model **tek bir 48 GB GPU'da** ince ayarlanabiliyor ve sonuçlar tam 16-bit ince ayarın görev performansını koruyor (QLoRA makalesi, özet).

### QLoRA sonrası akış: birleştir, nicemle, servis et

Eğitim bittiğinde elinizde yalnızca adaptör vardır (birkaç MB). Üretime giden tipik yol üç adımdır:

1. **16-bit tabanda birleştirin:** Temel modeli **16-bit (bf16/fp16) yeniden yükleyip** adaptörü uygulayın ve `merge_and_unload()` ile tek modele birleştirin. peft'te bu yöntem, temel modelin mimarisinde bağımsız bir model döndürür; sonucu bir değişkene atamanız gerekir — yerinde işlem değildir (peft dokümanı). Adım adım anlatım: [LoRA Birleştirme](/kullanim/lora-birlestirme/).
2. **Nicemleyin (isteğe bağlı):** Birleşik 16-bit modeli GGUF gibi dağıtım formatlarına çevirin: [Nicemleme](/kullanim/quantization/).
3. **Servis edin:** Yerel kullanım için [Ollama](/kullanim/ollama/), API için [Sunma ve API](/kullanim/sunma-api/).

:::caution
Adaptörü **4-bit nicemli tabana doğrudan birleştirmeyin.** Doğru ve önerilen akış, taban modeli 16-bit yükleyip birleştirmek, dilediğinizde sonucu yeniden nicemlemektir. 4-bit tabana doğrudan merge, kalite kaybı riski taşır; topluluk deneyimi de "önce serbest bırak (dequantize), sonra birleştir" yönündedir (ör. Hugging Face forum tartışmaları ve bağımsız QLoRA yazıları). Birleştirdiğiniz modeli, birleştirme öncesiyle aynı sabit test sorularında karşılaştırmadan üretime almayın.
:::

## Kritik Parametreler

| Parametre | Ne yapar | Tipik değer | Seçim ipucu |
| --- | --- | --- | --- |
| `r` (rank) | Adaptörün kapasitesi | 8 / 16 / 32 / 64 | Basit format görevi: 8-16. Geniş davranış değişimi: 32-64. Küçük veri: 8. |
| `lora_alpha` | Güncellemenin etkisini ölçekler | Genelde `2 × r` | r=16 → alpha=32. r ile birlikte büyütün. |
| `lora_dropout` | Aşırı uyumu (overfitting) engeller | 0.0 – 0.05 | Veri azsa 0.05; veri bolsa 0 bırakılabilir. |
| `target_modules` | Adaptör hangi katmanlara eklenecek | `q_proj, k_proj, v_proj, o_proj` + MLP kapıları | "Tüm doğrusal katmanlar" (`q,k,v,o,gate,up,down`) güvenli ve iyi bir başlangıçtır. |
| `bias` | Ek sapma (bias) terimleri eğitilsin mi | `"none"` | Neredeyse her zaman `"none"`; eski rehberlerde `"all"` görürseniz şaşırmayın, gerekmez. |
| `use_gradient_checkpointing` | Ara aktivasyonları saklamak yerine yeniden hesaplar | Az VRAM'de açık | VRAM'i belirgin düşürür, eğitimi ~%20-30 yavaşlatır. |

:::tip
İlk denemenizde şu başlangıç ayarını kullanın: `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, `target_modules` tüm doğrusal katmanlar. Ancak sonuçtan memnun kalmayıp "model yeterince değişmiyor" derseniz, ilk deneyeceğiniz şey `r`'ı 32-64'e çıkarmak olsun. Diğer detaylar için [Hiperparametreler](/llm/hiperparametreler/) sayfasına bakın.
:::

## Rank Seçimi Neye Bağlı? Kanıt: "LoRA Learns Less and Forgets Less"

"Rank'ı büyütünce tam ince ayara yaklaşır mıyım?" sorusunun en kapsamlı deneysel yanıtlarından biri Biderman ve arkadaşlarının çalışmasıdır (arXiv:2405.09673). Öne çıkan bulgular:

- **Hedef alanda (on-target) geride kalır:** Kod gibi hedef alanlarda LoRA, tam ince ayarın belirgin biçimde altında kalır; rank artırmak bu farkı kapatmaz.
- **Alana göre fark değişir:** Matematik tarafında LoRA, tam ince ayara daha çok yaklaşır; buna karşın tam ince ayar daha **örnek verimli**dir (aynı başarı için daha az veri yeter).
- **Hedef dışı alanda (off-target) avantaj LoRA'da:** LoRA, temel modelin hedef alan dışındaki yeteneklerini tam ince ayardan daha iyi korur — yani daha az unutur.
- **Neden böyle?** Tam ince ayar, tipik LoRA yapılandırmalarından **10-100 kat daha yüksek ranklı** değişiklikler öğrenir; LoRA'nın düşük rank kısıtı bazı hedeflerde doğal bir tavan oluşturur.

Pratik çeviri: rank seçimi "büyük olsun, zararı yok" işi değil, **hedefinizin karakterine** bağlıdır.

| Durumunuz | Rank önerisi |
| --- | --- |
| Üslup/format değişimi, tek görev | r=8-16 yeterli; enerjiyi veriye harcayın |
| Kod/matematik gibi yoğun hedef alan eğitimi | r=32-64 deneyin; fark sürüyorsa tam ince ayarı değerlendirin |
| Alan uyarlama + eski yetenekleri koruma önceliği | LoRA zaten tam ince ayardan daha az unutur; rank'ı abartmayın |
| Az veri (birkaç bin örnek) | Küçük rank (r=8) genelde daha güvenli |

## rsLoRA ve DoRA: İki İyileştirme, Ne Zaman Düşünülür?

Klasik LoRA güncellemeyi `alpha / r` ile ölçekler. Rank büyüdükçe bu ölçek küçülür ve yüksek ranklarda adaptörün etkisi beklenmedik biçimde zayıflayabilir. İki popüler çözüm:

| Yöntem | Fikri | peft'te | Ne zaman düşünülür? |
| --- | --- | --- | --- |
| **rsLoRA** (arXiv:2312.03732) | Ölçeği `alpha / r` yerine `alpha / sqrt(r)` yapar; yüksek ranklarda eğitimi dengeler | `LoraConfig(use_rslora=True)` | Rank'ı 64 ve üzeri kullanacaksanız; yüksek rankta "model öğrenmiyor" hissi varsa |
| **DoRA** (arXiv:2402.09353) | Ağırlık güncellemesini **büyüklük (magnitude)** ve **yön (direction)** olarak ikiye ayırır: yönü LoRA öğrenir, büyüklüğü ayrı bir parametre taşır | `LoraConfig(use_dora=True)` | Özellikle **düşük ranklarda** kaliteyi artırmak istiyorsanız |

Maliyet farkı önemli: rsLoRA neredeyse bedavadır (yalnızca ölçek formülü değişir, ek parametre gelmez). DoRA ise eğitimi yavaşlatır ve bellek kullanımını artırır; peft dokümanı DoRA'da çıkarım öncesi birleştirmeyi önerir ve DoRA'nın yalnızca doğrusal (linear) ve Conv2D katmanlarını desteklediğini not eder. İkisi de "varsayılan" değil, ihtiyaç halinde denenecek seçeneklerdir: önce klasik LoRA ile iyi bir taban sonuç alın, sonra karşılaştırın.

## Hangi Katmanlara LoRA? `q,v` mi, Tüm Doğrusal Katmanlar mı?

Ablasyonların en net bulgularından biri QLoRA makalesinden gelir: tam ince ayar performansına ulaşmak için LoRA'nın **tüm doğrusal transformer bloğu katmanlarına** uygulanması gerektiğini raporlar (arXiv:2305.14314). Modern rehberlerin çoğu bu yüzden `q,v` ile sınırlı kalmaz:

| Seçim | Kapsam | Ne zaman mantıklı? |
| --- | --- | --- |
| `["q_proj", "v_proj"]` | Klasik tariflerden kalan en ucuz seçenek | Çok basit üslup ayarı; VRAM iyice kısıtlıysa |
| `["q_proj", "k_proj", "v_proj", "o_proj"]` | Dikkat projeksiyonlarının tamamı | Orta yol; değişim ağırlıkla dikkat katmanlarında yaşanıyorsa |
| `"all-linear"` | Modeldeki tüm doğrusal katmanlar: dikkat + MLP (`gate`, `up`, `down`) | Modern varsayılan; QLoRA tarifleri bu kapsamı kullanır |

peft'te kısayol: `LoraConfig(target_modules="all-linear")` ifadesi tüm doğrusal/Conv1D modülleri seçer (çıktı katmanı hariç — peft dokümanı). Model ailelerine göre isimler değişir (Qwen/Llama: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`); emin değilseniz `all-linear` bırakın. Yanlış isim verirseniz peft eğitilebilir modül bulamaz ve hata verir — sessizce boş bir eğitim yapmaz.

BERT ailesinde (embedding modelleri dâhil) dikkat hatları `query` / `key` / `value` / `dense` olarak adlandırılır; `q_proj` verdiğinizde hata alırsınız. Bu tuzağı bir gömme modelinde gerçekten çalıştırarak ölçtük: [Gömme Modeli Eğitmek](/rag/gomme-egitimi/) sayfasındaki LoRA kolunda hedefler `["query", "value"]` ve eğitilebilir parametre oranı sayıyla veriliyor.

:::tip
Katman kapsamını genişletmek (ör. yalnız `q,v` yerine `all-linear`), tipik olarak aynı rank ile daha fazla görev kazanımı getirir; karşılığında eğitilebilir parametre sayısı ve VRAM kullanımı biraz artar. Önerilen sıra: önce katman kapsamını açın, sonra rank'ı büyütün.
:::

## LoRA mı, Tam İnce Ayar mı?

| | LoRA / QLoRA | Tam ince ayar (full fine-tuning) |
| --- | --- | --- |
| VRAM ihtiyacı | Az (4-8x tasarruf) | Çok |
| Eğitim hızı | Hızlı | Yavaş |
| Çıktı boyutu | Adaptör: birkaç MB | Modelin tamamı: GB'lar |
| Davranış değişimi derinliği | Çoğu format/üslup görevi için yeterli | Çok derin davranış değişimi gerekirse |
| Çoklu görev | Aynı temel model + farklı adaptörler | Her görev için ayrı tam model |
| Zorluk | Kolay | Daha zor (kararlılık, kaynak yönetimi) |
| Ne zaman seçilir | **Neredeyse her zaman ilk tercih** | Yeterli donanım + LoRA'nın yetmediği durumlar |

:::caution
"LoRA gerçek ince ayar değil" yaygın ama yanlış bir inanıştır. Format, üslup, alan jargonu ve görev davranışı değişikliklerinin çoğu LoRA ile gayet iyi öğrenilir. Tam ince ayar, ancak LoRA ile doygunluğa ulaştığınızda (genellikle çok özel durumlarda) gündeme gelir.
:::

## Tam Örnek: peft + transformers ile QLoRA

[SFT sayfasındaki](/llm/sft/) örnek `SFTTrainer` kullanıyordu. Burada ise **klasik `Trainer` akışını** görüyoruz; böylece altta dönen mekanizmayı (veri işleme, collator, kayıp) daha net görürsünüz:

```python title="qlora_egitimi.py"
# QLoRA: temel modeli 4-bit'e nicemle + üzerine LoRA adaptörü eğit
# Kurulum:
#   pip install transformers peft bitsandbytes datasets accelerate

import torch
from datasets import load_dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, TrainingArguments, Trainer,
                          DataCollatorForLanguageModeling)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

MODEL_ADI = "Qwen/Qwen3-4B"

# ---------------------------------------------------------------------------
# 1) 4-bit nicemleme ayarı — VRAM tasarrufunun sırrı burada
# ---------------------------------------------------------------------------

bnb_ayari = BitsAndBytesConfig(
    load_in_4bit=True,                      # ağırlıkları 4-bit olarak yükle
    bnb_4bit_quant_type="nf4",              # "normal float 4": önerilen nicemleme türü
    bnb_4bit_use_double_quant=True,         # ikinci nicemleme katmanı: biraz daha tasarruf
    bnb_4bit_compute_dtype=torch.bfloat16,  # matris çarpımları bf16'da hesaplanır
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ADI)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ADI,
    quantization_config=bnb_ayari,
    device_map="auto",                      # katmanları GPU'ya otomatik yerleştir
)

# ---------------------------------------------------------------------------
# 2) 4-bit eğitime hazırla:
#    - gradyan checkpointing açılır (VRAM tasarrufu)
#    - layernorm katmanları hesaplama kararlılığı için fp32'ye çekilir
# ---------------------------------------------------------------------------

model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

# ---------------------------------------------------------------------------
# 3) LoRA yapılandırması
# ---------------------------------------------------------------------------

lora_ayari = LoraConfig(
    r=16,                                   # rank: adaptörün kapasitesi
    lora_alpha=32,                          # ölçek: genelde r'nin 2 katı
    lora_dropout=0.05,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],  # tüm doğrusal katmanlar
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_ayari)
model.print_trainable_parameters()  # "trainable: ~%0,5-1" göreceksiniz

# ---------------------------------------------------------------------------
# 4) Veri: basit bir ön eğitim tarzı "sonraki jetonu tahmin et" örneği.
#    (Talimat verisiyle çalışmak için /llm/sft/ sayfasındaki örneğe bakın.)
# ---------------------------------------------------------------------------

veri = load_dataset("atasoglu/instruction-turkish", split="train[:3000]")

def hazirla(ornek):
    # "prompt + completion" alanlarını tek bir metne birleştirin;
    # veri setinizin alan adlarını kendi verinize göre uyarlayın.
    metin = ornek.get("prompt", "") + "\n" + ornek.get("completion", "")
    paket = tokenizer(metin, truncation=True, max_length=1024)
    paket["labels"] = paket["input_ids"].copy()  # dil modellemesi: hedef = girdinin kendisi
    return paket

veri = veri.map(hazirla, remove_columns=veri.column_names)

# ---------------------------------------------------------------------------
# 5) Eğitim ayarları ve klasik Trainer akışı
# ---------------------------------------------------------------------------

egitim_ayari = TrainingArguments(
    output_dir="./qlora-cikti",
    num_train_epochs=2,
    per_device_train_batch_size=2,          # VRAM yetmezse 1 yapın
    gradient_accumulation_steps=4,          # etkin batch = 8
    learning_rate=2e-4,                     # LoRA/QLoRA için tipik değer
    lr_scheduler_type="cosine",
    warmup_steps=0.03,                      # oran: adımların %3'ü (v5; eskiden warmup_ratio)
    bf16=torch.cuda.is_bf16_supported(),
    gradient_checkpointing=True,
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
)

egitici = Trainer(
    model=model,
    args=egitim_ayari,
    train_dataset=veri,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
)
egitici.train()

# ---------------------------------------------------------------------------
# 6) Yalnızca adaptörü kaydet (temel model değil — sadece birkaç MB):
# ---------------------------------------------------------------------------

model.save_pretrained("./qlora-adaptor")
tokenizer.save_pretrained("./qlora-adaptor")
```

:::note
Dikkat: Bu klasik akışta kayıp **tüm** jetonlardan hesaplanır (kayıp maskesi yoktur). Talimat verisiyle çalışırken kayıp maskesini kullanmak isterseniz `SFTTrainer(assistant_only_loss=True)` kullanan [SFT](/llm/sft/) örneğini tercih edin. Kavramın kendisi [SFT sayfasında](/llm/sft/) anlatılıyor.
:::

## Sık Sorular

:::tip
**"r'ı ne seçeyim?"**
İlk deneme: `r=16`. Modelin davranışı yeterince değişmiyorsa `r=32` veya `64` deneyin (alpha'yı da 2×r yapın). Veri az ve ezber riski varsa `r=8` daha güvenli olabilir. `r`'ı artırmak VRAM'i çok az artırır; tek maliyeti biraz hız ve fazlaca ezber potansiyelidir.

**"Adaptörü nasıl kaydederim, nasıl geri yüklerim?"**

```python
# Kaydetme (eğitim sonunda):
model.save_pretrained("./adaptor")

# Geri yükleme (çıkarım için):
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

temel = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-4B")
model = PeftModel.from_pretrained(temel, "./adaptor")
```

Adaptör tek başına çalışmaz; her zaman bir **temel model** ile birlikte yüklenir. Tek dosyada taşımak isterseniz adaptörü temel modele birleştirin: [LoRA Birleştirme](/kullanim/lora-birlestirme/).

**"Modeli nasıl çalıştırırım?"**
Hızlı yerel kullanım için [Ollama](/kullanim/ollama/), API olarak sunmak için [Sunma ve API](/kullanim/sunma-api/), Hugging Face'te paylaşmak için [Hugging Face Paylaşımı](/kullanim/huggingface-paylasim/) sayfalarına bakın.

**"Birden çok adaptör eğitebilir miyim?"**
Evet, LoRA'nın en güzel yanlarından biri bu: aynı temel model üzerinde farklı görevler için ayrı adaptörler eğitin, çalışma anında ihtiyacınıza göre adaptör değiştirin. Disk maliyeti adaptör başına yalnızca birkaç MB'dır.
:::

## Adaptör Yaşam Döngüsü: Sürümle, Servis Et, Doğrula

Adaptör bir "yan dosya" değil, yönetilmesi gereken bir **artefakttır**:

- **Sürümleyin:** Her adaptörü kaydederken yanına şunları not edin: temel modelin adı **ve revizyonu**, eğitim verisinin sürümü/özeti, `r`, `alpha`, `target_modules`, epoch sayısı ve öğrenme oranı. Aynı temel modelin farklı revizyonlarıyla eğitilmiş adaptörler uyumsuz olabilir; "bu hangi koşunun çıktısı?" sorusu mutlaka geri döner.
- **Çoklu adaptör servis edin:** Aynı temel model üzerinde birden çok adaptör çalıştırılabilir. peft'te `model.load_adapter("...", adapter_name="gorev_a")` ile adaptörler yüklenir, `set_adapter` ile aktif olan seçilir. vLLM gibi sunum motorları, `--enable-lora` ve `--lora-modules` bayraklarıyla birden çok LoRA'yı aynı anda sunar (`max_loras` ve `max_lora_rank` ile sınırlar ayarlanır).
- **Birleştirme sonrasını doğrulayın:** Birleştirme matematiksel olarak eşdeğer olmalıdır, ama "olmalı" ile "oldu" farklıdır: 10-20 sabit test sorusu belirleyin ve birleştirme öncesi/sonrası çıktıları karşılaştırın. Sessiz bozulmaların çoğu bu adımda yakalanır.
- **Ham adaptörü saklayın:** Birleştirilmiş modelin yanında orijinal adaptörü (birkaç MB) da arşivleyin; yeni bir temel model sürümüne geçerken sıfırdan eğitim yerine yeniden birleştirme + doğrulama yeterli olabilir.

## Unsloth: Hızlı Alternatif (2026 Durumu)

Unsloth, aynı peft/TRL iş akışını hızlandıran, Hugging Face ekosistemiyle uyumlu bir eğitim çerçevesidir; TRL dokümanları onu "2 kata kadar hızlı, %70'e kadar az VRAM" iddiasıyla anar (TRL dokümanı, 2026). Dürüst durum tespiti:

- 2026 itibarıyla proje çok hızlı bir sürüm temposunda ve sürümlerini "beta" etiketiyle yayınlıyor (13 Ekim 2026 itibarıyla en güncel etiket: `v0.1.907-beta`, GitHub sürümleri).
- Beta etiketi "kullanılamaz" demek değildir; ancak üretim hattınızı güncellemeden önce sürüm notlarını okuyun ve kendi testlerinizi koşun.
- Geçişten önce klasik TRL/peft akışıyla çalışan bir taban sonuç alın; hız kazancını kendi verinizle ölçün.

Karşılaştırma tablosu ve kurulum için: [Araçlar Karşılaştırması](/llm/araclar/).

## Türkçe Token Verimliliği: Neden Model Seçimi Maliyeti Değiştirir

Türkçe eklemeli (agglutinative) bir dildir: tek bir kelime, başka bir dilde birkaç kelimeye karşılık gelebilir. Farklı modellerin sözlükleri (vocabulary) farklı verilerle eğitildiği için **aynı Türkçe metin, modele göre farklı sayıda jetona ayrılabilir**. Bu doğrudan iki şeyi etkiler:

- **Eğitim ve çıkarım maliyeti:** Fiyatlandırma çoğunlukla jeton başına yapılır; aynı metin daha çok jetona bölünürse aynı iş daha pahalıdır.
- **Etkin bağlam penceresi:** 8.192 jetonluk bir bağlam, Türkçe'de "daha az metin" anlamına gelebilir; uzun belge veya RAG işlerinde bu sınırı erken hissedersiniz.

Bu konuda kamuya açık, güvenilir ve karşılaştırılabilir bir ölçüm bulamadık — uydurma oranlar vermektense ölçmenin tarifini verelim. Kendi adaylarınızı şöyle kıyaslayın:

```python
from transformers import AutoTokenizer

metin = ("Model eğitimi sabır isteyen uzun bir yolculuktur; veri kalitesi "
         "hiperparametrelerden önce gelir.")
kelime_sayisi = len(metin.split())

adaylar = ["Qwen/Qwen3-4B", "BURAYA-KENDI-ADAYINIZI-YAZIN"]

for ad in adaylar:
    tok = AutoTokenizer.from_pretrained(ad)
    jeton = len(tok.encode(metin))
    print(f"{ad}: {jeton} jeton  (jeton/kelime = {jeton / kelime_sayisi:.2f})")
```

Yöntem: tek cümle yanıltıcıdır — **gerçek verinizden** 20-50 cümlelik bir örneklem alın ve her aday tokenizer için jeton/kelime oranını hesaplayın. Düşük oran, aynı veriyi daha az jetonla temsil eden (Türkçe'de daha verimli) bir tokenizer işaretidir; nihai kararı yine görev başarımı verir. Tokenizasyonun temelleri için: [Tokenizasyon](/temeller/tokenizasyon/).

## Toparlarsak

- LoRA: orijinal ağırlıklar donar, küçük adaptör matrisleri eğitilir. Çıktı birkaç MB'tır.
- QLoRA: temel model 4-bit nicemlenir; 8B model bile ~5-6 GB VRAM'e sığar, kalite kaybı küçüktür.
- Başlangıç ayarı: `r=16`, `alpha=32`, `dropout=0.05`, tüm doğrusal katmanlar, `bias="none"`.
- İlk tercih her zaman LoRA/QLoRA olsun; tam ince ayar sonraki adımdır.

Sıradaki duraklar: [Adım Adım Eğitim](/llm/adim-adim-egitim/), [Hiperparametreler](/llm/hiperparametreler/) ve eğitim sonrası [LoRA Birleştirme](/kullanim/lora-birlestirme/).

## Kaynaklar ve İleri Okuma

- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314) — NF4, çift niceleme ve paged optimizer; 65B modelin tek 48 GB GPU'da eğitimi.
- [LoRA: Low-Rank Adaptation of Large Language Models (arXiv:2106.09685)](https://arxiv.org/abs/2106.09685) — orijinal LoRA makalesi.
- [LoRA Learns Less and Forgets Less (arXiv:2405.09673)](https://arxiv.org/abs/2405.09673) — hedef/hedef dışı alan ayrımı, rank etkisi ve unutma karşılaştırması.
- [A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA (arXiv:2312.03732)](https://arxiv.org/abs/2312.03732) — rsLoRA.
- [DoRA: Weight-Decomposed Low-Rank Adaptation (arXiv:2402.09353)](https://arxiv.org/abs/2402.09353) — DoRA.
- [peft — LoRA referansı](https://huggingface.co/docs/peft/package_reference/lora) — `use_rslora`, `use_dora` ve `all-linear` parametrelerinin güncel tanımları.
- [TRL — SFT Trainer dokümanı](https://huggingface.co/docs/trl/sft_trainer) — Unsloth entegrasyonu ve eğitim varsayılanları.
- [vLLM — LoRA desteği](https://docs.vllm.ai/en/latest/features/lora.html) — çoklu adaptör sunumu (`--enable-lora`, `--lora-modules`).
