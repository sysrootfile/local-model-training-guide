#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kişisel veri tarayıcısının denetimi: Örnek 2'deki maskeleyici (`atolye.py`) gerçekten neyi görüyor?

Üç kol:
  A) Kalibrasyon — elle yazılmış, üç türlüsüyle etiketli sentetik Türkçe vakalar:
       POZİTİF  : kişisel veri ve araç onu görmeli
       KUYRUK   : kişisel veri DEĞİL; araç onu işaretlememeli (yanlış pozitif ölçümü)
       KÖR NOKTA: kişisel veri AMA aracın kapsamı dışında (ölçülen eksik, başarı değil)
  B) Depo taraması — bu sitede yayında olan sayfalar + örnek veri kütlevi + koşum günlükleri
     üzerinden kategori bazlı vuruş sayısı; "yalın regex" ile "sağlamalı regex" farkı.
  C) Agresif normalizasyonun faturası — ayraçları (boşluk/nokta/tire/parantez) silip rakamları
     birleştirince kaç yeni vuruş geliyor, kaç yeni YANLIŞ pozitif geliyor.

Çıkarım isteği YOKTUR; ağ erişimi YOKTUR. Rastgelelik tohumu: 20261017.
Koşum:  PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u pii_denetim.py --kol hepsi > cikti/pii-kaydi.txt 2>&1
"""

from __future__ import annotations

import argparse
import importlib.util
import random
import re
import sys
import time
from pathlib import Path

DEPO = Path(__file__).resolve().parents[2]
TOHUM = 20261017
IBAN_GOVDE = "0001234567890123456789"  # 22 hane: banka 5 + şube 1 + hesap 16


def atolye_yukle():
    """Örnek 2'nin temizlik modülünü oldugu yerden yükle: denetlenen şey sitede öğretilen araçtır."""
    yol = DEPO / "ornekler" / "veri-temizleme" / "atolye.py"
    spec = importlib.util.spec_from_file_location("atolye", yol)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


A = atolye_yukle()

# ---------------------------------------------------------------------------
# Sağlama doğrulayıcıları (deneyim için kendi kolumuz; maskeleyicide bunlar YOK)
# ---------------------------------------------------------------------------


def tckn_uret(rng: random.Random) -> str:
    """Sağlaması tutan 11 haneli kimlik numarası üret (ilk hane sıfır olamaz)."""
    while True:
        govde = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
        tek = govde[0] + govde[2] + govde[4] + govde[6] + govde[8]
        cift = govde[1] + govde[3] + govde[5] + govde[7]
        govde.append((tek * 7 - cift) % 10)
        govde.append(sum(govde) % 10)
        aday = "".join(str(h) for h in govde)
        if A.tckn_gecerli_mi(aday):
            return aday


def iban_mod97_gecerli_mi(iban: str) -> bool:
    rakamli = re.sub(r"\s+", "", iban).upper()
    if not re.fullmatch(r"TR\d{24}", rakamli):
        return False
    # gövde + "TR"->2927 + kontrol hanesi; mod 97 = 1 olmalı
    tas = rakamli[4:] + "2927" + rakamli[2:4]
    return int(tas) % 97 == 1


def iban_uret(govde: str) -> str:
    """TR + 2 kontrol hanesi + 22 hane gövde; kontrol hanesini mod-97'den hesapla."""
    assert len(govde) == 22 and govde.isdigit(), "IBAN gövdesi 22 haneli olmalı"
    kontrol = 98 - int(govde + "292700") % 97
    assert 2 <= kontrol <= 98, "bu gövde için kontrol hanesi üretilmedi"
    return f"TR{kontrol:02d}{govde}"


# ---------------------------------------------------------------------------
# KOL A — kalibrasyon
# ---------------------------------------------------------------------------

TURLER = ("POZİTİF", "KUYRUK", "KÖR NOKTA")


