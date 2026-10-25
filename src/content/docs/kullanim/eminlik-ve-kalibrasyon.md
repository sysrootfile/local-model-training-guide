---
title: "Eminlik ve Kalibrasyon: Model Kendinden Ne Kadar Emin?"
description: "Ollama'da logprobs ve top_logprobs fiilen ne üretir, kayıt sayısı ile üretilen token sayısı neden farklıdır, P(True) kalıbı Türkçe çoktan seçmelide konum yanılgısına mı düşüyor, sıcaklık bildirilen olasılığı değiştiriyor mu, sözlü güven kaç soruda okunabiliyor — 2026-10-17 kayıtlarından ölçülmüş sayılar."
dogrulama: 2026-10-19
---

Bir modelin "bilmiyorum" demesini istemek, ürettiği metnin kalitesinden ayrı bir iştir. Bunu yapmanın tek yolu modele iç durumunu sormak değil; üç ayrı güven kaynağı var: **üretim olasılığı** (model doğru şıkkı token token ne kadar olası görüyor), **öz-tutarlılık** (aynı soruyu örnekleyince aynı cevaba mı düşüyor) ve **sözlü beyan** (model kendine kaç puan veriyor). Bu sayfa üç kaynağı da bu makinede koştu ve bir de dördüncü şeyi ölçtü: **Ollama'nın `logprobs` alanı belgeye göre mi davranıyor, yoksa belgeyi okurken sandığımızdan farklı mı?**

:::note[Künye: dört koşum, tek makine]
Betik: `ornekler/eminlik-olcu/eminlik.py`. Kayıtlar: `ornekler/eminlik-olcu/cikti/` altında
`prob.txt` (A + H sözleşme probu, **2026-10-17 22:09:25 → 22:09:59**, 27 çıkarım isteği),
`olcum.txt` (B–F tam koşumu, **23:05:00 → 23:10:02**, 5 dakika 2 saniye, 176 sohbet + 100 gömme isteği),
`g2.txt` (G kolu düzeltilmiş ayrıştırıcıyla, **23:12:27 → 23:13:16**, 10 sohbet isteği) ve
`kontrol-b.txt` (B hanesi kontrolü, 23:04:00 → 23:04:33).
Ollama **0.40.5**, modeller `qwen2.5:3b-instruct-q4_K_M` ve `bge-m3`, CPU'da; adres `http://127.0.0.1:11434`. [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasının koşumu 0.40.4 ile alınmıştı; bu sayfanın kayıtları 0.40.5'tendir. Makinenin sunucusu 2026-10-19'da 0.40.6; bu sayfadaki sayılar o sürümde yeniden ölçülmedi.
Altın cevaplar modelin ezberinden değil, bu sitede zaten belgelenmiş sayfalardan elle yazıldı. Koşumlar sırasında başka Ollama isteği gönderilmedi.
:::

## `logprobs` Fiilen Ne Üretiyor

`/api/chat` gövdesine `"logprobs": true` eklediğinizde yanıtta bir `logprobs` alanı geliyor; her kayıtta `token`, `logprob`, `bytes` alanları var (prob.txt A1). `top_logprobs` sayısını da gönderirseniz dördüncü alan olarak `top_logprobs` ekleniyor ve o konumun aday listesi geliyor (A2). Ölçülen sınırlar:

| İstek | Sonuç |
| --- | --- |
| `top_logprobs` gönderilmedi | aday listesi yok (`min 0 / max 0`), `token`/`logprob`/`bytes` geldi |
| `top_logprobs = 1` … `20` | istenen aday sayısı birebir döndü (5 → 5, 10 → 10, 20 → 20) |
| `top_logprobs = 0` | aday alanı geldi ama liste boş |
| `top_logprobs = 100` | **HTTP 400**, gövde: `{"error":"top_logprobs must be between 0 and 20"}` |
| `top_logprobs = 5` ama `logprobs: false` | **`logprobs` alanı hiç gelmedi** — `top_logprobs` sessizce yok sayıldı |

