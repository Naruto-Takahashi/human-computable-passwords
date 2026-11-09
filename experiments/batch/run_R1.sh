#!/usr/bin/env bash
# =============================================================================
# 実験R1: C2・C2.1 で決めた I_1 の閾値で，新しいランダムな鍵の離陸を当てられるか（2026-11-09 設計）
# =============================================================================
# 閾値と各鍵の予測は学習前に results/path_c/R1_prereg.json に書き出してコミット済み
# （experiments/analyze_R1.py prereg）。このバッチは予測された鍵をそのまま学習するだけ。
#
# 鍵: N=26 のランダムな鍵（選別しない）
#   f_{2,2}（func_22）    : seed 70000000〜70000029 の30本
#   f_{1,3}（func_13_k26）: seed 71000000〜71000029 の30本
# 構成・予算は C2 と同一（d_model 32・2層・cls・lr 1e-3・50,000件 × 100エポック）。初期値 700・701。
# run 数: 60鍵 × 2 = 120。1プロセス = 1鍵 × 初期値2通り（約35分）。10並列・2スレッドで約3.5時間。
# 2関数を交互に並べる（途中で止めても両関数がそろう）。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_R1.sh
#   nohup bash experiments/batch/run_R1.sh > results/logs/R1.out 2>&1 & disown
#
# 集計: python3 experiments/analyze_R1.py evaluate
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-10}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

COMMON="--datasize 50000 --epochs 100 --readout cls --d_model 32 --num_layers 2 \
--learning_rate 0.001 --warmup_epochs 0 --init_seed_base 700 --runs 2 --experiment R1"

plan() {
  for i in $(seq 0 29); do
    echo "--algorithm func_22 --key_seeds $((70000000 + i)) $COMMON"
    echo "--algorithm func_13_k26 --key_seeds $((71000000 + i)) $COMMON"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験R1: ${N} プロセス / $((N * 2)) run を ${JOBS} 並列 ==="
echo "    N=26 のランダムな鍵 f22・f13 各30本 × 初期値2（予測は R1_prereg.json に固定済み）"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: python3 experiments/analyze_R1.py evaluate"
