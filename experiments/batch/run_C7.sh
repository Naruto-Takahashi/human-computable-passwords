#!/usr/bin/env bash
# =============================================================================
# 実験C7: 同じ鍵・同じデータで，小川らの CNN は j 項を越えるか（2026-10-31 設計，11-05 見直し）
# =============================================================================
# Transformer の結果が分かっている鍵に，同じデータのまま小川らの埋め込み＋CNN を当て，
# 学習器の差と鍵の差を切り分ける（docs/experiment_index.md の実験C7）。
#
# このバッチで回すもの（順に）:
#   1. 再現の確認: Transformer を C2 と同じ設定・同じスレッド数（4）で5 run
#      （f22，鍵 seed 20260927〜20260931 × 初期値700）。C2 の保存値と3状態が一致するかを見る
#   2. 腕①: CNN，f22（C2 の鍵20本 seed 20260927〜20260946）× 初期値 700〜703 = 80 run
#      初期値 700・701 の40 run を先に，702・703 を後に回す（途中で止めても2通りで比べられる）
#   3. 腕②の関門: CNN，f13（C6 の鍵15本の高い版）× 初期値700 = 15 run
#      1本でも検証正解率の最大が 0.40 以上なら，残りの45 run を別のバッチで回す
#
# CNN の予算は小川らの卒論の付録のコードどおり（バッチ25・200エポック，Adam 既定）。
# データは鍵 seed（と付け替え）だけで決まるので，C2・C6 の Transformer と完全に同じ。
# run 数: 5 + 80 + 15 = 100。1 run 約15〜20分（8並列・2スレッド），全体で約3.5時間。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_C7.sh
#   nohup bash experiments/batch/run_C7.sh > results/logs/C7.out 2>&1 & disown
#
# 集計: results/path_c/C7/*.jsonl を model・algorithm・key_seed・digit_perm で仕分ける。
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

# 腕②の関門: C6 の高い版（select_C6_keys.py の出力，run_C6.sh の HIGH と同じ）
HIGH="60000000:6013749825 60000001:8014365972 60000002:1947802563 60000007:6031258794 \
60000023:5643781092 60000025:4230567189 60000027:5618029473 60000028:1632784905 \
60000029:1693254078 60000032:8761032459 60000036:3071269584 60000041:7384296051 \
60000045:4302817659 60000048:1896523470 60000064:4716598302"

CNN="--model cnn --datasize 50000 --epochs 200 --batch_size 25 --experiment C7"
# C2 の Transformer と同じ引数（run_C2.sh の COMMON）。スレッド数も C2 の4にそろえる
TRF="--model transformer --algorithm func_22 --datasize 50000 --epochs 100 --readout cls \
--d_model 32 --num_layers 2 --key_seed_base 20260927 --n_keys 5 --runs 5 --init_seed_base 700 --experiment C7"

plan() {
  echo "4 $TRF"
  for i in 700 702; do
    for s in $(seq 20260927 20260946); do
      echo "$THREADS --algorithm func_22 --key_seeds $s --init_seed_base $i --runs 2 $CNN"
    done
  done
  for hi in $HIGH; do
    echo "$THREADS --algorithm func_13_k26 --key_seeds ${hi%%:*} --digit_perm ${hi##*:} \
--init_seed_base 700 --runs 1 $CNN"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験C7: ${N} プロセス / 100 run を ${JOBS} 並列 ==="
echo "    再現の確認（Transformer 5 run）→ 腕① CNN f22 80 run → 腕②の関門 CNN f13 高い版 15 run"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
# 各行の先頭はスレッド数（再現の確認だけ C2 と同じ4）
plan | xargs -P "$JOBS" -I{} sh -c \
  'set -- {}; t=$1; shift; OMP_NUM_THREADS=$t TF_NUM_INTRAOP_THREADS=$t TF_NUM_INTEROP_THREADS=1 \
  '"$PY"' experiments/train_pathC.py "$@" 2>/dev/null | grep -E "run[0-9]|±"'
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: 再現の確認を C2 と突き合わせ，腕①を鍵ごとの対・分散分解・偏相関に，関門は 0.40 以上の本数を数える"
