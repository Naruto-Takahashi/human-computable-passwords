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
	@echo ""
	@echo "make report         # 週次報告を全てPDF化（docs/reports/pdf/）"
	@echo "make report-latest  # 最新の週次報告だけPDF化"
	@echo "make report-live    # プレビュー配信＋自動再ビルド（通常はこれ）"
	@echo "make report-watch   # 保存を検知して再ビルドするだけ"
	@echo "make report-send    # 最新PDFを Taildrop で手元の端末へ送る"

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

# =============================================================================
# 週次報告書（docs/reports/*.md -> PDF）
# =============================================================================
# 原本は Markdown。組版は pandoc + Typst で行い，体裁は docs/reports/template.typ
# に集約している。Word は経由しない。
#
# 典型的な流れ:
#   手元の端末$ ssh -L 8765:localhost:8765 labpc
#   その中で   $ make report-live
#   手元のブラウザで http://localhost:8765/preview.html を開く

REPORT_DIR := docs/reports
REPORT_TPL := $(REPORT_DIR)/template.typ
REPORT_OUT := $(REPORT_DIR)/pdf
REPORT_PORT ?= 8765
SEND_TO ?= surface-pro

REPORT_MDS  := $(sort $(wildcard $(REPORT_DIR)/weekly_report_*.md))
REPORT_PDFS := $(patsubst $(REPORT_DIR)/%.md,$(REPORT_OUT)/%.pdf,$(REPORT_MDS))
REPORT_LATEST_MD  := $(lastword $(REPORT_MDS))
REPORT_LATEST_PDF := $(patsubst $(REPORT_DIR)/%.md,$(REPORT_OUT)/%.pdf,$(REPORT_LATEST_MD))

# auto_identifiers を切っているのは，日本語や下付き文字を含む見出しから生成される
# Typst のラベルが不正になり，コンパイルが落ちるため。
REPORT_FLAGS := \
	--from markdown-auto_identifiers \
	--pdf-engine=typst \
	--template=$(REPORT_TPL) \
	--resource-path=.:$(REPORT_DIR) \
	-V papersize=a4

.PHONY: report report-latest report-link report-watch report-live report-send

report: $(REPORT_PDFS) report-link

report-latest: $(REPORT_LATEST_PDF) report-link

$(REPORT_OUT)/%.pdf: $(REPORT_DIR)/%.md $(REPORT_TPL)
	@mkdir -p $(REPORT_OUT)
	pandoc $< -o $@ $(REPORT_FLAGS)
	@echo "[OK] $@"

# プレビューが見る latest.pdf は常に「日付が最新の1本」を指す。
# ビルド規則の中で張ると make report のときに最後にビルドされた1本を
# 指してしまうため，独立した手順にしてある。
report-link: $(REPORT_LATEST_PDF)
	@cp -f $(REPORT_DIR)/preview.html $(REPORT_OUT)/preview.html
	@ln -sf $(notdir $(REPORT_LATEST_PDF)) $(REPORT_OUT)/latest.pdf

report-watch:
	@echo "[INFO] 監視中（Ctrl-C で終了）: $(REPORT_LATEST_MD)"
	@ls $(REPORT_MDS) $(REPORT_TPL) | entr -n -s 'make report-latest'

# 配信サーバと自動再ビルドを1つの窓でまとめて動かす（通常はこちらを使う）
report-live:
	@PORT=$(REPORT_PORT) bash $(REPORT_DIR)/live.sh

report-send: report-latest
	@tailscale file cp $(REPORT_LATEST_PDF) "$(SEND_TO):" \
	  && echo "[OK] $(SEND_TO) に送信しました: $(notdir $(REPORT_LATEST_PDF))"
