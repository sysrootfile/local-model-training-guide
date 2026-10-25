---
title: "Hiperparametreler: Doğru Ayar Rehberi"
description: "Öğrenme oranından paketlemeye kadar eğitimin tüm düğmeleri, QLoRA taramasından kanıtlar, kütüphane varsayılanları, kopyala-yapıştır başlangıç ayarları ve belirti-çözüm tablosu."
dogrulama: 2026-10-17
---

Model ağırlıkları veriden öğrenilir; **hiperparametreler ise sizin elle çevirdiğiniz düğmelerdir**. Aynı veri ve aynı model, yanlış düğme ayarlarıyla hiç öğrenmezken doğru ayarlarla gayet iyi sonuç verebilir. Bu sayfa, düğmeleri tek tek tanıtır; sonunda üç hazır ayar seti ve bir belirti-çözüm tablosu bulacaksınız.

:::tip
Panik yapmayın: Gerçekte çoğu projede **iki düğme** belirleyicidir — öğrenme oranı ve veri miktarı. Diğerlerini makul bir varsayılanla bırakıp, yalnızca sorun çıktığında kurcalamak tamamen normaldir.
:::

## Learning Rate (Öğrenme Oranı): En Kritik Düğme

Modelin her adımda ne kadar "büyük adım" atacağını belirler. Çok küçükse model öğrenmez (kayıp inatla aynı kalır); çok büyükse model bir oraya bir buraya savrulur, hatta kayıp NaN olur.

| Senaryo | Tipik öğrenme oranı |
| --- | --- |
| LoRA / QLoRA | 1e-4 – 2e-4 |
| Tam ince ayar (full fine-tuning) | 1e-5 – 2e-5 |
| DPO | 5e-7 – 1e-6 |
| Sıfırdan ön eğitim | 1e-4 – 6e-4 (genelde büyük modellerde küçülür) |

Neden LoRA'da daha büyük? Çünkü eğitilen parametre sayısı azdır; adaptörün etkili olması için daha büyük adımlar gerekir. Tam ince ayarda tüm ağırlıklar oynadığı için küçük adımlar yeterlidir ve güvenlidir.

:::caution
Bir ayarı kopyalarken **hangi yönteme ait olduğuna** dikkat edin: LoRA örneğinden `2e-4` alıp tam ince ayara koyarsanız model büyük olasılıkla bozulur. DPO'da ise `2e-4` felakettir; `5e-7`'den büyük başlamayın.
:::

### Kanıt: QLoRA makalesinin hiperparametre taraması

Yukarıdaki bantlar deneyimden geliyor; en bilinen dayanaklardan biri QLoRA makalesinin kendi taramasıdır (arXiv:2305.14314, Tablo 9). Makale, model boyutuna göre en iyi LoRA öğrenme oranını şöyle raporlar:

| Model boyutu | En iyi LoRA öğrenme oranı |
| --- | --- |
| 7B ve 13B | 2e-4 |
| 33B ve 65B | 1e-4 (öğrenme oranı yarıya indirilirken batch boyutu iki katına çıkarılır) |

Eğilim net: **model büyüdükçe en iyi öğrenme oranı düşer.** Bu değerleri "kanun" değil, kendi model boyutunuz için taramanın başlangıç noktası olarak alın. İkinci bir not: "LoRA Learns Less and Forgets Less" çalışması, LoRA'nın tam ince ayara kıyasla öğrenme oranına **daha duyarlı** olduğunu ve kararlılığı bozmayan en yüksek orandan fayda gördüğünü raporlar (arXiv:2405.09673). Yani LoRA'da aşırı muhafazakâr bir lr seçimi, tam ince ayardakinden daha görünür bir kayıp yaratır.

## Learning Rate Zamanlaması: Scheduler ve Warmup

- **`lr_scheduler_type`:** Öğrenme oranının eğitim boyunca nasıl değişeceği. `cosine` neredeyse her zaman iyi bir varsayılandır (yüksek başlar, yumuşakça sıfıra iner). Kısa işlerde (yarım saat altı) `linear` de yaygındır. `constant` basit ama genelde bir tık kötüdür.
- **Isınma (warmup — v5'te `warmup_steps`, eski sürümlerde `warmup_ratio`):** Eğitimin ilk adımlarında öğrenme oranı sıfırdan hedefe kademeli açılır. Tipik değer **0.03 – 0.1** (adımların %3-10'u). Warmup, eğitimin başındaki kararsızlığı (kayıp patlamalarını) önler; NaN alıyorsanız ilk bakılacak yerdir.

