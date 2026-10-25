# -*- coding: utf-8 -*-
"""Örnek 7 — çok turlu ajan döngüsü: Örnek 6'nın RAG'ini bir ARACA sarmak.

Sabit hat (Örnek 6) şunu yapar: soruyu göm -> parça getir -> bağlamı modele
okut -> cevap. Ajan döngüsü ise kararı modele bırakır: "bu soru için aracı
çağırır mısın, hangi argümanla, kaç kez?" Bu betik o farkın bu makinede ne
kadara mal olduğunu ölçer; ajan kurmak değil, ajanın faturasını görmek içindir.

Ölçülenler:
  A) aynı soruda sabit hat vs ajan döngüsü (duvar, tur sayısı, tokenlar)
  B) iki geçiş gerektiren karşılaştırma sorusu (döngü kaç turda kapanıyor?)
  C) RAG gerektirmeyen soruda ikinci aracın seçimi (iki araçlı seçim)
  D) hicbir aracın yanitlayamayacagi soru (boşa yanan tur sayısı)
  E) araç tanımının isteme eklediği token (tools'lu vs tools'suz aynı istek)
  F) `tool_choice` alanının gerçekten bir şey yapıp yapmadığı (Ollama
     dokümanında listelenmez — burada sunucuya sorulur)
  G) `format` + `tools` birlikte (doküman HTTP 400 der; bu makinede?)
  H) araç sonucunu geri verirken `tool_name` alanının gerekip gerekmediği
     (doküman "önerilir" der; iki araç varken denenir)

Korpus ilk koşumda Vikipedi'den indirilir ve cikti/korpus.json'a yazılır;
sonraki koşumlar o dosyayı okur. Bilinçli: aynı gün içinde art arda korpus
çekimi Wikimedia'da HTTP 429 üretti (olc.py'da yaşandı). Gömme vektörleri de
Örnek 6/hibrit'in önbelleğiyle eşleşirse yeniden vektörleştirme atlanır.

Kullanım (Ollama açık, başka Ollama isteği gönderilmiyor olmalı):
    ../../.venv/Scripts/python.exe -u ajan.py > cikti/ajan-kaydi.txt 2>&1
"""

import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BURADA = Path(__file__).resolve().parent
sys.path.insert(0, str(BURADA.parent / "viki-rag"))
import viki_rag as v6                                   # noqa: E402

_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


OLLAMA = _url_dogrula("http://127.0.0.1:11434")   # 'localhost' istek başına ~2 sn ekliyor (ölçüldü)
CHAT = _url_dogrula(f"{OLLAMA}/api/chat")
SOHBET = getattr(v6, "SOHBET_MODELI")
KORPUS = BURADA / "cikti" / "korpus.json"
VEKTÖR_ÖNBELLEK = BURADA.parent / "viki-rag" / "cikti" / "vektor-indeks.json.gz"
MAKS_TUR = 5
NUM_PREDICT = 300


