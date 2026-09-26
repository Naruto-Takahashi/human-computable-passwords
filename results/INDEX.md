# 結果の索引（自動生成 — `make index`）

> 実験ごとの run 一覧。**このファイルを手で編集しない。**
>
> 📚 [ドキュメント索引](../docs/README.md) ／ 実験の設計と考察は [experiment_index.md](../docs/experiment_index.md)

保存場所は条件アドレス（`results/llm_eval/<関数>/<タスク>/<条件>/…`）のままで，
実験はラベルとして与えている。実験ごとに実体を分けない理由は
[tools/experiment_map.py](../tools/experiment_map.py) の冒頭にある。
`results/by_experiment/<ラベル>/` にシンボリックリンクを張ってあるので，
ディレクトリとしても辿れる（実体は1つ）。

接頭辞 `B` は経路B（重み格納型学習），`A` は経路A（in-context 推論）。

> [!NOTE]
> **ここで数えているのは run であって条件ではない。**同じ条件を複数回
> 評価した run があるため，[experiment_index.md](../docs/experiment_index.md) の
> 条件数と一致しないことがある（例: 実験12 は8条件だが，`func_22_k10` 鍵0 を
> 2run 使って錨にしているので9run になる）。
> `※共有` が付いた run は複数の実験に数えられている。

| 実験 | 題 | run 数 | 関数 |
|---|---|---:|---|
| **A1** | 動的参照は in-context 推論でも壁になるか（小川ら CNN の3世代目） | 53 | `func_22_k13`，`func_22_k4`，`func_22_k6`，`func_22_k8`ほか |
| **A13** | 経路Aの基準線: m*_info の確定 | 8 | `func_13_k10`，`func_22_k10`，`func_31_k10`，`lookup_k10`ほか |
| **B1** | 難易度ラダーの探索（記憶・合成・動的参照） | 27 | `func_13`，`func_13_k26`，`func_22`，`func_31`ほか |
| **B12** | 素朴な手順の誤判定はどれだけ起きるか | 9 | `func_22_k10`，`narrowptr_k10_m1`，`narrowptr_k10_m2`，`table_add3_k10` |
| **B2** | 動的参照の深さ | 8 | `pointer_chain_k10_d1`，`pointer_chain_k10_d2`，`pointer_chain_k10_d3` |
| **B3** | 動的参照の本数と依存構造 | 6 | `dualptr_k10`，`func_22_k10`，`recptr_k10` |
| **B4** | 学習量を増やせば床から出るか | 3 | `func_22_k10` |
| **B5** | 動的参照の強さを連続的に刻む（narrowptr） | 8 | `narrowptr_k10_m1`，`narrowptr_k10_m2`，`narrowptr_k10_m3`，`narrowptr_k10_m5` |
| **B5b** | 静的端点が離陸しないのはなぜか | 2 | `table_add3_k10` |
| **B6** | 鍵の効果はどこまで大きいか | 8 | `func_22_k10`，`table_add3_k10` |
| **B7** | 鍵の性質か，run のばらつきか | 5 | `table_add3_k10` |
| **B8a** | 予算を外せば動的参照は離陸するか | 3 | `func_22_k10`，`table_add3_k10` |
| **B8b** | 参照範囲のどこで学習できなくなるか | 2 | `narrowptr_k10_m1`，`narrowptr_k10_m2` |
| **B9** | 課題を極小にしても動的参照は学習されないか | 7 | `narrowptr_k4_m1`，`narrowptr_k4_m2`，`table_add4_k4`，`table_add5_k4`ほか |

