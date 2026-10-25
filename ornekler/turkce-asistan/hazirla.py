# ---------------------------------------------------------------------------
# Örnek Proje 3a: Türkçe Sohbet Asistanı — Veri Hazırlama
# Hugging Face'ten Türkçe bir SFT (talimat) veri setini indirir; alan adlarını
# esnek biçimde eşler, kalite filtresinden geçirir, %95/%5 train-test ayrımı
# yapar ve chat formatında (messages) iki .jsonl dosyası yazar.
# İkinci betik (egitim.py) bu dosyaları doğrudan okur.
#
# Kurulum:  pip install datasets
# Çalıştır: python hazirla.py                        (tam veri seti)
#           python hazirla.py --limit 200            (hızlı deneme)
#           python hazirla.py --veri-seti sayhan/aya_dataset_tur   (alternatif)
#
# Alternatif veri setleri (ID'ler 2026 itibarıyla geçerlidir, değişebilir):
#   - AlicanKiraz0/Turkish-SFT-Dataset-v1.0  (~5.579 satır, MIT)   [varsayılan]
#   - sayhan/aya_dataset_tur                 (4.046 train + 250 test, Apache-2.0)
#
# Çıktı: cikti/egitim.jsonl, cikti/test.jsonl, cikti/rapor.json
# ---------------------------------------------------------------------------

import argparse
import json
import random
import sys
from pathlib import Path

# Windows konsolları UTF-8 dışı kodlama kullanabilir; Türkçe için sabitliyoruz.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datasets import load_dataset

VARSAYILAN_VERI_SETI = "AlicanKiraz0/Turkish-SFT-Dataset-v1.0"
SEED = 42  # ayrımın her çalıştırmada aynı çıkması için sabit tohum

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def baslik(metin: str) -> None:
    print("\n" + "=" * 60)
    print(metin)
    print("=" * 60)


# ---------------------------------------------------------------------------
# Alan eşleme: farklı veri setlerinin sütun adlarını ortak "messages" şemasına
# çevirir. NEDEN gerekli: veri setleri aynı bilgiyi farklı adlarla tutar
# (user / talimat / instruction / prompt ...). Eğitim betiği yalnızca tek bir
# şemadan (messages) anlar; eşleme burada, veri tarafında bir kez yapılır.
# ---------------------------------------------------------------------------

MESAJ_ADLARI = {"messages", "mesajlar", "conversation", "conversations"}
KULLANICI_ADLARI = {
    "user", "kullanici", "kullanıcı", "talimat", "instruction",
    "prompt", "soru", "question", "inputs",
}
ASISTAN_ADLARI = {
    "assistant", "asistan", "cikti", "çıktı", "output", "completion",
    "cevap", "answer", "target", "targets", "response",
}
SISTEM_ADLARI = {"system", "sistem", "system_prompt", "system_message"}

# Eşlemede hangi sütunun hangi role gittiğini raporlamak için son kullanılanlar
son_esleme: dict[str, str] = {}


def sohbet_mi(deger: object) -> bool:
    """Değer, içinde role/content olan bir mesaj listesi mi? (messages alanı)"""
    return (
        isinstance(deger, list)
        and len(deger) > 0
        and all(
            isinstance(m, dict) and "role" in m and "content" in m for m in deger
        )
    )


