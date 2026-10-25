#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Eşzamanlılık ölçüm kafesi: aynı makinede 1 / 2 / 4 istek yarıştığında ne olur?

Ollama tek kullanıcılık bir sıra gibi davranır; `OLLAMA_NUM_PARALLEL` kaç isteğin
birlikte işlenebildiğini söyler (varsayılan 1). Bu kafes istemci tarafında K isteği
**aynı anda** salar ve üç şeyi birden kaydeder:

  1. istek başına duvar süresi (kullanıcının beklediği),
  2. sunucunun kendi faz süreleri (`total / load / prefill / decode`),
  3. bir dalganın toplam yapılır süresi (hepsinin bitmesi).

Sayfaya giren sayılar yalnız bu betiğin **bitmiş** kaydından alınır; özet
`ozetle.py` ile yeniden hesaplanır. Yalnızca Python standard kütüphanesi, tek uç
`http://127.0.0.1:11434`.

Koşum higienı: koşum sürerken Ollama'ya başka istek göndermeyin ve CPU'yu yoran
başka bir iş çalıştırmayın.
"""

import argparse
import json
import platform
import sys
import threading
import time
import urllib.error
import urllib.request

_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


UC = _url_dogrula("http://127.0.0.1:11434")
CHAT = _url_dogrula(UC + "/api/chat")
PS = _url_dogrula(UC + "/api/ps")
VERSION = _url_dogrula(UC + "/api/version")

SOHBET_MODELI = "qwen2.5:3b-instruct-q4_K_M"
NUM_PREDICT = 64
ZAMAN_ASIMI_SN = 900
DALGA_ARASI_SN = 3.0
BARIYER_BEKLEME_SN = 30.0

SORU = ("İstanbul'daki toplu taşıma seçeneklerini anlatan tek bir paragraf yaz; "
        "metro, metrobüs, vapur ve otobüs hattından söz et.")


def yaz(*parcalar):
    print(*parcalar, flush=True)


def gonder(uç, gövde, zaman_asımı=ZAMAN_ASIMI_SN):
    """(http_kod, veri_sözlüğü, hata_metni) döndürür; hata yoksa None.

    Asla sessiz olmaz: 200 dışı ya da ayrıştırılamayan yanıt hata alanına yazılır
    ve istek kaydı yine de loga geçer.
    """
    veri = json.dumps(gövde).encode("utf-8")
    istek = urllib.request.Request(_url_dogrula(uç), data=veri,
                                   headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asımı) as yanıt:
            kod = yanıt.getcode()
            gövde_ = yanıt.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, {}, "HTTPError {0}: {1}".format(e.code, e.reason)
    except Exception as e:  # zaman aşımı, bağlantı reddi, çökme
        return None, {}, "{0}: {1}".format(type(e).__name__, e)
    if kod != 200:
        return kod, {}, "beklenmeyen HTTP kodu {0}".format(kod)
    try:
        return 200, json.loads(gövde_), None
    except json.JSONDecodeError as e:
        return kod, {}, "bozuk JSON: {0} ({1} bayt)".format(e, len(gövde_))


def ns_sn(deger):
    """Ollama'nın nanosaniye alanını saniyeye çevirir; yoksa None."""
    if deger is None:
        return None
    return round(float(deger) / 1e9, 4)


def secenekler():
    return {"temperature": 0.0, "num_predict": NUM_PREDICT, "keep_alive": "10m"}


def istek_gövdesi(denek_no):
    return {"model": SOHBET_MODELI,
            "messages": [{"role": "user",
                          "content": "[denek {0}] {1}".format(denek_no, SORU)}],
            "stream": False,
            "options": secenekler()}


