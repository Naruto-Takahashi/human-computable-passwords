#!/usr/bin/env python3
"""実験C1 の統計量を出す（報告書・卒論の数値の出所）．

    python3 tools/pathC_stats.py

出す量:
  1. 離陸率の Wilson 95% 信頼区間（二項比率。正規近似は n=20・p が 0/1 付近で破綻する）
  2. 関数間の比較は **対応のある検定**（McNemar の正確検定）。
     同じ (鍵, 初期値) の組を4関数すべてで共有しているため対応がある。
     実験13 で Kruskal-Wallis → Friedman に直したのと同じ理由。
  3. 鍵サイズ 26 対 50 は対応なし（鍵の長さが違えば別の鍵）→ Fisher の正確検定
  4. 「離陸は鍵で決まるか」= 鍵5本 × 離陸/非離陸 の 5×2 表の Fisher 正確検定
  5. 鍵のエントロピーと離陸数の Spearman 相関（鍵5本なので検出力は低い）
"""
import glob
import itertools
import json
import os
import sys

import numpy as np
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL = {"func_pow": "h (統制)", "func_22": "f22", "func_13_k26": "f13", "func_31": "f31",
         "func_pow_k50": "h (統制)", "func_22_k50": "f22", "func_13_k50": "f13",
         "func_31_k50": "f31"}
K26 = ["func_pow", "func_22", "func_13_k26", "func_31"]
K50 = ["func_pow_k50", "func_22_k50", "func_13_k50", "func_31_k50"]
THRESHOLD = 0.5


def load(experiment="C1"):
    rows = []
    for f in glob.glob(os.path.join(REPO, f"results/path_c/{experiment}/runs_*.jsonl")):
        for line in open(f):
            rows.append(json.loads(line))
    return rows


