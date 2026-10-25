---
title: "Veri Formatları: JSONL, Alpaca, ShareGPT ve Diğerleri"
description: Eğitim araçlarının beklediği veri formatlarını (JSONL, Alpaca, ShareGPT, ChatML/messages) örneklerle öğrenin; sohbet şablonu farkı, dönüştürme kodu ve sık yapılan hatalar.
dogrulama: 2026-10-15
---

Eğitim araçları verinizi belirli formatlarda bekler. **Yanlış format, bu alanda en sık karşılaşılan hata kaynağıdır**: kodunuz doğrudur, model doğrudur, ama araç verinizi ya okuyamaz ya da okur gibi yapıp boş bir eğitim çalıştırır. Bu sayfada yaygın formatları, aralarındaki farkı ve dönüşüm yollarını göreceksiniz.

## JSONL: Satır Başına Bir JSON

JSONL (JSON Lines), her satırda **tek bir bağımsız JSON nesnesi** bulunan metin dosyasıdır. Uzantı genelde `.jsonl` olur (bazen `.ndjson`).

```json title="veri.jsonl"
{"instruction": "Merhaba de.", "output": "Merhaba! Size nasıl yardımcı olabilirim?"}
{"instruction": "Teşekkür et.", "output": "Rica ederim, iyi çalışmalar dilerim."}
```

Neden JSONL?

- **Satır satır okunabilir:** dev dosyalar belleğe tamamen yüklenmeden akış (stream) halinde işlenir.
- **Hata izole edilir:** bozuk bir satır, dosyanın tamamını okunamaz hale getirmez; yalnızca o satırı düzeltirsiniz.
- **Eklenebilir:** yeni örnek eklemek, dosyanın sonuna bir satır yazmaktır.

Karşılaştırma için aynı verinin "tek dizi" JSON hali: `[ {...}, {...} ]`. Bu, ufak dosyalarda çalışır ama büyüdükçe akış dostu değildir ve tek hata tüm dosyayı düşürür.

## Alpaca Formatı: instruction / input / output

SFT (talimat ayarı) için en yaygın format. Üç alan:

- **instruction:** görev/soru (zorunlu).
- **input:** görevle birlikte verilen ek metin (opsiyonel).
- **output:** modelin öğrenmesi istenen cevap.

Tam ve gerçekçi bir örnek:

```json title="alpaca_ornek.jsonl"
{
  "instruction": "Aşağıdaki paragrafı en fazla üç maddede özetle.",
  "input": "Fotosentez, bitkilerin güneş ışığını kullanarak su ve karbondioksitten glikoz ürettiği süreçtir. Bu süreç kloroplastlarda gerçekleşir ve yan ürün olarak oksijen açığa çıkar. Fotosentez, Dünya'daki oksijen dengesinin ve besin zincirinin temelini oluşturur.",
  "output": "- Bitkiler güneş ışığıyla su ve karbondioksitten glikoz üretir.\n- Süreç kloroplastlarda gerçekleşir ve yan ürün oksijendir.\n- Fotosentez, oksijen dengesi ile besin zincirinin temelidir."
}
```

:::tip
**input ne zaman boş bırakılır?** Talimat kendi başına yeterliyse — ör. `"instruction": "Türkiye'nin başkenti neresidir?"`. Böyle durumlarda `"input": ""` yazmak en güvenlisidir; bazı araçlar `null` yerine boş string bekler. Alan adlarını (instruction/input/output) aracınızın dokümanından doğrulayın: Alpaca ailesinde `prompt`/`response` çifti kullanan türevler de yaygındır.
:::

## ShareGPT / conversations: Çok Turlu Sohbet

Modeli çok turlu sohbet için eğitecekseniz ShareGPT formatı devreye girer: tek örnek, sıralı mesajlardan oluşan bir `conversations` listesidir.

