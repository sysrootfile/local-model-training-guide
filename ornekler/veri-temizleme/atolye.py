# ---------------------------------------------------------------------------
# Örnek Proje 2: Veri Temizleme Atölyesi
# Gerçek bir Türkçe talimat (instruction) veri setini Hugging Face'ten indirir;
# tekrar temizliği, kalite filtreleme, PII (kişisel veri) maskeleme ve
# SFT (chat) formatına çevirme adımlarını uygular; öncesi/sonrası raporlar.
#
# Kurulum:  pip install datasets ftfy datasketch
# Çalıştır: python atolye.py                        (varsayılan: 3000 örnek)
#           python atolye.py --ornek 1000           (daha hızlı deneme)
#           python atolye.py --veri-seti AlicanKiraz0/Turkish-SFT-Dataset-v1.0
#
# Alternatif veri setleri (ID'ler 2026 itibarıyla geçerlidir, değişebilir):
#   - merve/turkish_instructions           (~52 bin satır, apache-2.0)  [varsayılan]
#   - AlicanKiraz0/Turkish-SFT-Dataset-v1.0 (~5,6 bin satır, MIT)
#   - ogulcanaydogan/Turkish-LLM-v10-Training (~144 bin satır, apache-2.0)
#   - atasoglu/instruction-turkish         (327 satır, apache-2.0 — hızlı test)
# ---------------------------------------------------------------------------

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

# Windows konsolları UTF-8 dışı kodlama kullanabilir; Türkçe için sabitliyoruz.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import ftfy
from datasketch import MinHash, MinHashLSH
from datasets import load_dataset

VARSAYILAN_VERI_SETI = "merve/turkish_instructions"

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def baslik(metin: str) -> None:
    print("\n" + "=" * 60)
    print(metin)
    print("=" * 60)


def tr_kucult(metin: str) -> str:
    """Türkçe'ye uygun küçük harfe çevirme.

    Python'ın lower() fonksiyonu Türkçe'yi bilmez: "İ".lower() -> "i̇"
    (i + birleşik nokta) ve "I".lower() -> "i" üretir; ikisi de yanlıştır.
    Bu yüzden İ/I'yı açıkça eşler, sonra kalan harfleri küçültürüz.
    Karşılaştırma anahtarı üretmek için kullanılır; metnin kendisi DEĞİŞMEZ.
    """
    return metin.replace("İ", "i").replace("I", "ı").lower()


def normalize_et(metin: str) -> str:
    """Bir metni temizler: kodlama onarımı, Unicode normalizasyonu, fazlalıklar."""
    metin = ftfy.fix_text(metin)              # mojibake onarımı (ör. "Ä°stanbul" -> "İstanbul")
    metin = unicodedata.normalize("NFC", metin)  # birleşik karakterleri standart biçime getir
    metin = html.unescape(metin)              # &amp; gibi HTML varlıklarını çöz
    metin = re.sub(r"<[^>]{1,80}>", " ", metin)  # HTML/XML etiketlerini kaldır
    metin = re.sub(r"[\u200b-\u200f\u202a-\u202e\ufeff]", "", metin)  # görünmez/yön karakterleri
    metin = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", metin)       # kontrol karakterleri
    metin = re.sub(r"\s+", " ", metin)        # boşlukları sadeleştir
    return metin.strip()


# ---------------------------------------------------------------------------
# PII (kişisel veri) maskeleme
# ---------------------------------------------------------------------------

EPOSTA_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")
TELEFON_RE = re.compile(
    r"(?<!\d)(?:\+90|0)?[\s.-]?\(?(?:5\d{2}|[2-4]\d{2})\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)"
)
IBAN_RE = re.compile(r"(?<!\w)TR\d{2}[\s]?(?:\d{4}[\s]?){5}\d{2}(?!\d)")
TCKN_ADAY_RE = re.compile(r"(?<!\d)\d{11}(?!\d)")


def tckn_gecerli_mi(aday: str) -> bool:
    """TC kimlik numarasının sağlama hanelerini doğrular."""
    if aday[0] == "0":
        return False
    rakamlar = [int(r) for r in aday]
    tek_toplam = rakamlar[0] + rakamlar[2] + rakamlar[4] + rakamlar[6] + rakamlar[8]
    cift_toplam = rakamlar[1] + rakamlar[3] + rakamlar[5] + rakamlar[7]
    onuncu = (tek_toplam * 7 - cift_toplam) % 10
    on_birinci = sum(rakamlar[:10]) % 10
    return rakamlar[9] == onuncu and rakamlar[10] == on_birinci