## A1 — 動的参照は in-context 推論でも壁になるか（小川ら CNN の3世代目）

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_22_k13` | info_limit | — | — | — | — | — | — | — | `results/solver/func_22_k13_info_limit.csv` |
| `func_22_k4` | recover_key | 0 | 0 | 9 | 2 | — | A | 不正解 | `results/llm_eval/func_22_k4/recover_key/n9_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `func_22_k4` | recover_key | 1 | 0 | 9 | 2 | — | A | 打切 | `results/llm_eval/func_22_k4/recover_key/n9_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `func_22_k4` | recover_key | 2 | 0 | 9 | 2 | — | A | 打切 | `results/llm_eval/func_22_k4/recover_key/n9_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `func_22_k4` | info_limit | — | — | — | — | — | — | — | `results/solver/func_22_k4_info_limit.csv` |
| `func_22_k6` | recover_key | 0 | 0 | 11 | 2 | — | A | 不正解 | `results/llm_eval/func_22_k6/recover_key/n11_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `func_22_k6` | recover_key | 1 | 0 | 11 | 2 | — | A | 打切 | `results/llm_eval/func_22_k6/recover_key/n11_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `func_22_k6` | recover_key | 2 | 0 | 11 | 2 | — | A | 不正解 | `results/llm_eval/func_22_k6/recover_key/n11_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `func_22_k6` | recover_key | 3 | 0 | 11 | 2 | — | A | 不正解 | `results/llm_eval/func_22_k6/recover_key/n11_t500_stage2_k0/ks3_ds0/qwen3.5_4b` |
| `func_22_k6` | recover_key | 4 | 0 | 11 | 2 | — | A | 打切 | `results/llm_eval/func_22_k6/recover_key/n11_t500_stage2_k0/ks4_ds0/qwen3.5_4b` |
| `func_22_k6` | info_limit | — | — | — | — | — | — | — | `results/solver/func_22_k6_info_limit.csv` |
| `func_22_k8` | recover_key | 0 | 0 | 16 | 2 | — | A | 不正解 | `results/llm_eval/func_22_k8/recover_key/n16_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `func_22_k8` | recover_key | 1 | 0 | 16 | 2 | — | A | 不正解 | `results/llm_eval/func_22_k8/recover_key/n16_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `func_22_k8` | recover_key | 2 | 0 | 16 | 2 | — | A | 打切 | `results/llm_eval/func_22_k8/recover_key/n16_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `func_22_k8` | info_limit | — | — | — | — | — | — | — | `results/solver/func_22_k8_info_limit.csv` |
| `narrowptr_k10_m1` | recover_key | 0 | 0 | 18 | 2 | — | A | 打切 | `results/llm_eval/narrowptr_k10_m1/recover_key/n18_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `narrowptr_k10_m1` | recover_key | 1 | 0 | 18 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k10_m1/recover_key/n18_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `narrowptr_k10_m1` | recover_key | 2 | 0 | 18 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k10_m1/recover_key/n18_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `narrowptr_k10_m1` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k10_m1_info_limit.csv` |
| `narrowptr_k13_m1` | recover_key | 0 | 0 | 27 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k13_m1/recover_key/n27_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `narrowptr_k13_m1` | recover_key | 1 | 0 | 27 | 2 | — | A | 打切 | `results/llm_eval/narrowptr_k13_m1/recover_key/n27_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `narrowptr_k13_m1` | recover_key | 2 | 0 | 27 | 2 | — | A | 打切 | `results/llm_eval/narrowptr_k13_m1/recover_key/n27_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `narrowptr_k13_m1` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k13_m1_info_limit.csv` |
| `narrowptr_k26_m1` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k26_m1_info_limit.csv` |
| `narrowptr_k4_m1` | recover_key | 0 | 0 | 12 | 2 | — | A | 完全一致 | `results/llm_eval/narrowptr_k4_m1/recover_key/n12_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `narrowptr_k4_m1` | recover_key | 1 | 0 | 12 | 2 | — | A | 完全一致 | `results/llm_eval/narrowptr_k4_m1/recover_key/n12_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `narrowptr_k4_m1` | recover_key | 2 | 0 | 12 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k4_m1/recover_key/n12_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `narrowptr_k4_m1` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k4_m1_info_limit.csv` |
| `narrowptr_k6_m1` | recover_key | 0 | 0 | 14 | 2 | — | A | 完全一致 | `results/llm_eval/narrowptr_k6_m1/recover_key/n14_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `narrowptr_k6_m1` | recover_key | 1 | 0 | 14 | 2 | — | A | 完全一致 | `results/llm_eval/narrowptr_k6_m1/recover_key/n14_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `narrowptr_k6_m1` | recover_key | 2 | 0 | 14 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k6_m1/recover_key/n14_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `narrowptr_k6_m1` | recover_key | 3 | 0 | 14 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k6_m1/recover_key/n14_t500_stage2_k0/ks3_ds0/qwen3.5_4b` |
| `narrowptr_k6_m1` | recover_key | 4 | 0 | 14 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k6_m1/recover_key/n14_t500_stage2_k0/ks4_ds0/qwen3.5_4b` |
| `narrowptr_k6_m1` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k6_m1_info_limit.csv` |
| `narrowptr_k8_m1` | recover_key | 0 | 0 | 13 | 2 | — | A | 完全一致 | `results/llm_eval/narrowptr_k8_m1/recover_key/n13_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `narrowptr_k8_m1` | recover_key | 1 | 0 | 13 | 2 | — | A | 完全一致 | `results/llm_eval/narrowptr_k8_m1/recover_key/n13_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `narrowptr_k8_m1` | recover_key | 2 | 0 | 13 | 2 | — | A | 不正解 | `results/llm_eval/narrowptr_k8_m1/recover_key/n13_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `narrowptr_k8_m1` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k8_m1_info_limit.csv` |
| `table_add3_k13` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k13_info_limit.csv` |
| `table_add3_k4` | recover_key | 0 | 0 | 10 | 2 | — | A | 完全一致 | `results/llm_eval/table_add3_k4/recover_key/n10_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `table_add3_k4` | recover_key | 1 | 0 | 10 | 2 | — | A | 打切 | `results/llm_eval/table_add3_k4/recover_key/n10_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `table_add3_k4` | recover_key | 2 | 0 | 10 | 2 | — | A | 完全一致 | `results/llm_eval/table_add3_k4/recover_key/n10_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `table_add3_k4` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k4_info_limit.csv` |
| `table_add3_k6` | recover_key | 0 | 0 | 14 | 2 | — | A | 完全一致 | `results/llm_eval/table_add3_k6/recover_key/n14_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `table_add3_k6` | recover_key | 1 | 0 | 14 | 2 | — | A | 完全一致 | `results/llm_eval/table_add3_k6/recover_key/n14_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `table_add3_k6` | recover_key | 2 | 0 | 14 | 2 | — | A | 完全一致 | `results/llm_eval/table_add3_k6/recover_key/n14_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `table_add3_k6` | recover_key | 3 | 0 | 14 | 2 | — | A | 不正解 | `results/llm_eval/table_add3_k6/recover_key/n14_t500_stage2_k0/ks3_ds0/qwen3.5_4b` |
| `table_add3_k6` | recover_key | 4 | 0 | 14 | 2 | — | A | 完全一致 | `results/llm_eval/table_add3_k6/recover_key/n14_t500_stage2_k0/ks4_ds0/qwen3.5_4b` |
| `table_add3_k6` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k6_info_limit.csv` |
| `table_add3_k8` | recover_key | 0 | 0 | 22 | 2 | — | A | 不正解 | `results/llm_eval/table_add3_k8/recover_key/n22_t500_stage2_k0/ks0_ds0/qwen3.5_4b` |
| `table_add3_k8` | recover_key | 1 | 0 | 22 | 2 | — | A | 打切 | `results/llm_eval/table_add3_k8/recover_key/n22_t500_stage2_k0/ks1_ds0/qwen3.5_4b` |
| `table_add3_k8` | recover_key | 2 | 0 | 22 | 2 | — | A | 不正解 | `results/llm_eval/table_add3_k8/recover_key/n22_t500_stage2_k0/ks2_ds0/qwen3.5_4b` |
| `table_add3_k8` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k8_info_limit.csv` |

