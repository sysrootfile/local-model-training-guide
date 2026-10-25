---
title: "Tokenizasyon: Model Metni Nasıl Görür?"
description: "Token nedir, BPE nasıl çalışır, Türkçe neden İngilizce'den daha fazla token tüketir ve sohbet şablonları neden kritiktir: hepsini örneklerle anlatıyoruz."
dogrulama: 2026-10-15
---

Bir dil modeli harf görmez, kelime de görmez. Gördüğü tek şey **sayılardır**: "Merhaba dünya" yazdığınızda model aslında `[9707, 3591]` gibi bir sayı listesi işler. Metni bu sayılara çeviren köprüye **tokenizasyon (tokenization)** denir. Bu sayfa, o köprünün nasıl çalıştığını ve özellikle Türkçe için neden bu kadar önemli olduğunu anlatıyor.

## Token Nedir?

Token, modelin gördüğü en küçük metin parçasıdır. Bazen bir kelime, bazen kelimenin bir parçası, bazen de bir noktalama işaretidir. Süreç iki adımda işler:

1. Metin, tokenizer tarafından parçalara ayrılır: `"Merhaba dünya"` → `["Mer", "haba", " dünya"]` gibi.
2. Her parça, kelime dağarcığındaki bir **id**'ye (sayıya) eşlenir: `["Mer"], ["haba"]...` → `[9707, ...]`.

**Analoji:** Lego. Model, hazır Lego parçalarıyla çalışır; sık kullanılan parçalar (ör. "ve", "bir") tek parça halinde kutuda durur, nadir ve uzun parçalar daha küçük parçalardan birleştirilir.

## Neden Harf veya Kelime Değil?

İki uç yaklaşımın da ciddi kusurları vardır:

- **Harf bazlı:** Kelime dağarcığı minicik olur (alfabe) ama cümleler 3-4 kat uzar. Her harfin anlam taşımaması, modelin işini gereksiz zorlaştırır; bağlam penceresi de boşa akar.
- **Kelime bazlı:** Türkçe gibi eklemeli dillerde "ev, evler, evlerimizden, evlerimizdekiler..." milyonlarca kelime biçimi üretir. Kelime dağarcığı patlar ve eğitimde hiç görülmemiş kelimeler (bilinmeyen kelime / OOV) `<unk>` ile geçiştirilir — yani bilgi kaybolur.

Çözüm, ikisinin arası: **alt kelime (subword)** mantığı. Sık geçen parçalar tek token olur; nadir kelimeler anlamlı parçalara ayrılır. Model, "görmediği" kelimeyi bile tanıdık parçalarından okuyabilir.

## BPE (Byte-Pair Encoding) Sezgisel Anlatım

Türkçe'de "bayt çifti kodlaması" diyebileceğimiz BPE, basit bir fikre dayanır: **veride en sık yan yana geçen sembol çiftini birleştir, bunu binlerce kez tekrarla.**

Temsili bir örnek üzerinden izleyelim:

```text title="Temsili BPE birleştirme adımları"
Başlangıç: kelimeler harflerine ayrılmış durumda
  e v,  e v l e r,  e v d e n

1. Adım: En sık çift "e v" → yeni sembol: "ev"
  ev,  ev l e r,  ev d e n

2. Adım: Şimdi en sık çift "l e" → yeni sembol: "le"
  ev,  ev le r,  ev d e n

3. Adım: "le r" sık geçiyor → yeni sembol: "ler"
  ev,  ev ler,  ev d e n
...
Sonuç: "ev" ve "ler" artık tek token; nadir "evden" ise "ev" + "d" + "en" gibi parçalara ayrılıyor.
```

Gerçek eğitimde bu işlem yüz binlerce kelimelik bir külliye üzerinde binlerce kez tekrarlanır ve sonuçta modele özgü bir **kelime dağarcığı (vocabulary)** doğar. Boyutlar modelden modele değişir ve modelin yapılandırma dosyasında (config.json) açıkça yazar: Llama 3'te 128.256, Qwen3'te 151.936, Gemma 3'te 262.208; OpenAI'nin GPT-4o tokenizer'ı ise yaklaşık 200 bindir. (Kesin sayılar model kartlarından alınmıştır; son doğrulama 2026-10.)

