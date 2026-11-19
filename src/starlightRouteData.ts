import { defineRouteMiddleware } from '@astrojs/starlight/route-data';

// Sayfanın `dogrulama` damgası bu eşiği geçerse sayfanın üstüne banner basılır.
// Eşikler keyfidir; dayanağı: kaynak adları, fiyatlar ve sürüm zincirleri bu sitenin kendi
// ölçüm kayıtlarında bile 1-2 gün içinde oynuyor. 90 gün = "yeniden gözden geçir",
// 180 gün = "bu sayfada okuduğunu varsayma".
const BAYAT_GUN = 90;
const COK_BAYAT_GUN = 180;

function guncelTarih(damga: string, simdi: Date): number | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(damga)) return null;
  // Yerel gece yarısı: UTC'ye çevirirsek kış/yaz saati ve saat dilimi tarihi bir gün oynatıyor.
  const baslangic = new Date(`${damga}T00:00:00`);
  if (Number.isNaN(baslangic.getTime())) return null;
  return Math.floor((simdi.getTime() - baslangic.getTime()) / 86_400_000);
}

export const onRequest = defineRouteMiddleware((context) => {
  const { entry } = context.locals.starlightRoute;
  const damga = entry.data.dogrulama as string | undefined;
  const simdi = new Date();
  const gun = damga ? guncelTarih(damga, simdi) : null;

  let metin: string;
  if (damga === undefined || gun === null) {
    metin =
      'Bu sayfada doğrulama damgası yok ya da biçimi bozuk. Sayfadaki sürüm adları, fiyatlar ve ' +
      'ölçülmüş sayılar için herhangi bir güvence verilmiyor.';
  } else if (gun < BAYAT_GUN) {
    return;
  } else if (gun < COK_BAYAT_GUN) {
    metin =
      `Bu sayfadaki iddialar en son <strong>${damga}</strong> tarihinde (${gun} gün önce) doğrulandı. ` +
      'Araç sürümleri, model adları ve fiyatlar o zamandan beri değişmiş olabilir.';
  } else {
    metin =
      `Bu sayfa <strong>${damga}</strong> tarihinden beri (${gun} gün) doğrulanmadı. ` +
      'Buradaki sayıları ve sürüm adlarını güncel varsaymayın.';
  }

  // Base önekli adres (GitHub Pages): BASE_URL '/' ise önek yok, değilse base'i taşı.
  const kok = import.meta.env.BASE_URL === '/' ? '' : import.meta.env.BASE_URL;
  metin += ` Nasıl çalışır: <a href="${kok}/kaynaklar/dogrulama-mekanizmasi/">Doğrulama Mekaniği</a>.`;
  entry.data.banner = { content: metin };
});
