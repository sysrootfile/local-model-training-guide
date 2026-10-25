---
title: "Araç Çağırma Mekaniği ve MCP"
description: "Ollama'da araç çağırmanın istek ve cevap biçimi satır satır: tools alanı, tool_calls, role tool mesajı, arguments sözlüğü, tur sayacı ve MCP'nin bu işi nerede standartlaştırdığı."
dogrulama: 2026-10-16
---

Önceki sayfa ajanı **kimi** seçeceğinizi anlatıyordu; bu sayfa **nasıl yazıldığını** anlatıyor. Önce çıplak mekaniği Ollama'nın yerel API'siyle, sonra o mekaniği uygulamalar arasında taşınabilir kılan protokolü (MCP) ele alıyoruz. Sıralı kod örneklerinin tamamı bu makinede gerçekten gönderilmiş isteklerden; hangisinin hangi koşumdan geldiğini her kutuda belirttik.

**Tek cümlelik cevap:** Araç çağırma, modele bir işlev kataloğu verip "cevap üretme, kataloğun adını ve argümanlarını üret" demek; döngünün geri kalanı (çağırmak, sonucu geri koymak, tekrar sormak) sizin yazdığınız sıradan yazılımdır.

## Bir Turun Anatomisi

Araç çağırmanın ağ tarafında yeni bir metot yok: yine `POST /api/chat`. Fark, istekteki `tools` alanı ve cevaptaki `tool_calls` alanı.

```jsonc title="İstek — Örnek 7'deki viki_ara tanımının sadeleştirilmiş hâli"
{
  "model": "qwen2.5:3b-instruct-q4_K_M",
  "messages": [{ "role": "user", "content": "Marmaray hangi yılında hizmete açıldı?" }],
  "tools": [{
    "type": "function",
    "function": {
      "name": "viki_ara",
      "description": "İstanbul toplu ulaşımıyla ilgili Vikipedi parçalarını getirir.",
      "parameters": {
        "type": "object",
        "properties": { "soru": { "type": "string", "description": "Aranan konu, tek cümle" } },
        "required": ["soru"]
      }
    }
  }],
  "stream": false
}
```

```jsonc title="Cevap — bu makinede ölçüldü (keşif koşumu, cikti/kesif.txt)"
{
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [{
      "id": "call_au6z32fo",
      "function": { "index": 0, "name": "sehir_nufusu", "arguments": { "sehir": "Izmir" } }
    }]
  },
  "done_reason": "stop",
  "prompt_eval_count": 190,
  "eval_count": 26
}
```

Dikkat edilecek üç yer:

- **`arguments` bir sözlük, JSON metni değil.** Birçok OpenAI uyumlu API'de bu alan escaped bir string gelir (`"{\"sehir\": \"Izmir\"}"`); Ollama'nın yerel `/api/chat`'inde sözlük geliyor. Yine de iki tipi birden kabul eden bir çevirme katmanı yazmak ucuz bir sigortadır — Örnek 7 `argümanları_cevir()` ile yapıyor.
- **`content` boş.** Araç çağıran turda model genelde metin üretmez; üretirse de o metni cevap saymayın, beklemeye alın.
- **Sunucunun verdiği `id` ve `index` alanları.** Tek araç çağrısında işe yaramazlar; aynı turda iki çağrı geldiğinde hangi sonucun hangi çağrıya ait olduğunu ayırmak için gerekir.

Sonucu geri vermenin biçimi de bir mesaj:

```python title="Araç sonucunu isteme eklemek (Örnek 7, ajan())"
mesajlar.append({"role": "assistant", "content": "", "tool_calls": çağrılar})
mesajlar.append({"role": "tool", "tool_name": "viki_ara", "content": sonuç})
```

`tool_name` mi `tool_call_id` mi? Belgelenmiş öneri `tool_call_id`; bu makinede üç biçim de (`tool_name` ile, yalın `content`, `tool_call_id` ile) aynı cevabı ve **aynı girdi token sayısını** (240) üretti — bkz. `ornekler/ajan-dongusu/cikti/kesif-dongu.txt`. Yani tek araçlı, tek çağrılı bir döngüde bu alanlar pratikte fark yaratmıyor. İki araç varken ve aynı araç iki kez çağrılırken hangisinin hangi sonuç olduğunu karıştırmamanın garantisi ise **`tool_call_id` kullanmaktır**; bu, ölçülmüş bir davranış değil, sıralamanın bozulma riskine karşı verilen bir savunmadır.

