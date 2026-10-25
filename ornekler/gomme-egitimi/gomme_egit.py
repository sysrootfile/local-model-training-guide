#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gömme (embedding) modeli eğitim kafesi — CPU'da gerçek koşum.

Kol A: sıfır atış. Eğitim görmemiş çok dilli MiniLM ile aynı test kümesinde
bge-m3 (Ollama) karşılaştırması, kosinüs / nokta çarpımı / Öklid farkı, sorgu
önek etkisi ve bağlam tavanının (max_seq_length) uzun parçaya etkisi.
Kol B: eğitim. MultipleNegativesRankingLoss ile (anchor, positive) çiftleri,
zor negatifli üçlüler ve ikinci tohum. Her kolda aynı sabit test kümesiyle
hit@1 / hit@3 / MRR yeniden ölçülür; ezber kontrolü ayrı sayılır.
Kol C: LoRA. Aynı eğitim, tüm ağırlıklar yerine adaptör; eğitilebilir parametre
sayısı, adım başına süre ve diske yazılan bayt ölçülür.
Kol D: batch tavanı. In-batch negatif sayısının süreye ve getiriye etkisi.
Kol E: /api/embed gideri. 24 parçayı tek istekte vs 24 ayrı istekte gönderme;
beş tekrar, dönüşümlü sıra, ön kayıtlı min-maks aralık kuralı.

Kullanım:
    python -u gomme_egit.py --kol a
    python -u gomme_egit.py --kol b
    python -u gomme_egit.py --kol e
    python -u gomme_egit.py --kol hepsi         # a, b, c, d (e hariç)
    python -u gomme_egit.py --kol b --duman     # 8 adımlık hızlı devre testi

