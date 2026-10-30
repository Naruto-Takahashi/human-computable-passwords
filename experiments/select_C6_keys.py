#!/usr/bin/env python3
r"""実験C6 のための鍵選定: 同じ鍵の数字の付け替えで $I_1$ の低い版と高い版を作る．

数字の付け替え $\sigma' = \pi \circ \sigma$ は，どの位置どうしが同じ数字かとヒストグラムの形
（エントロピー・最多重複）を変えず，$I_1$ だけを動かす（docs/experiment_index.md の実験C6）。

候補の鍵を連番 seed で順に見て，次を満たす最初の `N_SELECT` 本を選ぶ。

- 高い版: $I_1$ が `HIGH_BAND` に入る付け替え
- 低い版: $I_1 \le$ `LOW_MAX` で，期待基準線 $\max P(z)$ が高い版と `BASE_TOL` 以内の付け替え

組が複数あるときは，期待基準線の差が最も小さい組を取る（結果を見る前に決めた規則）。
$I_1$ と基準線は付け替えの間でも強く相関する（$\rho \approx 0.95$）ため，素朴に選ぶと
差が許容幅いっぱいで常に高い版の側に偏る。付け替えの候補は固定 seed の
並べ替え `N_PERMS` 通りで，恒等写像を含む。

    python3 experiments/select_C6_keys.py

出力: `results/path_c/C6_keys.json`（鍵 seed・2つの付け替え・それぞれの $I_1$ と期待基準線）。
`train_pathC.py --key_seeds <seed> --digit_perm <付け替え>` にそのまま渡せる形。
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

OUT = os.path.join(REPO, "results/path_c/C6_keys.json")
ALGO, K1, K2 = "func_13_k26", 1, 3
N_SELECT = 15
SEED_BASE = 60000000
N_CANDIDATES = 1000
N_PERMS = 5000
PERM_SEED = 0
LOW_MAX = 0.002
HIGH_BAND = (0.010, 0.020)
BASE_TOL = 0.003


def relabel_signal(key, perms):
    """各付け替えの (I_1, 期待基準線)。付け替え後の分布は p'[π[d]] = p[d]。"""
    p = digit_dist(key)[0]
    P = np.empty((len(perms), 10))
    np.put_along_axis(P, perms, np.broadcast_to(p, P.shape), axis=1)
    return first_order_signal(P, K1, K2)


def pick(i1, base):
    lo = np.where(i1 <= LOW_MAX)[0]
    hi = np.where((i1 >= HIGH_BAND[0]) & (i1 <= HIGH_BAND[1]))[0]
    if not len(lo) or not len(hi):
        return None
    diff = np.abs(base[hi][:, None] - base[lo][None, :])
    a, b = np.unravel_index(np.argmin(diff), diff.shape)
    return (lo[b], hi[a]) if diff[a, b] <= BASE_TOL else None


def main():
    rng = np.random.default_rng(PERM_SEED)
    perms = np.array([np.arange(10)] + [rng.permutation(10) for _ in range(N_PERMS - 1)])
    algo = get_algorithm(ALGO)
    chosen, n_seen = [], 0
    for seed in range(SEED_BASE, SEED_BASE + N_CANDIDATES):
        n_seen += 1
        key = make_dataset(algo, 1, seed)[2]
        i1, base = relabel_signal(key, perms)
        found = pick(i1, base)
        if found is None:
            continue
        lo, hi = found
        chosen.append({
            "key_seed": seed,
            "counts_sorted": sorted(np.bincount(key, minlength=10).tolist(), reverse=True),
            "I1_original": float(i1[0]),
            "low": {"digit_perm": "".join(map(str, perms[lo])), "I1": float(i1[lo]),
                    "baseline_expected": float(base[lo])},
            "high": {"digit_perm": "".join(map(str, perms[hi])), "I1": float(i1[hi]),
                     "baseline_expected": float(base[hi])},
        })
        if len(chosen) == N_SELECT:
            break
    if len(chosen) < N_SELECT:
        raise SystemExit(f"条件を満たす鍵が {len(chosen)} 本しかない")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"algorithm": ALGO, "candidates_seen": n_seen, "keys": chosen},
                  f, ensure_ascii=False, indent=2)
    print(f"候補 {n_seen} 本中 {N_SELECT} 本を選んだ。保存: {OUT}")
    print(f"{'seed':>9s} {'形':>11s} {'元':>7s} {'低い版':>18s} {'高い版':>18s} {'基準線の差':>8s}")
    for c in chosen:
        lo, hi = c["low"], c["high"]
        print(f"{c['key_seed']:>9d} {''.join(map(str, c['counts_sorted'])):>11s} {c['I1_original']:.4f}"
              f"  {lo['digit_perm']} {lo['I1']:.4f}  {hi['digit_perm']} {hi['I1']:.4f}"
              f"  {hi['baseline_expected'] - lo['baseline_expected']:+.4f}")


if __name__ == "__main__":
    main()
