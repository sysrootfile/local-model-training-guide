---
title: "Hugging Face'te Paylaşım: Modelini Dünyaya Aç"
description: "Eğittiğiniz modeli Hugging Face Hub'a yükleme, GGUF dosyalarını düzenleme, etkili bir model kartı yazma ve lisans seçimi rehberi."
dogrulama: 2026-10-17
---

Modeli eğittiniz, test ettiniz, beğendiniz. Sıradaki adım onu paylaşmak. Hugging Face Hub, modelinizi tek komutla dünyaya açabileceğiniz ücretsiz bir platformdur; bu sayfada yükleme, GGUF dosyaları, model kartı ve lisans konularını uçtan uca ele alıyoruz.

## Neden paylaşmalısınız?

- **Gerçek geri bildirim:** Modeli indirenler sizin göremediğiniz hataları ve kullanım senaryolarını bildirir; modeliniz topluluk sayesinde iyileşir.
- **Türkçe ekosisteme katkı:** Açık Türkçe model ve veri sayısı, İngilizce'ye kıyasla hâlâ çok az. Sizin 500 örnekle eğittiğiniz mütevazı bir model, benzer bir iş yapan birinin günlerini kurtarabilir.
- **Portföy değeri:** "Şu depoda benim eğittiğim, indirilip denenebilen bir model var" demek, en güçlü özgeçmiş maddelerinden biridir.
- **Kolaylık:** Kamuya açık modeller ve veri setleri için HF Hub ücretsizdir; indirme, sürümleme ve demo (Spaces) aynı çatı altındadır.

## Hazırlık: hesap, jeton ve giriş

