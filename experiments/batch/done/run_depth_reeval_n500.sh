#!/usr/bin/env bash
# =============================================================================
# 段階2-3: 既存の学習済みアダプタを n_test=500 で再評価（再学習なし・推論のみ）
#
# 動機: これまでの深さラダーは全て n_test=50 で評価してきたが，この規模では
#   検出できる最小の差が約27ポイントしかない（深さ1→3で観測された差は12〜18
#   ポイント）。つまり「差がなかった」という結論が，本当に差がないのか，単に
#   測定解像度が足りないのかを区別できていない。
#   一方，評価コストは50件で82秒（学習は約2時間）と極めて低い。500件に増やせば
#   検出可能な差が約10ポイントまで下がり，既存の全結論を10倍の解像度で
#   測り直せる。学習は一切不要。
#
# 安全性: 学習用チャレンジは data_seed + TRAIN_SEED_OFFSET から，評価用は素の
#   data_seed から生成されるため，n_test を増やしても訓練データとは重複しない。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
N_TEST=500

# 既存アダプタ: run_dir と (algorithm, key_seed) の対応
# d1: ks0/1/2, d2: ks0/1/2, d3: ks1/2 の計8個
eval_one() {
    local algo=$1 key_seed=$2 run_dir=$3
    local tag="${algo}_ks${key_seed}_n${N_TEST}"
    local log="$LOGDIR/reeval_${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL $tag (n_test=$N_TEST) ===" > "$log"
    echo "run_dir=$run_dir" >> "$log"
    # --overwrite が必要: 評価結果の保存先パスに n_test が含まれないため，
    # 既存の n_test=50 の結果があると「完了済み」と判定されスキップされる。
    # n=50 の結果は results/llm_eval_backup_n50_20260817/ に退避済み。
    # なお n=500 は n=50 の上位互換（同じ乱数列の先頭50件を含む）。
    $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$algo" \
        --stage 2 --n_shot 0 --n_test "$N_TEST" --key_seeds "$key_seed" --data_seeds 0 \
        --overwrite >>"$log" 2>&1
    echo "=== [$(date '+%m/%d %H:%M:%S')] DONE $tag ===" >>"$log"
}

BASE=results/llm_finetune/qwen2.5_3b

eval_one pointer_chain_k10_d1 0 "$REPO/$BASE/pointer_chain_k10_d1/run_20260816_143142"
eval_one pointer_chain_k10_d1 1 "$REPO/$BASE/pointer_chain_k10_d1/run_20260816_195925"
eval_one pointer_chain_k10_d1 2 "$REPO/$BASE/pointer_chain_k10_d1/run_20260816_235035"
eval_one pointer_chain_k10_d2 0 "$REPO/$BASE/pointer_chain_k10_d2/run_20260816_161732"
eval_one pointer_chain_k10_d2 1 "$REPO/$BASE/pointer_chain_k10_d2/run_20260816_214500"
eval_one pointer_chain_k10_d2 2 "$REPO/$BASE/pointer_chain_k10_d2/run_20260817_013649"
eval_one pointer_chain_k10_d3 1 "$REPO/$BASE/pointer_chain_k10_d3/run_20260817_095544"
eval_one pointer_chain_k10_d3 2 "$REPO/$BASE/pointer_chain_k10_d3/run_20260817_120042"

$PY experiments/summarize.py >"$LOGDIR/summarize_reeval_n500.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 段階2-3 再評価バッチ完了 ===" >> "$LOGDIR/depth_reeval_done.log"
