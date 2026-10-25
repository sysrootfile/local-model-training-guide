---
title: "Temel Kavramlar: Model Eğitiminin Sözlüğü"
description: "Yapay zekadan LoRA'ya, eğitim döngüsünden nicemlemeye: model eğitiminde karşınıza çıkacak 30 temel kavramı analojiler ve örneklerle açıklıyoruz."
dogrulama: 2026-10-15
---

Model eğitimine dair yazılmış her şey; kayıp (loss), epoch, gradyan, embedding gibi terimlerle dolu görünür. Bu sayfa o terimleri **dört katmanda**, en temelden en özele doğru açıklıyor. Amaç ezberletmek değil; her kavramı bir analojiye ve mümkünse somut bir sayıya bağlamak.

:::note[Hızlı referans arıyorsanız]
Bu sayfa anlatıcıdır; uzun okumak istemiyorsanız tek satırlık tanımların bulunduğu [Hızlı Sözlük](/kaynaklar/sozluk/) sayfasına bakabilirsiniz. İkisi de aynı terimleri kapsar, ama buradaki anlatım "neden" sorusunu da yanıtlar.
:::

## Katman 1: En Temel Kavramlar

### Yapay zeka (artificial intelligence)

İnsan gibi görünen görevleri bilgisayara yaptırma çabasının şemsiye adı. Satranç oynayan programlar, öneri sistemleri, sohbet botları; hepsi yapay zekâ sayılır. **Analoji:** Yapay zeka bir araç kutusuysa, aşağıdaki kavramlar o kutudaki farklı aletlerdir.

### Makine öğrenmesi (machine learning)

Kuralları elle yazmak yerine, modele **örneklerden** kural çıkarmayı öğretme yaklaşımı. E-posta filtresine "içinde 'bedava' geçen ve bağlantı olan postalara şüpheli de" diye kural yazmak yerine, 10.000 spam ve 10.000 normal posta gösterip örüntüyü bulmasını sağlarsınız. Yapay zekanın bugünkü başarısının tamamına yakını bu yaklaşımdan gelir.

### Derin öğrenme (deep learning)

Makine öğrenmesinin, **çok katmanlı yapay sinir ağları** kullanan alt dalı. "Derin" kelimesi katman çokluğunu ifade eder. Görüntü, ses ve metin gibi karmaşık verilerde klasik yöntemleri büyük farkla geçer. Bugünkü LLM'ler, difüzyon modelleri; hepsi birer derin öğrenme modelidir. Katmanların işleyişi için [Transformer Mimarisi](/temeller/transformer/) sayfasına bakın.

### Model

Öğrenme süreci sonucunda ortaya çıkan, parametrelerden (sayılardan) oluşan matematiksel yapı. Bir fonksiyon gibi düşünün: metin girer, metin çıkar; görüntü girer, etiket çıkar. Modelin kendisi birkaç `.safetensors` dosyasından oluşur; boyutu gigabaytlarla ölçülür.

### Veri seti (dataset)

Modelin öğrenmesi için kullanılan örnek koleksiyonu. Genellikle üçe bölünür: **eğitim seti** (modelin gördüğü), **doğrulama seti** (eğitim sürerken ezberleyip ezberlemediğini kontrol ettiklerimiz) ve **test seti** (en sonda, hiç dokunulmamış veriyle yapılan son sınav). Bu ayrımın neden kritik olduğu [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/) sayfasında anlatılıyor.

### Özellik ve hedef (feature / label)

Tablo verisinde sütunlar ikiye ayrılır: modelin **girdi olarak gördüğü** sütunlar özellik, **tahmin etmesini istediğimiz** sütun hedeftir. Örnek: ev fiyatı tahmininde "metrekare, oda sayısı, konum" özellik; "fiyat" hedeftir. Uygulaması için [İlk Model](/klasik-ml/ilk-model/).

## Katman 2: Eğitim Süreci

### Parametre ve ağırlık (parameter / weight)

Modelin eğitim sırasında **öğrendiği sayılar**. "7B model" ifadesi "7 milyar parametreli model" demektir. Parametre sayısı hem modelin kapasitesini hem de bellek ihtiyacını belirler: her parametre fp16 hassasiyetinde 2 bayt yer kaplar, yani 7B bir model yalnızca ağırlıkları için yaklaşık **14 GB** VRAM ister. Sayıların detayı: [VRAM Hesabı](/donanim/vram-hesabi/).

