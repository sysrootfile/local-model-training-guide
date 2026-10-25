---
title: "RAG mi İnce Ayar mı? Doğru Yaklaşımı Seçmek"
description: "Modele yeni bilgi mi, yeni davranış mı öğretmek istiyorsunuz? RAG ile ince ayar arasındaki kararı maliyet, güncellik, gecikme, alıntı ve halüsinasyon eksenlerinde karşılaştırıyor; melez yolun haritasını çıkarıyoruz."
dogrulama: 2026-10-16
---

Model eğitimine yatırım yapmadan önce cevaplamanız gereken en önemli soru budur: problemi mi çözeceğiniz, yoksa problemi hiç var etmemeyi mi? Çoğu "modeli eğitmeliyim" sanılan durumun asıl ilacı eğitim değildir; açık kitap gibi çalışan **RAG** (getirimle desteklenen üretim), bilgiye dayalı problemleri GPU süresi harcamadan çözer. Bu sayfa, kararın haritasını çıkarır: hangi araç hangi işi çözer, hangisi ne kadar tutar ve çoğu projenin gerçek cevabı olan melez yol nasıl kurulur.

**Tek cümlelik cevap:** Modele **bilgi** öğretecekseniz RAG, **davranış** öğretecekseniz ince ayar; gerçek projelerin çoğu ikisini birlikte kullanır.

## Karar Merdiveni: En Ucuz Araçtan Başlayın

Kararı "RAG mi ince ayar mı?" olarak çerçevelemek, aslında merdivenin iki basamağını atlamak demektir. Her zaman en alt basamaktan başlayın ve yukarı çıkmak için somut bir sebep gerekçelendirin:

```text title="Karar merdiveni — yukarı çıkarken maliyet ve emek büyür"
4. Melez yol        → RAG (bilgi) + ince ayar (davranış) birlikte
3. İnce ayar        → modelin davranışı, üslubu veya formatı yanlış
2. RAG              → modelin bilgisi eksik, eski veya özel (kendi belgeleriniz)
1. Prompt mühendisliği → iyi bir talimat + birkaç örnek sorunu çözer mi?
```

:::tip[1. basamağı ciddiye alın]
Talimatı netleştirip cevaba dair 2-3 örnek (few-shot) vermek, birçok format ve tutarlılık problemini sıfır maliyetle çözer. İnce ayar, prompt ile ulaşılamayan **kalıcı** davranış değişimi için ayrılmalıdır: [SFT](/llm/sft/).
:::

## Ana Ayrım: Bilgi mi, Davranış mı?

Kararı tek bir soruya indirgeyebilirsiniz: **model yanlış mı konuşuyor, yoksa yanlış şekilde mi konuşuyor?**

- **Yanlış konuşuyor** (bilgi sorunu): Şirket iç politikanızı bilmiyor, ürün kataloğunuzdan haberi yok, dünkü veriyle konuşuyor, alan terimlerini yanlış bağlamda kullanıyor. Bilgi, modelin ağırlıklarında **yoktur**. Çözüm: bilgiyi sorgu anında dışarıdan getirin — RAG.
- **Yanlış şekilde konuşuyor** (davranış sorunu): Bilgiye sahip ama üç cümlede bitirmesi gereken cevabı üç sayfada veriyor, resmî üslup yerine sohbet üslubu kullanıyor, JSON istediğinizde düz metin döküyor, müşteri temsilcisi gibi konuşması gerekirken asistan gibi konuşuyor. Bilgi vardır, **biçim yanlıştır**. Çözüm: davranışı örneklerle öğretin — ince ayar ([SFT](/llm/sft/), tercihler için [DPO ve RLHF](/llm/dpo-rlhf/)).

**Analoji:** Yeni işe alınan bir uzmana şirket içi doküman havuzuna erişim vermek (RAG) başka şeydir; onu şirketin yazışma üslubuyla yazması için eğitmek (ince ayar) başka şey. Birine dokümanları verdiğinizde yazı stili değişmez; stili değiştirmek için gerçekten alıştırma (örneklerle çalışma) gerekir.

## İki Yaklaşım Yan Yana

