#!/usr/bin/env bash
# =============================================================================
# 週次報告のライブプレビュー（配信サーバ＋自動再ビルドを1つの窓で動かす）
#
#   make report-live        （このスクリプトを呼ぶだけ）
#   PORT=9000 make report-live
#
# 手元の端末からは SSH のポート転送で見る:
#   ssh -L 8765:localhost:8765 labpc
#   ブラウザで http://localhost:8765/preview.html
#
# Ctrl-C で配信サーバごと終了する。
# =============================================================================
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

PORT="${PORT:-8765}"
OUT=docs/reports/pdf

# 先に一度ビルドしておく（preview.html と latest.pdf もここで置かれる）
make report-latest

# 配信サーバを裏で起動し，終了時に確実に落とす
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$OUT" >/dev/null 2>&1 &
SERVER_PID=$!
cleanup() {
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
    echo ""
    echo "[INFO] 終了しました"
}
trap cleanup EXIT INT TERM

# サーバが立ち上がったか確認
sleep 0.5
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "[ERROR] ポート $PORT を使えませんでした。PORT=9000 make report-live のように変えてください。" >&2
    exit 1
fi

cat <<EOS

  ────────────────────────────────────────────────────────────
   手元のブラウザで  http://localhost:$PORT/preview.html
     転送:  ssh -L $PORT:localhost:$PORT labpc
   保存するたびに自動で再ビルドされます（Ctrl-C で終了）
  ────────────────────────────────────────────────────────────

EOS

# 監視は前面で回す。Ctrl-C がここに届き，trap でサーバも落ちる。
# 監視対象は Makefile 側に持たせている（ここで二重に書かない）。
make report-watch
