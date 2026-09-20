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
#   results/inventory.md   人間が読む一覧（いま動いている実験だけ詳細）
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
import re
from collections import defaultdict
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FT_DIR = os.path.join(REPO_ROOT, "results", "llm_finetune")
EVAL_DIR = os.path.join(REPO_ROOT, "results", "llm_eval")

# 検証損失がこの値を下回ったエポックを「離陸した」とみなす。
# 未学習の run は 0.19 前後で張り付き，離陸した run は 0.02 以下まで落ちるため，
# その中間に取った（2026-09-12 の監査，docs/measurement_audit.md 参照）。
TAKEOFF_THRESHOLD = 0.15

# 過去の run がどの実験に属するかの対応表（run ディレクトリ名の時刻で引く）。
#
# 段階の定義そのものは docs/experiment_index.md が正本である。ここはツールが日付から
# 段階名を引くための対応表にすぎないので，段階を追加・改称するときは
# まず docs/experiment_index.md を直し，それに合わせてここを更新すること。
#
# 2026-09-12 より前の run には実験名が記録されていないため，ここで後づけする。
# 以降の run は train_finetuning.py の --tag で記録されるので，そちらが優先される。
# 区間は [開始, 終了) で，実験を追加したらここに1行足す。
#
# 「決着済み」に分類された実験は既定では1行に畳んで表示する。研究の焦点が
# 移ったあとも全 run を並べ続けると，いま動いている実験が埋もれてしまうため。
STAGES: list[tuple[str, str, str, bool]] = [
    # (開始, 終了, 実験名, いま関心があるか)
    ("20260601", "20260801", "7月: 難易度ラダーの探索（記憶・合成・動的参照）", False),
    ("20260801", "20260823", "実験2: 深さラダー（pointer_chain）", False),
    ("20260823", "20260824", "実験3: 構造ラダー（dualptr / recptr）", False),
    ("20260824", "20260901", "実験4: 学習量スイープ", False),
    ("20260901", "20260905", "実験5: 参照範囲ラダー（narrowptr）", False),
    ("20260905", "20260909", "実験5b: 静的端点の検証", False),
    ("20260909", "20260912", "実験6: 鍵の交絡", False),
    ("20260912", "20260913", "実験7: seed ばらつきの検証", False),
    ("20260913", "20260915", "実験8a: 学習予算の探り", False),
    ("20260915", "20260919", "実験8b: 参照範囲ラダー", False),
    ("20260919", "20270101", "実験9: 最小課題と項数", True),
]


# 日付の区間では拾えない run の例外（run 名 → (実験名, いま関心があるか)）。
# 区間の境界をまたいで実施した実験や，あとから別の実験の一部として読み直した run を
# ここで正す。--tag が使えない過去の run のための措置であり，新しい run では不要。
RUN_STAGE_OVERRIDES: dict[str, tuple[str, bool]] = {
    # 7月に学習したが，2026-09 に500件で再評価して実験5b・6 の静的参照の端点
    # （99.6%）として使っている。学習日は7月でも，議論に効いているのは現在。
    "run_20260729_023201": ("実験5b: 静的端点の検証", True),
    # 学習量スイープ（n_train=3000 / 5000）。実験3 の当日に走り始めたため
    # 日付の区間では実験3 に入ってしまう。
    "run_20260823_151707": ("実験4: 学習量スイープ", False),
    "run_20260823_210006": ("実験4: 学習量スイープ", False),
}