| Eksen | RAG | İnce ayar |
| --- | --- | --- |
| Neyi değiştirir | Modelin **eriştiği bilgiyi** | Modelin **kendini** (davranış, üslup, format) |
| Güncellik | Belge güncellenince bilgi güncellenir; yeniden eğitim yok | Güncelleme = yeniden eğitim |
| Alıntı (kaynak gösterme) | Doğal: hangi belgeden geldiği izlenebilir | Yok: cevabın kaynağı gösterilemez |
| Halüsinasyon riski | Düşürür: cevap sağlanan belgelere yaslanır | Bilgi için kullanılırsa artar (aşağıda) |
| Gecikme | Sorgu başına arama adımı ekler | Ek arama yok; tek geçiş |
| Veri ihtiyacı | Ham belgeler yeterli (etiket gerekmez) | Binlerce tutarlı örnek gerekir: [Kendi verini oluştur](/veri/kendi-verini-olustur/) |
| Eğitim donanımı | Gerekmez | GPU veya kiralık kart: [Bulut Seçenekleri](/donanim/bulut-secenekleri/) |
| Bakım yükü | Vektör veritabanı + arama kalitesi | Veri hattı + eğitim + değerlendirme döngüsü |

İkisinin kesişmediği tek satır yok gibidir; ama en sık atlanan satır **alıntıdır**. Cevabın hangi belgeden geldiğini göstermek zorunda olduğunuz her senaryo (hukuk, tıp, iç politikalar, müşteri desteği) fiilen RAG'ı zorunlu kılar — ince ayar bu işi yapamaz.

## Bilgi Öğretmek İçin Neden İnce Ayar Kötü Bir Fikir?

Sezgi "modele bilgiyi de ezberletirim" der ama pratik üç sebeple ters yönde işler:

1. **Ezber genellemez.** Bir gerçeği tek örnekle ezberletirseniz model onu yalnızca o örnek formülasyonunda hatırlar; soru biraz değişince yanıt kaybolur veya uydurulur. Microsoft Research ekibinden Ovadia ve arkadaşlarının 2023 karşılaştırması (Fine-Tuning or Retrieval?), hiç görülmemiş bilgiyi modele kazandırma işinde **RAG'ın ince ayarı belirgin biçimde geride bıraktığını** gösterdi.
2. **Az veri, büyük hasar.** Dar bir bilgi yığınıyla yapılan ince ayar, modelin var olan yeteneklerinde bozulmaya (unutma) yol açabilir; binlerce dengeli örnekle çalışmak gerekir: [Veri Temizleme](/veri/veri-temizleme/).
3. **Güncelleme maliyeti süreklidir.** Envanter, fiyat listesi veya politika değiştiğinde yeniden eğitim gerekir; RAG'da belgeyi değiştirmek yeterlidir.

:::note[LIMA'nın gösterdiğinin tersi değil]
LIMA çalışması "yalnızca 1.000 örnekle ince ayar yeterli olabilir" der — ama o örnekler **davranış ve format** öğretir; bilgi çoğunlukla ön eğitimde zaten vardır: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/). Bu sayfanın ayrımıyla çelişmez, tam olarak onu doğrular: ince ayarın işi davranıştır, bilgiyi o taşımaz.
:::

Bir istisna var: modelde **hiç olmayan bir dil veya çok dar bir alan dili** (tıbbi jargonun yoğun kullanımı gibi) devam ön eğitimi (DAPT) gerektirebilir — bu da ince ayar değil, ölçekli bir eğitim işidir: [Ön Eğitim](/llm/pretraining/).

## Davranış Öğretmek İçin Neden RAG Yetersiz?

RAG, modelin bağlamına **içerik** ekler; modelin **üretme biçimini** değiştiremez. Açık kitap sınavına giren öğrenci, kitabı okumakla cevap yazma stilini değiştirmez. Şu istekler RAG ile karşılanamaz:

- "Her cevabı üç madde ve resmî dilde ver." (format)
- "Müşteriye asla 'bilmiyorum' demeden çözüm öner." (politika davranışı)
- "Şirketin ses tonuyla konuş." (üslup)
- "Soruyu JSON şemasında yanıtla." (yapı)

