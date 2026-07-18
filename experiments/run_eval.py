#!/usr/bin/env python3
# =============================================================================
# run_eval.py — 統一評価ランナー（旧 run_prompting.py の後継）
# =============================================================================
# 1条件・複数シードの評価を実行する．タスクは2種類:
#   - predict     : テスト問題1問ずつの応答予測（paradigm: pure / pot）
#   - recover_key : 観察データから鍵テーブルを丸ごと逆推定（1シードあたり1回の推論）
#
# 例:
#   # Stage 2・N=30 で鍵復元を鍵5個分（シード0〜4）測定
#   python experiments/run_eval.py --task recover_key --provider ollama --model qwen2.5:7b \
#       --algorithm func_22 --stage 2 --n_shot 30 --key_seeds 0-4
#
#   # mock によるドライラン
#   python experiments/run_eval.py --provider mock --model test --n_test 5
# =============================================================================

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from hcp import algorithm_names, generate_dataset, get_algorithm
from hcp.clients import create_client
from hcp.evaluation import is_run_completed, make_run_dir, run_predict, run_recover_key

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "results", "llm_eval")


def parse_seed_list(spec: str) -> list[int]:
    """"0-4" や "0,1,5" 形式のシード指定をリストへ展開する．"""
    seeds: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-")
            seeds.extend(range(int(lo), int(hi) + 1))
        elif part:
            seeds.append(int(part))
    if not seeds:
        raise argparse.ArgumentTypeError(f"シード指定を解釈できません: {spec}")
    return seeds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="HCP LLM ベンチマーク統一評価ランナー",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # ---- タスク・実験条件 ----
    parser.add_argument("--task", type=str, default="predict",
                        choices=["predict", "recover_key"], help="評価タスク")
    parser.add_argument("--algorithm", "--generator", dest="algorithm", type=str,
                        default="func_22", choices=algorithm_names(), help="HCP アルゴリズム名")
    parser.add_argument("--paradigm", type=str, default="pure", choices=["pure", "pot"],
                        help="predict タスクの回答形式（pure: JSON, pot: Pythonコード実行）")
    parser.add_argument("--stage", type=int, default=2, choices=[0, 1, 2, 3],
                        help="情報開示ステージ（0:なし, 1:鍵のみ, 2:ルールのみ, 3:ルール+鍵K個）")
    parser.add_argument("--k_disclosed", type=int, default=0,
                        help="Stage 3 で開示する鍵の要素数 K")
    parser.add_argument("--n_shot", type=int, default=10,
                        help="観察データ（Few-shot ペア）の件数 N")
    parser.add_argument("--n_test", type=int, default=50,
                        help="テスト問題数（recover_key では held-out 採点に使用）")
    parser.add_argument("--key_seeds", type=parse_seed_list, default=[0],
                        help="鍵シード（例: '0-4' や '0,1,7'）．シードごとに独立な鍵で反復する")
    parser.add_argument("--data_seeds", type=parse_seed_list, default=[0],
                        help="データシード（チャレンジ集合の乱数）")
    # ---- モデル設定 ----
    parser.add_argument("--provider", type=str, default="ollama",
                        choices=["gemini", "ollama", "mock", "lora"], help="LLM プロバイダ")
    parser.add_argument("--model", type=str, default="qwen2.5:7b",
                        help="モデル名（lora の場合は学習 run ディレクトリのパス）")
    parser.add_argument("--sleep_sec", type=float, default=4.0,
                        help="リクエスト間の待機時間（Gemini のみ）")
    parser.add_argument("--parallel", type=int, default=8,
                        help="predict タスクの並列リクエスト数")
    parser.add_argument("--thinking_budget", type=int, default=1024,
                        help="Gemini の思考トークン予算")
    # ---- 出力・制御 ----
    parser.add_argument("--output_base_dir", type=str, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true",
                        help="完了済み条件（metrics.json あり）も再実行する")
    parser.add_argument("--verbose", action="store_true")
    return parser


def task_label(args) -> str:
    return f"predict_{args.paradigm}" if args.task == "predict" else "recover_key"


def run_one(client, args, key_seed: int, data_seed: int) -> dict | None:
    """1シード分の評価を実行する．完了済みならスキップして None を返す．"""
    algorithm = get_algorithm(args.algorithm)
    run_dir = make_run_dir(
        base_dir=args.output_base_dir,
        model=client.model_name if args.provider == "lora" else args.model,
        algorithm=args.algorithm,
        task_label=task_label(args),
        stage=args.stage,
        k_disclosed=args.k_disclosed,
        n_shot=args.n_shot,
        key_seed=key_seed,
        data_seed=data_seed,
    )
    if is_run_completed(run_dir) and not args.overwrite:
        print(f"  [skip] 完了済み: {os.path.relpath(run_dir, REPO_ROOT)}")
        return None

    ds = generate_dataset(
        algorithm, n_shot=args.n_shot, n_test=args.n_test,
        key_seed=key_seed, data_seed=data_seed,
    )
    config = {
        **{k: v for k, v in vars(args).items() if k not in ("key_seeds", "data_seeds")},
        "key_seed": key_seed,
        "data_seed": data_seed,
        "task_label": task_label(args),
    }

    if args.task == "predict":
        return run_predict(
            client, ds, stage=args.stage, k_disclosed=args.k_disclosed,
            paradigm=args.paradigm, run_dir=run_dir, config=config,
            parallel=args.parallel, verbose=args.verbose,
        )
    return run_recover_key(
        client, ds, stage=args.stage, k_disclosed=args.k_disclosed,
        run_dir=run_dir, config=config,
    )


def main():
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    client_kwargs = {}
    if args.provider == "gemini":
        client_kwargs = {"sleep_sec": args.sleep_sec, "thinking_budget": args.thinking_budget}
    client = create_client(args.provider, args.model, **client_kwargs)

    print("=" * 60)
    print("【評価設定】")
    print(f"  タスク       : {task_label(args)}")
    print(f"  プロバイダ   : {args.provider} / {args.model}")
    print(f"  アルゴリズム : {args.algorithm}")
    print(f"  Stage / K    : {args.stage} / {args.k_disclosed}")
    print(f"  N (n_shot)   : {args.n_shot}")
    print(f"  鍵シード     : {args.key_seeds} × データシード: {args.data_seeds}")
    print("=" * 60)

    for key_seed in args.key_seeds:
        for data_seed in args.data_seeds:
            print(f"\n>>> key_seed={key_seed}, data_seed={data_seed}")
            run_one(client, args, key_seed, data_seed)

    print("\n完了しました．集計は: python experiments/summarize.py")


if __name__ == "__main__":
    main()
