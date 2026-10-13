#!/usr/bin/env bash
# =============================================================================
# N=100 段階A追加: 学習率を下げると統制の停滞が直るか（2026-10-12 設計）
# =============================================================================
# warmup{0,5エポック}だけでは統制 func_pow_k100 の停滞（エポック0から完全に
# 平坦）はほとんど直らなかった（docs/experiment_index.md の該当節，
# run_n100_warmup_probe.sh の結果: 離陸数は1/5→1/5で変わらず，鍵の入れ替わり
# だけだった）。
#
# 「最初から全く動かない」という形は，学習率過大による初期の勾当の暴れが
# 良い基底に入れずに固定点へ落ちる典型的な症状に近い。N=26→100で系列長が
# 伸びたことで注意機構の勾当スケールが変わっている可能性があるため，学習率
# そのものを下げて確かめる。
#
# lr=1e-3（既定値）は run_n100_datasize_probe.sh（datasize=50000, warmup=0,
# d_model=32, 同じ5鍵）で既に走らせたデータをそのまま基準線として使う
# （再実行しない）。ここでは lr=3e-4 と 1e-4 の2条件だけを新たに走らせる。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_n100_lr_probe.sh
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_n100_lr_probe.sh \
#     > results/logs/n100_lr_probe.out 2>&1 & disown
#
# 比較用の基準線（lr=1e-3）: results/path_c/n100_datasize_probe/*.jsonl の
# datasize=50000 の行を読むこと。
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

COMMON="--algorithm func_pow_k100 --datasize 50000 --d_model 32 --readout cls \
--num_layers 2 --warmup_epochs 0 --n_keys 5 --runs 5 --epochs 30 --experiment n100_lr_probe"

plan() {
  for lr in 0.0003 0.0001; do
    echo "--learning_rate $lr $COMMON"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] N=100 lr追加検証: ${N} 条件 / $((N * 5)) run を ${JOBS} 並列 ==="
echo "    統制 func_pow_k100・d_model=32・50,000件・warmupなし・lr{3e-4,1e-4}・鍵5本"
echo "    基準線 lr=1e-3 は results/path_c/n100_datasize_probe/*.jsonl (datasize=50000) を流用"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: results/path_c/n100_lr_probe/*.jsonl と n100_datasize_probe(datasize=50000)をlrで比べる"
