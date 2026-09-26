#!/usr/bin/env python3
"""results/ を実験ごとに索引する（`make index`）．

生成するもの:
  - `results/INDEX.md`        … 実験ごとの run 一覧（結果の確認用）
  - `results/by_experiment/`  … 実験ごとのシンボリックリンク（辿る用．実体は1つ）

**実体は動かさない。**理由は tools/experiment_map.py の冒頭に書いた。
"""
import json
import os
import re
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment_map import all_labels, TITLES, SOLVER_EXPERIMENTS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def _train_args(model_path: str) -> dict:
    meta = os.path.join(model_path, "train_metadata.json")
    if not os.path.isfile(meta):
        return {}
    try:
        with open(meta, encoding="utf-8") as f:
            return json.load(f).get("args", {}) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def collect_evals() -> list[dict]:
    rows = []
    for dirpath, _dirs, files in os.walk(os.path.join(RESULTS, "llm_eval")):
        if "metrics.json" not in files:
            continue
        path = os.path.join(dirpath, "metrics.json")
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
        cfg = m.get("config", {}) or {}
        model = cfg.get("model", "") or ""
        args = _train_args(model)
        ts = re.search(r"run_(\d{8})_(\d{6})", model)
        # 成績は predict と recover_key で指標が違う
        if m.get("task") == "recover_key":
            score = ("完全一致" if m.get("key_exact_match") else
                     "等価" if m.get("key_functionally_equivalent") else
                     "打切" if m.get("truncated") else
                     "解析不可" if m.get("parse_error") else "不正解")
        else:
            acc = m.get("accuracy")
            score = f"{acc * 100:.1f}%" if acc is not None else "—"
        rows.append({
            "kind": "eval",
            "experiment": m.get("experiment") or cfg.get("experiment"),
            "date": ts.group(1) if ts else m.get("finished_at", "")[:10].replace("-", ""),
            "algorithm": cfg.get("algorithm", "?"),
            "task": m.get("task", "?"),
            "prompt_level": m.get("prompt_level"),
            "model": os.path.basename(model) if model else cfg.get("model", "?"),
            "key_seed": cfg.get("key_seed"), "data_seed": cfg.get("data_seed"),
            "n_shot": cfg.get("n_shot"), "stage": cfg.get("stage"),
            "epochs": args.get("epochs"), "n_train": args.get("n_train"),
            "score": score,
            "path": os.path.relpath(dirpath, ROOT),
        })
    return rows


def collect_solver() -> list[dict]:
    rows = []
    d = os.path.join(RESULTS, "solver")
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not name.endswith("_info_limit.csv"):
            continue
        alg = name.replace("_info_limit.csv", "")
        rows.append({
            "kind": "solver", "experiment": SOLVER_EXPERIMENTS.get(alg),
            "date": "", "algorithm": alg, "task": "info_limit",
            "prompt_level": None, "model": "solver",
            "key_seed": None, "data_seed": None, "n_shot": None, "stage": None,
            "epochs": None, "n_train": None, "score": "—",
            "path": os.path.relpath(os.path.join(d, name), ROOT),
        })
    return rows


