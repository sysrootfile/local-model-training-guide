---
title: "Transformer Mimarisi: Modelin İçinde Ne Var?"
description: "Yapay sinir ağlarından attention mekanizmasına, encoder-decoder ayrımından parametre sayısının anlamına: LLM'lerin içindeki mimariyi sezgisel olarak anlatıyoruz."
dogrulama: 2026-10-15
---

Bir dil modelini, kutunun içini hiç açmadan da kullanabilirsiniz; çoğu kişi öyle yapar. Ama modelin neden bu kadar VRAM yediğini, neden bağlam penceresinin sınırlı olduğunu ve ince ayarda tam olarak neyi değiştirdiğinizi anlamak için kutunun içine bir kez bakmak gerekir. Bu sayfa, sizi sıkmadan ama basitleştirmeden transformer mimarisini anlatıyor.

## Yapay Sinir Ağından Transformer'a Kısa Yolculuk

### Sinir ağı nedir?

En küçük yapı taşı **nöron**: bir grup girdiyi alır, her birini bir ağırlıkla çarpar, toplar ve sonucu bir aktivasyon fonksiyonundan geçirir. Tek nöron basit bir karar vericidir; binlercesi katmanlar halinde dizildiğinde ise inanılmaz karmaşık örüntüleri yakalayabilir. Klasik örnek: 28×28 piksellik bir rakam görüntüsünden (784 sayı) hangi rakam olduğunu (10 çıktı) tahmin eden ağ. Eğitim sürecinin işleyişi [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/) sayfasında; burada konumuz ağın **şekli**.

Dil için problem şudur: metin sabit boyutlu bir sayı listesi değildir. Cümleler değişken uzunluktadır ve anlam **sıradan** gelir: "kedi balığı yedi" ile "balık kediyi yedi" aynı kelimelerden oluşur ama anlamları zıttır.

### Neden sıralı modeller (RNN) yetmedi?

Transformer'dan önce metin, RNN (tekrarlayan sinir ağı) türevleriyle işlenirdi. RNN, kelimeleri **tek tek ve sırayla** işler: her adımda bir "hafıza" (gizli durum) güncellenir. İki temel sorun ortaya çıktı:

1. **Uzun bağımlılıklarda unutma:** 500 kelimelik bir metnin başındaki bilgi, sona gelindiğinde hafızada iyice solmuş olur.
2. **Paralelleştirilemezlik:** Her kelime bir öncekini beklemek zorundadır; GPU'nun binlerce çekirdeği büyük ölçüde boş bekler.

2017'de yayımlanan "Attention Is All You Need" makalesi bu iki sorunu da sıralamayı tamamen bırakarak çözdü — ve bugünkü LLM çağı başladı.

## Attention: Modelin "Neye Bakacağım?" Mekanizması

Şu cümleye bakın: *"Kediyi besledim çünkü **o** çok açtı."* "O" kimdir? İnsan olarak saniyesinde kediyi bulursunuz çünkü cümledeki diğer kelimelere **dikkat** edersiniz. Attention (dikkat) mekanizması tam olarak bunu yapar: her kelime, diğer tüm kelimelere bakar ve anlamını onlardan alır.

### Soru, anahtar, değer (Q/K/V) benzetmesi

Attention'ı bir kütüphane aramasıyla düşünün:

- **Query (soru):** Sizin arama isteğiniz — "kediyle ilgili ne var?"
- **Key (anahtar):** Her kitabın etiketi — "kitaplar hakkında", "kediler hakkında"...
- **Value (değer):** Kitabın içeriği.

Model her kelime için bir soru üretir, tüm anahtarlarla karşılaştırır (benzerlik skoru), en benzer anahtarlara en yüksek ağırlığı verir ve değerleri bu ağırlıklarla toplar. Sonuç: "o" kelimesinin vektörü, ağırlıklı olarak "kedi" kelimesinin bilgisiyle dolar.

Gerçekte bunlar üç ayrı **öğrenilmiş matris** çarpımıdır (W_q, W_k, W_v) ve ağırlıklar softmax ile normalize edilir; yani sistemin tamamı birkaç matris çarpımından ibarettir. GPU'ların sevdiği şey tam olarak budur: tek bir büyük paralel hesap.

