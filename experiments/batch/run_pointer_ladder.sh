#!/usr/bin/env bash
# =============================================================================
# 動的参照のみを単独で測る診断バッチ（pointer_k10 / pointer_k26）
#   Z = X[j]（j = (X10+X11) mod 10，足し算なし）
# table_add_k{同じk} と表サイズを揃えることで，「静的な2箇所参照+足し算」と
# 「動的な参照先決定+単純な読み出し」を同一データ量で比較する．
# 各学習後に held-out 50件評価まで自動実行．
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"

run_one() {
    local algo=$1 n_train=$2
    local tag="${algo}_stage2_n${n_train}"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$algo" --paradigm pure --stage 2 --n_shot 0 --n_train "$n_train" --epochs 5 >>"$log" 2>&1; then
        local run_dir
        run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
        echo "run_dir=$run_dir" >> "$log"
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$algo" --stage 2 --n_shot 0 --n_test 50 --key_seeds 0 --data_seeds 0 >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

run_one pointer_k10 1000
run_one pointer_k26 1000
run_one pointer_k26 5000

python3 experiments/summarize.py >"$LOGDIR/summarize_pointer.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] pointer ladder バッチ完了 ===" >> "$LOGDIR/pointer_batch_done.log"
