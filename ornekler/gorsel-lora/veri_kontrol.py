# ---------------------------------------------------------------------------
# Örnek Proje 4: Görsel Stil LoRA — veri seti denetçisi (veri_kontrol.py)
#
# NE YAPAR: Bir görsel klasörünü (LoRA eğitim veri setini) eğitimden ÖNCE
# denetler: format ve boyut dağılımını raporlar; SDXL hedefi olan 1024px'in
# altındaki görselleri uyarı olarak listeler; birebir aynı dosyaları sha1 ile,
# birkaç pikseli değişmiş "neredeyse aynı" kareleri dHash (difference hash)
# ile bulur; caption (.txt) eksik/fazla dosyaları çıkarır; caption'lardaki
# tetikleyici kelimeyi sayar. Özeti ekrana ve cikti/denetim-raporu.json'a yazar.
#
# NEDEN CPU YETER: Eğitim GPU ister ama denetim yalnızca görsellere "bakar".
# Her görselin 9x8 gri küçük kopyası üzerinden parmak izi çıkarıldığı için
# 1024px'lik onlarca görsel bile saniyeler içinde taranır.
#
# NEDEN eğitimden önce denetim: 1024px altı görseller bulanık sonuç üretir;
# birebir/yakın tekrarlar veri çeşitliliğini düşürüp modeli ezberletir; caption
# eksikliği eğitimde sessizce atlanır; tetikleyicisiz caption ise üslubu
# kelimeye bağlamayı imkânsızlaştırır. Hepsi eğitimden önce 30 saniyede görülür.
#
# Kurulum:  pip install pillow
# Çalıştır: python veri_kontrol.py --klasor veri/stilim
#           python veri_kontrol.py --klasor veri/stilim --tetikleyici stilim
#
# DÜRÜSTLÜK NOTU (bu makinede test): Betik, cikti/test-gorseller/ klasöründe
# PIL ile ÜRETİLMİŞ 6 SAHTE görselle çalıştırıldı. O görseller kasten
# kusurludur (512px küçük görsel, birebir kopya, birkaç pikseli değişik kopya,
# caption'sız görsel) ve gerçek bir veri setini TEMSİL ETMEZ. Amaç, betiğin
# uyarıları gerçekten yakaladığını göstermektir.
# ---------------------------------------------------------------------------

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

# Windows konsolları varsayılan olarak UTF-8 dışı bir kodlama (ör. cp1252)
# kullanır; Türkçe karakterler yazdırılırken hata vermesin diye çıktıyı
# UTF-8'e sabitliyoruz. (reconfigure her ortamda bulunmaz, korumalı çağırıyoruz.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from PIL import Image

# Pillow'un desteklediği yaygın uzantılar; kohya/ai-toolkit de bu tipleri alır.
GORSEL_UZANTILARI = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

KUCUK_ESIK = 1024   # SDXL eğitimi için hedeflenen en küçük kenar (piksel)
YAKIN_ESIK = 6      # dHash Hamming mesafesi: 64 bitte <=6 ise "neredeyse aynı"
DHASH_BOYUT = 8     # dHash klasik ayarı: 9x8 gri görüntüden 64 bit üretilir

# Bu betik tamamen deterministiktir: rastgelelik kullanmaz, dosyalar ad
# sırasıyla taranır; aynı klasör her çalıştırmada aynı raporu üretir.


def baslik(metin: str) -> None:
    """Çıktıyı bölümlere ayırmak için basit bir başlık yazdırır."""
    print("\n" + "=" * 60)
    print(metin)
    print("=" * 60)


