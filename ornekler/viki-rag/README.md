# Örnek 6: Vikipedi'den Türkçe RAG

İstanbul toplu ulaşımı üzerine **yerel RAG asistanı**. Örnek 5'ten (`yerel-rag/rag.py`) iki farkla ayrılır:

1. **Veri yükleme:** Belgeler elle yazılmaz; çalışma anında Türkçe Vikipedi API'sinden indirilir (8 madde, ~100+ parça).
2. **Parçalama:** Uzun maddeler paragraf tabanlı ~800 karakterlik parçalara bölünür, aralarında bir paragraf örtüşme kalır.

## Gereksinimler

- İnternet bağlantısı (korpus her çalıştırmada Vikipedi'den çekilir)
- Çalışır bir Ollama sunucusu (`http://127.0.0.1:11434`)
- Modeller:

```bash
ollama pull bge-m3
ollama pull qwen2.5:3b-instruct-q4_K_M
```

Harici Python paketi gerekmez — yalnızca standart kütüphane.

## Çalıştırma

```bash
python viki_rag.py                     # tüm demo: korpus + 2 soru + iki test
python viki_rag.py --soru "Marmaray kaç kilometre?"   # tek soru
python viki_rag.py --test              # yalnızca getirim testi
```

Ölçüm betikleri (aynı korpusu indirir, cevap üretmeden arama tarafını sayar):

```bash
python olc.py                          # bge-m3 + nomic-embed-text bant karşılaştırması
python olc.py --model bge-m3           # tek model (daha hızlı)
python hibrit.py                       # vektör / BM25 / RRF hibrit yarıştırmalı arama
```

- `olc.py` → `cikti/olc-kaydi.txt`: kapsam içi/kapsam dışı benzerlik bantları, ayırma payı ve `ZAYIF_ESIK` değerinin bu korpusta geçerli olup olmadığı.
- `hibrit.py` → `cikti/hibrit-kaydi.txt`: üç arama yönteminin hit@1/hit@4 karşılaştırması. Gömme vektörlerini `cikti/vektor-indeks.json.gz` içine yazar; ikinci çalıştırma vektörleştirmeyi atlar (`cikti/hibrit-onbellek.txt`).
- İki betik de `nomic-embed-text` ister; kurulu değilse `olc.py` o modeli atlar (`ollama pull nomic-embed-text`).

## Ölçümler (bu makinede, CPU)

Aynı korpus iki kez koşuldu; tek fark Ollama adresiydi:

| Koşum | Adres | bge-m3 indeksi (125 parça) | nomic indeksi | Vektör sorgu gecikmesi |
| --- | --- | --- | --- | --- |
| 2026-10-15 | `http://localhost:11434` | 495,7 sn | 503,7 sn | 2,168 sn |
| 2026-10-16 | `http://127.0.0.1:11434` | **259,2 sn** | **158,6 sn** | **0,144 sn** |

- `olc.py`, bge-m3: kapsam içi **0,598-0,714**, kapsam dışı **0,321-0,485**, ayırma payı **+0,113** → Örnek 5'ten devralınan `0.35` bu korpusta **geçersiz**; önerilen **0,541**, koda **0,54** olarak işlendi. İki koşumun bantları, hit@k ve MRR satırları **birebir aynı** çıktı.
- `olc.py`, nomic-embed-text: kapsam dışı bandı **0,642-0,737** kapsam içini **içine alıyor** (ayırma **-0,112**) → bu modelle hiçbir eşik "bilmiyorum" dalı üretemez. Parafraz hit@1 ise **1,00** (bge-m3: 0,67).
- `hibrit.py` hit@1 (orijinal/parafraz/leksik): vektör **5/6 · 4/6 · 3/6**, BM25 **3/6 · 2/6 · 3/6**, RRF hibrit **4/6 · 2/6 · 2/6** — üç koşumda da aynı. BM25 tek başına bir soruda vektörün 14. sırasını 2'ye taşıdı; ama hibrit hiçbir kümede en iyi kol olamadı.
- BM25 sorgusu **0,0001 sn** (saf Python). Düşüşün tamamı Windows'ta `localhost` adının istek başına ~2 sn çözümülmesinden; `127.0.0.1` ile 0,00 sn.

## Notlar

- Vikipedi maddeleri **CC BY-SA** lisanslıdır; metinleri yeniden kullanırken kaynak göstermek zorunludur.
- **Aralıksız tekrar koşmayın:** aynı makineden ~15 dakikada 4 kez korpus indirildiğinde Wikimedia `HTTP 429 Too Many Requests` döndürdü. Betikler korpusu her çalıştırmada yeniden indirdiği için, gecikme ölçümü gibi tekrar eden işlerde ya bekleyin ya da `hibrit.py`'deki vektör önbelleğini kullanın.
- Korpus canlı bir kaynaktan geldiği için madde içerikleri zamanla değişir; aynı soruların benzerlik skorları birkaç yüzde puanı oynayabilir.
- Değerlendirme yöntemi (hit@k, eşik ayırma) [RAG Değerlendirmesi](../../src/content/docs/rag/rag-degerlendirme.md) sayfasında; daha küçük kardeş örnek [Örnek 5](../../src/content/docs/ornekler/yerel-rag.mdx)'te.