def alan_esle(satir: dict) -> dict | None:
    """Bir ham satırı {"messages": [...]} biçimine çevirir; olmuyorsa None.

    İki yol var:
    1) Veri seti zaten `messages` (rol listesi) tutuyorsa dokunmadan al.
    2) Ayrı sütunlar (talimat/çıktı ya da user/assistant) tutuyorsa
       bilinen adlarla eşle ve standart üçlüyü kur.
    """
    alanlar = {str(k).strip().lower(): v for k, v in satir.items()}

    # Yol 1: hazır sohbet alanı
    for ad in MESAJ_ADLARI:
        if ad in alanlar and sohbet_mi(alanlar[ad]):
            son_esleme["messages"] = ad
            mesajlar = [
                {"role": str(m["role"]), "content": str(m["content"])}
                for m in alanlar[ad]
                if str(m.get("content", "")).strip()
            ]
            return {"messages": mesajlar} if mesajlar else None

    # Yol 2: ayrı sütunlar
    kullanici = next((alanlar[a] for a in KULLANICI_ADLARI if a in alanlar), None)
    asistan = next((alanlar[a] for a in ASISTAN_ADLARI if a in alanlar), None)
    if not isinstance(kullanici, str) or not isinstance(asistan, str):
        return None

    for ad in KULLANICI_ADLARI:
        if ad in alanlar:
            son_esleme["kullanici"] = ad
            break
    for ad in ASISTAN_ADLARI:
        if ad in alanlar:
            son_esleme["asistan"] = ad
            break

    mesajlar = []
    sistem = next((alanlar[a] for a in SISTEM_ADLARI if a in alanlar), None)
    if isinstance(sistem, str) and sistem.strip():
        son_esleme["sistem"] = next(a for a in SISTEM_ADLARI if a in alanlar)
        mesajlar.append({"role": "system", "content": sistem.strip()})
    mesajlar.append({"role": "user", "content": kullanici.strip()})
    mesajlar.append({"role": "assistant", "content": asistan.strip()})
    return {"messages": mesajlar}


# ---------------------------------------------------------------------------
# Kalite filtresi: boş, çok kısa veya talimatı cevapla aynı olan örnekler
# eğitime zarar verir (model kopyalamayı öğrenir). Eleme NEDENİ raporlanır ki
# filtreyi kendi verinizde ayarlayabileceğiniz sayıları görebilin.
# ---------------------------------------------------------------------------

EN_AZ_KULLANICI_KARAKTER = 10
EN_AZ_ASISTAN_KARAKTER = 20


def kaliteli_mi(kayit: dict) -> tuple[bool, str]:
    """Chat kaydını kalite kurallarından geçirir. Dönüş: (geçti mi, sebep)"""
    mesajlar = kayit["messages"]
    sorular = [m["content"] for m in mesajlar if m["role"] == "user"]
    cevaplar = [m["content"] for m in mesajlar if m["role"] == "assistant"]
    if not sorular or not cevaplar:
        return False, "kullanıcı veya asistan mesajı eksik"
    soru = sorular[-1]
    cevap = cevaplar[-1]
    if len(soru) < EN_AZ_KULLANICI_KARAKTER:
        return False, "soru çok kısa"
    if len(cevap) < EN_AZ_ASISTAN_KARAKTER:
        return False, "cevap çok kısa"
    # Talimat ile cevap birebir aynıysa örnek hiçbir şey öğretmez.
    if soru.casefold().strip() == cevap.casefold().strip():
        return False, "soru ve cevap aynı"
    return True, ""


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------