def pii_maskele(metin: str) -> tuple[str, int]:
    """Metindeki e-posta, telefon, IBAN ve geçerli TCKN'leri maskeler.

    Dönüş: (maskelenmiş metin, maskeleme sayısı)
    """
    sayac = 0
    metin, n = EPOSTA_RE.subn("[E-POSTA]", metin)
    sayac += n
    metin, n = IBAN_RE.subn("[IBAN]", metin)
    sayac += n
    metin, n = TELEFON_RE.subn("[TELEFON]", metin)
    sayac += n

    def tckn_degistir(eslesme: re.Match) -> str:
        nonlocal sayac
        aday = eslesme.group(0)
        if tckn_gecerli_mi(aday):  # yalnızca sağlaması tutan numaralar TCKN'dir
            sayac += 1
            return "[TC-KIMLIK]"
        return aday

    metin = TCKN_ADAY_RE.sub(tckn_degistir, metin)
    return metin, sayac


# ---------------------------------------------------------------------------
# Kalite filtreleri
# ---------------------------------------------------------------------------

EN_FAZLA_TEKRAR_ORANI = 0.30  # en sık 3'lü kelime grubu toplamın %30'undan fazlaysa: kalitesiz


def tekrar_orani(metin: str) -> float:
    """En sık geçen 3'lü kelime grubunun toplam 3'lü gruba oranı."""
    kelimeler = [tr_kucult(k) for k in metin.split()]
    if len(kelimeler) < 6:
        return 0.0
    ucgenler = [" ".join(kelimeler[i : i + 3]) for i in range(len(kelimeler) - 2)]
    en_sik = max(ucgenler.count(u) for u in set(ucgenler))
    return en_sik / len(ucgenler)


def kaliteli_mi(kayit: dict) -> tuple[bool, str]:
    """Kaydı kalite kurallarından geçirir. Dönüş: (geçti mi, sebep)"""
    cikti = kayit["cikti"]
    if len(cikti) < 20 or len(cikti.split()) < 3:
        return False, "çıktı çok kısa"
    if tekrar_orani(cikti) > EN_FAZLA_TEKRAR_ORANI:
        return False, "aşırı kelime tekrarı"
    harf_ve_rakam = sum(k.isalnum() for k in cikti)
    if harf_ve_rakam / max(len(cikti), 1) < 0.5:
        return False, "alfanümerik oran düşük (gürültü)"
    if tr_kucult(kayit["talimat"]).strip() == tr_kucult(cikti).strip():
        return False, "talimat ve çıktı aynı"
    return True, ""


# ---------------------------------------------------------------------------
# Veri çekme
# ---------------------------------------------------------------------------


def veri_cek(veri_seti: str, ornek_sayisi: int) -> list[dict]:
    """Hugging Face'ten akış (streaming) ile ilk N kaydı çeker.

    streaming=True sayesinde tüm veri seti indirilmez; yalnızca ihtiyaç
    kadar satır çekilir (disk ve zaman tasarrufu).
    """
    ds = load_dataset(veri_seti, split="train", streaming=True)
    kayitlar = []
    for satir in ds:
        kayitlar.append(satir)
        if len(kayitlar) >= ornek_sayisi:
            break
    return kayitlar


TALIM_ADLARI = {"talimat", "instruction", "prompt", "soru", "question", "inputs"}
GIRIS_ADLARI = {"giriş", "giris", "input", "context", "bağlam", "baglam"}
CIKTI_ADLARI = {"çıktı", "cikti", "output", "completion", "cevap", "answer", "target", "targets", "response"}


def alan_esle(satir: dict) -> dict | None:
    """Farklı veri setlerindeki sütun adlarını ortak şemaya eşler.

    Ham veri setlerinde sütun adları değişir (talimat/instruction/prompt...)
    ve başında/sonunda boşluk olabilir; hepsini normalize edip eşliyoruz.
    """
    alanlar = {k.strip().lower(): v for k, v in satir.items()}
    talimat = next((alanlar[a] for a in TALIM_ADLARI if a in alanlar), None)
    cikti = next((alanlar[a] for a in CIKTI_ADLARI if a in alanlar), None)
    giris = next((alanlar[a] for a in GIRIS_ADLARI if a in alanlar), "") or ""
    if not isinstance(talimat, str) or not isinstance(cikti, str):
        return None
    return {"talimat": talimat, "giris": giris if isinstance(giris, str) else "", "cikti": cikti}


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------