## A13 — 経路Aの基準線: m*_info の確定

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_13_k10` | info_limit | — | — | — | — | — | — | — | `results/solver/func_13_k10_info_limit.csv` |
| `func_22_k10` | info_limit | — | — | — | — | — | — | — | `results/solver/func_22_k10_info_limit.csv` |
| `func_31_k10` | info_limit | — | — | — | — | — | — | — | `results/solver/func_31_k10_info_limit.csv` |
| `lookup_k10` | info_limit | — | — | — | — | — | — | — | `results/solver/lookup_k10_info_limit.csv` |
| `narrowptr_k10_m2` | info_limit | — | — | — | — | — | — | — | `results/solver/narrowptr_k10_m2_info_limit.csv` |
| `table_add3_k10` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k10_info_limit.csv` |
| `table_add3_k15` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k15_info_limit.csv` |
| `table_add3_k26` | info_limit | — | — | — | — | — | — | — | `results/solver/table_add3_k26_info_limit.csv` |

## B1 — 難易度ラダーの探索（記憶・合成・動的参照）

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_13` | info_limit | — | — | — | — | — | — | — | `results/solver/func_13_info_limit.csv` |
| `func_13_k26` | info_limit | — | — | — | — | — | — | — | `results/solver/func_13_k26_info_limit.csv` |
| `func_22` | predict | 0 | 0 | 0 | 2 | 5 | — | 8.0% | `results/llm_eval/func_22/predict_pure/n0_t200_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260718_024256` |
| `func_22` | predict | 0 | 0 | 0 | 2 | 5 | — | 6.5% | `results/llm_eval/func_22/predict_pure/n0_t200_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260716_210311` |
| `func_22` | predict | 0 | 0 | 0 | 0 | — | — | 12.0% | `results/llm_eval/func_22/predict_pure/n0_t50_stage0_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_func_22_run_20260717_000604` |
| `func_22` | info_limit | — | — | — | — | — | — | — | `results/solver/func_22_info_limit.csv` |
| `func_31` | info_limit | — | — | — | — | — | — | — | `results/solver/func_31_info_limit.csv` |
| `lookup_k10` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/lookup_k10/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_lookup_k10_run_20260716_142731` |
| `lookup_k26` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/lookup_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_lookup_k26_run_20260716_160156` |
| `lookup_k4` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/lookup_k4/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_lookup_k4_run_20260716_125310` |
| `pointer_k10` | predict | 0 | 0 | 0 | 2 | 5 | — | 34.0% | `results/llm_eval/pointer_k10/predict_pure/n0_t50_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260728_033104` |
| `pointer_k26` | predict | 0 | 0 | 0 | 2 | 5 | — | 18.0% | `results/llm_eval/pointer_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260728_070545` |
| `pointer_k26` | predict | 0 | 0 | 0 | 2 | 5 | — | 14.0% | `results/llm_eval/pointer_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260728_051352` |
| `secret_add` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/secret_add/predict_pure/n0_t50_stage2_k0/ks0_ds0/results_finetuned_models_qwen2.5_3b_secret_add_run_20260716_121139` |
| `secret_add` | predict | 0 | 0 | 0 | 0 | — | — | 100.0% | `results/llm_eval/secret_add/predict_pure/n0_t50_stage0_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_secret_add_run_20260717_011729` |
| `simple_add` | predict | 0 | 0 | 0 | 0 | — | — | 100.0% | `results/llm_eval/simple_add/predict_pure/n0_t50_stage0_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_simple_add_run_20260716_225546` |
| `simple_add` | predict | 0 | 1000000 | 0 | 0 | — | — | 100.0% | `results/llm_eval/simple_add/predict_pure/n0_t20_stage0_k0/ks0_ds1000000/results_finetuned_models_qwen2.5_3b_simple_add_run_20260716_120102` |
| `table_add3_k10` | predict | 0 | 0 | 0 | 2 | 5 | — | 99.6% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260729_023201` |
| `table_add3_k26` | predict | 0 | 0 | 0 | 2 | 5 | — | 14.0% | `results/llm_eval/table_add3_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260729_055650` |
| `table_add3_k26` | predict | 0 | 0 | 0 | 2 | 5 | — | 12.0% | `results/llm_eval/table_add3_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260729_041333` |
| `table_add_k10` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/table_add_k10/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_table_add_k10_run_20260716_173814` |
| `table_add_k13` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/table_add_k13/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_table_add_k13_run_20260717_132044` |
| `table_add_k16` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/table_add_k16/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_table_add_k16_run_20260717_150129` |
| `table_add_k20` | predict | 0 | 0 | 0 | 2 | — | — | 24.0% | `results/llm_eval/table_add_k20/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_table_add_k20_run_20260717_164228` |
| `table_add_k26` | predict | 0 | 0 | 0 | 2 | — | — | 8.0% | `results/llm_eval/table_add_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_table_add_k26_run_20260716_192129` |
| `table_add_k26` | predict | 0 | 0 | 0 | 2 | 5 | — | 100.0% | `results/llm_eval/table_add_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260721_161433` |
| `table_add_k26` | predict | 0 | 0 | 0 | 2 | — | — | 100.0% | `results/llm_eval/table_add_k26/predict_pure/n0_t50_stage2_k0/ks0_ds0/_home_nalt_ghq_github.com_Naruto-Takahashi_human-computable-passwords_results_finetuned_models_qwen2.5_3b_table_add_k26_run_20260717_182330` |

