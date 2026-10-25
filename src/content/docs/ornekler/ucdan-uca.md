---
title: "Uçtan Uca Tek Hat: Veriden Ollama'ya Yürümek"
description: "Sıfırdan bir Türkçe asistanın beş istasyonunu tek bir hatta yürüyen sayfa: veri toplama, temizleme, CPU'da eğitim, değerlendirme ve Ollama'da çalıştırma. Her istasyonda hangi betiğin koştuğu, sayının hangi kayıt dosyasında durduğu, hangi kademe olduğunu ve hattın nerede koptuğunu gösterir; sayıları tekrar yazmaz."
dogrulama: 2026-10-19
---

Sitedeki diğer örnekler **konu konu** ilerliyor: bir sayfa veriyi, bir sayfa temizlemeyi, bir sayfa
eğitimi, bir sayfa değerlendirmeyi anlatıyor. Okuyucu beş sayfayı kendisi dikiyor. Bu sayfa o dikişi
açıkça kurar: **tek bir hat, beş istasyon, sırayla.**

Bu hat bu makinede gerçekten yüründü — ama iki yerde koptu. Sayfanın asıl işi yürünen kısmı göstermek
değil, **kopmanın nerede ve neden olduğunu** okuyucunun eline vermektir.

## Bu Sayfada Neden Sayı Yok

[Kapsam Haritası](/kaynaklar/kapsam-haritasi/) kuralı: aynı birimi iki sayfa söylüyorsa biri yanlış,
ikisi de kaynaktır. Saniyenin adresi [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/), hit@k/MRR'nin adresi
[Gömme Modeli Eğitmek](/rag/gomme-egitimi/) ve RAG sayfaları, eşzamanlı isteğin adresi
[Eşzamanlılık](/kullanim/eszamanlilik/). Bu sayfa o rakamları **yeniden yazmaz**; hangi kayıt dosyasında
durduklarını ve iddianın hangi kademe olduğunu taşır. Bu sayfanın kendisi üç şeyin tek kaynağıdır:
**istasyon sırası, kademe etiketi, kayıt dosyasının adı.**

## Hattın Beş İstasyonu

| # | İstasyon | Bu makinede koşan betik | Kayıt | Kademe |
| --- | --- | --- | --- | --- |
| 1 | Veri toplamak | `ornekler/turkce-asistan/hazirla.py` | `cikti/rapor.json`, `cikti/egitim.jsonl`, `cikti/test.jsonl` | 2 — tek koşum |
| 2 | Veriyi temizlemek | `ornekler/veri-temizleme/atolye.py` | `cikti/rapor.json`, `cikti/temiz_veri.jsonl`, `calistirma-kaydi.txt` + `-eski`/`-oncesi` çiftleri | 2 — tek ölçüm, bir düzeltme çifti |
| 3 | Modeli eğitmek | `ornekler/gomme-egitimi/gomme_egit.py --kol b/c/d`, `kos.py` | `cikti/kol-b.txt` `kol-c.txt` `kol-d.txt`, `kos-iz.txt`, `cikti/lora-adapter/` | 3 — aynı konfigürasyon iki tohumda |
| 4 | Değerlendirmek | `gomme_egit.py` içindeki sabit test kümesi + `ornekler/yerel-rag/olc.py`, `ornekler/viki-rag/olc.py` | `kol-*.txt`, `yerel-rag/cikti/olc-kaydi-127.txt`, `viki-rag/cikti/olc-kaydi-127.txt` | 2 — iki kayıt ama aynı koşulda değil |
| 5 | Ollama'da çalıştırmak | `ornekler/cikarim-olcu/*`, `ornekler/eszamanli-olcu/eszamanli_olcu.py`, `gomme_egit.py`'nin `/api/embed` kolu | `eszamanli-kaydi-*.txt`, `kol-a.txt` | 3 — üç sunucu ayarı |

:::note[İki uç, tek hat değil]
Birinci istasyonla üçüncü istasyon **aynı veriyi taşımıyor.** İstasyon 1'in çıktısı sohbet eğitimi
içindir, istasyon 3'ün girdisi gömme eğitimi için yazılmış ayrı bir Türkçe korpustur. Bu, hattın
birinci dikiş yeri ve aşağıda "Nerede Kırılır" başlığında duruyor.
:::

