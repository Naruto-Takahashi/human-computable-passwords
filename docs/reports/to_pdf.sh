#!/usr/bin/env bash
# =============================================================================
# 週次報告のMarkdownをPDFに変換する（Markdown -> HTML -> PDF）
#
# 使い方:
#   docs/reports/to_pdf.sh weekly_report_20260818.md
#   docs/reports/to_pdf.sh                            # 最新の週次報告を自動選択
#
# 出力先: docs/reports/pdf/<同名>.pdf
#
# 経路について:
#   当初は pandoc + lualatex(ltjsarticle) を使っていたが，この環境の Noto CJK が
#   可変フォント（NotoSerifCJK-VF.otf.ttc）であるため，和文の太字が
#   "! Missing font identifier" で解決できずPDF化できなかった。
#   weasyprint は fontconfig 経由でウェイトを引くのでこの問題が起きない。
#   体裁は docs/reports/pdf_style.css で調整する。
# =============================================================================
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

SRC="${1:-}"
if [ -z "$SRC" ]; then
    SRC=$(ls -1 docs/reports/weekly_report_*.md | sort | tail -1)
    echo "[INFO] 入力を自動選択: $SRC"
else
    # ファイル名だけ渡された場合は docs/reports/ を補う
    [ -f "$SRC" ] || SRC="docs/reports/$SRC"
fi
[ -f "$SRC" ] || { echo "[ERROR] ファイルが見つかりません: $SRC" >&2; exit 1; }

OUTDIR=docs/reports/pdf
mkdir -p "$OUTDIR"
BASE="$(basename "${SRC%.md}")"
OUT="$OUTDIR/${BASE}.pdf"
TMP_HTML="$(mktemp -t "${BASE}.XXXXXX.html")"
trap 'rm -f "$TMP_HTML"' EXIT

echo "[INFO] $SRC → $OUT"
nix-shell -p pandoc python3Packages.weasyprint --run "
set -e
# --mathml: 数式をMathMLで出す（weasyprintが描画できる）
pandoc '$SRC' -f markdown -t html5 --standalone --mathml \
  --metadata title='' \
  -o '$TMP_HTML'
weasyprint '$TMP_HTML' '$OUT' -s docs/reports/pdf_style.css
"
echo "[OK] 生成しました: $OUT"
