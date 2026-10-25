# -*- coding: utf-8 -*-
"""
RAG değerlendirme ölçümleri — rag.py'in test çerçevesini genişletir.

Deneyler (hepsi aynı korpus ve Ollama üzerinde):
  1. Parafraz sağlamlığı: aynı 6 sorunun farklı ifade edilmiş hâlleri
  2. Kapsam dışı benzerlik dağılımı: 5 alakasız sorunun en iyi benzerliği
  3. Embedding modeli karşılaştırması: bge-m3 vs nomic-embed-text

Gereksinim: rag.py ile aynı ortam (Ollama + en az bir embedding modeli).
nomic-embed-text deneyi için: ollama pull nomic-embed-text

Kullanım:
    python olc.py                    # iki modeli de karşılaştır
    python olc.py --model bge-m3     # tek model
"""

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

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

# rag.py ile tek doğruluk kaynağı: aynı belgeler ve aynı orijinal sorular
from rag import BELGELER, TEST_SORULARI

# Aynı bilgi ihtiyacının farklı ifade edilmiş hâlleri (parafraz)
PARAFRAZLAR = [
    ("Ürünü geri gönderebilir miyim, süresi ne kadar?", "iade"),
    ("Paketim ezik ve yırtılmış ulaştı, ne yapmam gerek?", "hasar"),
    ("Elimdeki gönderi ne zaman bana ulaşır?", "teslimat"),
    ("Verilerimin sistemden tamamen kaldırılmasını talep edebilir miyim?", "kvkk"),
    ("Teslimatta ödeme yaparsam fazladan bir bedel öder miyim?", "odeme"),
    ("Talebe özel indirim günü var mı?", "kampanya"),
]

# Belgelerde karşılığı olmayan sorular (ekik/sessiz kalma davranışının ölçümü)
KAPSAM_DISI = [
    "Ankara'da hava nasıl?",
    "Dünyanın en uzun nehri hangisidir?",
    "Pilav nasıl yapılır?",
    "İstanbul'un nüfusu kaç milyondur?",
    "Gitar öğrenmek ne kadar sürer?",
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
    skorlar = sorted(
        ((kosinus(soru_v, v), b["id"]) for b, v in indeks["parcalar"]),
        key=lambda c: c[0],
        reverse=True,
    )
    return skorlar


def metrikleri_olc(sorular, indeks):
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


def indeks_olustur(model):
    t0 = time.time()
    parcalar = [(b, gomme(b["metin"], model)) for b in BELGELER]
    print(f"  [{model}] indeks: {len(parcalar)} belge, boyut={len(parcalar[0][1])}, "
          f"{time.time() - t0:.1f} sn")
    return {"model": model, "parcalar": parcalar}


def kapsam_disi_olc(indeks):
    sonuc = []
    for soru in KAPSAM_DISI:
        skorlar = tam_siralama(soru, indeks)
        sonuc.append((soru, skorlar[0][0]))
    return sonuc


def model_deneyi(model):
    print("\n" + "=" * 62)
    print(f"MODEL: {model}")
    print("=" * 62)
    indeks = indeks_olustur(model)

    orijinal = metrikleri_olc(TEST_SORULARI, indeks)
    print(f"\n  Orijinal sorular  : hit@1={orijinal['hit@1']:.2f}  "
          f"MRR={orijinal['mrr']:.3f}  (n={orijinal['n']})")
    print(f"  benzerlik bandı   : {orijinal['benzerlik_min']:.3f} - "
          f"{orijinal['benzerlik_max']:.3f}")

    parafraz = metrikleri_olc(PARAFRAZLAR, indeks)
    print(f"  Parafraz sorular  : hit@1={parafraz['hit@1']:.2f}  "
          f"MRR={parafraz['mrr']:.3f}  (n={parafraz['n']})")
    print(f"  benzerlik bandı   : {parafraz['benzerlik_min']:.3f} - "
          f"{parafraz['benzerlik_max']:.3f}")

    # Hangi parafraz kaçtı? (hit@1 kaçıranları listele)
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

    ayırma = min(orijinal["benzerlik_min"], parafraz["benzerlik_min"]) - max(degerler)
    print(f"  ayırma payı       : {ayırma:.3f} "
          f"(en düşük kapsam içi eksi en yüksek kapsam dışı)")

    return {"model": model, "orijinal": orijinal, "parafraz": parafraz,
            "kapsam_disi": degerler}


def ana():
    ayrıştırıcı = argparse.ArgumentParser(description="RAG değerlendirme ölçümleri")
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

    sonuçlar = [model_deneyi(m) for m in modeller]

    if len(sonuçlar) > 1:
        print("\n" + "=" * 62)
        print("KARŞILAŞTIRMA ÖZETİ")
        print("=" * 62)
        başlık = f"  {'model':<20} {'hit@1(ory)':<12} {'hit@1(para)':<13} {'MRR(para)':<11} ayırma"
        print(başlık)
        for s in sonuçlar:
            ayırma = (min(s["orijinal"]["benzerlik_min"], s["parafraz"]["benzerlik_min"])
                      - max(s["kapsam_disi"]))
            print(f"  {s['model']:<20} {s['orijinal']['hit@1']:<12.2f} "
                  f"{s['parafraz']['hit@1']:<13.2f} {s['parafraz']['mrr']:<11.3f} "
                  f"{ayırma:+.3f}")


if __name__ == "__main__":
    ana()
