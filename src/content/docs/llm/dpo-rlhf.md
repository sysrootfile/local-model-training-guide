---
title: "DPO ve RLHF: Modeli Tercihlerle Şekillendirmek"
description: "RLHF'in üç aşaması, DPO'nun neden pratik olduğu, TRL'de yöntem manzarası, DPO pratiği ve başarısızlık modları, RLAIF ve sentetik veri, tercih verisi hazırlama ve TRL DPOTrainer ile açıklamalı bir örnek."
dogrulama: 2026-10-15
---

[Talimat ayarından (SFT)](/llm/sft/) çıkan model çoğu zaman "doğru şeyi bilir ama davranışı istediğiniz gibi değildir". Örneklere bakalım:

- Sorulara hep çok uzun cevap verir (kullanıcı kısa cevap istemişti),
- İstenen resmi üslup yerine fazla laubali konuşur,
- Bazen güvensiz veya kaba bir ton tutturur,
- "Yardım edemem" demesi gereken yerde gereksiz tavsiye verir.

SFT bu sorunları örneklerle *kısmen* düzeltse de her davranışı "iyi örnek yazarak" anlatmak zordur. Tercih ayarı (preference tuning) tam bunun için vardır: modele "iyi örnek" yerine **"şu cevap şundan daha iyidir"** bilgisini öğretiriz.

## RLHF: Klasik Yöntem ve Üç Aşaması

İnsan geri bildirimiyle pekiştirmeli öğrenme (RLHF, reinforcement learning from human feedback) fikri üç aşamadan oluşur:

```text title="Klasik RLHF hattı"
[1] SFT: İyi örneklerle modeli eğit  -->  /llm/sft/
            |
            v
[2] ÖDÜL MODELİ: İnsanlara aynı soruya verilen iki cevabı gösterip
    "hangisi daha iyi?" diye sorun; verilen tercihlerden "cevap puanlamayı"
    öğrenen ayrı bir model eğitin.
            |
            v
[3] PPO: Ana modeli, ödül modelinden yüksek puan alacak şekilde
    pekiştirmeli öğrenmeyle (reinforcement learning) güncelleyin.
      - Aynı anda bellekte 4 model tutulur: politika, referans, ödül, değer
      - Kararsız ve pahalıdır; ciddi mühendislik ve donanım ister
```

RLHF güçlüdür (GPT serisinin hizalanmasında kullanıldı) ama bireysel proje için maliyetlidir: ekstra bir ödül modeli eğitmeniz, PPO'nun kararlılığını yönetmeniz ve ciddi VRAM'e sahip olmanız gerekir.

## DPO: Aynı Fikir, Çok Daha Basit

**DPO (direct preference optimization)**, 2023'te "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" makalesiyle (2305.18290) popülerleşti. Bulgu kısaca şudur: Ödül modeli + PPO karmaşasını atlayıp, **doğrudan "seçilen vs reddedilen" cevap çiftlerinden** modeli güncelleyebilirsiniz.

```text title="DPO hattı"
[Tercih verisi: (soru, seçilen cevap, reddedilen cevap)]
            |
            v
[DPO kaybı: 'seçilen' cevabın olasılığı artarken
 'reddedilen' cevabın olasılığı düşsün; ikisi birden, tek eğitimde]
            |
            v
[Tek eğitim döngüsü — ödül modeli yok, PPO yok]
  - Sabit bir 'referans model' yalnızca karşılaştırma ölçüsü olarak tutulur
  - SFT kadar basit bir eğitim betiğiyle çalışır
```

DPO'nun pratik avantajları:

- RLHF ile **aynı veri türünü** kullanır (insan tercihleri), ama çok daha basit bir hattı vardır.
- [LoRA/QLoRA](/llm/lora-qlora/) ile birleştirilebilir; tek tüketici GPU'da bile denenebilir.
- Eğitim döngüsü SFT'ye benzer: veri yükle, eğit, kaydet.

## Tercih Verisi: Format ve Üretim