## B12 — 素朴な手順の誤判定はどれだけ起きるか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_22_k10` | predict | 0 | 0 | 0 | 2 | 20 | — | 11.4% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260913_102443` ※共有 |
| `func_22_k10` | predict | 0 | 0 | 0 | 2 | 20 | — | 23.6% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260913_175931` ※共有 |
| `narrowptr_k10_m1` | predict | 1 | 0 | 0 | 2 | 20 | — | 10.2% | `results/llm_eval/narrowptr_k10_m1/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260923_070802` |
| `narrowptr_k10_m1` | predict | 2 | 0 | 0 | 2 | 20 | — | 11.8% | `results/llm_eval/narrowptr_k10_m1/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260924_045936` |
| `narrowptr_k10_m2` | predict | 1 | 0 | 0 | 2 | 20 | — | 9.4% | `results/llm_eval/narrowptr_k10_m2/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260923_143933` |
| `narrowptr_k10_m2` | predict | 2 | 0 | 0 | 2 | 20 | — | 16.6% | `results/llm_eval/narrowptr_k10_m2/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260924_122836` |
| `table_add3_k10` | predict | 1 | 0 | 0 | 2 | 20 | — | 9.8% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260923_001601` |
| `table_add3_k10` | predict | 6 | 0 | 0 | 2 | 20 | — | 100.0% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks6_ds0/qwen2.5_3b_ft_20260913_032850` ※共有 |
| `table_add3_k10` | predict | 8 | 0 | 0 | 2 | 20 | — | 97.0% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks8_ds0/qwen2.5_3b_ft_20260923_221047` |

