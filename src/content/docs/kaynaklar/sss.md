---
title: "Sıkça Sorulan Sorular"
description: "Başlangıç seviyesinde en çok sorulan 15 soru: donanım, maliyet, veri miktarı, Türkçe eğitim, lisanslar ve öğrenme sırası."
dogrulama: 2026-10-17
---

Bu sayfa, makine öğrenmesine yeni başlayanların en sık sorduğu soruları tek yerde toplar. Cevaplar kısa tutuldu; her cevabın sonundaki bağlantılarla ilgili sayfaya geçip derinleşebilirsiniz.

## 1. GPU'm yok, yine de model eğitebilir miyim?

Evet, ama küçük ölçekte. LoRA/QLoRA yöntemleriyle 1-4B parametreli modeller CPU üzerinde de eğitilebilir; ancak eğitim, GPU'ya kıyasla kat kat yavaş olur ve veriyi küçük tutmanız gerekir. CPU'da pratik sınır genellikle 1B civarı modellerdir. Ciddi denemeler için ücretsiz bulut GPU'lar (bir sonraki soru) çok daha mantıklıdır. Donanım planlaması için [VRAM Hesabı](/donanim/vram-hesabi/) ve yöntemler için [LoRA ve QLoRA](/llm/lora-qlora/) sayfalarına bakın.

## 2. Ücretsiz nerede eğitirim?

Google Colab'ın ücretsiz katmanında T4 sınıfı GPU, Kaggle'da ise haftalık sınırlı bir GPU kotası ücretsiz sunulur; ikisi de küçük QLoRA deneyleri için fazlasıyla yeterlidir. Hugging Face Spaces'teki ZeroGPU gibi paylaşımlı kaynaklar da hafif deneyler için değerlendirilebilir. Ücretsiz GPU'lar yoğun saatlerde sıra bekletebilir ve oturum süresi sınırlıdır; uzun eğitimler için kiralık GPU daha güvenilirdir. Ayrıntılı karşılaştırma: [Bulut Seçenekleri](/donanim/bulut-secenekleri/).

## 3. Küçük bir eğitim ne kadar sürer?

T4 benzeri bir GPU'da, QLoRA ile 1.000-10.000 örnek arası eğitimler tipik olarak yarım saat ile birkaç saat arasında sürer. Süreyi belirleyen üç şey: örnek sayısı, model boyutu ve dizi uzunluğu (sequence length). En güvenilir yöntem, 100 örnekle bir deneme koşup toplam süreyi ölçeklemektir. Zaman bütçesi planlaması için [Adım Adım Eğitim](/llm/adim-adim-egitim/) ve [Hiperparametreler](/llm/hiperparametreler/) sayfalarını okuyun.

## 4. Ne kadar veriye ihtiyacım var?

Kalite, miktardan önce gelir: LIMA deneyi, 1.000 özenle seçilmiş örnekle şaşırtıcı derecede iyi sonuç alındığını gösterdi. Çoğu kişisel proje için 500-5.000 temiz ve tutarlı örnek yeterlidir; bir milyon kötü örnek, bin iyi örnekten kötüdür. Dar bir görev (ör. e-posta taslağı yazma) için birkaç yüz örnek bile iş görebilir. Veri üretimi ve temizliği için [Kendi Verini Oluştur](/veri/kendi-verini-olustur/) ve [Veri Temizleme](/veri/veri-temizleme/) sayfalarına bakın.

## 5. Hangi modelle başlamalıyım?

Türkçe için Qwen3 (4B/8B), Gemma 3 (4B/12B) ve Llama 3.2 (1B/3B) iyi başlangıçlardır; hepsi çok dilli veriyle eğitildi ve Türkçe yetenekleri makuldür. 8-16 GB VRAM'de 4B modeller QLoRA ile rahat eğitilir; çok küçük bir kartta 1B ile başlayın. Seçim yaparken lisansın kullanım amacınıza uygunluğunu da kontrol edin ([Faydalı Linkler](/kaynaklar/faydali-linkler/) listesinde Türkçe model koleksiyonları var). Araç ve model ekosistemi için [Araçlar](/llm/araclar/) sayfası yol gösterir.

