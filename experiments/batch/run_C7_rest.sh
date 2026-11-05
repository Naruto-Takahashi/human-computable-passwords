#!/usr/bin/env bash
# =============================================================================
# 実験C7 腕②の残り: 関門を通ったので，f13 の高い版の初期値701と低い版の初期値700・701を回す
# =============================================================================
# 関門（run_C7.sh の末尾，高い版15本 × 初期値700）で 60000027 の高い版が 0.71 に届いた
# （0.40 以上が1本以上という事前の条件を満たした，2026-11-06）。
# 高い版と低い版を鍵ごとの対にし，CNN でも I_1 の高い版だけが伸びるかを片側符号検定で見る
# （docs/experiment_index.md の実験C7，副次の比較 (d)）。
#
# 鍵と付け替え: C6 と同じ15本（results/path_c/C6_keys.json，run_C6.sh の LOW・HIGH）
# 予算: run_C7.sh の CNN と同じ（バッチ25・200エポック，Adam 既定）。
# run 数: 高い版 15 × 初期値701 + 低い版 15 × 初期値700・701 = 45。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C7_rest.sh
#   HCP_JOBS=5 nohup nice -n 10 bash experiments/batch/run_C7_rest.sh > results/logs/C7_rest.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

LOW="60000000:0245368719 60000001:8401762935 60000002:9570214368 60000007:3067594281 \
60000023:2364517980 60000025:7431086925 60000027:6892134507 60000028:2673089514 \
60000029:6947250381 60000032:9081452736 60000036:2507618394 60000041:2150964783 \
60000045:1674230859 60000048:0861973425 60000064:6320854917"
HIGH="60000000:6013749825 60000001:8014365972 60000002:1947802563 60000007:6031258794 \
60000023:5643781092 60000025:4230567189 60000027:5618029473 60000028:1632784905 \
60000029:1693254078 60000032:8761032459 60000036:3071269584 60000041:7384296051 \
60000045:4302817659 60000048:1896523470 60000064:4716598302"

CNN="--model cnn --algorithm func_13_k26 --datasize 50000 --epochs 200 --batch_size 25 --experiment C7"

plan() {
  set -- $HIGH
  for lo in $LOW; do
    hi=$1; shift
    echo "--key_seeds ${lo%%:*} --digit_perm ${lo##*:} --init_seed_base 700 --runs 2 $CNN"
    echo "--key_seeds ${hi%%:*} --digit_perm ${hi##*:} --init_seed_base 701 --runs 1 $CNN"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C7 腕②の残り: ${N} プロセス / 45 run を ${JOBS} 並列 ==="
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: f13 の CNN を鍵ごとに高い版・低い版の対にし（どちらかの初期値で「解けた」，少なければ「中間以上」），片側符号検定"