DPO için verinin en yaygın formatı JSONL dosyasında `prompt`, `chosen`, `rejected` alanlarıdır:

```json title="tercih_verisi.jsonl"
{"prompt": "Müşteri, kargosu 3 gün geciktiği için öfkeli bir e-posta yazdı. Nazik, çözüm odaklı ve 150 kelimeyi geçmeyen bir yanıt taslağı hazırla.", "chosen": "Merhaba, yaşadığınız gecikme için çok üzgünüz. Durumu hemen inceledim: kargonuz dağıtım merkezinde bekletilmiş ve bugün yola çıkacak. Takip numaranız üzerinden hareketleri izleyebilirsiniz; gecikme 48 saati geçerse kargo ücretini iade edeceğiz. Anlayışınız için teşekkür eder, konuyu takip etmeye devam edeceğimizi bildiririz.", "rejected": "Kargo gecikmeleri bizim kontrolümüzde olan bir şey değil, kargo firmasına sorun. Yoğunluk vardır illa ki, biraz bekleyin."}
{"prompt": "Bir kullanıcı, şifresini unuttuğunu söylüyor. Yardım et.", "chosen": "Elbette yardımcı olayım. 'Şifremi unuttum' bağlantısına tıklayıp kayıtlı e-posta adresinize gelen sıfırlama bağlantısını kullanabilirsiniz. E-posta gelmezse spam klasörünü kontrol edin; hâlâ sorun varsa hesabınızın kayıtlı telefonuyla doğrulama yapmayı deneyin.", "rejected": "Şifreni bilmiyorsan yapabileceğim bir şey yok, yeni hesap aç bence."}
```

:::note
Veriyi nereden bulacaksınız?

- Açık tercih veri setleri ve Türkçe kaynaklar için [Veri Nereden Bulunur](/veri/veri-nereden-bulunur/) sayfasına bakın. (Çoğu açık tercih seti İngilizcedir; Türkçe setler 2026 itibarıyla büyüyor ama henüz İngilizce kadar zengin değil.)
- Kendiniz üretmek de son derece geçerli bir yoldur: aynı soruya iki farklı cevap yazın (ya da iki farklı modelden alın) ve hangisinin daha iyi olduğunu etiketleyin.
- Hız için: Güçlü bir modelden iki cevap üretip (ör. farklı sıcaklık ayarlarıyla), daha iyi olanı işaretlemek de yaygın bir yaklaşımdır. Otomatik etiketleme gürültü getirir; küçük bir sette mutlaka gözle kontrol edin.
:::

Veri hazırlığında altın kural: `chosen` gerçekten iyi, `rejected` gerçekten kötü olmalı — ama **aynı soruya cevap** olmalılar. İkisi tamamen farklı sorulara cevapsa, model "tercih" yerine "konu" öğrenir.

## Kısa Örnek: TRL DPOTrainer

```python title="dpo_egitimi.py"
# DPO ile tercih ayarı — SFT'den geçmiş (veya temel) bir model üzerinde
# Kurulum: pip install "trl" "peft" "datasets" "transformers" "accelerate"

from datasets import load_dataset
from peft import LoraConfig
from trl import DPOConfig, DPOTrainer

# Tercih verisi: prompt / chosen / rejected alanlı JSONL
veri = load_dataset("json", data_files="tercih_verisi.jsonl", split="train")
bolme = veri.train_test_split(test_size=0.1, seed=42)

lora_ayari = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    task_type="CAUSAL_LM",
)

egitim_ayari = DPOConfig(
    output_dir="./dpo-cikti",
    beta=0.1,                        # referans modelden ne kadar uzaklaşılabilir (0.01-0.5)
    num_train_epochs=1,              # DPO'da 1 epoch genelde yeterlidir
    learning_rate=5e-7,              # DİKKAT: DPO'da lr SFT'den çok daha küçüktür (5e-7 - 1e-6)
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    lr_scheduler_type="cosine",
    warmup_steps=0.03,               # oran: adımların %3'ü (v5; eskiden warmup_ratio)
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
)

egitici = DPOTrainer(
    model="Qwen/Qwen3-4B",           # ideal olarak SFT'den geçmiş modelinizin yolunu verin
    args=egitim_ayari,
    train_dataset=bolme["train"],
    eval_dataset=bolme["test"],
    peft_config=lora_ayari,          # QLoRA ile birleştirmek isterseniz modeli 4-bit yükleyip verin
)
egitici.train()
egitici.save_model("./dpo-adaptor")  # yine yalnızca birkaç MB'lık adaptör
```