def stage_of(run_name: str, tag: str) -> tuple[str, bool]:
    """(実験名, いま関心があるか) を返す．--tag があればそれを優先する．"""
    if tag:
        return tag, True
    if run_name in RUN_STAGE_OVERRIDES:
        return RUN_STAGE_OVERRIDES[run_name]
    m = re.match(r"run_(\d{8})", run_name)
    if m:
        for start, end, name, active in STAGES:
            if start <= m.group(1) < end:
                return name, active
    return "分類なし", False


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
        stage, active = stage_of(os.path.basename(run_dir), args.get("tag", ""))
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
            "stage": stage,
            "active": active,
            "run": os.path.basename(run_dir),
            "path": os.path.relpath(run_dir, REPO_ROOT),
        })
    rows.sort(key=lambda r: (r["algorithm"], r["key_seed"] or 0, r["data_seed"] or 0,
                             r["n_train"] or 0, r["epochs"] or 0))
    _mark_active(rows)
    return rows


def _mark_active(rows: list[dict]) -> None:
    """「いま動いている」を絞り込む．

    --tag が付いた run を無条件に active にしていたため，終わった実験も
    詳細表示に残り続け，一覧が読めなくなっていた（2026-09-20）。
    人間が知りたいのは「いま何が走っているか」と「直前に何が出たか」だけなので，

    **最も新しい実験だけ**を詳細に出し，残りは要約に畳む．走行中のバッチは
    必ず最新の実験に属するので，これで「いま何が走っているか」は必ず見える．
    過去の結果は docs/experiment_index.md で実験単位に読む．

    「未評価だから走行中」という判定にはしない．7月に学習が完走せず放棄された
    run が16本あり，それらを走行中とみなすと7月の実験が丸ごと詳細表示に
    戻ってしまうためである．
    """
    if not rows:
        return
    latest: dict[str, str] = {}
    for r in rows:
        st = r["stage"]
        latest[st] = max(latest.get(st, ""), r["run"])
    newest = max(latest, key=lambda st: latest[st]) if latest else None
    for r in rows:
        r["active"] = r["stage"] == newest


def pct(v) -> str:
    return "未評価" if v is None else f"{v:.1%}"


def num(v, spec="{:.4f}") -> str:
    return "-" if v is None else spec.format(v)


