#!/usr/bin/env bash
# =============================================================================
# 手元のマシンへファイルを送る（Tailscale Taildrop）
#
# この研究室PCへは自宅から Tailscale 経由でSSH接続しているため，ここで生成した
# 図表・PDF・CSV などはそのままでは手元に無い。Taildrop で直接送る。
#
# 使い方:
#   scripts/send.sh results/figures/phase_transition.png
#   scripts/send.sh docs/reports/pdf/*.pdf            # 複数可
#   SEND_TO=other-machine scripts/send.sh file.csv    # 送り先を変える
#
# 送り先の既定は surface-pro。届け先は受信側のダウンロードフォルダ。
# 初回のみ受信側ではなく送信側(このPC)で以下が必要:
#   sudo tailscale set --operator=$USER
# =============================================================================
set -euo pipefail
SEND_TO="${SEND_TO:-surface-pro}"

if [ $# -eq 0 ]; then
    echo "使い方: $(basename "$0") <ファイル> [ファイル...]" >&2
    echo >&2
    echo "送信可能なマシン:" >&2
    tailscale status 2>/dev/null | awk '$1 ~ /^100\./ {printf "  %s (%s)\n", $2, $4}' >&2
    exit 1
fi

for f in "$@"; do
    if [ ! -f "$f" ]; then
        echo "[SKIP] ファイルがありません: $f" >&2
        continue
    fi
    printf '[SEND] %s -> %s ... ' "$f" "$SEND_TO"
    if tailscale file cp "$f" "${SEND_TO}:" 2>/dev/null; then
        echo "OK"
    else
        echo "失敗"
        echo "       初回は 'sudo tailscale set --operator=\$USER' が必要です。" >&2
        exit 1
    fi
done
echo "[DONE] $SEND_TO のダウンロードフォルダを確認してください。"