def tek_istek(k, tekrar_no, sıra_no, bariyer, kilitle, yerel, başlangıç):
    """Bir iş parçacığı: bariyerde bekler, sonra tek istek atar, kaydeder."""
    kayıt = {"k": k, "tekrar": tekrar_no, "no": sıra_no}
    try:
        bariyer.wait(timeout=BARIYER_BEKLEME_SN)
    except threading.BrokenBarrierError:
        kayıt.update({"bariyer_sn": None, "duvar_sn": 0.0, "http_kod": None,
                      "hata": "bariyer kırıldı (eşzamanlı başlanamadı)",
                      "eval_count": 0, "prompt_eval_count": 0,
                      "prompt_eval_cached_count": 0})
        with kilitle:
            yerel.append(kayıt)
        return
    kayıt["bariyer_sn"] = round(time.monotonic() - başlangıç, 4)
    t0 = time.monotonic()
    kod, veri, hata = gonder(CHAT, istek_gövdesi(tekrar_no))
    kayıt.update({
        "duvar_sn": round(time.monotonic() - t0, 4),
        "http_kod": kod,
        "hata": hata,
        "total_sn": ns_sn(veri.get("total_duration")),
        "load_sn": ns_sn(veri.get("load_duration")),
        "prefill_sn": ns_sn(veri.get("prompt_eval_duration")),
        "decode_sn": ns_sn(veri.get("eval_duration")),
        "prompt_eval_count": veri.get("prompt_eval_count", 0),
        "prompt_eval_cached_count": veri.get("prompt_eval_cached_count", 0),
        "eval_count": veri.get("eval_count", 0),
        "done_reason": veri.get("done_reason"),
        "cevap_uzunluk": len(veri.get("message", {}).get("content", "")),
    })
    with kilitle:
        yerel.append(kayıt)


def dalga(k, tekrar_no, kayıtlar):
    """K isteği aynı anda salar; döner: (yapılan_sn, tamamlanan, hata_sayısı)."""
    bariyer = threading.Barrier(k)
    kilitle = threading.Lock()
    yerel = []
    başlangıç = time.monotonic()
    işler = []
    for sıra_no in range(1, k + 1):
        t = threading.Thread(target=tek_istek,
                             args=(k, tekrar_no, sıra_no, bariyer, kilitle, yerel, başlangıç))
        t.start()
        işler.append(t)
    for t in işler:
        t.join(timeout=ZAMAN_ASIMI_SN + 60)
        if t.is_alive():
            with kilitle:
                yerel.append({"k": k, "tekrar": tekrar_no, "no": -1, "bariyer_sn": None,
                              "duvar_sn": None, "http_kod": None, "hata": None,
                              "eval_count": 0, "prompt_eval_count": 0,
                              "prompt_eval_cached_count": 0,
                              "aciklama": "istemci join zaman aşımında dönmedi"})
    yapılan = round(time.monotonic() - başlangıç, 4)
    for kayıt in yerel:
        kayıtlar.append(kayıt)
        yaz("#KAYIT " + json.dumps(kayıt, ensure_ascii=False, sort_keys=True))
    hatalı = sum(1 for kayıt in yerel
                 if kayıt.get("hata") or (kayıt.get("eval_count") or 0) == 0)
    yaz("#DALGA " + json.dumps({"k": k, "tekrar": tekrar_no, "yapilan_sn": yapılan,
                                "beklenen": k, "tamamlanan": len(yerel),
                                "hata_sayisi": hatalı}, ensure_ascii=False, sort_keys=True))
    return yapılan, len(yerel), hatalı


def durum_al():
    """`/api/ps` görüntüsü: bellekte hangi model, kaç bayt, ne zamana kadar."""
    try:
        with urllib.request.urlopen(PS, timeout=10) as yanıt:
            veri = json.loads(yanıt.read().decode("utf-8", "replace"))
    except Exception as e:
        return {"hata": "{0}: {1}".format(type(e).__name__, e)}
    return {"models": [{"name": m.get("name"), "size": m.get("size"),
                        "size_vram": m.get("size_vram"), "expires_at": m.get("expires_at"),
                        "processor": m.get("processor")}
                       for m in veri.get("models", [])]}


