---
title: "LoRA Birleştirme: Adaptörü Ana Modele Kaynaştırmak"
description: "Eğittiğiniz LoRA adaptörünü taban modelle tek parça haline getirmenin ne zaman gerekli olduğunu ve adım adım nasıl yapıldığını öğrenin."
dogrulama: 2026-10-15
---

LoRA ile ince ayar bittiğinde elinizde iki ayrı parça olur: devasa **taban model** ve onun üzerine takılan küçük **adaptör**. Bu sayfada "Adaptörü ayrı mı saklayayım, taban modelle birleştirip (merge) tek model mi yapayım?" sorusunu netleştirip birleştirmeyi adım adım uygulayacağız.

:::note
LoRA, adaptör ve QLoRA kavramlarına yeniyseniz önce [LoRA ve QLoRA](/llm/lora-qlora/) sayfasına göz atın. Eğitim akışının tamamını görmek için [Adım Adım Eğitim](/llm/adim-adim-egitim/) rehberi sizi bekliyor.
:::

## Adaptör tek başına çalışamaz

Tipik bir LoRA eğitimi sonunda diskinizdeki manzara şudur:

| Parça | Örnek | Tipik boyut |
|---|---|---|
| Taban model | `Qwen/Qwen3-4B` ağırlıkları | ~8 GB (fp16) |
| Adaptör | `adapter_model.safetensors` + `adapter_config.json` | 50-200 MB |

Adaptör bağımsız bir model değildir; taban modele takılan bir "yama" gibidir. `PeftModel.from_pretrained(taban, adaptor)` ile taban modelin üzerine takılmadan çalışmaz. Bu yüzden adaptörü kullanacak herkes (ve her araç) taban modele de ihtiyaç duyar.

## İki yol: ayrı tutmak ve birleştirmek

| | Adaptörü ayrı tut | Birleştir (merge) |
|---|---|---|
| Disk boyutu | Taban + birkaç yüz MB | Taban boyutunda tek model |
| Çalıştırma | Taban + adaptör birlikte yüklenir | Tek başına, standart model gibi çalışır |
| Çoklu varyant | Tek taban + onlarca adaptör tak-çıkar | Her varyant tam boyutlu ayrı kopya |
| Paylaşım | İki parçayı birlikte göndermek gerekir | Tek klasör, tek depo |
| GGUF'a dönüşüm | Desteklenmez (aşağıya bakın) | Gerekli |

Kısa kural: **deney aşamasında adaptörü ayrı tutun, dağıtım aşamasında birleştirin.**

## Neden birleştirmek gerekir?

En pratik sebep, [nicemleme (quantization)](/kullanim/quantization/) ve GGUF dönüşümüdür. Ollama, LM Studio ve llama.cpp gibi araçlar bir GGUF dosyası bekler; llama.cpp'nin dönüştürme araçları ise girdi olarak standart bir Hugging Face model klasörü alır. Adaptörleri bu araçlara doğrudan veremezsiniz. Pratik akış şöyledir:

**Eğitim → birleştirme (bu sayfa) → GGUF dönüşümü → nicemleme → Ollama'da çalıştırma**

Birleştirmenin diğer faydaları:

- Modeli indiren kişi "önce tabanı indir, sonra adaptörü şu şekilde tak" adımlarıyla uğraşmaz; tek `from_pretrained` çağrısı yeter.
- Adaptör desteklemeyen araçlar ve sunum motorları birleşik modelle sorunsuz çalışır.

:::tip
llama.cpp'de sınırlı düzeyde ayrı LoRA yükleme desteği vardır; ancak Ollama bu akışı desteklemez ve araç zinciri zahmetlidir. Başlangıç seviyesi için "önce birleştir, sonra nicemle" neredeyse her zaman doğru tercihtir.
:::

## Birleştirme: adım adım

:::danger Merge'ü asla 4-bit model üzerinde yapmayın!
QLoRA ile eğitim sırasında taban model 4-bit yüklenmişti; ama birleştirme her zaman **fp16/bf16 hassasiyetinde temiz bir taban model** üzerinde yapılır. 4-bit modeli birleştirirseniz nicemleme hatası ağırlıklara kalıcı olarak işler ve kalite belirgin şekilde düşer. Yani: eğitim 4-bit olabilir, birleştirme asla.
:::

