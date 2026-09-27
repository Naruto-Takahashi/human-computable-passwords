#!/usr/bin/env bash
# =============================================================================
# 実験C1 の予備実験1〜4（経路C: Transformer を1から学習）
# =============================================================================
# なぜこれを回すのか:
#   予備実験0 で，読み出しを `flatten` にすると統制すら床に落ちることが分かった
#   （mean/cls は 1.0000）。1構成だけで「Transformer では解けない」と書けば，
#   読み出しの選択をアーキテクチャの限界と取り違えていた。残る3つの不確かさを
#   潰してから本実験に入る。
#
#   1: 統制が天井に届くデータ量はどこか（届かなければ C1 は組めない）
#   2: 反復数 R をいくつにすべきか（標準偏差から決める）
#   3: 予算（エポック・データ量）が天井を作っていないか
#   4: 構成（規模・読み出し・学習率）に結果が依存しないか
#
# **GPU は使わない。**TensorFlow が CUDA を見つけられないためで，かつ実測で
# GPU（Keras 3 の torch バックエンド）は速くならなかった（モデルが小さく
# 1ステップあたりの起動費が支配するため）。20コアの CPU を分割して
# 複数条件を同時に回す方が速い。経路A・B の GPU 実験と並行できる。
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_pathC_pre.sh      # 疎通確認
#   nohup bash experiments/batch/run_pathC_pre.sh \
#     > results/logs/pathC_pre.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

JOBS=${HCP_JOBS:-5}            # 同時に走らせる条件数（20コア ÷ 4スレッド）
THREADS=${HCP_THREADS:-4}
PY=.venv/bin/python
CONTROLS="func_pow table_add3_k26 narrowptr_k26_m1"

# 条件を1行1コマンドで組み立て，xargs -P で並列に流す。
# bash はバイト位置で逐次読むので，走行中にこのファイルを編集しないこと（CLAUDE.md）。
plan() {
  # 予備実験1: 統制が天井に届くデータ量（3関数 × 3データ量 × 3run = 27）
  for a in $CONTROLS; do
    for d in 1000 10000 50000; do
      echo "--algorithm $a --datasize $d --epochs 30 --runs 3 --experiment C1pre1"
    done
  done
  # 予備実験2: 反復数 R の決定（j 項ありの分散を 20 run で測る）
  echo "--algorithm func_22 --datasize 10000 --epochs 30 --runs 20 --experiment C1pre2"
  # 予備実験3: 予算が天井を作っていないか（エポック × データ量，各3run）
  for e in 30 100 300; do
    for d in 10000 50000; do
      echo "--algorithm func_22 --datasize $d --epochs $e --runs 3 --experiment C1pre3"
    done
  done
  # 予備実験4: 構成の3軸（規模・読み出し・学習率），各3run
  for dm in 32 64 128; do
    echo "--algorithm func_22 --datasize 50000 --epochs 30 --runs 3 --d_model $dm --experiment C1pre4_size"
  done
  for nl in 1 2 4; do
    echo "--algorithm func_22 --datasize 50000 --epochs 30 --runs 3 --num_layers $nl --experiment C1pre4_size"
  done
  for r in mean cls flatten; do
    # 統制も一緒に回す。j 項ありだけ見ても「読み出しが悪いのか」が分からない
    echo "--algorithm func_22 table_add3_k26 --datasize 50000 --epochs 30 --runs 3 --readout $r --experiment C1pre4_readout"
  done
  for lr in 1e-3 3e-4 1e-4; do
    echo "--algorithm func_22 --datasize 50000 --epochs 30 --runs 3 --learning_rate $lr --experiment C1pre4_lr"
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 経路C 予備実験1〜4: ${N} 条件を ${JOBS} 並列 ==="
plan | nl

if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない（引数の妥当性だけ確認する）"
  plan | HCP_DRY_RUN=1 xargs -P "$JOBS" -I{} sh -c "$PY experiments/train_pathC.py {} 2>/dev/null | head -1"
  exit 0
fi

export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "echo \"[\$(date '+%H:%M')] 開始 {}\"; $PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
