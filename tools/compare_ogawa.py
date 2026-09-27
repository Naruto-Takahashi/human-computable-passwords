#!/usr/bin/env python3
"""小川ら Table 5/6（embedding+CNN）と経路C（Transformer）を横並びにする．

    python3 tools/compare_ogawa.py           # 表を標準出力へ
    python3 tools/compare_ogawa.py --md      # docs に貼る markdown

小川らの数値は英語論文 PDF の Table 3/4/5/6 から写した（2026-09-27 に原典確認）。
出所は docs/literature/ogawa2025_learning_hcp_neural_models.md §3.3。

**揃っている条件**: 鍵サイズ $N$，データ量，関数，10クラス分類，鍵は run ごとに独立生成。
**揃っていない条件**:
  - 予算: 小川らはエポック数を予備実験で選んだと書くだけで値を報告していない（§3.3）
  - 分割: 小川らは 8:2（試験集合なし，検証最大を報告）。経路C は 8:1:1
  - 基準線: 小川らは偶然水準 0.1 と比べる。経路C は鍵ごとの最頻値予測器を持つ
"""
import argparse
import collections
import glob
import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 小川ら Table 5（embedding+CNN）: 関数 → 件数 → N → (平均, sd, 最大)
OGAWA_CNN = {
    "f13": {
        1000:  {26: (0.1450, 0.0112, 0.1600), 50: (0.1450, 0.0117, 0.1550), 100: (0.1350, 0.0197, 0.1550)},
        5000:  {26: (0.1119, 0.0097, 0.1190), 50: (0.1168, 0.0036, 0.1200), 100: (0.1222, 0.0095, 0.1360)},
        10000: {26: (0.1103, 0.0112, 0.1275), 50: (0.1068, 0.0092, 0.1180), 100: (0.1069, 0.0083, 0.1150)},
        50000: {26: (0.1049, 0.0029, 0.1107), 50: (0.1041, 0.0015, 0.1060), 100: (0.1051, 0.0030, 0.1085)},
    },
    "f22": {
        1000:  {26: (0.1430, 0.0148, 0.1600), 50: (0.1390, 0.0147, 0.1600), 100: (0.1385, 0.0194, 0.1700)},
        5000:  {26: (0.1216, 0.0038, 0.1260), 50: (0.1151, 0.0075, 0.1310), 100: (0.1172, 0.0089, 0.1310)},
        10000: {26: (0.1545, 0.0423, 0.2115), 50: (0.1050, 0.0087, 0.1145), 100: (0.1053, 0.0080, 0.1120)},
        50000: {26: (0.2872, 0.1651, 0.6858), 50: (0.1054, 0.0020, 0.1083), 100: (0.1038, 0.0018, 0.1071)},
    },
    "f31": {
        1000:  {26: (0.1560, 0.0164, 0.1700), 50: (0.1490, 0.0156, 0.1700), 100: (0.1450, 0.0318, 0.1900)},
        5000:  {26: (0.1606, 0.0393, 0.2180), 50: (0.1264, 0.0117, 0.1420), 100: (0.1224, 0.0080, 0.1330)},
        10000: {26: (0.2036, 0.0547, 0.2640), 50: (0.1199, 0.0134, 0.1395), 100: (0.1162, 0.0098, 0.1250)},
        50000: {26: (0.2673, 0.0308, 0.2924), 50: (0.1666, 0.0729, 0.3214), 100: (0.1065, 0.0042, 0.1110)},
    },
    # Table 6（no-j ablation，50,000件のみ報告）
    "h": {
        50000: {26: (0.8080, 0.3917, 0.9987), 50: (0.5133, 0.4350, 1.0000), 100: (0.1278, 0.0470, 0.2118)},
    },
}

# 経路C の関数名 → 小川らの記号（統制②③は対応が無い＝本研究独自）
ALGO_TO_OGAWA = {
    "func_13_k26": "f13", "func_22": "f22", "func_31": "f31", "func_pow": "h",
    "table_add3_k26": None, "narrowptr_k26_m1": None,
}
LABEL = {
    "func_13_k26": "f13 (s=2.0)", "func_22": "f22 (s=1.5)", "func_31": "f31 (s=1.0)",
    "func_pow": "h  no-j 多項式", "table_add3_k26": "静的3項和 (独自)",
    "narrowptr_k26_m1": "j≡0 (独自)",
}
ORDER = ["func_13_k26", "func_22", "func_31", "func_pow", "table_add3_k26", "narrowptr_k26_m1"]


def load(readout="mean", epochs=30, d_model=64, num_layers=2, lr=1e-3):
    out = collections.defaultdict(list)
    for f in glob.glob(os.path.join(REPO, "results/path_c/*/runs_*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            if (r["readout"] == readout and r["epochs"] == epochs
                    and r["d_model"] == d_model and r["num_layers"] == num_layers
                    and abs(r["learning_rate"] - lr) < 1e-12):
                out[(r["algorithm"], r["datasize"])].append(r)
    return out


def cell(rs):
    if not rs:
        return "—", 0, 0
    v = np.array([x["val_accuracy_max"] for x in rs])
    sd = v.std(ddof=1) if len(v) > 1 else 0.0
    off = sum(1 for x in rs if x["val_accuracy_max"] > 0.5)
    return f"{v.mean():.4f}±{sd:.4f} ({v.max():.4f})", off, len(rs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--readout", default="mean")
    ap.add_argument("--epochs", type=int, default=30)
    a = ap.parse_args()
    data = load(readout=a.readout, epochs=a.epochs)

    sep = " | " if a.md else "  "
    pre = "| " if a.md else ""
    post = " |" if a.md else ""
    print(f"{pre}関数{sep}件数{sep}小川ら emb+CNN{sep}経路C Transformer{sep}離陸{post}")
    if a.md:
        print("|---|---:|---|---|---:|")
    for algo in ORDER:
        for d in (1000, 5000, 10000, 50000):
            rs = data.get((algo, d), [])
            ours, off, n = cell(rs)
            sym = ALGO_TO_OGAWA[algo]
            theirs = "—（本研究独自）"
            if sym and d in OGAWA_CNN.get(sym, {}):
                m, s, mx = OGAWA_CNN[sym][d][26]
                theirs = f"{m:.4f}±{s:.4f} ({mx:.4f})"
            takeoff = f"{off}/{n}" if n else "—"
            print(f"{pre}{LABEL[algo]}{sep}{d:,}{sep}{theirs}{sep}{ours}{sep}{takeoff}{post}")


if __name__ == "__main__":
    main()
