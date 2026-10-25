---
title: "Adım Adım: Kendi Görsel LoRA'nı Eğit"
description: 15-20 görselle kendi karakter veya üslup LoRA'nı veri toplamadan test etmeye kadar adım adım nasıl eğiteceğini anlatıyoruz.
dogrulama: 2026-10-15
---

Bu sayfada gerçek bir senaryoyu baştan sona işleyeceğiz: elimizde bir avuç görsel var ve sonunda bunları üretebilen, MB boyutunda tek bir dosyamız olacak. Örnek senaryomuz: **"kendi çizim üslubumu öğretsem?"** ya da **"kedimi istediğim sahnede üretebilsem?"** İkisinin de yolu aynı.

Ön koşullar: Difüzyonun ne yaptığını kabaca bilmek ([Difüzyon Temelleri](/gorsel/diffusion-temelleri/)) ve bir bilgisayar ya da bulut hesabı. 6-8 GB VRAM'li bir Windows makinesi SD 1.5/SDXL LoRA için yeterlidir; hiç GPU yoksa ücretsiz bulut var.

## Adım 1 — Veri toplama

İyi bir LoRA'nın sırrı modelden önce veridedir. Kurallar:

- **Sayı:** 10-30 görsel yeterli. 15-20, başlangıç için tatlı noktadır.
- **Çözünürlük:** Kısa kenar en az 512 piksel (SDXL eğitecekseniz 1024 hedefleyin). Yüksek çözünürlüklü, net görseller seçin; eğitim betikleri gerekirse kırpar veya küçültür.
- **Kalite:** Bulanık, hareket bulanıklığı olan, filigranlı, aşırı sıkıştırılmış görseller kullanmayın. Model kötü örnekten de öğrenir.
- **Çeşitlilik:** Açı, ışık, arka plan ve poz çeşitlensin. Hep aynı kanepeyi öğretirseniz model kanepeden ayrılmaz.
- **Tutarlılık:** Çeşitliliğe rağmen öğretmek istediğiniz şey (yüz, üslup, nesne) her görselde net görünmeli. Yarısında güneş gözlüğü olan bir karakterin yüzünü öğrenmek zorlaşır.
- **Tekrar yok:** Yan yana çekilmiş neredeyse aynı 20 kare, aslında 1 görseldir. Benzer kareleri eleyin.

:::danger[Telif hakkı ve etik]
LoRA'nızı yalnızca kendi çektiğiniz/çizdiğiniz, lisansı uygun veya açık rızası olan görsellerle eğitin. Yaşayan bir sanatçının üslubunu taklit edip eserlerini çoğaltmak, "sadece eğitim" olsa bile hukuki ve etik sorunlar doğurur. Karakter eğitiyorsanız, kişinin kendi görselini LoRA'ya dönüştürmek rızasına bağlıdır.
:::

| | Karakter LoRA'sı | Üslup LoRA'sı |
|---|---|---|
| Kaç görsel? | 15-30, öznenin her açıdan | 15-30, üslubun farklı konularda |
| Kritik olan | Yüz/özne netliği ve tutarlılık | Fırça/doku/renk paletinin tutarlılığı |
| Arka plan | Çeşitli olmalı (ezberlemesin) | Konu çeşitli olmalı (üslubu öğrensin) |

## Adım 2 — Etiketleme (caption)

Etiketleme (captioning), her görsele onu tarif eden bir metin yazmaktır. Mantık şu: model, görseldeki **etiketin kapsamadığı her şeyi** "taban modele ait genel bilgi" sayar; etiketlediğiniz şeyi ise öğrenmesi gereken özel bilgi olarak ayırır.

