#!/usr/bin/env bash
# =============================================================================
# 実験C5: 数字の個数をそろえた鍵では学習攻撃は離陸しないか（2026-10-30 設計）
# =============================================================================
# 各数字を3個ずつ持つ N=30 の鍵（そろえた鍵）では数字の分布が厳密に一様になり，
# k2+1 個未満の位置と答えが無相関になる（I_1 = 0）。偏りを取り除く介入で
# 離陸が消えるかを，偏りの大きい鍵（陽性対照）と比べる。
#
#   ① そろえた鍵   seed 50000000〜50000014，--balanced_key
#   ② ランダムな鍵 seed 50000000〜50000014（選別しない）
#   ③ 偏りの大きい鍵 I_1 が帯に入る15本（experiments/select_C5_keys.py が選んだもの）
#
# 構成・予算は C2 と同一（d_model 32・2層・cls・lr 1e-3・50,000件 × 100エポック）。
# 関数: f_{2,2}（func_22_k30），f_{1,3}（func_13_k30）。初期値: 700, 701。
# run 数: 3腕 × 15鍵 × 2初期値 × 2関数 = 180。
# 主な比較は ① 対 ③ を鍵単位で（docs/experiment_index.md の実験C5）。
# 1 run 約17分（C2.1 の実測，8並列・2スレッド），全体で約6.4時間。
#
# 並べ方: 鍵を3本ずつの塊に分けて60プロセスにし，負荷をならす。
# 主な比較に要る f_{2,2} の ①③ を先に，② を最後に回す（途中で止めても主な比較が残る）。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C5.sh
#   nohup bash experiments/batch/run_C5.sh > results/logs/C5.out 2>&1 & disown
#
# 集計: jsonl を直接読む。腕は balanced_key（①）と key_seed の範囲（② 5000xxxx・③ 5100xxxx）で区別できる。
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

# 15本の鍵を3本ずつの塊に分ける
SEQ="50000000,50000001,50000002 50000003,50000004,50000005 50000006,50000007,50000008 \
50000009,50000010,50000011 50000012,50000013,50000014"
SKEW_22="51000000,51000001,51000003 51000008,51000016,51000024 51000029,51000030,51000032 \
51000035,51000045,51000058 51000067,51000073,51000078"
SKEW_13="51000003,51000008,51000016 51000024,51000029,51000035 51000045,51000058,51000069 \
51000078,51000081,51000136 51000146,51000147,51000156"

COMMON="--datasize 50000 --epochs 100 --readout cls --d_model 32 --num_layers 2 \
--learning_rate 0.001 --warmup_epochs 0 --runs 3 --experiment C5"

arm() {  # arm <関数> <鍵の塊> [--balanced_key]
  local algo=$1 chunks=$2 extra=${3:-}
  for i in 700 701; do
    for c in $chunks; do
      echo "--algorithm $algo --key_seeds $c --init_seed_base $i $extra $COMMON"
    done
  done
}

plan() {
  arm func_22_k30 "$SEQ" --balanced_key
  arm func_22_k30 "$SKEW_22"
  arm func_13_k30 "$SEQ" --balanced_key
  arm func_13_k30 "$SKEW_13"
  arm func_22_k30 "$SEQ"
  arm func_13_k30 "$SEQ"
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C5: ${N} プロセス / $((N * 3)) run を ${JOBS} 並列 ==="
echo "    ① そろえた鍵 ③ 偏りの大きい鍵 ② ランダムな鍵 × f22・f13（N=30）× 初期値2"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: results/path_c/C5/*.jsonl を鍵単位にまとめ（どちらかの初期値で離陸＝離陸），① 対 ③ を片側 Fisher で比べる"