Model ağırlıkları Hugging Face'ten bir kez iner ve depo kökündeki .hfcache
klasöründe durur; eğitim ve değerlendirme tamamen yerelde, CPU'da koşar.
Kol A'daki bge-m3 satırları için Ollama'nın 127.0.0.1:11434 adresinde çalışması
gerekir; çalışmıyorsa o satırlar atlanır, betik çökmez.
"""
import argparse
import json
import os
import random
import statistics
import time
import urllib.request
from pathlib import Path

BURADA = Path(__file__).resolve().parent
DEPO = BURADA.parent.parent
CIKTI = BURADA / "cikti"
os.environ.setdefault("HF_HOME", str(DEPO / ".hfcache"))

MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


OS = _url_dogrula("http://127.0.0.1:11434")
GOMME = "bge-m3"
ADIM = 240
BATCH = 16
OGRENME = 2e-5
TOHUM = 1234
ONEK = "Represent this sentence for searching relevant passages: "

# --------------------------------------------------------------------- veri --
# Kurgusal Yıldıztepe mahallesine ait metinler; tamamı bu betik için elle
# yazıldı, gerçek bir kurumun verisi değil. EGİTİM kümesi ile GEVDE/SORULAR
# kümesi bilerek ayrık: aynı cümle iki yerde geçmiyor.
GEVDE = [
    "Yıldıztepe Aile Sağlığı Merkezi hafta içi 08.00-17.00 arasında hizmet veriyor; randevular MHRS üzerinden alınıyor.",
    "Bağlantı yolu hattı tek yön çalışıyor ve sabah 07.00-09.30 arası yalnızca otobüs geçişine açık.",
    "Su kesintisi planlaması belediye sitesinin duyurular sekmesinde üç günlük pencereyle yayınlanıyor.",
    "Emlak vergisinin ikinci taksiti kasım ayının son iş gününe kadar çevrim içi ödeme ekranından yatırılıyor.",
    "Çöp toplama takvimi mahalleden mahalleye değişiyor; akşam 20.00'den sonra çıkarılan poşetler ertesi güne kalıyor.",
    "Aile hekimliği raporları sistemde onaylandıktan iki iş günü sonra eczanede görünüyor.",
    "Semt polikliniğinde ultrason randevusu için yönlendirme kâğıdı şart; yoksa kayıt alınmıyor.",
    "Okul servisleri kayıt döneminde belediye taşıma kartına bağlanıyor; kartsız biniş yapılamıyor.",
    "Gürültü şikâyeti için önce zabıta nöbet hattı aranıyor, tutanak numarası sonraki başvuruda isteniyor.",
    "Park yasağı tabelaları kaldırım çalışmasının bittiği gün toplanıyor, bir gün önce değil.",
    "Eczacı nöbet listesi her pazar 18.00'de ilçe ecza odasının panosuna asılıyor.",
    "Anne-bebek izlem aşıları ayın ilk salı günü sağlık ocağında toplu yapılıyor.",
    "Geri dönüşüm konteynerleri kahverengi ve yeşil olmak üzere iki bölmeli; cam ayrı toplanmıyor.",
    "Taziye evi başvurusu muhtarlık imzasıyla belediye masasına gidiyor, onay iki günde çıkıyor.",
    "Kapalı pazar yerinde tezgâh yeri kurası aralık ayında çekiliyor ve numara sezon boyunca sabit kalıyor.",
    "Yaya geçidi talep formu e-belediye ekranından dolduruluyor, fotoğraf eklenmesi şart.",
    "Doğalgaz açma randevusu için tesisat uygunluk raporu ibraz edilmek zorunda.",
    "Muhtarlık belgeleri mesai bitiminden yarım saat önce kesiliyor; nüfus kayıt örneği verilemiyor.",
    "Kreş kayıtları kontenjan doluysa yedek listeden yürüyor, sıra telefonla güncelleniyor.",
    "Büyükşehir otobüsünde aktarma ilk binişten sonraki altmış dakika boyunca ücretsiz sayılıyor.",
    "Sokak hayvanları için ihbar edilen adres tutanağa geçiyor, aynı gün ekip yönlendiriliyor.",
    "İtfaiye eğitim talebi okul müdürlüğü üzerinden yazılı yapılıyor, sözlü başvuru kabul edilmiyor.",
    "İş makinesi kiralama ihalesi her yıl şubat ayında yenileniyor; sözleşme üç ay önceden bildirilmeden feshedilemez.",
    "Yol bakım çalışmasında kaldırım geçici kapatılıyor, karşı kaldırım çift yön kullanılıyor.",
]

SORULAR = [
    ("Aile sağlığı merkezine randevuyu nereden alabilirim?", 0),
    ("Bağlantı yolunda sabah trafiği nasıl işliyor?", 1),
    ("Sular ne zaman kesilecek, nereden öğrenirim?", 2),
    ("Emlak vergisinin son taksitini ne zamana kadar ödemeliyim?", 3),
    ("Yazdırılan raporu eczane sistemde görecek mi?", 5),
    ("Okul servisine binmek için ne gerekiyor?", 7),
    ("Gece gürültü yapan komşu için kimi aramalıyım?", 8),
    ("Otobüs aktarmasında indirim ne kadar sürüyor?", 19),
]

EGITIM = [
    ("Randevular MHRS üzerinden alınıyor.", "Aile Sağlığı Merkezi randevuları MHRS'den yapılıyor."),
    ("Sabah otobüsten başka araç giremiyor.", "07.00-09.30 arası bağlantı yolu yalnızca otobüse açık."),
    ("Kesintiler sitede duyuruluyor.", "Belediye sitesinin duyurular sekmesinde üç günlük kesinti listesi var."),
    ("Verginin son ödemesi kasımın sonunda.", "Emlak vergisi ikinci taksiti kasım ayının son iş gününe kadar."),
    ("Rapor iki günde eczaneye düşüyor.", "Aile hekimliği raporu onaylandıktan iki iş günü sonra eczanede görünür."),
    ("Kartsız servise binilmez.", "Okul servisleri belediye taşıma kartına bağlıdır, kartsız biniş yapılamaz."),
    ("Önce zabıta aranmalı.", "Gürültü için önce zabıta nöbet hattı aranır, tutanak numarası saklanır."),
    ("Tabelalar iş bitince kalkıyor.", "Park yasağı tabelaları çalışmanın bittiği gün toplanıyor."),
    ("Nöbet listesi pazar asılıyor.", "Eczacı nöbet listesi her pazar 18.00'de panoya asılıyor."),
    ("Aşılar ayın ilk salısı.", "Anne-bebek izlem aşıları ayın ilk salı günü toplu yapılıyor."),
    ("Cam ayrı alınmıyor.", "Konteynerler kahverengi ve yeşil bölmelidir; cam ayrı toplanmıyor."),
    ("Muhtar imzası gerekiyor.", "Taziye evi başvurusu muhtarlık imzasıyla belediyeye gidiyor."),
    ("Kura aralıkta çekiliyor.", "Pazar tezgâhı kurası aralıkta çekilir, numara sezon boyunca sabittir."),
    ("Formu e-belediyeden doldurun.", "Yaya geçidi talebi e-belediye formuyla olur, fotoğraf eklenmesi şarttır."),
    ("Rapor olmadan gaz açılmaz.", "Doğalgaz açma randevusunda tesisat uygunluk raporu isteniyor."),
    ("Belgeler mesai bitmeden alınmalı.", "Muhtarlık belgeleri mesai bitiminden yarım saat önce kesiliyor."),
    ("Yedek liste telefonla yürüyor.", "Kreşte kontenjan doluysa kayıt yedek listeden, telefonla güncelleniyor."),
    ("Aktarma bir saat ücretsiz.", "Büyükşehir otobüsünde ilk binişten sonraki altmış dakika aktarma ücretsizdir."),
    ("Adres tutanağa işleniyor.", "Sokak hayvanı ihbarında adres tutanağa yazılır, aynı gün ekip çıkar."),
    ("Yazılı başvuru şart.", "İtfaiye eğitimi için okul müdürlüğü üzerinden yazılı talep gerekir."),
    ("İhale şubatta yenilenir.", "İş makinesi kiralama ihalesi her şubat yenilenir, fesih üç ay önceden bildirilir."),
    ("Karşı kaldırım çift yön.", "Çalışma sırasında kaldırım kapanır, karşı kaldırım çift yön kullanılır."),
    ("Eczane raporu sistemden görür.", "Onaylanan rapor sistem üzerinden eczaneye iki iş gününde düşüyor."),
    ("Servis kartı binmek için lazım.", "Taşıma kartı olmayan öğrenci okul servisine binemiyor."),
    ("Nöbetçi eczane panoda yazar.", "İlçe ecza odasının panosuna pazar günleri nöbet listesi asılıyor."),
    ("Tutanak numarası sorulur.", "Zabıta tutanağının numarası sonraki başvurularda isteniyor."),
    ("Çalışma bitince tabela iniyor.", "Yol çalışması bittiği gün park yasakları tabelaları kaldırılıyor."),
    ("Aşı takvimi ocakta uygulanır.", "İzlem aşıları için ayın ilk salı günü sağlık ocağına geliniyor."),
    ("Atık iki bölmeye ayrılır.", "Geri dönüşüm atıkları kahverengi ve yeşil bölmelere ayrılıyor."),
    ("Dilekçe evrak masasına verilir.", "Muhtar onaylı dilekçe belediye evrak masasına teslim ediliyor."),
    ("Tezgâh numarası sezon boyu sabit.", "Kapalı pazarda çekilen kura numarası tüm sezon geçerli oluyor."),
    ("Forma fotoğraf eklenmeli.", "Yaya geçidi formuna kaldırım fotoğrafı eklenmesi zorunlu tutuluyor."),
    ("Uygunluk kâğıdı ibraz edilmeli.", "Gaz açma işleminde tesisat raporu ibraz edilmeden randevu verilmiyor."),
    ("Öğleden sonra belge yok.", "Muhtarlık mesai bitiminden yarım saat önce nüfus kaydı vermiyor."),
    ("Sıra telefon görüşmesiyle güncellenir.", "Kreş yedek listesindeki sıra telefonla teyit edilerek ilerliyor."),
    ("Binişten sonra altmış dakika.", "Otobüs aktarması ilk binişin üzerinden bir saat dolana kadar ücretsizdir."),
    ("Ekip aynı gün gönderilir.", "İhbar adresine kayıttan sonra aynı gün sokak hayvanı ekibi yollanıyor."),
    ("Müdürlük yazısı istenir.", "Okul için itfaiye eğitimi talebi müdürlük yazısıyla yapılıyor."),
    ("Sözleşme erken bozulamaz.", "Makine kiralama sözleşmesi üç ay önceden bildirilmeden feshedilemiyor."),
    ("Yaya karşı tarafa alınıyor.", "Bakım boyunca yayalar karşı kaldırımdan iki yönlü yürüyor."),
]

ALTIN = [g for _, g in SORULAR]
SORU_METINLERI = [q for q, _ in SORULAR]


# ---------------------------------------------------------------- yardımcılar -
def yaz(metin=""):
    print(metin, flush=True)


def baslik(metin):
    yaz("")
    yaz("=" * 78)
    yaz(metin)
    yaz("=" * 78)


def sn(t0):
    return f"{time.time() - t0:.2f} sn"


def yol_boyutu(yol):
    toplam = 0
    for kok, _, dosyalar in os.walk(yol):
        for ad in dosyalar:
            try:
                toplam += (Path(kok) / ad).stat().st_size
            except OSError:
                pass
    return toplam


def ollama_gomme_istek(metinler, model=GOMME, keep_alive=None):
    govde = {"model": model, "input": metinler}
    if keep_alive is not None:
        govde["keep_alive"] = keep_alive
    istek = json.dumps(govde).encode("utf-8")
    req = urllib.request.Request(_url_dogrula(f"{OS}/api/embed"), data=istek,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as yanit:
        veri = json.loads(yanit.read().decode("utf-8"))
    return ([[float(x) for x in satir] for satir in veri["embeddings"]],
            time.time() - t0, veri)


def ollama_gommeler(metinler, model=GOMME):
    return ollama_gomme_istek(metinler, model)[0]


def kosinus(a, b):
    return sum(x * y for x, y in zip(a, b))


def oksid(a, b):
    return -sum((x - y) ** 2 for x, y in zip(a, b))


def puan_matrisi(sorgular, adaylar, fonksiyon):
    return [[fonksiyon(q, c) for c in adaylar] for q in sorgular]


def derece(puanlar, altin_id):
    sirali = sorted(range(len(puanlar)), key=lambda j: -puanlar[j])
    return sirali.index(altin_id) + 1


def degerlendir(etiket, sorgular, adaylar, fonksiyon=kosinus):
    satirlar = puan_matrisi(sorgular, adaylar, fonksiyon)
    rler = [derece(satirlar[i], ALTIN[i]) for i in range(len(ALTIN))]
    dogru = [satirlar[i][ALTIN[i]] for i in range(len(ALTIN))]
    yanlis = [p for i, satir in enumerate(satirlar)
              for j, p in enumerate(satir) if j != ALTIN[i]]
    ozet = {
        "etiket": etiket,
        "hit1": sum(r == 1 for r in rler),
        "hit3": sum(r <= 3 for r in rler),
        "mrr": statistics.fmean(1.0 / r for r in rler),
        "dogru_min": min(dogru),
        "dogru_ort": statistics.fmean(dogru),
        "dogru_maks": max(dogru),
        "yanlis_maks": max(yanlis),
        "ayirma": min(dogru) - max(yanlis),
        "dereceler": rler,
    }
    n = len(rler)
    yaz(f"  {etiket:<32} hit@1 {ozet['hit1']}/{n}  hit@3 {ozet['hit3']}/{n}  "
        f"MRR {ozet['mrr']:.3f} | doğru bandı {ozet['dogru_min']:.3f}"
        f"-{ozet['dogru_maks']:.3f} (ort {ozet['dogru_ort']:.3f}), en iyi yanlış "
        f"{ozet['yanlis_maks']:.3f}, ayırma {ozet['ayirma']:+.3f} | {rler}")
    return ozet


def encode(model, metinler, normalize=True, **kw):
    t0 = time.time()
    v = model.encode(metinler, convert_to_numpy=True,
                     normalize_embeddings=normalize, **kw)
    return [[float(x) for x in satir] for satir in v], time.time() - t0


def cift_benzerlik(model, ciftler):
    a, _ = encode(model, [x for x, _ in ciftler], batch_size=8)
    p, _ = encode(model, [y for _, y in ciftler], batch_size=8)
    return statistics.fmean(kosinus(x, y) for x, y in zip(a, p))


def agirlik_klasoru():
    """HF önbelleğinde modelin gerçek klasörü: org adı da klasör adına girer."""
    hub = DEPO / ".hfcache" / "hub"
    adlar = [y for y in hub.glob("models--*") if MODEL in y.name]
    return adlar[0] if adlar else hub


def model_yukle(ol=False):
    from sentence_transformers import SentenceTransformer
    t0 = time.time()
    model = SentenceTransformer(MODEL)
    sure = time.time() - t0
    return (model, sure) if ol else model


def argumanlar(etiket, adim, batch, lr, seed):
    from sentence_transformers import SentenceTransformerTrainingArguments
    return SentenceTransformerTrainingArguments(
        output_dir=str(CIKTI / f"chk-{etiket}"), max_steps=adim,
        per_device_train_batch_size=batch, learning_rate=lr, seed=seed,
        optim="adamw_torch", logging_steps=10, save_strategy="no",
        report_to=[], warmup_steps=0.1, dataloader_drop_last=True, use_cpu=True)


def ollama_zaman(metinler):
    t0 = time.time()
    return ollama_gommeler(metinler), time.time() - t0


# -------------------------------------------------------------------- kol A ---
def kol_a(args):
    t0 = time.time()
    baslik("KOL A: SIRI ATIŞ (eğitim görmemiş model + sabit test kümesi)")
    import psutil
    import torch

    surec = psutil.Process()
    r0 = surec.memory_info().rss / 1024 ** 2
    y0 = time.time()
    model = model_yukle()
    yukleme = time.time() - y0
    tam = sum(p.numel() for p in model.parameters())
    r1 = surec.memory_info().rss / 1024 ** 2
    yaz(f"model                      : {MODEL}")
    yaz(f"önbellekten yükleme        : {yukleme:.2f} sn")
    yaz(f"parametre {tam:,} | çıkış boyutu {model.get_embedding_dimension()} | "
        f"varsayılan max_seq_length {model.max_seq_length}")
    yaz(f"süreç RSS                  : {r0:.0f} MB -> {r1:.0f} MB (+{r1 - r0:.0f} MB)")
    yaz(f"torch {torch.__version__} | kullanan is parçacığı {torch.get_num_threads()}")
    t_w = time.time()
    _ikinci = model_yukle()
    yaz(f"tekrar yükleme (2.)        : {time.time() - t_w:.2f} sn")
    del _ikinci
    kayit_yol = agirlik_klasoru()
    yaz(f"indirilen ağırlık klasörü   : {yol_boyutu(kayit_yol) / 1024 ** 2:.1f} MB "
        f"({kayit_yol.name})")

    tok = model.tokenizer
    uzunlar = [len(tok.encode(t, add_special_tokens=False)) for t in GEVDE]
    yaz(f"gövde parça token sayıları  : min {min(uzunlar)}, ort "
        f"{statistics.fmean(uzunlar):.1f}, maks {max(uzunlar)}")

    aday_v, s_aday = encode(model, GEVDE, batch_size=8)
    sorgu_v, s_sorgu = encode(model, SORU_METINLERI, batch_size=8)
    yaz(f"encode                     : {len(GEVDE)} parça {s_aday:.2f} sn "
        f"({len(GEVDE) / s_aday:.1f} parça/sn), {len(SORU_METINLERI)} sorgu "
        f"{s_sorgu:.2f} sn ({len(SORU_METINLERI) / s_sorgu:.2f} sorgu/sn)")

    ham_a, _ = encode(model, GEVDE, normalize=False, batch_size=8)
    ham_q, _ = encode(model, SORU_METINLERI, normalize=False, batch_size=8)

    yaz("")
    yaz("MiniLM — dört puanlama biçimi, aynı test kümesi:")
    sonuclar = [
        degerlendir("normalize + kosinus", sorgu_v, aday_v),
        degerlendir("normalize + negatif Öklid", sorgu_v, aday_v, oksid),
        degerlendir("ham + nokta çarpımı", ham_q, ham_a),
        degerlendir("ham + negatif Öklid", ham_q, ham_a, oksid),
    ]

    yaz("")
    yaz("bge-m3 (Ollama, yerel) — aynı test kümesi:")
    try:
        with urllib.request.urlopen(f"{OS}/api/version", timeout=5) as yanit:
            surum = json.loads(yanit.read().decode("utf-8")).get("version", "?")
        yaz(f"  Ollama sürümü: {surum}")
        a3, s_a = ollama_zaman(GEVDE)
        q3, s_q = ollama_zaman(SORU_METINLERI)
        yaz(f"  indeks {s_a:.2f} sn ({len(GEVDE) / s_a:.1f} parça/sn), "
            f"{len(SORU_METINLERI)} sorgu {s_q:.2f} sn, boyut {len(a3[0])}")
        sonuclar.append(degerlendir("bge-m3 + kosinus", q3, a3))
        onekli, s_on = ollama_zaman([ONEK + q for q in SORU_METINLERI])
        yaz(f"  önekli sorgu encode {s_on:.2f} sn")
        sonuclar.append(degerlendir("bge-m3 + onekli sorgu", onekli, a3))
    except Exception as hata:  # noqa: BLE001
        yaz(f"  atlandı: {type(hata).__name__}: {hata}")

    yaz("")
    yaz("BAĞLAM TAVANI — kuyrukta kalan bilgi görünür mü?")
    kres_sorgusu = "Kreşte sıra yedek listesinden mi ilerliyor?"
    govde = " ".join([GEVDE[0], GEVDE[5], GEVDE[12], GEVDE[22], GEVDE[9], GEVDE[14],
                      GEVDE[2]])
    uzun_parca = govde + " " + GEVDE[18]
    kt = len(tok.encode(uzun_parca, add_special_tokens=False))
    adaylik = GEVDE + [uzun_parca]
    hedef = len(GEVDE)
    yaz(f"  birleşik parça {kt} token; kuyruk cümlesi = [{GEVDE[18][:48]}...] "
        f"(gövde {len(tok.encode(govde, add_special_tokens=False))} token)")
    for tavan in (128, 512):
        model.max_seq_length = tavan
        gorunen = min(kt, tavan - 2)
        v, _ = encode(model, [uzun_parca, kres_sorgusu], batch_size=2)
        a_t, _ = encode(model, adaylik, batch_size=8)
        puan = [kosinus(v[1], c) for c in a_t]
        yaz(f"  tavan {tavan} (~{gorunen} token görünüyor): kres sorusuyla "
            f"kosinüs {kosinus(v[1], v[0]):.3f}, uzun parçanın aday sırası "
            f"{derece(puan, hedef)} / 25")
    model.max_seq_length = 128
    v128, _ = encode(model, [uzun_parca], batch_size=1)
    model.max_seq_length = 512
    v512, _ = encode(model, [uzun_parca], batch_size=1)
    model.max_seq_length = 128
    yaz(f"  aynı parçanın 128 ve 512 tavanıyla üretilen vektörlerinin "
        f"kosinüsü {kosinus(v128[0], v512[0]):.3f}")

    yaz("")
    yaz("NOT: 8 soru / 24 parça. Bu tablo modellerin genel kapasitesini değil, "
        "bu korpustaki davranışını ölçer; güven aralığı hesaplanmadı.")
    (CIKTI / "kol-a.json").write_text(json.dumps(sonuclar, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    yaz(f"koşum süresi: {sn(t0)}")


# -------------------------------------------------------------------- kol B ---
def kol_b(args):
    baslik("KOL B: EĞİTİM (adım sayısı / öğrenme hızı / zor negatif / tohum)")
    from datasets import Dataset
    from sentence_transformers import SentenceTransformerTrainer
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
    import psutil

    kisa = 8 if args.duman else 30
    orta = 8 if args.duman else 120
    uzun = 8 if args.duman else 240
    # (etiket, veri, adim, lr, tohum)  — veri: "cift" veya "zor"
    kollar = [
        ("cift-30", "cift", kisa, OGRENME, TOHUM),
        ("cift-120", "cift", orta, OGRENME, TOHUM),
        ("cift-240", "cift", uzun, OGRENME, TOHUM),
        ("zor-240", "zor", uzun, OGRENME, TOHUM),
        ("cift-240-lr4", "cift", uzun, 1e-4, TOHUM),
        ("cift-240-t5678", "cift", uzun, OGRENME, 5678),
    ]
    if args.duman:
        kollar = kollar[:2]

    surec = psutil.Process()
    veri = Dataset.from_list([{"anchor": a, "positive": p} for a, p in EGITIM])
    zor_veri = None
    yaz(f"eğitim çiftleri {len(EGITIM)} | test {len(SORULAR)} soru / {len(GEVDE)} parça | "
        f"batch={BATCH} kollar=" + ", ".join(k[0] for k in kollar))

    ozet = []
    for etiket, vtip, adim, lr, seed in kollar:
        yaz("")
        yaz(f"--- {etiket} (adim={adim}, lr={lr:g}, tohum={seed}, veri={vtip}) ---")
        model, yukleme = model_yukle(True)
        aday_once, _ = encode(model, GEVDE, batch_size=8)
        sorgu_once, _ = encode(model, SORU_METINLERI, batch_size=8)
        once = degerlendir(f"{etiket} ÖNCE", sorgu_once, aday_once)
        ezber_once = cift_benzerlik(model, EGITIM)

        hedef = veri
        if vtip == "zor":
            from sentence_transformers import mine_hard_negatives
            if zor_veri is None:
                t1 = time.time()
                zor_veri = mine_hard_negatives(
                    dataset=veri, model=model, anchor_column_name="anchor",
                    positive_column_name="positive",
                    corpus=[p for _, p in EGITIM], num_negatives=1,
                    sampling_strategy="top", range_min=1, verbose=False)
                yaz(f"  zor negatif madenciliği {sn(t1)} | sütunlar "
                    f"{zor_veri.column_names}")
                yaz(f"  örnek üçgen: ({zor_veri[0]['anchor'][:44]} | "
                    f"{zor_veri[0]['positive'][:44]} | -{zor_veri[0]['negative'][:44]})")
            hedef = zor_veri

        kayip = MultipleNegativesRankingLoss(model)
        r0 = surec.memory_info().rss / 1024 ** 2
        t1 = time.time()
        trainer = SentenceTransformerTrainer(
            model=model, args=argumanlar(etiket, adim, BATCH, lr, seed),
            train_dataset=hedef, loss=kayip)
        trainer.train()
        sure = time.time() - t1
        iz = [k for k in trainer.state.log_history if "loss" in k]
        r1 = surec.memory_info().rss / 1024 ** 2
        yaz(f"  eğitim {adim} adım {sure:.2f} sn -> adım başına {sure / adim:.2f} sn | "
            f"RSS {r0:.0f} -> {r1:.0f} MB")
        if iz:
            yaz("  kayıp izi: " + " -> ".join(f"{k['loss']:.3f}@{k['step']}" for k in iz))

        aday_s, s_i = encode(model, GEVDE, batch_size=8)
        sorgu_s, _ = encode(model, SORU_METINLERI, batch_size=8)
        sonra = degerlendir(f"{etiket} SONRA", sorgu_s, aday_s)
        ezber_son = cift_benzerlik(model, EGITIM)
        yaz(f"  ezber kontrolü: eğitim çiftlerinin ortalama kosinüsü "
            f"{ezber_once:.3f} -> {ezber_son:.3f} (+{ezber_son - ezber_once:.3f}) | "
            f"yeniden indeks {s_i:.2f} sn")
        ozet.append({"kol": etiket, "veri": vtip, "tohum": seed, "adim": adim,
                     "lr": lr, "yukleme": yukleme, "sure": sure, "sn_adim": sure / adim,
                     "rss_son": r1,
                     "kayip_ilk": iz[0]["loss"] if iz else None,
                     "kayip_son": iz[-1]["loss"] if iz else None,
                     "kayip_izi": [(k["step"], k["loss"]) for k in iz],
                     "ezber_once": ezber_once, "ezber_son": ezber_son,
                     "once": once, "sonra": sonra})
        del model, trainer, kayip

    yaz("")
    yaz("FARKLAR (her kol aynı sabit test kümesinde):")
    for d in ozet:
        yaz(f"  {d['kol']:<16} hit@1 {d['once']['hit1']}->{d['sonra']['hit1']}  "
            f"hit@3 {d['once']['hit3']}->{d['sonra']['hit3']}  "
            f"MRR {d['once']['mrr']:.3f}->{d['sonra']['mrr']:.3f}  "
            f"ayırma {d['once']['ayirma']:+.3f}->{d['sonra']['ayirma']:+.3f}  "
            f"ezber {d['ezber_son'] - d['ezber_once']:+.3f}  "
            f"doğru bandı ort {d['once']['dogru_ort']:.3f}->{d['sonra']['dogru_ort']:.3f}")
    ayni = [d for d in ozet if d["kol"] in ("cift-240", "cift-240-t5678")]
    if len(ayni) == 2:
        yaz(f"  tohum varyansı ({TOHUM} vs 5678, {uzun_adim(ayni)} adım): hit@1 "
            f"{ayni[0]['sonra']['hit1']} vs {ayni[1]['sonra']['hit1']}, MRR "
            f"{ayni[0]['sonra']['mrr']:.3f} vs {ayni[1]['sonra']['mrr']:.3f}, "
            f"adım süresi {ayni[0]['sn_adim']:.2f} vs {ayni[1]['sn_adim']:.2f} sn")
    (CIKTI / "kol-b.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1),
                                      encoding="utf-8")


def uzun_adim(ayni):
    return ayni[0]["adim"]


# -------------------------------------------------------------------- kol C ---
def kol_c(args):
    baslik("KOL C: LoRA (eğitilebilir parametre / süre / disk boyutu)")
    from datasets import Dataset
    from peft import LoraConfig
    from sentence_transformers import SentenceTransformerTrainer
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
    import psutil

    adim = 8 if args.duman else ADIM
    surec = psutil.Process()
    model = model_yukle()
    tam = sum(p.numel() for p in model.parameters())
    # BERT ailesinde dikkat hatları query/key/value olarak adlandırılır;
    # Llama/Qwen ailesinin q_proj/v_proj adıyla verilen yapılandırma bu modelde hedef bulamaz.
    hedefler = ["query", "value"]
    model.add_adapter(LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                 target_modules=hedefler))
    aktif = sum(p.numel() for p in model.parameters() if p.requires_grad)
    eslesen = sum(1 for n, _ in model.named_modules()
                  if n.endswith(tuple(hedefler)))
    yaz(f"tüm ağırlıklar   : {tam:,} parametre")
    yaz(f"LoRA (r=16, hedef {hedefler}) : {aktif:,} eğitilebilir parametre "
        f"({aktif / tam * 100:.3f}%) | eşleşen modül {eslesen}")

    veri = Dataset.from_list([{"anchor": a, "positive": p} for a, p in EGITIM])
    aday_once, _ = encode(model, GEVDE, batch_size=8)
    sorgu_once, _ = encode(model, SORU_METINLERI, batch_size=8)
    once = degerlendir("lora ÖNCE", sorgu_once, aday_once)

    t1 = time.time()
    trainer = SentenceTransformerTrainer(
        model=model, args=argumanlar("lora", adim, BATCH, 1e-4, TOHUM),
        train_dataset=veri, loss=MultipleNegativesRankingLoss(model))
    trainer.train()
    sure = time.time() - t1
    iz = [k for k in trainer.state.log_history if "loss" in k]
    yaz(f"LoRA eğitimi     : {adim} adım {sure:.2f} sn -> adım başına "
        f"{sure / adim:.2f} sn | RSS {surec.memory_info().rss / 1024 ** 2:.0f} MB")
    if iz:
        yaz("  kayıp izi: " + " -> ".join(f"{k['loss']:.3f}@{k['step']}" for k in iz))

    aday_s, _ = encode(model, GEVDE, batch_size=8)
    sorgu_s, _ = encode(model, SORU_METINLERI, batch_size=8)
    sonra = degerlendir("lora SONRA", sorgu_s, aday_s)

    lora_yol = CIKTI / "lora-adapter"
    model.save(str(lora_yol))
    lora_mb = yol_boyutu(lora_yol) / 1024 ** 2
    kaynak_mb = yol_boyutu(agirlik_klasoru()) / 1024 ** 2
    yaz(f"diske yazılan     : LoRA adaptörü {lora_mb:.1f} MB | indirilen taban "
        f"ağırlık {kaynak_mb:.1f} MB")
    (CIKTI / "kol-c.json").write_text(
        json.dumps({"tam_parametre": tam, "aktif_parametre": aktif, "sure": sure,
                    "sn_adim": sure / adim, "lora_mb": lora_mb,
                    "kaynak_mb": kaynak_mb, "once": once, "sonra": sonra,
                    "kayip_izi": [(k["step"], k["loss"]) for k in iz]},
                   ensure_ascii=False, indent=1), encoding="utf-8")


# -------------------------------------------------------------------- kol D ---
def kol_d(args):
    baslik("KOL D: BATCH TAVANI (in-batch negatif sayısı 8 vs 32)")
    from datasets import Dataset
    from sentence_transformers import SentenceTransformerTrainer
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss

    adim = 8 if args.duman else ADIM
    veri = Dataset.from_list([{"anchor": a, "positive": p} for a, p in EGITIM])
    sonuc = []
    for batch in (8, 32):
        model = model_yukle()
        aday_once, _ = encode(model, GEVDE, batch_size=8)
        sorgu_once, _ = encode(model, SORU_METINLERI, batch_size=8)
        once = degerlendir(f"batch{batch} ÖNCE", sorgu_once, aday_once)
        t1 = time.time()
        trainer = SentenceTransformerTrainer(
            model=model, args=argumanlar(f"b{batch}", adim, batch, OGRENME, TOHUM),
            train_dataset=veri, loss=MultipleNegativesRankingLoss(model))
        trainer.train()
        sure = time.time() - t1
        aday_s, _ = encode(model, GEVDE, batch_size=8)
        sorgu_s, _ = encode(model, SORU_METINLERI, batch_size=8)
        sonra = degerlendir(f"batch{batch} SONRA", sorgu_s, aday_s)
        yaz(f"  batch {batch}: {adim} adım {sure:.2f} sn -> adım başına "
            f"{sure / adim:.2f} sn | sıra başına {sure / adim / batch * 1000:.0f} ms")
        sonuc.append({"batch": batch, "adim": adim, "sure": sure,
                      "sn_adim": sure / adim, "once": once, "sonra": sonra})
        del model, trainer
    (CIKTI / "kol-d.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1),
                                      encoding="utf-8")


# -------------------------------------------------------------------- kol E ---
def ns(veri, alan):
    return (veri.get(alan) or 0) / 1e9


def yuzdelik(degerler, p):
    sirali = sorted(degerler)
    if len(sirali) == 1:
        return sirali[0]
    yer = (len(sirali) - 1) * p / 100
    alt = int(yer)
    ust = min(alt + 1, len(sirali) - 1)
    return sirali[alt] + (sirali[ust] - sirali[alt]) * (yer - alt)


def ps_oku():
    try:
        with urllib.request.urlopen(f"{OS}/api/ps", timeout=30) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
    except OSError as hata:
        return {"hata": str(hata)}
    return [{"ad": m.get("name"), "boyut": m.get("size"),
             "vram": m.get("size_vram"), "bitis": m.get("expires_at")}
            for m in veri.get("models", [])]


def kol_e(args):
    baslik("KOL E: /api/embed GİDERİ (24 parça tek istekte vs 24 ayrı istekte)")
    tekrar = 1 if args.duman else 5
    yaz("ön kayıtlı kural: her yan {0} tekrar; iki yanın tekrar toplamlarının "
        "min-maks aralıkları çakışırsa 'fark ölçülemedi' yayımlanır, çakışmazsa "
        "p50'si düşük olan yan kazanır. Sıra tekrarlar arasında dönüşümlü."
        .format(tekrar))
    yaz(f"parça={len(GEVDE)} tekrar={tekrar} ölçüm isteği="
        f"{tekrar * (1 + len(GEVDE))} (+1 ısıtma, +1 tahliye sayılmaz)")
    try:
        with urllib.request.urlopen(f"{OS}/api/version", timeout=30) as yanit:
            surum = json.loads(yanit.read().decode("utf-8")).get("version")
        yaz(f"Ollama sürümü: {surum}")
    except OSError as hata:
        yaz(f"Ollama sürümü: okunamadı ({hata})")
    yaz(f"ölçüm öncesi /api/ps: {ps_oku()}")

    t_bas = time.time()
    _, is_duvar, is_veri = ollama_gomme_istek(GEVDE)
    yaz(f"ısıtma (sayılmaz): {is_duvar:.2f} sn duvar | "
        f"sunucu {ns(is_veri, 'total_duration'):.2f} sn | "
        f"yükleme {ns(is_veri, 'load_duration'):.2f} sn | "
        f"{is_veri.get('prompt_eval_count')} token | "
        f"{len(is_veri['embeddings'])} vektör")
    yaz(f"ısıtma sonrası /api/ps: {ps_oku()}")

    kayitlar = []
    for i in range(tekrar):
        sira = ("batch", "teker") if i % 2 == 0 else ("teker", "batch")
        yaz("")
        yaz(f"tekrar {i + 1}/{tekrar} (sıra: {' -> '.join(sira)})")
        satir = {"tekrar": i + 1}
        for yan in sira:
            if yan == "batch":
                gommeler, duvar, veri = ollama_gomme_istek(GEVDE)
                kayit = {"duvar": duvar, "sunucu": ns(veri, "total_duration"),
                         "yuk": ns(veri, "load_duration"),
                         "token": veri.get("prompt_eval_count"),
                         "vektor": len(gommeler)}
                yaz(f"  batch : {duvar:.2f} sn duvar | "
                    f"sunucu {kayit['sunucu']:.2f} sn | "
                    f"yükleme {kayit['yuk']:.2f} sn | {kayit['token']} token | "
                    f"{kayit['vektor']} vektör")
            else:
                duvarlar, sunucular, tokenler = [], [], []
                t0 = time.time()
                for metin in GEVDE:
                    _, duvar, veri = ollama_gomme_istek([metin])
                    duvarlar.append(duvar)
                    sunucular.append(ns(veri, "total_duration"))
                    if veri.get("prompt_eval_count") is not None:
                        tokenler.append(veri["prompt_eval_count"])
                kayit = {"duvar": time.time() - t0, "sunucu": sum(sunucular),
                         "istekler": duvarlar,
                         "p50": yuzdelik(duvarlar, 50),
                         "p95": yuzdelik(duvarlar, 95), "maks": max(duvarlar),
                         "token": sum(tokenler)}
                yaz(f"  teker : {kayit['duvar']:.2f} sn duvar | "
                    f"sunucu {kayit['sunucu']:.2f} sn | istek p50 "
                    f"{kayit['p50']:.3f} / p95 {kayit['p95']:.3f} / maks "
                    f"{kayit['maks']:.3f} sn | {kayit['token']} token")
            satir[yan] = kayit
        kayitlar.append(satir)

    ozet = {}
    for yan in ("batch", "teker"):
        duvarlar = [k[yan]["duvar"] for k in kayitlar]
        ozet[yan] = {"p50": yuzdelik(duvarlar, 50), "p95": yuzdelik(duvarlar, 95),
                     "min": min(duvarlar), "maks": max(duvarlar),
                     "ort": statistics.mean(duvarlar), "toplam": sum(duvarlar),
                     "sunucu_p50": yuzdelik([k[yan]["sunucu"] for k in kayitlar], 50)}
    if tekrar > 1:
        ozet["teker"]["istek_p50"] = yuzdelik(
            [k["teker"]["p50"] for k in kayitlar], 50)
        ozet["teker"]["istek_p95"] = yuzdelik(
            [x for k in kayitlar for x in k["teker"]["istekler"]], 95)

    baslik("KOL E ÖZET")
    for yan, ad in (("batch", "tek istek (24 parça)"), ("teker", "24 ayrı istek")):
        o = ozet[yan]
        yaz(f"{ad:<22}: p50 {o['p50']:.2f} sn | p95 {o['p95']:.2f} sn | "
            f"min {o['min']:.2f} | maks {o['maks']:.2f} | ort {o['ort']:.2f} | "
            f"toplam {o['toplam']:.2f} sn")
    fark = ozet["teker"]["p50"] - ozet["batch"]["p50"]
    yaz(f"fark (teker - batch) p50: {fark:+.2f} sn | "
        f"oran: {ozet['teker']['p50'] / ozet['batch']['p50']:.2f}x")
    if "istek_p50" in ozet["teker"]:
        yaz(f"ayrı istek başına        : p50 {ozet['teker']['istek_p50']:.3f} sn | "
            f"p95 {ozet['teker']['istek_p95']:.3f} sn (batch p50'nin 1/24'ü "
            f"{ozet['batch']['p50'] / 24:.3f} sn)")
    cakisma = not (ozet["teker"]["maks"] < ozet["batch"]["min"]
                   or ozet["batch"]["maks"] < ozet["teker"]["min"])
    if tekrar == 1:
        hukum = "tek tekrar (duman): hüküm kurulmaz"
    elif cakisma:
        hukum = "fark ölçülemedi (tekrar aralıkları çakışıyor)"
    elif ozet["teker"]["p50"] > ozet["batch"]["p50"]:
        hukum = "tek istek daha ucuz (24 ayrı istek aralığı batch'in üstünde)"
    else:
        hukum = "24 ayrı istek daha ucuz (batch aralığı 24 ayrı isteğin üstünde)"
    yaz(f"hüküm: {hukum}")
    (CIKTI / "kol-e.json").write_text(
        json.dumps({"model": GOMME, "parca": len(GEVDE), "tekrar": tekrar,
                    "duman": args.duman, "kayitlar": kayitlar, "ozet": ozet,
                    "fark_p50": fark, "hukum": hukum},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    yaz(f"ölçüm sonrası /api/ps: {ps_oku()}")
    tahliye_gommeler, tahliye_duvar, _ = ollama_gomme_istek(["tahliye"],
                                                            keep_alive=0)
    yaz(f"tahliye isteği (sayılmaz): {tahliye_duvar:.2f} sn | "
        f"{len(tahliye_gommeler)} vektör")
    yaz(f"tahliye sonrası /api/ps: {ps_oku()}")
    yaz(f"kol e toplam süre: {time.time() - t_bas:.2f} sn")


def main():
    ayristirici = argparse.ArgumentParser()
    ayristirici.add_argument("--kol", default="a",
                             choices=["a", "b", "c", "d", "e", "hepsi"])
    ayristirici.add_argument("--duman", action="store_true")
    args = ayristirici.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)
    random.seed(TOHUM)
    yaz(f"koşum başlangıcı: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    yaz(f"kol={args.kol} duman={args.duman} model={MODEL} tohum={TOHUM} "
        f"adım={8 if args.duman else ADIM} batch={BATCH} lr={OGRENME}")
    if args.kol in ("a", "hepsi"):
        kol_a(args)
    if args.kol in ("b", "hepsi"):
        kol_b(args)
    if args.kol in ("c", "hepsi"):
        kol_c(args)
    if args.kol in ("d", "hepsi"):
        kol_d(args)
    if args.kol == "e":
        kol_e(args)
    yaz(f"koşum bitişi: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
