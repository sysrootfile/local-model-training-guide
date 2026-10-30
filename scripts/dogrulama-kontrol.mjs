// Dogrulama damgasi denetimi: node scripts/dogrulama-kontrol.mjs [--strict]
// Cikis kodu 1: (a) damgasi eksik/bicimi bozuk/gelecek tarihli bir sayfa varsa,
//                (b) --strict verilmis ve bayat (>=90 gun) sayfa varsa.
// Cikis kodu 0, uyarilara ragmen: bayat sayfalar varsayilan olarak rapor edilir, kirilmaz;
// cunku "bayat" normal bir durumdur, eksik damga ise bir hatadir.
import fs from 'node:fs';
import path from 'node:path';

const root = path.join(new URL('.', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'), '..');
const docsDir = path.join(root, 'src', 'content', 'docs');
const strict = process.argv.includes('--strict');
const BAYAT_GUN = 90;
const YAKLASAN_GUN = 75;
const COK_BAYAT_GUN = 180;

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/\.mdx?$/.test(e.name)) out.push(p);
  }
  return out;
}

const simdi = new Date();
const satirlar = [];
const hatalar = [];

for (const file of walk(docsDir).sort()) {
  const g = path.relative(docsDir, file).replaceAll('\\', '/');
  const metin = fs.readFileSync(file, 'utf8');
  const fm = metin.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!fm) {
    hatalar.push(`${g}: frontmatter yok`);
    continue;
  }
  const eslesme = fm[1].match(/^dogrulama:\s*(\S+)\s*$/m);
  if (!eslesme) {
    hatalar.push(`${g}: dogrulama damgasi yok`);
    continue;
  }
  const damga = eslesme[1];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(damga)) {
    hatalar.push(`${g}: bozuk bicim -> "${damga}"`);
    continue;
  }
  const gun = Math.floor((simdi.getTime() - new Date(`${damga}T00:00:00`).getTime()) / 86_400_000);
  if (gun < 0) {
    hatalar.push(`${g}: gelecekte damga (${damga}, ${-gun} gun ileri)`);
    continue;
  }
  satirlar.push({ g, damga, gun });
}

satirlar.sort((a, b) => b.gun - a.gun);
const dagilim = {};
for (const s of satirlar) dagilim[s.damga] = (dagilim[s.damga] || 0) + 1;

console.log(`Bugun: ${simdi.getFullYear()}-${String(simdi.getMonth() + 1).padStart(2, '0')}-${String(simdi.getDate()).padStart(2, '0')}`);
console.log(`Damgali sayfa: ${satirlar.length}`);
console.log(`En eski damga: ${satirlar.length ? `${satirlar[0].damga} (${satirlar[0].gun} gun)` : 'yok'}`);
console.log('\nTarih dagilimi:');
for (const [t, n] of Object.entries(dagilim).sort()) console.log(`  ${t}  ${n} sayfa`);

const bayat = satirlar.filter((s) => s.gun >= BAYAT_GUN);
const yaklasan = satirlar.filter((s) => s.gun >= YAKLASAN_GUN && s.gun < BAYAT_GUN);
const cokBayat = satirlar.filter((s) => s.gun >= COK_BAYAT_GUN);
console.log(`\nBayat (>=${BAYAT_GUN} gun): ${bayat.length}`);
for (const s of bayat) console.log(`  ${s.gun} gun  ${s.damga}  ${s.g}`);
console.log(`Bakim yaklasiyor (${YAKLASAN_GUN}-${BAYAT_GUN - 1} gun): ${yaklasan.length}`);
for (const s of yaklasan) console.log(`  ${s.gun} gun  ${s.damga}  ${s.g}`);
console.log(`Cok bayat (>=${COK_BAYAT_GUN} gun): ${cokBayat.length}`);

if (hatalar.length) {
  console.log('\nHATA:');
  for (const h of hatalar) console.log(`  ${h}`);
}

if (hatalar.length || (strict && bayat.length)) process.exitCode = 1;
else console.log('\nTAMAM: her sayfada gecerli damga var.');
