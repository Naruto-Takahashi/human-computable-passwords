#!/usr/bin/env bash
# =============================================================================
# 実験4: 基準線を床から持ち上げられるか（学習データ量スイープ）
#
# 実験3（構造ラダー）で 6条件すべてが 10〜20% に張り付き，基準線
# func_22_k10 の時点で既に床にあった。このため「動的参照を増やすと
# 難しくなる」という仮説は下がる余地が無く，識別できなかった
# （weekly_report_20260823 §2.2）。
#
# 【回復の見込みについて，正直な見積り】
# 学習量で床から回復した前例は table_add_k26（8% → 100%）だが，これは
# 「合成のみ」で動的参照を含まない。7月の結論は
#   ①記憶・②合成 → データ量で解決する
#   ③動的参照     → データ量で解決しない
# であり，動的参照を含む課題で学習量を5倍にした記録は2件とも回復していない：
#   func_22（k=26）  1000件 6〜12% → 5000件  8%（不変）
#   pointer_k26      1000件 14%    → 5000件 18%（ほぼ不変）
# したがって基準線が回復する見込みは高くない。
#
# それでも回す理由は，過去の検証がすべて n=26 だったことにある。7月には
# 「n=26 では組み合わせが多すぎること（26^3≈17,576通り）が支配的で，
# 動的参照固有の効果と区別できない」と結論していた。n=10 なら値の組み合わせは
# 10^3=1000 通りで，3000〜5000件はその3〜5倍にあたる。
#   回復する   → 組み合わせ爆発が主因。その水準で3点比較をやり直せる
#   回復しない → 動的参照そのものが主因。n=26 で切り分けられなかった
#                7月の積み残しに決着がつく
# どちらに転んでも報告できる。
#
# まず基準線1条件だけを振る（構造ラダー全体をやり直す前の判定）。
#   func_22_k10 × key_seed=1 × n_train ∈ {3000, 5000}
#   （n_train=1000 は実験3で実施済み: 13.0%）
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
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験4 データ量スイープ 完了 ===" >> "$LOGDIR/baseline_datascale_done.log"