def vakalar() -> list[dict]:
    # Mimosa "guvensiz rastgelelik" der; bilerek: tohumlu test vakasi uretimi,
    # kripto degil — ayni tohum ayni vakalari verir, denetim tekrarlanir.
    rng = random.Random(TOHUM)
    gecerli1, gecerli2 = tckn_uret(rng), tckn_uret(rng)
    bozuk = None
    for i in range(11):  # tek hane kaydırarak sağlama düşüren bir varyant bul
        aday = gecerli1[:i] + str((int(gecerli1[i]) + 1) % 10) + gecerli1[i + 1 :]
        if not A.tckn_gecerli_mi(aday):
            bozuk = aday
            break
    assert bozuk, "bozuk varyant üretilemedi"
    iban_dogru = iban_uret(IBAN_GOVDE)

    v: list[dict] = []

    def ekle(tur: str, kategori: str, metin: str, aciklama: str) -> None:
        v.append(dict(tur=tur, kategori=kategori, metin=metin, aciklama=aciklama))

    # --- TCKN ---
    ekle("POZİTİF", "tckn", f"Müşteri kaydımızda {gecerli1} numarası ile açılmış bir dosya var.", "sağlaması tutan kimlik no")
    ekle("POZİTİF", "tckn", f"Kimlik: {gecerli2}, kayıt tarihi 12.03.2024", "ikinci geçerli, noktalı bağlam")
    ekle("KUYRUK", "tckn", f"Sipariş numarası {bozuk} olarak geçiyor.", "geçerlinin tek hanesi kaydırıldı -> sağlama düşer")
    ekle("KUYRUK", "tckn", "Referans 01234567890 (başında sıfır).", "sıfırla başlayan 11 hane")
    ekle("KUYRUK", "tckn", "Kargo takip kodu 12345678901 ve 98765432109.", "şans eseri yazılmış 11 hanelik diziler")
    ekle("KÖR NOKTA", "tckn", f"Kimlik no: {gecerli1[:3]} {gecerli1[3:6]} {gecerli1[6:9]} {gecerli1[9:]} (boşluklu yazılmış).", "ayraç gruplu geçerli kimlik no")
    ekle("KÖR NOKTA", "tckn", f"TC: {gecerli2[:2]}.{gecerli2[2:5]}.{gecerli2[5:8]}.{gecerli2[8:]} noktalı biçim.", "nokta gruplu geçerli kimlik no")
    # --- e-posta ---
    ekle("POZİTİF", "eposta", "Bize veli.yilmaz@ornek.org adresinden yazın.", "klasik")
    ekle("POZİTİF", "eposta", "Yedek: VELI.YILMAZ@ORNEK.ORG", "büyük harf")
    ekle("POZİTİF", "eposta", "Filtreli hesap: veli+liste@alt-alan.com.tr", "artı etiketi, çok noktalı alan adı")
    ekle("POZİTİF", "eposta", 'İletişim: <a href="mailto:veli@ornek.org">veli@ornek.org</a>', "HTML mailto bağlantısı")
    ekle("KUYRUK", "eposta", "Kullanıcı adı veli olarak kayıtlı.", "et içermeyen düz ad")
    ekle("KÖR NOKTA", "eposta", "E-posta: veli (at) ornek nokta org", "sözcükle obfuscate edilmiş")
    # --- telefon ---
    ekle("POZİTİF", "telefon", "Cep: 0532 123 45 67", "başında sıfır, boşluklu")
    ekle("POZİTİF", "telefon", "+90 532 123 45 67", "ülke kodlu")
    ekle("POZİTİF", "telefon", "(0212) 345-67-89", "sabit hat, parantez+tire")
    ekle("POZİTİF", "telefon", "5321234567", "boşluksuz, sıfırsız")
    ekle("KUYRUK", "telefon", "Sürüm 5.32.123 yayımlandı.", "sürüm numarası")
    ekle("KUYRUK", "telefon", "Konteyner 53212345678901 numaralı limanda.", "14 hanelik dizi (iki koşut alan adı)")
    ekle("KUYRUK", "telefon", "Tel: 0532 123 456", "tek grup eksik yazılmış (10 değil 9 hane)")
    ekle("KÖR NOKTA", "telefon", "Cep: 0 532 12 34 56 7 (ikişerli gruplama).", "ikişerli gruplı numara")
    # --- IBAN ---
    ekle("POZİTİF", "iban", f"Hesabımız {iban_dogru}", "mod-97 tutan IBAN")
    ekle("POZİTİF", "iban", "EFT için TR33 0001 0001 2345 6789 0123 45", "boşluklu; mod-97 tutmasa da biçim IBAN")
    ekle("KUYRUK", "iban", "TR99 kısa kodu", "IBAN biçimi olmayan TR + 2 hane")
    ekle("KUYRUK", "iban", "Fatura tanım dizisi TR111111111111111111111111 (IBAN değil).", "TR + 24 özdeş hane")
    # --- yapısız kişisel veri: aracın kapsamı dışındaki KVKK maddeleri ---
    ekle("KÖR NOKTA", "ad-soyad", "Fatih Mah. Çukurçeşme Sok. No 12/3, Kadıköy/İstanbul — Veli Yılmaz", "adres + ad soyad")
    ekle("KÖR NOKTA", "dogum-tarihi", "Doğum tarihi: 01.02.1990, doğum yeri Sivas.", "doğum tarihi")
    ekle("KÖR NOKTA", "konum", "Depo koordinatı 41.0082, 28.9784", "GPS koordinatı")
    ekle("KÖR NOKTA", "plaka", "Araç 34 ABC 123 plakalı.", "plaka")
    ekle("KÖR NOKTA", "saglik", "Epicrisis: hastada tip 2 diabetes mellitus ve hipertansiyon var.", "sağlık bilgisi (özel nitelikli veri)")
    return v


