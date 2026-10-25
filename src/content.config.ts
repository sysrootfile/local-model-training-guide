import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { docsLoader, i18nLoader } from '@astrojs/starlight/loaders';
import { docsSchema, i18nSchema } from '@astrojs/starlight/schema';

// `dogrulama` zorunludur: alanı olmayan bir sayfa build'i kırar. Mekaniğin ne söylediği ve
// ne söylemediği: src/content/docs/kaynaklar/dogrulama-mekanizmasi.md
//
// YAML tuzagi: kosul yazilmis `dogrulama: 2026-10-19` frontmatter'da dize degil, YAML 1.1 tarih
// skalari oldugu icin Date nesnesi olarak gelir. Bu yuzden alan hem dizeyi hem Date'i kabul edip
// ikisini de tek bicime indiriyor; aksi hâlde build "Expected type string, received object" veriyor.
function yerelISO(deger: Date): string {
  const y = deger.getFullYear();
  const a = String(deger.getMonth() + 1).padStart(2, '0');
  const g = String(deger.getDate()).padStart(2, '0');
  return `${y}-${a}-${g}`;
}

const BICIM = /^\d{4}-\d{2}-\d{2}$/;

const dogrulamaDamgasi = z
  .union([z.string(), z.date()])
  .transform((deger) => (deger instanceof Date ? yerelISO(deger) : deger.trim()))
  .refine((deger) => BICIM.test(deger), {
    message: '`dogrulama` YYYY-AA-GG biçiminde olmalı (ör. 2026-10-19).',
  });

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({ extend: () => z.object({ dogrulama: dogrulamaDamgasi }) }),
  }),
  i18n: defineCollection({ loader: i18nLoader(), schema: i18nSchema() }),
};
