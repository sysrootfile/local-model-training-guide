---
title: "Çıkarım Parametreleri: Ağırlıklara Dokunmadan Davranışı Değiştirmek"
description: "Sıcaklık, top-k, top-p, min-p, tohum, num_predict ve stop: Ollama'da bu ayarlar nereden gelir, üretim dağılımını nasıl biçimlendirir, belgedeki varsayılanlar neden kendi makinenizde doğrulanmalı."
dogrulama: 2026-10-19
---

Eğitim bitti, ağırlıklar sabit. Aynı soruyu iki kez soruyorsunuz; birinde net bir cümle, diğerinde dağınık bir paragraf çıkıyor. Model değişmedi. Değişen, sıradaki token'ın olasılık dağılımından **nasıl seçildiği**. Bu sayfa o seçimi yöneten düğmeleri, Ollama'da nereden geldiklerini ve her birinin üretimde neyi kestiğini anlatıyor.

:::note[Bu sayfada yeni ölçüm yok]
Buradaki sayıların iki kaynağı var: Ollama'nın resmî Modelfile ve API belgesi (**son doğrulama 2026-10-17**) ve bu makinedeki model dosyasından gerçekten okunan üstveri. Düğmelerin davranış üzerindeki etkisini bu sayfa ölçmüyor; o ölçüm artık var: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfası aynı istemleri onar kez koştu ve aşağıda "ölçülmedi" dediğim üç yerin cevabını sayıyla veriyor. Diğer ölçümlü sayfalar [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/), [Ajan Ölçümü](/ajan/ajan-olcumu/) ve [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/). Belgeden aktardığım her varsayılanı kendi makinenizde nasıl kontrol edeceğinizi de satır satır veriyorum; çünkü aşağıda göreceğiniz gibi **iki belge aynı parametre için iki farklı varsayılan yazıyor.**
:::

## Ayar Nereden Gelir: Dört Katman

Bir değerin fiilen ne olduğunu anlamak için sırayla dört yere bakılır:

1. **Ollama'nın kendi varsayılanları.** Hiçbir şey yazmazanız kullanılan değerler; aşağıdaki tabloda.
2. **Model dosyasının gömülü üstverisi (GGUF başlığı).** Dönüştürücüler modele örnekleme ayarı gömebilir.
3. **Modelfile'daki `PARAMETER` satırları.** Kendi modelinizi `ollama create` ile kurarken yazdığınız satırlar ([Ollama sayfasındaki Modelfile örneği](/kullanim/ollama/)).
4. **İstek gövdesindeki `options` nesnesi.** En taşınabilir ve en geçici katman: betiğiniz hangi değeri gönderiyorsa odur.

İlk iki katmanı kontrol etmenin komutu bu makinede gerçekten çalıştırıldı.

```shell
ollama show --modelfile qwen2.5:3b-instruct-q4_K_M
```

Çıktıda `FROM`, `TEMPLATE` ve `LICENSE` blokları var, **`PARAMETER` satırı yok**. Yani bu model Ollama'ya hiçbir örnekleme ayarı dayatmıyor; fiilî değerler Ollama'nın kendi varsayılanları. Aynı modelin GGUF başlığı da ikinci bir kontrol: `scripts/gguf-baslik.py` betiği dosyayı belleğe yüklemeden yalnızca başlık üstverisini yazdırır.

```text
GGUF sürüm 3 | tensör 434 | üstveri anahtarı 35
  qwen2.context_length                     32768
  qwen2.rope.freq_base                     1000000.0
  tokenizer.ggml.eos_token_id              151645
  tokenizer.ggml.padding_token_id          151643
  tokenizer.ggml.bos_token_id              151643
  tokenizer.ggml.add_bos_token             False
```

İki soru iki komutla kapanır: dosyada örnekleme ayarı gömülü mü, ve bu üç token numarası gerçekte hangi dizgiler?

```shell
python scripts/gguf-baslik.py "<blob dosyasi>" "sampl|penal"
python scripts/gguf-baslik.py "<blob dosyasi>" 151643 151644 151645
```

```text
  (eşleşen anahtar yok)
  token 151643  ->  (dolgu ve başlangıç olarak kullanılan eski işaret)
  token 151644  ->  (sohbet mesajını açan şablon işareti)
  token 151645  ->  (sohbet mesajını bitiren işaret; EOS olarak kayıtlı)
```