- **Üslup öğretirken:** Etiketleme çok önemli. "Suluboya, pastel, sisli dağ manzarası" gibi açıklamalar üslubu ve içeriği ayrıştırır; böylece üslubu her sahneye uygulayabilirsiniz.
- **Karakter öğretirken:** İki yaklaşım var. (1) **Sadece tetikleyici kelime:** her etiketin başına nadir bir kelime koyun, gerisini boş bırakın. Model karakteri o kelimeyle birlikte ezberler; basit ama esnekliği düşük. (2) **Tetikleyici + kısa açıklama:** "ohwx kedim, koltukta uyuyor, gündüz" gibi. Daha esnek sonuç verir, biraz daha fazla emek ister.

:::note[Türkçe mi İngilizce mi?]
Popüler SD modelleri (SD 1.5, SDXL ve CLIP tabanlı diğerleri) ağırlıklı olarak **İngilizce** metinle eğitilmiştir. Etiketleri İngilizce yazmak ve üretimde İngilizce prompt kullanmak, modelin metni anlama isabetini belirgin şekilde artırır. Türkçe etiketlerle de eğitim çalışır, fakat sonuçlar genelde daha düzensiz olur.
:::

Üç örnek etiket (İngilizce, tetikleyici dâhil):

```text title="örnek captionlar"
ohwx kedim, parkta oturuyor, gün batımı ışığı, fotoğraf
ohwx kedim, mutfak tezgahında, sabah, doğal ışık, yakın çekim
sksstyle, suluboya manzara, sisli dağlar ve göl, pastel renkler
```

Etiketler, görselle **aynı isimli** `.txt` dosyasına yazılır; kohya şu klasör düzenini bekler:

```text title="klasör yapısı"
veri_klasoru/
├── kedim_01.jpg
├── kedim_01.txt     →  "ohwx kedim, koltukta uyuyor, gündüz"
├── kedim_02.jpg
├── kedim_02.txt     →  "ohwx kedim, parkta, gün batımı"
└── ...
```

Birden fazla konsept klasörü kullanmak isterseniz kohya'da alt klasör adının başındaki sayı "tekrar" (repeats) anlamına gelir; örneğin `5_karakterim/` klasörü her turda 5 kez okunur. Tek set ile başlıyorsanız bu ayrıntıyı şimdilik düşünmeniz gerekmez.

**Tetikleyici kelime (trigger word)** tekniği: "ohwx", "sks" gibi modelin eğitim verisinde nadir görülen kısa dizeler seçilir. Bu kelime sizin etiketlerinizde karaktere/üsluba bağlanır; üretimde onu yazınca öğrettiğiniz şey devreye girer. Gerçek kelimeler ("kedi" gibi) seçerseniz modelin kafası karışır — nadir ve anlamsız bir dize en güvenlisidir.

## Adım 3 — Araç seçimi

| Seçenek | Kurulum | Artıları | Eksileri | Ne zaman? |
|---|---|---|---|---|
| **kohya_ss (yerel)** | [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) — `git clone` + `setup.bat` | Ücretsiz, sınırsız kullanım, veriniz bilgisayarınızda kalır | Kurulum ilk seferde uğraştırır; VRAM sınırınız kadar | Düzenli eğitim yapacaksanız |
| **Colab** | Hazır kohya notebook'u | T4 GPU, kurulum yok, ücretsiz katman | Oturum süreleri kısıtlı, veriyi yüklemek gerekir | Öğrenme ve tek seferlik denemeler |
| **Kaggle** | Notebook ortamı | Haftalık ücretsiz GPU kotası, veri seti barındırma | Arayüz deneyimi Colab'den farklı | Colab limitine takılınca |

Basit karar: ilk LoRA'nızı **Colab'de** eğitin (riski sıfır, öğrenmesi hızlı); düzenli üretime geçince **yerel kohya_ss**'ye taşıyın. Windows yerel kurulum adımları için: [Yerel Kurulum](/donanim/yerel-kurulum/); GPU yoksa: [Bulut Seçenekleri](/donanim/bulut-secenekleri/).

## Adım 4 — Eğitim parametreleri

kohya_ss arayüzünde onlarca alan görürsünüz; ilk eğitim için önemli olanlar şunlardır (SD 1.5/SDXL için tipik değerlerle):

