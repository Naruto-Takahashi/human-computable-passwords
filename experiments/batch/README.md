# バッチスクリプト一覧

`experiments/batch/` には，これまでに回した実験が1本1ファイルで残っている．
**各ファイルの冒頭に「なぜこれを回すのか」が書いてある**ので，過去の判断を
たどりたいときはそこを読む．結果と考察は [docs/log.md](../../docs/log.md)，
どの run がどの実験に属するかは `make inventory` で分かる．

## 回し方

```bash
# 疎通確認（GPU を掴まないので，走行中のバッチがあっても安全）
HCP_DRY_RUN=1 bash experiments/batch/run_xxx.sh

# 本番。セッションを閉じても走り続ける
nohup bash experiments/batch/run_xxx.sh > /dev/null 2>&1 & disown

# 進捗
make status
```

## 新しく書くとき

`_common.sh` を読み込むと，学習と評価の手順を書かずに済む．

```bash
#!/usr/bin/env bash
# ここに「なぜこれを回すのか」を書く（将来の自分と，報告書のための記録）
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

hcp_init "段階X: 実験の名前"      # この名前が make inventory の見出しになる
HCP_EPOCHS=40                     # 既定値を変えたいときだけ書く

hcp_run --algorithm func_22_k10 --key_seed 0
hcp_run --algorithm func_22_k10 --key_seed 1 --n_train 3000

hcp_finish
```

既定値は `--paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5`，
評価500件，モデルは Qwen2.5-3B-Instruct．`hcp_init` の後に `HCP_N_TEST` などで上書きできる．

## これまでの実験（新しい順）

| スクリプト | 実験 | 内容 | 結果 |
|---|---|---|---|
| `run_seed_variance.sh` | 段階7 | 鍵を固定して data_seed だけ変える（ks=3,6 × ds=1,2） | 走行中 |
| `run_key_effect.sh` | 段階6 | `func_22_k10` を学習可能な鍵 ks=0 で／`table_add3_k10` を鍵10本で | 同じ鍵で静的99.6% vs 動的20.0%。鍵の分布は二峰性 |
| `run_static_endpoint_check.sh` | 段階5b | `table_add3_k10` を鍵だけ変えて（ks=1,2）＋7月アダプタの再評価 | 99.6% / 26.2% / 10.6%。学習可否は鍵で決まる |
| `run_range_ladder.sh` | 段階5 | 参照範囲ラダー `narrowptr_k10_m{1,2,3,5}` × 鍵2本 | 勾配は出ず。端点の前提が崩れた |
| `run_baseline_datascale.sh` | 段階4 | `func_22_k10` の学習量を 1000/3000/5000 に振る | 12.2〜13.0% で不変 |
| `run_structure_ladder.sh` | 段階3 | 動的参照の構造（1本／並列2本／直列2本）× 鍵2本 | 全条件が床で識別できず |
| `run_depth_reeval_n500.sh` | 段階2 | 深さラダーを500件で再評価（50件では結論が覆ったため） | 点推定が最大13ポイントずれていた |
| `run_depth_ladder_step2.sh` | 段階2 | `pointer_chain` 深さ3 を追加 | 深さ3 で精度が上がる異常 → 不動点が原因 |
| `run_depth_ladder_step1b.sh` | 段階2 | 深さラダー 鍵2本目 | |
| `run_depth_ladder_step1.sh` | 段階2 | `pointer_chain_k10_d{1,2}` | |
| `run_stage3b.sh` | 7月 | Stage 3（ルール＋鍵の部分開示）の追試 | |
| `run_stage3.sh` | 7月 | Stage 3 の情報開示スイープ | |
| `run_control_table_add3.sh` | 7月 | 統制実験 `table_add3`（動的参照なし） | n=10 で100%。**この鍵は ks=0 だった** |
| `run_pointer_ladder.sh` | 7月 | `pointer_k{10,26}` の難易度比較 | |
| `run_ab_20260718.sh` | 7月 | A/B（`exclude_pairs` による未見ペアの検証） | |

> **注意** `run_control_table_add3.sh` の「n=10 で100%」は key_seed=0 かつ評価50件の
> 1点である．2026-09 の段階5b・6 で，同じ関数でも鍵を変えると 10.6% まで落ちることが
> 分かった（[docs/log.md](../../docs/log.md) の 2026/09/06）．この結果を引用するときは
> 鍵を確認すること．

## 既存スクリプトと `_common.sh` の関係

`_common.sh` は 2026-09-12 に追加した．それ以前のスクリプトは学習・評価の手順を
各自が抱えたままにしてある（すでに実行を終えた実験の記録であり，書き換えると
当時の実行内容が分からなくなるため）．新しく書くものだけ `_common.sh` を使う．
