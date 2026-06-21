# 人間計算可能なパスワード（HCP）に基づく<br>推論特化型AIのアルゴリズム推論ベンチマーク

このリポジトリは，  
**人間計算可能なパスワード（Human-Computable Password, HCP）に基づく推論特化型AIのアルゴリズム推論ベンチマーク**  
に関する研究コードおよび研究資料をまとめたものです．

---

## 概要

人間計算可能なパスワード（HCP）とは，ユーザーが記憶している秘密のテーブル（鍵）と，頭の中で実行可能な簡素なアルゴリズムを用いて，提示されたランダムな「チャレンジ」に対する「レスポンス」を暗算で計算し，認証を行う仕組みです．

従来の安全性評価では，チャレンジとレスポンスの組み合わせが流出した際の「従来の機械学習（MLP, LSTM, CNN等）に対する耐性」が主な焦点でした．しかし本研究では，HCPが持つ「人間の暗算で実行できる簡潔さ」と「間接参照（ポインタ）やモジュロ演算（剰余）などの構造的・非線形なアルゴリズム関係」という性質に着目し，**近年の推論特化型AI（o1, o3-mini, Gemini, Claude, Qwen等）の記号論理的・アルゴリズム的推論能力を検証するためのベンチマーク**として再定義し，評価を行います．

---

## ディレクトリ構造

本リポジトリのディレクトリ構成および主要ファイルの説明は以下の通りです．

```text
human-computable-passwords/
├── src/                      # コアライブラリ（再利用可能なロジック）
│   ├── hcp/                  # HCP生成・モデル・ユーティリティ
│   │   ├── generator.py      # HCPデータおよびチャレンジ生成器
│   │   ├── models.py         # 従来の機械学習モデル（MLP, LSTM, CNN）の定義
│   │   └── utils.py          # データ分割，乱数シード固定，可視化ユーティリティ
│   └── llm/                  # LLM推論用モジュール
│       ├── clients.py        # Gemini / Ollama (ローカルLLM) クライアント
│       ├── prompt.py         # Few-shot プロンプト構築ロジック
│       ├── evaluator.py      # 推論結果の評価・パース・記録
│       └── data_generator.py # LLM評価用データセット生成器
├── experiments/              # 実行用スクリプト（実験の入り口）
│   ├── training/             # 従来の機械学習モデルの学習実験
│   │   ├── train.py          # 個別学習実行スクリプト
│   │   ├── batch_run.py      # 複数条件のバッチ学習
│   │   └── summarize.py      # 学習結果の自動集計
│   └── benchmarks/           # LLMベンチマーク評価実験
│       ├── runner.py         # LLM推論実行スクリプト
│       ├── batch_benchmark.py # 全アルゴリズムの一括評価
│       └── summarize.py      # LLM評価結果の自動集計
├── research/                 # 研究資料およびドキュメント
│   ├── previous-works/       # 既存研究の論文PDFおよび卒論スライド等
│   └── log/                  # 研究計画書 (plan.md) および研究ログ (log.md)
├── outputs/                  # 実験結果の出力先ディレクトリ（Git管理対象外）
│   ├── training/             # 学習実験のログ・グラフ・メタデータ
│   ├── benchmarks/           # LLMベンチマークの結果（モデル/手法/アルゴリズム/実行日時の階層構造）
│   ├── summary.md            # 学習実験結果の自動集計表
│   └── summary_llm.md        # LLMベンチマーク結果の自動集計表
├── flake.nix                 # Nix (Flakes) による再現可能なPython開発環境の定義
├── flake.lock                # Nix環境の依存パッケージのバージョンロックファイル
├── .envrc                    # direnv用設定ファイル
├── requirements.txt          # Pythonパッケージの依存関係リスト
└── README.md                 # 本ドキュメント
```

---

## 本研究の意義

1. **「データ汚染（Data Contamination）」からの完全な脱却**: 合成データによる未知の論理推論能力の測定．
2. **人間とAIの「Jagged Frontier」の可視化**: 暗算可能なルールがAIにとってどの程度の障壁になるかを評価．
3. **難易度の厳密な理論的制御**: アルゴリズムの構造を変更することで難易度を段階的に制御．
4. **AIの暗号解読能力の実践的評価**: 既知平文攻撃に対するLLMの耐性を測定．

---

## 実験

### 開発環境の構築

`Nix` (Flakes) と `direnv` を用いて環境を管理しています．

```bash
direnv allow
```

以降，ディレクトリに入るだけで必要なライブラリが自動的に読み込まれます．ローカルLLMの評価には `ollama` が必要です．

### 従来の機械学習モデルの学習

```bash
# 個別モデルの学習
python experiments/training/train.py

# 学習結果の集計
python experiments/training/summarize.py
```

### LLMベンチマーク評価

ローカルLLM（Ollama），Gemini API，または検証用モックを用いた評価が可能です．
詳細な実行手順やパラメータの仕様，トラブルシューティングについては，[LLM ベンチマーク実行ガイド](research/log/BENCHMARK_GUIDE.md) を参照してください．

```bash
# 1. 単発手法の実行
python experiments/benchmarks/runner.py --model gemma2:9b --generator simple_add --rationale --use_code

# 2. オフライン検証用（Mockプロバイダによるドライラン）
python experiments/benchmarks/runner.py --provider mock --model test-mock-model --n_test 5

# 3. 全4パラダイム（手法）の自動比較
python experiments/benchmarks/run_paradigms.py --model gemma2:9b --generator simple_add

# 評価結果の集計（ summary_llm.md の生成）
python experiments/benchmarks/summarize.py
```

- **実験パラダイム**: `pure` (ゼロショット)，`rationale` (ヒントあり)，`pot` (コード実行)，`rationale_pot` (最強構成) の4段階で評価可能．
- **PoT (Program-of-Thought)**: `--use_code` を有効にすると，AIに Python コードを書かせ，それをローカルで実行して答えを得ることで算数ミスを排除します．
- **出力構造**: `outputs/benchmarks/<モデル>/<手法>/<アルゴリズム>/run_<日時>/` に自動整理されます．

---

## ドキュメント・実行結果へのリンク

- [LLM ベンチマーク実行ガイド (`BENCHMARK_GUIDE.md`)](research/log/BENCHMARK_GUIDE.md)
- [研究計画書 (`plan.md`)](research/log/plan.md)
- [研究ログ (`log.md`)](research/log/log.md)
- [学習実験結果のサマリー (`summary.md`)](outputs/summary.md)
- [LLMベンチマーク結果のサマリー (`summary_llm.md`)](outputs/summary_llm.md)
