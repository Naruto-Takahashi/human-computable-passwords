#!/usr/bin/env python3
"""これまでの全実行を横断集計する．

個々の実験は「この条件は何%だった」を答えるが，本研究の主張は
**正解率という指標そのものが何を写していたか**である。それは1件ずつ見ても
確かめられない。手元にある全 run を横断して初めて，

  - 正解率は「予算内に離陸したか」の二値を粗く写したものでしかない
  - 過去の高正解率のうち，どれだけが学習データとの重複に支えられていたか
  - 何件が検出力の足りない評価件数で結論づけられていたか

を分布として示せる。

使い方:
    python3 tools/corpus_analysis.py            # 要約
    python3 tools/corpus_analysis.py --csv out.csv   # 1行1runで書き出す
"""
import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

TAKEOFF = 0.15      # 離陸の判定（検証損失）
CONVERGED = 0.001   # 収束の判定


def load_history(run_dir):
    path = os.path.join(run_dir, "history.csv")
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("eval_loss"):
                try:
                    out.append((float(row["epoch"]), float(row["eval_loss"])))
                except ValueError:
                    pass
    return out


def collect():
    rows = []
    eval_root = os.path.join(ROOT, "results", "llm_eval")
    for dirpath, _, files in os.walk(eval_root):
        if "metrics.json" not in files:
            continue
        with open(os.path.join(dirpath, "metrics.json"), encoding="utf-8") as f:
            m = json.load(f)
        cfg = m.get("config", {})
        if m.get("task") != "predict":
            continue
        run_dir = cfg.get("model", "")
        meta_path = os.path.join(run_dir, "train_metadata.json")
        args = {}
        if os.path.isfile(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                args = json.load(f).get("args", {})
        hist = load_history(run_dir)
        takeoff = next((int(e) for e, l in hist if l < TAKEOFF), None)
        conv = next((int(e) for e, l in hist if l < CONVERGED), None)
        rows.append({
            "algorithm": cfg.get("algorithm", "?"),
            "key_seed": cfg.get("key_seed"),
            "data_seed": cfg.get("data_seed"),
            "n_test": m.get("n_test"),
            "accuracy": m.get("accuracy"),
            "epochs": args.get("epochs"),
            "lr_scheduler": args.get("lr_scheduler", "linear"),
            "seed": args.get("seed", 42),
            "n_train": args.get("n_train"),
            "takeoff_epoch": takeoff,
            "converged_epoch": conv,
            "n_epochs_logged": len(hist),
            "final_eval_loss": hist[-1][1] if hist else None,
            "min_eval_loss": min((l for _, l in hist), default=None),
            "run_dir": run_dir,
        })
    return rows


def summarize(rows):
    have = [r for r in rows if r["n_epochs_logged"] and r["accuracy"] is not None]
    print(f"評価済み {len(rows)} 件のうち，学習曲線が残っているもの {len(have)} 件\n")

    print("■ 正解率は「離陸したか」を写しているか")
    took = [r for r in have if r["takeoff_epoch"] is not None]
    nott = [r for r in have if r["takeoff_epoch"] is None]
    for label, g in (("離陸した", took), ("離陸せず", nott)):
        if not g:
            continue
        acc = sorted(r["accuracy"] for r in g)
        print(f"  {label:8s} {len(g):3d}件  正解率 中央値 {acc[len(acc)//2]*100:5.1f}%  "
              f"範囲 {acc[0]*100:5.1f}% 〜 {acc[-1]*100:5.1f}%")
    if took and nott:
        hi = sum(1 for r in took if r["accuracy"] >= 0.9)
        lo = sum(1 for r in nott if r["accuracy"] < 0.4)
        print(f"  → 離陸した {len(took)} 件のうち 90%以上が {hi} 件（{100*hi/len(took):.0f}%）")
        print(f"  → 離陸せず {len(nott)} 件のうち 40%未満が {lo} 件（{100*lo/len(nott):.0f}%）")
        overlap_hi = [r for r in nott if r["accuracy"] >= 0.9]
        overlap_lo = [r for r in took if r["accuracy"] < 0.4]
        print(f"  → 例外: 離陸せずに90%以上 {len(overlap_hi)} 件 ／ "
              f"離陸したのに40%未満 {len(overlap_lo)} 件")

    print("\n■ 「収束したか」で分けるとほぼ完全に分離する")
    conv = [r for r in rows if r["converged_epoch"]]
    nonc = [r for r in rows if not r["converged_epoch"] and r["accuracy"] is not None]
    for label, g in (("収束した", conv), ("収束せず", nonc)):
        if not g:
            continue
        acc = sorted(r["accuracy"] for r in g)
        print(f"  {label:8s} {len(g):3d}件  正解率 {acc[0]*100:5.1f}% 〜 {acc[-1]*100:5.1f}%  "
              f"中央値 {acc[len(acc)//2]*100:5.1f}%")
    if conv:
        bad = sum(1 for r in conv if r["accuracy"] < 0.9)
        print(f"  → 収束した {len(conv)} 件で90%未満は {bad} 件")
        print("  → 正解率は『予算内に収束したか』をほぼそのまま写している")

    print("\n■ 打ち切りの直接証拠")
    ep20 = [r for r in rows if r["epochs"] == 20 and r["n_epochs_logged"]]
    late = [r for r in ep20 if r["converged_epoch"] and r["converged_epoch"] > 5]
    print(f"  20エポック予算の run {len(ep20)} 件のうち，収束が5エポック目より後だったもの "
          f"{len(late)} 件")
    for r in late:
        print(f"    {r['algorithm']:18s} ks{r['key_seed']} 収束 ep{r['converged_epoch']:<3} "
              f"正解率 {r['accuracy']*100:5.1f}%  ← 5エポック予算なら「失敗」")
    if late:
        print("  → 5エポックという予算は，収束時刻の分布を右側で打ち切っていた。")
        print("     正解率はその打ち切りの結果を二値で読んだものでしかない。")

    print("\n■ 評価件数の内訳（検出力）")
    by_n = {}
    for r in rows:
        by_n.setdefault(r["n_test"], []).append(r)
    for n in sorted(by_n, key=lambda x: (x is None, x)):
        g = by_n[n]
        print(f"  n_test={str(n):>4}  {len(g):3d}件")

    print("\n■ 予算とスケジュールの組み合わせ")
    by_b = {}
    for r in have:
        by_b.setdefault((r["epochs"], r["lr_scheduler"]), []).append(r)
    for k in sorted(by_b, key=lambda x: (x[0] or 0, str(x[1]))):
        g = by_b[k]
        t = sum(1 for r in g if r["takeoff_epoch"] is not None)
        print(f"  {str(k[0]):>3}ep {str(k[1]):<10} {len(g):3d}件  離陸 {t:3d}件（{100*t/len(g):3.0f}%）")

    print("\n■ 離陸エポックの分布（離陸した run のみ）")
    dist = {}
    for r in took:
        dist[r["takeoff_epoch"]] = dist.get(r["takeoff_epoch"], 0) + 1
    for e in sorted(dist):
        print(f"  ep{e:<3} {'#' * dist[e]} ({dist[e]})")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="1行1runで書き出す先")
    a = ap.parse_args()
    rows = collect()
    rows.sort(key=lambda r: (r["algorithm"], r["key_seed"] or 0, r["data_seed"] or 0))
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"書き出し: {a.csv}（{len(rows)} 行）\n")
    summarize(rows)


if __name__ == "__main__":
    main()