def main() -> None:
    rows = collect_evals() + collect_solver()
    for r in rows:
        r["labels"] = all_labels(r)
        r["experiment"] = r["labels"][0]

    by = collections.defaultdict(list)
    for r in rows:
        for lbl in r["labels"]:
            by[lbl].append(r)

    md = [
        "# 結果の索引（自動生成 — `make index`）",
        "",
        "> 実験ごとの run 一覧。**このファイルを手で編集しない。**",
        ">",
        "> 📚 [ドキュメント索引](../docs/README.md) ／ "
        "実験の設計と考察は [experiment_index.md](../docs/experiment_index.md)",
        "",
        "保存場所は条件アドレス（`results/llm_eval/<関数>/<タスク>/<条件>/…`）のままで，",
        "実験はラベルとして与えている。実験ごとに実体を分けない理由は",
        "[tools/experiment_map.py](../tools/experiment_map.py) の冒頭にある。",
        "`results/by_experiment/<ラベル>/` にシンボリックリンクを張ってあるので，",
        "ディレクトリとしても辿れる（実体は1つ）。",
        "",
        "接頭辞 `B` は経路B（重み格納型学習），`A` は経路A（in-context 推論）。",
        "",
        "> [!NOTE]",
        "> **ここで数えているのは run であって条件ではない。**同じ条件を複数回",
        "> 評価した run があるため，[experiment_index.md](../docs/experiment_index.md) の",
        "> 条件数と一致しないことがある（例: 実験12 は8条件だが，`func_22_k10` 鍵0 を",
        "> 2run 使って錨にしているので9run になる）。",
        "> `※共有` が付いた run は複数の実験に数えられている。",
        "",
        "| 実験 | 題 | run 数 | 関数 |",
        "|---|---|---:|---|",
    ]
    for label in sorted(by, key=lambda x: (x == "?", x)):
        algs = sorted({r["algorithm"] for r in by[label]})
        shown = "，".join(f"`{a}`" for a in algs[:4]) + ("ほか" if len(algs) > 4 else "")
        md.append(f"| **{label}** | {TITLES.get(label, '—')} | {len(by[label])} | {shown} |")
    md.append("")

    for label in sorted(by, key=lambda x: (x == "?", x)):
        md += [f"## {label} — {TITLES.get(label, '—')}", "",
               "| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |",
               "|---|---|---:|---:|---:|---:|---:|:-:|---|---|"]
        for r in sorted(by[label], key=lambda r: (r["algorithm"], str(r["key_seed"]),
                                                  str(r["data_seed"]))):
            def g(v):
                return "—" if v is None else str(v)
            md.append(
                f"| `{r['algorithm']}` | {r['task']} | {g(r['key_seed'])} | "
                f"{g(r['data_seed'])} | {g(r['n_shot'])} | {g(r['stage'])} | "
                f"{g(r['epochs'])} | {g(r['prompt_level'])} | {r['score']} | "
                f"`{r['path']}`{' ※共有' if len(r['labels']) > 1 else ''} |")
        md.append("")

    md += ["## 次に読む", "",
           "| | |", "|---|---|",
           "| [実験の一覧](../docs/experiment_index.md) | 設計と考察を読みたいとき |",
           "| [研究計画](../docs/plan.md) | 位置づけを確かめたいとき |", ""]

    out = os.path.join(RESULTS, "INDEX.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # --- シンボリックリンクの張り直し ---
    link_root = os.path.join(RESULTS, "by_experiment")
    if os.path.isdir(link_root):
        for lbl in os.listdir(link_root):
            d = os.path.join(link_root, lbl)
            for n in os.listdir(d):
                os.unlink(os.path.join(d, n))
            os.rmdir(d)
    for label, items in by.items():
        d = os.path.join(link_root, label)
        os.makedirs(d, exist_ok=True)
        for r in items:
            target = os.path.join(ROOT, r["path"])
            parts = [r["algorithm"], str(r.get("key_seed")), str(r.get("data_seed")),
                     r.get("prompt_level") or ""]
            name = "_".join(p for p in parts if p and p != "None")
            link = os.path.join(d, name)
            i = 2
            while os.path.lexists(link):
                link = os.path.join(d, f"{name}#{i}")
                i += 1
            os.symlink(os.path.relpath(target, d), link)

    print(f"保存完了: {os.path.relpath(out, ROOT)}（{len(rows)} run / {len(by)} 実験）")
    unassigned = len(by.get("?", []))
    if unassigned:
        print(f"  ⚠ 未割り当て {unassigned} 件 — tools/experiment_map.py に規則を足してください")
    print(f"          {os.path.relpath(link_root, ROOT)}/ にリンクを張りました")


if __name__ == "__main__":
    main()