### Varsayılan ne, gelenek ne?

Sık karışan bir ayrım: `cosine + warmup` neredeyse her rehberde görünür ama bu bir **topluluk geleneğidir**; kütüphanelerin varsayılanı değil.

| Ayar | HF Trainer / TRL varsayılanı | Yaygın gelenek |
| --- | --- | --- |
| `lr_scheduler_type` | `"linear"` | `"cosine"` |
| Isınma (warmup) | Yok — varsayılan warmup adımı 0 | Adımların ~%3'ü |
| `learning_rate` | Trainer: 5e-5; TRL SFTConfig: 2e-5 | Yönteme göre: LoRA 1e-4–2e-4, tam ince ayar 1e-5–2e-5 |

(2026 itibarıyla transformers ve TRL v1.15 varsayılanları. TRL'in SFTConfig'i birkaç değeri bilinçli olarak farklı tutar: öğrenme oranı 2e-5, gradient checkpointing açık, `logging_steps` 10, fp16 ayarlanmadıysa bf16 açık.)

Bir güncelleme notu (2026 itibarıyla): `warmup_ratio` transformers v5'te kullanımdan çıkarıldı ve v5.2'de tamamen kaldırıldı; güncel sürümlerde artık kabul edilmiyor. Yerini `warmup_steps` aldı ve bu parametre 1'den küçük ondalık değerleri "toplam adımlara oran" olarak yorumluyor: adımların %3'ü için `warmup_steps=0.03` yazmanız yeterli (v5 öncesi kodlardaki `warmup_ratio=0.03` ile aynı etki; eski adı yazmaya devam eden örnekler güncel sürümde hata verir).

Peki cosine + %3 warmup neden bu kadar yaygın? Çünkü iyi çalışıyor: öğrenme oranının sona doğru yumuşakça küçülmesi kayıp eğrisini sakinleştirir, küçük bir ısınma da ilk adımlardaki kararsızlığı (kayıp patlamalarını) önler. Yani gelenek "yanlış" değil, sadece varsayılan değil. Varsayılanları (linear + ısınmasız) olduğu gibi bırakıp denemek de tamamen geçerlidir.

## Epoch: Verinin Üzerinden Kaç Kez Geçilecek?

- **1 – 3 epoch** tipik ve güvenli aralıktır.
- 5+ epoch aynı veride = ezber (overfitting) riski: eğitim kaybı düşmeye devam ederken doğrulama kaybı yükselmeye başlar. Detay: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).
- Veri arttıkça epoch sayısını azaltmak genelde daha iyidir: 20.000 örnekle 1 epoch, 5.000 örnekle 3 epoch'tan çoğu zaman daha iyidir.

### Adım bütçesi ve erken durdurma

Epoch yerine **optimizasyon adımı** cinsinden düşünmek, farklı veri boyutlarını karşılaştırmayı kolaylaştırır:

```text title="Adım bütçesi"
toplam_adım ≈ epoch × örnek_sayısı ÷ etkin_batch

Örnek: 5.000 örnek, etkin batch 8, 2 epoch  →  ~1.250 adım
Aynı ~1.250 adım, 10.000 örnekte 1 epoch'a denk gelir.
```

Erken durdurma: `eval_strategy="steps"` ile doğrulama kaybını izleyin; kayıp düşmeyi bırakıp artmaya başladığında en iyi nokta geçilmiş demektir. Bunu otomatikleştirmek için transformers'ta `EarlyStoppingCallback(early_stopping_patience=2)` kullanın: `metric_for_best_model` ile birlikte, izlenen metrik belirtilen sayıda değerlendirme boyunca kötüleşirse eğitim durur. Aşırı öğrenme (overfitting) belirtileri: eğitim kaybı düşmeye devam ederken **doğrulama kaybının artması** ve model yanıtlarının ezberlenmiş örnekleri andırmaya başlaması.

## Batch Boyutu ve Gradyan Birikimi

