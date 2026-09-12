# このリポジトリで作業するときの約束

**運用ルールの正本。** 他のドキュメントはここを参照するだけにして，同じルールを
二度書かない。

- 研究の概要・現状 → [README.md](README.md)
- ドキュメントの索引 → [docs/README.md](docs/README.md)

---

## 実験を回すとき

**設計を書いたら，回す前に必ず見直す。** 1回書いて終わりにしない。
チェックリストは [docs/experiment_index.md](docs/experiment_index.md) の
「新しい実験を設計したら，回す前に見直す」にある（評価件数・基準線・鍵の本数・
1条件1run・予算が測定値に混ざっていないか）。すべて実際に失敗して得た規則なので，
順に当てるだけで穴が見つかる。

| | |
|---|---|
| **GPU を回す前に必ず確認を取る** | 長時間かかるため |
| 疎通確認 | `HCP_DRY_RUN=1 bash experiments/batch/<名前>.sh`（GPU を掴まない） |
| 本番 | `nohup bash experiments/batch/<名前>.sh > results/logs/<名前>.out 2>&1 & disown` |
| 進捗 | `make status` |

> [!WARNING]
> **走行中のスクリプトは編集しない。** bash はバイト位置で逐次読むため，行を足すと
> 実行位置がずれて別の箇所が再実行される（2026-09-12 に実際に発生し，同じ条件を
> 2回学習した）。直したいときはバッチの終了を待つ。

新しいバッチの書き方 → [experiments/batch/README.md](experiments/batch/README.md)

---

## ドキュメントを書くとき

| | |
|---|---|
| 冒頭 | 一言でいうと何の文書か ＋ 📚 索引への戻りリンク ＋ 関連文書 |
| 目次 | 150行を超え，見出しが4つ以上あるなら付ける |
| 末尾 | 「次に読む」を置いて読者を次の文書へ送る |
| 注記 | 読み飛ばすと事故になるものは GitHub のアラート（`> [!IMPORTANT]` 等）に |
| 図 | 関係・流れ・分岐は mermaid，値・判定・対比は表。迷ったら表。1ページ1枚まで |
| 数式 | 下記の「数式の書き方」に従う |

mermaid を書いたら `make check-mermaid` で構文を確かめる（誤ると GitHub 上で
図の代わりにエラーが出る）。

### 数式の書き方

GitHub の markdown は数式の中身にも手を入れるため，素直に書くと崩れる。
`make test` に検査が入っているので，迷ったら書いてから走らせる。

| | 書き方 | 理由 |
|---|---|---|
| インライン | **`` $`x_1`$ ``** | 素の書き方だと `_` が強調記法として食われ，下付き文字が消える |
| ブロック | **`$$` を単独行に置く** | 同じ行に式を詰めるとインライン扱いになり `\left` の対応が壊れる |
| 波括弧 | **`\lbrace` `\rbrace`** | `\{` は markdown のエスケープとして食われ `{` になる |
| 不等号 | **`\lt` `\gt`** | `<` は HTML タグの開始と解釈される |
| 下付き | Unicode（`k₁`）で代用しない | |

**週次報告は別。** pandoc + Typst を通すので，素の `$...$` と `\{` のままでよい。
[docs/hcp_background.md](docs/hcp_background.md) を報告書へ写すときは，
上記の書き方を元に戻すこと。

**同じ情報を2箇所に置かない。** 役割を分ける。

| 書くもの | 置き場 |
|---|---|
| 実験の結果・数値 | [docs/experiment_index.md](docs/experiment_index.md) |
| 研究の計画・位置づけ | [docs/plan.md](docs/plan.md) |
| 日々の記録 | [docs/log.md](docs/log.md) |
| 運用ルール | このファイル |

---

## 週次報告（docs/reports/）

**Markdown が唯一の原本。** そこから pandoc + Typst で PDF を組む。Word は使わない。

- 新しい報告は [docs/reports/TEMPLATE.md](docs/reports/TEMPLATE.md) を写して
  `weekly_report_YYYYMMDD.md` として作る
- **「前提知識」節は手で書き直さず，[docs/hcp_background.md](docs/hcp_background.md)
  から写す**（正本）
- 体裁の約束（フロントマター・表・図）は
  **[docs/reports/README.md](docs/reports/README.md) を読んでから編集する**
- 章番号は手で打たない。`1.` と `###` を記法どおりに使う
- 体裁は Typst の `js` パッケージに任せ，独自の装飾を足さない。変更が要るときは
  `docs/reports/template.typ` の `js.with(...)` で行い，理由をコメントに残す
- ビルドは `make report-latest`，確認は `make report-live`

---

## コミットメッセージ

Conventional Commits 形式（`feat:` / `fix:` / `docs:` など）を使う。
