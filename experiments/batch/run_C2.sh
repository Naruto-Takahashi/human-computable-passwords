#!/usr/bin/env bash
# =============================================================================
# 実験C2: 破れやすい鍵とは何か（2026-09-28 設計）
# =============================================================================
# H-C2: 鍵の数字分布の偏り（エントロピーの低さ）が離陸しやすさを決める。
#       その効き方は k2（末尾の加算項の数）が小さいほど強い。
#
#   予測    : エントロピーと離陸率が負に相関し，相関の強さが
#             f31(k2=1) > f22(k2=2) > f13(k2=3) の順になる
#   反証条件: 相関が出ないか，k2 の順に並ばない。そのとき鍵の効果の正体は
#             エントロピー以外（数字の配置・衝突の構造など）にある
#
# 機構は原論文の r(f) = k2+1（Blocki ら §4.2）。末尾で足す項が少ないほど
# 鍵のヒストグラムの偏りがレスポンス分布に漏れる。k2=0 で完全に漏れることは
# 2026年8月に確認済みで（plan.md §3.1.1），H-C2 はその連続的な版である。
#
# **構成は実験C1 と完全に同一**（N=26・cls・d_model 32・2層・lr 1e-3・
# 100エポック・50,000件）。変えるのは鍵の本数だけ（5本 → 20本）。
# 実験C1 では鍵5本のため rho=-0.79 でも p=0.111 にしかならなかった。
# n=20 なら |rho| >= 0.44 で有意になる。
#
# 設計と検出力の検討は docs/experiment_index.md の実験C2 にある。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C2.sh     # 条件一覧だけ出す
#   nohup bash experiments/batch/run_C2.sh > results/logs/C2.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-5}
THREADS=${HCP_THREADS:-4}
PY=.venv/bin/python

# 鍵20本 × 初期値2通り = 40 run。--runs は n_keys で割られて初期値の通り数になる
# （key_index = run_index % n_keys, init は run_index / n_keys）。
# 1コマンドで 40 run を回すと1プロセスが長時間占有するので初期値ごとに分ける。
COMMON="--datasize 50000 --epochs 100 --readout cls --d_model 32 --num_layers 2 \
--n_keys 20 --runs 20 --experiment C2"

plan() {
  for a in func_31 func_22 func_13_k26; do
    for i in 700 701; do
      echo "--algorithm $a --init_seed_base $i $COMMON"
    done
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C2: ${N} 条件 / $((N * 20)) run を ${JOBS} 並列 ==="
echo "    鍵20本 × 初期値2通り × 3関数。1 run 約11分，見込み約4.5時間"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: .venv/bin/python tools/pathC_stats.py"
