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

## コミットメッセージ

Conventional Commits 形式（`feat:` / `fix:` / `docs:` など）を使う。

## その他

- 実験の回し方は `docs/experiment_guide.md`，設計の経緯は `docs/refactor_notes.md`，
  計画は `docs/plan.md` にある。
- 運用コマンドは `make help` で一覧できる。
