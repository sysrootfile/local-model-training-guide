---
title: "Sözlük: Türkçe-İngilizce Terimler"
description: "Makine öğrenmesi ve LLM dünyasının en sık kullanılan terimlerinin Türkçe karşılıkları, okunuşları ve tek cümlelik açıklamaları."
dogrulama: 2026-10-19
---

Makine öğrenmesi metinlerinde sürekli karşınıza çıkan terimler için hızlı başvuru kaynağı. Terimler İngilizce adlarına göre alfabetik sıralanmıştır; ilk sütunda terimin kendisi, ikinci sütunda Türkçe karşılığı veya yaygın okunuşu, üçüncü sütunda tek cümlelik açıklaması yer alır.

:::tip
Bu sayfa sözlüktür, ders değil. Kavramları hikâyesiyle anlatan asıl sayfa [Kavramlar](/baslangic/kavramlar/) sayfasıdır; buradaki terimler orada bağlamıyla karşınıza çıkar.
:::

| Terim (İngilizce) | Türkçe okunuş / karşılık | Açıklama |
|---|---|---|
| Activation | aktivasyon | Bir sinir ağı katmanının çıktısını dönüştüren fonksiyon (ör. ReLU); ağa doğrusal olmayanlık katar. |
| Abstention | kaçınma | Modelin cevap vermemeyi (veya "bilmiyorum" şıkkını) seçmesi; güven eşiğinin altında kalan sorular için istenen davranış. Ölçümü: [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/). |
| AdamW | "adam-dablyu" | En yaygın kullanılan optimize edici (optimizer); gradyanları uyarlamalı ölçekler ve ağırlık sönümü uygular. |
| Adapter | adaptör | Taban modele sonradan eklenen, az sayıda eğitilebilir parametre içeren küçük modül (LoRA'da A ve B matrisleri). |
| Attention | "dikkat" (ıtenşın) | Her token'ın dizideki diğer token'ların hangilerine ve ne kadar "bakacağını" hesaplayan Transformer bileşeni. |
| AWQ | "ey-dablyu-kyu" | GPU'lar için donanım dostu 4-bit nicemleme yöntemi; vLLM gibi sunum motorlarında yaygındır. |
| Backpropagation | geri yayılım (bekpropıgeyşın) | Kaybın her ağırlığa ne kadar bağlı olduğunu geriye doğru hesaplayan, sinir ağı öğrenmesinin temel algoritması. |
| Batch size | yığın boyutu (beç says) | Modelin tek adımda birlikte işlediği örnek sayısı; VRAM tüketimini doğrudan etkiler. |
| Benchmark | kıyas testi (bençmark) | Modelleri aynı koşullarda karşılaştırmayı sağlayan standart görev ve test setleri. |
| bf16 / fp16 | "b-f-16", "f-p-16" | 16 bit sayı biçimleri: fp16 daha hassas, bf16 daha geniş aralıklı; modern GPU'da eğitim için bf16 tercih edilir. |
| bitsandbytes | "bits end bayts" | Modelleri 8/4-bit yükleyen kütüphane; QLoRA'nın NF4 desteğini sağlar. |
| BPE | "bi-pi-i" | Byte-Pair Encoding: en sık geçen karakter çiftlerini birleştirerek metni parçalara bölen tokenizasyon algoritması. |
| Calibration | kalibrasyon | Modelin bildirdiği olasılığın doğruluk oranıyla uyuşması: "0,9 dediğim soruların %90'ı doğru mu?" |
| Catastrophic forgetting | felaket unutma | İnce ayar sonrasında modelin önceki genel yeteneklerini büyük ölçüde kaybetmesi. |
| Chain-of-thought (CoT) | düşünce zinciri (çeyn-of-tot) | Modelin cevaba varmadan önce ara adımları yazmasını teşvik eden istem tekniği; akıl yürütme görevlerinde doğruluğu artırır. |
| Chat template | sohbet şablonu | Mesajları modelin beklediği özel denetim token'lı metin biçimine çeviren şablon. |
| Checkpoint | kontrol noktası (çekpoynt) | Eğitim sırasında periyodik olarak kaydedilen ağırlık anlık görüntüsü. |
| Concurrency | eşzamanlılık | Aynı anda sunucuya gelen istek sayısı. İstemci tarafı (kaç isteği birden salıyorsunuz) ile sunucu tarafı (`OLLAMA_NUM_PARALLEL`) ayrı şeylerdir; sunucu varsayılan ayardayken CPU'da artan istemci eşzamanlılığı gecikmeyi bölmez, her kullanıcı önündekilerin tamamını bekler. Yuva açılınca sıra kalkar ama iş paylaşılır: tek isteğin çözme hızı düşer. Yuvadan çok istek gelirse ikisi karışır — hız yuva sayısına göre düşer, taşan istekler sıraya girer. Ölçümü: [Eşzamanlılık](/kullanim/eszamanlilik/). |
| Confidence, verbalized | sözlü güven | Modele sayısal olarak kaçta kaç emin olduğu sorulduğunda verdiği bildirim; okunması zor çıktılar üretir. Ölçümü: [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/). |
| Context window | bağlam penceresi | Modelin tek seferde işleyebildiği en fazla token sayısı. |
| Cosine schedule | kosinüs programı | Öğrenme oranını eğitim boyunca kosinüs eğrisiyle azaltan planlama. |
| Cross-entropy | çapraz entropi | Modelin doğru token'a verdiği olasılığı cezalandıran temel dil modelleme kaybı. |
| Data collator | veri toplayıcı | Farklı uzunluktaki örnekleri eğitim için düzenli batch'lere dönüştüren yardımcı bileşen. |
| Dataset | veri kümesi | Eğitim ve doğrulama için kullanılan örnek koleksiyonu. |
| Diffusion model | difüzyon modeli | Görüntü ve ses üretiminde kullanılan, gürültüden temiz veri üretmeyi öğrenen model ailesi. |
| Distillation | damıtma (distileşın) | Büyük "öğretmen" modelin davranışını küçük "öğrenci" modele aktarma. |
| DPO | "di-pi-o" | Direct Preference Optimization: "iyi cevap / kötü cevap" tercih çiftleriyle modeli hizalayan yöntem. |
| Dropout | "dırap-aut" | Eğitim sırasında nöronların rastgele bir kısmını devre dışı bırakarak ezberlemeyi azaltan teknik. |
| ECE (Expected Calibration Error) | beklenen kalibrasyon hatası | Modelin verdiği olasılıkları kovalara ayırıp, her kovada bildirdiği sayı ile gerçek isabet oranı arasındaki farkı ağırlıklı toplayan tek sayı. |
| Embedding | gömme (embeding) | Metni anlam taşıyan sayı vektörlerine çevirme; arama ve RAG sistemlerinin temelidir. |
| Epoch | tur (epok) | Eğitim verisinin baştan sona bir tam geçişi. |
| Evaluation | değerlendirme | Model kalitesinin test setleri, metrikler ve insan incelemesiyle ölçülmesi. |
| Few-shot | az örnekli (fyu-şot) | İstem içinde birkaç örnek göstererek modele görevi tarif etme. |
| Fine-tuning | ince ayar (fayn-tüning) | Ön eğitilmiş modeli kendi verinizle yeni bir göreve uyarlama. |
| Flash Attention | "flaş ıtenşın" | Attention hesabını GPU belleğinde verimli yapan hızlandırma çekirdeği. |
| FP8 | "ef-pi-sekiz" | 8 bit kayan noktalı sayı biçimi; yeni nesil GPU'larda eğitim ve çıkarımı hızlandırır. |
| GGUF | "ci-ci-yu-ef" | llama.cpp ailesinin nicemlenmiş model dosya biçimi; Ollama ve LM Studio'nun standardı. |
| GPTQ | "ci-pi-ti-kyu" | GPU'da 4-bit çıkarım için eski ama yaygın nicemleme yöntemi. |
| Gradient | gradyan (eğim) | Kaybı azaltmak için her ağırlığın hangi yönde güncelleneceğini söyleyen türev. |
| Gradient accumulation | gradyan biriktirme | Küçük batch'lerin gradyanlarını toplayarak büyük batch etkisi yaratma. |
| Gradient checkpointing | gradyan kontrol noktalaması | Ara aktivasyonları saklamak yerine gerektiğinde yeniden hesaplayarak VRAM tasarrufu sağlama. |
| GRPO | "ci-ar-pi-o" | Group Relative Policy Optimization: cevap gruplarını birbiriyle kıyaslayan pekiştirmeli öğrenme yöntemi. |
| Hallucination | halüsinasyon | Modelin bilmediği konuda emin bir dille yanlış veya uydurma bilgi üretmesi. |
| Hard negative | zor negatif | Modelin doğru sandığı yanlış eşleşme; gömme eğitiminde en öğretici ama en tehlikeli negatif türü, çünkü madenciyi yanlışı doğrulayan modelin kendisi seçer. |
| Hyperparameter | hiperparametre | Eğitimin kendisinin öğrenmediği ayarlar: öğrenme oranı, batch boyutu, LoRA rütbesi vb. |
| In-batch negatives | batch içi negatifler | Aynı batchteki diğer örneklerin, her satır için bedava negatif sayılması; `MultipleNegativesRankingLoss` mantığı budur. |
| Inference | çıkarım (infirıns) | Eğitilmiş modelin yeni bir girdiye cevap üretmesi; "kullanım" aşaması. |
| Instruction tuning | talimat ayarı | Modeli "istek → yanıt" biçimindeki örneklerle ince ayarlama. |
| JSONL | "cey-son-el" | Her satırında bağımsız bir JSON nesnesi bulunan dosya biçimi; veri setlerinde yaygındır. |
| KL divergence | KL ayrışması (ka-el diverjansı) | İki olasılık dağılımının birbirinden ne kadar farklı olduğunu ölçen metrik; hizalama eğitimlerinde modeli tabandan fazla uzaklaştırmamak için kullanılır. |
| KV cache | "kı-vi" önbellek | Üretim sırasında önceki token'ların dikkat hesaplarını saklayarak hız kazandıran bellek alanı. |
| Learning rate | öğrenme oranı (lörning reyt) | Her güncellemede ağırlıkların ne kadar değişeceğini belirleyen en kritik hiperparametre. |
| LLM | büyük dil modeli (el-el-em) | Yüz milyonlarca ila trilyonlarca parametreli, dev metinlerle eğitilmiş dil modeli. |
| Logprob | log olasılığı (logprob) | Bir token'ın doğal logaritmik olasılığı; sıfıra yaklaştıkça kesinlik artar. Ollama'da `logprobs: true` ile istenir, `top_logprobs` tavanı 20'dir. |
| LoRA | "lora" | Low-Rank Adaptation: taban modeli dondurup küçük düşük rütbeli matrisler eğiten verimli ince ayar yöntemi. |
| LoRA alfa (alpha) | "lora alfa" | Adaptörün taban modele etki gücünü ayarlayan ölçek katsayısı; pratikte sıkça rütbenin iki katı seçilir. |
| Loss | kayıp | Modelin tahmininin doğru cevaptan ne kadar uzak olduğunu ölçen sayı; eğitimde düşürülmeye çalışılır. |
| Merge | birleştirme (merc) | LoRA adaptör ağırlıklarının taban modele kalıcı olarak kaynaştırılması. |
| Mixture of Experts | uzmanlar karışımı (MoE) | Her token için uzman alt ağların yalnızca küçük bir kısmını devreye alan verimli mimari. |
| Model card | model kartı | Modelin tanıtım, eğitim ve lisans bilgilerini içeren, modelle birlikte yayınlanan sayfa. |
| Multimodal | çok modlu (multimodal) | Metin, görüntü ve ses gibi birden fazla veri türünü birlikte işleyebilen model. |
| Multiple Negatives Ranking Loss (MNRL) | çoklu negatif sıralama kaybı | Gömme eğitiminde en yaygın kayıp: her satırın doğrusunu, aynı batchteki diğerlerinden ayırmayı öğretir; negatifleri siz etiketlemezsiniz. |
| NF4 | "en-ef-dört" | QLoRA'nın kullandığı 4-bit NormalFloat sayı biçimi. |
| Overfitting | aşırı öğrenme, ezberleme | Modelin eğitim verisini ezberleyip yeni verilerde kötüleşmesi. |
| Packing | paketleme | Kısa örnekleri tek diziye birleştirerek dolgu israfını azaltma tekniği. |
| P(True) | doğru şıkkın olasılığı | Doğru cevabı veren token'ların kütlesinin, tüm cevap adaylarının kütlesine bölünmesiyle bulunan güven ölçüsü. |
| Padding | doldurma (peding) | Farklı uzunluktaki dizileri eşitlemek için eklenen dolgu token'ları; gereksizse israftır. |
| Parameter | parametre | Modelin veriden öğrendiği sayısal ağırlıklardan her biri; model boyutu bu sayıyla ölçülür. |
| PEFT | "peft" | Parameter-Efficient Fine-Tuning: parametrelerin küçük bir bölümünü eğiten yöntemler ailesi (LoRA vb.). |
| Perplexity | şaşkınlık (perpleksiti) | Modelin bir metne "şaşırma" derecesi; düşük değer daha iyi dil modeli demektir. |
| Pipeline | akış hattı (payplayn) | Veri toplama, temizleme, eğitim ve değerlendirme adımlarının uçtan uca zinciri. |
| Position bias | konum yanlılığı | Modelin içeriğe değil şıkkın harfine veya yerine bakması; seçimler tek bir harfe yığılıyorsa olasılık eşiği ayırıcı olmaktan çıkar. |
| Precision | hassasiyet | Sayıların kaç bitte tutulduğu: fp32, fp16, bf16, int8, int4 gibi. |
| Pretraining | ön eğitim (pri-treynig) | Modelin devasa metinlerle "sonraki token'ı tahmin et" göreviyle sıfırdan eğitilmesi. |
| Prompt | istem | Modele verilen talimat veya metin. |
| Prompt engineering | istem mühendisliği | Model davranışını eğitim olmadan yönlendirmek için istemin dikkatle tasarlanması. |
| QLoRA | "kyu-lora" | Taban modeli 4-bit (NF4) yükleyip üzerine LoRA eğitme yöntemi; tek tüketici GPU'sunda büyük model eğitmenin anahtarı. |
| Quantization | nicemleme (kuantizasyon) | Ağırlıkları daha az bitte temsil ederek modeli küçültme ve hızlandırma. |
| Rank (r) | rütbe, derece | LoRA'nın eklediği düşük rütbeli matrislerin boyutu; büyüdükçe kapasite artar, eğitim ağırlaşır. |
| RAG | "rag" | Retrieval-Augmented Generation: modelin istemine dış belgelerden getirilen bilgilerin eklenmesi. |
| Reinforcement Learning | pekiştirmeli öğrenme | Ödül sinyaliyle deneme-yanılma üzerinden öğrenme. |
| RLHF | "er-el-eyç-ef" | Reinforcement Learning from Human Feedback: insan tercihleriyle eğitilen ödül modeli üzerinden pekiştirmeli öğrenme. |
| RoPE | "rope" (döner konum kodlaması) | Modelin token sırasını anlamasını sağlayan, günümüzde en yaygın konum kodlama yöntemi. |
| Safetensors | "seyf-tensırs" | Hugging Face ekosisteminde yaygın, hızlı ve kod çalıştırmayan güvenli ağırlık dosya biçimi. |
| Sampling | örnekleme | Sıradaki token'ın olasılık dağılımından seçilmesi; temperature ve top-p ile ayarlanır. |
| Seed | tohum (sid) | Rastgeleliği sabitleyen sayı; aynı tohum aynı deneyi tekrarlanabilir kılar. Dil modelinde neyi sabitleyip neyi sabitlemediği ölçüldü: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/). |
| Self-consistency | öz-tutarlılık | Aynı soruyu sıcaklıkla birkaç kez örnekleyip çoğunluk cevabını alma; örnekler tek cevaba yığılıyorsa çeşitlilik, dağılıyorsa belirsizlik okunur. |
| Semantic entropy | anlamsal entropi | Örneklenen cevaplar **anlam** düzeyinde kümelenip küme ağırlıklarından entropi çıkarır; kelime farkını değil kavram farkını ölçer. |
| SFT | "es-ef-ti" | Supervised Fine-Tuning: etiketli girdi-çıktı örnekleriyle denetimli ince ayar. |
| Small Language Model | küçük dil modeli | Yaklaşık 0,5-15 milyar parametreli, yerel donanımda çalışabilen dil modelleri. |
| Slot | yuva (slot) | Sunucunun aynı anda işlediği bir istek kovanı: bağlam ve KV önbelleği yuva başına ayrılır, yani yuva sayısı bellek bedelidir — ama bedel yuva başına **eşit adım değil** (ölçülen: ilk ek yuva ≈233 MiB, sonraki ikisinin başına ≈145 MiB). Ollama'da sayısını `OLLAMA_NUM_PARALLEL` belirler, sunucu açılışında okunur ve yeniden başlatma ister. Ölçümü: [Eşzamanlılık](/kullanim/eszamanlilik/). |
| Step | adım (step) | Tek bir batch üzerinden yapılan ağırlık güncellemesi; epoch'un alt birimi. |
| System prompt | sistem istemi | Modelin kişiliğini ve kurallarını belirleyen, sohbetin başında verilen talimat. |
| Temperature | sıcaklık | Örnekleminin rastgelelik derecesi; 0'a yakın değerler tutarlı, yüksek değerler yaratıcı çıktı üretir. |
| Test set | test seti | Hiçbir ayar için kullanılmayan, son ölçüm için ayrılmış veri kümesi. |
| Throughput | verim (trurput) | Sunucunun saniyede ürettiği token sayısı; eşzamanlı kullanıcı sayısıyla birlikte değerlendirilir. |
| Token | "token" (jeton) | Metnin tokenizer tarafından bölündüğü en küçük birim; kelimeden küçük, karakterden büyük olabilir. |
| Tokenizer | "tokenizer" (jetonlaştırıcı) | Metni token'lara ve onların sayısal kimliklerine çeviren bileşen. |
| Top-p | "top-p", çekirdek örnekleme | En olası token'ların toplam olasılığı p'ye ulaşana kadarki kümeden örnekleme. |
| Training | eğitim | Model ağırlıklarının veriyle güncellendiği süreç. |
| Transformer | "transformer" | Attention tabanlı, günümüz LLM'lerinin temel mimarisi. |
| Truncated entropy | kırpılmış entropi | Yalnızca dönen ilk k aday yeniden normalize edilerek hesaplanan entropi; kuyruk görünmediği için **alt sınırdır**, gerçek entropiyi geçmez. |
| Underfitting | eksik öğrenme | Modelin eğitim verisini bile yeterince öğrenememesi; kapasite, veri veya süre yetersizliğinden olur. |
| Validation | doğrulama | Modelin eğitimde görmediği veriler üzerindeki performansının izlenmesi. |
| Vocabulary | sözlük (vokebüleri) | Tokenizer'ın tanıdığı tüm token'ların kümesi; boyutu, modelin diller arası verimliliğini etkiler. |
| VRAM | "vi-ram" | Ekran kartı (GPU) belleği; model boyutu ve nicemleme seçimini belirleyen ana kısıt. |
| Warmup | ısınma | Öğrenme oranının eğitimin başında sıfırdan hedef değere kademeli çıkarılması. |
| Weight decay | ağırlık sönümü | Ağırlıkların büyümesini engelleyerek ezberlemeyi azaltan düzenlileştirme. |
| Weights | ağırlıklar (veyts) | Modelin öğrenilmiş parametreleri; nicemleme ve birleştirme işlemlerinin konusu olan sayılar. |
| Zero-shot | sıfır örnekli | Hiç örnek vermeden modele doğrudan görev sorma. |

