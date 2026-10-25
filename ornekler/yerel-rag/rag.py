# -*- coding: utf-8 -*-
"""
Yerel RAG örneği — Ollama üzerinde uçtan uca çalışır.

Akış:
  1. Kurgusal "Bulut Kargo A.Ş." politika belgelerini bge-m3 ile vektörleştir
  2. Soruyu vektörleştirip kosinüs benzerliğiyle en ilgili belgeleri getir
  3. Getirilen belgeleri bağlama ekleyip qwen2.5:3b ile cevap üret
  4. Getirim testi (hit@1 / hit@3) ve kapsam dışı soru testi

Gereksinim: çalışır durumda bir Ollama sunucusu (http://127.0.0.1:11434) ve:
    ollama pull bge-m3
    ollama pull qwen2.5:3b-instruct-q4_K_M

Harici Python paketi GEREKMEZ — yalnızca standart kütüphane kullanılır.

Kullanım:
    python rag.py                     # tüm demo: indeks + 3 soru + iki test
    python rag.py --soru "soru"       # tek soru sor
    python rag.py --test              # yalnızca getirim testi
"""

import argparse
import json
import math
import sys
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


# Windows'ta "localhost" ad çözümlemesi istek başına ~2 sn ekliyor (ölçüldü: 2,03 sn);
# sayısal adres aynı isteği 0,00 sn'de çözüyor.
OLLAMA = _url_dogrula("http://127.0.0.1:11434")
GOMME_MODELI = "bge-m3"
SOHBET_MODELI = "qwen2.5:3b-instruct-q4_K_M"
K = 2                     # bağlama eklenecek belge sayısı
ZAYIF_ESIK = 0.35         # en iyi benzerlik bunun altındaysa uyarı basılır (bu korpus üzerinde ölçüldü)

SISTEM_TALIMATI = (
    "Sen Bulut Kargo A.Ş.'nin müşteri destek asistanısın. "
    "SADECE sana verilen belgelerdeki bilgiyi kullan; kendi bilgiinden ekleme yapma. "
    "Belgelerde cevap yoksa 'Bu konuda belgelerde bilgi yok' de. "
    "Türkçe, kısa ve net cevap ver. Kullandığın belgelerin kimliğini köşeli parantezle belirt, örn. [iade]."
)

BELGELER = [
    {
        "id": "iade",
        "baslik": "İade Politikası",
        "metin": ("Müşteriler, ürünü teslim aldıktan sonra 14 gün içinde hiçbir gerekçe göstermeden iade edebilir. "
                  "İade kabul edilen ürünler ambalajı açılmamış ve kullanılmamış olmalıdır. "
                  "İade kargo ücreti alıcıya aittir; hatalı ürünlerde bu ücret şirketimize aittir. "
                  "Dijital olarak indirilen ürünler ve kişiselleştirilmiş baskılar iade kapsamı dışındadır."),
    },
    {
        "id": "teslimat",
        "baslik": "Teslimat Süreleri",
        "metin": ("Gönderiler Türkiye'nin 81 iline teslim edilir. Şehir içinde teslimat 1-2 iş günü, "
                  "şehirler arası 2-4 iş günü sürer. Köy ve mahalle yolu kapalı adreslere teslimat bir iş günü daha eklenir. "
                  "Resmî tatiller iş günü sayılmaz; Cuma 17:00 sonrası verilen siparişler Pazartesi işleme alınır."),
    },
    {
        "id": "hasar",
        "baslik": "Hasar ve Kayıp Süreci",
        "metin": ("Hasarlı paket teslim aldığınızda 48 saat içinde müşteri hizmetlerimize fotoğrafıyla birlikte bildirimde bulunmalısınız. "
                  "Tazminat, gönderinin beyan edilen değeriyle sınırlıdır; beyan yapılmamışsa standart tazminat tablosu uygulanır. "
                  "Kayıp kargolar, son takip güncellemesinden 10 iş günü sonra kayıp sayılır ve tazmin süreci başlar."),
    },
    {
        "id": "kvkk",
        "baslik": "Kişisel Verilerin Korunması",
        "metin": ("Fatura ve sözleşme kayıtları, vergi mevzuatının zorunlu kıldığı 5 yıl boyunca saklanır. "
                  "Kişisel verilerinizin silinmesini yazılı olarak talep edebilirsiniz; talepler 30 gün içinde yanıtlanır. "
                  "Ticari elektronik ileti izninizi dilediğiniz an geri alabilirsiniz; izin geri alınca pazarlama iletileri sonraki gönderim döneminde durur."),
    },
    {
        "id": "odeme",
        "baslik": "Ödeme Yöntemleri",
        "metin": ("Kredi kartı, banka kartı, havale/EFT ve kapıda ödeme kabul edilir. "
                  "Kapıda ödemede 15 TL hizmet bedeli alınır. 500 TL ve üzeri siparişlerde kredi kartına 3 taksit yapılabilir. "
                  "Havale/EFT ödemelerinde gönderi, ödeme hesabımıza ulaştıktan sonra işleme alınır."),
    },
    {
        "id": "kampanya",
        "baslik": "Kampanya ve İndirimler",
        "metin": ("İlk siparişinde %10 indirim kazanır. Her salı günü öğrencilere %15 indirim uygulanır; öğrenci belgesi gönderimde zorunludur. "
                  "Kampanya kodları tek kullanımlıktır ve başka indirimle birleştirilemez. Kampanya süreleri duyuru sayfasında yayımlanır."),
    },
    {
        "id": "ek-hizmet",
        "baslik": "Ek Gönderim Hizmetleri",
        "metin": ("Sigortalı gönderimde ücret, beyan edilen değerin %0,5'idir. SMS ile takip bildirimi tüm gönderilerde ücretsizdir. "
                  "Adrese teslimatta saat dilimi seçimi 20 TL'dir ve yalnızca metropol illerde sunulur. "
                  "Yurt dışına gönderim şu anda sadece Kuzey Kıbrıs'a yapılmaktadır."),
    },
    {
        "id": "kurumsal",
        "baslik": "Hakkımızda",
        "metin": ("Bulut Kargo A.Ş. 2011 yılında İzmir'de kuruldu. Bugün 3.200 çalışanı ve 45 dağıtım merkeziyle yılda 90 milyon gönderi taşır. "
                  "Şirket, 2023'ten bu yana tüm şehir içi teslimatlarda elektrikli araç filosu kullanır."),
    },
]