:::note[Çoklu kafa (multi-head) attention]
Tek attention, tek bir "bakış açısı" sağlar. Transformer bunu 8-64 kez paralel yapar: bir kafa dilbilgisine, bir diğeri anlam yakınlığına, bir diğeri konuma odaklanabilir. Sonuçlar birleştirilir. Buna **çoklu kafa attention** denir ve modellerin dilbilgisel yapıyı bu kadar iyi yakalamasının nedenlerinden biridir.
:::

### Neden devrim yarattı?

Attention'ın üç pratik üstünlüğü, bugünkü LLM çağını mümkün kıldı:

- **Tam paralellik:** Tüm token'lar aynı anda işlenir; GPU'nun gücü boşa gitmez. RNN'in "sırayla bekleme" darboğazı ortadan kalkar.
- **Kısa yol, uzun hafıza:** İki kelime arasındaki mesafe ne olursa olsun, aralarındaki hesap tek adımdır. 5.000 kelime ötedeki bilgi de 5 kelime ötedeki kadar erişilebilirdir.
- **Ölçeklenebilirlik:** Yapı, model büyüdükçe daha iyi çalışır. Aynı blok yapısının kopyalanmasıyla 1B'den 400B'ye aynı reçeteyle çıkılabilir.

## Bir Transformer Bloğunun Anatomisi

Bir LLM, aynı yapının üst üste dizilmiş onlarca kopyasından oluşur. Her blokta dört bileşen vardır:

1. **Attention katmanı:** Yukarıda anlatılan "diğer kelimelere bakma" işi. Token'lar arası ilişkileri kurar.
2. **İleri beslemeli ağ (FFN):** Attention'dan geçen her vektörü bağımsız olarak işleyen iki katmanlı küçük bir sinir ağı. Modelin parametrelerinin önemli bir kısmı burada yaşar; "bilgi deposu" gibi çalıştığı düşünülür.
3. **Artık bağlantılar (residual):** Her katmanın çıktısı, girdisiyle toplanır. **Analoji:** Hiçbir şeyi kaybetmemek için her düzeltmenin üzerine eklenen notlar. Bu bağlantılar olmadan 30+ katmanlı modeller eğitilemez.
4. **Katman normalizasyonu (RMSNorm/LayerNorm):** Her adımda değerleri dengeli bir aralıkta tutan bir ölçekleme. Eğitimin çökmemesini sağlar.

**Katman sayısı** modelin "derinliği", **gizli boyut (hidden size)** ise her token'ın dolaştığı vektörün uzunluğudur. 8B sınıfı bir modelde tipik olarak 30-40 katman ve 3.000-4.000 arası gizli boyut görülür. Neden önemli? Bellek ve hesap ihtiyacı bu iki sayıyla neredeyse doğru orantılı büyür: [VRAM Hesabı](/donanim/vram-hesabi/).

## Encoder mu Decoder mı? Neden Herkes Decoder-Only?

Transformer'ın ilk yıllarında iki farklı kullanım öne çıktı:

| Mimari | Temsilci | Eğitim görevi | Güçlü olduğu iş |
| --- | --- | --- | --- |
| Encoder-only | BERT | Maskeli dil modellemesi: cümledeki kelimelerin bir kısmı gizlenir, model doldurur | Anlama: sınıflandırma, duygu analizi, arama |
| Encoder-decoder | T5 | Girdiyi okuyup farklı bir metin üretme | Çeviri, özetleme |
| Decoder-only | GPT, Llama, Qwen, Gemma, Mistral | Her adımda **bir sonraki token'ı** tahmin etme | Üretim: sohbet, kod, genel amaç |