## 1) Veri Toplamak

**Koşan:** `hazirla.py`, Hugging Face'teki Türkçe bir SFT veri setini canlı indirip satır satırdan
geçiren betik. **Baktığınız şey:** `cikti/rapor.json` — ham kayıt sayısı, elenen sayısı ve **elenme
sebebinin metni**, eğitim/test ayrımı, `seed`. Sayılar [Örnek 3: Türkçe Sohbet Asistanı](/ornekler/turkce-asistan/)
sayfasında durur; burada olan şey o kayıtların varlığı ve nedenidir.

**Neden rapor.json yetmez:** çünkü indirdiğiniz veri bugün aynı ad altında değişmiş olabilir. İstasyon
1'in çıktısı model değil **kanıt zinciridir**: hangi dataset, hangi sürüm, hangi tohum, hangi filtre.
[Lisans ve Model Kartı](/kullanim/lisans-ve-model-karti/) sayfasının kişisel veri taraması aynı
dosyanın ikinci işidir; temizlemeden önce neyin girdiğini bilmezseniz eğitimden sonra bilemezsiniz.

**İstasyonun diğer biçimi:** istasyon 3'ün korpusu indirilmedi, betiğin içine **elle yazıldı**
(parçalar, sorular, eğitim çiftleri tek dosyada). Bu kusur değil, bilinçli bir tercih: sabit küçük bir
test kümesi olmadan "eğitim işe yaradı mı" sorusu sorulamaz. El yazımı kümenin bedeli şudur: sonuç o
korpustaki davranıştır, modelin genel kapasitesi değil.

**Tuzak:** veri bulmayı veri toplamak sanmak. Nereden toplanacağını anlatan sayfa:
[Veri Nereden Bulunur](/veri/veri-nereden-bulunur/), biçimler: [Veri Formatları](/veri/veri-formatlari/).

## 2) Veriyi Temizlemek

**Koşan:** `atolye.py` — streaming ile çekilmiş Türkçe talimat verisi üzerinde yakın-tekrar eleme
(MinHash + LSH), uzunluk/nitelik filtresi, alan normalizasyonu ve kişisel veri maskelemesi.
**Baktığınız şey:** `cikti/rapor.json` artı `calistirma-kaydi.txt` — betiğin stdout'u, yani **hangi
filtrenin kaç satır yuttuğu**.

Bu istasyonun diskte iki kaydı var, ama bunlar **bir tekrar değil**: `-eski`/`-oncesi` sonekli
dosyalar, düzeltme öncesi ve sonrasını tutuyor. Betiğin kendi çıktısında bir sızıntı bulundu —
normalizasyon üç alana uygulanıyordu da kişisel veri maskelemesi yalnız ikisine; SFT yazıcısı
maskelenmemiş alanı kullanıcı mesajına gömdüğü için **maskelenmiş bir boru hattının yayınladığı
satırda** maskelenmemiş bir e-posta kalıyordu. Öncesi/sonrası satırı ve satır numarası
[Örnek 2](/ornekler/veri-temizleme/) sayfasında durur.

Hattın buradaki dersi kademe ile ilgili: bir temizleme adımının ikinci kaydı, o adımı tekrarlanabilir
yapmaz — **kanıtlanabilir** yapar. İki sayı aynı çıkarsa kademe 3'e çıkarsınız; biri diğerini
düzeltiyse elinizde kalan şey, düzeltmenin hangi kayıtta yaşadığıdır.

**Neden ayrı istasyon:** çünkü istasyon 1'in filtresi ile istasyon 2'nin filtresi farklı iş yapar.
Biri "bu satır eğitim için yeterli mi"ye, öbürü "bu satır doğru mu"ya bakar. İkisini tek betiğe
yığan projede, hangi kuralın kaç veri öldürdüğünü kimse söyleyemez.