Önce gerekli kütüphaneler:

```bash title="kurulum.sh"
pip install -U torch transformers peft accelerate
```

Sonra birleştirme betiği:

```python title="birlestir.py"
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

TABAN   = "Qwen/Qwen3-4B"                    # eğitimde kullandığınız taban model
ADAPTOR = "kullanici/qwen3-4b-turkce-lora"   # adaptör deposu (HF'te ya da yerel klasör)
CIKTI   = "birlestirilmis-model"             # sonucun kaydedileceği klasör

# 1) Taban modeli fp16 olarak yükle. ASLA 4-bit/8-bit yüklemeyin!
taban = AutoModelForCausalLM.from_pretrained(
    TABAN,
    torch_dtype=torch.float16,
    device_map="cpu",       # birleştirme için CPU yeterli; GPU varsa "auto" da olur
)

# 2) Adaptörü taban modelin üzerine tak
model = PeftModel.from_pretrained(taban, ADAPTOR)

# 3) Adaptör ağırlıklarını ana modele kaynaştır
model = model.merge_and_unload()

# 4) Tek parça modeli ve tokenizer'ı kaydet
model.save_pretrained(CIKTI)

# Tokenizer'ı adaptör klasöründen alıyoruz; eğitim sırasında oraya kaydedilmişti.
# (Emin değilseniz TABAN modelinin tokenizer'ını da kullanabilirsiniz.)
tokenizer = AutoTokenizer.from_pretrained(ADAPTOR)
tokenizer.save_pretrained(CIKTI)

print("Birleştirme tamamlandı:", CIKTI)
```

`merge_and_unload()` çağrısı, adaptörün düşük rütbeli (low-rank) matris çarpımını taban ağırlıklara ekler ve PeftModel sarmalayıcısını kaldırır. Sonuç sıradan bir Hugging Face modelidir: artık `AutoModelForCausalLM.from_pretrained("birlestirilmis-model")` yeterlidir. İki ayrıntı PEFT belgelerinden not edilmeli: `merge_and_unload()` yerinde (in-place) çalışmaz, dönen modeli bir değişkene atamak şarttır (yukarıdaki betik bunu yapıyor); ve birleştirme geri alınamaz, farklı adaptörler denemek için taban modeli yeniden yüklemeniz gerekir. Çıktı formatını açık seçmek isterseniz `model.save_pretrained(CIKTI, safe_serialization=True)` yazın; safetensors, pickle tabanlı `.bin` yerine önerilen güvenli formatın ta kendisidir.

:::caution Tokenizer ve sohbet şablonu kaybolmasın
Birleşik klasörde yalnızca ağırlıklar değil, **tokenizer dosyaları ve sohbet şablonu (chat template)** da bulunmalıdır. Bunlar kaydedilmezse model yüklenir ama `apply_chat_template` hata verir; sohbet yeteneği "buharlaşır". Şablonu eğitimde değiştirmediyseniz taban tokenizer'ı yeterlidir; değiştirdiyseniz (özel token eklediyseniz) mutlaka adaptör klasöründeki tokenizer'ı kaydedin.
:::

### Unsloth ile tek satırda birleştirme

Eğitimi Unsloth ile yaptıysanız yukarıdaki akışı elle yazmanıza gerek yoktur; Unsloth aynı işi tek çağrıyla yapar:

```python title="unsloth_birlestir.py"
# Adaptörü taban modele merge edip tek parça fp16 model olarak kaydeder
model.save_pretrained_merged("cikti", tokenizer, save_method = "merged_16bit")
```

`save_method` parametresinin diğer seçenekleri için Unsloth belgelerine bakın. Aynı araç GGUF dışa aktarımını da üstlenir (`save_pretrained_gguf`); o akışın tamamı [Nicemleme](/kullanim/quantization/) sayfasında anlatılıyor.

### QLoRA sonrası birleştirme

QLoRA ile eğittiyseniz iki noktaya dikkat edin:

1. **Eğitim 4-bit, birleştirme fp16:** 4-bit yalnızca eğitim sırasında VRAM tasarrufu içindi; birleştirmeyi temiz fp16 taban model üzerinde yaparsınız.
2. **Disk beklentisi:** Birleşik model, taban modelin fp16 boyutundadır (ör. 4B için ~8 GB). Eğitim bittiğinde diskte beliren 100 MB'lık adaptör dosyasıyla karıştırmayın; asıl model bu adımda oluşur.

### Doğrulama: gerçekten birleşti mi?

```python title="dogrula.py"
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("birlestirilmis-model", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("birlestirilmis-model")

mesajlar = [{"role": "user", "content": "Merhaba! Kendini bir cümleyle tanıt."}]
girdi = tokenizer.apply_chat_template(
    mesajlar, add_generation_prompt=True, return_tensors="pt"
).to(model.device)

cikti = model.generate(girdi, max_new_tokens=100)
print(tokenizer.decode(cikti[0][girdi.shape[1]:], skip_special_tokens=True))
```

Eğitim verinizin üslubuna uygun, düzgün cevaplar alıyorsanız birleştirme başarılıdır. Sohbet şablonunun çalıştığını görmek için özellikle "Merhaba" gibi basit bir sohbet mesajıyla test edin.

## Birden fazla adaptörü tekilleştirme: add_weighted_adapter

Elinizde aynı taban üzerine eğitilmiş birden çok adaptör varsa (örneğin biri Türkçe sohbet, biri kod), PEFT bunları tek yeni adaptörde harmanlayabilir; sonra bu tek adaptörü yukarıdaki gibi kalıcı olarak merge edersiniz:

```python title="adaptör_birlestir.py"
import torch
from transformers import AutoModelForCausalLM
from peft import PeftModel

taban = AutoModelForCausalLM.from_pretrained(
    TABAN,  # yukarıdaki betiktekiyle aynı taban model
    torch_dtype=torch.float16, device_map="cpu"
)

# İki adaptörü farklı adlarla yükle
model = PeftModel.from_pretrained(taban, "kullanici/turkce-lora", adapter_name="turkce")
model.load_adapter("kullanici/kod-lora", adapter_name="kod")

# Ağırlıklı harmanlama: yeni tek adaptör
model.add_weighted_adapter(
    adapters=["turkce", "kod"],   # harmanlanacak adaptörler
    weights=[0.7, 0.3],           # ağırlıklar (negatif de olabilir)
    adapter_name="birlesik",
    combination_type="linear",    # harmanlama stratejisi
)
model.set_adapter("birlesik")

# Artık tek adaptör var: kalıcı birleştirme
model = model.merge_and_unload()
model.save_pretrained("birlestirilmis-model", safe_serialization=True)
```

`combination_type` harmanlamanın matematiğini seçer. `linear` ağırlıklı basit toplamdır; `svd` birleşik sonucu yeniden düşük rütbeli ayrıştırır (fp16/bf16 ile yüklenmiş modellerde desteklenmez, fp32 gerekir); `ties`, `dare_ties`, `dare_linear` ve `magnitude_prune` çakışan güncellemeleri budayan yöntemlerdir; `cat` ise adaptörleri bitiştirip rütbeyi büyütür (bellek kullanımı artar). Hangi stratejinin daha iyi olduğu modele ve göreve göre değişir; sonucu kendi değerlendirme setinizde karşılaştırmadan yayına almayın: [Benchmarklar ve Değerlendirme](/degerlendirme/benchmarklar/).

## mergekit'in yeri: tam model birleştirme, LoRA merge'i değildir