| Alan | Tipik değer | Ne yapar? |
|---|---|---|
| `max_train_steps` | 1500-3000 | Toplam eğitim adımı. Kaba kılavuz: görsel başına ~100 adım. |
| `learning_rate` | ~1e-4 | Öğrenme hızı. Çok yüksek = bozuk sonuç, çok düşük = boşa geçen adım. |
| `network_dim` (rank) | 16-32 | LoRA'nın kapasitesi. Basit karakter için 16, karmaşık üslup için 32. |
| `network_alpha` | dim/2 (8-16) | Eğitimin "ölçeği"; genelde dim'in yarısı iyi bir başlangıçtır. |
| `train_batch_size` | 1-2 | Aynı anda işlenen görsel sayısı. VRAM darsa 1'de kalın. |
| `mixed_precision` | fp16 (SD 1.5), bf16 (SDXL/Flux) | Bellek tasarrufu + hız; kalite kaybı yok denecek kadar az. |
| `save_every_n_steps` | 250-500 | Ara kayıtlar. Son kararı tek bir dosyaya bağlamayın; ara dosyaları test edin. |
| Çözünürlük | 512 (SD 1.5), 1024 (SDXL) | Eğitim çözünürlüğü; bucket özelliği farklı boy oranlarını yönetir. |

kohya arayüzü bu alanları altta bir komuta çevirir. Arka planda ne çalıştığını görmek isteyenler için eşdeğeri (sd-scripts):

```bash title="lora_egitimi.sh (sd-scripts karşılığı, özet)"
accelerate launch --num_cpu_threads_per_process 4 train_network.py \
  --pretrained_model_name_or_path=model.safetensors \
  --train_data_dir=veri \
  --output_dir=cikti \
  --network_module=networks.lora \
  --network_dim=16 --network_alpha=8 \
  --learning_rate=1e-4 \
  --train_batch_size=1 \
  --max_train_steps=2000 \
  --save_every_n_steps=500 \
  --mixed_precision=fp16 \
  --resolution=512 \
  --caption_extension=.txt
```

:::caution[Aşırı eğitim (overfit) nasıl anlaşılır?]
Her 250-500 adımda kaydedilen ara dosyalarla aynı test prompt'unu üretin ve üç sinyale bakın: (1) Sonuç eğitim görsellerinin neredeyse kopyası olmaya başladıysa, (2) prompt'a ne yazarsanız yazın arka plan değişmiyorsa, (3) tetikleyici kelime olmadan da her üretiminizde karakter/üslup zorla beliriyorsa — model ezberlemeye geçmiştir. Çözüm: daha erken bir adımdaki ara dosyayı kullanmak, adım sayısını ya da learning rate'i düşürmek. Genelde "az eğitilmiş" bir LoRA, aşırı eğilmiş olandan kurtarılması kolaydır.
:::

## Adım 5 — Test ve kullanım

Eğitim bitince elinizde `*.safetensors` uzantılı, tipik olarak onlarca MB (SD 1.5) ile yüzlerce MB (SDXL, Flux) arasında tek bir dosya olur. Bu dosya taban modelin **üzerine** uygulanan bir yamadır; tek başına çalışmaz.

**AUTOMATIC1111 WebUI'de:**

1. Dosyayı `models/Lora/` klasörüne kopyalayın.
2. Prompt'a şu sözdizimiyle ekleyin: `<lora:dosya_adi:0.8>`

**ComfyUI'de:** `LoraLoader` düğümünü model ile örnekleyici (sampler) arasına ekleyin, dosyayı ve gücü seçin.

```text title="örnek test prompt'u"
<lora:kedim_v1:0.8> ohwx kedim, sahil kenarında yürüyor, altın saat, fotoğraf
```

Test ederken şunları deneyin:

- **Güç (weight) taraması:** 0.6 / 0.8 / 1.0 değerlerini karşılaştırın. 0.6-1.0 aralığı çoğu LoRA için tatlı noktadır; 1.0'ın üzeri genelde gereksizdir ve görüntüyü "yapış yapış" yapar.
- **Ezber testi:** Eğitimde olmayan sahneler isteyin (farklı şehir, farklı mevsim). Karakter/üslup hâlâ geliyorsa model genellemiş demektir.
- **Tetikleyicisiz test:** Tetikleyici kelime olmadan da hafif bir etki görmek normaldir; tamamen tetikleyicisiz de geliyorsa aşırı eğitilmiş olabilir.

## LLM LoRA'sı ile karşılaştırma

:::tip[Aynı fikir, farklı malzeme]
[LLM tarafında LoRA/QLoRA](/llm/lora-qlora/) ile görsel LoRA tamamen aynı mantıktır: taban modelin ağırlıkları **donar**, ona eklenen küçük düşük-rank matrisler (A ve B) eğitilir. Farklar sadece veride ve araçlarda.
:::

| | LLM LoRA / QLoRA | Görsel LoRA |
|---|---|---|
| Veri tipi | Metin (talimat + yanıt çiftleri) | Görsel + etiket (caption) |
| Tipik veri miktarı | Yüzler-binlerce örnek | 10-30 görsel |
| Araçlar | peft / trl / Unsloth | kohya_ss (sd-scripts), diffusers |
| Tipik süre | Saatler (7B model, tek GPU) | Dakikalar-saatler (modele göre) |
| Çıktı | Adaptör dosyası (onlarca-yüzlerce MB) | `safetensors` LoRA (onlarca-yüzlerce MB) |
| Değerlendirme | Kayıp, benchmark, sohbet çıktısı | Üretilen görselleri gözle inceleme |

## Maliyet ve süre beklentisi

- **Colab ücretsiz T4 + SD 1.5 LoRA:** yaklaşık 30-60 dakika. İlk deneme için ideal.
- **SDXL LoRA:** T4'te belirgin şekilde daha uzun; yerel 12 GB bir kartta birkaç saat.
- **Flux LoRA:** Bulutta (güçlü GPU ile) yaklaşık 1-2 saat; yerelde 16-24 GB VRAM ister. Bu değerler kabaca; veri ve adım sayısına göre ciddi değişir.
- Gizlilik notu: bulutta eğitirken görsellerinizi platforma yüklersiniz; hassas görseller için yerel eğitim veya [bulut seçenekleri](/donanim/bulut-secenekleri/) sayfasındaki kiralık GPU yollarını değerlendirin.

## Kontrol listesi

Eğitime başlamadan önce:

- [ ] 10-30 görsel hazır; hepsi net, konu tutarlı, tekrarlı kareler ayıklandı
- [ ] Her görselin etiketi, aynı isimli `.txt` dosyasında
- [ ] Tetikleyici kelime seçildi ve etiketlerin başına eklendi
- [ ] Taban model dosyası (SD 1.5 / SDXL `safetensors`) indirildi
- [ ] `save_every_n_steps` 250-500 olarak ayarlandı

Eğitimden sonra:

- [ ] Ara checkpoint'ler aynı test prompt'u ve aynı seed ile karşılaştırıldı
- [ ] En iyi checkpoint ezber testini geçti (eğitimde olmayan sahneler istendi)
- [ ] Güç (weight) 0.6-1.0 arasında tarandı
- [ ] Dosya yedeklendi; paylaşılacaksa model kartı yazıldı

## Özet ve devam

- 10-30 tutarlı, kaliteli görsel topla; gerekirse İngilizce etiketle.
- kohya_ss (yerel) veya Colab (bulut) ile eğit; adım sayısı ve learning rate'i kılavuz değerlerle başlat.
- Ara kayıtları test et, overfit'i yakala, en iyi checkpoint'i seç.
- Dosyayı webui/ComfyUI'ye tak, gücü 0.6-1.0 arasında ayarla.

Kavramları tazelemek için: [Difüzyon Modelleri](/gorsel/diffusion-temelleri/). LoRA'nız hazır olduğunda topluluğa açmayı düşünün: [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/).
