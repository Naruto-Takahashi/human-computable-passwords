#!/usr/bin/env bash
# =============================================================================
# Markdown 内の mermaid 図の構文を確かめる
# =============================================================================
# GitHub は ```mermaid をそのまま描画するが，構文を誤ると図の代わりに
# エラーが表示される。README では特に目立つので事前に検出する。
#
# mermaid-cli（描画までする公式ツール）は puppeteer の Chrome が NixOS で
# 起動しないため使えない。ここでは mermaid 本体のパーサだけを jsdom 上で
# 動かして構文を検査する。依存は一時ディレクトリに入れ，リポジトリには残さない。
#
#   bash tools/check_mermaid.sh
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 各 Markdown から mermaid ブロックを取り出す
python3 - "$WORK" <<'PY'
import re, sys, glob, os, io
work = sys.argv[1]
n = 0
files = ["README.md"] + sorted(glob.glob("docs/**/*.md", recursive=True)) \
        + sorted(glob.glob("experiments/**/*.md", recursive=True)) + ["results/README.md"]
for f in files:
    if not os.path.exists(f):
        continue
    for i, b in enumerate(re.findall(r"```mermaid\n(.*?)```", io.open(f, encoding="utf-8").read(), re.S), 1):
        name = f.replace("/", "_").replace(".md", "") + f"__{i}.mmd"
        io.open(os.path.join(work, name), "w", encoding="utf-8").write(b)
        n += 1
print(f"  mermaid 図 {n} 個を検査します")
PY

if ! ls "$WORK"/*.mmd >/dev/null 2>&1; then
    echo "  mermaid 図はありません。"
    exit 0
fi

cat > "$WORK/check.mjs" <<'JSEOF'
import { JSDOM } from 'jsdom';
import fs from 'fs';
const dom = new JSDOM('<!doctype html><html><body></body></html>');
for (const k of ['window','document','Element','SVGElement','Node','DOMParser','navigator']) {
  try { Object.defineProperty(globalThis, k, { value: dom.window[k], configurable: true, writable: true }); } catch {}
}
const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
let bad = 0;
for (const f of process.argv.slice(2)) {
  try { await mermaid.parse(fs.readFileSync(f, 'utf8')); console.log(`  ${f.split('/').pop()}: OK`); }
  catch (e) { bad++; console.log(`  ${f.split('/').pop()}: エラー — ${String(e.message).split('\n')[0]}`); }
}
process.exit(bad ? 1 : 0);
JSEOF

echo "  依存を取得中（一時ディレクトリ）..."
( cd "$WORK" && npm install --silent mermaid@11 jsdom >/dev/null 2>&1 )
node "$WORK/check.mjs" "$WORK"/*.mmd