def başlık_yaz(etiket, kollar, tekrar, toplam_istek):
    try:
        with urllib.request.urlopen(VERSION, timeout=10) as yanıt:
            sürüm = json.loads(yanıt.read().decode("utf-8", "replace")).get("version")
    except Exception as e:
        yaz("#HATA sunucu sürümü okunamadı: {0}: {1}".format(type(e).__name__, e))
        return False
    yaz("#BASLIK " + json.dumps({
        "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": platform.python_version(),
        "isletim": "{0} {1}".format(platform.system(), platform.release()),
        "ollama_suru": sürüm,
        "model": SOHBET_MODELI,
        "secenekler": secenekler(),
        "kollar": kollar,
        "tekrar": tekrar,
        "toplam_istek": toplam_istek,
        "sunucu_etiketi": etiket,
        "uyari": ("OLLAMA_NUM_PARALLEL sunucunun kendi ortam değişkenidir; betik onu "
                  "okuyamaz. 'sunucu_etiketi' yazılan değerdir; fiilen uygulanıp "
                  "uygulanmadığı sunucu günlüğünden doğrulanır: 'server config' satiri "
                  "ve 'llama-server ... -np N' komut satiri."),
        "dalga_arasi_sn": DALGA_ARASI_SN,
        "bariyer_bekleme_sn": BARIYER_BEKLEME_SN,
    }, ensure_ascii=False, sort_keys=True))
    return True


def boşalt():
    """Modeli bellekten düşür: makineyi bulduğumuz gibi bırakıyoruz."""
    gövde = {"model": SOHBET_MODELI,
             "messages": [{"role": "user", "content": "boşalt"}],
             "stream": False, "keep_alive": 0,
             "options": {"temperature": 0.0, "num_predict": 1}}
    kod, _, hata = gonder(CHAT, gövde, zaman_asımı=120)
    yaz("#BOSALT " + json.dumps({"http_kod": kod, "hata": hata}, ensure_ascii=False))


def biçim_testi():
    """Koşucu ile ayrıştırıcının aynı kayıt biçiminde anlaştığını ağa çıkmadan doğrular."""
    import ozetle
    kayıtlar = []
    for sıra_no in (1, 2):
        kayıtlar.append({"k": 2, "tekrar": 1, "no": sıra_no,
                         "bariyer_sn": 0.001 * sıra_no, "duvar_sn": 1.0 * sıra_no,
                         "http_kod": 200, "hata": None, "total_sn": 1.0, "load_sn": 0.0,
                         "prefill_sn": 0.2, "decode_sn": 0.8, "prompt_eval_count": 40,
                         "prompt_eval_cached_count": 0, "eval_count": 10,
                         "done_reason": "stop", "cevap_uzunluk": 60})
    satırlar = ["#KAYIT " + json.dumps(k, ensure_ascii=False, sort_keys=True)
                for k in kayıtlar]
    satırlar.append("#DALGA " + json.dumps({"k": 2, "tekrar": 1, "yapilan_sn": 2.0,
                                            "beklenen": 2, "tamamlanan": 2,
                                            "hata_sayisi": 0},
                                           ensure_ascii=False, sort_keys=True))
    for alan in ("k", "tekrar", "no", "bariyer_sn", "duvar_sn", "http_kod", "hata",
                 "total_sn", "load_sn", "prefill_sn", "decode_sn", "prompt_eval_count",
                 "prompt_eval_cached_count", "eval_count", "done_reason", "cevap_uzunluk"):
        assert alan in satırlar[0], alan
    k, d = ozetle.ayristir(satırlar)
    assert len(k) == 2 and len(d) == 1, (len(k), len(d))
    ö = ozetle.ozet(k, d)
    assert set(ö) == {2}, sorted(ö)
    a = ö[2]
    assert a["p50_duvar"] == 1.0 and a["p95_duvar"] == 2.0, a
    assert a["sistem_tok_sn"] == 10.0, a
    assert a["tamamlanan"] == 2 and a["hatali"] == 0 and a["eksik_dalga"] == 0, a
    print("BICIM TESTI TAMAM: koşucunun yazdığı satırı ayrıştırıcı okuyor")