:::caution
DPO eğitiminde öğrenme oranını SFT'deki gibi yüksek bırakmak (ör. 2e-4) en sık yapılan hatadır; model hızla bozulur ("çöküş" yaşar). DPO için `5e-7 – 1e-6` aralığında kalın. `beta` değerini anlamak için: küçük beta (0.01-0.05) modelin daha serbest değişmesine, büyük beta (0.2-0.5) referans modele daha bağlı kalmasına izin verir.
:::

## Kısa Notlar: ORPO, SimPO ve GRPO

- **ORPO ve SimPO:** DPO'nun daha yeni akrabalarıdır. ORPO, SFT aşamasını tamamen atlayıp tercih verisinden tek aşamada öğrenmeyi hedefler; SimPO ise referans model ihtiyacını ortadan kaldıran bir DPO çeşididir. Doğrudan SFT+DPO yapıyorsanız şimdilik bunları denemek zorunda değilsiniz; ilginç bir araştırma alanı olarak not düşün.
- **GRPO:** Derin akıl yürütme (reasoning) modellerinde popüler olan pekiştirmeli öğrenme yöntemidir; matematik ve kod gibi **doğru cevabı otomatik doğrulanabilen** görevlerde güçlüdür. TRL'de `GRPOTrainer` olarak bulunur. Küçük, özel verili projeler için genellikle DPO'dan da fazlasıdır; ileri seviye bir konu olarak aklınızın bir köşesinde dursun.

## 2026 İtibarıyla TRL'de Yöntem Manzarası

TRL v1 (2026), trainer'ları olgunluk düzeyine göre ayırıyor: bir bölümü çekirdek (yıllardır üretimde kullanılan ve resmî dokümanda ana akışta listelenen), bir bölümü deneysel. 2026 itibarıyla durum şöyle:

| Yöntem | Trainer | Durum (TRL v1.x) | Ne zaman tercih edilir |
| --- | --- | --- | --- |
| DPO | `DPOTrainer` | Çekirdek | Elinizde `chosen`/`rejected` çiftleri varsa; ilk denenecek tercih yöntemi |
| KTO | `KTOTrainer` | Çekirdek | Tercih çifti toplayamıyorsanız: tek cevap + "iyi/kötü" (ikili) etiketi yeterlidir |
| GRPO | `GRPOTrainer` | Çekirdek (çevrimiçi) | Ödülü fonksiyonla otomatik doğrulayabiliyorsanız (matematik, kod) |
| RLOO | `RLOOTrainer` | Çekirdek (çevrimiçi) | Çevrimiçi pekiştirmeli öğrenme; ödül fonksiyonlu akışta hafif bir alternatif |
| ORPO | `ORPOTrainer` | Deneysel | SFT aşamasını atlayıp tercih verisinden tek adımda öğrenmek isterseniz |
| CPO | `CPOTrainer` | Deneysel | ORPO'ya benzer; SFT'siz tek aşamalı bir diğer akraba |

(Kaynak: TRL dokümantasyonundaki "Taxonomy" bölümü — çekirdek/deneysel ayrımı resmî olarak orada yapılıyor.)

DPO'da kalırsanız kaybın (loss) varyantları da var; TRL'de `loss_type` parametresiyle seçilir. Varsayılan `sigmoid`'dir; öne çıkan birkaç seçenek:

| `loss_type` | Fikir | Kaynak |
| --- | --- | --- |
| `sigmoid` (varsayılan) | Klasik DPO hedefi: seçilen ile reddedilen arasındaki olasılık farkını büyüt | DPO makalesi, arXiv:2305.18290 |
| `ipo` | Logit dönüşümü yerine kimlik dönüşümü; aşırı uyuma karşı | IPO, arXiv:2310.12036 |
| `sigmoid_norm` | Sigmoid kaybının cevap uzunluğuna göre normalize edilmiş hâli (SimPO) | SimPO, arXiv:2405.14734 |
| `hinge` | Marj (margin) tabanlı kayıp | RSO, arXiv:2309.06657 |
| `bco_pair` | Tercihi ikili sınıflandırma problemi gibi ele alır | BCO, arXiv:2404.04656 |
| `robust` | Gürültülü/ters etiketlenmiş tercihlere dayanıklı | Robust DPO, arXiv:2403.00409 |

:::tip
Yeni başlıyorsanız varsayılan `sigmoid` ile kalın. `loss_type` değiştirmek, veri kalitesini düzeltmenin yerini tutmaz; asıl kaldıraç veridir. Uzunluk istismarından şikâyetçiyseniz `sigmoid_norm` (SimPO tarzı uzunluk normalizasyonu) denenebilir — bu sorunu "Bilinen Başarısızlık Modları" bölümünde derinleştiriyoruz.
:::

## DPO Pratiği: beta, ref_model ve Öğrenme Oranı

Örnekteki ayar dosyasının dört kritik düğmesini TRL dokümanına dayanarak açalım:

- **`beta` (varsayılan 0.1):** Modelin referans modelden sapmasını cezalandırır. TRL dokümanındaki tanımla: "yüksek beta, referans modelden daha az sapma" demektir. Model neredeyse hiç değişmiyorsa (çok muhafazakâr kaldıysa) beta'yı bir tık düşürün; model referanstan kopup tuhaf davranmaya başlarsa yükseltin.
- **`ref_model=None` (bellek tasarrufu):** Ayrı bir referans modeli tutmak istemiyorsanız `None` bırakın; bu durumda eğitici, eğitim başlamadan önceki model durumunu referans kabul eder. LoRA/QLoRA (PEFT) kullanırken bu daha da pratikleşir — TRL dokümanının ifadesiyle: "DPO'da PEFT kullanırken ayrı bir referans modeli vermenize gerek yok; eğitici otomatik olarak dondurulmuş temel modeli referans alır." Böylece ikinci bir model kopyasını belleğe almanız gerekmez.
- **Epoch:** Tercih verisi küçükse 1-2 tur genelde yeterlidir; artırmadan önce doğrulama kaybına bakın ([Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/)).
- **Öğrenme oranı:** TRL'nin PEFT entegrasyon dokümanındaki öneriler (LoRA için tam ince ayarın yaklaşık 10 katı):

| Eğitim türü | TRL önerisi (DPO) |
| --- | --- |
| Tam ince ayar | `5.0e-7` |
| LoRA | `5.0e-6` (yaklaşık 10 katı) |

TRL'nin DPO trainer sayfası, adaptör eğitirken `≈1e-5` mertebesinin de kullanılabileceğini not eder. Tek bir "doğru" sayı yoktur; doğrulama kaybını ve örnek çıktıları izleyerek kendi verinizde karar verin.

Veri tarafında TRL hem düz metin hem sohbet biçimini kabul eder. Elinizdeki veri rol etiketliyse (user/assistant) sohbet biçimi işleri kolaylaştırır:

```json title="sohbet_biciminde_tercih.jsonl"
{"prompt": [{"role": "user", "content": "Kargom 3 gün gecikti, ne yapmalıyım?"}], "chosen": [{"role": "assistant", "content": "Gecikme için üzgünüz; durumu hemen inceliyoruz ve takip numaranız üzerinden sizi bilgilendireceğiz."}], "rejected": [{"role": "assistant", "content": "Kargo firmasına sorun, bizim elimizde bir şey yok."}]}
```