```json title="sharegpt_ornek.jsonl"
{
  "conversations": [
    {"from": "human", "value": "Python'da bir listenin tersini nasıl alırım?"},
    {"from": "gpt", "value": "En kısa yol ters dilimlemedir: liste[::-1]. Bu ifade listenin tersten bir kopyasını döndürür."},
    {"from": "human", "value": "Orijinal listeyi bozmadan sıralı olarak tersten istersem?"},
    {"from": "gpt", "value": "sorted(liste, reverse=True) kullanabilirsiniz; bu, yeni bir liste döndürür ve orijinal liste değişmez."}
  ]
}
```

Bir varyant da `from`/`value` yerine `role`/`content` adlarını kullanan sürümdür:

```json
{"conversations": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Hangi adların beklendiği araca göre değişir: Unsloth, LLaMA-Factory ve Axolotl geleneksel `from`/`value` biçimini destekler; birçok araç `role`/`content` varyantını da kabul eder. Emin değilseniz aracın örnek veri setini indirip alan adlarına bakın.

## ChatML / messages: Roller ve Sistem İstemi

En modern yaklaşım: rol tabanlı mesaj listesi. Üç rol vardır:

- **system:** modelin genel davranış çerçevesi (ton, dil, sınırlar).
- **user:** kullanıcının mesajı.
- **assistant:** modelin cevabı.

```json title="messages_ornek.jsonl"
{
  "messages": [
    {"role": "system", "content": "Sen bir çevrim içi mağazanın müşteri hizmetleri asistanısın. Türkçe, kısa ve nazik cevap verirsin."},
    {"role": "user", "content": "Siparişim üç gündür yolda görünüyor, ne yapmalıyım?"},
    {"role": "assistant", "content": "Sipariş numaranızı paylaşırsanız kargo durumunu hemen kontrol edip size bilgi verebilirim."}
  ]
}
```

**Sistem istemi (system prompt) nedir, neden önemli?** Modelin "kişiliğini ve kurallarını" taşıyan ilk mesajdır. Eğitim verinizdeki sistem istemleri **tutarlı** olmalıdır: bir örnekte "resmi bir avukat gibi konuş", diğerinde hiç sistem mesajı yoksa model, sistem istemine uymayı değil onu görmezden gelmeyi öğrenir. Karar verin: ya her örnekte aynı/benzer sistem istemi olsun ya da hiç olmasın. Dağıtımda (çıkarımda) da eğitimdekiyle aynı veya çok benzer istemi kullanın.

"ChatML" adı, `messages` yapısının arka planda özel token'lara (`<|im_start|>`, `<|im_end|>` gibi) çevrildiği şablondan gelir; bu çevirmeyi birazdan göreceğiz.

## Özet Tablo: Hangi Format, Hangi Durum?

| Format | Alanlar | Çok turlu mu? | Seven araçlar |
| --- | --- | --- | --- |
| Alpaca | instruction, input, output | Hayır (tek tur) | Unsloth, TRL (SFT), LLaMA-Factory, Axolotl |
| ShareGPT | conversations: from/value | Evet | Unsloth, LLaMA-Factory, Axolotl |
| ChatML / messages | messages: role/content | Evet | Unsloth, TRL, LLaMA-Factory, Axolotl |
| Düz metin | — | Hayır | Ön eğitim / devam eğitimi (TRL, Axolotl) |
| prompt-completion | prompt, completion | Hayır | TRL (completion eğitimi) |

:::note
Araçlar zaman içinde destekledikleri formatları değiştirir; tablo 2026 itibarıyla tipik durumu yansıtır. Kesin bilgi aracın kendi dokümanındadır: [Araçlar](/llm/araclar/).
:::

## Format ≠ Şablon: Sohbet Şablonları

En kritik ayrım: **format**, verinin dosyadaki hali; **şablon (chat template)** ise tokenizer'ın bu yapıyı modelin beklediği özel token'lı düz metne çevirme kuralıdır. Her model ailesi farklı bir şablon kullanır (Qwen, Llama, Mistral... hepsi farklı).

```python title="sablon.py"
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B")  # kullandığınız modelin HF adını yazın