Toplulukta "model merge" denince sık duyulan [mergekit](https://github.com/arcee-ai/mergekit), sizin LoRA adaptörünüzü kaynaştıran araç değildir; karışıklık sık yaşanır. mergekit, **iki ya da daha fazla tam eğitilmiş modeli** (örneğin aynı tabanın farklı ince ayarları) tek yeni modelde birleştiren araçtır: birleşim stratejisi YAML dosyasıyla tanımlanır ve SLERP (iki modelin küresel enterpolasyonu), TIES ve DARE (çakışan görev güncellemelerini budaarak birleştirme), linear ve Model Stock gibi yöntemler sunar.

mergekit'in işinize yarayabilecek ikinci bir yüzü vardır: `mergekit-extract-lora` aracı, ince ayarlı bir model ile tabanı arasındaki farkı alıp buna PEFT uyumlu bir LoRA adaptörü çıkarır. "Elimdeki büyük modelin farkını küçük bir adaptöre indirgemek istiyorum" senaryosunda pratik bir keşif aracıdır.

:::note
Özet: kendi QLoRA/LoRA adaptörünüzü dağıtıma hazırlamak için mergekit'e gerek yoktur; PEFT'in `merge_and_unload()` akışı (ya da Unsloth) yeterlidir. mergekit ayrı bir problem olan model-model birleşimi içindir.
:::

## Sık yapılan hatalar

| Hata | Belirti | Çözüm |
|---|---|---|
| 4-bit yüklenmiş modeli merge etmek | Kalite düşer, cevaplar tutarsızlaşır | Temiz tabanı fp16 yükleyip yeniden merge edin |
| Tokenizer'ı kaydetmeyi unutmak | `apply_chat_template` hatası, garip çıktılar | `tokenizer.save_pretrained(CIKTI)` ekleyin |
| Sohbet şablonunun kaybolması | Model "sohbet etmeyi bilmiyor" gibi davranır | Tokenizer'ı adaptörden kaydedin; şablon dosyalarını kontrol edin |
| Aynı adaptörü iki kez merge etmek | Adaptörün etkisi iki katına çıkar, model bozulur | Her merge'e her zaman **temiz** (adaptörsüz) taban modelle başlayın |
| Yanlış taban modelle merge etmek | Boyut uyuşmazlığı ya da anlamsız çıktılar | Adaptördeki `base_model` alanını kontrol edin |

## Ne zaman birleştirmemelisiniz?

- **Hâlâ deney yapıyorsanız:** Adaptörler 50-200 MB'tır; onlarca denemenin adaptörünü saklamak, onlarca tam modelden kat kat kolaydır. Birleştirmeyi işin en sonuna bırakın.
- **Aynı tabanla farklı yetenekler kullanacaksanız:** "Türkçe", "hukuk", "kod" gibi adaptörleri ayrı tutarsanız taban model diskte bir kez durur ve aralarında geçiş yaparsınız.
- **Sunucuda dinamik adaptör değiştirecekseniz:** [vLLM](/kullanim/sunma-api/) gibi motorlar `--enable-lora` ve `--lora-modules` bayraklarıyla adaptörü taban modele merge etmeden doğrudan sunabilir; çalışma anında yeni adaptör de yüklenebilir. Bu senaryoda birleştirmeye gerek yoktur.

## Kaynaklar ve İleri Okuma

- [PEFT — LoRA geliştirici rehberi](https://huggingface.co/docs/peft/developer_guides/lora): `merge_and_unload()` akışı ile `add_weighted_adapter`/`combination_type` seçeneklerinin resmi dokümanı.
- [mergekit](https://github.com/arcee-ai/mergekit): SLERP, TIES, DARE gibi tam model birleştirme yöntemleri ile `mergekit-extract-lora` aracının deposu.
- [Unsloth — Saving to GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf): `save_pretrained_merged` ve GGUF dışa aktarımının resmi belgesi.
- [vLLM — LoRA desteği](https://docs.vllm.ai/en/latest/features/lora.html): Adaptörleri merge etmeden `--enable-lora` ile sunmanın dokümanı.
- [safetensors](https://huggingface.co/docs/safetensors/index): Birleşik modeli paylaşırken kullanılan güvenli tensor formatının dokümanı.

## Sonraki adımlar

- Birleşik modeli küçültmek için: [Nicemleme (Quantization)](/kullanim/quantization/)
- Yerel olarak çalıştırmak için: [Ollama Rehberi](/kullanim/ollama/)
- Toplulukla paylaşmak için: [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/)
- Baştan sona akışı görmek için: [Adım Adım Eğitim](/llm/adim-adim-egitim/)
