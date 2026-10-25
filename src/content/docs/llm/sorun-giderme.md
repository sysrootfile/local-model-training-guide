---
title: "Sorun Giderme: Eğitimde Karşılaşılan Hatalar"
description: "CUDA bellek hatasından NaN kaybına, Windows tuzaklarından disk sorunlarına ve GGUF/sürüm uyuşmazlıklarına: eğitimde karşılaşılan 11 yaygın sorunun belirti-neden-çözüm rehberi."
dogrulama: 2026-10-15
---

Eğitim sırasında bir hata aldığınızda paniklemeyin: deneyimli kişilerin günlerini yiyen sorunların %90'ı bu sayfadaki on bir başlıktan biridir. Her başlıkta şu yapıyı izliyoruz: **belirti → neden → çözüm öncelik sırası**. Çözümleri sırayla deneyin; her adımdan sonra eğitimi yeniden başlatıp sonucu gözlemleyin.

**Hızlı indeks:**

| Yakınmanız | Bölüm |
| --- | --- |
| "CUDA out of memory" | 1 |
| Kayıp NaN / inf | 2 |
| Kayıp hiç düşmüyor | 3 |
| Model saçmalıyor | 4 |
| Eğitim çok yavaş | 5 |
| Windows'a özel hatalar | 6 |
| "input too long" / bağlam aşımı | 7 |
| "no space left on device" | 8 |
| "Expected all tensors to be on the same device" | 9 |
| "Ollama/GGUF'ta bozuk konuşma" | 10 |
| "bitsandbytes / CUDA sürüm hatası" | 11 |

## 1. CUDA out of memory (En Sık Karşılaşılan)

**Belirti:** `torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate ...` — eğitim bazen hemen başlarken, bazen saatler sonra düşer.

**Neden:** İhtiyaç duyulan bellek, GPU'nuzdakinin üzerine çıkmıştır. En pahalı üç kalem: model ağırlıkları, gradyanlar + iyileştirici (optimizer) durumu, ve aktivasyonlar (dizi uzunluğu × batch).

**Çözüm merdiveni — sırayla inin:**

| # | Adım | Etki | Maliyet |
| --- | --- | --- | --- |
| 1 | `per_device_train_batch_size` değerini 1'e indirin | Yüksek | Hafif yavaşlar |
| 2 | `gradient_accumulation_steps` ile etkin batch'i koruyun (ör. 8'e çıkarın) | — | Biraz yavaşlar |
| 3 | `max_length` değerini kısaltın (ör. 2048 → 1024 → 512) | Yüksek | Uzun örnekler kırpılır |
| 4 | `gradient_checkpointing=True` açın | Orta-yüksek | ~%20-30 yavaşlar |
| 5 | 4-bit QLoRA'ya geçin (`load_in_4bit=True`) | Çok yüksek | Küçük kalite/hız maliyeti |
| 6 | Daha küçük model (8B → 4B) veya daha küçük `r` | Çok yüksek | Görev performansı düşebilir |
| 7 | Buluta taşının (daha büyük GPU) | Sorun biter | Para maliyeti |