## Döngü: Kaç Satır?

Aşağıdaki on iki satır, bir ajanın tamamıdır. Örnek 7'nin `ajan()` fonksiyonundan sadeleştirildi:

```python
mesajlar = [{"role": "system", "content": SİSTEM}, {"role": "user", "content": soru}]
for tur in range(MAKS_TUR):
    yanıt = chat(model=MODEL, messages=mesajlar, tools=ARAÇLAR, stream=False)
    çağrılar = yanıt["message"].get("tool_calls") or []
    if not çağrılar:
        return yanıt["message"]["content"]          # döngü burada kapanır
    mesajlar.append(yanıt["message"])
    for c in çağrılar:
        sonuç = UYGULA[c["function"]["name"]](c["function"]["arguments"])
        mesajlar.append({"role": "tool", "tool_call_id": c["id"], "content": sonuç})
```

Kapanış koşulu tek satırdır: **model araç çağırmadığında bitecek.** Onu yazmazsanız döngü değil sonsuzluk üretirsiniz. `MAKS_TUR` ikinci emniyet supabıdır; [Ajan Ölçümü](/ajan/ajan-olcumu/) sayfasında sayaç sınırına yapışan bir durum var (`done_reason=length`).

## Şart: Modelin Şablonu Araç Bilmeli

Araç çağırma modelin ağırlıklarında değil, **sohbet şablonunda** durur. Modelin şablonu `<tool_call>` gibi bir blok üretmeyi bilmiyorsa, API'ye `tools` göndermek işe yaramaz; Ollama böyle bir modeli araç listesiyle çağırmayı reddeder (belgelenmiş davranış — HTTP 400). Kontrol tek komutluk iştir:

```bash
ollama show qwen2.5:3b-instruct-q4_K_M
# capabilities: completion, tools      <- bu makinede görülen çıktı
```

:::note[Küçük model, kırılgan seçim]
`tools` yeteneği listelemek, modelin o aracı **doğru seçeceğini** garanti etmez. Örnek 7'nin kaydında model, uzunluk sorusuna rağmen birim dönüştürme aracını `{"miktar": 1, "kaynak": "sa", "hedef": "m"}` argümanlarıyla çağırdı; aracımız bu çöp isteği reddetmedi (`"1 sa = 3600 m"` döndürdü) ve sonraki turda model "T1 hattının uzunluğu 3600 metredir" dedi. İki kusur üst üste bindi: birincisi 3 milyar parametreli modelin katalog okuma sınırı, ikincisi araç kodumuzun eksik doğrulaması. Yerelde hatayı küçültmenin yolu araç sayısını az, açıklamaları tek cümle, argümanları **sunucu tarafında** zorunlu tutmaktır.
:::

## tool_choice: Belgesiz Alan

OpenAI arayüzünden alıştığımız `tool_choice: "required"` (mutlaka araç çağır) alanı, Ollama'nın yerel `/api/chat` belgelemesinde **yok**; hem OpenAI hem Anthropic uyumluluk katmanı sayfalarında `tool_choice` "not supported" olarak işaretli. Önceki sürümlerde bu alanın sessizce yok sayıldığı bildiriliyor (ollama/ollama#11171).

Bu sayfada o iddiayı varsaymadık: sunucuya gönderip sonucu ölçtük (`F` denemesi). `tool_choice` alanının dört biçimi — hiç göndermemek, `"auto"`, `"required"` ve geçersiz bir değer (`"bulutmeydan"`) — bu makinede **dördünde de HTTP 200 ve aynı davranışı** üretti: model araç çağırdı, `content` boş kaldı. Yani sunucu ne alanı reddediyor ne de geçersiz bir değeri farkediyor.

Dürüst sınır: bu test **ayırt edici değildi.** Seçtiğimiz soru, modelin alan olmadan da araç çağırdığı bir soruydu; "zorladı" ile "yok saydı" ayrımı ancak modelin araç çağırmadan cevaplayacağı bir sorguyla koşulabilir. O deneme yapılmadı. Pratik sonuç değişmiyor: **belgelenmemiş bir alanın üstüne tasarım kurmayın**; zorlama gerekiyorsa diziyi kendi kodunuzda sabitleyin ya da aracı yapılandırılmış çıktı kipiyle siz tetikleyin.

