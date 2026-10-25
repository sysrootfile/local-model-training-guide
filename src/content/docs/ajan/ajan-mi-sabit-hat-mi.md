---
title: "Ajan mı Sabit RAG Hattı mı?"
description: "RAG hattınızı bir ajan döngüsüne çevirmenin ne zaman değer, ne zaman gecikme ve belirsizlik getirdiğini karar merdiveni, dört soru ve ölçülmüş maliyet bantlarıyla karşılaştırıyoruz."
dogrulama: 2026-10-16
---

[RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/) sayfası "ince ayara gerek var mı?" sorusunu çözüyor. Bu sayfa bir alt soruyu çözüyor: **kurduğunuz RAG hattı akıllı mı olsun, sabit mi?** Örnek 6'nın hattı sabittir: her soruda gömme yapar, parça getirir, bağlamı modele okutur, cevap verir. Kararı model vermez; sizin yazdığınız kodun sırası verir. Bir **ajan döngüsü** ise kararı modele bırakır: aracı çağıracak mı, hangi argümanla, kaç tur? Bu fark ilk bakışta bir yetenek kazanımı gibi görünür; yerelde ölçüldüğünde bir kısmının gecikme ve belirsizlik ödemesi olduğu görülür. Bu sayfa, o ödemenin ne zaman yapılmaya değer olduğunu anlatır.

**Tek cümlelik cevap:** Araç dizisi belliyse ve her sorguda aynıysa sabit hat; hangi kaynağın çağrılacağına ya da ikinci bir geçişe gerek olup olmadığına modelin karar vermesi gerekiyorsa ajan döngüsü — ve geçişe kadar ajanın faturasını ölçün.

## Karar Merdiveni: Ajan En Üst Basamaktır

[RAG mi İnce Ayar mı?](/rag/rag-mi-ince-ayar-mi/) sayfasındaki merdivenin RAG üstü kısmını açarsak:

```text title="Aynı ilke, daha ince basamaklar"
5. Ajan döngüsü        → aracı kaç kez ve hangi sırayla çağıracağını model karar verir
4. Sabit çok araçlı    → iki aracı siz sıralarsınız, dizi sorgudan bağımsız
3. Sabit tek hat      → bir arama, bir üretim (Örnek 5 ve 6)
2. Anahtarlama (router)→ sorguyu sınıflandırıp HATTI seçiyorsunuz (kod, model değil)
1. Sadece prompt       → araç hiç yok
```

Merdivenin kuralı önceki sayfayla aynı: yukarı çıkmak için somut bir gerekçe gösterin. 2. basamak çoğu "ajan yapmalıyım" planının yerini doldurur — tek bir sınıflandırıcı sorgunun RAG mi yoksa araçsız cevap mı istediğini ayırır ve maliyeti tek bir ek geçiştir.

## Dört Soru

Cevabı dörtlüde de "evet" olan bir hattı sabit bırakmak kayıptır; birinde bile "hayır" varsa ajan haklıdır.

| Soru | "Sabit hat yeter" diyen cevap | "Ajan gerekir" diyen cevap |
| --- | --- | --- |
| **Araç dizisi sabit mi?** | Her sorguda önce arama, sonra cevap | Kaynak sorguya göre değişiyor (bazen arama, bazen hesaplama, bazen ikisi) |
| **Kaç geçiş gerektiği önceden biliniyor mu?** | Bir geçiş | "Gerekirse tekrar ara" kararı veriye bağlı |
| **Araç sonucunu yorumlamak gerekiyor mu?** | Sonuç doğrudan bağlama giriyor | Sonuç yetersizse farklı argümanla denemek gerekiyor |
| **Gecikme bütçesi kaç saniye?** | Saniyelerce tolerans | Kullanıcı bekleme süresini tur sayısıyla bilmiyor |

Üçüncü soru ajanın asıl gerekçesidir ve en az konuşulanıdır: sabit hat, getirdiği bağlam kötü olsa da onu okutmak zorundadır. Ajan, alt eşikli bir araç sonucunda soruyu yeniden kurup tekrar arayabilir. [Parçalama ve Hibrit Arama](/rag/parcalama-ve-hibrit-arama/) sayfasındaki "eşik altında ne yapılır" tartışmasının dinamik hâlidir bu.

## Ajanın Faturası: Üç Kalemin Üçü de Ölçülmüş

Ajan döngüsü bedavaya akıllanmaz. Bu makinede (AMD Ryzen 5 2600, CPU, `qwen2.5:3b-instruct-q4_K_M`) ölçülmüş üç gider kalemi:

**1. Araç tanımı, girdi tokenı olarak her turda ödenir.** Araç şemaları isteme gömülür ve girdi tokenı sayılır. OpenAI'nin resmî dokümanı bunu açık söyler: *"callable function definitions count against the model's context limit and are billed as input tokens"* ve araç sayısını/uzunluğunu azaltmayı ilk önlem olarak önerir. Anthropic'in dokümanı tek bir araç tanımının açıklaması için "en az 3-4 cümle" tavsiye eder — bu, istem başına eklenen metindir. Bu makinede ölçüldü: taban 73 tokenlık bir istem, bir araçla 237'ye, iki araçla 346'ya çıkıyor (**+273 token**), ve o 273 token döngünün her turunda baştan ödenir (`E` denemesi: [Ajan Ölçümü](/ajan/ajan-olcumu/)).

**2. Her tur, büyüyen mesaj listesini baştan okur.** Döngünün ikinci turu, ilk turun mesajlarını ve araç sonucunu tekrar taşır. Buradaki tek teselli istem önbelleğidir: [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) sayfasında aynı öneğin ikinci okunuşu **18,96 sn → 0,08 sn** olarak ölçüldü (687 token önbellekten geldi). Önbellek, değişmeyen önekin okunmasını tur başına ucuza getirir; ama araç sonucunun eklediği yeni tokenlar her turda yeniden ödenir. Döngüde tur başına kaç tokenın önbellekten kaçtığı Örnek 7'nin kaydında satır satır döküldü: [Ajan Ölçümü](/ajan/ajan-olcumu/).

