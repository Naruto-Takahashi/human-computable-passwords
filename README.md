# 人間計算可能パスワード (HCP) に基づく LLM のルール実行（演繹）およびルール逆推定（帰納）の限界評価ベンチマーク

このリポジトリは，  
**人間計算可能パスワード（Human-Computable Password，HCP）に基づく LLM のルール実行（演繹）およびルール逆推定（帰納）の限界評価ベンチマーク**  
に関する研究コードおよび研究資料をまとめたものです．

---

## 概要

人間計算可能パスワード（HCP）とは，ユーザーが記憶している秘密のテーブル（鍵）と，頭の中で実行可能な簡素なアルゴリズムを用いて，提示されたランダムな「チャレンジ」に対する「レスポンス」を暗算で計算し，認証を行う仕組みです．

本研究では，HCPが持つ「人間の暗算で実行できる簡潔さ」と「間接参照（ポインタ）やモジュロ演算（剰余）などの構造的・非線形なアルゴリズム関係」という性質に着目し，**LLMにおける「ルール実行（演繹）およびルール逆推定（帰納）の限界（臨界点）」を定量的に明らかにするためのベンチマーク**として再定義しました．

予備実験において，ローカルLLM単体では入出力ペアのみから背後にあるルールを完全逆推定することはほぼ不可能であることが示されました．本ベンチマークでは，完全に不可能なブラックボックス状態から出発し，プロンプトへ提示する情報（アルゴリズム仕様や鍵の部分開示数 $K$）を段階的に変化（Stage 0〜3）させていくことで，**AIの推論（ルール実行・ルール逆推定）が「崩壊」から「成功」へと転移する境界（相転移境界）**を数理的・実証的に特定・スキャンします．

また，実験結果のログは，LLMの思考過程と解答の成否を明確に追跡できるよう，大文字のステータスを用いた連番形式（例：`001_CORRECT.md`，`002_INCORRECT.md`）で詳細に記録されます．

---

## ディレクトリ構造

本リポジトリのディレクトリ構成および主要ファイルの説明は以下の通りです．

```text
human-computable-passwords/
├── code/                      # システムのソースコード
│   ├── core/                  # HCPコアモジュール
│   │   ├── generator.py       # HCPデータおよびチャレンジ生成器
│   │   ├── models.py          # 従来の機械学習モデル（MLP，LSTM，CNN）の定義
│   │   └── utils.py           # データ分割，乱数シード固定，可視化ユーティリティ
│   ├── llm_agent/             # LLM推論用モジュール
│   │   ├── clients.py         # Gemini / Ollama / Mock クライアント
│   │   ├── prompt.py          # Few-shot プロンプト構築ロジック
│   │   ├── evaluator.py       # 推論結果の評価・パース・記録（連番ステータスログの生成等）
│   │   ├── code_executor.py   # PoT方式用の Python コード実行器
│   │   └── data_generator.py  # LLM評価用データセット生成器
│   └── scripts/               # 実験用の実行エントリースクリプト群
│       ├── run_benchmark.py   # LLMベンチマーク実行スクリプト
│       ├── run_paradigms.py   # 複数パラダイム（手法）の自動比較実行スクリプト
│       ├── batch_eval.py      # 全アルゴリズムの一括評価実行
│       ├── summarize_llm.py   # LLM評価結果の自動集計
│       ├── train_baseline.py  # 従来の機械学習モデルの個別学習
│       ├── batch_train.py     # 複数条件のバッチ学習
│       └── summarize_baseline.py # 学習結果の自動集計
├── docs/                      # 計画書・ログ・実行手順書
│   ├── plan.md                # 研究計画書
│   ├── log.md                 # 研究開発ログ
│   ├── benchmark_guide.md     # 実験手順ガイド
│   └── ultimate_showdown_prompt.md # プロンプト検証用メモ
├── literature/                # 先行研究の文献（論文PDF，卒論スライド，学会スライド等）
│   ├── Towards Human Computable Passwords.pdf
│   ├── R7_小川.pdf
│   ├── R6_池田.pdf
│   └── ...
├── results/                   # 実験結果の出力先（Git管理対象外，summaryのみコミット対象）
│   ├── benchmarks/            # LLMベンチマーク結果データ（モデル/手法/アルゴリズム/実行日時の階層）
│   ├── baselines/             # 機械学習モデルの学習ログ・グラフ・メタデータ
│   ├── summary.md             # 機械学習実験結果の自動集計表
│   └── summary_llm.md         # LLMベンチマーク結果の自動集計表
├── flake.nix                  # Nix (Flakes) による再現可能なPython開発環境の定義
├── flake.lock                 # Nix環境の依存パッケージのバージョンロックファイル
├── .envrc                     # direnv用設定ファイル
├── requirements.txt           # Pythonパッケージの依存関係リスト
└── README.md                  # 本ドキュメント
```

