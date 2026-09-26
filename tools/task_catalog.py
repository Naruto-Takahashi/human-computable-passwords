#!/usr/bin/env python3
"""扱っている課題の一覧（パラメータと理論値）を生成する．

関数の定義は algorithms.py，記号の定義は docs/hcp_background.md が正本である．
ここはそれらから**計算で出せる量**を一覧にするだけで，手で数値を書かない。

出力: docs/task_catalog.md（`make catalog` で再生成）
"""
import argparse
import collections
import statistics
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
          "func_22_k10": (2, 2), "func_31": (3, 1),
          "func_13_k10": (1, 3), "func_31_k10": (3, 1)}

# 一覧に出す課題（研究で実際に使っているもの）
CATALOG = [
    "narrowptr_k4_m1", "narrowptr_k4_m2",
    "table_add4_k4", "table_add5_k4", "table_add6_k4",
    "table_add3_k10", "narrowptr_k10_m1", "narrowptr_k10_m2",
    "func_13_k10", "func_22_k10", "func_31_k10",
    "narrowptr_k5_m2", "table_add3_k15", "table_add3_k26",
    "func_22", "func_31", "func_13_k26", "func_13",
]


def security_parameter(k1: int, k2: int) -> float:
    """原論文 Claim 1 の s(f) = min{(k2+1)/2, k1+1, 11}."""
    return min((k2 + 1) / 2, k1 + 1, 11)


def info_limits() -> dict:
    """ソルバーの測定結果から，条件ごとの m*_info を求め，中央値と最悪値を返す．

    **単位は「鍵」ではなく (鍵シード, データシード) の条件である。**
    2026-09-26 の点検で，閾値のばらつきの 77〜85% は**どの観測を引いたか**に
    由来し，鍵で説明できるのは 15〜23% だけだと分かった。同じ鍵が引き次第で
    10 にも 17 にもなる。「鍵ごとの閾値」と呼ぶと実験5b と同じ誤りになる。

    **「全条件が一意になる最小の m」を使ってはいけない。**それは最大値統計で，
    頑固な1条件に引きずられる。本研究が先行研究の「エポック最大値で語る」集計を
    批判しているのと同じ誤りである。

    戻り値は (中央値, 最悪値, 測定した最大の m)。条件ごとの閾値は「その m 以降
    ずっと一意であり続ける最小の m」とする（単発の一致を拾わない）。
    """
    out = {}
    for path in glob.glob(os.path.join(ROOT, "results", "solver", "*_info_limit.csv")):
        name = os.path.basename(path).replace("_info_limit.csv", "")
        by_cond = collections.defaultdict(dict)
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cond = (int(row["key_seed"]), int(row["data_seed"]))
                by_cond[cond][int(row["n_shot"])] = (row["unique"] == "True")
        ms = sorted({m for d in by_cond.values() for m in d})
        thresholds = []
        for d in by_cond.values():
            for i, m in enumerate(ms):
                if all(d.get(later, False) for later in ms[i:]):
                    thresholds.append(m)
                    break
        if thresholds:
            med = statistics.median(thresholds)
            med = int(med) if float(med).is_integer() else med
            out[name] = (med, max(thresholds),
                         max(ms) if ms else None)
        else:
            out[name] = (None, None, max(ms) if ms else None)
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


