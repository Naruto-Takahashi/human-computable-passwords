#!/usr/bin/env python3
"""
登録されているアルゴリズムを，難易度の分解にそって一覧にする．

algorithms.py は 900行を超えており，定義を上から読んでも「どれとどれが
比較のために作られたのか」が見えない。ここでは ①記憶 ②合成 ③動的参照 の
分解（docs/plan.md）にそって並べ，鍵のサイズと1行の要約を添える。

    python3 tools/list_algorithms.py            # 一覧
    python3 tools/list_algorithms.py func_22_k10  # 1つを詳しく（ルール文・教師コード）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from hcp.algorithms import ALGORITHMS, get_algorithm  # noqa: E402

# (グループ名, 説明, 名前で判定する述語)。上から順に当てはめ，最初に一致した組に入れる。
GROUPS: list[tuple[str, str, object]] = [
    ("鍵なし", "鍵を使わない対照（下限の確認用）",
     lambda n: n in ("simple_add", "secret_add")),
    ("①記憶", "鍵を引くだけ。参照は1箇所",
     lambda n: n.startswith("lookup")),
    ("②合成", "鍵を複数箇所引いて足す。動的参照は無い",
     lambda n: n.startswith("table_add")),
    ("③動的参照・深さ", "同じ写像を繰り返し適用する（不動点の問題あり）",
     lambda n: n.startswith("pointer_chain") or n.startswith("pointer_k")),
    ("③動的参照・構造", "参照の本数と依存関係を変える",
     lambda n: n.startswith("dualptr") or n.startswith("recptr")),
    ("③動的参照・範囲", "ポインタの行き先の数 m を変える。m=1 は静的，m=10 は func_22_k10",
     lambda n: n.startswith("narrowptr")),
    ("原論文の関数族", "f_{k1,k2}（k1=添字を作る項数, k2=末尾で足す項数）",
     lambda n: n.startswith("func_")),
]


def summarize(name: str) -> str:
    """rule_text から計算の中身を1行に詰める．"""
    algo = ALGORITHMS[name]
    lines = [ln.strip() for ln in algo.rule_text.splitlines() if ln.strip()]
    body = [ln for ln in lines
            if not ln.startswith("ルール") and "SGM_TABLE のインデックス" not in ln]
    text = " ".join(body)
    text = text.replace("を計算します。", " / ").replace("を計算します", "")
    for pre in ("1. ", "2. ", "3. "):
        text = text.replace(pre, "")
    return (text[:78] + "…") if len(text) > 79 else text


def main() -> None:
    if len(sys.argv) > 1:
        name = sys.argv[1]
        algo = get_algorithm(name)
        print(f"=== {algo.name}（level {algo.level} / 鍵 {algo.key_size} マス / "
              f"チャレンジ {algo.challenge_len} 個）\n")
        print("[ルール文（Stage 2 でモデルに見せるもの）]")
        print(algo.rule_text)
        print("[教師コード]")
        print(algo.code_body)
        return

    assigned: set[str] = set()
    print(f"登録されているアルゴリズム: {len(ALGORITHMS)} 種類")
    print("（詳細は tools/list_algorithms.py <名前>，定義は src/hcp/algorithms.py）\n")
    for title, desc, pred in GROUPS:
        names = sorted(n for n in ALGORITHMS if n not in assigned and pred(n))
        if not names:
            continue
        assigned |= set(names)
        print(f"── {title} — {desc}")
        for n in names:
            print(f"   {n:<22} 鍵{ALGORITHMS[n].key_size:>4}  {summarize(n)}")
        print()
    rest = sorted(set(ALGORITHMS) - assigned)
    if rest:
        print("── 未分類")
        for n in rest:
            print(f"   {n:<22} 鍵{ALGORITHMS[n].key_size:>4}  {summarize(n)}")


if __name__ == "__main__":
    main()
