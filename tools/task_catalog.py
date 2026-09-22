#!/usr/bin/env python3
"""扱っている課題の一覧（パラメータと理論値）を生成する．

関数の定義は algorithms.py，記号の定義は docs/hcp_background.md が正本である．
ここはそれらから**計算で出せる量**を一覧にするだけで，手で数値を書かない。

出力: docs/task_catalog.md（`make catalog` で再生成）
"""
import argparse
import collections
import csv
import glob
import itertools
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from hcp import generate_dataset                      # noqa: E402
from hcp.algorithms import ALGORITHMS                 # noqa: E402
from seen_unseen import relevant_positions            # noqa: E402

# f_{k1,k2} 族のパラメータ（それ以外の関数は族の外なので s(f) が定義されない）
FAMILY = {"func_13": (1, 3), "func_13_k26": (1, 3), "func_22": (2, 2),
          "func_22_k10": (2, 2), "func_31": (3, 1)}

# 一覧に出す課題（研究で実際に使っているもの）
CATALOG = [
    "narrowptr_k4_m1", "narrowptr_k4_m2",
    "table_add4_k4", "table_add5_k4", "table_add6_k4",
    "table_add3_k10", "narrowptr_k10_m1", "narrowptr_k10_m2", "func_22_k10",
    "narrowptr_k5_m2", "table_add3_k15", "table_add3_k26",
    "func_22", "func_31", "func_13_k26", "func_13",
]


def security_parameter(k1: int, k2: int) -> float:
    """原論文 Claim 1 の s(f) = min{(k2+1)/2, k1+1, 11}."""
    return min((k2 + 1) / 2, k1 + 1, 11)


def info_limits() -> dict:
    """ソルバーの測定結果から，一意特定率100%になった最小の観測数 m を拾う．"""
    out = {}
    for path in glob.glob(os.path.join(ROOT, "results", "solver", "*_info_limit.csv")):
        name = os.path.basename(path).replace("_info_limit.csv", "")
        by = collections.defaultdict(list)
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                by[int(row["n_shot"])].append(row["unique"] == "True")
        uniq = [m for m, flags in sorted(by.items()) if all(flags)]
        out[name] = (min(uniq) if uniq else None, max(by) if by else None)
    return out


def true_case_count(algo, key, pos, n_keys=80, cap=40000, seed=0):
    """「どの鍵でも同じ答えを与える入力」を同一視した場合の数．

    k^位置数 は対称な関数で過大評価になる（table_add6 は 4^6=4096 ではなく84）。
    """
    n = len(key)
    total = n ** len(pos)
    rng = np.random.default_rng(seed)
    keys = [rng.integers(0, 10, n).tolist() for _ in range(n_keys)]
    exact = total <= cap
    if exact:
        tuples = list(itertools.product(range(n), repeat=len(pos)))
    else:
        tuples = list({tuple(rng.integers(0, n, len(pos))) for _ in range(cap)})
    sig = np.empty((len(tuples), n_keys), dtype=np.int8)
    for i, t in enumerate(tuples):
        ch = [0] * 14
        for p, v in zip(pos, t):
            ch[p] = v
        for j, k in enumerate(keys):
            sig[i, j] = algo.fn(ch, k)
    return len(np.unique(sig, axis=0)), exact


def collision_probability(algo, key, samples=20000, seed=7):
    rng = np.random.default_rng(seed)
    n = len(key)
    ch = rng.integers(0, n, size=(samples, 14))
    z = np.array([algo.fn(c.tolist(), key) for c in ch])
    p = np.bincount(z, minlength=10) / samples
    return float((p ** 2).sum())


def addend_count(name, fam):
    if name.startswith("narrowptr"):
        return "3"
    if "table_add" in name:
        tail = name.split("add")[1]
        return tail[0] if tail[0].isdigit() else "2"
    return str(fam[1] + 1) if fam else "—"