### Eğitim (training)

Parametrelerin, verideki örnekler üzerinden adım adım güncellenmesi süreci. Rastgele başlayan sayılar, her adımda gerçeğe biraz daha yaklaşır. **Analoji:** Sürekli ufak düzeltmeler yapılan uzun bir kalibrasyon süreci.

### Çıkarım (inference)

Eğitilmiş modelin yeni bir girdiye cevap üretmesi. Eğitimin aksine burada parametreler **değişmez**; yalnızca ileri yönlü bir hesap yapılır. Bu yüzden çıkarım eğitimden kat kat ucuzdur ama hızı model boyutuna ve donanıma bağlıdır. Uygulamada: [Ollama](/kullanim/ollama/).

### Kayıp (loss)

Modelin tahmini ile gerçek cevap arasındaki farkın **tek bir sayıya** indirgenmiş ölçüsü. Eğitimin pusulasıdır: hedefimiz bu sayıyı küçültmek. Örnek: kayıp 3,2'den 1,4'e düştüyse eğitim iyi gidiyor demektir; eğrilerin nasıl okunacağı [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfasında.

### Epoch

Eğitim setinin tamamı üzerinden **bir tam geçiş**. 10.000 örneklik veriyle eğitim yapıp hepsini bir kez gördüyseniz 1 epoch tamamlanmıştır. Model çok küçük veri setlerinde ezberlemeye başladığı için genellikle 1-3 epoch yeterlidir.

### Batch ve step

**Batch**, aynı anda işlenen örnek grubudur (örneğin 8 örnek). **Step** ise bir batch'lik veriyle yapılan bir parametre güncellemesidir. Basit hesap: 10.000 örnek ÷ batch 8 = epoch başına **1.250 step**. GPU belleği küçükse batch küçültülür; kararlılık için gradyan birikimiyle (gradient accumulation) etkin batch büyütülür.

### Öğrenme oranı (learning rate)

Her güncellemede parametrelerin **ne kadar hızlı** değişeceğini belirleyen katsayı. Çok büyükse model savrulur ve öğrenemez; çok küçükse eğitim sonsuza kadar sürer. LoRA ince ayarında tipik değerler 1e-4 ile 2e-4 arasındadır; ayar rehberi için [Hiperparametreler](/llm/hiperparametreler/).

### Checkpoint

Eğitim sırasında belirli aralıklarla diske kaydedilen **model anlık görüntüsü**. Eğitim çökerse son checkpoint'ten devam edilir; ayrıca en iyi checkpoint (doğrulama kaybı en düşük olan) sonraki aşamalar için saklanır. **Analoji:** Video oyunlarındaki kayıt noktası.

## Katman 3: Dil Modelleri

### Token

Modelin gördüğü en küçük metin parçası. Örneğin `yapabileceklerimizden` kelimesi Türkçe için tipik bir tokenizer'da yaklaşık 6-8 token'a bölünür. Cümle önce token'lara ayrılır, sonra her token bir sayı kimliğine (id) çevrilir. Ayrıntılı anlatım: [Tokenizasyon](/temeller/tokenizasyon/).

### Tokenizer

Metni token'lara bölen ve her token'ı bir id'ye eşleyen araç. Her model ailesinin kendi tokenizer'ı vardır ve **değiştirilemez**; modelin öğrendiği id'ler yalnızca kendi tokenizer'ıyla anlamlıdır. Kelime dağarcığı (vocabulary) büyüklüğü modele göre değişir: Llama 3'te yaklaşık 128 bin, Qwen ailesinde yaklaşık 151 bin token vardır.

### Embedding

Token id'sinin, anlamı temsil eden **sayı vektörüne** dönüştürülmüş hali. Benzer anlamlı kelimelerin vektörleri birbirine yakın düşer; "kral - erkek + kadın ≈ kraliçe" meşhur örneği bu yüzden çalışır. 8B sınıfı modellerde vektör boyutu kabaca 4.000 civarındadır. Görsel karşılığı için [Difüzyon Temelleri](/gorsel/diffusion-temelleri/) sayfasında latent uzay anlatımına bakın.

### Transformer

2017'de "Attention Is All You Need" makalesiyle tanıtılan mimari; bugünkü tüm büyük dil modellerinin temeli. Özü **attention (dikkat)** mekanizmasıdır: cümledeki her kelime, diğer kelimelere "bakarak" anlamını bağlamdan alır. Detaylar: [Transformer Mimarisi](/temeller/transformer/).

### LLM (büyük dil modeli)

Milyarlarca parametreli, devasa metin külliyatıyla ön eğitilmiş dil modeli. Yapabildiği tek şey özünde bir olasılık tahminidir: "verilen metnin ardından en olası devamı üret". Sohbet, çeviri, kod yazma; hepsi bu tek becerinin yan ürünleridir. Örnek aileler (2026 itibarıyla): Llama 4, Mistral Small, Phi-4.

### SLM (küçük dil modeli)

Yaklaşık 0,5-8 milyar parametre aralığındaki modeller: Qwen3 (0,6B/1,7B/4B/8B), Gemma 3 (1B/4B/12B), Llama 3.2 (1B/3B), SmolLM3, Phi-4-mini. Tek GPU'ya sığdıkları ve ince ayara izin verdikleri için bu rehberin **asıl kahramanları** bunlar. Bağımsız karşılaştırmalarda Qwen3-8B, ince ayar için en iyi genel sonuçları veriyor.

### Bağlam penceresi (context window)

Modelin aynı anda "görebildiği" token sayısı. Llama 3.2'de 128 bin token, Qwen3'te yerel olarak 32 bin (YaRN tekniğiyle yaklaşık 131 bine genişletilebiliyor). Pencerenin ne kadar Türkçe metne denk geldiği, token verimliliğinize bağlıdır; bu yüzden Türkçe'de pencere kabaca yarı yarıya daralır — hesaplaması [Tokenizasyon](/temeller/tokenizasyon/) sayfasında. Güncel değerler için model kartını kontrol edin.

### Sohbet şablonu (chat template)

Modele "kim konuşuyor?" bilgisini veren özel token kalıbı. Qwen'in kullandığı ChatML'de mesajlar `<|im_start|>` ve `<|im_end|>` işaretleriyle çerçevelenir; Llama 2'de `[INST]` görürsünüz. Model bu kalıbı ön eğitimden sonraki talimat aşamasında öğrenir. **Kritik kural:** eğitimde hangi şablon kullanıldıysa, çıkarımda da o kullanılmalıdır; aksi halde model bozulur. Eğitimdeki rolü: [SFT](/llm/sft/).

## Katman 4: Özelleştirme

### İnce ayar (fine-tuning)

Ön eğitilmiş bir modelin ağırlıklarını, kendi verinizle **ek eğitimle** güncellemek. **Analoji:** Üniversite mezunu birine meslek içi eğitim vermek; sıfırdan okutmak değil, mevcut bilginin üzerine uzmanlık eklemek. Türlerine göre sırası: [Ön Eğitim](/llm/pretraining/) → [SFT](/llm/sft/) → [DPO ve RLHF](/llm/dpo-rlhf/).

### LoRA (Low-Rank Adaptation)

Tüm modeli eğitmek yerine, modele **küçük ek matrisler** takıp yalnızca onları eğitme yöntemi. Temel model donar; orijinal parametrelerin %1'inden azı eğitilir. Sonuç, ana modelden bağımsız, onlarca-yüz megabayt boyutunda bir **adaptör** dosyasıdır. Tek ekran kartında 8B modeli ince ayarlamanın standart yolu budur: [LoRA ve QLoRA](/llm/lora-qlora/).

### QLoRA

LoRA'nın bellek dostu kardeşi: temel model önce 4-bit'e **nicemlenir** (sıkıştırılır), LoRA adaptörü o sıkıştırılmış model üzerinde eğitilir. 7B'lik bir modelin bellek ihtiyacı ~14 GB'den 5 GB civarına iner; böylece 4-6 GB VRAM'li ekran kartlarında bile 0,5-2B modeller eğitilebilir. 2026'nın en yaygın ince ayar yöntemidir.

### Talimat ayarı (instruction tuning)

Modele "soru sorulduğunda cevap ver" davranışını öğretmek. Ham ön eğitimli model metni devam ettirir; talimat ayarı görmüş model ise soru-cevap, görev tamamlama gibi kalıpları izler. Bu aşamanın teknik adı **denetimli ince ayardır (SFT)** ve verisi hep aynı üçlüden oluşur: talimat, girdi (varsa), cevap. Ayrıntı: [SFT](/llm/sft/).

### RLHF ve DPO

Modeli **insan tercihleriyle** hizalama yöntemleri. RLHF'te (insan geri bildirimiyle pekiştirmeli öğrenme) önce "iyi cevap" puanlayan bir ödül modeli eğitilir, sonra dil modeli bu ödüle göre pekiştirmeli öğrenmeyle (PPO) güncellenir. DPO ise aynı işi daha basit yapar: "A cevabını B'ye tercih ettim" çiftleriyle doğrudan eğitim. 2026 itibarıyla topluluk pratiğinde DPO açık ara daha yaygındır: [DPO ve RLHF](/llm/dpo-rlhf/).

### Nicemleme (quantization)

Sayıları daha az bit ile temsil etme sanatı: fp16'dan 8-bit veya 4-bit'e indirmek. **Analoji:** Fotoğrafı yüksek kaliteden JPEG'e çevirmek; dosya 4 kat küçülür, kalite biraz düşer. 8B bir model 4-bit'te yaklaşık 5 GB'a iner ve sıradan bir dizüstünde çalışır. Eğitimde (QLoRA) ve dağıtımda (GGUF) hep karşınıza çıkar: [Nicemleme](/kullanim/quantization/).

### Damıtma (distillation)

Büyük "öğretmen" modelin çıktılarını taklit eden küçük bir "öğrenci" model eğitmek. Öğrenci, öğretmenin yalnızca cevabını değil, cevap dağılımını (hangi yanlışın "daha az yanlış" olduğunu) da öğrenir. Örnek: DeepSeek-R1'in çıktılarıyla eğitilmiş R1-Distill ailesi, davranışı küçük modellere taşır. Sizin ölçeğinizde en pratik kullanımı: büyük modelden veri üretip küçük modeli eğitmek: [Kendi verini oluştur](/veri/kendi-verini-olustur/).

### RAG (getirimle desteklenen üretim)

Bilgiyi modelin ağırlıklarına gömmek yerine, soru gelince ilgili belgeleri veritabanından **getirip** bağlama ekleme yöntemi. **Analoji:** Ezber sınavı yerine açık kitap sınavı. Eğitim gerektirmez, güncel ve özel bilgi için mükemmeldir; ancak modelin üslubunu veya davranışını değiştirmez — bu yüzden çoğu projede ince ayarla birlikte kullanılır. Karar rehberi: [RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/) · Uygulama tarafı: [Sunma ve API](/kullanim/sunma-api/).

## Bu Terimler Nerede Derinleşiyor?

| Kavram | Derinleştiği sayfa |
| --- | --- |
| Token, tokenizer, sohbet şablonu | [Tokenizasyon](/temeller/tokenizasyon/) |
| Transformer, embedding, attention, katman | [Transformer Mimarisi](/temeller/transformer/) |
| Kayıp, epoch, batch, step, öğrenme oranı | [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/) |
| Öğrenme oranı ve diğer eğitim ayarları | [Hiperparametreler](/llm/hiperparametreler/) |
| Parametre, VRAM, fp16/4-bit bellek | [VRAM Hesabı](/donanim/vram-hesabi/) |
| İnce ayar, talimat ayarı, SFT verisi | [SFT](/llm/sft/) |
| LoRA, QLoRA, adaptör | [LoRA ve QLoRA](/llm/lora-qlora/) |
| RLHF, DPO, hizalama | [DPO ve RLHF](/llm/dpo-rlhf/) |
| Nicemleme, GGUF, 4-bit | [Nicemleme](/kullanim/quantization/) |
| Sıfırdan ön eğitim, küçük ölçekte | [Ön Eğitim](/llm/pretraining/) |
| Çıkarım, yerel çalıştırma | [Ollama](/kullanim/ollama/) |
| Damıtma, veri sentezi | [Kendi Verini Oluştur](/veri/kendi-verini-olustur/) |
| Klasik ML: özellik, hedef, model | [Klasik ML Temelleri](/klasik-ml/temeller/) |

:::tip[Nasıl ilerlemeli?]
Kavramlar oturduysa sıradaki durak donanımınıza uygun yolu çizen [Yol Haritası](/baslangic/yol-haritasi/). Teknik derinlik istiyorsanız [Temeller](/temeller/transformer/) bölümüne geçin. Aklınıza takılan terim olduğunda bu sayfaya geri dönün — her terim yerinde, bağlamıyla anlatılıyor.
:::
