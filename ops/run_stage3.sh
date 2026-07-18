#!/usr/bin/env bash
# =============================================================================
# 段階3: 重み格納型学習の境界探索バッチ（難易度ラダー + CNN同条件比較）
# =============================================================================
# 実行順:
#   1. Stage 2（ルール開示）: lookup_k4/k10/k26 → table_add_k10/k26 → func_22
#   2. Stage 0（ルール非開示・CNN同条件）: simple_add, func_22, secret_add
#   3. CNNベースライン（CPU実行, TensorFlow）
#   4. 集計
# 各学習は full ログを results/logs/ に保存し，学習後すぐ held-out 50件で評価する．
# 共通条件: Bパラダイム（n_shot=0）, n_train=1000, epochs=5, key_seed=0, data_seed=0
# =============================================================================
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"

MODEL="Qwen/Qwen2.5-3B-Instruct"
N_TRAIN=1000
EPOCHS=5

run_one() {
    local algo=$1 stage=$2
    local tag="${algo}_stage${stage}"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date +%H:%M:%S)] TRAIN $tag ==="
    if ! $PY code/scripts/train_finetuning.py \
        --model "$MODEL" --algorithm "$algo" --paradigm pure \
        --stage "$stage" --n_shot 0 --n_train "$N_TRAIN" --epochs "$EPOCHS" \
        >"$log" 2>&1; then
        echo "!!! TRAIN FAILED: $tag（ログ: $log）"
        return 1
    fi
    local run_dir
    run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
    if [ -z "$run_dir" ]; then
        echo "!!! run_dir を検出できません: $tag"
        return 1
    fi
    echo "=== [$(date +%H:%M:%S)] EVAL  $tag → held-out 50件 ==="
    if ! $PY code/scripts/run_eval.py \
        --provider lora --model "$run_dir" --algorithm "$algo" \
        --stage "$stage" --n_shot 0 --n_test 50 --key_seeds 0 --data_seeds 0 \
        >>"$log" 2>&1; then
        echo "!!! EVAL FAILED: $tag（ログ: $log）"
        return 1
    fi
    grep -E "正解率|accuracy" "$log" | tail -2 || true
}

# ---- 1. 難易度ラダー（Stage 2: ルール開示・鍵のみ未知） ----
for algo in lookup_k4 lookup_k10 lookup_k26 table_add_k10 table_add_k26 func_22; do
    run_one "$algo" 2 || true
done

# ---- 2. CNN同条件（Stage 0: ルール非開示） ----
for algo in simple_add func_22 secret_add; do
    run_one "$algo" 0 || true
done

# ---- 3. CNN ベースライン（TensorFlow は nix 環境の python3 / CPUで実行） ----
echo "=== [$(date +%H:%M:%S)] CNN baseline ==="
CUDA_VISIBLE_DEVICES="" python3 code/scripts/train_baseline.py \
    >"$LOGDIR/cnn_baseline.log" 2>&1 || echo "!!! CNN baseline failed（ログ: $LOGDIR/cnn_baseline.log）"

# ---- 4. 集計 ----
python3 code/scripts/summarize.py >"$LOGDIR/summarize.log" 2>&1 || true
echo "=== [$(date +%H:%M:%S)] 段階3 バッチ完了 ==="