def build() -> list[str]:
    limits = info_limits()
    md = [
        "# 課題の一覧（パラメータと理論値）",
        "",
        "> 扱っている関数・鍵サイズ・理論値を1枚に。**`make catalog` で再生成**",
        ">",
        "> 📚 [ドキュメント索引](README.md) ／ 関連: [記号と関数の正本](hcp_background.md) ・"
        " [実験の一覧](experiment_index.md)",
        "",
        "> [!IMPORTANT]",
        "> **記号が先行研究と衝突している。**原論文（および本ドキュメント）では"
        " $`n`$ が鍵サイズ，$`m`$ が観測数だが，**小川(2025) の卒論は $`N`$ を鍵サイズ**"
        "として使っている。引用時は「$`N=26`$（本研究の $`n=26`$）」のように併記すること。",
        "",
        "| 記号 | 意味 |",
        "|---|---|",
        "| $`n`$ | 鍵 $`\\sigma`$ のマス数（$`\\sigma : [n] \\to \\mathbb{Z}_{10}`$） |",
        "| $`m`$ | 観測したチャレンジ・応答の組数 |",
        "| $`k`$ | チャレンジ長。本研究では常に **14**（$`= 10 + k_1 + k_2`$） |",
        "| $`k_1, k_2`$ | 関数族 $`f_{k_1,k_2}`$ のパラメータ |",
        "| $`s(f)`$ | 安全性パラメータ $`\\min\\lbrace (k_2+1)/2,\\ k_1+1,\\ 11 \\rbrace`$。"
        "攻撃に $`m = \\tilde{\\Omega}(n^{s(f)})`$ の観測を要する |",
        "",
        "## 一覧",
        "",
        "| 関数 | $`n`$ | $`k_1,k_2`$ | $`s(f)`$ | 足す項数 | 効く位置 |"
        " 真の場合の数 | 衝突確率 | $`m^*_{\\text{info}}`$ |",
        "|---|---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in CATALOG:
        algo = ALGORITHMS.get(name)
        if algo is None:
            continue
        ds = generate_dataset(algo, n_shot=0, n_test=1, key_seed=0, data_seed=0)
        key = ds.key
        pos = relevant_positions(algo, key, n_probe=120)
        fam = FAMILY.get(name)
        s = f"{security_parameter(*fam):.1f}" if fam else "—"
        fam_s = f"{fam[0]},{fam[1]}" if fam else "—"
        if len(key) ** len(pos) <= 10 ** 7:
            tc, exact = true_case_count(algo, key, pos)
            tc_s = f"{tc:,}" + ("" if exact else "+")
        else:
            tc_s = "—"
        coll = collision_probability(algo, key) * 100
        lo, hi = limits.get(name, (None, None))
        lim = str(lo) if lo else (f"> {hi}" if hi else "未測定")
        md.append(f"| `{name}` | {len(key)} | {fam_s} | {s} | {addend_count(name, fam)} "
                  f"| {len(pos)} | {tc_s} | {coll:.1f}% | {lim} |")

    md += [
        "",
        "## 列の意味",
        "",
        "| 列 | 意味 |",
        "|---|---|",
        "| **足す項数** | 最後に足し合わせる値の個数。実験9 でここが結果を分けた |",
        "| **効く位置** | 14個の入力のうち答えに影響するものの数。値を振って実測する |",
        "| **真の場合の数** | 「どの鍵でも同じ答えを与える入力」を同一視した数。"
        "対称な関数では $`n^{\\text{位置数}}`$ を大きく下回る（`table_add6_k4` は 4096 ではなく 84） |",
        "| **衝突確率** | $`\\sum p_i^2`$。**偶然水準の 10% ではなくこれと比べる** |",
        "| $`m^*_{\\text{info}}`$ | 鍵が一意に定まる最小の観測数（ソルバーで数え上げ）。"
        "**これ未満では復元は原理的に不可能**で，LLM の失敗は能力の問題ではない |",
        "",
        "## $`m^*_{\\text{info}}`$ の読み方",
        "",
        "経路A（プロンプティング）はこの境界を使って3つの領域に分ける。",
        "",
        "| 領域 | 状態 | LLM が失敗したら |",
        "|---|---|---|",
        "| $`m \\lt m^*_{\\text{info}}`$ | 鍵が一意に定まらない | **能力の問題ではない**。原理的に不可能 |",
        "| $`m \\approx m^*_{\\text{info}}`$ | 鍵によって分かれる | 情報限界そのものを測れる |",
        "| $`m \\ge m^*_{\\text{info}}`$ | 一意。ソルバーが1秒未満で復元 | **純粋な推論の欠損** |",
        "",
        "`func_22_k10` では $`m^*_{\\text{info}} = 15`$ である"
        "（$`m=10`$ では鍵の 2/3 でしか一意にならない）。",
        "鍵26マス系は $`m=26`$ でもまだ一意化しておらず，より大きな $`m`$ の測定が要る。",
        "",
        "## 次に読む",
        "",
        "- [記号と関数の定義](hcp_background.md) — $`f_{k_1,k_2}`$ の定義，$`s(f)`$ の導出",
        "- [実験の一覧](experiment_index.md) — どの課題で何を測ったか",
    ]
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", default=os.path.join(ROOT, "docs", "task_catalog.md"))
    args = ap.parse_args()
    md = build()
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"保存完了: {args.output}（{len(CATALOG)} 課題）")


if __name__ == "__main__":
    main()