def wilson(k: int, n: int, z: float = 1.959963985) -> tuple[float, float]:
    """二項比率の Wilson スコア信頼区間．

    正規近似（Wald）は k=0 や k=n で幅0になり，n=20 では被覆率も悪い．
    Wilson は端点でも区間を返す．
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def takeoff_map(rows, algo, datasize):
    """(鍵seed, 初期値seed) -> 離陸したか"""
    return {(r["key_seed"], r["init_seed"]): r["val_accuracy_max"] > THRESHOLD
            for r in rows if r["algorithm"] == algo and r["datasize"] == datasize}


def mcnemar_exact(a: dict, b: dict) -> tuple[int, int, float]:
    """対応のある2条件の離陸率の差（McNemar の正確検定，両側）．"""
    keys = sorted(set(a) & set(b))
    b01 = sum(1 for k in keys if not a[k] and b[k])
    b10 = sum(1 for k in keys if a[k] and not b[k])
    n = b01 + b10
    if n == 0:
        return b10, b01, 1.0
    p = min(1.0, 2 * stats.binom.cdf(min(b01, b10), n, 0.5))
    return b10, b01, p


def main():
    rows = load()
    print("=" * 78)
    print("1. 離陸率と Wilson 95% 信頼区間（50,000件）")
    print("=" * 78)
    print(f"{'関数':12s}{'N':>4s}{'離陸':>8s}{'率':>8s}{'95% CI':>18s}{'平均正解率':>14s}")
    for algos, N in ((K26, 26), (K50, 50)):
        for a in algos:
            rs = [r for r in rows if r["algorithm"] == a and r["datasize"] == 50000]
            v = np.array([r["val_accuracy_max"] for r in rs])
            k = int((v > THRESHOLD).sum())
            lo, hi = wilson(k, len(v))
            print(f"{LABEL[a]:12s}{N:>4d}{k:>5d}/{len(v):<3d}{k/len(v):>8.2f}"
                  f"   [{lo:.2f}, {hi:.2f}]   {v.mean():>7.4f}±{v.std(ddof=1):.4f}")
    print()
    print("=" * 78)
    print("2. 関数間の比較（McNemar の正確検定・両側）— 同じ (鍵, 初期値) を共有する対応データ")
    print("=" * 78)
    for algos, N in ((K26, 26), (K50, 50)):
        print(f"  N={N}")
        for x, y in itertools.combinations(algos, 2):
            a, b = takeoff_map(rows, x, 50000), takeoff_map(rows, y, 50000)
            n10, n01, p = mcnemar_exact(a, b)
            star = "**" if p < 0.01 else "*" if p < 0.05 else "  "
            print(f"    {LABEL[x]:10s}対 {LABEL[y]:10s} "
                  f"{LABEL[x]}のみ離陸 {n10:2d} / {LABEL[y]}のみ離陸 {n01:2d}  p={p:.4f} {star}")
    print()
    print("=" * 78)
    print("3. 鍵サイズ 26 対 50（Fisher の正確検定・両側）— 鍵の長さが違うので対応なし")
    print("=" * 78)
    for a26, a50 in zip(K26, K50):
        k26 = sum(takeoff_map(rows, a26, 50000).values()); n26 = len(takeoff_map(rows, a26, 50000))
        k50 = sum(takeoff_map(rows, a50, 50000).values()); n50 = len(takeoff_map(rows, a50, 50000))
        odds, p = stats.fisher_exact([[k26, n26 - k26], [k50, n50 - k50]])
        star = "**" if p < 0.01 else "*" if p < 0.05 else "  "
        print(f"  {LABEL[a26]:12s} {k26:2d}/{n26} → {k50:2d}/{n50}   p={p:.4f} {star}")
    print()
    print("=" * 78)
    print("4. 離陸は鍵で決まるか（鍵5本 × 離陸/非離陸 の Fisher 正確検定）")
    print("=" * 78)
    for algos, N in ((K26, 26), (K50, 50)):
        for a in algos:
            m = takeoff_map(rows, a, 50000)
            keys = sorted({k for k, _ in m})
            tbl = [[sum(1 for (kk, ii), v in m.items() if kk == k and v),
                    sum(1 for (kk, ii), v in m.items() if kk == k and not v)] for k in keys]
            if sum(r[0] for r in tbl) in (0, sum(sum(r) for r in tbl)):
                print(f"  {LABEL[a]:12s} N={N}  全一致（検定不能）")
                continue
            p = stats.fisher_exact(tbl)[1] if len(tbl) == 2 else _fisher_rxc(tbl)
            star = "**" if p < 0.01 else "*" if p < 0.05 else "  "
            print(f"  {LABEL[a]:12s} N={N}  鍵ごとの離陸 "
                  f"{[r[0] for r in tbl]}  p={p:.4f} {star}")
    print()
    print("=" * 78)
    print("5. 鍵のエントロピーと離陸数（Spearman，鍵5本なので検出力は低い）")
    print("=" * 78)
    for algos, N in ((K26, 26), (K50, 50)):
        for a in algos:
            rs = [r for r in rows if r["algorithm"] == a and r["datasize"] == 50000]
            ent, off = [], []
            for ks in sorted({r["key_seed"] for r in rs}):
                sub = [r for r in rs if r["key_seed"] == ks]
                c = np.bincount(sub[0]["key"], minlength=10)
                pr = c[c > 0] / len(sub[0]["key"])
                ent.append(float(-(pr * np.log2(pr)).sum()))
                off.append(sum(1 for r in sub if r["val_accuracy_max"] > THRESHOLD))
            if len(set(off)) == 1:
                print(f"  {LABEL[a]:12s} N={N}  離陸数が全鍵で同一（相関を定義できない）")
                continue
            rho, p = stats.spearmanr(ent, off)
            print(f"  {LABEL[a]:12s} N={N}  エントロピー {np.round(ent,3).tolist()} "
                  f"離陸 {off}  rho={rho:+.2f} p={p:.3f}")


def _fisher_rxc(table, n_perm=20000, seed=0):
    """r×2 表の並べ替え検定（scipy に r×c の正確検定が無いため Monte Carlo）．

    統計量は Pearson のカイ二乗．行の大きさを保ったまま列ラベルを並べ替え，
    観測値以上になる割合を p 値とする（ベクトル化して 20,000 回）．
    """
    table = np.asarray(table, dtype=float)
    rows_n = table.sum(1)
    k = int(table[:, 0].sum())
    n = int(table.sum())

    def chi2(counts):
        exp = rows_n[None, :] * (k / n)
        other = rows_n[None, :] * (1 - k / n)
        return ((((counts - exp) ** 2) / exp)
                + ((((rows_n[None, :] - counts) - other) ** 2) / other)).sum(1)

    obs = chi2(table[:, 0][None, :])[0]
    rng = np.random.default_rng(seed)
    labels = np.zeros(n, dtype=np.int8)
    labels[:k] = 1
    perm = np.tile(labels, (n_perm, 1))
    perm = np.take_along_axis(perm, rng.random(perm.shape).argsort(1), 1)
    counts = np.stack([seg.sum(1) for seg in
                       np.split(perm, np.cumsum(rows_n).astype(int)[:-1], axis=1)],
                      axis=1).astype(float)
    return float((chi2(counts) >= obs - 1e-12).mean())


if __name__ == "__main__":
    main()
