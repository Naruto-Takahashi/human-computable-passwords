# =============================================================================
# _common.sh — バッチスクリプトの共通部分
# =============================================================================
# 各バッチの中身は「1条件を学習して評価する」の繰り返しでしかないのに，
# その手順が15本のスクリプトに丸ごとコピーされていた（run_one の本体を
# md5 で比べると複数が完全一致していた）。学習条件を変えたくなるたびに
# 15箇所を直すことになるため，ここに集約する。
#
# 使い方:
#   source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
#   hcp_init "段階X: 実験の名前"          # cd・ログ先・既定値の設定
#   hcp_run --algorithm func_22_k10 --key_seed 1
#   hcp_run --algorithm func_22_k10 --key_seed 2 --n_train 3000
#   hcp_finish
#
# 書いたスクリプトの疎通確認（GPU を掴まないので走行中のバッチに影響しない）:
#   HCP_DRY_RUN=1 bash experiments/batch/run_xxx.sh
#
# 既定値は hcp_init のあとに上書きできる:
#   HCP_N_TEST=200
#   HCP_EPOCHS=40
# =============================================================================

hcp_init() {
    HCP_TAG="${1:?実験の名前を渡してください（make inventory の見出しになります）}"
    # リポジトリの位置は git に聞く。呼び出し元のパスから ../.. で辿る方法だと，
    # experiments/batch/ 以外から source されたときに無関係な場所（/ など）へ
    # cd してしまい，そこに results/ を作ろうとする事故になる。
    HCP_REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [ -z "$HCP_REPO" ]; then
        HCP_REPO="$(cd "$(dirname "${BASH_SOURCE[1]}")/../.." 2>/dev/null && pwd)"
    fi
    if [ -z "$HCP_REPO" ] || [ ! -f "$HCP_REPO/experiments/train_finetuning.py" ]; then
        echo "hcp_init: リポジトリのルートを特定できません（HCP_REPO='$HCP_REPO'）" >&2
        echo "          リポジトリ内から実行してください。" >&2
        return 1
    fi
    cd "$HCP_REPO" || return 1
    # HCP_PY を無条件に代入しないのは，呼び出し側で差し替えられるようにするため。
    HCP_PY="${HCP_PY:-.venv/bin/python}"
    HCP_LOGDIR=results/logs
    mkdir -p "$HCP_LOGDIR"
    # 既定値。呼び出し側で上書きしてよい。
    HCP_MODEL="${HCP_MODEL:-Qwen/Qwen2.5-3B-Instruct}"
    HCP_N_TEST="${HCP_N_TEST:-500}"
    HCP_N_TRAIN="${HCP_N_TRAIN:-1000}"
    HCP_EPOCHS="${HCP_EPOCHS:-5}"
    HCP_STAGE="${HCP_STAGE:-2}"
    HCP_PARADIGM="${HCP_PARADIGM:-pure}"
    HCP_N_SHOT="${HCP_N_SHOT:-0}"
    HCP_FAILED=0
    HCP_DONE=0
    # 何本回す予定かを HCP_TOTAL に入れておくと「[2/4]」のように進捗が出る。
    HCP_TOTAL="${HCP_TOTAL:-0}"
    # HCP_DRY_RUN=1 で，実際には学習・評価を起動せず実行内容だけを表示する。
    # スクリプトの疎通確認に使う。GPU を掴まないので，走行中のバッチに影響しない。
    HCP_DRY_RUN="${HCP_DRY_RUN:-0}"
    if [ "$HCP_DRY_RUN" = "1" ]; then
        echo "=== [空実行] $HCP_TAG — 実際には何も起動しません ==="
    else
        echo "=== [$(date '+%m/%d %H:%M:%S')] 開始: $HCP_TAG ==="
    fi
}

