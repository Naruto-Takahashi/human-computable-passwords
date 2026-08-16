# LLM ベンチマーク実験結果 サマリー

`experiments/summarize.py` により自動生成（2026-08-16 18:23:28）．
一次データ: `results/summary_llm.csv`（46 実験）

| モデル | アルゴリズム | タスク | Stage | K | N | 反復数 | 応答精度 | 鍵セル一致率 | 鍵完全一致率 | held-out精度 |
|---|---|---|---|---|---|---|---|---|---|---|
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/func_22/run_20260717_000604 | func_22 | predict(pure) | 0 | 0 | 0 | 1 | 12.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/lookup_k10/run_20260716_142731 | lookup_k10 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/lookup_k26/run_20260716_160156 | lookup_k26 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/lookup_k4/run_20260716_125310 | lookup_k4 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/secret_add/run_20260717_011729 | secret_add | predict(pure) | 0 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/simple_add/run_20260716_225546 | simple_add | predict(pure) | 0 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/table_add_k10/run_20260716_173814 | table_add_k10 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/table_add_k13/run_20260717_132044 | table_add_k13 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/table_add_k16/run_20260717_150129 | table_add_k16 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/table_add_k20/run_20260717_164228 | table_add_k20 | predict(pure) | 2 | 0 | 0 | 1 | 24.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/table_add_k26/run_20260716_192129 | table_add_k26 | predict(pure) | 2 | 0 | 0 | 1 | 8.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/finetuned_models/qwen2.5_3b/table_add_k26/run_20260717_182330 | table_add_k26 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/pointer_chain_k10_d1/run_20260816_143142 | pointer_chain_k10_d1 | predict(pure) | 2 | 0 | 0 | 1 | 36.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/pointer_chain_k10_d2/run_20260816_161732 | pointer_chain_k10_d2 | predict(pure) | 2 | 0 | 0 | 1 | 46.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/pointer_k10/run_20260728_033104 | pointer_k10 | predict(pure) | 2 | 0 | 0 | 1 | 34.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/pointer_k26/run_20260728_051352 | pointer_k26 | predict(pure) | 2 | 0 | 0 | 1 | 14.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/pointer_k26/run_20260728_070545 | pointer_k26 | predict(pure) | 2 | 0 | 0 | 1 | 18.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/table_add3_k10/run_20260729_023201 | table_add3_k10 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/table_add3_k26/run_20260729_041333 | table_add3_k26 | predict(pure) | 2 | 0 | 0 | 1 | 12.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/table_add3_k26/run_20260729_055650 | table_add3_k26 | predict(pure) | 2 | 0 | 0 | 1 | 14.00% | - | - | - |
| /home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/results/llm_finetune/qwen2.5_3b/table_add_k26/run_20260721_161433 | table_add_k26 | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| qwen2.5:14b | func_13 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 20.00% | - | - | - |
| qwen2.5:14b | func_31 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 60.00% | - | - | - |
| qwen2.5:14b | func_pow | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 100.00% | - | - | - |
| qwen2.5:14b | simple_add | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 100.00% | - | - | - |
| qwen2.5:7b | func_13 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 40.00% | - | - | - |
| qwen2.5:7b | func_31 | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 40.00% | - | - | - |
| qwen2.5:7b | func_pow | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 100.00% | - | - | - |
| qwen2.5:7b | simple_add | predict(rationale_pot) [旧] | 1 | 5 | 10 | 1 | 100.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260703_160130 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 1 | 0.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260703_164407 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 1 | 0.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260703_200935 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 1 | 6.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260704_060001 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 1 | 0.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260704_132018 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 1 | 13.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260704_143051 | func_22 | predict(pot) [旧] | 0 | 0 | 10 | 1 | 100.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260704_204311 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 1 | 5.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260705_021019 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 1 | 12.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260705_025608 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 1 | 16.00% | - | - | - |
| qwen2.5_3b/func_22/run_20260706_115157 | func_22 | predict(pure) [旧] | 0 | 0 | 10 | 1 | 20.00% | - | - | - |
| qwen2.5_3b/simple_add/run_20260705_132018 | simple_add | predict(pure) [旧] | 0 | 0 | 10 | 1 | 8.00% | - | - | - |
| qwen2.5_3b/simple_add/run_20260705_190237 | simple_add | predict(pure) [旧] | 0 | 0 | 10 | 1 | 20.00% | - | - | - |
| qwen2.5_3b/simple_add/run_20260705_233644 | simple_add | predict(pure) [旧] | 0 | 0 | 10 | 1 | 6.00% | - | - | - |
| results/finetuned_models/qwen2.5_3b/secret_add/run_20260716_121139 | secret_add | predict(pure) | 2 | 0 | 0 | 1 | 100.00% | - | - | - |
| results/finetuned_models/qwen2.5_3b/simple_add/run_20260716_120102 | simple_add | predict(pure) | 0 | 0 | 0 | 1 | 100.00% | - | - | - |
| results/llm_finetune/qwen2.5_3b/func_22/run_20260716_210311 | func_22 | predict(pure) | 2 | 0 | 0 | 1 | 6.50% | - | - | - |
| results/llm_finetune/qwen2.5_3b/func_22/run_20260718_024256 | func_22 | predict(pure) | 2 | 0 | 0 | 1 | 8.00% | - | - | - |