## 6. Full fine-tuning mi LoRA mı?

Neredeyse herkes için cevap LoRA/QLoRA: full fine-tuning modelin tüm parametrelerini günceller ve tipik olarak A100 sınıfı GPU'lar gerektirir. LoRA ile aynı işi çok daha mütevazı donanımla yaparsınız; kalite farkı çoğu görevde küçüktür. Full eğitim ancak büyük veri setiniz ve büyük GPU bütçeniz varsa anlamlıdır. Karşılaştırma için [LoRA ve QLoRA](/llm/lora-qlora/) ile [SFT (Denetimli İnce Ayar)](/llm/sft/) sayfalarına bakın.

## 7. Eğittiğim model kötü cevap veriyor, neden?

İlk şüpheli her zaman **veridir**: tutarsız, gürültülü ya da çok az örnek en yaygın sorundur. İkinci şüpheli sohbet şablonu (chat template) uyumsuzluğudur; eğitimde kullanılan şablonla çıkarımda kullanılan aynı değilse model "şaşkın" davranır. Aşırı eğitim (overfitting) da modeli eğitim verisine kilitler; loss eğrisinde doğrulama kaybının yükselmeye başlaması tipik işarettir. Sistematik teşhis için [Sorun Giderme](/llm/sorun-giderme/) ve metrik okuma için [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfalarını izleyin.

## 8. Türkçe eğitmek için özel bir şey gerekli mi?

Tek büyük fark **tokenizasyonda**: Türkçe, aynı içerik için İngilizce'ye kıyasla belirgin biçimde daha fazla token harcar (çoğu zaman 1,5-2 katı). Bu durum bağlam penceresini çabuk doldurur ve eğitim/maliyet hesabını şişirir; nedenini [Tokenizasyon](/temeller/tokenizasyon/) sayfasında anlatıyoruz. Ek Türkçe token eklemek (vocabulary extension) ileri seviye bir çözümdür; başlangıç için gerekli değildir. Kaliteli Türkçe veri setleri ve çok dilli modeller çoğu durumda yeterlidir: [Veri Nereden Bulunur](/veri/veri-nereden-bulunur/).

## 9. Sıfırdan model eğitmek istiyorum, olur mu?

Teknik olarak mümkün, bütçe olarak gerçekçi olalım: modern LLM ön eğitimi milyonlarca dolar ve binlerce GPU saati gerektirir. Öğrenme amaçlıysa cevap farklı: 10-100M parametreli küçük modelleri küçük veri setleriyle sıfırdan eğitmek harika bir deneyimdir ve dil modellerinin nasıl çalıştığını gerçekten öğretir. "Sıfırdan" hedefi üretim modeli değil anlayışsa [Ön Eğitim](/llm/pretraining/) ve [Klasik ML Temelleri](/klasik-ml/temeller/) sayfalarından başlayın.

## 10. DPO/RLHF şart mı?

Hayır. SFT (talimat verisiyle denetimli ince ayar) çoğu proje için yeterlidir; DPO ikinci bir iyileştirme aşamasıdır. DPO, "şu cevap iyi, bu cevap kötü" biçiminde tercih verisi toplayabildiğinizde anlam kazanır; RLHF ise daha ağır bir boru hattıdır ve başlangıç için kesinlikle gerekli değildir. Sıralamayı görmek için [SFT](/llm/sft/) ve [DPO ve RLHF](/llm/dpo-rlhf/) sayfalarına bakın.

## 11. Eğitim maliyeti ne olur?

Yerel donanımda maliyet elektrik ve zaman; ücretsiz bulut katmanlarında sıfır. Kiralık GPU'larda T4 sınıfı saatlik yaklaşık yarım dolar mertebesinde, A100 sınıfı birkaç dolar civarındadır ve 8B'lik bir QLoRA eğitimi tipik olarak birkaç GPU saati tutar. Yani ilk deneyleriniz çoğu zaman "bir kahve" bütçesiyle mümkündür. Güncel fiyatlar ve seçenekler için [Bulut Seçenekleri](/donanim/bulut-secenekleri/) sayfasına bakın.

## 12. Eğittiğim modeli nasıl test ederim?

En az 20-30 soruluk sabit bir test seti hazırlayıp cevapları gözle puanlayın; mümkünse sizi tanımayan birkaç kişiye de test ettirin. Loss ve doğrulama metrikleri yol göstericidir ama tek başına yeterli değildir; asıl ölçü insan değerlendirmesidir. Türkçe değerlendirme setleriyle karşılaştırma yapmak ve standart benchmarkları tanımak için [Benchmarklar ve Değerlendirme](/degerlendirme/benchmarklar/) ile [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/) sayfalarını okuyun.

## 13. Windows'ta sorun yaşar mıyım?

Genel akış Windows'ta çalışır: Python, PyTorch/CUDA, Unsloth ve Ollama Windows'u destekliyor. Sorunlar genellikle iki yerden çıkar: yalnızca Linux için derlenen paketler (ör. flash-attention) ve Linux gerektiren sunum araçları (ör. vLLM). Bu durumlarda WSL2 pratik çözümdür; başlangıç için buna ihtiyacınız yok. Kurulum adımları ve sık yaşanan sürücü/CUDA sorunları için [Yerel Kurulum](/donanim/yerel-kurulum/) sayfasına bakın.

## 14. Hangi sırayla öğrenmeliyim?

Önerilen sıra: kavramlar → Transformer mantığı → tokenizasyon → veri hazırlama → LoRA/QLoRA ile ilk ince ayar → değerlendirme → nicemleme ve paylaşım. [Yol Haritası](/baslangic/yol-haritasi/) sayfası bu sırayı haftalara bölünmüş biçimde ve bağlantılarıyla verir. [Kavramlar](/baslangic/kavramlar/) sayfası temel sözlük görevi görür; anlamını unuttuğunuz terimlerde [Sözlük](/kaynaklar/sozluk/) hızlı başvuru kaynağınızdır.

## 15. Eğittiğim modeli ticari olarak kullanabilir miyim?

Büyük ölçüde taban modelin lisansına bağlı: Apache-2.0 ve MIT lisanslı modellerle ürettiğiniz türevler ticari kullanıma açıktır. Llama ve Gemma modelleri de ticari kullanıma izin verir ama koşullarla (isimlendirme, kullanıcı sayısı eşiği, kullanım politikaları gibi). Türev modelinizin lisansı, taban modelinkinden daha serbest olamaz; veri setinizin lisansı da ayrıca önemlidir. Ayrıntılı tablo için [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/) sayfasındaki lisans bölümüne bakın.

Bir uyarı: **lisans bir model ailesinin adı değil, depodaki dosyadır.** Ölçtüğümüz bir örnek var — Qwen ailesinin çoğu boyutu Apache-2.0 iken `Qwen2.5-3B-Instruct` boyutu "Qwen Research License" altında ve ticari kullanım açıkça kapalı; o boyut, CPU'da çalıştığı için en çok seçilen boyut. Yerel paketlerinizdeki lisans alanlarının denetimi ve kişisel veri taraması: [Lisans, Kişisel Veri ve Model Kartı](/kullanim/lisans-ve-model-karti/).

---

Sorunuzun cevabını bulamadıysanız topluluk kaynakları ve Türkçe veri/model depoları için [Faydalı Linkler ve Kaynaklar](/kaynaklar/faydali-linkler/) sayfasına, temel kavramların tanımları için [Sözlük](/kaynaklar/sozluk/) sayfasına göz atın.