```bash title="VRAM_izleme.sh"
# Linux / WSL2: canlı VRAM takibi
watch -n 1 nvidia-smi

# Tek seferlik özet sorgu
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

Python içinden tepe (pik) bellek kullanımını ölçmek isterseniz: `torch.cuda.max_memory_allocated() / 1024**3` o ana kadarki en yüksek tahsisi GB cinsinden verir; sayaç `torch.cuda.reset_peak_memory_stats()` ile sıfırlanır. Bu değer `nvidia-smi`'nin gösterdiğinden biraz düşük olabilir — aradaki fark PyTorch'un önbellek havuzudur, sızıntı değildir.

:::caution
**"VRAM boşta görünüyor ama OOM alıyorum" notu (Windows):** Windows'ta tarayıcı sekmeleri, oyun istemcileri ve hatta masaüstü bile GPU belleği tutar; Görev Yöneticisi bunu "paylaşımlı bellek" diye gösterebilir. Eğitim öncesi tarayıcıyı kapatmak bazen 1-2 GB kazandırır. Ayrıca `torch.cuda.empty_cache()` yalnızca boşta duran önbelleği bırakır; aktif eğitim sırasında mucize beklemeyin.
:::

:::danger
`max_split_size_mb` gibi ortam değişkeni hileleri bazen yardımcı olur ama kök sorun belliyken (model + batch + dizi) bunlarla vakit kaybetmeyin; merdivende bir adım daha inin.
:::

İlgili sayfalar: [VRAM Hesaplama](/donanim/vram-hesabi/), [LoRA ve QLoRA](/llm/lora-qlora/), [Bulut Seçenekleri](/donanim/bulut-secenekleri/).

## 2. Kayıp (Loss) NaN veya inf Oluyor

**Belirti:** Kayıp tablosunda `nan` veya `inf`; ardından tüm gradyanlar bozulur, model çöp olur.

**Nedenleri ve çözümleri (sırayla):**

1. **Öğrenme oranı çok yüksek** — model başlangıçta savrulur. lr'ı yarıya indirin; LoRA için 2e-4'ten başladıysanız 1e-4 deneyin. Detay: [Hiperparametreler](/llm/hiperparametreler/).
2. **fp16 kararsızlığı** — fp16 sayı aralığı dardır; taşma (overflow) NaN üretir. Mümkünse `bf16=True` kullanın (RTX 30xx ve üstü destekler). Eski kartta kalmak zorundaysanız loss scaling açık olsun (Trainer varsayılan olarak yapar).
3. **Bozuk veri** — bir örnekte NaN içeren sayısal alan veya bozuk karakter dizisi olabilir. Veriyi tazeleyin: metin alanlarının string, sayıların sonlu olduğunu doğrulayan küçük bir kontrol betiği yazın.
4. **Warmup eksikliği** — eğitimin en başında hedef lr'a direkt atlamak patlamalara yol açar; `warmup_steps=0.03` ekleyin (v5; eskiden `warmup_ratio` — eski ad güncel transformers sürümlerinde hata verir).

:::tip
NaN'ın hangi örnekten geldiğini bulmanın basit yolu: eğitim verisini 100 örnekten oluşan küçük parçalara bölüp hangi parçada NaN oluştuğunu deneyerek daraltın. Genelde suçlu, verinin binde birlik kesimindeki birkaç bozuk örnektir.
:::

İlgili sayfa: [Hiperparametreler](/llm/hiperparametreler/).

## 3. Kayıp Düşmüyor / Model Öğrenmiyor

**Belirti:** Kayıp eğitim boyunca neredeyse sabit; model çıktısı eğitim öncesiyle aynı.

**Kontrol listesi (sırayla bakın):**

1. **Veri formatı ve chat template** — en sık neden! Eğitimde `apply_chat_template` kullanmadıysanız veya verinin alan adları beklenenden farklıysa model aslında "alakasız metin" görüyor olabilir. Bir örneği tokenizer'dan geçirip **insan gözüyle** okuyun.
2. **Öğrenme oranı çok düşük** — tam ince ayar lr'ı (2e-5) ile LoRA yapmak klasik hatadır; LoRA 1e-4 – 2e-4 ister.
3. **Hiçbir katman eğitilmiyor olabilir** — PEFT kullanıyorsanız `model.print_trainable_parameters()` çıktısını kontrol edin; "%0" görüyorsanız LoRA yanlış yere uygulanmıştır (ör. `target_modules` hiçbir katman adıyla eşleşmiyor).
4. **Etiketler tümden maskeli** — `assistant_only_loss` kullanıp veri şablonu bozuksa tüm etiketler `-100` olabilir ve kayıp anlamsızlaşır. Kayıp değeri tam olarak 0 veya sabit bir tuhaf değerse şüphelenin.
5. **Tokenizer uyumsuzluğu** — model ve tokenizer farklı sürümlerden yüklenmişse (ör. base vs. instruct) jetonlar eşleşmez. İkisini aynı model kimliğinden yükleyin.

İlgili sayfalar: [Talimat Ayarı (SFT)](/llm/sft/), [Veri Formatları](/veri/veri-formatlari/).

## 4. Eğitim Bitti Ama Model Saçmalıyor

**Belirti:** "Kayıp düştü, her şey yolunda görünüyordu ama model ya aynı cümleyi tekrarlıyor, ya soruyu cevaplamıyor, ya da anlamsız metin üretiyor."

Bu, eğitim sürecinin en yanıltıcı senaryosudur. Sırayla kontrol edin:

1. **Yanlış chat template (en klasik):** Eğitimde kullanılan şablonla çıkarımda (inference) kullanılan şablon farklıysa model "dağılır". Eğitim verinizde Qwen şablonu varsa çıkarımda da aynı şablon kullanılmalı: `tokenizer.apply_chat_template(mesajlar, tokenize=False, add_generation_prompt=True)`.
2. **Aşırı ezber (overfitting):** Çok epoch + az veri = model eğitim örneklerini kelime kelime tekrarlar, yeni sorularda tökezler. Çözüm: epoch azaltın, doğrulama kaybını izleyin ([Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/)).
3. **Adaptör hiç yüklenmemiş:** `PeftModel.from_pretrained(temel_model, "./adaptor")` yerine sadece temel modeli yüklediyseniz elbette değişiklik görmezsiniz. Çıkarım betiğinizin adaptörü yüklediğini doğrulayın.
4. **Veri kalitesi:** Örneklerin bir kısmı çeviri artığı, yarım cümle veya yanlış cevapsa model bunların ortalaması olur. 200 örneği elle okuyun — kaç tanesi gerçekten örnek alınacak kalitede?
5. **Üretim ayarları:** `temperature`, `top_p`, `repetition_penalty` gibi üretim parametreleri bozuksa model suçsuzdur. Varsayılanlarla deneyin (`temperature=0.7, top_p=0.9` civarı).

İlgili sayfalar: [Talimat Ayarı (SFT)](/llm/sft/), [Ollama](/kullanim/ollama/) ile hızlı üretim testi.

## 5. Eğitim Çok Yavaş İlerliyor

**Belirti:** Adım başına saniyeler; GPU kullanımı `nvidia-smi`'de %100'ün altında geziyor.

**Nedenler ve çözümler:**

- **Veri yükleme darboğazı** — GPU veri bekliyor. `dataloader_num_workers` değerini artırın (ör. 4-8); veriyi önceden jetonlayıp diske kaydedin (map işlemini her çalıştırmada tekrarlamayın, `dataset.map(..., num_proc=4)` ve `save_to_disk` kullanın).
- **Packing kapalı** — kısa örneklerde GPU'nun yarısı boş bekler; `packing=True` belirgin hız kazandırır ([Hiperparametreler](/llm/hiperparametreler/)).
- **Batch 1 ile çalışmak** — zorunluysa gradient accumulation'ı artırın; ama mümkünse batch'i 2-4'e çıkarın.
- **Flash Attention yok** — açıksa kayda değer hızlanma sağlar; ancak kurulumu (özellikle Windows'ta) zahmetlidir. Önce her şeyi onsuz çalıştırın, sonra optimizasyon olarak ekleyin.

:::note
**Beklenti yönetimi:** Tek RTX 4090'da 4B modelin QLoRA ile 5.000 örnek üzerinde 1 epoch eğitimi kabaca **1-2 saat** sürer. "10 dakikada bitti" diyorsanız bir şey yanlıştır (muhtemelen veri okunmuyor); "3 gündür sürüyor" diyorsanız packing kapalı veya veri darboğazı vardır.
:::

İlgili sayfalar: [Hiperparametreler](/llm/hiperparametreler/), [VRAM Hesaplama](/donanim/vram-hesabi/).

## 6. Windows'a Özel Sorunlar

Windows'ta doğrudan eğitim mümkündür ama ekosistem ağırlıklı olarak Linux varsayar. En pratik çözüm: **WSL2** (Windows içinde gerçek bir Linux ortamı) — GPU sürücüleri doğrudan desteklenir ve `bitsandbytes`, `flash-attn`, `triton` gibi paketler sorunsuz kurulur.

- **bitsandbytes sürüm sorunları:** Windows'ta native kurulumda bazı sürümler hata verir; WSL2'ye geçin veya güncel `bitsandbytes` sürümünü kullanın. "4-bit eğitim açılmıyor" hatasının %90'ı bununla ilgilidir. Kurulum ayrıntıları: [Yerel Kurulum](/donanim/yerel-kurulum/).
- **Uzun dosya yolu hatası:** Windows'ta 260 karakteri aşan yollar (derin `site-packages` + cache klasörleri) hata üretir. Çözüm: "Uzun yolları etkinleştir" ayarını açın (Yönetici PowerShell: `Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name LongPathsEnabled -Value 1`) ve projeleri kısa bir yol altında tutun (ör. `C:\ml\`).
- **triton / flash-attn kurulumu:** Windows native'de derleme gerekebilir ve saatler alabilir. WSL2 kullanın; flash-attn gerekmiyorsa kurmayın.

İlgili sayfa: [Yerel Kurulum](/donanim/yerel-kurulum/).

## 7. Jeton / Bağlam Aşımı Hataları

**Belirti:** `Token indices sequence length is longer than the specified maximum...` uyarısı, `input too long` hatası veya kesilen garip örnekler.

**Ne yapmalı:**

1. Verinin jeton uzunluğu dağılımına bakın: `dataset.map(lambda x: {"n": len(tokenizer(x["text"])["input_ids"])})` ile ölçüp yüzdelik dilimlere bakın. `max_length`'i %95'i kapsayacak şekilde seçin.
2. Kırpma stratejisi bilinçli olsun: sohbette sistem istemini **asla** kırpmayın; uzun konuşmalarda son N turu tutun.
3. Modelin mimari üst sınırını (ör. 8.192 veya 32.768 jeton) aşmayın — aşarsanız sessiz bozulma veya hata alırsınız.

İlgili sayfalar: [Jetonizasyon](/temeller/tokenizasyon/), [Hiperparametreler](/llm/hiperparametreler/).

## 8. Disk Doldu

**Belirti:** Eğitim ortasında "no space left on device" veya checkpoint kaydederken hata. Model eğitimleri diski hızla şişirir: her checkpoint, modelin tam boyutu (ve iyileştirici durumuyla birlikte daha fazlası) kadar yer kaplar.

**Çözümler:**

- **Checkpoint stratejisi:** `save_strategy` ve `save_steps` ile kayıt sıklığını seyreltin; `save_total_limit=2` ile en yeni 2 checkpoint'in dışındakiler otomatik silinsin.
- **Eski deneyleri temizleyin:** `output_dir` altındaki eski `checkpoint-*` klasörlerini düzenli olarak silin.
- **Hugging Face önbelleği:** İndirilen her model `~/.cache/huggingface` (Windows: `C:\Users\<kullanıcı>\.cache\huggingface`) altında birikir. Kullanmadığınız modelleri silin; `HF_HOME` ortam değişkeniyle önbelleği başka bir diske taşıyabilirsiniz.
- **LoRA avantajı:** Adaptör eğitiyorsanız sonuçlar zaten MB boyutundadır; asıl yük checkpoint'lerdedir — bu yüzden `save_total_limit` en etkili çözümdür.

## 9. Cihaz Uyuşmazlığı: "Expected all tensors to be on the same device"

**Belirti:** `RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!`

**Neden:** Modelin veya girdilerin bir kısmı GPU'da, bir kısmı CPU'da kalmıştır. `device_map="auto"` ile yüklenen 4-bit modellerde bu özellikle yaygındır: bazı katmanlar bilinçli olarak CPU'da tutulur ve modele elle müdahale etmek dengeyi bozar.

**Çözümler (sırayla):**

1. Kod içinde `model.to("cuda")` veya `model.cuda()` çağrısı varsa **kaldırın** — `device_map` kullanan modellerde bu yasaktır.
2. Girdi tensörlerini modelin cihazına taşıyın: `girdiler = {k: v.to(model.device) for k, v in girdiler.items()}`.
3. Eğitimde `Trainer` kullanıyorsanız cihaz yerleşimini Trainer'a bırakın; elle müdahale etmeyin.
4. Sorun sürerse `device_map="auto"` yerine tek GPU'ya açık yerleşim deneyin: `device_map={"": 0}`.

İlgili sayfa: [Yerel Kurulum](/donanim/yerel-kurulum/).

## 10. Model Eğitildi Ama Ollama/GGUF'ta Bozuk Konuşuyor

**Belirti:** Aynı model Python'da (transformers/PEFT ile) düzgün yanıt verirken GGUF'a çevrilip Ollama'da çalıştırıldığında üç klasik davranıştan birini gösterir: soruyu yankılıyor, base model gibi devam metni üretiyor ya da sohbet şablonu token'larını (ör. `<|im_start|>` / `<|im_end|>`) düz metin olarak yazıyor.

**Neden:** Model eğitim boyunca belirli bir sohbet şablonuyla jetonlanmış örnekler gördü; çıkarımda bu şablon uygulanmazsa "soru-cevap" değil "metin tamamlama" yapmaya başlar. Unsloth dokümantasyonu, bu tür bozuk çıktıların en yaygın nedenini "eğitimde kullanılanla aynı olmayan sohbet şablonu" olarak gösterir. Şablon GGUF/Modelfile katmanına taşınmadıysa Ollama ham metni modele verir; sonuç tanıdık "bozuk konuşma" tablosudur.

**Çözümler (sırayla):**

1. **Şüpheyi izole edin:** GGUF öncesi modeli transformers/PEFT ile `tokenizer.apply_chat_template(..., add_generation_prompt=True)` kullanarak test edin ([SFT](/llm/sft/) sayfasındaki çıkarım örnekleri). Python'da düzgün yanıt veriyorsa hata, dışa aktarım / şablon taşıma katmanındadır.
2. **Şablonu dışa aktarım akışına dahil edin:** Tokenizer'da eğitimdeki sohbet şablonu ayarlıyken GGUF üretin (ör. Unsloth'un `save_pretrained_gguf` akışı — Unsloth, "eğitimde ve çıkarımda aynı şablon" kuralını vurgular ve şablonu zorlamak için konuşmalı not defterlerini önerir). Kullandığınız dönüştürücünün şablonu GGUF dosyasına gerçekten gömdüğünü küçük bir testle doğrulayın; gömülmüyorsa 3. adıma geçin.
3. **Şablonu Ollama Modelfile'da tanımlayın:** GGUF'ta şablon yoksa `TEMPLATE` bloğu ve `PARAMETER stop` ile dışarıdan verin; kapanış token'ı modele göre değişir (ör. Qwen/ChatML'de `<|im_end|>`, Llama 3'te `<|eot_id|>`). Hazır Modelfile örneği [Ollama Rehberi](/kullanim/ollama/) sayfasında.
4. **Veri tarafını da kontrol edin:** Eğitim verisinde alanlar yanlış eşlendiyse model şablonu hiç öğrenmemiş olabilir; verinizi [Veri Formatları](/veri/veri-formatlari/) sayfasıyla karşılaştırın.

:::note
Unsloth resmî SSS'sinin özeti: bu davranışların en yaygın çözümü, eğitimde kullanılan sohbet şablonunu çıkarımda da zorlamaktır. Şüphelendiğinizde ilk test şu sorudur: "Aynı istem, GGUF öncesi modelde Python'da çalışıyor mu?"
:::

İlgili sayfalar: [Ollama Rehberi](/kullanim/ollama/), [Veri Formatları](/veri/veri-formatlari/), [SFT](/llm/sft/).

## 11. Sürüm Uyuşmazlıkları: bitsandbytes / CUDA / PyTorch

**Belirti:** Kurulum veya eğitim başlangıcında sürüm kaynaklı klasik hatalar: `ImportError: libbitsandbytes_cuda...so: cannot open shared object file`, `CUDA error: no kernel image is available for execution on the device` ya da PyTorch'un beklediği CUDA sürümü ile sistem sürücüsünün uyuşmaması.

**Neden:** Bu üç bileşen bir zincirdir: GPU sürücüsü → PyTorch'un derlendiği CUDA sürümü → bitsandbytes'in derlendiği CUDA sürümü. Zincirdeki bir halka uyuşmazsa paket yüklenmez (import hatası), derlenmiş çekirdek (kernel) bulunamaz ya da eğitim sessizce başlamadan düşer.

**Tanı adımları (sırayla):**

```bash title="surum_tanisi.sh"
# 1) Sürücü sürümü ve desteklenen en yüksek CUDA sürümü ("CUDA Version" sürücünün üst sınırıdır)
nvidia-smi