def model(yük):
    istek = urllib.request.Request(
        _url_dogrula(CHAT), data=json.dumps(yük).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(istek, timeout=900) as yanıt:
        return json.loads(yanıt.read().decode("utf-8"))


def faz(yanıt):
    """Ollama'nın nanosaniye alanlarını tek okunur satıra çevirir."""
    girdi = yanıt.get("prompt_eval_count", 0)
    önb = yanıt.get("prompt_eval_cached_count", 0) or 0
    öny = yanıt.get("prompt_eval_duration", 0) / 1e9
    çöz = yanıt.get("eval_duration", 0) / 1e9
    return ("sunucu %5.2f | yük %5.2f | ön-yük %4d tok / %5.2f sn [%6.1f tok/sn, "
            "%4d önb.] | çözme %3d tok / %5.2f sn [%5.1f tok/sn]" % (
                yanıt.get("total_duration", 0) / 1e9,
                yanıt.get("load_duration", 0) / 1e9,
                girdi, öny, (girdi / öny if öny else 0.0), önb,
                yanıt.get("eval_count", 0), çöz,
                (yanıt.get("eval_count", 0) / çöz if çöz else 0.0)))


# ------------------------------------------------------------- korpus ve indeks

def korpus_indir_ve_yazdır():
    kok = (BURADA / "cikti").resolve()
    guvenli = kok / "korpus.json"
    if not str(guvenli).startswith(str(kok) + os.sep):
        raise ValueError("korpus kaydi cikti dizininin disina yaziliyor: %s" % guvenli)
    if guvenli.exists():
        belgeler = json.loads(guvenli.read_text(encoding="utf-8"))
        print(f"[korpus] önbellekten {len(belgeler)} parça ({KORPUS.name})")
        return belgeler
    print("[korpus] Vikipedi'den indiriliyor (ilk koşum)...")
    belgeler = v6.korpus_olustur()
    kok.mkdir(parents=True, exist_ok=True)
    guvenli.write_text(json.dumps(belgeler, ensure_ascii=False), encoding="utf-8")
    print(f"[korpus] {len(belgeler)} parça {KORPUS.name} dosyasına yazıldı")
    return belgeler


def imza(belgeler):
    # Korpus onbellek imzasi; guvenlik amacli degil, degisiklik algilama amacli.
    return hashlib.sha1(
        "".join(f"{b['id']}|{len(b['metin'])}" for b in belgeler).encode("utf-8")
    ).hexdigest()


def indeks_kur(belgeler):
    """Vektörleri Örnek 6'nın önbelleğinden okumayı dener, olmazsa üretir."""
    if VEKTÖR_ÖNBELLEK.exists():
        with gzip.open(VEKTÖR_ÖNBELLEK, "rt", encoding="utf-8") as dosya:
            veri = json.load(dosya)
        if veri.get("model") == v6.GOMME_MODELI and veri.get("imza") == imza(belgeler):
            print(f"[indeks] önbellekten {len(veri['vektorler'])} vektör okundu")
            return list(zip(belgeler, veri["vektorler"]))
        print("[indeks] önbellek imzası uyuşmadı — yeniden vektörleştiriliyor")
    t0 = time.time()
    indeks = v6.indeksle(belgeler)
    print(f"[indeks] vektörleştirme {time.time() - t0:.1f} sn sürdü")
    return indeks


# ------------------------------------------------------------------- araçlar

def viki_ara(soru, indeks, k=3):
    skorlu = v6.getir(soru, indeks, k=k)
    if not skorlu:
        return "(Hiç parça bulunamadı.)"
    en_iyi = skorlu[0][0]
    if en_iyi < v6.ZAYIF_ESIK:
        return (f"(Eşik altında: en iyi benzerlik {en_iyi:.3f} < {v6.ZAYIF_ESIK}. "
                f"Belgelerde cevap olmayabilir; kullanıcıya bunu söyle.)")
    return "\n\n".join(f"[{b['id']}] benzerlik {s:.3f}\n{b['metin']}"
                       for s, b in skorlu)


BİRİMLER = {"km": 1000.0, "m": 1.0, "cm": 0.01, "sa": 3600.0, "dk": 60.0, "sn": 1.0}


def birim_donüştür(miktar, kaynak, hedef):
    if kaynak not in BİRİMLER or hedef not in BİRİMLER:
        return f"(Bilinmeyen birim: {kaynak} -> {hedef})"
    # BİLİNÇLİ BIRAKILDI: ölçüm bu hâliyle alındı (ajan-kaydi.txt, C senaryosu).
    # Bu çarpım hiçbir zaman <=0 olmaz, dolayısıyla süre<->uzunluk geçişi reddedilmiyor;
    # kayıttaki "1 sa = 3600 m" ve modelin "3600 metredir" cevabı bu kusurdan geldi.
    if BİRİMLER[kaynak] * BİRİMLER[hedef] <= 0:
        return "(Uzunluk ve süre birimleri birbirine çevrilmez.)"
    değer = float(miktar) * BİRİMLER[kaynak] / BİRİMLER[hedef]
    return f"{miktar} {kaynak} = {değer:.4g} {hedef}"


ARAÇLAR = [
    {
        "type": "function",
        "function": {
            "name": "viki_ara",
            "description": ("İstanbul toplu ulaşımıyla ilgili Vikipedi parçalarını "
                            "getirir. Tarih, hat, istasyon gibi bir bilgi soruluyorsa kullan."),
            "parameters": {
                "type": "object",
                "properties": {
                    "soru": {"type": "string", "description": "Aranan konu, tek cümle"},
                },
                "required": ["soru"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "birim_donustur",
            "description": "Uzunluk (km, m, cm) veya süre (sa, dk, sn) birimini çevirir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "miktar": {"type": "number", "description": "Çevrilecek sayı"},
                    "kaynak": {"type": "string", "description": "kaynak birim"},
                    "hedef": {"type": "string", "description": "hedef birim"},
                },
                "required": ["miktar", "kaynak", "hedef"],
            },
        },
    },
]

UYGULA = {
    "viki_ara": lambda a, indeks: viki_ara(str(a.get("soru", "")), indeks),
    "birim_donustur": lambda a, indeks: birim_donüştür(
        a.get("miktar", 0), str(a.get("kaynak", "")), str(a.get("hedef", ""))),
}

SİSTEM = ("Sen bir aracı olan bir asistansın. Bir bilgiyi kendi başına uydurma; "
          "aracı çağırıp sonucunu kullan. Araç sonucu yeterli değilse tekrar çağır.")


def argümanları_cevir(değer):
    """Sunucu burada sözlük döndürüyor; JSON metni gelirse de çalışsın."""
    if isinstance(değer, str):
        try:
            return json.loads(değer)
        except json.JSONDecodeError:
            return {}
    return değer or {}


# --------------------------------------------------------------- ajan döngüsü

def ajan(soru, indeks, etiket, tool_choice=None, isimle=True, bekle=MAKS_TUR):
    print("=" * 78)
    print(etiket)
    print(f"  soru: {soru}")
    mesajlar = [{"role": "system", "content": SİSTEM},
                {"role": "user", "content": soru}]
    duvar_toplam = 0.0
    girdi_toplam = çıktı_toplam = 0
    çağrılan = []
    tur = 0
    for tur in range(1, bekle + 1):
        yük = {"model": SOHBET, "messages": mesajlar, "stream": False,
               "tools": ARAÇLAR,
               "options": {"temperature": 0, "num_predict": NUM_PREDICT}}
        if tool_choice is not None:
            yük["tool_choice"] = tool_choice
        t0 = time.time()
        yanıt = model(yük)
        duvar = time.time() - t0
        duvar_toplam += duvar
        girdi_toplam += yanıt.get("prompt_eval_count", 0)
        çıktı_toplam += yanıt.get("eval_count", 0)
        mesaj = yanıt.get("message", {})
        çağrılar = mesaj.get("tool_calls") or []
        print(f"  tur {tur}: duvar {duvar:6.2f} sn | {faz(yanıt)} | "
              f"done_reason={yanıt.get('done_reason')}")
        if not çağrılar:
            içerik = (mesaj.get("content") or "").strip()
            print(f"  -> araç çağırmadı. cevap: {içerik[:220]!r}")
            break
        mesajlar.append({"role": "assistant", "content": mesaj.get("content") or "",
                        "tool_calls": çağrılar})
        for c in çağrılar:
            ad = c["function"]["name"]
            argüman = argümanları_cevir(c["function"].get("arguments"))
            çağrılan.append(ad)
            fn = UYGULA.get(ad)
            sonuç = fn(argüman, indeks) if fn else f"(Bilinmeyen araç: {ad})"
            araç_mesajı = {"role": "tool", "content": sonuç}
            if isimle:
                araç_mesajı["tool_name"] = ad
            mesajlar.append(araç_mesajı)
            print(f"     araç {ad}({json.dumps(argüman, ensure_ascii=False)[:110]}) "
                  f"-> {len(sonuç)} karakter, eşik/üretim sonucu kaydedildi")
    else:
        print(f"  ! {bekle} turda döngü kapanmadı — model araç çağırmaya devam etti")
    print(f"  ÖZET: {tur} tur | araçlar: {çağrılan or 'yok'} | "
          f"toplam duvar {duvar_toplam:.1f} sn | girdi {girdi_toplam} tok | "
          f"çıktı {çıktı_toplam} tok")
    return {"tur": tur, "duvar": duvar_toplam, "girdi": girdi_toplam,
            "çıktı": çıktı_toplam, "araçlar": çağrılan}


def sabit_hat(soru, indeks, etiket):
    print("=" * 78)
    print(etiket)
    print(f"  soru: {soru}")
    t0 = time.time()
    bağlam = viki_ara(soru, indeks)
    arama = time.time() - t0
    mesajlar = [{"role": "system", "content": "Belgeleri kaynak alarak cevap ver."},
                {"role": "user", "content": f"Belgeler:\n{bağlam}\n\nSoru: {soru}"}]
    t0 = time.time()
    yanıt = model({"model": SOHBET, "messages": mesajlar, "stream": False,
                   "options": {"temperature": 0, "num_predict": NUM_PREDICT}})
    duvar = time.time() - t0
    print(f"  arama {arama:.2f} sn | üretim duvar {duvar:6.2f} sn | {faz(yanıt)}")
    içerik = (yanıt.get("message", {}).get("content") or "").strip()
    print(f"  cevap: {içerik[:220]!r}")
    return {"arama": arama, "duvar": duvar, "girdi": yanıt.get("prompt_eval_count", 0),
            "çıktı": yanıt.get("eval_count", 0)}


def araç_token_gideri(soru, indeks):
    print("=" * 78)
    print("E) ARAÇ TANIMININ TOKEN GİDERİ — aynı istek, tek fark: tools alanı")
    taban = [{"role": "system", "content": SİSTEM}, {"role": "user", "content": soru}]
    sus = model({"model": SOHBET, "messages": taban, "stream": False,
                 "options": {"temperature": 0, "num_predict": 40}})
    açlık = model({"model": SOHBET, "messages": taban, "tools": ARAÇLAR[:1], "stream": False,
                   "options": {"temperature": 0, "num_predict": 40}})
    çift = model({"model": SOHBET, "messages": taban, "tools": ARAÇLAR, "stream": False,
                  "options": {"temperature": 0, "num_predict": 40}})
    a, b, c = (x.get("prompt_eval_count", 0) for x in (sus, açlık, çift))
    print(f"  0 araç {a} tok | 1 araç {b} tok (+{b - a}) | 2 araç {c} tok (+{c - a})")
    print(f"  araç başına yaklaşık {(c - a) / 2:.0f} token")
    for ad, yanıt in (("tools'suz", sus), ("1 araç", açlık), ("2 araç", çift)):
        çağrı = bool((yanıt.get("message", {}) or {}).get("tool_calls"))
        print(f"  {ad:11s}: {faz(yanıt)} | araç çağırdı: {çağrı}")


def tool_choice_denemesi(soru, indeks):
    print("=" * 78)
    print("F) tool_choice — Ollama dokümanında listelenmiyor; sunucuya soruluyor")
    for etiket, değer in (("yok (belgelenmiş davranış)", None),
                          ('"auto"', "auto"),
                          ('"required"', "required"),
                          ('"bulutmeydan"(çöp değer)', "bulutmeydan")):
        mesajlar = [{"role": "system", "content": SİSTEM}, {"role": "user", "content": soru}]
        yük = {"model": SOHBET, "messages": mesajlar, "stream": False,
               "tools": ARAÇLAR[:1],
               "options": {"temperature": 0, "num_predict": 60}}
        if değer is not None:
            yük["tool_choice"] = değer
        try:
            yanıt = model(yük)
            mesaj = yanıt.get("message", {})
            içerik = repr((mesaj.get("content") or "")[:60])
            print(f"  {etiket:28s}: araç çağırdı={bool(mesaj.get('tool_calls'))} | "
                  f"içerik={içerik}")
        except urllib.error.HTTPError as h:
            print(f"  {etiket:28s}: HTTP {h.code} -> "
                  f"{h.read().decode('utf-8', 'replace')[:120]}")


def biçim_ve_araç(soru, indeks):
    print("=" * 78)
    print("G) format + tools birlikte — doküman 'HTTP 400' diyor, bu makinede?")
    try:
        yanıt = model({"model": SOHBET, "stream": False,
                       "messages": [{"role": "user", "content": soru}],
                       "tools": ARAÇLAR[:1], "format": "json",
                       "options": {"temperature": 0, "num_predict": 60}})
        print("  sunucu kabul etti:",
              json.dumps(yanıt.get("message"), ensure_ascii=False)[:200])
    except urllib.error.HTTPError as h:
        print(f"  HTTP {h.code}: {h.read().decode('utf-8', 'replace')[:200]}")


def ana():
    belgeler = korpus_indir_ve_yazdır()
    indeks = indeks_kur(belgeler)
    print(f"korpus {len(belgeler)} parça | eşik {v6.ZAYIF_ESIK} | sohbet {SOHBET} | "
          f"{len(ARAÇLAR)} araç tanımlı | maks tur {MAKS_TUR}\n")

    tek = "Marmaray hangi yılında hizmete açıldı?"
    A = sabit_hat(tek, indeks, "A) SABİT HAT — tek geçişlik RAG (Örnek 6 tarzı)")
    B = ajan(tek, indeks, "B) AJAN — aynı soru, aracı modelin çağırması bırakıldı")
    print(f"  KARBON KARŞILAŞTIRMA: aynı soru, sabit hat {A['duvar']:.1f} sn / "
          f"1 geçiş | ajan {B['duvar']:.1f} sn / {B['tur']} tur | "
          f"ek girdi tokenı {B['girdi'] - A['girdi']}")

    ajan("Marmaray ile T1 tramvay hattının açılış yıllarını karşılaştır; hangisi daha "
         "eski? İki bilgiyi de araçla doğrula.", indeks,
         "B2) AJAN — iki geçiş gerektiren karşılaştırma sorusu")
    ajan("T1 hattının uzunluğu kaç metredir? Uzunluğu araçtan öğren, sonra birim "
         "dönüştürme aracını kullan.", indeks,
         "C) AJAN — iki aracın sırayla kullanılması gerekiyor")
    ajan("Şu anda İstanbul'da yağmur yağıyor mu?", indeks,
         "D) AJAN — hiçbir aracın yanıtlayamayacağı soru (kaç tur yakıyor?)")
    ajan("Tünel füniküler hattı nerede?", indeks,
         "D2) AJAN — tool_choice='required' ile zorlanmış hâli",
         tool_choice="required")
    ajan("Marmaray hangi yılında hizmete açıldı?", indeks,
         "H) AJAN — araç sonucunda tool_name YOK (iki araç varken)", isimle=False)

    araç_token_gideri(tek, indeks)
    tool_choice_denemesi(tek, indeks)
    biçim_ve_araç(tek, indeks)
    print("=" * 78)
    print("bitti.")


if __name__ == "__main__":
    ana()