Betik numara gördüğünde token dizisini de çözüp yazıyor; parantez içleri burada özet, gerçek çıktı dizginin kendisi. 35 anahtarın hiçbiri `general.sampling` ya da benzeri bir örnekleme alanı taşımıyor: **bu modelde örnekleme ayarı gömülü değil**, fiilî değerler Ollama'nın kendi varsayılanları. `add_bos_token: False` satırı da aynı okumanın parçası; başlangıç işareti eklenmediği için sohbet şablonu ile `raw` modu arasındaki fark, gönderdiğiniz dizgilere bağlı kalıyor.

Betik, `ollama show --modelfile` çıktısındaki `FROM` satırının gösterdiği blob dosyasını okur ve yalnızca başlığı çözer: 1,9 GB dosya için saniyenin altında. Kendi modelinizde bir örnekleme anahtarı yazdırıyorsa (ör. `general.sampling.temperature`) o değer gömülüdür; hangi katmanın kazandığını tahmin etmek yerine tek bir istekle kontrol edin.

## Belgedeki Varsayılanlar

| Ayar | Belge varsayılanı | Ne yapar |
| --- | --- | --- |
| `temperature` | 0,8 | Logitleri böler; dağılımı yumuşatır ya da sivrilir |
| `top_k` | 40 | Yalnızca en olası 40 adayı bırakır |
| `top_p` | 0,9 | Olasılıkları azalan sırayla 0,9 toplama ulaşana kadar aday tutar |
| `min_p` | 0,0 | En olası adayın onda birinden hafif adayları eler |
| `seed` | 0 | Örnekleme zincirini sabitler |
| `num_predict` | -1 | Üretilecek en çok token; -1 "model kendi bitsin" |
| `num_ctx` | 2048 | Bağlam penceresi; sunucu bunu makinenin belleğine göre dinamik kurar |
| `repeat_last_n` | 64 | Tekrar cezasının bakacağı son token sayısı |
| `repeat_penalty` | 1,0 | O aralıkta tekrar eden token'a ceza |
| `stop` | tanımsız | Bu dizgilerden biri üretildiğinde durur |

:::caution[İki belge iki farklı varsayılan]
Yukarıdaki tablo `docs.ollama.com/modelfile` sayfasından alındı. Ollama belgesinin İngilizce aynası olan readthedocs kopyası aynı iki satırda başka değerler yazıyor: `repeat_penalty` **1,1**, `num_predict` **128**; tablosunda ayrıca `mirostat` (0), `mirostat_tau` (5,0), `mirostat_eta` (0,1), `tfs_z` (1) satırları var — bunların hiçbiri `docs.ollama.com` tablosunda geçmiyor. Bu çelişki bu makinede ölçülerek kapatıldı: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasındaki K0 kolunda `num_predict` **hiç gönderilmedi** ve üretim 1060 ile 1460 token arasında sürdü, üç isteğin de bitişi `stop`. Yani Ollama 0.40.4'te (makinenin sunucusu 2026-10-19'da 0.40.6; bu davranış o sürümde yeniden test edilmedi) iki belgeden hiçbiri yürürlükte değil; tavan fiilen yok. Kendi sürümünüzde kontrolün maliyeti yine tek bir istek.
:::

`num_ctx` satırı ayrı bir kafa karışıklığı: Modelfile belgesi 2048 yazıyor, ama Ollama'nın çalışma zamanı belleğiniz büyükse bunu otomatik yükseltiyor (eşikler ve ölçümler için [Ollama sayfası](/kullanim/ollama/) ile [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/)). Bağlamı sessizce kırpmanın ölçülmüş kanıtı orada: `num_ctx` 512 iken 688 token'lık istemin 430 token'ı hiç okunmadı ve yanıtta hiçbir uyarı yoktu.

## Beş Kesim Düğmesi, Tek Dağılım

Sıradaki token için altı adayın logitleri 6, 5, 4, 3, 2, 1 olsun. Aşağıdaki olasılıklar softmax'tan **elle** hesaplandı; gerçek bir modelin dağılımı değil, gösterim.

