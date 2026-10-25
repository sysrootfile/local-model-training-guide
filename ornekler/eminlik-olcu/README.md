# Eminlik ve kalibrasyon ölçüm kafesi

Bu kafe, sitenin *Eminlik ve kalibrasyon* kullanım sayfasına kaynak olmak için
yazıldı: sayfa [`src/content/docs/kullanim/eminlik-ve-kalibrasyon.md`](../../src/content/docs/kullanim/eminlik-ve-kalibrasyon.md)
adresinde yayımlandı ve aşağıdaki tamamlanmış kayıtlardan başkasını kullanmaz.
İki aşamada koşuldu: önce **A + H sözleşme probu**
(`logprobs` alanının Ollama'da fiilen ne ürettiği ve tekrarlanabilirliği), sonra
**B–G ölçüm kolları** (cevap-harf olasılığı, sıcaklık, serbest cevap logprobu,
öz-tutarlılık, semantik kümeleme, sözlü güven).

## Koşum

```bash
# A + H sözleşme probu: 27 çıkarım isteği (+1 sürüm sorgusu), 34 sn
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eminlik.py --kol a > cikti/prob.txt 2>&1
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eminlik.py --kol h >> cikti/prob.txt 2>&1

# B-G tam koşum: 176 sohbet + 100 gomme istegi (276 toplam), 5 dk 2 sn (23:05:00 -> 23:10:02)
# Koşum sırasında başka Ollama isteği GÖNDERMEYİN.
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eminlik.py --kol olcum \
  > cikti/olcum.txt 2> cikti/olcum-err.txt

# G kolu tek başına (biçim düzeltmesinden sonra): 10 istek, 49 sn
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eminlik.py --kol g > cikti/g2.txt 2>&1

# duman: B(6 soru) + C/D/E/G(3 soru) + F, iki tekrar
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eminlik.py --kol olcum --duman > cikti/duman-bg.txt 2>&1
```

Yönlendirme doğrudan `>` ile yapılır (`| tee` bu projede uzun bir koşumu kaybetti),
`-u` olmadan çıktı tamponda kalır. Betik yalnız `http://127.0.0.1:11434` ile
konuşur; dışarıya istek atmaz.

## Hücreler

| Kod | Ölçtüğü |
| --- | --- |
| A1–A11 | `logprobs` / `top_logprobs` sözleşmesi: kayıt sayısı, `eval_count` farkı, `top_logprobs` sınırı (0–20), `/api/generate`, OpenAI ucu, `format=json`/şema bozucusu, Türkçe karakter baytları |
| H1–H4 | Aynı isteğin logprob tekrarı (T=0), tohumlu/tohumsuz, tek token ve soğuk/sıcak yükleme |
| B | 20 bilgi + 6 "bilinemez" çoktan seçmeli soruda cevap-harf kütlesi: `P(secilen)`, `P(altın)`, eşik taraması, seçilme harfi dağılımı |
| C | Aynı sorunun `P` değerinin T=0 / 0,7 / 1,0 ile değişip değişmediği (seed 1234) |
| D | Serbest (tek-tokene zorlamasız) cevabın ortalama logprobu ve kırpılmış entropisi |
| E | Öz-tutarlılık: soru başına 10 örnek, T=0,8; harf uyuşması ve çoğunluk doğruluğu |
| F | E'nin serbest metinlerinin bge-m3 kosinüs benzerliğiyle kümelenmesi ve semantik entropi (0,70 ve 0,80 eşiği) |
| G | Sözle bildirilen güven: `GUVEN:` etiketli 0–100 sayısının cevap doğruluğuyla ilişkisi |

## Kayıtlar

- `cikti/prob.txt` — A + H probu, 2026-10-17 22:09:25 → 22:09:59. **Sitedeki
  sözleşme satırları buradan alındı** (`top_logprobs must be between 0 and 20`,
  `eval_count 18 / logprob kaydı 17`, şema koşulunda ilk aday `'{\n'=0,9969`,
  H4 soğuk-sıcak sapması `maks |Δlogprob| 2,286e-01`).
- `cikti/duman.txt` — probun duman koşumu (22:07:35 → 22:08:13).
- `cikti/olcum.txt` — B–G tam koşumu, 23:05:00 → 23:10:02. **B–F sayıları
  buradan alındı.** Aynı koşumdaki G bloğu ilk (bozuk) araçla koşulmuştur;
  aşağıdaki "Bilinen sınırlar" maddesine bakın.
- `cikti/g2.txt` — G kolu düzeltilmiş ayrıştırıcıyla yeniden koşumu,
  23:12:27 → 23:13:16. **Sitedeki G sayıları bu logdan alındı**; `g.json` de bu
  koşumdandır.
- `cikti/duman-bg.txt` — B–G dumanı, 22:44:50 → 22:57:59. Makine bu ilk 10
  dakikada ağır rakip yük altındaydı (tek tokenlık istek 101 sn); **bu logun süre
  kolonları hiçbir yerde kullanılmadı**, içerik kolonları (seçilen harf, `P`,
  metinler) kullanıldı.
- `cikti/kontrol-b.txt` — B hanesi düzeltme sonrası kontrolü, 23:04:00 → 23:04:33.
- `cikti/{b,c,d,e,serbest,g}.json` — tam koşumun satır kayıtları (G için `g2.txt`
  koşumu).

Makine: AMD Ryzen 5 2600 (6/12), 15,9 GB RAM, Ollama 0,40,5,
`qwen2.5:3b-instruct-q4_K_M` ve `bge-m3` CPU'da. Altın cevaplar sitede zaten
belgelenmiş olgulardan elle yazıldı (sözlük boyutları, vektör boyutları, DPO
beta'sı, derleme boyutları, bağlam penceresi, `keep_alive`, fiyatlar); modelin
ezberinden gelen sayılar altın olarak kullanılmadı.

## Yöntem sapmaları

- **Kümeleme kosinüs eşiklidir, NLI değil.** Semantik entropinin özgür tanımı
  çift yönlü entailment ister; burada bge-m3 kosinüs benzerliği ≥ eşik kullanıldı.
- **Açgöz kümeleme kümenin İLK örneğiyle karşılaştırır**, ortalama vektörüyle
  veya tüm çiftlerle değil. Sıralamaya bağlı bir sapmadır.
- **Kırpılmış entropi bir alt sınırdır** (logdaki etiketi `kirpik entropi`).
  Yalnız `top_logprobs`daki 20 adayın yeniden normalize edilen dağılımından
  hesaplanır; 20'den uzun kuyruk görünmez.
- **Eşik taraması `P(secilen)` üzerinden yapılır.** `P(altın)` altın etiketi
  sızdırdığı için yalnız `[analiz]` satırlarındadır, eşik kurmaz.
- **G ayrıştırıcısı yalnız `GUVEN:` etiketini okur.** Etiket yoksa soru
  ortalamalara girmez ve ayrı sayılır. İlk koşumda etiket zorunlu değildi; model
  talimatı yankılayıp "1 ile 100 arasında tek bir tam sayı: 50" yazdı ve sayı
  yankıdan geldi. Bu yüzden `olcum.txt`'deki G bloğu geçersiz sayıldı ve G,
  `g2.txt` koşumuyla değiştirildi.
- **Talimat yankısı temizlenmedi**, F satırlarında `talimat yankisi N` olarak
  sayıldı ve bırakıldı (küme sayısını şişirdiği F2'de görünüyor).

## Ölçülmedi

- Tam sözlük entropisi (`top_logprobs` 20 ile sınırlı olduğundan erişilemiyor).
- Niceliklendirilmiş (Q4 vs Q8) modelde güven davranışı — yeni model indirmesi
  gerektirir, onaylanmadı.
- ECE, güven aralıkları, sıcaklık ölçekleme uydurması, risk-kapsama eğrisinin
  düzeltilmiş tahmincisi. N=20 ve N=6 için güven aralığı hesaplanmadı; oranlar
  nokta tahminidir.
- RAG bağlamı verildiğinde kalibrasyonun değişmesi, türetme (chain-of-thought)
  koşulunda `P` karşılaştırması, ajan döngüsünde eşik kullanımı.

## Bilinen sınırlar

- Tek model, tek makine, tek Ollama sürümü, tek soru seti (20 + 6).
- **B kolu geçersizlik kapısını tetikledi:** 20 soruda seçilen harfin 16'sı C
  (A:0 B:3 C:16 D:1), doğruluk 6/20. Bu durumda `P(secilen)` konum yanılgısının
  ölçüsüdür, bilginin değil; eşik/risk tablosu ayırıcı sayılmaz. Aynı soruların
  içerik kontrolü D ve G kollarındadır.
- E kolu T=0,8'de çeşitlilik üretmedi (10/10 soruda uyuşma 1,00), bu yüzden F'nin
  semantik entropisi 6 soruda sıfır kümesine düştü.
- Soğuk/sıcak yükleme logprobu kaydırıyor (H4) ve iki ayrı koşum arasında da
  kayma görüldü (`kontrol-b` B1 `P(C)` 0,9634 vs `olcum` 0,9613); kaymanın
  nedeni (toplama yolu, önbellek durumu, makine yükü) ayırt eden bir kol
  yazılmadı.
- B–G süreleri `>` yönlendirmeli tek koşumdan alınmıştır; eşzamanlı Ollama
  trafiği veya rakip CPU yükü olursa süreler anlamsızlaşır (duman koşumunda
  görüldü).
- **Maliyet birimi:** `num_predict=1` + `top_logprobs=20` isteği taze (~100
  tokenlık) istemle 2,1–2,9 sn sürüyor (prefill baskın); aynı istem hemen
  yeniden koşulursa 0,10–0,15 sn'ye düşüyor (istem önbelleği). `olcum.txt`
  B1–B6 satırları `kontrol-b.txt`'ten sıcak önbellekle 0,10–0,15 sn, B7–B26
  ise 2,09–2,97 sn ölçtü. Kafesin ~5 dk sürmesi bu birimden gelir.
