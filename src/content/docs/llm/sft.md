---
title: "Talimat Ayarı (SFT): Modeli Görev Odaklı Eğitmek"
description: "SFT'nin ne yaptığı, veri hazırlığı kuralları, veri bütçesi (LIMA ve s1), kayıp maskesi, unutma ve replay, paketleme ve TRL ile Qwen3-4B üzerinde açıklamalı tam bir eğitim örneği."
dogrulama: 2026-10-15
---

**Talimat ayarı (supervised fine-tuning, SFT)**, ön eğitilmiş bir modeli "soru-cevap" örnekleriyle eğitip görev odaklı hale getirmektir. Ön eğitimden çıkan model dili bilir ama "asistanlık" bilmez; SFT ona soru sorulduğunda nasıl davranacağını öğretir.

Sezgi: [Ön eğitim](/llm/pretraining/) öğrenciye dili öğretti. SFT ise ona "müşteri bir soru sorduğunda nasıl yanıt yazılır", "kod istenince hangi formatta verilir", "özet istenince ne kadar kısa tutulur" gibi **davranışları** öğretir. Yeni bir yetenek inşa etmez; var olan yeteneğe bir kullanım kılavuzu ekler.

## SFT Neyi Değiştirir, Neyi Değiştirmez?

| Değiştirir | Değiştirmez (veya çok az değiştirir) |
| --- | --- |
| Cevap üslubu (resmi/samimi, kısa/uzun) | Modelin temel bilgisi |
| Çıktı formatı (JSON, markdown, madde listesi) | Dil yeteneği (milyarlarca jetonla öğrenilmiş) |
| Görev davranışı (özetle, çevir, sınıflandır) | Genel akıl yürütme kapasitesi |
| İstenmeyen çıktıların baskılanması | Modelin ön eğitimde görmediği bilgiler |

:::caution
SFT, modele **yeni bilgi öğretmenin zayıf bir yoludur**. Modelin hiç görmediği bir gerçeği SFT ile "ezberletebilirsiniz" ama bu güvenilmezdir: model ezberlediği bilgiyi yeni durumlara genelleyemez, hatta yanlış yerlerde tekrarlamaya başlar. Bilgi eksiği varsa doğru araçlar [devam ön eğitimi](/llm/pretraining/) veya dış bilgi kaynağı (RAG) kullanmaktır; "RAG mi ince ayar mı?" kararının tam haritası: [RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/)
:::

SFT hangi durumlarda gerekir?

- Sohbet botu veya asistan modeli üretiyorsanız (neredeyse her zaman gerekir),
- Modelin çıktısı belirli bir formatta olacaksa (ör. JSON, etiket listesi, SQL),
- Alan jargonu ve üslubu önemliyse (ör. hukuk, tıp, e-ticaret),
- Genel model isteğinizi doğru davranışa çevirmiyorsa (ör. hep çok uzun cevap veriyor).

## Veri Hazırlığı

SFT'de başarının büyük kısmı veriden gelir. Model, gördüğü örneklerin **ortalaması** olur: örnekler özensizse model özensiz, örnekler kısa ve net ise model kısa ve net cevap verir.

### Hangi formatlarda veri var?

Yaygın üç format (detaylar için [Veri Formatları](/veri/veri-formatlari/) sayfasına bakın):

**Alpaca tarzı** — basit soru-cevap ikilisi:

```json title="alpaca_ornek.json"
{
  "instruction": "Aşağıdaki cümleyi daha resmi bir dille yeniden yaz: 'Yarın toplantıya gelemeyeceğim.'",
  "input": "",
  "output": "Yarın gerçekleşecek toplantıya katılamayacağımı bildirmek isterim."
}
```

**Sohbet (chat / messages) tarzı** — çok turlu konuşmalar için:

```json title="sohbet_ornek.json"
{
  "messages": [
    { "role": "system", "content": "Sen yardımcı bir Türkçe asistansın." },
    { "role": "user", "content": "İstanbul'da yağmurlu bir günde ne yapılır?" },
    { "role": "assistant", "content": "Müze ve kafe gezmek için harika bir gün..." }
  ]
}
```

**ShareGPT tarzı** — `conversations` alanı içinde insan/gpt rollerinin listesi. Modern eğitim kütüphanelerinin hepsi bu üç formatı okuyabilir; önemli olan **tüm verinin tek biçimde** olmasıdır.