Bunların hepsi örneklerle öğretilen kalıcı davranışlardır; doğru araç SFT'dir ve bu yüzden çoğu ürün senaryosunda sıralama şöyledir: RAG sorunu çözerse eğitmeyin; çözmüyorsa, artık RAG'lı örneklerle beslenen modele davranışı öğretin (aşağıdaki melez yol).

## Melez Yol: Çoğu Projenin Gerçek Cevabı

Üretimdeki tipik kurulum iki katmanlıdır:

1. **RAG katmanı** doğru bilgiyi sağlar: belgeler vektör veritabanında, sorguyla en ilgili parçalar bağlama eklenir, cevap belgeye dayanır ve kaynak gösterebilir.
2. **İnce ayar katmanı** cevabın biçimini sabitler: modele "getirilen bağlamla, şu üslupta, şu formatta cevap ver" davranışı öğretilir.

Pratik sıralama: önce RAG boru hattını çalıştırın; sonra sistemin verdiği **iyi cevapları toplayıp** ince ayar verinize çevirin. Böylece eğitim veriniz gerçek dağılımı yansıtır ve iki katman birbirini destekler. RAG mimarilerinin naive → advanced → modular evrimini inceleyen kapsamlı kaynak için aşağıdaki Gao anketine bakın.

:::caution[Sıralamayı tersine çevirmeyin]
Önce ince ayar yapıp sonra RAG eklemek, en sık görülen yanlış kuruldur: ince ayar, RAG'sız sorulara verilen cevaplarla eğitildiyse, RAG'lı gerçek kullanımda gördüğü bağlam formatına alışkın değildir ve kazandığı davranış kaybolur. Eğitim verinizi, üretimdeki bağlam formatıyla (belge parçaları + soru) aynı şablonda hazırlayın: [Veri Formatları](/veri/veri-formatlari/).
:::

## Uzun Bağlam RAG'i Öldürdü mü?

2016'lı yılların küçük bağlam pencerelerinde RAG bir zorunluluktu; bugün 128K token pencereler "tüm belgeleri bağlama at, arama altyapısı kurma" seçeneğini doğurdu. Bu seçenek üç durumda çalışır:

- Korpus küçükse (birkaç düzine belge, toplamda pencerenin altında),
- Sorgu sayısı düşükse ve maliyet/gecikme önemsizse,
- Kalite kaybını kabul edebiliyorsanız.

Üç ciddi bedeli vardır:

1. **Maliyet sorgu başına ödenir.** Bağlama atılan her token her istekte faturalanır — ve Türkçe bu hesabı 1,5-2,5 kat şişirir: [Tokenizasyon](/temeller/tokenizasyon/). RAG'da ise yalnızca ilgili parçalar ödenir.
2. **Bellek ve hız.** Uzun bağlam, çıkarımda KV cache belleğini lineer büyütür: [Transformer Mimarisi](/temeller/transformer/). Yerel kartta 128K bağlam çoğu zaman hayaldir.
3. **Kalite ortada düşer.** Liu ve arkadaşlarının "Lost in the Middle" çalışması, uzun bağlamlarda modelin baştaki ve sondaki bilgiye ortadakilerden daha çok güvendiğini gösterdi. Arama ile seçilmiş, kısa ve ilgili bağlam bu riski tabii olarak azaltır.

Sonuç: uzun bağlam RAG'in yerine geçmez; **küçük korpus + düşük trafik** kombinasyonunda RAG'i yerine koyar.

## Maliyet ve Emek Karşılaştırması

**RAG tarafı:** Ana maliyet tek seferlik indekslemedir ve şaşırtıcı kadar ucuzdur. Yerel embedding modelleri (aşağıda) ücretsizdir; API kullanırsanız 2026 itibarıyla OpenAI text-embedding-3-small **$0,02**, text-embedding-3-large **$0,13** per 1M token'dır — yani yarım milyon tokenlık bir belge havuzunu küçük modelle indekslemek yaklaşık **$0,01** eder. Sürekli maliyet, sorgu başına eklenen bağlam token'ları ve vektör veritabanının işletilmesidir.

