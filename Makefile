# =============================================================================
# HCP ベンチマーク — 運用タスク
# =============================================================================
# 前提: nix develop / direnv 環境（torch 系が必要な FT のみ .venv/bin/python）

PY ?= python3

.PHONY: test smoke summarize sync info-limit clean-pycache help

help:
	@echo "make test           # アルゴリズム自己検証 + ソルバー健全性チェック"
	@echo "make smoke          # mock プロバイダによる E2E ドライラン（predict/recover_key）"
	@echo "make info-limit     # func_22 の情報限界 N*_info を測定（results/theory/）"
	@echo "make summarize      # results/evals/ を集計して summary_llm.{md,csv} を生成"
	@echo "make sync           # results/ を Google Drive へ rclone 同期"
	@echo "make clean-pycache  # __pycache__ を削除"

test:
	$(PY) src/hcp/algorithms.py
	$(PY) experiments/info_limit.py --algorithm func_pow --n_shots 60 --key_seeds 0 \
		--output_dir /tmp/hcp_test_theory

smoke:
	$(PY) experiments/run_eval.py --provider mock --model smoke --task predict --paradigm pure \
		--algorithm func_22 --stage 2 --n_shot 10 --n_test 5 --overwrite \
		--output_base_dir /tmp/hcp_smoke
	$(PY) experiments/run_eval.py --provider mock --model smoke --task predict --paradigm pot \
		--algorithm func_22 --stage 2 --n_shot 10 --n_test 5 --overwrite \
		--output_base_dir /tmp/hcp_smoke
	$(PY) experiments/run_eval.py --provider mock --model smoke --task recover_key \
		--algorithm func_22 --stage 2 --n_shot 10 --n_test 20 --overwrite \
		--output_base_dir /tmp/hcp_smoke
	@echo "smoke OK（出力: /tmp/hcp_smoke）"

info-limit:
	$(PY) experiments/info_limit.py --algorithm func_22 \
		--n_shots 5,10,15,20,26,30,40,50 --key_seeds 0-4

summarize:
	$(PY) experiments/summarize.py

sync:
	bash tools/sync_results.sh

clean-pycache:
	find src experiments legacy -type d -name __pycache__ -exec rm -rf {} +