def kategori_vuruslari(metin: str) -> dict[str, list[str]]:
    sonuc: dict[str, list[str]] = {}
    saglamali = [a.group(0) for a in A.TCKN_ADAY_RE.finditer(metin) if A.tckn_gecerli_mi(a.group(0))]
    if saglamali:
        sonuc["tckn"] = saglamali
    for anahtar, regex in (("eposta", A.EPOSTA_RE), ("telefon", A.TELEFON_RE), ("iban", A.IBAN_RE)):
        bulunan = [m.group(0) for m in regex.finditer(metin)]
        if bulunan:
            sonuc[anahtar] = bulunan
    return sonuc


SONUC_ETIKETLERI = ("yakalandı", "KAPSAM İÇİ KAÇIRILDI", "yanlış pozitif", "doğru red", "kapsam dışı (kabul)", "sürpriz vuruş")


def siniflandir(vaka: dict) -> str:
    bulundu = bool(kategori_vuruslari(vaka["metin"]).get(vaka["kategori"]))
    if vaka["tur"] == "POZİTİF":
        return "yakalandı" if bulundu else "KAPSAM İÇİ KAÇIRILDI"
    if vaka["tur"] == "KUYRUK":
        return "yanlış pozitif" if bulundu else "doğru red"
    return "sürpriz vuruş" if bulundu else "kapsam dışı (kabul)"


