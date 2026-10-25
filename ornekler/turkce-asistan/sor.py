# ---------------------------------------------------------------------------
# Örnek Proje 3c: Türkçe Sohbet Asistanı — Öncesi/Sonrası Karşılaştırma
# Aynı Türkçe soruyu önce temel model (Qwen3-4B) sonra LoRA'lı model cevaplar;
# iki cevabı yan yana yazdırır. "Fine-tuning gerçekten bir şey değiştirdi mi?"
# sorusunun en ikna edici kanıtı bu yan yana çıktıdır.
#
# Kurulum:  pip install unsloth peft accelerate bitsandbytes
#           (egitim.py ile aynı ortam; GPU gerekir)
# Çalıştır: python sor.py
#           python sor.py --soru "Bana kısa bir motivasyon sözü yaz."
#           python sor.py --temel unsloth/Qwen3-1.7B-unsloth-bnb-4bit   (8 GB VRAM için)
#
# NOT: İki model aynı anda VRAM'de durur (2 x ~2,5 GB 4-bit ağırlık + önbellek).
# 12 GB ve üzeri rahat; 8 GB'da küçük bir taban modelle (ör. 1.7B) deneyin.
# ---------------------------------------------------------------------------

import argparse
import sys
from pathlib import Path

# Windows konsolları UTF-8 dışı kodlama kullanabilir; Türkçe için sabitliyoruz.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch

# Unsloth 2026 sürümlerinde hem FastModel hem FastLanguageModel aynı işi yapar.
try:
    from unsloth import FastModel
except ImportError:  # eski Unsloth sürümleri
    from unsloth import FastLanguageModel as FastModel

SEED = 42  # örneklemenin iki modelde de aynı başlaması için sabit tohum
VARSAYILAN_TEMEL = "unsloth/Qwen3-4B-unsloth-bnb-4bit"
VARSAYILAN_SORU = "Kendini kısaca tanıtır mısın? Ne konularda yardımcı olabilirsin?"
VARSAYILAN_SISTEM = (
    "Sen Türkçe konuşan yardımcı bir asistansın. Sorulara kısa, net ve doğru "
    "cevaplar verirsin. Bilmediğin bir konuda emin olmadığını açıkça söylersin."
)

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def baslik(metin: str) -> None:
    print("\n" + "=" * 60)
    print(metin)
    print("=" * 60)


def cevap_uret(model, tokenizer, soru: str, sistem: str, max_yeni_token: int) -> str:
    """Tek bir soruya modelin cevabını üretir ve metni döndürür."""
    mesajlar = []
    if sistem:
        mesajlar.append({"role": "system", "content": sistem})
    mesajlar.append({"role": "user", "content": soru})

    # Qwen3 hibrit bir "düşünen" modeldir; şablon varsayılan olarak think
    # bloğu açar. Sohbet asistanında kısa ve doğrudan cevap istiyorsak düşünme
    # bloğunu kapatırız: enable_thinking=False. (Eski şablonlarda bu parametre
    # olmayabilir; o durumda Type/ValueError'a düşüp parametresiz devam ederiz.)
    try:
        girdi = tokenizer.apply_chat_template(
            mesajlar, tokenize=True, add_generation_prompt=True,
            return_tensors="pt", enable_thinking=False,
        )
    except (TypeError, ValueError):
        girdi = tokenizer.apply_chat_template(
            mesajlar, tokenize=True, add_generation_prompt=True, return_tensors="pt",
        )
    girdi = girdi.to("cuda")

    torch.manual_seed(SEED)  # iki modelde de aynı örnekleme başlangıcı
    with torch.no_grad():
        cikti = model.generate(
            input_ids=girdi,
            max_new_tokens=max_yeni_token,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            use_cache=True,
        )
    # Yalnızca YENİ üretilen jetonları çöz: girdi geri yazdırılırsa cevap
    # içinde soru da tekrarlanır ve karşılaştırma okunmaz hale gelir.
    return tokenizer.decode(cikti[0][girdi.shape[1]:], skip_special_tokens=True).strip()