### Veri Kalite Kontrol Listesi

Eğitime başlamadan önce verinize şu 5 soruyu sorun:

1. **Tutarlı mı?** Tüm örnekler aynı alan adlarını ve aynı şemayı mı kullanıyor? Karışık format, eğitim betiğini kırar veya modeli şaşırtır.
2. **Cevaplar doğru mu?** Yanlış bilgi içeren örnekler, modelin yanlış bilgiyi öğrenmesine neden olur. Şüpheli cevapları ya düzeltin ya da silin.
3. **Çeşitli mi?** Aynı kalıbın binlerce kopyası yerine, farklı görevler, farklı uzunluklar ve farklı üsluplar görmelidir. Model "kalıp" değil "beceri" öğrensin.
4. **Tekrar var mı?** Birebir kopya örnekler ezberlemeyi (overfitting) tetikler. Basit bir tekilleştirme (deduplication) büyük fark yaratır.
5. **Sistem istemi uyumlu mu?** Eğitimde kullandığınız sistem istemi (system prompt) ile çıkarımda kullanacağınız aynı olmalı. Eğitimde "Sen Fransızca öğretmenisin" deyip, üretimde hiç sistem istemi vermezseniz, model beklediğiniz gibi davranmaz.

:::tip
1.000 örnekle başlayın, modelin öğrenip öğrenmediğine bakın. Sistem çalışıyorsa veriyi büyütün. Baştan 100.000 örnek toplayıp 6 saat eğitim yapmak yerine, 1.000 örnekle 20 dakikada "hattın çalıştığını" doğrulayın.
:::

## Kayıp Maskesi (Loss Masking): Sadece Asistan Cevaplarından Öğrenmek

Bir sohbet örneği hem kullanıcı sorusunu hem asistan cevabını içerir. Eğitimde kayıp (loss) normalde **tüm** jetonlardan hesaplanır — ama biz modelin "kullanıcı gibi soru yazmayı" öğrenmesini istemeyiz, sadece "asistan gibi cevap yazmayı" öğrensin isteriz.

Bunun çözümü **kayıp maskesi**dir: kullanıcı (ve varsa sistem) jetonlarının etiketleri `-100` yapılır. Kayıp fonksiyonu `-100` etiketli jetonları yok sayar; gradyan yalnızca asistanın cevap jetonlarından akar.

:::note
Bu ayarın kütüphanelerdeki karşılıkları:

- **TRL:** `SFTConfig(assistant_only_loss=True)` — verinin `messages` formatında ve tokenizer'ın bir sohbet şablonu (chat template) olması gerekir.
- **Unsloth:** `train_on_responses_only(...)` ile maske; [Araçlar](/llm/araclar/) sayfasında karşılaştırması var.
- **Axolotl:** `train_on_inputs: false`.
:::

Maskeleme yapılmazsa ne olur? Model kullanıcı sorusunu da üretmeye çalışır; bazen kendi kendine soru uydurup cevaplamaya başlar ("kullanıcı: ... asistan: ..." kalıbını taklit eder). Küçük veriyle bu davranış hızla ortaya çıkar.

### Maske teknik olarak nasıl çıkarılır?

TRL, maske eşleşmesini sohbet verisinden **otomatik** çıkarır; ancak bunun çalışması için tokenizer'ın sohbet şablonunun (chat template), asistan bölümünü `{% generation %}` ve `{% endgeneration %}` etiketleriyle işaretlemesi gerekir (TRL v1.15 dokümanı, 2026). Qwen3 gibi bilinen model ailelerinde TRL şablonu kendisi düzeltir; diğer modellerde şablonu siz kontrol edin. Şablon uygun değilse TRL hata verir — sessizce yanlış maskeleme yapmaz.

Maskenin verinizde doğru çıktığını şöyle test edebilirsiniz:

```python
mesajlar = [
    {"role": "user", "content": "Türkiye'nin başkenti neresi?"},
    {"role": "assistant", "content": "Ankara."},
]
cikti = tokenizer.apply_chat_template(
    mesajlar,
    tokenize=True,
    return_dict=True,
    return_assistant_tokens_mask=True,  # asistan jetonları 1, diğerleri 0
)
print(sum(cikti["assistant_masks"]), "asistan jetonu /",
      len(cikti["assistant_masks"]), "toplam jeton")
```

