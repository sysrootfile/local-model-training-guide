# -*- coding: utf-8 -*-
"""
Örnek 6 ölçümü — viki_rag.py sisteminin eşik bantlarını GERÇEKTEN ölçer.

rag.py tarafındaki olc.py'nin (Örnek 5) büyük korpus karşılığı:
  1. Parafraz sağlamlığı: 6 orijinal soru + 6 farklı ifade (hit@1, MRR)
  2. Kapsam içi benzerlik bandı: her kapsam içi sorunun EN İYİ benzerliği
  3. Kapsam dışı benzerlik bandı: 8 alakasız sorunun en iyi benzerliği
  4. Ayırma payı ve eşik önerisi: viki_rag.py'deki ZAYIF_ESIK'nin bu korpusta
     geçerli olup olmadığı ölçülür (devralınan eşik testi)
  5. Model karşılaştırması: bge-m3 vs nomic-embed-text (aynı 125 parça)

UYARI (maliyet): korpus 125 parça — indeksleme CPU'da model başına dakikalar sürer.
Ölçüldü (aynı korpus, aynı makine, tek fark adres):
  - 2026-10-15, http://localhost : bge-m3 495,7 sn + nomic-embed-text 503,7 sn (~17 dk)
  - 2026-10-16, http://127.0.0.1 : bge-m3 259,2 sn + nomic-embed-text 158,6 sn (~7 dk)
Windows'ta "localhost" adının çözülmesi istek başına ~2 sn; 125 istek = ~250 sn.
Tek model için --model kullanın.

Gereksinim: Ollama + viki_rag.py ile aynı modeller; nomic deneyi için
    ollama pull nomic-embed-text

Kullanım:
    python olc.py                     # iki modeli de ölç (korpus bir kez indirilir)
    python olc.py --model bge-m3      # tek model (daha hızlı)
"""

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# viki_rag.py ile tek doğruluk kaynağı: aynı korpus tanımı ve aynı sorular
from viki_rag import korpus_olustur, TEST_SORULARI

_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


# Windows'ta "localhost" ad çözümlemesi istek başına ~2 sn ekliyor (ölçüldü: 2,03 sn).
OLLAMA = _url_dogrula("http://127.0.0.1:11434")
VARSAYILAN_MODELLER = ["bge-m3", "nomic-embed-text"]
# viki_rag.py'nin Örnek 5'ten devraldığı değer; bilerek sabit bırakıldı, böylece
# ölçüm "devralınan eşik bu korpusta geçerli mi?" sorusunu yanıtlıyor.
# Ölçüm (2026-10-15, bge-m3): 0,35 kapsam dışı bandının İÇİNDEN geçiyor -> geçersiz;
# önerilen 0,541 ve viki_rag.py o tarihte 0,54'e çekildi. nomic-embed-text'te bantlar
# çakıştığı için (ayırma -0,112) hiçbir eşik "bilmiyor" davranışı üretemez.
MEVCUT_ESIK = 0.35

# Orijinal 6 sorunun farklı ifade edilmiş hâlleri (beklenen: madde başlığı)
PARAFRAZLAR = [
    ("Marmaray servise ne zaman girdi?", "Marmaray"),
    ("Tünel füniküleri hangi iki istasyonu birbirine bağlıyor?", "Tünel (İstanbul)"),
    ("Metrobüs hattı nereden nereye gidiyor?", "Metrobüs"),
    ("İETT'nin kuruluş yılı hangisidir?", "İETT"),
    ("İstanbul metrosundaki en eski hat hangisi?", "İstanbul Metrosu"),
    ("T1 tramvay hattı hangi duraklardan geçiyor?", "T1 (İstanbul Tramvayı)"),
]

