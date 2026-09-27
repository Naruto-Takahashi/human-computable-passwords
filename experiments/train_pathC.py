#!/usr/bin/env python3
"""
経路C: Transformer を1から学習させる（実験C1 の実行器）．

引き継いだ `experiments/train_baseline.py` は測定値を壊す欠陥を4つ持っており，
そのまま経路C に使えない（docs/experiment_index.md の実験C1 を参照）．

| # | 旧実装の欠陥 | 本実装 |
|---|---|---|
| 1 | `Models.list_models()` がモデルを1度だけ構築し，関数ループ内で `fit` を呼び続ける → **前の条件の重みが残る** | 1 run ごとに新規構築 |
| 2 | 生成器の `seed` 既定値が 42 固定 → **鍵1本・引き1通り** | run ごとに独立な seed |
| 3 | メタデータが最終エポックのみ → 小川ら（各run の最大）と揃わない | 最大・最終・全履歴 |
| 4 | `except Exception: continue` → 失敗が静かに流れる | 捕まえない |

さらに2つ足している．

- **試験集合を分ける**（訓練:検証:試験 = 8:1:1）．「検証最大」は検証集合で選んだ
  値なので汎化性能として読めない．最大のエポックでの試験正解率も記録する．
- **鍵ごとの基準線**（同じ鍵での最頻値予測器の正解率）．偶然水準 0.1 と比べる
  設計は実験2で否定されている．

使い方:

    python3 experiments/train_pathC.py --algorithm func_22 --datasize 10000 --runs 3
    HCP_DRY_RUN=1 python3 experiments/train_pathC.py --algorithm func_22   # 疎通確認

本モジュールは GPU を掴まない（TensorFlow が CUDA を見つけられない環境のため
CPU で動く）．経路A・B の GPU 実験と並行して回せる．
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from hcp.algorithms import get_algorithm  # noqa: E402

DRY_RUN = os.environ.get("HCP_DRY_RUN") == "1"


def make_dataset(algorithm, datasize: int, seed: int):
    """鍵とチャレンジを seed から独立に引く．

    小川らも「$\\sigma$ は実行ごとに独立生成」としている（多対一写像であり
    全単射ではない）．旧実装は seed=42 固定で，鍵が1本しか出てこなかった．
    """
    rng = np.random.default_rng(seed)
    key = rng.integers(0, 10, algorithm.key_size).tolist()
    n_values = algorithm.challenge_domain()
    challenges = rng.integers(0, n_values, (datasize, algorithm.challenge_len))
    z = np.array(
        [algorithm.compute([int(v) for v in ch], key) for ch in challenges],
        dtype=np.int64,
    )
    return challenges, z, key


def split_8_1_1(x, y, seed: int):
    rng = np.random.default_rng(seed + 1)
    idx = rng.permutation(len(x))
    n_val = n_test = len(x) // 10
    test, val, train = idx[:n_test], idx[n_test:n_test + n_val], idx[n_test + n_val:]
    return (x[train], y[train]), (x[val], y[val]), (x[test], y[test])


def majority_baseline(y_train, y_eval) -> float:
    """鍵ごとの基準線: 訓練集合の最頻値を常に答える予測器の正解率．

    偶然水準 0.1 ではなくこれと比べる（実験2）．鍵の数字ヒストグラムが偏って
    いると偶然水準より高くなるため，0.1 と比べると「学習した」と誤判定する．
    """
    most = np.bincount(y_train, minlength=10).argmax()
    return float((y_eval == most).mean())


def one_run(args, algorithm, run_index: int) -> dict:
    import tensorflow as tf
    from tensorflow import keras

    from baseline_ml.models import Models

    seed = args.seed_base + run_index
    # 重みの初期化と shuffle も run ごとに変える（run のばらつきを測るため）
    keras.utils.set_random_seed(seed)

    x, y, key = make_dataset(algorithm, args.datasize, seed)
    (xtr, ytr), (xva, yva), (xte, yte) = split_8_1_1(x, y, seed)

    model = Models.embed_transformer(          # 欠陥1: run ごとに新規構築
        n_images=algorithm.challenge_domain(),
        d_model=args.d_model,
        num_heads=args.num_heads,
        num_layers=args.num_layers,
        ff_dim=args.ff_dim,
        readout=args.readout,
        learning_rate=args.learning_rate,
    )
    n_params = int(model.count_params())

    to_cat = keras.utils.to_categorical
    start = time.time()
    hist = model.fit(
        xtr, to_cat(ytr, 10),
        batch_size=args.batch_size,
        epochs=args.epochs,
        verbose=2 if args.verbose else 0,
        validation_data=(xva, to_cat(yva, 10)),
    ).history
    elapsed = time.time() - start

    val_acc = hist["val_accuracy"]
    best_epoch = int(np.argmax(val_acc))

    # 検証最大のエポックの重みは保持していないので，最終重みでの試験正解率と
    # 併せて「最終エポックの検証」も残す．最大値だけで語らないための材料．
    test_acc_final = float(model.evaluate(xte, to_cat(yte, 10), verbose=0)[1])

    return {
        "algorithm": algorithm.name,
        "run_index": run_index,
        "seed": seed,
        "n_images": algorithm.challenge_domain(),
        "key": key,
        "datasize": args.datasize,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "d_model": args.d_model,
        "num_heads": args.num_heads,
        "num_layers": args.num_layers,
        "ff_dim": args.ff_dim,
        "readout": args.readout,
        "learning_rate": args.learning_rate,
        "n_params": n_params,
        "elapsed_seconds": round(elapsed, 1),
        # 欠陥3: 最大・最終・全履歴のすべてを残す
        "val_accuracy_max": float(max(val_acc)),
        "val_accuracy_final": float(val_acc[-1]),
        "best_epoch": best_epoch,
        "train_accuracy_max": float(max(hist["accuracy"])),
        "train_accuracy_final": float(hist["accuracy"][-1]),
        "test_accuracy_final": test_acc_final,
        # 鍵ごとの基準線
        "baseline_majority_val": majority_baseline(ytr, yva),
        "baseline_majority_test": majority_baseline(ytr, yte),
        "history": {k: [float(v) for v in vs] for k, vs in hist.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algorithm", nargs="+", required=True)
    ap.add_argument("--datasize", type=int, default=10000)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--runs", type=int, default=3, help="反復数（1条件1run にしない）")
    ap.add_argument("--seed_base", type=int, default=20260927)
    ap.add_argument("--d_model", type=int, default=64)
    ap.add_argument("--num_heads", type=int, default=4)
    ap.add_argument("--num_layers", type=int, default=2)
    ap.add_argument("--ff_dim", type=int, default=128)
    ap.add_argument("--readout", default="flatten", choices=("flatten", "mean", "cls"))
    ap.add_argument("--learning_rate", type=float, default=1e-3)
    ap.add_argument("--experiment", default="C1pre0", help="results/ の仕分け用ラベル")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    algorithms = [get_algorithm(name) for name in args.algorithm]
    out_dir = os.path.join(REPO_ROOT, "results", "path_c", args.experiment)

    print(f"条件: {len(algorithms)} 関数 × {args.runs} run = "
          f"{len(algorithms) * args.runs} run")
    for a in algorithms:
        print(f"  {a.name}: 鍵{a.key_size}マス, 値域 0〜{a.challenge_domain() - 1}")
    if DRY_RUN:
        print("HCP_DRY_RUN=1 のため学習はしない")
        return

    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"runs_{stamp}.jsonl")
    rows = []
    for algorithm in algorithms:
        for i in range(args.runs):
            row = one_run(args, algorithm, i)      # 欠陥4: 例外は捕まえない
            rows.append(row)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"  {row['algorithm']:18s} run{i} "
                  f"検証最大 {row['val_accuracy_max']:.4f} "
                  f"最終 {row['val_accuracy_final']:.4f} "
                  f"試験 {row['test_accuracy_final']:.4f} "
                  f"基準線 {row['baseline_majority_test']:.4f} "
                  f"訓練最大 {row['train_accuracy_max']:.4f} "
                  f"({row['elapsed_seconds']:.0f}s)", flush=True)

    print(f"\n{'関数':20s} {'検証最大(平均±sd)':>22s} {'試験最終':>18s} {'基準線':>8s}")
    for a in algorithms:
        v = np.array([r["val_accuracy_max"] for r in rows if r["algorithm"] == a.name])
        t = np.array([r["test_accuracy_final"] for r in rows if r["algorithm"] == a.name])
        b = np.array([r["baseline_majority_test"] for r in rows if r["algorithm"] == a.name])
        print(f"{a.name:20s} {v.mean():.4f}±{v.std(ddof=1) if len(v) > 1 else 0:.4f}"
              f"  最大{v.max():.4f}   {t.mean():.4f}±{t.std(ddof=1) if len(t) > 1 else 0:.4f}"
              f"   {b.mean():.4f}")
    print(f"\n保存: {path}")


if __name__ == "__main__":
    main()