def main() -> None:
    ayarlar = argparse.ArgumentParser(description="Türkçe veri temizleme atölyesi")
    ayarlar.add_argument("--veri-seti", default=VARSAYILAN_VERI_SETI)
    ayarlar.add_argument("--ornek", type=int, default=3000, help="çekilecek kayıt sayısı")
    ayarlar.add_argument("--cikti-klasoru", default=str(Path(__file__).parent / "cikti"))
    secenekler = ayarlar.parse_args()

    cikti_klasoru = Path(secenekler.cikti_klasoru)
    cikti_klasoru.mkdir(parents=True, exist_ok=True)

    baslik(f"1) Veri çekme: {secenekler.veri_seti} (ilk {secenekler.ornek} kayıt, streaming)")
    ham_satirlar = veri_cek(secenekler.veri_seti, secenekler.ornek)
    print(f"Çekilen ham kayıt: {len(ham_satirlar)}")
    print(f"Sütunlar: {list(ham_satirlar[0].keys())}")

    baslik("2) Alan eşleme ve ön istatistik")
    kayitlar = []
    atilan_alan = 0
    for satir in ham_satirlar:
        eslenmis = alan_esle(satir)
        if eslenmis is None:
            atilan_alan += 1
        else:
            kayitlar.append(eslenmis)
    print(f"Alan eşlemesi başarılı: {len(kayitlar)} | eşlenemeyip atılan: {atilan_alan}")
    ortalama_uzunluk = sum(len(k["cikti"]) for k in kayitlar) / max(len(kayitlar), 1)
    print(f"Ortalama çıktı uzunluğu (ham): {ortalama_uzunluk:.0f} karakter")

    log: list[tuple[str, int]] = [("Çekilen ham kayıt", len(ham_satirlar))]

    # 3) Araçların mini testi -------------------------------------------------
    # Seçilen veri seti temiz olabilir (bu sette PII ve tekrar neredeyse yok);
    # araçların gerçekten çalıştığını görmek için 3 bilerek bozuk örnek metin
    # üzerinde deneriz. Gerçek projelerde bu bozukluklar veri setinin içinde gelir.
    baslik("3) Araçların mini testi (bilerek bozuk örnek metinler)")
    minik_ornekler = [
        "Bana 0532 123 45 67'den ulaşın; e-posta: ali@example.com, TCKN: 10000000146.",
        "Ä°stanbul'da hava Ã§ok gÃ¼zel, yarÄ±n da gÃ¼zel olacak.",
        "çok çok çok çok çok güzel güzel güzel güzel bir gün",
    ]
    for metin in minik_ornekler:
        duzeltilmis = normalize_et(metin)
        maskelenmis, maske_sayisi = pii_maskele(duzeltilmis)
        print(f"Girdi       : {metin}")
        print(f"Normalize   : {duzeltilmis}")
        print(f"Maskelenmiş : {maskelenmis}  (maskeleme: {maske_sayisi})")
        print(f"Tekrar oranı: {tekrar_orani(metin):.2f}  (eşik: {EN_FAZLA_TEKRAR_ORANI})")
        print("-" * 40)

    # 4) Normalizasyon ------------------------------------------------------
    baslik("4) Normalizasyon (mojibake onarımı, NFC, HTML temizliği, boşluklar)")
    duzelen = 0
    for kayit in kayitlar:
        for alan in ("talimat", "giris", "cikti"):
            eski = kayit[alan]
            kayit[alan] = normalize_et(eski)
            if kayit[alan] != eski:
                duzelen += 1
    print(f"Düzeltilen alan sayısı: {duzelen}")
    log.append(("Normalizasyon sonrası", len(kayitlar)))

    # 5) PII maskeleme ------------------------------------------------------
    baslik("5) PII maskeleme (e-posta, telefon, TCKN, IBAN)")
    toplam_maske = 0
    pii_olan_kayit = 0
    for kayit in kayitlar:
        yeni_talimat, n1 = pii_maskele(kayit["talimat"])
        yeni_giris, n3 = pii_maskele(kayit["giris"])
        yeni_cikti, n2 = pii_maskele(kayit["cikti"])
        if n1 + n2 + n3 > 0:
            pii_olan_kayit += 1
        toplam_maske += n1 + n2 + n3
        kayit["talimat"], kayit["giris"], kayit["cikti"] = yeni_talimat, yeni_giris, yeni_cikti
    print(f"Maskelenen kişisel veri: {toplam_maske} adet ({pii_olan_kayit} kayıtta)")
    log.append(("PII maskeleme sonrası", len(kayitlar)))

    # 6) Kalite filtreleme --------------------------------------------------
    baslik("6) Kalite filtreleri (uzunluk, tekrar, gürültü)")
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
    log.append(("Kalite filtreleri sonrası", len(kalanlar)))
    kayitlar = kalanlar

    # 7) Tam tekrar temizliği ----------------------------------------------
    baslik("7) Tam tekrar temizliği (aynı metinler)")
    gorulen: set[str] = set()
    benzersiz = []
    for kayit in kayitlar:
        anahtar = hashlib.sha1(
            tr_kucult(kayit["talimat"]).encode("utf-8")
            + b"|"
            + tr_kucult(kayit["cikti"]).encode("utf-8")
        ).hexdigest()
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            benzersiz.append(kayit)
    print(f"Tam tekrar olarak atılan: {len(kayitlar) - len(benzersiz)}")
    print(f"Kalan kayıt: {len(benzersiz)}")
    log.append(("Tam tekrar temizliği sonrası", len(benzersiz)))
    kayitlar = benzersiz

    # 8) Yakın tekrar temizliği (MinHash + LSH) ----------------------------
    baslik("8) Yakın tekrar temizliği (MinHash + LSH, eşik=0.8)")
    lsh = MinHashLSH(threshold=0.8, num_perm=64)
    benzersiz2 = []
    yakin_tekrar = 0
    for i, kayit in enumerate(kayitlar):
        mh = MinHash(num_perm=64)
        for kelime in tr_kucult(kayit["cikti"]).split():
            mh.update(kelime.encode("utf-8"))
        if lsh.query(mh):
            yakin_tekrar += 1
            continue
        lsh.insert(f"k{i}", mh)
        benzersiz2.append(kayit)
    print(f"Yakın tekrar olarak atılan: {yakin_tekrar}")
    print(f"Kalan kayıt: {len(benzersiz2)}")
    log.append(("Yakın tekrar temizliği sonrası", len(benzersiz2)))
    kayitlar = benzersiz2

    # 9) SFT (chat) formatına çevir ve diske yaz ---------------------------
    baslik("9) SFT formatına çevirme ve kaydetme")
    temiz_yolu = cikti_klasoru / "temiz_veri.jsonl"
    with temiz_yolu.open("w", encoding="utf-8") as f:
        for kayit in kayitlar:
            kullanici_metni = kayit["talimat"]
            if kayit["giris"]:
                kullanici_metni += "\n\nBağlam: " + kayit["giris"]
            sft_kaydi = {
                "messages": [
                    {"role": "user", "content": kullanici_metni},
                    {"role": "assistant", "content": kayit["cikti"]},
                ]
            }
            f.write(json.dumps(sft_kaydi, ensure_ascii=False) + "\n")
    print(f"Temiz veri yazıldı: {temiz_yolu} ({len(kayitlar)} kayıt)")

    rapor = {
        "veri_seti": secenekler.veri_seti,
        "cekilen": len(ham_satirlar),
        "asamalar": log,
        "pii_maskeleme": toplam_maske,
        "pii_olan_kayit": pii_olan_kayit,
        "elenen_sebepler": sebepler,
        "son_kayit": len(kayitlar),
    }
    rapor_yolu = cikti_klasoru / "rapor.json"
    rapor_yolu.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rapor yazıldı: {rapor_yolu}")

    # 10) Önizleme ----------------------------------------------------------
    baslik("10) Örnek çıktı (ilk 2 kayıt)")
    with temiz_yolu.open(encoding="utf-8") as f:
        for satir in list(f)[:2]:
            ornek = json.loads(satir)
            print(json.dumps(ornek, ensure_ascii=False, indent=2)[:600])
            print("-" * 40)

    baslik("ÖZET: Öncesi -> Sonrası")
    for asama, sayi in log:
        print(f"  {asama:36s} {sayi:6d}")
    print(f"\nTemiz veri oranı: {len(kayitlar) / max(len(ham_satirlar), 1):.1%}")


if __name__ == "__main__":
    main()
