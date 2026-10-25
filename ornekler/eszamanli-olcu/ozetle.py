#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`eszamanli_olcu.py` kaydını okuyup kol başına özet çıkarır.

Kayıt biçimi: satır satır `#KAYIT {json}` ve `#DALGA {json}`. Ayrı bir şey
hesaplamaz, yalnız okur — yani özeti koşum bittikten sonra istediğiniz kadar
yeniden üretebilirsiniz.

Yüzdelik yöntemi: en yakın rütbe (nearest-rank), indis = tavan(p x n) - 1.
n = 5 iken p95 listenin en büyüğüdür; bu bilinçli bir seçim, çünkü beş
tekrarda "kuyruğun kuyruğu"nu ölçmüş oluruz.

İkinci iş: `--kirletme` sunucu günlüğünü (Ollama'nın `server.log`u) tarayıp
ölçüm penceresine yabancı isteğin girip girmediğini sayar. Ayrı bir şey
ölçmez; yalnızca satırları sayar.

Bağımlılık: yalnızca Python standard kütüphanesi.
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

BURADA = Path(__file__).resolve().parent

KAYIT_OTU = "#KAYIT "
DALGA_OTU = "#DALGA "
SAAT_OTU = re.compile(r"time=\d{4}-\d{2}-\d{2}T(\d{2}:\d{2}:\d{2})")
YENI_ISTEM_OTU = re.compile(r"id\s+(\d+)\s*\|.*?task\.n_tokens\s*=\s*(\d+)")


def ayristir(cizgiler):
    """Log satırlarından kayıt ve dalga listelerini döndürür."""
    kayitlar, dalgalar = [], []
    for c in cizgiler:
        c = c.strip()
        if c.startswith(KAYIT_OTU):
            kayitlar.append(json.loads(c[len(KAYIT_OTU):]))
        elif c.startswith(DALGA_OTU):
            dalgalar.append(json.loads(c[len(DALGA_OTU):]))
    return kayitlar, dalgalar


def yuzdelik(degerler, p):
    s = sorted(degerler)
    if not s:
        return None
    r = math.ceil(p / 100.0 * len(s)) - 1
    return s[max(0, min(r, len(s) - 1))]


def iyi_mi(kayit):
    """Bir istek yalnız gerçekten cevap üretmişse özete girer.

    Fail-closed: HTTP 200 olup boş metin ya da `eval_count` 0 dönen istek
    'başarılı' sayılmaz; ortalamadan sessizce düşmek yerine hane sayısına
    yazılır.
    """
    return (kayit.get("hata") is None
            and kayit.get("http_kod") == 200
            and (kayit.get("eval_count") or 0) > 0)


def merdiven(kayitlar):
    """Dalga içi isteklerin duvarını sıralı verip ardışık adımları hesaplar.

    Sayfanın 'kuyruk mu, yarış mı' okuması bu tabloya dayanır: sıralı kuyrukta
    adımlar yaklaşık tek istek süresine eşit ve sabit çıkar, gerçek eşzamanlılıkta
    ise isteklerin duvarı üst üste biner (adımlar küçülür). Yalnız iyi kayıtlar
    girer; hatalı istek merdivende bir basamak uydurmaz.
    """
    grup = defaultdict(list)
    for k in kayitlar:
        if iyi_mi(k):
            grup[(int(k["k"]), int(k["tekrar"]))].append(float(k["duvar_sn"]))
    sonuc = defaultdict(list)
    for (seviye, tekrar), degerler in sorted(grup.items()):
        s = sorted(degerler)
        sonuc[seviye].append({"tekrar": tekrar, "degerler": s,
                              "adimlar": [round(b - a, 4) for a, b in zip(s, s[1:])]})
    return dict(sonuc)


def gunluk_tara(cizgiler, pencere=None):
    """Ollama sunucu günlüğünün satırlarını (saat, slot id, istem token) üçlüsüne çevirir.

    llama.cpp satırlarında zaman damgası yoktur (Ollama `--no-log-timestamps`
    ile çalıştırır); o yüzden her 'new prompt' satırı kendinden önce görülen
    son `time=` etiketini taşır. Damgası henüz bulunmayan satır pencere
    dışındadır (fail-closed: saati bilinmeyen bir isteği ölçüm aralığına
    yazmayız).
    """
    saat = None
    out = []
    for c in cizgiler:
        m = SAAT_OTU.search(c)
        if m:
            saat = m.group(1)
        if "new prompt," not in c:
            continue
        n = YENI_ISTEM_OTU.search(c)
        if not n:
            continue
        if pencere and not (pencere[0] <= (saat or "") <= pencere[1]):
            continue
        out.append((saat, int(n.group(1)), int(n.group(2))))
    return out


def kirletme_ozeti(ucguler, beklenen_token):
    """İstem token boyutuna ve yuva id'sine göre sayım; beklenmeyen boyutlar listelenir.

    Beklenmeyen boyut otomatik olarak 'yabancı' hükmü değildir: kafesi yazan
    betiğin kendi kısa istemleri (model boşaltma çağrısı) de buraya düşer.
    Sayan ve gösteren bu, karar veren insandır.
    """
    boyut, slot = defaultdict(int), defaultdict(int)
    for _, sid, tok in ucguler:
        boyut[tok] += 1
        slot[sid] += 1
    return {"toplam": len(ucguler),
            "dagilim": dict(sorted(boyut.items())),
            "slotlar": dict(sorted(slot.items())),
            "beklenmeyen": [u for u in ucguler if u[2] != beklenen_token]}


def kirletme_yazdir(ozet, beklenen_token, cikti):
    w = cikti.write
    w("\nKIRLETME DENETIMI (sunucu gunlugunden, yeni-istem satirlari)\n")
    w("toplam yeni-istem satiri: {0}\n".format(ozet["toplam"]))
    w("istem token boyutlari: {0}  (beklenen: {1})\n".format(
        ", ".join("{0} token x {1}".format(t, a) for t, a in ozet["dagilim"].items()),
        beklenen_token))
    w("yuva id dagilimi: {0}\n".format(
        ", ".join("id {0}: {1}".format(s, a) for s, a in ozet["slotlar"].items())))
    if ozet["beklenmeyen"]:
        w("beklenmeyen boyutlu satirlar:\n")
        for saat, sid, tok in ozet["beklenmeyen"]:
            w("  {0} | id {1} | {2} token\n".format(saat, sid, tok))
        w("Yorum: bu satirlar ya baska bir istemcinin istekleri (KOŞUM KIRLIDIR) "
          "ya da kafesin kendi kısa istemleridir (model boşaltma). Saat ve yuva "
          "id'sine bakarak ayirin.\n")
    else:
        w("Beklenmeyen boyut yok: penceredeki her yeni-istem satırı {0} token.\n".format(
            beklenen_token))
    w("\n")


def ozet(kayitlar, dalgalar):
    by_k = defaultdict(list)
    for k in kayitlar:
        by_k[int(k["k"])].append(k)
    kd = defaultdict(list)
    for d in dalgalar:
        kd[int(d["k"])].append(d)

    sonuc = {}
    for seviye in sorted(set(by_k) | set(kd)):
        ks = by_k.get(seviye, [])
        ds = kd.get(seviye, [])
        iyiler = [k for k in ks if iyi_mi(k)]
        hatalar = [k for k in ks if not iyi_mi(k)]
        beklenen = sum(int(d.get("beklenen", 0)) for d in ds)
        tamamlanan = sum(int(d.get("tamamlanan", 0)) for d in ds)
        yapilan_toplam = sum(float(d.get("yapilan_sn", 0.0)) for d in ds)
        uretim = sum(int(k.get("eval_count") or 0) for k in iyiler)
        duvarlar = [float(k["duvar_sn"]) for k in iyiler]
        tek_hiz = [int(k["eval_count"]) / float(k["decode_sn"])
                   for k in iyiler
                   if k.get("decode_sn") and float(k["decode_sn"]) > 0]
        sonuc[seviye] = {
            "dalga": len(ds),
            "beklenen_istek": beklenen,
            "kayit_istek": len(ks),
            "tamamlanan": tamamlanan,
            "hatali": len(hatalar),
            "eksik_dalga": sum(1 for d in ds
                               if int(d.get("tamamlanan", 0)) != int(d.get("beklenen", 0))),
            "p50_duvar": yuzdelik(duvarlar, 50),
            "p95_duvar": yuzdelik(duvarlar, 95),
            "maks_duvar": max(duvarlar) if duvarlar else None,
            "ort_yapilan": (yapilan_toplam / len(ds)) if ds else None,
            "toplam_yapilan": yapilan_toplam,
            "uretilen_token": uretim,
            "sistem_tok_sn": (uretim / yapilan_toplam) if yapilan_toplam > 0 else None,
            "tek_istek_tok_sn": yuzdelik(tek_hiz, 50),
            "on_yuk_token": sum(int(k.get("prompt_eval_count") or 0) for k in iyiler),
            "onek_bellekten": sum(int(k.get("prompt_eval_cached_count") or 0) for k in iyiler),
        }
    return sonuc


def tablo_oku(ozetler):
    """Kol sırası + K=1'e oran. K=1 yoksa oran None olarak geçer (uydurma değil)."""
    s1 = ozetler.get(1)
    for seviye in sorted(ozetler):
        o = ozetler[seviye]
        if o["ort_yapilan"] is None:
            continue
        oran = (o["ort_yapilan"] / s1["ort_yapilan"]) if (
            s1 and s1["ort_yapilan"]) else None
        verim = (o["sistem_tok_sn"] / s1["sistem_tok_sn"]) if (
            s1 and s1["sistem_tok_sn"] and o["sistem_tok_sn"]) else None
        yield seviye, o, oran, verim


def yazdir(ozetler, cikti, merdiven_veri=None):
    w = cikti.write
    w("\nOLCU OZETI (kayittan yeniden hesaplandi)\n")
    w("kol | dalga | beklenen/kayit | hatali | eksik dalga | p50 duvar | p95 duvar | maks duvar | ort yapilan | sistem tok/sn | tek istek tok/sn\n")
    for seviye, o, oran, verim in tablo_oku(ozetler):
        w("K{0} | {1} | {2}/{3} | {4} | {5} | {6} | {7} | {8} | {9} | {10} | {11}\n".format(
            seviye, o["dalga"], o["beklenen_istek"], o["kayit_istek"], o["hatali"],
            o["eksik_dalga"],
            "-" if o["p50_duvar"] is None else round(o["p50_duvar"], 2),
            "-" if o["p95_duvar"] is None else round(o["p95_duvar"], 2),
            "-" if o["maks_duvar"] is None else round(o["maks_duvar"], 2),
            round(o["ort_yapilan"], 2),
            "-" if o["sistem_tok_sn"] is None else round(o["sistem_tok_sn"], 2),
            "-" if o["tek_istek_tok_sn"] is None else round(o["tek_istek_tok_sn"], 2),
        ))
        if oran is not None and seviye != 1:
            w("     K{0}: bir dalga K=1'in {1} kati; sistem verimi K=1'in {2} kati\n".format(
                seviye, round(oran, 2),
                "-" if verim is None else round(verim, 2)))
    for seviye in sorted(ozetler):
        o = ozetler[seviye]
        if o["beklenen_istek"]:
            w("K{0} on-yukleme: {1} token, bunlarin {2} onbeki bellekten\n".format(
                seviye, o["on_yuk_token"], o["onek_bellekten"]))
    if merdiven_veri:
        w("\nMERDIVEN (dalga icindeki isteklerin duvari, kucukten buyuge; adimlar ardisi)\n")
        for seviye in sorted(merdiven_veri):
            if seviye < 2:
                continue
            satirlar = merdiven_veri[seviye]
            for dalga in satirlar:
                w("K{0} tekrar={1}: {2} | adimlar: {3}\n".format(
                    seviye, dalga["tekrar"],
                    " / ".join("{0:.2f}".format(x) for x in dalga["degerler"]),
                    " / ".join("{0:.2f}".format(x) for x in dalga["adimlar"]) or "-"))
            adimlar = [a for dalga in satirlar for a in dalga["adimlar"]]
            if adimlar:
                w("K{0}: adim araligi {1:.2f}-{2:.2f} sn, adim ortalamasi {3:.2f} sn "
                  "({4} adim)\n".format(seviye, min(adimlar), max(adimlar),
                                        sum(adimlar) / len(adimlar), len(adimlar)))
    w("\n")


def _test():
    """Ayrıştırma ve toplama katmanının kendi testi (Ollama'ya dokunmaz)."""
    satirlar = [
        "#YORUM bu bir yorum satiri, okunmaz",
        '#KAYIT {"k": 2, "tekrar": 1, "no": 1, "duvar_sn": 1.0, "decode_sn": 1.0, '
        '"eval_count": 10, "prompt_eval_count": 40, "prompt_eval_cached_count": 0, '
        '"http_kod": 200, "hata": null}',
        '#KAYIT {"k": 2, "tekrar": 1, "no": 2, "duvar_sn": 2.0, "decode_sn": 2.0, '
        '"eval_count": 10, "prompt_eval_count": 40, "prompt_eval_cached_count": 0, '
        '"http_kod": 200, "hata": null}',
        '#KAYIT {"k": 2, "tekrar": 2, "no": 1, "duvar_sn": 3.0, "decode_sn": 1.0, '
        '"eval_count": 10, "prompt_eval_count": 40, "prompt_eval_cached_count": 0, '
        '"http_kod": 200, "hata": null}',
        '#KAYIT {"k": 2, "tekrar": 2, "no": 2, "duvar_sn": 4.0, "decode_sn": 1.0, '
        '"eval_count": 10, "prompt_eval_count": 40, "prompt_eval_cached_count": 0, '
        '"http_kod": 500, "hata": "HTTP 500"}',
        '#DALGA {"k": 2, "tekrar": 1, "yapilan_sn": 2.0, "beklenen": 2, "tamamlanan": 2, "hata_sayisi": 0}',
        '#DALGA {"k": 2, "tekrar": 2, "yapilan_sn": 4.0, "beklenen": 2, "tamamlanan": 1, "hata_sayisi": 1}',
        '#KAYIT {"k": 1, "tekrar": 1, "no": 1, "duvar_sn": 2.0, "decode_sn": 1.0, '
        '"eval_count": 20, "prompt_eval_count": 40, "prompt_eval_cached_count": 5, '
        '"http_kod": 200, "hata": null}',
        '#DALGA {"k": 1, "tekrar": 1, "yapilan_sn": 2.0, "beklenen": 1, "tamamlanan": 1, "hata_sayisi": 0}',
    ]
    k, d = ayristir(satirlar)
    assert len(k) == 5 and len(d) == 3, (len(k), len(d))
    o = ozet(k, d)

    # K=2: dort kayit, biri HTTP 500 -> ozete girmez; ucret iyi istek.
    a = o[2]
    assert a["kayit_istek"] == 4 and a["hatali"] == 1, a
    assert a["beklenen_istek"] == 4 and a["tamamlanan"] == 3, a
    assert a["eksik_dalga"] == 1, a
    assert round(a["p50_duvar"], 6) == 2.0, a          # n=3 -> tavan(1.5)-1 = 1
    assert round(a["p95_duvar"], 6) == 3.0, a          # n=3 -> tavan(2.85)-1 = 2
    assert round(a["maks_duvar"], 6) == 3.0, a          # hatali istek dahil degil
    assert round(a["ort_yapilan"], 6) == 3.0, a         # (2+4)/2
    assert round(a["sistem_tok_sn"], 6) == round(30 / 6.0, 6), a
    assert round(a["tek_istek_tok_sn"], 6) == 10.0, a
    assert a["onek_bellekten"] == 0, a

    # K=1: tek iyi istek, onbek bellek sayimi tasiniyor.
    b = o[1]
    assert round(b["p50_duvar"], 6) == 2.0 and round(b["p95_duvar"], 6) == 2.0, b
    assert b["uretilen_token"] == 20 and b["on_yuk_token"] == 40, b
    assert b["onek_bellekten"] == 5, b

    # Bos girdi: sifir bölmesine düsmemeli, özet None üretmeli.
    bos = ozet([], [])
    assert bos == {}, bos
    bos2 = ozet([{"k": 3, "duvar_sn": 1.0, "http_kod": 200, "hata": None,
                  "eval_count": 0}], [])
    assert bos2[3]["p50_duvar"] is None and bos2[3]["hatali"] == 1, bos2[3]
    assert bos2[3]["sistem_tok_sn"] is None, bos2[3]

    # kismi liste: tek degerli listede p50 = p95 = degerin kendisi.
    assert yuzdelik([7.5], 50) == 7.5 and yuzdelik([7.5], 95) == 7.5, "tek deger"

    # merdiven: dalga icindeki iyi isteklerin duvari sirali + ardisik adimlar.
    m = merdiven(k)
    assert [x["tekrar"] for x in m[2]] == [1, 2], m[2]
    assert m[2][0]["degerler"] == [1.0, 2.0], m[2][0]
    assert m[2][0]["adimlar"] == [1.0], m[2][0]
    # tekrar=2'de ikinci istek HTTP 500: iyi sayilmaz, merdivene girmez.
    assert m[2][1]["degerler"] == [3.0], m[2][1]
    assert m[2][1]["adimlar"] == [], m[2][1]
    assert m[1][0]["degerler"] == [2.0] and m[1][0]["adimlar"] == [], m[1][0]
    # K olmayan kol: anahtar uretilmez, bos girdi patlamaz.
    assert merdiven([]) == {}, "bos merdiven"

    # gunluk_tara: llama.cpp satirlari damgasizdir, son gorulen saat tasinir.
    gunluk = [
        'time=2026-10-19T12:19:56.658+03:00 level=INFO source=llama_server.go:1083 '
        'msg="loading model via llama-server"',
        'slot   operator(): id  0 | task 0 | new prompt, n_ctx_slot = 4096, '
        'n_keep = 4, task.n_tokens = 74',
        'slot      release: id  0 | task 0 | stop processing: n_tokens = 138, truncated = 0',
        'time=2026-10-19T12:20:04.100+03:00 level=INFO source=routes.go:1 msg="ok"',
        'slot   operator(): id  1 | task 5 | new prompt, n_ctx_slot = 4096, '
        'n_keep = 4, task.n_tokens = 74',
        'slot   operator(): id  2 | task 9 | new prompt, n_ctx_slot = 4096, '
        'n_keep = 4, task.n_tokens = 32',
        'time=2026-10-19T12:24:00.000+03:00 level=INFO source=routes.go:1 msg="ok"',
        'slot   operator(): id  0 | task 77 | new prompt, n_ctx_slot = 4096, '
        'n_keep = 4, task.n_tokens = 99',
    ]
    u = gunluk_tara(gunluk)
    assert len(u) == 4, u
    assert [x[2] for x in u] == [74, 74, 32, 99], u
    assert [x[0] for x in u] == ["12:19:56", "12:20:04", "12:20:04", "12:24:00"], u
    assert [x[1] for x in u] == [0, 1, 2, 0], u
    # pencere: aralik disindaki satir sayilmaz.
    assert [x[2] for x in gunluk_tara(gunluk, ("12:19:50", "12:23:35"))] == [74, 74, 32], "pencere"
    # fail-closed: hic damga gorulmeden gelen satir pencereye girmez.
    damgasiz = ['slot   operator(): id  0 | task 0 | new prompt, n_ctx_slot = 4096, '
                'n_keep = 4, task.n_tokens = 74']
    assert gunluk_tara(damgasiz) == [(None, 0, 74)], "damgasiz ama sayimda"
    assert gunluk_tara(damgasiz, ("12:00:00", "12:30:00")) == [], "damgasiz pencerede yok"
    assert gunluk_tara([]) == [], "bos gunluk"

    k_ozet = kirletme_ozeti(u, 74)
    assert k_ozet["toplam"] == 4, k_ozet
    assert k_ozet["dagilim"] == {32: 1, 74: 2, 99: 1}, k_ozet
    assert k_ozet["slotlar"] == {0: 2, 1: 1, 2: 1}, k_ozet
    assert [x[2] for x in k_ozet["beklenmeyen"]] == [32, 99], k_ozet
    assert kirletme_ozeti([], 74)["toplam"] == 0, "bos sayim patlamaz"
    from io import StringIO
    buf = StringIO()
    kirletme_yazdir(k_ozet, 74, buf)
    assert "beklenmeyen boyutlu satirlar" in buf.getvalue(), buf.getvalue()[:200]
    buf2 = StringIO()
    kirletme_yazdir(kirletme_ozeti([x for x in u if x[2] == 74], 74), 74, buf2)
    assert "Beklenmeyen boyut yok" in buf2.getvalue(), buf2.getvalue()

    print("TEST TAMAM: ayristirma, yuzdelik, merdiven, kirletme sayimi, "
          "hatali/eksik sayimi ve sifir korumasi")


def _kok_dogrula(yol, tur):
    # Ozet araci yalniz iki yerden okur: kafes cikti kayitlari ve sunucu gunlogu.
    cozulen = os.path.realpath(yol)
    kok1 = os.path.realpath(str(BURADA / "cikti"))
    kok2 = os.path.expanduser("~")
    if not (cozulen.startswith(kok1 + os.sep) or cozulen.startswith(kok2 + os.sep)):
        print("HATA: {0} izinli kokte degil: {1}".format(tur, cozulen))
        return None
    return cozulen


def main():
    ayristirici = argparse.ArgumentParser(
        prog="ozetle.py",
        description="eszamanli_olcu kaydini ozetler; --kirletme ile sunucu gunlugunu tarar.")
    ayristirici.add_argument("kayit", nargs="?",
                             help="ozetlenecek kosum kaydi (cikti/eszamanli-kaydi-*.txt)")
    ayristirici.add_argument("--kirletme", metavar="GUNLUK",
                             help="Ollama server.log kirletme denetimi (yol deger olarak verilir)")
    ayristirici.add_argument("--istem", type=int, default=74,
                             help="beklenen istem boyutu (varsayilan 74 token)")
    ayristirici.add_argument("--pencere", metavar="SAAT-SAAT",
                             help="yalniz bu saat araligi, orn. 12:19:50-12:23:35")
    ayristirici.add_argument("--test", action="store_true", help="oz-sinav")
    args = ayristirici.parse_args()

    if args.test:
        _test()
        return 0

    pencere = None
    if args.pencere:
        a, b = args.pencere.split("-")
        pencere = (a.strip(), b.strip())

    if args.kirletme:
        beklenen = args.istem
        gunluk_p = Path(_kok_dogrula(args.kirletme, "gunluk"))
        if gunluk_p is None:
            return 2
        if not gunluk_p.is_file():
            print("HATA: gunluk dosyasi bulunamadi: {0}".format(gunluk_p))
            return 2
        with gunluk_p.open(encoding="utf-8", errors="replace") as f:
            uclu = gunluk_tara(f, pencere)
        print("gunluk: {0}   beklenen istem boyutu: {1} token   pencere: {2}".format(
            gunluk_p, beklenen, "-".join(pencere) if pencere else "tum dosya"))
        if not uclu:
            print("HATA: günlekte 'new prompt' satırı bulunamadı — yanlış dosya ya da "
                  "boş pencere. Denetim yapılmış sayılmaz.")
            return 1
        kirletme_yazdir(kirletme_ozeti(uclu, beklenen), beklenen, sys.stdout)
        return 0

    if not args.kayit:
        ayristirici.print_usage(sys.stderr)
        return 2
    kayit_p = Path(_kok_dogrula(args.kayit, "kayit"))
    if kayit_p is None:
        return 2
    if not kayit_p.is_file():
        print("HATA: kayit dosyasi bulunamadi: {0}".format(kayit_p))
        return 2
    with kayit_p.open(encoding="utf-8") as f:
        kayitlar, dalgalar = ayristir(f)
    if not kayitlar and not dalgalar:
        print("HATA: kayıtta '#KAYIT' ya da '#DALGA' satırı yok — koşum yarıda mı kaldı?")
        return 1
    oz = ozet(kayitlar, dalgalar)
    yazdir(oz, sys.stdout, merdiven(kayitlar))
    eksik = sum(o["eksik_dalga"] + o["hatali"] for o in oz.values())
    if eksik:
        print("UYARI: {} eksik dalga / hatali istek. Sayilar eksik kosumu anlatir; "
              "ozetteki 'eksik dalga' sutununa bakin.".format(eksik))
    return 0


if __name__ == "__main__":
    sys.exit(main())
