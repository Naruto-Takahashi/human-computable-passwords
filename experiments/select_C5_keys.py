#!/usr/bin/env python3
r"""実験C5 のための鍵選定: 3つの腕の鍵 seed を決め，$I_1$ を記録する．

- ① そろえた鍵: 連番 seed（`train_pathC.py --balanced_key` で作る）。$I_1$ は厳密に 0
- ② ランダムな鍵: ① と同じ連番 seed（選別しない）
- ③ 偏りの大きい鍵: 候補 seed を順に見て，$I_1$ が帯に入る最初の `N_SELECT` 本

③ の帯は「実験C2 で離陸率 0.5 以上だった鍵の $I_1$ の中央値」から，その2倍まで
（docs/experiment_index.md の実験C5）。候補を ①② と別の範囲から取るのは，
② の鍵が ③ にも選ばれて腕の間で鍵が重なるのを避けるため。

学習なしで $I_1$ を計算するだけなので数秒で終わる。鍵は `make_dataset` で作り，
学習時とまったく同じ鍵を見る。

    python3 experiments/select_C5_keys.py

出力: `results/path_c/C5_keys.json`（関数ごと・腕ごとの鍵 seed と $I_1$）。
"""
import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "experiments"))

from hcp.algorithms import get_algorithm  # noqa: E402
from signal_strength import digit_dist, first_order_signal  # noqa: E402
from train_pathC import make_dataset  # noqa: E402

OUT = os.path.join(REPO, "results/path_c/C5_keys.json")
N_SELECT = 15
SEED_BASE = 50000000         # ①② の連番 seed
CAND_BASE = 51000000         # ③ の候補（①② と重ならない範囲）
N_CANDIDATES = 5000
# 関数 → (k1, k2, ③ の I_1 の帯)。帯の下端は C2 で離陸率 0.5 以上だった鍵の I_1 の中央値
FUNCS = {
    "func_22_k30": (2, 2, (0.0388, 0.0776)),
    "func_13_k30": (1, 3, (0.0072, 0.0144)),
}


def key_of(algo, seed, balanced=False):
    return make_dataset(algo, 1, seed, balanced=balanced)[2]


def i1(keys, k1, k2):
    return first_order_signal(digit_dist(keys), k1, k2)[0]


def main():
    result = {}
    print(f"{'関数':12s}{'腕':>6s}{'I_1 の範囲':>22s}")
    for name, (k1, k2, (lo, hi)) in FUNCS.items():
        algo = get_algorithm(name)
        seq = list(range(SEED_BASE, SEED_BASE + N_SELECT))
        cand = list(range(CAND_BASE, CAND_BASE + N_CANDIDATES))
        cand_i1 = i1([key_of(algo, s) for s in cand], k1, k2)
        skewed = [s for s, v in zip(cand, cand_i1) if lo <= v <= hi][:N_SELECT]
        if len(skewed) < N_SELECT:
            raise SystemExit(f"{name}: 帯に入る候補が {len(skewed)} 本しかない")

        arms = {
            "balanced": (seq, i1([key_of(algo, s, True) for s in seq], k1, k2)),
            "random": (seq, i1([key_of(algo, s) for s in seq], k1, k2)),
            "skewed": (skewed, i1([key_of(algo, s) for s in skewed], k1, k2)),
        }
        result[name] = {"band": [lo, hi]}
        for arm, (seeds, v) in arms.items():
            result[name][arm] = [{"key_seed": s, "I1": float(x)} for s, x in zip(seeds, v)]
            print(f"{name:12s}{arm:>9s}  {v.min():.4f}〜{v.max():.4f}（中央値 {np.median(v):.4f}）")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n保存: {OUT}")
    for name in FUNCS:
        seeds = ",".join(str(r["key_seed"]) for r in result[name]["skewed"])
        print(f"  {name} ③: --key_seeds {seeds}")


if __name__ == "__main__":
    main()
