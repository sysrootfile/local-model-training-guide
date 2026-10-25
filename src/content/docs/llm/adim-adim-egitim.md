---
title: "Adım Adım: İlk Modelini Eğit (Uçtan Uca)"
description: Veriden başlayıp eğitilmiş ve çalışan bir Türkçe asistana ulaşana kadar tek sayfada, tam kodlu uçtan uca rehber.
dogrulama: 2026-10-15
---

Bu sayfa rehberin kalbi: **sıfırdan başlayıp eğitilmiş, test edilmiş ve çalışan bir modele** ulaşacağız. Adımların tamamı gerçek komutlar ve gerçek kod içeriyor.

**Senaryomuz:** Türkçe bir müşteri destek asistanı eğitmek istiyoruz.

| Karar | Seçimimiz | Neden? |
| --- | --- | --- |
| Model | Qwen3-4B | 2026 itibarıyla 4B sınıfının en güçlü açık modellerinden; Türkçesi iyi |
| Yöntem | QLoRA | Az VRAM'le, hızlı ve güvenli başlangıç ([neden?](/llm/lora-qlora/)) |
| Araç | Unsloth | Tek GPU'da hızlı ve kod içinde çok basit ([araç karşılaştırması](/llm/araclar/)) |
| Veri | 500-5.000 Türkçe talimat örneği | Kalite, miktardan önemli ([veri türleri](/veri/veri-turleri/)) |

:::note[Ön koşul]
Bu rehber, kurulu bir Python ortamı varsayar. Ortamın yoksa önce [Yerel Kurulum](/donanim/yerel-kurulum/) sayfasını tamamla ya da hiçbir şey kurmadan [bulutta ücretsiz bir GPU](/donanim/bulut-secenekleri/) ile devam et.
:::

## Yolculuk Haritası

```text
1. Veriyi hazırla        (30-60 dk)  → JSONL, sohbet formatında
2. Ortamı kur            (10-15 dk)  → Python + Unsloth
3. Modeli yükle          (5 dk)      → Qwen3-4B, 4-bit
4. LoRA adaptörünü ekle  (2 dk)      → Eğitilebilir küçük katmanlar
5. Eğitimi başlat        (30 dk-2 sa)→ trainer.train()
6. Test et               (5 dk)      → Hızlı çıkarım
7. Kaydet / birleştir    (5-10 dk)   → Adaptör veya birleşik model
8. Çalıştır              (10 dk)     → GGUF → Ollama
9. Değerlendir           (30 dk)     → Mini test seti, kör karşılaştırma
```

## Adım 1: Veriyi Hazırla

Eğitimin başarısı büyük ölçüde bu adıma bağlıdır. İki seçeneğin var:

**Seçenek A — Hazır Türkçe veri seti kullan:** [Veri Nereden Bulunur](/veri/veri-nereden-bulunur/) sayfasındaki Türkçe setlerden birini indir (ör. `atasoglu/turkish-instruction-datasets` koleksiyonundan bir set ya da `ogulcanaydogan/Turkish-LLM` eğitim verisi).

**Seçenek B — Kendi verinden oluştur:** Elindeki destek kayıtlarından/SSS'lerden 500-5.000 örnek çıkar. Format ve kalite için: [Veri Formatları](/veri/veri-formatlari/) ve [Kendi Verini Oluştur](/veri/kendi-verini-olustur/).

Verin şu sohbet (chat) formatında olmalı — her satır bir JSON:

```json title="veri.jsonl"
{"messages": [{"role": "system", "content": "Sen bir müşteri destek asistanısın."}, {"role": "user", "content": "Kargom ne zaman gelir?"}, {"role": "assistant", "content": "Kargo takip numaranızla ..."}]}
{"messages": [{"role": "user", "content": "İade süresi kaç gün?"}, {"role": "assistant", "content": "İade süresi 14 gündür..."}]}
```

Veriyi yükleyip eğitim/doğrulama olarak ikiye ayıran kısa kod:

```python title="veri_hazirla.py"
from datasets import load_dataset

# Kendi JSONL dosyandan yükle (Seçenek B)
ds = load_dataset("json", data_files="veri.jsonl", split="train")

# Hazır bir veri seti indirmek istersen (Seçenek A) — alan adlarını mutlaka kontrol et:
# ds = load_dataset("kullanici/veri-seti-adi", split="train")
# print(ds.column_names)

# %5'ini doğrulama (validation) için ayır
bolme = ds.train_test_split(test_size=0.05, seed=42)
egitim_verisi = bolme["train"]
dogrulama_verisi = bolme["test"]

print(f"Eğitim örneği: {len(egitim_verisi)} | Doğrulama: {len(dogrulama_verisi)}")
print(egitim_verisi[0])  # İlk örneği gözle kontrol et — şart!
```

:::caution
Her veri setinin alan adları farklıdır (`instruction/input/output` ya da `prompt/completion` gibi). Yüklemeden sonra `ds.column_names` ile kontrol et ve [Veri Formatları](/veri/veri-formatlari/) sayfasındaki dönüştürme örneklerine bakarak kendi `messages` yapına çevir.
:::

## Adım 2: Ortamı Kur

```bash title="kurulum.sh"
pip install unsloth
# Ortam zaten PyTorch içeriyorsa yukarıdaki komut yeterli.
# Colab/Kaggle'da bu komut tek başına çalışır; yerelde CUDA uyumu için
# https://docs.unsloth.ai adresindeki güncel kurulum notlarına bak.
```

:::tip
Google Colab veya Kaggle kullanıyorsan GPU'yu seçmeyi unutma: Colab'da **Runtime → Change runtime type → GPU**, Kaggle'da **Settings → Accelerator → GPU T4 x2**.
:::

## Adım 3: Modeli Yükle

Modeli 4-bit olarak yüklüyoruz — VRAM kullanımı böylece birkaç kat düşer.

```python title="egitim.py (1/4)"
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3-4B-bnb-4bit",  # 4-bit'e hazırlanmış sürüm
    max_seq_length=2048,                      # Bağlam penceresi: verine göre ayarla
    load_in_4bit=True,
    dtype=None,                               # Otomatik: Ampere+ için bf16
)
```

:::note
`unsloth/Qwen3-4B-bnb-4bit` gibi hazır 4-bit depoları Hugging Face'te arayarak bulabilirsin. Farklı bir model (Gemma 3, Llama 3.2) denemek istersen yalnızca `model_name` değişir — akış aynıdır. Model seçimi için: [Yol Haritası](/baslangic/yol-haritasi/).
:::

:::note[Unsloth sürüm notu]
Yeni Unsloth sürümlerinde `FastLanguageModel` yerine, görsel modelleri de kapsayan üst kümesi `FastModel` adını görebilirsin. Dil modelleri için ikisi de aynı işi yapar; sürüme uygun olanı kullan.
:::

## Adım 4: LoRA Adaptörünü Ekle

Taban modelin ağırlıkları donar; yalnızca küçük "adaptör" katmanları eğitilir. Parametre seçimlerinin mantığı: [LoRA ve QLoRA](/llm/lora-qlora/).

```python title="egitim.py (2/4)"
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                 # Rank: 8 daha hafif, 32 daha kapasiteli
    lora_alpha=32,        # Genelde r x 2
    lora_dropout=0.0,     # 0 hızlı ve genelde yeterli
    target_modules=[      # Tüm dikkat + MLP katmanlarına uygula
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_gradient_checkpointing="unsloth",  # VRAM tasarrufu
    random_state=42,
)
```

## Adım 5: Veriyi Sohbet Şablonuna Çevir ve Eğitimi Başlat

Model, veriyi kendi **sohbet şablonuyla** (chat template) görmeli. Bu dönüşümü tokenizer'a yaptırıyoruz:

```python title="egitim.py (3/4)"
from trl import SFTTrainer, SFTConfig

def sohbete_cevir(ornek):
    metin = tokenizer.apply_chat_template(
        ornek["messages"], tokenize=False, add_generation_prompt=False
    )
    return {"text": metin}

egitim_verisi = egitim_verisi.map(sohbete_cevir)
dogrulama_verisi = dogrulama_verisi.map(sohbete_cevir)

egitici = SFTTrainer(
    model=model,
    processing_class=tokenizer,      # TRL v1: tokenizer parametresinin yeni adı
    train_dataset=egitim_verisi,
    eval_dataset=dogrulama_verisi,
    args=SFTConfig(
        dataset_text_field="text",
        max_length=2048,                 # TRL v1: max_length (eski adı max_seq_length)
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,   # Etkin batch = 2 x 4 = 8
        warmup_steps=10,
        num_train_epochs=2,
        learning_rate=2e-4,              # LoRA için tipik değer
        lr_scheduler_type="cosine",
        optim="adamw_8bit",
        weight_decay=0.01,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_steps=100,
        output_dir="cikti",
        seed=42,
    ),
)

egitici.train()
```

:::note[TRL v1'de alan adları değişti]
İki ad TRL v1.x'te yenilendi (TRL v1.15 dokümanı, 2026): `SFTConfig` alanı artık `max_length` (eski sürümlerdeki `max_seq_length` yerine) ve `SFTTrainer` parametresi artık `processing_class` (eski adı `tokenizer`; eski adı kullanmak yeni sürümlerde hata verir). Unsloth'un kendi `FastLanguageModel.from_pretrained(max_seq_length=...)` parametresi ise aynı adla kullanılmaya devam eder — ikisi farklı kütüphanelerin parametreleridir, karıştırma.
:::

:::tip
Hiperparametrelerin ne anlama geldiğini ve duruma göre nasıl değiştirileceğini [Hiperparametreler](/llm/hiperparametreler/) sayfasında bulabilirsin. İlk denemende yukarıdaki değerlerle başla, sonuçları gördükçe oyna.
:::

Eğitim sırasında konsolda buna benzer bir akış görürsün:

```text title="örnek eğitim çıktısı (değerler temsilîdir)"
Adım 10/250   | Loss: 2.41
Adım 50/250   | Loss: 1.87
Adım 100/250  | Loss: 1.52   | Doğrulama loss: 1.61
Adım 200/250  | Loss: 1.21   | Doğrulama loss: 1.44
```

Kayıp (loss) düzenli düşüyorsa işler yolunda demektir. Eğrileri nasıl okuyacağın: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).

## Adım 6: Test Et

Eğitimden sonra ilk iş modeli kendi elinle denemek:

```python title="egitim.py (4/4)"
from unsloth import FastLanguageModel

FastLanguageModel.for_inference(model)  # Çıkarım moduna geç (hızlanır)

mesajlar = [
    {"role": "system", "content": "Sen bir müşteri destek asistanısın."},
    {"role": "user", "content": "Siparişim hâlâ elime ulaşmadı, ne yapmalıyım?"},
]
girdi = tokenizer.apply_chat_template(
    mesajlar, tokenize=False, add_generation_prompt=True
)
girdi = tokenizer(girdi, return_tensors="pt").to("cuda")

cikti = model.generate(**girdi, max_new_tokens=256, temperature=0.7, do_sample=True)
cevap = tokenizer.decode(cikti[0][girdi["input_ids"].shape[1]:], skip_special_tokens=True)
print(cevap)
```

:::caution[En klasik tuzak]
Test ederken **eğitimde kullandığın sohbet şablonunun aynısını** kullanmalısın (`apply_chat_template`). Elle `"Kullanıcı: ... Asistan:"` gibi metin kurarsan model saçmalayabilir; bu, modelin kötü olduğu anlamına gelmez. Detay: [Sorun Giderme](/llm/sorun-giderme/).
:::

## Adım 7: Kaydet

```python title="kaydet.py"
# Yalnızca adaptörü kaydet (birkaç MB — önerilen)
model.save_pretrained("lora_adaptor")
tokenizer.save_pretrained("lora_adaptor")

# Birleştirilmiş tam modeli kaydet (dağıtım/GGUF için gerekli — yaklaşık 8-10 GB, 4B model için)
# model.save_pretrained_merged("birlestirilmis_model", tokenizer, save_method="merged_16bit")
```

Adaptör ve birleştirme arasındaki fark: [LoRA Birleştirme](/kullanim/lora-birlestirme/).

## Adım 8: Kendi Modelini Çalıştır

En pratik yol: modeli GGUF formatına çevirip Ollama ile çalıştırmak.

