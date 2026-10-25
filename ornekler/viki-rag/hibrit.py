# -*- coding: utf-8 -*-
"""
Hibrit arama deneyi — viki_rag.py'nin vektör getirimine iki karşıt yöntem ekler:
sözlük araması (BM25) ve ikisinin birleşimi (RRF).

Yöntemler aynı Vikipedi korpusunda, aynı sorularla yarışır:
  vektör : bge-m3 gömme + kosinus benzerliği (viki_rag.py'nin yaptığı)
  bm25   : saf Python BM25 — k1=1,2 ve b=0,75 (Lucene'in BM25Similarity
           varsayılanları), IDF Lucene'in negatif olmayan sürümü
  hibrit : iki sıralamanın reciprocal-rank fusion birleşimi — sabit 60
           (Elasticsearch rrf retriever'ın rank_constant varsayılanı),
           her listeden ilk 20 sırada aday havuzu

Ölçülen: madde başlığına göre hit@1 / hit@4 üç soru kümesinde, tekil sorgu
gecikmesi, ve kapsam dışı sorularda her yöntemin ne yaptığı. Gömme
vektörleri cikti/vektor-indeks.json.gz önbelleğine yazılır; korpus aynı
kaldığı sürece ikinci çalıştırma vektörleştirmeyi atlar.

Gereksinim: Ollama çalışıyor + bge-m3 kurulu + internet (korpus çekişi).

Maliyet (ölçüldü, 2026-10-15, CPU): ilk çalıştırma 607 sn — 529,3 sn'si
vektörleştirme. Önbellekle ikinci çalıştırma 75 sn; sıralama tabloları
birebir aynı çıktı (yalnız gecikme ölçümü oynadı).

Kullanım:
    python hibrit.py
"""

import gzip
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from olc import KAPSAM_DISI, PARAFRAZLAR
from viki_rag import TEST_SORULARI, GOMME_MODELI, gomme, korpus_olustur, kosinus

K1, B = 1.2, 0.75      # Lucene BM25Similarity varsayılanları (son doğrulama 2026-10)
RRF_SABİT = 60         # Elasticsearch rank_constant varsayılanı
ADAY_HAVUZU = 20       # her listeden kaç sıra birleştirmeye giriyor
ÜST_K = 4              # hit@4 için bakılan bağlam boyu (viki_rag.K ile aynı)
ÖNBELLEK = Path("cikti") / "vektor-indeks.json.gz"
ÖLÇÜM_TEKRAR = 12      # gecikme ölçümünün örneklem büyüklüğü

# Sözlük aramasının avantajlı olması beklenen sorular: hedef maddede geçen somut
# bir terim içeriyorlar (özel ad, hat kodu, sayı). Üçüncü alan o terimdir; betik
# çalışırken terimin korpusta gerçekten hangi maddelerde geçtiğini de doğrular.
LEKSIK_SORULAR = [
    ("Marmaray'da batırma tüp tünel nasıl çalışır?", "Marmaray", "batırma"),
    ("Ayrılık Çeşmesi istasyonu hangi hatta?", "Marmaray", "Ayrılık Çeşmesi"),
    ("M11 hattı hangi istasyonlardan geçiyor?", "İstanbul Metrosu", "M11"),
    ("Seyrantepe'ye hangi metro hattıyla gidilir?", "İstanbul Metrosu", "Seyrantepe"),
    ("İETT hangi yıl kuruldu?", "İETT", "1869"),
    ("Vapur seferleri hangi iskeleye uğrar?", "İstanbul Deniz Otobüsleri", "vapur"),
]

HARF_DEĞİŞİM = str.maketrans({"İ": "i", "I": "ı"})
SÖZCÜK = re.compile(r"[a-zçğıöşüâîû0-9]+")


def sözcükle(metin):
    # Türkçe büyük harfler elle indirilir: str.lower() "İ" harfini "i" +
    # birleşik nokta (U+0307) yapar ve ayırıcı regex onu sözcükten koparır.
    return SÖZCÜK.findall(metin.translate(HARF_DEĞİŞİM).lower())


def bm25_indeksi(belgeler):
    belge_sözcükleri = [sözcükle(b["metin"]) for b in belgeler]
    uzunluklar = [len(s) for s in belge_sözcükleri]
    sözlükler = [Counter(s) for s in belge_sözcükleri]

    belge_sayısı = Counter()
    terim_belgeler = {}
    for sıra, sözlük in enumerate(sözlükler):
        for terim in sözlük:
            belge_sayısı[terim] += 1
            terim_belgeler.setdefault(terim, []).append(sıra)

    n = len(belgeler)
    return {
        "terim_belgeler": terim_belgeler,
        "idf": {t: math.log(1 + (n - df + 0.5) / (df + 0.5))
                for t, df in belge_sayısı.items()},
        "sözlükler": sözlükler,
        "uzunluklar": uzunluklar,
        "ortalama": sum(uzunluklar) / n,
    }