mesajlar = [
    {"role": "system", "content": "Kısa ve net cevap ver."},
    {"role": "user", "content": "Merhaba!"},
]

metin = tok.apply_chat_template(mesajlar, tokenize=False, add_generation_prompt=True)
print(metin)
```

Çıktı, mesajların modelin istediği özel token'larla çevrilmiş düz metin halidir (ChatML benzeri modellerde `<|im_start|>system ... <|im_end|>` kalıbı). Eğitim araçları bu dönüşümü çoğu zaman sizin yerinize yapar; yapmadıkları durumda bu adımı atlamak en sinsi hatalardan birini yaratır:

:::caution
**Aynı şablon kuralı:** Eğitimde `apply_chat_template` ile (ör. ChatML kalıbıyla) eğittiğiniz modeli, çıkarımda farklı bir şablonla (ör. `[INST]` kalıbıyla) sorgularsanız model "talimat formatını" tanımaz: cevap vermek yerine girişi tamamlamaya çalışır, soruyu yankılar veya saçmalar. Model bozulmamıştır; giriş biçiminiz eğitimdeki kalıba uymuyordur. "SFT yaptım ama model düzgün konuşmuyor" sorularının arkasında çoğu zaman bu vardır. Yerel dağıtımda şablonun doğru seçildiğinden emin olun: [Ollama Rehberi](/kullanim/ollama/), [Sorun Giderme](/llm/sorun-giderme/).
:::

## Python ile Format Dönüştürme

Elinizdeki Alpaca formatlı veriyi ShareGPT'ye çevirmek çok basittir. Burada iki incelik var: `ensure_ascii=False` (Türkçe karakterler `\u0130` gibi kaçış dizilerine dönüşmesin) ve satır satır yazma (JSONL kuralı):

```python title="alpaca_to_sharegpt.py"
import json

def alpaca_to_sharegpt(ornek: dict) -> dict:
    soru = ornek["instruction"]
    if ornek.get("input"):
        soru = f"{soru}\n\n{ornek['input']}"
    return {
        "conversations": [
            {"from": "human", "value": soru},
            {"from": "gpt", "value": ornek["output"]},
        ]
    }

with open("alpaca.jsonl", encoding="utf-8") as f:
    veriler = [json.loads(satir) for satir in f if satir.strip()]

with open("sharegpt.jsonl", "w", encoding="utf-8") as f:
    for ornek in veriler:
        f.write(json.dumps(alpaca_to_sharegpt(ornek), ensure_ascii=False) + "\n")

print(f"{len(veriler)} örnek dönüştürüldü")
```

:::tip
Dönüşümden sonra ilk 5 satırı mutlaka gözle kontrol edin. Dosya "geçerli JSON" olsa bile semantik hatayı (yanlış alana yazılmış cevap, boş conversation listesi) yalnızca gözünüz yakalar.
:::

Modern varsayılan `messages` formatına çevirmek de aynı kalıptadır; bu kez sistem istemini parametre olarak alın ki aynı veriyi farklı istemlerle denemek kolaylaşsın:

```python title="alpaca_to_messages.py"
import json

def alpaca_to_messages(ornek: dict, sistem_istemi: str | None = None) -> dict:
    soru = ornek["instruction"]
    if ornek.get("input"):
        soru = f"{soru}\n\n{ornek['input']}"
    mesajlar = []
    if sistem_istemi:
        mesajlar.append({"role": "system", "content": sistem_istemi})
    mesajlar.append({"role": "user", "content": soru})
    mesajlar.append({"role": "assistant", "content": ornek["output"]})
    return {"messages": mesajlar}


SISTEM_ISTEMI = "Sen kısa ve net cevap veren bir asistansın."