## format + tools: Dokümanın Söylemediği

Yapılandırılmış çıktı (`"format": "json"`) ve araçlar aynı istekte buluştuğunda ne olur? Ollama'nın belgelemesi bu ikilinin etkileşimini anlatmıyor. `G` denemesi bu makinede HTTP 200 döndü ve cevapta **`tool_calls` alanı hiç yoktu**: model araç çağrısını JSON *metni* olarak `content` içine yazdı (`{"name": "viki_ara", "arguments": {...}}`). Yani protokol kazanmadı, yerine geçti: `tool_calls` bekleyen bir döngü bu istekte hiç başlamaz. Ham kayıt [Ajan Ölçümü](/ajan/ajan-olcumu/) sayfasında; tek gözeme dayalı bu davranışa karşı en sağduyulu yol, araç kullanan isteklerde `format` bırakmamak.

## Araçların Token Fiyatı

Katalog bedava değil. İki taraf da bunu yazılı söylüyor:

- OpenAI, Function calling → Token Usage: *"callable function definitions count against the model's context limit and are billed as input tokens"*; önlem olarak daha az/ daha kısa araç öneriyor.
- Anthropic, Define tools: her araç açıklaması için "en az 3-4 cümle" tavsiye ediyor — isteme eklenen metin.

Açık bir sayı veren tek resmî metin Anthropic'in `input_examples` bandı: basit örnekler **~20-50**, içi içe geçmiş karmaşık nesneler **~100-200 token**. Genel bir işlev şemasının token sayısı için resmî bir rakam yok; bu yüzden ölçtük. Bu makinede iki ayrı koşum var: yalın bir deneme istekte taban **54** token iken tek bir araç tanımı eklenince **190** token (**+136**), Örnek 7'nin gerçek sistem talimatıyla koşan denemede taban **73** token iken `viki_ara` **+164**, ikinci araç olarak `birim_donustur` **+109** token ekledi. Tablo ve yorum: [Ajan Ölçümü](/ajan/ajan-olcumu/).

Araç sayısının seçimi bozduğu iddiası (dokümanlarda "dozens of tools" uyarısı) niteliklidir; sayısal bir eşik veren resmî kaynak yok.

## MCP: Aynı Kataloğu Birden Fazla Uygulamaya Taşımak

Yukarıdaki `tools` alanı **uygulamaya özeldir**: aynı aracı hem kendi betiğinizde hem bir editörde hem de bir sohbet arayüzünde kullanmak isterseniz, her biri için ayrı entegrasyon yazarsınız. **MCP (Model Context Protocol)** bu köprüyü standardize eden açık protokol.

Spesifikasyonun kendi tanımı (rev 2026-07-28): *"MCP is an open protocol that enables seamless integration between LLM applications and external data sources and tools."* Protokol **David Soria Parra** ve **Justin Spahr-Summers** tarafından yazıldı, Anthropic **2024-11-25** tarihinde duyurdu (tarih satıcının kendi sayfasından). Bugün yönetimi "Model Context Protocol a Series of LF Projects, LLC" altında; Linux Vakfı **9 Aralık 2025**'te Agentic AI Foundation'ı kurduğunu ve ilk katkıların **Anthropic'in MCP'si, Block'un goose'u ve OpenAI'ın AGENTS.md'si** olduğunu duyurdu.

:::caution[Lisans konusunda iki metin çelişiyor]
Spesifikasyon deposunun `LICENSE` dosyası **MIT** diyor; topluluk yönetim sayfası katkılardan **Apache-2.0** (dokümanlar CC BY 4.0) istiyor. İkisini ayrı ayrı belirtmek doğrusu — tek birini "MCP'nin lisansı" diye yazmak, kaynak göstermeden iddia olur.
:::

### Üç Taraf, Üç Yetenek

MCP'nin sözlüğü (rev 2026-07-28):

| Taraf | Kim | Ne yapar |
| --- | --- | --- |
| Host | Sizin uygulamanız (editör, sohbet arayüzü) | Modelleri çağıran, kullanıcıyla konuşan taraf |
| Client | Host içindeki köprü | Sunucuya bağlanır, bildirimleri iletir (uygulamada bir tane sunucu başına) |
| Server | Araçları saran küçük servis | **Tools**, **Resources**, **Prompts** sunar |