| `temperature` | en olası aday | `top_p` 0,9 kaç aday tutar | `min_p` 0,1 kaç aday tutar |
| --- | --- | --- | --- |
| 0,3 | 0,964 | 1 | 1 |
| 0,8 | 0,714 | 2 | 2 |
| 1,5 | 0,496 | 4 | 4 |

Üç kesimin kestiği şey farklı, ve bu tablo onun için var:

- **`top_k` sayıyı sabitler.** "En olası 40 aday" der, olasılık toplamına bakmaz. Dağılım sivriyken (düşük sıcaklık) bu 40'ın 39'u zaten ihmal edilebilir olasılıktadır, kesimin etkisi olmaz; dağılım düzken 40 adayın içi gerçek adaylarla dolar ve yanlış seçim olasılığı yükselir.
- **`top_p` toplamı sabitler.** Adayları azalan sıraya dizer ve birikimli toplam 0,9'a ulaşınca kalanı atar. Kümenin büyüklüğü dağılıma göre değişir: yukarıdaki satırlarda 1, 2, 4 aday.
- **`min_p` bağıl eşik koyar.** "En olası adayın en az onda biri kadar olasılığı olsun." Kuyruğu biçimi itibarıyla sıcaklıktan **etkilenir** — o yüzden `min_p`, `temperature`'ın etkisini bastırmaz; düşük sıcaklıkta kesim zaten kendiliğinden sertleşir, tabloda görünen bu.

Bu üçünün hangi sırada uygulandığını Ollama belgesi sıralı olarak tanımlamıyor; bu sayfada sıra iddiası yok. Pratik sonuç: tek başlarına etkileri, sıralarından daha belirleyici.

## Üretim Nerede Biter: `num_predict`, `stop`, EOS

Üretimin üç yerde bitme biçimi var ve üçü yanıtta farklı görünür.

| Bitiş | Yanıtta görünen | Anlamı |
| --- | --- | --- |
| Model kendi biter | `done_reason: stop` | EOS ya da `stop` dizgisi üretildi; cevap tam |
| Uzunluk sınırına değer | `done_reason: length` | `num_predict` bitti; cevap **cümlenin ortasında kesik** |
| Cevap boş döner | `done_reason: stop`, içerik boş | şablon/uygulama uyuşmazlığı; boş içeriği kullanıcıya göstermeden önce ayıklayın |

İkinci satır yerel kurulumların en sık sessiz arızası. [Ajan Ölçümü](/ajan/ajan-olcumu/) sayfasında bu gerçekten yaşandı: `num_predict: 300` sınırına takılan cevap cümlenin ortasında bitti, HTTP 200 döndü, logda hata yoktu. [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/) kaydında da kesik (`length`) ve tam (`stop`) bitişler birlikte görülüyor. İzlemede `done_reason` alanına bakmıyorsanız, "yarım cevap" kullanıcı şikâyeti olarak geri gelir.

Üçüncü satırın ölçeği önemli: `num_predict` **token** sayar, kelime değil. Türkçe metin ~2,99 karakter/token üretiyor — bu [Hız ve Maliyet sayfasında ölçülmüş bir oran](/kullanim/hiz-ve-maliyet/). Kaba hesap: `num_predict: 40` Türkçe'de yaklaşık 24 kelime, bir-iki cümle demektir. Uzun cevap istiyorsanız sınırı yükseltin; kısaltmak istiyorsanız sınırın kelimeyle değil tokenla çalıştığını hesaba katın.

:::tip[Uzun cevabı kesmek yerine yapılandırın]
"Uzun yaz" demek yerine "üç madde yaz" deyin ve sınımı istemde yapın; sonra `num_predict`'i o biçime göre bir tamponla (ör. beklenenin iki katı) açın. Kesilmiş cevapla tam cevabı ayırt eden tek şey `done_reason`.
:::

## Sıcaklık 0: "Aynı Girdi, Aynı Çıktı" Garantisi mi?

`temperature: 0` dağılımı örneklemez, her adımda en olası adayı seçer (açgözlü üretim). Bu, karşılaştırma sayfalarının neden sıcaklığı sıfırda tuttuğunun gerekçesi: [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/), [Ajan Ölçümü](/ajan/ajan-olcumu/) ve [Enjeksiyon Ölçümü](/ajan/enjeksiyon-olcumu/) koşumlarının hepsi `temperature: 0` ve açık `num_predict` ile çalıştırıldı; iki ölçüm arasındaki farkı örneklem gürültüsünden ayırmanın yolu bu.

