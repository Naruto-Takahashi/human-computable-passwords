# LLM ベンチマーク実行ガイド

このドキュメントは、人間計算可能なパスワード（HCP）のLLM評価実験を自分で行うための手順とパラメータの解説です。

## 1. 基本的な実行手順

### 単発テスト実行（思考プロセスの観察用）
特定のアルゴリズムに対し、少数のテストでLLMの挙動（Chain-of-Thought）を詳しく見たい場合に使用します。

```bash
python experiments/benchmarks/runner.py \
  --provider ollama \
  --model deepseek-r1:7b \
  --generator func_31 \
  --n_test 3 \
  --parallel 1 \
  --verbose
```

### 一括評価実行（統計データの取得用）
全てのアルゴリズム（simple_add, func_13, func_31, func_pow）に対して一気に精度を測定したい場合に使用します。

```bash
python experiments/benchmarks/batch_benchmark.py \
  --model qwen2.5:7b \
  --parallel 12
```

### 結果の集計
実験完了後、以下のコマンドを叩くと `outputs/summary_llm.md` が更新され、表形式で結果を確認できます。

```bash
python experiments/benchmarks/summarize.py
```

---

## 2. 主要なパラメータ解説

| パラメータ | 意味 | 設定の目安 |
| :--- | :--- | :--- |
| `--provider` | LLMの実行基盤 | ローカルなら `ollama`、APIなら `gemini` |
| `--model` | 使用するモデル名 | `ollama list` で表示される名前を指定 |
| `--generator` | HCPアルゴリズム | `simple_add`, `func_13`, `func_31`, `func_pow` |
| `--n_shot` | ヒント（例題）の数 | デフォルト `10`。モデルの記憶力に合わせて調整 |
| `--n_test` | テスト問題数 | 精度測定なら `50` 以上、観察なら `1~5` |
| `--parallel` | 並列実行数 | 推論モデルは `1`、軽量モデル(7B以下)は `12~32` |
| `--verbose` | 詳細ログ出力 | 思考プロセスを見たい場合は必ず付ける |

---

## 3. 研究を進めるための Tips

### Q. モデルの「考え方」を知りたい
**A.** `runner.py` に `--verbose` を付けて実行してください。
画面に表示される `[Raw Response]` や `<think>` タグの中身を読むことで、モデルがルールをどう誤解しているか、どこで計算ミスをしたかが分かります。

### Q. GPUの使用率を上げたい（高速化したい）
**A.** `--parallel` の値を増やしてください。
ただし、モデルが巨大な場合や `deepseek-r1` のように推論が重いモデルでは、値を上げすぎるとVRAM不足でクラッシュしたり、逆に遅くなったりします。

### Q. 新しいモデルを試したい
**A.** 以下の手順で簡単に追加できます。
1. `ollama pull llama3.1:8b` (例) でモデルをダウンロード
2. `--model llama3.1:8b` を指定してスクリプトを実行

---

## 4. 実行ディレクトリの注意
全てのコマンドはプロジェクトのルートディレクトリ（`README.md` がある場所）で実行することを想定しています。
環境が読み込まれていない場合は、先に `direnv allow` を実行してください。