## Bilinen Başarısızlık Modları ve Önlemler

DPO güçlüdür ama bedava değildir; literatürde iyi belgelenmiş üç tuzağı vardır:

1. **Olasılık kayması (likelihood displacement):** DPO normalde yalnızca reddedilen cevabı bastırmalıdır; ama bazı durumlarda "seçilen" cevabın olasılığı da düşer — model, tercih edilen cevaptan uzaklaşırken farklı bir yöne savrulur. "Unintentional Unalignment" çalışması bunun özellikle benzer gösterimlere (embedding) sahip tercih çiftlerinde yaşandığını ve bu tür örnekleri filtrelemenin sorunu belirgin şekilde azalttığını gösteriyor (arXiv:2410.08847).
2. **Uzunluk istismarı:** İnsanlar (ve yargıç modeller) uzun cevapları kayırma eğilimindedir; DPO bunu öğrenip her cevabı şişirmeye başlayabilir. Park ve arkadaşları bu istismarı DPO'nun örtük ödülündeki uzunluk yanlılığıyla ilişkilendirir ve basit bir uzunluk düzenlileştirmesi önerir (arXiv:2403.19159); TRL'deki `sigmoid_norm` (SimPO) gibi uzunluk-normalize kayıplar da bu yanlılığı azaltmayı hedefler.
3. **Akıl yürütmede gerileme:** DPO sohbet benchmark'larında etkilidir ama uzun adımlı akıl yürütmede kazancı marjinal kalır; Step-DPO çalışması matematik problemlerinde düz DPO'nun neredeyse hiç fayda sağlamadığını raporlar (arXiv:2406.18629). DPO ile PPO'yu karşılaştıran kapsamlı çalışmalar da DPO'nun bazı görevlerde PPO'nun gerisinde kalabildiğini gösteriyor (arXiv:2404.10719).