def kol_a() -> None:
    print("=" * 78)
    print("KOL A: KALİBRASYON KÜMESİ (sentetik, elle etiketli)")
    print("=" * 78)
    v = vakalar()
    print(f"vaka sayısı: {len(v)}   tohum={TOHUM}")
    print(f"tur dağılımı: " + ", ".join(f"{t}={sum(1 for x in v if x['tur'] == t)}" for t in TURLER))
    sayim: dict[str, int] = {etiket: 0 for etiket in SONUC_ETIKETLERI}
    for i, vaka in enumerate(v, 1):
        etiket = siniflandir(vaka)
        sayim[etiket] += 1
        tumaden = kategori_vuruslari(vaka["metin"])
        print(f"\n[{i:02d}] {vaka['tur']:11s} {vaka['kategori']:13s} -> {etiket}")
        print(f"     {vaka['aciklama']}")
        if tumaden:
            print(f"     vuruşlar: { {k: d for k, d in tumaden.items()} }")
    print("\n--- özet ---")
    for etiket, adet in sayim.items():
        print(f"{etiket:24s} {adet}")
    pozitif = sum(1 for x in v if x["tur"] == "POZİTİF")
    kuyruk = sum(1 for x in v if x["tur"] == "KUYRUK")
    kor = sum(1 for x in v if x["tur"] == "KÖR NOKTA")
    print(f"\ntutma (recall, kapsam içi) : {sayim['yakalandı']}/{pozitif} = {sayim['yakalandı'] / pozitif:.2f}")
    print(f"yanlış pozitif              : {sayim['yanlış pozitif']}/{kuyruk} kuyruk vakası işaretlendi")
    print(f"kapsam dışı kişisel veri  : {sayim['kapsam dışı (kabul)']}/{kor} kaçırıldı (tarayıcının gördüğü dilim bu)")

    print("\n--- biçim mi, geçerlilik mi? ---")
    dogru = iban_uret(IBAN_GOVDE)
    ekli = "TR" + f"{(int(dogru[2:4]) + 1) % 100:02d}" + dogru[4:]
    print(f"IBAN mod-97 tutan    : {dogru}  -> sağlayıcı: {iban_mod97_gecerli_mi(dogru)}")
    print(f"IBAN mod-97 tutmayan : {ekli}  -> sağlayıcı: {iban_mod97_gecerli_mi(ekli)}")
    print(f"maskeleyici ikisini de IBAN sayıyor mu: {bool(A.IBAN_RE.findall(dogru)) and bool(A.IBAN_RE.findall(ekli))}")
    sahte = "TR111111111111111111111111"
    print(f"IBAN biçimli sahte dizi {sahte}: maskeleyici VURUYOR, mod-97 {iban_mod97_gecerli_mi(sahte)}")
    aday = re.search(A.TCKN_ADAY_RE, "Sipariş numarası 12345678901").group(0)
    print(f"11 haneli rakam dizisi {aday}: yalın regex VURUYOR, sağlama {A.tckn_gecerli_mi(aday)}")
    vuruslar = [x for x in v if x["tur"] == "POZİTİF"]
    maskelenmis, adet = A.pii_maskele("\n".join(x["metin"] for x in vuruslar))
    print(f"pozitiflerin hepsi tek geçişte: {adet} maske")
    print(f"maske örneği: {maskelenmis.splitlines()[0][:90]}")


# ---------------------------------------------------------------------------
# KOL B — depo taraması
# ---------------------------------------------------------------------------

HEDEF_GRUPLARI = {
    "yayındaki sayfalar": sorted((DEPO / "src" / "content" / "docs").rglob("*.md")) + sorted((DEPO / "src" / "content" / "docs").rglob("*.mdx")),
    "örnek veri kümeleri": [
        DEPO / "ornekler" / "turkce-asistan" / "cikti" / "egitim.jsonl",
        DEPO / "ornekler" / "turkce-asistan" / "cikti" / "test.jsonl",
        DEPO / "ornekler" / "veri-temizleme" / "cikti" / "temiz_veri.jsonl",
    ],
    "koşum günlükleri": sorted((DEPO / "ornekler").glob("*/cikti/*.txt")),
    "betikler ve README": sorted((DEPO / "ornekler").glob("*/*.py")) + sorted((DEPO / "ornekler").glob("*/README.md")),
}


def dosyalari(grup: str) -> list[Path]:
    # Denetimin kendi çıktıları sentetik kişisel veri taşır; hem kendini hem yarım yazılmış
    # bu logu saymasın diye bu klasörün cikti/ dizisi taramanın dışındadır.
    oz = (DEPO / "ornekler" / "lisans-ve-gizlilik" / "cikti").resolve()
    return [
        y
        for y in HEDEF_GRUPLARI[grup]
        if "__pycache__" not in str(y) and y.exists() and oz not in y.resolve().parents
    ]


def grup_say(grup: str, temizleme=None) -> tuple[dict, dict]:
    g = {"dosya": 0, "karakter": 0, "tckn_aday": 0, "tckn_gecerli": 0, "eposta": 0, "telefon": 0, "iban": 0, "iban_mod97": 0}
    ornekler: dict[str, list[str]] = {k: [] for k in ("tckn_gecerli", "eposta", "telefon", "iban", "iban_mod97")}
    for yol in dosyalari(grup):
        metin = yol.read_text(encoding="utf-8", errors="replace")
        if temizleme is not None:
            metin = temizleme(metin)
        g["dosya"] += 1
        g["karakter"] += len(metin)
        adaylar = [m.group(0) for m in A.TCKN_ADAY_RE.finditer(metin)]
        g["tckn_aday"] += len(adaylar)
        for a in adaylar:
            if A.tckn_gecerli_mi(a):
                g["tckn_gecerli"] += 1
                if len(ornekler["tckn_gecerli"]) < 6:
                    ornekler["tckn_gecerli"].append(f"{yol.name}: {a}")
        for anahtar, regex in (("eposta", A.EPOSTA_RE), ("telefon", A.TELEFON_RE), ("iban", A.IBAN_RE)):
            bulunan = [m.group(0) for m in regex.finditer(metin)]
            g[anahtar] += len(bulunan)
            for b in bulunan[:3]:
                if len(ornekler[anahtar]) < 9:
                    ornekler[anahtar].append(f"{yol.name}: {b}")
            if anahtar == "iban":
                for iban in bulunan:
                    if iban_mod97_gecerli_mi(iban):
                        g["iban_mod97"] += 1
                        if len(ornekler["iban_mod97"]) < 4:
                            ornekler["iban_mod97"].append(f"{yol.name}: {iban}")
    return g, ornekler


