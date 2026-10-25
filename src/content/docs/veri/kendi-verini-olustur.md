---
title: "Kendi Verini Oluştur: SSS ve Dokümanlardan Eğitim Verisi"
description: Elindeki SSS'leri, destek kayıtlarını ve dokümanları modele öğretilebilir soru-cevap verisine dönüştürmenin yolları — manuel üretim, sentetik üretim ve kalite kontrolü.
dogrulama: 2026-10-15
---

Şimdiye kadar hazır veri setlerini kullandık. Ama işin gerçek değeri burada başlar: **senin verin.** Aldığın her kurumsal destek kaydı, yazdığın her SSS, hazırladığın her ürün dokümanı — bunların hiçbiri internetteki açık setlerde yok. Bu sayfa, "elimde şu materyaller var" noktasından "elimde eğitime hazır JSONL var" noktasına giden yolu anlatır.

## Elindeki Materyalleri Envanterle

Başlamadan önce bir tablo yap — hangi kaynağın hangi formata dönüşeceğini belirle:

| Elindeki materyal | Dönüşeceği veri | Uygun yöntem |
| --- | --- | --- |
| SSS sayfası / sık sorulan sorular | Soru-cevap (SFT) | Doğrudan eşleştirme |
| Destek e-postaları / canlı sohbet kayıtları | Soru-cevap (SFT) | Temizle + özetle |
| Ürün dokümanları, kılavuzlar | Soru-cevap (SFT) veya düz metin | LLM ile üretim + doğrulama |
| Teknik yazılar / makaleler yığını | Düz metin (devam ön eğitimi) | Parçala → düz metin verisi |
| İş akışları, iç süreçler | Talimat-cevap (SFT) | Uzmana yazdır veya yaz |

:::note[Veri nereden bulunur ile farkı ne?]
[Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/) sayfası "hazır veri" avıdır; bu sayfa "kendi hammaddenden veri imalatı"dır. İkisi birbirini tamamlar: hazır veriyle döngüyü öğren, kendi verinle farklılaş.
:::

## Yöntem 0: Uzmandan Mülakat (En Değerli Veri)