:::caution
Bu yüzden DPO sonrası yalnızca "tercih kazandı mı?" sorusuna bakmak yetmez: modelin zaten iyi olduğu görevlerde (bilgi soruları, JSON üretimi, matematik) regresyon testleri koşun. Önlemler: (1) tercih verisinin kalitesi ve uzunluk dengesi, (2) beta ve öğrenme oranının temkinli ayarı, (3) DPO öncesi/sonrası kendi mini test setinizle kör karşılaştırma ([Benchmark'lar](/degerlendirme/benchmarklar/)).
:::

## RLAIF ve Sentetik Tercih Verisi

Tercih etiketini illa insan koymak zorunda değilsiniz: **RLAIF** (AI geri bildirimiyle pekiştirmeli öğrenme), etiketlemeyi bir modele yaptırmaktır. Bu fikrin en bilinen uygulaması Anthropic'in **Constitutional AI** çalışmasıdır: modele yazılı bir ilkeler listesi ("anayasa") verilir, model kendi çıktılarını bu ilkelerle değerlendirip düzeltir; insan zararsızlık etiketlerinin büyük bölümü modele devredilir (arXiv:2212.08073).

Sentetik tercih/veri üretmek için iki pratik yaklaşım:

- **Magpie:** Hizalanmış bir modele neredeyse boş bir sohbet şablonu verip "kullanıcı sorusu" ürettirmek, sonra aynı modele cevaplattırmak; böylece eldeki modelin dağılımından büyük ölçekli talimat verisi sentezlenir (arXiv:2406.08464).
- **distilabel (Argilla):** Üretici ve yargıç modelleri ardışık adımlara bağlayıp sentetik veri ve tercih çiftleri üretme hattı kurmanızı sağlayan açık kaynak Python kütüphanesi ([argilla-io/distilabel](https://github.com/argilla-io/distilabel)).

:::caution
Yalnızca kendi model çıktılarınızla döngüsel eğitim "model çöküşü" (model collapse) riski taşır: üst üste sentetik veriyle eğitilen modeller zamanla dağılımın kuyruklarını kaybeder, çeşitlilik düşer (Shumailov ve ark., Nature, 631, 755-759, 2024). Denge: sentetik veriyi insan yazımı ya da insan onaylı veriyle karıştırın, tek bir modelin çıktısına bel bağlamayın ve örnekleri gözle kontrol edin. Başlangıç noktaları: [Veri Nereden Bulunur](/veri/veri-nereden-bulunur/) ve [Kendi Verini Oluştur](/veri/kendi-verini-olustur/).
:::

## SFT ve DPO Yan Yana

| | SFT | DPO |
| --- | --- | --- |
| Veri türü | (girdi, iyi cevap) ikilileri | (girdi, iyi cevap, kötü cevap) üçlüleri |
| Öğrettiği şey | "Şöyle cevap ver" | "Şöyle cevap ver, şöyle verme" |
| Öğrenme oranı (LoRA ile) | 1e-4 – 2e-4 | 5e-7 – 1e-6 |
| Tipik epoch | 1 – 3 | 1 |
| Tipik veri ihtiyacı | Binlerce soru-cevap örneği | Binlerce tercih çifti |
| Eğitim süresi | Saatler | Saatler (SFT'ye benzer) |
| Ne zaman kullanılır | Her zaman ilk adım | Üslup/güvenlik/tercih kritikse ikinci adım |

:::note
DPO sonrası değerlendirme ipucu: Yalnızca eğitim kaybına bakmak yetmez; "seçilen" cevaplara benzeyen çıktılar üretiyor mu diye **gözle** kontrol edin. Ayrıntı için [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).
:::

## Sana Gerekli mi? Karar Kutusu

:::tip
- **Bireysel proje / tek görev modeli:** [SFT](/llm/sft/) neredeyse kesinlikle yeterlidir. Önce SFT yapın, sonuçları [değerlendirin](/degerlendirme/loss-ve-metrikler/); davranış gerçekten problemliyse DPO düşünün.
- **Üslup, güvenlik veya "tercih" kritik:** DPO anlamlıdır. Elinizde binlerce kaliteli tercih çifti varsa (veya toplayabiliyorsanız) iyi sonuç verir.
- **200-300 tercih çiftiyle deney yapmak:** Yeterli değildir; model ezberler veya kutuplaşır. Veri arttırmaya yatırım yapın.
- **Sadece meraktan DPO:** Kategorik olarak zararlı değil ama zaman ve GPU maliyetini bilinçli harcayın. Aşırı mühendislik, yeni başlayanların en sık tuzağıdır; "SFT + iyi veri + iyi değerlendirme" sizi çoğu zaman hedefe götürür.
:::

## DPO Sonrası Ne Ölçülür?

DPO bir "tercih" eğitimidir; ölçüm de üç katmanda yapılır:

1. **Tercih ölçümü (asıl hedef):** Modelin cevapları DPO öncesine göre gerçekten daha çok tercih ediliyor mu? En güvenilir yol, aynı sorulara önce/sonra cevapları üretip kör (hangi model olduğunu bilmeden) karşılaştırmaktır. Bunu ölçeklemek isterseniz AlpacaEval gibi LLM yargıçlı araçlar vardır ([tatsu-lab/alpaca_eval](https://github.com/tatsu-lab/alpaca_eval)) — ama yargıç modellerin de kendi yanlılıkları olduğunu unutmayın; ayrıntı [Benchmark'lar](/degerlendirme/benchmarklar/) sayfasında.
2. **Regresyon testleri (sessiz hasar sigortası):** DPO, modelin zaten iyi olduğu becerileri bozabilir ("Bilinen Başarısızlık Modları" bölümüne bakın). Elinizdeki mini test setini DPO öncesi ve sonrası çalıştırıp görev bazında başarıyı karşılaştırın; düşüş varsa beta'yı yükseltin veya veriyi gözden geçirin.
3. **Davranış testleri:** İstenen davranış gerçekten kazanıldı mı? "Kısa cevap ver", "nazik ol", "gerektiğinde yardım edemem de" gibi hedef davranışlar için elle yazılmış 20-30 örnek yeterlidir; iki modelin çıktısını yan yana koyup kör okuyun.

:::tip
Tek bir sayıya ("kazanma oranı %67") bel bağlamayın: küçük setlerde birkaç örneğin değişmesi sonucu savurur. Örnek sayısı küçükken farkların istatistiksel gürültü olabileceğini hesaba katın ([Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/)).
:::

## Toparlarsak

- RLHF = SFT + ödül modeli + PPO. Güçlü ama ağır bir hattır.
- DPO = aynı tercih verisini kullanan, ödül modeli ve PPO gerektirmeyen basit bir alternatif.
- Veri: `prompt / chosen / rejected` çiftleri; az ve kalitesiz veri DPO'yu bozar.
- Öğrenme oranı SFT'den çok daha küçük (5e-7 – 1e-6); 1 epoch tipiktir.
- Çoğu projede önce SFT, sonra yalnızca gerekliyse DPO.

İlgili sayfalar: [Araçlar Karşılaştırması](/llm/araclar/), [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/), [Benchmark'lar](/degerlendirme/benchmarklar/), [Hiperparametreler](/llm/hiperparametreler/).

## Kaynaklar ve İleri Okuma

- [TRL — DPO Trainer dokümantasyonu](https://huggingface.co/docs/trl/main/en/dpo_trainer) — `loss_type` seçenekleri, `beta` varsayılanı ve veri biçimleri için resmî başvuru.
- [TRL — PEFT Entegrasyonu](https://huggingface.co/docs/trl/main/en/peft_integration) — PEFT kullanırken ayrı referans model gerekmediği ve önerilen öğrenme oranları burada.
- [TRL — Ana Sayfa (Taxonomy bölümü)](https://huggingface.co/docs/trl/en/index) — hangi trainer çekirdek, hangisi deneysel: resmî ayrım.
- [Direct Preference Optimization (arXiv:2305.18290)](https://arxiv.org/abs/2305.18290) — DPO'nun orijinal makalesi (Rafailov ve ark., 2023).
- [Unintentional Unalignment: Likelihood Displacement (arXiv:2410.08847)](https://arxiv.org/abs/2410.08847) — "seçilen" cevabın olasılığının neden düşebildiği ve filtreleme çözümü.
- [Disentangling Length from Quality in DPO (arXiv:2403.19159)](https://arxiv.org/abs/2403.19159) — uzunluk istismarının mekanizması ve düzenlileştirme önerisi.
- [Is DPO Superior to PPO for LLM Alignment? (arXiv:2404.10719)](https://arxiv.org/abs/2404.10719) — DPO ile PPO'nun kapsamlı karşılaştırması.
- [STEP-DPO (arXiv:2406.18629)](https://arxiv.org/abs/2406.18629) — akıl yürütmede düz DPO'nun sınırları ve adım bazlı alternatif.
- [Constitutional AI (arXiv:2212.08073)](https://arxiv.org/abs/2212.08073) — RLAIF fikrinin temel çalışması (Anthropic).
- [Magpie (arXiv:2406.08464)](https://arxiv.org/abs/2406.08464) — hizalanmış bir modelden talimat verisi sentezleme yöntemi.
- [distilabel (GitHub)](https://github.com/argilla-io/distilabel) — sentetik veri ve tercih çifti üretme hattı kuran açık kaynak kütüphane.
- [Model collapse (Nature 631, 755-759, 2024)](https://www.nature.com/articles/s41586-024-07566-y) — sentetik veriyle döngüsel eğitimin dağılımı nasıl daralttığı.
- [SimPO (arXiv:2405.14734)](https://arxiv.org/abs/2405.14734) — referans model gerektirmeyen, uzunluk-normalize DPO varyantı.
- [AlpacaEval (GitHub)](https://github.com/tatsu-lab/alpaca_eval) — LLM yargıçla otomatik tercih karşılaştırması yapan açık araç.
