---
title: "Giriş: Bu Rehber Nedir, Kimler İçin?"
description: "Türkçe kaynak boşluğunu kapatmak için yazılan Model Eğitimi Rehberi'nin amacını, hedef kitlesini, kapsamını ve en verimli kullanım yollarını anlatıyoruz."
dogrulama: 2026-10-15
---

Türkçe kaynaklarda en sık karşılaşılan cümlelerden biri şu: "Kendi modelimi eğitmek istiyorum ama nereden başlayacağımı bilmiyorum." İngilizce tarafta binlerce blog yazısı, video ve açık kaynak depo varken Türkçe içerik çoğu zaman ya yüzeysel kalıyor ya da birbirinden kopuk tek tük örneklerle sınırlı kalıyor. **Model Eğitimi Rehberi** tam olarak bu boşluğu kapatmak için yazıldı: veri bulmaktan veri temizlemeye, model eğitmekten değerlendirmeye ve modeli bir uygulamaya bağlamaya kadar tüm süreci baştan sona, sıfırdan ve Türkçe anlatıyor.

Rehber; metin modellerinden (LLM) görsel üretim modellerine ve klasik makine öğrenmesine kadar geniş bir yelpazeyi kapsıyor. Amaç hiçbir konuyu "nasıl olsa herkes biliyor" varsayımıyla geçiştirmemek: her kavram önce sezgiyle, sonra gerçek parametreler ve sayılarla, en son da çalıştırılabilir örneklerle anlatılıyor.

:::tip[Rehberin üç ilkesi]
1. **Önce sezgi, sonra detay, en son pratik.** Her konu "bu neden var?" sorusuyla başlar.
2. **Gerçek sayılar.** "Küçük bir model" demek yerine "Qwen3-4B'nin ağırlıkları fp16'da yaklaşık 8 GB tutar" gibi somut değerler kullanılır.
3. **Uydurma yok.** Fiyat, sürüm ve model listesi gibi değişken bilgilerde "2026 itibarıyla" ibaresi geçer ve güncel değeri kontrol etmeniz önerilir.
:::

:::note[Kod bilgisi şart mı?]
Örneklerin çoğu Python ile yazıldı. Değişken, döngü ve fonksiyon kavramlarını duymuş olmak işinizi kolaylaştırır ama **şart değil**: her bölüm sıfırdan anlatır ve kod blokları satır satır açıklanır. Kodla hiç tanışmadıysanız en yumuşak başlangıç [Klasik Makine Öğrenmesi](/klasik-ml/temeller/) bölümüdür.
:::

## Rehber Kimler İçin Yazıldı?

Bu rehber belirli bir ön bilgi düzeyi varsaymaz. Kendinizi şu gruplardan birinde görüyorsanız doğru yerdesiniz:

- **Yeni başlayan meraklılar:** "Yapay zeka modelleri nasıl eğitilir?" sorusunun peşine düşmüş, henüz hiç model eğitmemiş kişiler.
- **Öğrenciler:** Bitirme projesi, tez veya ders kapsamında kendi verisiyle model eğitmesi gereken lisans ve lisansüstü öğrencileri.
- **Yazılım geliştiriciler:** Uygulamasına özel bir model katmak isteyen, Python bilen ama makine öğrenmesine yeni giren geliştiriciler.
- **Kendi modelini özelleştirmek isteyenler:** Hazır bir modeli kendi üslubu, alan bilgisi veya veri formatıyla uyarlamak isteyen bireyler ve küçük ekipler.
- **Türkçe çalışanlar:** İngilizce kaynak takip etmekte zorlanan ya da Türkçe veriyle uğraşan herkes. Veri bölümünde Türkçe'ye özel kaynaklar ve tuzaklar ayrıca ele alınıyor.

**Ön koşullar:** Temel Python bilgisi iyi olur ama kesin şart değil. Dosya ve klasör kavramına aşina olmanız yeterli; gerisini rehber adım adım kuruyor.

## "Model Eğitmek" Ne Demek? Beş Senaryo

Model eğitmek tek bir şey değil. Sektörde bu ifade en az beş farklı işi anlatmak için kullanılır ve hangisinden bahsedildiğini bilmek, doğru yolu seçmenin ilk adımıdır.

### 1. Hazır bir modeli ince ayar (fine-tuning) ile özelleştirmek

