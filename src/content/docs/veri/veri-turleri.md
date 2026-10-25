---
title: "Veri Türleri: Hangi Eğitim Hangi Veriyi İster?"
description: Ön eğitimden talimat ayarına, DPO'dan görsel model eğitimine; her yöntemin hangi veri türünü, hangi formatta ve ne kadar istediğini örneklerle öğrenin.
dogrulama: 2026-10-15
---

> **"Model, verisinin aynasıdır."**

Bir modele ne verirseniz onu öğrenir: kaba veri verirseniz kaba, özenli verirseniz özenli sonuç alırsınız. Ama "veri" tek bir şey değildir; ham metin, soru-cevap çifti, "iyi/kötü cevap" karşılaştırması, tablo satırı ve fotoğraf aynı sepete girmez. **Hangi eğitimi yapmak istediğiniz, hangi veriyi toplayacağınızı belirler.** Bu sayfa, o eşleşmeyi kurmanız için bir haritadır.

## Hangi Eğitim, Hangi Veri?

| Eğitim türü | İstediği veri | Tipik format | Tipik miktar |
| --- | --- | --- | --- |
| Ön eğitim (pretraining) | Ham metin: kitap, web, kod | Düz metin / parquet | Milyarlarca token |
| Devam ön eğitimi (continued pretraining) | Alan metni: hukuk, tıp, şirket dokümanları | Düz metin | 1-100 milyon token |
| Talimat ayarı (SFT) | Soru-cevap / görev-çözüm çiftleri | JSONL (Alpaca vb.) | 1K-100K örnek |
| Tercih optimizasyonu (DPO/RLHF) | Tercih çiftleri: aynı soruya iyi + kötü cevap | JSONL | 1K-50K örnek |
| Görsel model eğitimi | Görsel + açıklama(lar) | Klasör + eşleme dosyası (json/csv) | 10-10.000 görsel |
| Klasik makine öğrenmesi | Satır = örnek, sütun = özellik tablosu | CSV / parquet | Yüzlerce - milyon satır |
| Değerlendirme (eval) | Held-out soru seti: kendi yazdığınız sınav soruları | JSONL / liste | 20-200+ soru; eğitime asla karıştırılmaz |

### Ön Eğitim (Pretraining)

Modelin dilin kendisini öğrendiği aşama; en ham ve en büyük veri. Kendi projenizde sıfırdan ön eğitim nadiren mantıklıdır — mevcut bir modeli 1-100 milyon token'lık alan verisiyle "devam ettirmek" neredeyse her zaman daha akıllıdır. Ayrıntı: [Ön Eğitim](/llm/pretraining/).

### Talimat Ayarı (SFT)

Modele "sorulana cevap verme" davranışını kazandırır; bu sitede en çok kullanacağınız tür. Veri, gerçek kullanım senaryolarınızı yansıtan soru-cevap çiftleridir. Eğitim: [SFT Rehberi](/llm/sft/). Format örnekleri: [Veri Formatları](/veri/veri-formatlari/).

### Tercih Optimizasyonu (DPO/RLHF)

Aynı soruya "iyi cevap / kötü cevap" çiftleri verip modelin tercih "zevkini" eğitirsiniz. Örnek:

```json title="tercih_ornek.jsonl"
{
  "prompt": "Müşteri iade talebini nasıl karşılamalıyım?",
  "chosen": "İade talebinizi aldım; sipariş numaranızı paylaşırsanız süreci hemen başlatabilirim.",
  "rejected": "İade koşullarımızı web sitemizden inceleyebilirsiniz."
}
```

Ayrıntı: [DPO ve RLHF](/llm/dpo-rlhf/).

### Görsel Model Eğitimi

Difüzyon modelleri ve görsel dil modelleri için görsel-açıklama eşlemesi gerekir; genelde bir klasör dolusu görsel ve yanında bir eşleme dosyası:

```csv title="gorsel_esleme.csv"
dosya, aciklama
urun_001.jpg, "kırmızı deri kadın çantası, önden görünüm, beyaz zemin"
urun_002.jpg, "lacivert erkek gömleği, düz kesim, mankende"
```

