# Örnek 7: Ajan Döngüsü

[Örnek 6](../viki-rag/)'nın 125 parçalık Vikipedi korpusunu **bir araca** saran ölçüm betiği. Amaç ajan kurmak değil, ajan döngüsünün bu makinedeki faturasını ve arıza biçimlerini kayıt altına almak: tur sayısı, tur başına duvar süresi, araç kataloğunun token gideri, `tool_choice` ve `format` alanlarının gerçek davranışı.

Sitedeki sayfalar: [Ajan mı Sabit RAG Hattı mı?](../../src/content/docs/ajan/ajan-mi-sabit-hat-mi.md), [Araç Çağırma Mekaniği ve MCP](../../src/content/docs/ajan/arac-cagirma-ve-mcp.md), [Ajan Ölçümü](../../src/content/docs/ajan/ajan-olcumu.md), [Örnek 7 sayfası](../../src/content/docs/ornekler/ajan-dongusu.mdx).

## Gereksinimler

- Çalışır bir Ollama sunucusu (`http://127.0.0.1:11434`) — `localhost` istek başına ~2 sn ekliyor, ölçüldü
- Modeller:

```bash
ollama pull bge-m3
ollama pull qwen2.5:3b-instruct-q4_K_M
```

- İlk koşumda internet (korpus Vikipedi'den iner ve `cikti/korpus.json`a yazılır; sonraki koşumlar önbelleği okur)
- `../viki-rag/cikti/vektor-indeks.json.gz` varsa ve korpus imzası tutuyorsa vektörleştirme atlanır
- Harici Python paketi gerekmez. `viki_rag.py` import edildiği için `ornekler/viki-rag/` klasörü yerinde olmalı.

## Çalıştırma

```bash
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u ajan.py > cikti/ajan-kaydi.txt 2>&1
```

Koşum **7,5 dakika** sürdü (2026-10-16 02:11-02:18, tek süreç, başka Ollama isteği yok). Çıktıyı `| tee` ile değil `>` ile yönlendirin ve `-u` kullanın.

Yardımcı keşif betikleri (tek isteklik, ucuz):

```bash
python kesif.py         # istek/cevap alanlarını dökümeler -> cikti/kesif.txt
python kesif_dongu.py   # araç mesajının üç biçimini karşılaştırır -> cikti/kesif-dongu.txt
```

## Ölçülenler (bu makinede, CPU)

| Deneme | Sonuç |
| --- | --- |
| A) sabit hat | arama 10,79 sn (soğuk `bge-m3`) + üretim 68,03 sn; girdi 1.926, çıktı 120 token |
| B) ajan, aynı soru | 2 tur, 95,2 sn; girdi 2.623, çıktı 336; ikinci turun cevabı `num_predict=300`de **kesildi** (`done_reason=length`) |
| B2) iki bilgi isteyen soru | 2 tur, 61,8 sn; cevap **İngilizce** geldi, tek `viki_ara` çağrısıyla yetindi |
| C) uzunluk + birim dönüşümü | 2 tur, 12,1 sn; **yanlış araç** seçildi, sonuçtan "3600 metredir" uyduruldu |
| D) kapsam dışı soru | 2 tur, 11,9 sn; araç eşik metnini döndürdü, model 0,496 sayısını kullanıcıya sızdırdı |
| D2) `tool_choice="required"` | 2 tur, 61,8 sn — alanın etkisi ayrı ölçülemedi (aşağıya bakın) |
| E) katalog gideri | 0 araç 73 tok → 1 araç 237 (**+164**) → 2 araç 346 (**+273**) |
| F) `tool_choice` | alan yok / `auto` / `required` / çöp değer: **dördü de HTTP 200 ve araç çağırdı**. Test ayırt edici değildi (soru zaten araç çağrıştırıyordu); geçersiz değerin reddedilmemesi "sessiz yok sayma"yı destekler ama kanıtlamaz |
| G) `format: "json"` + `tools` | HTTP 200, ama **`tool_calls` alanı yok**: araç çağrısı `content` içinde JSON **metni** olarak döndü |
| H) `tool_name` yok | B ile birebir aynı girdi (2.623 tok), aynı 2 tur; döngü bozulmadı |

Önbellek ayrıntısı: B'nin ikinci turu 2.277 token okudu, yalnız **363'ü** önbellekten geldi; kalan ~1.914 token 43,7 tok/sn ile yeniden okundu — bu bant `cikarim-olcu` ölçümündeki 43,9-45,9 tok/sn değeriyle çakışıyor.

## Bilinen kusur (bilerek düzeltilmedi)

`birim_donustur()` içindeki boyut kontrolü `BİRİMLER[kaynak] * BİRİMLER[hedef] <= 0` biçiminde yazıldı; faktörler pozitif olduğu için koşul hiçbir zaman çalışmıyor ve süre↔uzunluk geçişleri reddedilmiyor. C senaryosundaki "3600 metre" cevabının yarısı bu kusurdan geldi. Kayıt bu hâliyle alındığı için kod değiştirilmedi, satırın üstüne not düşüldü. Düzeltmek isteyen `BİRİMLER`i iki kümeye ayırıp küme eşitliğini kontrol etsin.

## Notlar

- **Aralıksız tekrar koşmayın:** Wikimedia aynı gün içindeki art arda tam korpus çekimlerinde `HTTP 429` döndürmüştü (`olc.py` koşumunda yaşandı); bu betik korpusu `cikti/korpus.json`da sabitliyor.
- Vikipedi maddeleri **CC BY-SA**; metinleri yeniden kullanırken kaynak göstermek zorunlu.
- Küçük modelle ölçüldü: `qwen2.5:3b-instruct-q4_K_M`, `ollama show` çıktısında `capabilities: completion, tools`. Araç seçim hataları bu kapasitenin davranışıdır, bulut modelleriyle tekrarlanmadı.
- `tool_choice` Ollama'nın yerel `/api/chat` belgelemesinde **yok**; OpenAI ve Anthropic uyumluluk sayfaları "not supported" diyor. Kod bunu varsaymıyor, sunucuya soruyor.
