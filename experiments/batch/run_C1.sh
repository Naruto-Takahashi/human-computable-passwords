#!/usr/bin/env bash
# =============================================================================
# 実験C1: 1から学習した Transformer は j 項をどこまで解くか（2026-09-27）
# =============================================================================
# H-C1′: j 項の壁は self-attention で消える。ただし消えるのは観測密度が高い
#        領域に限られ，崩壊点を決めるのは理論指標 s(f) ではなく観測密度である。
#
#   予測    : N=26・50,000件で f13 / f22 / f31 の3つとも離陸率 > 0 になり，
#             s(f) の順に並ばない
#   反証条件: 離陸率が s(f) の順（f13 < f22 < f31）に並ぶ。理論指標が学習
#             可能性を予測していることになる。あるいは f13 が全く離陸しない
#             （小川らと同じ）なら，壁は関数によって残る
#
# 構成は予備実験0〜4 で決めた（docs/experiment_index.md 実験C1）:
#   読み出し cls / d_model 32 / 2層 / lr 1e-3 / 100エポック
#   100エポック: 離陸した33 run すべてが val 0.9 を第37エポックまでに超える。
#                第38エポック以降の離陸は1本もない。300 は無駄で 30 は足りない
#   d_model 32 : 離陸は dm64 と同等以上で 2.4 倍速い（128 は崩壊）
#
# 反復は「鍵5本 × 初期値4通り = 20」。鍵 seed と初期化 seed を分けたので，
# ばらつきを鍵由来と初期化由来に分解できる（実験7 の先）。
# 1,000/5,000 件は予備実験で全条件が床（丸暗記）と分かっているので鍵5本のみ。
#
# 追試の規則（結果を見てから回す）:
#   - ある関数が 50,000件で 0/20 → その関数を mean・dm64・4層でも回して
#     構成依存でないことを確かめる
#   - 第100エポックで val がまだ上昇中の run → その run だけ 400 で回し直す
#
# N=100 と「10,000〜50,000 のどこに閾値があるか」は実験C2 とする。
# N=50 は本実験に含める（1エポック4秒の実測から，2つの鍵サイズで約5時間）。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C1.sh
#   nohup bash experiments/batch/run_C1.sh > results/logs/C1.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-5}
THREADS=${HCP_THREADS:-4}
PY=.venv/bin/python
COMMON="--epochs 100 --readout cls --d_model 32 --num_layers 2 --n_keys 5 --experiment C1"

# 鍵サイズ 26（小川らの主設定）と 50（第2列）。関数の役は同じ。
ALGOS_K26="func_13_k26 func_22 func_31 func_pow"
ALGOS_K50="func_13_k50 func_22_k50 func_31_k50 func_pow_k50"

# R=20 は「鍵5本 × 初期値4通り」だが，1コマンドで20run を回すと1プロセスが
# 2時間以上占有して並列の枠が埋まらない。初期値ごとに4分割して投げる
# （--init_seed_base をずらすだけで，合計は 5鍵 × 4初期値 と同一）。
plan() {
  for a in $ALGOS_K26 $ALGOS_K50; do
    for d in 1000 5000; do
      echo "--algorithm $a --datasize $d --runs 5 --init_seed_base 700 $COMMON"
    done
    for d in 10000 50000; do
      for i in 700 701 702 703; do
        echo "--algorithm $a --datasize $d --runs 5 --init_seed_base $i $COMMON"
      done
    done
  done
}

N=$(plan | wc -l)
R=$(plan | grep -oE -- "--runs [0-9]+" | awk '{s+=$2} END {print s}')
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C1: ${N} 条件 / ${R} run を ${JOBS} 並列 ==="
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