**3. Cevaplamayacak sorular tur yakar.** "Şu an İstanbul'da yağmur yağıyor mu?" tipinde, hiçbir aracın yanıtlayamayacağı bir sorgu, model araç çağırmaya devam ederse tur sayacı kadar geçiş yakar. Sabit hatta bu durum tek bir eşik kontrolüdür ([Örnek 5](/ornekler/yerel-rag/) kapsam dışı testi); ajan döngüsünde çok turlu bir denemedir.

Tur başına duvar süresi, kaç tur yakıldığı ve `tool_choice` alanının bunu kısıp kısımadığı Örnek 7'nin betiğiyle bu makinede ölçüldü: [Ajan Ölçümü](/ajan/ajan-olcumu/).

## Melez Yol: Çoğu Projenin Gerçek Cevabı

Sabit hat ile ajan sahte bir ikilemdir; üretilen çözümün çoğu ikisini karıştırır:

- **Dışarıda sabit, içeride serbest.** Kullanıcının ilk sorusu sabit RAG hattından geçer (gecikme belli, alıntı garantili). Model "ikinci bir kaynak gerekli" derse ajan devreye girer. Böylece en kötü durum gecikmesi tek turluk hattan başlar.
- **Tur sayacı.** Döngüye bir üst sınır koyun (Örnek 7 `MAKS_TUR = 5` kullanıyor). Sayaçsız döngü, model araç çağırmayı bırakmadığında sonu olmayan bir maliyettir.
- **Zorla araç yerine yapılandırılmış çıktı.** Modelden "şu alanları doldur" biçiminde yapılandırılmış çıktı isteyip araç çağrısını siz tetiklersiniz; serbestlik sadece argüman metninde kalır. Bu, diziyi sabit tutup yorumlamayı modele bırakmanın en ucuz yoludur.

:::caution[Yereldeki küçük model, kapalı modelle aynı değil]
Ajan davranışı model kapasitesine bağlıdır. Araç çağırabilen modellerin listesi Ollama dokümanında ayrı, model kartlarında ayrı durur ve bu rehberde ölçtüğümüz `qwen2.5:3b-instruct-q4_K_M` küçük bir modeldir. Aynı döngü, araç seçiminde daha az hata yapan bir bulut modelinde kaç turda kapanır — burada ölçülmedi. Bu sayfadaki "tur yakan" davranışlarını bir kusur değil, kapasiteyle ölçeklenen bir gider olarak okuyun.
:::

## Sık Kararlar

| Durum | Öneri | Nedeni |
| --- | --- | --- |
| Kurumsal doküman soru-cevap, tek kaynak | Sabit hat (Örnek 5/6) | Gecikme ve alıntı denetimi sizde kalır |
| Arama + hesap makinesi + veritabanı var, sorgu hangisini istediği belli değil | Ajan, tur sayaçlı | Dizi sorgudan bağımsız olarak yazılamaz |
| Çok adımlı rapor üretimi, kullanıcı bekleyebilir | Ajan | Tur maliyeti, kazanılan doğruluk karşısında ikinci sırada |
| Anlık arama kutusu, 1 sn bütçe | Sabit tek hat ya da araçsız | Tur sayısı gecikmeyi doğrusal büyütür |
| Model cevabı bilmiyor olabilir | Sabit hat + eşik | Kapsam dışı kontrolü tek satırlık programatik iştir |

## Burada Ölçülmeyenler

- Ajanın sabit hattan **daha doğru** cevap verdiği durumların oranı: bu sayfa maliyeti ölçüyor, faydayı ölçmüyor. Fayda ölçümü için [RAG Değerlendirme](/rag/rag-degerlendirme/) sayfasındaki soru-cevap setini iki hatta da koşmak gerekir.
- Çoklu araç gerçekçi senaryolar (10+ araç): burada iki araç tanımlı. Araç sayısının seçim doğruluğunu nasıl bozduğu literatürde "too many tools" diye geçer ama OpenAI'nin "dozens of tools → high cost and latency" uyarısı niteliktir; sayısal eşiği yok.
- Kalıcı bellek, planlama, geri bildirim (Reflexion tipi öz-eleştiri) gibi ajan özellikleri; bu sayfa yalnızca araç çağırma döngüsünü kapsar.

## Kaynaklar ve ileri okuma

- [Ajan Ölçümü](/ajan/ajan-olcumu/) — Örnek 7'nin tur, token ve saniye sayıları; `tool_choice` ve `format` denemelerinin bu makinedeki sonucu.
- [Araç Çağırma Mekaniği ve MCP](/ajan/arac-cagirma-ve-mcp/) — döngünün istek/cevap biçimi ve MCP'nin bu işi nerede standartlaştırdığı.
- [Örnek 7: Ajan Döngüsü](/ornekler/ajan-dongusu/) — ölçümü üreten betiğin kendisi ve satır satır açıklaması.
- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — önbellek, tur başına düşen sunucu işi ve ölçümün nasıl tekrarlanacağı.
- ReAct: Synergizing Reasoning and Acting in Language Models, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) — akıl yürütme ve eylemi sırayla üretme deseni; ajan döngüsünün akademik adı.
- Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity, [arXiv:2403.14403](https://arxiv.org/abs/2403.14403) — sorguyu sınıflandırıp arama adımını hiç/tek/tekrarlı olarak seçen kontrolü; bu sayfadaki 2. basamağın eğitimli hâli.
