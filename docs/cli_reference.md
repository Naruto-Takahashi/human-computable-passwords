# コマンドライン引数の手引き

> `train_finetuning.py` と `run_eval.py` の引数。既定値の落とし穴つき
>
> 📚 [ドキュメント索引](README.md) ／ 関連: [学習の基礎](llm_training_basics.md) ・ [バッチの書き方](../experiments/batch/README.md) ・ [結果の置き場](../results/README.md)

> [!IMPORTANT]
> **研究のパラメータ（鍵サイズ $n$・チャレンジ長 $k$・$`k_1`$・$`k_2`$・安全性
> パラメータ $s(f)$）ではなく，スクリプトの引数の話．** 前者は
> [hcp_background.md](hcp_background.md) にある。
> 旧ファイル名 `parameters.md`（2026-09-13 に改名。研究のパラメータと
> 紛らわしかったため）。

`train_finetuning.py` と `run_eval.py` の引数を，**既定値をソースから確認したうえで**
まとめたもの（2026-09-12 時点）．旧 `experiment_guide.md` の §2 を現行の実装に合わせて
書き直し，内容が古くなっていた箇所を訂正した．

各引数が何をしているのか（LoRA のランクとは，ドロップアウトとは）は
[llm_training_basics.md](llm_training_basics.md) を参照．

実際に回すときは `experiments/batch/_common.sh` を使うと，ここの多くを書かずに済む
（[experiments/batch/README.md](../experiments/batch/README.md) 参照）．

## つまずきやすい3点

**1. `--paradigm` の語彙が学習と評価で違う**

| スクリプト | 選択肢 | 既定値 |
|---|---|---|
| `train_finetuning.py` | `pure` / **`rationale`** | `rationale` |
| `run_eval.py` | `pure` / **`pot`** | `pure` |

同じ `--paradigm` という名前だが取りうる値が違う．学習側の `rationale` は
「考え方の説明つきで学習する」，評価側の `pot` は「Python コードを生成させて実行する」．
**本研究の現行実験はすべて `pure`（答えだけ）で統一している**が，既定値は `rationale` なので
バッチスクリプトでは必ず明示している．

**2. 既定値が現行の実験条件と違う**

| 引数 | ソース上の既定値 | 現行実験で使う値 |
|---|---|---|
| `--model` | `Qwen/Qwen2.5-1.5B-Instruct` | `Qwen/Qwen2.5-3B-Instruct` |
| `--n_train` | 500 | 1000 |
| `--epochs` | 3 | 5 |
| `--paradigm`（学習） | `rationale` | `pure` |
| `--n_shot` | 10 | 0 |
| `--n_test`（評価） | 50 | **500** |

`--n_test` の既定値50 をそのまま使うと，点推定が最大13ポイントずれて結論を誤らせる
（2026-08 に実際に起きた．§3.1.1 of [plan.md](plan.md)）．**500件を標準とする．**

**3. 学習と評価で揃えるべき引数**

`--algorithm` / `--stage` / `--key_seed` / `--n_shot` は，学習時と評価時で同じ値を
指定しないと意味のない測定になる（違う鍵で学習したモデルを別の鍵で採点することになる）．
`_common.sh` の `hcp_run` を使えば自動的に揃う．

## 共通の実験条件

| 引数 | 既定 | 説明 |
|---|---|---|
| `--algorithm` | 必須 | HCP アルゴリズム名．一覧は `make algorithms` |
| `--stage` | 2 | 情報の開示段階．0: なし / 1: 鍵のみ / 2: **ルールのみ（現行）** / 3: ルール＋鍵をK個 |
| `--k_disclosed` | 0 | Stage 3 で事前に開示する鍵セルの数 $K$ |
| `--n_shot` | 学習10 / 評価10 | プロンプトに入れる Few-shot 例の数．**現行のFT実験は0**（例を見せず重みに覚えさせる） |
| `--key_seed` | 0 | 鍵を決めるシード．**結果を最も強く左右する変数**（同じ関数で 10.2%〜99.8%，§3.1.2 of plan.md） |
| `--data_seed` | 0 | チャレンジの抽選を決めるシード．鍵は変えない |