**En yaygın senaryo bu.** Elinizdeki büyük bir model (örneğin Qwen3-8B veya Gemma 3) zaten dil bilir; siz ona kendi verinizle "şu işi şu üslupla yap" demeyi öğretirsiniz. LoRA/QLoRA gibi yöntemlerle bu iş 8-12 GB VRAM'lik tek bir oyuncu ekran kartında bile yapılabilir. Rehberin ana omurgası bu senaryodur: [LoRA ve QLoRA](/llm/lora-qlora/) ve [SFT](/llm/sft/) sayfalarından başlayın.

### 2. Sıfırdan dil modeli ön eğitimi (pretraining)

Bir modeli rastgele ağırlıklardan başlatıp milyarlarca kelimelik bir veriyle dil öğretmek. GPT-4 sınıfı bir model bu yöntemle eğitilir ve maliyeti milyonlarca doları bulur. **Bunu bu rehberde yapmayacağız** — ama aynı sürecin küçük ölçekli versiyonunu (birkaç yüz MB metin, tek GPU, birkaç saat) görmek eğitim mantığını anlamak için paha biçilmezdir: [Ön Eğitim](/llm/pretraining/).

### 3. Görsel model eğitimi (LoRA)

Stable Diffusion tarzı difüzyon (diffusion) modellerine kendi görsellerinizle yeni bir stil, nesne veya karakter öğretmek. Metin tarafındaki LoRA ile büyük ölçüde aynı mantık: temel model donar, küçük bir ek katman eğitilir. [Difüzyon Temelleri](/gorsel/diffusion-temelleri/) ve [Görsel LoRA Eğitimi](/gorsel/lora-egitimi/).

### 4. Klasik makine öğrenmesi modeli

Tablo verisiyle (Excel benzeri satır-sütun verisi) tahmin modeli kurmak: ev fiyatı tahmini, müşteri kaybı öngörüsü, sınıflandırma. LLM'lerin gölgesinde kalmış görünse de gerçek dünyadaki kurumsal işlerin çoğu hâlâ bu modellerle çözülür — üstelik GPU'suz, saniyeler içinde. [Klasik ML Temelleri](/klasik-ml/temeller/) ve [İlk Model](/klasik-ml/ilk-model/).

### 5. Modeli yalnızca kullanmak (çıkarım / inference)

Modeli eğitmeden indirip çalıştırmak: sohbet etmek, özet çıkarmak, kod üretmek. Rehberin ana kapsamına girmez ama eğittiğiniz modeli çalıştırmak için zaten bu becerilere ihtiyacınız olacak: [Ollama](/kullanim/ollama/) ve [Sunma ve API](/kullanim/sunma-api/).

:::note[Bir cümlelik özet]
Bu rehber 1-4 arasındaki senaryoları sıfırdan öğretir; 5. senaryo için pratik sayfaları sunar.
:::

## Bu Rehberi Nasıl Kullanmalısınız? Üç Yol

Kitap gibi baştan sona okumak zorunda değilsiniz. Kendinize uygun yolu seçin:

### Yol 1 — Hızlı Başlangıç (1-2 günde ilk eğitim)

Amacınız en kısa sürede çalışan bir eğitim görmekse şu sırayı izleyin:

1. [VRAM Hesabı](/donanim/vram-hesabi/) — elinizdeki donanımla hangi model eğitilebilir?
2. [Bulut Seçenekleri](/donanim/bulut-secenekleri/) — GPU'nuz yoksa saatlik kiralama seçenekleri.
3. [Veri Formatları](/veri/veri-formatlari/) — eğitim verisi dosyası nasıl görünmeli?
4. [LoRA ve QLoRA](/llm/lora-qlora/) — neden tüm modeli değil de küçük bir eki eğitiyoruz?
5. [Adım Adım Eğitim](/llm/adim-adim-egitim/) — ilk eğitiminizi birlikte çalıştırıyoruz.
6. [Ollama](/kullanim/ollama/) — eğittiğiniz modeli kendi bilgisayarınızda konuşturun.

:::caution[Hızlı yolun bedeli]
Bu yolda attention, tokenizer ayrıntıları ve kayıp fonksiyonları gibi temelleri atlarsınız. Eğitim beklenmedik davrandığında (ki mutlaka olacak) nedenini anlamak için [Temeller](/temeller/transformer/) bölümüne geri dönmeniz gerekir.
:::

### Yol 2 — Sağlam Temel (baştan sona sırayla)