**Derinleşme:** [Veri Temizleme](/veri/veri-temizleme/) kavram sayfası, yürünmüş hâli
[Örnek 2: Veri Temizleme Atölyesi](/ornekler/veri-temizleme/).

## 3) Modeli Eğitmek — Bu Makinede Koşan Tek Eğitim

:::caution[Seçim: neden sohbet değil de gömme modeli?]
Sohbet eğitimi (LoRA/QLoRA) GPU ister; bu makinede çalıştırılmadı ve o kol aşağıdaki kutuda duruyor.
GPU'suz bir makinede **gerçekten koşabilen** eğitim yolu gömme modeli eğitimidir: küçük bir taban
model, CPU'da adım süresi ölçülebilir bir döngü, ve sonucu ölçülebilir bir test kümesi. Bu hat o
kolundan yürünür.
:::

**Koşan:** `gomme_egit.py` — dört kol: sıradan atış (A), tam eğitim (B), LoRA (C), batch tavanı (D).
**Baktığınız şey:** `kol-b.txt`, `kol-c.txt`, `kol-d.txt` ve A→B→C'yi tek seferde koşan `kos.py`'nin
ızı `kos-iz.txt`; eğitilen adaptörün kendisi `cikti/lora-adapter/` altında.

Hattın en öğretici satırı burada: LoRA **hız ve disk tarafında gerçek kazandırdı** (eğitilebilir
parametre oranı, adım süresi, diske yazılan adaptörün taban ağırlığa karşı boyutu), **sıralama
tarafında kıpırdatmadı** — sabit test kümesinde hit@1 eğitim öncesi ve sonrasında aynı kaldı. Kayıp
eğrisi düşerken rütbenin düşmemesi, bu sitenin "eğitim işe yaradı" cümlesine temkinli bakmasının
asıl sebebidir. Sayıların tamamı ve altı eğitim kolunun dökümü
[Gömme Modeli Eğitmek](/rag/gomme-egitimi/) sayfasında.

Bu istasyon kademe 3'tür, ama sebebi altı kolun tekrarı değil: kol farklıları birer **karşılaştırma**,
tekrar değil. Aynı konfigürasyonun tekrarı ancak ikinci bir tohumla koşan koldan gelir, ve o tekrar
bir isabet oranını değiştirmedi — değiştirdiği şey o oranın **içinde hangi soruların** durduğu oldu.

**Okuma bilgesi:** bir eğitim kolunu okurken bakılacak üç katman orada tanımlı — getiri (hit@1/hit@3/
MRR), ayrışma (doğru parçanın en düşük skoru ile en iyi yanlışın skoru farkı), maliyet (adım süresi,
RSS, diske yazılan MB). Üçünden birini yazıp diğerini yazmayan sonuç tablosu eksik tablodur.

**Kaybedilen kayıt:** bu kafeste `| tee` yerine doğrudan `>` yönlendirmesi kullanılır; bir ara denemede
`tee` hattı uzun bir koşumun çıktısını düşürdü ve `-u` bayrağı olmadan da betik çıktısı tamponda kaldı.
Betiklerin README'sinde yazılı olmasının sebebi bir tercih değil bir kazadır.

## 4) Değerlendirmek

**Koşan:** istasyon 3'ün kendi içindeki sabit test kümesi (eğitim ÖNCE/SONRA aynı ölçümle yazılır),
ayrıca `yerel-rag/olc.py` ve `viki-rag/olc.py` eşik bandı ve sıralama metrikleri için.

**Baktığınız şey:** her `olc-kaydi-127.txt` satırında **hangi adresin** kullanıldığı. Bu sitede
`localhost` yerine `127.0.0.1` geçişi tek başına ölçüm sonucu değiştirdi; o yüzden değerlendirme
kayıtlarının iki sürümü birden diskte duruyor (eski adres ve yeni adres). Bir değerlendirme sayfasının
kendi başına doğrulanması budur.

**İki ölçüm sınırı:**
1. Sabit test kümesi **küçüktür** ve güven aralığı hesaplanmadı. Aynı isabet oranının iki farklı
   tohumda **farklı sorular** tarafından üretilmesi ölçülmüş bir durumdur: oran aynı, içindeki
   doğru-yanlış deseni farklı. Tohum/tekrar tarafı: [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/).
