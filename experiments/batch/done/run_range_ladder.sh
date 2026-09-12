#!/usr/bin/env bash
# =============================================================================
# 実験5: 動的参照の「参照範囲」ラダー — 壁の位置を刻む
#
# 【なぜこれをやるのか】
# 実験3（構造ラダー）と実験4（学習量スイープ）で，動的参照を1本→2本
# （並列・直列）に増やしても，学習量を5倍にしても，正解率は 10〜16% の床から
# 動かなかった（weekly_report_20260823 §2）。一方，動的参照を持たない
# table_add3_k10 は 100% で学習できている。つまり
#
#     壁は「動的参照0本と1本の間」に立っており，1本より上に刻みを
#     増やしても平坦な床しか測れない
#
# ことが分かった。したがって刻むべきは 0本と1本の「間」である。
#
# 【設計】
#   narrowptr_k10_m{m}:  j = (X[10] + X[11]) mod m
#                        Z = (X[j] + X[12] + X[13]) mod 10
# m は「ポインタの行き先の数」であり，動的参照の強さを連続的に刻むつまみ。
#   m = 1  … j は常に0。参照先が固定＝静的参照3箇所の足し算（100% 側の端点）
#   m = 10 … func_22_k10 と定義が完全に一致（床側の端点，13.0% / 16.0%）
#
# 両端が 100% と 13% なので，本研究で初めて「床でない勾配」が測れる見込み。
#
# 【交絡の事前チェック（済）】
# 5条件 × 鍵2種のすべてで，答えの値の種類は10，最頻値割合 10.2〜12.7%，
# 衝突確率 10.0〜10.5%（偶然水準 10% の近傍）と揃っている。つまり
# 答えの分布は m によらず一定であり，正解率の差が出たならそれは
# 参照範囲 m だけに帰属できる（3.4節の鍵の偏りによる嵩上げは起きない）。
# また ch[i] は 0〜9 一様なので，m によらず鍵10マス全部が必要になる。
# 記憶の負荷も m に対して一定である。
#
# 【m=1 についての注意】
# m=1 のときルール文は「j = (X[10] + X[11]) mod 1 を計算します」となる。
# 数学的には常に j=0 だが，「mod 1」という書き方自体がモデルにとって
# 不自然で，構造の易しさとは別の理由で失点する可能性がある。
# したがって m=1 が低く出た場合は，端点の破綻ではなく表記の問題を
# 先に疑うこと（7月の table_add3_k10 は key_seed=0 ながら 100% だった）。
# m=1 が想定どおり高く出れば，端点が機能していることの確認になる。
#
# 【m=10 は回さない】
# narrowptr_k10_m10 は rule_text / rationale_text / code_body / key_size /
# level のすべてが func_22_k10 と一致することを確認済み（機械的に比較）。
# 実験3の結果をそのまま端点として使う： ks1 = 13.0%, ks2 = 16.0%（各500件）。
#
# 【table_add3_k10 は端点として使わない】
# 7月の table_add3_k10（100%）は key_seed=0 かつ評価50件であり，鍵が
# 揃っていない。本ラダーでは m=1 が鍵を揃えた静的参照の端点になる。
#
# 【条件】
#   narrowptr_k10_m{1,2,3,5} × key_seed {1,2} = 8本
#   学習条件は実験3・4と完全に同一（pure / stage2 / n_train=1000 / epochs=5）
#   評価は500件（50件では点推定が最大13ポイントずれる: §4.1）
#   所要は1本あたり約2時間，合計約16時間。
#
# 【順序】
# 鍵1で m 昇順に4点そろえてから鍵2へ移る。8時間後には片方の鍵で曲線が
# 完成しているので，勾配が出ているかを途中で判断できる。
# =============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
PY=.venv/bin/python
LOGDIR=results/logs
mkdir -p "$LOGDIR"
MODEL="Qwen/Qwen2.5-3B-Instruct"
N_TEST=500
N_TRAIN=1000

run_one() {
    local algo=$1 key_seed=$2
    local tag="${algo}_ks${key_seed}_stage2_n${N_TRAIN}"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$algo" \
        --paradigm pure --stage 2 --n_shot 0 --n_train "$N_TRAIN" --epochs 5 \
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

for ks in 1 2; do
    for m in 1 2 3 5; do
        run_one "narrowptr_k10_m${m}" "$ks"
    done
done

$PY experiments/summarize.py >"$LOGDIR/summarize_range_ladder.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験5 参照範囲ラダー 完了 ===" >> "$LOGDIR/range_ladder_done.log"
