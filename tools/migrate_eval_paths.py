#!/usr/bin/env python3
"""
既存の評価結果を，n_test を含む新しいディレクトリ構造へ移す．

旧: {base}/{model}/{algo}/{task}/n{N}_stage{S}_k{K}/ks{ks}_ds{ds}
新: {base}/{model}/{algo}/{task}/n{N}_t{T}_stage{S}_k{K}/ks{ks}_ds{ds}

T は各 metrics.json に記録されている n_test から取る．旧構造では評価件数が
違っても同じ場所に書かれていたため，50件と500件の結果が見分けられなかった
（2026-09-12 の監査で発見。詳しくは hcp.evaluation.make_run_dir の docstring）。

    python3 tools/migrate_eval_paths.py            # 変更内容の確認のみ（既定）
    python3 tools/migrate_eval_paths.py --apply    # 実際に移動する
"""
import argparse
import json
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS_DIR = os.path.join(REPO_ROOT, "results", "llm_eval")
OLD_RE = re.compile(r"^n(\d+)_stage(\d+)_k(\d+)$")


def plan_moves() -> list[tuple[str, str, int]]:
    moves = []
    for dirpath, _dirnames, filenames in os.walk(EVALS_DIR):
        if "metrics.json" not in filenames:
            continue
        seeds_dir = os.path.basename(dirpath)
        cond_dir = os.path.basename(os.path.dirname(dirpath))
        m = OLD_RE.match(cond_dir)
        if not m:
            continue  # すでに新形式，または想定外の構造
        with open(os.path.join(dirpath, "metrics.json"), encoding="utf-8") as f:
            data = json.load(f)
        n_test = data.get("n_test") or data.get("config", {}).get("n_test")
        if n_test is None:
            print(f"[警告] n_test が読めないため据え置き: {dirpath}", file=sys.stderr)
            continue
        n_shot, stage, k = m.groups()
        new_cond = f"n{n_shot}_t{n_test}_stage{stage}_k{k}"
        parent = os.path.dirname(os.path.dirname(dirpath))
        moves.append((dirpath, os.path.join(parent, new_cond, seeds_dir), n_test))
    return moves


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="実際に移動する（既定は確認のみ）")
    args = ap.parse_args()

    moves = plan_moves()
    if not moves:
        print("移行対象はありません（すべて新形式です）。")
        return

    by_n = {}
    for _src, _dst, n in moves:
        by_n[n] = by_n.get(n, 0) + 1
    print(f"移行対象 {len(moves)} 件（評価件数の内訳: "
          + ", ".join(f"{n}件×{c}" for n, c in sorted(by_n.items())) + "）\n")
    for src, dst, _n in moves[:10]:
        print(f"  {os.path.relpath(src, REPO_ROOT)}\n    -> {os.path.relpath(dst, REPO_ROOT)}")
    if len(moves) > 10:
        print(f"  ... 他 {len(moves) - 10} 件")

    conflicts = [d for _s, d, _n in moves if os.path.exists(d)]
    if conflicts:
        print(f"\n[中止] 移動先がすでに存在します（{len(conflicts)} 件）。手で確認してください。",
              file=sys.stderr)
        for d in conflicts[:5]:
            print(f"  {os.path.relpath(d, REPO_ROOT)}", file=sys.stderr)
        sys.exit(1)

    if not args.apply:
        print("\n確認のみです。実行するには --apply を付けてください。")
        return

    for src, dst, _n in moves:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
    # 空になった旧条件ディレクトリを掃除する
    for dirpath, dirnames, filenames in os.walk(EVALS_DIR, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)
    print(f"\n完了: {len(moves)} 件を移動しました。")


if __name__ == "__main__":
    main()
