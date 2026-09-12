# ドキュメントの索引

どれを読めばよいかの地図．**迷ったら「目的別」の表から入る．**

## 目的別

| 知りたいこと | 読むもの |
|---|---|
| この研究は何をしているのか | [plan.md](plan.md)（研究計画書．背景・問い・実験設計・現状） |
| 何をやってきたか，いつ何が分かったか | [log.md](log.md)（日誌．新しい順） |
| 教授に何を報告したか | [reports/](reports/)（週次報告．Markdown が原本） |
| 実験の回し方 | [../README.md](../README.md)，`make help` |
| 引数の意味と既定値 | [parameters.md](parameters.md) |
| QLoRA・LoRA・SFT とは何か（学習の仕組みそのもの） | [finetuning_basics.md](finetuning_basics.md) |
| 学習率・エポック数とは何か／なぜ5エポックが問題だったか | [training_dynamics.md](training_dynamics.md) |
| 過去のバッチ実験の一覧・新しい書き方 | [../experiments/batch/README.md](../experiments/batch/README.md) |
| 結果がどこに保存されるか | [../results/README.md](../results/README.md) |
| 先行研究の要約 | [literature/](literature/) |
| コードがいまの形になった経緯 | [refactor_notes.md](refactor_notes.md) |

## 一覧

### 研究の記録

- **[plan.md](plan.md)** — 研究計画書（v2）．問い・実験設計・スケジュール．
  実験で何かが分かったらここに反映する．§3.1.2 に測定系の監査（2026-09-12）と，
  それによって修正された過去の主張がまとまっている．
- **[log.md](log.md)** — 日誌．実施内容・得られた知見・次にやることを日付ごとに．
  新しいものを**上**に足す．
- **[reports/](reports/)** — 週次報告．書き方の約束は
  [reports/README.md](reports/README.md)，雛形は [reports/TEMPLATE.md](reports/TEMPLATE.md)．
  `make report-latest` で PDF 化，`make report-live` でプレビュー．

### 手引き

- **[finetuning_basics.md](finetuning_basics.md)** — QLoRA によるファインチューニングの
  仕組み．4bit 量子化と LoRA が何をしているか，損失とは何か，乱数が効く3箇所
  （初期化・並び順・ドロップアウト），再現性と GPU の非決定性．数字はすべて
  このリポジトリの実測値．**学習の話が出てきたらまずここ．**
- **[parameters.md](parameters.md)** — `train_finetuning.py` / `run_eval.py` の引数．
  既定値が現行の実験条件と違う点や，`--paradigm` の語彙が学習と評価で違う点など，
  つまずきやすい箇所を先頭にまとめてある．
- **[training_dynamics.md](training_dynamics.md)** — 学習率とエポック数の前提知識と，
  「5エポックという予算そのものが測定器になっていた」という監査結果．
  検証損失の読み方（離陸したかどうか）もここ．

### 背景

- **[literature/](literature/)** — 先行研究の要約．Blum ら（原論文），小川ら，可知ら．
- **[refactor_notes.md](refactor_notes.md)** — 2026-07 の監査とリファクタリングの記録
  （アルゴリズム定義の単一情報源化，PoT の鍵リーク修正など）．

### 保存用

- `legacy/experiment_guide_20260712.md` — 旧実行ガイド．参照しているファイルの多くが
  既に存在しない．現行の手順は上記を見ること．

## 書くときの約束

- 週次報告は **Markdown が唯一の原本**．Word は使わない．体裁の約束は
  [reports/README.md](reports/README.md) を読んでから編集する（章番号を手で打たない，
  数式は `$...$` で書く，など）．
- 実験で分かったことは **log.md に日付つきで**書き，結論が変わるものは **plan.md にも
  反映する**．過去の記述を消すのではなく，「いつ何が分かって，どの主張がどう変わったか」
  が追える形にする．
