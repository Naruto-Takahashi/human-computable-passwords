# ドキュメントの索引

> ここが **docs/ の入口**。各ドキュメントは冒頭に索引への戻りリンク、
> 末尾に「次に読む」を持っているので、どこからでも回遊できる。

> [!TIP]
> **初めて読むなら** [研究計画](plan.md) → [HCP の前提知識](hcp_background.md) → [実験の一覧](experiment_index.md)
>
> **いま何が起きているかを知りたいなら** [実験の一覧](experiment_index.md)（結論が生きているか）と [日誌](log.md)（新しい順）

---

## 研究の内容

| | |
|---|---|
| [authentication_background.md](authentication_background.md) | **認証とは何か** — 3分類・パスワード認証の限界・チャレンジレスポンス・Passkey。卒論 第2章の素材（出典は未確定） |
| [hcp_background.md](hcp_background.md) | **HCP とは何か** — 記号（σ・C・Z）・関数族 $f_{k_1,k_2}$・安全性パラメータ $s(f)$・難易度の分解。**週次報告の「前提知識」節の正本** |
| [literature/lab_theses.md](literature/lab_theses.md) | **研究室の卒論4本** — MLP → LSTM → BiLSTM → CNN → 本研究の系譜。卒論 第3章の素材 |
| [literature/](literature/) | **先行研究の要約** — Blocki ら（原論文）・小川ら・加地ら |

## 計画と記録

| | |
|---|---|
| [plan.md](plan.md) | **研究計画** — 背景・問い・実験設計・評価指標・スケジュール。結果の数値は持たない |
| [experiment_index.md](experiment_index.md) | **実験の一覧** — 実験1〜8の問い・結果・**いまその結論が生きているか**。末尾に方法論の規則8項目 |
| [log.md](log.md) | **日誌** — 実施内容・得られた知見・次にやることを日付ごとに（新しい順） |
| [../results/README.md](../results/README.md) | **結果の置き場と歩き方** — 学習の成果物・評価結果・ログの構造 |

## 実験の道具

| | |
|---|---|
| [llm_training_basics.md](llm_training_basics.md) | **LLM の学習の基礎** — 事前学習・SFT・LoRA・損失・過学習・乱数。**学習の話が出てきたらまずここ** |
| [measurement_audit.md](measurement_audit.md) | **測定系の監査** — 5エポックという予算が測定値を作っていた。検証損失の読み方 |
| [cli_reference.md](cli_reference.md) | **コマンドライン引数** — 既定値が現行の条件と違う点、`--paradigm` の語彙が学習と評価で違う点 |
| [../experiments/batch/README.md](../experiments/batch/README.md) | **バッチの一覧と書き方** — 過去の実験がどのファイルか引ける |

## 成果物

| | |
|---|---|
| [thesis/README.md](thesis/README.md) | **卒論の章立てと素材** — 各章に何を書くか・根拠はどこか・何が足りないか（本文は書かない） |
| [thesis/ch1_contribution.md](thesis/ch1_contribution.md) | **第1章 貢献の主張** — 実験の結果で分岐する下書き |
| [reports/](reports/) | **週次報告** — Markdown が原本。[書き方](reports/README.md)・[雛形](reports/TEMPLATE.md) |

## 開発

| | |
|---|---|
| [refactor_notes.md](refactor_notes.md) | **コードがいまの形になった経緯** — 時期ごとの記録 |
| [../CLAUDE.md](../CLAUDE.md) | **作業の約束** — 実験の回し方・ドキュメントの書き方・コミットメッセージ |
| `../legacy/experiment_guide_20260712.md` | 旧実行ガイド（保存用。参照先の多くが既に存在しない） |

---

🏠 [リポジトリの入口へ戻る](../README.md)