2018-2020 arasında üç mimari yarışıyordu; bugün ise neredeyse tüm büyük modeller **decoder-only**. Sebep, basitliğin ölçeklenmedeki gücü: tek bir eğitim hedefi (sıradaki token'ı tahmin et) internet ölçeğindeki her metinden otomatik etiket üretmeye izin verir. Encoder modeller anlama görevlerinde hâlâ kullanılır (ör. benzerlik arama), ama genel amaçlı asistanların tamamı decoder-only. Bu tablo 2026 itibarıyla aynen geçerli; fark edeceğiniz değişiklik, çok modlu modellerin görüntüleri işlemek için modele **ayrı bir vision encoder** bağlamasıdır — o bileşen girdi okuyucudur, metin üreten çekirdek yine decoder-only kalır.

:::note["Sıradaki token'ı tahmin etmek" nasıl sohbete dönüşür?]
Model aslında tek bir şey yapar: o ana kadarki metne bakıp sıradaki token'ın olasılık dağılımını üretir. Sohbet, talimat ve rol işaretleriyle (sohbet şablonu) aynı mekanizmanın yönlendirilmesidir. Ayrıntı: [Tokenizasyon](/temeller/tokenizasyon/) ve [SFT](/llm/sft/).
:::

## Parametre Sayısı Neyi Belirler?

Model adlarındaki "B" harfi **milyar** parametredir. Parametre sayısı üç şeyi birden etkiler:

- **Kapasite:** Daha çok parametre, daha karmaşık örüntüleri öğrenme potansiyeli demek — ama veri ve eğitim bütçesi yeterliyse.
- **Bellek:** Her parametre fp16'da 2 bayt tutar. Yani 1B model ~2 GB, 8B model ~16 GB, 70B model ~140 GB yer ister (yalnızca ağırlıklar). 4-bit nicemlemeyle bu değerler kabaca 4'te 1'e iner: [Nicemleme](/kullanim/quantization/).
- **Hız:** Çıkarım hızı ağırlıklı olarak parametre sayısıyla ters orantılıdır; iki kat büyük model iki kata yakın yavaşlar.

2026 itibarıyla tipik örnekler: Qwen3 ailesi 0,6B / 1,7B / 4B / 8B; Gemma 3 ailesi 1B / 4B / 12B; Llama 3.2 ailesi 1B / 3B. Bu boyutlar rastgele değil — tek bir oyuncu ekran kartına sığacak şekilde tasarlanmış "yerel dostu" sürümlerdir.

| Model boyutu | Yalnızca ağırlıklar (fp16) | Yalnızca ağırlıklar (4-bit, yaklaşık) |
| --- | --- | --- |
| 1B | ~2 GB | ~0,6 GB |
| 8B | ~16 GB | ~4-5 GB |
| 70B | ~140 GB | ~35-40 GB |

:::note[Peki 0,5B model nelerden feragat eder?]
Kapasite farkı en çok şu işlerde hissedilir: uzun zincirli akıl yürütme, az bilinen alan bilgisi ve çok dilli çıkarım. Buna karşılık 0,5-2B modeller, tek bir göreve daraltılmış işlerde (ör. sınıflandırma, üslup aktarma, biçim dönüştürme) şaşırtıcı derecede iyi olabilir ve 4 GB VRAM'e sığar. Bu yüzden rehber boyunca "önce görevi tanımla, sonra model boyunu seç" diyoruz: [Yol Haritası](/baslangic/yol-haritasi/).
:::

## İki Kısa Not

### Mixture-of-Experts (MoE)

Bazı modern modeller, her token için parametrelerin **tamamını** değil yalnızca bir kısmını devreye sokar: uzman (expert) adı verilen alt ağlardan birkaçı seçilir. Farkı net görmek için üç resmî örnek (toplam → token başına aktif):

- **Llama 4 Scout:** 109B toplam, 17B aktif; 16 uzmandan seçim (Meta'nın duyurusu).
- **Qwen3-30B-A3B:** 30,5B toplam, 3,3B aktif; 128 uzman var, her token için 8'i seçilir.
- **DeepSeek-V3:** 671B toplam, 37B aktif.

Böylece "büyük model bilgisi, küçük model maliyeti"ne yaklaşılır. Ama dikkat: **VRAM tarafında indirim yoktur.** Model, hangi uzmanın seçileceğine token token karar verir; hangi uzmana ihtiyaç olacağını önceden bilemezsiniz, bu yüzden **tüm uzmanların ağırlıkları yine tamamen bellekte durur.** 30B'lik bir MoE modeli hesap gücü açısından 3B'lik bir model gibi davranır ama bellek açısından 30B'lik modelin tamamını ister: [VRAM Hesabı](/donanim/vram-hesabi/).

### Konum kodlaması (positional encoding)

Attention, kelimelerin **sırasını** kendiliğinden bilmez — ona "kedi balığı yedi" ile "balık kediyi yedi" aynı görünür. Bu yüzden her token'ın vektörüne konum bilgisi eklenir. İlk modeller öğrenilmiş konum vektörleri kullanırken, 2026 itibarıyla baskın yöntem **RoPE** (döner konum kodlaması; [RoFormer makalesi](https://arxiv.org/abs/2104.09864)): konum bilgisi vektörlerin döndürülmesiyle kodlanır; hem mutlak konumu taşır hem de iki kelime arasındaki göreli mesafenin dikkat skoruna doğal biçimde karışmasını sağlar. Eğitimde görülenden uzun bağlamlara çıkarken ölçekleme teknikleri devreye girer: YaRN ([makale](https://arxiv.org/abs/2309.00071)), RoPE frekanslarını özenli biçimde yeniden ölçekleyerek pencereyi büyütür. Somut örnek: Qwen3-8B 32.768 token yerel pencereyle gelir; model kartına göre YaRN ile 131.072 token'a kadar doğrulanmıştır.

## 2026 Mimari Sözlüğü: Config Dosyasında Göreceğiniz Terimler

Modern model kartlarını açtığınızda karşınıza çıkacak terimlerin mini sözlüğü. Hiçbiri sihir değil; az önce anlattığımız bloğun bileşenlerinin güncellenmiş halleridir.

- **GQA (gruplu sorgu dikkati) ve MQA:** Attention'da soru (query) kafaları çok, anahtar/değer (KV) kafaları azdır: Llama 3'te 32 soru kafasına karşılık 8 KV kafası, Qwen3-8B'de yine 32'ye 8, Gemma 3'te 8'e 4 vardır. KV cache'i ve bellek trafiğini doğrudan küçültür; kaliteden büyük ölçüde ödün vermez. Uç hâli **MQA**'dır: tek KV kafası. Config'de `num_key_value_heads` sayısının `num_attention_heads`'ten küçük görmeniz bunun işaretidir.
- **RMSNorm:** Katman normalizasyonunun hafifletilmiş hâli ([makale](https://arxiv.org/abs/1910.07467)): ortalama çıkarma adımını atar, değerleri yalnızca kareler ortalamasının kareköküyle ölçekler. Daha az işlemle benzer eğitim kararlılığı sağladığı için Llama ve Qwen dahil modern modellerin standart tercihi olmuştur.
- **SwiGLU:** FFN'in aktivasyon fonksiyonu ailesi ([makale](https://arxiv.org/abs/2002.05202)); config'lerde "SiLU" aktivasyonu olarak görünür. Kapılı (gated) yapısı sayesinde aynı parametre bütçesinde genellikle daha iyi öğrenme sağlar.
- **RoPE:** Konum kodlamasının bugünkü baskın cevabı; az önceki bölümde ayrıntısı ve YaRN ile uzatma hikâyesi var.

Bu terimleri gördüğünüzde şunu bilin: omurga değişmemiştir; 2017'deki bloğun her bileşeni, ölçek ve kararlılık için yıllar içinde test edilmiş en iyi uygulamalarla yenilenmiştir.

## Bir Token'ın Yolculuğu: Baştan Sona Özet

"Merhaba" yazdığınızda modelin içinde şu yol izlenir:

1. **Tokenizasyon:** Metin token'lara ve id'lere çevrilir (ör. "Merhaba" → `[9707]`).
2. **Embedding:** Her id, gizli boyutlu bir vektöre dönüştürülür.
3. **Konum ekleme:** Her vektöre sıra bilgisi (RoPE) işlenir.
4. **Blok turu:** Vektör, N adet transformer bloğundan sırayla geçer; her blokta dikkat (attention) ve ileri beslemeli ağ (FFN) işlemleri uygulanır.
5. **Çıkış katmanı:** Son vektör, kelime dağarcığı boyutunda bir skor listesine (logit) dönüştürülür.
6. **Olasılığa çevirme ve örnekleme:** Softmax ile olasılıklar hesaplanır; model bir token "seçer" ve süreç onunla tekrarlanır.

Dikkat: Adım 6'daki seçim her zaman en olası token değildir; `temperature` ve `top_p` gibi örnekleme ayarları, üretimin yaratıcılığını ve çeşitliliğini kontrol eder. Bunlar eğitim parametresi değil, **çıkarım** ayarlarıdır.

## Çıkarımda Bellek Sınırı: KV Cache

Model her yeni token üretirken önceki tüm token'ların attention bilgilerini (key ve value vektörlerini) yeniden hesaplamamak için saklar. Bu hafızaya **KV cache** denir. Sonuç: bağlam penceresi büyüdükçe çıkarım belleği hızla büyür ve uzun konuşmalarda model yavaşlar, daha çok VRAM ister. "128K bağlam" vaadinin pratikte donanım sınırlarına takılmasının başlıca sebebi KV cache'tir.

Hesabı kabaca şöyle yaparsınız: cache boyutu ≈ 2 (key + value) × katman sayısı × KV kafa sayısı × kafa başına boyut × bağlam uzunluğu × bayt. Qwen3-8B üzerinden örnek (fp16, yani 2 bayt): 2 × 36 katman × 8 KV kafa × 128 boyut × 2 bayt ≈ 0,14 MB token başına. 32.768 token'lık bağlamda bu ~4,5 GB eder; YaRN ile 131K'ya çıkarırsanız ~18 GB — yalnızca cache için. Burada GQA'nın payı büyüktür: KV kafası 32 olsaydı (GQA olmasaydı) dört katı bellek öderdiniz. Bu ek belleğin, modelin kendi ağırlıklarının (fp16'da yaklaşık 16 GB) üzerine bindiğini unutmayın.

## Hız Tekniği: FlashAttention

KV cache belleği şişirir; attention'ın kendisi de bağlam uzadıkça hızla pahalılaşır: basit uygulamada her token çifti için bir skor hesaplanır ve bu dev ara matrisi belleğe yazıp geri okumak, hesabın kendisinden bile zaman alabilir. **FlashAttention**'ın fikri matematiksel değil mühendisliktir: dikkat matrisini hiç belleğe yazmadan hesabı küçük bloklar (tile) hâlinde, GPU'nun hızlı çip içi belleğinde tutarak yapar ([makale](https://arxiv.org/abs/2205.14135)). Sonuç birebir aynıdır; yalnızca bellek trafiği kısaldığı için hem hızlanır hem uzun bağlam daha az bellekle mümkün olur.

Bu tekniği elle yazmazsınız; hazır kullanırsınız:

- HF transformers'ta modeli yüklerken `attn_implementation="flash_attention_2"` demeniz yeterli. Hiçbir şey demeseniz de varsayılan olarak **SDPA** (PyTorch'un gömülü, optimize dikkat uygulaması) devreye girer; çoğu yerel kullanıcı SDPA ile gayet iyi yaşar.
- vLLM ve Ollama gibi çıkarım araçları bu optimizasyonları kendiliğinden kullanır; sizin bir şey yapmanız gerekmez.

:::caution[Windows kullanıyorsanız]
FlashAttention kütüphanesi Linux'u hedefler; deposundaki not, Windows derlemesinin hâlâ yeterince test edilmediğini açıkça söyler. Windows makinesinde buna ihtiyaç duyarsanız en pürüzsüz yol WSL2 üzerinden çalışmaktır: kurulum adımları için [Yerel Kurulum](/donanim/yerel-kurulum/#wsl2-ne-zaman-gerekir) sayfasındaki WSL2 bölümüne bakın.
:::

## Sık Karşılaşılan Yanlış Anlamalar

:::caution[Bu üç inanış yaygın ama yanlış]
- **"Parametreler ezberlenmiş metin deposudur."** Hayır; bilgi, milyarlarca ağırlığa **dağıtık** olarak sinmiştir. Tek bir nöron "Ankara"yı temsil etmez.
- **"Attention, insan dikkati gibi çalışır."** Benzetme faydalıdır ama mekanizma duygusal değil, tamamen matris çarpımı ve softmax'tır.
- **"Daha çok parametre her zaman daha iyi."** Kapasite ancak yeterli veri ve eğitim bütçesi varsa değere dönüşür; 8B, iyi veriyle eğitilmiş 70B'yi belirli bir alanda geçebilir.
:::

## İnce Ayar Buraların Neresinde Devreye Girer?

LoRA ve QLoRA sayfalarında karşınıza çıkacak "hangi katmanlara adaptör takılacak?" sorusunun cevabı tam da bu mimaridedir. Adaptörler genellikle attention'ın soru/anahtar/değer ve çıkış projeksiyonlarına (q_proj, k_proj, v_proj, o_proj) ve bazı araçlarda ileri beslemeli ağ matrislerine eklenir. Bu matrisler modeldeki tüm parametrelerin küçük bir bölümünü oluşturur; işte 8B bir modeli "parametrelerin %1'inden azı" ile eğitebilmenizin sırrı budur.

Bir sonraki durak: [LoRA ve QLoRA](/llm/lora-qlora/) sayfasında bu adaptörlerin rütbe (rank), alfa gibi ayarlarıyla nasıl yapılandırıldığını göreceksiniz. Eğitim döngüsünün kendisini anlamak için: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/).

## Bu Rehberde Mimarı Değiştirmeyeceğiz

İyi haber: ince ayar yaptığınızda mimariye dokunmazsınız. Model aynı bloklardan oluşmaya devam eder; siz yalnızca ağırlıkların bir kısmını kendi verinizle güncellersiniz. Kötü haber: mimari aynı kaldığı için bellek ihtiyacı da aynı kalır — ve artık neden o kadar VRAM yediğini biliyorsunuz.

Attention'ın her token için hesap yapması, bağlam penceresi büyüdükçe bellek tüketiminin hızla artması demektir; katmanlar ve gizli boyut, ağırlık dosyasının boyutunu belirler. Bu bilgiyle VRAM planlaması artık bir tahmin oyunu değil: [VRAM Hesabı](/donanim/vram-hesabi/).

:::tip[Sıradaki adım]
Metnin sayılara dönüştüğü ilk durak tokenizasyonu öğrenin: [Tokenizasyon](/temeller/tokenizasyon/). Mimari oturduysa eğitim döngüsüne geçin: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/). Kendi küçük modelinizi sıfırdan eğitmek isterseniz: [Ön Eğitim](/llm/pretraining/).
:::