Hedef sayfalar: [Diffusion Temelleri](/gorsel/diffusion-temelleri/), [Görsel LoRA Eğitimi](/gorsel/lora-egitimi/).

### Klasik Makine Öğrenmesi

Burada veri, satır başına bir örnek ve sütun başına bir özellikten oluşan tablodur: gayrimenkul fiyatı tahmini için "metrekare, oda sayısı, konum, fiyat" gibi. Metin/görsel işleme yok; eksik değer doldurma ve ölçekleme gibi işler burada başlar: [Klasik ML Temelleri](/klasik-ml/temeller/), [İlk Model](/klasik-ml/ilk-model/).

:::note
Tablodaki "tipik miktar" değerleri gerçekçi bir **başlangıç aralığıdır**, eşik değil. Miktarların birimi "token" veya "örnek"tir; token'a tazeleme: [Tokenizasyon](/temeller/tokenizasyon/). Türkçe metin, aynı içerik için İngilizce'ye göre genellikle **daha fazla token** harcar; "1 GB metin şu kadar token eder" tahminlerini kendi tokenizer'ınızla ölçün.
:::

### Veri Miktarını Kabaca Hesaplamak

Bir "epoch", tüm örneklerin bir kez görülmesidir. Toplam iş yükü şu basit formülden çıkar:

```text
toplam token ≈ örnek sayısı × örnek başına ortalama token × epoch sayısı
```

Örnek: 2.000 soru-cevap örneğiniz var ve örnek ortalaması ~500 token → 1 epoch ≈ 1 milyon token; 3 epoch ≈ 3 milyon token. Bu sayı yakıt göstergenizdir: eğitim süresi, bulut maliyeti ve "bu veri yeterli mi?" kararı hep buradan çıkar.

## Ne Kadar Tekrar Kabul Edilebilir?

Veri azsa ilk akla gelen çözüm, aynı veriyi daha çok epoch boyunca göstermektir. Tekrarın işe yaradığı bir bölge vardır; ama sınırsız değildir.