with open("alpaca.jsonl", encoding="utf-8") as f:
    veriler = [json.loads(satir) for satir in f if satir.strip()]

with open("messages.jsonl", "w", encoding="utf-8") as f:
    for ornek in veriler:
        f.write(json.dumps(alpaca_to_messages(ornek, SISTEM_ISTEMI), ensure_ascii=False) + "\n")

print(f"{len(veriler)} örnek dönüştürüldü")
```

Sistem istemini setin **tamamında aynı** tutmayı unutmayın (yukarıdaki "Sistem istemi (system prompt) nedir, neden önemli?" bölümü); istemi parametreye çıkarmak, dönüşüm kodunu değiştirmeden yalnızca istem metnini denemenizi sağlar.

## Hugging Face Datasets ile Yükleme ve Bölme

```python title="yukle.py"
from datasets import load_dataset

ds = load_dataset("json", data_files="veri.jsonl", split="train")

# %10'luk doğrulama (validation) bölmesi — seed sabit olsun ki tekrarlanabilsin
bolumler = ds.train_test_split(test_size=0.1, seed=42)
train_ds, val_ds = bolumler["train"], bolumler["test"]

print(train_ds)
print(val_ds)
```

:::note
Sınıflandırma gibi dengesiz veri setlerinde `train_test_split(stratify_by_column="etiket")` kullanın ki her sınıftan dengeli örnek düşsün. Eğitim/doğrulama bölmesinde sabit `seed` seçmek, farklı denemeleri adil karşılaştırmanızı sağlar. Eğitim bitince modeli paylaşma: [Hugging Face'te Paylaşım](/kullanim/huggingface-paylasim/).
:::

## Sık Format Hataları

| Sorun | Belirti | Çözüm |
| --- | --- | --- |
| Eksik/fazla virgül, kapanmayan tırnak | `JSONDecodeError` (satır numarasıyla) | İlgili satırı düzeltin; dosyayı satır satır `json.loads`'tan geçiren minik bir betik yazın |
| Yanlış anahtar adı | Araç "field not found" der ya da 0 örnek yükler | Alpaca: instruction/input/output; ShareGPT: conversations + from/value; messages: role/content |
| Tüm veri tek satırda | Örnek sayısı 1 görünür | Satır sonlarıyla (LF) ayrıldığından emin olun; dosyayı tek JSON dizisi olarak yazmayın |
| BOM / encoding sorunu | Türkçe karakterler bozulur; "utf-8 codec can't decode" | Dosyayı UTF-8 (BOM'suz) kaydedin; Python'da her okuma/yazmaya `encoding="utf-8"` verin |
| Aşırı uzun tek satırlar | Yükleme çok yavaş / bellek patlaması | Çok uzun örnekleri filtreleyin; uzun dokümanları parçalara bölün |
| Eğitimde kayıp (loss) düşmüyor | "Eğitim çalışıyor ama model öğrenmiyor" | Şablon eğitim ve çıkarımda aynı mı? Loss hesaplanan token'lar (maskeleme) doğru mu? → [Sorun Giderme](/llm/sorun-giderme/) |

## Eğitim Öncesi Doğrulama Betiği

Format hataları en pahalı hatalardır: genellikle fark edilmeden, saatler süren bir eğitimin içine gömülürler. Aşağıdaki tek dosyalık betik, veriyi eğitime vermeden önce üç kontrolü birlikte yapar: satır satır linter, zorunlu alan kontrolü ve tokenizer ile doğrulama. Betik, eğiteceğiniz modelin tokenizer'ını yükler, GPU gerektirmez ve veri setine yapılan her değişiklikten sonra yeniden çalıştırılabilir.

```python title="veri_dogrula.py"
import json
import math

from transformers import AutoTokenizer

YOL = "veri.jsonl"            # doğrulanacak dosya
MODEL = "Qwen/Qwen3-4B"       # eğiteceğiniz modelin HF adı
ILK_N = None                  # dosya çok büyükse: yalnızca ilk N satırı kontrol et


