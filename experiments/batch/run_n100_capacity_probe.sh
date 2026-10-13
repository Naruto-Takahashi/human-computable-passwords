#!/usr/bin/env bash
# =============================================================================
# N=100 段階B: 埋め込み容量(d_model)を増やすと統制の停滞が直るか（2026-10-12 設計）
# =============================================================================
# warmupだけ（run_n100_warmup_probe.sh）・lrだけ（run_n100_lr_probe.sh）を
# 振っても，統制 func_pow_k100 の停滞（4/5鍵が床，1/5だけ鍵依存で離陸）は
# 直らなかった。
#
# 実装を確認すると，Transformerへの入力系列長は N に関わらず常に14トークン
# 固定で，Nが効くのは「値の埋め込み（Embedding(input_dim=N, output_dim=d_model)）
# が区別すべき記号の種類数」である。N=26→100で記号数が増えても d_model=32
# のままなら，1記号あたりに使える表現力（埋め込み容量）は変わっていない。
#
# ここでは d_model を {32(既存流用), 64, 128} で振り，容量を増やせば停滞が
# 直るか確かめる。N=26では d_model=128 はwarmupなしで崩壊した実績があるため，
# 「128がダメ」と「128はwarmupが必要なだけ」を区別するよう，64・128は
# warmup{0,5}も同時に振る。
#
# d_model=32（warmup=0,5）は既存データをそのまま使う（再実行しない）：
#   results/path_c/n100_datasize_probe/*.jsonl （datasize=50000, warmup=0）
#   results/path_c/n100_warmup_probe/*.jsonl    （warmup=0,5 両方。0はこちらと同一条件）
#
# 使い方:
#   HCP_DRY_RUN=1 bash experiments/batch/run_n100_capacity_probe.sh
#   nohup env HCP_JOBS=8 HCP_THREADS=2 bash experiments/batch/run_n100_capacity_probe.sh \
#     > results/logs/n100_capacity_probe.out 2>&1 & disown
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-8}
THREADS=${HCP_THREADS:-2}
PY=.venv/bin/python

COMMON="--algorithm func_pow_k100 --datasize 50000 --readout cls \
--num_layers 2 --n_keys 5 --runs 5 --epochs 30 --experiment n100_capacity_probe"

plan() {
  for d in 64 128; do
    for w in 0 5; do
      echo "--d_model $d --warmup_epochs $w $COMMON"
    done
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] N=100 容量追加検証: ${N} 条件 / $((N * 5)) run を ${JOBS} 並列 ==="
echo "    統制 func_pow_k100・50,000件・d_model{64,128}×warmup{0,5}・鍵5本"
echo "    基準線 d_model=32 は n100_datasize_probe / n100_warmup_probe を流用"
plan | nl
if [ "${HCP_DRY_RUN:-}" = "1" ]; then
  echo "HCP_DRY_RUN=1 のため学習はしない"
  exit 0
fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]|±'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
echo "集計: results/path_c/n100_capacity_probe/*.jsonl をd_model×warmupで比べ，32系列(既存流用)と合わせて見る"
