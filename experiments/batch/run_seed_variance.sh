#!/usr/bin/env bash
# =============================================================================
# 実験7: 「鍵の性質」なのか「run のばらつき」なのかを切り分ける
#
# 【なぜ必要になったのか】
# 実験6で table_add3_k10（静的参照3箇所の足し算）を鍵10本で回したところ，
# 正解率の分布が二峰性になった。
#     ks=3 99.8% / ks=0 99.6% / ks=4 96.8%     ← 上の山（3本）
#     ks=7 33.6% / ks=2 26.2% / ks=5 17.4% /
#     ks=9 11.6% / ks=1 10.6% / ks=8 10.6% / ks=6 10.2%   ← 下の山（7本）
# 間がぽっかり空いており，なだらかな難易度差ではなく「学習が決まるか
# 決まらないか」の二択に見える。
#
# しかも鍵の統計量では説明できない。正解率との順位相関は
#   異なる数字の数 ρ=-0.11 (p=0.76) / 最多重複 ρ=0.36 (p=0.31)
#   最長連 ρ=0.55 (p=0.10) / エントロピー ρ=-0.32 (p=0.38)
# といずれも有意でない。決定的な反例として：
#   ks=3 [8,0,1,2,1,8,8,5,0,0] 種類5・エントロピー2.17・最多重複3・最長連2 → 99.8%
#   ks=6 [4,5,5,3,9,3,6,3,4,9] 種類5・エントロピー2.25・最多重複3・最長連2 → 10.2%
# 鍵の統計量がほぼ同一なのに結果が正反対である。
#
# 【疑い】
# これは鍵の性質ではなく，学習の run ごとのばらつき（初期化や事例の並びの運）
# ではないか。二峰性はその見方と整合する（一種の「当たりくじ」的な挙動）。
# もしそうなら，この実験系では1条件1runでの条件間比較が成立しない。
# 実験3〜6の数字はすべて運の1サンプルだったことになる。
#
# 【切り分け】
# 鍵を固定したまま data_seed だけを変える。data_seed はチャレンジ集合の
# 抽選のみを動かし，鍵は動かさない。
#   ks=3（上の山）と ks=6（下の山）× data_seed {1, 2} の4本。
#   既存の data_seed=0 と合わせて各3点になる。
# この2鍵を選んだのは，鍵の統計量がほぼ同一なのに結果が正反対だからである。
#
#   ks=3 が3回とも99%付近，ks=6 が3回とも床
#       → 鍵の性質であることが確定。まだ特定できていない構造が効いている。
#   ばらつく
#       → run のばらつきである。今後すべての条件を複数 seed で回して
#         分布で比較する必要があり，過去の結論はすべて測り直しになる。
#
# 学習条件は実験3〜6と完全に同一（pure / stage2 / n_train=1000 / epochs=5），
# 評価は500件。約8時間。
#
# 【注意】評価の出力先パスは data_seed を含む（ks{key}_ds{data}）ので，
# 既存の ds0 の結果は上書きされない。--overwrite は不要。
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

run_one() {
    local key_seed=$1 data_seed=$2
    local tag="${ALGO}_ks${key_seed}_ds${data_seed}_stage2_n1000"
    local log="$LOGDIR/${tag}.log"
    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    if $PY experiments/train_finetuning.py --model "$MODEL" --algorithm "$ALGO" \
        --paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5 \
        --key_seed "$key_seed" --data_seed "$data_seed" \
        --tag "実験7: seed ばらつきの検証" >>"$log" 2>&1; then
        local run_dir
        run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
        echo "run_dir=$run_dir" >> "$log"
        echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag (n_test=$N_TEST) ===" >>"$log"
        $PY experiments/run_eval.py --provider lora --model "$run_dir" --algorithm "$ALGO" \
            --stage 2 --n_shot 0 --n_test "$N_TEST" --key_seeds "$key_seed" \
            --data_seeds "$data_seed" >>"$log" 2>&1
    else
        echo "!!! TRAIN FAILED: $tag" >>"$log"
    fi
}

# 上の山と下の山を交互に回す。早い段階で両方の挙動が見えるようにするため。
run_one 3 1
run_one 6 1
run_one 3 2
run_one 6 2

$PY experiments/summarize.py >"$LOGDIR/summarize_seed_variance.log" 2>&1 || true
echo "=== [$(date '+%m/%d %H:%M:%S')] 実験7 seed ばらつきの検証 完了 ===" >> "$LOGDIR/seed_variance_done.log"
