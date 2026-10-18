#!/usr/bin/env python3
"""tools/lit_search.py の重複除去と追記が正しいことを，ネットワークなしで確かめる．

**なぜ必要か**: 候補一覧 candidates.csv の状態・関連度は人が付ける。追記で既存の
行を壊したり，同じ論文を版違いで二重に足したりすると，読んだ判断が失われる。

    python3 tests/check_lit_search.py   # make test に含まれる
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import lit_search as L  # noqa: E402

failures = []


def check(name, got, want):
    if got != want:
        failures.append(f"{name}: {got!r} != {want!r}")


check("doi の正規化", L.norm_doi("https://doi.org/10.1007/ABC"), "10.1007/abc")
check("doi: 接頭辞", L.norm_doi("doi:10.1/X"), "10.1/x")
check("引用キー", L.make_key("Jeremiah Blocki", 2017, "Towards Human Computable Passwords"),
      "blocki2017human")
check("引用キー（記号）", L.make_key("Hassan Jameel Asghar", 2017,
                                 "When are identification protocols with sparse challenges safe?"),
      "asghar2017identification")
check("引用キー（著者なし）", L.make_key("", 2020, "On the"), "anon2020")

existing = [{"key": "blocki2017human", "title": "Towards Human Computable Passwords",
             "doi": "10.4230/lipics.itcs.2017.10", "arxiv": "", "status": "本文"}]
found = [
    {"key": "blocki2014human", "title": "Towards human computable passwords.", "doi": "", "arxiv": "1404.0024"},
    {"key": "x2023a", "title": "Paper A", "doi": "10.1/A", "arxiv": ""},
    {"key": "x2023a", "title": "Paper A (journal version)", "doi": "https://doi.org/10.1/a", "arxiv": ""},
    {"key": "x2023a", "title": "Paper B", "doi": "", "arxiv": "2301.00001"},
]
new = L.merge_new(existing, found)
check("題名で版違いを除く・DOI の表記揺れを除く", [r["title"] for r in new], ["Paper A", "Paper B"])
L.unique_keys(existing, new)
check("キーの衝突に a, b を付ける", [r["key"] for r in new], ["x2023a", "x2023aa"])

with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "c.csv")
    L.append_candidates([{"key": "k1", "title": "T1", "status": "本文", "note": "読んだ"}], path)
    L.append_candidates([{"key": "k2", "title": "T2", "status": "未読"}], path)
    rows = L.read_candidates(path)
    check("追記で既存の行が残る", [(r["key"], r["status"], r["note"]) for r in rows],
          [("k1", "本文", "読んだ"), ("k2", "未読", "")])
    check("列の順", list(rows[0].keys()), L.FIELDS)

if failures:
    print("lit_search の検査に失敗:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("lit_search: 重複除去・引用キー・追記 OK")
