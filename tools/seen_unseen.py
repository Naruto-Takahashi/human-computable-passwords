#!/usr/bin/env python3
"""評価結果を「学習で既出」と「未出」に分けて正解率を出す．

鍵を小さくすると答えを決める入力の組み合わせが減り，学習データが評価を
覆ってしまう（実験9 の narrowptr_k4_m1 では評価500件の約62%が既出の見込み）．
全体の正解率だけでは，規則を学んだのか丸暗記したのかを区別できない．

ここでの「既出」は14個の入力そのものではなく（k=4 でも 4^14 通りあり，
まず重複しない），**答えを決める位置の組**が既出という意味である．
どの位置が答えを決めるかはアルゴリズムごとに違うので，値を振って
出力が変わるかどうかで自動的に判定する．

使い方:
    python3 tools/seen_unseen.py <評価の run ディレクトリ>
    python3 tools/seen_unseen.py results/llm_eval/narrowptr_k4_m2/.../ks35_ds0/*/
"""
import argparse
import ast
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import numpy as np

from hcp import generate_dataset, get_algorithm

TRAIN_SEED_OFFSET = 1_000_000


def relevant_positions(algorithm, key, n_probe=400, seed=0):
    """答えに影響する位置を，値を振って実測で特定する．

    位置 i を別の値に変えて出力が一度でも変わるなら，i は答えに関与する．
    narrowptr_k*_m{m} なら {0..m-1, 10, 11, 12, 13} が返る．
    """
    rng = np.random.default_rng(seed)
    k = len(key)
    relevant = set()
    for _ in range(n_probe):
        ch = rng.integers(0, k, size=14).tolist()
        base = algorithm.fn(ch, key)
        for i in range(14):
            if i in relevant:
                continue
            for v in range(k):
                if v == ch[i]:
                    continue
                alt = list(ch)
                alt[i] = v
                if algorithm.fn(alt, key) != base:
                    relevant.add(i)
                    break
    return sorted(relevant)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", help="評価の run ディレクトリ（results.csv と metrics.json がある）")
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "metrics.json"), encoding="utf-8") as f:
        metrics = json.load(f)
    cfg = metrics["config"]
    algorithm = get_algorithm(cfg["algorithm"])
    key_seed, data_seed = cfg["key_seed"], cfg["data_seed"]

    # 学習件数は学習側の run から読む（評価の metrics には無い）
    train_meta_path = os.path.join(cfg["model"], "train_metadata.json")
    if not os.path.isfile(train_meta_path):
        sys.exit(f"学習の metadata が見つかりません: {train_meta_path}")
    with open(train_meta_path, encoding="utf-8") as f:
        train_meta = json.load(f)
    n_train = train_meta["args"]["n_train"]
    n_val = train_meta["args"]["n_val"]
    key = train_meta["sgm"]

    # 学習チャレンジを再生成する（train_finetuning.py と同じ手順）
    pool = generate_dataset(algorithm, n_shot=train_meta["args"]["n_shot"],
                            n_test=n_train + n_val, key_seed=key_seed,
                            data_seed=data_seed + TRAIN_SEED_OFFSET)
    cols = [c for c in pool.test_df.columns if c.startswith("X")]
    cols.sort(key=lambda c: int(c[1:]))
    train_ch = pool.test_df[cols].to_numpy()[:n_train]

    pos = relevant_positions(algorithm, key)
    seen = {tuple(row[pos]) for row in train_ch}

    with open(os.path.join(args.run_dir, "results.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    buckets = {True: [0, 0], False: [0, 0]}   # 既出/未出 -> [正解, 全体]
    for r in rows:
        ch = ast.literal_eval(r["challenge"])
        is_seen = tuple(ch[i] for i in pos) in seen
        buckets[is_seen][1] += 1
        if r["is_correct"].lower() in ("true", "1"):
            buckets[is_seen][0] += 1

    print(f"{cfg['algorithm']}  鍵{key_seed}（{key}） データ{data_seed}")
    print(f"  答えを決める位置: {pos}  → 組み合わせ {len(key) ** len(pos):,} 通り")
    print(f"  学習 {n_train} 件が覆った組み合わせ: {len(seen):,} 通り")
    print()
    print("  区分   件数   正解   正解率")
    for label, flag in (("既出", True), ("未出", False)):
        ok, tot = buckets[flag]
        rate = f"{100*ok/tot:5.1f}%" if tot else "    —"
        print(f"  {label}  {tot:5d}  {ok:5d}   {rate}")
    ok = sum(b[0] for b in buckets.values()); tot = sum(b[1] for b in buckets.values())
    print(f"  全体  {tot:5d}  {ok:5d}   {100*ok/tot:5.1f}%")
    print()
    if buckets[False][1] == 0:
        print("  ※ 未出が0件。学習が評価を完全に覆っている。")
    else:
        print("  ※ 未出の正解率が主データ。既出との差が大きければ丸暗記の寄与が大きい。")


if __name__ == "__main__":
    main()