学習用のチャレンジは `data_seed + 1,000,000` の別系列から引かれるので，
評価用と重複しない（`train_finetuning.py` 冒頭の `TRAIN_SEED_OFFSET`）．

## 学習（`train_finetuning.py`）

| 引数 | 既定 | 説明 |
|---|---|---|
| `--n_train` | 500 | 学習サンプル数．実効バッチ8なので `n_train/8` ステップ／エポック |
| `--n_val` | `n_train // 5` | 検証サンプル数．`history.csv` の `eval_loss` がここから出る |
| `--epochs` | 3 | **既定の線形減衰では，学習率が全エポックで0まで下がるため予算の指定でもある**（[measurement_audit.md](measurement_audit.md)） |
| `--lr_scheduler` | linear | `constant` にすると減衰しない．難易度を「離陸に要するステップ数」で測るときはこちら（予算の宣言が測定値に混ざらなくなる） |
| `--warmup_ratio` | 0.0 | 学習率を0から上げる区間．一般的な SFT レシピは 0.03〜0.1 だが本研究は従来 0 |
| `--seed` | 42 | 学習の乱数（$A$ の初期化・並び順・ドロップアウト）．鍵とデータの抽選とは独立 |
| `--lr` | 2e-4 | LoRA としては標準．フルファインチューニングなら2e-5 程度 |
| `--batch_size` | 2 | 8GB VRAM 前提 |
| `--grad_accum` | 4 | 実効バッチ = 2×4 = 8．数学的には8件のバッチと同じ |
| `--lora_r` / `--lora_alpha` | 16 / 32 | LoRA のランクとスケーリング |
| `--quant` | 4bit | QLoRA |
| `--max_len` | 2048 | 最大シーケンス長 |
| `--tag` | "" | この run が属する実験の名前．`make inventory` の見出しになる |
| `--exclude_pairs` | 0 | `table_add` 系専用．指定した組を学習から除き，丸暗記でないことを確かめる |

## 評価（`run_eval.py`）

| 引数 | 既定 | 説明 |
|---|---|---|
| `--task` | predict | `predict`（応答を当てる）／ `recover_key`（鍵を丸ごと逆推定させる） |
| `--provider` | ollama | `lora`（学習済みアダプタ）／ `gemini` ／ `ollama` ／ `mock`（デバッグ用） |
| `--model` | qwen2.5:7b | `lora` のときは**学習 run ディレクトリのパス** |
| `--n_test` | 50 | **500 を使うこと**（上記） |
| `--key_seeds` / `--data_seeds` | 0 | `0-4` や `1,3` のような書き方ができる |
| `--parallel` | 8 | 並列リクエスト数．`lora` では VRAM 保護のため自動的に絞られる |
| `--overwrite` | off | 完了済み条件を再実行する．評価件数を変えるだけなら**不要**（保存先パスに `n_test` が入るため） |

生成は決定的（`do_sample=False`, temperature 0）なので，同じアダプタ・同じ条件なら
何度走らせても同じ結果になる．

## 結果の読み方

- 正解率だけで判断しない．**衝突確率（$`\sum p_i^2`$）と最頻値基準線**を併記する
  （偶然の10%ではなく，鍵ごとの基準線と比べる）
- 500件評価を回す前に `history.csv` の `eval_loss` を見る．学習が離陸していなければ
  評価しても床しか出ない（[measurement_audit.md](measurement_audit.md)）
- 保存先の構造は [results/README.md](../results/README.md)

---

## 次に読む

| | |
|---|---|
| [バッチの書き方](../experiments/batch/README.md) | 毎回引数を書かずに済ませる |
| [結果の置き場](../results/README.md) | 回したあとどこを見るか |

📚 [ドキュメント索引](README.md) へ戻る