# 1条件を学習して評価する。
#   hcp_run --algorithm <名前> [--key_seed N] [--data_seed N]
#           [--n_train N] [--epochs N] [--n_test N] [--stage N] [--lr X]
# 指定しなかったものは hcp_init の既定値を使う。
hcp_run() {
    local algorithm="" key_seed=0 data_seed=0
    local n_train="$HCP_N_TRAIN" epochs="$HCP_EPOCHS" n_test="$HCP_N_TEST"
    local stage="$HCP_STAGE" lr=""
    while [ $# -gt 0 ]; do
        case "$1" in
            --algorithm) algorithm="$2"; shift 2 ;;
            --key_seed)  key_seed="$2";  shift 2 ;;
            --data_seed) data_seed="$2"; shift 2 ;;
            --n_train)   n_train="$2";   shift 2 ;;
            --epochs)    epochs="$2";    shift 2 ;;
            --n_test)    n_test="$2";    shift 2 ;;
            --stage)     stage="$2";     shift 2 ;;
            --lr)        lr="$2";        shift 2 ;;
            *) echo "hcp_run: 不明な引数 '$1'" >&2; return 2 ;;
        esac
    done
    [ -n "$algorithm" ] || { echo "hcp_run: --algorithm は必須です" >&2; return 2; }

    # ログ名は条件から決まるようにする（あとから grep で探せるように）。
    local tag="${algorithm}_ks${key_seed}_ds${data_seed}_n${n_train}_ep${epochs}"
    local log="$HCP_LOGDIR/${tag}.log"

    if [ "$HCP_DRY_RUN" = "1" ]; then
        printf '  学習: %-22s 鍵%-2s データ%-2s 件数%-5s ep%-3s → 評価 %s件\n' \
            "$algorithm" "$key_seed" "$data_seed" "$n_train" "$epochs" "$n_test"
        return 0
    fi

    # 標準出力にも1行ずつ出す。バッチは nohup で走らせるので，ここに何も
    # 出さないと「何時間も無言」になり，tail -f しても進捗が分からなかった。
    HCP_DONE=$((HCP_DONE + 1))
    local counter=""
    [ "$HCP_TOTAL" -gt 0 ] && counter=" [${HCP_DONE}/${HCP_TOTAL}]"
    printf '[%s]%s 開始 %s（鍵%s データ%s 件数%s ep%s → 評価%s件）\n' \
        "$(date '+%m/%d %H:%M')" "$counter" "$algorithm" \
        "$key_seed" "$data_seed" "$n_train" "$epochs" "$n_test"
    local started=$SECONDS

    echo "=== [$(date '+%m/%d %H:%M:%S')] TRAIN $tag ===" > "$log"
    local lr_opt=()
    [ -n "$lr" ] && lr_opt=(--lr "$lr")
    if ! $HCP_PY experiments/train_finetuning.py \
            --model "$HCP_MODEL" --algorithm "$algorithm" \
            --paradigm "$HCP_PARADIGM" --stage "$stage" --n_shot "$HCP_N_SHOT" \
            --n_train "$n_train" --epochs "$epochs" \
            --key_seed "$key_seed" --data_seed "$data_seed" \
            --tag "$HCP_TAG" "${lr_opt[@]}" >>"$log" 2>&1; then
        echo "!!! TRAIN FAILED: $tag" >>"$log"
        echo "[失敗] 学習: $tag（$log）" >&2
        HCP_FAILED=$((HCP_FAILED + 1))
        return 1
    fi

    local run_dir
    run_dir=$(grep -oP '(?<=^Results will be saved to: ).*' "$log" | head -1)
    if [ -z "$run_dir" ]; then
        echo "!!! run ディレクトリを特定できません: $tag" >>"$log"
        echo "[失敗] run ディレクトリ不明: $tag" >&2
        HCP_FAILED=$((HCP_FAILED + 1))
        return 1
    fi
    echo "run_dir=$run_dir" >> "$log"

    echo "=== [$(date '+%m/%d %H:%M:%S')] EVAL  $tag (n_test=$n_test) ===" >>"$log"
    if ! $HCP_PY experiments/run_eval.py --provider lora --model "$run_dir" \
            --algorithm "$algorithm" --stage "$stage" --n_shot "$HCP_N_SHOT" \
            --n_test "$n_test" --key_seeds "$key_seed" --data_seeds "$data_seed" \
            >>"$log" 2>&1; then
        echo "[失敗] 評価: $tag（$log）" >&2
        HCP_FAILED=$((HCP_FAILED + 1))
        return 1
    fi

    # 終わったその場で結果を出す。集計コマンドを別に叩かなくても
    # nohup の出力を見れば流れが追えるようにするため。
    local ok tot acc="?" vl="-" mins=$(( (SECONDS - started) / 60 ))
    ok=$(grep -c '✓' "$log" 2>/dev/null || true); ok=${ok:-0}
    tot=$(grep -c '✓\|✗' "$log" 2>/dev/null || true); tot=${tot:-0}
    [ "$tot" -gt 0 ] && acc=$(awk -v a="$ok" -v b="$tot" 'BEGIN{printf "%.1f%%", 100*a/b}')
    if [ -f "$run_dir/history.csv" ]; then
        vl=$(awk -F, 'NR==1{for(i=1;i<=NF;i++) if($i=="eval_loss") c=i; next}
                      c && $c != "" {v=$c} END{if(v!="") printf "%.4f", v}' \
             "$run_dir/history.csv" 2>/dev/null)
        vl=${vl:--}
    fi
    printf '[%s] 完了 %-20s 正解率 %-7s val損失 %-8s（%d分）\n' \
        "$(date '+%m/%d %H:%M')" "$algorithm(鍵$key_seed)" "$acc" "$vl" "$mins"
    return 0
}

hcp_finish() {
    if [ "$HCP_DRY_RUN" = "1" ]; then
        echo "=== [空実行] $HCP_TAG — ここまで ==="
        return 0
    fi
    $HCP_PY experiments/summarize.py >"$HCP_LOGDIR/summarize_last.log" 2>&1 || true
    $HCP_PY experiments/inventory.py >>"$HCP_LOGDIR/summarize_last.log" 2>&1 || true
    local marker="$HCP_LOGDIR/$(echo "$HCP_TAG" | tr ' :/' '___')_done.log"
    echo "  （結果一覧: make inventory / 進捗: make status）"
    if [ "$HCP_FAILED" -gt 0 ]; then
        echo "=== [$(date '+%m/%d %H:%M:%S')] $HCP_TAG 完了（失敗 $HCP_FAILED 件）===" | tee -a "$marker"
    else
        echo "=== [$(date '+%m/%d %H:%M:%S')] $HCP_TAG 完了 ===" | tee -a "$marker"
    fi
}