def yan_yana(
    sol_baslik: str, sag_baslik: str, sol_metin: str, sag_metin: str, genislik: int = 48
) -> None:
    """İki metni satır satır sütunlara bölüp yan yana yazdırır."""
    def satirlara(metin: str) -> list[str]:
        satirlar: list[str] = []
        for paragraf in metin.splitlines():
            paragraf = paragraf.strip()
            while len(paragraf) > genislik:  # uzun satırları pencereye sığdır
                satirlar.append(paragraf[:genislik])
                paragraf = paragraf[genislik:]
            satirlar.append(paragraf)
        return satirlar or [""]

    sol, sag = satirlara(sol_metin), satirlara(sag_metin)
    yukseklik = max(len(sol), len(sag))
    print(f"{sol_baslik:<48} | {sag_baslik:<48}")
    print("-" * 48 + "-+-" + "-" * 48)
    for i in range(yukseklik):
        s = sol[i] if i < len(sol) else ""
        g = sag[i] if i < len(sag) else ""
        print(f"{s:<48} | {g:<48}")


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------


def main() -> None:
    betik_klasoru = Path(__file__).parent
    ayarlar = argparse.ArgumentParser(description="Temel model ile LoRA'lı modeli karşılaştır")
    ayarlar.add_argument("--temel", default=VARSAYILAN_TEMEL, help="taban model adı")
    ayarlar.add_argument(
        "--lora", default=str(betik_klasoru / "cikti" / "lora-model"),
        help="egitim.py'nin ürettiği adaptör klasörü",
    )
    ayarlar.add_argument("--soru", default=VARSAYILAN_SORU)
    ayarlar.add_argument("--sistem", default=VARSAYILAN_SISTEM,
                         help="boş bırakılırsa sistem mesajı eklenmez")
    ayarlar.add_argument("--max-yeni-token", type=int, default=256)
    secenekler = ayarlar.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA bulunamadı; bu betik GPU gerektirir.")
    if not Path(secenekler.lora).exists():
        raise SystemExit(
            f"LoRA adaptörü bulunamadı: {secenekler.lora}\n"
            "Önce 'python egitim.py' ile eğitimi çalıştırın."
        )

    # 1) Temel model (referans: eğitilmemiş hali) ---------------------------
    baslik("1) Temel model yükleniyor (referans)")
    model_temel, tokenizer = FastModel.from_pretrained(
        model_name=secenekler.temel,
        max_seq_length=2048,
        load_in_4bit=True,
        dtype=None,
    )
    FastModel.for_inference(model_temel)  # çıkarım modu: daha hızlı üretim
    print("Hazır.")
    print(f"VRAM tahsisi: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

    # 2) LoRA'lı model ------------------------------------------------------
    # Unsloth, adaptör klasörünü tanır (adapter_config.json) ve taban ağırlık
    # adını oradan okuyup adaptörü üzerine uygular; yani ayrıca taban model
    # yolu vermeye gerek yoktur. (Farklı bir araç zincirinde PeftModel.
    # from_pretrained(taban_model, adapter_yolu) de aynı işi yapar.)
    baslik("2) LoRA'lı model yükleniyor")
    model_lora, _ = FastModel.from_pretrained(
        model_name=secenekler.lora,
        max_seq_length=2048,
        load_in_4bit=True,
        dtype=None,
    )
    FastModel.for_inference(model_lora)
    print("Hazır.")
    print(f"VRAM tahsisi (iki model): {torch.cuda.memory_allocated() / 1e9:.2f} GB")

    # 3) Aynı soru, iki model ----------------------------------------------
    baslik("3) Aynı soru iki modele soruluyor")
    print(f"Soru: {secenekler.soru}")
    cevap_temel = cevap_uret(model_temel, tokenizer, secenekler.soru,
                             secenekler.sistem, secenekler.max_yeni_token)
    cevap_lora = cevap_uret(model_lora, tokenizer, secenekler.soru,
                            secenekler.sistem, secenekler.max_yeni_token)

    baslik("4) Yan yana karşılaştırma")
    yan_yana("TEMEL MODEL (öncesi)", "LORA'LI MODEL (sonrası)",
             cevap_temel or "(boş cevap)", cevap_lora or "(boş cevap)")

    baslik("Nasıl yorumlanır?")
    print("- LoRA'lı cevap, eğitim verinizin üslubuna ve uzunluğuna yaklaşmalı.")
    print("- Temel model daha genel/uzun cevaplar verebilir; bu beklenir.")
    print("- Şüpheli kısalma ya da bozulma varsa: epoch'u azaltın, veri kalitesini")
    print("  kontrol edin (bkz. README.md ve /llm/sorun-giderme/).")


if __name__ == "__main__":
    main()
