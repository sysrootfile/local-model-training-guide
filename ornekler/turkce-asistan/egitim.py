# ---------------------------------------------------------------------------
# Örnek Proje 3b: Türkçe Sohbet Asistanı — QLoRA Eğitimi
# hazirla.py'nin ürettiği chat formatlı veriyle Qwen3-4B modelini 4-bit olarak
# yükleyip LoRA adaptörünü eğitir; kaybı (loss) grafiğe çizer; istenirse
# eğitim sonunda GGUF (Q4_K_M) dosyasını da üretir.
#
# Kurulum:  pip install unsloth trl peft accelerate bitsandbytes datasets matplotlib
#           (Unsloth kurulumu hızlı değişiyor; güncel komut için https://docs.unsloth.ai)
# Çalıştır: python egitim.py                       (cikti/egitim.jsonl ile eğit)
#           python egitim.py --epoch 1             (kısa deneme)
#           python egitim.py --gguf                (eğitim sonrası GGUF üret)
#           python egitim.py --fp16                (bf16 desteklemeyen GPU: T4, RTX 20xx)
#
# ÖNEMLİ NOTLAR
# - Windows'ta WSL2 önerilir; Linux veya bulut (ör. RunPod) daha sorunsuzdur.
#   bitsandbytes ve llama.cpp derlemesi Windows'ta düzenli olarak tıkanır.
# - T4 GPU'da bf16 YOK: betik donanımı otomatik algılar, gerekirse fp16'ya
#   düşer. Kendi kodunuzda bf16'yı koşulsuz açarsanız T4'te ya çöker ya da
#   sessizce yavaşlar — bu betikteki gibi "bf16=destekleniyorsa" yazın.
# - Eğitim GPU ister; bu proje GPU'suz bir makinede çalıştırılamaz.
# ---------------------------------------------------------------------------

import argparse
import sys
from pathlib import Path

# Windows konsolları UTF-8 dışı kodlama kullanabilir; Türkçe için sabitliyoruz.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
from datasets import load_dataset

# Unsloth 2026 sürümlerinde dil modelleri için hem FastModel hem
# FastLanguageModel aynı işi yapar; eski sürümlerde yalnızca ikincisi vardır.
try:
    from unsloth import FastModel
except ImportError:  # eski Unsloth sürümleri
    from unsloth import FastLanguageModel as FastModel

from trl import SFTConfig, SFTTrainer

VARSAYILAN_MODEL = "unsloth/Qwen3-4B-unsloth-bnb-4bit"  # Unsloth'un 4-bit hazır sürümü
SEED = 42

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def baslik(metin: str) -> None:
    print("\n" + "=" * 60)
    print(metin)
    print("=" * 60)


def kayip_egrisini_ciz(log_history: list[dict], cikti_yolu: Path) -> None:
    """Eğitim günlüğünden loss noktalarını çizip PNG olarak kaydeder.

    NEDEN grafik: kaybın düzenli düşüp düşmediğini onlarca satır log
    yerine tek bakışta görmek için. Düşmüyorsa hiçbir şey öğrenilmiyor demektir.
    """
    adimlar = [(k["step"], k["loss"]) for k in log_history if "loss" in k]
    if not adimlar:
        print("Uyarı: günlükte loss kaydı yok, grafik çizilemedi.")
        return
    try:
        import matplotlib

        matplotlib.use("Agg")  # ekransız sunucularda da çalışsın diye
        import matplotlib.pyplot as plt
    except ImportError:
        print("Uyarı: matplotlib kurulu değil (pip install matplotlib); grafik atlandı.")
        return
    x, y = zip(*adimlar)
    plt.figure(figsize=(9, 4.5))
    plt.plot(x, y, marker="o", markersize=3, linewidth=1.2)
    plt.xlabel("Eğitim adımı")
    plt.ylabel("Eğitim kaybı (loss)")
    plt.title("QLoRA eğitimi: kayıp eğrisi")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(cikti_yolu, dpi=120)
    plt.close()
    print(f"Kayıp eğrisi yazıldı: {cikti_yolu}")


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------


