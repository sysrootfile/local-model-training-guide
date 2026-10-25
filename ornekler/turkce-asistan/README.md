# Örnek 3: Türkçe Sohbet Asistanı (Qwen3-4B + QLoRA)

Qwen3-4B modelini Türkçe bir SFT veri setiyle QLoRA ile fine-tune edip GGUF'a
dönüştüren ve Ollama'da çalıştıran üç betik. Dokümantasyon sayfası:
`/ornekler/turkce-asistan/`.

```
hazirla.py ──► egitim.py ──► sor.py
 (veri)         (QLoRA)       (öncesi/sonrası)
                   └──► --gguf ──► Modelfile ──► ollama create turkce-asistan
```

## Ortam kurulumu

```bash
# Proje kökünde (yoksa):
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell/CMD)
# source .venv/bin/activate       # WSL2 / Linux / macOS

# 1) Veri hazırlama (CPU yeterli):
pip install datasets

# 2) Eğitim (GPU gerekir):
pip install unsloth trl peft accelerate bitsandbytes datasets matplotlib
```

> **Ortam notu:** Eğitim için **WSL2 veya Linux önerilir**; Unsloth + bitsandbytes
> ve GGUF üretimi Windows'ta düzenli olarak tıkanır. Bulut GPU (aşağıya bakın)
> en sorunsuz seçenektir.

## Üç betiğin sırası

```bash
cd ornekler/turkce-asistan

# 1) Veriyi indir, kalite filtresinden geçir, train/test ayır:
python hazirla.py                  # tam veri seti (~5.579 satır)
python hazirla.py --limit 200      # hızlı deneme

# 2) QLoRA ile eğit (GPU):
python egitim.py --epoch 2                    # bf16 destekleyen GPU
python egitim.py --epoch 2 --fp16             # T4 / RTX 20xx (bf16 yok)
python egitim.py --epoch 2 --gguf             # eğitim sonunda GGUF da üret

# 3) Öncesi/sonrası karşılaştır (GPU):
python sor.py
python sor.py --soru "Bana kısa bir motivasyon sözü yaz."
```

Çıktılar `cikti/` klasörüne yazılır: `egitim.jsonl`, `test.jsonl`,
`lora-model/` (adaptör), `egitim-gunlugu.png` (loss eğrisi), `gguf/` (GGUF).

## GGUF + Ollama

`egitim.py --gguf` sonrası GGUF dosyası `cikti/gguf/` altındadır. Ollama'ya
eklemek için GGUF'un yanında bir `Modelfile` oluşturun:

```dockerfile
# Modelfile (cikti/gguf klasöründe)
FROM ./model.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
PARAMETER stop "<|im_end|>"

SYSTEM """Sen Türkçe konuşan yardımcı bir asistansın. Sorulara kısa, net ve doğru cevaplar verirsin. Bilmediğin bir konuda emin olmadığını açıkça söylersin."""
```

```bash
ollama create turkce-asistan -f Modelfile
ollama run turkce-asistan
```

Not: Unsloth'un ürettiği GGUF dosyasının adı sürüme göre değişebilir
(`model-Q4_K_M.gguf` gibi); `FROM` satırını `cikti/gguf/` içindeki gerçek
dosya adıyla güncelleyin.

## Donanım gereksinimi (kestirme)

| VRAM | Öneri |
| --- | --- |
| 8 GB | `unsloth/Qwen3-1.7B-unsloth-bnb-4bit` ile QLoRA; 4B eğitiminde batch 1 + kısa `--max-uzunluk` ile sınırda |
| 12 GB | **4B QLoRA rahat** (bu projenin varsayılanı); `sor.py` iki modeli birlikte yükler, sorunsuz |
| 16 GB+ | 8B model QLoRA ya da 4B'de daha büyük batch/uzunluk |

Bulut alternatifi (2026 itibarıyla yaklaşık fiyatlar): **RunPod** RTX 4090
~0,34–0,74 $/saat; **Vast.ai** RTX 4090 ~0,13–0,47 $/saat. 2 epoch'luk 4B
QLoRA eğitimi kiralık 4090'da tipik olarak 1–2 saat sürer.

## Dürüstlük notu

Bu projede `hazirla.py` bir geliştirici makinesinde (CPU, `datasets` 5.1.0)
**gerçekten çalıştırıldı**; sayfadaki veri sayıları bu çalıştırmadan alındı.
`egitim.py` ve `sor.py` GPU gerektirdiğinden **çalıştırılmadı** — resmî araç
sürümlerine göre yazıldı; kendi GPU'nuzda ilk çalıştırmada küçük sürüm
farklarına bağlı düzeltmeler gerekebilir.
