#!/usr/bin/env python3
"""Markdown 内の mermaid 図が構文エラーを起こさないか確かめる．

GitHub は ```mermaid ブロックをそのまま描画するが，構文を誤ると
図の代わりにエラーが表示されてしまい，README では特に目立つ。
mermaid 本体のパーサ（jsdom 上で動かす）に通して事前に検出する。

初回は依存の取得が要る:
    cd tools/mermaid_check && npm install --silent mermaid@11 jsdom

    python3 tools/check_mermaid.py            # 全 Markdown
    python3 tools/check_mermaid.py README.md  # ファイル指定
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(ROOT, "tools", "mermaid_check", "check.mjs")


def main() -> None:
    targets = sys.argv[1:] or (
        glob.glob(os.path.join(ROOT, "*.md"))
        + glob.glob(os.path.join(ROOT, "docs/**/*.md"), recursive=True)
        + glob.glob(os.path.join(ROOT, "results/*.md"))
        + glob.glob(os.path.join(ROOT, "experiments/**/*.md"), recursive=True))

    if not os.path.exists(os.path.join(ROOT, "tools/mermaid_check/node_modules")):
        print("依存が未取得です。次を実行してください:", file=sys.stderr)
        print("  cd tools/mermaid_check && npm install --silent mermaid@11 jsdom",
              file=sys.stderr)
        sys.exit(2)

    blocks = []  # (元ファイル, 通し番号, 中身)
    for path in targets:
        src = open(path, encoding="utf-8").read()
        for i, b in enumerate(re.findall(r"```mermaid\n(.*?)```", src, re.S), 1):
            blocks.append((os.path.relpath(path, ROOT), i, b))

    if not blocks:
        print("mermaid ブロックはありません。")
        return

    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for path, i, body in blocks:
            name = os.path.join(tmp, f"{path.replace('/', '_')}__{i}.mmd")
            open(name, "w", encoding="utf-8").write(body)
            files.append(name)
        r = subprocess.run(["node", CHECKER, *files], capture_output=True, text=True,
                           cwd=os.path.join(ROOT, "tools/mermaid_check"))
        print(r.stdout.rstrip() or r.stderr.rstrip())
        print(f"\n  mermaid 図 {len(blocks)} 個を検査")
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