# Korpusla ilgisi olmayan sorular — bazıları kasıtlı tuzak: "İstanbul" kelimesi
# geçebilir ama konu ulaşım değil.
KAPSAM_DISI = [
    "Evde pizza hamuru nasıl yapılır?",
    "Ankara'da hangi müzeler gezilir?",
    "Türkiye'nin en uzun nehri hangisidir?",
    "Kedi yavrusu bakımı için nelere dikkat edilmeli?",
    "İstanbul'da nerede ucuz otel bulunur?",
    "Borsa İstanbul'dan hisse senedi nasıl alınır?",
    "Otomobil motor yağı ne zaman değiştirilir?",
    "Galatasaray kulübü kaç yılında kuruldu?",
]


def gomme(metin, model):
    istek = urllib.request.Request(
        _url_dogrula(f"{OLLAMA}/api/embeddings"),
        data=json.dumps({"model": model, "prompt": metin}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(istek, timeout=300) as yanıt:
        return json.loads(yanıt.read().decode("utf-8"))["embedding"]


def kosinus(a, b):
    iç_çarpım = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return iç_çarpım / (norm_a * norm_b)


def tam_siralama(soru, indeks):
    soru_v = gomme(soru, indeks["model"])
    return sorted(
        ((kosinus(soru_v, v), b["baslik"]) for b, v in indeks["parcalar"]),
        key=lambda c: c[0],
        reverse=True,
    )


def indeks_olustur(model, belgeler):
    t0 = time.time()
    parcalar = []
    for sıra, b in enumerate(belgeler, 1):
        parcalar.append((b, gomme(b["metin"], model)))
        if sıra % 25 == 0:
            print(f"  [{model}] indeks {sıra}/{len(belgeler)}...")
    print(f"  [{model}] indeks: {len(parcalar)} parça, boyut={len(parcalar[0][1])}, "
          f"{time.time() - t0:.1f} sn")
    return {"model": model, "parcalar": parcalar}


def metrikleri_olc(sorular, indeks):
    """Beklenen = madde başlığı; sıralama, o maddeden İLK parçanın sırasıdır."""
    hit1 = 0
    mrr = 0.0
    en_iyi_benzerlikler = []
    for soru, beklenen in sorular:
        skorlar = tam_siralama(soru, indeks)
        sıralama = [b for _, b in skorlar]
        r = sıralama.index(beklenen) + 1
        hit1 += r == 1
        mrr += 1.0 / r
        en_iyi_benzerlikler.append(skorlar[0][0])
    n = len(sorular)
    return {
        "n": n,
        "hit@1": hit1 / n,
        "mrr": mrr / n,
        "benzerlik_min": min(en_iyi_benzerlikler),
        "benzerlik_max": max(en_iyi_benzerlikler),
    }


def kapsam_disi_olc(indeks):
    return [(soru, tam_siralama(soru, indeks)[0][0]) for soru in KAPSAM_DISI]


def model_deneyi(model, belgeler):
    print("\n" + "=" * 62)
    print(f"MODEL: {model}")
    print("=" * 62)
    indeks = indeks_olustur(model, belgeler)

    orijinal = metrikleri_olc(TEST_SORULARI, indeks)
    print(f"\n  Orijinal sorular  : hit@1={orijinal['hit@1']:.2f}  "
          f"MRR={orijinal['mrr']:.3f}  (n={orijinal['n']})")
    print(f"  kapsam içi bandı  : {orijinal['benzerlik_min']:.3f} - "
          f"{orijinal['benzerlik_max']:.3f}")

    parafraz = metrikleri_olc(PARAFRAZLAR, indeks)
    print(f"  Parafraz sorular  : hit@1={parafraz['hit@1']:.2f}  "
          f"MRR={parafraz['mrr']:.3f}  (n={parafraz['n']})")
    print(f"  kapsam içi bandı  : {parafraz['benzerlik_min']:.3f} - "
          f"{parafraz['benzerlik_max']:.3f}")

    for soru, beklenen in PARAFRAZLAR:
        sıralama = [b for _, b in tam_siralama(soru, indeks)]
        if sıralama[0] != beklenen:
            print(f"  [MISS] '{soru}' -> beklenen {beklenen}, ilk sırada {sıralama[0]}")

    kapsam_disi = kapsam_disi_olc(indeks)
    degerler = [d for _, d in kapsam_disi]
    print(f"\n  Kapsam dışı (n={len(kapsam_disi)}) en iyi benzerlikler:")
    for soru, skor in kapsam_disi:
        print(f"    {skor:.3f}  {soru}")
    print(f"  kapsam dışı bandı : {min(degerler):.3f} - {max(degerler):.3f}")

    en_dusuk_ici = min(orijinal["benzerlik_min"], parafraz["benzerlik_min"])
    en_yuksek_disi = max(degerler)
    ayırma = en_dusuk_ici - en_yuksek_disi
    print(f"  ayırma payı       : {ayırma:+.3f} "
          f"(en düşük kapsam içi {en_dusuk_ici:.3f} eksi en yüksek kapsam dışı {en_yuksek_disi:.3f})")
    if ayırma > 0:
        öneri = (en_dusuk_ici + en_yuksek_disi) / 2
        print(f"  eşik önerisi      : {öneri:.3f} (bantların ortası)")
        if MEVCUT_ESIK < en_yuksek_disi or MEVCUT_ESIK > en_dusuk_ici:
            print(f"  [UYARI] devralınan eşik {MEVCUT_ESIK} bantların DIŞINDA — bu korpusta geçersiz!")
        else:
            print(f"  devralınan eşik {MEVCUT_ESIK} bantlar arasında — bu korpusta geçerli.")
    else:
        print("  eşik önerisi      : YOK — bantlar çakışıyor, hiçbir eşik 'bilmiyor' davranışı üretemez.")
        öneri = None

    return {"model": model, "orijinal": orijinal, "parafraz": parafraz,
            "kapsam_disi": degerler, "ayırma": ayırma, "eşik_önerisi": öneri}


def ana():
    ayrıştırıcı = argparse.ArgumentParser(description="Örnek 6 eşik/parafraz ölçümü (viki korpusu)")
    ayrıştırıcı.add_argument("--model", action="append", dest="modeller",
                             help="ölçülecek embedding modeli (birden çok verilebilir)")
    argümanlar = ayrıştırıcı.parse_args()
    modeller = argümanlar.modeller or VARSAYILAN_MODELLER

    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=10) as yanıt:
            kurulu = {m["name"].split(":")[0] for m in json.loads(yanıt.read())["models"]}
    except (urllib.error.URLError, ConnectionError):
        sys.exit("HATA: Ollama sunucusuna ulaşılamadı. Önce Ollama'yı baştırın.")
    eksik = [m for m in modeller if m.split(":")[0] not in kurulu]
    if eksik:
        print(f"UYARI: {', '.join(eksik)} kurulu değil; deney atlanıyor "
              f"(kurmak: ollama pull {eksik[0]})")
        modeller = [m for m in modeller if m not in eksik]
    if not modeller:
        sys.exit("Ölçülecek model kalmadı.")

    print(f"[veri] korpus Vikipedi'den indiriliyor (tek sefer, {len(modeller)} model paylaşacak)...")
    belgeler = korpus_olustur()

    sonuçlar = [model_deneyi(m, belgeler) for m in modeller]

    if len(sonuçlar) > 1:
        print("\n" + "=" * 62)
        print("KARŞILAŞTIRMA ÖZETİ (125 parçalık Vikipedi korpusu)")
        print("=" * 62)
        print(f"  {'model':<20} {'hit@1(ory)':<12} {'hit@1(para)':<13} {'MRR(para)':<11} ayırma")
        for s in sonuçlar:
            print(f"  {s['model']:<20} {s['orijinal']['hit@1']:<12.2f} "
                  f"{s['parafraz']['hit@1']:<13.2f} {s['parafraz']['mrr']:<11.3f} "
                  f"{s['ayırma']:+.3f}")


if __name__ == "__main__":
    ana()