- **`per_device_train_batch_size`:** Her GPU'nun tek adımda gördüğü örnek sayısı. VRAM'in baş düşmanı budur; OOM (bellek yetersizliği) alırsanız ilk inecek düğme.
- **`gradient_accumulation_steps`:** Gradyanlar bu sayıda adım boyunca biriktirilir, sonra tek güncelleme yapılır. Batch'i küçültmek zorunda kaldığınızda **etkin batch'i** korumanın yoludur.

**Etkin batch hesabı:**

```text title="Etkin batch boyutu"
etkin_batch = per_device_train_batch_size × gradient_accumulation_steps × GPU_sayısı

Örnek 1:  batch 2, accum 4, 1 GPU  →  etkin batch = 2 × 4 × 1 = 8
Örnek 2:  batch 1, accum 8, 1 GPU  →  etkin batch = 8    (aynı; daha az VRAM, biraz yavaş)
Örnek 3:  batch 2, accum 4, 2 GPU  →  etkin batch = 16   (iki kartla iki katı)
```

Kural: Etkin batch 8-32 aralığında tutmak çoğu ince ayar işi için iyi bir dengedir. Kayıp çok zıplıyorsa (zigzag), ilk çare etkin batch'i büyütmektir.

:::note
Öğrenme oranı, gradyan birikimiyle **otomatik ölçeklenmez.** `gradient_accumulation_steps`'i 4'ten 8'e çıkarmak etkin batch'i büyütür ama LR ve scheduler hesabı aynı kalır. Etkin batch'i belirgin şekilde büyütüyorsanız LR'ı da yeniden gözden geçirin: "etkin batch'i ikiye katlarsan LR'ı da kabaca ikiye katla" yaygın bir başlangıç hipotezidir ama kanun değildir — kısa bir koşuyla doğrulamadan tam ölçekli eğitime geçmeyin.
:::

### Varyans ve tohum: tek koşuya güvenmeyin

Aynı model, aynı veri, aynı ayarlar; yalnızca rastgelelik farklı (tohum, veri sırası). Sonuç aynı olur mu? Hayır — ve bu beklenmelidir. Bu konudaki klasik referans, farklı rastgele tohumların ince ayar sonuçlarını **belirgin biçimde** değiştirebildiğini; ağırlık başlangıcının ve veri sırasının varyansa benzer ölçüde katkı verdiğini gösterir (Dodge vd., arXiv:2002.06305).

Pratik sonuçları:

- İki koşu arasındaki küçük bir farkı "iyileşme" saymayın; kararları **2-3 tohumlu tekrarlarla** verin.
- Önemli bir karşılaştırmada (A ayarı vs B ayarı) ikisini de birkaç kez koşup ortalamaya ve dağılıma bakın.
- Tekrar edilebilirlik için `seed` değerini açıkça ayarlayın (trainer varsayılanı 42'dir); ancak sabit tohumun her şeyi sabitlemediğini unutmayın — çekirdek düzeyindeki paralellik ve kütüphane sürümleri küçük farklar yaratabilir.
- Karşılaştırma ve değerlendirme pratiği için: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).
- Aynı ayrımın üretim tarafı ölçüldü: aynı istem onar kez gönderildiğinde sıcaklık 0 kısa cevapta aynılığı koruyor, 1000+ token'lık uzun üretimde korumuyor. Sayılar ve koşum künyesi [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasında.

## Maksimum Dizi Uzunluğu (max_length)

`max_length` (eski adıyla `max_seq_length`; bazı araçlarda `sequence_len`), her örneğin en fazla kaç jetona kırpılacağını belirler. Uzunluk arttıkça VRAM ve süre **karesel değil ama hızlı** büyür — dikkat çarpanı (attention) uzunlukla karesel büyüdüğü için 2048 jetonluk bir örnek, 1024 jetonluğun yaklaşık iki katından fazla bellek ister.

- Verinizin **%95'ini kaybetmeyecek** en küçük değeri seçin. Sohbet verileri genelde 512-2048 arasındadır.
- Gerçek bağlamı (modelin desteklediği üst sınır) hemen doldurmayın; veriniz kısaysa 4096'yı seçmek sadece para/elektrik yakmaktır.

### Packing (Veri Paketleme)

Kısa örnekleri (ör. 200 jetonluk soru-cevapları) tek bir `max_length` penceresine doldurup birleştirir. Kazanç: GPU boşa beklemez, eğitim belirgin hızlanır.

