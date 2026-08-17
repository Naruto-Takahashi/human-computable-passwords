#!/usr/bin/env bash
# =============================================================================
# 段階2-2: 深さ3を，偏りの小さい鍵（key_seed=1, 2）で先行実行
# 深さ1↔2では明確な効果が確認できなかった（段階2-1b）。深さをさらに増やして
# 「そもそも深さは効かない」のか「もっと深くしないと効果が出ない」のかを
# 切り分けるため，depth=3 を同じ2鍵で実行する。dualptr/recptrはこの結果と
# 教授との相談を踏まえて後続で判断する。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"

run_one() {
    local algo=$1 key_seed=$2
    local tag="${algo}_ks${key_seed}_stage2_n1000"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$algo" \
        --paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5 \
        --key_seed "$key_seed" --data_seed 0 >>"$log" 2>&1; then
        local run_dir
        run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
        echo "run_dir=$run_dir" >> "$log"
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$algo" \
            --stage 2 --n_shot 0 --n_test 50 --key_seeds "$key_seed" --data_seeds 0 >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

for ks in 1 2; do
    run_one pointer_chain_k10_d3 "$ks"
done

python3 experiments/summarize.py >"$LOGDIR/summarize_depth_step2.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 段階2-2 バッチ完了 ===" >> "$LOGDIR/depth_step2_done.log"