def main() -> None:
    betik_klasoru = Path(__file__).parent
    ayarlar = argparse.ArgumentParser(description="Qwen3-4B + QLoRA Türkçe sohbet eğitimi")
    ayarlar.add_argument("--veri", default=str(betik_klasoru / "cikti" / "egitim.jsonl"))
    ayarlar.add_argument("--test-veri", default=str(betik_klasoru / "cikti" / "test.jsonl"))
    ayarlar.add_argument("--cikti-klasoru", default=str(betik_klasoru / "cikti"))
    ayarlar.add_argument("--model", default=VARSAYILAN_MODEL)
    ayarlar.add_argument("--epoch", type=float, default=2.0, help="1-2 epoch tipik")
    ayarlar.add_argument("--batch-boyu", type=int, default=2, help="VRAM'e göre 1-4")
    ayarlar.add_argument("--gradyan-birikim", type=int, default=4, help="etkin batch = 2x4")
    ayarlar.add_argument("--max-uzunluk", type=int, default=2048, help="jeton; uzun veride artırın")
    ayarlar.add_argument("--gguf", action="store_true", help="eğitim sonunda GGUF (Q4_K_M) üret")
    ayarlar.add_argument("--fp16", action="store_true", help="T4 gibi bf16'sız GPU'larda zorla fp16")
    secenekler = ayarlar.parse_args()

    cikti_klasoru = Path(secenekler.cikti_klasoru)
    cikti_klasoru.mkdir(parents=True, exist_ok=True)
    lora_yolu = cikti_klasoru / "lora-model"

    if not Path(secenekler.veri).exists():
        raise SystemExit(
            f"Veri bulunamadı: {secenekler.veri}\n"
            "Önce 'python hazirla.py' çalıştırıp cikti/egitim.jsonl dosyasını üretin."
        )

    # 1) Modeli 4-bit yükle -------------------------------------------------
    # NEDEN 4-bit (QLoRA): 4B parametre fp16'da ~8 GB VRAM ister; 4-bit'e
    # nicemlenmiş sürüm ~2,5 GB'a iner ve üzerine eğitilen LoRA adaptörü
    # yalnızca birkaç on MB ekler. Kalite kaybı QLoRA makalesinde (2305.14314)
    # ölçülmüş ve çok küçük bulunmuştur.
    baslik("1) Model yükleme (4-bit)")
    gpu_mi = torch.cuda.is_available()
    if gpu_mi:
        print(f"GPU: {torch.cuda.get_device_name(0)} | "
              f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print("UYARI: CUDA bulunamadı; QLoRA eğitimi GPU olmadan pratikte çalışmaz.")
    bf16_uygun = gpu_mi and torch.cuda.is_bf16_supported()
    bf16_kullan = bf16_uygun and not secenekler.fp16
    print(f"bf16 desteği: {bf16_uygun} -> {'bf16' if bf16_kullan else 'fp16'} ile eğitilecek")

    model, tokenizer = FastModel.from_pretrained(
        model_name=secenekler.model,
        max_seq_length=secenekler.max_uzunluk,
        load_in_4bit=True,   # QLoRA'nın "Q"su: temel ağırlıklar 4-bit, eğitilmez
        dtype=None,          # bırakın Unsloth donanıma göre seçsin
    )

    # 2) LoRA adaptörünü ekle ----------------------------------------------
    # NEDEN r=16 / alpha=16: r adaptörün kapasitesi, alpha etkisinin ölçeği.
    # 16/16 Unsloth'un Qwen ailesi için önerdiği dengeli başlangıçtır (birçok
    # eğitimde alpha=32 da görülür: etkiyi büyütür, ezber riskini artırabilir).
    # Hedef modüller tüm dikkat (q/k/v/o) ve MLP (gate/up/down) projeksiyonları:
    # yalnızca q/v hedeflemek ucuzdur ama öğrenme kapasitesini ciddi kısıtlar.
    baslik("2) LoRA adaptörü (r=16, alpha=16, tüm projeksiyonlar)")
    model = FastModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        lora_dropout=0.0,       # 0 hem hızlı hem genelde yeterli
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",  # VRAM'i belirgin azaltır
        random_state=SEED,
    )
    egitilebilir = sum(p.numel() for p in model.parameters() if p.requires_grad)
    toplam = sum(p.numel() for p in model.parameters())
    print(f"Eğitilebilir parametre: {egitilebilir:,} / {toplam:,} "
          f"(%{100 * egitilebilir / toplam:.2f})")

    # 3) Veri + chat template kontrolü -------------------------------------
    # NEDEN tokenizer'ın kendi şablonu: Qwen3'ün sohbet formatı (<|im_start|>,
    # <|im_end|>) modele ön eğitimde öğretilmiştir. Elle ChatML metni yazmak
    # ya da apply_chat_template dışında özel token eklemek (add_special_tokens)
    # şablonu bozar. Şablon tokenizer ile birlikte gelir; biz yalnızca uygularız.
    baslik("3) Veri ve chat template")
    egitim_verisi = load_dataset("json", data_files=secenekler.veri, split="train")
    test_yolu = Path(secenekler.test_veri)
    test_verisi = (
        load_dataset("json", data_files=str(test_yolu), split="train")
        if test_yolu.exists() else None
    )
    print(f"Eğitim örneği: {len(egitim_verisi)} | Test örneği: "
          f"{len(test_verisi) if test_verisi is not None else 0}")
    print(f"Örnek sütunlar: {egitim_verisi.column_names}  (messages -> sohbet formatı)")
    print(f"tokenizer.eos_token = {tokenizer.eos_token!r}  "
          "(Qwen3'te <|im_end|>: cevabın bittiğini modele bu öğretir)")

    ornek_metin = tokenizer.apply_chat_template(
        egitim_verisi[0]["messages"], tokenize=False, add_generation_prompt=False
    )
    print("Chat şablonu önizlemesi (ilk 240 karakter):")
    print("  " + " ".join(ornek_metin.split())[:240] + " ...")

    # 4) Eğitim -------------------------------------------------------------
    # warmup_ratio=0.05: adımların %5'inde öğrenme oranı kademeli açılır —
    # eğitimin ilk anlarında büyük LoRA gradyanlarının modeli sarsmasını önler.
    # assistant_only_loss=True: kayıp yalnızca asistan cevaplarından hesaplanır;
    # sistem/kullanıcı metnini tahmin etmeyi öğrenmek zaman kaybıdır. Şablon
    # gerekli {% generation %} işaretlerini içermiyorsa TRL, Qwen3 gibi bilinen
    # ailelerde şablonu otomatik yamalar.
    baslik("4) Eğitim (SFTTrainer)")
    egitim_ayari = SFTConfig(
        output_dir=str(cikti_klasoru / "checkpoint"),  # save_steps ile ara kayıtlar
        num_train_epochs=secenekler.epoch,             # 1-2 epoch tipik; fazlası ezber
        per_device_train_batch_size=secenekler.batch_boyu,
        gradient_accumulation_steps=secenekler.gradyan_birikim,  # etkin batch = 2x4 = 8
        learning_rate=2e-4,                            # LoRA için tipik değer
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        weight_decay=0.01,
        optim="adamw_8bit",                            # 8-bit optimizer: VRAM tasarrufu
        bf16=bf16_kullan,
        fp16=not bf16_kullan,                          # ikisi AYNI ANDA açılamaz
        max_length=secenekler.max_uzunluk,             # eski TRL'de adı max_seq_length
        assistant_only_loss=True,                      # yalnızca asistan cevabından öğren
        logging_steps=10,
        save_steps=100,                                # 100 adımda bir checkpoint
        save_total_limit=2,                            # disk şişmesin
        eval_strategy="steps" if test_verisi is not None else "no",
        eval_steps=100 if test_verisi is not None else None,
        report_to="none",                              # wandb/tensorboard istemiyoruz
        seed=SEED,
    )
    egitici = SFTTrainer(
        model=model,
        processing_class=tokenizer,   # sohbet şablonunu uygulayan sınıf
        train_dataset=egitim_verisi,
        eval_dataset=test_verisi,
        args=egitim_ayari,
    )
    egitici.train()

    # 5) Adaptörü ve grafiği kaydet -----------------------------------------
    # Yalnızca adaptör (birkaç on MB) kaydedilir; taban model değişmez. GGUF
    # üretimi ve birleştirme bu dosyadan yeniden yapılabilir.
    baslik("5) Kaydetme")
    model.save_pretrained(str(lora_yolu))
    tokenizer.save_pretrained(str(lora_yolu))  # chat template de saklanır
    print(f"LoRA adaptörü yazıldı: {lora_yolu}")

    kayip_egrisini_ciz(egitici.state.log_history, cikti_klasoru / "egitim-gunlugu.png")
    son_kayitlar = [k for k in egitici.state.log_history if "loss" in k][-3:]
    for kayit in son_kayitlar:
        print(f"  adım {kayit['step']:>5} | loss = {kayit['loss']:.4f}")

    # 6) (İsteğe bağlı) GGUF: Ollama'nın istediği tek dosya formatı ---------
    # save_pretrained_gguf önce adaptörü taban modelle birleştirir, sonra
    # llama.cpp ile Q4_K_M'ye nicemler. llama.cpp derlemesi Windows'ta sık
    # tıkanır; WSL2/Linux'ta çok daha sorunsuz.
    if secenekler.gguf:
        baslik("6) GGUF üretimi (q4_k_m)")
        gguf_klasoru = cikti_klasoru / "gguf"
        model.save_pretrained_gguf(
            str(gguf_klasoru),
            tokenizer,
            quantization_method="q4_k_m",
        )
        print(f"GGUF yazıldı: {gguf_klasoru}")
        print("Ollama'ya ekleme adımları için README.md'ye bakın.")

    baslik("Bitti")
    print(f"Adaptör      : {lora_yolu}")
    print(f"Loss grafiği : {cikti_klasoru / 'egitim-gunlugu.png'}")
    print("Sıradaki adım: python sor.py  (öncesi/sonrası karşılaştırma)")


if __name__ == "__main__":
    main()
