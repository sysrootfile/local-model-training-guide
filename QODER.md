# Qoder.md — bu depoda çalışma sözleşmesi

Astro + Starlight ile yazılmış, tamamı Türkçe bir model eğitimi rehberi ve onu besleyen ölçüm
kafesleri. Kurulum, komutlar ve sayfa ekleme akışı için kaynak: [README.md](README.md). Bu dosya
yalnız README'nin anlatamadığı şeyi anlatır: **nasıl yazıldığı ve nasıl ölçüldüğü**.

## İki iş kipi

| Kipi | Makineye bedeli | Ne zaman açılır |
| --- | --- | --- |
| **Sayfa yazımı** | 0 dakika, 0 istek | her turda; her zaman pahalı koldan önce |
| **Kafes koşumu** | yerel CPU penceresi + Ollama trafiği | ayrıca onay alındıktan sonra |

Tur planlarken sıradaki adım **tek bir öneri** olarak sunulur ve cevap beklenir. Onaylanan kapsam
kelimesi kelimesinedir: onay bir dosya listesi saydıysa o listenin dışına çık, ve bittiğinde
"bilerek dokunmadım: X, çünkü Y" satırını ekle.

## Sayının kaydı (kademe)

İddia gücü dört basamak: **0 beklenti → 1 yukarı akış rakamı → 2 ölçüldü, tek gözlem → 3 ölçüldü ve
tekrarlandı.** Tam tablo ve her birimin tek doğrulanmış adresi:
[kapsam-haritası](src/content/docs/kaynaklar/kapsam-haritasi.md).

- Bir sayfa kademe 3'e çıkmadan kural cümlesi kuramaz; kurarsa o cümle kademe 0'a düşer.
- Bir metrik boş varsayılan yoldan üretilebiliyorsa (boş payda, sabit kopyalanan örnek değer)
  fail-closed dal + test gerekir; küçük modelin istemdeki örnek değeri olduğu gibi geri yazması
  gerçek bir vakadır.
- **Sayı yalnız bitmiş günlükten gelir.** Koşum sürerken durum söylenebilir (`hâlâ ısınıyor`),
  sonuç söylenemez — tahmin en iyi tahmin olsa bile uydurmadır.
- Ölçülemeyen satır `ÖLÇÜLMEDİ (<sebep>)` yazılır ve kapı yine kapalı sayılır; inferred `0.000`
  ya da `1.000` yazılmaz.
- **Yayımlanan komut da bir sayı kadar iddiadır.** Bir komut satırı ya bu makinede o turda
  çalıştırılmıştır ya da aracın kendi belgesinden alıntılanmıştır; ikisi de değilse "doğrulanmadı"
  diye etiketlenir. (`setx NAME /D` bu kurala takıldı: `setx`'in silme bayrağı yok, kullanıcı
  `ERROR: Invalid syntax` aldı.)
- Toplama değil türetilmiş bir rakam (iki ölçümün farkı/oranı) borçtur, sonuç değil; ölçümü bu
  makinede ulaşılabilirse yeniden koşmayı teklif et.

## Koşum hijyeni

1. Ortam: `ornekler/<kafes>/` altından `PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u <betik>.py … > cikti/<kayit>.txt 2>&1`.
   Türkçe çıktı için `PYTHONUTF8=1` şart; kayıt dosyası `#BASLIK` ile `#BITIS` arasında
   `#ETİKET {json}` satırları taşır (örnek: [eszamanlı kafes](ornekler/eszamanli-olcu/README.md)).
2. **Duman önce, tam koşum sonra.** Tek kol, tek tekrar: uçtan uca kayıt üretiyor mu?
3. Koşumdan önce ve sonra sunucu yoklaması: `/api/ps` boş olmalı ve günlükte beklenen satır
   okunmalı. Pencereye giren yabancı istek ölçümü geçersiz kılar; **sunucu ayarı doğru ve istekler
   hatasız olsa bile** veri elenebilir. Elenen kaydın tek sayısı bile yayımlanmaz, dosya adında
   kalır.
4. Tavanlar: kol ≤ 20 dk, gün ≤ 45 dk. Bu tavanın asıl bedeli süre değil, o süre boyunca makineyi
   başka işe kapatmak.
