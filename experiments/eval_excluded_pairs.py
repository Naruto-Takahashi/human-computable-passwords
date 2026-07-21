#!/usr/bin/env python3
# =============================================================================
# eval_excluded_pairs.py — 「暗記か合成か」の切り分け評価
# =============================================================================
# --exclude_pairs つきで学習したモデルに対し，学習から完全に除外された
# (X0, X1) の組だけを使ったチャレンジで held-out 評価を行う．
#   - 除外ペアで高精度 → 参照値の算術合成（計算方法）を獲得している
#   - 偶然水準       → 成功は入力クラスの丸暗記に過ぎない
# 結果は run ディレクトリの excluded_pair_eval.json に保存する．
# =============================================================================

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from hcp import get_algorithm
from hcp.clients import LoraClient
from hcp.dataset import challenges_to_df, extract_challenge_and_response
from hcp.executor import parse_answer_digit
from hcp.prompts import build_prompt


def main():
    parser = argparse.ArgumentParser(description="学習除外ペアのみでの held-out 評価")
    parser.add_argument("--model", type=str, required=True,
                        help="--exclude_pairs つきで学習した run ディレクトリ")
    parser.add_argument("--n_test", type=int, default=100)
    parser.add_argument("--eval_seed", type=int, default=0)
    args = parser.parse_args()

    with open(os.path.join(args.model, "train_metadata.json"), encoding="utf-8") as f:
        meta = json.load(f)
    train_args = meta["args"]
    excluded = [tuple(p) for p in meta.get("excluded_pairs", [])]
    if not excluded:
        raise SystemExit("このモデルは --exclude_pairs なしで学習されています")

    algorithm = get_algorithm(train_args["algorithm"])
    key = meta["sgm"]
    stage = train_args["stage"]
    domain = algorithm.challenge_domain()

    # 除外ペアだけを (X0, X1) に持つチャレンジを生成（残りの桁はランダム）
    rng = np.random.default_rng([args.eval_seed, 424242])
    challenges = []
    for i in range(args.n_test):
        x0, x1 = excluded[i % len(excluded)]
        rest = rng.integers(0, domain, algorithm.challenge_len - 2)
        challenges.append((x0, x1, *map(int, rest)))
    test_df = challenges_to_df(algorithm, challenges, key)

    print(f"除外ペア {len(excluded)} 組 / 評価 {args.n_test} 件 / stage {stage}")
    client = LoraClient(run_dir=args.model)

    records = []
    correct = 0
    for i, (_, row) in enumerate(test_df.iterrows()):
        challenge, ans = extract_challenge_and_response(row)
        prompt = build_prompt(
            algorithm=algorithm,
            shot_df=test_df.iloc[0:0],  # n_shot=0（学習時と同じ最小プロンプト）
            task="predict",
            stage=stage,
            key=key,
            test_challenge=challenge,
            paradigm="pure",
        )
        raw = client.predict(prompt)
        pred = parse_answer_digit(raw)
        ok = pred is not None and pred == ans
        correct += ok
        records.append({"challenge": challenge, "correct_ans": ans,
                        "predicted": pred, "is_correct": bool(ok)})
        print(f"  [{i + 1:3d}/{args.n_test}] {'✓' if ok else '✗'} 正解={ans}, 予測={pred}")

    accuracy = correct / args.n_test
    result = {
        "task": "excluded_pair_eval",
        "model": args.model,
        "algorithm": algorithm.name,
        "stage": stage,
        "n_excluded_pairs": len(excluded),
        "n_test": args.n_test,
        "correct_count": correct,
        "accuracy": round(accuracy, 4),
        "records": records,
    }
    out_path = os.path.join(args.model, "excluded_pair_eval.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n除外ペアのみの正解率: {accuracy:.2%} ({correct}/{args.n_test})")
    print(f"保存: {out_path}")


if __name__ == "__main__":
    main()