def main() -> None:
    ayarlar = argparse.ArgumentParser(description="Türkçe sohbet verisi hazırlama")
    ayarlar.add_argument("--veri-seti", default=VARSAYILAN_VERI_SETI)
    ayarlar.add_argument(
        "--limit", type=int, default=0,
        help="en fazla kaç kayıt kullanılsın (0 = tamamı)",
    )
    ayarlar.add_argument("--test-orani", type=float, default=0.05, help="test payı")
    ayarlar.add_argument("--cikti-klasoru", default=str(Path(__file__).parent / "cikti"))
    secenekler = ayarlar.parse_args()

    cikti_klasoru = Path(secenekler.cikti_klasoru)
    cikti_klasoru.mkdir(parents=True, exist_ok=True)

    # 1) Veri setini indir --------------------------------------------------
    baslik(f"1) Veri seti: {secenekler.veri_seti} (train bölümü)")
    ds = load_dataset(secenekler.veri_seti, split="train")
    butun_satirlar = list(ds)
    print(f"Ham kayıt sayısı: {len(butun_satirlar)}")
    print(f"Sütunlar: {list(butun_satirlar[0].keys())}")

    if secenekler.limit > 0:
        butun_satirlar = butun_satirlar[: secenekler.limit]
        print(f"--limit nedeniyle kullanılan kayıt: {len(butun_satirlar)}")

    # 2) Alan eşleme --------------------------------------------------------
    baslik("2) Alan eşleme (sütun adları -> messages şeması)")
    kayitlar = []
    atilan = 0
    for satir in butun_satirlar:
        eslenmis = alan_esle(satir)
        if eslenmis is None:
            atilan += 1
        else:
            kayitlar.append(eslenmis)
    for rol, ad in son_esleme.items():
        print(f"  '{ad}' sütunu -> {rol} rolü")
    eslenen_sayi = len(kayitlar)
    print(f"Eşlenen: {eslenen_sayi} | eşlenemeyip atılan: {atilan}")

    # 3) Kalite filtresi ----------------------------------------------------
    baslik("3) Kalite filtresi (boş / çok kısa / soru=cevap)")
    kalanlar = []
    sebepler: dict[str, int] = {}
    for kayit in kayitlar:
        gecti, sebep = kaliteli_mi(kayit)
        if gecti:
            kalanlar.append(kayit)
        else:
            sebepler[sebep] = sebepler.get(sebep, 0) + 1
    for sebep, sayi in sorted(sebepler.items(), key=lambda x: -x[1]):
        print(f"  elenen -> {sebep}: {sayi}")
    print(f"Kalan kayıt: {len(kalanlar)}")
    kayitlar = kalanlar

    # 4) Train/test ayrımı --------------------------------------------------
    # NEDEN sabit seed: aynı betiği iki kez çalıştırınca aynı dosyalar çıksın;
    # test setine eğitim sızmasın diye ayrım tek yerde ve bir kez yapılır.
    # Mimosa "guvensiz rastgelelik" der; bilerek: olcum tohumu, kripto degil
    # (secrets'a gecmek ayni veri kumelerini yeniden uretilemez yapardi).
    baslik(f"4) Train/test ayrımı (%{100 * (1 - secenekler.test_orani):.0f} / "
           f"%{100 * secenekler.test_orani:.0f}, seed={SEED})")
    rastgele = random.Random(SEED)
    rastgele.shuffle(kayitlar)
    test_sayisi = max(1, int(len(kayitlar) * secenekler.test_orani))
    test_kumesi = kayitlar[:test_sayisi]
    egitim_kumesi = kayitlar[test_sayisi:]
    print(f"Eğitim: {len(egitim_kumesi)} | Test: {len(test_kumesi)}")

    # 5) Diske yaz ----------------------------------------------------------
    baslik("5) Kaydetme (chat formatı: messages)")
    egitim_yolu = cikti_klasoru / "egitim.jsonl"
    test_yolu = cikti_klasoru / "test.jsonl"
    for yol, kume in ((egitim_yolu, egitim_kumesi), (test_yolu, test_kumesi)):
        with yol.open("w", encoding="utf-8") as f:
            for kayit in kume:
                f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
        print(f"Yazıldı: {yol} ({len(kume)} kayıt)")

    rapor = {
        "veri_seti": secenekler.veri_seti,
        "ham_kayit": len(butun_satirlar),
        "eslenen": eslenen_sayi,
        "elenen_sebepler": sebepler,
        "egitim": len(egitim_kumesi),
        "test": len(test_kumesi),
        "seed": SEED,
    }
    rapor_yolu = cikti_klasoru / "rapor.json"
    rapor_yolu.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Yazıldı: {rapor_yolu}")

    # 6) Önizleme: ham kayıt ile eğitime giren kaydın karşılaştırması ------
    baslik("6) Önizleme (ilk eğitim kaydı)")
    print("Chat formatına dönüşmüş ilk kayıt:")
    print(json.dumps(egitim_kumesi[0], ensure_ascii=False, indent=2)[:700])

    baslik("ÖZET")
    print(f"  Ham kayıt                       {len(butun_satirlar):6d}")
    print(f"  Kalite filtresi sonrası         {len(kayitlar):6d}")
    print(f"  Eğitim kümesi (cikti/egitim.jsonl) {len(egitim_kumesi):6d}")
    print(f"  Test kümesi   (cikti/test.jsonl)   {len(test_kumesi):6d}")
    print("\nSıradaki adım: egitim.py (Qwen3-4B + QLoRA). Bkz. README.md")


if __name__ == "__main__":
    main()
