#!/usr/bin/env python3
r"""実験R1: C2・C2.1 で決めた $I_1$ の閾値で，新しいランダムな鍵の離陸を当てられるか．

設計は docs/experiment_index.md の実験R1。2段に分ける（事前登録のため）。

    python3 experiments/analyze_R1.py prereg     # 学習前: D だけで閾値を決め，新しい鍵の予測を書き出す
    python3 experiments/analyze_R1.py evaluate   # 学習後: 予測を読み，判定する（閾値は決め直さない）

- D（閾値を決める）: C2・C2.1 の $f_{2,2}$・$f_{1,3}$（$N=26$），初期値 700・701
- 主（新しい鍵）: $N=26$ のランダムな鍵 各30本（seed 70000000〜／71000000〜），初期値 700・701
- 単位は鍵（C6 は版）。初期値のどれかで検証正解率の最大が 0.5 を超えたら離陸

`prereg` の出力 `results/path_c/R1_prereg.json` は学習を回す前にコミットする。
`evaluate` の図は `docs/reports/figures/r1_threshold.svg`。
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu, spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "experiments"))
sys.path.insert(0, os.path.join(REPO, "tools"))
from signal_strength import digit_dist, first_order_signal  # noqa: E402

THRESHOLD = 0.5
INITS = (700, 701)
N_NEW = 30
NEW_SEED = {"f22": 70000000, "f13": 71000000}
NEW_ALGO = {"f22": "func_22", "f13": "func_13_k26"}
N_BOOT = 10000
BOOT_SEED = 0
FUNCS = {"f22": (2, 2), "f13": (1, 3)}
PREREG = os.path.join(REPO, "results/path_c/R1_prereg.json")
OUT = os.path.join(REPO, "docs/reports/figures/r1_threshold.svg")


def func_of(algorithm):
    if algorithm.startswith("func_22"):
        return "f22"
    if algorithm.startswith("func_13"):
        return "f13"
    return None


def key_features(key, fn):
    k1, k2 = FUNCS[fn]
    p = digit_dist(key)
    i1, base_exp = first_order_signal(p, k1, k2)
    pr = p[0][p[0] > 0]
    return {"I1": float(i1[0]), "base_exp": float(base_exp[0]),
            "entropy": float(-(pr * np.log2(pr)).sum())}


def load_units(exp, keep=lambda r: True):
    """実験の jsonl → 鍵（版）ごとの dict。初期値は INITS だけを使う。"""
    units = defaultdict(lambda: {"vals": {}})
    for f in glob.glob(os.path.join(REPO, f"results/path_c/{exp}/*.jsonl")):
        for line in open(f):
            if not line.strip():
                continue
            r = json.loads(line)
            fn = func_of(r["algorithm"])
            if (fn is None or r.get("model", "transformer") != "transformer"
                    or r["init_seed"] not in INITS or not keep(r)):
                continue
            uid = (exp, r["algorithm"], r["key_seed"], r.get("digit_perm"), r.get("tile_key", 1),
                   r["epochs"], r["datasize"])
            u = units[uid]
            u.update(exp=exp, func=fn, algorithm=r["algorithm"], key_seed=r["key_seed"],
                     digit_perm=r.get("digit_perm"), tile=r.get("tile_key", 1), n=r["n_images"],
                     key=r["key"], baseline=r["baseline_majority_val"])
            u["vals"][r["init_seed"]] = r["val_accuracy_max"]
    out = []
    for u in units.values():
        if set(u["vals"]) != set(INITS):
            raise SystemExit(f"初期値が欠けている: {u['exp']} {u['algorithm']} {u['key_seed']}")
        u.update(key_features(u["key"], u["func"]))
        u["n_takeoff"] = sum(v > THRESHOLD for v in u["vals"].values())
        u["takeoff"] = u["n_takeoff"] > 0
        out.append(u)
    return out


def fit_threshold(units):
    r"""D で Youden 指数（感度＋特異度−1）が最大になる t（$I_1 \ge t$ なら離陸と予測）。

    隣り合う $I_1$ の間 (lo, hi] では予測が変わらないので，その区間の両端の幾何平均を取る。
    最大の区間が複数あるときは最も低い区間を取る（事前に決めた規則）。
    """
    x = np.array([u["I1"] for u in units])
    y = np.array([u["takeoff"] for u in units])
    xs = np.unique(x)
    gaps = list(zip(np.concatenate([[xs[0] / 2], xs]), np.concatenate([xs, [xs[-1] * 2]])))
    def youden(hi):
        pred = x >= hi
        return pred[y].mean() + (~pred[~y]).mean() - 1
    J = [youden(hi) for _, hi in gaps]
    best = max(J)
    ties = [g for g, j in zip(gaps, J) if np.isclose(j, best)]
    lo, hi = ties[0]
    correct = int(((x >= hi) == y).sum())
    return float(np.sqrt(lo * hi)), float(best), correct, (float(lo), float(hi)), len(ties)


def prereg():
    sys.path.insert(0, os.path.join(REPO, "src"))
    from hcp.algorithms import get_algorithm
    from train_pathC import make_dataset
    D = load_units("C2") + load_units("C2_1")
    out = {"rule": "I1 >= t なら離陸と予測。t は C2・C2.1（初期値700・701）の Youden 最大",
           "inits": list(INITS), "functions": {}}
    for fn in FUNCS:
        d = [u for u in D if u["func"] == fn]
        t, J, correct, iv, nties = fit_threshold(d)
        algo = get_algorithm(NEW_ALGO[fn])
        keys = []
        for s in range(NEW_SEED[fn], NEW_SEED[fn] + N_NEW):
            f = key_features(make_dataset(algo, 1, s)[2], fn)
            keys.append({"key_seed": s, **f, "predict_takeoff": f["I1"] >= t})
        n_pos = sum(k["predict_takeoff"] for k in keys)
        out["functions"][fn] = {"algorithm": NEW_ALGO[fn], "threshold": t, "youden_D": J,
                                "correct_D": correct, "n_D": len(d),
                                "takeoff_D": int(sum(u["takeoff"] for u in d)),
                                "interval": iv, "n_ties": nties, "keys": keys}
        print(f"{fn}: t = {t:.5f}（区間 {iv[0]:.5f}〜{iv[1]:.5f}，同点 {nties}），D の Youden {J:.3f}・"
              f"正答 {correct}/{len(d)}（D の離陸 {sum(u['takeoff'] for u in d)}/{len(d)}）")
        print(f"    新しい鍵 {N_NEW} 本: 離陸と予測 {n_pos}・離陸しないと予測 {N_NEW - n_pos}，"
              f"I1 {min(k['I1'] for k in keys):.4f}〜{max(k['I1'] for k in keys):.4f}")
    with open(PREREG, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"保存: {PREREG}（学習を回す前にコミットする）")


def auc(x, y):
    pos, neg = x[y], x[~y]
    if not len(pos) or not len(neg):
        return float("nan")
    return mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg))


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def two_by_two(units, t):
    """閾値以上・未満それぞれの離陸数と，片側 Fisher（以上の側が離陸しやすい）の p。"""
    hi = [u["takeoff"] for u in units if u["I1"] >= t]
    lo = [u["takeoff"] for u in units if u["I1"] < t]
    table = [[sum(hi), len(hi) - sum(hi)], [sum(lo), len(lo) - sum(lo)]]
    p = fisher_exact(table, alternative="greater").pvalue if hi and lo else float("nan")
    correct = sum(hi) + len(lo) - sum(lo)
    return table, p, correct


def key_level_aic(units, feature):
    """鍵単位の二値（どちらかの初期値で離陸）を1変数のロジスティック回帰で当てたときの AIC。"""
    from scipy.optimize import minimize
    from scipy.special import log_expit
    x = np.array([feature(u) for u in units])
    x = (x - x.mean()) / x.std()
    y = np.array([u["takeoff"] for u in units])

    def nll(b):
        eta = b[0] + b[1] * x
        return -(y * log_expit(eta) + (~y) * log_expit(-eta)).sum()

    return 2 * 2 + 2 * minimize(nll, np.zeros(2), method="BFGS").fun


def report_block(name, units, t):
    if not units:
        return
    table, p, correct = two_by_two(units, t)
    y = np.array([u["takeoff"] for u in units])
    x = np.array([u["I1"] for u in units])
    print(f"  {name:22s}: 離陸 {int(y.sum())}/{len(y)}，閾値以上 {table[0][0]}/{sum(table[0])}・"
          f"未満 {table[1][0]}/{sum(table[1])}，正答 {correct}/{len(y)}（多数派 {max(y.sum(), len(y) - y.sum())}），"
          f"Fisher p={p:.3g}，AUC {auc(x, y):.3f}")


def evaluate():
    pre = json.load(open(PREREG))
    new = load_units("R1")
    D = load_units("C2") + load_units("C2_1")
    arm = {}
    for algo, d in json.load(open(os.path.join(REPO, "results/path_c/C5_keys.json"))).items():
        for name in ("balanced", "random", "skewed"):
            for k in d[name]:
                arm[(algo, k["key_seed"])] = name
    C5 = load_units("C5")
    for u in C5:
        u["arm"] = arm[(u["algorithm"], u["key_seed"])]
    C6 = load_units("C6")
    C3 = load_units("C3", keep=lambda r: r["n_images"] == 104 and r["epochs"] == 100)

    ps, res = [], {}
    for fn, spec in pre["functions"].items():
        t = spec["threshold"]
        v = [u for u in new if u["func"] == fn]
        pred = {k["key_seed"]: k for k in spec["keys"]}
        if len(v) != N_NEW or any(abs(pred[u["key_seed"]]["I1"] - u["I1"]) > 1e-9 for u in v):
            raise SystemExit(f"{fn}: 新しい鍵が事前登録と一致しない（{len(v)} 本）")
        table, p, correct = two_by_two(v, t)
        ps.append(p)
        res[fn] = (t, v, table, p, correct)
    adj = holm(np.array(ps))

    rng = np.random.default_rng(BOOT_SEED)
    for (fn, (t, v, table, p, correct)), padj in zip(res.items(), adj):
        y = np.array([u["takeoff"] for u in v])
        print(f"=== {fn}（t = {t:.5f}）===")
        print(f"[主] 新しい鍵: 閾値以上 {table[0][0]}/{sum(table[0])} 離陸，未満 {table[1][0]}/{sum(table[1])} 離陸，"
              f"片側 Fisher p = {p:.3g}，Holm 後 {padj:.3g}")
        print(f"     閾値での正答 {correct}/{len(v)}（多数派の予測 {max(y.sum(), len(y) - y.sum())}/{len(v)}）")
        aucs = {}
        for feat, sign in (("I1", 1), ("base_exp", 1), ("entropy", -1)):
            x = sign * np.array([u[feat] for u in v])
            aucs[feat] = auc(x, y)
        diffs = []
        for _ in range(N_BOOT):
            idx = rng.integers(len(v), size=len(v))
            yb = y[idx]
            if yb.all() or not yb.any():
                continue
            xi = np.array([v[i]["I1"] for i in idx])
            xb = np.array([v[i]["base_exp"] for i in idx])
            diffs.append(auc(xi, yb) - auc(xb, yb))
        lo, hi = np.percentile(diffs, [2.5, 97.5]) if diffs else (np.nan, np.nan)
        print(f"     AUC: I1 {aucs['I1']:.3f}・期待基準線 {aucs['base_exp']:.3f}・エントロピー（負） {aucs['entropy']:.3f}，"
              f"I1 − 基準線 の 95% 区間 [{lo:.3f}, {hi:.3f}]")
        rho = spearmanr([u["I1"] for u in v], [u["n_takeoff"] for u in v])
        print(f"     離陸した初期値の数（0/1/2）と I1 の順位相関 {rho.statistic:.2f}（p={rho.pvalue:.3g}）")
        for u in sorted([u for u in v if (u["I1"] >= t) != u["takeoff"]], key=lambda u: u["I1"]):
            print(f"     外れ: seed {u['key_seed']} I1 {u['I1']:.4f} 基準線 {u['baseline']:.3f} "
                  f"離陸 {u['n_takeoff']}/2（{'離陸と予測' if u['I1'] >= t else '離陸しないと予測'}）")
        print("[副] 既存の鍵（記述）")
        report_block("C5② ランダム（N=30）", [u for u in C5 if u["func"] == fn and u["arm"] == "random"], t)
        report_block("C5③ 偏りの大きい（N=30）", [u for u in C5 if u["func"] == fn and u["arm"] == "skewed"], t)
        c5b = [u for u in C5 if u["func"] == fn and u["arm"] == "balanced"]
        if c5b:
            print(f"  {'C5① そろえた（N=30）':22s}: 離陸 {sum(u['takeoff'] for u in c5b)}/{len(c5b)}"
                  f"（I1=0 で離陸しないと予測。並べ替えで移り合う1つの塊として数える）")
        report_block("C6 付け替え（N=26）", [u for u in C6 if u["func"] == fn], t)
        report_block("C3② 双子（N=104）", [u for u in C3 if u["func"] == fn and u["tile"] > 1], t)
        report_block("C3③ ランダム（N=104）", [u for u in C3 if u["func"] == fn and u["tile"] == 1], t)
        d = [u for u in D if u["func"] == fn]
        print(f"[R1b] D の AIC（鍵単位の二値）: log10 I1 {key_level_aic(d, lambda u: np.log10(u['I1'])):.1f}，"
              f"エントロピー {key_level_aic(d, lambda u: u['entropy']):.1f}，"
              f"期待基準線 {key_level_aic(d, lambda u: u['base_exp']):.1f}\n")
    figure(D, new, C5 + C6, {fn: s["threshold"] for fn, s in pre["functions"].items()})


def figure(D, new, old, th):
    import matplotlib.pyplot as plt
    from palette import LIGHT, INK2, AXIS, matplotlib_rc
    plt.rcParams.update(matplotlib_rc())
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
    floor = 3e-5
    rows = [("C2・C2.1（閾値を決めた）", D, LIGHT[0]), ("新しい鍵（予測した）", new, LIGHT[1]),
            ("C5・C6（参考）", old, LIGHT[2])]
    rng = np.random.default_rng(1)
    for ax, fn, title in zip(axes, ("f22", "f13"), ("$f_{2,2}$", "$f_{1,3}$")):
        for yi, (label, us, col) in enumerate(rows):
            us = [u for u in us if u["func"] == fn]
            if not us:
                continue
            x = np.array([max(u["I1"], floor) for u in us])
            jit = rng.uniform(-0.1, 0.1, len(us))
            off = np.array([u["takeoff"] for u in us])
            ax.scatter(x[off], yi + 0.17 + jit[off], s=12, color=col)
            ax.scatter(x[~off], yi - 0.17 + jit[~off], s=12, facecolor="none", edgecolor=col)
        ax.axvline(th[fn], color=INK2, lw=0.8, ls="--")
        ax.set_xscale("log")
        ax.set_xlim(floor / 1.5, 0.3)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("$I_1$（bit，0 は左端）")
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r[0] for r in rows])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(color=AXIS)
    fig.text(0.5, -0.05, "各段の上＝離陸した鍵，下（白抜き）＝離陸しなかった鍵，破線＝C2・C2.1 で決めた閾値",
             ha="center", fontsize=8, color=INK2)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"図: {OUT}")


if __name__ == "__main__":
    {"prereg": prereg, "evaluate": evaluate}[sys.argv[1] if len(sys.argv) > 1 else "evaluate"]()
