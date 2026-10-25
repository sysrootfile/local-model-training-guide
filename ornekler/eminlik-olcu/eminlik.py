#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Eminlik olcum kafesi: logprob, Oz-tutarliluk, sozlu guven.

Kol A/H : sozlesme probu (Ollama logprobs'u ne donduruyor, tekrar bit-bit ayni mi)
Kol B   : coktan secmeli sorularda cevap-harf olasiligi (P(True) kalibi)
Kol C   : sicaklik, dönen logprob'u degistiriyor mu (belgesiz davranis)
Kol D   : serbest cevabin token basi ortalamasi + KIRPik entropi (ust sinir 20 aday)
Kol E   : Oz-tutarliluk - ayni sorunun 10 ornegi (harf kolu + serbest kolu)
Kol F   : semantik kumeleme (bge-m3 kosinüs) - yontem sapmasi belgeli
Kol G   : sozlu guven (0-100) - logprob'la karsilastirmali, ornek deger YOK

Fail-closed kurali: bir hucre kendi aday tokenlarini goren listede bulamazsa
varsayilana dusmez, o soruyu metrikten cikarir ve sayisini raporlar.

Kullanim:
    python -u eminlik.py --kol olcum            # B,C,D,E,F,G
    python -u eminlik.py --kol a                # sozlesme probu
    python -u eminlik.py --kol h                # tekrar probu
    python -u eminlik.py --kol olcum --duman    # kucuk kume, hizli dogrulama

Sadece 127.0.0.1:11434 ile konusulur; dışarıya istek atilmaz.
"""
import argparse
import json
import math
import platform
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

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
GOMME = "bge-m3"
CIKTI = Path(__file__).resolve().parent / "cikti"

HARFLER = ["A", "B", "C", "D"]
ADAY_TAVANI = 20          # probda olculen tavan: 20 ustu HTTP 400
ORNEK = 10                # Kol E'de soru basina ornek (Kuhn vd. 10/soru)
SICAKLIKLAR = [0.0, 0.7, 1.0]

SORU_KAPALI = ("Marmaray Istanbul'da hangi yil hizmete acildi? "
               "Yanitiniz yildan baska bir sey olmasin.")
SORU_TURKCE = ("Istanbul'da bir vapur iskelesinin adini, icinde 'h' ve 'ş' "
               "gecen bir Turkce sozcukle tek satirda yaz.")
SORU_JSON = ("Marmaray hangi yil hizmete acildi? Yalnizca iki alanli JSON yaz: "
             "yil (sayi) ve gerekce (kisa metin).")
SEMA_JSON = {"type": "object",
             "properties": {"yil": {"type": "integer"},
                            "gerekce": {"type": "string"}},
             "required": ["yil", "gerekce"]}

# --------------------------------------------------------------- soru seti
# Altinlar bu sitede dogrulanmis sayfalardan alindi (dosya notu README'de).
# (soru, dogru_secenek, [3 yanlis], tip)  tip: "bilgi" | "bilinemez"
SORULAR = [
    ("Llama 3'un kelime dagarcigi (tokenizer sozlugui) kactir?",
     "128.256", ["151.936", "262.208", "50.257"], "bilgi"),
    ("Qwen3'un kelime dagarcigi kactir?",
     "151.936", ["128.256", "262.208", "32.768"], "bilgi"),
    ("Gemma 3'un kelime dagarcigi kactir?",
     "262.208", ["128.256", "151.936", "200.000"], "bilgi"),
    ("BAAI/bge-m3 embedding modeli kac boyutlu vektor uretir?",
     "1024", ["384", "768", "4096"], "bilgi"),
    ("paraphrase-multilingual-MiniLM-L12-v2 kac boyutlu cikis verir?",
     "384", ["1024", "768", "128"], "bilgi"),
    ("TRL'de DPO egitiminin varsayilan beta degeri nedir?",
     "0,1", ["0,5", "0,01", "1,0"], "bilgi"),
    ("TRL kütüphanesinde SimPO karsiligi olan kayip turu hangisidir?",
     "sigmoid_norm", ["simpo", "sigmoid", "cosine_similarity"], "bilgi"),
    ("FineWeb-2 derlemesinin tur_Latn bolümü kac belge icerir?",
     "95.129.129", ["88.838", "1.100.000", "41.933"], "bilgi"),
    ("OpenAssistant oasst1 derlemesinin Turkce kismi kac mesajdir?",
     "37", ["3.700", "88.838", "120"], "bilgi"),
    ("RunPod'da ag volume'unun fiyati (1 TB altinda) nedir?",
     "$0,07/GB-ay", ["$0,10/GB-ay", "$0,07/saat", "$1,00/GB-ay"], "bilgi"),
    ("CUDA 12 ailesi icin Windows'ta asgari ekran karti surucusu hangisidir?",
     "527.41", ["450.80.02", "525.60.13", "580.00"], "bilgi"),
    ("Ollama, 24 GB altindaki VRAM'de varsayilan olarak kac tokenlik baglam acar?",
     "4096", ["32768", "256000", "8192"], "bilgi"),
    ("Ollama varsayilan keep_alive degeriyle modeli bellekte ne kadar tutar?",
     "5 dakika", ["30 dakika", "1 saat", "10 saniye"], "bilgi"),
    ("Bu makinede olculen Turkce metnin karakter/token orani kactir?",
     "2,99", ["4,20", "1,50", "3,75"], "bilgi"),
    ("Qwen3-30B-A3B modelinin AKTIF parametre miktari nedir?",
     "3,3B", ["30,5B", "37B", "8B"], "bilgi"),
    ("DeepSeek-V3 modelinin TOPLAM parametre miktari nedir?",
     "671B", ["37B", "109B", "30,5B"], "bilgi"),
    ("Ornek 6'nin kodunda ZAYIF_ESIK olcumden sonra hangi degere cekildi?",
     "0,54", ["0,35", "0,75", "0,41"], "bilgi"),
    ("MMLU'da ust modellerin yerlestigi doygunluk bandi yaklasik kactir?",
     "%90", ["%60", "%75", "%99"], "bilgi"),
    ("Qwen3-30B-A3B'de her token icin 128 uzmandan kaci secilir?",
     "8", ["2", "16", "128"], "bilgi"),
    ("vLLM icin Ekim 2026'da ulasilan surum hattini hangisidir?",
     "v0,31", ["v0,12", "v1,0", "v0,8"], "bilgi"),
    # ---- bilinemez: dogru davranis "bilmiyorum" secenegini secmek
    ("2031 yilinda duzenlenecek yerel secimin kesin sonucu nedir?",
     "Hiçbiri / bilmiyorum", ["Akpartinin adayi kazanacak", "Muhalif aday kazanacak",
     "Sonuc esitlikle belirlenecek"], "bilinemez"),
    ("Bulut Kargo A.S.'nin iade suresi kac is gunudur?",
     "Hiçbiri / bilmiyorum", ["7 is gunu", "14 is gunu", "3 is gunu"], "bilinemez"),
    ("Yildiztepe mahallesinde kac hane yasiyor?",
     "Hiçbiri / bilmiyorum", ["1.240", "860", "3.500"], "bilinemez"),
    ("Gomme egitimi kafesinde batch 16 kolunun hit@1 skoru kactir?",
     "Hiçbiri / bilmiyorum", ["8/8", "7/8", "6/8"], "bilinemez"),
    ("Bu makinede q4_K_M ile fp16 arasindaki logprob farki olculdu mu?",
     "Hiçbiri / bilmiyorum", ["Evet, 0,05", "Evet, 0,23", "Evet, 0,00"], "bilinemez"),
    ("2027'de yayimlanacak bir modelin MMLU skoru ne olacak?",
     "Hiçbiri / bilmiyorum", ["%95", "%88", "%70"], "bilinemez"),
]


def yaz(metin=""):
    print(metin, flush=True)


def post(yol, govde, timeout=600):
    veri = json.dumps(govde).encode("utf-8")
    istek = urllib.request.Request(_url_dogrula(OS + yol), data=veri,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(istek, timeout=timeout) as yanit:
        return json.loads(yanit.read().decode("utf-8"))


def model_bilgi():
    with urllib.request.urlopen(_url_dogrula(OS + "/api/version"), timeout=30) as yanit:
        return json.loads(yanit.read().decode("utf-8")).get("version", "?")


# ------------------------------------------------------------------ secenek
def secenekler(satir, indeks):
    """Altin secenegi rotasyonla dagitir (A/B/C/D sirasi sabit kalmasın)."""
    soru, dogru, yanlislar, tip = satir
    hepsi = list(yanlislar)
    yer = indeks % 4
    hepsi.insert(yer, dogru)
    return soru, dogru, tip, hepsi, yer


def mc_istem(soru, sekiller):
    satirlar = "\n".join("%s) %s" % (h, s) for h, s in zip(HARFLER, sekiller))
    return ("SORU: %s\nSIKKLAR:\n%s\n\nYalnizca dogru sikkin harfini yaz. "
            "Baska hicbir karakter yazma." % (soru, satirlar))


def govde_chat(soru, logprobs=True, top=None, tavan=None, sicaklik=0.0,
               seed=None, bicim=None):
    secenek = {"temperature": sicaklik}
    if tavan is not None:
        secenek["num_predict"] = tavan
    if seed is not None:
        secenek["seed"] = seed
    govde = {"model": SOHBET,
             "messages": [{"role": "user", "content": soru}],
             "stream": False,
             "options": secenek}
    if logprobs:
        govde["logprobs"] = True
    if top is not None:
        govde["top_logprobs"] = top
    if bicim is not None:
        govde["format"] = bicim
    return govde


def harf_kitlesi(top, harf):
    """Aday listesinde bu harfe dusen olasilik kitlesi. Esmeyi de sayar
    ('A' ve 'A)'), baska sekilleri saymaz. Bulunamazsa None doner."""
    toplam, bulundu = 0.0, False
    for aday in top:
        t = (aday.get("token") or "").strip()
        if t == harf or t == harf + ")" or t == harf + ":":
            toplam += math.exp(aday["logprob"])
            bulundu = True
    return toplam if bulundu else None


# ------------------------------------------------------------ sozlesme probu
def ozetle_logprobs(lp_listesi):
    alanlar, aday_sayilari, tokenlar, bayt_uyumu = [], [], [], 0
    for kayit in lp_listesi:
        for anahtar in kayit:
            if anahtar not in alanlar:
                alanlar.append(anahtar)
        token = kayit.get("token")
        tokenlar.append(token)
        top = kayit.get("top_logprobs") or []
        aday_sayilari.append(len(top))
        baytlar = kayit.get("bytes")
        if isinstance(baytlar, list) and isinstance(token, str):
            try:
                if bytearray(baytlar).decode("utf-8") == token:
                    bayt_uyumu += 1
            except Exception:
                pass
    return {"n": len(lp_listesi), "alanlar": alanlar,
            "aday_min": min(aday_sayilari) if aday_sayilari else 0,
            "aday_max": max(aday_sayilari) if aday_sayilari else 0,
            "tokenlar": tokenlar, "bayt_basina_uydu": bayt_uyumu}


def kirpik_entropi(kayit):
    top = kayit.get("top_logprobs") or []
    if not top:
        return None
    olasiliklar = [math.exp(k["logprob"]) for k in top]
    toplam = sum(olasiliklar)
    if toplam <= 0:
        return None
    dus = [p / toplam for p in olasiliklar]
    return -sum(p * math.log(p) for p in dus if p > 0)


def a_hucre(etiket, aciklama, yol, govde):
    yaz("")
    yaz("%s | %s | %s" % (etiket, yol, aciklama))
    try:
        t0 = time.time()
        yanit = post(yol, govde)
        duvar = time.time() - t0
    except urllib.error.HTTPError as h:
        govdeyi = h.read().decode("utf-8", "replace")[:200]
        yaz("  HTTP %s | govde: %s" % (h.code, govdeyi))
        return {"etiket": etiket, "hata": h.code, "mesaji": govdeyi}
    lp = yanit.get("logprobs")
    if yol.startswith("/v1"):
        secici = (yanit.get("choices") or [{}])[0]
        lp = secici.get("logprobs", {}).get("content")
        icerik = (secici.get("message", {}) or {}).get("content", "")
        ctki = (yanit.get("usage", {}) or {}).get("completion_tokens", 0)
    else:
        icerik = (yanit.get("message", {}) or {}).get("content",
                 yanit.get("response", ""))
        ctki = yanit.get("eval_count", 0)
    icerik = (icerik or "").strip()
    if lp is None:
        yaz("  logprobs ALANININ KENDISI YOK/GOK | duvar %5.2f sn | ctki %d | cevap %r"
            % (duvar, ctki, icerik[:60]))
        return {"etiket": etiket, "logprobs_yok": True, "duvar": duvar,
                "ctki": ctki, "icerik": icerik}
    yapi = ozetle_logprobs(lp)
    yaz("  duvar %5.2f sn | ctki %d | logprob kaydi %d | alanlar: %s"
        % (duvar, ctki, yapi["n"], ",".join(yapi["alanlar"]) or "-"))
    yaz("  top_logprobs aday sayisi: min %d / max %d | bayt-uzanti uyumu %d/%d"
        % (yapi["aday_min"], yapi["aday_max"], yapi["bayt_basina_uydu"], yapi["n"]))
    yaz("  cevap %r" % icerik[:90])
    yaz("  tokenlari: %s" % " ".join(repr(t) for t in yapi["tokenlar"][:14]))
    if yapi["n"] > 14:
        yaz("  son tokenlar: %s" % " ".join(repr(t) for t in yapi["tokenlar"][-6:]))
    yaz("  sozlesme: eval_count %d - logprob kaydi %d = %d kayit YOK"
        % (ctki, yapi["n"], ctki - yapi["n"]))
    ent = [e for e in (kirpik_entropi(k) for k in lp) if e is not None]
    if ent:
        yaz("  kirpik entropi (nat): ilk %.4f | ort %.4f | son %.4f  [ALT SINIR]"
            % (ent[0], statistics.mean(ent), ent[-1]))
    ilk = lp[0] if lp else {}
    if ilk.get("top_logprobs"):
        yaz("  ilk konum adaylari: %s" % ", ".join(
            "%s=%.4f" % (repr(a["token"]), math.exp(a["logprob"]))
            for a in ilk["top_logprobs"][:6]))
    yaz("  yanit anahtarlari: %s" % ",".join(sorted(yanit.keys())))
    return {"etiket": etiket, "duvar": duvar, "ctki": ctki, "yapi": yapi,
            "icerik": icerik, "yanit_anahtarlari": sorted(yanit.keys())}


def kol_a(duman):
    sonuclar = [
        a_hucre("A1", "logprobs=true, top_logprobs GONDERILMEDI", "/api/chat",
                govde_chat(SORU_KAPALI, top=None, tavan=32)),
        a_hucre("A2", "top_logprobs=5", "/api/chat",
                govde_chat(SORU_KAPALI, top=5, tavan=32)),
        a_hucre("A3", "num_predict=1, top_logprobs=10", "/api/chat",
                govde_chat(SORU_KAPALI, top=10, tavan=1)),
    ]
    if duman:
        return sonuclar
    for top in (1, 20, 100, 0):
        sonuclar.append(a_hucre("A4.%d" % top, "top_logprobs=%d sinir aramasi" % top,
                                 "/api/chat", govde_chat(SORU_KAPALI, top=top, tavan=1)))
    gen = {"model": SOHBET, "prompt": SORU_KAPALI, "stream": False,
           "logprobs": True, "top_logprobs": 5,
           "options": {"temperature": 0.0, "num_predict": 32}}
    sonuclar.append(a_hucre("A5", "native generate ucu (prompt/response govdesi)",
                             "/api/generate", gen))
    oai = {"model": SOHBET, "messages": [{"role": "user", "content": SORU_KAPALI}],
           "logprobs": True, "top_logprobs": 3, "max_tokens": 32,
           "temperature": 0, "stream": False}
    sonuclar.append(a_hucre("A6", "OpenAI uyumlu chat completions",
                             "/v1/chat/completions", oai))
    sonuclar.append(a_hucre("A7", "format=json + logprobs", "/api/chat",
                             govde_chat(SORU_JSON, top=5, tavan=64, bicim="json")))
    sonuclar.append(a_hucre("A8", "format=sema + logprobs", "/api/chat",
                             govde_chat(SORU_JSON, top=5, tavan=64, bicim=SEMA_JSON)))
    sonuclar.append(a_hucre("A9", "Turkce karakter bayt eslesmesi", "/api/chat",
                             govde_chat(SORU_TURKCE, top=3, tavan=24)))
    sonuclar.append(a_hucre("A10", "top_logprobs=5 AMA logprobs gonderilmedi",
                             "/api/chat", govde_chat(SORU_KAPALI, logprobs=False,
                                                    top=5, tavan=8)))
    sonuclar.append(a_hucre("A11", "logprobs GONDERILMEDI (karsit kanit)", "/api/chat",
                             govde_chat(SORU_KAPALI, logprobs=False, top=None, tavan=8)))
    return sonuclar


def h_tekil(govde):
    yanit = post("/api/chat", govde)
    lp = yanit.get("logprobs") or []
    return [(k.get("token"), k.get("logprob")) for k in lp], \
           (yanit.get("message", {}) or {}).get("content", "")


def karsilastir(dizilar):
    if len(dizilar) < 2:
        return "OLCULMEDI (tek tekrar: karsilastirma boslukta yapilir)"
    referans = dizilar[0]
    if any(len(d) != len(referans) for d in dizilar):
        return "HAYIR (kayit sayilari farkli: %s)" % [len(d) for d in dizilar]
    en_buyuk, ilk_fark = 0.0, None
    for d in dizilar[1:]:
        for (t1, l1), (t2, l2) in zip(referans, d):
            if t1 != t2:
                return "HAYIR (token zinciri farkli: %r vs %r)" % (t1, t2)
            if abs((l1 or 0.0) - (l2 or 0.0)) > en_buyuk:
                en_buyuk = abs((l1 or 0.0) - (l2 or 0.0))
                ilk_fark = t1
    if en_buyuk == 0.0:
        return "EVET (token + logprob bit bit ayni)"
    return "HAYIR (ayni tokenlar, max |delta logprob| %.3e, ilk: %r)" % (en_buyuk, ilk_fark)


def kol_h(duman):
    yaz("")
    yaz("=" * 57)
    yaz("KOL H - LOGPROB TEKRARI (sicaklik 0, ayni istem)")
    yaz("=" * 57)
    tekrar = 2 if duman else 3
    ayarlar = [("H1", govde_chat(SORU_KAPALI, top=5, tavan=32, seed=1234),
                "T=0, seed=1234, num_predict=32"),
               ("H2", govde_chat(SORU_KAPALI, top=5, tavan=32, seed=None),
                "T=0, seed YOK, num_predict=32"),
               ("H3", govde_chat(SORU_KAPALI, top=5, tavan=1, seed=1234),
                "T=0, seed=1234, num_predict=1")]
    for etiket, govde, not_ in ayarlar:
        dizilar = []
        for i in range(tekrar):
            t0 = time.time()
            tokens, icerik = h_tekil(json.loads(json.dumps(govde)))
            yaz("%s.%d | %5.2f sn | kayit %2d | %r" %
                (etiket, i + 1, time.time() - t0, len(tokens),
                 (icerik or "").strip()[:40]))
            dizilar.append(tokens)
        yaz("  %s | %d tekrar -> %s" % (etiket, tekrar, karsilastir(dizilar)))
        yaz("  not: %s" % not_)
    yaz("")
    yaz("H4 | keep_alive=0 ile model dusurulur, sonra ayni istem")
    try:
        post("/api/chat", {"model": SOHBET,
                           "messages": [{"role": "user", "content": "dur"}],
                           "stream": False, "keep_alive": 0,
                           "options": {"num_predict": 1, "temperature": 0}})
        yaz("  dusurma istegi gonderildi (keep_alive=0)")
    except Exception as hata:
        yaz("  [UYARI] dusurma cagrisi: %r" % (hata,))
    dizilar = []
    for i in range(tekrar):
        t0 = time.time()
        tokens, icerik = h_tekil(govde_chat(SORU_KAPALI, top=5, tavan=32, seed=1234))
        yaz("  H4.%d | %5.2f sn | kayit %2d | %s | %r"
            % (i + 1, time.time() - t0, len(tokens),
               "soguk (model yeni yuklendi)" if i == 0 else "sicak",
               (icerik or "").strip()[:40]))
        dizilar.append(tokens)
    yaz("  H4 | soguk vs sicak -> %s" % karsilastir(dizilar))
    yaz("  not: H1 ile ayni ayar; fark yalnizca yukleme durumundan gelmelidir")
    return {"tekrar": tekrar, "ozet": "logda"}


# ---------------------------------------------------------------- tek atis
def mc_tekil(istem, sicaklik=0.0, seed=None, tavan=1, etiket=""):
    """Tek tokenlik secim: harf kitlesi + secilen harf + aday dogrulamasi."""
    govde = govde_chat(istem, top=ADAY_TAVANI, tavan=tavan,
                       sicaklik=sicaklik, seed=seed)
    t0 = time.time()
    try:
        yanit = post("/api/chat", govde)
    except urllib.error.HTTPError as h:
        return {"hata": h.code, "govde": h.read().decode("utf-8", "replace")[:160]}
    duvar = time.time() - t0
    lp = yanit.get("logprobs") or []
    icerik = (yanit.get("message", {}) or {}).get("content", "") or ""
    if not lp:
        return {"hata": "logprobs alan yok", "duvar": duvar, "icerik": icerik.strip()}
    top = lp[0].get("top_logprobs") or []
    kitles = {h: harf_kitlesi(top, h) for h in HARFLER}
    eksik = [h for h, k in kitles.items() if k is None]
    ham = sum(k for k in kitles.values() if k is not None)
    renorm = None
    if kitles and not eksik and ham > 0:
        renorm = {h: kitles[h] / ham for h in HARFLER}
    secilen = (icerik.strip()[:1] or "").upper()
    return {"duvar": duvar, "ctki": yanit.get("eval_count", 0), "kayit": len(lp),
            "token": lp[0].get("token"), "icerik": icerik.strip(),
            "secilen": secilen if secilen in HARFLER else None,
            "kitles": kitles, "eksik_harf": eksik, "renorm": renorm,
            "aday": len(top), "etiket": etiket}


# -------------------------------------------------------------------- KOL B
def kol_b(duman, kayitlar):
    sorular = SORULAR[:6] if duman else SORULAR
    yaz("")
    yaz("=" * 57)
    yaz("KOL B - CEVAP-HARF OLASILIGI (P(True) kalibi, T=0, num_predict=1)")
    yaz("=" * 57)
    for i, satir in enumerate(sorular):
        soru, dogru, tip, sekiller, yer = secenekler(satir, i)
        hedef_harf = HARFLER[yer]
        metin = mc_istem(soru, sekiller)
        if i == 0:
            yaz("  istem kalibi (bir kerelik):")
            yaz("  %r" % metin[-150:])
        r = mc_tekil(metin, etiket="B%d" % (i + 1))
        r.update({"no": i + 1, "soru": soru, "tip": tip, "dogru": dogru,
                  "altin_harf": hedef_harf, "sekiller": sekiller})
        if r.get("hata"):
            yaz("B%-2d | HATA %s" % (i + 1, r["hata"]))
            kayitlar.append(r)
            continue
        p = (r["renorm"] or {}).get(hedef_harf)
        dogri = r["secilen"] == hedef_harf
        yaz("B%-2d | %5.2f sn | %-9s | altin %s secim %-4s | P(altin) %-8s | en yuksek %s"
            % (i + 1, r["duvar"], tip, hedef_harf, r["secilen"] or "?",
               "%.4f" % p if p is not None else "YOK",
               max((r["renorm"] or {"?": 0}).items(), key=lambda kv: kv[1])[0]
               if r["renorm"] else "?"))
        if r["renorm"]:
            yaz("     P vektoru  %s" % " ".join(
                "%s=%.4f" % (h, r["renorm"][h]) for h in HARFLER))
        if r["eksik_harf"]:
            yaz("     [FAIL-CLOSED] aday listesinde bulunmayan harf: %s "
                "-> bu soru P metriklerinden DISARI" % ",".join(r["eksik_harf"]))
        kayitlar.append(r)
    return kayitlar


def b_ozeti(kayitlar):
    yaz("")
    yaz("-" * 57)
    yaz("KOL B OZETI")
    yaz("  onemli: esik, SECILEN harfin olasiligi uzerinden taranir (uretimde altin")
    yaz("  etiket bilinmez). P(altin) satirlari YALNIZ analiz degeridir, esik kurmaz.")
    bilgi = [k for k in kayitlar if k.get("tip") == "bilgi"]
    bilinemez = [k for k in kayitlar if k.get("tip") == "bilinemez"]
    lp_ok = [k for k in bilgi if k.get("renorm") and k.get("secilen")]
    aday_eksik = [k for k in bilgi if k.get("eksik_harf")]
    bicim_bozuk = [k for k in bilgi if k.get("renorm") and not k.get("secilen")]
    yaz("  bilgi sorulari: toplam %d | olculen %d | aday-eksik (metrik disi) %d | "
        "harf disi secim (bicim kirilmasi) %d"
        % (len(bilgi), len(lp_ok), len(aday_eksik), len(bicim_bozuk)))
    if not lp_ok:
        yaz("  OLCULEMEDI: kullanilabilir bilgi sorusu kalmadi")
        return
    dogrular = [k for k in lp_ok if k["secilen"] == k["altin_harf"]]
    yanlislar = [k for k in lp_ok if k["secilen"] != k["altin_harf"]]
    yaz("  dogru secim %d/%d (%.2f)" % (len(dogrular), len(lp_ok),
                                        len(dogrular) / len(lp_ok)))
    dagilim = {h: sum(1 for k in lp_ok if k["secilen"] == h) for h in HARFLER}
    yaz("  secim harfi dagilimi: %s | en sik %.2f"
        % (" ".join("%s:%d" % (h, dagilim[h]) for h in HARFLER),
           max(dagilim.values()) / len(lp_ok)))
    if max(dagilim.values()) / len(lp_ok) > 0.5:
        yaz("  [GECERSIZLIK KAPISI] tek bir harf secimlerin yarisindan cogunu aldi: "
            "bu kolda P(secilen) konum yanliliginin olcusudur, bilginin degil. "
            "Esik/risk tablolaru bu durumda ayirici sayilmaz; serbest metin kolu "
            "(D/G) ayni sorularin icerik kontroludur.")
    p_secim_d = [k["renorm"][k["secilen"]] for k in dogrular]
    p_secim_y = [k["renorm"][k["secilen"]] for k in yanlislar]
    for ad, grup in [("dogru secimlerin P(secilen)", p_secim_d),
                    ("yanlis secimlerin P(secilen)", p_secim_y)]:
        if grup:
            yaz("  %s: min %.4f | ort %.4f | max %.4f"
                % (ad, min(grup), statistics.mean(grup), max(grup)))
    if p_secim_d and p_secim_y:
        pay = min(p_secim_d) - max(p_secim_y)
        yaz("  ayrisma payi (en kotu dogru - en iyi yanlis): %.4f" % pay)
    p_altin_d = [k["renorm"][k["altin_harf"]] for k in dogrular]
    if p_altin_d:
        yaz("  [analiz] P(altin) dogrularda: ort %.4f (min %.4f max %.4f)"
            % (statistics.mean(p_altin_d), min(p_altin_d), max(p_altin_d)))
    p_altin_y = [k["renorm"][k["altin_harf"]] for k in yanlislar]
    if p_altin_y:
        yaz("  [analiz] P(altin) yanlislarda: ort %.4f (min %.4f max %.4f)"
            % (statistics.mean(p_altin_y), min(p_altin_y), max(p_altin_y)))
    yaz("  esik tarasi (P(secilen) >= tau -> cevap ver; yoksa cekil):")
    for tau in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99):
        gecen = [k for k in lp_ok if k["renorm"][k["secilen"]] >= tau]
        hata = sum(1 for k in gecen if k["secilen"] != k["altin_harf"])
        yaz("    tau %-5.2f | kapsama %.2f (%2d/%d) | risk %s"
            % (tau, len(gecen) / len(lp_ok), len(gecen), len(lp_ok),
               "%.3f" % (hata / len(gecen)) if gecen else "OLCUSUZ (kume bos)"))
    if bilinemez:
        oklar = [k for k in bilinemez if k.get("renorm") and k.get("secilen")]
        kacinan = sum(1 for k in oklar if k["secilen"] == k["altin_harf"])
        yaz("  bilinemez sorular: olculen %d/%d | 'bilmiyorum' secimi %d"
            % (len(oklar), len(bilinemez), kacinan))
        for k in oklar:
            if k["secilen"] != k["altin_harf"]:
                yaz("     -> B%-2d bilinen bir secer gibi cevap verdi: secim %s, "
                    "P(secilen) %.4f" % (k["no"], k["secilen"],
                                         k["renorm"][k["secilen"]]))


# -------------------------------------------------------------------- KOL C
def kol_c(duman, kayitlar):
    sorular = SORULAR[:3] if duman else SORULAR[:10]
    yaz("")
    yaz("=" * 57)
    yaz("KOL C - SICAKLIK DONEN LOGPROB'U DEGISTIRIYOR MU (seed=1234)")
    yaz("=" * 57)
    for i, satir in enumerate(sorular):
        soru, dogru, tip, sekiller, yer = secenekler(satir, i)
        istem = mc_istem(soru, sekiller)
        satir_sonuc = []
        for t in SICAKLIKLAR:
            r = mc_tekil(istem, sicaklik=t, seed=1234, etiket="C%d@%.1f" % (i + 1, t))
            kayitlar.append(r)
            if r.get("renorm"):
                satir_sonuc.append((t, r["renorm"].get(HARFLER[yer]), r["secilen"]))
        metin = " | ".join("T=%.1f P=%s sec=%s"
                           % (t, "%.4f" % p if p is not None else "YOK", s or "?")
                           for t, p, s in satir_sonuc)
        yaz("C%-2d | %s" % (i + 1, metin))
        ps = [p for _, p, _ in satir_sonuc if p is not None]
        if len(ps) == len(satir_sonuc) and satir_sonuc:
            fark = max(ps) - min(ps)
            yaz("      P araligi %.5f  -> sicaklik logprob'u %s"
                % (fark, "DEGISTIRMIYOR" if fark < 1e-6 else "DEGISTIRIYOR"))
    return kayitlar


# -------------------------------------------------------------------- KOL D
def kol_d(duman, kayitlar):
    sorular = SORULAR[:3] if duman else SORULAR[:10]
    yaz("")
    yaz("=" * 57)
    yaz("KOL D - SERBEST CEVAP: ORTALAMA LOGPROB + KIRPIK ENTROPI (ALT SINIR)")
    yaz("=" * 57)
    tavan = 32 if duman else 64
    for i, satir in enumerate(sorular):
        soru, dogru, tip, sekiller, yer = secenekler(satir, i)
        istem = ("SORU: %s\nSIKKLAR:\n%s\n\nDogru sikkin METNINI tek satirda yaz, "
                 "aciklama yapma." % (soru, "\n".join(
                     "%s) %s" % (h, s) for h, s in zip(HARFLER, sekiller))))
        govde = govde_chat(istem, top=ADAY_TAVANI, tavan=tavan, sicaklik=0.0)
        try:
            t0 = time.time()
            yanit = post("/api/chat", govde)
            duvar = time.time() - t0
        except urllib.error.HTTPError as h:
            yaz("D%-2d | HATA %s" % (i + 1, h.code))
            continue
        lp = yanit.get("logprobs") or []
        icerik = (yanit.get("message", {}) or {}).get("content", "") or ""
        if not lp:
            yaz("D%-2d | logprobs yok -> OLCULEMEDI" % (i + 1))
            continue
        lps = [k["logprob"] for k in lp]
        ent = [e for e in (kirpik_entropi(k) for k in lp) if e is not None]
        ctki = yanit.get("eval_count", 0)
        r = {"no": i + 1, "duvar": duvar, "ctki": ctki, "kayit": len(lp),
             "eksik_kayit": ctki - len(lp), "ort_logprob": statistics.mean(lps),
             "entropi_ort": statistics.mean(ent) if ent else None,
             "entropi_max": max(ent) if ent else None, "icerik": icerik.strip(),
             "dogru_metin": dogru}
        kayitlar.append(r)
        yaz("D%-2d | %5.2f sn | ctki %3d | kayit %3d (%d yok) | ort lp %8.4f | "
            "kirpik ent ort %6.4f max %6.4f"
            % (i + 1, duvar, ctki, len(lp), r["eksik_kayit"], r["ort_logprob"],
               r["entropi_ort"] if r["entropi_ort"] is not None else -1,
               r["entropi_max"] if r["entropi_max"] is not None else -1))
        yaz("      cevap %r | dogru %r" % (icerik.strip()[:60], dogru))
    return kayitlar


# --------------------------------------------------------------- KOL E + F
TURKCE_KATLAR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def talimat_yankisi_mi(metin):
    """Ornek, istemin kendisini mi tekrarliyor (talimat yankisi)? Kümelemeyi
    bozan bu artefakt sayilir, temizlenmez (README'de belgeli)."""
    duz = metin.translate(TURKCE_KATLAR).lower()
    return any(p in duz for p in ("sikkin metnini", "dogru sikkin", "tek satirda",
                                  "asagidaki", "istemin"))


def kol_e(duman, kayitlar):
    sorular = SORULAR[:3] if duman else SORULAR[:10]
    n = 2 if duman else ORNEK
    yaz("")
    yaz("=" * 57)
    yaz("KOL E - OZ-TUTARLILIK (%d ornek/soru, T=0,8, seed yok)" % n)
    yaz("=" * 57)
    serbest = []
    tum_harfler = []
    for i, satir in enumerate(sorular):
        soru, dogru, tip, sekiller, yer = secenekler(satir, i)
        altin = HARFLER[yer]
        istem = mc_istem(soru, sekiller)
        harfler, ps = [], []
        for j in range(n):
            r = mc_tekil(istem, sicaklik=0.8, tavan=1, etiket="E%d.%d" % (i + 1, j + 1))
            kayitlar.append(r)
            if r.get("secilen"):
                harfler.append(r["secilen"])
                if r.get("renorm"):
                    ps.append(r["renorm"].get(altin))
        if not harfler:
            yaz("E%-2d | ornekler secim yapamadi -> OLCULEMEDI" % (i + 1))
            continue
        sayim = {}
        for h in harfler:
            sayim[h] = sayim.get(h, 0) + 1
        cogunluk_harf = max(sayim, key=lambda k: sayim[k])
        oran = sayim[cogunluk_harf] / len(harfler)
        tum_harfler.extend(harfler)
        yaz("E%-2d | anlasma %.2f (%s) | cogunluk %s | altin %s | cogunluk %s"
            % (i + 1, oran, ",".join("%s:%d" % (h, s) for h, s in sorted(sayim.items())),
               cogunluk_harf, altin,
               "DOGRU" if cogunluk_harf == altin else "YANLIS"))
        # serbest kol: semantik kumeleme icin metinler
        acik = ("SORU: %s\nSIKKLAR:\n%s\n\nDogru sikkin METNINI tek satirda yaz, "
                "aciklama yapma." % (soru, "\n".join(
                    "%s) %s" % (h, s) for h, s in zip(HARFLER, sekiller))))
        metinler = []
        for j in range(n):
            govde = govde_chat(acik, top=None, tavan=32, sicaklik=0.8)
            try:
                yanit = post("/api/chat", govde)
            except urllib.error.HTTPError as h:
                yaz("   [UYARI] serbest ornek hatasi: %s" % h.code)
                break
            metin = ((yanit.get("message", {}) or {}).get("content", "") or "").strip()
            if metin:
                metinler.append(metin)
        yanki = sum(1 for m in metinler if talimat_yankisi_mi(m))
        serbest.append({"no": i + 1, "soru": soru, "dogru": dogru,
                        "anlasma": oran, "cogunluk_dogru": cogunluk_harf == altin,
                        "metinler": metinler, "talimat_yankisi": yanki,
                        "ortalama_p_altin":
                        (statistics.mean(ps) if ps else None)})
    if tum_harfler:
        sayim = {h: sum(1 for x in tum_harfler if x == h) for h in HARFLER}
        yaz("")
        yaz("  E toplami: %d secim | harf dagilimi %s | en sik %.2f | anlasma ort %.2f"
            % (len(tum_harfler), " ".join("%s:%d" % (h, sayim[h]) for h in HARFLER),
               max(sayim.values()) / len(tum_harfler),
               statistics.mean(k["anlasma"] for k in serbest) if serbest else -1))
        yaz("  not: anlasma 1,00'e yakinse oz-tutarlilik ornekleminde cesitlilik "
            "yoktur; semantik entropi ~0 cikar ve bu bir bulgudur, olcum hatasi degil")
    return serbest


def gomme(icerik):
    govde = {"model": GOMME, "input": icerik}
    yanit = post("/api/embed", govde)
    v = yanit.get("embeddings") or []
    return v[0] if v else None


def kosinus(a, b):
    if not a or not b:
        return None
    za = math.sqrt(sum(x * x for x in a))
    zb = math.sqrt(sum(x * x for x in b))
    if za == 0 or zb == 0:
        return None
    return sum(x * y for x, y in zip(a, b)) / (za * zb)


def kumele(vektorler, esik):
    """acgöz yiginlama: bir metin mevcut kumenin ILK ornegiyle karsilastirilir
    (Kuhn vd.'nin yontemi bir siralamaya baglidir; bu sapma README'de yazili)."""
    kumeler = []
    for v in vektorler:
        if v is None:
            continue
        yerlesti = False
        for kume in kumeler:
            benzerlik = kosinus(v, kume[0])
            if benzerlik is not None and benzerlik >= esik:
                kume.append(v)
                yerlesti = True
                break
        if not yerlesti:
            kumeler.append([v])
    return [len(k) for k in kumeler]


def semantik_entropi(boyutlar, toplam):
    if toplam == 0 or not boyutlar:
        return None
    ps = [b / toplam for b in boyutlar]
    return -sum(p * math.log(p) for p in ps if p > 0)


def kol_f(serbest, duman, kayitlar):
    yaz("")
    yaz("=" * 57)
    yaz("KOL F - SEMANTIK KUMELEME (bge-m3 kosinus; yontem sapmasi belgeli)")
    yaz("=" * 57)
    if not serbest:
        yaz("  OLCULEMEDI: E'nin serbest kolu metin uretmedi")
        return
    for esik in (0.70, 0.80):
        yaz("")
        yaz("  kosinus esigi %.2f" % esik)
        sayilar, entropiler = [], []
        for kayit in serbest:
            vektorler = []
            for metin in kayit["metinler"]:
                anahtar = ("F|%d|%s" % (kayit["no"], metin))
                if anahtar in kayitlar:
                    vektorler.append(kayitlar[anahtar])
                    continue
                v = gomme(metin)
                kayitlar[anahtar] = v
                vektorler.append(v)
            boyutlar = kumele(vektorler, esik)
            if not boyutlar:
                yaz("    F%-2d | OLCULEMEDI (vektor alinamadi)" % kayit["no"])
                continue
            e = semantik_entropi(boyutlar, sum(boyutlar))
            cogunluk = max(boyutlar) / sum(boyutlar)
            sayilar.append(len(boyutlar))
            if e is not None:
                entropiler.append(e)
            kayit["kume_sayisi_%.2f" % esik] = len(boyutlar)
            kayit["cogunluk_%.2f" % esik] = cogunluk
            kayit["semantik_entropi_%.2f" % esik] = e
            yaz("    F%-2d | ornek %2d | talimat yankisi %d | kume %d | cogunluk %.2f | sem-ent %s"
                % (kayit["no"], len(vektorler), kayit.get("talimat_yankisi", 0),
                   len(boyutlar), cogunluk,
                   "%.4f" % e if e is not None else "YOK"))
        if sayilar:
            yaz("    ozet: kume sayisi ort %.2f (min %d max %d) | semantik entropi ort %s"
                % (statistics.mean(sayilar), min(sayilar), max(sayilar),
                   "%.4f" % statistics.mean(entropiler) if entropiler else "YOK"))


# -------------------------------------------------------------------- KOL G
GUVEN_DESESI = re.compile(r"GUVEN\s*:\s*(\d{1,3})", re.IGNORECASE)


def guven_ayristir(metin):
    """Guven SADECE GUVEN: etiketiyle okunur. Etiketsiz sayilar (talimat yankisi,
    sik metnindeki '95.129.129' gibi) guven sayilmaz -> fail-closed."""
    katlasilmis = metin.translate(TURKCE_KATLAR)
    tum = [int(m) for m in GUVEN_DESESI.findall(katlasilmis)]
    aday = [v for v in tum if 0 <= v <= 100]
    return (aday[-1] if aday else None), len(tum)


def tam_eslesme(metin, altin):
    """Altin metin cevaba gecmis mi; rakam siniri zorunlu: '8' altini '128'
    icinde yanlis pozitif vermesin, '0,1' altini '0,15' icinde gecerli sayilmasin."""
    deseni = r"(?<![\d.,])%s(?![\d.,])" % re.escape(altin)
    return re.search(deseni, metin, flags=re.IGNORECASE) is not None


def kol_g(duman, kayitlar):
    sorular = SORULAR[:3] if duman else SORULAR[:10]
    yaz("")
    yaz("=" * 57)
    yaz("KOL G - SOZLU GUVEN (0-100) | sayi YALNIZ GUVEN: etiketinden okunur")
    yaz("=" * 57)
    for i, satir in enumerate(sorular):
        soru, dogru, tip, sekiller, yer = secenekler(satir, i)
        istem = ("SORU: %s\nSIKKLAR:\n%s\n\nBirinci satira secigin metnini yaz. "
                 "Ikinci satir tam olarak GUVEN: ile baslasin ve sonrasinda 0 ile "
                 "100 arasinda tek bir tam sayi olsun."
                 % (soru, "\n".join("%s) %s" % (h, s)
                                    for h, s in zip(HARFLER, sekiller))))
        if i == 0:
            yaz("  istem kalibi (bir kerelik):")
            yaz("  %r" % istem[-230:])
        govde = govde_chat(istem, top=None, tavan=64, sicaklik=0.0)
        try:
            t0 = time.time()
            yanit = post("/api/chat", govde)
            duvar = time.time() - t0
        except urllib.error.HTTPError as h:
            yaz("G%-2d | HATA %s" % (i + 1, h.code))
            continue
        icerik = ((yanit.get("message", {}) or {}).get("content", "") or "").strip()
        guven, etiket_sayisi = guven_ayristir(icerik)
        dogri = tam_eslesme(icerik, dogru)
        r = {"no": i + 1, "duvar": duvar, "icerik": icerik, "guven": guven,
             "dogru_mu": dogri, "guven_etiketi": etiket_sayisi,
             "dogru_metin": dogru}
        kayitlar.append(r)
        yaz("G%-2d | %5.2f sn | guven %-4s | GUVEN etiketi %d | cevap dogru mu %s | %r"
            % (i + 1, duvar, str(guven) if guven is not None else "YOK",
               etiket_sayisi, "EVET" if dogri else "HAYIR",
               icerik.replace("\n", " / ")[:70]))
    gecen = [k for k in kayitlar if isinstance(k, dict) and k.get("guven") is not None]
    yaz("")
    yaz("  G ozet: ayristirilabilen %d/%d" % (len(gecen), len(sorular)))
    if gecen:
        yaz("  genel guven ortalamasi %.1f | min %d | max %d"
            % (statistics.mean(k["guven"] for k in gecen),
               min(k["guven"] for k in gecen), max(k["guven"] for k in gecen)))
        d1 = [k["guven"] for k in gecen if k["dogru_mu"]]
        d0 = [k["guven"] for k in gecen if not k["dogru_mu"]]
        if d1:
            yaz("  dogru cevaplarin guveni: n=%d ort %.1f (min %d max %d)"
                % (len(d1), statistics.mean(d1), min(d1), max(d1)))
        if d0:
            yaz("  yanlis cevaplarin guveni: n=%d ort %.1f (min %d max %d)"
                % (len(d0), statistics.mean(d0), min(d0), max(d0)))
    if len(gecen) < len(sorular):
        yaz("  [UYARI] %d soruda GUVEN: etiketi (veya etiketten okunabilir 0-100 "
            "sayisi) YOK -> bu sorular yukaridaki ortalamalara GIRMEZ, ayri sayilir"
            % (len(sorular) - len(gecen)))


# --------------------------------------------------------------------- main
def json_yaz(ad, veri):
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / ("%s.json" % ad)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    yaz("  -> %s yazildi (%d kayit)" % (yol.name, len(veri)))


def main():
    ayirici = argparse.ArgumentParser()
    ayirici.add_argument("--kol", default="olcum",
                         choices=["a", "h", "b", "c", "d", "e", "f", "g", "olcum"])
    ayirici.add_argument("--duman", action="store_true")
    secim = ayirici.parse_args()

    yaz("EMINLIK OLCUM KAFESI")
    yaz("  baslangic: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    yaz("  python %s | %s %s" % (platform.python_version(),
                                  platform.system(), platform.release()))
    yaz("  ollama %s | sohbet %s | gomme %s" % (model_bilgi(), SOHBET, GOMME))
    yaz("  mod: %s | kol: %s" % ("DUMAN" if secim.duman else "TAM", secim.kol))
    yaz("  sozlesme notu: eval_count logprob kayindan 1 fazladir (probda olculen "
        "off-by-one); ortalamalar KAYIT sayisina alinir")

    if secim.kol == "a":
        kol_a(secim.duman)
    elif secim.kol == "h":
        kol_h(secim.duman)
    else:
        b_kayit, c_kayit, d_kayit, e_kayit, g_kayit = [], [], [], [], []
        f_oturak = {}
        if secim.kol in ("b", "olcum"):
            kol_b(secim.duman, b_kayit)
            b_ozeti(b_kayit)
        if secim.kol in ("c", "olcum"):
            kol_c(secim.duman, c_kayit)
        if secim.kol in ("d", "olcum"):
            kol_d(secim.duman, d_kayit)
        serbest = []
        if secim.kol in ("e", "f", "olcum"):
            serbest = kol_e(secim.duman, e_kayit)
        if secim.kol in ("f", "olcum"):
            kol_f(serbest, secim.duman, f_oturak)
        if secim.kol in ("g", "olcum"):
            kol_g(secim.duman, g_kayit)
        # tek kol kosumunda diger kol json'larini EZME: yalnizca kosan kol yazilir
        if secim.kol in ("b", "olcum"):
            json_yaz("b", b_kayit)
        if secim.kol in ("c", "olcum"):
            json_yaz("c", c_kayit)
        if secim.kol in ("d", "olcum"):
            json_yaz("d", d_kayit)
        if secim.kol in ("e", "f", "olcum"):
            json_yaz("e", e_kayit)
            json_yaz("serbest", serbest)
        if secim.kol in ("g", "olcum"):
            json_yaz("g", g_kayit)

    yaz("")
    yaz("bitti: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
