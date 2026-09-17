# LLM ベンチマーク実験結果 サマリー

`experiments/summarize.py` により自動生成（2026-09-14 01:34:19）．
一次データ: `results/summary_llm.csv`（86 実験）

**この表は「評価1件」が1行**．ファインチューニングもプロンプティングも含む．
学習条件（件数・エポック・lr）や検証損失，まだ評価していない学習 run を見たいなら
[inventory.md](inventory.md)（`make inventory`）を見ること．

| モデル | アルゴリズム | タスク | Stage | K | N_shot | 評価件数 | 鍵 | 反復数 | 応答精度 | 鍵セル一致率 | 鍵完全一致率 | held-out精度 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dualptr_k10/run_20260823_045542 | dualptr_k10 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 14.40% | - | - | - |
| dualptr_k10/run_20260823_092300 | dualptr_k10 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 13.80% | - | - | - |
| func_22/run_20260703_160130 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 3 | 42 | 1 | 0.00% | - | - | - |
| func_22/run_20260703_164407 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 3 | 42 | 1 | 0.00% | - | - | - |
| func_22/run_20260703_200935 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 100 | 42 | 1 | 6.00% | - | - | - |
| func_22/run_20260704_060001 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 100 | 42 | 1 | 0.00% | - | - | - |
| func_22/run_20260704_132018 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 100 | 42 | 1 | 13.00% | - | - | - |
| func_22/run_20260704_143051 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 100 | 42 | 1 | 100.00% | - | - | - |
| func_22/run_20260704_204311 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 100 | 42 | 1 | 5.00% | - | - | - |
| func_22/run_20260705_021019 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 50 | 42 | 1 | 12.00% | - | - | - |
| func_22/run_20260705_025608 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 50 | 42 | 1 | 16.00% | - | - | - |
| func_22/run_20260706_115157 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 50 | 42 | 1 | 20.00% | - | - | - |
| func_22/run_20260716_210311 | func_22 | predict(pure) | 2 | 0 | 0 | 200 | 0 | 1 | 6.50% | - | - | - |
| func_22/run_20260717_000604 | func_22 | predict(pure) | 0 | 0 | 0 | 50 | 0 | 1 | 12.00% | - | - | - |
| func_22/run_20260718_024256 | func_22 | predict(pure) | 2 | 0 | 0 | 200 | 0 | 1 | 8.00% | - | - | - |
| func_22_k10/run_20260823_004525 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 13.00% | - | - | - |
| func_22_k10/run_20260823_025131 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 16.00% | - | - | - |
| func_22_k10/run_20260823_151707 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 12.20% | - | - | - |
| func_22_k10/run_20260823_210006 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 12.60% | - | - | - |
| func_22_k10/run_20260909_195019 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 0 | 1 | 20.00% | - | - | - |
| func_22_k10/run_20260913_102443 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 0 | 1 | 11.40% | - | - | - |
| func_22_k10/run_20260913_175931 | func_22_k10 | predict(pure) | 2 | 0 | 0 | 500 | 0 | 1 | 23.60% | - | - | - |
| lookup_k10/run_20260716_142731 | lookup_k10 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| lookup_k26/run_20260716_160156 | lookup_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| lookup_k4/run_20260716_125310 | lookup_k4 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| narrowptr_k10_m1/run_20260902_015225 | narrowptr_k10_m1 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 9.80% | - | - | - |
| narrowptr_k10_m1/run_20260902_101812 | narrowptr_k10_m1 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 13.40% | - | - | - |
| narrowptr_k10_m2/run_20260902_035831 | narrowptr_k10_m2 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 9.60% | - | - | - |
| narrowptr_k10_m2/run_20260902_122450 | narrowptr_k10_m2 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 17.40% | - | - | - |
| narrowptr_k10_m3/run_20260902_060434 | narrowptr_k10_m3 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 9.00% | - | - | - |
| narrowptr_k10_m3/run_20260902_143124 | narrowptr_k10_m3 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 19.80% | - | - | - |
| narrowptr_k10_m5/run_20260902_081227 | narrowptr_k10_m5 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 9.80% | - | - | - |
| narrowptr_k10_m5/run_20260902_164130 | narrowptr_k10_m5 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 13.60% | - | - | - |
| pointer_chain_k10_d1/run_20260816_143142 | pointer_chain_k10_d1 | predict(pure) | 2 | 0 | 0 | 500 | 0 | 1 | 30.40% | - | - | - |
| pointer_chain_k10_d1/run_20260816_195925 | pointer_chain_k10_d1 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 24.80% | - | - | - |
| pointer_chain_k10_d1/run_20260816_235035 | pointer_chain_k10_d1 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 35.80% | - | - | - |
| pointer_chain_k10_d2/run_20260816_161732 | pointer_chain_k10_d2 | predict(pure) | 2 | 0 | 0 | 500 | 0 | 1 | 38.40% | - | - | - |
| pointer_chain_k10_d2/run_20260816_214500 | pointer_chain_k10_d2 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 24.20% | - | - | - |
| pointer_chain_k10_d2/run_20260817_013649 | pointer_chain_k10_d2 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 35.60% | - | - | - |
| pointer_chain_k10_d3/run_20260817_095544 | pointer_chain_k10_d3 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 31.60% | - | - | - |
| pointer_chain_k10_d3/run_20260817_120042 | pointer_chain_k10_d3 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 44.00% | - | - | - |
| pointer_k10/run_20260728_033104 | pointer_k10 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 34.00% | - | - | - |
| pointer_k26/run_20260728_051352 | pointer_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 14.00% | - | - | - |
| pointer_k26/run_20260728_070545 | pointer_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 18.00% | - | - | - |
| qwen2.5:14b | func_13 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 20.00% | - | - | - |
| qwen2.5:14b | func_31 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 60.00% | - | - | - |
| qwen2.5:14b | func_pow | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 100.00% | - | - | - |
| qwen2.5:14b | simple_add | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 100.00% | - | - | - |
| qwen2.5:7b | func_13 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 40.00% | - | - | - |
| qwen2.5:7b | func_31 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 40.00% | - | - | - |
| qwen2.5:7b | func_pow | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 100.00% | - | - | - |
| qwen2.5:7b | simple_add | predict(rationale_pot) [旧] | 1 | 5 | 10 | 5 | 42 | 1 | 100.00% | - | - | - |
| recptr_k10/run_20260823_070158 | recptr_k10 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 10.40% | - | - | - |
| recptr_k10/run_20260823_113251 | recptr_k10 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 20.00% | - | - | - |
| secret_add/run_20260716_121139 | secret_add | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| secret_add/run_20260717_011729 | secret_add | predict(pure) | 0 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| simple_add/run_20260705_132018 | simple_add | predict(pure) [旧] | 0 | 0 | 10 | 50 | 42 | 1 | 8.00% | - | - | - |
| simple_add/run_20260705_190237 | simple_add | predict(pure) [旧] | 0 | 0 | 10 | 50 | 42 | 1 | 20.00% | - | - | - |
| simple_add/run_20260705_233644 | simple_add | predict(pure) [旧] | 0 | 0 | 10 | 50 | 42 | 1 | 6.00% | - | - | - |
| simple_add/run_20260716_120102 | simple_add | predict(pure) | 0 | 0 | 0 | 20 | 0 | 1 | 100.00% | - | - | - |
| simple_add/run_20260716_225546 | simple_add | predict(pure) | 0 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| table_add3_k10/run_20260729_023201 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 0 | 1 | 99.60% | - | - | - |
| table_add3_k10/run_20260905_231205 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 1 | 1 | 10.60% | - | - | - |
| table_add3_k10/run_20260906_010906 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 2 | 1 | 26.20% | - | - | - |
| table_add3_k10/run_20260909_215428 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 3 | 1 | 99.80% | - | - | - |
| table_add3_k10/run_20260909_234850 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 4 | 1 | 96.80% | - | - | - |
| table_add3_k10/run_20260910_014404 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 5 | 1 | 17.40% | - | - | - |
| table_add3_k10/run_20260910_033625 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 6 | 1 | 10.20% | - | - | - |
| table_add3_k10/run_20260910_053027 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 7 | 1 | 33.60% | - | - | - |
| table_add3_k10/run_20260910_072655 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 8 | 1 | 10.60% | - | - | - |
| table_add3_k10/run_20260910_092238 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 9 | 1 | 11.60% | - | - | - |
| table_add3_k10/run_20260912_171242 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 3 | 1 | 100.00% | - | - | - |
| table_add3_k10/run_20260912_190607 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 3 | 1 | 99.00% | - | - | - |
| table_add3_k10/run_20260912_210005 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 6 | 1 | 100.00% | - | - | - |
| table_add3_k10/run_20260912_225525 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 3 | 1 | 98.20% | - | - | - |
| table_add3_k10/run_20260913_004808 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 6 | 1 | 96.20% | - | - | - |
| table_add3_k10/run_20260913_032850 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 500 | 6 | 1 | 100.00% | - | - | - |
| table_add3_k26/run_20260729_041333 | table_add3_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 12.00% | - | - | - |
| table_add3_k26/run_20260729_055650 | table_add3_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 14.00% | - | - | - |
| table_add_k10/run_20260716_173814 | table_add_k10 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| table_add_k13/run_20260717_132044 | table_add_k13 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| table_add_k16/run_20260717_150129 | table_add_k16 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| table_add_k20/run_20260717_164228 | table_add_k20 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 24.00% | - | - | - |
| table_add_k26/run_20260716_192129 | table_add_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 8.00% | - | - | - |
| table_add_k26/run_20260717_182330 | table_add_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
| table_add_k26/run_20260721_161433 | table_add_k26 | predict(pure) | 2 | 0 | 0 | 50 | 0 | 1 | 100.00% | - | - | - |
