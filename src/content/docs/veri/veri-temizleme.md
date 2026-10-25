---
title: "Veri Temizleme: Kaliteli Veri, İyi Model"
description: Ham veriyi eğitime hazır hale getirmenin adımları — normalizasyon, tekrar temizleme, kalite filtreleme, kişisel veri maskeleme ve uçtan uca mini bir temizlik betiği.
dogrulama: 2026-10-15
---

Eğitim sürecinde harcadığın zamanın çoğu burada geçer ve buna değer: **model, verisinin aynasıdır.** Kirli veriyle eğitilen model kirli öğrenir. Bu sayfa, ham veriyi eğitime hazır hale getiren tipik bir boru hattını (pipeline) adım adım anlatır.

:::note
Veri **nereden** bulunur sorusunun cevabı ayrı bir sayfada: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/). Bu sayfa ise eline geçen veriyle **ne yapacağını** anlatır.
:::

## Temizlik Boru Hattı

```text
Ham veri
   ↓ 1. Normalizasyon        (encoding, boşluk, HTML kalıntıları)
   ↓ 2. Tekrar temizleme     (birebir + yakın tekrarlar)
   ↓ 3. Kalite filtreleme    (uzunluk, anlamsız içerik, spam)
   ↓ 4. Kişisel veri (PII)   (isim, e-posta, telefon maskeleme)
   ↓ 5. Format dönüşümü      (JSONL / sohbet formatı)
   ↓ 6. Gözle doğrulama      (100 örnek elle okunur — atlanmaz!)
Eğitime hazır veri
```

## 1. Normalizasyon

Aynı metnin farklı teknik biçimlerini tek biçime indirgemek:

- **Unicode normalizasyonu (NFC):** Görselde aynı, baytlarda farklı karakterleri birleştirir. `é` tek karakter mi, `e` + birleşik aksan mı?
- **Boşluk düzeltmeleri:** Çoklu boşluklar, satır sonu karmaşası, baştaki/sondaki boşluklar.
- **HTML kalıntıları:** `<p>`, `&amp;`, `&#39;` gibi parçaların temizlenmesi (web'den gelen veride çok olur).
- **Encoding hataları:** `Ä°stanbul` gibi bozuk görünen ("mojibake") metinler; kaynağı yanlış encoding'le okumaktan gelir.

:::caution[Türkçe'ye özgü dikkat]
Türkçe'de `I→ı` ve `İ→i` dönüşümleri, büyük/küçük harf işlemlerinde beklenmedik sonuçlar üretir (`"İSTANBUL".lower()` bazı dillerde `"i̇stanbul"` olur). Normalizasyon betiğinde Türkçe kuralları test etmeyi unutma.
:::

```python title="normalize.py"
import re
import unicodedata

def normalize_et(metin: str) -> str:
    metin = unicodedata.normalize("NFC", metin)      # unicode birleştirme
    metin = re.sub(r"<[^>]+>", " ", metin)           # HTML etiketlerini sök
    metin = metin.replace("&nbsp;", " ").replace("&#39;", "'")
    metin = re.sub(r"[ \t]+", " ", metin)            # çoklu boşlukları sadeleştir
    metin = re.sub(r"\n{3,}", "\n\n", metin)         # 3+ boş satırı 2'ye indir
    return metin.strip()
```

## 2. Tekrar Temizleme (Deduplication)

:::note[Tekrarlı veri neden bu kadar zararlı?]
Üç bulgu yön verir. (1) Tekrar ve yakın-tekrar temizliği, modelin eğitim verisini birebir ezberlemesini azaltır ve eğitimi iyileştirir ("Deduplicating Training Data Makes Language Models Better", arXiv:2107.06499). (2) Bu, yeni bir moda değil, klasik bir uygulamadır: C4 derlemi kurulurken üç cümlelik tekrar eden spanların fazlaları atılmıştı (T5 makalesi, arXiv:1910.10683). (3) Tekrar sınırsız da değildir: veri kısıtlıyken aynı veriyi birkaç tur (ölçümlere göre ~4 epoch'a kadar) tekrarlamak benzersiz veriyle eğitime yakın kayıp verir; ötesinde getiri hızla düşer — tekrar, eksik verinin telafisi değildir ("Scaling Data-Constrained Language Models", arXiv:2305.16264).
:::

Tekrarlı veri, modeli **ezbere** iter: aynı cümleyi 50 kez gören model onu "her yerde geçerli" sanır. İki tür tekrar var:

| Tür | Nedir | Yöntem |
| --- | --- | --- |
| Birebir tekrar | Aynı metin birebir kopya | Hash karşılaştırması (aşağıdaki kod) |
| Yakın tekrar | %90+ benzer, ufak değişiklikli | MinHash / LSH (ileri seviye; `datasets` veya `datasketch` kütüphanesi) |

```python title="tekrar_temizle.py"
import hashlib

def metin_hash(metin: str) -> str:
    return hashlib.sha256(metin.strip().encode("utf-8")).hexdigest()

gorulen = set()
tekil = []
for ornek in veriler:                      # veriler: sözlük listesi
    h = metin_hash(ornek["text"])
    if h not in gorulen:
        gorulen.add(h)
        tekil.append(ornek)

print(f"Önce: {len(veriler)} | Sonra: {len(tekil)}")
```

Birebir tekrarı hallettin; sıra **yakın tekrarda** — ufak değişikliklerle kopyalanmış örneklerde. MinHash imzası + LSH indeksi, her örneği tüm veriyle tek tek karşılaştırmadan benzer çiftleri yüksek olasılıkla yakalar. Metnin tamamı yerine 5 kelimelik kayan pencerelerden (shingle) imza çıkarırız:

```python title="yakin_tekrar.py"
from datasketch import MinHash, MinHashLSH

def besli_shingle(metin: str) -> set[str]:
    """Metni 5 kelimelik kayan pencerelere böl (küçük değişime dayanıklı çekirdek)."""
    kelimeler = metin.split()            # metin, 1. bölümdeki normalizasyondan geçmiş olmalı
    return {" ".join(kelimeler[i : i + 5]) for i in range(len(kelimeler) - 4)}

# threshold=0.8: yaklaşık Jaccard benzerliği %80 ve üzeri "tekrar" sayılır
lsh = MinHashLSH(threshold=0.8, num_perm=128)
tekil_yakin = []
yakin_tekrar = 0

for i, ornek in enumerate(tekil):        # tekil: birebir tekrarı silinmiş liste
    shinglelar = besli_shingle(ornek["text"])
    if len(shinglelar) < 2:
        tekil_yakin.append(ornek)        # çok kısa metinde imza anlamsız, doğrudan geçir
        continue
    mh = MinHash(num_perm=128)
    for s in shinglelar:
        mh.update(s.encode("utf-8"))
    if lsh.query(mh):                    # eşiği aşan bir eşi zaten eklendiyse: yakın tekrar
        yakin_tekrar += 1
        continue
    lsh.insert(f"o{i}", mh)
    tekil_yakin.append(ornek)

print(f"Yakın tekrar olarak elenen: {yakin_tekrar} | Kalan: {len(tekil_yakin)}")
```

:::note[Eşik ve olasılık]
`num_perm=128` ile dengeli bir hassasiyet elde edersin (num_perm büyüdükçe tahmin isabetlenir, bellek artar); datasketch 2.0.0 ile doğrulanmış bu değerler 2026 itibarıyla günceldir. LSH sorgusu olasılıksaldır: eşik civarındaki nadir çiftleri kaçırabilir. Karar kritikse şüpheli çiftlerin kesin benzerliğini `mh1.jaccard(mh2)` ile doğrula. Eşiği verine göre kalibre et: yalnızca bariz kopyaları istiyorsan `threshold=0.9`'a çıkar; 0,80 başlangıç için dengelidir.
:::

:::tip
SFT verisinde tekrar kontrolünü **soru bazında** da yap: aynı soruya farklı cevaplar varsa model çelişkili öğrenir. "Aynı soru → tek cevap" kuralını benimse.
:::

## 3. Kalite Filtreleme

Kurallarla başla; kurallar yetmediğinde gözle devam et:

- **Uzunluk:** Çok kısa (<10 karakter) veya saçma derecede uzun örnekleri ele.
- **Kelime çeşitliliği:** Aynı kelimenin tekrar oranı yüksekse (spam/bozuk toplama) ele.
- **Boilerplate:** "Bu site çerez kullanır", "Yorumlar kapalı" gibi her sayfada tekrar eden kalıplar — web verisinin gizli hastalığı.
- **Dil kontrolü:** Verinin gerçekten Türkçe olup olmadığı (karışık setlerde önemli).

```python title="filtrele.py"
def kaliteli_mi(ornek: dict) -> bool:
    metin = ornek["text"]
    if len(metin) < 20 or len(metin) > 8000:
        return False
    kelimeler = metin.split()
    if len(kelimeler) < 5:
        return False
    benzersiz = len(set(kelimeler)) / len(kelimeler)
    if benzersiz < 0.3:                 # kelimelerin %70'i aynıysa şüpheli
        return False
    return True

temiz = [o for o in tekil if kaliteli_mi(o)]
```

:::caution[Altın kural]
Filtre istatistiklerine bak: **%1 bile elenmeli.** "%80'ini eledim" görüyorsan filtre çok agresif, "%0" görüyorsan filtre hiç çalışmıyor. Ardından mutlaka 100 örneği **gözle oku** — otomatik kontrol hiçbir zaman tek başına yeterli değildir.
:::

## 4. Kişisel Veri (PII) Maskeleme

Eğitim verisinde isim, e-posta, telefon, TC kimlik numarası gibi kişisel veri varsa **KVKK/GDPR kapsamına** girersin. Veriyi kullanmadan önce tespit edip maskele (ör. `[E-POSTA]`).

```python title="pii_maskele.py"
import re

KALIPLAR = {
    "[E-POSTA]": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "[TELEFON]": r"(?:\+90|0)?\s?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}",
    "[TCKN]":    r"\b[1-9]\d{10}\b",
    "[URL]":     r"https?://\S+",
}

def maska(metin: str) -> str:
    for etiket, kalip in KALIPLAR.items():
        metin = re.sub(kalip, etiket, metin)
    return metin
```

:::danger
Basit regex'ler yalnızca **ilk savunma hattıdır.** Gerçek isimler ve adresler regex'e takılmaz. Hassas veriyle çalışıyorsan daha kapsamlı araçlar (ör. `presidio` tarzı PII tespit kütüphaneleri) kullan veya mümkünse hassas alanları veri setinden tamamen çıkar.
:::

## 5. SFT Verisine Özel Kontroller

Talimat (instruction) verisi hazırlıyorsan ek olarak şunlara bak:

1. **Cevap doğru mu?** Yanlış cevaplı örnek, modele yanlışı öğretir. Örnekleme yaparak elle kontrol et.
2. **Talimat-cevap tutarlı mı?** Soru "fiyat" soruyor, cevap "kargo" anlatıyorsa örnek çöp.
3. **Çeşitlilik** var mı, yoksa 500 örnek 5 kalıbın kopyası mı?
4. **Sistem istemi (system prompt)** her örnekte tutarlı mı?
5. **Uzunluk dağılımı** doğal mı (hepsi 3 satır ya da hepsi 1 paragraf mı)?

Kalite-miktar dengesini [Veri Türleri](/veri/veri-turleri/) sayfasında LIMA bulgusuyla anlatmıştık: 1.000 seçkin örnek, 100.000 gürültülü örnekten iyi olabilir.

## Sızıntı Kontrolü: Eğitim ve Test Örtüşmesi

**Kontaminasyon (sızıntı)**, test veya benchmark örneklerinin — ya da yakın kopyalarının — eğitim verisinde bulunmasıdır. Sonuç: model cevabı "biliyordur" çünkü ezberlemiştir; [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) ve [Benchmark'lar](/degerlendirme/benchmarklar/) üzerinden gördüğün skorlar şişer ve model gerçekte olduğundan iyi görünür. Sızıntı iki kapıdan girer: web'den topladığın veriye benchmark soruları kazara karışmış olabilir; kendi setinde ise sentetik üretim, test setindeki bir sorunun benzerini eğitim tarafına yazmış olabilir.

Pratik kontrol: test örneklerini 8-13 kelimelik n-gram'lara böl ve bu n-gram'ların eğitim setinde geçip geçmediğine bak. 8'den kısa n-gram'lar yaygın kalıplar yüzünden sahte eşleşme üretir; bu yüzden alt sınırı 8'in altına indirme. Örtüşen test örneklerini ayıkla — test setin küçükse, örneği eğitimden silmek yerine testten çıkarmak daha pratiktir.

```python title="sizinti_kontrol.py"
def ngram_ornekleri(metin: str, n: int) -> set[str]:
    kelimeler = metin.split()
    return {" ".join(kelimeler[i : i + n]) for i in range(len(kelimeler) - n + 1)}

def egitim_ngramlari(egitim_seti, n: int = 13) -> set[str]:
    hepsi: set[str] = set()
    for ornek in egitim_seti:
        hepsi |= ngram_ornekleri(ornek["soru"], n)
        hepsi |= ngram_ornekleri(ornek["cevap"], n)    # iki alanı da tara
    return hepsi

EGITIM_NGRAM = egitim_ngramlari(egitim_seti, n=13)

temiz_test = []
for ornek in test_seti:
    if ngram_ornekleri(ornek["soru"], 13) & EGITIM_NGRAM:
        continue          # eğitimle örtüşüyor: testten çıkar
    temiz_test.append(ornek)

print(f"Örtüşme nedeniyle çıkarılan test örneği: {len(test_seti) - len(temiz_test)}")
```

:::caution[Sıralama önemli]
Önce tekrar temizle, **sonra** eğitim/doğrulama/test bölmesini yap; aynı örneğin iki kopyası biri eğitime biri teste düşerse sızıntı kendiliğinden oluşur. Bölmeden sonra da bu betiği çalıştırıp örtüşmeyi tara — "böldüm, bitti" demek yeterli değildir.
:::

## Dil Tespiti ve Karışık Dil

Web kazımalarında ve çeviri kaynaklı setlerde bir örnek bile karışık dillerden oluşabilir: Türkçe sayfanın ortasında İngilizce menü kalıntısı kalır ya da makine çevirisi "çeviri kokan" cümleler üretir. Karışık dil, kalite filtresinin gözünden kaçar ama modelin dil dağılımını bozar. İki pratik araç var: `langdetect` (kurulumu kolay, model dosyası indirmez) ve fastText'in `lid.176` modeli (176 dil destekler; küçük sürümü `lid.176.ftz` 917 KB'dır — daha isabetli, ayrı indirme gerektirir).

:::note[Kısa metin uyarısı]
Dil tespit araçları kısa metinlerde yanılır: "Evet.", "2026" gibi girdilerde sonuca güven olmaz. Başlık ve tablo hücresi gibi kısa parçaları tek başına tespit ettirme; ana metne bitiştir ya da bu parçaları tespit dışı bırak.
:::

Pratik eşik: örneği cümlelere böl, cümle bazında dil tespiti yap ve **Türkçe çıkan cümle oranı ~%90'ın altındaki örnekleri işaretle**; işaretlileri gözle incele. Bu oran bir başlangıç eşiğidir — kendi verinden birkaç on örnek okuyup kalibre et.

```python title="dil_tespiti.py"
import re
from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0      # tekrarlanabilirlik için şart: aynı metin, aynı sonuç

def cumlelere_bol(metin: str) -> list[str]:
    parcalar = re.split(r"[.!?]+", metin)
    return [p.strip() for p in parcalar if len(p.strip()) >= 30]   # çok kısa cümlede tespit güvenilmez

def turkce_orani(metin: str) -> float:
    cumleler = cumlelere_bol(metin)
    if not cumleler:
        return 1.0            # ölçülecek kadar uzun cümle yoksa dokunma
    turkce = 0
    for cumle in cumleler:
        try:
            if detect(cumle) == "tr":
                turkce += 1
        except LangDetectException:
            pass              # rakam/noktalama ağırlıklı cümleler tespit edilemez
    return turkce / len(cumleler)

supheli = [o for o in veriler if turkce_orani(o["text"]) < 0.90]
print(f"Gözle incelenecek karışık dil şüphelisi: {len(supheli)}")
```

Çeviri kokusu ayrı bir sinyaldir: makine çevirisi, İngilizce söz diziminin birebir kopyasını, aşırı düz kalıpları ve terim tutarsızlıklarını bırakır; web kazımalarında "Powered by ... çeviri" gibi araç imzaları da kalabilir. Bunları kural olarak filtreleyemiyorsan en azından işaretleyip örneklemle gözle oku — cilalı ama doğal olmayan çeviri dili, modele doğal olmayan üslup öğretir.

## Uçtan Uca Mini Boru Hattı

Parçaları birleştirelim — JSONL okuyup temizleyen, tekrarları atan, filtreleyen ve özet basan tek dosyalık betik:

```python title="temizlik_pipeline.py"
import json, hashlib, re, unicodedata

GIRDI, CIKTI = "ham_veri.jsonl", "temiz_veri.jsonl"

def normalize(metin):
    metin = unicodedata.normalize("NFC", metin)
    metin = re.sub(r"<[^>]+>", " ", metin)
    metin = re.sub(r"\s+", " ", metin)
    return metin.strip()

def maskele(metin):
    metin = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[E-POSTA]", metin)
    metin = re.sub(r"(?:\+90|0)?\s?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}", "[TELEFON]", metin)
    return metin

sayac = {"okunan": 0, "tekrar": 0, "filtre": 0, "yazilan": 0}
gorulen = set()

with open(GIRDI, encoding="utf-8") as f_in, open(CIKTI, "w", encoding="utf-8") as f_out:
    for satir in f_in:
        sayac["okunan"] += 1
        ornek = json.loads(satir)
        for mesaj in ornek["messages"]:
            mesaj["content"] = maskele(normalize(mesaj["content"]))
        anahtar = hashlib.sha256(
            json.dumps(ornek, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        if anahtar in gorulen:
            sayac["tekrar"] += 1
            continue
        gorulen.add(anahtar)
        toplam_uzunluk = sum(len(m["content"]) for m in ornek["messages"])
        if toplam_uzunluk < 30 or toplam_uzunluk > 12000:
            sayac["filtre"] += 1
            continue
        f_out.write(json.dumps(ornek, ensure_ascii=False) + "\n")
        sayac["yazilan"] += 1

print(sayac)
```

Çıktıyı oku: `okunan` ile `yazilan` arasındaki farkın **nedenini** açıklayabiliyor musun? Açıklayamadığın bir düşüş varsa filtrelerden biri fazla agresif demektir.

## Temizlik Karnesi: Ölçmeden Bitti Deme

Uçtan uca betikteki `sayac` sözlüğü, işin çekirdeğini tutar: `okunan`, `tekrar`, `filtre`, `yazilan`. Ama "bitti" demek için bu sayıları **karneye** dökmelisin. Eğitim raporuna şu tabloyu doldurup koy — üç ay sonra "bu veri nereden geldi, ne eledim?" sorusunun cevabı arşivde olur:

| Aşama | Örnek sayısı | Neden (kısa not) |
| --- | --- | --- |
| Okunan (ham) | — | ham dosyadaki satır sayısı |
| Birebir tekrar (elenen) | — | hash eşleşmesi |
| Yakın tekrar (elenen) | — | MinHash/LSH, eşik 0,80 |
| Kalite filtresi (elenen) | — | kural bazında kırılımı da yaz |
| PII maskelenen örnek | — | maskeleme silmez; bu satırda düşüş bekleme |
| Eğitim seti | — | |
| Doğrulama + test seti | — | eğitimle örtüşme taraması yapıldı |

Tabloyu elle doldur ("—" yerine kendi sayıların); istersen her satıra bir üst satıra oranını da ekle. Karnedeki kritik soru şudur: **`okunan` ile eğitime giren sayı arasındaki farkı satır satır açıklayabiliyor musun?** Açıklayamadığın her fark, görünmez bir filtrenin — ya da görünmez bir hatanın — işareti olabilir.

## Temizlik Kontrol Listesi

- [ ] Encoding ve Türkçe karakterler doğru görünüyor
- [ ] Birebir tekrarlar silindi
- [ ] Uzunluk ve kelime çeşitliliği filtreleri uygulandı
- [ ] Kişisel veriler maskelendi (veya çıkarıldı)
- [ ] Format, aracın beklediği şemayla uyumlu ([Veri Formatları](/veri/veri-formatlari/))
- [ ] Eğitim/doğrulama ayrımı yapıldı, sızıntı yok
- [ ] 100 örnek gözle okundu ve not alındı

:::tip[Son adım]
Temizlik bittiğinde tek bir "neden" sorusunu yanıtlayabilmelisin: **"Bu veri, modelime ne öğretmek için var?"** Cevap netse eğitime hazır; bulanıksa [Kendi Verini Oluştur](/veri/kendi-verini-olustur/) sayfasına dönüp kapsamı netleştir.
:::

## Kaynaklar ve İleri Okuma

- [Deduplicating Training Data Makes Language Models Better (arXiv:2107.06499)](https://arxiv.org/abs/2107.06499) — tekrar ve yakın tekrar temizliğinin ezberi azaltıp eğitimi iyileştirdiğini gösteren temel çalışma (Lee vd., ACL 2022).
- [Exploring the Limits of Transfer Learning (T5/C4, arXiv:1910.10683)](https://arxiv.org/abs/1910.10683) — C4 derleminin üç cümlelik tekrar eden spanları nasıl temizlediğini anlatan klasik kaynak (Raffel vd., 2019).
- [Scaling Data-Constrained Language Models (arXiv:2305.16264)](https://arxiv.org/abs/2305.16264) — veri kısıtlıyken tekrarın sınırını ölçen çalışma: ~4 epoch'a kadar tekrar zararsız, ötesinde getiri düşüyor (Muennighoff vd., 2023).
- [datasketch (GitHub)](https://github.com/ekzhu/datasketch) — MinHash, LSH ve benzeri olasılıksal veri yapıları için Python kütüphanesi; bu sayfadaki örnek, 2026 itibarıyla 2.0.0 sürümüyle uyumludur.
- [Microsoft Presidio (GitHub)](https://github.com/data-privacy-stack/presidio) — PII tespiti ve maskeleme çerçevesi; 2026 itibarıyla data-privacy-stack topluluğu sürdürüyor (eski `microsoft/presidio` adresi buraya yönlenir).
