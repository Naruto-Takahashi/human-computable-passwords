#!/usr/bin/env bash
# =============================================================================
# 実験6: 鍵の交絡を正面から測る
#
# 【なぜ必要になったのか】
# 実験5b（2026/09/06）で，関数もルール文も学習条件も同一のまま鍵だけを
# 変えると，static な table_add3_k10 の正解率が
#     ks=0 → 99.6%,  ks=2 → 26.2%,  ks=1 → 10.6%
# と動くことが分かった（各 n_test=500，χ² 検定 p=1.6e-198）。
# ks=1 は衝突確率 10.0% に対して有意ですらない。
#
# 実験3（構造ラダー）・実験4（学習量スイープ）・実験5（参照範囲ラダー）は
# いずれも ks=1, 2 でしか測っていない。ks=1 は「自明に学習できるはずの
# 静的参照ですら床になる鍵」だったので，これらで観測した床を
# 「動的参照だから」と帰属することはできない。
#
# 【このバッチで確かめること】
#
# (A) func_22_k10（動的参照1本）を ks=0 で1本 ── 最も情報量が多い
#     ks=0 は静的参照が 99.6% で学習できた「学習可能な鍵」である。
#     その上で動的参照がどうなるかを見る。
#       99% 付近が出る → 「動的参照は学習できない」という本研究の柱が崩れる。
#                        これまでの床はすべて鍵の交絡だったことになる。
#       床のまま       → 学習可能な鍵の上で初めて「静的は解ける・動的は
#                        解けない」を公平に比較できたことになり，
#                        従来の主張が正しい形で裏づけられる。
#     どちらに転んでも決定的なので先頭に置く（約2時間）。
#
# (B) table_add3_k10 を ks=3〜9 の7本 ── 鍵ごとの正解率の分布を取る
#     既存の ks=0,1,2 と合わせて10鍵になる。何が学習可能性を決めているのか
#     （異なる数字の数・同じ数字の連なり・その他）を特定する材料にする。
#     実験5b の時点では3点しかなく，「異なる数字が7種類」でも ks=0（99.6%）と
#     ks=2（26.2%）で大きく違ったため，仮説を立てるには点が足りない。
#     約14時間。
#
# 【今後の標準手順】
# 条件間比較は鍵を複数引いて分布で行う。鍵1〜2本での比較は解釈できない
# ことが実験5b で確定したため，このバッチ以降そのように運用する。
#
# 学習条件は実験3・4・5・5b と完全に同一（pure / stage2 / n_train=1000 /
# epochs=5），評価は500件。
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

# (A) 最も情報量の多い1本を先に
run_one func_22_k10 0

# (B) 鍵ごとの分布（ks=0,1,2 は取得済み）
for ks in 3 4 5 6 7 8 9; do
    run_one table_add3_k10 "$ks"
done

$PY experiments/summarize.py >"$LOGDIR/summarize_key_effect.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験6 鍵の交絡 完了 ===" >> "$LOGDIR/key_effect_done.log"
