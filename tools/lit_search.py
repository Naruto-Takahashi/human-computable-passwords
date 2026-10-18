#!/usr/bin/env python3
"""論文を検索して，候補一覧 docs/literature/candidates.csv に追記する．

文献調査の3方向（被引用・参考文献・語句検索）を1コマンドで回し，結果を
DOI・arXiv ID・題名で重複を除いてから「未読」として追記する。既存の行は
書き換えない（状態や関連度は人が付けるため）。実行のたびに
docs/literature/search_log.md に1行残す。

    python3 tools/lit_search.py cites  10.4230/LIPIcs.ITCS.2017.10   # 引用している論文
    python3 tools/lit_search.py refs   10.1007/978-3-031-25659-2_22  # 参考文献
    python3 tools/lit_search.py search "human identification protocol"
    python3 tools/lit_search.py add    10.1007/978-3-030-65411-5_9   # 1本だけ足す

識別子は DOI，`arxiv:1404.0024`，`openalex:W2964003456`，`s2:<paperId>` のどれでもよい。
同じ論文が版ごとに別の項目になっていることがある（原論文は arXiv 版・ITCS 版・
2014年の "Human Computable Passwords" 版）。被引用を集めるときは全部の版で回す。
`--dry-run` を付けると，追記する予定の行を表示するだけで何も書かない。

検索先: OpenAlex（主），Semantic Scholar（環境変数 S2_API_KEY があれば常に，
無ければ回数制限に当たった時点で諦める），DBLP と arXiv（search のみ）。
どのデータベースも被引用の網羅率は Google Scholar より低い。Google Scholar は
API が無いので手で確かめること。
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIT = os.path.join(ROOT, "docs", "literature")
CANDIDATES = os.path.join(LIT, "candidates.csv")
SEARCH_LOG = os.path.join(LIT, "search_log.md")

FIELDS = ["key", "year", "title", "authors", "venue", "doi", "arxiv",
          "route", "status", "relevance", "note"]
# OpenAlex は連絡先を付けた要求を優先的に通す。付けたいときは環境変数で渡す
UA = "hcp-lit-search/1.0" + (f" (mailto:{os.environ['HCP_MAILTO']})" if os.environ.get("HCP_MAILTO") else "")
# 引用キーは「第1著者の姓＋年＋題名の最初の中身のある語」。台帳の中で論文を指す名前で，
# Zotero の引用キーと揃えるかは Better BibTeX の設定で決める
STOPWORDS = {"a", "an", "the", "on", "of", "in", "for", "to", "and", "with",
             "towards", "toward", "via", "is", "are", "when", "what", "how"}


# ---------------------------------------------------------------------------
# 正規化と重複除去（ネットワークに依存しない。tests/check_lit_search.py が検査する）
# ---------------------------------------------------------------------------

def ascii_fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def norm_doi(doi: str) -> str:
    doi = (doi or "").strip().lower()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi)


def norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", ascii_fold(title or "").lower())


def make_key(first_author: str, year, title: str) -> str:
    """blocki2017human のような引用キー"""
    last = ascii_fold(first_author or "anon").split()[-1] if first_author else "anon"
    last = re.sub(r"[^a-z]", "", last.lower()) or "anon"
    words = [w for w in re.findall(r"[a-z0-9]+", ascii_fold(title or "").lower())
             if w not in STOPWORDS]
    return f"{last}{year or ''}{words[0] if words else ''}"


def identities(row: dict) -> set:
    ids = set()
    if row.get("doi"):
        ids.add("doi:" + norm_doi(row["doi"]))
    if row.get("arxiv"):
        ids.add("arxiv:" + row["arxiv"].lower())
    if row.get("title"):
        ids.add("title:" + norm_title(row["title"]))
    return ids


def merge_new(existing: list, found: list) -> list:
    """existing に無い行だけを返す。found の中の重複もまとめる"""
    seen = set()
    for r in existing:
        seen |= identities(r)
    new = []
    for r in found:
        ids = identities(r)
        if ids & seen:
            continue
        seen |= ids
        new.append(r)
    return new


def unique_keys(existing: list, new: list) -> None:
    """引用キーが衝突したら a, b, ... を付ける"""
    used = {r["key"] for r in existing}
    for r in new:
        base, k, i = r["key"], r["key"], 0
        while k in used:
            k = base + "abcdefghijklmnopqrstuvwxyz"[i]
            i += 1
        r["key"] = k
        used.add(k)


# ---------------------------------------------------------------------------
# ファイル
# ---------------------------------------------------------------------------

def read_candidates(path=CANDIDATES) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def append_candidates(rows: list, path=CANDIDATES) -> None:
    fresh = not os.path.exists(path)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if fresh:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def append_log(command: str, sources: str, hits: int, new: int, note: str = "",
               path=SEARCH_LOG) -> None:
    today = datetime.date.today().isoformat()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"| {today} | `{command}` | {sources} | {hits} | {new} | {note} |\n")


# ---------------------------------------------------------------------------
# 通信
# ---------------------------------------------------------------------------

def get(url: str, params=None, headers=None, tries=4):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 and i < tries - 1:
                time.sleep(5 * (i + 1))
                continue
            raise
    return None


class RateLimited(Exception):
    pass


# --- OpenAlex ---------------------------------------------------------------

OA = "https://api.openalex.org"
OA_SELECT = "id,doi,title,publication_year,authorships,primary_location,ids"


def oa_row(w: dict, route: str) -> dict:
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    authors = [a["author"]["display_name"] for a in w.get("authorships") or []]
    arxiv = ""
    for loc in [w.get("primary_location") or {}] + (w.get("locations") or []):
        m = re.search(r"arxiv\.org/abs/([\d.]+)", (loc or {}).get("landing_page_url") or "")
        if m:
            arxiv = m.group(1)
    doi = norm_doi(w.get("doi") or "")
    if doi.startswith("10.48550/arxiv."):
        arxiv, doi = arxiv or doi.split("arxiv.")[1], ""
    return {"key": make_key(authors[0] if authors else "", w.get("publication_year"), w.get("title")),
            "year": w.get("publication_year") or "", "title": w.get("title") or "",
            "authors": "; ".join(authors[:6]) + ("; ..." if len(authors) > 6 else ""),
            "venue": src, "doi": doi, "arxiv": arxiv, "route": route, "status": "未読"}


def oa_work(ident: str):
    if ident.startswith("s2:"):
        return None
    if ident.startswith("openalex:"):
        path = ident.split(":", 1)[1]
    elif ident.startswith("arxiv:"):
        path = "doi:10.48550/arXiv." + ident.split(":", 1)[1]
    else:
        path = "doi:" + norm_doi(ident)
    body = get(f"{OA}/works/{path}")
    return json.loads(body) if body else None


def oa_list(filt: str, route: str) -> list:
    rows, cursor = [], "*"
    while cursor:
        d = json.loads(get(f"{OA}/works", {"filter": filt, "per-page": 200,
                                          "cursor": cursor, "select": OA_SELECT}))
        rows += [oa_row(w, route) for w in d["results"]]
        cursor = d["meta"].get("next_cursor") if d["results"] else None
    return rows


def oa_search(q: str, route: str, n=100) -> list:
    d = json.loads(get(f"{OA}/works", {"search": q, "per-page": n, "select": OA_SELECT}))
    return [oa_row(w, route) for w in d["results"]]


# --- Semantic Scholar --------------------------------------------------------

S2 = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,year,venue,authors,externalIds"


def s2_get(path: str, params: dict):
    key = os.environ.get("S2_API_KEY")
    try:
        body = get(S2 + path, params, {"x-api-key": key} if key else None, tries=4 if key else 2)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimited from e
        raise
    return json.loads(body) if body else None


def s2_row(p: dict, route: str) -> dict:
    ext = p.get("externalIds") or {}
    authors = [a["name"] for a in p.get("authors") or []]
    return {"key": make_key(authors[0] if authors else "", p.get("year"), p.get("title")),
            "year": p.get("year") or "", "title": p.get("title") or "",
            "authors": "; ".join(authors[:6]) + ("; ..." if len(authors) > 6 else ""),
            "venue": p.get("venue") or "", "doi": norm_doi(ext.get("DOI") or ""),
            "arxiv": ext.get("ArXiv") or "", "route": route, "status": "未読"}


def s2_ident(ident: str) -> str:
    if ident.startswith("arxiv:"):
        return "arXiv:" + ident.split(":", 1)[1]
    if ident.startswith("s2:"):
        return ident.split(":", 1)[1]
    if ident.startswith("openalex:"):
        return ""
    return "DOI:" + norm_doi(ident)


def s2_links(ident: str, kind: str, route: str) -> list:
    """kind は citations（引用している側）か references（参考文献）"""
    sid = s2_ident(ident)
    if not sid:
        return []
    d = s2_get(f"/paper/{sid}/{kind}", {"fields": S2_FIELDS, "limit": 1000})
    side = "citingPaper" if kind == "citations" else "citedPaper"
    return [s2_row(x[side], route) for x in (d or {}).get("data") or [] if x.get(side, {}).get("title")]


# --- DBLP / arXiv（語句検索のみ） --------------------------------------------

def dblp_search(q: str, route: str, n=100) -> list:
    d = json.loads(get("https://dblp.org/search/publ/api", {"q": q, "format": "json", "h": n}))
    rows = []
    for h in (d["result"]["hits"].get("hit") or []):
        info = h["info"]
        a = (info.get("authors") or {}).get("author") or []
        a = [x["text"] if isinstance(x, dict) else x for x in (a if isinstance(a, list) else [a])]
        title = re.sub(r"\.$", "", info.get("title", ""))
        rows.append({"key": make_key(a[0] if a else "", info.get("year"), title),
                     "year": info.get("year", ""), "title": title,
                     "authors": "; ".join(a[:6]), "venue": info.get("venue", ""),
                     "doi": norm_doi(info.get("doi", "")), "arxiv": "", "route": route,
                     "status": "未読"})
    return rows


def arxiv_search(q: str, route: str, n=100) -> list:
    body = get("https://export.arxiv.org/api/query",
               {"search_query": f'all:"{q}"', "max_results": n})
    ns = {"a": "http://www.w3.org/2005/Atom"}
    rows = []
    for e in ET.fromstring(body).findall("a:entry", ns):
        title = " ".join(e.findtext("a:title", "", ns).split())
        a = [x.findtext("a:name", "", ns) for x in e.findall("a:author", ns)]
        aid = re.sub(r"v\d+$", "", e.findtext("a:id", "", ns).rsplit("/", 1)[-1])
        year = e.findtext("a:published", "", ns)[:4]
        rows.append({"key": make_key(a[0] if a else "", year, title), "year": year,
                     "title": title, "authors": "; ".join(a[:6]), "venue": "arXiv",
                     "doi": "", "arxiv": aid, "route": route, "status": "未読"})
    return rows


# ---------------------------------------------------------------------------

def collect(args) -> tuple[list, list, list]:
    """(見つかった行, 使えた検索先, 失敗した検索先) を返す"""
    found, used, failed = [], [], []
    if args.cmd in ("cites", "refs", "add"):
        w = oa_work(args.target)
        if args.cmd == "add":
            if not w:
                sys.exit(f"OpenAlex に見つからない: {args.target}")
            return [oa_row(w, args.route or "手で追加")], ["OpenAlex"], []
        if args.route:
            seed = args.route
        elif w:
            a = w.get("authorships") or []
            seed = make_key(a[0]["author"]["display_name"] if a else "", w.get("publication_year"), w.get("title"))
        else:
            seed = args.target
        route = f"{'被引用' if args.cmd == 'cites' else '参考文献'}:{seed}"
        if w:
            oid = w["id"].rsplit("/", 1)[-1]
            if args.cmd == "cites":
                found += oa_list(f"cites:{oid}", route)
            else:
                refs = [r.rsplit("/", 1)[-1] for r in w.get("referenced_works") or []]
                for i in range(0, len(refs), 50):
                    found += oa_list("openalex_id:" + "|".join(refs[i:i + 50]), route)
            used.append("OpenAlex")
        try:
            found += s2_links(args.target, "citations" if args.cmd == "cites" else "references", route)
            used.append("Semantic Scholar")
        except RateLimited:
            failed.append("Semantic Scholar（回数制限）")
            print("Semantic Scholar は回数制限で取れなかった（S2_API_KEY を設定すると避けられる）",
                  file=sys.stderr)
    else:
        route = f"語句:{args.target}"
        for name, fn in [("OpenAlex", oa_search), ("DBLP", dblp_search), ("arXiv", arxiv_search)]:
            try:
                found += fn(args.target, route)
                used.append(name)
            except (urllib.error.URLError, ET.ParseError, KeyError) as e:
                failed.append(name)
                print(f"{name} で失敗: {e}", file=sys.stderr)
    return found, used, failed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["cites", "refs", "search", "add"])
    ap.add_argument("target", help="DOI / arxiv:ID / openalex:W... / s2:ID / 検索語")
    ap.add_argument("--route", help="見つけた経路の名前（既定は種の論文の引用キー）")
    ap.add_argument("--dry-run", action="store_true", help="表示するだけで書かない")
    args = ap.parse_args()

    found, used, failed = collect(args)
    if not used:
        sys.exit("どの検索先からも取れなかったので記録しない（時間をおいてやり直す）")
    existing = read_candidates()
    new = merge_new(existing, found)
    unique_keys(existing, new)
    for r in new:
        print(f"  + {r['year']} {r['title'][:80]}  [{r['venue'][:30]}]")
    print(f"{len(found)} 件取得 / 新規 {len(new)} 件（{', '.join(used)}）")
    if args.dry_run:
        print("--dry-run のため書き込まない")
        return
    append_candidates(new)
    cmd = f"{args.cmd} {args.target}" + (f" --route {args.route}" if args.route else "")
    append_log(cmd, ", ".join(used), len(found), len(new),
               "取れず: " + "・".join(failed) if failed else "")


if __name__ == "__main__":
    main()
