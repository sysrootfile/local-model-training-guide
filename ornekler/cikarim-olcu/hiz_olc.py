# -*- coding: utf-8 -*-
"""
Yerel çıkarım ölçümü — "bir soru neden 60 saniye sürüyor?" sorusunun cevabını
bu makinede gerçekten ölçer. RAG ve ajan örneklerindeki gecikme sayıları bu
kafesten gelir; sayfa üzerinde tahmin bırakılmaz.

Deneyler (hepsi tek modelde, qwen2.5:3b-instruct-q4_K_M, %100 CPU):
  E1  soguk / sicak: model bellekte degilken ne ödenir (load_duration)
  E2  cozme hizi: uretilen token sayisina gore token/sn
  E3  on-yukleme (prefill) egrisi + turkce karakter/token orani (fark yontemi)
  E4  num_ctx etkisi: bellek, yuklenme ve SESSIZ KIRPMA kaniti
  E5  KV onbellegi: ayni uzun prompt ikinci kez ne kadar cok gercekten okuyor
  E6  num_thread: CPU'da iplik sayisi hizayi ciziyor mu
  E7  ilk token suresi (TTFT): akis modunda kullanicinin bekledigi ilk an
  E8  embedding vs uretim: RAG sorgusunun gercek maliyet dagilimi
  E9  takilma avisi: agir bir istekte sure tokenlarda mi sunucu durumunda mi?
      (8 sicak cagri -> keep_alive=0 ile bosalt -> yeniden yukle -> 8 cagri;
       ayrica server.log'daki "prompt cache update" satirlarinin birim kontrolu)
  E2b cozme hizi egrisi, uretmeye zorlayan istekle (E2'de model 16 token'da kasti)
  E3b on-yukleme egrisi onbelleksiz (benzersiz on ek) + karakter/token orani
  E7b sicak TTFT: onbellek kurulusikken ilk token
  E8b embedding'in sunucu tarafi: /api/embed kendi sure alanlariyla, iki fazda
  E10 bosalt/yukle cevrimi x5: 42,7 sn'lik aykiri degerin dagilimi
  E11 duvar-sunucu farki: urllib vekil sunucu algilama gideri mi?
  E12 2,05 sn'nin kaynagi: localhost cozumlemesi mi, baglanti kurma mi?
  E13 indekleme A/B: localhost vs 127.0.0.1 (10 parca)

Gereksinim: Ollama calisiyor + qwen2.5:3b-instruct-q4_K_M + bge-m3 kurulu.
Harici Python paketi YOK (urllib + zamanlama alanlari).

Uyarı: bu betik çalışırken Ollama'ya başka istek göndermeyin — gecikme
sayıları yarışmalı isteklerden bozulur.

Kullanim:
    python hiz_olc.py            # tumu (~20-40 dk, CPU)
    python hiz_olc.py --kisa     # hizli alt küme (~5 dk): E1, E2, E3, E7
"""

import argparse
import ctypes
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_IZINLI_ANA_MAKINE = ("127.0.0.1", "localhost")   # localhost: E12 isim cozumleme A/B olcumu icin


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


# Varsayılan adres sayısal: Windows'ta "localhost" çözümlemesi istek başına ~2 sn
# ekliyor (E12 bunu A/B olarak ölçüyor; oradaki sabitler localhost'u korur).
OLLAMA_CHAT = _url_dogrula("http://127.0.0.1:11434/api/chat")
OLLAMA_EMBED = _url_dogrula("http://127.0.0.1:11434/api/embed")
SOHBET = "qwen2.5:3b-instruct-q4_K_M"
GOMME = "bge-m3"
ISI = "Ölç"  # ısıtma için kısa soru

# Türkçe gerçek metin: Örnek 6 korpusundan bir Vikipedi parçası. Token/karakter
# oranının Türkçe metinle ölçülmesi için kurgu değil gerçek cümle kullanılır.
VIKI_PARCA = (
    "Marmaray, İstanbul Boğazı'nın altına inşa edilen batırma tüp tünel ile "
    "Ayrılık Çeşmesi ile Kazlıçeşme istasyonları arasında servis veren bir "
    "kent içi raylı sistem hattıdır. Proje, Osmanlı döneminden itibaren "
    "gündeme gelmiş, ancak tünelin inşaatına 2004 yılında başlanabilmiştir. "
    "Hat, 2013 yılında hizmete açılmış ve ilk yılında on bir milyonun üzerinde "
    "yolcu taşımıştır. Marmaray ile İstanbul metrosu ve İETT otobüsleri "
    "entegre çalışır; yolcular tek kartla aktarma yapabilir. "
)

BASLATMA_SORUSU = "Bu metne göre Marmaray hangi iki istasyon arasında çalışır? Tek cümle."


