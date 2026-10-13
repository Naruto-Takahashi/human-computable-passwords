#!/usr/bin/env bash
# =============================================================================
# N=100 段階A: 統制がどのデータ量で天井に届くか（2026-10-10 設計）
# =============================================================================
# N=100スケーリングの前提確認。小川さんらの報告では N=100 だと統制（no-j，
# 一番簡単な問題）すら50,000件で最大0.2118（データ密度不足）。もし統制が
# 床のままなら，次段階（容量×warmupの感度）を振っても「床で差が出ない」
# だけで何も分からない（「床にいるとき差が無いは効果の否定にならない」。
# docs/experiment_index.md 参照）。
#
# ここでは容量・warmupは固定（N=26で分かっている既定: d_model=32・cls・
# warmupなし。統制にはwarmupが無関係と確認済み）し，**データ量だけ**を
# 50,000/100,000/200,000で振って，統制 func_pow_k100 が天井（1.0近く）に
# 届く最小のデータ量を特定する。
#
# ここで届いたデータ量を，段階B（容量×warmupの感度，func_22_k100 と
# func_pow_k100 の両方）でそのまま使う。
#
# 鍵5本（「母数が少なすぎると結論が弱くなる」との指摘を受け，予備実験の
# 通例の3本から増やした）。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_n100_datasize_probe.sh
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_n100_datasize_probe.sh \
#     > results/logs/n100_datasize_probe.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

COMMON="--algorithm func_pow_k100 --d_model 32 --readout cls --num_layers 2 \
--n_keys 5 --runs 5 --epochs 30 --experiment n100_datasize_probe"

plan() {
  for d in 50000 100000 200000; do
    echo "--datasize $d $COMMON"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] N=100 段階A: ${N} 条件 / $((N * 5)) run を ${JOBS} 並列 ==="
echo "    統制 func_pow_k100・d_model=32・warmupなし・データ量{50000,100000,200000}・鍵5本"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: results/path_c/n100_datasize_probe/*.jsonl を直接読んでデータ量ごとの正解率を比べる"
