#!/usr/bin/env python3
# =============================================================================
# inventory.py — 「どのパラメータで実験したことがあるか」の棚卸し
# =============================================================================
# ファインチューニングの学習 run（results/llm_finetune/）と，その評価結果
# （results/llm_eval/）を突き合わせ，1本の run を1行にした一覧を作る．
#
# summarize.py との違い:
#   summarize.py … 評価結果だけを見る。学習条件（n_train・epochs・lr）や
#                   学習曲線は見えない。
#   inventory.py … 学習条件と評価結果を1行に並べ，さらに検証損失から
#                   「離陸したエポック」を出す。まだ評価していない学習 run も載る。
#
# 出力:
#   results/inventory.md   人間が読む一覧＋未実施の組み合わせ
#   results/inventory.csv  一次データ
#
#   python3 experiments/inventory.py                    # 全部
#   python3 experiments/inventory.py --algorithm func_22_k10
# =============================================================================

import argparse
import csv
import glob
import json
import os
from collections import defaultdict
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FT_DIR = os.path.join(REPO_ROOT, "results", "llm_finetune")
EVAL_DIR = os.path.join(REPO_ROOT, "results", "llm_eval")

# 検証損失がこの値を下回ったエポックを「離陸した」とみなす。
# 未学習の run は 0.19 前後で張り付き，離陸した run は 0.02 以下まで落ちるため，
# その中間に取った（2026-09-12 の監査，docs/training_dynamics.md 参照）。
TAKEOFF_THRESHOLD = 0.15


def read_history(run_dir: str) -> tuple[float | None, int | None, float | None]:
    """(最終val損失, 離陸エポック, 最小val損失) を返す．"""
    path = os.path.join(run_dir, "history.csv")
    if not os.path.exists(path):
        return None, None, None
    epochs: list[tuple[float, float]] = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row.get("eval_loss")
            e = row.get("epoch")
            if v and e:
                try:
                    epochs.append((float(e), float(v)))
                except ValueError:
                    continue
    if not epochs:
        return None, None, None
    epochs.sort()
    takeoff = next((int(round(e)) for e, v in epochs if v < TAKEOFF_THRESHOLD), None)
    return epochs[-1][1], takeoff, min(v for _e, v in epochs)


def run_key(path: str) -> str:
    """学習 run を指す短い鍵（{model}/{algorithm}/{run_xxx}）．

    絶対パスで突き合わせないのは，2026-07 のリファクタリングで学習結果の置き場が
    results/finetuned_models/ から results/llm_finetune/ へ変わっており，
    それ以前の評価結果には旧パスが記録されているため（14件）．末尾3階層で
    照合すれば，この改名をまたいでも対応が取れる．
    """
    return "/".join(os.path.normpath(path).rstrip("/").split("/")[-3:])


def collect_evals() -> dict[str, list[dict]]:
    """学習 run の鍵 → その run に対する評価結果の一覧．"""
    out: dict[str, list[dict]] = defaultdict(list)
    for path in glob.glob(os.path.join(EVAL_DIR, "**", "metrics.json"), recursive=True):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        cfg = data.get("config", {})
        if cfg.get("provider") != "lora":
            continue
        out[run_key(cfg.get("model", ""))].append({
            "n_test": data.get("n_test", cfg.get("n_test")),
            "accuracy": data.get("accuracy"),
            "key_seed": cfg.get("key_seed"),
            "data_seed": cfg.get("data_seed"),
            "finished_at": data.get("finished_at", ""),
        })
    return out


def collect_rows(algorithm_filter: str | None) -> list[dict]:
    evals = collect_evals()
    rows: list[dict] = []
    for meta_path in glob.glob(os.path.join(FT_DIR, "*", "*", "run_*", "train_metadata.json")):
        run_dir = os.path.dirname(meta_path)
        with open(meta_path, encoding="utf-8") as f:
            args = json.load(f).get("args", {})
        # リファクタリング前のメタデータは algorithm を generator，key_seed/data_seed を
        # seed という名前で持っている。アルゴリズム名はディレクトリ名が最も確実なので
        # それを最終的な拠り所にする。
        algo = args.get("algorithm") or args.get("generator") or os.path.basename(
            os.path.dirname(run_dir))
        legacy_seed = args.get("seed")
        key_seed = args.get("key_seed", legacy_seed)
        data_seed = args.get("data_seed", legacy_seed)
        if algorithm_filter and algo != algorithm_filter:
            continue
        final_vl, takeoff, min_vl = read_history(run_dir)
        matched = evals.get(run_key(run_dir), [])
        # 同じ run を複数の n_test で評価している場合は，件数の多い方を代表にする
        best = max(matched, key=lambda r: r["n_test"] or 0) if matched else {}
        rows.append({
            "algorithm": algo,
            "key_seed": key_seed,
            "data_seed": data_seed,
            "n_train": args.get("n_train"),
            "epochs": args.get("epochs"),
            "lr": args.get("lr"),
            "stage": args.get("stage"),
            "paradigm": args.get("paradigm"),
            "n_test": best.get("n_test"),
            "accuracy": best.get("accuracy"),
            "n_evals": len(matched),
            "final_val_loss": final_vl,
            "min_val_loss": min_vl,
            "takeoff_epoch": takeoff,
            "legacy_meta": args.get("algorithm") is None,
            "run": os.path.basename(run_dir),
            "path": os.path.relpath(run_dir, REPO_ROOT),
        })
    rows.sort(key=lambda r: (r["algorithm"], r["key_seed"] or 0, r["data_seed"] or 0,
                             r["n_train"] or 0, r["epochs"] or 0))
    return rows


