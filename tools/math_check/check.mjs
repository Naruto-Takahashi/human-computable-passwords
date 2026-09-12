import katex from 'katex';
import fs from 'fs';
const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let bad = 0;
for (const { file, kind, body } of items) {
  try {
    katex.renderToString(body, { displayMode: kind === 'display', throwOnError: true });
  } catch (e) {
    bad++;
    console.log(`  ${file} [${kind}] ${String(e.message).split('\n')[0]}`);
    console.log(`      ${body.replace(/\n/g, ' ').slice(0, 90)}`);
  }
}
console.log(`\n  数式 ${items.length} 個を検査 / エラー ${bad} 個`);
process.exit(bad ? 1 : 0);
