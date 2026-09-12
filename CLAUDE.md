# このリポジトリで作業するときの約束

## 週次報告（docs/reports/）

教授に提出する週次報告は **Markdown が唯一の原本**で，そこから pandoc + Typst で
PDF を組む。Word は使わない。

- 新しい報告は `docs/reports/TEMPLATE.md` を写して
  `docs/reports/weekly_report_YYYYMMDD.md` として作る。
- 書き方の約束（フロントマター・LaTeX数式・表の列幅・図）は
  **`docs/reports/README.md` を必ず読んでから編集する**。
- 数式をコードブロックや Unicode の下付き文字（`k₁`）で代用しない。`$...$` /
  `$$...$$` で書く。
- 章番号は手で打たない。番号つきの並びは `1.`，小見出しは `###` と，記法どおりに
  書く（行頭の `1 ` や太字段落で代用しない）。
- 体裁は Typst Universe の `js` パッケージ（jsarticle 相当）に任せている。
  独自の装飾を足さない。変更が要るときは `docs/reports/template.typ` の
  `js.with(...)` の引数で行い，理由をコメントに残す。
- ビルドは `make report-latest`，確認は `make report-live`。

## 実験を回すとき

**設計を書いたら，回す前に必ず見直す。** 1回書いて終わりにしない。
見直しの手順は [`docs/experiments.md`](docs/experiments.md) の
「新しい実験を設計したら，回す前に見直す」にあるチェックリストを使う
（評価件数・基準線・鍵の本数・1条件1run・予算が測定値に混ざっていないか，など）。
これらはすべて実際に失敗して得た規則なので，順に当てるだけで穴が見つかる。

- **GPU を回す前に必ず確認を取る。**
- 長時間のバッチは `nohup ... & disown` で切り離す。
- **走行中のスクリプトは編集しない。** bash はバイト位置で逐次読むため，
  行を足すと実行位置がずれて別の箇所が再実行される（2026-09-12 に実際に起きた）。
- 疎通確認は `HCP_DRY_RUN=1 bash experiments/batch/<名前>.sh`（GPU を掴まない）。

## コミットメッセージ

Conventional Commits 形式（`feat:` / `fix:` / `docs:` など）を使う。

## その他

- ドキュメントの索引は [`docs/README.md`](docs/README.md)。迷ったらまずここ。
- 「実験N」が何を指すかは [`docs/experiments.md`](docs/experiments.md)。
  `Stage 0〜3`（プロンプトで何を開示するか）とは別物なので混同しない。
- 運用コマンドは `make help` で一覧できる。