## B2 — 動的参照の深さ

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `pointer_chain_k10_d1` | predict | 0 | 0 | 0 | 2 | 5 | — | 30.4% | `results/llm_eval/pointer_chain_k10_d1/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260816_143142` |
| `pointer_chain_k10_d1` | predict | 1 | 0 | 0 | 2 | 5 | — | 24.8% | `results/llm_eval/pointer_chain_k10_d1/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260816_195925` |
| `pointer_chain_k10_d1` | predict | 2 | 0 | 0 | 2 | 5 | — | 35.8% | `results/llm_eval/pointer_chain_k10_d1/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260816_235035` |
| `pointer_chain_k10_d2` | predict | 0 | 0 | 0 | 2 | 5 | — | 38.4% | `results/llm_eval/pointer_chain_k10_d2/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260816_161732` |
| `pointer_chain_k10_d2` | predict | 1 | 0 | 0 | 2 | 5 | — | 24.2% | `results/llm_eval/pointer_chain_k10_d2/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260816_214500` |
| `pointer_chain_k10_d2` | predict | 2 | 0 | 0 | 2 | 5 | — | 35.6% | `results/llm_eval/pointer_chain_k10_d2/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260817_013649` |
| `pointer_chain_k10_d3` | predict | 1 | 0 | 0 | 2 | 5 | — | 31.6% | `results/llm_eval/pointer_chain_k10_d3/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260817_095544` |
| `pointer_chain_k10_d3` | predict | 2 | 0 | 0 | 2 | 5 | — | 44.0% | `results/llm_eval/pointer_chain_k10_d3/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260817_120042` |