**İnce ayar tarafı:** İki gider kalemi vardır: veri emeği (tutarlı örnek hazırlamak çoğu projenin en uzun adımıdır: [Veri](/veri/kendi-verini-olustur/)) ve eğitim süresi (tipik bir QLoRA eğitimi, donanıma göre 30 dakika ile 6 saat arası sürer: [Eğitim Nasıl Çalışır?](/temeller/egitim-nasil-calisir/)). Eğitilen modeli sunmak, [birleştirme](/kullanim/lora-birlestirme/) ve [nicemleme](/kullanim/quantization/) adımlarını da zincire ekler.

Kural: bilgi sorununuz için RAG neredeyse her zaman daha ucuz **ve** daha doğrudur; ince ayar bütçesini davranışa ayırın.

## Yerel RAG Yığını (2026 itibarıyla)

Tüm bileşenleri yerelde çalıştırmak mümkündür; akış dört parçadır:

```text title="Yerel RAG boru hattı"
1. Belgeleri parçala        → 256-1024 tokenlık parçalar (uçlarda %10-20 örtüşme)
2. Parçaları vektörleştir   → embedding modeli (yerel, ücretsiz)
3. Vektör veritabanına yaz  → benzerlik araması için indeks
4. Sorgu akışı              → soruyu vektörleştir → en yakın k parçayı getir → bağlama ekle → üret
```

