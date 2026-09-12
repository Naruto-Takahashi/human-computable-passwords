#!/usr/bin/env python3
r"""Markdown 内の数式が実際に描画できるか確かめる．

GitHub は数式を KaTeX 系のエンジンで描画するため，構文を誤ると
「Missing or unrecognized delimiter for \left」のようなエラーが本文に出る。
目視では気づきにくいので，同じパーサに通して事前に検出する。

週次報告（pandoc + Typst 用）は記法が異なるため対象外。

初回のみ依存の取得が要る:
    cd tools/math_check && npm install --silent katex

    python3 tools/check_math.py
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "tools", "math_check")


def collect() -> list[dict]:
    items = []
    files = [p for p in glob.glob(os.path.join(ROOT, "docs/**/*.md"), recursive=True)
             if "reports/weekly" not in p]
    files += [os.path.join(ROOT, "README.md"), os.path.join(ROOT, "results/README.md")]
    for path in sorted(set(files)):
        if not os.path.exists(path):
            continue
        rel = os.path.relpath(path, ROOT)
        text = re.sub(r"```.*?```", "", open(path, encoding="utf-8").read(), flags=re.S)
        for m in re.finditer(r"\$\$(.+?)\$\$", text, re.S):
            items.append({"file": rel, "kind": "display", "body": m.group(1).strip()})
        rest = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
        for m in re.finditer(r"\$`([^`]+)`\$", rest):        # GitHub の推奨記法
            items.append({"file": rel, "kind": "inline", "body": m.group(1)})
        rest = re.sub(r"\$`[^`]*`\$", "", rest)
        for m in re.finditer(r"\$([^$\n]+)\$", rest):        # 素の $...$
            items.append({"file": rel, "kind": "inline", "body": m.group(1)})
    return items


def main() -> None:
    if not os.path.exists(os.path.join(HERE, "node_modules")):
        print("依存が未取得です。次を実行してください:", file=sys.stderr)
        print("  cd tools/math_check && npm install --silent katex", file=sys.stderr)
        sys.exit(2)

    items = collect()
    payload = os.path.join(HERE, "items.json")
    with open(payload, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    r = subprocess.run(["node", os.path.join(HERE, "check.mjs"), payload],
                       cwd=HERE, capture_output=True, text=True)
    print(r.stdout.rstrip() or r.stderr.rstrip())
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