- **Açık (packing=True):** Kısa örnekli, homojen veri kümelerinde harikadır; hızı ciddi artırır.
- **Kapalı:** Örnek sınırlarının kesin olması gerektiğinde (ör. değerlendirme, hassas maskeleme deneyleri) veya örnekler zaten uzun olduğunda kapatın.

:::note
Packing, kaybın (loss) "örnek başına" değil "jeton başına" yorumlanmasına yol açar; kayıp değerleri packing kapalıyken aldıklarınızla birebir karşılaştırılamaz. Deneyleri aynı ayarla karşılaştırın.
:::

## Diğer Düğmeler

| Düğme | Ne yapar | Tipik değer | Ne zaman değiştirilir? |
| --- | --- | --- | --- |
| `lora r / alpha / dropout` | Adaptörün kapasitesi, ölçeği, düzenlileştirmesi | r=16, alpha=32, dropout=0.05 | Model yeterince değişmiyorsa r'ı 32-64'e çıkarın; veri azsa dropout'u artırın. Detay: [LoRA ve QLoRA](/llm/lora-qlora/) |
| `weight_decay` | Ağırlıkları küçük tutarak ezberi azaltır | 0.0 – 0.1 (genelde 0.01) | Doğrulama kaybı erken artıyorsa (ezber) artırın; LoRA'da 0 da yaygındır |
| `optim` | Optimizasyon algoritması | `adamw_torch`; az VRAM'de `paged_adamw_8bit` | Bellek darsa paged sürüme geçin; QLoRA'da paged sürüm VRAM kazandırır |
| `bf16 / fp16` | Hesaplama hassasiyeti | bf16 tercih edilir | NaN/kayıp patlaması yaşıyorsanız fp16'dan bf16'ya geçin; eski GPU bf16 desteklemiyorsa fp16 + loss scaling |
| `gradient_checkpointing` | Ara aktivasyonları saklamak yerine yeniden hesaplar | TRL SFTConfig'de varsayılan açık; klasik Trainer'da kapalı | OOM alıyorsanız açın; hız öncelikli ve VRAM bolsa kapatın (eğitim belirgin hızlanır) |
| `max_grad_norm` | Gradyan normunu kırpar; patlamaları engeller | 1.0 (varsayılan) | Kayıpta ani sıçramalar sürüyorsa düşürün (ör. 0.3); çok düşük değer öğrenmeyi yavaşlatır |
| `seed` | Rastgeleliğin sabitlenmesi | 42 (varsayılan) | Karşılaştırmalı deneylerde bilinçli olarak birkaç değer deneyin (yukarıdaki varyans bölümüne bakın) |

## Kopyala-Yapıştır Başlangıç Ayarları

Üç hazır set — ihtiyacınıza uygun olanı alın ve kendi değerlerinizle oynayın:

```python title="hazir_ayarlar.py"
# A) QLoRA — 4B/8B model, tek GPU. Çoğu bireysel proje için başlangıç noktası.
qlora_4b_8b = {
    "learning_rate": 2e-4,
    "num_train_epochs": 2,          # 1-3 arası deneyebilirsiniz
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,   # etkin batch = 8
    "lr_scheduler_type": "cosine",
    "warmup_steps": 0.03,           # oran: adımların %3'ü (v5; eskiden warmup_ratio)
    "max_length": 1024,
    "bf16": True,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "packing": True,
}

# B) Tam ince ayar — küçük model (1B-3B), yeterli VRAM varsa (ör. 24 GB+)
tam_ince_ayar = {
    "learning_rate": 2e-5,          # DİKKAT: LoRA değerinin ~10 kat KÜÇÜĞÜ
    "num_train_epochs": 2,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 2,
    "lr_scheduler_type": "cosine",
    "warmup_steps": 0.05,           # oran: adımların %5'i (v5)
    "max_length": 1024,
    "bf16": True,
    "weight_decay": 0.01,
}

# C) DPO — tercih ayarı (SFT'den sonra, isteğe bağlı)
dpo = {
    "learning_rate": 5e-7,          # DİKKAT: SFT'den çok çok küçük
    "num_train_epochs": 1,
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 8,
    "beta": 0.1,
    "warmup_steps": 0.03,           # oran (v5)
    "bf16": True,
}
```

