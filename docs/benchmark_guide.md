# LLM ベンチマーク実行ガイド

このドキュメントは，人間計算可能なパスワード（HCP）のLLM評価実験を行うための手順とパラメータの解説です．

> [!IMPORTANT]
> すべてのコマンドはプロジェクトのルートディレクトリで実行することを想定しています．
> コマンド実行前に必ず `direnv allow` または `nix develop` を実行し，必要なPython環境を読み込んでください．

## 目次
- [1. 基本的な実行手順](#1-基本的な実行手順)
  - [単発テスト実行（思考プロセスの観察用）](#単発テスト実行思考プロセスの観察用)
  - [一括評価実行（統計データの取得用）](#一括評価実行統計データの取得用)
  - [結果の集計](#結果の集計)
- [2. 主要なパラメータ解説](#2-主要なパラメータ解説)
- [3. 実験パラダイム（手法）の選び方](#3-実験パラダイム手法の選び方)
- [4. 実験結果の分析方法](#4-実験結果の分析方法)
- [5. オフライン開発用のモック（Mock）実行手順](#5-オフライン開発用のモックmock実行手順)
- [6. 研究を進めるための Tips](#6-研究を進めるための-tips)
- [7. 実行ディレクトリの注意](#7-実行ディレクトリの注意)

---

## 1. 基本的な実行手順

### 単発テスト実行（思考プロセスの観察用）
特定のアルゴリズムに対し，少数のテストでLLMの挙動（Chain-of-Thought）を詳しく見たい場合に使用します．
`--verbose` を付けると，各回答の終わりにパースされた結果と推論の断片が表示されます．

```bash
python code/scripts/run_benchmark.py \
  --provider ollama \
  --model qwen2.5:7b \
  --generator func_31 \
  --stage 0 \
  --paradigm pure \
  --n_test 3 \
  --parallel 1 \
  --verbose
```

### 一括評価実行（統計データの取得用）
全てのアルゴリズム（simple_add，func_13，func_31，func_pow）に対して一気に精度を測定したい場合に使用します．

```bash
python code/scripts/batch_eval.py \
  --model qwen2.5:7b \
  --parallel 1 \
  --n_shot 10 \
  --n_test 20 \
  --stage 1 \
  --paradigm rationale_pot
```

### 結果の集計
実験完了後，以下のコマンドを叩くと `results/summary_llm.md` が更新され，表形式で結果を確認できます．

```bash
python code/scripts/summarize_llm.py
```

---

## 2. 主要なパラメータ解説

| パラメータ | 意味 | 設定の目安 |
| :--- | :--- | :--- |
| `--provider` | LLMの実行基盤 | ローカルなら `ollama`，APIなら `gemini`，検証用なら `mock` |
| `--model` | 使用するモデル名 | `ollama list` で表示される名前を指定 |
| `--generator` | HCPアルゴリズム | `simple_add`，`func_13`，`func_31`，`func_pow` |
| `--n_shot` | ヒント（例題）の数 | デフォルト `10`．圧縮形式により多く指定可能 |
| `--parallel` | 並列実行数 | 7B/9Bモデルなら `2~3`，推論モデルは `1` |
| `--stage` | 開示情報ステージ | `0` (鍵・ルール無), `1` (鍵有・ルール無), `2` (鍵無・ルール有), `3` (鍵部分公開・ルール有) |
| `--k_disclosed` | 鍵の部分公開数 | Stage 3 で公開する秘密鍵の要素数 $K$。デフォルト `5` |
| `--paradigm` | 実験手法（パラダイム） | `pure` (ゼロショット), `rationale` (計算解説あり), `pot` (Pythonコード実行), `rationale_pot` (解説+コード実行) |
| `--verbose` | 詳細ログ出力 | 思考プロセスを見たい場合は必ず付ける |

---

## 3. 実験パラダイム（手法）の選び方

研究目的に応じて，`--paradigm` に以下のいずれかを指定して実行してください．結果はディレクトリに自動分類されます（`stage{stage}_{paradigm}`）．

1. **Pure Few-shot** (`pure`)
   - AIが具体例のみから背後のルールを「帰納（逆推定）」できるかをテストする．
2. **Rationalized Few-shot** (`rationale`)
   - AIに解き方の手順を教えた状態で，それを正確に「演繹（実行）」できるかをテストする．
3. **Program-of-Thought (PoT)** (`pot`)
   - AIに計算ロジック（プログラム）を生成させ，計算機で実行することで，単純な算数ミスを排除した論理推論力をテストする．
4. **Rationalized PoT** (`rationale_pot`)
   - 教えられた解法アルゴリズムを正確に Python コードとして「演繹（実装・実行）」できるかをテストする（最強構成）．

---

## 4. 実験結果の分析方法

### 実験結果の保存先ディレクトリ構造
実験結果はモデル・手法ごとに以下のツリー構造に自動整理されて保存されます．
`results/benchmarks/{model_name}/{paradigm}/{generator_name}/run_{timestamp}/`

### 質的分析（思考ログの確認）
各テストケースの**「生の思考プロセス」**が自動保存されます．
`results/benchmarks/.../reasoning_logs/` を確認してください．
* `001_CORRECT.md`: 正解したケースの論理展開
* `002_WRONG.md`: 間違えたケースでの「迷い」や「誤解」
* `003_PARSE_ERROR.md`: 回答フォーマットが崩れた原因の特定

### 定量的分析（統計データの集計）
複数の実験が終わったら，`python code/scripts/summarize_llm.py` を実行して，モデル間や難易度ごとの正解率を比較します．

---

## 5. オフライン開発用のモック（Mock）実行手順
ローカルLLMやAPIキーのない環境において，実行パイプラインやディレクトリ生成が正常に動作するかを確認するために，`mock` プロバイダが利用可能です．このモードでは実際のAPIリクエストは発生しません．

```bash
nix develop --command python3 code/scripts/run_benchmark.py \
  --provider mock \
  --model test-mock-model \
  --n_test 5
```

---

## 6. 研究を進めるための Tips

### Q. モデルの「考え方」を知りたい
**A.** `run_benchmark.py` に `--verbose` を付けて実行してください．
画面に表示される `[Result Tail]` やファイル内のフルログを読むことで，モデルがルールをどう誤解しているか，どこで計算ミスをしたかが分かります．

### Q. GPUの使用率を上げたい（高速化したい）
**A.** `--parallel` の値を増やしてください．
ただし，`deepseek-r1` のように推論が重いモデルでは，値を上げすぎるとVRAM不足でクラッシュしたり，逆に遅くなったりします．RTX 2080 Ti (11GB) では 7B モデルなら 1〜2 並列が安全です．

### Q. 新しいモデルを試したい
**A.** 以下の手順で簡単に追加できます．
1. `ollama pull llama3.1:8b` (例) でモデルをダウンロード
2. `--model llama3.1:8b` を指定してスクリプトを実行

---

## 7. 実行ディレクトリの注意
すべてのコマンドはプロジェクトのルートディレクトリ（`README.md` がある場所）で実行することを想定しています．
環境が読み込まれていない場合は，先に `direnv allow` を実行してください．

---

## 8. LLM Fine-tuning (ファインチューニング) の実行手順

### 環境のセットアップ
ファインチューニングを行うには、Nix環境内で Python 仮想環境を作成し、PyTorchおよび Hugging Face パッケージをインストールします。

```bash
# 1. Nix環境の自動ロード
direnv allow   # または nix develop

# 2. 仮想環境の作成とパッケージインストール
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### ファインチューニングの学習実行 (`train_lora.py`)
QLoRA (4-bit量子化LoRA) を用い、指定したアルゴリズム・開示ステージに対してローカル環境で軽量モデルの微調整学習を実行します。

```bash
python code/scripts/train_lora.py \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --generator func_31 \
  --stage 1 \
  --n_train 500 \
  --n_val 100 \
  --epochs 3 \
  --batch_size 2
```

**主なオプション**:
* `--model`: 使用するHugging Faceモデル識別子 (例: `Qwen/Qwen2.5-1.5B-Instruct`, `meta-llama/Llama-3.2-1B-Instruct`)
* `--generator`: HCPアルゴリズムの名前
* `--stage`: 実験ステージ (0〜3)
* `--epochs`: エポック数 (デフォルト: 3)
* `--batch_size`: バッチサイズ (デフォルト: 2)
* `--include_rationale`: 微調整の学習ターゲットに出力までの思考プロセス（解説）を含める場合はこのフラグを有効にします。

### ファインチューニング済みモデルの評価 (`eval_lora.py`)
学習が完了すると、結果は以下の形式で保存されます：
`results/finetuning/{model}/stage{stage}/{generator}/run_{timestamp}/`

このディレクトリパス（`adapter` や `train_metadata.json` が含まれるフォルダ）を引数に渡し、テストセットでの予測精度（Zの正答率）を評価します。

```bash
python code/scripts/eval_lora.py \
  --run_dir results/finetuning/Qwen_Qwen2.5-1.5B-Instruct/stage1/func_31/run_XXXXXXXX_XXXXXX \
  --n_test 100
```
結果は指定されたディレクトリ配下に `eval_report.json` として出力されます。

