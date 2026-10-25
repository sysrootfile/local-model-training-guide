---
title: "Doğrulama Mekaniği — Bir Sayfa Ne Zaman Bayatlar?"
description: "Her sayfanın üst bilgisinde duran `dogrulama` alanının ne anlama geldiği, ilk değerlerinin nereden türetildiği, neyi garanti etmediği ve bayat sayfaya banner basan mekanizmanın üç dosyası."
dogrulama: 2026-10-19
---

Bu sitede sürüm adı, model adı, fiyat ve ölçülmüş sayı var. Dördü de bayatlıyor. Bayatlamayı
gizlemenin bir yolu yok; ama bayatlığı **okuyucuya göstermenin** bir yolu var ve bu sayfa onu
anlatıyor.

## Neden Böyle Bir Alan Var

Bir rehber sayfası yazıldığında iki iddia türü iç içe geçer:

- **Zamansız iddialar:** "LoRA'da taban model bellekte durur", "epoch tüm verinin bir turudur".
  Bunlar araç sürümünden bağımsız.
- **Zamanlı iddialar:** "Ollama 0.40.4", "vLLM v0.31.0", "`transformers` v5'te `warmup_ratio`
  kaldırıldı", "RunPod'da ağ volume'ü pod kapalıyken de faturalanır". Bunların her biri, yukarı
  akış değiştiğinde sessizce yanlış olur.

Bu sitenin kendi künyeleri üç günde tam olarak bunu yaptı: `ornekler/tekrarlanabilirlik` kaydı
**Ollama 0.40.4** ile 17 Ekim'de, `ornekler/eminlik-olcu` kaydı **0.40.5** ile aynı günün akşamında
koştu; makine 19 Ekim'de **0.40.6**'da. Yani "bu makinede ölçüldü" cümlesinin içındaki sürüm bile
iki günde bayatlıyor — sayılar yanlış değil, hangi sürümün sayısı oldukları yazılmadığı anda
eksik.

Sitede zamansız/zamanlı ayrımı hiç yapılmamıştı. Her sayfa, üç ay önceki bir sürüm adını, dün
yazılmış gibi aynı kesinlikle gösteriyordu. `dogrulama` alanı bu ikisini ayıran tek şey: **sayfanın
üst bilgisi artık "bu iddialar en son ne zaman gözden geçirildi" sorusuna bir tarih veriyor** ve
tarih eşikleri geçince sayfanın üstünde banner beliriyor.

## Damga Ne Söyler, Ne Söylemez

| Damga söyler | Damga söylemez |
| --- | --- |
| Sayfadaki iddialar o tarihte **bir kez gözden geçirildi**. | İddiaların **hâlâ** doğru olduğu. Gözden geçirme tarihi, doğruluğun kanıtı değil. |
| Bu sayfaya o tarihten sonra içerik dokunuşu oldu. | Dokunuşun ne olduğu — bir iç bağlantı eklemek de damgayı ileri taşır. |
| Eşik aşıldıysa okuyucu uyarılıyor. | Sitenin hiçbir yere gidip "bu sürüm hâlâ geçerli mi" diye **sormadığı**. Otomatik yukarı akış kontrolü yok. |
| Her sayfanın tek bir damgası var. | Sayfadaki her satırın aynı yaşta olduğu. Altmışı aşkın sayfalık bir sitede satır bazlı damga tutulmuyor. |

:::caution[Damga bir güvence değil, bir takvim]
Yanlış okuma şu olur: "damga taze, o hâlde güvenli." Damga tazeliği yalnızca *bakım tarihini*
söyler. Bir sayfadaki fiyat ya da sürüm adının gerçekten güncel olup olmadığını anlamak hâlâ iki
işe dayanıyor: yukarı akış dokümanına bakmak ve — bu sitenin yaptığı gibi — kendi makinenizde
koşum almak.
:::

## Mekanizma Üç Dosyada Duruyor

**1. Zorunlu alan** — `src/content.config.ts`:

```ts
const dogrulamaDamgasi = z
  .union([z.string(), z.date()])
  .transform((deger) => (deger instanceof Date ? yerelISO(deger) : deger.trim()))
  .refine((deger) => /^\d{4}-\d{2}-\d{2}$/.test(deger), {
    message: '`dogrulama` YYYY-AA-GG biçiminde olmalı (ör. 2026-10-19).',
  });

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({ extend: () => z.object({ dogrulama: dogrulamaDamgasi }) }),
  }),
};
```

