#!/usr/bin/env bash
# =============================================================================
# N=100 段階A追加: warmupで統制の完全な停滞が直るか（2026-10-10 設計）
# =============================================================================
# 段階A（run_n100_datasize_probe.sh）で，統制 func_pow_k100 がデータ量を
# 50,000〜200,000に増やしても変わらず，検証正解率がエポック0から完全に
# 平坦だった（docs/experiment_index.md の該当節）。これは「データ不足」
# ではなく，N=26でd_model=128・warmupなしのときに見た崩壊パターンと同じ
# 形に見える。Nが大きくなると埋め込みテーブルが大きくなり，実質的に
# 容量が増えたことと同じ効果を持つのではないかという仮説を検証する。
#
# データ量は段階Aの最小値（50,000）に固定し，warmupの有無だけを振る。
# 鍵は段階Aと同じ5本（key_seed_baseの既定値で揃う）にして，直接比較できる
# ようにする。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_n100_warmup_probe.sh
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_n100_warmup_probe.sh \
#     > results/logs/n100_warmup_probe.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

COMMON="--algorithm func_pow_k100 --datasize 50000 --d_model 32 --readout cls \
--num_layers 2 --n_keys 5 --runs 5 --epochs 30 --experiment n100_warmup_probe"

plan() {
  for w in 0 5; do
    echo "--warmup_epochs $w $COMMON"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] N=100 warmup追加検証: ${N} 条件 / $((N * 5)) run を ${JOBS} 並列 ==="
echo "    統制 func_pow_k100・d_model=32・50,000件・warmup{0,5エポック}・鍵5本"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: results/path_c/n100_warmup_probe/*.jsonl を直接読んでwarmup有無で正解率を比べる"