def alanlari_kontrol_et(ornek: dict) -> str | None:
    """Geçerliyse None, değilse açıklayıcı hata metni döndürür."""
    if "messages" in ornek:
        mesajlar = ornek["messages"]
        if not isinstance(mesajlar, list) or not mesajlar:
            return "'messages' boş veya liste değil"
        for i, mesaj in enumerate(mesajlar):
            if "role" not in mesaj or "content" not in mesaj:
                return f"messages[{i}] içinde 'role'/'content' eksik"
        return None
    if "instruction" in ornek and "output" in ornek:
        return None
    return "'messages' ya da 'instruction' + 'output' alanları yok"


def mesaja_cevir(ornek: dict) -> list:
    """Her iki formatı da mesaj listesine çevirir (şablon render'ı için)."""
    if "messages" in ornek:
        return ornek["messages"]
    soru = ornek["instruction"]
    if ornek.get("input"):
        soru = f"{soru}\n\n{ornek['input']}"
    return [
        {"role": "user", "content": soru},
        {"role": "assistant", "content": ornek["output"]},
    ]


def yuzdelik(sirali: list, p: int) -> int:
    """Saf Python yüzdelik hesabı (nearest-rank); numpy gerekmez."""
    if not sirali:
        return 0
    k = math.ceil(p / 100 * len(sirali))
    return sirali[min(k, len(sirali)) - 1]


# 1) Linter: satır satır JSON + zorunlu alan kontrolü
gecerli = []
with open(YOL, encoding="utf-8") as f:
    for numara, satir in enumerate(f, start=1):
        if ILK_N and numara > ILK_N:
            break
        if not satir.strip():
            continue
        try:
            ornek = json.loads(satir)
        except json.JSONDecodeError as hata:
            print(f"HATA satır {numara}: bozuk JSON ({hata.msg})")
            continue
        sorun = alanlari_kontrol_et(ornek)
        if sorun:
            print(f"HATA satır {numara}: {sorun}")
            continue
        gecerli.append(ornek)

print(f"\n{len(gecerli)} geçerli örnek bulundu.")
if not gecerli:
    raise SystemExit("Geçerli örnek yok; dosyayı düzeltip betiği yeniden çalıştırın.")

# 2) Şablon render'ı: ilk örneği gözle kontrol edin
tok = AutoTokenizer.from_pretrained(MODEL)
print("\n--- İlk örneğin şablonla render edilmiş hali ---")
print(tok.apply_chat_template(mesaja_cevir(gecerli[0]), tokenize=False, add_generation_prompt=False))
print("--- Rol token'ları, sıralama ve boşluklar doğru mu? ---\n")

