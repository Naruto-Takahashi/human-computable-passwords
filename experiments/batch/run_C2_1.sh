#!/usr/bin/env bash
# =============================================================================
# 実験C2.1（H-C2″）: 鍵の偏りは，基準線を揃えても離陸率に効くか（2026-10-04 設計）
# =============================================================================
# 実験C2で「最多重複が離陸率に効く」という素の相関を見つけたが，最多重複は
# 鍵ごとの基準線（最頻値予測器の正解率）自体と強く相関しており（f31でrho=0.85），
# 固定しきい値（検証正解率>0.5）による離陸判定を経由した見かけの相関だった
# 疑いが強い（docs/experiment_index.md の実験C2「撤回」節）。
#
# 統計的に基準線を除く（偏相関）のではなく，**鍵の選び方そのもので基準線を
# 揃える**ことで検証する。`experiments/select_baseline_matched_keys.py` が
# 関数ごとに，基準線を狙った狭い帯（幅0.01）に揃えつつエントロピーが
# 広く散らばる鍵20本を，学習なしで（基準線は決定的に計算できる）選定済み
# （results/path_c/C2_1_keys.json）。
#
#   予測    : 基準線をほぼ揃えた鍵集合でも，エントロピーと離陸率の相関が残る
#   反証条件: 相関が消える。そのとき鍵の効果の正体は基準線のシフトだった
#             ことになる（f_2,2 はC2の時点ですでにこの形）
#
# 構成はC2と完全に同一（N=26・cls・d_model 32・2層・lr 1e-3・100エポック・
# 50,000件）。鍵の選び方と，鍵を明示的に渡す `--key_seeds`（今回追加した
# 引数）だけが違う。初期値の配分もC2と同じ非対称（f_2,2のみ4通り，交互作用
# 48%対策）。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C2_1.sh     # 条件一覧だけ出す
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_C2_1.sh \
#     > results/logs/C2_1.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

KEYS_FILE=results/path_c/C2_1_keys.json
if [ ! -f "$KEYS_FILE" ]; then
  echo "鍵選定が未実施: $PY experiments/select_baseline_matched_keys.py を先に実行"
  exit 1
fi

seeds_for() {  # $1=関数名
  $PY -c "import json,sys; d=json.load(open('$KEYS_FILE')); \
print(','.join(str(k['key_seed']) for k in d['$1']))"
}

SEEDS_F31=$(seeds_for func_31)
SEEDS_F22=$(seeds_for func_22)
SEEDS_F13=$(seeds_for func_13_k26)

COMMON="--datasize 50000 --epochs 100 --readout cls --d_model 32 --num_layers 2 \
--runs 20 --experiment C2_1"

plan() {
  for i in 700 701; do
    echo "--algorithm func_31 --key_seeds $SEEDS_F31 --init_seed_base $i $COMMON"
  done
  for i in 700 701; do
    echo "--algorithm func_13_k26 --key_seeds $SEEDS_F13 --init_seed_base $i $COMMON"
  done
  # f_2,2 だけ初期値4通り（実験C2と同じ理由。交互作用48%対策）
  for i in 700 701 702 703; do
    echo "--algorithm func_22 --key_seeds $SEEDS_F22 --init_seed_base $i $COMMON"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C2.1: ${N} 条件 / $((N * 20)) run を ${JOBS} 並列 ==="
echo "    基準線を揃えた鍵20本（帯幅0.01）× 初期値2通り（f31・f13）／4通り（f22）"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: .venv/bin/python tools/pathC_stats.py --experiment C2_1"