def shift_symmetries(algo, key, samples=3000, seed=0):
    """鍵の全マスに同じ値 c を足しても，全チャレンジで答えが変わらない c の個数．

    1 なら鍵は一意に復元しうる。2 以上なら **観測をいくら増やしても
    その個数まで候補が残る**ので，`recover_key` の完全一致は原理的に不可能である。

    純粋な和（ポインタなし）では $\gcd(\text{足す項数}, 10)$ に一致する。
    ポインタがあると，鍵をずらすと行き先 $j$ 自体が動くため対称性が壊れ，
    多くの場合 1 になる。**式で決め打ちせず実測する**のはそのため
    （2026-09-23 に $\gcd$ だけで判断して誤った）。
    """
    rng = np.random.default_rng(seed)
    n = len(key)
    ch = rng.integers(0, n, size=(samples, 14))
    base = [algo.fn(c.tolist(), key) for c in ch]
    count = 0
    for c in range(10):
        shifted = [(v + c) % 10 for v in key]
        if all(algo.fn(x.tolist(), shifted) == b for x, b in zip(ch, base)):
            count += 1
    return count


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
        " 真の場合の数 | 衝突確率 | 鍵の一意性 | $`m^*_{\\text{info}}`$ |",
        "|---|---:|:---:|---:|---:|---:|---:|---:|:---:|---:|",
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
        sym = shift_symmetries(algo, key)
        sym_s = "一意" if sym == 1 else f"**{sym}通り**"
        med, worst, top = limits.get(name, (None, None, None))
        if med is None:
            lim = f"> {top}" if top else "未測定"
        elif worst == med:
            lim = str(med)
        else:
            lim = f"{med}（最悪 {worst}）"
        md.append(f"| `{name}` | {len(key)} | {fam_s} | {s} | {addend_count(name, fam)} "
                  f"| {len(pos)} | {tc_s} | {coll:.1f}% | {sym_s} | {lim} |")

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
        "| **鍵の一意性** | 鍵の全マスに同じ値を足しても答えが変わらない「ずらし対称性」の数。"
        "**2通り以上なら `recover_key` の完全一致は原理的に不可能**（観測をいくら増やしても"
        "その個数まで候補が残る）。予測タスクには影響しない（縮退した鍵は全チャレンジで同じ答えを返す） |",
        "| $`m^*_{\\text{info}}`$ | 鍵が一意に定まる最小の観測数（ソルバーで数え上げ）。"
        "**これ未満では復元は原理的に不可能**で，LLM の失敗は能力の問題ではない |",
        "",
        "## 鍵の一意性 — `recover_key` に使える課題の見分け方",
        "",
        "純粋な和（ポインタなし）では，ずらし対称性の数は $`\\gcd(\\text{足す項数}, 10)`$ に一致する。",
        "",
        "| 足す項数 | 2 | 3 | 4 | 5 | 6 | 7 |",
        "|---|---|---|---|---|---|---|",
        "| $`\\gcd(N,10)`$ | 2 | **1** | 2 | 5 | 2 | **1** |",
        "",
        "**`table_add3` が一意なのは偶然である。**3 が 10 と互いに素だったからにすぎない。",
        "2項の `table_add_k*` は以前から2通りに縮退していたが，`recover_key` を"
        "使っていなかったため表面化しなかった。",
        "",
        "> [!WARNING]",
        "> **$`\\gcd`$ の式だけで判断してはいけない。**ポインタがあると，鍵をずらすと"
        "行き先 $`j`$ 自体が動くため対称性が壊れる。`func_13`（4項）や `func_31`（2項）は"
        "式の上では縮退しそうだが，実測では一意である。**この列は実測値である。**",
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
        "**$`n=10`$ の3点（2026-09-26 測定．鍵10本 × 観測の引き5本 = 各50条件，"
        "打ち切りゼロの厳密値）では，$`s(f)`$ が 1.0 / 1.5 / 2.0 と変わっても "
        "$`m^*_{\\text{info}}`$ の中央値は 3点とも 11 で変わらない。**"
        "平均は 11.20 / 11.26 / 11.74 で，鍵を単位にした保守的な検定でも "
        "$`p = 0.16`$（Kruskal-Wallis）。検出力から言えるのは「差は 0.6 観測より小さい」"
        "までで，差がゼロだとは示していない。",
        "",
        "$`\\approx 1.1n`$ である。「1観測が10進1桁を与えるので $`m \\ge n`$ が必要」"
        "という数え上げの下限に 10% 上乗せしただけの値で，"
        "$`s(f)`$ は統計的攻撃者の標本量 $`m = \\tilde{\\Omega}(n^{s(f)})`$ を支配する指数，"
        "$`m^*_{\\text{info}}`$ は識別可能性——という別物だという読みと整合する。",
        "",
        "**ばらつきは鍵ではなく観測の引きに由来する。**分散分解では鍵で説明できるのが "
        "15〜23%，残り 77〜85% はどの観測を引いたかである。同じ鍵が引き次第で 10 にも "
        "17 にもなるため，**「鍵ごとの閾値」と呼んではいけない**（実験5b と同じ誤りになる）。",
        "",
        "差の兆しがあるのは中央ではなく**裾**である。条件内分散は足す項数 2 の "
        "`func_31_k10` で 3.51，3 の `func_22_k10` で 0.87，4 の `func_13_k10` で 1.84，"
        "最悪値は 18 / 13 / 17。ただし Fligner-Killeen で $`p = 0.054`$ と境界であり，"
        "3群しかないので確定していない。",
        "",
        "鍵26マス系は関数によって分かれる。`func_22` は $`m=50`$ で一意性を証明できたが，"
        "`func_31` / `func_13_k26` は足す項数が少なく制約が弱いため，$`m=50`$・"
        "ノード上限200万では869秒かけて打ち切りになる（真の鍵自体は見つかる）。"
        "より大きな $`m`$ での測定は継続中。",
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
