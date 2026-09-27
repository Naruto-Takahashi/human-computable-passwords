#!/usr/bin/env bash
# =============================================================================
# 小川ら Table 5/6 と横並びにするための格子（経路C，2026-09-27）
# =============================================================================
# なぜこれを回すのか:
#   予備実験では func_22 と統制3本しか測っていない。小川らの表は
#   f13 / f22 / f31 × データ量4種なので，同じ形に埋めないと横並びにできない。
#   条件は小川らに合わせる: N=26，データ量 1,000 / 5,000 / 10,000 / 50,000。
#
#   **構成は予備実験4 で最も離陸した組み合わせを使う**（2026-09-27 に修正）。
#   最初は既存の func_22 の値と揃えるため mean・64次元・30エポックで回したが，
#   それは予備実験0〜4 の知見を捨てる設定だった。30エポックは相転移の前で
#   切れており（統制 h が 0.3995 対 小川ら 0.8080 と負ける），予算が測定値に
#   混ざる。CLAUDE.md の「予算が測定値に混ざっていないか」に反する。
#
#     読み出し cls    統制 5/5 が 1.0000（mean は 4/5, 2/6）
#     d_model 32      離陸 2/3（64 は 5/15，128 は 0/3 で崩壊）
#     300エポック     50,000件で 2/3 離陸（30エポックは 5/15）
#
#   **これは実験C1 本体ではない。**小川らの表と横並びにするための格子で，
#   1セル3run しかない。本体は離陸率を R>=20 で測る（鍵 seed と初期化 seed を
#   分けてから）。
# =============================================================================
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
JOBS=${HCP_JOBS:-5}
THREADS=${HCP_THREADS:-4}
PY=.venv/bin/python

plan() {
  for a in func_13_k26 func_31 func_22 func_pow table_add3_k26 narrowptr_k26_m1; do
    for d in 1000 5000 10000 50000; do
      echo "--algorithm $a --datasize $d --epochs 300 --runs 3 --readout cls --d_model 32 --experiment C1grid_tuned"
    done
  done
}

N=$(plan | wc -l)
echo "=== [$(date '+%m/%d %H:%M:%S')] 小川ら格子: ${N} 条件を ${JOBS} 並列 ==="
if [ "${HCP_DRY_RUN:-}" = "1" ]; then plan | nl; exit 0; fi
export OMP_NUM_THREADS=$THREADS TF_NUM_INTRAOP_THREADS=$THREADS TF_NUM_INTEROP_THREADS=1
plan | xargs -P "$JOBS" -I{} sh -c \
  "$PY experiments/train_pathC.py {} 2>/dev/null | grep -E 'run[0-9]'"
echo "=== [$(date '+%m/%d %H:%M:%S')] 完了 ==="
