#!/usr/bin/env python3
"""
深さラダー（pointer_chain_k10_d{1,2,3}）の結果を分解して分析する．

正解率という単一の数字では，モデルが何を学習し何を学習していないかが見えない．
本スクリプトは以下を分解して出力する：

  1. 鍵に存在しない数字を予測しているか（＝答えの値域を学習できているか）
  2. 「正解の周辺分布を完全に知った上で独立サンプリング」する戦略（衝突確率 Σp_i²）
     を超えるか（＝チャレンジ内容に依存した計算をしているか）
  3. タスクA「値域の記憶」とタスクB「ポインタ計算」への分解と，各々の達成度

使い方: PYTHONPATH=src .venv/bin/python experiments/analyze_depth_ladder.py
"""
import collections
import csv
import glob
import json

from scipy.stats import binomtest, fisher_exact

ALGO = "pointer_chain_k10_d{d}"
DEPTHS = (1, 2, 3)
KEY_SEEDS = (1, 2)


def load_results(name, key_seed):
    paths = glob.glob(
        f"results/llm_eval/*/{name}/predict_pure/n0_stage2_k0/ks{key_seed}_ds0/results.csv"
    )
    if not paths:
        return None
    return list(csv.DictReader(open(sorted(paths)[-1])))


def load_key(key_seed):
    for path in glob.glob(
        "results/llm_finetune/qwen2.5_3b/pointer_chain_k10_d1/run_*/train_metadata.json"
    ):
        meta = json.load(open(path))
        if meta["args"].get("key_seed") == key_seed:
            return meta["sgm"]
    return None


def main():
    for key_seed in KEY_SEEDS:
        key = load_key(key_seed)
        if key is None:
            print(f"key_seed={key_seed}: 鍵のメタデータが見つかりません．スキップします．")
            continue

        hist = collections.Counter(key)
        keyset = set(key)
        missing = sorted(set(range(10)) - keyset)
        # 「正解の周辺分布から独立に引く」戦略の期待正解率＝衝突確率
        collision = sum((hist.get(v, 0) / len(key)) ** 2 for v in range(10))
        p_outside = len(missing) / 10

        print(f"\n{'=' * 72}")
        print(f"key_seed={key_seed}  鍵={key}")
        print(f"  値のヒストグラム={dict(sorted(hist.items()))}")
        print(f"  鍵に無い数字={missing}  値域={len(keyset)}種類")
        print(f"  タスクAのみ達成した場合の期待正解率（衝突確率）={collision:.0%}")

        accuracies = {}
        for depth in DEPTHS:
            rows = load_results(ALGO.format(d=depth), key_seed)
            if rows is None:
                print(f"\n  d{depth}: 結果が見つかりません．スキップします．")
                continue
            n = len(rows)
            correct = sum(1 for r in rows if r["is_correct"] == "True")
            accuracies[depth] = (correct, n)
            outside = sum(1 for r in rows if int(r["predicted"]) not in keyset)
            preds = collections.Counter(r["predicted"] for r in rows)

            # 値域の学習: 鍵外を1件も出さない確率（一様予測を帰無仮説とする）
            if outside == 0:
                p_range = (1 - p_outside) ** n if missing else float("nan")
            else:
                p_range = binomtest(outside, n, p_outside, alternative="less").pvalue

            # 計算の証拠: 周辺分布サンプリングを超えるか
            p_calc = binomtest(correct, n, collision, alternative="greater").pvalue

            # タスクB達成度: A水準から100%へどれだけ進んだか
            task_b = (correct / n - collision) / (1.0 - collision)

            print(f"\n  d{depth}: 正解 {correct}/{n} = {correct / n:.0%}")
            print(f"      鍵外の数字を予測: {outside}/{n}件 "
                  f"(一様なら{p_outside * n:.0f}件, p={p_range:.2e}) → 値域の学習")
            print(f"      周辺分布サンプリング({collision:.0%})を超えるか: p={p_calc:.4f}"
                  f"{' ★' if p_calc < 0.05 else ''} → 計算の証拠")
            print(f"      タスクB（ポインタ計算）達成度: {task_b:+.0%}")
            print(f"      予測分布: {dict(sorted(preds.items(), key=lambda x: -x[1]))}")

        # 深さ間の比較
        if len(accuracies) > 1:
            print("\n  深さ間のFisher exact検定:")
            depths = sorted(accuracies)
            for i, da in enumerate(depths):
                for db in depths[i + 1:]:
                    ca, na = accuracies[da]
                    cb, nb = accuracies[db]
                    _, p = fisher_exact([[ca, na - ca], [cb, nb - cb]])
                    print(f"    d{da} vs d{db}: p={p:.3f}")


if __name__ == "__main__":
    main()
