---
title: "Bu Rehberi Agent ile Başka Makinede Çoğaltmak"
description: "Rehberdeki ölçüm kafeslerini ikinci bir makinede ve bir kod agent'ıyla kurup koşturmak için adım adım rehber: kurulum, duman-önce protokolü, pencere hijyeni, kirletme denetimi, kayıt düzeni ve makine künyesi. Kendi sayılarınızın hangi kademede duracağı."
dogrulama: 2026-10-30
---

Bu rehberdeki her ölçüm tek makineden geldi ve sayfalar bunu açıkça söylüyor: mutlak sayılar
(Ryzen 5 2600, 15,9 GB RAM, CPU) sizin donanımınızda **farklı çıkacaktır**; sayfaların taşıdığı
iddia desendir, saniye değildir. "Benim makinemde ne oluyor?" sorusunun iki dürüst cevabı var:
betikleri kendiniz koşturmak ya da bir kod agent'ına kurdurup koşturtmak. İkisi de aynı disiplini
ister — bu sayfa o disiplinin kurulum ve koşum talimatıdır. Sözleşmenin site özeti
[Doğrulama Mekaniği](/kaynaklar/dogrulama-mekanizmasi/) ve
[Kapsam Haritası](/kaynaklar/kapsam-haritasi/)'ndadır; tam metin depodaki AGENT.md dosyasıdır.

## Kurulum (insan da agent da aynı sırayı izler)

1. **Depoyu alın:** `git clone <depo-adresi>`; ölçüm kafesleri site derlemesinden bağımsızdır,
   `ornekler/` altındaki her klasör kendi README'siyle gelir.
2. **Tek ortak sanal ortam:** depo kökünde `python -m venv .venv` — klasör başına ortam yok;
   kafesler `.venv`'e göreli çağrılır (`../../.venv/Scripts/python.exe`, Linux/macOS'ta
   `../../.venv/bin/python`).