:::note
**Araştırma bulgusu:** "Scaling Data-Constrained Language Models" (Muennighoff ve ark., 2023), ön eğitim deneylerinde **~4 epoch'a kadar tekrarın** taze veriyle neredeyse aynı kaybı (loss) verdiğini gösterdi; bu noktadan sonra tekrarlanan token'ın değeri her turda biraz daha azalır, yani azalan verim (diminishing returns) devreye girer. Kaynak: [arXiv:2305.16264](https://arxiv.org/abs/2305.16264).
:::

- **Ön eğitim ve devam ön eğitimi için:** Elinizdeki korpusu birkaç epoch tekrar etmek olağandır; pratikte "kabul edilebilir" bölge ~4 epoch'a kadardır. Ötesi yasak değildir ama her ek turun katkısı küçülür; "daha çok tekrar = daha çok bilgi" varsayımı geçersiz kalır.
- **SFT'de eşik belirgin biçimde düşer:** Talimat verisi küçük ve örnekler birbirine benzediği için tekrar hızla ezbere dönüşür; tipik güvenli aralık **1-3 epoch**, 5+ epoch ise ezber riski taşır (ayrıntı: [SFT Rehberi](/llm/sft/), [Hiperparametreler](/llm/hiperparametreler/)). SFT'de kaliteyi artırmanın yolu epoch yükseltmek değil, örnek kalitesini ve çeşitliliğini artırmaktır.
- **Görünmez tekrar:** Birebir kopyaların yanında "neredeyse aynı" örnekler de etkin tekrara girer; 1 epoch yaparken bile setin içinde eş örnekler varsa model bazı içeriği birkaç kez görür. Eğitimden önce yakın kopyaları ayıklayın: [Veri Temizleme](/veri/veri-temizleme/).
- **Yukarıdaki tablodaki "tipik miktar" aralıklarıyla ilişkisi:** Miktarınız tablodaki aralığın içindeyse veriyi tekrar tekrar okutmanıza genelde gerek yoktur; aralığın altındaysanız tekrarla bir miktar telafi edilebilir. Ama tekrar, taze verinin yerini tamamen tutmaz: az sayıda örneği onlarca kez göstermek öğretmez, ezberletir.

## Karışım (Mixture): Birden Çok Veri Türünü Birleştirmek

Gerçek projelerde tek veri türü nadiren yeter; modelin aynı anda öğrenmesi gerekenler çeşitlidir: soru-cevap davranışı, alan bilgisi, istenen biçim, üslup. Bu yüzden eğitim seti genellikle bir **karışım (mixture)** olarak kurulur ve iki şey birer hiperparametreye dönüşür:

1. **Görev çeşitliliği:** Hangi görev türleri sette temsil edilecek?
2. **Oranlar:** Her görev türünden kaç örnek girecek?

Açık bir tarif örneği: **TÜLU 3** post-training tarifi, küratörlü (özenle seçilmiş) veriyi, sentetik veriyi, tercih (DPO) verisini ve doğrulanabilir ödüllü pekiştirmeli öğrenme (RLVR) verisini tek bir karışımda birleştirir; karışımın nasıl kurulduğunu ve rafine edildiğini ayrıntılı biçimde açıklar ([arXiv:2411.15124](https://arxiv.org/abs/2411.15124)). Yani "hangi görevden ne kadar?" sorusu sezgisel bir liste değil, deneyle ölçülen bir tasarım kararıdır.

Pratik başlangıç rehberi (evrensel bir oran yoktur; oran seçimi kendi verinizde deneyle doğrulanır):

- **Gerçek kullanım dağılımına benzetin:** Model, dağıtımda hangi görevlerle ne sıklıkta karşılaşacaksa karışım ağırlıkları o sıklığa benzemelidir; en sık kullanılacak görev en çok örneği alır.
- **Az temsil edilen göreve bilinçli ağırlık verin:** Nadir ama önemli bir görev, doğal sıklığına bırakılırsa baskın görevlerin gölgesinde kalır ve davranışı öğrenilmez.
- **Oranları ölçerek seçin:** "Doğru karışım" önceden bilinemez; farklı oranlanmış küçük sürümlerle karşılaştırma koşuları yapıp held-out sette ölçmeden karar vermeyin. Ölçüm tarafı: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/), [Benchmarklar](/degerlendirme/benchmarklar/).

Bileşenleri nereden bulacağınız: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/). Karışımdaki boşluğu sentetik üretimle doldurmak isterseniz yukarıdaki "Sentetik Veri" bölümüne ve [Kendi Verini Oluştur](/veri/kendi-verini-olustur/) sayfasına bakın.

## Kalite mi, Miktar mı? (Kısa cevap: Kalite)

- **LIMA bulgusu:** Meta'nın [LIMA çalışması](https://arxiv.org/abs/2305.11206), yalnızca ~1.000 özenle seçilmiş örnekle yapılan talimat ayarının, gelişigüzel toplanmış on binlerce örnekle yarışabildiğini gösterdi. Az ama öz, çoğu zaman çok ama özensizden iyidir.
- **Garbage in, garbage out:** Model, verinin ortalamasını ve hatalarını öğrenir. Veri setinizde yanlış bilgi varsa model onu özgüvenle tekrarlar.
- **Tekrar, ezberi öğretir:** Aynı örneği 100 kez tekrarlarsanız model genellemek yerine onu ezberler; benzer ama farklı bir soruda performans düşer. Aşırı tekrar, diğer örneklerin etkisini de gölgeler.
- **Çeşitlilik:** Hepsi tek bir kaynaktan geliyorsa modelin bakışı da tek olur; farklı kaynak ve üslup karışımı genellemeyi artırır.

:::tip
Kaba sezgiler (kaliteli ve tutarlı veri varsayımıyla): bir **format/davranışı** öğretmek için yüzlerce örnek yeterli olabilir; bir **üslubu** kopyalamak için 500-2.000; dar bir **bilgi alanını** işlemek için 2.000-10.000. Bunlar kesin eşik değildir; gözlem ve değerlendirme her zaman öndedir.
:::

## Alan Verisi Nasıl Görünür? Üç Mini Örnek

**1) Müşteri destek SSS'leri → SFT.** Elinizde 3 yıllık destek yazışması var. Bunlardan 300-2.000 gerçek soru-cevap çıkarırsınız; her biri `{"instruction": "...", "output": "..."}` biçiminde JSONL'e yazılır. Temizlikte kopyala-yapıştır şablon cevaplar ve "merhaba/teşekkürler" dolguları ayıklanır. Sonuç: şirketinizin üslubuyla ve doğru bilgiyle cevap veren küçük bir model.

