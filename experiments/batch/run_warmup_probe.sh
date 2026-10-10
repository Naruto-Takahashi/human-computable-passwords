#!/usr/bin/env bash
# =============================================================================
# warmup予備実験: d_model=128の崩壊はpost-LN＋warmupなしが原因か（2026-10-10 設計）
# =============================================================================
# 実験C1 予備実験4で d_model=128 にすると func_22 が崩壊することが分かったが，
# warmupを入れれば直るかは未検証だった（docs/experiment_index.md の実験C1，
# 構成の3軸）。これをN=100スケーリングの前に潰す。
#
# 統制（func_pow，h。j項なしの簡単な問題）も同じグリッドに含める。
# func_22 だけで測ると，崩壊が「j項の難しさとの相性」なのか「容量とwarmupなし
# の組み合わせそのものが持つ，タスクに依らない不安定性」なのかを区別できない
# （ユーザー指摘，2026-10-10）。
#
#   読み方:
#   - 統制も func_22 も d_model=128 で崩壊する     → タスクに依らない最適化問題
#   - 統制は崩壊せず func_22 だけ崩壊する          → j項の難しさとの相性
#   - warmupを入れるとどちらの崩壊も消える         → post-LN＋warmupなしが原因
#   - warmupを入れても崩壊が残る                   → 容量そのものが原因（別の対策が必要）
#
# 条件は予備実験4と揃える（N=26・30エポック）。warmupは全エポックの1/6
# （5エポック相当）。鍵3本×初期値1通り（予備実験4の「各3run」に合わせた）。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_warmup_probe.sh
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_warmup_probe.sh \
#     > results/logs/warmup_probe.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

COMMON="--datasize 50000 --epochs 30 --readout cls --num_layers 2 \
--n_keys 3 --runs 3 --experiment warmup_probe"

plan() {
  for a in func_22 func_pow; do
    for d in 32 64 128; do
      for w in 0 5; do
        echo "--algorithm $a --d_model $d --warmup_epochs $w $COMMON"
      done
    done
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] warmup予備実験: ${N} 条件 / $((N * 3)) run を ${JOBS} 並列 ==="
echo "    func_22・func_pow(統制) × d_model{32,64,128} × warmup{0,5エポック} × 鍵3本"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: tools/pathC_stats.py は func_22/func_pow 2関数構成に対応していないため使えない。"
echo "      results/path_c/warmup_probe/*.jsonl を直接読んで d_model×warmup×関数で正解率を比べる。"