## Belirti → Çözüm Tablosu

Eğitim sırasında bir şeyler ters giderse şu tabloyu kullanın; ayrıntılı hata ayıklama için [Sorun Giderme](/llm/sorun-giderme/) sayfasına geçin.

| Belirti | Olası neden | Önce deneyin |
| --- | --- | --- |
| Kayıp (loss) hiç düşmüyor | lr çok düşük; veri format hatası | lr'ı 2-5 kat artırın; veriyi bir örnek üzerinde gözle kontrol edin (chat template!) |
| Kayıp NaN / inf | lr çok yüksek; fp16 kararsızlığı; bozuk örnek | lr'ı yarıya indirin; bf16'ya geçin; NaN içeren örnekleri temizleyin; warmup ekleyin |
| Kayıp çok oynak (zigzag) | Etkin batch küçük; lr yüksek | `gradient_accumulation_steps` artırın; lr'ı biraz düşürün |
| Doğrulama kaybı erken artıyor (ezber) | Epoch fazla; veri az | Epoch azaltın; `lora_dropout`/`weight_decay` ekleyin; veri artırın |
| Eğitim çok yavaş | Packing kapalı; dizi çok uzun; veri yükleme darboğazı | Packing açın; `max_length` kısaltın; `dataloader_num_workers` artırın |
| Model eğitim sonrası bozuk | Yanlış chat template; epoch fazla; adaptör yüklenmemiş | [Sorun Giderme](/llm/sorun-giderme/) 4. bölüm |

## Hangi Araçta Hangi İsim?

Kavramlar aynı, isimler araçtan araca biraz değişir:

| Kavram | TRL (SFTConfig) | Axolotl (YAML) | Unsloth |
| --- | --- | --- | --- |
| Öğrenme oranı | `learning_rate` | `learning_rate` | `learning_rate` |
| Epoch | `num_train_epochs` | `num_epochs` | `num_train_epochs` |
| Mikro batch | `per_device_train_batch_size` | `micro_batch_size` | `per_device_train_batch_size` |
| Gradyan birikimi | `gradient_accumulation_steps` | `gradient_accumulation_steps` | `gradient_accumulation_steps` |
| Dizi uzunluğu | `max_length` | `sequence_len` | `max_seq_length` |
| LoRA rankı | `r` (LoraConfig) | `lora_r` | `r` (LoraConfig) |

Araç seçimi ve kurulumları için [Araçlar Karşılaştırması](/llm/araclar/) sayfasına bakın.

## Toparlarsak

- Önce **öğrenme oranını** ve veriyi doğru kurun; diğer düğmeler ikincildir.
- Etkin batch = mikro batch × birikim × GPU sayısı; 8-32 aralığını hedefleyin.
- `max_length`'i verinize göre seçin, modelin üst sınırına göre değil.
- Eğriyi izlemek için: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/); hata mesajları için: [Sorun Giderme](/llm/sorun-giderme/).

## Kaynaklar ve İleri Okuma

- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314) — Tablo 9'daki model boyutuna göre öğrenme oranı taraması.
- [LoRA Learns Less and Forgets Less (arXiv:2405.09673)](https://arxiv.org/abs/2405.09673) — LoRA'nın öğrenme oranı duyarlılığı ve hedef alan karşılaştırması.
- [Fine-Tuning Pretrained Language Models: Weight Initializations, Data Orders, and Early Stopping (arXiv:2002.06305)](https://arxiv.org/abs/2002.06305) — tohum (seed) varyansı ve erken durdurma üzerine klasik çalışma.
- [transformers — Trainer ve TrainingArguments](https://huggingface.co/docs/transformers/main_classes/trainer) — varsayılan değerler ve EarlyStoppingCallback.
- [transformers — "Deprecate warmup_ratio" değişikliği](https://github.com/huggingface/transformers/pull/41326) — `warmup_ratio` yerine `warmup_steps` (ondalık = oran) geçişi; kaldırma v5.2'de tamamlandı.
- [TRL — SFTConfig referansı](https://huggingface.co/docs/trl/sft_trainer) — SFT'ye özgü varsayılanlar (`packing`, `gradient_checkpointing`, öğrenme oranı vb.).