Rakam mantıklıysa (küçük bir asistan cevabı için maske toplamı sıfırdan büyük ve toplamdan küçük) maskeleme beklendiği gibi çalışıyor demektir. Maske tümüyle 0 gelirse (bazı şablonlarda görülen bir durum) tokenizer'ınız asistan bölümünü işaretlemiyor demektir; eğitim şablonunu değiştirmeniz ya da maskeyi elle kurmanız gerekir.

:::note
İki benzer parametreyi karıştırmayın: `assistant_only_loss` **sohbet (conversational)** verisi içindir ve maske şablondan çıkarılır. `completion_only_loss` ise **prompt-completion** verisi içindir; bu formatta TRL zaten varsayılan olarak yalnızca "completion" kısmından kayıp hesaplar ve `completion_only_loss=False` ile tüm dizinden hesaplamaya zorlayabilirsiniz. Yani ikisi farklı veri formatlarına bakan kardeş parametrelerdir (TRL v1.15 dokümanı) — biri diğerinin eski adı değildir.
:::

## Tam Örnek: TRL ile Qwen3-4B Talimat Ayarı

Aşağıdaki örnek, Unsloth gibi kolaylaştırıcılar kullanmadan, doğrudan Hugging Face araçlarıyla (transformers + peft + trl) klasik bir SFT akışı gösterir. 4B model tercih edildi çünkü tek tüketici GPU'da rahatça dener:

- 4-bit yükleme (QLoRA) ile ~5-6 GB VRAM civarında çalışır,
- LoRA sayesinde eğitilebilir parametre oranı %1 civarındadır.

```python title="sft_egitimi.py"
# Talimat ayarı (SFT) — TRL SFTTrainer ile sade, açıklamalı örnek
# Kurulum:
#   pip install "trl" "peft" "datasets" "transformers" "accelerate" "bitsandbytes"

import torch
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

MODEL_ADI = "Qwen/Qwen3-4B"  # 4 milyar parametreli, Türkçe'de de iyi çalışan küçük bir model

# ---------------------------------------------------------------------------
# 1) Veri: hedefimiz "messages" alanlı sohbet formatıdır.
#    (Türkçe talimat veri setleri için /veri/veri-nereden-bulunur/ sayfasına bakın.)
#    Aşağıdaki örnekte elimizde alpaca tarzı bir veri olduğunu varsayıp
#    sohbet formatına çeviriyoruz. Kullanırken veri setinizin alan adlarını
#    sayfasındaki "Data Studio" bölümünden kontrol edin.
# ---------------------------------------------------------------------------

veri = load_dataset("atasoglu/instruction-turkish", split="train")
veri = veri.select(range(min(5000, len(veri))))  # küçük başlayın: 5.000 örnek

SISTEM_ISTEMI = "Sen yardımcı, dürüst ve nazik bir Türkçe asistansın."

def sohbete_cevir(ornek):
    kullanici = ornek.get("instruction", "") or ornek.get("prompt", "")
    cevap = ornek.get("output", "") or ornek.get("response", "")
    return {
        "messages": [
            {"role": "system", "content": SISTEM_ISTEMI},
            {"role": "user", "content": kullanici},
            {"role": "assistant", "content": cevap},
        ]
    }

veri = veri.map(sohbete_cevir)
bolme = veri.train_test_split(test_size=0.05, seed=42)  # %5 doğrulama için ayrılır

# ---------------------------------------------------------------------------
# 2) LoRA yapılandırması: tüm ağırlıklar yerine küçük "adaptör" matrisleri
#    eğitilir. (Detaylar: /llm/lora-qlora/)
# ---------------------------------------------------------------------------

lora_ayari = LoraConfig(
    r=16,                          # adaptörün kapasitesi
    lora_alpha=32,                 # genelde r'nin 2 katı
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],  # dikkat + MLP katmanları
    bias="none",
    task_type="CAUSAL_LM",
)

# ---------------------------------------------------------------------------
# 3) Eğitim ayarları: her düğmenin anlamı için /llm/hiperparametreler/
# ---------------------------------------------------------------------------

egitim_ayari = SFTConfig(
    output_dir="./qwen3-4b-turkce-sft",
    num_train_epochs=1,               # 1-3 epoch tipik; fazlası ezber riski
    per_device_train_batch_size=2,    # VRAM'e göre 1-4 arasında tutun
    gradient_accumulation_steps=4,    # etkin batch = 2 x 4 = 8 örnek
    learning_rate=2e-4,               # LoRA için tipik öğrenme oranı
    lr_scheduler_type="cosine",
    warmup_steps=0.03,                # oran: adımların %3'ü (v5; eskiden warmup_ratio)
    max_length=1024,                  # örnek başına en fazla jeton sayısı
    bf16=torch.cuda.is_bf16_supported(),  # eski GPU'da False döner (fp16 kullanın)
    logging_steps=10,
    save_strategy="epoch",
    eval_strategy="steps",
    eval_steps=50,                    # her 50 adımda doğrulama kaybını ölç
    report_to="none",                 # wandb/tensorboard istemiyorsanız
    assistant_only_loss=True,         # yalnızca asistan cevabından öğren (maskeleme)
)

# ---------------------------------------------------------------------------
# 4) Eğiticiyi oluştur ve eğit
# ---------------------------------------------------------------------------

egitici = SFTTrainer(
    model=MODEL_ADI,
    args=egitim_ayari,
    train_dataset=bolme["train"],
    eval_dataset=bolme["test"],
    peft_config=lora_ayari,           # LoRA burada devreye girer
)
egitici.train()

# ---------------------------------------------------------------------------
# 5) Kaydet: yalnızca adaptör kaydedilir, birkaç MB tutar!
# ---------------------------------------------------------------------------

egitici.save_model("./qwen3-4b-turkce-sft/adaptor")
egitici.push_to_hub("KULLANICI-ADINIZ/qwen3-4b-turkce-sft")  # isteğe bağlı
```