Alan **zorunlu**: damgası olmayan bir sayfa `astro build`'i kırar. Bu, mekaniğin fail-closed
tarafı — yeni sayfa yazmayı unutan biri, sessizce damgasız bir sayfa yayımlayamıyor.

**2. Banner** — `src/starlightRouteData.ts` (Starlight'ın route middleware'i):

```ts
const BAYAT_GUN = 90;
const COK_BAYAT_GUN = 180;

// ...
} else if (gun < COK_BAYAT_GUN) {
  metin = `Bu sayfadaki iddialar en son <strong>${damga}</strong> tarihinde (${gun} gün önce) doğrulandı. ...`;
} else {
  metin = `Bu sayfa <strong>${damga}</strong> tarihinden beri (${gun} gün) doğrulanmadı. ...`;
}
entry.data.banner = { content: metin };
```

Eşikler keyfî ve bilinçli olarak yüksek: 90 gün "yeniden gözden geçir" uyarısı, 180 gün "buradaki
sayıları güncel varsayma" uyarısı. Bugün için (2026-10-19) ikisini de aşan sayfa yok; en eski
damga dört gün öncesine ait.

**3. Denetim betiği** — `scripts/dogrulama-kontrol.mjs`, `npm run dogrula` ile koşulur. Eksik,
biçimi bozuk ya da **geleceğe tarih basmış** her sayfa çıkış kodu 1 ile hatadır. Bayat sayfalar
varsayılan olarak yalnızca rapor edilir; `--strict` verilirse hata olur. Ayrım kasıtlı: bayatlık
normal bir durumdur, damgasız sayfa ise bir hata.