TEST_SORULARI = [
    ("İade sürem var mı, ne kadar sürede iade edebilirim?", "iade"),
    ("Kargom hasarlı geldi, ne yapmalıyım?", "hasar"),
    ("Siparişim kaç günde teslim olur?", "teslimat"),
    ("Kişisel verilerimin silinmesini isteyebilir miyim?", "kvkk"),
    ("Kapıda ödeme ek ücret gerektiriyor mu?", "odeme"),
    ("Öğrencilere indirim var mı?", "kampanya"),
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


def _get(uç_nokta):
    with urllib.request.urlopen(f"{OLLAMA}{uç_nokta}", timeout=10) as yanıt:
        return json.loads(yanıt.read().decode("utf-8"))


def ön_kontrol():
    try:
        modeller = [m["name"] for m in _get("/api/tags")["models"]]
    except (urllib.error.URLError, ConnectionError):
        sys.exit("HATA: Ollama sunucusuna ulaşılamadı. Önce Ollama'yı baştırın (ollama serve ya da masaüstü uygulaması).")
    for gerekli in (GOMME_MODELI, SOHBET_MODELI):
        varsa = any(m == gerekli or m.split(":")[0] == gerekli.split(":")[0] for m in modeller)
        if not varsa:
            sys.exit(f"HATA: '{gerekli}' modeli bulunamadı. Kurun: ollama pull {gerekli}")


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


def indeksle():
    t0 = time.time()
    indeks = []
    for belge in BELGELER:
        vektör = gomme(belge["metin"])
        indeks.append((belge, vektör))
    print(f"[indeks] {len(indeks)} belge vektörleştirildi ({time.time() - t0:.1f} sn, "
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
        f"[{b['id']}] {b['baslik']}: {b['metin']}" for _, b in skorlu
    )
    print(f"[arama] en iyi benzerlik: {en_iyi_skor:.3f} -> {', '.join(b['id'] for _, b in skorlu)}")
    if en_iyi_skor < ZAYIF_ESIK:
        print(f"[uyarı] en iyi benzerlik {ZAYIF_ESIK} eşiğinin altında — model 'yok' demelidir.")

    mesajlar = [
        {"role": "system", "content": SISTEM_TALIMATI},
        {"role": "user", "content": f"Belgeler:\n{bağlam}\n\nSoru: {soru}"},
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
    print("GETİRİM TESTİ — doğru belge ilk k'ta geldi mi?")
    print("=" * 62)
    hit1 = 0
    hit3 = 0
    for soru, beklenen in TEST_SORULARI:
        üst3 = getir(soru, indeks, k=3)
        sıralama = [b["id"] for _, b in üst3]
        durum1 = "OK " if beklenen == sıralama[0] else "MISS"
        durum3 = "OK " if beklenen in sıralama else "MISS"
        hit1 += beklenen == sıralama[0]
        hit3 += beklenen in sıralama
        print(f"  [{durum1}|{durum3}] {soru}")
        print(f"        beklenen: {beklenen}  bulunan: {sıralama}")
    print(f"\n  hit@1: {hit1}/{len(TEST_SORULARI)}   hit@3: {hit3}/{len(TEST_SORULARI)}\n")


def kapsam_disi_testi(indeks):
    print("=" * 62)
    print("KAPSAM DIŞI TEST — belgelerde olmayan soru")
    print("=" * 62)
    cevapla("Ankara'da hava nasıl?", indeks)


def ana():
    ayrıştırıcı = argparse.ArgumentParser(description="Yerel RAG örneği (Ollama)")
    ayrıştırıcı.add_argument("--soru", help="tek soru sor ve çık")
    ayrıştırıcı.add_argument("--test", action="store_true", help="yalnızca getirim testi")
    argümanlar = ayrıştırıcı.parse_args()

    ön_kontrol()
    indeks = indeksle()

    if argümanlar.soru:
        cevapla(argümanlar.soru, indeks)
        return

    if not argümanlar.test:
        print("=" * 62)
        print("DEMO — üç örnek soru (ikincisi kapsam dışı)")
        print("=" * 62)
        for soru in ("İade sürem var mı?", "Kargom hasarlı geldi, ne yapmalıyım?"):
            cevapla(soru, indeks)
        kapsam_disi_testi(indeks)

    getirim_testi(indeks)


if __name__ == "__main__":
    ana()