Sunucunun üç sunduğu şey birbirinin yerine geçmez: **Tools** modelin çağırması içindir (bizim `tools` alanının karşılığı), **Resources** uygulamanın okuduğu veridir, **Prompts** kullanıcının seçtiği hazır şablonlardır. İstem tarafındaki yetenekler (Elicitation, Sampling, Roots) ve yardımcılar (progress, cancellation, completion, logging) da ayrı adlandırılmış.

Taşıma katmanı olarak **stdio** (aynı makinede, alt süreç olarak) ve **Streamable HTTP** var; spesifikasyon "custom transports"na izin veriyor. JSON-RPC 2.0 ve UTF-8 taban zorunlu.

### Sürüm Tarihi: İşin Bu Kısımı Hareketli

Revizyonlar: **2024-11-05 → 2025-03-26 → 2025-06-18 → 2025-11-25 → 2026-07-28** (güncel). Bu bir vitrin bilgisi değil, kod etkileyen bir ayrım:

- **HTTP+SSE transportu 2025-03-26'da kullanımdan kaldırıldı**; geçiş yolu Streamable HTTP. Eski örnekleri kopyalarsanız bu hatayı alırsınız.
- **Roots, Sampling ve Logging, 2026-07-28 revizyonunda kullanımdan kaldırıldı** (SEP-2577). Önerilen geçişler: araç parametreleri / kaynak URI'leri / sunucu ayarları, model sağlayıcı API'siyle doğrudan çalışmak, loglar için stderr ya da OpenTelemetry. Kaldırılma için en erken tarih "2027-07-28 sonrasında çıkan ilk revizyon".
- 2026-07-28 **durumsuz (stateless) bir yeniden yazım**: oturum ve `Mcp-Session-Id` kaldırıldı, `initialize` / `notifications/initialized` el sıkışması kaldırıldı; sürüm, yetenekler ve istemci bilgisi artık istek başına `_meta` içinde taşınıyor, sunucuların `server/discover` yanıtlaması zorunlu. Spesifikasyon bunu "Modern" ve "Legacy" dönem diye ayırıyor; ikisini destekleyen "Dual-era" da tanımlı.

Resmî SDK'lar (2026-07-28 dokümanı): Tier 1 TypeScript, Python, C#, Go, Rust, Ruby; Tier 2 Java; Tier 3 Swift, PHP, Kotlin. Sunucu bulmak için **Official MCP Registry** var ama hâlâ **ön izleme** aşamasında: kendi dokümanı "breaking changes or data resets may occur before general availability" diyor — kalıcı bir bağımlılık gibi davranmayın.

## Ollama ve MCP: Bugünkü Gerçek Durum