- **Embedding modeli:** Ollama, gömme modellerini doğrudan çalıştırır (`/api/embeddings` ucu): yaygın seçenekler `nomic-embed-text` ve BAAI'in çok dilli `bge-m3`'ü. Kurulum ve örnek akış: [Ollama](/kullanim/ollama/).
- **Vektör veritabanı:** Basit projeler için [Chroma](https://docs.trychroma.com/) (pip ile kurulur, gömülü çalışır); daha büyük ölçek ve filtreleme için [Qdrant](https://qdrant.tech/documentation/); tek dosyalık hafif çözüm için `sqlite-vec`.
- **Orkestrasyon:** Belge yükleme → parçalama → indeksleme → sorgu zincirini elle yazmak istemiyorsanız [LlamaIndex](https://docs.llamaindex.ai/) veya LangChain hazır sunar.
- **Sıfır kod çözüm:** [Open WebUI](/kullanim/ollama/) belge yükleyip üzerinde soru sormayı arayüzden yapar; karar aşamasında kavramları hissetmek için en hızlı yoldur.

:::tip[Önce uçtan uca çalıştırın, sonra iyileştirin]
İlk gecede "harika cevap" değil "çalışan cevap" hedefleyin. Arama kalitesi probleminizse (doğru belge bulunamıyor) ince ayar değil, parçalama boyutu, embedding modeli veya [hibrit arama](/rag/parcalama-ve-hibrit-arama/) (anahtar kelime + vektör) seçimini değiştirin — hangisini değiştireceğinize ölçüm karar verir: [RAG Değerlendirmesi](/rag/rag-degerlendirme/). Bu boru hattının **bu makinede gerçekten çalıştırılmış iki hâli** var: [Yerel RAG Asistanı örneği](/ornekler/yerel-rag/) (donanmış belgelerle) ve [Vikipedi'den Türkçe RAG örneği](/ornekler/viki-rag/) (canlı veri + parçalama).
:::

## Türkçe İçin Pratik Notlar

- **Embedding seçimini kendi verinizle ölçün.** Çok dilli modeller (bge-m3, multilingual-e5) Türkçe'de genelde iyi çalışır ama bu genel bir gözlemdir; kendi belgelerinizden 20-30 soru-cevap çifti hazırlayıp "doğru parça ilk k'ta geliyor mu?" ölçümü yapın — yarım günlük iş, tüm sistemin kalitesini belirler. Rakamları kendi ölçümünüzle doldurun; başkasının tablosu sizin korpusunuzu temsil etmez.
- **Token çarpanı bütçeyi belirler.** Türkçe'nin 1,5-2,5 kat token tüketimi, aynı pencereye daha az parça sığdırır; bağlam bütçesini İngilizce varsayımıyla planlamayın: [Tokenizasyon](/temeller/tokenizasyon/).
- **Parça sınırları ek bölmesin.** Eklemeli dilde kelime içi bölünme, embedding kalitesini İngilizce'ye kıyasla daha çok düşürür; parçalayıcıyı cümle sınırında kesmeye zorlamak genellikle doğru tercihtir.

## Mini Karar Tablosu

| Senaryo | Öneri |
| --- | --- |
| Şirket iç belgelerine dayalı soru-cevap, kaynak gösterilecek | RAG |
| Cevap üslubu/formatı tutarsız, bilgi doğru | İnce ayar (SFT) |
| Model her iki sorunda da: bilgisi eksik, formatı bozuk | Melez yol (RAG + SFT) |
| Ürün kataloğu / fiyat / politika sık güncelleniyor | RAG (yeniden eğitim yok) |
| Türkçe cevap vermiyor veya bozuk Türkçe konuşuyor | İnce ayar — Türkçe davranış verisiyle: [türkce-asistan örneği](/ornekler/turkce-asistan/) |
| Küçük korpus, düşük trafik, hızlı prototip | Bağlama direkt ekleme (RAG'sız) |
| Yeni bir dil veya çok dar alan dili gerekiyor | Devam ön eğitimi (DAPT): [Ön Eğitim](/llm/pretraining/) |
| Yanlış cevapların hangi kaynaklardan geldiği denetlenecek | RAG (alıntı izlenebilirliği) |

## Sonraki adımlar

- Karar ince ayardan yana çıktıysa: [SFT](/llm/sft/) ve [LoRA ve QLoRA](/llm/lora-qlora/)
- RAG'dan yana çıktıysa: [Yerel RAG Asistanı örneği](/ornekler/yerel-rag/) (çalışan betik), [Vikipedi'den Türkçe RAG](/ornekler/viki-rag/) (canlı veri + parçalama) ve [Ollama](/kullanim/ollama/) ile yerel embedding kurulumu
- İki yolun da ön koşulu olan altyapı: [VRAM Hesabı](/donanim/vram-hesabi/), [Yol Haritası](/baslangic/yol-haritasi/)
- Kavramlara hızlı bakış: [Kavramlar](/baslangic/kavramlar/), [Sıkça Sorulan Sorular](/kaynaklar/sss/)

## Kaynaklar ve İleri Okuma

- [Ajan mı Sabit RAG Hattı mı?](/ajan/ajan-mi-sabit-hat-mi/) — RAG hattınızı kurduktan sonraki basamak: araç dizisine siz mi karar verin, model mi? Maliyeti ölçüldü.
- [Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs (Ovadia vd. 2023, arXiv:2312.05934)](https://arxiv.org/abs/2312.05934) — bilgi enjeksiyonunda RAG ile ince ayarı doğrudan karşılaştıran çalışma; RAG'ın belirgin üstünlüğünü gösterir.
- [Retrieval-Augmented Generation for LLMs: A Survey (Gao vd. 2023, arXiv:2312.10997)](https://arxiv.org/abs/2312.10997) — naive/advanced/modular RAG evrimini haritalayan kapsamlı anket.
- [Lost in the Middle (Liu vd. 2023, arXiv:2307.03172)](https://arxiv.org/abs/2307.03172) — uzun bağlamlarda bilginin ortada kalmasının performansı düşürdüğünü gösteren çalışma.
- [OpenAI — API fiyatlandırması](https://developers.openai.com/api/docs/pricing) — text-embedding-3-small/large fiyatlarının resmî sayfası (2026 itibarıyla doğrulandı; güncel değeri kontrol edin).
- [Ollama — API dokümanı](https://docs.ollama.com/api) — `/api/embeddings` ucunun resmî belgesi.
- [BAAI/bge-m3 model kartı](https://huggingface.co/BAAI/bge-m3) — çok dilli, yoğun+seyrek aramayı destekleyen embedding modeli.
- [nomic-embed-text (Ollama kütüphanesi)](https://ollama.com/library/nomic-embed-text) — yerel RAG için yaygın embedding modeli.
- [Chroma dokümanları](https://docs.trychroma.com/) — pip ile kurulabilen gömülü vektör veritabanı.
- [Qdrant dokümanları](https://qdrant.tech/documentation/) — filtreleme ve ölçek odaklı vektör arama motoru.
- [LlamaIndex dokümanları](https://docs.llamaindex.ai/) — belge yüklemeden sorguya RAG zincirini kuran orkestrasyon çerçevesi.
