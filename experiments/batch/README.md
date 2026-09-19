# バッチスクリプト一覧

> バッチスクリプトの一覧と書き方。過去の実験がどのファイルか引ける
>
> 📚 [ドキュメント索引](../../docs/README.md) ／ 関連: [実験の一覧](../../docs/experiment_index.md) ・ [引数の手引き](../../docs/cli_reference.md)

**各段階が何だったかの一覧は [docs/experiment_index.md](../../docs/experiment_index.md) にある．**
ここはスクリプト側の索引で，「どのファイルがどの実験か」を引くためのもの．

`experiments/batch/` には，これまでに回した実験が1本1ファイルで残っている．
**各ファイルの冒頭に「なぜこれを回すのか」が書いてある**ので，過去の判断を
たどりたいときはそこを読む．結果と考察は [docs/log.md](../../docs/log.md)，
どの run がどの実験に属するかは `make inventory` で分かる．

## 回し方

疎通確認・本番の起動・進捗の見方は **[../../CLAUDE.md](../../CLAUDE.md)** の
「実験を回すとき」にある。

実行中は1条件につき2行が標準出力に出る。終わったその場で正解率と検証損失が分かるので，
集計コマンドを別に叩かなくても流れが追える。

```
=== [09/12 18:27:11] 開始: 実験8a: 学習予算を外す ===
[09/12 18:27] [1/2] 開始 func_22_k10（鍵0 データ0 件数1000 ep40 → 評価500件）
[09/12 21:14] 完了 func_22_k10(鍵0)     正解率 31.2%   val損失 0.1103  （167分）
```

## 新しく書くとき

`_common.sh` を読み込むと，学習と評価の手順を書かずに済む．

```bash
#!/usr/bin/env bash
# ここに「なぜこれを回すのか」を書く（将来の自分と，報告書のための記録）
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

HCP_TOTAL=2                       # 何本回すか（進捗表示 [1/2] に使う。省略可）
hcp_init "段階X: 実験の名前"      # この名前が make inventory の見出しになる
HCP_EPOCHS=40                     # 既定値を変えたいときだけ書く

hcp_run --algorithm func_22_k10 --key_seed 0
hcp_run --algorithm func_22_k10 --key_seed 1 --n_train 3000

hcp_finish
```

既定値は `--paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5`，
評価500件，モデルは Qwen2.5-3B-Instruct．`hcp_init` の後に `HCP_N_TEST` などで上書きできる．

## これまでの実験（新しい順）

実行済みのスクリプトは [`done/`](done/) にある（記録として残しているだけで，
そのまま再実行することは想定していない．理由は [done/README.md](done/README.md)）．

| スクリプト | 実験 | 内容 | 結果 |
|---|---|---|---|
| `run_static_arity.sh` | 実験9 段階2 | 位置数を揃えた静的対照 `table_add6_k4`（鍵35） | **未実施** |
| `run_minimal_task.sh` | 実験9 段階1 | 鍵4マスの最小課題 `narrowptr_k4_m{1,2}`（鍵35） | **走行中** |
| `run_range_ladder_budget.sh` | 実験8b | 参照範囲ラダーを予算を外して測る `narrowptr_k10_m{1,2}` | m=1 98.6% / m=2 9.2%。壁は最小の刻みにあった |
| `run_budget_probe.sh` | 実験8a | 20エポック・定数学習率で静的／動的を測り直す | 静的100.0%／動的 11.4%・23.6%（丸暗記） |
| `run_seed_variance.sh` | 実験7 | 鍵を固定して data_seed だけ変える（ks=3,6 × ds=1,2） | 鍵6が 10.2%/100.0%/96.2%。測っていたのは離陸の有無 |
| [`done/run_key_effect.sh`](done/run_key_effect.sh) | 実験6 | `func_22_k10` を学習可能な鍵 ks=0 で／`table_add3_k10` を鍵10本で | 同じ鍵で静的99.6% vs 動的20.0%。鍵の分布は二峰性 |
| [`done/run_static_endpoint_check.sh`](done/run_static_endpoint_check.sh) | 実験5b | `table_add3_k10` を鍵だけ変えて（ks=1,2）＋7月アダプタの再評価 | 99.6% / 26.2% / 10.6%。学習可否は鍵で決まる |
| [`done/run_range_ladder.sh`](done/run_range_ladder.sh) | 実験5 | 参照範囲ラダー `narrowptr_k10_m{1,2,3,5}` × 鍵2本 | 勾配は出ず。端点の前提が崩れた |
| [`done/run_baseline_datascale.sh`](done/run_baseline_datascale.sh) | 実験4 | `func_22_k10` の学習量を 1000/3000/5000 に振る | 12.2〜13.0% で不変 |
| [`done/run_structure_ladder.sh`](done/run_structure_ladder.sh) | 実験3 | 動的参照の構造（1本／並列2本／直列2本）× 鍵2本 | 全条件が床で識別できず |
| [`done/run_depth_reeval_n500.sh`](done/run_depth_reeval_n500.sh) | 実験2 | 深さラダーを500件で再評価（50件では結論が覆ったため） | 点推定が最大13ポイントずれていた |
| [`done/run_depth_ladder_step2.sh`](done/run_depth_ladder_step2.sh) | 実験2 | `pointer_chain` 深さ3 を追加 | 深さ3 で精度が上がる異常 → 不動点が原因 |
| [`done/run_depth_ladder_step1b.sh`](done/run_depth_ladder_step1b.sh) | 実験2 | 深さラダー 鍵2本目 | |
| [`done/run_depth_ladder_step1.sh`](done/run_depth_ladder_step1.sh) | 実験2 | `pointer_chain_k10_d{1,2}` | |
| [`done/run_stage3b.sh`](done/run_stage3b.sh) | 7月 | Stage 3（ルール＋鍵の部分開示）の追試 | |
| [`done/run_stage3.sh`](done/run_stage3.sh) | 7月 | Stage 3 の情報開示スイープ | |
| [`done/run_control_table_add3.sh`](done/run_control_table_add3.sh) | 7月 | 統制実験 `table_add3`（動的参照なし） | n=10 で100%。**この鍵は ks=0 だった** |
| [`done/run_pointer_ladder.sh`](done/run_pointer_ladder.sh) | 7月 | `pointer_k{10,26}` の難易度比較 | |
| [`done/run_ab_20260718.sh`](done/run_ab_20260718.sh) | 7月 | A/B（`exclude_pairs` による未見ペアの検証） | |

> **注意** `run_control_table_add3.sh` の「n=10 で100%」は key_seed=0 かつ評価50件の
> 1点である．2026-09 の実験5b・6 で，同じ関数でも鍵を変えると 10.6% まで落ちることが
> 分かった（[docs/log.md](../../docs/log.md) の 2026/09/06）．この結果を引用するときは
> 鍵を確認すること．

## ディレクトリ

```
experiments/batch/
├── _common.sh        学習→評価の共通手順（新しいスクリプトはこれを使う）
├── README.md         このファイル
├── run_*.sh          いま走っている／これから走らせるもの
└── done/             実行済み（記録．そのままの再実行は想定しない）
```

`_common.sh` を実行済みスクリプトに遡って適用していないのは，
[done/README.md](done/README.md) に理由を書いてある．

---

## 次に読む

| | |
|---|---|
| [実験の一覧](../../docs/experiment_index.md) | 各実験の問いと結果 |
| [実行済みのバッチ](done/README.md) | 過去のスクリプト |
| [結果の置き場](../../results/README.md) | 回したあとどこを見るか |

📚 [ドキュメント索引](../../docs/README.md) へ戻る