Modern modellerde bir de güvenlik ağı vardır: **byte-level BPE**. Sözlüğü Unicode karakterler üzerine değil, 256 **bayt** değeri üzerine kurar; böylece hangi dilde ve hangi karakterle yazarsanız yazın (İ, ğ, ş, emoji, tanımadığınız herhangi bir simge dahil), metin mutlaka bir bayt zinciri olarak temsil edilebilir. Bu, kelime bazlı yaklaşımların `<unk>` (bilinmeyen token) sorununu kökten çözer: hiçbir metin "bilinmeyen"e düşemez. GPT-2'den bu yana Llama, Qwen ve Gemma dahil yaygın modellerin çoğu bu yaklaşımı kullanır.

## Algoritma Aileleri: BPE, WordPiece, Unigram

BPE sahnedeki tek oyuncu değildir; üç ana algoritma ailesini ayırt etmek, model kartlarında okuduklarınızı anlamanıza yeter:

- **BPE:** En sık yan yana gelen çifti birleştirir; en alttan (harflerden) yukarıya inşa eder. Deterministiktir: aynı metin hep aynı şekilde bölünür. Llama, Qwen ve Gemma dahil bugünün çoğu üretici modeli BPE kullanır.
- **WordPiece:** BERT'in yöntemi. Birleştirme adayını en sık çiftten değil, eğitimdeki olabilirliği (likelihood) en çok artıran çiftten seçer; yani en "bilgilendirici" birleşmeyi bulmaya çalışır.
- **Unigram:** Ters yönde çalışır: önce büyük bir alt kelime havuzu kurar, sonra eğitimdeki kayba katkısı en düşük adayları kademeli olarak eler. T5 bu ailedendir.

Bunlardan ayrı bir not: **SentencePiece** bir algoritma değil, ham metin üzerinde BPE veya Unigram çalıştıran bir kütüphanedir. Boşluğu da (▁) bir token olarak sözlüğe kattığı için boşluksuz dillerde (Çince, Japonca) ve çok dilli modellerde tercih edilir; Türkçe odaklı projelerde de sıkça karşınıza çıkar.

## Türkçe'nin Krizi: Eklemeli Dil, Pahalı Tokenlar

Buraya dikkat: **Türkçe, model eğitiminde İngilizce'ye göre dezavantajlı bir dildir — ve bunun sebebi dilbilimseldir.**

Türkçe, sona ek getirerek kelime türeten **eklemeli (aglütinatif)** bir dildir. "Yapabileceklerimizden" kelimesini parçalayalım:

```text title="Tek kelime, yedi morfem"
yap - abil - ecek - ler - imiz - den
kök   yeterlik  gelecek  çoğul  iyelik  ayrılma hâli

İngilizce karşılığı: "from the things that we will be able to do"
```