**2) Hukuk metinleri → devam ön eğitimi.** Mevzuat, içtihat ve kurum içi dokümanlardan 5-50 milyon token düz metin (.txt). İki zorunluluk var: telif/lisans kontrolü ve kişisel veri ayıklama. Model bu aşamada alanın dilini ve üslubunu öğrenir; hukuki doğruluk ayrıca dikkatli değerlendirme gerektirir.

**3) Ürün fotoğrafları → görsel model.** 100-1.000 ürün fotoğrafı ve her biri için tutarlı açıklamalar ("kırmızı deri kadın çantası, önden görünüm, beyaz zemin"). Açıklamalar aynı dilde ve benzer şablonla yazılmalı; az fotoğrafla başlayıp sonucu gözlemleyerek büyütmek en sağlıklısıdır.

## Veriyi Tanımak: Eğitimden Önce 30 Dakika

Veri setini eğitime vermeden önce mutlaka "elinizle" gezin. İstatistik sizi yanıltabilir, gözünüz yanıltmaz:

1. **Rastgele 20-30 örnek okuyun.** Cevaplar kırpılmış mı, kod veya şablon artığı karışmış mı, ton tutarlı mı?
2. **Uzunluk dağılımına bakın.** Tek bir dev örnek, ortalamayı yüksek gösterip aktivasyon bütçenizi yanlış planlatır.
3. **Kodlama kontrolü:** Türkçe karakterler (ş, ğ, ı) doğru mu? "Ã¼nlÃ¼" gibi bozulmalar (mojibake) gördüğünüz seti düzeltmeden kullanmayın.
4. **Tekrar oranı:** Aynı örnek kaç kez geçiyor? Yüzde birkaç normaldir; yüzdeler mertebesindeyse kesinlikle ayıklayın.
5. **Denge:** Sınıflandırmada her sınıftan kaç örnek var; SFT'de hangi görev türleri baskın?
6. **Kaynak ve lisans izi:** Her örneğin hangi kaynaktan geldiğini bir alanda tutun; yayın/gösterim sırasında bu kayıt paha biçilmez olur.

Araçlar ve pratik yöntemler: [Veri Temizleme](/veri/veri-temizleme/).

## Sentetik Veri: Ne Zaman Kullanılır?

Sentetik veri, güçlü bir modelden üretilen eğitim örnekleridir; küçük model büyük modeli taklit edecek şekilde eğitiliyorsa buna **damıtma (distillation)** denir.

**Ne zaman mantıklı:**

