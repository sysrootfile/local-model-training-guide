#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tekrarlanabilirlik olcu kafesi.

Kol A (Ollama): ayni istemin tekrarlanmasi sicakliga ve tohume ne kadar
basli? Varsayilan num_predict gercekten ne? format=json ile format=sema
ayni istemde neyi garanti ediyor?
Kol B (scikit-learn): ayni veri, ayni akis, bes farkli tohum - dogruluk
ne kadar oynuyor? Bolme tohumu mu, model tohumu mu daha etkili?

Kullanim:
    python -u tekrar.py --kol hepsi
    python -u tekrar.py --duman

Cikti: stdout (kayit dosyasina yonlendirin) + ozet tablosu.
Baska hicbir ag istegi atilmaz; sadece 127.0.0.1:11434 konusulur.
"""
import argparse
import hashlib
import json
import statistics
import sys
import time
import urllib.request

_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


OS = _url_dogrula("http://127.0.0.1:11434")
SOHBET = "qwen2.5:3b-instruct-q4_K_M"
TEKRAR = 10
NUM_PREDICT = 48

SORU_KAPALI = ("Marmaray hangi yilinda hizmete acildi? "
               "Yanitiniz tek kelime olsun, yildan baska bir sey yazmayin.")
SORU_ACIK = ("Kadıköy'de bir kahve dükkânı için üç slogan öner. "
             "Her slogan bir satırda olsun.")

SORU_JSON = ("Marmaray hangi yilinda hizmete acildi? Yalnizca iki alanli JSON yaz: "
             "yil (sayi) ve gerekce (kisa metin).")
SEMA_JSON = {"type": "object",
             "properties": {"yil": {"type": "integer"},
                            "gerekce": {"type": "string"}},
             "required": ["yil", "gerekce"]}

HUCRELER = [
    # (etiket, soru, sicaklik, seed, aciklama, bicim, num_predict)
    ("A1", SORU_KAPALI, 0.0, None, "sicaklik 0, tohum yok", None, NUM_PREDICT),
    ("A2", SORU_KAPALI, 0.0, 1234, "sicaklik 0, tohum 1234", None, NUM_PREDICT),
    ("A3", SORU_KAPALI, 0.8, None, "sicaklik 0,8, tohum yok", None, NUM_PREDICT),
    ("A4", SORU_KAPALI, 0.8, 1234, "sicaklik 0,8, tohum 1234", None, NUM_PREDICT),
    ("A5", SORU_KAPALI, 0.8, 1234, "A4 ile ayni ayar, ikinci diz", None, NUM_PREDICT),
    ("A6", SORU_KAPALI, 0.8, 9999, "sicaklik 0,8, tohum 9999", None, NUM_PREDICT),
    ("C1", SORU_ACIK, 0.8, None, "acik istem, sicaklik 0,8, tohum yok", None, 200),
    ("C2", SORU_ACIK, 0.8, 1234, "acik istem, tohum 1234", None, 200),
    ("C3", SORU_ACIK, 0.8, 1234, "C2 ile ayni ayar, ikinci diz", None, 200),
    ("D1", SORU_JSON, 0.8, None, "format=json, sicaklik 0,8, tohum yok", "json", 300),
    ("D2", SORU_JSON, 0.8, None, "format=sema, sicaklik 0,8, tohum yok", SEMA_JSON, 300),
    ("D3", SORU_JSON, 0.8, None, "format=sema AMA num_predict 48", SEMA_JSON, 48),
]


def yaz(metin=""):
    print(metin, flush=True)


def imza(metin):
    duz = " ".join(metin.split())
    return hashlib.md5(duz.encode("utf-8")).hexdigest()[:10], duz


def post(govde, kuyruk=""):
    veri = json.dumps(govde).encode("utf-8")
    istek = urllib.request.Request(_url_dogrula(OS + "/api/chat"), data=veri,
                                   headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(istek, timeout=600) as yanit:
        return json.loads(yanit.read().decode("utf-8"))


def model_bilgi():
    with urllib.request.urlopen(OS + "/api/version", timeout=30) as yanit:
        return json.loads(yanit.read().decode("utf-8")).get("version", "?")


def chat(soru, sicaklik, seed, num_predict=NUM_PREDICT, bicim=None):
    secenek = {"temperature": sicaklik, "num_predict": num_predict}
    if seed is not None:
        secenek["seed"] = seed
    govde = {"model": SOHBET,
             "messages": [{"role": "user", "content": soru}],
             "stream": False,
             "options": secenek}
    if bicim is not None:
        govde["format"] = bicim
    t0 = time.time()
    yanit = post(govde)
    duvar = time.time() - t0
    cevap = (yanit.get("message", {}).get("content") or "").strip()
    return {"cevap": cevap,
            "duvar": duvar,
            "girdi": yanit.get("prompt_eval_count", 0),
            "ctki": yanit.get("eval_count", 0),
            "bitis": yanit.get("done_reason", "?")}


# --------------------------------------------------------------- K0: varsayilan

def k0_varsayilan(say=3):
    """num_predict GONDERMEDEN uzun bir istek: fiili tavan ne?"""
    yaz("")
    yaz("K0 - VARSAYILAN NUM_PREDICT ARAMASI")
    yaz("   gonderim: options = {temperature: 0} (num_predict YOK)")
    soru = ("Türkiye'deki yedi bölgeyi ve her bölgenin en bilinen yemeğini "
            "tek tek yaz. Uzun yaz, hepsini sırala.")
    for i in range(1, say + 1):
        govde = {"model": SOHBET,
                 "messages": [{"role": "user", "content": soru}],
                 "stream": False,
                 "options": {"temperature": 0}}
        t0 = time.time()
        yanit = post(govde)
        duvar = time.time() - t0
        yaz("  K0.%d: duvar %5.2f sn | ctki token %3d | bitis %s"
            % (i, duvar, yanit.get("eval_count", 0), yanit.get("done_reason")))


# ------------------------------------------------------------------ kol A

def json_ayristir(metin):
    """Cevabini JSON olarak okunup okunmadigini ve yil alanini dondurur."""
    try:
        veri = json.loads(metin)
    except Exception:
        return False, None, ()
    if not isinstance(veri, dict):
        return False, None, ()
    return True, veri.get("yil"), tuple(sorted(veri.keys()))


def kol_a(tekrar):
    ozet = []
    for etiket, soru, sicaklik, seed, not_, bicim, tavan in HUCRELER:
        tur = ("kapali" if soru is SORU_KAPALI else
               "json" if soru is SORU_JSON else "acik")
        yaz("")
        yaz("%s | %s | T=%.1f | seed=%s | format=%s | num_predict=%d | %d tekrar"
            % (etiket, tur, sicaklik, seed if seed is not None else "-",
               "yok" if bicim is None else ("json" if bicim == "json" else "sema"),
               tavan, tekrar))
        yaz("   istem: %s" % soru[:78])
        kayitlar = []
        for i in range(1, tekrar + 1):
            k = chat(soru, sicaklik, seed, tavan, bicim=bicim)
            kod, duz = imza(k["cevap"])
            ok, yil, anahtarlar = (None, None, ()) if bicim is None else json_ayristir(k["cevap"])
            kayitlar.append({"kod": kod, "duz": duz, "json_ok": ok, "yil": yil,
                             "json_anahtarlar": anahtarlar, **k})
            ek = "" if bicim is None else " | JSON %s yil=%s alanlar=%s" % (
                "ok" if ok else "BOZUK", yil, ",".join(anahtarlar) or "-")
            yaz("  %2d. [%s] duvar %5.2f sn | girdi %4d | ctki %3d | bitis %-6s | %s%s | %r"
                % (i, kod, k["duvar"], k["girdi"], k["ctki"], k["bitis"],
                   "AYNI" if i > 1 and kod == kayitlar[0]["kod"] else "FARKLI", ek,
                   duz[:74]))
        ozet.append(ozetle(etiket, kayitlar, not_))
    return ozet


def ozetle(etiket, kayitlar, not_):
    kodlar = [k["kod"] for k in kayitlar]
    benzersiz = {}
    for kod in kodlar:
        benzersiz[kod] = benzersiz.get(kod, 0) + 1
    en_sik = max(benzersiz.values())
    uzunluklar = [len(k["duz"]) for k in kayitlar]
    bitisler = {}
    for k in kayitlar:
        bitisler[k["bitis"]] = bitisler.get(k["bitis"], 0) + 1
    satir = {"etiket": etiket, "n": len(kayitlar),
             "benzersiz": len(benzersiz), "en_sik_oran": en_sik / len(kayitlar),
             "uz_ort": statistics.mean(uzunluklar),
             "uz_min": min(uzunluklar), "uz_max": max(uzunluklar),
             "ctki_ort": statistics.mean(k["ctki"] for k in kayitlar),
             "duvar_toplam": sum(k["duvar"] for k in kayitlar),
             "bitisler": bitisler, "not": not_}
    if any(k["json_ok"] is not None for k in kayitlar):
        satir["json_ok"] = sum(1 for k in kayitlar if k["json_ok"])
        satir["yillar"] = sorted(set(str(k["yil"]) for k in kayitlar))
        satir["alan_setleri"] = sorted(set(",".join(k["json_anahtarlar"]) or "-"
                                           for k in kayitlar))
    return satir


def ozet_tablosu(ozet):
    yaz("")
    yaz("=========================================================")
    yaz("OZET (kol A)")
    yaz("=========================================================")
    yaz("hucre  n  benzersiz  en-sik-oran  uz-ort  uz-min/max  ctki-ort  duvar")
    for s in ozet:
        yaz("%-6s %2d  %9d  %11.2f  %6.1f  %3d/%-4d %8.1f  %6.1f sn"
            % (s["etiket"], s["n"], s["benzersiz"], s["en_sik_oran"],
               s["uz_ort"], s["uz_min"], s["uz_max"], s["ctki_ort"],
               s["duvar_toplam"]))
    yaz("")
    for s in ozet:
        json_ = "" if "json_ok" not in s else " | JSON okunan %d/%d | yil kodlari: %s | alan setleri: %d cesit" % (
            s["json_ok"], s["n"], ",".join(s["yillar"]), len(s["alan_setleri"]))
        yaz("%-6s bitis: %s%s | not: %s" % (s["etiket"], s["bitisler"], json_, s["not"]))


# ------------------------------------------------------------------ kol B

TOHUMLAR = [0, 1, 2, 7, 42]


def kol_b():
    from pathlib import Path
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    yol = Path(__file__).resolve().parents[1] / "klasik-ml" / "veri" / "breast_cancer.csv"
    df = pd.read_csv(yol, skiprows=1, header=None)
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1].astype(int)
    yaz("")
    yaz("=========================================================")
    yaz("KOL B - SCIKIT-LEARN TOHUM VARYANSI")
    yaz("=========================================================")
    yaz("   veri: %s | satir %d | özellik %d" % (yol.name, df.shape[0], X.shape[1]))

    senaryolar = [
        ("B1", "bolme + model tohumu birlikte degisir", True, True),
        ("B2", "bolme SABIT (42), yalniz model tohumu degisir", False, True),
        ("B3", "model tohumu SABIT (42), yalniz bolme degisir", True, False),
    ]
    sonuc = {}
    for etiket, aciklama, bolme_oynar, model_oynar in senaryolar:
        yaz("")
        yaz("%s | %s" % (etiket, aciklama))
        for t in TOHUMLAR:
            bs = t if bolme_oynar else 42
            ms = t if model_oynar else 42
            Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.2,
                                              stratify=y, random_state=bs)
            a1 = accuracy_score(yb, rf_t(ms).fit(Xa, ya).predict(Xb))
            a2 = accuracy_score(yb, lr_t(ms).fit(Xa, ya).predict(Xb))
            yaz("  tohum %-3d | egitim %3d test %3d | RF %.4f | Lojistik %.4f"
                % (t, Xa.shape[0], Xb.shape[0], a1, a2))
            sonuc.setdefault(etiket + "-rf", []).append(a1)
            sonuc.setdefault(etiket + "-lr", []).append(a2)
    yaz("")
    yaz("OZET (kol B, bes tohum)")
    for anahtar, degerler in sonuc.items():
        yaz("%-8s min %.4f | ort %.4f | max %.4f | acik %.4f"
            % (anahtar, min(degerler), statistics.mean(degerler),
               max(degerler), max(degerler) - min(degerler)))
    return sonuc


def rf_t(tohum):
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=300, random_state=tohum)


def lr_t(tohum):
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    return Pipeline([("olcekle", StandardScaler()),
                     ("model", LogisticRegression(max_iter=5000, random_state=tohum))])


# --------------------------------------------------------------------- main

def main():
    ayirici = argparse.ArgumentParser()
    ayirici.add_argument("--kol", default="hepsi", choices=["a", "b", "hepsi"])
    ayirici.add_argument("--duman", action="store_true",
                         help="iki tekrar, bes hucre: hizli dogrulama")
    secim = ayirici.parse_args()
    tekrar = 2 if secim.duman else TEKRAR

    import platform
    yaz("TEKRARLANABILIRLIK OLCUM KAFESI")
    yaz("  baslangic: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    yaz("  python %s | %s %s" % (platform.python_version(),
                                  platform.system(), platform.release()))
    yaz("  ollama %s | model %s | tekrar %d | varsayilan num_predict %d"
        % (model_bilgi(), SOHBET, tekrar, NUM_PREDICT))
    if secim.duman:
        yaz("  DUMAN TESTI: A1-A3 + D2-D3, iki tekrar, K0 tek istek")

    if secim.kol in ("a", "hepsi"):
        global HUCRELER
        if secim.duman:
            HUCRELER = HUCRELER[:3] + HUCRELER[-2:]
            k0_varsayilan(1)
        else:
            k0_varsayilan()
        ozet = kol_a(tekrar)
        ozet_tablosu(ozet)
    if secim.kol in ("b", "hepsi"):
        kol_b()

    yaz("")
    yaz("bitti: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

