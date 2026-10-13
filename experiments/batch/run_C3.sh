#!/usr/bin/env bash
# =============================================================================
# 実験C3: N≈100 の壁は「記号の数」か「鍵の分布」か（2026-10-13 設計，双子の鍵）
# =============================================================================
# 学習の問題は「記号の数 N」と「鍵の各数字の個数（分布 p）」だけで決まる
# （入力は一様，埋め込みは記号ごとに独立なので，記号の並べ替えに対して対称）。
# ランダムな鍵で N=26→100 にすると両方が同時に変わる（N が増え，p は一様に近づく）。
# 双子の鍵（N=26 の鍵を4回並べた N=104 の鍵。p が厳密に一致）で片方ずつ動かす。
#
#   ① 元の鍵   N=26,  C2 の鍵20本            … C2 の再実行（実験内の比較相手）
#   ② 双子     N=104, C2 の鍵20本 × 4回並べ   … ①と比べて N の効果
#   ③ ランダム N=104, 連番 seed 10本          … ②と比べて分布の効果
#
# 予算:
#   B1 = 50,000件 × 100エポック  … C2 と同一（①②③）
#   B2 = 200,000件 × 25エポック  … 1記号あたりの出現数を N=26・B1 に揃え，
#        更新ステップ数（62,500）も B1 に揃える（②③のみ。N=26 では B1 と同じ意味）
#
# 関数: f_{2,2}（func_22 / func_22_k104），f_{1,3}（func_13_k26 / func_13_k104）
# 初期値: 700, 701（C2 と同じ）。解析の単位は鍵，①②は同じ鍵・同じ初期値で1対1に対応。
# run 数: ① 80 + ② 160 + ③ 80 = 320。1 run 約8分，20並列で約2.5〜3時間。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C3.sh
#   nohup env HCP_JOBS=20 HCP_THREADS=1 bash experiments/batch/run_C3.sh \
#     > results/logs/C3.out 2>&1 & disown
#
# 集計: jsonl を直接読む。腕は algorithm（k26/k104）と tile_key（4=双子, 1=ランダム）で，
#       予算は datasize で区別できる。
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-20}
THREADS=${HCP_THREADS:-1}
PY=.venv/bin/python

seq_csv() { seq -s, "$1" "$2"; }
C2_A=$(seq_csv 20260927 20260936)   # C2 の鍵 前半10本
C2_B=$(seq_csv 20260937 20260946)   # C2 の鍵 後半10本
RAND=$(seq_csv 40000000 40000009)   # ランダムな N=104 の鍵

B1="--datasize 50000 --epochs 100"
B2="--datasize 200000 --epochs 25"
COMMON="--readout cls --d_model 32 --num_layers 2 --learning_rate 0.001 \
--warmup_epochs 0 --runs 10 --experiment C3"

plan() {
  for pair in "func_22 func_22_k104" "func_13_k26 func_13_k104"; do
    set -- $pair
    a26=$1; a104=$2
    for i in 700 701; do
      for half in "$C2_A" "$C2_B"; do
        echo "--algorithm $a26 --key_seeds $half --init_seed_base $i $B1 $COMMON"
        echo "--algorithm $a104 --tile_key 4 --key_seeds $half --init_seed_base $i $B1 $COMMON"
        echo "--algorithm $a104 --tile_key 4 --key_seeds $half --init_seed_base $i $B2 $COMMON"
      done
      echo "--algorithm $a104 --key_seeds $RAND --init_seed_base $i $B1 $COMMON"
      echo "--algorithm $a104 --key_seeds $RAND --init_seed_base $i $B2 $COMMON"
    done
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C3: ${N} プロセス / $((N * 10)) run を ${JOBS} 並列 ==="
echo "    ① N=26 元の鍵(B1) ② N=104 双子(B1,B2) ③ N=104 ランダム(B1,B2) × f22・f13 × 初期値2"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: results/path_c/C3/*.jsonl を algorithm・tile_key・datasize で腕と予算に分け，鍵単位で比べる"