def main(argv):
    a = argparse.ArgumentParser(description="Eşzamanlılık ölçüm kafesi")
    a.add_argument("--kollar", default="1,2,4",
                   help="virgülle eşzamanlılık seviyeleri (varsayilan 1,2,4)")
    a.add_argument("--tekrar", type=int, default=5, help="seviye başına dalga sayısı")
    a.add_argument("--sunucu",
                   default="OLLAMA_NUM_PARALLEL tanimli degil (Ollama varsayilani 1)",
                   help="sunucu ayarı etiketi (betik okuyamaz; server.log'daki "
                        "'server config' ve '-np' satirlariyla dogrulanir)")
    a.add_argument("--duman", action="store_true", help="kısa koşum: K=1 ve K=2, tek tekrar")
    a.add_argument("--test-format", dest="test_format", action="store_true",
                   help="biçim testi: ağa çıkmadan koşucu/ayrıştırıcı anlaşmasını doğrula")
    args = a.parse_args(argv[1:])

    if args.test_format:
        biçim_testi()
        return 0

    kollar = [int(x) for x in args.kollar.split(",") if x.strip()]
    tekrar = args.tekrar
    if args.duman:
        kollar, tekrar = [1, 2], 1
    if not kollar or tekrar < 1 or min(kollar) < 1:
        print("HATA: boş/geçersiz kol listesi ya da tekrar < 1")
        return 2
    toplam_istek = sum(k * tekrar for k in kollar)

    if not başlık_yaz(args.sunucu, kollar, tekrar, toplam_istek):
        print("HATA: sunucuya ulaşılamıyor ya da sürüm okunamadı — ölçüm yapılmadı.")
        return 2
    yaz("#PS_GIRIS " + json.dumps(durum_al(), ensure_ascii=False))
    yaz("#NOT {0} istek; her dalgadan sonra {1} sn boşluk, model 10m sicak tutuluyor."
        .format(toplam_istek, int(DALGA_ARASI_SN)))

    t0 = time.monotonic()
    kod, veri, hata = gonder(CHAT, istek_gövdesi(0))
    yaz("#ISITMA " + json.dumps({"duvar_sn": round(time.monotonic() - t0, 4),
                                 "http_kod": kod, "hata": hata,
                                 "eval_count": veri.get("eval_count", 0),
                                 "load_sn": ns_sn(veri.get("load_duration"))},
                                ensure_ascii=False))
    if hata or (veri.get("eval_count") or 0) == 0:
        print("HATA: ısıtma isteği başarısız — soğuk yükleme eşzamanlılık ölçümünü "
              "zehirler, koşum başlamadı.")
        return 3

    kayıtlar = []
    olcu_yapilan = 0.0
    for k in kollar:
        for tekrar_no in range(1, tekrar + 1):
            yapılan, tamamlanan, hatalı = dalga(k, tekrar_no, kayıtlar)
            olcu_yapilan += yapılan
            if tamamlanan != k or hatalı:
                yaz("#UYARI K{0}-t{1}: beklenen {0}, tamamlanan {2}, hatali {3}".format(
                    k, tekrar_no, tamamlanan, hatalı))
            time.sleep(DALGA_ARASI_SN)
        yaz("#PS_KOL " + json.dumps({"k": k, "ps": durum_al()}, ensure_ascii=False))

    boşalt()
    yaz("#PS_BITIS " + json.dumps(durum_al(), ensure_ascii=False))
    yaz("#BITIS " + json.dumps({"zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "toplam_kayit": len(kayıtlar),
                                "olcu_dalga_sn": round(olcu_yapilan, 2),
                                "kullanim": "python ozetle.py <bu-dosya> ile yeniden hesaplayin"},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