2. Değerlendirme, geri-getirmenin **kesintiye uğradığını** yakalayabilir: aradığınız parça indeksleme
   sınırının dışında kaldıysa model değil hattın kendisi kaybeder. Parçalama ve kesinti:
   [Parçalama ve Hibrit Arama](/rag/parcalama-ve-hibrit-arama/).

Üçüncü not istasyonun kademesine ait: diskteki iki kayıt bir **bant** oluşturmaz. Aralarındaki fark
tekrardan değil adres değişiminden geliyor, yani ikisi aynı koşulun iki ölçümü değil, aynı hattın iki
farklı koşuludur. Tabloda bu yüzden kademe 2 yazıyor.

Metriklerin tanımı: [RAG Değerlendirmesi](/rag/rag-degerlendirme/), [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).

## 5) Ollama'da Çalıştırmak

**Koşan:** hat burada eğitilen gömme modellerini **Ollama'nın kendi modeliyle** karşılaştırır
(`/api/embed`, yalnız `127.0.0.1`), sonra aynı sunucuda sohbet modeliyle gecikme ve eşzamanlılık
ölçülür. **Baktığınız şey:** `kol-a.txt` (Ollama üzerinden gömme üretimi), `eszamanli-kaydi-*.txt`
(üç sunucu ayarı), `ornekler/cikarim-olcu/` çıktıları (faz dökümü: yükleme, ön-yükleme, çözme).

Bu istasyonun ölçülmüş üç dersi var, hepsi ilgili sayfada: tek isteğin fazları birbirinden bağımsız
değildir; sunucuda yuva sayısı kadar istek gerçekten yarışır, taşanı sırada bekler; ve bellek bedeli
yuva başına **eşit adımlarla** artmaz. Sayılar: [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/),
[Eşzamanlılık](/kullanim/eszamanlilik/). Sunucu tarafı ayarların okunması:
[Çıkarım Parametreleri](/kullanim/cikarim-parametreleri/).

## Yürünmemiş Kol: Sohbet Asistanının GPU Adımları

:::danger[Bu kol bu makinede hiç koşmadı]
`hazirla.py` gerçekten koştu; `egitim.py` (QLoRA) ve `sor.py` (öncesi/sonrası karşılaştırma) GPU
istediği için **koşulmadı**. Bu sayfada ve ilgili örnek sayfasında o adımlara ait tek bir loss eğrisi,
tek bir cevap metni ya da tek bir karşılaştırma satırı **gerçek çalıştırma olarak sunulmaz**;
`sor.py`'nın örnek çıktısı sayfanın kendi deyişiyle *temsilîdir*. Betikler 2026 itibarıyla güncel
Unsloth/TRL API'lerine göre yazılmıştır (kademe 1) ve ilk gerçek koşumda sürüm farkı düzeltmesi
gerektirebilir.
:::

Kural gereği bu proje para harcayan kol koşmaz: [Kapsam Haritası](/kaynaklar/kapsam-haritasi/) kural 1.
Yani o kol ya kendi GPU'nuzda ya da kiralık kartla yürünür; plan ve saat ücretleri
[Bulut GPU Seçenekleri](/donanim/bulut-secenekleri/) sayfasında, kademe 1 olarak durur. Eğitilen bir
LoRA'nın GGUF'a oradan Ollama'ya taşınması da dahil: [LoRA Birleştirme](/kullanim/lora-birlestirme/),
[Nicemleme](/kullanim/quantization/), [Ollama](/kullanim/ollama/).

## Hattı Kendi Makinenizde Yürüme Sırası

Aşağıdaki iki blok **ilgili kafesin kendi README'sinden olduğu gibi alınmıştır** ve bu makinede bu
biçimde koşulmuştur; yeni bir komut burada üretilmedi.

```bash
# kaynak: ornekler/gomme-egitimi/README.md — tek kol koşumu
PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u gomme_egit.py --kol c  > cikti/kol-c.txt 2>&1
```

```bash
# kaynak: ornekler/turkce-asistan/README.md — veri hazırlamanın hızlı denemesi (CPU)
python hazirla.py --limit 200
```