def detail_table(items: list[dict]) -> list[str]:
    md = ["| アルゴリズム | 鍵 | データ | 学習件数 | エポック | 評価件数 | 正解率 "
          "| 最終val損失 | 離陸ep | run |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in items:
        md.append(
            f"| {r['algorithm']} | {r['key_seed']} | {r['data_seed']} | {r['n_train']} "
            f"| {r['epochs']} | {r['n_test'] or '-'} | {pct(r['accuracy'])} "
            f"| {num(r['final_val_loss'])} | {r['takeoff_epoch'] or '-'} | `{r['run']}` |"
        )
    return md


def missing_combos(items: list[dict]) -> list[tuple]:
    """そのアルゴリズムで一度でも使った値の直積のうち，実施記録が無いもの．"""
    keys = sorted({r["key_seed"] for r in items if r["key_seed"] is not None})
    seeds = sorted({r["data_seed"] for r in items if r["data_seed"] is not None})
    trains = sorted({r["n_train"] for r in items if r["n_train"] is not None})
    eps = sorted({r["epochs"] for r in items if r["epochs"] is not None})
    done = {(r["key_seed"], r["data_seed"], r["n_train"], r["epochs"]) for r in items}
    return [(k, d, t, e) for k in keys for d in seeds for t in trains for e in eps
            if (k, d, t, e) not in done]


def build_md(rows: list[dict], show_all: bool) -> list[str]:
    active = [r for r in rows if r["active"]]
    settled = [r for r in rows if not r["active"]]

    md = [
        "# 実験の棚卸し（どのパラメータで走らせたか）",
        "",
        f"`experiments/inventory.py` により自動生成（{datetime.now():%Y-%m-%d %H:%M:%S}）．",
        f"一次データ: `results/inventory.csv`（学習 run {len(rows)} 本）",
        "",
        "**この表は「学習 run」が1行**．学習条件（件数・エポック・lr）と検証損失が見える．"
        "まだ評価していない run も載る．",
        "評価そのものを一覧したいなら [summary_llm.md](summary_llm.md)（`make summarize`）を見ること"
        "（プロンプティング評価も含む，評価1件が1行）．",
        "",
        f"「離陸」は検証損失が {TAKEOFF_THRESHOLD} を下回った最初のエポック．"
        "`-` は最後まで下回らなかったこと（＝学習が始まっていないこと）を表す．"
        "詳しくは [docs/measurement_audit.md](../docs/measurement_audit.md)．",
        "",
        "**この表は道具であって，読み物ではない．**「いま何が走っているか」と"
        "「直前に何が出たか」だけを詳細に出し，残りは要約に畳む．"
        "過去の結果を実験単位で追うなら [docs/experiment_index.md](../docs/experiment_index.md)，"
        "指標そのものの分布を見るなら `make corpus` を使うこと．",
        "",
    ]

    # ---- いま関心のある実験 ----
    md += ["## いま動いている実験", ""]
    by_stage: dict[str, list[dict]] = defaultdict(list)
    for r in active:
        by_stage[r["stage"]].append(r)
    for stage in sorted(by_stage, reverse=True):
        items = by_stage[stage]
        md += [f"### {stage}", "", *detail_table(items), ""]

    # ---- 決着済み ----
    md += ["## 決着済みの実験（要約）", "",
           "`--all` を付けると全 run の明細が出る。", "",
           "| 実験 | run数 | アルゴリズム | 正解率の幅 |", "|---|---|---|---|"]
    st_settled: dict[str, list[dict]] = defaultdict(list)
    for r in settled:
        st_settled[r["stage"]].append(r)
    for stage in sorted(st_settled, reverse=True):
        items = st_settled[stage]
        accs = [r["accuracy"] for r in items if r["accuracy"] is not None]
        span = f"{min(accs):.1%} 〜 {max(accs):.1%}" if accs else "評価なし"
        algos = sorted({r["algorithm"] for r in items})
        shown = ", ".join(algos[:4]) + (f" 他{len(algos) - 4}種" if len(algos) > 4 else "")
        md.append(f"| {stage} | {len(items)} | {shown} | {span} |")
    md.append("")

    if show_all:
        md += ["### 決着済みの明細", ""]
        for stage in sorted(st_settled, reverse=True):
            md += [f"#### {stage}", "", *detail_table(st_settled[stage]), ""]

    return md


def main() -> None:
    ap = argparse.ArgumentParser(description="実験の棚卸しを作る")
    ap.add_argument("--algorithm", default=None, help="このアルゴリズムだけに絞る")
    ap.add_argument("--all", action="store_true",
                    help="決着済みの実験も明細で出す（既定は要約のみ）")
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

    md = build_md(rows, show_all=args.all)
    md_path = os.path.join(REPO_ROOT, "results", "inventory.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    # 「未評価」には，走行中のものと，学習が完走せず放棄されたものが混ざる。
    # 一緒に数えると「17本も評価し忘れている」ように見えてしまうので分ける。
    未評価 = [r for r in rows if r["accuracy"] is None]
    # history.csv は学習が完走した時点で書かれるので，走行中の run にはまだ無い。
    # checkpoints があれば少なくとも学習は動いている＝放棄ではない。
    def _abandoned(r: dict) -> bool:
        d = os.path.join(REPO_ROOT, r["path"])
        return not (os.path.isfile(os.path.join(d, "history.csv"))
                    or os.path.isdir(os.path.join(d, "checkpoints")))
    放棄 = [r for r in 未評価 if _abandoned(r)]
    print(f"保存完了: {csv_path}")
    print(f"          {md_path}")
    print(f"学習 run {len(rows)} 本 / アルゴリズム "
          f"{len({r['algorithm'] for r in rows})} 種類")
    if 未評価:
        走行中 = len(未評価) - len(放棄)
        print(f"  未評価 {len(未評価)} 本 = 走行中 {走行中} 本 ＋ "
              f"放棄 {len(放棄)} 本（7月の，学習が完走しなかった run）")


if __name__ == "__main__":
    main()
