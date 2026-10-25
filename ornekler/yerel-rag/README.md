# Yerel RAG örneği — Bulut Kargo destek asistanı

Ollama üzerinde uçtan uca çalışan minimal bir RAG boru hattı:

1. **bge-m3** ile belge ve soru vektörleştirme (`/api/embeddings`)
2. Kosinüs benzerliğiyle en ilgili 2 belgeyi getirme
3. Belgeleri bağlama ekleyip **qwen2.5:3b** ile cevap üretme (`/api/chat`)
4. Getirim testi (hit@1/hit@3) ve kapsam dışı soru testi

## Gereksinimler

- Çalışır durumda bir Ollama sunucusu: `http://127.0.0.1:11434`
- İki model: `ollama pull bge-m3` ve `ollama pull qwen2.5:3b-instruct-q4_K_M`
- Harici Python paketi **gerekmez** (yalnızca standart kütüphane)

## Çalıştırma

```bash
python rag.py                     # tüm demo: indeks + 3 soru + iki test
python rag.py --soru "iade süresi?"   # tek soru
python rag.py --test              # yalnızca getirim testi
```

## Belgeler

`BELGELER` listesi kurgusal "Bulut Kargo A.Ş." politikalarını içerir; kendi
belgelerinizle denemek için listeyi değiştirmeniz yeterli. Gerçek projelerde
belgeler dosyadan okunur ve parçalara bölünür — bu örnekte öğretim amaçlı
olarak her belge tek parçadır.

Sayfası: `src/content/docs/ornekler/yerel-rag.mdx`