Makine öğrenmesini hakkıyla anlamak istiyorsanız sayfaları site menüsündeki sırayla okuyun: Başlangıç → Temeller → Donanım → Veri → LLM Eğitimi → Görsel Modeller → Klasik ML → Değerlendirme → Kullanım ve Paylaşım. Bu yol daha uzun sürer ama "kopyala-yapıştır" seviyesinden "kendi kararını verebilen" seviyesine çıkarır. Başlangıç noktanız: [Temel Kavramlar](/baslangic/kavramlar/).

### Yol 3 — İhtiyaca Göre Atlama

Tek bir hedefiniz varsa doğrudan ona gidin:

| Amacım | Okumam gerekenler |
| --- | --- |
| Türkçe sohbet asistanı eğitmek | [SFT](/llm/sft/), [LoRA ve QLoRA](/llm/lora-qlora/), [Türkçe veri kaynakları](/veri/veri-nereden-bulunur/) |
| Modeli kendi verimle özelleştirmek | [Kendi verini oluştur](/veri/kendi-verini-olustur/), [Veri temizleme](/veri/veri-temizleme/), [Adım adım eğitim](/llm/adim-adim-egitim/) |
| Görsel üretimde kendi stilim | [Görsel LoRA Eğitimi](/gorsel/lora-egitimi/) |
| Tablo verisiyle tahmin | [Klasik ML Temelleri](/klasik-ml/temeller/), [İlk Model](/klasik-ml/ilk-model/) |
| Model eğitimi kavramlarını anlamak | [Temel Kavramlar](/baslangic/kavramlar/), [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/) |

Hangi yöntemin size uyduğundan emin değilseniz [Yol Haritası](/baslangic/yol-haritasi/) sayfası bu kararı donanımınıza ve hedefinize göre veriyor.

## Bölümlerde Neler Var?

| Bölüm | Ne anlatıyor | İlk sayfa |
| --- | --- | --- |
| Başlangıç | Rehberin tanıtımı, temel kavramlar, yöntem seçimi | [Giriş](/baslangic/giris/) |
| Temeller | Transformer mimarisi, tokenizasyon, eğitim döngüsü | [Transformer](/temeller/transformer/) |
| Donanım | VRAM hesabı, yerel kurulum, bulut seçenekleri | [VRAM Hesabı](/donanim/vram-hesabi/) |
| Veri | Veri türleri, nereden bulunur, formatlar, temizleme, kendi verin | [Veri Türleri](/veri/veri-turleri/) |
| LLM Eğitimi | Ön eğitim, SFT, LoRA/QLoRA, DPO, araçlar, sorun giderme | [Ön Eğitim](/llm/pretraining/) |
| Görsel Modeller | Difüzyon temelleri, görsel LoRA eğitimi | [Difüzyon Temelleri](/gorsel/diffusion-temelleri/) |
| Klasik ML | Makine öğrenmesi temelleri, tablo verisiyle ilk model | [Klasik ML Temelleri](/klasik-ml/temeller/) |
| Değerlendirme | Kayıp ve metrikler, karşılaştırma testleri (benchmark) | [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) |
| Kullanım ve Paylaşım | LoRA birleştirme, nicemleme, Ollama, API, Hugging Face | [LoRA Birleştirme](/kullanim/lora-birlestirme/) |
| Kaynaklar | Sık sorulan sorular, sözlük, faydalı linkler | [SSS](/kaynaklar/sss/) |

## Terimler ve Güncellik Hakkında İki Not

- **İngilizce terimler:** Her önemli İngilizce terim, ilk geçtiği yerde parantezle verilir — "ince ayar (fine-tuning)" gibi — ve sonrasında tutarlı biçimde kullanılır. Sektörde aynı terimin farklı Türkçe karşılıkları dolaşımda olabilir (ör. nicemleme yerine "kuantizasyon"); bu rehberde tercih edilen karşılıkları her zaman [Sözlük](/kaynaklar/sozluk/) sayfasından kontrol edebilirsiniz.
- **Güncellik:** Rehber 2026 itibarıyla ekosistemi yansıtır. Model sürümleri, bulut fiyatları ve araç sürümleri hızlı değişir; değişken bilgilerin yanında "2026 itibarıyla" notu göreceksiniz. Kritik kararlardan (model seçimi, bulut satın alma) önce resmi kaynaklardan doğrulama yapmanızı öneririz.

## Gerçekçi Beklentiler

### Neler öğreneceksiniz?

