# =============================================================================
# HCP ベンチマーク — 運用タスク
# =============================================================================
# 前提: nix develop / direnv 環境（torch 系が必要な FT のみ .venv/bin/python）

PY ?= python3

.PHONY: test smoke summarize inventory status algorithms check-mermaid migrate-eval-paths sync info-limit clean-pycache help

help:
	@echo "── 日々の確認 ───────────────────────────────────────"
	@echo "make status         # 走行中バッチと各ログの進捗を1画面で"
	@echo "make inventory      # どのパラメータで学習したかの棚卸し（results/inventory.md）"
	@echo "make summarize      # 評価結果を集計して summary_llm.{md,csv} を生成"
	@echo "make algorithms     # 登録アルゴリズムを難易度の分解にそって一覧"
	@echo ""
	@echo "  results/ の歩き方         : results/README.md"
	@echo "  過去のバッチ実験の一覧     : experiments/batch/README.md"
	@echo ""
	@echo "── 実験を回す ───────────────────────────────────────"
	@echo "  学習:  .venv/bin/python experiments/train_finetuning.py \\"
	@echo "           --model Qwen/Qwen2.5-3B-Instruct --algorithm func_22_k10 \\"
	@echo "           --paradigm pure --stage 2 --n_shot 0 --n_train 1000 --epochs 5 \\"
	@echo "           --key_seed 0 --data_seed 0"
	@echo "  評価:  .venv/bin/python experiments/run_eval.py --provider lora \\"
	@echo "           --model <学習が出力した run ディレクトリ> --algorithm func_22_k10 \\"
	@echo "           --stage 2 --n_shot 0 --n_test 500 --key_seeds 0 --data_seeds 0"
	@echo "         ※ 学習時と同じ algorithm / stage / key_seed を指定すること"
	@echo "  一括:  HCP_DRY_RUN=1 bash experiments/batch/<名前>.sh   # まず空実行で確認"
	@echo "         nohup bash experiments/batch/<名前>.sh > /dev/null 2>&1 & disown"
	@echo "         （新規作成は experiments/batch/README.md の雛形を使う）"
	@echo ""
	@echo "── 保守 ─────────────────────────────────────────────"
	@echo "make test           # アルゴリズム自己検証 + 文面の非退行検査 + 記法検査 + ソルバー"
	@echo "make smoke          # mock プロバイダによる E2E ドライラン（predict/recover_key）"
	@echo "make info-limit     # func_22 の情報限界 N*_info を測定（results/theory/）"
	@echo "make check-mermaid  # Markdown 内の mermaid 図の構文を検査"
	@echo "make migrate-eval-paths  # 評価結果を n_test 入りのパス構造へ移行（確認のみ）"
	@echo "make sync           # results/ を Google Drive へ rclone 同期"
	@echo "make clean-pycache  # __pycache__ を削除"
	@echo ""
	@echo "── 報告書 ───────────────────────────────────────────"
	@echo "make report         # 週次報告を全てPDF化（docs/reports/pdf/）"
	@echo "make report-latest  # 最新の週次報告だけPDF化"
	@echo "make report-live    # プレビュー配信＋自動再ビルド（通常はこれ）"
	@echo "make report-watch   # 保存を検知して再ビルドするだけ"
	@echo "make report-send    # 最新PDFを Taildrop で手元の端末へ送る"

test:
	$(PY) src/hcp/algorithms.py
	$(PY) tests/check_algorithm_texts.py
	$(PY) tools/check_docs.py
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

inventory:
	$(PY) experiments/inventory.py

status:
	@bash tools/status.sh

algorithms:
	@$(PY) tools/list_algorithms.py

# 構文を誤ると GitHub 上で図の代わりにエラーが出るため，事前に検査する。
# 依存は一時ディレクトリに入るのでリポジトリには残らない（初回は取得に時間がかかる）。
check-mermaid:
	@bash tools/check_mermaid.sh


# 引数なしは確認のみ。実際に移動するには APPLY=1 を付ける。
migrate-eval-paths:
	$(PY) tools/migrate_eval_paths.py $(if $(APPLY),--apply,)

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
