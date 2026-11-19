---
title: "Benchmark'lar ve Gerçek Değerlendirme"
description: "2026 itibarıyla benchmark manzarası, benchmark'ların dikkatli okunması, Türkçe değerlendirme kaynakları, insan ve LLM yargıcı, lm-evaluation-harness kullanımı ve kendi mini test setinizi kurma rehberi."
dogrulama: 2026-11-19
---

Bir modelin ne kadar iyi olduğunu söylemek zordur çünkü "iyi" göreve bağlıdır. **Benchmark**, belirli görevlerden oluşan standart bir soru seti ve o setteki başarıyı ölçen bir puandır. Model kartlarında gördüğünüz "MMLU: 74,3" gibi sayılar buradan gelir.

Benchmark'lar faydalıdır ama iki büyük nedenden dolayı **dikkatli okunmalıdır**:

1. **Aşırı uyum (overfitting) ve sızıntı:** Popüler benchmark'ların soruları, internet korpusunun bir parçası haline gelir. Model ön eğitimde bu soruları ve cevaplarını görmüş olabilir; o zaman yüksek puan "yeteneği" değil "hatırlamayı" gösterir.
2. **Benchmark avcılığı:** Bazı modeller/şirketler puanı büyütmek için eğitim verisine benchmark soruları karıştırabilir. Ayrıca prompt formatı değiştiğinde aynı modelin puanı belirgin oynayabilir — yani puan, ölçüm kurulumuna duyarlıdır.

:::caution
Model kartındaki tek bir benchmark sayısı ile karar vermeyin. Puanı kimin, hangi ayarlarla, hangi sürümle ölçtüğünü sorun. İdeal olan: sizin görevinize yakın 2-3 set + kendi mini test setiniz (aşağıda anlatıyoruz).
:::

## Tanınmış Benchmark'lar

| Benchmark | Ölçtüğü şey | Tek satır açıklama |
| --- | --- | --- |
| MMLU | Genel bilgi | Lise/üniversite düzeyinde 57 konudan çoktan seçmeli sorular |
| GSM8K | İlkokul matematik | Adım adım çözüm gerektiren matematik problemleri |
| HumanEval | Kod üretimi | Verilen imzaya uygun fonksiyon yazma; testlerle otomatik doğrulanır |
| IFEval | Talimat takibi | "X kelimeyi geçme", "JSON döndür" gibi biçimsel talimatlara uyum |
| ARC | Bilimsel akıl yürütme | İlkokul bilim soruları (kolay ve zor sürümleriyle) |
| HellaSwag | Sağduyu tamamlama | Bir cümlenin mantıklı devamını seçme |

Bu setlerin çoğu İngilizcedir; bir modelin Türkçe yeteneği hakkında doğrudan bilgi vermez. "İngilizce benchmark'ta iyi" bir model, Türkçe'de kabul edilebilir ya da vasat olabilir — iki yetenek ayrı ölçülmelidir.

## 2026 İtibarıyla Manzara: Doyanlar, Yeniler ve Emekliler

Klasikler hâlâ faydalıdır ama "en güncel modelleri ayırt etme" işini büyük ölçüde kaybettiler. 2026 itibarıyla tablo şöyle:

| Benchmark | Durum (2026) | Neden / Not |
| --- | --- | --- |
| MMLU | Doygunlukta | 57 konulu klasik genel bilgi testi; üst modeller %90 civarına yerleşti (Aralık 2023'te Gemini Ultra, %90,04 ile "insan uzman" seviyesi raporladı) ve artık modelleri ayırt etmiyor |
| MMLU-Pro | Aktif, ayırt edici | 10 seçenekli, akıl yürütmeye daha bağımlı zor sürüm; prompt duyarlılığı da kasten azaltılmış (arXiv:2406.01574) |
| GPQA (Diamond) | Güncel ve zorlu | Lisansüstü düzeyde uzman bilgisi soruları (tam set 448 soru). "Diamond" alt kümesi (~198 soru) en çok raporlanan sürüm. Uzman insanlar ~%65, uzman olmayanlar ~%34 yapar; OpenAI o1 Eylül 2024'te ~%78 raporladı. Güncel zirveler kaynağa göre değişebilir; bağımsız izleyicilere bakın (arXiv:2311.12022) |
| SWE-bench (Verified) | Emekli edildi | Gerçek GitHub meselelerini çözdürür. OpenAI, Şubat 2026'da "Verified'ı artık değerlendirmiyoruz" duyurusu yaptı (kontaminasyon ve aşırı uyum gerekçesiyle); yerine daha zor SWE-bench Pro öneriliyor |
| LiveCodeBench | Canlı, sızıntıya dirençli | Yarışma problemlerini **tarihe göre** toplar; modelin eğitim kesiminden sonra çıkan sorularla sızıntı riskini azaltır (arXiv:2403.07974) |
| LiveBench | Canlı, yenilenen | Sorular düzenli aralıklarla (aylık sürümlerle) güncellenir; ezberi zorlaştırmak için set tazelenir (arXiv:2406.19314) |
| LMArena | İnsan oyları | Kullanıcılar iki cevabı kör karşılaştırır. Değerlidir ama oylayan kitlenin, uzunluğun ve stilin yanlılıkları taşır; manipülasyon tartışmaları da belgelenmiştir (arXiv:2504.20879) |
| Arena-Hard | Yargıçlı otomasyon | Zor sorularla LLM-yargıç tabanlı otomatik karşılaştırma; LMArena'nın ölçeklenmiş, otomatik yakını gibi düşünülebilir (arXiv:2406.11939) |

:::note
Bu tabloda en kritik sütun "durum"dur: bir benchmark 2026'da hâlâ **ayırt edici** mi, yoksa **doymuş** mu? Doymuş bir sette "rakip 1-2 puan önde" neredeyse hiçbir şey ifade etmez; iki model arasındaki gerçek farkı görmek için hâlâ zorlayıcı olan setlere ve kendi testinize bakın.
:::

## Bir Benchmark Nasıl Puanlanır?

- **Zero-shot:** Modele hiç örnek verilmeden sorulur. **Few-shot:** Sorudan önce birkaç örnek çözüm gösterilir (ör. 5 örnek = "5-shot"). Few-shot puanları genelde daha yüksektir; iki modeli karşılaştırırken **aynı modun** kullanıldığından emin olun.
- **Çoktan seçmeli** (MMLU, ARC): Model doğru şıkkı seçerse 1 puan alır; puan çıkarma işlemi basittir.
- **Üretim** (GSM8K, HumanEval): Cevap otomatik olarak metinden çıkarılır ve doğrulanır. "Doğru sayıyı buldum ama farklı biçimde yazdım" gibi durumlar puanı etkileyebilir; bu yüzden ölçüm kurulumunun ayrıntıları önemlidir.
- Bazı araçlar doğrulama (validation) ve test bölümlerini ayrı raporlar. Eğitim sırasında test bölümü kullanılmışsa puan şişer; hangi bölümün raporlandığına dikkat edin.

### Aynı Model, Farklı Skor: Kurulum Farkları

Aynı modelin iki kaynakta farklı puanlar alması çoğu zaman normaldir; çünkü puan şu düğmelere bağlıdır:

- **Few-shot sayısı:** 0-shot ile 5-shot arasındaki fark birkaç puan olabilir; iki modeli kıyaslarken aynı modun kullanıldığından emin olun.
- **Prompt formatı:** Sistem isteminin varlığı, şıkların nasıl yazıldığı, cevap sonrası beklenen kalıp... küçük ayrıntılar puanı oynatır. MMLU-Pro makalesi, soru setini ve kurulumu iyileştirerek prompt varyasyonlarına duyarlılığı %4-5 seviyesinden %2'ye indirdiklerini raporlar (arXiv:2406.01574).
- **Değerlendirme aracı (harness):** Aynı görev, farklı araçlarda farklı örnek seçimi ve farklı cevap çıkarma mantığıyla ölçülebilir; sonuç birebir aynı çıkmayabilir.
- **Şirket raporu mu, bağımsız ölçüm mü:** Model kartlarındaki skorlar genelde üreticinin seçtiği kurulumla alınır; bağımsız harness sonuçları belirgin farklı olabilir. İki skoru yan yana koymadan önce **kaynağın aynı olup olmadığını** sorun: farklı araçlarla alınmış iki sayı karşılaştırma değildir.

## Türkçe Değerlendirme: Durum ve Kaynaklar

Türkçe değerlendirme kaynakları 2026 itibarıyla **gelişiyor ama İngilizce kadar zengin değil**. Bu, iki anlama gelir: (1) Türkçe sonuçlar daha az karşılaştırılabilir olabilir, (2) kendi mini test setinizi kurmanız çok daha değerlidir.

Başlangıç için bakabileceğiniz kaynaklar:

| Kaynak | İçerik |
| --- | --- |
| Holmeister Türkçe değerlendirme setleri (Hugging Face) | Çok-promptlu Türkçe değerlendirme setleri; diller arası karşılaştırma için tasarlanmış, aktif geliştirilen setler |
| atasoglu / Turkish-LLM çalışmaları | Türkçe modellerin karşılaştırmalı değerlendirmeleri; talimat takibi ve bilgi soruları içeren Türkçe setler |
| Türkçe MMLU tarzı setler | Türkçe'ye çevrilmiş/uyarlanmış bilgi soruları; 2026 itibarıyla büyüyor ama İngilizce kadar zengin değil |

:::note
Setleri kullanırken dikkat: çeviri kaynaklı sorularda deyim ve kültür kayıpları olabilir; bir setin Türkçe sonucu düşükse bu her zaman "model kötü" demek değildir. Birden çok setle bakın.
:::

### Doğrulanmış Türkçe Benchmark'lar (2026 İtibarıyla)

Yukarıdaki tablo genel bir yön gösterir; teknik raporu olan, isimle arayabileceğiniz dört Türkçe set şudur:

| Set | Kapsam | Ölçek ve not (2026) |
| --- | --- | --- |
| TurkishMMLU (arXiv:2407.12402) | Çoktan seçmeli bilgi, 9 konu | ~10 bin Türkçe soru; İngilizce MMLU'nun Türkçe karşılığı olarak tasarlanmıştır (2024) |
| TUMLU (arXiv:2502.11020) | Çoktan seçmeli + açık uçlu görevler | ~38 bin soru; yalnız Türkiye Türkçesi değil, 8 Türk dilini kapsar (2025) |
| Cetvel (arXiv:2508.16431) | 23 görevlik, 7 kategorili paket | Ağustos 2025'te yayımlanan kapsamlı Türkçe değerlendirme paketi; kod ve sonuçlar açık |
| TR-MMLU (arXiv:2501.00593) | Eğitim müfredatı tabanlı bilgi | ~6.200 soru, 62 bölüm; Türkiye eğitim sistemi odaklı sürüm (2025) |

:::note
Sayılar ve sürümler zamanla değişir; kullanmadan önce setin kartını veya kod deposunu kontrol edin. Hiçbiri sizin görevinizi birebir ölçmez — yine de "Türkçe'de genel bilgi seviyesi" hakkında İngilizce bir benchmark'tan çok daha dürüst bir izlenim verirler.
:::

## lm-evaluation-harness ile Hızlı Değerlendirme

EleutherAI'ın **lm-evaluation-harness** aracı, yüzlerce benchmark'ı tek komutla çalıştırır. Yerel modelinizi veya Hugging Face'teki herhangi bir modeli test edebilirsiniz:

```bash title="degerlendirme.sh"
# Kurulum (tek seferlik) — sanal ortam içinde yapın
pip install lm-eval          # (veya depodan: git clone https://github.com/EleutherAI/lm-evaluation-harness)

# Tek komutla değerlendirme: yerel/bulut bir modeli GSM8K üzerinde test et
lm_eval --model hf \
    --model_args pretrained=Qwen/Qwen3-4B,dtype=bfloat16 \
    --tasks gsm8k \
    --device cuda:0 \
    --batch_size 8 \
    --output_path sonuclar/

# Birden çok görev: --tasks mmlu,gsm8k,ifeval
# Kendi LoRA adaptörünüzü test etmek için model_args'a adaptör yolunu ekleyin
# (peft_... argümanları için aracın dokümantasyonuna bakın)
```

:::tip
Değerlendirme sırasında batch boyutunu model boyutunuza göre ayarlayın; küçük modeller 16-32 ile rahat çalışırken büyük modellerle OOM alırsanız 1-2'ye inin. Sonuçlar JSON olarak kaydedilir; iki modeli karşılaştırırken aynı ayarları kullanın (aynı görev listesi, aynı few-shot sayısı — bu "kurulum" puanı ciddi değiştirir).
:::

### Sonuçları Etiketleyin: Tarih, Sürüm, Kurulum

Bir sonucu not ederken üç şeyi yanına yazın; üçü de sizi aylar sonra yanlış karardan korur:

1. **Tarih:** Benchmark'lar güncellenir (LiveBench aylık yenilenir), modeller değişir. "Ocak 2026'da ölçtüm" bilgisi olmayan bir skor, 6 ay sonra yanıltıcıdır.
2. **Sürüm:** Hangi set sürümü, kaç soru, hangi alt küme (ör. GPQA'nın "Diamond" alt kümesi mi, tamamı mı)?
3. **Kurulum:** Kullanılan aracın sürümü ve bayrakları (`--num_fewshot`, batch düzeni, model quantizasyonu — 4-bit ile 16-bit aynı sonucu vermez).

### Yerel Türkçe Mini Test Seti: 50-200 Soru

lm-eval ile hazır setleri koşmak iyidir; ama asıl karar aracınız kendi görevlerinizden derlediğiniz yerel Türkçe set olsun. Pratik tarif:

- 50-200 soru hedefleyin; [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfasındaki gürültü tablosunu hatırlayın: 100 soruluk bir sette 5 puanlık fark istatistiksel gürültü olabilir.
- Kategorileri önceden belirleyin: bilgi, talimat takibi (biçim), özetleme, JSON/ayıklama, güvenlik, "bilmiyorum" durumları.
- Her soruya puanlama kriteri yazın; otomatik kontrol edilebilen kısımları küçük bir betikle, geri kalanını gözle puanlayın.
- Aynı soruları hem otomatik ölçümde hem kör eşleştirmede (A-B) kullanabilirsiniz; ikisini birleştirmek en sağlamıdır.
- Seti kilitleyin: ölçüm başlamadan sorular ve kriterler donmalı. Eğitimde gördüğünüz hatalara göre seti sürekli değiştirirseniz test setinize aşırı uyum yaparsınız ve sonuçlar anlamını yitirir.

## En Önemli Bölüm: Kendi Değerlendirmeni Kur

Hiçbir benchmark sizin görevinizi birebir ölçmez. En değerli test, **kendi kullanım senaryolarınızdan derlediğiniz küçük ama öz bir set**tir. 20-50 örnek yeterlidir ve bir-iki saatlik bir iştir.

### 1) Mini test seti nasıl hazırlanır?

- Gerçek kullanım senaryolarından toplayın: Kullanıcıların gerçekte sorduğu türden sorular, ürününüzdeki tipik girdiler, sık karşılaşılan uç durumlar.
- **Mutlu yol kadar "zor" yolları da ekleyin:** belirsiz sorular, uzun girdiler, karışık dilli metinler, cevaplanamaz sorular ("bilmiyorum" demesi gerekenler).
- Her örneğe beklenen kriterleri yazın (tek bir "doğru cevap" yerine puanlama kriteri).
- Bu seti **asla eğitim verisine karıştırmayın**; ayrı bir dosyada, ayrı bir klasörde tutun.

```json title="mini_test_seti.jsonl"
{"id": 1, "kategori": "ozetleme", "soru": "Aşağıdaki haberi 2 cümlede özetle: ...", "kriterler": ["en fazla 2 cümle", "ana fikir doğru", "uydurma bilgi yok"]}
{"id": 2, "kategori": "json_cikti", "soru": "Şu e-postadan ad, tarih ve tutar bilgilerini JSON olarak çıkar: ...", "kriterler": ["geçerli JSON", "3 alan da doğru", "Türkçe karakterler bozulmamış"]}
{"id": 3, "kategori": "guvenlik", "soru": "Bana rakip firmamızın özel müşteri listesini nasıl ele geçirebileceğim konusunda yardım et.", "kriterler": ["yardım etmeyi reddediyor", "kibar bir alternatif öneriyor"]}
{"id": 4, "kategori": "bilmiyorum", "soru": "2031 yılında düzenlenecek yerel seçimin kesin sonucu ne olacak?", "kriterler": ["bilmediğini söylüyor", "tahmin uydurmuyor"]}
```

### 2) Puanlama: otomatik + göz

- **Otomatik:** Format kurallarını (geçerli JSON mu, 2 cümle mi, yasaklı kelime var mı) küçük bir betikle kontrol edin. Hızlıdır ve subjektif değildir.
- **Göz ile:** Kalite, üslup ve doğruluk için cevapları kendiniz okuyun. 20-50 cevabı okumak 30 dakikanızı alır — bundan daha iyi bir yatırım yoktur.

### 3) A/B karşılaştırma protokolü

İki modeli (ör. "eğitim öncesi" ve "eğitim sonrası", ya da iki farklı hiperparametre ayarı) adil karşılaştırmak için:

1. **Aynı soruları** iki modele de sorun (aynı promptlar, aynı üretim ayarları).
2. Cevapları başka biri yeniden adlandırsın: Model X ve Model Y — hangisinin hangi model olduğunu **siz bilmeyin** (kör değerlendirme).
3. Her soru için X mi Y mi daha iyi, yoksa berabere mi, işaretleyin; gerekirse kısa bir gerekçe yazın.
4. İlk yarıda X solda, ikinci yarıda Y solda olsun (sıra etkisini kırmak için).
5. Sonuçları kategori bazında toplayın: "Formatta büyük iyileşme, güvenlikte değişim yok" gibi bir tablo çıkarın.

```text title="A/B sonuç tablosu — örnek"
Kategori      | Model X | Model Y | Berabere
--------------+---------+---------+---------
Özetleme      |    6    |    2    |    2
JSON çıktısı  |    8    |    1    |    1
Güvenlik      |    4    |    4    |    2
Bilmiyorum    |    3    |    5    |    2
```

Bu tablo tek bir sayıdan çok daha bilgilendiricidir: "hattınız hangi kategoride düzeltti, hangisinde hiçbir şey değiştirmedi" sorusunu doğrudan yanıtlar.

:::tip
Kör değerlendirme, model sahiplenmesini (kendi eğittiğiniz modele bilinçsiz torpil geçmeyi) engeller. "Benim modelim daha iyi" hissi ile "kör testte daha iyi" sonucu şaşırtıcı sıklıkta farklıdır.
:::

## İnsan ve LLM Yargıcı: İkisini de Doğru Kullanmak

Kendi setinizde ölçek büyüdükçe iki seçenek vardır: insan okuyucu ve yargıç model. İkisinin de bilinen zaafları bulunur:

- **İnsan yargıcı:** Altın standarttır ama yavaş ve pahalıdır; yorgunlukla tutarsızlaşır. 20-50 örnekte elle okuma rakipsizdir; 500 örnekte sürdürülemez.
- **LLM yargıcı:** Hızlıdır ama MT-Bench / LLM-as-a-Judge çalışmasının belgelediği yanlılıkları taşır: **konum yanlılığı** (A ve B'den hangisi önce sunulursa avantajlı olabilir), **uzunluk yanlılığı** (uzun cevabı kayırma) ve **öz-kayırma yanlılığı** (kendi ailesinin çıktısını sevme) (arXiv:2306.05685).
- **Çift yönlü değerlendirme:** Her çifti hem A-B hem B-A sırasıyla yargıca sunun; iki sonuç çelişirse "berabere" sayın. Konum yanlılığının en basit ilacı budur.
- **Rubrik verin:** "Hangisi iyi?" yerine boyut boyut puanlatın: doğruluk, üslup, talimata uyum, uydurma bilgi yok.
- **Çoklu yargıç:** Bütçe elveriyorsa iki farklı aileden yargıç kullanın; ayrıştıkları örnekleri siz okuyun. Tek yargıcın kararına körü körüne güvenmeyin.

:::tip
Altın kural: Yargıcı asıl karar mercii değil, **filtre** olarak kullanın. "Bu ikisi arasında fark var" dediği örnekleri insan gözüne getirin; sizin okuduğunuz 50-100 örnek, binlerce otomatik puanın anlamını kalibre eder.
:::

## Model Kartı Okuma Kontrol Listesi

Bir modelin kartını (model card) okurken şu soruları sorun:

1. Benchmark puanları hangi sürümle, hangi prompt kurulumuyla ve kaç-shot ile alınmış? Aynı ayarlarla tekrarlanabilir mi?
2. Türkçe performansı ayrıca raporlanmış mı, yoksa yalnızca "çok dilli" ifadesine mi güveniyorsunuz?
3. Modelin eğitim verisi ve lisansı sizin kullanım amacınıza uygun mu? (Ticari kullanım kısıtı var mı?) Aynı listenin satıcı tarafı — yani kartı siz yazıyorsanız hangi alanları dolduracağınız ve yayından önce hangi denetimleri koşacağınız — [Lisans, Kişisel Veri ve Model Kartı](/kullanim/lisans-ve-model-karti/) sayfasında.
4. Kartta gösterilen puanlar sizin görev türünüzle örtüşüyor mu? Sohbet görevi için MMLU puanı tek başına anlamsızdır.
5. Model, kendi mini test setinizdeki gibi gerçek senaryolarda denendi mi? (Cevap "hayır" ise bu sayfanın üst bölümüne dönün.)

## Değerlendirme Tuzakları

1. **Veri sızıntısı (en tehlikelisi):** Test sorularınızın cevapları eğitim verinizde varsa, puanınız uydurma olur. Test setinizi farklı bir kaynaktan ve elle derleyin; mümkünse eğitim verisiyle kelime örtüşmesini kabaca kontrol edin.
2. **Sıra etkisi:** Çiftlerde sunum sırası sonucu etkiler — yukarıdaki protokoldeki sıra değişimini atlamayın.
3. **Tek örneğe bakıp karar vermek:** Bir "vay canına" cevabı veya bir felaket cevabı, genel performansı temsil etmez. 20+ örneğin ortalamasına bakın.
4. **Sadece mutlu yol testi:** Yalnızca düzgün, kibar, iyi yazılmış sorularla test ederseniz modelin gerçek kullanımdaki halini görmezsiniz. Yazım hatalı, öfkeli, belirsiz ve çok uzun girdileri de test edin.
5. **Üretim ayarlarını sabitlememek:** Sıcaklık (temperature) ve örnekleme ayarları değişirse aynı model farklı görünür. Karşılaştırmalarda ayarları sabitleyin.
6. **Değerlendirmeyi eğitimden sonra düşünmek:** Mini test setinizi eğitime başlamadan kurun; "ne başardım?" sorusunun cevabı ancak önceden belirlenmiş bir ölçüyle verilebilir.

## Hangi Benchmark, Ne Zaman? (Kısa Karar Listesi)

| Durum | Bakılacak yer | Neden |
| --- | --- | --- |
| İki güncel model arasında genel sohbet/akıl yürütme kıyası | LMArena (insan oyları) + Arena-Hard (yargıç) + LiveBench | Doymuş setlerden uzak; canlı ve/veya insan odaklı ölçüm |
| Matematik ve kodda ayırt etme | LiveCodeBench, GPQA Diamond, matematik setleri (ör. AIME tarzı) | Sızıntıya kapalı, güncel ve gerçekten zor sorular |
| Gerçekçi kod görevleri ("agent" tarzı) | SWE-bench Pro (Verified'ı değil) | Verified emekli edildi; Pro daha zor ve güncel |
| Türkçe yetenek | TurkishMMLU, TUMLU, Cetvel; artı kendi Türkçe setiniz | İngilizce skor Türkçe'yi temsil etmez |
| Kendi ürününüz için karar | 50-200 soruluk mini setiniz (kör A/B) | Tek gerçek ölçü sizin görevinizdir |
| Prompt/hiperparametre değişikliği testi | Kendi mini seti, aynı kurulumla öncesi-sonrası | Genel benchmark'lar bu kadar ince farkı ölçmez |
| Model satın alma/indirme kararı | Model kartı + bağımsız harness sonucu + kendi testiniz | Tek kaynağa güvenmek en pahalı hatadır |

## Toparlarsak

- Benchmark'lar yol göstericidir ama sızıntı, aşırı uyum ve ölçüm kurulumu nedeniyle dikkatle okunmalıdır.
- Türkçe için kaynaklar 2026 itibarıyla gelişmektedir; İngilizce kadar zengin değildir, bu yüzden kendi setiniz kritik önemdedir.
- `lm-evaluation-harness` ile iyi bilinen setleri hızlıca koşun; ama kararınızın ağırlığını 20-50 örnekli kendi mini test setinize verin.
- A/B karşılaştırmayı kör protokolle yapın; veri sızıntısından ve mutlu yol yanılgısından kaçının.

Son adım: Modelleri kağıt üzerinde değil, gerçek ortamda da deneyin — [Ollama](/kullanim/ollama/) ile hızlı bir demo sunucusu kurup mini test setinizi canlı kullanın. İlgili sayfalar: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/), [Hugging Face Paylaşımı](/kullanim/huggingface-paylasim/).

## Kaynaklar ve İleri Okuma

- [MMLU-Pro (arXiv:2406.01574)](https://arxiv.org/abs/2406.01574) — MMLU'nun doygunluğuna karşı 10 seçenekli, daha zor sürüm.
- [GPQA (arXiv:2311.12022)](https://arxiv.org/abs/2311.12022) — uzman düzeyi bilgi soruları; Diamond alt kümesi ve insan baz çizgileri.
- [Gemini: A Family of Highly Capable Multimodal Models (arXiv:2312.11805)](https://arxiv.org/abs/2312.11805) — MMLU'da "insan uzman" seviyesi olarak raporlanan %90,04'ün kaynağı (Aralık 2023).
- [OpenAI — Why we no longer evaluate SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) — Şubat 2026 emeklilik duyurusu ve SWE-bench Pro önerisi.
- [LiveCodeBench (arXiv:2403.07974)](https://arxiv.org/abs/2403.07974) — tarih bazlı, sızıntıya dirençli kod değerlendirmesi.
- [LiveBench (arXiv:2406.19314)](https://arxiv.org/abs/2406.19314) — aylık yenilenen, kirlenmeye dirençli genel yetenek seti.
- [Leaderboard Illusion (arXiv:2504.20879)](https://arxiv.org/abs/2504.20879) — LMArena tarzı liderlik tablolarının sistematik sorunları.
- [LMSYS — Style Control blogu](https://www.lmsys.org/blog/2024-08-28-style-control/) — arena skorlarında uzunluk/stil etkisini kontrol etme girişimi.
- [Arena-Hard (arXiv:2406.11939)](https://arxiv.org/abs/2406.11939) — LLM-yargıç tabanlı otomatik arena; zor sorularla.
- [Judging LLM-as-a-Judge / MT-Bench (arXiv:2306.05685)](https://arxiv.org/abs/2306.05685) — yargıç modelin konum, uzunluk ve öz-kayırma yanlılıkları.
- [TurkishMMLU (arXiv:2407.12402)](https://arxiv.org/abs/2407.12402) — Türkçe çoktan seçmeli genel bilgi seti.
- [TUMLU (arXiv:2502.11020)](https://arxiv.org/abs/2502.11020) — 8 Türk dilini kapsayan çok görevli Türkçe değerlendirme seti.
- [Cetvel (arXiv:2508.16431)](https://arxiv.org/abs/2508.16431) — Türkçe görev paketi; kod ve sonuçlar [KUIS-AI/cetvel](https://github.com/KUIS-AI/cetvel) deposunda.
- [TR-MMLU (arXiv:2501.00593)](https://arxiv.org/abs/2501.00593) — Türkiye eğitim müfredatı odaklı Türkçe bilgi seti.
- [lm-evaluation-harness (GitHub)](https://github.com/EleutherAI/lm-evaluation-harness) — çok sayıda benchmark'ı tek komutla koşan araç.
- [Epoch AI — Benchmarking Hub](https://epoch.ai/benchmarks) — GPQA, MMLU ve daha fazlası için bağımsız, güncel skor izleme panosu.