İngilizce'de "will", "be", "able", "to", "do" gibi parçalar ayrı ve çok sık geçen kelimelerdir; BPE'de neredeyse hepsi tek token'a dönüşür. Türkçe'de ise bu anlam **tek kelimede** birleştiği ve kelime biçimleri son derece çeşitli olduğu için tokenizer kelimeyi 6-8 parçaya böler. Sonuç: aynı içerik, İngilizce'ye kıyasla Türkçe'de yaklaşık **1,5-2,5 kat daha fazla token** tüketir (oran; metnin türüne ve tokenizer'a göre değişir). Bu yalnızca Türkçe'ye özgü bir gözlem de değildir: araştırmalar, ticari tokenizer'ların diller arasında sistematik verimlilik farkı ürettiğini ve İngilizce'nin bu oyunda ayrıcalıklı olduğunu gösteriyor.

| Metin (Türkçe) | Yaklaşık token | İngilizce karşılığı | Yaklaşık token |
| --- | --- | --- | --- |
| merhaba | 1-2 | hello | 1 |
| kitaplar | 2-3 | books | 1 |
| evlerimizden | 4-5 | from our houses | 3 |
| yapabileceklerimizden | 6-8 | what we can do | 3-4 |
| yapay zeka | 2-3 | artificial intelligence | 2 |

:::caution[Tablodaki sayılar temsilidir]
Token sayıları kullandığınız tokenizer'a göre değişir; yukarıdaki değerler 2026 itibarıyla yaygın modellerde görülen yaklaşık aralıklardır. Kendi metninizle tam sayıyı ölçmek için bu sayfanın sonundaki [Python örneğini](#pratik-python-ile-token-sayma) çalıştırın.
:::

Bu durumun üç somut sonucu var:

1. **Bağlam penceresi daralır:** 128 bin token'lık bir pencere İngilizce'de on binlerce kelime alırken Türkçe'de etkin olarak kabaca yarısı kadar metin alır.
2. **Maliyet artar:** Çoğu API ve bulut hizmeti token başına ücretlendirir; aynı iş Türkçe'de 1,5-2,5 kat pahalıya gelebilir.
3. **Eğitim ve çıkarım yavaşlar:** Token başına işlem süresi sabit olduğundan, aynı cümle daha uzun işlenir.

:::tip[Türkçe için pratik ipuçları]
- Mümkünse **Türkçe verisiyle eğitilmiş** veya çok dilli veri görmüş modelleri seçin (Qwen, Gemma aileleri bu konuda görece iyidir).
- Bağlam planlaması yaparken token bütçesini İngilizce varsayımlarıyla değil, **kendi verinizle ölçerek** hesaplayın.
- Sistem talimatlarınızı gereksiz uzatmayın; her ek cümle bütçeden çalar.
:::

## Tokenizer Seçimi ve Sözlük Genişletme

**Bir modelin tokenizer'ı değiştirilemez.** Sebep basit: modelin embedding tablosu, tokenizer'ın ürettiği id'lere göre öğrenilmiştir; id 9707'nin ne anlama geldiğini kimse "yeniden söyleyemez". Bu yüzden tokenizer, modelin doğduğu alfabe gibidir.

**Sözlük genişletme (vocabulary extension)** ne zaman gündeme gelir? Bazı projeler Türkçe'ye özel yeni token'lar ekleyip (ör. çok sık geçen ekler), token sayısını düşürmek ister. Görünüşte cazip olsa da riskleri büyüktür:

- **Yeni embedding'ler sıfırdan doğar:** `resize_token_embeddings` ile tablo büyür ama yeni satırlar rastgele başlar; model bu token'ların anlamını yüz binlerce örnek görmeden öğrenemez.
- **Unutma riski:** Sözlük büyütüldüğünde tüm embedding katmanı etkilenir; mevcut yeteneklerde bozulma (unutma) görülebilir.
- **Ek VRAM ve uyumluluk sorunları:** Daha büyük embedding tablosu daha çok bellek ister; topluluk araçları (Ollama, llama.cpp) özel vocab'lerle sorun çıkarabilir.

2026 itibarıyla pratik öneri: çoğu Türkçe proje için **mevcut tokenizer'la devam etmek** daha akıllıcadır; model tarafındaki kazanç artık veri kalitesinden geliyor, vocab genişletmekten değil. Genişletmeyi ancak sıfırdan ön eğitim veya çok özel bir alan (ör. tıbbi terimler) için düşünün.

## Özel Token'lar ve Sohbet Şablonları

Tokenizer'ın bir de gizli görevi var: modele "kim konuşuyor?" demek. Bunun için kelime dağarcığında hiçbir doğal metinde geçmeyen **özel token'lar** ayrılır:

- Qwen/ChatML: `<|im_start|>`, `<|im_end|>`
- Llama 2: `[INST]`, `[/INST]`; Llama 3: `<|begin_of_text|>`, `<|start_header_id|>`, `<|eot_id|>`
- Genel: `<|user|>`, `<|assistant|>`, `<|system|>`

Bu token'lar bir sıra ve kalıp içinde birleştiğinde **sohbet şablonu (chat template)** ortaya çıkar:

```text title="ChatML benzeri bir sohbet şablonu"
<|im_start|>system
Sen yardımcı bir asistansın.<|im_end|>
<|im_start|>user
Bana üç kitap öner.<|im_end|>
<|im_start|>assistant
Tabii! İşte üç öneri: ...<|im_end|>
```

Qwen3 gibi akıl yürüten modellerin şablonunda bir de düşünme alanı vardır: model, cevabını vermeden önce `<think>...</think>` bloğu içinde gerekçesini üretir. `apply_chat_template` çağrısında `enable_thinking=False` diyerek bu modu kapatabilirsiniz.

Model, talimat ayarı aşamasında bu kalıbı görür ve rollerin sınırlarını öğrenir. İki kritik nokta:

1. **Eğitimde kullanılan şablonla çıkarımda kullanılan şablon aynı olmalıdır.** Uyumsuzluk, modelin "saçmalamasının" en yaygın sebebidir; kendi modelinizin davranışı bozuksa önce şablonu kontrol edin. Eğitim tarafı: [SFT](/llm/sft/).
2. **Kayıp (loss) hangi token'lar için hesaplanacak?** SFT'de genellikle yalnızca asistanın cevap token'ları için kayıp hesaplanır; kullanıcı mesajı ezberlenmez. Ayrıntı: [SFT](/llm/sft/).

## Pratik: Python ile Token Sayma

Artık kendi metninizin kaç token tükettiğini ölçelim. `transformers` kütüphanesiyle modelin kendi tokenizer'ını indirip üç satırda sayabilirsiniz:

```python title="token_say.py"
from transformers import AutoTokenizer

# Modelin kendi tokenizer'ı — başkası değil!
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

metin = "Yapabileceklerimizden bahsedelim."
id_listesi = tokenizer.encode(metin)

print("Token sayısı:", len(id_listesi))
print("Parçalar:", tokenizer.convert_ids_to_tokens(id_listesi))
# Örnek çıktı (tokenizer sürümüne göre değişir; tek kelime
# birden çok parçaya ayrılabiliyor):
# Parçalar: ['Yap', 'abile', 'cek', 'ler', 'imiz', 'den', ' bahs', 'edelim', '.']
```

:::note[OpenAI modellerini sayacaksanız: tiktoken]
OpenAI'nin kendi modellerinin token'larını sayacaksanız doğru araç `tiktoken` kütüphanesidir (`o200k_base`, `cl100k_base` gibi OpenAI'ye özgü kodlamalarla çalışır). Kendi eğittiğiniz ya da yerelde çalıştırdığınız başka bir model içinse sayacınız her zaman modelin kendi tokenizer'ıdır — yani yukarıdaki `AutoTokenizer` yöntemi. OpenAI sayacını yabancı bir modelin metnine uygulamak, o modelin sözlüğüyle yapılan sayımdan sapar ve maliyet hesabınızı yanıltır.
:::

Aynı metni sohbet şablonundan geçirip nihai girdiyi görmek de bir o kadar kolay:

```python title="sohbet_sablonu.py"
mesajlar = [{"role": "user", "content": "Merhaba, nasılsın?"}]

girdi = tokenizer.apply_chat_template(
    mesajlar,
    tokenize=False,             # ham metin olarak göster
    add_generation_prompt=True, # "asistan:" kısmını ekle
)
print(girdi)
```

Son olarak, token farkının maliyete nasıl yansıdığını basitçe modelleyelim:

```python title="maliyet.py"
# Varsayım: kullandığınız API 1 milyon token için 0,50 dolar alsın.
# Aynı içerik İngilizce'de 1.000, Türkçe'de 2.000 token tutsun:

ingilizce = 1_000 / 1_000_000 * 0.50
turkce    = 2_000 / 1_000_000 * 0.50

print(f"İngilizce: ${ingilizce:.4f}  Türkçe: ${turkce:.4f}")
print(f"Türkçe yaklaşık {turkce / ingilizce:.1f} kat daha pahalı")
```

:::note[Bu oran neden önemli?]
Günde 100.000 çağrı yapan bir uygulamada 2 kat token, 2 kat fatura demektir. Türkçe bir ürün geliştiriyorsanız bu fark bütçe planlamasında mutlaka hesaba katılmalıdır.
:::

## Token Ekonomisi ve Maliyet

Token sayısının paraya ve kapasiteye çevirisi iki basit hesaptır.

**Harcama hesabı:** API veya bulut çıkarımında fatura kabaca şöyle oluşur:

```text
maliyet = (girdi token'ları + üretilen token'lar) × 1M-token fiyatı / 1.000.000
```

Türkçe'nin 1,5-2,5 kat token tüketmesi, faturanın da aynı oranda şişmesi demektir; önceki bölümdeki maliyet.py tam olarak bu çarpımı hesaplıyor.

**Bütçe hesabı:** Bağlam penceresi bir bütçedir ve dört payı vardır: sistem talimatı, sabit metinler (few-shot örnekleri, referans belge parçaları), kullanıcının o anki girdisi ve modelin cevabı için ayırdığınız alan. Sistem talimatı **her istekte yeniden ödenen sabit giderdir** — gereksiz uzun bir sistem talimatı, her çağrıda bütçeden ödenen bir kira gibidir. Bağlam penceresinin mimarideki karşılığını [Transformer Mimarisi](/temeller/transformer/) sayfasında, eğitim tarafında bu bütçenin etki ettiği `max_length` ayarını [Hiperparametreler](/llm/hiperparametreler/) sayfasında göreceksiniz.

Kural basit: tasarım kararlarınızı token cinsinden düşünün. Prompt'u kısaltmak doğrudan tasarruftur; uzun bağlam hem pahalı hem yavaştır; Türkçe'nin ek yükü ise gerçek ama ölçülebilir bir maliyettir.

## Veri Hazırlarken Token Bütçesi

Tokenizasyonu anlamak, veri hazırlığının temelidir: kaç örnek sığdırabileceğiniz, bağlam penceresini nasıl böleceğiniz ve maliyetiniz ne olacağı hep token sayılarıyla hesaplanır. Bu bütçeyi nasıl planlayacağınızı [Veri Türleri](/veri/veri-turleri/) sayfasında, verinizi sohbet formatına nasıl çevireceğinizi [Veri Formatları](/veri/veri-formatlari/) sayfasında bulacaksınız.

:::tip[Sıradaki adım]
Tokenlar sayılara dönüştü; peki bu sayılar modelin içinde nasıl işleniyor? [Transformer Mimarisi](/temeller/transformer/) sayfasına geçin. Ya da doğrudan eğitimin işleyişine atlayın: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/).
:::

## Kaynaklar ve İleri Okuma

- [HF Transformers: Tokenizer özeti](https://huggingface.co/docs/transformers/tokenizer_summary) — BPE, WordPiece, Unigram ve byte-level BPE'nin resmî karşılaştırması; Türkçe'nin eklemeli yapısına özel bir not da içerir.
- [Sennrich vd. 2015: Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — BPE'yi doğal dil işlemeye taşıyan orijinal makale.
- [Kudo 2018: Subword Regularization](https://arxiv.org/abs/1804.10959) — Unigram tokenizasyonunun makalesi (T5'in kullandığı aile).
- [Kudo & Richardson 2018: SentencePiece](https://arxiv.org/abs/1808.06226) — boşluksuz diller için ham metin tokenizasyonu.
- [HF Tokenizers](https://huggingface.co/docs/tokenizers) — kendi tokenizer'ınızı eğitmek isterseniz hızlı, Rust tabanlı kütüphane.
- [HF LLM Kursu, Bölüm 6](https://huggingface.co/learn/llm-course/chapter6/1) — tokenizer algoritmalarını ve sıfırdan eğitim sürecini anlatan uygulamalı bölüm.
- [tiktoken (GitHub)](https://github.com/openai/tiktoken) — OpenAI modelleri için hızlı BPE token sayacı.
- [Ahia vd. 2023: Do All Languages Cost the Same?](https://aclanthology.org/2023.emnlp-main.614/) — ticari tokenizer'larda diller arası maliyet eşitsizliğini ölçen çalışma.
- [Qwen3-8B model kartı](https://huggingface.co/Qwen/Qwen3-8B) — chat template, `<think>` bloğu ve YaRN ile bağlam uzatmanın resmî ayrıntıları.