Garanti mi? Artık ölçülmüş bir cevabı var, ve cevabı üretim uzunluğuna göre değişiyor. [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasında aynı istem onar kez koşuldu: 5 token'lık kısa cevapta sıcaklık sıfır, **tohum gönderilmeden** yirmi isteğin yirmisinde de karakter karakter aynı dizgiyi üretti; 68 token'lık serbest üretimde de tohumla sabitlenen cevap iki ayrı dizde birebir aynı kaldı. Ama `num_predict` gönderilmeden yapılan 1000+ token'lık üç uzun üretimde aynı sıcaklık sıfır, aynı istem **farklı uzunluklar** verdi (1060, 1460, 1460 token). Yani "sıcaklık 0 yeter" kuralı kısa çıktıda bu makinede tutuyor, uzun çıktıda tutmadı; farkın nedenini ayırt eden kol ölçülmedi. Ölçüm sayfalarının hepsinde `temperature: 0` yanında **açık** `num_predict` gönderilmesinin gerekçesi bu.

## Yapılandırılmış Çıktı: `format` Alanı

Ollama'nın API belgesinde `format` alanı iki şey kabul ediyor: `"json"` ya da doğrudan bir **JSON şeması**. İkincisi birincisinden daha işinize yarar, çünkü "geçerli JSON" ile "sizin alanlarınız" aynı şey değil.

```python
istek = {
    "model": "qwen2.5:3b-instruct-q4_K_M",
    "messages": [{"role": "user", "content": soru}],
    "format": {
        "type": "object",
        "properties": {
            "cevap": {"type": "string"},
            "kaynak_var": {"type": "boolean"},
        },
        "required": ["cevap", "kaynak_var"],
        "additionalProperties": False,
    },
    "stream": False,
    "options": {"temperature": 0, "num_predict": 200},
}
```

Bu sayfa şemayı kendisi koşmadı; gövde biçimi [Ollama API belgesinden](https://docs.ollama.com/api/chat), alan adları oradan alındı. Aynı gövde biçimi [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasının D kolunda onar tekrarlı olarak gerçekten koşuldu: `"json"` ile şemanın farkı ölçüldü ve token tavanının JSON'u nasıl bozduğu görüldü. OpenAI uyumlu bir sunucuya geçince aynı niyet `response_format` alanına, sunucu tarafında ise şemayı gerçekten zorlayan ayrıştırıcıya denk geliyor — karşılaştırma [API Sunumu sayfasında](/kullanim/sunma-api/).

:::caution[Şema biçimi garanti eder, içeriği garanti etmez]
`format` sizi biçim bozukluğundan — ayrıştırılamayan çıktı, eksik alan — korur; uydurulmuş değerden korumaz. İki ölçülmüş örnek: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasının D kolunda şemayla üretilen on cevabın alan adları ononda aynıydı (`yil`, `gerekce`) ama `yil` değeri on istekte **dört farklı yıla** dağıldı. İkincisi, [Ajan Ölçümü](/ajan/ajan-olcumu/) sayfasındaki C senaryosunda araç yanlış çağrıldı ve model sonuçta hiç olmayan **"3600 metredir"** sayısını üretti. Biçim doğru, içerik yanlıştı. Aynı sebeple araç argümanlarını doğrulama katmanı şemadan ayrıdır; kötü niyetli belgeye tepki kısmı ise [Prompt Enjeksiyonu sayfasında](/ajan/prompt-enjeksiyonu/).
:::

Aynı belgede geçen `think` alanı, destekleyen modellerde "akıl yürütme" bölümünü açma/kapama denetimi; bu sitede ölçülmedi, çünkü burada koşan Qwen2.5 modelinin düşünme modu yok. `logprobs` ve `top_logprobs` ise artık ölçülmüş durumda: [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) sayfası bu iki alanın Ollama'da fiilen ne döndürdüğünü, `top_logprobs` tavanının 20 olduğunu ve `logprobs` gönderilmediğinde `top_logprobs`un **sessizce yok sayıldığını** tek tek koşarak gösterdi.

## Tohum: `seed`

`seed`, örnekleme zincirinin başlangıcını sabitler; sıcaklığın **sıfır dışında** olduğu her koşumda tekrarlanabilirliğin tek çaresi bu. Belge varsayılanı 0. İki uyarı:

- Aynı tohum, aynı **istem** ile birlikte anlamlı. İstem bir token bile değişirse (RAG'da bağlama giren parça farklıysa) tohum aynı kalsa da örnekleme zinciri başka adımdan devam eder; sabit tohumu "aynı sonuç" sanmak, iki koşumu karşılaştırırken yapılan en sık hata. Bağlamın kendisinin ne kadar oynadığı ölçülmüş bir konu: [Parçalama ve Hibrit Arama](/rag/parcalama-ve-hibrit-arama/) sayfasında vektör araması beklenen parçayı bir soruda **14. sıraya** düşürdü, yani `k=4` bağlam penceresinin dışına.
- Tohumun **değeri** ile **etkisi** ayrı şeyler. Ölçülmüş hâli: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasında sıcaklık 0,8'de tohum 1234 ile tohum 9999 aynı cevabı verdi (onar isteğin yirmisi de aynı dizgi), tohumsuz aynı ayar ise on istekte beş farklı cevaba dağıldı. Tohum zinciri sabitler; hangi cevaba düşüleceği dağılımın kendisine bağlı kalır.
- Tohumu sonucu bildirirken yanında verin. [Benchmarklar](/degerlendirme/benchmarklar/) sayfasının beşinci maddesi aynı noktaya değinir: örnekleme ayarları sabitlenmezse aynı model iki farklı görünür.

## Pratik Karar Listesi

- Ölçüm/karşılaştırma yapıyorsanız: `temperature: 0`, açık `num_predict`, sabit `seed`, sabit model etiketi, sabit `num_ctx`. Neden hepsi: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasında uzun üretimde sıcaklık sıfır tek başına aynılığı korumadı, açık tavan gönderilmeyince üretim 1460 token'a kadar çıktı.
- Yaratıcılık istiyorsanız: sıcaklığı 0,8-1,1 bandında tutup `top_p` ile oynayın; aday kümeniz zaten 40'tan kısaysa `top_k`'yı büyütmenin faydası yok.
- Makineden makineye taşınabilirlik: `PARAMETER` satırına güvenmeyin, değeri istekte gönderin.
- Uygulama çıktıları: JSON şeması **ve** alan doğrulaması; `done_reason` kontrolü; boş içerik uyarısı.
- Kendi makinenizin fiilî varsayılanını öğrenmek: `ollama show --modelfile`, gerekirse `scripts/gguf-baslik.py`.

## Kaynaklar ve ileri okuma

- [Ollama Modelfile başvurusu](https://docs.ollama.com/modelfile/) — `PARAMETER` adları ve varsayılan tablosu; buradaki 0,8 / 40 / 0,9 / 0,0 değerleri bu sayfadan alındı (son doğrulama 2026-10-17).
- [Ollama Modelfile aynası (readthedocs)](https://ollama.readthedocs.io/en/modelfile/) — aynı tablonun `repeat_penalty` 1,1, `num_predict` 128 yazan ve `mirostat`/`tfs_z` satırlarını içeren kopyası; iki belgenin uyuşmadığı yerin kanıtı.
- [Ollama API başvurusu](https://docs.ollama.com/api/chat/) — `format`, `think`, `keep_alive`, `logprobs` alanlarının biçimi.
- [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/) — `logprobs` ve `top_logprobs` alanlarının bu makinede ölçülmüş davranışı; bu sayfanın "ölçülmedi" diye bıraktığı borcun kapandığı yer.
- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — `num_ctx` kırpması, Türkçe karakter/token oranı ve faz süreleri; bu sayfadaki atıfların ölçülmüş kaynağı.
- [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) — bu sayfanın "ölçülmedi" diye bıraktığı üç iddianın (varsayılan `num_predict`, sıcaklık 0 garantisi, `"json"` ile şema farkı) onar tekrarlı ölçümü.
- [Ajan Ölçümü](/ajan/ajan-olcumu/) — `done_reason: length` ile kesilen cevabın ve uydurulan araç argümanının gerçek kaydı.
- [Tokenizasyon](/temeller/tokenizasyon/) — Türkçe metnin neden daha çok token yediğinin dilbilgisel nedeni.


