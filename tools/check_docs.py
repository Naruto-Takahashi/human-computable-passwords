#!/usr/bin/env python3
r"""GitHub で描画が崩れる書き方が混ざっていないか確かめる．

週次報告は pandoc + Typst で組むため，GitHub が解釈できない記法を使っている
（グリッド表・`: キャプション`・`\_` のエスケープ）。それらを docs/ に持ち込むと，
GitHub 上では表が生のテキストとして出てしまう。実際 hcp_background.md は
週次報告から抽出したため崩れていた（2026-09-13 に修正）。

週次報告そのもの（docs/reports/weekly_report_*.md）と TEMPLATE，および
書き方の例を載せている reports/README.md のコードブロックは対象外。

    python3 tools/check_docs.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHECKS = [
    ("pandoc のグリッド表（GitHub では描画されない）", r"^\+[-=]{3,}"),
    ("pandoc の表キャプション `: ...`", r"^: \S"),
    ("不要なエスケープ `\\_`（GitHub では不要）", r"\\_"),
]


def targets() -> list[str]:
    out = []
    for pat in ("*.md", "docs/**/*.md", "results/*.md", "experiments/**/*.md"):
        out += glob.glob(os.path.join(ROOT, pat), recursive=True)
    skip = ("reports/weekly_report_", "reports/TEMPLATE.md", "legacy/")
    return sorted(f for f in out if not any(s in f for s in skip))


def strip_code(text: str) -> str:
    """コードブロックと数式を取り除く（書き方の例は検査しない）．"""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"\$`[^`]*`\$", "", text)    # GitHub 記法の数式は先に丸ごと除く
    text = re.sub(r"``[^`]*``", "", text)      # `` ... `` の入れ子
    text = re.sub(r"`[^`\n]*`", "", text)      # インラインコード
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
    return re.sub(r"\$[^$\n]+\$", "", text)


def main() -> None:
    problems = 0
    for path in targets():
        raw = open(path, encoding="utf-8").read()
        # コードブロックだけ落とした原文で判定する（インラインコードを消すと
        # 行頭に : が現れるなどの誤検出が起きるため）
        body = re.sub(r"```.*?```", "", raw, flags=re.S)
        for label, pattern in CHECKS:
            hits = [i for i, l in enumerate(body.splitlines(), 1)
                    if re.search(pattern, l)]
            if hits:
                rel = os.path.relpath(path, ROOT)
                print(f"  {rel}: {label} — {len(hits)} 箇所（{hits[:5]} 行目）")
                problems += len(hits)

    # インライン数式が markdown の強調に食われないか
    # GitHub は $...$ の中の _ を強調記法として解釈してしまうことがあり，
    # そうなると下付き文字が消えて数式が崩れる。公式の回避策は $`...`$ である。
    for path in targets():
        if "reports/" in path:      # 週次報告は pandoc を通すので $...$ のままが正しい
            continue
        body = open(path, encoding="utf-8").read()
        body = re.sub(r"```.*?```", "", body, flags=re.S)
        body = re.sub(r"\$\$.*?\$\$", "", body, flags=re.S)
        body = re.sub(r"\$`[^`]*`\$", "", body)     # 変換済みは除く
        bad = [m for m in re.findall(r"\$([^$\n]+)\$", body) if "_" in m or "*" in m]
        if bad:
            rel = os.path.relpath(path, ROOT)
            print(f"  {rel}: インライン数式が強調に食われる — {len(bad)} 箇所"
                  f"（例 ${bad[0][:30]}$ → $`{bad[0][:30]}`$ と書く）")
            problems += len(bad)

    # 数式の中の \{ \} は markdown にエスケープとして食われる
    # （\{ → { になり，MathJax が \left{ を受け取って
    #  「Missing or unrecognized delimiter for \left」になる）。
    # \lbrace / \rbrace を使うこと。
    for path in targets():
        if "reports/" in path:
            continue
        body = re.sub(r"```.*?```", "", open(path, encoding="utf-8").read(), flags=re.S)
        hits = 0
        for m in list(re.finditer(r"\$\$(.+?)\$\$", body, re.S)) + \
                 list(re.finditer(r"\$`([^`]+)`\$", body)):
            hits += m.group(1).count("\\{") + m.group(1).count("\\}")
        if hits:
            rel = os.path.relpath(path, ROOT)
            print(f"  {rel}: 数式内の \\{{ \\}} — {hits} 箇所"
                  f"（markdown に食われる。\\lbrace \\rbrace を使う）")
            problems += hits

    # $$ が独立した行にあるか（1行に詰めるとインライン扱いになり \left が壊れる）
    for path in targets():
        if "reports/" in path:
            continue
        body = re.sub(r"```.*?```", "", open(path, encoding="utf-8").read(), flags=re.S)
        body = re.sub(r"\$`[^`]*`\$", "", body)
        body = re.sub(r"``[^`]*``", "", body)
        body = re.sub(r"`[^`\n]*`", "", body)
        inline_dd = re.findall(r"^.*\S\$\$.*$|^\$\$.+\$\$$", body, re.M)
        if inline_dd:
            rel = os.path.relpath(path, ROOT)
            print(f"  {rel}: $$ が独立行にない — {len(inline_dd)} 箇所"
                  f"（前後で改行する）")
            problems += len(inline_dd)

    # 数式の $ が閉じているか
    for path in targets():
        body = re.sub(r"```.*?```", "", open(path, encoding="utf-8").read(), flags=re.S)
        body = re.sub(r"\$\$.*?\$\$", "", body, flags=re.S)
        for i, line in enumerate(body.splitlines(), 1):
            if line.count("$") % 2:
                print(f"  {os.path.relpath(path, ROOT)}:{i} 数式の $ が閉じていない")
                problems += 1

    if problems:
        print(f"\n  {problems} 箇所に問題があります。")
        sys.exit(1)
    print(f"  check_docs: {len(targets())} ファイル、GitHub で崩れる記法はありません")


if __name__ == "__main__":
    main()