:::note[Starlight'ın kendi `lastUpdated` alanı neden kullanılmadı]
Starlight'ta yerleşik bir `lastUpdated` alanı var ve sayfa altında "son güncelleme" satırı olarak
görünüyor. Anlamı farklı: o, **dosyanın** güncellenmesi. Bizim damgamız **iddianın** gözden
geçirildiği tarih olmak zorunda; bu ikisi aynı şey değil — aşağıdaki kuruluş bölümü tam da bu
farkın ölçüldüğü yer. Yerleşik alan ayrıca bayatlık uyarısı üretmiyor.
:::

## İlk Damgalar Nereden Geldi

Bu depoda git geçmişi yok, yani "bu sayfa en son ne zaman değişti" sorusunun nesnel tek yanıtı
dosyanın değiştirilme zamanıydı. `scripts/dogrulama-baslat.mjs`, o sırada var olan 60 dosyanın
tamamına — önce `--yaz`sız bir deneme koşumuyla gösterdiği planı uyguladıktan sonra — mtime tarihini
damga olarak yazdı. Bu sayfa o koşumdan sonra eklendiği için kendi damgası (2026-10-19) mtime'dan
değil, gerçekten yazıldığı günden geliyor. Denetim betiğinin ilk koşumda ürettiği gerçek dağılım:

| Damga | Sayfa | Ne yapılıyordu |
| --- | --- | --- |
| 2026-10-15 | 27 | Site iskeleti + derinlik fazı (beş parti) |
| 2026-10-16 | 11 | Hız/Maliyet, 127.0.0.1 geçişi, ajanlar, enjeksiyon |
| 2026-10-17 | 14 | Çıkarım parametreleri, tekrarlanabilirlik, lisans, gömme eğitimi |
| 2026-10-18 | 8 | Eminlik sayfası + yedi sayfaya iç bağlantı |

:::caution[Dağılımın bilinen kusuru]
2026-10-18 damgalı sekiz sayfadan yedisinde o gece yapılan iş **iç bağlantı eklemekti**; iddialar
yeniden doğrulanmadı. Damga bu yedi sayfada, iddiaların 18 Ekim'de gözden geçirildiğini söylüyor —
oysa gözden geçirilen şey bağlantıydı. Sekizinci sayfa ([Eminlik ve Kalibrasyon](/kullanim/eminlik-ve-kalibrasyon/))
istisna: orada o gece ölçüm kayıtlarına yeniden bakıldı ve yanlış istek sayıları (266 yerine
176 sohbet + 100 gömme) düzeltildi, yani damga iddia gözden geçirmesine dayanıyor.
Bu kusur mekanizmadan değil, mtime'ın neyi ölçtüğünden geliyor — ve damgaların bundan sonra
elle taşınmasının gerekçesi tam olarak bu.
:::

:::note[Tablo artık tarih, bugünün dağılımı değil]
Tablo, damgalar ilk basıldığında denetim betiğinin yazdığı dağılımı gösteriyor. 19 Ekim'de yukarıdaki
sürüm künyesi düzeltmesi yapıldı: on iki sayfanın damgası **2026-10-19**'a taşındı; sonra kapsam
haritası ve eşzamanlılık sayfası eklendi. Betik aynı günün ikinci koşumunda
`2026-10-15: 27 · 10-16: 5 · 10-17: 13 · 10-18: 3 · 10-19: 15` yazdırdı. Bu sayı da donmuş bir anlık
görüntüdür — güncel olan tek şey `npm run dogrula` çıktısıdır.
:::

## Bugün Test Edilen Koşumlar

Banner kodu, eşikleri geçen sayfa olmadığı için doğal olarak hiç çalışmamıştı. Çalıştığı, geçici
dosyalarla doğrulandı — yayımlanmış hiçbir sayfanın damgasına dokunulmadı ve yedi test dosyasının
tamamı koşum biter bitmez silindi.

**Build ve banner tarafı:**

| Koşum | Beklenti | Ölçülen çıktı |
| --- | --- | --- |
| damgası hiç yazılmamış sayfa | build kırılır | `[InvalidContentEntryDataError] … data does not match collection schema.` ve altında `> Required`; çıkış kodu 1 |
| damga 2026-07-15 (96 gün) | 90–179 bandındaki banner | `.sl-banner` basıldı: "Bu sayfadaki iddialar en son 2026-07-15 tarihinde (96 gün önce) doğrulandı…" |
| damga 2026-04-01 (201 gün) | 180 ve üzeri bandındaki banner | "Bu sayfa 2026-04-01 tarihinden beri (201 gün) doğrulanmadı. Buradaki sayıları ve sürüm adlarını güncel varsaymayın." |
| damga 2026-10-19 (bugün, negatif kontrol) | banner yok | `.sl-banner` elemanı yok |

**Denetim betiği tarafı:**

| Koşum | Beklenti | Ölçülen çıktı |
| --- | --- | --- |
| tek bayat sayfa, `npm run dogrula` | raporla, build'i kırma | "Bayat (>=90 gun): 1" + "TAMAM: her sayfada gecerli damga var.", çıkış 0 |
| aynı sayfa, `npm run dogrula --strict` | bayatlık hataya dönüşsün | çıkış 1 |
| damga 2027-01-01 (gelecek) | reddedilmeli | "HATA: … gelecekte damga (2027-01-01, 74 gun ileri)", çıkış 1 |
| damga alanı yok | yakalanmalı | "HATA: … dogrulama damgasi yok", çıkış 1 |

Banner'ın yeri ve okunurluğu tarayıcıda ölçüldü: sayfadaki `<h1>` öğesinden **önce** geliyor,
`rgb(211, 204, 255)` zemin üzerinde `rgb(27, 23, 64)` metin ve 16 px yazı basıyor; test sayfasındaki
iç bağlantı `/kaynaklar/dogrulama-mekanizmasi/` adresine gidiyor ve konsol boş.

**Build süreleri de bu koşumda ölçüldü:** 65 HTML üretimi **7,84 sn**, ikinci koşum **4,48 sn**.
Farkın sebebi tahmin değil, günlüğün yazdığı: şema değiştiği için ilk koşum `[content] Content
config changed → Clearing content store` yapıp içeriği baştan senkron etti. Denetim betiği, damgası
yeni yazılmış 60 dosyalık kümeyi **110 ms**'de taradı; bu yüzden `astro build`'in içine gömülmedi,
`npm run dogrula` olarak ayrı duruyor.

:::caution[YAML damgayı dize olarak görmüyor]
İlk build denemesi `dogrulama: Expected type "string", received "object"` hatası verdi. Sebep Türkçe
metin ya da yazım hatası değil: tırnaksız yazılan `2026-10-19` YAML 1.1 kurallarına göre bir **tarih**
olarak ayrıştırılıyor ve şemaya `Date` nesnesi olarak geliyor. `src/content.config.ts` bu yüzden alanı
hem dize hem `Date` kabul edip ikisini de `YYYY-AA-GG` dizesine indiriyor. Sonuç: damgayı tırnaklı ya
da tırnaksız yazmak eşdeğer.
:::

:::note[Kanıtın sınırı]
Bu koşumlar banner'ın **kodda doğru metni ürettiğini** gösteriyor, zamanlamasını göstermiyor. Gerçek
bir sayfanın 90 güne düşeceği takvim tarihini beklemek gerekiyor; testteki tarihler suni olarak
geriye alındı ve hiçbiri yayımlanmış bir sayfada kalmadı. Doğrulama tarayıcı yüzeyinden DOM ve
hesaplanmış stil üzerinden yapıldı, piksel ekran görüntüsü alınamadı — banner'ın dar mobil genişlikte
nasıl kıvrıldığı bu koşumda ölçülmedi.
:::

## Bu Mekaniğin Kapamadığı Boşluklar

- **Yukarı akış yoklanmıyor.** Betik hiçbir paket sitesine, fiyat sayfasına ya da Ollama
  arayüzüne dokunup "bu hâlâ geçerli mi" diye sormuyor. Sorması da gerekmiyor; sorsa, o sayfa
  kendi iddiasını üretmeye başlamış olurdu.
- **Satır bazlı damga yok.** Zamansız bir kavram sayfası ile fiyat tablosu aynı ağırlıkta
  uyarılıyor. Daha doğru olan, sayfa başına birden çok damga ya da bölüm başına damga; ikisi de
  bu sitenin bakım yükünü iki katına çıkarır.

## Ölçülmedi

- 90 ve 180 günlük eşiklerin bu sitenin bayatlama hızına uygun olduğu **ölçülmedi** — bir tahmindir,
  ölçüm değil. Uygunluk, takvim gerçekten 90 günü doldurduğunda, yani en erken **2027-01-13**'te
  (en eski damga 2026-10-15) görülecek. O tarihe kadar mekanizma, yukarıdaki tabloda olduğu gibi
  suni tarihlerle doğrulanmış durumda.
- **Damga taze, iddia yanlış** durumu bu denetimin kapsamında değil. Mekanizma hiçbir iddiayı yukarı
  akışa soru sorarak doğrulamadığı için, şeması ve banner'ı kusursuz çalışırken de bayat bir sayfa
  "taze" görünebilir. Bunun oranı ölçülemez; ölçülemeyeceği için de burada duruyor.
- Damgasız sayfanın build'i hangi aşamada kırdığı tek bir hata mesajıyla görüldü; yüzlerce sayfalık
  bir depoda bu hatanın ayıklanabilirliği test edilmedi.
- Banner'ın okuyucuyu gerçekten daha dikkatli yapıp yapmadığı **ölçülmedi**; sitede ölçülmüş olan tek
  şey banner'ın render edildiği ve konsol temizliği.

## İlgili Sayfalar

- [Yerel Kurulum](/donanim/yerel-kurulum/) — sürüm sabitleme ve `pip freeze` alışkanlığı; damga
  mekaniğinin okuyucu tarafındaki karşılığı.
- [Hız ve Maliyet](/kullanim/hiz-ve-maliyet/) — sitedeki gecikme sayılarının ölçülmüş kaynağı;
  "ölçüldü" ile "gözden geçirildi" arasındaki farkın en somut örneği.
- [Sıkça Sorulan Sorular](/kaynaklar/sss/) — "bu rehber ne kadar güncel" sorusunun kısa yanıtı.

## Kaynaklar ve İleri Okuma

- [Starlight — Route Data](https://starlight.astro.build/guides/route-data/) — sayfa başına
  üretilen veriyi middleware ile değiştirme; banner basmanın kullanıldığı kanal. (Son okuma:
  2026-10-19.)
- [Starlight — Frontmatter](https://starlight.astro.build/reference/frontmatter/) — yerleşik
  `banner` ve `lastUpdated` alanlarının biçimi ile `docsSchema` üzerine alan ekleme. (Son okuma:
  2026-10-19.)