def kol_b() -> None:
    print("=" * 78)
    print("KOL B: DEPO TARAMASI (bu sitenin kendi yayınları + örnek kütlevi)")
    print("=" * 78)
    basla = time.perf_counter()
    satir_basligi = f"{'grup':22s} {'dosya':>6s} {'karakter':>11s} {'TCKN-aday':>10s} {'TCKN-geçerli':>13s} {'e-posta':>8s} {'telefon':>8s} {'IBAN':>5s} {'IBAN-mod97':>11s}"
    print(satir_basligi)
    toplanan = dict.fromkeys(("dosya", "karakter", "tckn_aday", "tckn_gecerli", "eposta", "telefon", "iban", "iban_mod97"), 0)
    ornek_topla: dict[str, list[str]] = {}
    for grup in HEDEF_GRUPLARI:
        g, ornekler = grup_say(grup)
        for anahtar, adet in g.items():
            toplanan[anahtar] += adet
        for anahtar, liste in ornekler.items():
            ornek_topla.setdefault(anahtar, []).extend(liste)
        print(
            f"{grup:22s} {g['dosya']:6d} {g['karakter']:11d} {g['tckn_aday']:10d} {g['tckn_gecerli']:13d} "
            f"{g['eposta']:8d} {g['telefon']:8d} {g['iban']:5d} {g['iban_mod97']:11d}"
        )
    sure = time.perf_counter() - basla
    print(
        f"{'TOPLAM':22s} {toplanan['dosya']:6d} {toplanan['karakter']:11d} {toplanan['tckn_aday']:10d} "
        f"{toplanan['tckn_gecerli']:13d} {toplanan['eposta']:8d} {toplanan['telefon']:8d} {toplanan['iban']:5d} "
        f"{toplanan['iban_mod97']:11d}"
    )
    print(f"koşum süresi: {sure:.2f} sn (tek süreç, CPU)")
    oran = toplanan["tckn_gecerli"] / toplanan["tckn_aday"] if toplanan["tckn_aday"] else 0
    print(f"11 haneli rakam dizilerinin sağlama tutan oranı: {toplanan['tckn_gecerli']}/{toplanan['tckn_aday']} = {oran:.3f}"
          f"  -> yalın '\\d{{11}}' kullansaydık {toplanan['tckn_aday'] - toplanan['tckn_gecerli']} yanlış maske")
    print("\n--- vuruş örnekleri ---")
    for anahtar, liste in ornek_topla.items():
        print(f"{anahtar}: {len(liste)} örnek")
        for o in liste[:7]:
            print(f"   - {o[:120]}")

    print("\n--- örnek veri kümelerinde dosya bazında döküm ---")
    for yol in dosyalari("örnek veri kümeleri"):
        metin = yol.read_text(encoding="utf-8", errors="replace")
        adaylar = [m.group(0) for m in A.TCKN_ADAY_RE.finditer(metin)]
        gecerli = sum(1 for a in adaylar if A.tckn_gecerli_mi(a))
        maske_token = sum(metin.count(t) for t in ("[E-POSTA]", "[TELEFON]", "[TC-KIMLIK]", "[IBAN]"))
        print(
            f"  {yol.name:22s} karakter {len(metin):9d}  e-posta {len(A.EPOSTA_RE.findall(metin)):4d}"
            f"  telefon {len(A.TELEFON_RE.findall(metin)):3d}  IBAN {len(A.IBAN_RE.findall(metin)):2d}"
            f"  TCKN-aday {len(adaylar):3d}  geçerli {gecerli:2d}  hazır-maske-token {maske_token}"
        )

    print("\n--- yayındaki sayfalarda en çok vuruş ---")
    vuruslar = []
    for yol in dosyalari("yayındaki sayfalar"):
        metin = yol.read_text(encoding="utf-8", errors="replace")
        adet = len(A.EPOSTA_RE.findall(metin)) + len(A.TELEFON_RE.findall(metin)) + len(A.IBAN_RE.findall(metin))
        tckn = sum(1 for m in A.TCKN_ADAY_RE.finditer(metin) if A.tckn_gecerli_mi(m.group(0)))
        vuruslar.append((adet, tckn, str(yol.relative_to(DEPO))))
    vuruslar.sort(reverse=True)
    for adet, tckn, yol in vuruslar[:8]:
        print(f"  biçim:{adet:4d}  geçerli-TCKN:{tckn:3d}  {yol}")
    print(f"  ... {sum(1 for a, _, _ in vuruslar if a == 0)}/{len(vuruslar)} sayfada sıfır biçim vuruşu")


