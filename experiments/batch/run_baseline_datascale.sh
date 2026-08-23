#!/usr/bin/env bash
# =============================================================================
# 段階4: 基準線を床から持ち上げられるか（学習データ量スイープ）
#
# 段階3（構造ラダー）で 6条件すべてが 10〜20% に張り付き，基準線
# func_22_k10 の時点で既に床にあった。このため「動的参照を増やすと
# 難しくなる」という仮説は下がる余地が無く，識別できなかった
# （weekly_report_20260823 §2.2）。
#
# 7月に table_add_k26（合成のみ）で前例がある：
#   n_train=1000 →   8%（床）
#   n_train=5000 → 100%（完全回復）
# 学習量だけで床から離れた。同じことが基準線でも起きるなら，その水準で
# 3点比較をやり直す価値がある。起きないなら，構造の効果をFTで測ること
# 自体が難しいと判断できる。
#
# まず基準線1条件だけを振る（構造ラダー全体をやり直す前の判定）。
#   func_22_k10 × key_seed=1 × n_train ∈ {3000, 5000}
#   （n_train=1000 は段階3で実施済み: 13.0%）
#
# 学習時間は n_train に比例し，1000件で約2時間。したがって
# 3000件で約6時間，5000件で約10時間，合計16時間程度。
# 面談（8/26）まで4日あるため収まる。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"
N_TEST=500
ALGO=func_22_k10
KEY_SEED=1

run_one() {
    local n_train=$1
    local tag="${ALGO}_ks${KEY_SEED}_stage2_n${n_train}"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$ALGO" \
        --paradigm pure --stage 2 --n_shot 0 --n_train "$n_train" --epochs 5 \
        --key_seed "$KEY_SEED" --data_seed 0 >>"$log" 2>&1; then
        local run_dir
        run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
        echo "run_dir=$run_dir" >> "$log"
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag (n_test=$N_TEST) ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$ALGO" \
            --stage 2 --n_shot 0 --n_test "$N_TEST" --key_seeds "$KEY_SEED" --data_seeds 0 \
            >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

# 少ない方から回す。3000件で明確に上がるなら5000件を待たずに判断できる。
run_one 3000
run_one 5000

$PY experiments/summarize.py >"$LOGDIR/summarize_baseline_datascale.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 段階4 データ量スイープ 完了 ===" >> "$LOGDIR/baseline_datascale_done.log"
