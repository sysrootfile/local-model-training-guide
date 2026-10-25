---
title: "Ajan Ölçümü: Tur, Token ve Saniye Karşılığı"
description: "Örnek 7'nin ajan döngüsünü bu makinede koşan kayıt: sabit hatta karşı tur başına duvar süresi, önbellek kazancı, araç tanımının token gideri, tool_choice ve format alanlarının gerçek davranışı."
dogrulama: 2026-10-19
---

Bu sayfadaki her satır `ornekler/ajan-dongusu/cikti/ajan-kaydi.txt` kaydından alınmıştır; koşum **2026-10-16, 02:11-02:18** arasında, tek bir Python süreciyle, başka Ollama isteği gönderilmeden yapılmıştır. Makine: AMD Ryzen 5 2600 (6 çekirdek/12 iş parçacığı), 15,9 GB RAM, SATA SSD, Ollama 0.40.4 (makine 2026-10-19'da 0.40.6; bu sayfadaki sayılar o sürümde yeniden ölçülmedi), sohbet modeli `qwen2.5:3b-instruct-q4_K_M`, gömme modeli `bge-m3`. Aşağıdaki sayılar o donanımın sayılarıdır; başka bir makinede bantlar değişir, sıralama genellikle değişmez.

Ölçülen iki hat aynı Vikipedi korpusu (125 parça) ve aynı sorularla çalışıyor. Sabit hat Örnek 6'nın yaptığı: soruyu göm, parça getir, bağlamı okut. Ajan döngüsü ise [Mekanik sayfasındaki](/ajan/arac-cagirma-ve-mcp/) `for` döngüsünün kendisi: aracı model çağırıyor, sonucu görüyor, sonra ya cevap veriyor ya tekrar çağırıyor. Tur tavanı 5, `num_predict` 300.

:::note[İlk sayı soğuk başlangıcın sayısını içeriyor]
Koşum başladığında Ollama'da hiç model yüklü değildi (`ollama ps` boş). Bu yüzden sabit hattın arama adımı **10,79 sn** sürdü: o süre, sorguyu gömmek için `bge-m3`'ün belleğe yüklenmesidir. Örnek 6'nın sıcak ölçümü **0,09-0,13 sn**. Benzer şekilde sabit hattın üretim çağrısında `yük 7,64` sn görünüyor; sonraki tüm turlarda 0,01 sn. Soğuk/sıcak ayrımı [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasının konusu; burada sadece hangi satırın soğuk olduğunu işaretliyoruz.
:::

## Aynı Soru, İki Hat

Soru: "Marmaray hangi yılında hizmete açıldı?"

| Hat | Tur | Duvar süresi | Girdi tokenı | Çıktı tokenı | Olay |
| --- | --- | --- | --- | --- | --- |
| Sabit hat | 1 geçiş | arama 10,79 + üretim 68,03 = **78,8 sn** | 1.926 | 120 | Tek okuma, cevap tam |
| Ajan döngüsü | 2 tur | **95,2 sn** | 2.623 | 336 | Cevap 300 tokenda **kesildi** (`length`) |

Betik kendi satırında "sabit hat 68,0 sn / ajan 95,2 sn" karşılaştırması yazıyor; bu, arama adımını dışarıda bırakan bir okumadır. Arama dahil toplam, üstteki 78,8 sn'dir. İki okuma da geçerli ama ikisini karıştırmak ajanın faturasını olduğundan küçük gösterir: ajan, üretim adımıyla kıyaslanınca **27,2 sn**, arama dahil hatla kıyaslanınca **16,4 sn** daha uzun sürdü.

**Farkın kaynağı tek satırda:** ajan, araçtan dönen 4.994 karakterlik parçayı ikinci turun istemine ekliyor. Aynı soruda ek girdi **697 token**. Kazancı bu kayıttan ölçemiyoruz: iki hat da aynı cevabı verdi ve ajanın cevabı yarıda kesildi.

## Tur Tur Döküm: Ajanın İkinci Turu Neden Pahalı?

| Tur | Duvar | Ön-yükleme | Önbellek | Çözme | `done_reason` |
| --- | --- | --- | --- | --- | --- |
| 1 (araç kararı) | 10,82 sn | 346 tok / 8,12 sn (42,6 tok/sn) | 3 tok | 36 tok / 2,65 sn (13,6 tok/sn) | `stop` |
| 2 (bağlamla cevap) | 84,41 sn | 2.277 tok / 52,13 sn (43,7 tok/sn) | **363 tok** | 300 tok / 32,24 sn (9,3 tok/sn) | **`length`** |

Üç okuma:

1. **Birinci tur ucuz ama sıfır değil.** Araç kararını veren istem 346 token; bunun 273'ü araç kataloğu ve sistem talimatı (aşağıdaki `E` ölçümü). Model cevap üretmiyor, sadece `tool_calls` yazıyor: 36 token.
2. **İkinci tur, ilk turun tümünü tekrar okuyor.** 346 → 2.277 token. Önbellek bunun 363 tokenını bedavaya getirdi; kalan ~1.914 token 43,7 tok/sn bantında yeniden okundu. O bant, [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasının 43,9-45,9 tok/sn ölçümüyle çakışıyor — yani ajanın gecikmesi modelin tuhaflığı değil, bağlamın büyümesi.
3. **Cevap kesildi.** `num_predict: 300` sınırına yapıştı (`done_reason=length`), cümlenin ortasında bitti. Yerelde ajan kurarken bu en sık görülen sessiz hatadır: kullanıcı "yarım cevap" alır, logda hata yoktur. `done_reason` alanına bakmayan her izleme bunu kaçırır.

## Beş Senaryo, Beş Farklı Arıza

| Etiket | Soru | Tur | Duvar | Girdi | Çıktı | Kayıtta görülen |
| --- | --- | --- | --- | --- | --- | --- |
| B2 | Marmaray ve T1 açılış yıllarını karşılaştır | 2 | 61,8 sn | 2.239 | 210 | Cevap **İngilizce** geldi; model tek `viki_ara` çağrısıyla yetindi |
| C | T1 hattının uzunluğu, sonra birim dönüşümü | 2 | 12,1 sn | 794 | 120 | Yanlış araç çağrıldı, sonuçtan **"3600 metredir"** uyduruldu |
| D | Şu an İstanbul'da yağmur yağıyor mu? | 2 | 11,9 sn | 774 | 121 | Araç "eşik altında" metni döndürdü; model 0,496 sayısını kullanıcıya sızdırdı |
| D2 | Tünel füniküler hattı nerede? (`tool_choice="required"`) | 2 | 61,8 sn | 2.087 | 207 | Zorlama alanıyla da aynı iki tur; alanın etkisi ayrı ölçülmedi |
| H | Marmaray sorusu, araç mesajında `tool_name` yok | 2 | 84,4 sn | 2.623 | 253 | Girdi tokenı B ile birebir aynı; döngü bozulmadı |

Bu beş satır "ajan kötü" demek için değil, **ajanın hata biçiminin sabit hattan farklı** olduğunu göstermek için burada. Sabit hatta arıza tek yerden gelir: getirilen parça yanlış. Ajan döngüsünde arıza dört yerden gelebilir — araç seçimi, argümanlar, tur sayısı ve cevap uzunluğu. Dördü de farklı alanlarda görünür: seçim ve argüman `tool_calls` içinde, tur sayısı döngü sayacında, cevap uzunluğu `done_reason` ve `eval_count`ta.

## Araç Tanımının Token Gideri (E)

Aynı istem, aynı sistem talimatı, tek fark: `tools` alanında kaç tanımlı araç var.

| Katalog | Girdi tokenı | Ek gider | Model araç çağırdı mı? |
| --- | --- | --- | --- |
| 0 araç | 73 | — | Hayır |
| 1 araç (`viki_ara`) | 237 | **+164** | Evet |
| 2 araç (`viki_ara` + `birim_donustur`) | 346 | **+273** | Evet |

İki araçlık katalog tek araçlıya göre **+109** token, tek araçlık tabana göre **+164** token ekliyor; betik bunun ortalamasını "araç başına yaklaşık 136 token" diye yazıyor. Ortalamaya değil iki farka bakın: gider aracın **açıklama ve şema uzunluğuyla** orantılı, araç sayısıyla değil. Uzun açıklamalı bir araç, kısa açıklamalı ikisinden pahalıdır.

Bu sayının iki tarafı da gördüğü bir karşılığı var: B/D turlarının birinci turun girdisi 345-346 token — yani taban (73) + iki araçlık katalog (273). Araç kataloğu, tek turda cevap üretmeden ödenen bedavadır.

:::caution[Bulut fiyatı ile yerel gider aynı şey değil]
OpenAI ve Anthropic bu gideri **para** olarak tarif ediyor ("billed as input tokens"). Yerel Ollama'da para yok; ödemenin karşılığı ön-yükleme süresi ve bağlam penceresidir. E denemesinin üç satırında ön-yükleme süreleri sırayla **0,82 / 4,88 / 4,55 sn**; bu üç sayıyı hız karşılaştırması olarak kullanmayın, çünkü önbellek isabetleri satırlar arasında farklıydı (48 / 48 / 171 token). Giderin sabit karşılığı token cinsindendir ve her turda ödenir. Asıl risk, katalog yüzünden dolan `num_ctx` penceresi: [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasındaki sessiz kırpma, on araçlık bir katalogda çok daha erken devreye girer.
:::

## tool_choice Dört Biçimde Denendi (F)

Alan Ollama'nın yerel `/api/chat` belgesinde yok; OpenAI ve Anthropic uyumluluk sayfaları "not supported" diyor. Sunucuya dört biçimde sorduk — tek araçlık katalog, araç çağırması beklenen bir soru:

| Gönderilen | Sunucu cevabı | Araç çağrıldı mı? |
| --- | --- | --- |
| alan yok | HTTP 200 | Evet (`content` boş) |
| `"auto"` | HTTP 200 | Evet (`content` boş) |
| `"required"` | HTTP 200 | Evet (`content` boş) |
| `"bulutmeydan"` (geçersiz değer) | HTTP 200 | Evet (`content` boş) |

**Ne kanıtlar:** Sunucu hiçbir biçimde hataya düşmüyor; geçersiz bir değeri de reddetmiyor. **Ne kanıtlamaz:** Dörtlünün aynı çıkması alanın yok sayıldığını kanıtlamaz, çünkü seçtiğimiz soru modelin zaten araç çağırdığı bir soruydu — yani test **ayırt edici değil**. Ayırt edici test, modelin araç çağırmadan cevaplayacağı bir soruya `tool_choice="required"` gönderip çağrıya zorlanıp zorlanmadığına bakmaktır; bu koşumda o deneme yapılmadı. Pratik sonuç değişmiyor: **zorlama alanına dayanan bir tasarım yapmayın**, davranışı belgelemeyen bir alanın üstüne kurmayın.

## format + tools: En Beklenmedik Bulgu (G)

`"format": "json"` ile `tools` aynı istekte gönderildi. Doküman bu ikilinin davranışını anlatmıyor. Bu makinede sunucu **HTTP 200 döndürdü** ve cevap şöyleydi:

```json title="Kayıttan, alan adları korunarak"
{ "role": "assistant", "content": "{\"name\": \"viki_ara\", \"arguments\": {\"soru\": \"Marmaray hangi yılında hizmete açıldı?\"}}" }
```

Yani: `message` içinde `tool_calls` **yok**. Model araç çağırmadı; araç çağrısının **JSON metnini düz içerik olarak** yazdı. Yapılandırılmış çıktı kipi, araç protokolünün yerine geçmiş görünüyor. Bunun pratik karşılığı, `format: "json"` kullanan bir hatta `tool_calls` beklerseniz döngünün hiç başlamamasıdır: çağrı bir metin yığını olarak kalır, uygulamanız onu ya hiç görmez ya da elle ayrıştırmak zorunda kalır. Elle ayrıştırmayı seçerseniz o artık araç çağırma değil, **modelin bir metin üretip sizin onu yorumladığınız** bir hatta dönüşür; tip, zorunlu alan ve isim denetimi size kalır.

:::note[Çözüm önerisi, ölçülmüş değil]
Bu davranışa karşı en sağduyulu yol, araç kullanan isteklerde `format` alanını boş bırakmak ve biçimi gerekiyorsa **araçtan sonra** ayrı bir geçişte yaptırmak. Bu tavsiye tek bir gözleme dayanıyor ve alternatifleri bu makinede koşmadık; kendi kataloğunuzda `G` denemesini tekrar edin.
:::

## Araç Mesajında tool_name Gerekli mi (H)

`tool_name` ile gönderilen B ve alanın çıkarıldığı H aynı soruda **birebir aynı girdi tokenını** (2.623) ve aynı iki turu üretti; H'nin çıktısı 253 token, B'ninki 336 token (B sınırda kestiği için uzun). İki araçlık katalogda, tek çağrılı turda `tool_name` alanının yokluğu döngüyü bozmadı. Keşif koşumunda üç biçim de (`tool_name`, yalın `content`, `tool_call_id`) aynı 240 tokenlık girdiyi üretmişti. Yine de aynı araç **iki kez** çağrıldığında sonucu doğru çağrıya eşlemenin garantisi `tool_call_id`dir; bu senaryo bu koşumda oluşmadığı için iddia değil savunma olarak yazıyoruz.

## Ölçümün Kendi Hatası: 3600 Metre Nereden Geldi?

C senaryosunda model `birim_donustur({"miktar": 1, "kaynak": "sa", "hedef": "m"})` çağırdı — uzunluk sorusuna süre birimiyle. Araç bunu reddetmeliydi; **etmedi**, `1 sa = 3600 m` döndürdü ve sonraki turda model "T1 hattının uzunluğu 3600 metredir" dedi. Sebep betiğin kendi satırında:

```python
if BİRİMLER[kaynak] * BİRİMLER[hedef] <= 0:   # boyut kontrolü değil, çarpım kontrolü
```

Faktörler pozitif olduğu için koşul hiçbir zaman çalışmıyor; süre ve uzunluk birimleri birbirine çevriliyor. Bu, ölçülen davranışın değil ölçüm aletinin kusuru — ve kaydın dürüst okunuşu şu: **ajanın uydurduğunu sandığımız sayının yarısı, bizim aracın kabul ettiği çöp argümandı.** Araçlarınız kötü argümanı reddetmezse, modeli suçlayacak bir deliliniz kalmaz. Betikteki bu satır [Örnek 7 sayfasında](/ornekler/ajan-dongusu/) düzeltme önerisiyle duruyor; sayfadaki sayılar reddetme öncesi koşumdan geldiği için değiştirilmedi.

## Pratik Sonuçlar

1. **Tur sayısı gecikmeyi doğru orantılı büyütmez, bağlam büyüklüğü büyütür.** Aynı iki turluk döngü 12,1 sn (C) ile 95,2 sn (B) arasında değişti; fark tur sayısı değil, ikinci turun okuduğu token.
2. **`done_reason` olmadan ajan logu eksiktir.** Yarım kalan cevap hata değildir, logda sessizdir.
3. **Araç sonuçlarını kısa tutun.** `viki_ara` 3.498-4.994 karakter döndürdü; bir sonraki turun ön-yüklemesini doğrudan o belirledi. Örnek 6'daki `k` değerini düşürmek, ajanda daha çok işe yarar.
4. **Kataloğu küçük tutun, açıklamayı tek cümleye indirin.** Gider araç başına sabit değil, uzunlukla ölçekli.
5. **Eşiği geçen araç sonucu modele metin olarak söyletilsin, sayı olarak değil.** D senaryosunda kullanıcıya "0,496" göründü.
6. **Ajanı cevap kalitesi iddiasıyla kurmayın.** Bu koşumda iki hat da aynı cevabı verdi; ajan iki tur ve kesik bir cümle karşılığında hiçbir şey kazanmadı.

## Burada Ölçülmeyenler

- **Kazanç.** Sabit hattın yanlış, ajanın doğru cevapladığı soru bu sette yok; sayılar yalnız maliyeti anlatıyor. Kalite için [RAG Değerlendirme](/rag/rag-degerlendirme/) sayfasındaki setle iki hattı karşılaştırmak gerekir.
- **Ayırt edici `tool_choice` testi** (araç gerektirmeyen soru + `required`) ve **üçüncü tur davranışı**: `MAKS_TUR` 5 ama hiçbir senaryo 3. tura gitmedi; sayaç sınırıyla kapanan bir döngü gözlenmedi.
- 3+ araçlık katalogda seçim doğruluğu; `stream: true` ile araç çağrısı; 4.000+ tokenlık katalogun `num_ctx` kırpmasına etkisi.
- Daha büyük/bulut modellerle tur sayısı: burada ölçülen davranış `qwen2.5:3b` kapasitesinin davranışıdır.
- MCP sunucusu üzerinden aynı iki aracın maliyeti: Ollama'nın MCP istemcisi olarak belgelenmiş bir yolu yok (bkz. [Mekanik](/ajan/arac-cagirma-ve-mcp/) sayfası).

## Bu Ölçümü Kendi Makinenizde Tekrar Edin

```bash
cd ornekler/ajan-dongusu
# Ollama açık olmalı; başka Ollama isteği göndermeyin
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u ajan.py > cikti/ajan-kaydi.txt 2>&1
```

Betik ilk koşumda korpusu Vikipedi'den indirir ve `cikti/korpus.json`a yazar (ikinci koşum okur); gömme vektörlerini `ornekler/viki-rag/cikti/vektor-indeks.json.gz` önbelleğinden alır, imza tutmazsa yeniden vektörleştirir. Yönlendirmeyi `| tee` ile değil `>` ile yapın ve `-u` kullanın — bu projede tampon yüzünden uzun bir koşum, `tee` yüzünden 20 dakikalık bir koşum kaybedildi: [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/).

## Kaynaklar ve ileri okuma

- [Örnek 7: Ajan Döngüsü](/ornekler/ajan-dongusu/) — betiğin kendisi, araç tanımları ve satır satır okuma.
- [Araç Çağırma Mekaniği ve MCP](/ajan/arac-cagirma-ve-mcp/) — istek/cevap biçimi, şablon şartı, MCP'nin kapsamı.
- [Ajan mı Sabit RAG Hattı mı?](/ajan/ajan-mi-sabit-hat-mi/) — bu sayıların hangi kararı haklı çıkardığı.
- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — önbellek, ön-yükleme bantları, soğuk başlangıç ve ölçümün tekrarı.
- [Örnek 6: Vikipedi'den Türkçe RAG](/ornekler/viki-rag/) — sabit hattın sıcak ölçülmüş gecikmesi.
- [Ollama Chat API](https://docs.ollama.com/api/chat.md) — `tools`, `tool_calls`, `format` ve kullanım alanlarının resmî belgelemesi.
