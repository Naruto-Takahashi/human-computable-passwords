#!/usr/bin/env bash
# =============================================================================
# 実験C2.1 の f_3,1 やり直し: 基準線0.13〜0.15の帯で選び直す（2026-10-05）
# =============================================================================
# 実験C2.1（run_C2_1.sh）で f_3,1 だけ低基準線（最小値+0.01）の帯を選んだ
# ために全40 runが離陸せず検証不能だった（docs/experiment_index.md の
# 実験C2.1）。実験C2の実測で，離陸した5鍵の基準線が0.1328〜0.1568だったため，
# `experiments/select_baseline_matched_keys.py --algorithms func_31` で
# 帯を [0.125, 0.165]（既知の離陸鍵全てに余裕を持たせた範囲）に固定して
# 選び直した（`BAND_OVERRIDE`）。帯の幅は他2関数の0.01より広いが，f_3,1 は
# 基準線の取りうる範囲自体が広い（約0.12）関数なので，relativeな比率では
# 他関数と同程度（約33%）である。基準線統制が効いているかは，結果が出たら
# 帯内の残差基準線で偏相関を取って別途確認する。
#
# 他の2関数（f_2,2・f_1,3）はC2.1の結果で十分なので回し直さない。
# f_3,1 だけを別の実験ラベル（C2_1_f31b）に出力し，低基準線帯の無効な
# run（C2_1）と混ざらないようにする。構成はC2.1と同一。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C2_1_f31.sh
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_C2_1_f31.sh \
#     > results/logs/C2_1_f31.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

KEYS_FILE=results/path_c/C2_1_keys.json
if [ ! -f "$KEYS_FILE" ]; then
  echo "鍵選定が未実施: $PY experiments/select_baseline_matched_keys.py --algorithms func_31 を先に実行"
  exit 1
fi

SEEDS_F31=$($PY -c "import json; d=json.load(open('$KEYS_FILE')); \
print(','.join(str(k['key_seed']) for k in d['func_31']))")

COMMON="--algorithm func_31 --key_seeds $SEEDS_F31 \
--datasize 50000 --epochs 100 --readout cls --d_model 32 --num_layers 2 \
--runs 20 --experiment C2_1_f31b"

plan() {
  for i in 700 701; do
    echo "--init_seed_base $i $COMMON"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C2.1 f_3,1やり直し: ${N} 条件 / $((N * 20)) run を ${JOBS} 並列 ==="
echo "    基準線0.125〜0.165の帯で選び直した鍵20本 × 初期値2通り"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: .venv/bin/python tools/pathC_stats.py --experiment C2_1_f31b"