## B3 — 動的参照の本数と依存構造

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `dualptr_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 14.4% | `results/llm_eval/dualptr_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260823_045542` |
| `dualptr_k10` | predict | 2 | 0 | 0 | 2 | 5 | — | 13.8% | `results/llm_eval/dualptr_k10/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260823_092300` |
| `func_22_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 13.0% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260823_004525` ※共有 |
| `func_22_k10` | predict | 2 | 0 | 0 | 2 | 5 | — | 16.0% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260823_025131` |
| `recptr_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 10.4% | `results/llm_eval/recptr_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260823_070158` |
| `recptr_k10` | predict | 2 | 0 | 0 | 2 | 5 | — | 20.0% | `results/llm_eval/recptr_k10/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260823_113251` |

## B4 — 学習量を増やせば床から出るか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_22_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 13.0% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260823_004525` ※共有 |
| `func_22_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 12.6% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260823_210006` |
| `func_22_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 12.2% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260823_151707` |

## B5 — 動的参照の強さを連続的に刻む（narrowptr）

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `narrowptr_k10_m1` | predict | 1 | 0 | 0 | 2 | 5 | — | 9.8% | `results/llm_eval/narrowptr_k10_m1/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260902_015225` |
| `narrowptr_k10_m1` | predict | 2 | 0 | 0 | 2 | 5 | — | 13.4% | `results/llm_eval/narrowptr_k10_m1/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260902_101812` |
| `narrowptr_k10_m2` | predict | 1 | 0 | 0 | 2 | 5 | — | 9.6% | `results/llm_eval/narrowptr_k10_m2/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260902_035831` |
| `narrowptr_k10_m2` | predict | 2 | 0 | 0 | 2 | 5 | — | 17.4% | `results/llm_eval/narrowptr_k10_m2/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260902_122450` |
| `narrowptr_k10_m3` | predict | 1 | 0 | 0 | 2 | 5 | — | 9.0% | `results/llm_eval/narrowptr_k10_m3/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260902_060434` |
| `narrowptr_k10_m3` | predict | 2 | 0 | 0 | 2 | 5 | — | 19.8% | `results/llm_eval/narrowptr_k10_m3/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260902_143124` |
| `narrowptr_k10_m5` | predict | 1 | 0 | 0 | 2 | 5 | — | 9.8% | `results/llm_eval/narrowptr_k10_m5/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260902_081227` |
| `narrowptr_k10_m5` | predict | 2 | 0 | 0 | 2 | 5 | — | 13.6% | `results/llm_eval/narrowptr_k10_m5/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260902_164130` |

## B5b — 静的端点が離陸しないのはなぜか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `table_add3_k10` | predict | 1 | 0 | 0 | 2 | 5 | — | 10.6% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks1_ds0/qwen2.5_3b_ft_20260905_231205` |
| `table_add3_k10` | predict | 2 | 0 | 0 | 2 | 5 | — | 26.2% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks2_ds0/qwen2.5_3b_ft_20260906_010906` |

## B6 — 鍵の効果はどこまで大きいか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_22_k10` | predict | 0 | 0 | 0 | 2 | 5 | — | 20.0% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260909_195019` |
| `table_add3_k10` | predict | 3 | 0 | 0 | 2 | 5 | — | 99.8% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks3_ds0/qwen2.5_3b_ft_20260909_215428` |
| `table_add3_k10` | predict | 4 | 0 | 0 | 2 | 5 | — | 96.8% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks4_ds0/qwen2.5_3b_ft_20260909_234850` |
| `table_add3_k10` | predict | 5 | 0 | 0 | 2 | 5 | — | 17.4% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks5_ds0/qwen2.5_3b_ft_20260910_014404` |
| `table_add3_k10` | predict | 6 | 0 | 0 | 2 | 5 | — | 10.2% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks6_ds0/qwen2.5_3b_ft_20260910_033625` |
| `table_add3_k10` | predict | 7 | 0 | 0 | 2 | 5 | — | 33.6% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks7_ds0/qwen2.5_3b_ft_20260910_053027` |
| `table_add3_k10` | predict | 8 | 0 | 0 | 2 | 5 | — | 10.6% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks8_ds0/qwen2.5_3b_ft_20260910_072655` |
| `table_add3_k10` | predict | 9 | 0 | 0 | 2 | 5 | — | 11.6% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks9_ds0/qwen2.5_3b_ft_20260910_092238` |

