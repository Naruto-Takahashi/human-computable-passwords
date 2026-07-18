#!/usr/bin/env bash
# results/ を Google Drive へ同期する（旧実装では各実験スクリプト内に
# ハードコードされていた処理を運用スクリプトとして分離）．
# 実験の後に手動または Makefile (make sync) から実行する．
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="$REPO_ROOT/results"
REMOTE="gdrive:human-computable-passwords-results"

if ! command -v rclone >/dev/null 2>&1; then
    echo "rclone が見つかりません" >&2
    exit 1
fi

echo "同期中: $RESULTS_DIR -> $REMOTE"
rclone sync "$RESULTS_DIR" "$REMOTE" --progress
echo "同期完了"