- Gerçek veri az ama temsil edici olduğunda onu çoğaltmak için.
- Veriyi başka bir formata/göreve dönüştürürken (ör. SSS'leri tercih çiftlerine çevirmek).
- Zor ve negatif örnekler (modelin tipik yanlış cevapları) üretmek için.

**Riskler:**

- Öğretmen modelin hataları öğrenciye miras kalır.
- Tek tip istemle üretilen veri çeşitliliği daraltır; model gerçek dünyayı değil, üretim şablonunu öğrenir.
- Kötü filtreleme, gerçek veriden öğrenilenin üzerine gürültü bindirir.

Altın kural: üretilen veriyi örnekleyip elle doğrulamadan eğitime katmayın. Ayrıntılı rehber: [Kendi Verini Oluştur](/veri/kendi-verini-olustur/).

:::note
**Türkçe veri manzarası:** Açık Türkçe veri, İngilizce'ye kıyasla belirgin biçimde azdır. Bu yüzden Türkçe bir model için genelde üç yol birlikte kullanılır: (1) mevcut açık setler, (2) İngilizce veriyi çevirme, (3) kendi verinizi üretme. Başlangıç noktaları: Hugging Face'teki `atasoglu/turkish-instruction-datasets` koleksiyonu, `ogulcanaydogan/Turkish-LLM` (Qwen2.5 üzerine QLoRA ile eğitilmiş Türkçe model ve verisi), FineWeb-2'nin Türkçe alt kümesi, Turkish Data Depository (OSCAR + mC4 tabanlı büyük korpus) ve `hasankursun/turkish-corpus-100b`. Değerlendirme tarafında Holmeister Türkçe değerlendirme setleri (11 görev için 17 set) işinizi görür. Derli toplu liste: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/).
:::

:::danger
**Aynı veriyi hem eğitim hem test için kullanmayın!** Modelin gördüğü örneklerde yüksek skor alması beklenen bir şeydir — bu başarı değil, ezberdir. Veri sızıntısı (data leakage) değerlendirmenizi anlamsız kılar: modele "sınavda da aynı soruları" sormuş olursunuz. Test setini en baştan ayırın ve hiçbir eğitim aşamasında (SFT, DPO...) kullanmayın. Ölçüm tarafı: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/), [Benchmarklar](/degerlendirme/benchmarklar/).
:::

## Yaygın Kaynaklar Hangi Veri Türüne Denk Gelir?

- **Hugging Face Datasets:** Bu sayfadaki tüm türler için birinci adres; SFT setlerinden görsel veriye kadar binlerce seçenek.
- **Kaggle:** Tablo verisi (klasik ML) ve hazır yarışma/SFT setleri.
- **Wikipedia dökümleri (trwiki):** Devam ön eğitimi için temiz, telifi uygun düz metin.
- **OPUS / Tatoeba:** Çeviri çiftleri; İngilizce veriyi Türkçe'ye taşımanın hammaddesi (SFT'ye dönüştürülebilir).
- **The Stack:** Kod ön eğitimi için büyük kod korpusu (lisans filtresiyle kullanın).
- **Common Crawl / FineWeb-2:** Ön eğitim ölçeğinde web metni; burada filtreleme kalitesi her şeydir.

Türkçe'ye özel koleksiyonlar ve indirme yöntemleri: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/).

## Kontrol Listesi: Veriye Başlamadan Önce

1. **Hangi eğitimi yapıyorum?** → Veri türünü yukarıdaki tablodan seçin.
2. **Hangi formatta olmalı?** → [Veri Formatları](/veri/veri-formatlari/).
3. **Yeterince temiz mi?** → [Veri Temizleme](/veri/veri-temizleme/).
4. **Test setini ayırdım mı?** → Sızıntıyı en baştan engelleyin.
5. **Lisans ve gizlilik kontrolü tamam mı?** → Metin ve görsellerde telif, kişisel veride KVKK.

## Kaynaklar ve İleri Okuma

- [Chinchilla çalışması: Training Compute-Optimal Large Language Models (arXiv:2203.15556)](https://arxiv.org/abs/2203.15556) — model boyutu ile eğitim token sayısının birlikte, eşit oranda ölçeklenmesi gerektiğini gösteren çalışma; "ne kadar veri yeter?" sorusunun temel referansı.
- [LIMA: Less Is More for Alignment (arXiv:2305.11206)](https://arxiv.org/abs/2305.11206) — yalnızca 1.000 özenle seçilmiş örnekle güçlü bir talimat takipçisi eğitilebildiğini gösteren "az ama öz" çalışması.
- [Scaling Data-Constrained Language Models (arXiv:2305.16264)](https://arxiv.org/abs/2305.16264) — veri kısıtı altında tekrarın ~4 epoch'a kadar taze veriye yakın sonuç verdiği, ötesinde azalan verime girildiği bulgusu.
- [TÜLU 3: Pushing Frontiers in Open Language Model Post-Training (arXiv:2411.15124)](https://arxiv.org/abs/2411.15124) — küratörlü, sentetik, tercih ve doğrulanabilir ödül verisini karıştıran açık bir post-training tarifi.

Sırada: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/) sayfasıyla ilk veri setinizi indirin.