En kaliteli veri, hiçbir dokümanda yazmayan veridir. Deneyimli bir çalışanın kafasındaki **örtük bilgi** (tacit knowledge) — "iade talebi gelince önce kargo etiketine bakılır", "bu hatayı görürsen müşteriye yeni hesap açılır" gibi deneyimle öğrenilen işler — SSS sayfalarına ve kılavuzlara nadiren girer. Yazılı soru-cevap çiftlerin zaten varsa [Yöntem 1'e](#yöntem-1-doğrudan-dönüştürme-en-kaliteli) geç; mülakat, henüz yazılmamış olanı çıkarır. Bunun en doğrudan yolu, o kişiyle **30-60 dakikalık yapılandırılmış bir mülakat** yapmaktır.

İşleyiş:

1. **Hazırlık (10 dk):** Soruları önceden yaz. İyi mülakat soruları: "En sık karşılaştığın 10 sorun ne?", "Müşteriler en çok neyi yanlış anlıyor?", "Yeni birine öğrettiğin ilk üç kural ne?", "Hangi durumda 'bu iş kurala sığmaz' dersin?"
2. **Mülakat (30-60 dk):** Kaydı al (izinle). Uzmanın anlattığı örnekleri ve adım adım akışları not et; "neden?" sorusunu sormaktan çekinme — kuralın ardındaki gerekçe, modelin genellemesi için değerlidir.
3. **Yazıya dökme (1-2 saat):** Kaydı soru-cevap çiftlerine çevir. Cümleleri kurumsal üsluba düzelt ama içeriği değiştirme.
4. **Uzman onayı:** Çıkardığın çiftleri uzmana okut. "Söylediğim buydu" onayı, yanlış aktarımı yakalar ve uzmanı sürece bağlar.

Beklenti yönetimi: **1 mülakat ≈ 50-100 örnek.** 30-60 dakikalık sohbetten çıkan düzenli notlar, rahatlıkla bu kadar çift üretir.

**Altın set:** Elle yazılmış **100-200 örnekten oluşan "altın set"** ayır (yöntem ne olursa olsun, ilk örnekleri kendin yaz). Bu set iki iş görür: (1) sonraki sentetik üretimin kalite çıtası olur — yeni örnekler bu seviyeye gelmiyorsa tekrar yaz; (2) model değerlendirmesinde referans test sorusu olarak kullanılır. Altın seti sentetik üretimle kirletme; o, çıtanın kendisidir.

:::tip
Mülakatı tek oturumda bitirmeye çalışma: ilk turda ana akışı çıkar, ikinci turda ("geçen sefer şunu demiştin; şu durumda ne olur?") ayrıntıyı derinleştir. İki kısa tur, tek uzun turdan daha verimlidir.
:::

## Yöntem 1: Doğrudan Dönüştürme (En Kaliteli)

SSS veya soru-cevap çiftleri zaten elindeyse, iş büyük ölçüde **biçimlendirme**dir:

```text title="dönüşüm örneği"
HAM (SSS sayfası)                      →  JSONL (sohbet formatı)
                                                      
Soru: İade süresi kaç gün?             →  {"messages": [
Cevap: Ürünü teslim aldıktan sonra         {"role": "user", "content": "İade süresi kaç gün?"},
14 gün içinde iade edebilirsiniz.          {"role": "assistant", "content": "Ürünü teslim aldıktan
                                           sonra 14 gün içinde iade edebilirsiniz."}]}
```

Püf noktaları:

- Cevapları **olduğu gibi ama derli toplu** yaz: gereksiz giriş cümlelerini ("Merhaba, umarım iyi gününüzdedir...") buda, doğrudan bilgiye gir.
- Kurumsal ağzı koru — modelin öğrenmesini istediğin üslup buysa veriye öyle yansıt.
- Her örneğe aynı **sistem istemini** (system prompt) koy; tutarlılık, davranışın oturmasını sağlar.

## Yöntem 2: Dokümandan Soru-Cevap Üretme

Elinde 40 sayfalık ürün kılavuzu var ama soru-cevap yok. İki yol var:

### A) Manuel yazım (en kaliteli, en yavaş)

Dokümanı okuyup gerçek kullanıcı sorularını hayal ederek yazmak. 500 örnek hedefiyle başla; ilk 50-100 örneği kendin yazarsan kalite çıtasını da öğrenirsin.

### B) Büyük modelden üretim (sentetik veri)

Güçlü bir modelden (API ile bulut modeli veya yerelde büyük model) doküman parçasından soru-cevap üretmesini istemek:

```python title="sentetik_uretim_taslagi.py"
# Temsilî iskelet — hangi sağlayıcıyı kullanırsan kullan mantık aynıdır
ISTEM = """Aşağıdaki metne dayanarak {adet} adet soru-cevap çifti üret.
Kurallar:
- Sorular gerçek müşterilerin soracağı türden olsun.
- Cevaplar SADECE metindeki bilgiye dayansın, uydurma bilgi ekleme.
- Çıktıyı JSON listesi olarak ver: [{{"soru": "...", "cevap": "..."}}]

METİN:
{metin}
"""

uretilenler = []
for parca in dokuman_parcalari:            # dokümanı 1000-1500 karakterlik parçalara böl
    ham_cikti = llm_cagir(ISTEM.format(adet=5, metin=parca))
    for cift in json_yukle_guvenli(ham_cikti):
        uretilenler.append({
            "messages": [
                {"role": "system", "content": "Sen şirketin ürün asistanısın."},
                {"role": "user", "content": cift["soru"]},
                {"role": "assistant", "content": cift["cevap"]},
            ]
        })
```

Bu üretim mantığının kökeni **Self-Instruct**'tür: bir model, kendi ürettiği talimat-cevap örnekleriyle hizalanabilir ([arXiv:2212.10560](https://arxiv.org/abs/2212.10560)). Ama üretilen her örnek eşit değildir — kanıt **AlpaGasus**: Alpaca'nın 52 bin talimatını bir LLM hakeme puanlatarak süzmek, geriye ~9 bin yüksek kaliteli örnek bırakır ve **9 bin örnekle eğitilen model, 52 binin tamamıyla eğitileni belirgin biçimde geçer** ([arXiv:2307.08701](https://arxiv.org/abs/2307.08701)). Ders: sentetik üretimde hacme değil **süzgece** yatırım yap — "sadece metne dayan" istemi yetmediği yerde bir kalite puanlama adımı ekle, düşük puanlı örnekleri at.

Çeşitlilik için istem varyasyonu: WizardLM'in **Evol-Instruct** yaklaşımı, talimatları yapay olarak daha karmaşık ve farklı biçimlere evrimleştirir ([arXiv:2304.12244](https://arxiv.org/abs/2304.12244)) — aynı istemle aynı kalıpta üretmek yerine soruları zorlaştırıp çeşitlendirerek seti zenginleştirebilirsin.

:::danger[Sentetik verinin üç tuzağı]
1. **Uydurma:** Model, metinde olmayan bilgiyi "tamamlar". Bu yüzden istemde "sadece metne dayan" kuralı şart, üretimden sonra da örnekler **kaynağa karşı** doğrulanmalı.
2. **Kendi hatasını pekiştirme:** Modelin ürettiği veriyle model eğitmek, hatalarını da öğretir. Sentetik veriyi küçük bir insan doğrulamasıyla (örnekleme kontrolü) kullan.
3. **Kalıp tekrarı:** Aynı istemle üretilen veri, "robotik" bir kalıba bürünür. İstemde çeşitlilik iste, farklı soru türleri (neden/nasıl/değil mi) talep et.
:::

## Yöntem 3: Düz Metinden Devam Ön Eğitimi Verisi

Cevap üretmene gerek olmayan yol: elindeki uzun metinleri (makaleler, iç notlar) **düz metin** olarak kullanmak.

```python title="metin_parcala.py"
def parcala(metin: str, parca_boyu: int = 1500, ortusme: int = 150):
    """Uzun metni ortüşen (overlapping) parçalara böl."""
    parcalar = []
    baslangic = 0
    while baslangic < len(metin):
        parcalar.append(metin[baslangic : baslangic + parca_boyu])
        baslangic += parca_boyu - ortusme      # bağlam kopmasın diye ortüşme bırak
    return parcalar
```

:::caution
Devam ön eğitimi ile SFT'yi karıştırma: düz metinle "bilgi aşılama" yaparsın ama "talimat takibi" öğretmezsin. Genelde ikisi birlikte kullanılır — akış için [Sıfırdan Ön Eğitim](/llm/pretraining/) ve [Talimat Ayarı](/llm/sft/) sayfalarına bak.
:::

## Uçtan Uca Mini Vaka: 40 Sayfalık Kılavuzdan 200 Örnek

Yöntemleri tek bir senaryoda birleştirelim. Elinde 40 sayfalık ürün kılavuzu var; hedef, alanına özgü ~200 örneklik bir SFT seti:

1. **Parçala (Yöntem 3 kodu):** Kılavuzu 1500 karakterlik parçalara böl → **~60 parça**. Parçaları mümkünse cümle sınırından kes ki sorular bağlamsız kalmasın.
2. **Üret (Yöntem 2B):** Her parçadan 3-5 soru-cevap üret → **~250 aday**.
3. **Tekrar temizle ([Veri Temizleme](/veri/veri-temizleme/)):** Farklı parçalardan gelen benzer sorular — kılavuzun aynı bilgiyi iki yerde anlatması tipiktir — birebir ve yakın tekrar filtresine takılır → **~200 kalır**. Kalan fark, kopuk/bozuk üretimlerin ayıklanmasından gelir.
4. **Gözle doğrula:** Örneklerin %10'unu (20 örnek) rastgele seçip kaynağa karşı oku.
5. **Böl:** ~180 örnek eğitim, 20 örnek test. Test örneklerinin eğitimle örtüşmediğini sızıntı taramasıyla doğrula.

| Adım | Sayı | Not |
| --- | --- | --- |
| Ham kılavuz | ~40 sayfa | |
| Parçalama (1500 karakter) | ~60 parça | cümle sınırından kes |
| Sentetik üretim | ~250 aday | parça başına 3-5 soru |
| Birebir + yakın tekrar filtresi | ~200 kalan | tekrarlı sorular elenir |
| %10 gözle doğrulama | 20 örnek | kaynağa karşı okunur |
| Eğitim / test seti | ~180 / 20 | sızıntı taraması yapıldı |

Sayılar bu örnek senaryoya aittir; senin materyalinde oranlar değişir. Önemli olan akış: **parçala → üret → süz → doğrula → böl**.

## 500 Örnek Hedefiyle Gerçekçi Bir Plan

| Adım | Hedef | Süre (yaklaşık) |
| --- | --- | --- |
| Envanter + ham madde toplama | 1 doküman yığını | 1-2 saat |
| Elle yazım (altın set) | 150-200 örnek | 3-5 saat |
| Sentetik üretim | 300-500 örnek | 1-2 saat |
| Temizlik + tekrar filtresi | Tekilleştirilmiş set | 1 saat |
| Üretilenleri doğrulama (örnekleme) | %10 gözle kontrol | 1 saat |
| Eğitim/doğrulama ayrımı | %95 / %5 | 5 dakika |

Toplam: **1-2 günlük emek** ile alanına özgü, kimsenin erişemeyeceği bir veri seti. Eğitimin kendisi ise 1-3 saat sürebilir — yani **işin ağırlığı veride**, tıpkı bu rehberin baştan söylediği gibi.

## Kalite Kontrol ve Etik

Eğitime başlamadan son kontrol:

1. **Kaynağa dayanıklılık:** Rastgele 20 cevabı seç, kaynak dokümandan doğrula.
2. **Çelişki taraması:** Aynı soruya iki farklı cevap veren örnek var mı?
3. **Dağılım:** Kolay/orta/zor soru ve kısa/uzun cevap dengesi.
4. **Kişisel veri:** İsim, e-posta, müşteri kaydı kaldı mı? ([Veri Temizleme](/veri/veri-temizleme/))
5. **İzin ve lisans:** Müşteri verisi ve iç dokümanları kullanma yetkin var mı? Şirket politikası ve KVKK çerçevesini kontrol et.

:::danger[Etik sınır]
Başkalarının özel yazışmaları, müşteri verileri ve izinsiz toplanmış içeriklerle eğitim verisi oluşturma. Kendi ürettiğin, izinli veya açık lisanslı veriyle çalış.
:::

## Yayın Sonrası Döngü: Veri Güncelleme

Model yayına girdiğinde veri çalışması bitmez; **asıl veri kaynağın yeni açılır**: gerçek kullanıcı soruları. Döngü şöyledir:

1. **Topla:** Modelin başarısız olduğu soruları kaydet — modeli [Ollama Rehberi](/kullanim/ollama/) ile yerelde çalıştırıyorsan sohbet kayıtları, API'deysen istek logları. "Beğenmedim" geri bildirimleri en değerli sinyaldir.
2. **Etiketle:** Her başarısız soru için doğru cevabı yaz (gerekirse uzmana danış) ve soru-cevap çiftini altın sete ekle.
3. **Yeniden eğit:** Güncellenmiş setle modeli yeniden eğit; ilerlemeyi [Benchmark'lar](/degerlendirme/benchmarklar/) ve kendi test setinle ölç.
4. **Sürümle:** Her veri setini tarih/numarayla sakla (`veri_v2_2026-10.jsonl` gibi). "Bu model hangi veriyle eğitilmişti?" sorusu, günler sonra mutlaka sorulur.

İki kural:

- **Test setine asla dokunma.** Başarısız sorular eğitim/altın sete gider; test seti sabit kalır ki ilerleme dürüstçe ölçülebilsin. Test setini güncellemen şartsa yeni bir sürüm oluştur ve skorları sıfırdan raporla.
- **Az az, sık sık güncelle.** 500 soru biriktirip tek dev tur yerine, 50-100 yeni örnekte bir küçük eğitim turu at; her turda düzelip düzelmediğini ölç.

## Kaynaklar ve İleri Okuma

- [AlpaGasus (arXiv:2307.08701)](https://arxiv.org/abs/2307.08701) — 52 bin Alpaca talimatını kalite süzgeciyle ~9 bine indirmenin model kalitesini artırdığını gösteren çalışma (Chen vd., 2023).
- [Self-Instruct (arXiv:2212.10560)](https://arxiv.org/abs/2212.10560) — modelin kendi ürettiği talimatlarla hizalanması fikrinin köken makalesi (Wang vd., 2023).
- [LIMA (arXiv:2305.11206)](https://arxiv.org/abs/2305.11206) — az ama özenle seçilmiş verinin gücünü gösteren çalışma; 1.000 seçkin örnekle güçlü hizalama sonuçları (Zhou vd., 2023).
- [distilabel (GitHub)](https://github.com/argilla-io/distilabel) — sentetik veri üretimi ve AI geri bildirimi çerçevesi; 2026 itibarıyla topluluk tarafından sürdürülüyor.

## Sonraki Adım

Elinde temiz bir JSONL var. Artık [Talimat Ayarı (SFT)](/llm/sft/) ile modelini eğitebilir ya da [Adım Adım Eğitim](/llm/adim-adim-egitim/) rehberine dönerek döngüyü tamamlayabilirsin.