5. Sunucuya müdahale makine sahibinin: ortam değişkenini yazmak ve Ollama'yı yeniden başlatmak
   agent'ın işi değil. Agent yalnız betiği koşar ve değeri `server.log`'dan okur
   (`msg="server config"` satırı; `-c N -np M` ise bir model yüklendiğinde görünür).
6. Kapanış doğrulanmadan eksen kapanmaz: env değişkeni silindiysa `reg query` anahtarı bulmamalı
   **ve** günlükte `:1` + `-np 1` okunmalı. Bir komutun çıkış kodu, durumun kanıtı değildir.

## Tuzaklar (hiçbir config itiraf etmiyor)

- **Git Bash/MSYS:** `reg query "HKCU\Environment" /v NAME` → `Invalid syntax`, çünkü `/v` yol
  sanılıyor. Doğrusu `//v`.
- **Arka plan kuyruğu yönlendirmeyi yutabilir.** Kayıt dosyası boşsa wrapper yakalamasından
  `grep '^#'` ile yeniden kur ve özet betiği + `diff` ile birebir olduğunu doğrula; sonra bu
  yeniden kurmayı README'de açıkça yaz.
- **Pipe çıkış kodu maskele:** `cmd | tail` komutun değil `tail`'in kodunu döner. Üretilen dosyayı
  oku.
- **`/api/ps` POST'u** `JSONDecodeError: Extra data` veriyor; `GET` + satır satır ayır.
  `/api/chat` için `stream: False`.
- **Env değişkeni silme:** `[Environment]::SetEnvironmentVariable("AD", $null, "User")` veya
  `reg delete "HKCU\Environment" /v AD /f`. Silme, o sabah açılmış pencerelerde kalan kopyayı
  temizlemez: `Remove-Item Env:AD` (PowerShell) / `set AD=` (cmd).
- **In-app Browser kapalıysa** piksel/taşma yoklaması yapılamaz; DOM ve stil yoklaması da yapılamaz.
  Tarayıcı **açıkken de** pencere boyutu sıfır olabilir: `window.innerWidth: 0` ise yerleşim yoktur —
  DOM sayımları (H2, tablo, aside tipi, artık `:::`, sidebar bağlantısı) geçerli, yatay taşma ve
  piksel iddiaları geçersizdir. İkinci durumda raporlanacak satır "yoklanamadı"dır.
- **Önizleme sunucusu** (`npm run preview -- --port 4326 --host 127.0.0.1`) yoklama için açılır ve
  iş bitince kapatılır: portu dinleyen PID `netstat -ano | grep ':4326'` ile bulunur, komut satırı
  `Get-CimInstance Win32_Process` ile **kendin başlattığın doğrulanmadan** öldürülmez.
- **Betik yorumları ASCII:** JS/Python içindeki yorumlar Türkçe karakter olmadan yazılıyor
  (`Dogrulama damgasi denetimi`); sayfa metni tam Türkçe. Ondalık virgül, binlik nokta:
  `141,88 sn`, `2 412 794 346 B`.

## Bir sayfa bittiğinde sıra

```bash
npm run build                          # beklenti: sayfa sayısı + uyarısız derleme
node scripts/link-check.mjs            # dist/ tarar; "TÜM İÇ LİNKLER TAMAM (N sayfa tarandı)"
npm run dogrula                        # her sayfada dogrulama: damgası; eksikse çıkış 1
```

Sonra: içerik değiştiyse `dogrulama:` tarihini bugüne çek (metin değişmediyse çekme — damgası
`2026-10-18` olan bir sayfanın iddiası bugün değiştiyse kademe 1 dili artık yalan söyler), ve
kalan imzaları yokla: artık `:::` bloğu, beklenmeyen CJK, bozuk çok satırlı düzen. Tarayıcı
yoklaması ancak in-app Browser açıksa mümkündür.

## Kaynakların tek yeri

Aynı birimi iki sayfa söylüyorsa biri yanlış, ikisi de kaynaktır. Hangi birimi hangi sayfa taşıyor:
kapsam haritasının "Sayının Kaynağı Tek Yer" tablosu. Yeni sayfa o tabloya ya da "Bilerek
Ölçmediklerimiz" listesine kendisini ekleyerek girer; eklenmiyorsa kapsamı belirsizdir.