def bm25_getir(soru, indeks):
    """(puan, belge_sırası) azalan sırala; 0 puanlı belgeler listeye girmez."""
    puanlar = [0.0] * len(indeks["uzunluklar"])
    for terim in set(sözcükle(soru)):
        for sıra in indeks["terim_belgeler"].get(terim, ()):
            tf = indeks["sözlükler"][sıra][terim]
            doyma = indeks["uzunluklar"][sıra] / indeks["ortalama"]
            puanlar[sıra] += indeks["idf"][terim] * (
                tf * (K1 + 1) / (tf + K1 * (1 - B + B * doyma))
            )
    return sorted(((p, i) for i, p in enumerate(puanlar) if p > 0),
                  key=lambda çift: çift[0], reverse=True)


def vektör_getir(soru, indeks):
    soru_vektörü = gomme(soru)
    return sorted(((kosinus(soru_vektörü, v), i) for i, (_, v) in enumerate(indeks)),
                  key=lambda çift: çift[0], reverse=True)


def rrf_getir(vektör_sıralaması, bm25_sıralaması):
    """RRF puanı = sum 1/(sabit + rütbe); yalnız aday havuzları birleşir."""
    puanlar = {}
    for havuz in (vektör_sıralaması[:ADAY_HAVUZU], bm25_sıralaması[:ADAY_HAVUZU]):
        for rütbe, (_, sıra) in enumerate(havuz, 1):
            puanlar[sıra] = puanlar.get(sıra, 0.0) + 1.0 / (RRF_SABİT + rütbe)
    return sorted(((p, i) for i, p in puanlar.items()),
                  key=lambda çift: çift[0], reverse=True)


def vektör_indeksi(belgeler):
    """Gömme vektörlerini üretir ya da korpus imzası tutuyorsa önbellekten okur."""
    imza = hashlib.sha1(
        "".join(f"{b['id']}|{len(b['metin'])}" for b in belgeler).encode("utf-8")
    ).hexdigest()
    if ÖNBELLEK.exists():
        with gzip.open(ÖNBELLEK, "rt", encoding="utf-8") as dosya:
            veri = json.load(dosya)
        if veri.get("model") == GOMME_MODELI and veri.get("imza") == imza:
            print(f"[önbellek] {len(veri['vektorler'])} gömme vektörü okundu, "
                  f"vektörleştirme atlandı")
            return list(zip(belgeler, veri["vektorler"]))
        print("[önbellek] model/imza uyuşmadı — yeniden vektörleştiriliyor")

    t0 = time.time()
    vektörler = [gomme(b["metin"]) for b in belgeler]
    boyut = len(vektörler[0])
    if any(len(v) != boyut for v in vektörler):
        raise RuntimeError("gömme boyutları tutarsız — indeks bozuk")
    print(f"[indeks] {len(vektörler)} parça vektörleştirildi "
          f"({time.time() - t0:.1f} sn, boyut={boyut})")
    ÖNBELLEK.parent.mkdir(exist_ok=True)
    with gzip.open(ÖNBELLEK, "wt", encoding="utf-8") as dosya:
        json.dump({"model": GOMME_MODELI, "imza": imza, "vektorler": vektörler}, dosya)
    return list(zip(belgeler, vektörler))


def rütbe_bul(sıralama, beklenen, belgeler):
    """Beklenen maddenin ilk parçasının rütbesi (1-tabanlı).

    Listede yoksa korpus büyüklüğü + 1 döner. BM25 yalnız sözcüğü geçen
    parçaları listeler; 2 parçalık listenin 3. sırası hit@4 sayılmaz.
    """
    for rütbe, (_, sıra) in enumerate(sıralama, 1):
        if belgeler[sıra]["baslik"] == beklenen:
            return rütbe
    return len(belgeler) + 1