Sıra önemli: **duman önce, tam koşum sonra.** Tek kol, tek tekrar, uçtan uca bir kayıt ürettiğini
gördükten sonra tam koşuma geçin. Koşum sırasında aynı sunucuya başka istek göndermeyin; göndermiş
olabileceğinizi düşünüyorsanız koşumdan önce ve sonra `GET /api/ps` ile bellekte ne olduğunu yoklayın.
Bu kuralın bir bedeli vardı: eşzamanlılık kafesinde **sunucu ayarı doğru, tüm istekler hatasızken**
pencereye giren yabancı istekler yüzünden bir koşum elendi ve tek bir sayısı yayımlanmadı.

## Nerede Kırılır

- **Veri dikişi:** sohbet hattının verisi indirilmiş, gömme hattının verisi elle yazılmış. Tek bir
  veri kümesi beş istasyonu boydan boya geçmedi; geçseydi bu sayfa çok daha kısa olurdu.
- **Eğitim dikişi:** bu makinede koşan eğitim yalnız gömme modelininkidir. Dil modeli eğitimi kademe
  0-1'de duruyor (yukarıdaki kutu).
- **Değerlendirme dikişi:** sabit ve küçük test kümesi; güven aralığı yok. Ölçülen "bu korpustaki
  davranış", genelleme değil.
- **Çalıştırma dikişi:** Ollama ölçümleri **hazır modellerle** yapıldı. Bu hattın ürettiği adaptör
  GGUF'a dönüştürülüp `ollama create` ile sunucuya alınmadı; yani istasyon 5, istasyon 3'ün ürününü
  değil emsalinin ürününü çalıştırıyor.

## Ölçülmedi

- Bu sayfanın okuyucuya hattı gerçekten yürütüp yürütmediği **ölçülmedi**; ölçülen tek şey metnin
  render edildiği.
- Hattın **toplam yerel maliyeti** bu sayfada yok. İstasyonların kendi süreleri ilgili sayfalarda
  ölçülmüş durumda, ama beşinin toplamı bir **toplama** olurdu; toplama ölçüm değildir.
- Gömme LoRA'sının sıralamayı kıpırdatmamasının **büyük korpuslarda da** geçerli olup olmadığı
  ölçülmedi.
- El yazımı test kümesinin kaç soru/parça olduğu burada yazmıyor (tek kaynak kuralı); o sayı kafesin
  kendi sayfasında.
- İstasyon 5'te ölçülen `bge-m3` eşzamanlı davranışı: bu eksende **koşulmadı**, eşzamanlılık ölçümü
  sohbet modeliyle yapıldı.

## İlgili Sayfalar

- [Kapsam Haritası](/kaynaklar/kapsam-haritasi/) — kademelerin ve kabul kurallarının kaynağı; bu sayfa o haritanın "bir sonraki eksen" satırının yürünmüş hâlidir.
- [Gömme Modeli Eğitmek](/rag/gomme-egitimi/) — istasyon 3 ve 4'un sayı kaynağı.
- [Örnek 3: Türkçe Sohbet Asistanı](/ornekler/turkce-asistan/) — yürünmemiş kolun betikleri.
- [Adım Adım Eğitim](/llm/adim-adim-egitim/) — hattın kavramsal karşılığı.
- [Yerel RAG](/ornekler/yerel-rag/) ve [Viki RAG](/ornekler/viki-rag/) — eğitimsiz ama uçtan uca ölçülmüş bir diğer hat.

## Kaynaklar ve İleri Okuma

- [Sentence Transformers — Training Overview](https://sbert.net/docs/sentence_transformer/training_overview.html) — kayıp seçimi ve eğitim döngüsünün resmî anlatımı. (Son okuma: 2026-10.)
- [Sentence-BERT (arXiv 1908.10084)](https://arxiv.org/abs/1908.10084) — çiftli/cümleli sıralama kaybının orijinal tanımı. (Son okuma: 2026-10.)
- [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) — bu hatta eğitilen taban modelin kartı. (Son okuma: 2026-10.)