:::caution[Belge tek bir yere sıkışmış, ölçüm hiç yok]
Ollama, kendisini bir **MCP host'u ya da istemcisi** olarak belgelemiyor. docs.ollama.com'un tüm sayfa dizininde (`llms.txt`) MCP geçen tek yer **Web search** sayfasındaki "## MCP Server" başlığı: Ollama'nın **bulut** web arama/okuma hizmetini, `ollama-python` deposundaki `examples/web-search-mcp.py` ile bir **MCP stdio sunucusu olarak dışarı açıyor** (kullanmak için `OLLAMA_API_KEY` gerekiyor) ve belgelenmiş istemci örnekleri Cline, Codex ve Goose. Depoda "MCP desteği" ekleyen PR'lar (#13562, #13700) **birleştirilmeden kapatılmış**.
:::

Yerel bir döngü kuruyorsanız bugün anlamlı iki yol var:

1. **`/api/chat` + `tools`** (Örnek 7'nin yolu). Tek bağımlılık Ollama; sıfır ek süreç. Araçlarınız bir Python betiğinde yaşıyor.
2. **Ayrı bir MCP sunucusu yazıp onu kendi betiğinizden çağırmak.** Protokolün kazancı, aynı sunucuyu bir editör ya da Cline gibi ikinci bir uygulamanın da kullanabilmesi; maliyeti bir alt süreç, JSON-RPC haberleşmesi ve MCP sürüm takibi. `tool` mesajı biçimi ile MCP'nin `tools/call` biçimi aynı şey değildir; arada çeviri katmanı sizde kalır.

Bu rehber yerelde ölçüm yaptığı için 1. yolla yetiniyor; 2. yolun gecikme ve token maliyeti **bu makinede ölçülmedi**.

:::note[Kendi sunucunuzu denemek isterseniz]
En küçük MCP sunucusu bir Python betiği ve Tier 1 Python SDK ile kurulur; sunucunun `tools/list` yanıtı deterministik sıralı olmalı ve `inputSchema` geçerli bir JSON Şeması olmalı (2026-07-28 zorunlulukları). Örnek 7'deki iki araç (`viki_ara`, `birim_donustur`) MCP'ye birebir taşınabilir işlerdir — taşıma sonrasında yerel gecikmenin ne kadar değiştiği burada ölçülmediği için sayfa sayı vermiyor.
:::

## Pratik Kontrol Listesi

1. `ollama show <model>` çıktısında `tools` var mı? Yoksa bu modelle döngü kurmayın.
2. Katalog **küçük** tutun: bir araç, bir görev. Aynı işi yapan iki araç, seçimi bozan ilk etkendir.
3. `arguments` tipini kontrol edin: sözlük mü, JSON metni mi? İkisini de kabul eden bir çevirme yazın.
4. Kapanış koşulunu ve `MAKS_TUR` sayaçını yazmadan döngüye "ajan" demeyin.
5. Araç sonucu yetersizse **modelin yorumlayacağı bir metin** döndürün ("eşik altında", "bilinmeyen birim") — sessiz başarısızlık, uydurma cevabın yakıtıdır.
6. Tur başına `prompt_eval_count` ve `done_reason` alanlarını loglayın; maliyeti ve kesilen cevabı başka hiçbir alan göstermez.
7. `tool_choice` gibi belgelenmemiş alanlara dayanan bir tasarım yapmayın: önce bu makinede davranışını ölçün.

## Burada Ölçülmeyenler

- Araç sayısının (3, 10, 30) seçim doğruluğuna etkisi: iki araçlık katalogla çalışıldı.
- MCP sunucusunun yerel gecikme/token maliyeti; Ollama'nın MCP istemcisi olarak davranışı (belgelenmiş değil).
- `stream: true` ile araç çağrısı: parçalı (delta) gelen `tool_calls` birleştirmesi burada denenmedi.
- Küçük model yerine araç çağırmada daha güçlü bir modelle aynı katalogun kaç turda kapandığı.

## Kaynaklar ve ileri okuma

- [Ajan Ölçümü](/ajan/ajan-olcumu/) — bu mekanizmanın saniye, tur ve token karşılığı; `tool_choice` ve `format` denemelerinin bu makinedeki sonucu.
- [Ajan mı Sabit RAG Hattı mı?](/ajan/ajan-mi-sabit-hat-mi/) — mekanik değil karar sayfası.
- [Örnek 7: Ajan Döngüsü](/ornekler/ajan-dongusu/) — betiğin tamamı ve satır satır açıklaması.
- [Ollama Chat API](https://docs.ollama.com/api/chat.md) — `tools`, `tool_calls` ve kullanım alanlarının yerel belgelemesi.
- [Ollama Tool Calling](https://docs.ollama.com/capabilities/tool-calling.md) — çok turlu araç döngüsünün belgelenmiş örnek bölümü.
- [MCP spesifikasyonu 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) — güncel protokol; terminoloji, zorunluluklar ve taşima katmanları.
- [MCP kullanımından kaldırılanlar](https://modelcontextprotocol.io/specification/2026-07-28/deprecated.md) — HTTP+SSE, Roots, Sampling ve Logging için tarih ve geçiş yolları.
- [OpenAI Function calling](https://developers.openai.com/api/docs/guides/function-calling) — araç tanımlarının girdi tokenı sayıldığına dair resmî metin.
- ReAct, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) — akıl yürütme ve eylemi sırayla üretme; bu döngünün akademik adı.
- Toolformer, [arXiv:2302.04761](https://arxiv.org/abs/2302.04761) — modelin hangi API'yi ne zaman ve hangi argümanla çağıracağını kendisinin öğrenmesi.
