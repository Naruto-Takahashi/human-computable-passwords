# 人間計算可能パスワード (HCP) に基づく LLM の限界評価ベンチマーク

九州大学 工学部 電気情報工学科 櫻井研究室 / 卒業研究（令和8年度）

---

## まず読む

| | |
|---|---|
| [docs/README.md](docs/README.md) | **ドキュメントの索引**（目的別） |
| [docs/plan.md](docs/plan.md) | 研究計画書 — 背景・問い・実験設計・スケジュール |
| [docs/experiments.md](docs/experiments.md) | 実験の一覧 — 各実験の問い・結果・**いまその結論は生きているか** |

## 研究の内容

| | |
|---|---|
| [docs/authentication_background.md](docs/authentication_background.md) | 認証とは — 3分類・パスワード認証の限界・チャレンジレスポンス認証 |
| [docs/hcp_background.md](docs/hcp_background.md) | HCP とは — 記号（σ・C・Z）・関数族 $f_{k_1,k_2}$・安全性パラメータ $s(f)$ |
| [docs/literature/](docs/literature/) | 先行研究の要約 |
| [docs/literature/lab_theses.md](docs/literature/lab_theses.md) | 研究室の卒論4本 — MLP → LSTM → BiLSTM → CNN → 本研究 |

## 実験の道具

| | |
|---|---|
| [docs/llm_training_basics.md](docs/llm_training_basics.md) | LLM の学習の基礎 — 事前学習・SFT・LoRA・損失・過学習・乱数 |
| [docs/training_dynamics.md](docs/training_dynamics.md) | 学習率とエポック数 — なぜ固定予算が測定器になるのか |
| [docs/parameters.md](docs/parameters.md) | 実験パラメータの手引き — 既定値の落とし穴 |

## 実験の記録

| | |
|---|---|
| [docs/log.md](docs/log.md) | 日誌（新しい順） |
| [results/README.md](results/README.md) | 結果の置き場と歩き方 |
| [results/inventory.md](results/inventory.md) | 学習 run の棚卸し（`make inventory`） |
| [results/summary_llm.md](results/summary_llm.md) | 評価結果の集計（`make summarize`） |
| [experiments/batch/README.md](experiments/batch/README.md) | バッチスクリプトの一覧と書き方 |

## 卒業論文

| | |
|---|---|
| [docs/thesis/README.md](docs/thesis/README.md) | 章立てと素材の対応表（**本文は書かない**） |
| [docs/thesis/ch1_contribution.md](docs/thesis/ch1_contribution.md) | 第1章 貢献の主張（下書き） |
| [docs/reports/](docs/reports/) | 週次報告（Markdown が原本） |
| [docs/reports/README.md](docs/reports/README.md) | 報告書の書き方 |

## 動かす

| | |
|---|---|
| `make help` | コマンド一覧 |
| `make status` | 走行中バッチと進捗 |
| `make test` | アルゴリズム自己検証＋文面の非退行検査 |
| [CLAUDE.md](CLAUDE.md) | このリポジトリで作業するときの約束 |
| [docs/refactor_notes.md](docs/refactor_notes.md) | コードがいまの形になった経緯（2026-07） |

## 構成

```
src/hcp/          研究の中核（algorithms.py が全アルゴリズム定義の単一情報源）
src/baseline_ml/  従来ML（CNN等）ベースライン
experiments/      実験スクリプト（batch/ に夜間バッチ）
tools/            補助ツール（status / list_algorithms / read_pdf / migrate）
tests/            文面の非退行検査
docs/             ドキュメント（索引: docs/README.md）
results/          実験結果（歩き方: results/README.md）
literature/       先行研究の PDF（Git 管理外．実体は Google Drive）
legacy/           旧実装（参照用，動作保証なし）
```
