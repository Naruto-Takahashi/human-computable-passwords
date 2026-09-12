#!/usr/bin/env bash
# =============================================================================
# 実験5b: 「静的参照は100%学習できる」という端点の前提を検証する
#
# 【なぜ必要になったのか】
# 実験5（参照範囲ラダー）で，静的参照の端点として設計した narrowptr_k10_m1
# （j が常に0 ＝ Z = (X[0] + X[12] + X[13]) mod 10）が 9.8%（key_seed=1）と，
# 偶然水準から出なかった。ここは 100% 近くになる前提で組んだ端点である。
#
# 端点の根拠にしていたのは，7月の table_add3_k10 の 100% だが，これは
#   ・key_seed = 0 の1本のみ
#   ・評価 50 件のみ
# であり，鍵を揃えた確認をしていなかった（実験4で前例の引き違えをした
# のと同じ種類の誤り）。
#
# 【7月と今回で違う点は2つに絞られる】
#  (1) 鍵     7月は key_seed=0 で sgm=[8,6,5,2,3,0,0,0,1,8]。
#             異なる数字が7種類しかなく 0 が3個ある。今回の ks1 は9種類。
#             答えの分布の偏りではない（衝突確率は 10.0〜10.5% で同等）ので，
#             差があるとすれば「鍵そのものの覚えやすさ」である。
#  (2) 表記   m=1 のルール文は「j = (X[10] + X[11]) mod 1」となる。
#             数学的には常に j=0 だが，この書き方自体がモデルにとって
#             不自然である可能性を実験5の時点で懸念として挙げていた。
#
# 【切り分け】
# 7月とまったく同じ table_add3_k10（＝「mod 1」の表記を含まない）を，
# 鍵だけ ks=1, 2 に変えて学習する。
#   ks1/ks2 でも 100% → 鍵は無関係。「mod 1」の表記が m=1 を殺している。
#                       端点を書き換えて参照範囲ラダーを組み直す。
#   ks1/ks2 で床      → 鍵の引きで学習できるかどうかが決まっている。
#                       7月の「①記憶・②合成は学習できる」という結論自体が
#                       鍵1本に依存していたことになり，全結果の解釈が変わる。
#                       その場合は func_22_k10 を ks=0 で回して追確認する。
#
# 【手順】
#  0) 7月のアダプタを 500 件で再評価（学習不要，約15分）。
#     ks=0 の 100% が 50 件の偶然でないことを先に確かめる。
#     評価の出力先パスに n_test が入らないため --overwrite が必要。
#  1) table_add3_k10 × key_seed {1, 2} を学習（各約2時間）。
#     学習条件は実験3・4・5と完全に同一（pure / stage2 / n_train=1000 / epochs=5）。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"
N_TEST=500
ALGO=table_add3_k10
JULY_RUN=results/llm_finetune/qwen2.5_3b/table_add3_k10/run_20260729_023201

# --- 0) 7月アダプタ（key_seed=0）を500件で再評価 ---
log0="$LOGDIR/${ALGO}_ks0_reeval_n500.log"
echo "=== [$(date '+%m/%d %H:%M:%S')] REEVAL $ALGO ks0 (7月アダプタ, n_test=$N_TEST) ===" > "$log0"
$PY experiments/run_eval.py --provider lora --model "$JULY_RUN" --algorithm "$ALGO" \
    --stage 2 --n_shot 0 --n_test "$N_TEST" --key_seeds 0 --data_seeds 0 \
    --overwrite >>"$log0" 2>&1

# --- 1) 鍵を変えて学習 ---
run_one() {
    local key_seed=$1
    local tag="${ALGO}_ks${key_seed}_stage2_n1000"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$ALGO" \
        --paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5 \
        --key_seed "$key_seed" --data_seed 0 >>"$log" 2>&1; then
        local run_dir
        run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
        echo "run_dir=$run_dir" >> "$log"
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag (n_test=$N_TEST) ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$ALGO" \
            --stage 2 --n_shot 0 --n_test "$N_TEST" --key_seeds "$key_seed" --data_seeds 0 \
            >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

run_one 1
run_one 2

$PY experiments/summarize.py >"$LOGDIR/summarize_static_endpoint.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験5b 静的端点の検証 完了 ===" >> "$LOGDIR/static_endpoint_done.log"
