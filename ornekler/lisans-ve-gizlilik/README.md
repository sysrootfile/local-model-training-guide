# Lisans ve kişisel veri denetimi

Sitenin [Lisans, Kişisel Veri ve Model Kartı](../../src/content/docs/kullanim/lisans-ve-model-karti.md)
sayfasındaki sayıların geldiği kafe. İki betik var ve ikisi de **çıkarım isteği
göndermez, ağa çıkmaz**: biri lisans zincirini, diğeri kişisel veri tarayıcısını
ölçer. Sayfanın konusu tam olarak bu ikisi: yayınlamadan önce "iznim var mı" ve
"içinde başkasının verisi var mı".

## Koşum

```bash
# 1) lisans envanteri — Ollama çalışıyor olmalı (yalnızca /api/tags + `ollama show`)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py > cikti/lisans-envanter.txt 2>&1

# aynı bölümün Ollama'sız hâli (yalnız depo sayımı, ~1 sn)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py --depo > cikti/depo-sayimi.txt 2>&1

# 2) kişisel veri denetimi — üç kol birden (~52 sn, CPU, tek süreç)
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u pii_denetim.py --kol hepsi > cikti/pii-kaydi.txt 2>&1

# tek kol: a=kalibrasyon, b=depo taraması, c=ayraç silme
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u pii_denetim.py --kol a
```

Yönlendirme doğrudan `>` ile yapılır (`| tee` bu projede uzun bir koşumu kaybetti),
`-u` olmadan çıktı tamponda kalır.

## Ne ölçülüyor

| Betik / kol | Ölçtüğü |
| --- | --- |
| `lisans_envanter.py` Bölüm 1 | Yerel Ollama yığını: her modelin Modelfile `LICENSE` alanının başlığı, bayt/satır boyu, kısıt maddeleri (etiketlenmiş), şablon artığı (`[year]`, `[fullname]`), alıntı cümleleri ve `SYSTEM` satırı |
| `lisans_envanter.py` Bölüm 2 | Depodaki lisans sözcüğü sayımı (`ornekler/**` + `src/content/docs/**`, py/md/mdx) ve Örnek 6'nın Vikipedi atıf satırı, Örnek 3'ün veri kaynağı satırları |
| `pii_denetim.py` Kol A | Elle yazılmış 30 sentetik Türkçe vaka; üç tür etiket: POZİTİF (görülmeli), KUYRUK (işaretlenmemeli), KÖR NOKTA (kişisel veri ama kapsam dışı). Çıktı: tutma oranı, yanlış pozitif, kapsam dışı kaçırma |
| `pii_denetim.py` Kol B | Dört grupta vuruş sayımı: yayındaki sayfalar, örnek veri kümeleri, koşum günlükleri, betikler/README. Yalın `\d{11}` ile sağlamalı taramanın farkı + IBAN tarafında mod-97 ayrımı |
| `pii_denetim.py` Kol C | Rakam ayraçlarını (boşluk/nokta/tire) silip birleştirince: kalibrasyonda kaç kör nokta yakalamaya dönüyor, depoda kaç yeni aday/telefon vuruşu geliyor |

Denetlenen maskeleyici `ornekler/veri-temizleme/atolye.py` içinden **olduğu yerden**
yükleniyor (`atolye_yukle()`), yani kopyalanmış bir kural değil, sitede size
öğretilen aracın kendisi test ediliyor.

## Kendi kendini kirletmeme

Denetimler bu deponun üstünde koştuğu için iki özyineleme tuzağı var; ikisi de
betiklerin içinde kapatıldı ve logda satır olarak görünüyor:

- `lisans_envanter.py` **kendi `KISITLAR` anahtar sözcük listesini** sayardı; bu
  yüzden `ornekler/lisans-ve-gizlilik/` klasörünün tamamı (betikler + bu README)
  depo sayımının dışındadır.