# 2) PyTorch'un gördüğü CUDA sürümü ve GPU erişimi
python -c "import torch; print(torch.version.cuda, torch.cuda.is_available())"

# 3) bitsandbytes sürümü ve kurulum biçimi
pip show bitsandbytes
```

`torch.version.cuda` değeri `None` dönüyorsa CPU tekerleği (wheel) kurulmuş demektir; `torch.cuda.is_available()` `False` dönüyorsa GPU, sürücü düzeyinde bile görünmüyor.

**Çözüm yönleri:**

- **Uyumlu tekerlek seçin:** PyTorch'u resmî kurulum seçicisinden, işletim sistemi ve CUDA sürümünüze uygun komutla kurun; bitsandbytes'in CUDA ana sürümüyle eşleşen sürümünü tercih edin. Sürüm numaraları hızla değiştiği için burada sabit numara vermiyoruz — güncel eşleşme için seçici ve bitsandbytes sürüm notları esastır.
- **Temiz sanal ortam:** Yarım kalan kurulumlar bu hataların en sık nedenidir; venv'i silip tek seferde doğru sırayla (önce PyTorch, sonra bitsandbytes) kurun.
- **Windows'ta WSL2:** bitsandbytes/CUDA tekerlekleri ağırlıklı olarak Linux varsayar; Windows native kurulumda sorun sürerse WSL2 en pürüzsüz yoldur.

:::tip
Kurulum komutunu elle yazmayın: PyTorch'un "Get Started Locally" seçicisi, işletim sistemi + CUDA sürümünüze göre doğru `pip install` satırını üretir; bağlantı sayfa sonundaki kaynaklarda.
:::

İlgili sayfa: [Yerel Kurulum](/donanim/yerel-kurulum/).

## Hâlâ Çözülmedi mi?

Hata mesajının **tamamını** kopyalayıp arayın: çoğu hata mesajı, sizden önce yüzlerce kişinin karşılaştığı bir mesajdır. Bunun için:

- Projenin/kütüphanenin GitHub issue'ları ve tartışmaları (ör. TRL, Unsloth, transformers depoları),
- Hugging Face forumları ve Discord toplulukları,
- Türkçe topluluklar ve genel faydalı bağlantılar için [Faydalı Linkler](/kaynaklar/faydali-linkler/) sayfasına bakın.

Bir sorunu paylaşırken şunları eklemek, yanıt alma şansınızı katlar: tam hata metni, kullandığınız araç ve sürümleri, GPU modeli ve VRAM, çalıştırdığınız komut/betik, ve denediğiniz çözümler.

## Kaynaklar ve İleri Okuma

- [PyTorch CUDA bellek yönetimi](https://docs.pytorch.org/docs/stable/notes/cuda.html) — tahsis/önbellek davranışının ve `max_memory_allocated` gibi bellek API'lerinin resmî açıklaması.
- [PyTorch: Yerel Kurulum seçicisi](https://pytorch.org/get-started/locally/) — işletim sistemi ve CUDA sürümünüze uygun kurulum komutunu üretir.
- [bitsandbytes (GitHub)](https://github.com/bitsandbytes-foundation/bitsandbytes) — CUDA tekerlekleri, kurulum belgeleri ve sürüm notları.
- [Unsloth: Sorun Giderme ve SSS](https://unsloth.ai/docs/basics/troubleshooting-and-faqs) — GGUF/Ollama ve sohbet şablonu kaynaklı bozuk çıktıların en sık nedenleri.
- [Transformers: Sorun Giderme](https://huggingface.co/docs/transformers/en/troubleshooting) — CUDA out of memory dahil, kütüphanenin resmî hata rehberi.
