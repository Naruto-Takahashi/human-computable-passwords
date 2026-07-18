#!/usr/bin/env python3
# =============================================================================
# summarize.py — 評価結果の自動集計（旧 summarize_prompting.py の後継）
# =============================================================================
# results/evals/ 以下の metrics.json（新形式）と metadata.json（旧形式）を再帰的に
# 収集し，以下を生成する:
#   - results/summary_llm.csv : 全実験のフラットな一覧（プロット用の一次データ）
#   - results/summary_llm.md  : 人間可読の Markdown 表（シード平均済み）
# =============================================================================

import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS_DIR = os.path.join(REPO_ROOT, "results", "llm_eval")


def load_new_format(path: str) -> dict | None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = data.get("config", {})
    row = {
        "model": cfg.get("model", "unknown"),
        "provider": cfg.get("provider", "unknown"),
        "algorithm": cfg.get("algorithm", "unknown"),
        "task": data.get("task", cfg.get("task", "predict")),
        "paradigm": cfg.get("paradigm", ""),
        "stage": cfg.get("stage", ""),
        "k_disclosed": cfg.get("k_disclosed", 0),
        "n_shot": cfg.get("n_shot", ""),
        "n_test": data.get("n_test", cfg.get("n_test", "")),
        "key_seed": cfg.get("key_seed", ""),
        "data_seed": cfg.get("data_seed", ""),
        "accuracy": data.get("accuracy"),
        "parse_error": data.get("parse_error_count", data.get("parse_error")),
        "key_cell_accuracy": data.get("key_cell_accuracy"),
        "undisclosed_cell_accuracy": data.get("undisclosed_cell_accuracy"),
        "key_exact_match": data.get("key_exact_match"),
        "heldout_accuracy": data.get("heldout_accuracy"),
        "git_commit": data.get("git_commit", ""),
        "finished_at": data.get("finished_at", ""),
        "path": os.path.relpath(os.path.dirname(path), REPO_ROOT),
        "format": "v2",
    }
    return row


def load_legacy_format(path: str) -> dict | None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "accuracy" not in data:
        return None  # ベースライン等の別形式はスキップ
    model = str(data.get("model_name", "unknown"))
    if "/" in model:  # LoRA run ディレクトリのパスは末尾3階層に短縮
        model = "/".join(model.rstrip("/").split("/")[-3:])
    return {
        "model": model,
        "provider": data.get("provider", "unknown"),
        "algorithm": data.get("generator_name", "unknown"),
        "task": "predict",
        "paradigm": data.get("paradigm", "pure"),
        "stage": data.get("stage", ""),
        "k_disclosed": data.get("k_disclosed", 0),
        "n_shot": data.get("n_shot", ""),
        "n_test": data.get("n_test", ""),
        "key_seed": data.get("seed", ""),
        "data_seed": data.get("seed", ""),
        "accuracy": data.get("accuracy"),
        "parse_error": data.get("parse_error_count"),
        "key_cell_accuracy": None,
        "undisclosed_cell_accuracy": None,
        "key_exact_match": None,
        "heldout_accuracy": None,
        "git_commit": "",
        "finished_at": "",
        "path": os.path.relpath(os.path.dirname(path), REPO_ROOT),
        "format": "legacy",
    }


def fmt(v) -> str:
    if v is None or v == "":
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.2%}"
    return str(v)


def main():
    rows: list[dict] = []
    for path in glob.glob(os.path.join(EVALS_DIR, "**", "metrics.json"), recursive=True):
        try:
            row = load_new_format(path)
            if row:
                rows.append(row)
        except Exception as e:
            print(f"読み込み失敗 {path}: {e}", file=sys.stderr)
    for path in glob.glob(os.path.join(EVALS_DIR, "**", "metadata.json"), recursive=True):
        try:
            row = load_legacy_format(path)
            if row:
                rows.append(row)
        except Exception as e:
            print(f"読み込み失敗 {path}: {e}", file=sys.stderr)

    if not rows:
        print("集計対象の結果ファイルが見つかりませんでした。")
        return

    # ---- CSV（プロット用一次データ）----
    import csv as csv_mod

    csv_path = os.path.join(REPO_ROOT, "results", "summary_llm.csv")
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv_mod.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ---- Markdown（シードをまとめて平均）----
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = (r["model"], r["algorithm"], r["task"], r["paradigm"],
               r["stage"], r["k_disclosed"], r["n_shot"], r["format"])
        groups[key].append(r)

    def mean_of(items, field):
        vals = [x[field] for x in items if isinstance(x[field], (int, float))
                and not isinstance(x[field], bool)]
        return sum(vals) / len(vals) if vals else None

    md = [
        "# LLM ベンチマーク実験結果 サマリー",
        "",
        f"`experiments/summarize.py` により自動生成（{datetime.now():%Y-%m-%d %H:%M:%S}）．",
        f"一次データ: `results/summary_llm.csv`（{len(rows)} 実験）",
        "",
        "| モデル | アルゴリズム | タスク | Stage | K | N | 反復数 | 応答精度 | 鍵セル一致率 | 鍵完全一致率 | held-out精度 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(groups.keys(), key=lambda k: tuple(str(x) for x in k)):
        items = groups[key]
        model, algo, task, paradigm, stage, k, n_shot, fmt_ver = key
        task_str = f"{task}({paradigm})" if paradigm else task
        if fmt_ver == "legacy":
            task_str += " [旧]"
        exact_vals = [x["key_exact_match"] for x in items if x["key_exact_match"] is not None]
        exact_rate = sum(exact_vals) / len(exact_vals) if exact_vals else None
        md.append(
            f"| {model} | {algo} | {task_str} | {stage} | {k} | {n_shot} | {len(items)} "
            f"| {fmt(mean_of(items, 'accuracy'))} "
            f"| {fmt(mean_of(items, 'key_cell_accuracy'))} "
            f"| {fmt(exact_rate)} "
            f"| {fmt(mean_of(items, 'heldout_accuracy'))} |"
        )

    md_path = os.path.join(REPO_ROOT, "results", "summary_llm.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"保存完了: {csv_path}")
    print(f"          {md_path}")
    print("\n".join(md[5:]))


if __name__ == "__main__":
    main()
