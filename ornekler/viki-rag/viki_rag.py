# -*- coding: utf-8 -*-
"""
Vikipedi'den Türkçe RAG — veriyi internetteki Türkçe Vikipedi'den çeker.

Örnek 5'ten (yerel-rag/rag.py) farkı:
  1. Belgeler elle yazılmaz; çalışma anında Vikipedi API'sinden indirilir
  2. Uzun maddeler paragraf tabanlı parçalara bölünür (~800 karakter + örtüşme)
  3. Korpus 8 madde / 100+ parça ölçeğindedir (Örnek 5'te 8 kısa belge)

Akış:
  1. İstanbul ulaşım maddelerini Vikipedi API'sinden indir
  2. Maddeleri parçalara böl, bge-m3 ile vektörleştir
  3. Soruyu vektörleştirip kosinüs benzerliğiyle en ilgili parçaları getir
  4. Getirilen parçaları bağlama ekleyip qwen2.5:3b ile cevap üret
  5. Getirim testi (hit@1 / hit@4) ve kapsam dışı soru testi

Gereksinim:
    - İnternet bağlantısı (korpus ilk çalıştırmada Vikipedi'den çekilir)
    - Çalışır durumda bir Ollama sunucusu (http://127.0.0.1:11434) ve:
        ollama pull bge-m3
        ollama pull qwen2.5:3b-instruct-q4_K_M

Harici Python paketi GEREKMEZ — yalnızca standart kütüphane kullanılır.

Kullanım:
    python viki_rag.py                     # tüm demo: korpus + 2 soru + iki test
    python viki_rag.py --soru "soru"       # tek soru sor
    python viki_rag.py --test              # yalnızca getirim testi
"""

import argparse
import json
import math
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

_IZINLI_ANA_MAKINE = ("127.0.0.1", "tr.wikipedia.org")


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


WIKI_API = _url_dogrula("https://tr.wikipedia.org/w/api.php")
# Vikipedi politikası gereği anlamlı bir User-Agent gönderilir.
VIKI_UA = "ModelEgitimiRehberi-Ornek/1.0 (egitim amacli; yerel deneme)"
VIKI_LISANS = "Maddeler CC BY-SA lisansıyla yayımlanır; kaynak göstermeden yeniden kullanılamaz."

# Windows'ta "localhost" ad çözümlemesi istek başına ~2 sn ekliyor (ölçüldü: 2,03 sn);
# sayısal adres aynı isteği 0,00 sn'de çözüyor.
OLLAMA = _url_dogrula("http://127.0.0.1:11434")
GOMME_MODELI = "bge-m3"
SOHBET_MODELI = "qwen2.5:3b-instruct-q4_K_M"
K = 4                     # bağlama eklenecek parça sayısı (korpus büyük olduğu için Örnek 5'ten büyük)
HEDEF_PARCA = 800         # hedef parça uzunluğu (karakter)
ZAYIF_ESIK = 0.54         # bu korpusta ölçülen bantlardan (olc.py, 2026-10-15):
                          # kapsam içi en düşük 0,598, kapsam dışı en yüksek 0,485

SISTEM_TALIMATI = (
    "Sen İstanbul toplu ulaşımı hakkında yerel bir bilgi asistanısın. "
    "SADECE sana verilen belge parçalarındaki bilgiyi kullan; kendi bilgiinden ekleme yapma. "
    "Parçalarda cevap yoksa 'Bu konuda belgelerde bilgi yok' de. "
    "Türkçe, kısa ve net cevap ver. Kullandığın parçaların kimliğini köşeli parantezle belirt, örn. [Marmaray#2]."
)

# 2026-10-15'te tek tek doğrulanmış madde başlıkları (yönlendirmeler redirects=1 ile izlenir).
WIKI_BASLIKLARI = [
    "İstanbul ilinde toplu ulaşım",
    "İstanbul Metrosu",
    "Marmaray",
    "Tünel (İstanbul)",
    "T1 (İstanbul Tramvayı)",
    "Metrobüs",
    "İETT",
    "İstanbul Deniz Otobüsleri",
]