def kümesi_ölç(başlık, sorular, belgeler, indeks, bm25_indeks):
    print("\n" + "=" * 74)
    print(f"{başlık} — hücreler: beklenen maddenin ilk parçasının rütbesi")
    print("=" * 74)
    adlar = ("vektör", "bm25", "hibrit")
    print(f"  {'soru':<44}" + "".join(f"{a:>8}" for a in adlar))
    özet = {ad: {"hit1": 0, "hitk": 0} for ad in adlar}
    for soru, beklenen in sorular:
        v = vektör_getir(soru, indeks)
        b = bm25_getir(soru, bm25_indeks)
        hücreler = []
        for ad, sıralama in zip(adlar, (v, b, rrf_getir(v, b))):
            rütbe = rütbe_bul(sıralama, beklenen, belgeler)
            özet[ad]["hit1"] += rütbe == 1
            özet[ad]["hitk"] += rütbe <= ÜST_K
            hücreler.append(f"{rütbe:>8}")
        kısa = soru if len(soru) <= 43 else soru[:42] + "…"
        print(f"  {kısa:<44}" + "".join(hücreler))
    n = len(sorular)
    print(f"  {'':<44}{'hit@1':>9}{'hit@4':>9}")
    for ad in adlar:
        s = özet[ad]
        bir, dört = f"{s['hit1']}/{n}", f"{s['hitk']}/{n}"
        print(f"  {ad:<44}{bir:>9}{dört:>9}")
    return özet


def terimleri_doğrula(belgeler):
    print("\n" + "=" * 74)
    print("LEKSIK PROBLER — terimin korpusta geçtiği maddeler")
    print("=" * 74)
    for _, beklenen, terim in LEKSIK_SORULAR:
        geçenler = sorted({b["baslik"] for b in belgeler if terim in b["metin"]})
        ayrı = "hedef tek madde" if geçenler == [beklenen] else "birden çok madde"
        nerelerde = ", ".join(geçenler) if geçenler else "HİÇBİR YERDE"
        print(f"  '{terim}' -> {nerelerde}  ({ayrı})")


def kapsam_dışını_yorumla(sorular, belgeler, indeks, bm25_indeks):
    print("\n" + "=" * 74)
    print(f"KAPSAM DIŞI SORULAR (ilk {len(sorular)}) — sözlükte eşik kavramı yok")
    print("=" * 74)
    for soru in sorular:
        v = vektör_getir(soru, indeks)
        b = bm25_getir(soru, bm25_indeks)
        sözcükler = set(sözcükle(soru))
        tutan = [t for t in sözcükler if t in bm25_indeks["terim_belgeler"]]
        print(f"  {soru}")
        v_id = belgeler[v[0][1]]["id"]
        print(f"    vektör: en iyi benzerlik {v[0][0]:.3f} -> {v_id}")
        if b:
            print(f"    bm25  : {len(tutan)}/{len(sözcükler)} sözcük korpusta var, "
                  f"ilk sırada {belgeler[b[0][1]]['id']} (puan {b[0][0]:.2f})")
        else:
            print("    bm25  : eşleşen parça yok (sözcükler korpusta değil)")


def ana():
    print("[veri] korpus indiriliyor...")
    belgeler = korpus_olustur()
    terimleri_doğrula(belgeler)

    indeks = vektör_indeksi(belgeler)
    bm25_indeks = bm25_indeksi(belgeler)
    print(f"[bm25] {len(bm25_indeks['terim_belgeler'])} benzersiz terim, "
          f"ortalama parça {bm25_indeks['ortalama']:.0f} sözcük")

    kümeler = (
        ("ORİJİNAL SORULAR", TEST_SORULARI),
        ("PARAFRAZ SORULAR", PARAFRAZLAR),
        ("LEKSIK SORULAR", [(s, b) for s, b, _ in LEKSIK_SORULAR]),
    )
    for başlık, sorular in kümeler:
        kümesi_ölç(başlık, sorular, belgeler, indeks, bm25_indeks)

    print("\n" + "=" * 74)
    print(f"SORGU GECİKMESİ — {ÖLÇÜM_TEKRAR} deneme ortalaması "
          f"({len(TEST_SORULARI)} benzersiz soru, tekrarlı)")
    print("=" * 74)
    benzersiz = [soru for soru, _ in TEST_SORULARI]
    örnekler = (benzersiz * (1 + ÖLÇÜM_TEKRAR // len(benzersiz)))[:ÖLÇÜM_TEKRAR]
    t0 = time.perf_counter()
    for soru in örnekler:
        vektör_getir(soru, indeks)
    vektör_ort = (time.perf_counter() - t0) / len(örnekler)
    t0 = time.perf_counter()
    for soru in örnekler:
        bm25_getir(soru, bm25_indeks)
    bm25_ort = (time.perf_counter() - t0) / len(örnekler)
    print(f"  vektör (gömme çağrısı + kosinus, Ollama CPU): {vektör_ort:.3f} sn")
    print(f"  bm25   (saf Python, bellek içi indeks):       {bm25_ort:.4f} sn")

    kapsam_dışını_yorumla(KAPSAM_DISI[:4], belgeler, indeks, bm25_indeks)


if __name__ == "__main__":
    ana()
