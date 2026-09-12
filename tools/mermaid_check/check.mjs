import { JSDOM } from 'jsdom';
import fs from 'fs';
const dom = new JSDOM('<!doctype html><html><body></body></html>');
for (const k of ['window','document','Element','SVGElement','Node','DOMParser','navigator']) {
  try { Object.defineProperty(globalThis, k, { value: dom.window[k], configurable: true, writable: true }); }
  catch (e) { /* 既に定義済みなら無視 */ }
}
const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
let bad = 0;
for (const f of process.argv.slice(2)) {
  try {
    await mermaid.parse(fs.readFileSync(f, 'utf8'));
    console.log(`  ${f.split('/').pop()}: 構文OK`);
  } catch (e) {
    bad++;
    console.log(`  ${f.split('/').pop()}: エラー — ${String(e.message).split('\n').slice(0,2).join(' / ')}`);
  }
}
process.exit(bad ? 1 : 0);
