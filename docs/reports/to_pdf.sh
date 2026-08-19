#!/usr/bin/env bash
# =============================================================================
# 週次報告のMarkdownをPDFに変換する（Markdown -> HTML -> PDF）
#
# 使い方:
#   docs/reports/to_pdf.sh weekly_report_20260818.md
#   docs/reports/to_pdf.sh                            # 最新の週次報告を自動選択
#   docs/reports/to_pdf.sh --send                     # 生成後 Taildrop で手元へ送る
#   docs/reports/to_pdf.sh weekly_report_20260818.md --send
#
# 出力先: docs/reports/pdf/<同名>.pdf
#
# --send について:
#   このマシン(研究室)へは自宅から Tailscale 経由でSSH接続しているため，
#   生成したPDFはそのままでは手元に無い。Taildrop で直接送る。
#   受信先は SEND_TO で変更可（既定 surface-pro）。
#   初回のみ `sudo tailscale set --operator=$USER` が必要（設定済み）。
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

SEND_TO="${SEND_TO:-surface-pro}"
SEND=0
ARGS=()
for a in "$@"; do
    case "$a" in
        --send) SEND=1 ;;
        *) ARGS+=("$a") ;;
    esac
done
set -- "${ARGS[@]:-}"

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

if [ "$SEND" -eq 1 ]; then
    echo "[INFO] Taildrop で $SEND_TO へ送信中..."
    if tailscale file cp "$OUT" "${SEND_TO}:"; then
        echo "[OK] $SEND_TO のダウンロードフォルダに届きました"
    else
        echo "[ERROR] 送信に失敗しました。" >&2
        echo "        初回は once: sudo tailscale set --operator=\$USER が必要です。" >&2
        echo "        受信先を変えるには SEND_TO=<マシン名> を指定してください。" >&2
        exit 1
    fi
fi
