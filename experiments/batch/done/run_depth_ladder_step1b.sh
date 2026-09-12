#!/usr/bin/env bash
# =============================================================================
# 段階2-1b: 深さ1 vs 深さ2 を，偏りの小さい鍵で再確認
# key_seed=0（最頻値3/10=30%水準）は鍵の偏りが強く，「常に最頻値」戦略だけで
# 高い基準線になってしまうことが判明した。key_seed=1, 2（どちらも最頻値2/10=
# 20%水準）という，通常のランダム生成の中から偏りの小さいものを選んで
# 再実行し，d1→d2の逆転（36%→46%, key_seed=0）が鍵固有のノイズだったのか
# 再現する現象なのかを確認する。
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
    run_one pointer_chain_k10_d1 "$ks"
    run_one pointer_chain_k10_d2 "$ks"
done

python3 experiments/summarize.py >"$LOGDIR/summarize_depth_step1b.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 段階2-1b バッチ完了 ===" >> "$LOGDIR/depth_step1b_done.log"