---

## 本研究の意義

1. **「データ汚染（Data Contamination）」からの完全な脱却**:  
   独自のアルゴリズムと乱数シードから無限に未知の入出力パターンを合成可能なため，LLMが丸暗記している懸念のない純粋な「インコンテキスト推論能力（ルールの実行と逆推定）」を測定できます．
2. **推論能力が崩壊する「相転移境界（臨界点）」の特定**:  
   秘密鍵の部分開示（$K$ マス公開）などを段階的にスキャンし，AIが「崩壊」から「解読（復元）」へと移行する推論能力の限界値を境界探索できます．
3. **AIの暗号解読能力（Cryptanalysis）の実践的評価**:  
   流出した認証データから背後の秘密ルールやテーブルを再構築させる行為は，一種の「既知平文攻撃」であり，AIの敵対的耐性やセキュリティリスクを評価する指標となります．
4. **従来の機械学習との「データ効率性」の対比**:  
   数万 of データを用いた「教師あり学習」によって近似的に関数を再現する従来の機械学習に対し，僅かな Few-shot から論理構造を理解しようとするLLMの推論バイアスの違いを測定します．

---

## 実験

### 開発環境の構築

`Nix` (Flakes) と `direnv` を用いて環境を管理しています．

```bash
direnv allow
```

以降，ディレクトリに入るだけで必要なライブラリが自動的に読み込まれます．

### 従来の機械学習モデルの学習

```bash
# 個別モデルの学習
python code/scripts/train_baseline.py

# 学習結果の集計
python code/scripts/summarize_baseline.py
```

### LLMベンチマーク評価

ローカルLLM（Ollama），Gemini API，または検証用モックを用いた評価が可能です．
詳細な実行手順やパラメータの仕様，トラブルシューティングについては，[LLM ベンチマーク実行ガイド](docs/benchmark_guide.md) を参照してください．

```bash
# 1. 単発手法の実行
python code/scripts/run_benchmark.py --model gemma2:9b --generator simple_add --rationale --use_code

# 2. オフライン検証用（Mockプロバイダによるドライラン）
python code/scripts/run_benchmark.py --provider mock --model test-mock-model --n_test 5

# 3. 全4パラダイム（手法）の自動比較
python code/scripts/run_paradigms.py --model gemma2:9b --generator simple_add

# 評価結果の集計（ summary_llm.md の生成）
python code/scripts/summarize_llm.py
```

- **実験パラダイム**: `pure`（ゼロショット），`rationale`（ヒントあり），`pot`（コード実行），`rationale_pot`（最強構成）の4段階で評価可能．
- **PoT (Program-of-Thought)**: `--use_code` を有効にすると，AIに Python コードを書かせ，それをローカルで実行して答えを得ることで算数ミスを排除します．
- **出力構造**: `results/benchmarks/<モデル>/<手法>/<アルゴリズム>/run_<日時>/` に自動整理されます．

---

## ドキュメント・実行結果へのリンク

- [LLM ベンチマーク実行ガイド (`benchmark_guide.md`)](docs/benchmark_guide.md)
- [研究計画書 (`plan.md`)](docs/plan.md)
- [研究ログ (`log.md`)](docs/log.md)
- [学習実験結果のサマリー (`summary.md`)](results/summary.md)
- [LLMベンチマーク結果のサマリー (`summary_llm.md`)](results/summary_llm.md)