Son satır bu sayfanın en kullanışlı bulgusu: alanı göndermek ile alanın gelmesi aynı şey değil. Ölçüm kodu "istedim, o yüzden vardır" varsayarsa sessizce boş elle tutulur; kontrol edilecek şey isteğin gövdesi değil, **yanıtta `logprobs` anahtarının bulunup bulunmadığı**.

**Kayıt sayısı ile token sayısı farklı.** Üretilen token sayısı (`eval_count`) ile logprob kaydı arasında bu makinede hep 1 fark vardı:

```text
A1 | ctki 18 | logprob kaydi 17      (serbest üretim)
A3 | ctki  1 | logprob kaydi  1      (num_predict=1)
A7 | ctki 36 | logprob kaydi 35      (format=json)
```

Fark tek başına "model bir token daha üretti" anlamına gelmiyor; dizinin sonundaki durma tokenının logprob kaydının mı üretildiği, yoksa `eval_count`'un mu bir fazla saydığı **bu kafeste ayırt edilmedi**. Pratik sonuç: bir dizinin ortalama logprobunu alırken payda `eval_count` değil, **kayıt sayısı** olmalı. Bu sayfada tüm ortalamalar kayıt sayısına bölünerek alındı.

## Aynı İstem, Aynı Logprob — Ta ki Model Yeniden Yüklenene Kadar