:::tip
Bu betiği çalıştırmadan önce VRAM planınızı [VRAM Hesaplama](/donanim/vram-hesabi/) sayfasından yapın. 4-bit yükleme kapalıysa 4B model fp16'da ~8 GB VRAM ister; 4-bit mod ve LoRA ile 5-6 GB'a inebilir.
:::

## Ne Kadar Veri, Kaç Epoch?

| Veri miktarı | Ne beklersiniz? |
| --- | --- |
| 500 – 1.000 örnek | Zayıf başlangıç. Hattın çalıştığını doğrulamak için yeterli; üretim için değil. |
| 5.000 – 20.000 örnek | Dar bir görev (ör. belirli bir üslupta sınıflandırma) için ciddi başlangıç. |
| 50.000+ örnek | Geniş davranış değişimi, çok görevli asistan. |

Epoch (verinin üzerinden geçiş sayısı) için:

- **1–3 epoch** tipik ve güvenli aralıktır.
- Aynı veride **5+ epoch** ezber riski demektir: eğitim kaybı düşer ama model veriyi "anlamak" yerine "hatırlamaya" başlar; yeni sorularda tuhaf cevaplar üretir.
- Erken durdurma için eğitim verisinin bir kısmını (%5-10) **doğrulama (validation)** olarak ayırın ve doğrulama kaybını izleyin. Doğrulama kaybı düşmeyi bırakıp artmaya başladığında durun. Detaylar: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).

:::caution
Eğitim kaybının düşmesi her zaman iyi haber değildir. Veriyi ikiye bölüp doğrulama kaybını izlemiyorsanız, elinizde "ezberlemiş" bir model olup olmadığını göremezsiniz. Az veri + çok epoch, en klasik tuzaktır.
:::

## Az Veri Yeter mi? LIMA ve s1'in Gösterdikleri

"Kalite, miktardan önce gelir" cümlesi kulağa slogan gibi geliyor ama arkasında deneysel dayanaklar var. En çok konuşulan iki çalışma:

- **LIMA (arXiv:2305.11206):** Yalnızca **1.000 özenle seçilmiş istem-yanıt çiftiyle**, RLHF gibi herhangi bir tercih eğitimi kullanılmadan eğitilen LIMA'nın yanıtları, insan tercihi karşılaştırmalarında **%43 oranında GPT-4 ile eşdeğer ya da ondan üstün** bulundu.
- **s1 (arXiv:2501.19393):** `s1K` adı verilen **1.000 soru ve çözüm izi**, üç ölçütle küratörlendi: zorluk, çeşitlilik ve kalite. Eğitimin yanına bir de test-zamanı ölçekleme kondu: düşünme sürecini zorla sonlandıran ya da "Wait" ekleyerek uzatan "bütçe zorlama" (budget forcing). s1-32B, yarışma matematiğinde (MATH ve AIME24) o1-preview'ı %27'ye kadar geçti.