1. [huggingface.co](https://huggingface.co) üzerinden ücretsiz hesap açın.
2. **Erişim jetonu (token)** oluşturun: `Settings → Access Tokens → Create new token` ve **Write** yetkisini seçin. Jeton yalnızca bir kez gösterilir; kopyalayıp güvenli bir yere alın. (Bkz. `huggingface.co/settings/tokens`)
3. Terminalden giriş yapın:

```bash title="hf_giris.sh"
pip install -U huggingface_hub

# Yeni nesil komut satırı aracı (2026 itibarıyla önerilen)
hf auth login

# Eski sürümlerde yaygın olan eşdeğer komut:
# huggingface-cli login
```

Sorulan yere jetonunuzu yapıştırın. "Add token as git credential?" sorusunda, `git` ile de çalışacaksanız Evet seçebilirsiniz.

Komut setinin yeni adı `hf`'tir; `huggingface-cli` kullanımdan kaldırılmış (deprecated) eski addır ve yerini `hf`'e bırakmıştır. İndirme tarafının karşılığı da `hf download`'tır: `hf download kullanici/model` tüm repoyu, `hf download kullanici/model config.json` tek dosyayı indirir.

## Modeli yükleme

### Python ile: `push_to_hub`

En çok kullanılan yöntem, elinizdeki klasörü doğrudan repoya göndermektir:

```python title="yukle.py"
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_DIZINI = "birlestirilmis-model"           # yerel klasörünüz
REPO_ADI = "kullanici/qwen3-4b-turkce"          # kendi HF kullanıcı adınızla değiştirin

model = AutoModelForCausalLM.from_pretrained(MODEL_DIZINI)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIZINI)

model.push_to_hub(REPO_ADI)       # ağırlıkları (gerekiyorsa parçalara bölerek) yükler
tokenizer.push_to_hub(REPO_ADI)   # tokenizer dosyaları + sohbet şablonu
```

Notlar:

- Repo yoksa ilk çağrıda otomatik oluşturulur.
- Klasörde bir `README.md` varsa o da yüklenir; bu dosya model kartınız olur (aşağıda anlatıyoruz).
- Büyük yükleme kesilirse komutu yeniden çalıştırmak güvenlidir; eksik dosyalar tamamlanır.

### Komut satırı ile: `hf upload`

```bash title="hf_yukle.sh"
# Klasördeki her şeyi repoya yükle
hf upload kullanici/qwen3-4b-turkce ./birlestirilmis-model .

# Eski sürümlerde yaygın olan eşdeğer komut:
# huggingface-cli upload kullanici/qwen3-4b-turkce ./birlestirilmis-model .
```

## GGUF dosyalarını yükleme pratiği

Modelinizin GGUF sürümünü de paylaşmak isterseniz (ki indirilme sayısını artırır) iki yerleşik yöntem vardır:

1. **Aynı repo içinde `gguf/` klasörü:** Model ağırlıkları reponun kökünde, GGUF dosyaları `gguf/` altında durur. Dosya adları seviyeyi içermelidir: `qwen3-4b-turkce-Q4_K_M.gguf`, `qwen3-4b-turkce-Q8_0.gguf` gibi. Unsloth'un `push_to_hub_gguf` çıktısı da bu düzeni kullanır.
2. **Ayrı GGUF deposu:** `kullanici/qwen3-4b-turkce-GGUF` gibi "-GGUF" son ekli ikinci bir repo açmak topluluk standardıdır; LM Studio gibi araçlar GGUF dosyalarını bu son ekli depolarda arar.

```bash title="gguf_yukle.sh"
# Aynı repo içindeki gguf/ klasörüne yükleme
hf upload kullanici/qwen3-4b-turkce ./model_gguf gguf
```

:::note
GGUF dosyaları büyük dosya depolamasından geçer; `hf upload` bunu sizin için otomatik halleder. Hub'ın arka ucu 2025'ten itibaren Git LFS'ten Xet'e taşındı (aşağıda); eski reposerlerde ve araç arayüzlerinde hâlâ "LFS" ibaresini görebilirsiniz.
:::

## Xet: Hub'ın yeni depolama arka ucu

Hugging Face, 2025 boyunca Hub'ın büyük dosya depolamasını Git LFS'ten Xet adlı chunk tabanlı arka uca taşıdı; geçiş duyuruları Mart ve Temmuz 2025'te yayımlandı. Sizin için fark iki pratik sonuç doğurur:

- **Chunk tekilleştirme (deduplication):** Dosyalar parçalara (chunk) bölünür ve aynı parçalar yalnızca bir kez saklanır. Modelinize yeni bir sürüm yüklediğinizde yalnızca değişen parçalar gider; daha önce indirilmiş parçaları içeren indirmeler de hızlanır. Tekrarlı denemelerde (v2, v3...) bu fark hissedilir.
- **İstemci tarafı:** `huggingface_hub`'un 0.32.0 ve sonrası sürümleri `hf_xet` paketini varsayılan olarak kurar; eski istemciler ise LFS köprüsü üzerinden çalışmaya devam eder. Yapmanız gereken tek şey `huggingface_hub`'ı güncel tutmaktır.

## safetensors: standartlaşan ağırlık formatı

Ağırlıkları `.bin` (pickle) yerine **safetensors** formatında paylaşmak 2026 itibarıyla standarttır. İki gerekçesi vardır:

- **Güvenlik:** Pickle dosyaları yüklenirken keyfi Python kodu çalıştırabilir; Hub da pickle dosyalarını bu yüzden riskli sayar ve tarar. safetensors ise keyfi kod çalıştırmaya imkan veren bir yapı taşımaz.
- **Hız:** safetensors tensor'ları kopyasız (zero-copy) yükler; model açılışları pickle tabanlı dosyalardan hızlıdır.

PEFT örneklerinde gördüğünüz `save_pretrained(..., safe_serialization=True)` çağrısı safetensors çıktısını açıkça seçer. Ayrıca model kartındaki `library_name: transformers` ve `pipeline_tag` alanlarını doldurun: Hub bu alanlarla model sayfasında doğru kullanım parçacığını ve inference seçeneklerini sunar. Önemli ayrıntı: Ağustos 2024'ten sonra oluşturulan reposerlerde Hub kütüphaneyi artık otomatik varsaymıyor; `library_name`'i açıkça yazmak gerekiyor.

## Repo gizliliği: önce private, sonra public

Paylaşım tek yönlü bir kapı olmak zorunda değil; önerilen akış önce gizli yayınlamaktır:

1. Repoyu gizli oluşturun: `create_repo("kullanici/model-adi", visibility="private")`. Güncel `huggingface_hub` dokümanı `visibility` parametresini kullanır; eski eğitimlerde gördüğünüz `private=True` aynı işi yapan eski yazımdır. (`push_to_hub` repo yoksa herkese açık oluşturur; gizli test istiyorsanız repoyu önceden açın.)
2. Modeli kendi hesabınızdan indirip dışarıdan bir kullanıcı gibi test edin; kartın düzgün göründüğünü, dosyaların eksiksiz yüklendiğini kontrol edin.
3. Sorun yoksa repoyu herkese açın: Hub arayüzünde deponun **Settings** sayfasındaki görünürlük seçeneği ya da programatik olarak `update_repo_settings(repo_id=..., private=False)`.

:::tip
"İndirmeden önce bana iletişim bilgilerini paylaşsınlar" istiyorsanız Hub'ın **kapılı (gated) repo** özelliği tam buna yarar: erişim isteyen kullanıcı adını ve e-postasını sizinle paylaşmak zorunda kalır, siz onaylarsınız.
:::

## Model kartı (README.md) yazmak

Model kartı, modeli indirenlerin ilk gördüğü sayfadır; modelin "kullanım kılavuzu" olmalıdır. Kopyalayıp doldurarak başlayabileceğiniz bir şablon:

````markdown title="README.md"
---
language:
- tr
license: apache-2.0
base_model: Qwen/Qwen3-4B
datasets:
- kullanici/turkce-talimat-verisi
pipeline_tag: text-generation
library_name: transformers
tags:
- turkish
- lora
- qlora
---

# Qwen3-4B Türkçe Talimat Modeli

Bu model, Qwen3-4B'nin Türkçe talimat verisiyle QLoRA kullanılarak
ince ayarlanmış (fine-tune) halidir.

## Eğitim Detayları

- **Yöntem:** LoRA (QLoRA, 4-bit NF4 taban)
- **Donanım:** T4 16 GB
- **Veri:** ~5.000 Türkçe talimat örneği (kaynak ve derleme notu buraya)
- **Hiperparametreler:** r=16, alpha=32, lr=2e-4, 1 epoch, cosine schedule

## Kullanım

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "kullanici/qwen3-4b-turkce"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

mesajlar = [{"role": "user", "content": "Merhaba, kendini tanıt."}]
girdi = tokenizer.apply_chat_template(
    mesajlar, add_generation_prompt=True, return_tensors="pt"
).to(model.device)
cikti = model.generate(girdi, max_new_tokens=256)
print(tokenizer.decode(cikti[0][girdi.shape[1]:], skip_special_tokens=True))
```

## Sınırlamalar

- Dar bir veri setiyle eğitildiği için her konuda güvenilir değildir.
- Halüsinasyon üretebilir; kritik kararlar için doğrulama gerektirir.
- Yalnızca Türkçe için optimize edilmiştir.

## Lisans

Apache-2.0 (taban model lisansına tabidir).
````

İyi bir kartın olmazsa olmazları:

- **Ön bilgi (frontmatter):** `language: tr`, `license`, `base_model`, varsa `datasets`, ayrıca `library_name: transformers` ve `pipeline_tag`. Hub, `base_model` alanından ilişkiyi (finetune, adapter, quantized ya da merge) kendisi çıkarır ve model sayfasında türetme zincirini gösterir; `library_name` ve `pipeline_tag` ise kullanım parçacığını, tarayıcı içi widget'ı ve inference seçeneklerini besler. Değerlendirme sonuçlarınız varsa metin içine tablo olarak da ekleyin.
- **Eğitim detayları:** Yöntem, veri, donanım, hiperparametreler; bir başkası deneyinizi tekrarlayabilmeli.
- **Kullanım örneği:** Çalışan, kopyala-yapıştır kod.
- **Sınırlamalar:** Dürüst olun; kartların en çok atlanan ama en değerli bölümü budur.
- **Lisans:** Aşağıdaki tabloya göre netleştirin.

## Lisanslar: kısa rehber

| Lisans | Özet | Örnek modeller |
|---|---|---|
| **Apache-2.0** | Ticari kullanım dahil en serbest; atıf ve patent koşulları | Qwen3, Mistral Small |
| **MIT** | Neredeyse hiç koşul koymayan, kısa ve net lisans | Phi-4-mini |
| **Llama Community License** | Ticari kullanım serbest ama koşullu: 700 milyon+ aylık aktif kullanıcıda ayrı anlaşma; türev adında "Llama" geçmesi ve "Built with Llama" ibaresi | Llama 3.2, Llama 4 |
| **Gemma Terms of Use** | Ticari kullanım serbest; kullanım politikasına uyum ve "Gemma" ibaresinin korunması şart | Gemma 3 |
| **Qwen lisansı** | Ailenin büyük kısmı Apache-2.0; **bazı boyutlar "Qwen Research License" altında: ticari kullanım kapalı**, dağıtılan türevde "Built with Qwen" ibaresi ve `"Notice"` atıf dosyası şartı | Qwen2.5-3B (bu boyutta ölçüldü, bkz. [Lisans, Kişisel Veri ve Model Kartı](/kullanim/lisans-ve-model-karti/)) |

:::danger Lisans uyumu zorunludur
Türev modelinizin lisansı, taban modelin lisansından **daha serbest olamaz.** Örneğin Llama'dan eğittiğiniz bir modeli MIT lisansıyla yayınlayamazsınız; Llama Community License koşulları (isimlendirme dahil) türevinize de aynen uygulanır. Yayınlamadan önce taban modelin kartındaki lisansı mutlaka okuyun. Aynı şekilde, eğitimde kullandığınız **veri setinin lisansı** da önemlidir; izin vermeyen verilerle eğitilmiş modelleri paylaşmak hak ihlali doğurabilir.
:::

:::note[Yukarıdaki tablo bir anlık görüntüdür]
Lisans satırları 17 Ekim 2026'da okunan resmî metinlere ve bu makinedeki yerel paketlere göre yazıldı; modellerin lisansı sonraki sürümlerde değişebilir. Bu sayfadaki genel tablo yerine **kendi indirip kullandığınız paketin lisans alanını açarak okumak** her zaman daha güvenilir. Nasıl ölçüldüğünü — yerel Modelfile denetimi dâhil — [Lisans, Kişisel Veri ve Model Kartı](/kullanim/lisans-ve-model-karti/) sayfasında gösteriyoruz.
:::

## Spaces ile mini demo

Modeli paylaşmanın en ikna edici hali, insanların onu indirip kurmadan deneyebilmesidir. Hugging Face Spaces tam bunu yapar: profilinize bağlı küçük bir uygulama sayfasıdır ve Gradio SDK'sıyla tek bir `app.py` dosyasından oluşan bir sohbet arayüzü bile yeterlidir. Ücretsiz CPU katmanıyla başlayabilir, ilgi görürse GPU'ya yükseltebilirsiniz. Model kartınıza Space'in bağlantısını ekleyin; kart → canlı demo → kod/veri deposu üçlüsü, projenizin vitrinidir. Kurulum adımları için [Spaces dokümanındaki](https://huggingface.co/docs/hub/spaces) Gradio rehberine bakın.

## Kaynaklar ve İleri Okuma

- [Hub — Model Cards](https://huggingface.co/docs/hub/model-cards): Kart metadata alanlarının (license, base_model, pipeline_tag, datasets, library_name) resmi şeması.
- [huggingface_hub — CLI](https://huggingface.co/docs/huggingface_hub/guides/cli): `hf auth login`, `hf upload`, `hf download` komutlarının dokümanı.
- [huggingface_hub — Repository yönetimi](https://huggingface.co/docs/huggingface_hub/guides/repository): Repo oluşturma, görünürlük değiştirme ve gated erişimin resmi rehberi.
- [Hub — Xet Storage kullanımı](https://huggingface.co/docs/hub/xet/using-xet-storage): `hf_xet` paketi ve chunk tekilleştirmenin resmi belgesi.
- [Hub — Xet geçiş duyurusu](https://huggingface.co/blog/xet-on-the-hub): Depolamanın Xet'e taşınmasının duyurulduğu blog yazısı.
- [safetensors](https://huggingface.co/docs/safetensors/index): Güvenli ve hızlı tensor formatının dokümanı.
- [Hub — Spaces](https://huggingface.co/docs/hub/spaces): Gradio SDK ile demo kurma rehberinin giriş sayfası.

## Sonraki adımlar

- Eğitimden paylaşıma kadar tüm akışı bir kez daha görmek için: [Adım Adım Eğitim](/llm/adim-adim-egitim/)
- Türkçe veri setleri ve model depoları: [Faydalı Linkler ve Kaynaklar](/kaynaklar/faydali-linkler/)
- Sık sorulan lisans/maliyet soruları: [Sıkça Sorulan Sorular](/kaynaklar/sss/)
- Kartı yazmadan önce lisans zincirini ve kişisel veriyi denetlemek için: [Lisans, Kişisel Veri ve Model Kartı](/kullanim/lisans-ve-model-karti/)