# 3) Token istatistiği: p50 / p95 ve max_length önerisi
uzunluklar = sorted(
    len(tok.apply_chat_template(mesaja_cevir(ornek), tokenize=True, add_generation_prompt=False))
    for ornek in gecerli
)
p50 = yuzdelik(uzunluklar, 50)
p95 = yuzdelik(uzunluklar, 95)
onerilen = max(128, math.ceil(p95 / 128) * 128)  # 128'in katına yukarı yuvarla
print(f"Token uzunluğu: min={uzunluklar[0]}  p50={p50}  p95={p95}  max={uzunluklar[-1]}")
print(f"max_length önerisi: {onerilen} (p95'i kapsar; önerinin üzerindeki azınlık kırpılır)")
```

**Üç adımı da atlamayın:**

1. **Linter**, bozuk JSON'u ve eksik alanı satır numarasıyla söyler; dosyayı gözle taramanıza gerek kalmaz.
2. **Şablon render'ı**, ilk örneğin modelin göreceği tam metne dönüşmüş halini gösterir; yanlış rol sırası, eksik sistem istemi veya boş içerik ancak böyle yakalanır.
3. **Token istatistiği**, `max_length` ve bellek planınızın girdisidir; p95 ile max arasındaki fark büyükse önerilen `max_length`'te uzun kuyruk kırpılır — uzun örnekleri bölmeyi veya `max_length`'i yükseltmeyi düşünün.

## Araç Çağırma (Tool Calling) Verisi: Kısa Bakış

Modele, gerektiğinde tanımlı araçları çağırma davranışını kazandırmak isterseniz SFT verinizde assistant cevabı düz metin yerine **yapılandırılmış bir çağrı** olur. İşleyiş kabaca şöyledir: modele önce araç tanımları verilir (araç adı, açıklaması ve parametre şeması — genelde JSON Schema); model çağrı üretmek istediğinde serbest bir cümle değil, tanımlı alanlardan oluşan bir çağrı yazar. Araç çalıştırıldıktan sonra sonucu modele geri beslersiniz; model sonucu okuyup nihai cevabı üretir.

2026 itibarıyla yaygın biçim OpenAI Chat Completions tarzıdır: assistant mesajında bir `tool_calls` listesi döner; her çağrıda `id`, `type` ve `function` (araç adı + argümanlar) alanları bulunur. Kritik ayrıntı: `function.arguments` alanı **JSON-encode edilmiş bir string**'dir (iç içe JSON metni); kullanmak için `json.loads` ile ayrıştırmanız gerekir.

```json title="tool_calls_ornek.json"
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_ornek123",
      "type": "function",
      "function": {
        "name": "hava_durumu",
        "arguments": "{\"sehir\": \"Ankara\"}"
      }
    }
  ]
}
```

Araç sonucunu modele `{"role": "tool", "tool_call_id": "...", "content": "..."}` mesajıyla verirsiniz. Eğitim verinizde bu döngünün tamamı örneklenmelidir: araç listesi (`tools`) → `tool_calls` → araç sonucu → nihai cevap.

Her ekosistem aynı biçimi kullanmaz: örneğin Hermes tarzı modeller çağrıyı ChatML içine gömülü `<tool_call>...</tool_call>` etiketleriyle üretir; OpenAI'nin daha yeni Responses API'si ise farklı bir yapı kullanır. Bu yüzden veri setini hazırlarken eğitim aracınızın beklediği biçimi teyit edin: [Araçlar](/llm/araclar/) ve OpenAI [function calling kılavuzu](https://developers.openai.com/api/docs/guides/function-calling).

:::note
**İlk projeniz için çoğu zaman gerekmez.** Dış dünyaya erişen (arama, hesaplama, API çağrısı) bir asistan hedeflemiyorsanız tool calling verisini sonraya bırakabilirsiniz; basit soru-cevap setiyle başlamak sizi daha hızlı ilerletir.
:::

## Kaynaklar ve İleri Okuma

- [Hugging Face — Chat templates](https://huggingface.co/docs/transformers/chat_templating) — `apply_chat_template`'ın ve model ailesine göre değişen şablonların resmî anlatımı; "format ≠ şablon" ayrımının kaynağı.
- [TRL — Dataset formats](https://huggingface.co/docs/trl/dataset_formats) — TRL trainer'larının beklediği format ve türlerin tam listesi (language modeling, prompt-completion, preference ve tool calling dahil).
- [Unsloth — Chat Templates](https://unsloth.ai/docs/basics/chat-templates) — Unsloth'un desteklediği şablonlar (Conversational, ChatML, ShareGPT, Alpaca) ve kullanım notları.

## Sırada Ne Var?

- Format tamam, şimdi temizlik: [Veri Temizleme](/veri/veri-temizleme/)
- Verinizi sıfırdan üretin: [Kendi Verini Oluştur](/veri/kendi-verini-olustur/)
- Eğitime geçin: [SFT Rehberi](/llm/sft/) ve [Adım Adım Eğitim](/llm/adim-adim-egitim/)
