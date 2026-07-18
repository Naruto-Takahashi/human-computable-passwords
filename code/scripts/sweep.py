#!/usr/bin/env python3
# =============================================================================
# sweep.py — 相転移スイープハーネス（旧 batch_prompting.py / compare_prompting.py の後継）
# =============================================================================
# N（観察ペア数）× K（鍵開示数）× アルゴリズム × シードの直積を一括実行する．
# 完了済み条件（metrics.json あり）は自動でスキップされるため，
# 中断しても同じコマンドの再実行で続きから走る（レジューム）．
#
# 例:
#   # func_22 / Stage 2 の N スイープ（鍵5個で反復）— RQ1 の主実験
#   python code/scripts/sweep.py --task recover_key --provider ollama --model qwen2.5:7b \
#       --algorithms func_22 --stage 2 --n_shots 10,20,30,40,50,75,100 --key_seeds 0-4
#
#   # Stage 3 の K スイープ — RQ2 の主実験
#   python code/scripts/sweep.py --task recover_key --provider ollama --model qwen2.5:7b \
#       --algorithms func_22 --stage 3 --n_shots 30 --k_values 0,6,13,20,26 --key_seeds 0-4
#
#   # 実行計画の確認のみ（推論は行わない）
#   python code/scripts/sweep.py ... --dry_run
# =============================================================================

import argparse
import itertools
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hcp import algorithm_names
from hcp.clients import create_client
from hcp.evaluation import is_run_completed, make_run_dir
from run_eval import DEFAULT_OUTPUT, parse_seed_list, run_one


def parse_int_list(spec: str) -> list[int]:
    return parse_seed_list(spec)


def parse_str_list(spec: str) -> list[str]:
    return [s.strip() for s in spec.split(",") if s.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="HCP 相転移スイープハーネス",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--task", type=str, default="recover_key",
                        choices=["predict", "recover_key"])
    parser.add_argument("--paradigm", type=str, default="pure", choices=["pure", "pot"])
    parser.add_argument("--algorithms", type=parse_str_list, default=["func_22"],
                        help=f"カンマ区切り（選択肢: {algorithm_names()}）")
    parser.add_argument("--stage", type=int, default=2, choices=[0, 1, 2, 3])
    parser.add_argument("--n_shots", type=parse_int_list, default=[10, 20, 30, 50],
                        help="観察ペア数 N のリスト（例: '10,20,30,50' や '10-50'）")
    parser.add_argument("--k_values", type=parse_int_list, default=[0],
                        help="鍵開示数 K のリスト（Stage 3 用）")
    parser.add_argument("--key_seeds", type=parse_seed_list, default=[0, 1, 2, 3, 4])
    parser.add_argument("--data_seeds", type=parse_seed_list, default=[0])
    parser.add_argument("--n_test", type=int, default=50)
    parser.add_argument("--provider", type=str, default="ollama",
                        choices=["gemini", "ollama", "mock", "lora"])
    parser.add_argument("--model", type=str, default="qwen2.5:7b")
    parser.add_argument("--sleep_sec", type=float, default=4.0)
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--thinking_budget", type=int, default=1024)
    parser.add_argument("--output_base_dir", type=str, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry_run", action="store_true", help="実行計画の表示のみ")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.stage != 3 and args.k_values != [0]:
        parser.error("--k_values は --stage 3 のときのみ指定できます")

    conditions = list(itertools.product(
        args.algorithms, args.n_shots, args.k_values, args.key_seeds, args.data_seeds
    ))

    # 完了済みチェック
    task_lbl = f"predict_{args.paradigm}" if args.task == "predict" else "recover_key"
    plan = []
    for algo, n_shot, k, ks, ds_seed in conditions:
        run_dir = make_run_dir(
            base_dir=args.output_base_dir, model=args.model, algorithm=algo,
            task_label=task_lbl, stage=args.stage, k_disclosed=k,
            n_shot=n_shot, key_seed=ks, data_seed=ds_seed,
        )
        done = is_run_completed(run_dir) and not args.overwrite
        plan.append((algo, n_shot, k, ks, ds_seed, done))

    todo = [p for p in plan if not p[5]]
    print("=" * 70)
    print(f"スイープ計画: 全 {len(plan)} 条件（完了済み {len(plan) - len(todo)} / 実行予定 {len(todo)}）")
    print(f"  タスク: {task_lbl} / モデル: {args.provider}:{args.model} / Stage {args.stage}")
    print(f"  アルゴリズム: {args.algorithms} / N: {args.n_shots} / K: {args.k_values}")
    print(f"  鍵シード: {args.key_seeds} / データシード: {args.data_seeds}")
    if args.task == "predict":
        print(f"  推定リクエスト数: {len(todo) * args.n_test} 回（{args.n_test} 問 × {len(todo)} 条件）")
    else:
        print(f"  推定リクエスト数: {len(todo)} 回（recover_key は1条件1リクエスト）")
    print("=" * 70)

    if args.dry_run:
        for algo, n_shot, k, ks, ds_seed, done in plan:
            mark = "済" if done else "予"
            print(f"  [{mark}] {algo} n={n_shot} k={k} ks={ks} ds={ds_seed}")
        return

    if not todo:
        print("すべて完了済みです。")
        return

    client_kwargs = {}
    if args.provider == "gemini":
        client_kwargs = {"sleep_sec": args.sleep_sec, "thinking_budget": args.thinking_budget}
    client = create_client(args.provider, args.model, **client_kwargs)

    failed = []
    for idx, (algo, n_shot, k, ks, ds_seed, done) in enumerate(plan, 1):
        if done:
            continue
        print(f"\n>>> [{idx}/{len(plan)}] {algo} n_shot={n_shot} k={k} ks={ks} ds={ds_seed}")
        run_args = argparse.Namespace(
            **{**vars(args), "algorithm": algo, "n_shot": n_shot, "k_disclosed": k}
        )
        try:
            run_one(client, run_args, key_seed=ks, data_seed=ds_seed)
        except Exception as e:
            print(f"  [ERROR] 条件をスキップします: {e}")
            traceback.print_exc()
            failed.append((algo, n_shot, k, ks, ds_seed))

    print("\n" + "=" * 70)
    print(f"スイープ完了．失敗: {len(failed)} 条件")
    for f in failed:
        print(f"  失敗: {f}")
    print("集計は: python code/scripts/summarize.py")


if __name__ == "__main__":
    main()