def iste(payload, bekle=600, url=None):
    req = urllib.request.Request(
        _url_dogrula(url or OLLAMA_CHAT),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "model-egitimi-rehberi/1.0"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=bekle) as r:
        veri = json.loads(r.read().decode("utf-8"))
    return veri, time.time() - t0


def sn(ns):
    """Ollama süreleri nanosaniye döndürür; saniyeye çevirir."""
    return (ns or 0) / 1e9


def goster(etiket, d, duvar):
    pe, pd = d.get("prompt_eval_count", 0), sn(d.get("prompt_eval_duration"))
    ec, ed = d.get("eval_count", 0), sn(d.get("eval_duration"))
    top = sn(d.get("total_duration"))
    on = f"{pe / pd:>6.1f}" if pd else "     -"
    son = f"{ec / ed:>6.1f}" if ed else "     -"
    onek = d.get("prompt_eval_cached_count", 0)
    print(
        f"  {etiket:<30} duvar {duvar:>6.1f} | sunucu {top:>6.2f} | "
        f"yük {sn(d.get('load_duration')):>5.2f} | "
        f"ön-yük {pe:>5} tok / {pd:>5.2f} sn [{on} tok/sn, {onek} önb.] | "
        f"çözme {ec:>4} tok / {ed:>5.2f} sn [{son} tok/sn]"
    )
    if duvar - top > 3:
        print(f"  {'':<30} ^ duvar-sunucu farkı {duvar - top:.1f} sn: "
              f"istemci/HTTP/kuyruk gideri (Ollama bunu süre olarak raporlamıyor)")
    hesapsiz = top - faz_toplam(d)
    if hesapsiz > 3:
        print(f"  {'':<30} ^ sunucu içinde hesap dışı {hesapsiz:.1f} sn: "
              f"total_duration - (yük + ön-yükleme + çözme)")


def ollama_ps():
    """Modelin bellekte kapladığı alan ve bağlam; komut yoksa None döner."""
    try:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=15)
        for satır in (out.stdout or "").splitlines():
            if SOHBET.split(":")[0] in satır:
                return " ".join(satır.split())
    except Exception:
        pass
    return None


def faz_toplam(d):
    """Raporlanan üç fazın toplamı (yük + ön-yükleme + çözme), saniye."""
    return (sn(d.get("load_duration")) + sn(d.get("prompt_eval_duration"))
            + sn(d.get("eval_duration")))