## Sık karıştırılan kavramlar

- **Fine-tuning ile pretraining:** Pretraining sıfırdan, dev veriyle ve pahalıdır; fine-tuning mevcut bir modelle küçük veriyle ve görece ucuzdur.
- **LoRA ile QLoRA:** LoRA'da taban model normal hassasiyette (fp16) durur; QLoRA'da 4-bit yüklenir. QLoRA daha az VRAM ister, LoRA biraz daha yüksek sadakat sunar.
- **Epoch ile adım (step):** Bir adım tek batch'lik ağırlık güncellemesidir; epoch tüm verinin bir turudur. Örneğin 10.000 örnek ve batch boyutu 8 ise bir epoch = 1.250 adım.
- **Parameter ile hyperparameter:** Parametre modelin veriden öğrendiği ağırlıktır; hiperparametre sizin seçtiğiniz ayardır (öğrenme oranı gibi).
- **Precision ile quantization:** Precision "sayılar kaç bit?" sorusunun genel adıdır; quantization ise bu bit sayısını bilinçli olarak düşürme işlemidir.
- **Loss ile perplexity:** Loss eğitimde kullanılan hata ölçüsüdür; perplexity, loss'un yorumlaması daha kolay olan türevidir ve dil modellerinde sık kullanılır.
- **Validation ile test seti:** Doğrulama kümesine geliştirme sırasında (model seçimi, erken durdurma) bakılır; test seti ise en son ölçüm için ayrılmıştır.
- **Temperature ile top-p:** İkisi de örnekleme ayarıdır; temperature dağılımın şeklini, top-p ise seçilebilecek token kümesinin genişliğini değiştirir. Üçüncü bir kesim biçimi olan min-p, en olası adayın bir kesri kadar olasılığı olanları tutar; üçünün davranışı ve Ollama'daki varsayılanları: [Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/).
- **Temperature ile kalibrasyon:** Sıcaklık **hangi** token'ın seçileceğini değiştirir; modelin size bildirdiği olasılığın doğrulukla uyuşup uyuşmadığı (kalibrasyon) ayrı bir sorudur. Bu makinede Ollama'nın bildirdiği logprob'un sıcaklıktan etkilenmediği ölçüldü: [Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/).
- **Logprob ile doğruluk:** Dizin logprob'u modelin ne kadar **emin göründüğünü** ölçer, cevabın doğru olup olmadığını değil. Ölçülmüş örnek: ortalama logprob −0,0028 (yani neredeyse kesinlik) verilen bir cevabın yanlış çıkması.
- **P(secilen) ile P(altın):** Seçilen şıkkın olasılığı üretim anında elde vardır ve eşik kurmakta kullanılır; altın şıkkın olasılığı etiketi bildiği için yalnız analiz sayısıdır.

## İlgili sayfalar

- Kavramların hikâyeli anlatımı: [Kavramlar](/baslangic/kavramlar/)
- Eğitimde kullanılan hiperparametrelerin pratik anlamı: [Hiperparametreler](/llm/hiperparametreler/)
- Daha fazla Türkçe ve İngilizce kaynak: [Faydalı Linkler ve Kaynaklar](/kaynaklar/faydali-linkler/)