- Kendi verinizle hazır bir modeli **özelleştirmeyi** (LoRA/QLoRA ile ince ayar).
- Veri toplama, temizleme, biçimlendirme ve **token bütçesi** hesaplamayı.
- Eğitimi **izlemeyi ve değerlendirmeyi**: kayıp eğrileri, erken durdurma, karşılaştırma testleri.
- Eğittiğiniz modeli **nicemleyip (quantization)** yerel bilgisayarınızda çalıştırmayı, API olarak sunmayı ve Hugging Face'te paylaşmayı.
- Tablo verisiyle klasik makine öğrenmesi modelleri kurmayı ve görsel modellere LoRA eğitmeyi.

### Kapsam dışında kalanlar

- **Dağıtık eğitim:** Onlarca GPU'yu aynı anda koordine eden megatron tarzı altyapılar. Tek GPU ve tek düğüm odaklıyız.
- **Sıfırdan sınır (frontier) model eğitmek:** GPT-4 sınıfı modellerin ön eğitimi milyonlarca dolarlık bir bütçe ve binlerce GPU gerektirir; küçük ölçekli öğrenme denemeleri hariç bu işe girmiyoruz.
- **Araştırma düzeyinde matematik:** Attention'ın türevleri, optimizasyon teorisi gibi konular kavramsal düzeyde anlatılır, akademik derinlikte değil.
- **Veri etiketleme operasyonları:** Veri toplamanın mühendislik tarafını anlatıyoruz; büyük ölçekli etiketleme ekipleri kurmak ayrı bir uzmanlık alanı.

### Ne kadar sürer?

Rehberin tümünü okumak birkaç saat ile birkaç hafta arasında değişir (yoğunluğunuza bağlı). İlk LoRA eğitiminizi genellikle **ilk gün** içinde çalıştırabilirsiniz; ancak iyi bir veri seti hazırlamak, deneme-yanılma dahil, çoğu zaman eğitimin kendisinden uzun sürer. Sabırlı olun: bu rehberdeki en değerli beceri, veri hazırlamaktır.

## Öğrenirken En Sık Yapılan 5 Hata

Bu hataların hepsi rehber boyunca tekrar tekrar vurgulanıyor; baştan bilmekte fayda var:

1. **Modelden başlamak, veriden başlamamak.** Herkes "hangi modeli eğitsem?" diye sorar; oysa projelerin kaderini veri belirler. Önce [Veri](/veri/veri-turleri/) bölümünü anlayın.
2. **Tek seferde dev hedef koymak.** "ChatGPT rakibi yapacağım" yerine "üslubumu taklit eden küçük bir model eğiteceğim" gibi ölçülebilir, küçük hedeflerle başlayın; her başarı bir sonrakinin altyapısıdır.
3. **Donanımı sonradan düşünmek.** Model seçimi donanımdan bağımsız yapılamaz; ilk adım her zaman [VRAM Hesabı](/donanim/vram-hesabi/) olmalı.
4. **Değerlendirmeyi atlamak.** "Çıktılar güzel görünüyor" bir ölçüm değildir. Karşılaştırma testleri ve kayıp metrikleri olmadan iyileşme de bozulma da görülemez: [Değerlendirme](/degerlendirme/loss-ve-metrikler/).
5. **Kodu anlamadan çalıştırmak.** Hazır notebook'lar harika bir başlangıçtır ama her satırın ne yaptığını anlamazsanız hata çıktığında eliniz kolunuz bağlanır. Bu rehberdeki kod blokları bu yüzden açıklamalıdır.

## Yardım İhtiyacında

Eğitim sırasında bir hata mesajıyla karşılaştığınızda paniklemeyin: [Sorun Giderme](/llm/sorun-giderme/) sayfası en sık görülen hataları ve çözümlerini listeler. Kavram karmaşasında [Sözlük](/kaynaklar/sozluk/), sık sorulan sorularda [SSS](/kaynaklar/sss/), araç ve kaynak arayışında [Faydalı Linkler](/kaynaklar/faydali-linkler/) yanınızda.

Hazırsanız iki rota var: kavramları sırayla öğrenmek için [Temel Kavramlar](/baslangic/kavramlar/), doğrudan karar vermek için [Yol Haritası](/baslangic/yol-haritasi/). Ana sayfadaki etkileşimli yöntem seçiciyi de deneyebilirsiniz: [Ana sayfa](/).