- `pii_denetim.py` kendi çıktı dosyalarını sayardı — hem de yazıldığı sırada
  **yarım okunan** kendi logunu. Kol B taraması `ornekler/lisans-ve-gizlilik/cikti/`
  altındaki hiçbir dosyayı okumaz.

## Kayıtlar

- `cikti/lisans-envanter.txt` — **sayfadaki lisans tablosu buradan alındı.** Tam
  koşum 2026-10-17 14:22:37 → 14:22:38, üç model, `ollama show` başına ~0,09 sn.
- `cikti/pii-kaydi.txt` — **sayfadaki kişisel veri tabloları buradan alındı.**
  Üç kolun tek koşumu 2026-10-17 14:21:44 → 14:22:36; başlangıç/bitiş damgaları,
  grup toplamları ve koşum süreleri logda.
- `cikti/depo-sayimi.txt` — Ollama'sız bölüm 2 koşumu; lisans sayımını model
  yığınından bağımsız görmek için.
- Kalibrasyon (Kol A) sayıları her koşumda birebir aynı: tohum sabit, vaka
  listesi sabit. Depo taraması (Kol B) satırları ise **sayfa büyüdükçe oynar** —
  bu klasörün dışındaki her md/mdx/py dosyası taramanın konusu. Sayfadaki tablo,
  üstteki saat damgasıyla biten koşumun anlık görüntüsüdür; sayıyı yazdıktan
  sonra betiği yeniden koşarsanız aynı değeri geri vermelidir (sayfa metni
  uzarsa tabloyu yeniden koşumdan tazeleyin).

## Makine künyesi

AMD Ryzen 5 2600 (6/12), 15,9 GB RAM, Windows, proje `.venv` içindeki Python.
Ollama 0,40,4, adres `http://127.0.0.1:11434`. Denetlenen modeller:
`qwen2.5:3b-instruct-q4_K_M`, `bge-m3`, `nomic-embed-text`. Rastgelelik tohumu
`20261017` (Kol A'daki kimlik numaraları bu tohumla üretilir; aynı sürümle aynı
vakalar gelir).

## Bilinen sınırlar

- **Kalibrasyon kümesi 30 elle yazılmış vaka.** Kör nokta sayıları tarayıcının
  *kapsamını* gösterir, gerçek Türkçe metindeki sıklığını göstermez; kesinlik
  aralığı hesaplanmadı (ÖLÇÜLMEDİ).
- POZİTİF vakaların kimlik numaraları sağlama fonksiyonuyla üretildi: 12/12 tutma
  oranı doğrulayıcının kendi doğruluğunu değil, regex ile sağlama arasındaki
  davranışı ölçer.
- Depo taraması **bu projeye özgü**; kütlenin büyük kısmı sentetik/üretilik metin.
- Lisans envanteri bu makinedeki üç paketi kapsar. Başka etiket, başka sürüm,
  başka dağıtım kanalı farklı bir lisans alanı taşıyabilir.
- Dış kaynaklı iddialar (Hugging Face kart alanları, lisans metinleri) 17 Ekim
  2026 tarihli anlık görüntüdür. **Hukuki değerlendirme yapılmadı;** KVKK madde
  metinleri bu denetimde doğrulanmadı.

## Bu kafeden çıkan düzeltme

Kol B, maskeleyicide değil **boru hattında** bir hata buldu: `atolye.py`
normalizasyonu üç alana (`talimat`, `giris`, `cikti`) uyguluyor, maskelemeyi
ikisine uyguluyordu. SFT yazıcısı `giris` alanını kullanıcı mesajına gömdüğü için
yayınlanmış çıktı maskelenmemiş bir e-posta taşıyordu. Düzeltme sonrası Örnek 2
koşumu yeniden alındı (`ornekler/veri-temizleme/cikti/`); önceki çıktı
`temiz_veri-eski.jsonl` ve `rapor-eski.json` adıyla korundu. Ayrıntı: sayfanın
"Hattımızda Bulduğumuz Gerçek Hata" bölümü ve
[Örnek 2 sayfası](../../src/content/docs/ornekler/veri-temizleme.mdx).
