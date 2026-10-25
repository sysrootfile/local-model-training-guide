---
title: "Veri Nereden Bulunur? (Türkçe Kaynaklar Dahil)"
description: Hazır veri setleri, ham metin kaynakları ve doğrulanmış Türkçe veri kümeleri rehberi — büyük ön eğitim derlemleri, kazıma hukuku ve sentetik veri notlarıyla; nereden indirilir, nasıl kullanılır, nelere dikkat edilir.
dogrulama: 2026-10-15
---

Veri, model eğitiminin yakıtıdır. Bu sayfada üç farklı kaynak yolunu ve özellikle **Türkçe veri** bulma stratejilerini göreceksin.

:::note
Veri çok geniş bir konu: türleri için [Veri Türleri](/veri/veri-turleri/), biçimlendirme için [Veri Formatları](/veri/veri-formatlari/), temizlik için [Veri Temizleme](/veri/veri-temizleme/) sayfalarına da bak.
:::

## Üç Kaynak Yolu

```text
A) Hazır veri setleri     → Hugging Face, Kaggle ... (en hızlı başlangıç)
B) Ham kaynaklardan üretme → Wikipedia, Common Crawl, kendi kazıma işin ...
C) Kendi verin            → SSS'ler, destek kayıtları, ürün dokümanları ...
```

Çoğu proje için doğru strateji: **A ile başla, C ile bitir.** Hazır veriyle döngüyü öğren, sonra kendi verinle özelleştir.

## A) Hazır Veri Setleri

### Hugging Face Hub