```python title="gguf_export.py"
# Unsloth ile doğrudan GGUF dışa aktarma (yaklaşık 2-5 GB)
model.save_pretrained_gguf("model-gguf", tokenizer, quantization_method="q4_k_m")
```

Ardından `model-gguf` klasöründeki GGUF dosyasını Ollama'ya tanıt. Adım adım: [Ollama Rehberi](/kullanim/ollama/). Alternatif: [vLLM ile API sunumu](/kullanim/sunma-api/).

## Adım 9: Değerlendir

Eğitim bitti diye iş bitmez. 20-50 soruluk kendi mini test setini hazırlayıp modeli düzenli olarak yokla; hangi sorularda iyi, hangilerinde kötü olduğunu not et. Protokol: [Benchmark'lar ve Gerçek Değerlendirme](/degerlendirme/benchmarklar/).

### Eğitim Sonrası Kontrol Listesi

İlk eğitimin bittiğinde şu listeyi baştan sona geç — hepsi birkaç dakikalık iş, ama en pahalı hatalar burada yakalanır:

- [ ] Adaptör (veya birleşik model) doğru klasörden yüklendi; kaydettiğin dizini gösteriyor
- [ ] Testte eğitimdeki sohbet şablonunun **aynısı** kullanıldı (`apply_chat_template`)
- [ ] Sistem istemi eğitimdekiyle birebir aynı
- [ ] 20-50 soruluk mini test seti hazırlandı ve hem **eğitim öncesi** hem **sonrası** modelle koşuldu
- [ ] Karşılaştırma "kör" yapıldı: hangi cevabın hangi modelden geldiğini bilmeden tercih işaretlendi
- [ ] Regresyon kontrolü: test seti dışında birkaç genel soruya model hâlâ makul yanıt veriyor
- [ ] Eğitim kaybı ile doğrulama kaybı birlikte okundu (ezber sinyali var mı?) — [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/)
- [ ] Sonuçlar küçük bir not dosyasına yazıldı: hangi ayarla, hangi puan, hangi gözlem

## En Sinsi Tuzak: Model Çalışıyor Ama GGUF/Ollama'da Bozuk Konuşuyor

**Belirti:** Python'da test ettiğinde model düzgün cevap veriyor; GGUF'a çevirip Ollama'da çalıştırdığında ise soruyu yankılıyor ("Kargom ne zaman gelir? Kargom ne zaman gelir?"), kendi kendine yazmaya devam ediyor ya da eğitilmemiş base model gibi cümleyi sürdürüyor.

**Neden:** Suçlu neredeyse her zaman aynıdır: **sohbet şablonu taşınmamıştır**. Model eğitimde "system / user / assistant" işaretlerini görmüştür; çalıştırma tarafı hangi şablonu uygulayacağını bilmiyorsa farklı bir varsayılan kullanır. Yanlış işaretlerle beslenen model, eğitimde gördüğü kalıbı tanıyamaz ve davranışı base modele döner. Model bozuk değildir — yanlış biçimde paketlenmiştir.

**Çözüm iki yoldan biridir:**

1. **Şablonu dışa aktarımda taşı:** Unsloth ile `save_pretrained_gguf` kullandığında Unsloth, Ollama'nın istediği `Modelfile`'ı otomatik oluşturur ve bu dosya **eğitimde kullanılan sohbet şablonunu içerir** (Unsloth dokümantasyonu, 2026). GGUF dosyaları şablonu `tokenizer.chat_template` metadata alanında taşıyabilir; dönüştürmeyi başka araçlarla yapıyorsan bu alanın dosyaya girdiğini kontrol et.
2. **Modelfile'da elle tanımla:** Şablon eksikse Ollama Modelfile'ında `TEMPLATE` ile sohbet şablonunu, durma dizilerini de `PARAMETER stop` ile tanımla (Ollama modelfile dokümanı; sitedeki [Ollama Rehberi](/kullanim/ollama/) bu yapıyı örnekliyor):

```dockerfile title="Modelfile (iskelet)"
FROM ./model-q4_k_m.gguf

# Şablonu, eğitimde kullandığın tokenizer şablonuyla birebir aynı şekilde doldur
TEMPLATE """{{ .System }}...{{ .Prompt }}"""

# Durma dizileri (ör. Qwen3 için <|im_end|>)
PARAMETER stop "<|im_end|>"
```

:::caution[Şablonu asla "yaklaşık" yazma]
Yukarıdaki `TEMPLATE` bir **iskelettir** — gerçek değeri uydurma. Şablonu tokenizer'ından al (ör. `tokenizer.chat_template` içeriği) ve eğitimde kullandığın şablonla **birebir aynı** olduğundan emin ol. Unsloth dokümantasyonu da özellikle şunu vurgular: ince ayarda kullanılan şablonla çalıştırma tarafındaki şablon aynı olmalıdır; şablon uyuşmazlığı, sağlam bir modeli "bozuk" gösteren en yaygın nedendir.
:::

Eğitimde kullanılan sohbet formatının ayrıntıları için: [Veri Formatları](/veri/veri-formatlari/).

## Sonraki Adımlar

Modelin çalışıyor — şimdi ne yapabilirsin?

- **Daha iyi sonuç:** Veri kalitesini artır ([Veri Temizleme](/veri/veri-temizleme/)), örnek sayısını çoğalt, [Hiperparametreler](/llm/hiperparametreler/) ile oyna.
- **Devam eğitimi:** Yeni verilerle aynı adaptöre ekleme yap.
- **Üslup/tercih:** [DPO](/llm/dpo-rlhf/) ile davranışı ince ayarla.
- **Paylaş:** [Hugging Face'e yükle](/kullanim/huggingface-paylasim/), topluluk seni bulsun.

## Sık Yapılan Hatalar (Hızlı Bakış)

| Belirti | Muhtemel neden | Çözüm |
| --- | --- | --- |
| `CUDA out of memory` | Batch/dizi boyutu fazla | [Sorun Giderme: OOM merdiveni](/llm/sorun-giderme/) |
| Loss düşmüyor | Format/şablon hatası, lr çok düşük | Verinin `text` alanını gözle kontrol et |
| Cevaplar saçma | Testte şablon uyuşmazlığı | `apply_chat_template` kullan |
| Eğitim çok yavaş | Model GPU'ya tam yüklenmemiş | `nvidia-smi` ile kontrol et |
| Ollama'da model yankılıyor / base model gibi konuşuyor | Sohbet şablonu GGUF/Modelfile'a taşınmamış | Modelfile'da `TEMPLATE` ve `PARAMETER stop` tanımla (yukarıdaki "En Sinsi Tuzak" bölümü) |
| Birleştirilmiş model beklenenden kalitesiz | 4-bit ağırlıklar üzerine doğrudan birleştirme | 16-bit olarak birleştir; [LoRA Birleştirme](/kullanim/lora-birlestirme/) rehberini izle |
| Eğitimden sonra alan dışı sorularda gerileme | Felaket unutması (replay yok, lr yüksek) | Eğitim karışımına %5-10 genel veri ekle, lr'yi düşür; [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) ile ölç |

:::tip[Son söz]
İlk eğitimin mükemmel olmayacak — bu normal. Önemli olan **döngüyü bir kez baştan sona yaşamak**: veri → eğitim → test → ayar. İkinci ve üçüncü denemeler çok daha hızlı ve çok daha iyi olacak.
:::

## Kaynaklar ve İleri Okuma

- [TRL — SFT Trainer ve SFTConfig referansı](https://huggingface.co/docs/trl/sft_trainer) — `max_length`, `packing`, `assistant_only_loss` gibi tüm SFT parametrelerinin güncel tanımları (TRL v1.15, 2026).
- [Unsloth dokümantasyonu](https://unsloth.ai/docs) — `FastLanguageModel`, GGUF dışa aktarma ve Ollama'ya kaydetme dahil tüm akışlar (eski adres `docs.unsloth.ai` buraya yönleniyor).
- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv:2305.14314)](https://arxiv.org/abs/2305.14314) — 4-bit nicelemeli taban model üzerinde LoRA eğitimi fikrinin temel makalesi; bu rehberdeki yöntemin kaynağı.
- [TRL (GitHub)](https://github.com/huggingface/trl) — SFT, DPO ve diğer eğitim arayüzlerinin kaynak deposu; sürüm notları ve örnekler.