def pct(v) -> str:
    return "未評価" if v is None else f"{v:.1%}"


def num(v, spec="{:.4f}") -> str:
    return "-" if v is None else spec.format(v)


def build_md(rows: list[dict]) -> list[str]:
    md = [
        "# 実験の棚卸し（どのパラメータで走らせたか）",
        "",
        f"`experiments/inventory.py` により自動生成（{datetime.now():%Y-%m-%d %H:%M:%S}）．",
        f"一次データ: `results/inventory.csv`（学習 run {len(rows)} 本）",
        "",
        "「離陸」は検証損失が "
        f"{TAKEOFF_THRESHOLD} を下回った最初のエポック．`-` は最後まで下回らなかったことを表す．",
        "詳しくは [docs/training_dynamics.md](../docs/training_dynamics.md)．",
        "",
    ]
    by_algo: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_algo[r["algorithm"]].append(r)

    md += ["## 実施済みの学習 run", ""]
    for algo in sorted(by_algo):
        md += [f"### {algo}", "",
               "| 鍵 | データ | 学習件数 | エポック | lr | 評価件数 | 正解率 | 最終val損失 | 離陸ep | run |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for r in by_algo[algo]:
            md.append(
                f"| {r['key_seed']} | {r['data_seed']} | {r['n_train']} | {r['epochs']} "
                f"| {num(r['lr'], '{:.0e}')} | {r['n_test'] or '-'} | {pct(r['accuracy'])} "
                f"| {num(r['final_val_loss'])} | {r['takeoff_epoch'] or '-'} | `{r['run']}` |"
            )
        md.append("")

    # ---- 走らせていない組み合わせ ----
    md += ["## まだ走らせていない組み合わせ", "",
           "各アルゴリズムについて，**そのアルゴリズムで一度でも使った値**の直積のうち，",
           "実施記録が無いものを挙げる（全条件を埋めるべきという意味ではなく，",
           "「これは試したか？」を思い出すための一覧である）．", ""]
    for algo in sorted(by_algo):
        items = by_algo[algo]
        keys = sorted({r["key_seed"] for r in items if r["key_seed"] is not None})
        trains = sorted({r["n_train"] for r in items if r["n_train"] is not None})
        eps = sorted({r["epochs"] for r in items if r["epochs"] is not None})
        done = {(r["key_seed"], r["data_seed"], r["n_train"], r["epochs"]) for r in items}
        seeds = sorted({r["data_seed"] for r in items if r["data_seed"] is not None})
        missing = [(k, d, t, e) for k in keys for d in seeds for t in trains for e in eps
                   if (k, d, t, e) not in done]
        md.append(f"### {algo}")
        md.append("")
        md.append(f"使った値: 鍵={keys} / データ={seeds} / 学習件数={trains} / エポック={eps}")
        md.append("")
        if not missing:
            md.append("直積はすべて実施済み。")
        else:
            md.append(f"未実施 {len(missing)} 通り:")
            md.append("")
            md.append("| 鍵 | データ | 学習件数 | エポック |")
            md.append("|---|---|---|---|")
            for k, d, t, e in missing[:20]:
                md.append(f"| {k} | {d} | {t} | {e} |")
            if len(missing) > 20:
                md.append(f"| … | | | 他 {len(missing) - 20} 通り |")
        md.append("")
    return md


def main() -> None:
    ap = argparse.ArgumentParser(description="実験の棚卸しを作る")
    ap.add_argument("--algorithm", default=None, help="このアルゴリズムだけに絞る")
    args = ap.parse_args()

    rows = collect_rows(args.algorithm)
    if not rows:
        print("学習 run が見つかりませんでした。")
        return

    csv_path = os.path.join(REPO_ROOT, "results", "inventory.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md = build_md(rows)
    md_path = os.path.join(REPO_ROOT, "results", "inventory.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    未評価 = sum(1 for r in rows if r["accuracy"] is None)
    print(f"保存完了: {csv_path}")
    print(f"          {md_path}")
    print(f"学習 run {len(rows)} 本（うち未評価 {未評価} 本） / "
          f"アルゴリズム {len({r['algorithm'] for r in rows})} 種類")


if __name__ == "__main__":
    main()
