import fs from 'node:fs';
import path from 'node:path';

const dist = new URL('../dist', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}

const files = walk(dist);
let broken = [];

for (const f of files) {
  const html = fs.readFileSync(f, 'utf8');
  const links = [...html.matchAll(/href="(\/[^"#]*)/g)].map((m) => m[1]);
  for (const l of new Set(links)) {
    if (l.startsWith('/_astro') || l.startsWith('/pagefind')) {
      if (!fs.existsSync(path.join(dist, l))) broken.push(`${f} -> ${l} (asset)`);
      continue;
    }
    if (/\.(png|svg|webp|ico|css|js|xml|txt|woff2?|json)$/.test(l)) {
      if (!fs.existsSync(path.join(dist, l))) broken.push(`${f} -> ${l} (asset)`);
      continue;
    }
    let p = l.split('#')[0].split('?')[0];
    if (!p.endsWith('/')) p += '/';
    const target = path.join(dist, p, 'index.html');
    const target2 = path.join(dist, p);
    if (!fs.existsSync(target) && !fs.existsSync(target2)) broken.push(`${f} -> ${l}`);
  }
}

console.log(broken.length === 0 ? `TÜM İÇ LİNKLER TAMAM (${files.length} sayfa tarandı)` : `KIRIK: ${broken.length}`);
// Kirik link varsa cikis 1: betik CI'da "basarili" sayilmamali (QODER.md: cikis kodu kanittir).
if (broken.length) process.exitCode = 1;
broken.slice(0, 40).forEach((b) => console.log(b));
