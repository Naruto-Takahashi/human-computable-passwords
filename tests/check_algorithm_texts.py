#!/usr/bin/env python3
"""
アルゴリズムの文面と計算結果が，記録した基準から変わっていないことを確かめる．

**なぜ必要か**: 学習済みアダプタは `rule_text` の文字列で学習している．表現を
1文字でも変えると，そのアダプタを新しいプロンプトで評価することになり，過去の
結果と比較できなくなる（正解率が動いても，関数が難しくなったのか文面が変わった
のか区別できない）．リファクタリングで壊しやすい一方，壊れても気づきにくいので，
機械的に検査する．

    python3 tests/check_algorithm_texts.py           # 検査（make test に含まれる）
    python3 tests/check_algorithm_texts.py --update  # 意図して文面を変えたとき

`--update` は慎重に．基準を更新したら，そのルール文で学習したアダプタは
それ以前のものと比較できなくなる．更新する理由を docs/log.md に残すこと．
"""
import argparse
import json
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from hcp.algorithms import ALGORITHMS  # noqa: E402

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "algorithm_texts.json")
TEXT_FIELDS = ("level", "key_size", "challenge_len", "rule_text", "rationale_text", "code_body")
N_SAMPLES = 300
N_EXPLAIN = 20
SEED = 12345


def snapshot() -> dict:
    out = {}
    for name, algo in sorted(ALGORITHMS.items()):
        rng = np.random.default_rng(SEED)
        key = [int(v) for v in rng.integers(0, 10, algo.key_size)] if algo.key_size else None
        outputs, explains = [], []
        for i in range(N_SAMPLES):
            ch = [int(v) for v in rng.integers(0, algo.challenge_domain(), algo.challenge_len)]
            z = algo.compute(ch, key)
            outputs.append(z)
            if i < N_EXPLAIN:
                explains.append(algo.explain(ch, key, z))
        rec = {f: getattr(algo, f) for f in TEXT_FIELDS}
        rec["outputs"] = outputs
        rec["explain"] = explains
        out[name] = rec
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true", help="基準を現在の内容で上書きする")
    args = ap.parse_args()

    current = snapshot()
    if args.update or not os.path.exists(BASELINE):
        with open(BASELINE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"基準を更新しました: {os.path.relpath(BASELINE, REPO_ROOT)}"
              f"（{len(current)} アルゴリズム）")
        return

    with open(BASELINE, encoding="utf-8") as f:
        base = json.load(f)

    problems = []
    added = set(current) - set(base)
    removed = set(base) - set(current)
    if added:
        problems.append(f"基準に無いアルゴリズムが増えています: {sorted(added)}"
                        "（意図した追加なら --update）")
    if removed:
        problems.append(f"アルゴリズムが消えています: {sorted(removed)}")

    for name in sorted(set(base) & set(current)):
        for field in TEXT_FIELDS + ("outputs", "explain"):
            if base[name][field] != current[name][field]:
                problems.append(f"{name}.{field} が基準と違います")
                if field in TEXT_FIELDS and isinstance(base[name][field], str):
                    problems.append(f"    基準: {base[name][field]!r}")
                    problems.append(f"    現在: {current[name][field]!r}")
                break

    if problems:
        print("アルゴリズムの文面・計算結果が基準から変わっています。", file=sys.stderr)
        print("学習済みアダプタとの比較が成立しなくなるため，意図した変更か確認してください。",
              file=sys.stderr)
        for p in problems[:20]:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)

    print(f"check_algorithm_texts: {len(base)} アルゴリズムの文面・計算結果・解説が基準と一致")


if __name__ == "__main__":
    main()