## Kaynaklar ve İleri Okuma

- [Attention Is All You Need (Vaswani vd. 2017)](https://arxiv.org/abs/1706.03762) — transformer mimarisini tanıtan orijinal makale.
- [RoFormer / RoPE (Su vd. 2021)](https://arxiv.org/abs/2104.09864) — döner konum kodlamasının makalesi.
- [YaRN (Peng vd. 2023)](https://arxiv.org/abs/2309.00071) — RoPE tabanlı verimli bağlam penceresi uzatma yöntemi.
- [GQA (Ainslie vd. 2023)](https://arxiv.org/abs/2305.13245) — KV cache'i küçülten gruplu sorgu dikkatinin makalesi.
- [RMSNorm (Zhang & Sennrich 2019)](https://arxiv.org/abs/1910.07467) — katman normalizasyonunun hafifletilmiş hâli.
- [GLU Variants Improve Transformer (Shazeer 2020)](https://arxiv.org/abs/2002.05202) — SwiGLU aktivasyonunun kaynak makalesi.
- [FlashAttention (Dao vd. 2022)](https://arxiv.org/abs/2205.14135) ve [GitHub deposu](https://github.com/Dao-AILab/flash-attention) — IO-verimli, birebir aynı sonuç veren dikkat hesabı.
- [DeepSeek-V3 teknik raporu](https://arxiv.org/abs/2412.19437) — 671B toplam / 37B aktif parametreli MoE mimarisinin raporu.
- [HF Transformers: Attention backends](https://huggingface.co/docs/transformers/attention_interface) — SDPA, FlashAttention-2 vb. dikkat uygulamalarını seçme kılavuzu.
- [Meta Llama 4 duyurusu](https://ai.meta.com/blog/llama-4-multimodal-intelligence/) — Llama 4 Scout'un 109B toplam / 17B aktif MoE sayıları.
- [Qwen3-30B-A3B model kartı](https://huggingface.co/Qwen/Qwen3-30B-A3B) — 30,5B toplam / 3,3B aktif; 128 uzmandan 8 seçimi.
