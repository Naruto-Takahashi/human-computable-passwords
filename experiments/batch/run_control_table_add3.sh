#!/usr/bin/env bash
# =============================================================================
# 統制実験（指導教員レビュー対応）: table_add3_k10 / table_add3_k26
#   Z = (X0+X1+X2) mod 10 （中間結果の保持はあるが，添字＝動的参照としては使わない）
# pointer_k{同じk} と表サイズ・データ量を完全に揃えることで，
# 「動的参照（間接参照）」と「多段階推論・中間結果の保持」のどちらが
# 失敗の真因かを切り分ける対比実験．
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

# pointer_k10 (n=1000), pointer_k26 (n=1000, n=5000) と条件を揃える
run_one table_add3_k10 1000
run_one table_add3_k26 1000
run_one table_add3_k26 5000

python3 experiments/summarize.py >"$LOGDIR/summarize_control.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 統制実験バッチ完了 ===" >> "$LOGDIR/control_batch_done.log"
