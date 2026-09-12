#!/usr/bin/env bash
# =============================================================================
# status.sh — 走行中のバッチと，各条件の進捗を1画面で出す
# =============================================================================
# 長時間バッチが常時動く研究なので，「いまどこまで進んだか」を毎回
#   grep -c '✓' results/logs/....log
# と手打ちしていた。それを置き換える。
#
#   bash tools/status.sh          # 直近24時間に更新されたログ
#   bash tools/status.sh 72       # 直近72時間
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
HOURS="${1:-24}"
LOGDIR=results/logs

echo "===== 走行中のバッチ ====="
found=0
for f in experiments/batch/*.sh; do
    name=$(basename "$f")
    # pgrep のパターンに自分自身や grep が混ざらないよう，スクリプト名で厳密に引く
    pids=$(pgrep -f "bash .*${name}" 2>/dev/null | tr '\n' ' ')
    if [ -n "$pids" ]; then
        echo "  $name  (PID: ${pids% })"
        found=1
    fi
done
[ "$found" -eq 0 ] && echo "  （なし）"

echo
echo "===== 学習中のプロセス ====="
# 自分自身のシェル（パターン文字列を含むため pgrep に引っかかる）を除くために，
# python が train_finetuning.py を起動している行だけを残す。
# 同じ学習で親プロセスと worker が複数ヒットするので sort -u で畳む。
train_now=$(pgrep -a -f train_finetuning.py 2>/dev/null \
    | grep -E 'python[0-9.]* +[^ ]*train_finetuning\.py' \
    | sed -E 's/.*--algorithm +([^ ]+).*--key_seed +([^ ]+).*/  \1  (鍵 \2)/' \
    | sort -u)
if [ -n "$train_now" ]; then
    echo "$train_now"
else
    echo "  （なし — 評価中か，バッチが終了しています）"
fi

echo
echo "===== 直近 ${HOURS} 時間に更新されたログ ====="
printf "  %-46s %-10s %s\n" "ログ" "状態" "進捗"
find "$LOGDIR" -maxdepth 1 -name '*.log' -mmin "-$((HOURS * 60))" -print0 2>/dev/null \
  | sort -z \
  | while IFS= read -r -d '' f; do
    base=$(basename "$f" .log)
    # grep -c は一致0件でも "0" を出力しつつ終了コード1 を返すので，|| echo 0 を
    # 付けると "0\n0" になってしまう。|| true で終了コードだけ握り潰す。
    ok=$(grep -c '✓' "$f" 2>/dev/null || true)
    tot=$(grep -c '✓\|✗' "$f" 2>/dev/null || true)
    ok=${ok:-0}; tot=${tot:-0}
    if grep -q 'TRAIN FAILED' "$f" 2>/dev/null; then
        printf "  %-46s %-10s %s\n" "$base" "失敗" "-"
    elif [ "$tot" -gt 0 ]; then
        pct=$(awk -v a="$ok" -v b="$tot" 'BEGIN{printf "%.1f%%", (b?100*a/b:0)}')
        state=$([ "$tot" -ge 500 ] && echo "完了" || echo "評価中")
        printf "  %-46s %-10s %s/%s = %s\n" "$base" "$state" "$ok" "$tot" "$pct"
    else
        step=$(grep -oP '\d+%\|' "$f" 2>/dev/null | tail -1 | tr -d '|')
        printf "  %-46s %-10s %s\n" "$base" "学習中" "${step:-開始直後}"
    fi
done

echo
echo "===== 完了マーカー（直近5件） ====="
find "$LOGDIR" -maxdepth 1 -name '*_done.log' -printf '%T@ %p\n' 2>/dev/null \
  | sort -rn | head -5 | cut -d' ' -f2- \
  | while read -r f; do echo "  $(tail -1 "$f")"; done
[ -z "$(find "$LOGDIR" -maxdepth 1 -name '*_done.log' 2>/dev/null)" ] && echo "  （なし）"
exit 0