| Çalışma | Veri büyüklüğü | Gösterdiği |
| --- | --- | --- |
| LIMA (arXiv:2305.11206) | 1.000 özenli örnek | RLHF'siz eğitimle tercih karşılaştırmalarında GPT-4'e yakın sonuç |
| s1 (arXiv:2501.19393) | 1.000 soru + çözüm izi | Az veri + test-zamanı ölçekleme ile güçlü matematik performansı |

:::caution
Bu sonuçları fazla genelleştirmeyin. İkisi de tek bir eğitim tarifi ve dar sayılabilecek değerlendirme setleri üzerinde yapılmış kontrollü deneylerdir; "1.000 örnek her projeye yeter" anlamına gelmez. Bugünün güçlü açık asistanları, tek seferlik küçük bir setle değil, çok aşamalı ve geniş açık veri karışımlarıyla eğitiliyor (ör. TÜLU 3, arXiv:2411.15124). "Kalite > miktar" önermesi doğrudur; ama kalitenin ölçütü soyut bir "iyi" değil, şu üç somut şeydir:

1. **Tutarlılık:** Örnekler aynı şemayı ve aynı üslup normlarını mı kullanıyor?
2. **Çeşitlilik:** Farklı görevler, farklı uzunluklar ve farklı zorluk seviyeleri kapsanıyor mu? (s1'de zorluk bilinçli bir küratörlük ölçütüydü.)
3. **Format doğruluğu:** Çıktılar, üretimde beklediğiniz formatla birebir uyumlu mu?
:::

:::tip
Pratik başlangıç: ilk eğitimi **1.000-5.000 örnekle** yapın. Doğrulama setindeki davranış iyileşiyorsa veriyi kademeli büyütün; iyileşmiyorsa önce mevcut örneklerin tutarlılığını ve formatını düzeltin — yeni veri toplamak, bozuk veriyi çoğaltmaktan iyidir.
:::

## Unutma, Replay ve "Uyum Vergisi"

SFT'de gözden kaçan bir risk **unutmadır (catastrophic forgetting)**: model yeni görev verisinde uzmanlaşırken ön eğitimden getirdiği genel yeteneklerin bir kısmını yitirir. Belirtiler tipiktir: dar görevinizde başarı artar ama model alakasız sorularda eskisinden kötü yanıtlar vermeye başlar.

İki pratik refleks:

- **Replay (veri karıştırma):** Eğitim verinize, görev verinizin yanında **%5-10 oranında genel talimat verisi** karıştırın. Amaç, modele genel davranışını hatırlatan bir "can suyu" vermektir. Kesin bir kanun değil, toplulukta yaygın bir pratiktir; en doğru karışım oranını kendi doğrulama setinizle ölçün.
- **Uyum vergisi ölçümü (alignment tax):** Eğitimden **önce ve sonra** küçük bir genel yetenek testi çalıştırın (ör. 20-50 soruluk kısa bir bilgi/akıl yürütme kontrol listesi). Görev puanındaki artışı, genel puandaki düşüşle birlikte okuyun. Genel puan belirgin düşüyorsa replay oranını artırın veya öğrenme oranını düşürün.

:::note
Unutma riski yalnızca SFT yapıp yapmamanıza değil, **hangi yöntemle** yaptığınıza da bağlı. "LoRA Learns Less and Forgets Less" çalışması, düşük ranklı LoRA eğitiminin hedef alan dışındaki yetenekleri tam ince ayardan daha iyi koruduğunu gösteriyor (arXiv:2405.09673) — karşılaştırma için [LoRA ve QLoRA](/llm/lora-qlora/) sayfasına bakın.
:::

## Paketleme (Packing): Kısa Örneklerde GPU'yu Doldurmak

Sohbet verileri çoğu zaman kısadır (birkaç yüz jeton). `max_length=1024` ile çalışıyorsanız her örnek, pencerenin yalnızca küçük bir kısmını doldurur ve GPU'nun hesap gücü boşa akar. **Paketleme**, birden çok kısa örneği aynı sabit uzunluklu bloğa yerleştirir; eğitim belirgin biçimde hızlanır.

TRL'de tek satırlık açılışı:

```python
egitim_ayari = SFTConfig(packing=True, packing_strategy="bfd", ...)
```

- `packing=True` paketlemeyi açar; blok uzunluğu `max_length` olur.
- `packing_strategy="bfd"` **en uygun azalan (best-fit decreasing)** stratejisidir ve TRL'deki varsayılandır: uzun örnekler önce yerleştirilir, artan jetonlar kırpılır. Alternatifler: `"bfd_split"` (taşan örneği böler) ve `"wrapped"` (örneği ortasından kesebilen agresif sarma) (TRL v1.x dokümanı).
- Paketlemenin en hızlı yolu (padding-free) FlashAttention 2 veya 3 gerektirir; kurulumunuza göre kontrol edin.

Riskler ve dikkat edilecekler:

- **Örnek sınırları:** Dikkat (attention) katmanı paketlenen örneklerin sınırlarını düzgün ayırmazsa, model bitişik örneği aynı bağlamın devamı sanabilir; cevapların `EOS` yerine bir sonraki örneğin içeriğiyle devam etmesi gibi garipleşmeler görülebilir. Modern TRL sürümleri sınırları ayrı tutar; yine de paketlemeyi açtıktan sonra çıktıları gözle kontrol edin.
- **Kayıp karşılaştırması:** Paketlemede kayıp "jeton başına" hesaplandığı için değerler, paketlemesiz koşularla birebir karşılaştırılamaz; deneyleri aynı ayarla kıyaslayın (bu not [Hiperparametreler](/llm/hiperparametreler/) sayfasında da var).
- **Uzun örnekler:** Verinizin çoğu zaten `max_length`'e yakınsa paketlemenin kazancı azalır.

## SFT Sonrası Ne Ölçülür?

Eğitim bittiğinde üç soruya yanıtınız olmalı:

1. **Öğrendi mi?** Görev tanımınıza uygun 30-100 soruluk bir "görev testi" hazırlayın; eğitim öncesi ve sonrası yanıtları yan yana koyun. Ölçülebilir bir görev seçtiyseniz (sınıflandırma, format uyumu) sonucu sayıya dökün.
2. **Metrikler ne diyor?** Kayıp eğrileri, jeton doğruluğu ve dikkat edilecek sinyaller için [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).
3. **Genel yetenekler yerinde mi?** Unutma kontrolü için kısa bir genel test; daha kapsamlı karşılaştırma için [Benchmarklar](/degerlendirme/benchmarklar/).

## Toparlarsak

- SFT, davranış öğretir; bilgi öğretmez. Format, üslup ve görev davranışı burada kazanılır.
- Veri kalitesi veri miktarından önce gelir: tutarlı, doğru, çeşitli ve tekrarsız örnekler toplayın.
- Kayıp maskesi (`assistant_only_loss=True`) ile yalnızca asistan cevaplarından öğrenin.
- 1-3 epoch, düşük-orta öğrenme oranı ve doğrulama takibi ile ezberden kaçının.

Sıradaki adımlar:

- Daha büyük model veya daha az VRAM için [LoRA ve QLoRA](/llm/lora-qlora/) ile bu akışı birleştirin.
- Eğitimin gerçekten işe yaradığını [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfasıyla ölçün.
- Uçtan uca komut akışı için [Adım Adım Eğitim](/llm/adim-adim-egitim/) rehberini izleyin.

## Kaynaklar ve İleri Okuma

- [LIMA: Less Is More for Alignment (arXiv:2305.11206)](https://arxiv.org/abs/2305.11206) — 1.000 özenle seçilmiş örnekle, RLHF olmadan güçlü talimat takibi sonuçları.
- [s1: Simple test-time scaling (arXiv:2501.19393)](https://arxiv.org/abs/2501.19393) — 1.000 örnek + "bütçe zorlama" ile test-zamanı ölçekleme.
- [TÜLU 3: Pushing Frontiers in Open Language Model Post-Training (arXiv:2411.15124)](https://arxiv.org/abs/2411.15124) — açık, çok aşamalı post-training tarifleri.
- [TRL — SFT Trainer dokümanı](https://huggingface.co/docs/trl/sft_trainer) — `assistant_only_loss`, `completion_only_loss`, `packing` ve `packing_strategy` parametrelerinin güncel tanımları.
- [LoRA Learns Less and Forgets Less (arXiv:2405.09673)](https://arxiv.org/abs/2405.09673) — unutma ve hedef alan dışı performans üzerine deneysel karşılaştırma.
- [transformers — Chat templating](https://huggingface.co/docs/transformers/chat_templating) — sohbet şablonları ve asistan maskesi (`return_assistant_tokens_mask`).
