#!/usr/bin/env bash
# =============================================================================
# 週次報告のMarkdownをPDFに変換する
#
# 使い方:
#   docs/reports/to_pdf.sh weekly_report_20260818.md
#   docs/reports/to_pdf.sh                            # 最新の週次報告を自動選択
#
# 出力先: docs/reports/pdf/<同名>.pdf
# 初回は texliveFull の取得に時間がかかる場合があります。
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
OUT="$OUTDIR/$(basename "${SRC%.md}").pdf"

echo "[INFO] $SRC → $OUT"
nix-shell -p pandoc texliveFull --run "
pandoc '$SRC' -o '$OUT' \
  --pdf-engine=lualatex \
  -V documentclass=ltjsarticle \
  -V geometry:margin=22mm \
  -V mainfont='Noto Serif CJK JP' \
  -V linkcolor=blue
"
echo "[OK] 生成しました: $OUT"
