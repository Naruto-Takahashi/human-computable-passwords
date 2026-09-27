#!/usr/bin/env python3
"""実験ラベルの対応表 — どの run がどの実験のものかを決める規則．

**保存場所は条件アドレスのまま（results/llm_eval/<関数>/<タスク>/<条件>/…）で，
実験は「ラベル」として与える。**物理的に実験ごとへ分けない理由は3つある：

| 性質 | 依存している箇所 |
|---|---|
| 重複排除 | 実験12 は実験8a の run を再利用して8条件を作った |
| 再開・スキップ | `is_run_completed` は「そのパスに metrics.json があるか」だけを見る |
| 横断集計 | `corpus_analysis` が llm_eval を全 walk し，60run から診断を出している |

実験ごとにディレクトリを分けると，同じ条件が複製され，実験番号が違うだけで
GPU を再消費し，実験をまたぐ分析が壊れる。

## 規則の当て方

上から順に見て**最初に当たったものを採用する**。日付だけで切れない箇所
（09/13 は実験7と8a，08/23 は実験3と4）は epochs / n_train で分ける。

新しい run は `--experiment` で明示的にラベルを付ける。この表は
**それ以前（2026-09-26 より前）の run を遡って割り当てるため**のものである。
"""

# (ラベル, 題, 開始日, 終了日, 追加条件) — 追加条件は run の情報を受け取る述語
EXPERIMENTS = [
    ("B1",  "難易度ラダーの探索（記憶・合成・動的参照）", "20260716", "20260729", None),
    ("B2",  "動的参照の深さ",                              "20260816", "20260818", None),
    # 08/23 は実験3（構造）と実験4（学習量）が同居する。学習量スイープは n_train を振った側。
    ("B4",  "学習量を増やせば床から出るか",                "20260823", "20260824",
     lambda r: (r.get("n_train") or 1000) != 1000),
    ("B3",  "動的参照の本数と依存構造",                    "20260823", "20260823", None),
    ("B5",  "動的参照の強さを連続的に刻む（narrowptr）",   "20260902", "20260902", None),
    ("B5b", "静的端点が離陸しないのはなぜか",              "20260905", "20260906", None),
    ("B6",  "鍵の効果はどこまで大きいか",                  "20260909", "20260910", None),
    # 09/13 は実験7（5エポック・引きを振る）と実験8a（20エポック）が同居する。
    ("B8a", "予算を外せば動的参照は離陸するか",            "20260913", "20260914",
     lambda r: (r.get("epochs") or 5) > 5),
    ("B7",  "鍵の性質か，run のばらつきか",                "20260912", "20260913", None),
    ("B8b", "参照範囲のどこで学習できなくなるか",          "20260917", "20260918", None),
    ("B9",  "課題を極小にしても動的参照は学習されないか",  "20260919", "20260921", None),
    ("B12", "素朴な手順の誤判定はどれだけ起きるか",        "20260923", "20260924", None),
]

# ソルバーの測定（学習 run を持たないので日付では引けない）
SOLVER_EXPERIMENTS = {
    "func_13_k10": "A13", "func_22_k10": "A13", "func_31_k10": "A13",
    "table_add3_k10": "A13", "table_add3_k15": "A13", "table_add3_k26": "A13",
    "narrowptr_k10_m2": "A13", "lookup_k10": "A13",
    # 実験A1 の予備実験（A1pre）のはしご。5サイズ × 3役の基準線。
    # 2026-09-27: 設計が夜のうちに変わり条件が不揃いになったため（鍵の本数・予算・
    # プロンプト水準が混在），本番ではなく予備として扱う。得られた知見は有効。
    "func_22_k4": "A1pre", "table_add3_k4": "A1pre", "narrowptr_k4_m1": "A1pre",
    "func_22_k6": "A1pre", "table_add3_k6": "A1pre", "narrowptr_k6_m1": "A1pre",
    "func_22_k8": "A1pre", "table_add3_k8": "A1pre", "narrowptr_k8_m1": "A1pre",
    "narrowptr_k10_m1": "A1pre",
    "func_22_k13": "A1pre", "table_add3_k13": "A1pre", "narrowptr_k13_m1": "A1pre",
    # n=26 は in-context では測定範囲外と判明したが，基準線自体は測れている
    "narrowptr_k26_m1": "A1pre",
    "func_22": "B1", "func_31": "B1", "func_13": "B1", "func_13_k26": "B1",
}

# **1つの run は複数の実験に属しうる。**実験をまたいで再利用されるためで，
# これこそ実験ごとに実体を分けない理由である。下は「主ラベル以外にも
# この実験に数える」という追加規則。
SHARED = [
    # 実験12（偽陰性の再現率）は，既に測ってあった2件を8条件の一部として使った
    #   - table_add3_k10 鍵6（実験8a の20エポック run）
    #   - func_22_k10 鍵0（20エポック run。「予算を増やせば何でも100%になるわけではない」錨）
    ("B12", lambda r: (r.get("epochs") or 0) == 20
     and r.get("algorithm") in ("table_add3_k10", "func_22_k10")),
    # 実験4（学習量スイープ）は，実験3 の 1000件条件を基準線として共有する。
    # 実験4 は鍵1のみ（docs/experiment_index.md の「保留（鍵1のみ）」）なので鍵で絞る。
    ("B4", lambda r: r.get("date", "").startswith("202608")
     and r.get("algorithm") == "func_22_k10" and (r.get("n_train") or 0) == 1000
     and r.get("key_seed") == 1),
]


def all_labels(run: dict) -> list[str]:
    """run が属する実験ラベルをすべて返す（主ラベル＋共有分）．"""
    labels = [assign(run)]
    for label, pred in SHARED:
        if label not in labels and pred(run):
            labels.append(label)
    return labels


TITLES = {label: title for label, title, *_ in EXPERIMENTS}
TITLES["A13"] = "経路Aの基準線: m*_info の確定"
TITLES["A1pre"] = "予備実験: A1 の設計を固める（課題の選択・壁の所在の絞り込み）"
TITLES["A1"] = "動的参照は in-context 推論でも壁になるか（小川ら CNN の3世代目）"
TITLES["?"] = "未割り当て"


def assign(run: dict) -> str:
    """run（date / epochs / n_train を含む辞書）に実験ラベルを与える．

    run が `experiment` を自分で持っていればそれを優先する（新しい run）。
    """
    if run.get("experiment"):
        return run["experiment"]
    date = run.get("date")
    if not date:
        return "?"
    for label, _title, start, end, pred in EXPERIMENTS:
        if start <= date <= end and (pred is None or pred(run)):
            return label
    return "?"
