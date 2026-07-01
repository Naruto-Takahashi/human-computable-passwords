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
│       ├── run_prompting.py   # LLMプロンプティング評価実行スクリプト
│       ├── compare_prompting.py # 複数プロンプト手法の自動比較実行スクリプト
│       ├── batch_prompting.py # 全アルゴリズムの一括プロンプティング評価実行
│       ├── summarize_prompting.py # プロンプティング評価結果の自動集計
│       ├── train_finetuning.py # LLMのQLoRAファインチューニング（微調整学習）実行
│       ├── train_baseline.py  # 従来の機械学習モデルの個別学習
│       ├── batch_train_baseline.py # 従来の機械学習モデルのバッチ学習
│       └── summarize_baseline.py # 学習結果の自動集計
├── docs/                      # 計画書・ログ・実行手順書
│   ├── plan.md                # 研究計画書
│   ├── experiment_guide.md    # 実験実行ガイド
│   ├── log.md                 # 研究開発ログ
│   └── ultimate_showdown_prompt.md # プロンプト検証用メモ
├── literature/                # 先行研究の文献（論文PDF，卒論スライド，学会スライド等）
│   ├── Towards Human Computable Passwords.pdf
│   ├── R7_小川.pdf
│   ├── R6_池田.pdf
│   └── ...
├── results/                   # 実験結果の出力先（Git管理対象外，summaryのみコミット対象）
│   ├── prompting/             # LLMプロンプティング評価結果データ
│   ├── finetuning/            # [NEW] LLMファインチューニング結果（モデル/ステージ/アルゴリズムの階層）
│   ├── baselines/             # 機械学習モデルの学習ログ・グラフ・メタデータ
│   ├── summary.md             # 機械学習実験結果の自動集計表
│   └── summary_llm.md         # LLMベンチマーク結果の自動集計表
├── flake.nix                  # Nix (Flakes) による再現可能なPythonシステム・CUDA環境の定義
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

詳細な実行手順やパラメータの仕様，トラブルシューティングについては，[HCP LLM 実験実行ガイド](docs/experiment_guide.md) を参照してください．

```bash
# 1. 単発手法の実行
python code/scripts/run_prompting.py --model qwen2.5:7b --generator simple_add --paradigm pot

# 2. オフライン検証用（Mockプロバイダによるドライラン）
python code/scripts/run_prompting.py --provider mock --model test-mock-model --n_test 5

# 3. 全4パラダイム（手法）の自動比較
python code/scripts/compare_prompting.py --model qwen2.5:7b --generator simple_add

# 評価結果の集計（ summary_llm.md の生成）
python code/scripts/summarize_prompting.py
```

- **実験パラダイム**: `pure`（暗算直接出力）および `pot`（Pythonコード実行方式）の2段階で評価可能．
- **PoT (Program-of-Thought)**: `--paradigm pot` を指定すると，AIに Python コードを書かせ，それをローカルで実行して答えを得ることで算数ミスを排除します．
- **出力構造**: `results/evals/<モデル>/<手法>/run_<日時>/` に自動整理されます．

---

## ドキュメント・実行結果へのリンク

- [HCP LLM 実験実行ガイド (`experiment_guide.md`)](docs/experiment_guide.md)
- [研究計画書 (`plan.md`)](docs/plan.md)
- [研究ログ (`log.md`)](docs/log.md)
- [学習実験結果のサマリー (`summary.md`)](results/summary.md)
- [LLMベンチマーク結果のサマリー (`summary_llm.md`)](results/summary_llm.md)

---

QLoRA (4-bit量子化LoRA) を用いてローカル環境で軽量LLMの微調整学習を行い、共通のベンチマーク実行スクリプトを用いて評価を行います。

```bash
# 1. ファインチューニングの実行（学習済みアダプターは results/finetuned_models/ に保存）
python code/scripts/train_finetuning.py --model Qwen/Qwen2.5-3B-Instruct --generator func_22 --paradigm pot --n_train 800

# 2. 共通スクリプトを用いたファインチューニングモデルの評価 (provider に lora を指定)
python code/scripts/run_prompting.py --provider lora --model results/finetuned_models/qwen2.5_3b/func_22/run_XXXXXXXX_XXXXXX --generator func_22 --paradigm pot --n_test 100
```