## B7 — 鍵の性質か，run のばらつきか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `table_add3_k10` | predict | 3 | 1 | 0 | 2 | 5 | — | 99.0% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks3_ds1/qwen2.5_3b_ft_20260912_190607` |
| `table_add3_k10` | predict | 3 | 1 | 0 | 2 | 5 | — | 100.0% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks3_ds1/qwen2.5_3b_ft_20260912_171242` |
| `table_add3_k10` | predict | 3 | 2 | 0 | 2 | 5 | — | 98.2% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks3_ds2/qwen2.5_3b_ft_20260912_225525` |
| `table_add3_k10` | predict | 6 | 1 | 0 | 2 | 5 | — | 100.0% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks6_ds1/qwen2.5_3b_ft_20260912_210005` |
| `table_add3_k10` | predict | 6 | 2 | 0 | 2 | 5 | — | 96.2% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks6_ds2/qwen2.5_3b_ft_20260913_004808` |

## B8a — 予算を外せば動的参照は離陸するか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `func_22_k10` | predict | 0 | 0 | 0 | 2 | 20 | — | 11.4% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260913_102443` ※共有 |
| `func_22_k10` | predict | 0 | 0 | 0 | 2 | 20 | — | 23.6% | `results/llm_eval/func_22_k10/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260913_175931` ※共有 |
| `table_add3_k10` | predict | 6 | 0 | 0 | 2 | 20 | — | 100.0% | `results/llm_eval/table_add3_k10/predict_pure/n0_t500_stage2_k0/ks6_ds0/qwen2.5_3b_ft_20260913_032850` ※共有 |

## B8b — 参照範囲のどこで学習できなくなるか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `narrowptr_k10_m1` | predict | 0 | 0 | 0 | 2 | 20 | — | 98.6% | `results/llm_eval/narrowptr_k10_m1/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260917_191647` |
| `narrowptr_k10_m2` | predict | 0 | 0 | 0 | 2 | 20 | — | 9.2% | `results/llm_eval/narrowptr_k10_m2/predict_pure/n0_t500_stage2_k0/ks0_ds0/qwen2.5_3b_ft_20260918_025516` |

## B9 — 課題を極小にしても動的参照は学習されないか

| 関数 | タスク | 鍵 | 引 | 観測 | Stage | ep | 水準 | 結果 | 場所 |
|---|---|---:|---:|---:|---:|---:|:-:|---|---|
| `narrowptr_k4_m1` | predict | 35 | 0 | 0 | 2 | 20 | — | 100.0% | `results/llm_eval/narrowptr_k4_m1/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260919_130631` |
| `narrowptr_k4_m2` | predict | 35 | 0 | 0 | 2 | 20 | — | 100.0% | `results/llm_eval/narrowptr_k4_m2/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260919_203553` |
| `narrowptr_k4_m2` | predict | 35 | 0 | 0 | 2 | 20 | — | 63.8% | `results/llm_eval/narrowptr_k4_m2/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260921_031710` |
| `table_add4_k4` | predict | 35 | 0 | 0 | 2 | 20 | — | 100.0% | `results/llm_eval/table_add4_k4/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260920_125032` |
| `table_add5_k4` | predict | 35 | 0 | 0 | 2 | 20 | — | 11.8% | `results/llm_eval/table_add5_k4/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260921_104712` |
| `table_add6_k4` | predict | 35 | 0 | 0 | 2 | 20 | — | 10.4% | `results/llm_eval/table_add6_k4/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260920_194523` |
| `table_add6_k4` | predict | 35 | 0 | 0 | 2 | 20 | — | 10.6% | `results/llm_eval/table_add6_k4/predict_pure/n0_t500_stage2_k0/ks35_ds0/qwen2.5_3b_ft_20260920_040830` |

## 次に読む

| | |
|---|---|
| [実験の一覧](../docs/experiment_index.md) | 設計と考察を読みたいとき |
| [研究計画](../docs/plan.md) | 位置づけを確かめたいとき |