Sıcaklık sıfırda üç tekrar, üç ayrı ayar (prob.txt H1–H3): tohumlu, tohumsuz ve tek token. Üçünde de token dizisi ve logprob değerleri **bit bit aynı** döndü. [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasının A kolunda ölçülen "T=0'da birebir aynılık" burası için de tutuyor; üstelik aynılık metinde değil, kesirli sayılarda da var.

Ama `keep_alive: 0` ile model düşürülüp aynı istem yeniden gönderildiğinde (H4):

- soğuk ilk istek **6,68 sn**, sonraki iki sıcak istek 1,38 ve 1,37 sn;
- üretilen tokenlar yine birebir aynı;
- logproblar aynı değil: **en büyük mutlak fark 0,2286**, ilk fark `i` tokenında.

Kaydı sayısal olan bir fark da iki ayrı koşum arasında görüldü: aynı soruda `P(C)` `kontrol-b.txt` koşumunda 0,9634, `olcum.txt` koşumunda 0,9613. Kaymanın nedeni (toplama yolu, önbellek durumu, makine yükü) ayırt eden bir kol yazılmadı; **nedeni ölçülmedi**. İki sonuç: eşik kalibrasyonunu sabit bir yükleme durumunda yapın, ve farklı oturumlardan alınan logprobları ondalık basamağına kadar karşılaştırmayın.

## Türkçe, Şema ve Yirmi Aday Tavanı: Olasılığın Okunmasını Bozan Üç Durum

**Alt-kelime bölünmesi.** Qwen arayüzü Türkçeyi hece hece doğrar: "Marmaray" `M` `arm` `ar` `ay`, "2013" `2` `0` `1` `3` olarak logproba giriyor. İlk tokenda adaylar `M` 0,9668 / `1` 0,0113 / `İ` 0,0075 / `I` 0,0044 — yani model "Marmaray" mı, "1913 mü" mü, "İstanbul" mu diyeceğini ilk hecede kararlaştırıyor. Türkçe karakterin kendi başına olasılığı da ölçüldü (A9): `I` 0,5014, `İ` 0,1418, `H` 0,0525. Noktalama işaretleriyle birlikte bu, **tek tokenlık bir altın cevabı Türkçede imkânsız kılıyor**; bu kafesin çoktan seçmeli tasarımı bu yüzden harf ister.

**Kısıtlı üretim dağılımı şekillendiriyor.** `format: "json"` ve JSON şeması koşullarında ilk konumun en yüksek adayı neredeyse sabit: `'{\n'` 0,9969 (A7) ve 0,9975 (A8). Serbest biçemde aynı soru "2013" derken, iki alanlı JSON biçeminde model `"yil": 2022` üretti. **Bunu tek başına `format` alanına yazmıyoruz**: iki istemin sözcükleri de farklıydı, yani değişken tek değildi. Yine de okunacak şu var — şema, ilk tokenda olasılığın neredeyse tamamını yapı karakterine koyuyor; bu durumda "dizin olasılığı" ile "içeriğin doğruluğu" ayrı şeyler.

**Kuyruk görünmüyor.** `top_logprobs` 20 ile sınırlı olduğundan entropi yalnız o 20 adayın yeniden normalize edilmesiyle hesaplanabiliyor; 20'den uzun kuyruk hiç görünmez. Bu yüzden bu sayfadaki tüm entropi sayıları **alt sınırdır** ve kayıtlarda öyle etiketlendi: `prob.txt`'te `[ALT SINIR]`, `olcum.txt`'te `kirpik ent` (kırpılmış entropi).

## `P(secilen)`: Doğru Şıkkın Olasılığı Değil, Seçilen Şıkkın Olasılığı

20 bilgi + 6 "bilinemez" soru, dört şık, altın şıkkın yeri soru sırmasına göre döndürülerek tek harf istendi (`num_predict=1`, T=0, `top_logprobs=20`). A şıkkının kütlesi `A`, `A)` ve `A:` birebir eşleşen adayları toplayarak bulundu ve dört harfin kütlesi üzerinden yeniden normalize edildi (P(True) kalıbı).

Bu koşumun kendisi enstrümanın bozukluğuna dair bir bulgu üretti (`olcum.txt`, B özeti):

| Ölçülen | Değer |
| --- | --- |
| Doğru şık | 6/20 (0,30) |
| Seçilen harf dağılımı | A 0, B 3, **C 16**, D 1 |
| `P(secilen)` doğrularda | ort 0,8885 (aralık 0,6043–1,0000) |
| `P(secilen)` yanlışlarda | ort 0,9253 (aralık 0,6399–1,0000) |
| Ayırma payı (en kötü doğru − en iyi yanlış) | **−0,3957** |

Model yirmi sorunun 16'sında **C** demiş. Bu durumda `P(secilen)` bilginin değil konum yanlılığının ölçüsüdür; betik bu yüzden bir geçersizlik kapısı kurdu ve tek bir harf oyların yarısından çoğunu aldığında eşik/risk tablosunun ayırıcı sayılmayacağını loga yazdı. Yine de eşiği taradık, çünkü sayının kendisi de bulgu:

| Eşik τ (`P(secilen) ≥ τ` ise cevap ver) | Kapsama | Risk (kapsananlardaki hata) |
| --- | --- | --- |
| 0,30 – 0,60 | 1,00 (20/20) | 0,700 |
| 0,70 | 0,85 (17/20) | 0,706 |
| 0,80 – 0,90 | 0,80 (16/20) | 0,750 |
| 0,95 | 0,65 (13/20) | 0,692 |
| 0,99 | 0,45 (9/20) | 0,556 |

Eşik 0,99'a çekilince risk 0,700'den 0,556'ya iniyor ama kapsama yarıya yakınına düşüyor; yani bu modelde, bu soru setinde, olasılık eşiği **hatayı ancak cevapların yarıdan azını vermeyi göze alırsanız** biraz azaltıyor.

:::caution[Eşiği altın etiket üzerinde kurmayın]
Logda `P(altin)` satırları `[analiz]` etiketiyle ayrı yazıldı: doğrularda ort 0,8885, yanlışlarda ort 0,0044. Bu, "model yanlış bildiği şıkkın olasılığını neredeyse sıfır görüyor" demektir — ama üretim anında altın etiketi bilmediğinize göre bu sayı eşik kuramaz. Eşik **her zaman seçilen cevabın olasılığı** üzerinde taranır; altın üzerinden tarama etiketi sızdırır ve kendine yarar bir sonuç üretir.
:::

**Bilinemez sorular.** Altı sorunun altın şıkkı "Hiçbiri / bilmiyorum"du. İkisinde model gerçekten o şıkkı seçti; dördünde bilinen bir şeyi seçti ve kütle fena değildi: 0,5367, 0,8617, 0,9707, 0,8087. Yani kaçınma davranışı bu modelde, bu biçimde, kendiliğinden gelmiyor.

## Sıcaklık, Bildirilen Olasılığı Değiştirmiyor

Aynı sorular T = 0 / 0,7 / 1,0'da sabit tohumla (1234) üçer kez gönderildi. **On sorunun onunda da seçilen harf değişmedi**; `P` değerinin üç sıcaklık arasındaki aralığı dokuz soruda 0,00000, birinde 0,00001. Yani Ollama'nın bildirdiği logprob bu makinede sıcaklıktan bağımsız: soğutarak olasılıkları "keskinleştiremezsiniz".

:::tip[Karıştırmayın]
Bu, kalibrasyon literatüründeki *sıcaklık ölçekleme* (temperature scaling) tekniğinin tersi değildir — orada sıcaklık, logits üzerinde sonradan uygulanan bir dönüşümdür ve dağılımı gerçekten değiştirir. Burada ölçülen şey şu: Ollama'nın **size bildirdiği** sayı, çıkarım sıcaklığından etkilenmiyor. Hangi adımda hesaplandığını bu ölçüm açıklamıyor; yalnızca bildirim etkilenmiyor.
:::

## Serbest Cevapta Ortalama Logprob: En Emin Satır Yanlış Çıktı

Aynı on sorunun cevabı bu kez şık metni olarak istendi (64 token tavan, T=0). Ortalama logprob −0,4680 ile −0,0018 arasında dağıldı; içerik doğruluğu **3/10** (logdan sayıldı: D2, D3, D10). Sıra tuhaftı:

| Satır | Ortalama logprob | Cevap | Altın |
| --- | --- | --- | --- |
| D10 | −0,0018 | `B) $0,07/GB-ay` | `$0,07/GB-ay` — doğru |
| D9 | −0,0028 | `C) 88.838` | `37` — **yanlış** |
| D4 | −0,0706 | "bge-m3 768 boyutlu vektör üretir" | `1024` — **yanlış** |

−0,0028 yaklaşık **0,997** demektir; model yanlış cevabı neredeyse kesinlikle verdi. D4'te de aynı kesinlikle yanlış boyut söyledi. Öte yandan kırpılmış entropi burada işe yaradı: D9'un entropi ortalaması 0,0173 (maks 0,0792) iken, uzun ve dağınık D3'te 0,8391 (maks 2,7541). Dizinin logprob'u bir **özgüven** ölçüyor, doğruluk ölçmüyor.

## Öz-Tutarlılık ve Semantik Entropi: Çeşitlilik Çıkmayınca Entropi de Çıkmıyor

Soru başına on örnek, T=0,8 (`olcum.txt`, E kolunun özeti; 100 satırlık ham seçim dökümü logda duruyor): **on sorunun onunda da uyuşma 1,00** — yüz seçimin 80'i C, 20'si B, hiçbiri A veya D. Çoğunluk şıkkı üç soruda doğruydu. Yani örnekleme gürültüsü bu görevde çeşitlilik üretmedi; literatürün "aynı soruyu on kez örnekley" ilacı, tek harfe sıkışmış ve harf yanlılığı olan bir görevde işlemedi.

Serbest metin kolunda toplanan yüz cevap bge-m3 vektörleriyle kümelendi. Kosinüs eşiği 0,70'te küme sayısı ortalaması 1,90 (en fazla 5), semantik entropi ortalaması 0,3290; 0,80'de 2,20 (en fazla 7) ve 0,4426. **On sorunun altısında tek küme** çıktı, yani semantik entropi sıfır. Yöntem iki yerden özgün tariften sapıyor ve sapma kayıtta duruyor: özgün tanım çift yönlü entailment (NLI) ister, burada kosinüs kullanıldı; açgöz kümeleme kümenin **ilk** örneğiyle karşılaştırıyor, ortalamayla değil. Eşik 0,70→0,80 değişince aynı cevap kümesinde küme sayısı 2→3 ve 5→7 oldu — küme sayısının kendisi eşik-duyarlı bir sayı.

:::caution[Gürültü küme sayısını şişiriyor]
İki örnek, modelin istemi tekrarlamasından gelen "talimat yankısı" metinleriydi. O soruda (F2) 0,70'te 5, 0,80'de 7 küme çıktı; yankı temizlenmedi, logda `talimat yankisi 2` olarak sayıldı ve bırakıldı. Otomatik kaçınma eşikleri kurarken bu artefakt, gerçek çeşitlilik gibi görünür.
:::

## Sözle Bildirilen Güven: Etiket Yoksa Sayı Anlamsız

İlk koşumda modelden cevabın altına 0–100 arası bir sayı istedik. Model sayıyı çoğu kez **talimatı yankılayarak** üretti; ayrıştırıcı da son boş satırdaki ilk sayıyı aldı. Sonuç kayıtta böyle görünüyor (`olcum.txt`, G bloğu):

```text
G2  |  3.97 sn | guven 1  | cevap dogru mu HAYIR | 'A) 128.256 /  / 1 ile 100 arasinda tek bir tam sayi: 50'
G9  |  4.25 sn | guven 88 | cevap dogru mu HAYIR | 'C) 88.838 /  / Bu derlemenin Türkçeki kısım 88.838 mesajlık bir Türkçe'
```

Modelin kastettiği sayı **50**, ama satırın başındaki "1" ayrıştırıcıya güven olarak okundu. G9'da da benzer bir belirsizlik var: okunan 88, cevap metnindeki `88.838` sayısı ile çakışıyor; hangi sayıdan geldiği bu logdan ayırt edilmez. Bu yüzden G kolunun ayrıştırıcısı yalnızca `GUVEN:` etiketiyle gelen sayıyı okuyacak şekilde düzeltildi ve kol yeniden koşuldu (`g2.txt`). Yeni ölçüm:

- **7/10 soruda** etiket geldi; 3'ünde gelmedi ve ortalamalara **girmedi** (fail-closed).
- Okunan güvenlerin ortalaması 53,7 (0–88 aralığı).
- Yanlış cevaplarda güven 26, 85, 85, 0, 88, 7 (ort 48,5); **doğru tek cevapta 85** (n=1).

Bu haliyle sözlü güven bu makinede kullanılamaz: 10 sorudan 3'ü okunamıyor, okunanlarda model yanlış cevaba 85–88 veriyor, doğru cevabın tek örneği de 85. Yani yanlış ile doğru, beyan edilen sayıda da ayrılmıyor — literatürün "aşırı güven" (overconfidence) dediği davranışın bu modeldeki ölçümü. İlk (bozuk) araçla elde edilen "ortalama 16,2" sayısı **geçersizdir ve hiçbir yerde kullanılmadı**.

## Bugün Ne Yapılır

- **Güven sinyali istiyorsanız `P(secilen)` ile başlayın**, `P(altın)` ile değil; eşiği kendi verinizde tarayın. Bu kafesin τ taraması 20 soruda, tek modelde, altınları elle yazılmış bir sette ölçüldü — oradan çıkan sayı sizin uygulamanızın eşiği değildir.
- **Şık harfi yerine şık metni** isteyin ve metin eşleşmesini rakam/nokta sınırlarıyla yapın (`8` altını `128` içinde geçersiz pozitif üretir); harf tasarımında konum yanlılığını ayrı ölçüp raporlayın.
- **Ortalama logprobu kayıt sayısına bölün**, `eval_count`'a değil.
- **Entropiyi alt sınır olarak bildirin**; `top_logprobs` 20 ile sınırlı.
- **Kaçınmayı davranışla kurun**, olasılıkla değil: modele "bilmiyorum" şıkkını açıkça gösterin ve o şıkkı seçme oranını ölçün (burada 2/6).
- Ölçümü **aynı yükleme durumunda** yapın; soğuk/sıcak farkı logprob'u 0,2286 kaydırabiliyor.

## Ölçülmedi

- Tam sözlük entropisi (`top_logprobs` tavanı 20 olduğu için erişilemez).
- Nicemlenmiş modelde güven davranışı: Q4 ile Q8/Q16 karşılaştırması yeni indirme gerektirir, bu ayak izinde yok; bkz. [Niceleme](/kullanim/quantization/).
- **ECE, güven aralıkları ve sıcaklık ölçekleme uydurması.** N=20 ve N=6 için güven aralığı hesaplanmadı; bu sayfadaki tüm oranlar nokta tahminidir. Küçük örneklemde ECE tahmincisinin yanıltıcı olduğunu gösteren çalışma kayıtlarda duruyor (aşağıdaki Kaynaklar).
- Bağlam (RAG) verildiğinde kalibrasyonun değişmesi, zincirleme türetme koşulunda `P` karşılaştırması, ajan döngüsünde güven eşiği kullanımı. Eşiğin **başka bir veri setine taşınırken** nasıl geçersizleştiği benzerlik tarafında ölçülmüş durumda: [RAG Değerlendirmesi](/rag/rag-degerlendirme/).
- `eval_count` ile logprob kaydı arasındaki 1'lik farkın hangi taraftan geldiği.

## Kaynaklar ve ileri okuma

- [Ollama Chat API başvurusu](https://docs.ollama.com/api/chat/) — `logprobs`, `top_logprobs`, `format` alanlarının gövde biçimi (son doğrulama 2026-10-17).
- [On Calibration of Modern Neural Networks (arXiv:1706.04599)](https://arxiv.org/abs/1706.04599) — Guo ve ark., ICML 2017; ECE tanımı ve sonradan sıcaklık ölçekleme.
- [Language Models (Mostly) Know What They Know (arXiv:2207.05221)](https://arxiv.org/abs/2207.05221) — Kadavath ve ark.; doğru şıkkın olasılığını diğer şıklar üzerinde normalize eden P(True) kalıbının kaynağı.
- [Self-Consistency Improves Chain of Thought Reasoning (arXiv:2203.11171)](https://arxiv.org/abs/2203.11171) — Wang ve ark.; aynı soruyu çok örnekleyip çoğunluk alma, bu sayfada E kolu.
- [Semantic Uncertainty (arXiv:2302.09664)](https://arxiv.org/abs/2302.09664) — Kuhn ve ark.; anlam düzeyinde entropi. Nature 2024 cilt 630, sayfa 625–630'da yayımlandı.
- [Just Ask for Calibration (arXiv:2305.14975)](https://arxiv.org/abs/2305.14975) — Tian ve ark., EMNLP 2023; insan geri bildirimiyle hizalanmış modellerden sözlü güven istemenin ECE'yi yarıya indirmesi. Buradaki G kolu onun "iste" kısmını test ediyor, ECE kısmını test etmiyor.
- [Can LLMs Express Their Uncertainty? (arXiv:2306.13063)](https://arxiv.org/abs/2306.13063) — Xiong ve ark.; sözlü beyanlarda aşırı güven ve ölçek tuzakları.
- [Know Your Limits: A Survey of Abstention in Large Language Models (arXiv:2407.18418)](https://arxiv.org/abs/2407.18418) — Wen ve ark., TACL 2025; kaçınmanın hangi yolla sağlandığının sınıflandırması.
- [When Quantization Affects Confidence of Large Language Models? (arXiv:2405.00632)](https://arxiv.org/abs/2405.00632) — Proskurina ve ark.; nicemlemenin güven dağılımını kaydırması — bu sayfada **ölçülmedi**.
- [Revisiting Accuracy-Confidence Consistency in Neural Networks (NeurIPS 2021, cilt 34, 15682–15694)](https://proceedings.neurips.cc/paper/2021/hash/c91e5a8a9e1a6b4e04c05e90edbf2bcb-Abstract.html) — Minderer ve ark.; küçük örneklemde ECE tahmincisinin neden yanıltıcı olduğu.
- [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/) — `logprobs` alanının belge tarafı ve bu sayfanın kapattığı "denenmedi" notu.
- [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) — T=0 aynılığı, `num_predict` tavanı ve şema/içerik ayrımı; bu sayfanın H ve A7–A8 satırlarının tamamlayıcısı.
- [Tokenizasyon](/temeller/tokenizasyon/) — Türkçenin alt-kelime bölünmesinin dili.
- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — bu kafesin birim maliyeti: taze ~100 tokenlık istemle `num_predict=1` + `top_logprobs=20` isteği 2,1–2,9 sn, önbelleği sıcak aynı istem 0,10–0,15 sn.