# ---------------------------------------------------------------------------
# KOL C — agresif normalizasyon
# ---------------------------------------------------------------------------

def butunlestir(metin: str) -> str:
    """Rakam gruplarının ayraçlarını siler: '123 456 789 01' -> '12345678901'."""
    return re.sub(r"(?<=\d)[ .\-](?=\d)", "", metin)


def kol_c() -> None:
    print("=" * 78)
    print("KOL C: AGRESİF NORMALİZASYONUN FATURASI (ayraç silme)")
    print("=" * 78)
    v = vakalar()
    kor = [x for x in v if x["tur"] == "KÖR NOKTA"]
    print("kalibrasyondaki kör noktalar ayraç silinince:")
    for vaka in kor:
        onceki = kategori_vuruslari(vaka["metin"])
        sonraki = kategori_vuruslari(butunlestir(vaka["metin"]))
        kazanc = sorted(set(sonraki) - set(onceki))
        print(f"  - {vaka['kategori']:13s} {vaka['aciklama'][:44]:46s} -> {sonraki if kazanc else 'yine yok'}")

    print("\ndeponun tümünde ayraç silme öncesi/sonrası:")
    basla = time.perf_counter()
    fark = {}
    for grup in HEDEF_GRUPLARI:
        once, _ = grup_say(grup)
        sonra, _ = grup_say(grup, temizleme=butunlestir)
        fark[grup] = (once, sonra)
        print(
            f"  {grup:22s} TCKN-aday {once['tckn_aday']:5d} -> {sonra['tckn_aday']:5d}"
            f"   |  geçerli TCKN {once['tckn_gecerli']:3d} -> {sonra['tckn_gecerli']:3d}"
            f"   | telefon {once['telefon']:5d} -> {sonra['telefon']:5d}"
            f"   | IBAN {once['iban']:3d} -> {sonra['iban']:3d}"
            f"   | mod97 {once['iban_mod97']:3d} -> {sonra['iban_mod97']:3d}"
        )
    print(f"koşum süresi: {time.perf_counter() - basla:.2f} sn")
    print(
        "\nyorum: ayraç silme bitişik-hane kuralını gevşetir; kazandığı her gerçek vuruş için"
        " arka planda birleşen rakam dizileri kadar da YENİ ADAY üretir. Aday artışı sağlama"
        " filtresiyle bastırılabilir, telefon/IBAN artışı bastırılamaz."
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kol", choices=["a", "b", "c", "hepsi"], default="hepsi")
    args = ap.parse_args()
    print(f"koşum başlangıcı: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("denetlenen araç: ornekler/veri-temizleme/atolye.py içindeki pii_maskele + regex sabitleri")
    print("tarama maskesiz yapılır (neyi gördüğü sayılır); maskeleme ayrı bir geçişte denenir\n")
    if args.kol in ("a", "hepsi"):
        kol_a()
        print()
    if args.kol in ("b", "hepsi"):
        kol_b()
        print()
    if args.kol in ("c", "hepsi"):
        kol_c()
    print(f"\nkoşum bitişi: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    sys.exit(main())
