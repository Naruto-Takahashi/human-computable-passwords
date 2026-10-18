# 検索の記録

> 文献調査で，いつ・どこを・何で検索し，何件見つけたかの記録。関連研究の節で「どう調べたか」を書く根拠
>
> 📚 [ドキュメント索引](../README.md) ／ 関連: [候補論文の一覧](candidates.csv) ・ [関連研究の調査](related_work_survey.md) ・ [文献要約](README.md)

`tools/lit_search.py` を実行すると下の表に1行ずつ自動で足される。手で検索したとき
（Google Scholar・CiNii・指導教員からの紹介など）は，同じ形で手で足す。

| 列 | 中身 |
|---|---|
| 取得 | 検索先が返した件数（重複を含む） |
| 新規 | そのうち [candidates.csv](candidates.csv) に無かった件数 |
| メモ | 手で足した行の補足，検索語を変えた理由など |

> [!NOTE]
> 10/18 の行は，スクリプトを作る前に手で行った検索をさかのぼって記録したもの。
> 件数は当時の出力から写した。

| 日付 | 検索 | 検索先 | 取得 | 新規 | メモ |
|---|---|---|---:|---:|---|
| 2026-10-18 | 被引用: 原論文（arXiv 1404.0024 と2014年版） | Semantic Scholar | 42 | 27 | 版ごとに 13・13・16 件，重複を除いて27件（原論文の別の版を含む）。手作業 |
| 2026-10-18 | 被引用: 原論文 | OpenAlex | 12 | 3 | 新規は Murata ら（WISA 2022）・HIPHCP の解読（ISPEC 2023）・ICETITE 2024。手作業 |
| 2026-10-18 | 語句: "human computable passwords" | OpenAlex | 25 | 3 | LWO（Procedia CS 2023）・HIPHCP（ISPEC 2022）・人間計算 OTP（SEC 2022）。手作業 |
| 2026-10-18 | 語句: "人間計算可能パスワード" / "Human Computable Passwords" | CiNii | 30 | 1 | 櫻井（CSS 2022）。日本語の語では0件。手作業 |
| 2026-10-18 | 語句: 原論文の攻撃・Trenchcoat・疎なチャレンジ・planted CSP | Web 検索（英語） | — | 6 | FPV 2015・Subsampled Power Iteration・Basu ら・Asghar–Kaafar・Rosenfeld ら・Kofoed。手作業 |
| 2026-10-18 | `cites 10.4230/LIPIcs.ITCS.2017.10 --route blocki2017human` | OpenAlex | 11 | 11 | 取れず: Semantic Scholar（回数制限） |
| 2026-10-18 | `cites arxiv:1404.0024 --route blocki2017human` | OpenAlex, Semantic Scholar | 24 | 11 | |
| 2026-10-18 | `cites s2:a479e84f35f3b04f98d99441f5c21270c6798240 --route blocki2017human` | Semantic Scholar | 13 | 0 | |
| 2026-10-18 | `cites s2:c050a907cb8ef3a58c1ab8d495b5ad1e1c4ee6d8 --route blocki2017human` | Semantic Scholar | 16 | 6 |  |
| 2026-10-18 | `add 10.1007/978-3-031-25659-2_22 --route 研究室` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1007/978-981-99-7032-2_21 --route 手で追加` | OpenAlex | 1 | 0 |  |
| 2026-10-18 | `add arxiv:1407.2774 --route Web検索:攻撃の理論` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add arxiv:2507.10833 --route Web検索:攻撃の理論` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1515/jmc-2015-0059 --route Web検索:疎なチャレンジ` | OpenAlex | 1 | 0 |  |
| 2026-10-18 | `add 10.1073/pnas.1801839117 --route Web検索` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1007/978-3-031-21280-2_25 --route 手で追加` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1016/j.procs.2023.10.451 --route 手で追加` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1609/hcomp.v3i1.13233 --route Web検索` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1007/978-3-642-42045-0_19 --route 原論文の系統` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1007/3-540-45682-1_4 --route 参考文献:blocki2017human` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1007/3-540-46416-6_35 --route 手で追加:古典` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1007/978-3-540-85886-7_29 --route Web検索:疎なチャレンジ` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `add 10.1109/sec54971.2022.00034 --route 手で追加` | OpenAlex | 1 | 1 |  |
| 2026-10-18 | `refs 10.1007/978-3-031-25659-2_22 --route murata2023evaluating` | OpenAlex, Semantic Scholar | 10 | 5 | データベース上の参考文献は10件しかなく不完全。題名の頭に「A.:」が付いた重複1件を手で消した。本文の参考文献リストで補う |
