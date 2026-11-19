// Derleme sonrasi base oneklemesi: Starlight sidebar/baslik linklerini base ile onekler ama
// sayfa govdesindeki href'leri oneklemez; rehype eklentisi yolu Starlight'in markdown
// zincirine ulasmadigi icin duzeltme derlenen HTML uzerinde yapilir (2026-11-19).
// astro.config.mjs'teki `base` ile ayni degeri tasir; scripts/link-check.mjs bu duzeni denetler.
import fs from 'node:fs';
import path from 'node:path';

const dist = new URL('../dist', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const BASE = '/local-model-training-guide';

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}

let duzenlenen = 0;
let dosya = 0;
for (const f of walk(dist)) {
  const once = fs.readFileSync(f, 'utf8');
  // Kapanis tirnagina kadar al: href icindeki # çapası ilk regex'i yarida birakmasin
  // (href="/sayfa/#bolum" bicimi duzenlenmeden kalmisti).
  const sonra = once.replace(/href="(\/[^"]*)"/g, (tam, yol) => {
    if (yol.startsWith(BASE) || yol.startsWith('//')) return tam;
    duzenlenen++;
    return `href="${BASE}${yol}"`;
  });
  if (sonra !== once) {
    fs.writeFileSync(f, sonra);
    dosya++;
  }
}
console.log(`base-onekle: ${duzenlenen} href oneklendi (${dosya} dosya)`);
