// Sayfa sayfalarına `dogrulama:` damgasını dosyanın son degisim tarihinden yazan bir kerelik baslatma araci.
// Kullanim: node scripts/dogrulama-baslat.mjs          (dry-run, hicbir seye dokunmaz)
//           node scripts/dogrulama-baslat.mjs --yaz    (uygular)
// Neden mtime: bu depoda git gecmisi yok; bir sayfanin iceriginin son ne zaman elden gecirildigine
// dair elimizdeki tek nesnel kanit dosyanin degisim zamani. Damga "iddia o tarihte gozden gecirildi"
// der, "iddia hâlâ dogru" demez. Ayrinti: src/content/docs/kaynaklar/dogrulama-mekanizmasi.md
import fs from 'node:fs';
import path from 'node:path';

const root = path.join(new URL('.', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'), '..');
const docsDir = path.join(root, 'src', 'content', 'docs');
const yaz = process.argv.includes('--yaz');

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/\.mdx?$/.test(e.name)) out.push(p);
  }
  return out;
}

// Yerel takvim tarihi: UTC'ye dogrultanirsak gece kosumlarinda tarih bir gun geri gider.
function yerelTarih(d) {
  const y = d.getFullYear();
  const a = String(d.getMonth() + 1).padStart(2, '0');
  const g = String(d.getDate()).padStart(2, '0');
  return `${y}-${a}-${g}`;
}

const sonuç = { eklendi: 0, atlandı: 0, sorun: [] };

for (const file of walk(docsDir).sort()) {
  const ham = fs.readFileSync(file, 'utf8');
  const görel = path.relative(docsDir, file).replaceAll('\\', '/');
  if (/^dogrulama:/m.test(ham.split(/^---\r?\n/)[1] || '')) {
    sonuç.atlandı++;
    console.log(`atlandi  ${görel}`);
    continue;
  }
  const fm = ham.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!fm) {
    sonuç.sorun.push(`${görel}: frontmatter bulunamadi`);
    continue;
  }
  const eol = ham.includes('\r\n') ? '\r\n' : '\n';
  const tarih = yerelTarih(fs.statSync(file).mtime);
  const güncel = ham.replace(fm[0], `---${eol}${fm[1]}${eol}dogrulama: ${tarih}${eol}---`);
  console.log(`${yaz ? 'yazildi' : 'planlandi'}  ${görel}  dogrulama: ${tarih}`);
  if (yaz) fs.writeFileSync(file, güncel);
  sonuç.eklendi++;
}

console.log(`\n${sonuç.eklendi} dosya ${yaz ? 'guncellendi' : 'planlandi'}, ${sonuç.atlandı} dosyada damga zaten var.`);
if (sonuç.sorun.length) {
  console.log('\nSORUN:');
  for (const s of sonuç.sorun) console.log(`  ${s}`);
  process.exitCode = 1;
}
