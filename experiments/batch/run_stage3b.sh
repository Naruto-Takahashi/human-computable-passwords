#!/usr/bin/env bash
# =============================================================================
# 段階3b: 崖の細分化 + 露出回数仮説の検証
# =============================================================================
#   1. table_add k=13,16,20（n_train=1000, 5ep）… 崩壊境界の細分化（各 ≈1.2h）
#   2. table_add_k26 / func_22（n_train=5000, 5ep）… 露出回数仮説の検証（各 ≈6〜7h）
# 各学習後に held-out 50件評価まで自動実行。full ログは results/logs/。
# =============================================================================
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"

run_one() {
    local algo=$1 stage=$2 n_train=$3
    local tag="${algo}_stage${stage}_n${n_train}"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ==="
    if ! $PY experiments/train_finetuning.py \
        --model "$MODEL" --algorithm "$algo" --paradigm pure \
        --stage "$stage" --n_shot 0 --n_train "$n_train" --epochs 5 \
        >"$log" 2>&1; then
        echo "!!! TRAIN FAILED: $tag（ログ: $log）"
        return 1
    fi
    local run_dir
    run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
    [ -z "$run_dir" ] && { echo "!!! run_dir 不明: $tag"; return 1; }
    echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag ==="
    $PY experiments/run_eval.py \
        --provider lora --model "$run_dir" --algorithm "$algo" \
        --stage "$stage" --n_shot 0 --n_test 50 --key_seeds 0 --data_seeds 0 \
        >>"$log" 2>&1 || { echo "!!! EVAL FAILED: $tag"; return 1; }
    grep -oP '正解率 \(Accuracy\): .*|"accuracy": [0-9.]+' "$log" | tail -1 || true
}

# ---- 1. 崖の細分化 ----
for k in 13 16 20; do
    run_one "table_add_k${k}" 2 1000 || true
done

# ---- 2. 露出回数仮説（n_train=5000） ----
run_one table_add_k26 2 5000 || true
run_one func_22 2 5000 || true

python3 experiments/summarize.py >"$LOGDIR/summarize_3b.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 段階3b バッチ完了 ==="
