# legacy — 旧実装（2026-07-12 リファクタリング以前）

このディレクトリのコードは `code/hcp/` パッケージと新スクリプト群に置き換えられた旧実装であり，**動作保証はない**（`core/generator.py` が新アダプタに書き換えられたため import が壊れているものがある）．過去の実験結果（`results/evals/` の旧形式ディレクトリ）を解釈する際の参照用として残している．

| 旧 | 新 |
|---|---|
| `llm_agent/`（prompt/clients/evaluator/code_executor/data_generator） | `code/hcp/` パッケージ |
| `run_prompting.py` | `code/scripts/run_eval.py` |
| `batch_prompting.py`, `compare_prompting.py` | `code/scripts/sweep.py` |
| `summarize_prompting.py` | `code/scripts/summarize.py` |
| `run_finetuning_pipeline.py` | `train_finetuning.py` + `run_eval.py --provider lora` を個別に実行 |

なお，`run_prompting.py` には「`--provider lora` 時に stage/k_disclosed を 0 へ強制リセットする」バグの修正（未コミットだった変更）が含まれた状態で退避されている．新実装にはこのバグは存在しない．

主要な設計変更の理由は `docs/refactor_notes.md` を参照．
