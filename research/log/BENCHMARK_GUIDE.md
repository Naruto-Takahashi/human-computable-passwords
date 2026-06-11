# LLM ベンチマーク実行ガイド

このドキュメントは、人間計算可能なパスワード（HCP）のLLM評価実験を自分で行うための手順とパラメータの解説です。

## 1. 基本的な実行手順

### 単発テスト実行（思考プロセスの観察用）
特定のアルゴリズムに対し、少数のテストでLLMの挙動（Chain-of-Thought）を詳しく見たい場合に使用します。
`--verbose` を付けると、各回答の終わりにパースされた結果と推論の断片が表示されます。

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
  --model deepseek-r1:7b \
  --parallel 1 \
  --n_shot 10 \
  --n_test 20
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
| `--n_shot` | ヒント（例題）の数 | デフォルト `10`。圧縮形式により多く指定可能 |
| `--parallel` | 並列実行数 | 7B/9Bモデルなら `2~3`、推論モデルは `1` |
| `--rationale` | 手法：ヒントあり | 例題に計算過程の解説を付加する |
| `--use_code` | 手法：PoT (Code) | 言葉ではなく Python コードで計算させる |
| `--verbose` | 詳細ログ出力 | 思考プロセスを見たい場合は必ず付ける |

---

## 3. 実験パラダイム（手法）の選び方

研究目的に応じて、以下のフラグを組み合わせて実行してください。結果はディレクトリに自動分類されます。

1. **Pure Few-shot** (`フラグなし`)
   - AIが自力でルールを発見できるかをテストする。
2. **Rationalized Few-shot** (`--rationale`)
   - AIに計算手順を教えた状態で、論理的に振る舞えるかをテストする。
3. **Program-of-Thought (PoT)** (`--use_code`)
   - AIにコードを書かせ、算数ミスを排除した純粋なロジック力をテストする。
4. **Rationalized PoT** (`--rationale --use_code`)
   - 正解のロジックを教えた上で、それをコード化して実行できるか（最強構成）。

---

## 4. 実験結果の分析方法

### 質的分析（思考ログの確認）
今回のシステムでは、各テストケースの **「生の思考プロセス」** が自動保存されます。
`outputs/benchmarks/run_.../reasoning_logs/` を覗いてください。
- `case_001_correct.md`: 正解したケースの論理展開
- `case_002_wrong.md`: 間違えたケースでの「迷い」や「誤解」
- `case_003_parse_error.md`: 回答フォーマットが崩れた原因の特定

### 定量的分析（統計データの集計）
複数の実験が終わったら、`python experiments/benchmarks/summarize.py` を実行して、モデル間や難易度ごとの正解率を比較します。

---

## 4. 研究を進めるための Tips

### Q. モデルの「考え方」を知りたい
**A.** `runner.py` に `--verbose` を付けて実行してください。
画面に表示される `[Result Tail]` やファイル内のフルログを読むことで、モデルがルールをどう誤解しているか、どこで計算ミスをしたかが分かります。

### Q. GPUの使用率を上げたい（高速化したい）
**A.** `--parallel` の値を増やしてください。
ただし、`deepseek-r1` のように推論が重いモデルでは、値を上げすぎるとVRAM不足でクラッシュしたり、逆に遅くなったりします。RTX 2080 Ti (11GB) では 7B モデルなら 1〜2 並列が安全です。

### Q. 新しいモデルを試したい
**A.** 以下の手順で簡単に追加できます。
1. `ollama pull llama3.1:8b` (例) でモデルをダウンロード
2. `--model llama3.1:8b` を指定してスクリプトを実行

---

## 5. 実行ディレクトリの注意
全てのコマンドはプロジェクトのルートディレクトリ（`README.md` がある場所）で実行することを想定しています。
環境が読み込まれていない場合は、先に `direnv allow` を実行してください。