def bos_ram():
    """Windows'ta boş fiziksel RAM (GiB) ve doluluk yüzdesi; harici paket yok."""
    if os.name != "nt":
        return None
    class _StatEx(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    st = _StatEx()
    st.dwLength = ctypes.sizeof(_StatEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return None
    return st.dwMemoryLoad, st.ullAvailPhys / 2**30


LOG_YOLU = Path(os.environ.get("LOCALAPPDATA", "")) / "Ollama" / "server.log"


def log_kuyruk(mb=2):
    """Sunucu günlüğünün son mb megabaytı (büyük dosyayı okumadan)."""
    try:
        with open(LOG_YOLU, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - mb * 1024 * 1024))
            return f.read().decode("utf-8", "replace")
    except OSError:
        return ""


def baslik(ad):
    print("\n" + "=" * 78)
    print(ad)
    print("=" * 78)


def e1_soguk_sicak():
    baslik("E1 — SOĞUK / SICAK: model bellekte değilken ne ödenir")
    soru = [{"role": "user", "content": "Tek cümle: İstanbul nerede?"}]
    # keep_alive=0 -> cevap biter bitmez boşalt; sonraki çağrı soğuk başlar
    d, s = iste({"model": SOHBET, "messages": soru, "stream": False, "keep_alive": "0",
                 "options": {"temperature": 0, "num_predict": 16}})
    goster("A. keep_alive=0 (çağrı sonrası boşalttı)", d, s)
    time.sleep(2)
    print(f"  boşaltma sonrası ps    : {ollama_ps() or '(liste boş: model bellekte değil)'}")
    d, s = iste({"model": SOHBET, "messages": soru, "stream": False,
                 "options": {"temperature": 0, "num_predict": 16}})
    goster("B. soğuk çağrı (model yeniden yüklendi)", d, s)
    d, s = iste({"model": SOHBET, "messages": soru, "stream": False,
                 "options": {"temperature": 0, "num_predict": 16}})
    goster("C. sıcak çağrı (bellekte hazır)", d, s)
    print(f"  ollama ps (sıcak)      : {ollama_ps() or 'okunamadı'}")


def e2_cozme_hizi():
    baslik("E2 — ÇÖZME HIZI: üretilecek token sayısına göre")
    for n in (8, 32, 128):
        d, s = iste({"model": SOHBET,
                     "messages": [{"role": "user",
                                   "content": f"{n} token uzunluğunda düz bir cümle yaz: hava bugün"}],
                     "stream": False, "options": {"temperature": 0, "num_predict": n}})
        goster(f"num_predict={n}", d, s)


def e3_onyukleme_ve_oran():
    baslik("E3 — ÖN-YÜKLEME EĞRİSİ + Türkçe karakter/token oranı")
    taban = None
    satırlar = []
    for tekrar in (1, 2, 4, 8):
        metin = VIKI_PARCA * tekrar
        soru = BASLATMA_SORUSU if tekrar == 1 else f"{BASLATMA_SORUSU} {tekrar}."
        d, s = iste({"model": SOHBET,
                     "messages": [{"role": "user", "content": metin + "\n\n" + soru}],
                     "stream": False, "options": {"temperature": 0, "num_predict": 16, "num_ctx": 8192}})
        goster(f"prompt {len(metin):>6} karakter (x{tekrar})", d, s)
        if taban is None:
            taban = (len(metin), d.get("prompt_eval_count", 0))
        satırlar.append((len(metin), d.get("prompt_eval_count", 0), sn(d.get("prompt_eval_duration"))))
    for (k1, t1, _), (k2, t2, d2) in zip(satırlar, satırlar[1:]):
        dk, dt = k2 - k1, t2 - t1
        if dt > 0:
            print(f"  fark {dk:>6} karakter -> {dt:>4} token => Türkçe "
                  f"{dk / dt:.2f} karakter/token (şablon gideri dışlandı)")
            print(f"       farkın ön-yükleme süresi {d2:.2f} sn -> {dt / d2:.1f} tok/sn")


def e4_num_ctx():
    baslik("E4 — num_ctx: bellek, yüklenme ve SESSİZ KIRPMA")
    uzun = VIKI_PARCA * 4
    soru = [{"role": "user", "content": uzun + "\n\n" + BASLATMA_SORUSU}]
    # Beklenen token sayısı önce en geniş bağlamla ölçülür; kırpma kararı
    # "az token göründü" varsayımına değil bu tabana göre verilir.
    d, _ = iste({"model": SOHBET, "messages": soru, "stream": False,
                 "options": {"temperature": 0, "num_predict": 1, "num_ctx": 8192}})
    beklenti = d.get("prompt_eval_count", 0)
    print(f"  taban: istek {beklenti} token (num_ctx=8192, kırpma yok varsayımı)")
    for ctx in (512, 2048, 4096, 8192):
        try:
            d, s = iste({"model": SOHBET, "messages": soru, "stream": False,
                         "options": {"temperature": 0, "num_predict": 16, "num_ctx": ctx}})
            tok = d.get("prompt_eval_count", 0)
            goster(f"num_ctx={ctx}", d, s)
            if tok < beklenti:
                print(f"      ^ KIRPMA: {beklenti} token'lık istekten yalnız {tok} değerlendirildi "
                      f"({beklenti - tok} token sessizce düştü)")
            else:
                print(f"      sığdı: {tok}/{beklenti} token değerlendirildi")
            ps = ollama_ps()
            print(f"      ps: {ps if ps else 'okunamadı'}")
        except urllib.error.HTTPError as e:
            print(f"  num_ctx={ctx}: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:120]}")


def e5_kv_onbellek():
    baslik("E5 — KV ÖNBELLEĞİ: aynı uzun prompt ikinci kez")
    p = {"model": SOHBET, "messages": [{"role": "user", "content": VIKI_PARCA * 4 + "\n\n" + BASLATMA_SORUSU}],
         "stream": False, "options": {"temperature": 0, "num_predict": 16, "num_ctx": 8192}}
    d, s = iste(p)
    goster("ilk okuma", d, s)
    d, s = iste(p)
    goster("ikinci okuma (aynı önek)", d, s)
    d, s = iste({"model": SOHBET,
                 "messages": [{"role": "user", "content": VIKI_PARCA * 4 + "\n\nFarklı bir soru: hat ne zaman açıldı?"}],
                 "stream": False, "options": {"temperature": 0, "num_predict": 16, "num_ctx": 8192}})
    goster("üçüncü okuma (soru değişti)", d, s)


def e6_iplik():
    baslik("E6 — num_thread: CPU'da iplik sayısı")
    print(f"  görünen mantıksal iplik: {os.cpu_count()}")
    for t in (2, 6, 12):
        d, s = iste({"model": SOHBET,
                     "messages": [{"role": "user", "content": "Beş başlıkta İstanbul ulaşımını özetle"}],
                     "stream": False,
                     "options": {"temperature": 0, "num_predict": 120, "num_thread": t}})
        goster(f"num_thread={t}", d, s)


def e7_ttft():
    baslik("E7 — İLK TOKEN SÜRESİ (TTFT): akış modunda kullanıcı ne bekler")
    for tekrar, etiket in ((1, "kısa prompt"), (4, "uzun prompt (Vikipedi x4)")):
        payload = {"model": SOHBET,
                   "messages": [{"role": "user",
                                 "content": VIKI_PARCA * tekrar + "\n\n" + BASLATMA_SORUSU}],
                   "stream": True, "options": {"temperature": 0, "num_predict": 40, "num_ctx": 8192}}
        req = urllib.request.Request(_url_dogrula(OLLAMA_CHAT), data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        ilk = None
        parça = 0
        with urllib.request.urlopen(req, timeout=600) as r:
            for satır in r:
                if not satır.strip():
                    continue
                k = json.loads(satır.decode("utf-8"))
                if ilk is None and (k.get("message", {}).get("content") or k.get("message", {}).get("tool_calls")):
                    ilk = time.time() - t0
                if k.get("done"):
                    parça = k.get("eval_count", 0)
                    son = sn(k.get("eval_duration"))
        print(f"  {etiket:<20} ilk token {ilk:.2f} sn | {parça} token "
              f"| toplam {time.time() - t0:.1f} sn | son {son:.2f} sn")


def e8_embedding():
    baslik("E8 — EMBEDDING vs ÜRETİM: RAG sorgusunun maliyet dağılımı")
    sorgu = "Marmaray hangi iki istasyon arasında çalışır?"
    süreler = []
    for _ in range(3):
        t0 = time.time()
        with urllib.request.urlopen(
            urllib.request.Request(OLLAMA_EMBED,
                                   data=json.dumps({"model": GOMME, "input": sorgu}).encode(),
                                   headers={"Content-Type": "application/json"}), timeout=120) as r:
            json.loads(r.read().decode("utf-8"))
        süreler.append(time.time() - t0)
    print(f"  soruyu gömmek      : {statistics.mean(süreler):.3f} sn (ort, 3 deneme)")
    parça = VIKI_PARCA * 4
    t0 = time.time()
    with urllib.request.urlopen(
        urllib.request.Request(OLLAMA_EMBED, data=json.dumps({"model": GOMME, "input": parça}).encode(),
                               headers={"Content-Type": "application/json"}), timeout=300) as r:
        json.loads(r.read().decode("utf-8"))
    print(f"  {len(parça)} karakterlik parçayı gömmek: {time.time() - t0:.3f} sn")
    d, s = iste({"model": SOHBET,
                 "messages": [{"role": "system", "content": "Yalnızca verilen metne dayan."},
                              {"role": "user", "content": parça + "\n\n" + BASLATMA_SORUSU}],
                 "stream": False, "options": {"temperature": 0, "num_predict": 80, "num_ctx": 8192}})
    goster("aynı metni bağlam yapıp cevap üretmek", d, s)


def e9_takilma_avi():
    baslik("E9 — TAKILMA AVI: gecikme tokenlarda mı, sunucu durumunda mı?")
    print("  soru: daha önce bazı sıcak çağrılar ~60 sn sürdü; model işi 1-2 sn idi.")
    print("  yöntem: özdeş 8 çağrı (önbellek birikmiş) -> boşalt -> yeniden yükle -> yine 8 çağrı")

    sorgu = VIKI_PARCA * 4 + "\n\n" + BASLATMA_SORUSU

    def koş(n):
        sonuç = []
        for i in range(n):
            payload = {"model": SOHBET, "messages": [{"role": "user", "content": sorgu}],
                       "stream": False, "options": {"temperature": 0, "num_predict": 16, "num_ctx": 8192}}
            t0 = time.time()
            try:
                d, s = iste(payload)
            except Exception as e:
                print(f"  {i + 1:>2}. HATA {type(e).__name__}: {str(e)[:90]} ({time.time() - t0:.1f} sn duvar)")
                continue
            top, ft = sn(d.get("total_duration")), faz_toplam(d)
            ram = bos_ram()
            sonuç.append((s, top, top - ft))
            print(f"  {i + 1:>2}. duvar {s:>6.1f} | sunucu {top:>6.2f} | fazlar {ft:>6.2f} | "
                  f"hesap dışı {top - ft:>6.2f} | {d.get('prompt_eval_count', 0):>4} tok "
                  f"({d.get('prompt_eval_cached_count', 0):>4} önb.) | yük {sn(d.get('load_duration')):>5.2f} | "
                  + (f"RAM {ram[1]:.1f} GiB boş (%{ram[0]})" if ram else "RAM ?"))
        return sonuç

    def özet(ad, s):
        if not s:
            print(f"  {ad}: ölçüm alınamadı")
            return
        duvar = [x[0] for x in s]
        print(f"  {ad}: n={len(duvar)} duvar min {min(duvar):.1f} / medyan {statistics.median(duvar):.1f} / "
              f"maks {max(duvar):.1f} sn | 15 sn üstü {sum(1 for x in duvar if x > 15)} çağrı | "
              f"en büyük hesap dışı {max(x[2] for x in s):.2f} sn")

    print("\n  --- faz A: bellekte hazır, önbellek birikmiş ---")
    özet("faz A", koş(8))
    print(f"  ps: {ollama_ps() or '(bellekte değil)'}")

    print("\n  --- müdahale: keep_alive=0 ile boşalt, sonra yeniden yükle ---")
    d, s = iste({"model": SOHBET, "messages": [{"role": "user", "content": ISI}],
                 "stream": False, "keep_alive": "0", "options": {"temperature": 0, "num_predict": 8}})
    print(f"  boşaltma çağrısı {s:.1f} sn; ps -> {ollama_ps() or '(liste boş)'}")
    time.sleep(3)
    print("\n  --- faz B: sıfırdan yüklenmiş model, önbellek boş ---")
    özet("faz B", koş(8))

    print("\n  --- birim kontrolü: günlüğün en hızlı şüphelisi ---")
    kuyruk = log_kuyruk()
    önbellek_ms = [float(x.replace(",", ".")) for x in re.findall(r"prompt cache update took ([0-9.]+) ms", kuyruk)]
    if önbellek_ms:
        print(f"  son 2 MB günlükte {len(önbellek_ms)} 'prompt cache update took' satırı, "
              f"en büyük {max(önbellek_ms):.1f} ms -> 60 sn'lik takılmayı açıklayamaz (birim: ms)")
    durum = re.findall(r"cache state: (\d+) prompts, ([0-9.]+) MiB", kuyruk)
    if durum:
        print(f"  en son cache durumu: {durum[-1][0]} prompt, {durum[-1][1]} MiB")
    yavas = [float(x) for x in re.findall(
        r"\[GIN\] [^|]+\| \d{3} +\| *([0-9.]+)s *\| *[0-9.:]+ *\| POST +\"/api/[a-z]+\"", kuyruk)]
    if yavas:
        print(f"  aynı pencerede {len(yavas)} POST isteği, {sum(1 for x in yavas if x > 20)} tanesi 20 sn üstü "
              f"(maks {max(yavas):.1f} sn) — GIN süresi HTTP dahil, faz toplamları değil")


def e2b_cozme_egrisi():
    baslik("E2b — ÇÖZME HIZI EĞRİSİ (uzun üretimeye zorlayan istek)")
    print("  E2'de model 32 ve 128 token isteğini 16 token'da kendi kesmişti;")
    print("  bu kez saydıran bir istekle çözme fazını gerçekten uzatıyoruz.")
    for n in (64, 256, 512):
        d, s = iste({"model": SOHBET,
                     "messages": [{"role": "user",
                                   "content": "1'den başlayarak sayıları virgülle aralarında yaz, "
                                              "durmadan devam et: 1, 2, 3,"}],
                     "stream": False, "options": {"temperature": 0, "num_predict": n}})
        ec, ed = d.get("eval_count", 0), sn(d.get("eval_duration"))
        goster(f"num_predict={n} -> {ec} token üretildi", d, s)
        print(f"  {'':<30} istenen {n}, üretilen {ec}, ms/token "
              f"{(ed * 1000 / ec) if ec else 0:.1f}")


def e3b_onyuk_egrisi():
    baslik("E3b — ÖNBELLEKSİZ ÖN-YÜKLEME EĞRİSİ + Türkçe karakter/token oranı")
    print("  her satırın başına benzersiz bir numara konur: önbellek eşleşmez,")
    print("  böylece prompt_eval_duration gerçekten baştan sona önbelleksizdir.")
    ölçüm = []
    for tekrar in (1, 2, 4, 8):
        metin = f"Belge {tekrar}. " + VIKI_PARCA * tekrar
        soru = [{"role": "user", "content": metin + "\n\n" + BASLATMA_SORUSU}]
        iste({"model": SOHBET, "messages": [{"role": "user", "content": "ısıt"}],
              "stream": False, "options": {"temperature": 0, "num_predict": 1, "num_ctx": 8192}})
        d, s = iste({"model": SOHBET, "messages": soru, "stream": False,
                     "options": {"temperature": 0, "num_predict": 1, "num_ctx": 8192}})
        pe, pd = d.get("prompt_eval_count", 0), sn(d.get("prompt_eval_duration"))
        ölçüm.append((len(metin), pe, pd))
        print(f"  {len(metin):>5} karakter (x{tekrar}) -> {pe:>5} tok / {pd:>6.2f} sn "
              f"[{pe / pd if pd else 0:>6.1f} tok/sn, {d.get('prompt_eval_cached_count', 0)} önb.]")
    for i in range(1, len(ölçüm)):
        dk = ölçüm[i][0] - ölçüm[i - 1][0]
        dt = ölçüm[i][1] - ölçüm[i - 1][1]
        ds = ölçüm[i][2] - ölçüm[i - 1][2]
        if dt > 0 and ds > 0:
            print(f"  fark {dk:>5} karakter -> {dt:>4} token = {dk / dt:.2f} karakter/token | "
                  f"{ds:.2f} sn -> {dt / ds:.1f} tok/sn")


def e7b_sicak_ttft():
    baslik("E7b — İLK TOKEN SÜRESİ (model bellekte ve önbellek sıcak)")
    for tekrar, etiket in ((1, "kısa prompt"), (4, "uzun prompt (Vikipedi x4)")):
        metin = VIKI_PARCA * tekrar + "\n\n" + BASLATMA_SORUSU
        # aynı öneki iki kez gönder: ilk okuma önbelleği kurar, ikincisi TTFT'i ölçer
        for tur in (1, 2):
            payload = {"model": SOHBET, "messages": [{"role": "user", "content": metin}],
                       "stream": True, "options": {"temperature": 0, "num_predict": 40, "num_ctx": 8192}}
            req = urllib.request.Request(_url_dogrula(OLLAMA_CHAT), data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            t0 = time.time()
            ilk = None
            son = done = None
            with urllib.request.urlopen(req, timeout=600) as r:
                for satır in r:
                    if not satır.strip():
                        continue
                    k = json.loads(satır.decode("utf-8"))
                    if ilk is None and (k.get("message", {}).get("content")
                                        or k.get("message", {}).get("tool_calls")):
                        ilk = time.time() - t0
                    if k.get("done"):
                        done, son = k, sn(k.get("eval_duration"))
            print(f"  {etiket:<22} tur {tur}: ilk token {ilk:>6.2f} sn | duvar {time.time() - t0:>5.1f} sn | "
                  f"sunucu {sn(done.get('total_duration')):>5.2f} sn | "
                  f"ön-yük {done.get('prompt_eval_count', 0)} tok ({done.get('prompt_eval_cached_count', 0)} önb.) "
                  f"/ {sn(done.get('prompt_eval_duration')):>5.2f} sn | çözme {son:.2f} sn")


def e12_adres_ve_baglanti():
    baslik("E12 — 2,05 sn'NIN KAYNAĞI: localhost çözümlemesi mi, bağlantı kurma mı?")
    print("  E11 vekil sunucuyu eledi. Üç olasılık: DNS/hosts çözümü, TCP el sıkışması,")
    print("  ya da her istekte yeni bağlantı kuran istemci. Bağlantı yeniden kullanımı test edilir.")
    gövde = json.dumps({"model": SOHBET, "messages": [{"role": "user", "content": ISI}],
                        "stream": False, "options": {"temperature": 0, "num_predict": 16}})
    # ısıt
    iste({"model": SOHBET, "messages": [{"role": "user", "content": ISI}], "stream": False,
          "options": {"temperature": 0, "num_predict": 16}})

    def kez(etiket, url=None, sabit_baglanti=False):
        fark = []
        for _ in range(4):
            t0 = time.time()
            if sabit_baglanti:
                import http.client
                c = http.client.HTTPConnection("127.0.0.1", 11434, timeout=300)
                c.request("POST", "/api/chat", body=gövde,
                          headers={"Content-Type": "application/json", "Connection": "keep-alive"})
                d = json.loads(c.getresponse().read().decode())
                c.close()
            else:
                d, _ = iste({"model": SOHBET, "messages": [{"role": "user", "content": ISI}],
                             "stream": False, "options": {"temperature": 0, "num_predict": 16}},
                            url=url)
            fark.append((time.time() - t0) - sn(d.get("total_duration")))
        print(f"  {etiket:<34} fark medyan {statistics.median(fark):>5.2f} sn | "
              f"denemeler {' '.join(f'{x:.2f}' for x in fark)}")

    kez("http://localhost:11434 (urllib)", url="http://localhost:11434/api/chat")
    kez("http://127.0.0.1:11434 (urllib)", url="http://127.0.0.1:11434/api/chat")
    kez("127.0.0.1 + http.client", sabit_baglanti=True)


def e13_indeks_ab():
    baslik("E13 — İNDEKSLEME A/B: localhost mu, 127.0.0.1 mi (10 parça)")
    print("  Örnek 6 indeksi parça başına bir HTTP isteği atar; isim çözümleme gideri")
    print("  bu döngüde 125 kez ödenir. 10 parçalık bir A/B bunu doğrudan gösterir.")
    parcalar = [f"P{ i }. " + VIKI_PARCA * 2 for i in range(10)]

    def gönder(url, metin):
        t0 = time.time()
        with urllib.request.urlopen(
            urllib.request.Request(url, data=json.dumps({"model": GOMME, "input": metin}).encode(),
                                   headers={"Content-Type": "application/json"}), timeout=600) as r:
            d = json.loads(r.read().decode())
        return time.time() - t0, sn(d.get("total_duration"))

    for etiket, url in (("localhost ", "http://localhost:11434/api/embed"),
                        ("127.0.0.1 ", "http://127.0.0.1:11434/api/embed")):
        gönder(url, "ısınma")  # model yükleme giderini faz dışına at
        t0 = time.time()
        çift = [gönder(url, p) for p in parcalar]
        toplam = time.time() - t0
        sunucu = sum(x[1] for x in çift)
        print(f"  {etiket}: 10 parça {toplam:>6.1f} sn ({toplam / 10:>4.2f} sn/parça) | "
              f"sunucu işi {sunucu:>6.1f} sn | istemci gideri {toplam - sunucu:>6.1f} sn "
              f"({(toplam - sunucu) / toplam * 100:.0f}%)")


def e10_bosalt_yukle():
    baslik("E10 — BOŞALT/YÜKLE ÇEVRİMİ: 42,7 sn'lik aykırı değerin peşi")
    print("  E9 sırasında keep_alive=0 ile boşaltan küçük bir istek 42,7 sn sürdü;")
    print("  model işi 1-2 sn'ydi. Döngüyü 5 kez tekrarlayıp dağılımı ölçüyoruz.")
    sorgu = [{"role": "user", "content": "Tek cümle: İstanbul nerede?"}]
    for tur in range(1, 6):
        d, s = iste({"model": SOHBET, "messages": sorgu, "stream": False,
                     "keep_alive": "0", "options": {"temperature": 0, "num_predict": 16}})
        print(f"  {tur}. boşalt-çağrısı  duvar {s:>6.1f} | sunucu {sn(d.get('total_duration')):>6.2f} | "
              f"yük {sn(d.get('load_duration')):>5.2f} | "
              f"ön-yük {d.get('prompt_eval_count',0):>3} tok / {sn(d.get('prompt_eval_duration')):>5.2f} sn | "
              f"çözme {d.get('eval_count',0):>3} tok / {sn(d.get('eval_duration')):>5.2f} sn")
        time.sleep(3)
        t0 = time.time()
        d, s = iste({"model": SOHBET, "messages": sorgu, "stream": False,
                     "options": {"temperature": 0, "num_predict": 16}})
        top, ft = sn(d.get("total_duration")), faz_toplam(d)
        pe, pd = d.get("prompt_eval_count", 0), sn(d.get("prompt_eval_duration"))
        ram = bos_ram()
        print(f"     yeniden yükleme  duvar {s:>6.1f} | sunucu {top:>6.2f} | yük {sn(d.get('load_duration')):>5.2f} | "
              f"ön-yük {pe:>3} tok / {pd:>5.2f} sn [{pe / pd if pd else 0:>5.1f} tok/sn, "
              f"{d.get('prompt_eval_cached_count',0):>3} önb.] | fazlar {ft:>5.2f} | "
              f"hesap dışı {top - ft:>5.2f} | " + (f"RAM {ram[1]:.1f} GiB boş" if ram else "RAM ?"))
    kuyruk = log_kuyruk(4)
    yavas = re.findall(r"\[GIN\] ([^|]+)\| (\d{3}) +\| *([0-9.]+)s *\| *[0-9.:]+ *\| POST +\"/api/[a-z]+\"", kuyruk)
    agir = [(t, float(s)) for t, code, s in yavas if float(s) > 20]
    print(f"  günlük kuyruğunda 20 sn üstü {len(agir)} POST satırı (toplam {len(yavas)})")
    for t, s in agir[-6:]:
        print(f"    {t.strip()} {s:.1f} sn")


def e11_proxy_gideri():
    baslik("E11 — DUVAR-SUNUCU FARKI: ~2 sn'nin kaynağı (vekil sunucu algılama?)")
    print("  E1/E9'da her sıcak çağrıda duvar, sunucu süresinden ~2,0 sn büyüktü.")
    sorgu = [{"role": "user", "content": VIKI_PARCA + "\n\n" + BASLATMA_SORUSU}]
    opt = {"temperature": 0, "num_predict": 16}
    farklar = {"varsayılan": [], "proxy yok": []}
    for mod in ("varsayılan", "proxy yok"):
        for _ in range(4):
            payload = json.dumps({"model": SOHBET, "messages": sorgu, "stream": False, "options": opt})
            t0 = time.time()
            if mod == "proxy yok":
                istek = urllib.request.Request(OLLAMA_CHAT, data=payload.encode(),
                                               headers={"Content-Type": "application/json"})
                ac = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with ac.open(istek, timeout=300) as r:
                    d = json.loads(r.read().decode())
            else:
                d, _ = iste({"model": SOHBET, "messages": sorgu, "stream": False, "options": opt})
            duvar = time.time() - t0
            farklar[mod].append(duvar - sn(d.get("total_duration")))
            print(f"  {mod:<12} duvar {duvar:>5.2f} | sunucu {sn(d.get('total_duration')):>5.2f} | "
                  f"fark {duvar - sn(d.get('total_duration')):>5.2f} sn")
    for mod, f in farklar.items():
        print(f"  {mod}: fark medyan {statistics.median(f):.2f} sn (4 deneme)")


def e8b_embedding_sunucu():
    baslik("E8b — EMBEDDING'İN SUNUCU TARAFI (istemci gideri çıkarılmış)")
    print("  E8 duvar süresi ölçmüştü; /api/embed de kendi süre alanlarını döndürür.")
    print("  İki faz: sohbet modeli bellekteyken ve boşaltıldıktan sonra.")

    def gom(metnet, etiket):
        t0 = time.time()
        with urllib.request.urlopen(
            urllib.request.Request(OLLAMA_EMBED,
                                   data=json.dumps({"model": GOMME, "input": metnet}).encode(),
                                   headers={"Content-Type": "application/json"}), timeout=600) as r:
            d = json.loads(r.read().decode("utf-8"))
        duvar = time.time() - t0
        print(f"  {etiket:<26} duvar {duvar:>6.2f} | sunucu {sn(d.get('total_duration')):>6.2f} | "
              f"yük {sn(d.get('load_duration')):>5.2f} | "
              f"ön-yük {d.get('prompt_eval_count', 0):>5} tok / {sn(d.get('prompt_eval_duration')):>5.2f} sn "
              f"| {len(d.get('embeddings', []))} vektör, boyut "
              f"{len(d['embeddings'][0]) if d.get('embeddings') else '?'}")
        return sn(d.get("total_duration")), duvar

    uzun = VIKI_PARCA * 4
    for faz, sohbet_acik in (("A: sohbet modeli bellekte", True), ("B: sohbet boşaltıldı", False)):
        print(f"\n  --- faz {faz} ---")
        if sohbet_acik:
            iste({"model": SOHBET, "messages": [{"role": "user", "content": ISI}],
                  "stream": False, "options": {"temperature": 0, "num_predict": 4}})
        else:
            iste({"model": SOHBET, "messages": [{"role": "user", "content": ISI}],
                  "stream": False, "keep_alive": "0", "options": {"temperature": 0, "num_predict": 4}})
            time.sleep(2)
        print(f"  ps: {ollama_ps() or '(sohbet modeli bellekte degil)'}")
        sun = [gom("Marmaray hangi iki istasyon arasında çalışır?", f"sorgu {i + 1}") for i in range(4)]
        gom(uzun, "1.904 karakterlik parça")
        print(f"  sorgu gömme medyanı: sunucu {statistics.median(x[0] for x in sun):.2f} sn / "
              f"duvar {statistics.median(x[1] for x in sun):.2f} sn")


DENELER = [
    ("E1", e1_soguk_sicak), ("E2", e2_cozme_hizi), ("E3", e3_onyukleme_ve_oran),
    ("E4", e4_num_ctx), ("E5", e5_kv_onbellek), ("E6", e6_iplik),
    ("E7", e7_ttft), ("E8", e8_embedding), ("E9", e9_takilma_avi),
    ("E2b", e2b_cozme_egrisi), ("E3b", e3b_onyuk_egrisi),
    ("E7b", e7b_sicak_ttft), ("E10", e10_bosalt_yukle), ("E11", e11_proxy_gideri),
    ("E8b", e8b_embedding_sunucu), ("E12", e12_adres_ve_baglanti),
    ("E13", e13_indeks_ab),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kisa", action="store_true", help="yalnız E1, E2, E3, E7")
    ap.add_argument("--yalniz", nargs="*", help="seçili deneyler, örn. --yalniz E4 E5")
    args = ap.parse_args()
    secim = {k for k in (args.yalniz or [])} | ({"E1", "E2", "E3", "E7"} if args.kisa else set())
    print(f"model: {SOHBET} | embedding: {GOMME} | cpu (%100), Ollama yerel")
    print("süreler Ollama'nın döndürdüğü alanlardan; 'duvar' = HTTP dahil gerçek bekleme")
    for ad, fn in DENELER:
        if secim and ad not in secim:
            continue
        try:
            fn()
        except Exception as e:
            print(f"  [atlandı] {ad}: {type(e).__name__}: {str(e)[:180]}")
    print("\nbitti.")


if __name__ == "__main__":
    main()
