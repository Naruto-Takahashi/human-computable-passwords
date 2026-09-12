# results/ の歩き方

実験結果の置き場．**中身はほぼ Git 管理外**で，集計物（`summary_llm.*`，
`inventory.*`）と `solver/`・`figures/` だけが追跡されている（`.gitignore` 参照）．

## まずここを見る

| 見たいもの | 見る場所 |
|---|---|
| どのパラメータで学習したか，未実施の組み合わせ | `inventory.md`（`make inventory`）— **学習 run が1行** |
| 評価結果の一覧（鍵・評価件数つき） | `summary_llm.md`（`make summarize`）— **評価1件が1行** |
| いま何が走っているか | `make status` |
| 生の数値をプロットしたい | `inventory.csv` / `summary_llm.csv` |

手でディレクトリを掘る前に，まず `inventory.md` を見ると早い．

## ディレクトリ

```
results/
├── inventory.{md,csv}   学習 run の棚卸し（実験の段階ごと）
├── summary_llm.{md,csv} 評価結果の集計
├── llm_finetune/        学習の成果物
├── llm_eval/            評価の結果
├── logs/                バッチの実行ログ（学習の進捗・採点の ✓/✗）
├── solver/              厳密ソルバーによる情報限界 N*_info（Git管理）
├── figures/             報告用の図（Git管理）
└── ml_baseline/         従来ML（CNN等）ベースライン
```

## 学習: `llm_finetune/`

```
llm_finetune/{モデル}/{アルゴリズム}/run_{YYYYMMDD_HHMMSS}/
├── adapter/            ← 評価が読み込むのはこちら
├── checkpoints/          学習再開用。adapter/ と重みは同一で，本研究では未使用
├── train_metadata.json   学習条件（鍵・データ・件数・エポック・lr・--tag）と鍵の中身
├── history.csv           エポックごとの学習損失・検証損失 ← 離陸したかが分かる
├── summary.json
└── training_curves.png
```

`history.csv` の `eval_loss` は，500件評価を回さなくても学習の成否が読める指標である
（鍵10本で正解率を完全に順位づけることを確認済み）。読み方は
[docs/measurement_audit.md](../docs/measurement_audit.md)．

## 評価: `llm_eval/`

```
llm_eval/{アルゴリズム}/{タスク}/n{N}_t{T}_stage{S}_k{K}/ks{鍵}_ds{データ}/{モデル}/
├── metrics.json    正解率・パースエラー数・実行時の git コミット
├── results.csv     1問ごとの challenge / 正解 / 予測 / 正誤
└── prompt_example.txt
```

- `N` = few-shot の件数（ファインチューニング評価では 0）
- **`T` = 評価件数**（2026-09-12 に追加。それ以前は 50件と500件が同じ場所に
  書かれていて見分けられなかった）
- `S` = Stage（情報開示の段階），`K` = 鍵の部分開示数

**アルゴリズムが先頭**なので，1つの実験の結果は1箇所にまとまる．

```
$ find results/llm_eval/table_add3_k10 -name metrics.json
  .../n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260729_023201/metrics.json
  .../n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260905_231205/metrics.json
  .../n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260906_010906/metrics.json
  ...                    ^^^ 鍵だけが違う10本が並ぶ
```

2026-09-12 まではモデル名が先頭にあり，ファインチューニング評価ではモデル名が
学習 run ごとに変わるため，同じアルゴリズムの結果が60個のディレクトリに散っていた．

最下層の `{モデル}` は，ファインチューニングでは `qwen2.5_3b_ft_{学習runの時刻}` になる．
学習 run ディレクトリと対応している：

```
学習: llm_finetune/qwen2.5_3b/table_add3_k10/run_20260729_023201
評価: .../ks0_ds0/qwen2.5_3b_ft_20260729_023201/
                               ^^^^^^^^^^^^^^^ run_ を外した部分が一致する
```

`_legacy_format/` には 2026-07-12 のリファクタリング以前の結果が入っている
（`metadata.json` を持つ旧形式．集計には含まれ，`summary_llm.md` で「[旧]」と表示される）．

構造を変えたときは `make migrate-eval-paths`（確認）→ `APPLY=1` で既存結果を移せる．
移動先は各 `metrics.json` の条件から計算するので，どの構造から来ても同じ手順で済む．

## ログ: `logs/`

バッチが1条件につき1本書く．ファイル名は条件から決まる．

```
{アルゴリズム}_ks{鍵}_ds{データ}_n{学習件数}_ep{エポック}.log   （2026-09-12 以降）
{アルゴリズム}_ks{鍵}_stage{S}_n{学習件数}.log                  （それ以前）
```

中身は前半が学習の進捗，後半が採点の `✓` / `✗`．`*_done.log` はバッチの完了マーカー．
進捗は `make status` で見る（手で `grep -c '✓'` しなくてよい）．
