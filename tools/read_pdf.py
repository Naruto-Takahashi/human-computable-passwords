#!/usr/bin/env python3
"""
日本語 PDF からテキストを取り出す（研究室の過去の卒論を読むため）．

`literature/` の卒論 PDF は dvipdfmx 製で ToUnicode CMap を持たないものがあり
（R4 村田・R5 丸野），pypdf では1文字も読めない．pdfminer.six は Adobe-Japan1 の
CMap を内蔵しているため，こちらなら復号できる．

    python3 tools/read_pdf.py literature/R4_村田.pdf              # 全文
    python3 tools/read_pdf.py literature/R4_村田.pdf 10 14        # 10〜14ページ
    python3 tools/read_pdf.py literature/R4_村田.pdf --toc        # 目次だけ
"""
import re
import sys

from pdfminer.high_level import extract_text
from pdfminer.pdfpage import PDFPage


def page_count(path: str) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in PDFPage.get_pages(f))


def print_toc(path: str, scan: int = 6) -> None:
    pat = re.compile(r"^(第\s*\d+\s*章|\d+(\.\d+)*\s+\S)")
    for pg in range(scan):
        text = extract_text(path, page_numbers=[pg])
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        hits = [re.sub(r"\s*[.．]{3,}.*$", "", l) for l in lines if pat.match(l)]
        if len(hits) >= 3:
            for h in hits:
                print(" ", h[:70])
            return
    print("目次らしいページが見つかりませんでした。ページ範囲を指定して読んでください。")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    if "--toc" in sys.argv:
        print(f"# {path}（{page_count(path)} ページ）")
        print_toc(path)
        return
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    last = int(sys.argv[3]) if len(sys.argv) > 3 else page_count(path)
    for i in range(first - 1, last):
        print(f"\n----- p.{i + 1} -----")
        print(extract_text(path, page_numbers=[i]).strip())


if __name__ == "__main__":
    main()