3. **Paketler:** `pip install pandas scikit-learn joblib` (klasik-ml) ve
   `pip install datasets ftfy datasketch` (veri-temizleme); ölçüm kafeslerinin çoğu yalnız
   standart kütüphane ister (her kafesin README'si kendi listesini taşır).
4. **Ollama + modeller:** [Ollama](https://docs.ollama.com/) kurun; `ollama pull
   qwen2.5:3b-instruct-q4_K_M` ve `ollama pull bge-m3`. Sunucu `127.0.0.1:11434`'te dinliyor olmalı —
   kafesler başka adrese bağlanmaz (`_url_dogrula` guard'ı yalnız izinli ana makinelere izin verir).
5. **Türkçe çıktı:** Windows'ta `PYTHONUTF8=1` şart; koşum çıktıları `> cikti/<kayit>.txt 2>&1`
   ile dosyaya yazılır.

## Agent'a özel kurallar (AGENT.md'den damıtılmış)

- **Duman önce, tam koşum sonra.** Tek kol, tek tekrar: betik uçtan uca kayıt üretiyor mu?
  Duman geçmeden tam koşum başlamaz. Duman modu olmayan kafeslerde en kısa argüman kombinasyonu
  kullanılır ve kayıt "duman" diye etiketlenir.
- **Sayı yalnız bitmiş günlükten gelir.** Koşum sürerken durum söylenebilir, sonuç söylenmez;
  yarım log yayımlanmaz.
- **Sunucuya müdahale makine sahibinde.** `OLLAMA_NUM_PARALLEL` gibi ortam değişkenlerini yazmak
  ve Ollama'yı yeniden başlatmak agent'ın işi değildir; agent yalnız betiği koşar ve değeri
  `server.log`'dan okur (`server config` satırı + `llama-server … -np N` komut satırı).
- **Pencere hijyeni.** Ölçüm penceresi boyunca sunucuya başka istek gitmez. Bu makinede en sık
  kirletici sınıfı, arka planda çalışan IDE/entegrasyon araçlarının gömme istekleridir — bir
  pencere içinde bge-m3 gibi ikinci bir model kendiliğinden yükleniyorsa kirletici vardır.
- **Kirletme denetimi koşumdan hemen sonra.** Kafesin istem imzasına uymayan her yeni-istem
  satırı ya yabancıdır ya da betiğin kendi boşaltma çağrısı; dağılım imzaya uymuyorsa koşum
  elenir. Komut: `python ozetle.py --kirletme "<server.log>" --istem <istem-token> --pencere <başlangıç>-<bitiş>`.
- **Kol başına 20 dakika, gün başına 45 dakika** yerel CPU tavanı — tavan asıl bedeli ölçüm değil,
  o süre boyunca makinenin başka işe kapatılmasıdır.
- **Sürüm künyesi.** Ollama hızla güncellenir; her kaydın hangi sunucu sürümünden geldiği
  günlükte okunup kayıt yanına yazılır. İki sürümün sayıları yan yana konmaz.
- **Betik yorumları ASCII**, sayfa metni Türkçe; ondalık virgül, binlik nokta.

## Yeni makinede neyin farklı olacağı

- **Sayılar.** Tümü. Aynı betik, aynı model, farklı CPU: tek isteğin tok/sn'i, dalga duvarları,
  bellek adımları — hepsi sizin donanımınızın sayısıdır. Bu rehberin sayfalarıyla karşılaştırmayı
  **desen düzeyinde** yapın (merdiven var mı? kilit adımı var mı? kuyruk mu paylaşım mı?); saniye
  karşılaştırması yapılmaz.
- **Kademe.** Yeni makinedeki ilk koşum kademe 2'dir (tek gözlem); 5 tekrar + p50/p95 ile kademe 3'e
  çıkılır. Rehberin yayımlanmış sayıları sizinkilerin yerine geçmez — yanına makine künyesiyle
  yeni satır açar.
- **GPU.** `size_vram` sıfırdan farklı çıkarsa model GPU'da çalışıyordur; o koşum bu sayfadaki
  CPU koşumlarının yanına eklenir, onun yerine geçmez. Ollama sürümünüzün GPU keşfinin çalıştığını
  günlükten doğrulayın (`inference compute` satırı).
- **Kirleticiler her makinede olabilir.** IDE entegrasyonları, Docker benzeri araçlar, başlat
  uygulamaları — sunucu her açıldığında kendiliğinden model yükleyen bir şey varsa kirletme
  denetimi onu yakalar; pencere öncesi o aracı susturmak makine sahibinin kararıdır.

## Kayıt düzeni ve geri getirme

- Kayıt adına makine etiketi koyun: `cikti/eszamanli-kaydi-<makine>-<tarih>.txt`. Aynı dosya adı
  iki makinede aynı kaydı anlatmaz.
- Her kayıtla birlikte üç künye satırı gerekir: sunucu sürümü (`server config` satırından), model
  yüklemesinin `-np`/`-c` değerleri, ve makine (CPU modeli, RAM, işletim sistemi).
- Sonuç tablolarına girecek sayılar için kabul kriterleri kafes README'lerinde durur; ölçüm
  üretmeden önce o kafesin kabul kriterini okumadan pencere açılmaz.
- İki makinenin sayıları tek tabloda yan yana konmaz; konuşturulacak şey, aynı deseni iki donanımda
  da görüp görmediğinizdir. Bu, tek makineden taşınmayacak tek dürüst genelleme yoludur.

## Duman komutları (kurulum doğrulaması)

Her kafesin README'sindeki komut özetinin amacı burada tek satırda: kurulumun doğru kurulduğunu
kanıtlamak. Şunlar Ollama gerektirir ve dakikalarla biter:

```bash
cd ornekler/tekrarlanabilirlik && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u tekrar.py --duman > cikti/duman.txt 2>&1
cd ../enjeksiyon-deni && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u enjeksiyon.py --duman > cikti/duman.txt 2>&1
cd ../cikarim-olcu && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u hiz_olc.py --kisa > cikti/duman.txt 2>&1
cd ../eszamanli-olcu && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u eszamanli_olcu.py --duman > cikti/duman.txt 2>&1
cd ../gomme-egitimi && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u kos.py --duman --kollar a > cikti/duman.txt 2>&1
cd ../yerel-rag && PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u rag.py --test > cikti/duman.txt 2>&1
```

:::caution[İki kafesin dumanı kanonik kayıt adına yazar]
`gomme-egitimi/kos.py --duman` çıktısını `cikti/kol-a.txt`'ye, `eminlik-olcu/eminlik.py --duman`
yapılandırılmış çıktılarını `cikti/*.json` kanıt dosyalarına yazar. Kendi kaydınızı ezmeden önce
o dosyaların varlığını kontrol edin ya da duman çıktısını ayrı bir kopyada koşun. Bu rehberin
yazar makinesinde bu tuzak bir kez gerçek oldu ve git'ten geri alındı — sizde git geçmişi
yoksa duman koşumu öncesi kanıt dosyalarını yedekleyin.
:::

Ollama gerektirmeyen kafesler (klasik-ml, veri-temizleme, turkce-asistan veri hazırlama,
gorsel-lora denetimi) README'lerindeki komutlarla bağımsız doğrulanır.

## İlgili Sayfalar

- [Doğrulama Mekaniği](/kaynaklar/dogrulama-mekanizmasi/) — damga sistemi ve bayatlığın nasıl yönetildiği.
- [Kapsam Haritası](/kaynaklar/kapsam-haritasi/) — kabul kuralları, kanıt kademeleri ve ölçümün sunucu sürümü defteri.
- [Eşzamanlılık](/kullanim/eszamanlilik/) — çok makinede karşılaştırmaya en uygun ilk eksen: desenler sürüm ve donanım arasında korunuyor mu, sorusu oradan başlar.
- [Yerel Kurulum](/donanim/yerel-kurulum/) — Ollama kurulumunun kendi detayları.
