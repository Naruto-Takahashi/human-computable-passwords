#!/usr/bin/env python3
r"""実験C4（予備解析）: 鍵ごとの1次と2次の信号が分けられるかを見る（離陸の列は読まない）．

    python3 tools/signal_order_check.py      # 約7分（鍵1本あたり約3.5秒）

C2・C2.1・C2.1再測の鍵それぞれについて，$I_1$ と Efron–Stein の重み
$W_1$・$W_2$・$W_2$ のうちポインタ項の位置を含む組の分（`experiments/signal_strength.py`）を
計算し，鍵どうしの順位相関を出す．順位相関が1に近ければ，既存の鍵では
「1次を統制して2次が効くか」を問えない．
"""
import glob
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "experiments"))
from signal_strength import digit_dist, efron_stein_weights, first_order_signal  # noqa: E402

K = {"func_31": (3, 1), "func_22": (2, 2), "func_13_k26": (1, 3)}
SETS = {"C2": "C2", "C2.1": "C2_1", "C2.1再測": "C2_1_f31b"}


def main():
    for name, d in SETS.items():
        keys = {}
        for f in glob.glob(os.path.join(REPO, f"results/path_c/{d}/*.jsonl")):
            for line in open(f):
                r = json.loads(line)
                keys.setdefault(r["algorithm"], {})[r["key_seed"]] = r["key"]
        for algo, ks in keys.items():
            k1, k2 = K[algo]
            rows = []
            for key in ks.values():
                p = digit_dist(key)[0]
                W1, W2, W2p = efron_stein_weights(p, k1, k2)
                rows.append((first_order_signal(p, k1, k2)[0][0], W1, W2, W2p))
            rho = spearmanr(np.array(rows)).statistic
            print(f"{name} {algo} 鍵{len(rows)}本: rho(I1,W1)={rho[0, 1]:+.2f} "
                  f"rho(W1,W2)={rho[1, 2]:+.2f} rho(W1,W2ptr)={rho[1, 3]:+.2f}")


if __name__ == "__main__":
    main()