TEST_SORULARI = [
    ("Marmaray hangi yıl açıldı?", "Marmaray"),
    ("Tünel hangi iki semt arasında çalışır?", "Tünel (İstanbul)"),
    ("Metrobüs hangi güzergâhı izler?", "Metrobüs"),
    ("İETT ne zaman kuruldu?", "İETT"),
    ("İstanbul'un ilk metro hattı hangisidir?", "İstanbul Metrosu"),
    ("T1 tramvay hattı hangi güzergâhta çalışır?", "T1 (İstanbul Tramvayı)"),
]


def _post(uç_nokta, yük):
    istek = urllib.request.Request(
        _url_dogrula(f"{OLLAMA}{uç_nokta}"),
        data=json.dumps(yük).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(istek, timeout=600) as yanıt:
        return json.loads(yanıt.read().decode("utf-8"))


def vikipedi_cek(baslik):
    # Tek istekte tek madde: tam metin çıkarımı (explaintext) API'de exlimit=1 ile sınırlıdır.
    p = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "format": "json",
        "formatversion": "2",
        "titles": baslik,
    }
    url = f"{WIKI_API}?{urllib.parse.urlencode(p)}"
    istek = urllib.request.Request(_url_dogrula(url), headers={"User-Agent": VIKI_UA})
    with urllib.request.urlopen(istek, timeout=30) as yanıt:
        v = json.loads(yanıt.read().decode("utf-8"))
    sayfa = v["query"]["pages"][0]
    if sayfa.get("missing"):
        return None
    return sayfa.get("extract", "")


def parcalara_bol(metin, hedef=HEDEF_PARCA):
    satırlar = [s.strip() for s in metin.splitlines()]
    paragraflar = [s for s in satırlar if len(s) >= 40 and not s.startswith("==")]
    parcalar = []
    mevcut = []
    uzunluk = 0
    for p in paragraflar:
        mevcut.append(p)
        uzunluk += len(p)
        if uzunluk >= hedef:
            parcalar.append("\n\n".join(mevcut))
            mevcut = mevcut[-1:]   # örtüşme: son paragraf bir sonraki parçaya taşınır
            uzunluk = len(mevcut[0])
    if mevcut:
        kalan = "\n\n".join(mevcut)
        if parcalar and len(kalan) < 200:
            parcalar[-1] += "\n\n" + kalan
        else:
            parcalar.append(kalan)
    return parcalar


def korpus_olustur():
    belgeler = []
    toplam_karakter = 0
    for baslik in WIKI_BASLIKLARI:
        metin = vikipedi_cek(baslik)
        if not metin:
            print(f"[veri] UYARI: '{baslik}' maddesi bulunamadı, atlandı.")
            continue
        parcalar = parcalara_bol(metin)
        toplam_karakter += len(metin)
        for sıra, parca in enumerate(parcalar, 1):
            belgeler.append({"id": f"{baslik}#{sıra}", "baslik": baslik, "metin": parca})
        print(f"[veri] {baslik}: {len(metin):,} karakter -> {len(parcalar)} parça")
    print(f"[veri] toplam: {len(belgeler)} parça, {toplam_karakter:,} karakter")
    print(f"[veri] {VIKI_LISANS}")
    return belgeler


def gomme(metin):
    yanıt = _post("/api/embeddings", {"model": GOMME_MODELI, "prompt": metin})
    return yanıt["embedding"]


def kosinus(a, b):
    iç_çarpım = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return iç_çarpım / (norm_a * norm_b)