def sha1_dosya(yol: Path) -> str:
    """Dosyanın sha1 parmak izi. Birebir aynı iki dosya aynı değeri verir.

    DİKKAT: İçeriği aynı ama yeniden kaydedilmiş (ör. PNG -> JPEG) dosyalar
    farklı sha1 alır; onları dHash yakalar. sha1 baytları, dHash pikselleri
    karşılaştırır — iki yöntem bu yüzden birbirini tamamlar.
    """
    ozet = hashlib.sha1()
    with yol.open("rb") as f:
        for parca in iter(lambda: f.read(65536), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def dhash(im: Image.Image) -> int:
    """Difference hash: 9x8 gri görüntünün yatay komşu farklarından 64 bit.

    Piksel değerlerinin kendisi değil, komşulara göre ARTIŞ/AZALIŞ yönü
    saklanır; bu yüzden 8-10 byte'lık sıkıştırma gürültüsü ya da birkaç
    pikselin oynaması hash'i değiştirmez. Amacımız zaten "görsel olarak aynı
    sayılır mı?" sorusuna cevap vermek.
    """
    gri = im.convert("L").resize((DHASH_BOYUT + 1, DHASH_BOYUT), Image.Resampling.LANCZOS)
    pikseller = gri.tobytes()  # mode "L": her piksel 1 bayt -> 8 satır x 9 sütun
    bitler = 0
    for satir in range(DHASH_BOYUT):
        temel = satir * (DHASH_BOYUT + 1)
        for sutun in range(DHASH_BOYUT):
            sol = pikseller[temel + sutun]
            sag = pikseller[temel + sutun + 1]
            bitler = (bitler << 1) | (1 if sol > sag else 0)
    return bitler


def hamming(a: int, b: int) -> int:
    """İki dHash arasındaki Hamming mesafesi: kaç bit farklı? (0 = aynı)."""
    return bin(a ^ b).count("1")


def main() -> None:
    ayarlar = argparse.ArgumentParser(description="Görsel veri seti denetçisi (CPU; GPU gerekmez)")
    ayarlar.add_argument("--klasor", required=True, help="denetlenecek görsel klasörü")
    ayarlar.add_argument("--tetikleyici", default="stilim",
                         help="caption'larda aranacak tetikleyici kelime (varsayılan: stilim)")
    ayarlar.add_argument("--cikti-klasoru", default=str(Path(__file__).parent / "cikti"))
    secenekler = ayarlar.parse_args()

    klasor = Path(secenekler.klasor)
    if not klasor.is_dir():
        print(f"HATA: klasör bulunamadı: {klasor}")
        sys.exit(1)
    cikti_klasoru = Path(secenekler.cikti_klasoru)
    cikti_klasoru.mkdir(parents=True, exist_ok=True)
    tetikleyici = secenekler.tetikleyici.casefold()

    # Uyarılar burada toplanır; özette tek listede gösterilir ve rapora girer.
    uyarilar: list[str] = []

    # -----------------------------------------------------------------------
    # 1) Klasörü tara: her görselin boyutu, formatı, sha1 ve dHash'i
    # -----------------------------------------------------------------------
    baslik("1) Klasör taraması")
    gorsel_yollari = sorted(
        p for p in klasor.iterdir() if p.is_file() and p.suffix.lower() in GORSEL_UZANTILARI
    )
    txt_yollari = sorted(p for p in klasor.iterdir() if p.is_file() and p.suffix.lower() == ".txt")
    if not gorsel_yollari:
        print(f"Klasörde görsel bulunamadı: {klasor}")
        sys.exit(1)

    bilgiler: list[dict] = []
    okunamayanlar: list[str] = []
    for yol in gorsel_yollari:
        try:
            # im.load() şart: yarım inmiş, bozuk dosyalar burada patlar; basit
            # başlık okuma yeterli olmaz ve eğitim sırasında iş çıkarır.
            with Image.open(yol) as im:
                im.load()
                kayit = {
                    "dosya": yol.name,
                    "genislik": im.width,
                    "yukseklik": im.height,
                    "format": (im.format or "?").upper(),
                    "sha1": sha1_dosya(yol),
                    "dhash": dhash(im),
                }
            bilgiler.append(kayit)
        except Exception:
            okunamayanlar.append(yol.name)

    print(f"Klasör          : {klasor}")
    print(f"Görsel dosyası  : {len(gorsel_yollari)}")
    print(f"Caption (.txt)  : {len(txt_yollari)}")
    print(f"Tetikleyici     : {secenekler.tetikleyici!r}")
    if okunamayanlar:
        print("MİNİK UYARI: şu dosyalar açılamadı (bozuk/yarım indirme olabilir):")
        for ad in okunamayanlar:
            print(f"  {ad}")
        uyarilar.append(f"{len(okunamayanlar)} dosya okunamadı (bozuk/yarım indirme?)")
    if not bilgiler:
        print("Hiçbir görsel okunamadı; rapor üretilemez.")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # 2) Format ve boyut dağılımı
    #    NEDEN: Eğitimin "girdi profilini" görmek için. Hepsi tek boyuttaysa
    #    çeşitlilik zayıftır; format karışıksa sorun değil ama kayıpsız PNG
    #    tercih edilir.
    # -----------------------------------------------------------------------
    baslik("2) Format ve boyut dağılımı")
    format_sayilari = Counter(k["format"] for k in bilgiler)
    print("Format dağılımı:")
    for format_adi, adet in format_sayilari.most_common():
        print(f"  {format_adi:6s}: {adet} dosya")

    boyut_sayilari = Counter((k["genislik"], k["yukseklik"]) for k in bilgiler)
    print("\nBoyut dağılımı (genişlik x yükseklik):")
    for (genislik, yukseklik), adet in sorted(
        boyut_sayilari.items(), key=lambda x: (-x[1], x[0], x[1])
    ):
        print(f"  {genislik:4d} x {yukseklik:4d} : {adet} görsel")

    kisa_kenarlar = sorted(min(k["genislik"], k["yukseklik"]) for k in bilgiler)
    medyan = kisa_kenarlar[len(kisa_kenarlar) // 2]
    print(f"\nEn küçük kısa kenar: {kisa_kenarlar[0]} px | Medyan: {medyan} px")

    # -----------------------------------------------------------------------
    # 3) Çok küçük görseller: SDXL 1024px ister
    #    NEDEN uyarı: Eğitim betiği küçük görseli büyütür; büyütülmüş görsel
    #    detay taşımaz ve model "bulanık/düşük detay" üretmeyi öğrenir.
    # -----------------------------------------------------------------------
    baslik(f"3) Çok küçük görseller (kısa kenar < {KUCUK_ESIK}px)")
    kucukler = [
        k for k in bilgiler if min(k["genislik"], k["yukseklik"]) < KUCUK_ESIK
    ]
    if kucukler:
        for k in kucukler:
            print(f"  UYARI  {k['dosya']:24s} {k['genislik']} x {k['yukseklik']}")
        print(f"\n{len(kucukler)} görsel {KUCUK_ESIK}px altı. SDXL eğitiminde bu")
        print("görseller büyütülerek kullanılır; bulanıklık ve detay kaybı üretir.")
        print("Öneri: en az 1024 kısa kenarlı sürümlerle değiştirin.")
        uyarilar.append(
            f"{len(kucukler)} görselin kısa kenarı {KUCUK_ESIK}px altında (SDXL için bulanıklık riski)"
        )
    else:
        print("Uyarı yok: tüm görsellerin kısa kenarı hedefin üzerinde.")

    # -----------------------------------------------------------------------
    # 4) Birebir tekrarlar (sha1): aynı dosyanın iki kopyası
    #    NEDEN önemli: Kopya, o görselin eğitimdeki ağırlığını gizlice ikiye
    #    katlar; "20 görselim var" sanırken model 19 farklı kare görür.
    # -----------------------------------------------------------------------
    baslik("4) Birebir tekrarlar (sha1: bayt bayt aynı dosyalar)")
    sha1_gruplari: dict[str, list[str]] = {}
    for k in bilgiler:
        sha1_gruplari.setdefault(k["sha1"], []).append(k["dosya"])
    tam_tekrarlar = [grup for grup in sha1_gruplari.values() if len(grup) > 1]
    if tam_tekrarlar:
        for grup in tam_tekrarlar:
            print(f"  Grup (sha1: {grup[0][:8]}...): " + ", ".join(grup))
        fazladan = sum(len(g) - 1 for g in tam_tekrarlar)
        print(f"\n{len(tam_tekrarlar)} tekrar grubu, toplam {fazladan} fazladan kopya.")
        print("Kopyalardan birini silmek yeterlidir.")
        uyarilar.append(f"{len(tam_tekrarlar)} birebir tekrar grubu (sha1) var")
    else:
        print("Uyarı yok: birebir aynı dosya bulunamadı.")

    # -----------------------------------------------------------------------
    # 5) Yakın tekrarlar (dHash): birkaç piksel farklı, gözle "aynı" kareler
    #    NEDEN önemli: Ardışık çekilmiş kareler sha1'de farklı görünür ama
    #    eğitimde 1 görsel sayılır. NEDEN çift karşılaştırma: 15-30 görselde
    #    N² ~ 1000 karşılaştırma hiçbir şeydir; binlerce görselde LSH gerekir.
    # -----------------------------------------------------------------------
    baslik(f"5) Yakın tekrarlar (dHash Hamming mesafesi <= {YAKIN_ESIK}/64)")
    yakin_ciftler: list[tuple[str, str, int]] = []
    for i in range(len(bilgiler)):
        for j in range(i + 1, len(bilgiler)):
            a, b = bilgiler[i], bilgiler[j]
            if a["sha1"] == b["sha1"]:
                continue  # birebir kopyalar 4. bölümde listelendi, burada tekrar etmeyelim
            mesafe = hamming(a["dhash"], b["dhash"])
            if mesafe <= YAKIN_ESIK:
                yakin_ciftler.append((a["dosya"], b["dosya"], mesafe))
    if yakin_ciftler:
        for a, b, mesafe in sorted(yakin_ciftler, key=lambda x: x[2]):
            print(f"  {a:24s} <-> {b:24s} mesafe: {mesafe}/64")
        print(f"\n{len(yakin_ciftler)} çift görsel olarak neredeyse aynı. Bunlar aynı")
        print("pozu/frame'i iki kez sayar; birini eleyin. (Mesafe 0, gözle aynı")
        print("dosyaların yeniden kaydedilmiş sürümleri anlamına gelir.)")
        uyarilar.append(f"{len(yakin_ciftler)} çift neredeyse aynı görsel (dHash <= {YAKIN_ESIK})")
    else:
        print("Uyarı yok: birbirine benzer kare bulunamadı.")

    # -----------------------------------------------------------------------
    # 6) Caption denetimi: her görselin yanında AYNI ADLI .txt dosyası olmalı
    #    NEDEN uyarı: Caption'sız görsel eğitimde ya tamamen atlanır ya da boş
    #    etiketle öğrenilir; iki durumda da sessiz bir hata kaynağıdır.
    # -----------------------------------------------------------------------
    baslik("6) Caption (.txt) denetimi")
    txt_haritasi = {p.stem.casefold(): p for p in txt_yollari}
    caption_eksik = [
        k["dosya"] for k in bilgiler if Path(k["dosya"]).stem.casefold() not in txt_haritasi
    ]
    gorsel_stemleri = {Path(k["dosya"]).stem.casefold() for k in bilgiler}
    caption_fazla = [p.name for p in txt_yollari if p.stem.casefold() not in gorsel_stemleri]
    bos_captionlar = [
        p.name for p in txt_yollari
        if not p.read_text(encoding="utf-8", errors="replace").strip()
    ]
    print(f"Eşleşme kuralı: her görselin yanında AYNI ADLI .txt dosyası olmalı.")
    print(f"  Caption eksik : {len(caption_eksik)} görsel")
    for ad in caption_eksik:
        print(f"    {ad:24s} -> beklenen: {Path(ad).stem}.txt")
    print(f"  Fazla caption : {len(caption_fazla)} dosya (karşılık görsel yok)")
    for ad in caption_fazla:
        print(f"    {ad}")
    print(f"  Boş caption   : {len(bos_captionlar)} dosya")
    for ad in bos_captionlar:
        print(f"    {ad}")
    if caption_eksik:
        uyarilar.append(f"{len(caption_eksik)} görselin caption'ı eksik")
    if caption_fazla:
        uyarilar.append(f"{len(caption_fazla)} fazladan caption dosyası (görselsiz)")
    if bos_captionlar:
        uyarilar.append(f"{len(bos_captionlar)} boş caption dosyası")

    # -----------------------------------------------------------------------
    # 7) Tetikleyici kelime sayımı
    #    NEDEN: Stil/karakter öğretiminde üslup, tetikleyici kelimeye bağlanır.
    #    Kelimeyi içermeyen caption'lar modelin kafasını karıştırır: o görselde
    #    üslubu genel bilgi sanır. Her caption tetikleyiciyle başlamalıdır.
    # -----------------------------------------------------------------------
    baslik(f"7) Tetikleyici kelime denetimi: {secenekler.tetikleyici!r}")
    # Sayıma yalnızca görselle eşleşen gerçek caption'lar girer; görselsiz
    # fazla .txt dosyaları 6. bölümde zaten raporlandı ve bu oranı çarpıtmamalı.
    caption_yollari = [p for p in txt_yollari if p.stem.casefold() in gorsel_stemleri]
    tetikleyicili = 0
    toplam_gecis = 0
    tetikleyicisizler: list[str] = []
    for p in caption_yollari:
        metin = p.read_text(encoding="utf-8", errors="replace").casefold()
        gecis = metin.count(tetikleyici)
        toplam_gecis += gecis
        if gecis > 0:
            tetikleyicili += 1
        else:
            tetikleyicisizler.append(p.name)
    caption_sayisi = len(caption_yollari)
    print(f"Değerlendirilen caption     : {caption_sayisi} (görselsiz .txt'ler hariç)")
    print(f"Tetikleyici içeren caption : {tetikleyicili} / {caption_sayisi}")
    print(f"Toplam geçiş sayısı        : {toplam_gecis}")
    if tetikleyicisizler:
        print("Tetikleyici içermeyen caption'lar:")
        for ad in tetikleyicisizler:
            print(f"  UYARI  {ad}")
        print("\nBu caption'lardaki görseller üslubu kelimeye bağlamaz; eğitimden")
        print("önce tetikleyiciyi ekleyin (ör. caption başına: 'stilim, ...').")
        uyarilar.append(f"{len(tetikleyicisizler)} caption tetikleyici kelimeyi içermiyor")
    else:
        print("Uyarı yok: tüm caption'lar tetikleyici kelimeyi içeriyor.")

    # -----------------------------------------------------------------------
    # ÖZET: tek bakışta tablo + uyarı listesi
    # -----------------------------------------------------------------------
    baslik("ÖZET: Denetim sonucu")
    ozet_satirlari = [
        ("Toplam görsel dosyası", len(gorsel_yollari)),
        ("Okunamayan dosya", len(okunamayanlar)),
        (f"Kısa kenarı {KUCUK_ESIK}px altı görsel", len(kucukler)),
        ("Birebir tekrar grubu (sha1)", len(tam_tekrarlar)),
        (f"Neredeyse aynı çift (dHash <= {YAKIN_ESIK})", len(yakin_ciftler)),
        ("Caption eksik / fazla / boş", f"{len(caption_eksik)} / {len(caption_fazla)} / {len(bos_captionlar)}"),
        ("Tetikleyici içermeyen caption", len(tetikleyicisizler)),
    ]
    for etiket, deger in ozet_satirlari:
        print(f"  {etiket:38s} {deger}")

    print()
    if uyarilar:
        print("UYARILAR (eğitimden önce ele alın):")
        for uyari in uyarilar:
            print(f"  - {uyari}")
    else:
        print("Uyarı yok — veri seti eğitim için temiz görünüyor.")

    # -----------------------------------------------------------------------
    # Raporu diske yaz (JSON): sayıları başka araçlarla karşılaştırmak için
    # -----------------------------------------------------------------------
    rapor = {
        "klasor": str(klasor),
        "tetikleyici": secenekler.tetikleyici,
        "ozet": {
            "toplam_gorsel": len(gorsel_yollari),
            "okunamayan": len(okunamayanlar),
            "kucuk_gorsel": len(kucukler),
            "tam_tekrar_grup": len(tam_tekrarlar),
            "yakin_tekrar_cift": len(yakin_ciftler),
            "caption_eksik": len(caption_eksik),
            "caption_fazla": len(caption_fazla),
            "bos_caption": len(bos_captionlar),
            "tetikleyici_iceren_caption": tetikleyicili,
            "tetikleyici_toplam_gecis": toplam_gecis,
        },
        "format_dagilimi": dict(format_sayilari),
        "boyut_dagilimi": [
            {"boyut": f"{g}x{y}", "adet": adet}
            for (g, y), adet in sorted(boyut_sayilari.items(), key=lambda x: (-x[1], x[0], x[1]))
        ],
        "kucuk_gorseller": [
            {"dosya": k["dosya"], "boyut": f"{k['genislik']}x{k['yukseklik']}"} for k in kucukler
        ],
        "tam_tekrarlar": tam_tekrarlar,
        "yakin_tekrarlar": [
            {"a": a, "b": b, "hamming": mesafe} for a, b, mesafe in yakin_ciftler
        ],
        "caption_eksik": caption_eksik,
        "caption_fazla": caption_fazla,
        "bos_captionlar": bos_captionlar,
        "tetikleyici_icermeyen_captionlar": tetikleyicisizler,
        "uyarilar": uyarilar,
    }
    rapor_yolu = cikti_klasoru / "denetim-raporu.json"
    rapor_yolu.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRapor yazıldı: {rapor_yolu}")


if __name__ == "__main__":
    main()
