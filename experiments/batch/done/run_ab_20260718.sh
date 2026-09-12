#!/usr/bin/env bash
# =============================================================================
# A+B バッチ（2026-07-18）
#   A: func_22 アダプタ（n_train=1000 / 5000）の held-out 評価を n_test=200 に拡大
#      （「偶然水準と区別できない」主張の統計的裏づけ）
#   B: table_add_k26 を n_train=5000・--exclude_pairs 50 で学習し，
#      除外ペアのみの評価で「暗記か合成か」を切り分け
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"

echo "=== [$(date '+%m/%d %H:%M:%S')] A: func_22 n_train=1000 を n_test=200 で再評価 ==="
$PY experiments/run_eval.py --provider lora \
    --model results/llm_finetune/qwen2.5_3b/func_22/run_20260716_210311 \
    --algorithm func_22 --stage 2 --n_shot 0 --n_test 200 \
    --key_seeds 0 --data_seeds 0 --overwrite \
    >"$LOGDIR/A_func22_n1000_ntest200.log" 2>&1 || echo "!!! A(n1000) FAILED"

echo "=== [$(date '+%m/%d %H:%M:%S')] A: func_22 n_train=5000 を n_test=200 で再評価 ==="
$PY experiments/run_eval.py --provider lora \
    --model results/llm_finetune/qwen2.5_3b/func_22/run_20260718_024256 \
    --algorithm func_22 --stage 2 --n_shot 0 --n_test 200 \
    --key_seeds 0 --data_seeds 0 --overwrite \
    >"$LOGDIR/A_func22_n5000_ntest200.log" 2>&1 || echo "!!! A(n5000) FAILED"

echo "=== [$(date '+%m/%d %H:%M:%S')] B: table_add_k26 n=5000 exclude_pairs=50 学習 ==="
BLOG="$LOGDIR/B_table_add_k26_n5000_excl50.log"
if $PY experiments/train_finetuning.py \
    --model Qwen/Qwen2.5-3B-Instruct --algorithm table_add_k26 --paradigm pure \
    --stage 2 --n_shot 0 --n_train 5000 --epochs 5 --exclude_pairs 50 \
    >"$BLOG" 2>&1; then
    RUN_DIR=$(grep -oP '(?<=^Results will be saved to: ).*' "$BLOG" | head -1)
    echo "=== [$(date '+%m/%d %H:%M:%S')] B: 通常 held-out 評価（含まれるペア中心） ==="
    $PY experiments/run_eval.py --provider lora --model "$RUN_DIR" \
        --algorithm table_add_k26 --stage 2 --n_shot 0 --n_test 50 \
        --key_seeds 0 --data_seeds 0 >>"$BLOG" 2>&1 || echo "!!! B held-out eval FAILED"
    echo "=== [$(date '+%m/%d %H:%M:%S')] B: 除外ペアのみの評価 ==="
    $PY experiments/eval_excluded_pairs.py --model "$RUN_DIR" --n_test 100 \
        >>"$BLOG" 2>&1 || echo "!!! B excluded eval FAILED"
else
    echo "!!! B TRAIN FAILED（ログ: $BLOG）"
fi

python3 experiments/summarize.py >"$LOGDIR/summarize_ab.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] A+B バッチ完了 ==="