def indeksle(belgeler):
    t0 = time.time()
    indeks = []
    for sıra, belge in enumerate(belgeler, 1):
        vektör = gomme(belge["metin"])
        indeks.append((belge, vektör))
        if sıra % 25 == 0:
            print(f"[indeks] {sıra}/{len(belgeler)} parça...")
    print(f"[indeks] {len(indeks)} parça vektörleştirildi ({time.time() - t0:.1f} sn, "
          f"boyut={len(indeks[0][1])})")
    return indeks


def getir(soru, indeks, k=K):
    soru_vektörü = gomme(soru)
    skorlar = sorted(
        ((kosinus(soru_vektörü, v), b) for b, v in indeks),
        key=lambda çift: çift[0],
        reverse=True,
    )
    return skorlar[:k]


def cevapla(soru, indeks):
    skorlu = getir(soru, indeks)
    en_iyi_skor = skorlu[0][0]
    bağlam = "\n\n".join(
        f"[{b['id']}] {b['metin']}" for _, b in skorlu
    )
    print(f"[arama] en iyi benzerlik: {en_iyi_skor:.3f} -> {', '.join(b['id'] for _, b in skorlu)}")
    if en_iyi_skor < ZAYIF_ESIK:
        print(f"[uyarı] en iyi benzerlik {ZAYIF_ESIK} eşiğinin altında — model 'yok' demelidir.")

    mesajlar = [
        {"role": "system", "content": SISTEM_TALIMATI},
        {"role": "user", "content": f"Belge parçaları:\n{bağlam}\n\nSoru: {soru}"},
    ]
    t0 = time.time()
    yanıt = _post("/api/chat", {
        "model": SOHBET_MODELI,
        "messages": mesajlar,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 250},
    })
    print(f"[üretim] {time.time() - t0:.1f} sn")
    print(f"[cevap] {yanıt['message']['content'].strip()}\n")


def getirim_testi(indeks):
    print("=" * 62)
    print("GETİRİM TESTİ — doğru maddeden parça ilk k'ta geldi mi?")
    print("=" * 62)
    hit1 = 0
    hitk = 0
    for soru, beklenen in TEST_SORULARI:
        üst = getir(soru, indeks)
        sıralama = [b["baslik"] for _, b in üst]
        durum1 = "OK " if beklenen == sıralama[0] else "MISS"
        durumk = "OK " if beklenen in sıralama else "MISS"
        hit1 += beklenen == sıralama[0]
        hitk += beklenen in sıralama
        print(f"  [{durum1}|{durumk}] {soru}")
        print(f"        beklenen: {beklenen}")
        print(f"        bulunan: {', '.join(sıralama)}")
    print(f"\n  hit@1: {hit1}/{len(TEST_SORULARI)}   hit@{K}: {hitk}/{len(TEST_SORULARI)}\n")


def kapsam_disi_testi(indeks):
    print("=" * 62)
    print("KAPSAM DIŞI TEST — İstanbul ulaşımıyla ilgisiz soru")
    print("=" * 62)
    cevapla("Evde pizza hamuru nasıl yapılır?", indeks)


def ana():
    ayrıştırıcı = argparse.ArgumentParser(description="Vikipedi'den Türkçe RAG örneği (Ollama)")
    ayrıştırıcı.add_argument("--soru", help="tek soru sor ve çık")
    ayrıştırıcı.add_argument("--test", action="store_true", help="yalnızca getirim testi")
    argümanlar = ayrıştırıcı.parse_args()

    print(f"[veri] korpus Vikipedi'den indiriliyor: {len(WIKI_BASLIKLARI)} madde...")
    belgeler = korpus_olustur()
    indeks = indeksle(belgeler)

    if argümanlar.soru:
        cevapla(argümanlar.soru, indeks)
        return

    if not argümanlar.test:
        print("=" * 62)
        print("DEMO — iki örnek soru (ikincisi kapsam dışı)")
        print("=" * 62)
        cevapla("Marmaray hangi iki yakayı birbirine bağlar?", indeks)
        kapsam_disi_testi(indeks)

    getirim_testi(indeks)


if __name__ == "__main__":
    ana()
