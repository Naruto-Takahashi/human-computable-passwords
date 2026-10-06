#!/usr/bin/env python3
"""実験C2.1（H-C2″）のための鍵選定: 基準線を揃え，エントロピーだけ振る．

実験C2 では「鍵の最多重複が離陸率に効く」という素の相関が，鍵ごとの基準線
（最頻値予測器の正解率）自体との相関を経由した見かけの効果である疑いが強いと
分かった（docs/experiment_index.md の実験C2「撤回」節）。この疑いを統計的な
除去（偏相関）ではなく，**鍵の選び方そのもので基準線を揃える**ことで検証する。

基準線は学習なしで計算できる（チャレンジを生成して最頻値の頻度を数えるだけ）。
`train_pathC.py` の `make_dataset` / `majority_baseline` をそのまま再利用し，
GPU・モデル構築なしで鍵を大量に screening する。

    python3 experiments/select_baseline_matched_keys.py
    python3 experiments/select_baseline_matched_keys.py --algorithms func_31

出力: `results/path_c/C2_1_keys.json`（関数ごとに選んだ20本の鍵seed・エントロピー・
基準線・最多重複）。`experiments/train_pathC.py --key_seeds` にそのまま渡せる形。
`--algorithms` で絞ったときは，既存ファイルの他関数の選定結果を保ったまま
指定した関数だけを上書きする。

2026-10-05: 実験C2.1 の結果，$`f_{3,1}`$ は低基準線（最小値+0.01）の帯では
全40 runが離陸せず検証不能だった（docs/experiment_index.md の実験C2.1）。
$`f_{3,1}`$ が離陸する鍵は基準線0.15付近（C1の「鍵27」）に偏っていたため，
`BAND_OVERRIDE` で $`f_{3,1}`$ だけ帯を 0.13〜0.15 に固定できるようにした。
"""
import argparse
import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "experiments"))

from hcp.algorithms import get_algorithm  # noqa: E402
from train_pathC import make_dataset, majority_baseline  # noqa: E402

OUT = os.path.join(REPO, "results/path_c/C2_1_keys.json")
ALGOS = ["func_31", "func_22", "func_13_k26"]
N_CANDIDATES = 3000
SEED_BASE = 900000  # 既存実験（C1/C2）の鍵seedと重複しない範囲
SCREEN_DATASIZE = 5000  # 基準線の推定だけが目的なので本番の50,000件は不要
BAND_WIDTH = 0.01  # 基準線の帯の幅（既定: 最小値からこの幅まで）
N_SELECT = 20
# 関数ごとに帯を固定したいとき（既定は候補の最小値から BAND_WIDTH 幅）。
# func_31 は実験C2の実測（離陸した5鍵の基準線が0.1328〜0.1568）を根拠に，
# 余裕を持って [0.125, 0.165] とした（0.13〜0.15だと0.1568の鍵を取り落とす）。
BAND_OVERRIDE = {"func_31": (0.125, 0.165)}


def screen(algo_name: str):
    algo = get_algorithm(algo_name)
    rows = []
    for i in range(N_CANDIDATES):
        seed = SEED_BASE + i
        _, z, key = make_dataset(algo, SCREEN_DATASIZE, seed)
        base = majority_baseline(z, z)
        c = np.bincount(key, minlength=10)
        pr = c[c > 0] / len(key)
        ent = float(-(pr * np.log2(pr)).sum())
        rows.append({"key_seed": seed, "baseline": base, "entropy": ent,
                     "max_dup": int(c.max())})
    return rows


def select_band_matched(rows, algo_name):
    base = np.array([r["baseline"] for r in rows])
    if algo_name in BAND_OVERRIDE:
        lo, hi = BAND_OVERRIDE[algo_name]
    else:
        lo, hi = base.min(), base.min() + BAND_WIDTH
    band = [r for r in rows if lo <= r["baseline"] <= hi]
    band.sort(key=lambda r: r["entropy"])
    idx = np.unique(np.round(np.linspace(0, len(band) - 1, N_SELECT)).astype(int))
    # 境界の重複で N_SELECT に足りないことがあるので，足りない分は等間隔の隙間から補う
    chosen = [band[i] for i in idx]
    pool = [r for i, r in enumerate(band) if i not in set(idx)]
    while len(chosen) < N_SELECT and pool:
        chosen.append(pool.pop(len(pool) // 2))
    return lo, hi, len(band), chosen[:N_SELECT]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algorithms", nargs="+", default=ALGOS,
                     help="選び直す関数だけ指定する（既定は全関数）。"
                          "指定しなかった関数の既存の選定結果は保つ")
    args = ap.parse_args()

    result = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            result = json.load(f)

    print(f"{'関数':12s}{'候補':>6s}{'帯':>18s}{'帯内候補':>8s}{'選定エントロピー範囲':>22s}")
    for a in args.algorithms:
        rows = screen(a)
        lo, hi, n_band, chosen = select_band_matched(rows, a)
        ent = [r["entropy"] for r in chosen]
        result[a] = sorted(chosen, key=lambda r: r["entropy"])
        print(f"{a:12s}{len(rows):>6d}  [{lo:.4f},{hi:.4f}]{n_band:>8d}"
              f"  {min(ent):.3f}〜{max(ent):.3f}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n保存: {OUT}")
    for a in args.algorithms:
        seeds = ",".join(str(r["key_seed"]) for r in result[a])
        print(f"  {a}: --key_seeds {seeds}")


if __name__ == "__main__":
    main()
