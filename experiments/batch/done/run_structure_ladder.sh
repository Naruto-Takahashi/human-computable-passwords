#!/usr/bin/env bash
# =============================================================================
# 実験3: 動的参照の「構造」を振る3点比較
#
# 8月のご指示（動的参照を増やす方向でLLMの限界を探る）に対し，これまで
# pointer_chain（深さ方向）しか実験していなかった。しかもそれは3候補の中で
# 唯一，不動点により問題が自明化する欠陥を持っていた（weekly_report_20260819 §3.2-3.3）。
# 残る dualptr / recptr は同じ欠陥を持たないため，そのまま実験できる。
#
# 3関数はいずれも末尾に足し算があり（k2>0），答えの値の種類10・衝突確率
# 10〜12%（偶然水準近傍）であることを確認済み。したがって
# 「動的参照の構造」だけを変数にした公平な比較になる。
#
#   func_22_k10 : 動的参照1本            … 基準線（今回 k=10 版を追加）
#   dualptr_k10 : 独立な2本（並列）
#   recptr_k10  : 依存する2本（直列）
#
# 鍵は深さラダーの再評価で使った偏りの少ない2種類（key_seed=1,2）。
# 学習条件は深さラダーと完全に同一（pure/stage2/n_train=1000/epochs=5）。
# 評価は500件（§4.1 の知見：50件では点推定が最大13ポイントずれる）。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"
N_TEST=500

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
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag (n_test=$N_TEST) ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$algo" \
            --stage 2 --n_shot 0 --n_test "$N_TEST" --key_seeds "$key_seed" --data_seeds 0 \
            >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

# 基準線を先に回す（これが無いと他の2つを解釈できないため）
for ks in 1 2; do
    run_one func_22_k10 "$ks"
done
for ks in 1 2; do
    run_one dualptr_k10 "$ks"
    run_one recptr_k10  "$ks"
done

$PY experiments/summarize.py >"$LOGDIR/summarize_structure_ladder.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験3 構造ラダー バッチ完了 ===" >> "$LOGDIR/structure_ladder_done.log"
