---
title: "Lisans, Kişisel Veri ve Model Kartı"
description: "Eğittiğiniz modeli yayınlamadan önce lisans zinciri, kişisel veri taraması ve model kartı alanları — bu rehberin kendi yerel yığınının ve kendi veri hattının 2026-10-17 tarihli ölçülmüş denetimi."
dogrulama: 2026-10-19
---

Bir modeli eğitmek bittiğinde iki ayrı soru başlar: **bunu yapmaya izinli miyim** ve **içinde başkasının verisi var mı**. İkisi de "kodu çalıştırdım, loss düştü" ile cevaplanmaz. Bu sayfa o iki soruyu bu makinede ölçüyor — denetlenen şey rastgele bir depo değil, **bu rehberin kendi örnek yığını ve kendi yayınladığı metinler**.

:::note[Künye: ne nerede ölçüldü]
- Lisans envanteri: `ornekler/lisans-ve-gizlilik/lisans_envanter.py` → kayıt `ornekler/lisans-ve-gizlilik/cikti/lisans-envanter.txt` (koşum 2026-10-17 14:22:37 → 14:22:38, Ollama 0.40.4 — makinenin sunucusu 2026-10-19'da 0.40.6, envanter o sürümde yeniden alınmadı, `http://127.0.0.1:11434`).
- Kişisel veri denetimi: `ornekler/lisans-ve-gizlilik/pii_denetim.py` → kayıt `cikti/pii-kaydi.txt` (koşum **14:21:44 → 14:22:36**). Çıkarım isteği yok, ağ erişimi yok, tohum 20261017.
- Denetlenen maskeleyici: `ornekler/veri-temizleme/atolye.py` içindeki `pii_maskele` ve düzenli ifade sabitleri — yani Örnek 2'de size öğretilen araç.
- **Bu sayfanın kendi metni de taranan kümenin içinde.** Sayıları buraya yapıştırdıktan sonra betiği yeniden koşarsanız "yayındaki sayfalar" satırı, bu sayfa uzadığı kadar büyür: tablo aşağıdaki saat damgasıyla biten koşumun anlık görüntüsüdür, sabit bir gerçek değil. Denetimin kendi klasörü (`ornekler/lisans-ve-gizlilik/`) sayımdan çıkarıldı ki betikler kendi anahtar sözcüklerini ve yarım yazılmış kendi logunu saymasın.
- Dış kaynaklı her iddia (Hugging Face kart alanları, lisans metinleri) **son doğrulama: 17 Ekim 2026** tarihiyle verildi. O tarihten sonra bir lisans değişmiş olabilir; bu sayfa değişmez bir referans değil, bir anlık görüntüdür.
- Bu sayfa hukuki tavsiye vermez. Ürüne dönüşecek bir kullanımda bir hukuk uzmanına danışın.
:::

## Birinci Bulguyu Baştan Söyleyelim: Bu Sitenin Modeli Araştırma Lisanslı

Örnek 5, 6, 7 ve 8 ile sitedeki bütün ölçüm kafesleri aynı modeli kullanıyor: `qwen2.5:3b-instruct-q4_K_M`. Ollama'nın bu etiket için dağıttığı Modelfile'daki `LICENSE` alanı, Apache-2.0 değil **"Qwen RESEARCH LICENSE AGREEMENT"** metnini taşıyor — 7.387 bayt, 54 satır. Kayıttan, metnin kendi cümleleri:

- Tanım maddesi: `"Non-Commercial" shall mean for research or evaluation purposes only.`
- Verilen hak: `... to use, reproduce, distribute, copy, create derivative works of, and make modifications to the Materials FOR NON-COMMERCIAL PURPOSES ONLY.`
- Ticari taraf: `If you are commercially using the Materials, you shall request a license from us.`
- Türev model koşulu: `If you use the Materials or any outputs or results therefrom to create, train, fine-tune, or improve an AI model that is distributed or made available, you shall prominently display "Built with Qwen" or "Improved using Qwen" in the related product documentation.`
- Atıf dosyası: dağıtılan her kopyanın içine `"Notice"` adlı bir metin dosyası koymanız ve içinde Alibaba Cloud atıf cümlesinin durması isteniyor.
- Ayrıca: değiştirilmiş dosyaların "prominent notice" taşıması, ihracat kontrolü beyanı ve üçüncü kişi iddialarında tazmin yükümlülüğü.

**Bu sizin için ne demek:** bu rehberdeki örnekleri kendi bilgisayarınızda eğitim/ölçüm amaçlı koşmak lisansın açıkça izin verdiği alan. Çıktıyı bir ürüne koyacaksanız ya Alibaba Cloud'dan lisans istemeniz ya da taban modeli değiştirmeniz gerekir. LoRA eğitip yayınlarsanız `4.b` maddesi size kartta bir ibare yazdırır.

Aynı modelin Hugging Face kartındaki `license` alanı `other`, `license_link` alanı depo içindeki `LICENSE` dosyasını gösteriyor — yani kart ile paketleme çelişmiyor, ikisi de aynı özel lisansa işaret ediyor.

## Lisans Ailesi Değil, Depodaki Dosya Ölçülür

Qwen ailesinin beş deposunda kart alanına bugün baktık (`cardData.license`, HF API'si, son doğrulama 17 Ekim 2026):

| Depo | Kart alanı | Anlamı |
| --- | --- | --- |
| `Qwen/Qwen2.5-1.5B-Instruct` | `apache-2.0` | serbest |
| `Qwen/Qwen2.5-3B-Instruct` | `other` + `LICENSE` bağlantısı | Qwen Research, ticari değil |
| `Qwen/Qwen2.5-7B-Instruct` | `apache-2.0` | serbest |
| `Qwen/Qwen2.5-32B-Instruct` | `apache-2.0` | serbest |
| `Qwen/Qwen3-8B` | `apache-2.0` | serbest |

Ailenin içinde **tek bir boyut** farklı lisanslı — ve o boyut, CPU'da çalışabildiği için bu rehberin seçtiği boyut. "Qwen Apache'lidir" ya da "Llama koşulludur" gibi aile genellemeleri, tam da işin ucunun değdiği yerde yanlış çıkabiliyor. Kural: **lisansı model ailesinden değil, kullanacağınız depodan ve paketlenmiş hâlinin içinden okuyun.**

:::note[Lisans Alanı Dolu Olması Lisansın Doğru Olduğu Anlamına Gelmez]
Envantere giren üç yerel modelin Modelfile lisans alanı:

| Model | Lisans başlığı | Metin | Şablon artığı |
| --- | --- | --- | --- |
| `qwen2.5:3b-instruct-q4_K_M` (3,1B, Q4\_K\_M, 1.930 MB) | Qwen RESEARCH LICENSE AGREEMENT | 7.387 bayt / 54 satır | yok |
| `bge-m3` (566,7M, F16, 1.158 MB) | MIT License | 1.068 bayt / 21 satır | **`[year]` ve `[fullname]` olduğu gibi duruyor** |
| `nomic-embed-text` (137M, F16, 274 MB) | Apache License | 11.357 bayt / 201 satır | Apache'ın ek bölümündeki şablon parantezi (tasarım gereği) |

`bge-m3` satırına dikkat: telif satırında yıl ve telif sahibi yerinde köşeli parantezli şablon duruyor. Hak sahibi yazılmamış bir MIT metni, hukuken "MIT demeye çalışmış ama bildirmemiş" durumudur — yukarıdaki tabloda BAAI'nin kendi kartı `mit` diyor, yani sorun dağıtım paketinin kopyalama özensizliği. Çıkarılacak ders: **lisans metninin varlığı ile lisansın tanımlı olması farklı şeyler.** Nicemlenmiş/GGUF türevlerde lisans alanı çoğu zaman otomatik doldurulur ve çoğu zaman eksik doldurulur.
:::

## Türevin Lisansı: İnce Ayar, Birleştirme, Nicemleme

Üç kural, üçü de yukarıdaki metinlerin doğrudan okuması:

1. **Türev, taban modelden daha serbest olamaz.** Apache-2.0 tabanlı bir LoRA'yı MIT ile yayınlamak metnin izin verdiğinden fazlasını vaad etmektir; Qwen Research tabanlı bir ince ayarı Apache-2.0 ile yayınlamak ise açık ihlal. [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/) sayfasındaki uyum kutusu bu kuralı anlatıyor; burada ölçülen, kuralın hangi metinden doğduğu.
2. **Nicemleme lisansı düşürmez.** Q4\_K\_M bir kopyadır, yeni bir eser değil — envantere giren `qwen2.5:3b-instruct-q4_K_M` satırının kendi bunu gösteriyor: Q4\_K\_M paketi Research lisansını olduğu gibi taşıyor. [Nicemleme](/kullanim/quantization/) ve [LoRA Birleştirme](/kullanim/lora-birlestirme/) sayfalarındaki teknik adımların hukuki sonucu budur.
3. **Birleştirme en kısıtlayıcı olanı götürür.** İki taban modelden ağırlık ortalamasıyla üretilen bir model, ikisinin de koşullarına aynı anda uymak zorundadır; Apache-2.0 ile Research lisansını birleştirirseniz ticari kullanım Research tarafının yasağı altında kalır.

Hugging Face kart alanları bu zinciri yapısal olarak taşımak için var (bugünkü belge, son doğrulama 17 Ekim 2026): `base_model` ve `base_model_relation` (Hub ilişkiyi `adapter` / `merge` / `quantized` / `finetune` olarak kendisi çıkarıyor, elle de yazılabiliyor), `license`, özel lisans için `license: other` + `license_name` + `license_link`, `datasets`, `pipeline_tag`, `library_name`, `tags`.

## Kişisel Veri: Tarayıcıyı Denetledik

`ornekler/veri-temizleme/atolye.py` içindeki maskeleyici dört desene bakıyor: e-posta, telefon, IBAN ve 11 haneli TCKN adayı. Bugün iki şeyi ayırdık: **araç kendi kapsamındaki veriyi buluyor mu** ve **araç kendi kapsamını biliyor mu**.

### Kalibrasyon kümesi: 30 vaka, üç tür etiket

Elle yazılmış 30 sentetik Türkçe cümle. Her vaka ya POZİTİF (kişisel veri, araç görmeli), ya KUYRUK (kişisel veri değil, araç işaretlememeli), ya da KÖR NOKTA (kişisel veri, ama aracın kapsamı dışında).

| Sonuç | Sayı | Okunuşu |
| --- | --- | --- |
| Kapsam içi veri yakalandı | 12 / 12 | pozitif vakaların tamamı: tutma oranı 1,00 |
| Kapsam içi veri kaçırıldı | 0 | bu dilimde kayıp yok |
| Yanlış pozitif (kuyruk) | 1 / 9 | işaretlenen tek vaka: `TR` + 24 özdeş hane |
| Doğru red | 8 / 9 | sağlamasız TCKN, sürüm numarası, kısa TR kodu... |
| Kör nokta (kişisel veri, görünmüyor) | 9 / 9 | ad-soyad + adres, doğum tarihi, GPS koordinatı, plaka, sağlık cümlesi, obfuscate edilmiş e-posta, ayraç gruplu TCKN (2 biçim), ikişerli gruplu telefon |

İki sayı aynı şeyi söylüyor: araç **biçimsel** veride başarılı, **anlamsal** veride hiç yok. 12/12 tutma oranı "kütlemiz temiz" demek değildir — çünkü kaçırılan 9 vaka kişisel verinin ta kendisi.

### Biçim mi, geçerlilik mi?

| Denenen | Yalın düzenli ifade | Sağlama/hesap ile |
| --- | --- | --- |
| `12345678901` (11 hane, sipariş no) | TCKN sayıyor | sağlama tutmuyor → reddediliyor |
| `TR111111111111111111111111` | IBAN sayıyor | mod-97 tutmuyor |
| `TR680001234567890123456789` (hesaplanmış kontrol hanesi) | IBAN sayıyor | mod-97 tutuyor |

Sağlama adımları maskeleyicinin içinde zaten var (TCKN tarafı), IBAN tarafında **yok**. Depo taramasında bulunan yedi IBAN biçimli vuruşun **biri** mod-97'i tutuyor; o vuruş da bu sayfanın yukarıdaki kalibrasyon tablosunda alıntıladığım sentetik değer. Yani taramayı kirleten şey tam olarak denetimin kendi raporu. Gerçek bir IBAN yok; ama tarayıcı `TR111…` gibi biçimen bir diziyi de, mod-97'i tutmayan `TR00 0000 0000 0000 0000 0000 01`'i de (Örnek 3'ün eğitim kütlesinde geçiyor) IBAN sayıp maskelerdi.

### Ayraç silmenin faturası

Kör noktalardan üçü (iki TCKN biçimi ve bir telefon) "rakamların arasına boşluk/nokta girmiş" vakaları. Ayraçları silip rakamları birleştirince: kalibrasyonda **3 kör nokta yakalamaya döndü, 6 kör nokta olduğu yerde kaldı** (ad, adres, doğum tarihi, koordinat, plaka, sağlık, sözcüklerle yazılmış e-posta).

Deponun tümünde aynı hamle bedel değiştiriyor: TCKN adayı **34 → 57**, sağlaması tutan **8 → 8**, telefon vuruşu **78 → 107**, IBAN **7 → 7**. Yeni hiçbir gerçek kimlik numarası bulunmadı; 23 yeni aday ve 29 yeni telefon vuruşu eklendi. Sağlama filtresi aday artışını susturabiliyor, telefon/IBAN artışını susturamıyor. **Sonuç: ayraç silmek, yakalama oranını artıran bir kurnazlık değil, yanlış maske üreten bir trade-off; ancak gerçek kişisel veride (grup grup yazılmış kimlik numaraları) tek başına 3/9 kazandırıyor.**

### Kendi depomuzun taraması

| Grup | Dosya | Karakter | TCKN adayı | Sağlamalı TCKN | E-posta | Telefon | IBAN | mod-97 tutan |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Yayındaki sayfalar (md + mdx) | 58 | 862.300 | 4 | 3 | 4 | 1 | 3 | 1 |
| Örnek veri kümeleri (jsonl) | 3 | 47.049.122 | 20 | 0 | 149 | 68 | 1 | 0 |
| Koşum günlükleri (txt) | 33 | 192.645 | 4 | 4 | 4 | 4 | 0 | 0 |
| Betikler ve README | 28 | 274.187 | 6 | 1 | 6 | 5 | 3 | 0 |
| **TOPLAM** | **122** | **48.378.254** | **34** | **8** | **163** | **78** | **7** | **1** |

Koşum 12,68 sn, tek süreç, CPU. Dört satırın okunuşu:

- **Yalın `\d{11}` kullansaydık:** 34 adaydan sağlaması tutan 8 olduğu için (oran 0,235) **26 yanlış maske** üretirdik. Sağlamalı 8 vuruşun **sekizi de** bu sitenin bilerek koyduğu demo değeri `10000000146`: 3'ü yayındaki iki sayfada (bu sayfa + Örnek 2 sayfası), 4'ü Örnek 2'nin koşum günlüklerinde (ikisi düzeltme öncesi yedekte, ikisi yeni koşumda), 1'i maskeleyicinin kendi test satırında (`atolye.py:234`). Yani bu depoda gerçek bir kimlik numarası yok — ama düzenli ifade bunu bilmiyor, sağlama algoritması biliyor.
- **Örnek 3'ün eğitim kütlesi** taramanın gövdesini oluşturuyor: `egitim.jsonl` tek başına 43,42 M karakter, **130 e-posta ve 61 telefon** vuruşu; `test.jsonl` 2,31 M karakter, 19 e-posta ve 7 telefon. Bunlar `AlicanKiraz0/Turkish-SFT-Dataset-v1.0` üzerinden gelen, büyük kısmı `@example.com` / `+90 555 ...` kalıbında **sentetik görünen** iletişim bilgileri. Örnek 3'ün hazırlık hattı (`hazirla.py`) maskeleme adımı **içermiyor** — çünkü o örnek temizliği değil SFT formatına geçişi öğretiyor. Kendi verinizle çalışıyorsanız aynı kütle Örnek 2 hattından geçirilmelidir.
- **Örnek 2'nin kendi çıktısı temiz:** `temiz_veri.jsonl`'da e-posta ve telefon vuruşu **sıfır**; dört TCKN adayı var, sağlaması tutan yok. Ayrıca dosyada **2 hazır maske token'ı** (`[E-POSTA]` gibi) duruyor — yani maskeleyici kendi izini de görüyor; eğitim kütlesinde bu tokenlardan 4 tane var.
- **56/58 sayfada sıfır biçim vuruşu** var; vuruş alan iki sayfa kişisel veri konusunu *anlatan* sayfalar: Örnek 2 sayfası (4 vuruş, 2 sağlamalı TCKN) ve bu sayfa. Denetimin sonucu, denetlenen kümenin içine girdi — bu sayfa alıntıladığı desenlerin kendisini taşıdığı için taramada vuruş sayılıyor.
- Taranan 83 dosyada (py/md/mdx; `__pycache__`, `cikti/` ve denetimin kendi klasörü dışarıda) **32 dosya** en az bir lisans sözcüğü taşıyor; tam sözcük sayımı logda. Örnek 6'nın betiği `VIKI_LISANS` sabitinde Vikipedi'nin CC BY-SA atıf şartını taşıyor ve her koşumun sonuna basıyor.

## Hattımızda Bulduğumuz Gerçek Hata

Denetimin bulduğu şey tarayıcının değil, **boru hattının** hatasıydı ve düzeltildi. `atolye.py` normalizasyonu `talimat`, `giris`, `cikti` üç alanına uyguluyor; PII maskelemeyi ise yalnızca `talimat` ve `cikti`'ye uyguluyordu. SFT yazıcısı `giris` alanını `"Bağlam: "` olarak kullanıcı mesajına gömdüğü için, maskelenmiş bir hattın **yayınlanmış çıktısında** maskelenmemiş bir e-posta kalıyordu. Düzeltme (`atolye.py:263-270`) tek satır: maskeleme döngüsüne `giris` alanını eklemek.

| Koşum | `rapor.json` → `pii_maskeleme` | Yayınlanmış çıktıda kalan e-posta vuruşu | Diğer sayılar |
| --- | --- | --- | --- |
| 2026-10-15 (düzeltme öncesi) | 1 | 1 | 3.000 → 2.747, 5.732 düzeltilen alan |
| 2026-10-17 (düzeltme sonrası) | **2** | **0** | 3.000 → 2.747, 5.732 düzeltilen alan (birebir aynı) |

Aynı kaydın satırı, öncesi ve sonrası:

```text
Bağlam: Ad: John Doe Telefon: (123) 456-7890 E-posta: jdoe@email.com Şu anki rolü: ...
Bağlam: Ad: John Doe Telefon: (123) 456-7890 E-posta: [E-POSTA] Şu anki rolü: ...
```

:::caution[Bu iki satır maskeleme başarısı değil, maskeleme sınırıdır]
Satırın maskelenmiş hâli hâlâ kişisel veri taşıyor. **Ad: John Doe** hiçbir düzenli ifadenin işi değil. **(123) 456-7890** ABD biçiminde yazıldığı için `5xx` / `2xx-4xx` kalıbındaki Türk telefon kuralının kapsamı dışına düşüyor. Maske sayacı 1'den 2'ye çıktı, satır temizlenmedi. Kendi projenizde maske sayısını başarı ölçüsü yapmayın; ölçüsü **kapsam listesidir**: hangi veri türlerini taradığınızı ve hangilerini tarmadığınızı — belgeleyin.
:::

:::note[Aynı ad, iki anlam]
Çıktıda "John Doe" iki kayıtta geçiyor: birinde bir iletişim bloğunun parçası, diğerinde bir hikâye karakteri. İkincisi kişisel veri değil, biri öyle görünüyor; bu ayrımı otomatik yapan kural yok. Ölçekteki kör nokta sınıfının neden "kapsam dışı" olarak *yazılarak* bildirilmesi gerektiği tam olarak bu.
:::

## Kişisel Veri Tarafında Hukuki Çerçeve: Ne Bilinmeli

Türkiye'de işin adı KVKK (6698 sayılı Kanun). Bu sayfada kanun maddelerinin metnini doğrulanmış gibi aktarmıyorum — kurumun sitesi bugün yalnızca gezinme menüsü döndürdü, madde metni bu denetimde **doğrulanmadı**. Bilmeniz gereken yapı şu (bu sitede [Veri Nereden Bulunur](/veri/veri-nereden-bulunur/) sayfasında doğrulanmış hâliyle işlendi):

- İsim, TC kimlik numarası, telefon, e-posta, adres, konum ve sağlık bilgisi **kişisel veridir**; sağlık, inanç, biyometri gibi türler daha sıkı ölçütlerle **özel nitelikli** sayılır.
- Amaçla sınırlılık ve veri minimizasyonu: eğitim için ihtiyacınız olmayan alanı baştan toplmayın. Maskeleme, topladıktan sonra yapılan ikincil bir temizliktir.
- Modeli eğittiğiniz verideki kişisel veri, modelin *ağırlıklarına* da sızabilir — silme/idare etme talepleri açısından "veriyi maskeledik, bitti" demek yeterli olmayabilir. Çıkarma (machine unlearning) bu rehberde **doğrulanmış bir yöntem olarak sunulmuyor**; eğitim verinizi küçültmek ve temiz tutmak bugün için elimizdeki gerçek kontroldür.
- Kurumun ve Kanun'un güncel metnini kendiniz okuyun: [kvkk.gov.tr](https://www.kvkk.gov.tr/). Bu sayfa genel bilgilendirmedir.

## Model Kartı Yazmak: Okuma Listesinin Karşı Tarafı

[Değerlendirme sayfalarındaki](/degerlendirme/benchmarklar/) "model kartı okuma kontrol listesi" alıcı tarafıydı. Burası satıcı tarafı — Hugging Face'in model kartı belgesinden, bugün okundu (son doğrulama 17 Ekim 2026): kart, depo içindeki `README.md` dosyasıdır; üstünde YAML metadata, altında metin bulunur. Belge kartın şunları anlatmasını bekliyor: modeli, **amaçlanan kullanım ve sınırlamaları** (yanlılık ve etik boyutlar dahil — atıf: Mitchell vd., arXiv:1810.03993), eğitim parametreleri ve deneysel bilgi, **kullanılan veri setleri**, değerlendirme sonuçları. Metadata tarafında ölçülebilir/dolay alanlar: `license` (özel lisans için `other` + `license_name` + `license_link`), `base_model` + `base_model_relation`, `datasets`, `language`, `pipeline_tag`, `library_name`, `tags` (gerekirse `not-for-all-audiences`), `model-index` ile yapılandırılmış değerlendirme sonuçları ve CO2 salımı bölümü.

Küçük ama kritik iki ayrıntı: **Ağustos 2024 sonrası açılan depolarda `library_name: transformers` alanı otomatik varsayılmıyor** — siz yazmazsanız kart eksik görünür — ve `datasets` alanı doluysa model sayfası "Datasets used to train:" satırını kendisi basıyor; yani lisans zincirinizin ikinci halkası kartın içinde görünür hâle gelir.

Yukarıda lisansını ölçtüğümüz taban model — `Qwen/Qwen2.5-3B-Instruct` — üzerinden giden bir ince ayar için doldurulmuş kart başlığı. Madde 1'in kuralı burada uygulanmış hâlinde: **kart `apache-2.0` diyemez**, çünkü taban Research lisanslı.

```yaml
---
language: tr
license: other                       # taban modelin lisansından daha serbest olamaz
license_name: qwen-research-license  # aile genellemesi değil, ölçülen metin
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
base_model: Qwen/Qwen2.5-3B-Instruct
base_model_relation: finetune
datasets:
  - AlicanKiraz0/Turkish-SFT-Dataset-v1.0
library_name: transformers           # 2024-08 sonrası depolar için elle yazılmalı
pipeline_tag: text-generation
tags: [sft, turkish]
---
```

Kartın metin tarafına yazılacak üç şey, bu sayfanın ölçümlerinden doğrudan çıkıyor: (1) kişisel veri taramasının **kapsam listesi** — hangi türleri taradınız, hangilerini taramadınız; (2) tarayıcının **kalibrasyon sonucu** — 12/12 tutma, 9/9 kör nokta gibi kendi sayılarınız; (3) lisans zinciri — taban model, her veri seti ve atıf dosyası (`Notice`, CC BY-SA kaynak gösterimi). Bu örnekte ayrıca `4.b` maddesinin ibaresi var: dağıtılan türev için dokümanda **"Built with Qwen" / "Improved using Qwen"**.

## Yayın Öncesi Kontrol Listesi

- [ ] Taban modelin **lisans metnini** okudum; ticari kullanım, isimlendirme ve atıf koşullarını not aldım.
- [ ] Kullandığım **her veri setinin** lisansını tek tek yazdım; NC ve SA koşulları olan varsa çıktıma yansıttım.
- [ ] Türevimin lisansını taban modelden **daha serbest** tanımlamadım.
- [ ] Nicemlenmiş/birleştirilmiş dosyaların içindeki lisans alanını açıp baktım; şablon artığı (`[year] [fullname]`) var mı kontrol ettim.
- [ ] Araştırma lisanslı bir tabanla ürüne gideceksem lisans sahibine yazmam gerektiğini biliyorum.
- [ ] Kişisel veri taramasını **tüm alanların** üzerinde koşturdum (talimat + girdi + çıktı + metadata).
- [ ] Tarayıcının kapsam listesini yazdım: neyi tarıyor, neyi taramıyor.
- [ ] TCKN/IBAN için sağlama/hesap filtresi kullandım; yalın rakam desenine güvenmedim.
- [ ] Model kartında `license`, `base_model`, `datasets`, `library_name`, `pipeline_tag` ve değerlendirme sonuçları dolu.
- [ ] Kartın sınırlamalar bölümü dürüst: hangi dil, hangi görev, hangi ölçümde ne kadar.
- [ ] Varsa değerlendirme sonuçlarının **hangi ayarla** alındığı yazılı (sıcaklık, `num_predict`, tohum) — bkz. [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/).
- [ ] Atıf zorunlu ise (CC BY-SA gibi) kaynak gösterimi hem kartta hem çıktı dosyalarında var.
- [ ] Kişisel veri barındırabilecek bir kütleyle çalıştıysam: hukuki dayanağım, saklama yerim ve silme yolum yazılı.

## Bu Denetim Neyi Göstermiyor

:::caution[Sınırlar — sayıların okuma biçimi]
- **Kalibrasyon kümesi elle yazıldı, 30 vakalık küçük bir örneklem.** Kör nokta sayıları tarayıcının *kapsamını* gösterir, Türkçe metindeki gerçek sıklığını göstermez; kesinlik aralığı hesaplanmadı (ÖLÇÜLMEDİ).
- **POZİTİF vakaların kimlik numaraları sağlama fonksiyonuyla üretildi.** Yani 12/12 tutma oranı doğrulayıcının kendi doğruluğunu değil, regex ile sağlama arasındaki davranışı ölçer.
- **Depo taraması bu projeye özgü.** 48,4 M karakterin büyük kısmı sentetik/üretik metin; gerçek bir müşteri kütlesinde sayılar bu kadar temiz çıkmaz.
- **Lisans envanteri bu makinedeki üç modeli kapsıyor.** Başka bir etiket, başka bir sürüm, başka bir dağıtım kanalı farklı bir lisans alanı taşıyabilir.
- **Dış iddialar anlık görüntüdür.** HF kart alanları ve lisans metinleri 17 Ekim 2026'da okundu; lisanslar değişebilir.
- **Hukuki değerlendirme yapılmadı.** KVKK madde metinleri bu denetimde doğrulanmadı; ticari kullanım planında uzman görüşü gerekir.
:::

## Kendi Makinenizde Koşun

```bash
# lisans envanteri (Ollama çalışıyor olmalı; çıkarım isteği gitmez, yalnızca /api/tags + ollama show)
cd ornekler/lisans-ve-gizlilik
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py > cikti/lisans-envanter.txt 2>&1

# aynı bölümün Ollama'sız hâli (yalnız depo sayımı)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py --depo > cikti/depo-sayimi.txt 2>&1

# kişisel veri denetimi: a=kalibrasyon, b=depo taraması, c=ayraç silme
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u pii_denetim.py --kol hepsi > cikti/pii-kaydi.txt 2>&1
```

İki betik de kendi klasörünü taramanın dışarıda tutar: `lisans_envanter.py` sayım
anahtar sözcüklerini kendi listesinde gördüğü için, `pii_denetim.py` ise içinde
sentetik kimlik numaraları olan kendi logunu (yazıldığı sırada yarım hâlde)
okumamak için. Kendi verinizle: `pii_denetim.py` içindeki `HEDEF_GRUPLARI`
sözlüğüne veri dizininizi ekleyin; `--kol a` kısmına kendi kuyruk ve kör nokta
vakalarınızı yazın. Kapsam listesi olarak işe yarayan şey, kendi verinizde hangi
türlerin göründüğüdür.

## Kaynaklar ve ileri okuma

- [Ollama Modelfile referansı](https://docs.ollama.com/modelfile) — `LICENSE` alanının pakette nasıl taşındığı.
- [Qwen2.5-3B-Instruct kartı](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) ve deposundaki [LICENSE dosyası](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE) — ölçtüğümüz araştırma lisansının kaynağı.
- [Hugging Face Hub — Model Cards](https://huggingface.co/docs/hub/model-cards) — kart alanlarının resmî listesi (`license`, `base_model`, `datasets`, `model-index`).
- [Meta Llama 3 Community License](https://github.com/meta-llama/llama3/blob/main/LICENSE) — 700 milyon aylık aktif kullanıcı eşiği, türev adlandırma ve atıf cümlesi koşulları.
- [Gemma Terms of Use](https://ai.google.dev/gemma/terms) — ticari kullanım serbest, yasaklı kullanım politikası ve sözleşmenin kopyayla birlikte dağıtılması.
- [Mitchell vd., Model Cards for Model Reporting (arXiv:1810.03993)](https://arxiv.org/abs/1810.03993) — kart fikrinin ortaya çıktığı bildiri.
- [Gebru vd., Datasheets for Datasets (arXiv:1803.09010)](https://arxiv.org/abs/1803.09010) — veri kartının karşı tarafı: veri setini belgeleme şablonu.
- [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) — Örnek 6'nın Vikipedi kütlesinin atıf/türev koşulu.
- [KVKK Kurumu](https://www.kvkk.gov.tr/) — kişisel veri mevzuatının resmî adresi.