Günümüzde veri setlerinin bir numaralı adresi [Hugging Face Datasets](https://huggingface.co/datasets). On binlerce set; üstelik tarayıcıdan tek tek satırları inceleyebileceğin bir veri görüntüleyici (data viewer) ve tek satır kodla indirme var.

```python title="hf_veri_indir.py"
from datasets import load_dataset

# Tek satırla indir
ds = load_dataset("kullanici/veri-seti-adi", split="train")
print(ds)             # boyut ve alanları gör
print(ds[0])          # ilk örneğe göz at

# Büyük setlerde: diske indirmeden, akan (streaming) mod
ds_akis = load_dataset("kullanici/buyuk-veri-seti", split="train", streaming=True)
for ornek in ds_akis.take(3):
    print(ornek)
```

**Arama ipuçları:** HF'de arama yaparken sol panelden dil filtresini **Turkish (tr)** seç; sıralamayı "Most downloads" yap. Setin sayfasında önce **boyut ve lisans**, sonra veri görüntüleyiciden **örnek kalitesi** kontrol et.

:::tip
Kalite kontrolü 30 saniyede: Veri seti sayfasındaki veri görüntüleyicide 10-20 satır oku. Yazım hataları, boş alanlar veya ilgisiz örnekler çok mu? O set büyük ihtimalle ekstra temizlik gerektirir.
:::

### Kaggle

[Kaggle Datasets](https://www.kaggle.com/datasets) özellikle tablo verisi ve yarışma setlerinde güçlü. Kaggle notebook'larında veriye `pip install kagglehub` + `kagglehub.dataset_download("kullanici/set-adi")` ile erişebilirsin. Ayrıca haftalık ücretsiz GPU kotasıyla eğitim denemeleri de yapabilirsin ([bulut seçenekleri](/donanim/bulut-secenekleri/)).

## Türkçe Veri Setleri

Türkçe açık veri, İngilizce'ye göre belirgin şekilde daha az — bu yüzden Türkçe çalışanlar için bu bölüm altın değerinde. 2026 itibarıyla öne çıkan setler:

| Veri seti | Tür | Ölçek / Not | Ne için? |
| --- | --- | --- | --- |
| `atasoglu/turkish-instruction-datasets` | HF koleksiyonu | Talimat setleri bir arada (birçok set) | İnce ayar (SFT) için ilk durak |
| `ogulcanaydogan/Turkish-LLM` (HF + GitHub) | Talimat + eğitim verisi | ~173K-242K örnek; Qwen2.5 üzerine QLoRA ile kullanıldı | Türkçe talimat ayarı — gerçek proje örneği |
| `HuggingFaceFW/fineweb-2` (tr) | Web korpusu | ~95,1M belge / ~41,9B kelime / 125,53 GB disk (HF kartı dil tablosundan doğrulandı) | Devam ön eğitimi, ön eğitim |
| Turkish Data Depository (TDD) | Akademik korpus | OSCAR + mC4 Türkçe, ~240 GB / 82M döküman | Ön eğitim, dil modelleme araştırması |
| `hasankursun/turkish-corpus-100b` | Web + akıl yürütme karışımı | 100B token hedefli | Devam ön eğitimi |
| Holmeister Türkçe değerlendirme setleri | Değerlendirme | Çok görevli, çok istemli (17 set) | Eval — eğitim için değil! |
| `kesimeg/awesome-turkish-language-models` | Katalog (GitHub) | Türkçe model + veri + makale listesi | Keşif ve güncel takip |

FineWeb-2'nin Türkçe bölümünü yalnızca akış modunda çekmek istersen:

```python title="fineweb_tr.py"
from datasets import load_dataset

# Not: dil yapılandırma adı ("tur_Latn") sürümle değişebilir — HF sayfasından kontrol et
ds = load_dataset(
    "HuggingFaceFW/fineweb-2", "tur_Latn",
    split="train", streaming=True,
)
for ornek in ds.take(2):
    print(ornek["text"][:300])
```

:::caution
Türkçe web korpusları (OSCAR, mC4, fineweb gibi) ham web metni içerir: bozuk cümleler, spam, reklam metni bol olabilir. Doğrudan kullanmadan önce filtreleme şart: [Veri Temizleme](/veri/veri-temizleme/).
:::

### Doğrulanmış Türkçe veri kümeleri (son doğrulama: Ekim 2026)

Aşağıdaki her satır HF veri kümesi sayfasından ve veri görüntüleyiciden tek tek doğrulandı: satır sayıları gerçek dosyalardan, lisanslar veri kartındaki `license` alanından okundu. "Kartta belirtilmemiş" yazanlar bilinçli olarak o şekilde bırakıldı — doğrulanmamış lisans varsayma.

| Veri kümesi | Boyut / satır (2026 itibarıyla) | Lisans | Görev türü | HF sayfası |
| --- | --- | --- | --- | --- |
| `TFLai/Turkish-Alpaca` | 51.914 satır | Apache-2.0 | Talimat (SFT) | [HF](https://huggingface.co/datasets/TFLai/Turkish-Alpaca) |
| `merve/turkish_instructions` | 51.563 satır | Apache-2.0 | Talimat (SFT) | [HF](https://huggingface.co/datasets/merve/turkish_instructions) |
| `AlicanKiraz0/Turkish-SFT-Dataset-v1.0` | 5.579 satır | MIT | Talimat (SFT) | [HF](https://huggingface.co/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0) |
| `OpenAssistant/oasst1` (Türkçe kısmı) | 37 mesaj (tüm derlem 88.838 satır) | Apache-2.0 | Diyalog / tercih verisi | [HF](https://huggingface.co/datasets/OpenAssistant/oasst1) |
| `winvoker/turkish-sentiment-analysis-dataset` | 489.644 örnek (440.679 + 48.965) | CC-BY-SA-4.0 | Duygu analizi | [HF](https://huggingface.co/datasets/winvoker/turkish-sentiment-analysis-dataset) |
| `savasy/ttc4900` | 4.900 örnek / 7 haber kategorisi | Kartta belirtilmemiş | Metin sınıflandırma | [HF](https://huggingface.co/datasets/savasy/ttc4900) |
| `reciTAL/mlsum` (tr) | 273.617 satır (249.277 + 11.565 + 12.775) | Yalnızca ticari olmayan araştırma | Haber özetleme | [HF](https://huggingface.co/datasets/reciTAL/mlsum) |
| `facebook/xnli` (tr) | 400.202 satır (392.702 + 2.490 + 5.010) | Kartta belirtilmemiş | NLI (değerlendirme odaklı) | [HF](https://huggingface.co/datasets/facebook/xnli) |
| `GoktugD/turkish-nli-constructed-1.5m` | 1.500.000 çift (sentetik üretim) | CC0-1.0 | NLI | [HF](https://huggingface.co/datasets/GoktugD/turkish-nli-constructed-1.5m) |
| `hcsolakoglu/turkish-wikipedia-qa-4-million` | 449.844 satır (~4M soru-cevap; model üretimi) | CC-BY-NC-SA-4.0 | Soru-cevap | [HF](https://huggingface.co/datasets/hcsolakoglu/turkish-wikipedia-qa-4-million) |
| `tascib/turkish-llm-dataset` | 100M-1B token (HF boyut etiketi) | CC-BY-SA-4.0 | Ön eğitim / devam eğitimi | [HF](https://huggingface.co/datasets/tascib/turkish-llm-dataset) |

:::note
`oasst1` 35 dil içerdiğini söyler ama İngilizce ağırlıklıdır: Türkçe mesaj sayısı tüm derlemde yalnızca 37 (Ekim 2026, veri görüntüleyici filtresi). Türkçe hizalama için tek başına yetmez — İngilizce tercih verisiyle karıştır ve Türkçe değerlendirme setiyle ölç: [DPO ve RLHF](/llm/dpo-rlhf/).
:::

:::caution
Lisans sütununda "kartta belirtilmemiş" yazan setleri (`savasy/ttc4900`, `facebook/xnli`) ticari bir üründe kullanmadan önce kaynağına sor. `mlsum` yalnızca ticari olmayan araştırmaya açık; Türkçe Wikipedia QA seti CC-BY-NC-SA — ikisi de ticari kullanıma kapalı.
:::

## Büyük Ön Eğitim Derlemleri (Türkçe)

Ön eğitim ölçeğinde veri arıyorsan üç büyük seçenek var; karar neredeyse tamamen lisans ve erişim koşullarına bakıyor (ölçekler 2026 itibarıyla HF veri kartlarından, son doğrulama: Ekim 2026):

| Derlem (yapılandırma) | Ölçek (2026 itibarıyla) | Lisans / erişim | Ne zaman tercih edilir? |
| --- | --- | --- | --- |
| FineWeb-2 (`tur_Latn`) | 95.129.129 belge; 41.933.799.420 kelime; disk 125,53 GB (UTF-8 284,52 GB) | ODC-By — atıf zorunlu | Filtrelenmiş, tek boru hattından geçmiş metinle devam ön eğitimi yapacaksan: bugünün en dengeli başlangıcı. |
| CulturaX (`tr`) | 94.207.460 belge; 64.292.787.164 token | mC4 ve OSCAR lisanslarına tabi (mC4 tarafı ODC-By) | mC4 + OSCAR birleşiminden temizlenmiş, kaynak çeşitliliği yüksek derlem istiyorsan — ama iki kaynağın koşullarını ayrı ayrı incelemen gerekir. |
| OSCAR-2301 | Gated: yalnızca manuel onaylı erişim; kullanım hakları netleşene kadar **geçici olarak askıda** (Ekim 2026) | Ham veri için telif iddiası yok; meta veri ve açıklamalar CC0-1.0; indirme için ülke mevzuatına uygunluk beyanı ister | Hukuki durum netleşene kadar tercih etme; aynı ihtiyacı FineWeb-2 ve CulturaX rahatça karşılar. |

## B) Ham Kaynaklardan Veri Üretme

| Kaynak | İçerik | Tipik kullanım |
| --- | --- | --- |
| Wikipedia dumps (trwiki) | Ansiklopedi metni, CC BY-SA lisanslı | Devam ön eğitimi, bilgi tabanı |
| Common Crawl | Tüm web'in zaman zaman arşivleri | Ön eğitim (ciddi filtreleme gerekir) |
| OPUS | Paralel çeviri korpusları | Çeviri/çok dilli eğitim |
| Tatoeba | Örnek cümle çiftleri | Küçük ölçekli dil deneyleri |
| The Stack | Açık lisanslı kaynak kodu | Kod modelleri |
| Açık devlet verileri (data.gov.tr gibi) | Resmî belgeler, istatistikler | Alan modeli (hukuk, kamu) |

:::danger[Yasal ve etik sınırlar]
- **Telif hakkı:** Kitaplar, haber metinleri ve kapalı platform içerikleri izinsiz kullanılamaz. Açık lisans (CC, MIT, Apache) ve kamu malı kaynakları tercih et.
- **Kişisel veri:** Metinlerde isim, TC kimlik, adres, sağlık bilgisi gibi kişisel veriler varsa **KVKK/GDPR** kapsamına girersin; temizlemeden kullanma ([temizleme adımları](/veri/veri-temizleme/)).
- **Platform kuralları:** Bir siteyi kazımadan (scraping) önce kullanım şartlarına ve `robots.txt` kurallarına bak.
- **En güvenli yol:** Kendi ürettiğin veri, açık lisanslı setler ve kamu malı kaynaklar.
:::

## Resmî ve Kamusal Kaynakların Durumu

Resmî kaynaklar "açık" görünse de erişim modelleri birbirinden çok farklı. 2026 itibarıyla durum:

| Kaynak | Durum | Erişim ve koşullar |
| --- | --- | --- |
| Türkçe Wikipedia dump'ları (trwiki) | Açık ve düzenli: aylık dump'lar yayınlanıyor (Ekim 2026'daki güncel sürüm: 20261001) | [dumps.wikimedia.org/trwiki](https://dumps.wikimedia.org/trwiki/) — içerik CC BY-SA; yayınlarken atıf şart |
| TTC4900 (metin sınıflandırma klasiği) | HF'de mevcut: `savasy/ttc4900` (4.900 örnek, 7 kategori); kartta lisans yok | [HF sayfası](https://huggingface.co/datasets/savasy/ttc4900) — ticari kullanımdan önce lisansı kaynağından teyit et |
| TBMM tutanakları | Resmî web arayüzü var (dönem ve yasama yılı bazında, "ham metin" linkleriyle); resmî toplu indirme API'si yok | [Tutanak Metinleri](https://www.tbmm.gov.tr/Tutanaklar/TutanakMetinleri) — otomatik kazımadan önce kullanım koşullarını incele |
| YÖK Ulusal Tez Merkezi | Toplu indirme yok; üyelikle arama, tam metin yalnızca izinli tezlerde | [tez.yok.gov.tr](https://tez.yok.gov.tr/UlusalTezMerkezi) — ölçülü, kaynak gösterimli erişim; toplu kazıma yerine resmî talep yollarını dene |

## Kazıma ve Hukuk: Nelere Dikkat Etmeli?

Kazıma teknik olarak kolay, hukuken dikkat isteyen bir iştir. Türkiye'de üç katman birlikte değerlendirilir:

:::caution
- **KVKK (kişisel veri):** İsim, TC kimlik numarası, telefon, e-posta, adres, konum ve sağlık bilgisi kişisel veridir. Amaçla sınırlılık ve veri minimizasyonu gereği yalnızca ihtiyacın olan alanı topla; eğitim öncesinde tanımlayıcıları maskele ([Veri Temizleme](/veri/veri-temizleme/)). Sağlık, inanç, biyometri gibi özel nitelikli verilerde ölçüt daha sıkıdır.
- **robots.txt ve kullanım şartları:** Kazımadan önce sitenin `robots.txt` dosyasına ve kullanım koşullarına bak; yasaklı yolları tara, istek hızını siteyi yormayacak şekilde sınırla ve giriş/üyelik gerektiren alanlara hiç dokunma.
- **Lisans uyumu:** CC-BY-NC (ör. `mlsum`, Türkçe Wikipedia QA seti) ticari kullanıma kapalıdır; ODC-By (ör. FineWeb-2, mC4) atıf ister; CC-BY-SA (ör. Wikipedia, `winvoker` duygu seti) türev çalışmalara aynı lisansı şart koşar; MIT / Apache-2.0 ticari kullanıma açıktır.
- **Bu bölüm genel bilgilendirmedir, hukuki tavsiye değildir.** Ürüne dönüşecek bir kullanım planlıyorsan bir hukuk uzmanına danış — mevzuat ve içtihat zamanla değişir ([KVKK Kurumu](https://www.kvkk.gov.tr/)).
:::

## C) Kendi Verini Hazırlama

En değerli veri genelde elindekidir: destek e-postaları, SSS sayfaları, ürün dokümanları, iç yazışmalar... Bunları modele öğretmek için yapılandırılmış soru-cevap formatına çevirmen gerekir. Adım adım tarif: [Kendi Verini Oluştur](/veri/kendi-verini-olustur/).

## Sentetik Veri: Talimatı Modelden Üretmek

Sentetik veri, bir modelin ürettiği eğitim örneğidir. İki yaygın araç:

- **Kendinden talimat üretimi (Magpie):** Hizalı bir sohbet modeline yalnızca şablonun kullanıcı kısmına kadar olan bölümü verirsin; model kendi dağılımından talimatı ve yanıtı üretir — insan yazımı talimat olmadan kaliteli hizalama verisi ([Xu vd., 2024](https://arxiv.org/abs/2406.08464)).
- **Boru hattı aracı (distilabel):** Üretim, filtreleme ve yargıç-model değerlendirmesini tek boru hattında birleştirir ([GitHub](https://github.com/argilla-io/distilabel)); Argilla ekibinin başlattığı araç artık topluluk tarafından sürdürülüyor.

Sentetik veri özellikle şurada parlar: az temsil edilen alanlar (hukuk, tıp, oyun), `system` alanlı çok turlu senaryolar ve etiketli verinin pahalı olduğu görevler.

:::caution
Yalnızca sentetik veriyle döngülü eğitim **model çöküşü** (model collapse) riski taşır: model kendi ürettiği dağılımla tekrar tekrar eğitildikçe gerçek dağılımın kuyrukları silinir, çeşitlilik kuşaklar boyunca azalır (Shumailov vd., Nature 631, 755-759, 2024 — [bağlantı](https://www.nature.com/articles/s41586-024-07566-y)). Dengeli karışım: yanına mutlaka insan yazımı gerçek veri koy (yaygın başlangıç noktası yarı yarıya), tek modelin çıktısına bağımlı kalma ve üretilen veriyi filtrele. Tercih verisi tarafı için [DPO ve RLHF](/llm/dpo-rlhf/), kendi materyalini veriye çevirmek için [Kendi Verini Oluştur](/veri/kendi-verini-olustur/).
:::

## Değerlendirme Verisi Nereden Bulunur?

Eğitim + değerlendirme ayrımı kutsaldır — aynı veriyi ikisinde de kullanma. Türkçe değerlendirme için [Holmeister setleri](https://huggingface.co/collections/Holmeister/turkish-llm-multi-prompt-evaluation-datasets) (11 görev için 17 set; son doğrulama 2026-10), `atasoglu` koleksiyonundaki eval setleri ya da kendi 20-50 soruluk mini test setin (en pratik yol): [Benchmark'lar](/degerlendirme/benchmarklar/).

## Doğru Veri Kümesini Bulma Stratejisi

Arama, kalabalık bir raftan doğru kutuyu hızlıca çekme işidir — 2026 itibarıyla en verimli akış:

1. **Filtrele:** [HF Datasets](https://huggingface.co/datasets) aramasında sol panelden dili **Turkish (tr)** seç, görev kategorisini (talimat, özetleme, QA...) daralt ve sıralamayı önce **Most downloads**, sonra **Trending** yap.
2. **Veri kartını oku (5 dakika):** Lisans (ticari kullanıma açık mı, atıf şartı var mı?), boyut ve satır sayısı (veri görüntüleyiciyle tutarlı mı?), split'ler (değerlendirme seti ayrılmış mı?), dil kalitesi (karışık dil, çeviri kokusu, tekrar var mı?), kontaminasyon notu (benchmark'larla örtüşme uyarısı) ve son güncelleme tarihi (2023'te donmuş bir set güncel ihtiyacı karşılamayabilir).
3. **İndirmeden görüntüle:** `datasets-server` API'siyle ilk satırları dosyayı diske almadan çek:

```python title="on_izleme.py"
import requests

r = requests.get(
    "https://datasets-server.huggingface.co/rows",
    params={
        "dataset": "TFLai/Turkish-Alpaca",
        "config": "default",  # bazı setlerde farklıdır: veri kartındaki Configs listesine bak
        "split": "train",
        "offset": 0,
        "length": 5,
    },
    timeout=30,
)
veri = r.json()
print("Toplam satır:", veri["num_rows_total"])
for satir in veri["rows"]:
    print(satir["row"])
```

4. **Dev derlemlerde akış modu:** `streaming=True` ile diske indirmeden işle; ham web metnini doğrudan eğitime verme, [Veri Temizleme](/veri/veri-temizleme/) boru hattından geçir.

## Hızlı Kalite Kontrol Listesi

İndirdiğin her set için şu 6 kontrolü yap:

1. **Lisans** uygun mu (ticari kullanacaksan özellikle)?
2. **Dil** gerçekten Türkçe mi (karışık setler olur)?
3. **Boş/bozuk satır** oranı ne?
4. **Tekrarlar** var mı (aynı örnek defalarca)?
5. **Kişisel veri** var mı (isim, telefon, e-posta)?
6. **Format** senin aracına uygun mu ([dönüştürme](/veri/veri-formatlari/))?

:::tip
Bu kontrolleri elle yapman gerekmez; `datasets` + pandalar ile ilk 1.000 satırı tarayan mini bir script 10 dakikada hazırlanır — fikir için [Veri Temizleme](/veri/veri-temizleme/) sayfasına bak.
:::

## Kaynaklar ve İleri Okuma

- [FineWeb-2 veri kartı (Hugging Face)](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) — binden fazla dil alt kümeli filtrelenmiş web derlemi; Türkçe istatistikleri karttaki dil tablosunda.
- [FineWeb2 makalesi (arXiv:2506.20920)](https://arxiv.org/abs/2506.20920) — derleme ve filtreleme boru hattının teknik ayrıntıları.
- [CulturaX veri kartı (Hugging Face)](https://huggingface.co/datasets/uonlp/CulturaX) — mC4 ve OSCAR birleşiminden temizlenmiş çok dilli derlem; dil bazında belge ve token sayıları.
- [OSCAR-2301 veri kartı (Hugging Face)](https://huggingface.co/datasets/oscar-corpus/OSCAR-2301) — gated erişim, telif durumu ve kullanım koşulları.
- [Magpie: Alignment Data Synthesis from Scratch (arXiv:2406.08464)](https://arxiv.org/abs/2406.08464) — hizalı modelden kendiliğinden talimat üretme yöntemi.
- [distilabel (GitHub)](https://github.com/argilla-io/distilabel) — sentetik veri ve yargıç-model değerlendirmesi için boru hattı aracı.
- [AI models collapse when trained on recursively generated data (Nature 631, 755-759, 2024)](https://www.nature.com/articles/s41586-024-07566-y) — model çöküşünün deneysel gösterimi.
- [Wikimedia dumps: trwiki](https://dumps.wikimedia.org/trwiki/) — Türkçe Wikipedia'nın düzenli dump'ları (CC BY-SA).
- [TBMM Tutanak Metinleri](https://www.tbmm.gov.tr/Tutanaklar/TutanakMetinleri) — resmî tutanak arşivi; resmî toplu indirme API'si yok.
- [YÖK Ulusal Tez Merkezi](https://tez.yok.gov.tr/UlusalTezMerkezi) — tez arama ve izinli tam metinler; toplu indirme kısıtlı.
- [KVKK Kurumu](https://www.kvkk.gov.tr/) — kişisel verilerin korunması mevzuatının resmî kaynağı.
