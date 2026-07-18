#!/usr/bin/env python3
# =============================================================================
# info_limit.py — 情報理論的限界 N*_info とソルバー基準線の測定
# =============================================================================
# 観察データ N 件（および Stage 3 の鍵開示 K 個）に整合する鍵候補数を
# 厳密ソルバーで数え上げ，鍵が一意に特定される臨界点を求める．
#
# 出力（results/theory/）:
#   - {algorithm}_info_limit.csv : N, K, シードごとの整合鍵数・ソルバー復元の成否
#   - {algorithm}_info_limit.md  : 中央値まとめの Markdown 表
#
# この基準線の役割:
#   - 整合鍵数 > 1 の領域では鍵の一意復元は原理的に不可能（LLM の失敗は能力不足ではない）
#   - 整合鍵数 = 1 かつソルバーが復元に成功する領域での LLM の失敗が，
#     純粋な「推論の欠損」として解釈できる
#
# 例:
#   python experiments/info_limit.py --algorithm func_22 --n_shots 5,10,15,20,26,30,40,50 --key_seeds 0-9
#   python experiments/info_limit.py --algorithm func_22 --stage 3 --n_shots 10 --k_values 0,6,13,20 --key_seeds 0-9
# =============================================================================

import argparse
import csv
import itertools
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from hcp import generate_dataset, get_algorithm
from hcp.dataset import observations_from_df
from hcp.solver import count_consistent_keys
from run_eval import parse_seed_list

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "results", "solver")


def main():
    parser = argparse.ArgumentParser(
        description="整合鍵数の数え上げによる情報限界 N*_info の測定",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--algorithm", type=str, default="func_22")
    parser.add_argument("--stage", type=int, default=2, choices=[2, 3],
                        help="2: 鍵開示なし / 3: 先頭 K 要素開示")
    parser.add_argument("--n_shots", type=parse_seed_list, default=[5, 10, 15, 20, 26, 30, 40, 50])
    parser.add_argument("--k_values", type=parse_seed_list, default=[0])
    parser.add_argument("--key_seeds", type=parse_seed_list, default=[0, 1, 2, 3, 4])
    parser.add_argument("--data_seeds", type=parse_seed_list, default=[0])
    parser.add_argument("--solution_cap", type=int, default=100_000,
                        help="整合鍵数の数え上げ上限（超えたら '>=cap' として記録）")
    parser.add_argument("--node_budget", type=int, default=2_000_000,
                        help="探索ノード数の上限．中間領域（func_22/31 の N≈30〜60）は"
                             "厳密数え上げが重く，上限到達時は下限値として報告される")
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    algorithm = get_algorithm(args.algorithm)
    if algorithm.key_size == 0:
        parser.error(f"{args.algorithm} は鍵を持たないため対象外です")
    if args.stage != 3 and args.k_values != [0]:
        parser.error("--k_values は --stage 3 のときのみ指定できます")

    os.makedirs(args.output_dir, exist_ok=True)
    rows = []

    conditions = list(itertools.product(
        args.n_shots, args.k_values, args.key_seeds, args.data_seeds
    ))
    for n_shot, k, key_seed, data_seed in conditions:
        ds = generate_dataset(algorithm, n_shot=n_shot, n_test=0,
                              key_seed=key_seed, data_seed=data_seed)
        observations = observations_from_df(ds.shot_df)
        known = {i: ds.key[i] for i in range(k)} if k else None

        t0 = time.time()
        result = count_consistent_keys(
            algorithm, observations, known_cells=known,
            solution_cap=args.solution_cap, node_budget=args.node_budget,
        )
        elapsed = time.time() - t0

        # ソルバーが復元した鍵の正しさ（一意なら真の鍵と一致するはず）
        solver_exact = bool(result.solutions) and result.solutions[0] == ds.key
        unique = (not result.capped) and result.solution_count == 1

        count_str = f">={result.solution_count}" if result.capped else str(result.solution_count)
        print(
            f"  {args.algorithm} n={n_shot:3d} k={k:2d} ks={key_seed} ds={data_seed}: "
            f"整合鍵数={count_str}（{'一意' if unique else '非一意'}）, "
            f"ノード={result.nodes_expanded}, {elapsed:.2f}s"
        )
        rows.append({
            "algorithm": args.algorithm,
            "n_shot": n_shot,
            "k_disclosed": k,
            "key_seed": key_seed,
            "data_seed": data_seed,
            "consistent_keys": result.solution_count,
            "capped": result.capped,
            "unique": unique,
            "solver_recovered_true_key": solver_exact,
            "nodes_expanded": result.nodes_expanded,
            "elapsed_sec": round(elapsed, 3),
        })

    # ---- CSV 保存 ----
    csv_path = os.path.join(args.output_dir, f"{args.algorithm}_info_limit.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # ---- Markdown まとめ（N×K ごとの中央値と一意特定率） ----
    md_lines = [
        f"# {args.algorithm} — 整合鍵数と情報限界 N*_info",
        "",
        f"ソルバー: 厳密数え上げ（solution_cap={args.solution_cap}）",
        f"シード: 鍵 {args.key_seeds} × データ {args.data_seeds}",
        "",
        "| N | K | 整合鍵数（中央値） | 一意特定率 | ソルバー復元成功率 |",
        "|---|---|---|---|---|",
    ]
    for n_shot, k in itertools.product(args.n_shots, args.k_values):
        group = [r for r in rows if r["n_shot"] == n_shot and r["k_disclosed"] == k]
        med = statistics.median(r["consistent_keys"] for r in group)
        capped_any = any(r["capped"] for r in group)
        med_str = f">={med:g}" if capped_any else f"{med:g}"
        uniq_rate = sum(r["unique"] for r in group) / len(group)
        solver_rate = sum(r["solver_recovered_true_key"] for r in group) / len(group)
        md_lines.append(f"| {n_shot} | {k} | {med_str} | {uniq_rate:.0%} | {solver_rate:.0%} |")

    md_path = os.path.join(args.output_dir, f"{args.algorithm}_info_limit.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"\n保存完了: {csv_path}\n          {md_path}")


if __name__ == "__main__":
    main()
