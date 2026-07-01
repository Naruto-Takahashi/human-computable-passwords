# HCP LLM 実験実行ガイド (HCP LLM Experiment Execution Guide)

このドキュメントは，人間計算可能なパスワード（HCP）のLLM評価実験（プロンプティングおよびファインチューニング）を行うための手順，パラメータ仕様，および最適化に関する解説です．

> [!IMPORTANT]
> すべてのコマンドはプロジェクトのルートディレクトリで実行することを想定しています．
> コマンド実行前に必ず `direnv allow` または `nix develop` を実行し，必要なPython環境を読み込んでください．

## 目次
- [1. 基本的な実行手順](#1-基本的な実行手順)
  - [プロンプティング評価実行](#プロンプティング評価実行)
  - [ファインチューニング（QLoRA）学習実行](#ファインチューニングqlora学習実行)
  - [ファインチューニング済みモデルの評価](#ファインチューニング済みモデルの評価)
  - [結果の集計](#結果の集計)
- [2. ハイパーパラメータ一覧と整理](#2-ハイパーパラメータ一覧と整理)
  - [共通の実験条件（独立変数）](#共通の実験条件独立変数)
  - [プロンプティング固有のパラメータ](#プロンプティング固有のパラメータ)
  - [ファインチューニング固有のパラメータ](#ファインチューニング固有のパラメータ)
- [3. 実験パラダイム（手法）の選び方](#3-実験パラダイム手法の選び方)
- [4. 実験結果の分析方法](#4-実験結果の分析方法)
- [5. オフライン開発用のモック（Mock）実行手順](#5-オフライン開発用のモックmock実行手順)

---

## 1. 基本的な実行手順

### プロンプティング評価実行
特定のアルゴリズムに対し，LLMのインコンテキスト推論（Few-shot）の挙動や精度を測定します．
`--verbose` を付けると，各回答の終わりにパースされた結果と推論の断片が表示されます．

```bash
nix develop --command python3 code/scripts/run_prompting.py \
  --provider ollama \
  --model qwen2.5:7b \
  --generator func_31 \
  --stage 0 \
  --paradigm pure \
  --n_test 50
```

### ファインチューニング（QLoRA）学習実行
QLoRA (4-bit量子化LoRA) を用い、指定したアルゴリズム・開示ステージに対してローカル環境で軽量モデルの微調整学習を実行します。

```bash
nix develop --command python3 code/scripts/train_finetuning.py \
  --model Qwen/Qwen2.5-3B-Instruct \
  --generator func_22 \
  --stage 0 \
  --paradigm pot \
  --n_train 800 \
  --epochs 3 \
  --batch_size 2
```

### ファインチューニング済みモデルの評価
学習完了後、保存されたアダプター（`run_XXXXXXXX_XXXXXX` フォルダ）のパスを `--model` に指定し、`--provider lora` で実行して評価を行います。

```bash
nix develop --command python3 code/scripts/run_prompting.py \
  --provider lora \
  --model results/finetuned_models/qwen2.5_3b/stage0/func_22/run_XXXXXXXX_XXXXXX \
  --generator func_22 \
  --stage 0 \
  --paradigm pot \
  --n_test 100
```
*(※ `lora` および `ollama` プロバイダ指定時は、APIレートリミット用ウェイトが不要なため自動で `--sleep_sec 0.0` に設定され、さらに `lora` では VRAM 溢れ防止のため自動で `--parallel 1` に制限され高速かつ安定して動作します。)*

### 結果の集計
実験完了後，以下のコマンドを実行すると `results/summary_llm.md` が更新され，表形式で結果を確認できます．

```bash
nix develop --command python3 code/scripts/summarize_prompting.py
```

---

## 2. ハイパーパラメータ一覧と整理

実験で設定・比較可能なすべてのハイパーパラメータは以下のカテゴリに整理されます。

### 共通の実験条件（独立変数）
プロンプティングとファインチューニングの双方で共通する、HCPの安全性評価のためのパラメータです。

| パラメータ | 型 / デフォルト | 説明 |
| :--- | :--- | :--- |
| `--generator` | str (選択式) | 使用する HCP アルゴリズム名。`simple_add` (直接演算 / Easy), `func_13` (間接参照 / Medium), `func_22` (間接参照 / Medium), `func_31` (間接参照 / Medium), `func_pow` (累乗演算 / Hard) のいずれかを指定。 |
| `--stage` | int (`1`) | 情報の開示段階。`0` (鍵・ルール非公開), `1` (鍵公開・ルール非公開), `2` (鍵非公開・ルール公開), `3` (鍵部分公開・ルール公開) |
| `--k_disclosed`| int (`0`) | Stage 3 において事前に開示する秘密鍵の要素数 $K$（0 〜 26）。 |
| `--n_shot` | int (`10`) | プロンプトに埋め込む Few-shot 用の正解（入力・出力・あるいはコード）の例題数。 |
| `--seed` | int (`42`) | データセット生成に使用する乱数シード。再現性のために `42` 固定を推奨。 |

### プロンプティング固有のパラメータ
`run_prompting.py` で使用される、推論実行および環境制御のためのパラメータです。

| パラメータ | 型 / デフォルト | 説明 |
| :--- | :--- | :--- |
| `--provider` | str (`gemini`) | 利用する LLM の実行基盤。`gemini` (Google API), `ollama` (ローカル推論), `lora` (ファインチューニング済みモデル), `mock` (デバッグ用モック) のいずれか。 |
| `--model` | str (必須) | 使用するモデル名（Gemini: `gemini-2.0-flash` 等、Ollama: `qwen2.5:7b` 等、Lora: アダプターディレクトリの絶対/相対パス）。 |
| `--n_test` | int (`50`) | 評価を行うテスト問題の件数。 |
| `--parallel` | int (`32`) | 並列推論リクエスト数（※ `lora` 指定時は VRAM 保護のため自動的に `1` に制限されます）。 |
| `--sleep_sec` | float (`4.0`) | リクエスト間の待機時間（秒）。Gemini などの API レートリミット回避用（※ `lora`/`ollama`/`mock` 指定時は自動的に `0.0` に補正されます）。 |
| `--paradigm` | str (`pure`) | 実験パラダイム。`pure` (JSONのみ) または `pot` (Pythonコード生成実行) のいずれか。 |

### ファインチューニング固有のパラメータ
`train_finetuning.py` で使用される、学習および QLoRA 調整のためのパラメータです。

**データおよびタスクパラメータ**
| パラメータ | 型 / デフォルト | 説明 |
| :--- | :--- | :--- |
| `--n_train` | int (`500`) | ファインチューニング用の訓練サンプル数。 |
| `--n_val` | int (`-1`) | ファインチューニング用の検証サンプル数。未指定（`-1`）の場合は訓練データ量のバランスを取るために自動的に `n_train // 5` に決定されます。 |
| `--paradigm` | str (`pot`) | 学習の教師ターゲット形式。`pure` (JSONのみの出力を学習) または `pot` (Pythonコードブロックを出力するよう学習) のいずれか。 |

**QLoRA / 最適化パラメータ（固定推奨）**
| パラメータ | 型 / デフォルト | 説明 |
| :--- | :--- | :--- |
| `--epochs` | int (`3`) | 学習のエポック数。 |
| `--batch_size` | int (`2`) | 1GPUあたりのバッチサイズ。8GB VRAM を想定して設計されています。 |
| `--grad_accum` | int (`4`) | 勾配蓄積ステップ数（実質バッチサイズ = `batch_size * grad_accum` = 8）。 |
| `--lr` | float (`2e-4`) | 学習率。 |
| `--max_len` | int (`2048`) | 最大シーケンス長。 |
| `--lora_r` | int (`16`) | LoRA のランク数。 |
| `--lora_alpha` | int (`32`) | LoRA のスケーリングパラメータ。 |

---

## 3. 実験パラダイム（手法）の選び方

研究目的に応じて，`--paradigm` に以下のいずれかを指定して実行してください．結果はディレクトリに自動分類されます（`stage{stage}_{paradigm}`）．

1. **Pure Few-shot** (`pure`)
   - AIが入出力ペアの具体例のみから背後のルールや鍵を「暗算（直接出力）」で予測する方式。
2. **Program-of-Thought (PoT)** (`pot`)
   - AIに計算ロジック（プログラム）を生成させ，それを Python インタプリタで実行して答えを得ることで、単純な計算ミスを排除した論理推論力を検証する方式。


---

## 4. 実験結果 of 分析方法

### 実験結果の保存先ディレクトリ構造
実験結果はモデル・手法ごとに以下のツリー構造に自動整理されて保存されます．
`results/evals/{model_name}/{paradigm}/{generator_name}/run_{timestamp}/`

### 質的分析（思考ログの確認）
各テストケースの**「生の思考プロセス」**が自動保存されます．
`results/evals/.../reasoning_logs/` を確認してください．
* `001_CORRECT.md`: 正解したケースの論理展開
* `002_WRONG.md`: 間違えたケースでの「迷い」や「誤解」
* `003_PARSE_ERROR.md`: 回答フォーマットが崩れた原因の特定

---

## 5. オフライン開発用のモック（Mock）実行手順
ローカルLLMやAPIキーのない環境において，実行パイプラインやディレクトリ生成が正常に動作するかを確認するために，`mock` プロバイダが利用可能です．このモードでは実際のAPIリクエストは発生しません．

```bash
nix develop --command python3 code/scripts/run_prompting.py \
  --provider mock \
  --model test-mock-model \
  --n_test 5
```
