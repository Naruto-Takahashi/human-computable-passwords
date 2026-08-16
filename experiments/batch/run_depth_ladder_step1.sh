#!/usr/bin/env bash
# =============================================================================
# 段階2-1: 深さ1 vs 深さ2 の最小比較（指導教員指示 #pointer chasing）
# 既存 pointer_k10（34%, paradigm=pure, stage=2, n_shot=0, n_train=1000,
# epochs=5, key_seed=0, data_seed=0）と完全に同一条件で
# pointer_chain_k10_d1（再学習，学習のばらつき込みの対照）と
# pointer_chain_k10_d2 を学習・評価する。
# 手順書の例コマンドは --paradigm rationale だったが，既存34%結果との
# 「完全に同一条件」比較を優先し pure に揃えた（docs/log.md に理由を記録）。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"

run_one() {
    local algo=$1
    local tag="${algo}_stage2_n1000"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$algo" \
        --paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5 \
        --key_seed 0 --data_seed 0 >>"$log" 2>&1; then
        local run_dir
        run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
        echo "run_dir=$run_dir" >> "$log"
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$algo" \
            --stage 2 --n_shot 0 --n_test 50 --key_seeds 0 --data_seeds 0 >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

run_one pointer_chain_k10_d1
run_one pointer_chain_k10_d2

python3 experiments/summarize.py >"$LOGDIR/summarize_depth_step1.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 段階2-1 バッチ完了 ===" >> "$LOGDIR/depth_step1_done.log"
