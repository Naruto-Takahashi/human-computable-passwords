# 人間計算可能パスワード (HCP) に基づく LLM のルール実行（演繹）およびルール逆推定（帰納）の限界評価ベンチマーク

このリポジトリは，  
**人間計算可能パスワード（Human-Computable Password，HCP）に基づく LLM のルール実行（演繹）およびルール逆推定（帰納）の限界評価ベンチマーク**  
に関する研究コードおよび研究資料をまとめたものです．

---

## 概要

人間計算可能パスワード（HCP）とは，ユーザーが記憶している秘密のテーブル（鍵）と，頭の中で実行可能な簡素なアルゴリズムを用いて，提示されたランダムな「チャレンジ」に対する「レスポンス」を暗算で計算し，認証を行う仕組みです．

本研究では，HCPが持つ「人間の暗算で実行できる簡潔さ」と「間接参照（ポインタ）やモジュロ演算（剰余）などの構造的・非線形なアルゴリズム関係」という性質に着目し，**LLMにおける「ルール実行（演繹）およびルール逆推定（帰納）の限界（臨界点）」を定量的に明らかにするためのベンチマーク**として再定義しました．

予備実験において，ローカルLLM単体では入出力ペアのみから背後にあるルールを完全逆推定することはほぼ不可能であることが示されました．本ベンチマークでは，完全に不可能なブラックボックス状態から出発し，プロンプトへ提示する情報（アルゴリズム仕様や鍵の部分開示数 $K$）を段階的に変化（Stage 0〜3）させていくことで，**AIの推論（ルール実行・ルール逆推定）が「崩壊」から「成功」へと転移する境界（相転移境界）**を数理的・実証的に特定・スキャンします．

また，実験結果のログは，LLMの思考過程と解答の成否を明確に追跡できるよう，大文字のステータスを用いた連番形式（例：`001_CORRECT.md`，`002_INCORRECT.md`）で詳細に記録されます．

---

## ディレクトリ構造

本リポジトリのディレクトリ構成および主要ファイルの説明は以下の通りです．

```text
human-computable-passwords/
├── src/                       # ソースコード（ライブラリ）
│   ├── hcp/                   # 研究の中核パッケージ（アルゴリズム定義の単一情報源）
│   │   ├── algorithms.py      # HCPアルゴリズム定義（計算・ルール文・参照コード・解説）+ 自己検証
│   │   ├── dataset.py         # 鍵シード/データシード分離のデータセット生成
│   │   ├── prompts.py         # Stage 0〜3 × タスク（predict / recover_key）のプロンプト構築
│   │   ├── clients.py         # Gemini / Ollama / Mock / LoRA クライアント
│   │   ├── executor.py        # LLM出力のパース・鍵テーブル抽出・生成コード実行
│   │   ├── evaluation.py      # 実験実行・採点・記録（応答精度・鍵復元率）
│   │   ├── solver.py          # 厳密ソルバー（整合鍵の数え上げ=情報限界，鍵復元=計算可解性）
│   │   └── plotting.py        # 学習曲線などの可視化
│   └── baseline_ml/           # 従来ML（CNN等）ベースライン用モジュール
├── experiments/               # 実験の実行スクリプト
│   ├── run_eval.py            # 統一評価ランナー（predict / recover_key）
│   ├── sweep.py               # N×K×アルゴリズム×シードのスイープ（レジューム対応）
│   ├── info_limit.py          # 情報理論的限界 N*_info の測定
│   ├── summarize.py           # 評価結果の自動集計（summary_llm.{md,csv}）
│   ├── train_finetuning.py    # QLoRAファインチューニング
│   ├── train_baseline.py 等   # 従来MLベースライン
│   └── batch/                 # 夜間バッチ（デタッチ実行用 .sh）
├── tools/                     # 補助ツール（Google Drive 同期等）
├── legacy/                    # 旧実装（参照用，動作保証なし）
├── docs/                      # 計画書・ログ・リファクタリングノート
│   ├── plan.md               # 研究計画書（v2, 2026-07-18改訂）
│   ├── refactor_notes.md      # 2026-07 監査とリファクタリングの記録
│   ├── reports/               # 週次進捗報告
│   └── experiment_guide.md, log.md
├── Makefile                   # test / smoke / summarize / sync 等の運用タスク
├── literature/                # 先行研究の文献
├── results/                   # 実験結果
│   ├── llm_eval/              # LLM評価（モデル/アルゴリズム/タスク/条件/シードの階層）
│   ├── llm_finetune/          # FT学習の成果物（メタデータ・学習曲線）
│   ├── ml_baseline/           # 従来MLベースラインの結果
│   ├── solver/                # 情報限界 N*_info（ソルバー出力, Git管理）
│   ├── figures/               # 報告用の図（Git管理）
│   ├── logs/                  # 実験バッチの実行ログ
│   └── summary_llm.{md,csv}   # 自動集計（Git管理）
├── flake.nix / flake.lock     # Nix (Flakes) 環境定義
└── requirements.txt
```

---

## 本研究の意義

1. **「データ汚染（Data Contamination）」からの完全な脱却**:  
   独自のアルゴリズムと乱数シードから無限に未知の入出力パターンを合成可能なため，LLMが丸暗記している懸念のない純粋な「インコンテキスト推論能力（ルールの実行と逆推定）」を測定できます．
2. **推論能力が崩壊する「相転移境界（臨界点）」の特定**:  
   秘密鍵の部分開示（$K$ マス公開）などを段階的にスキャンし，AIが「崩壊」から「解読（復元）」へと移行する推論能力の限界値を境界探索できます．
3. **AIの暗号解読能力（Cryptanalysis）の実践的評価**:  
   流出した認証データから背後の秘密ルールやテーブルを再構築させる行為は，一種の「既知平文攻撃」であり，AIの敵対的耐性やセキュリティリスクを評価する指標となります．
4. **従来の機械学習との「データ効率性」の対比**:  
   数万 of データを用いた「教師あり学習」によって近似的に関数を再現する従来の機械学習に対し，僅かな Few-shot から論理構造を理解しようとするLLMの推論バイアスの違いを測定します．

---

## 実験

### 開発環境の構築

`Nix` (Flakes) と `direnv` を用いて環境を管理しています．

```bash
direnv allow
```

以降，ディレクトリに入るだけで必要なライブラリが自動的に読み込まれます．

### 動作確認

```bash
make test    # アルゴリズム自己検証 + ソルバー健全性チェック
make smoke   # mock プロバイダによる E2E ドライラン（predict / recover_key）
```

### LLM 評価実験

```bash
# 応答予測タスク（paradigm: pure = JSON回答 / pot = Pythonコード実行）
python experiments/run_eval.py --task predict --provider ollama --model qwen2.5:7b \
    --algorithm func_22 --stage 2 --n_shot 30 --n_test 50 --key_seeds 0-4

# 鍵復元タスク（観察データから鍵テーブルを丸ごと逆推定させ，鍵復元率を直接測定）
python experiments/run_eval.py --task recover_key --provider ollama --model qwen2.5:7b \
    --algorithm func_22 --stage 2 --n_shot 30 --key_seeds 0-4

# 相転移スイープ（N×K×シードの直積を一括実行．中断しても再実行で続きから走る）
python experiments/sweep.py --task recover_key --provider ollama --model qwen2.5:7b \
    --algorithms func_22 --stage 2 --n_shots 10,20,30,40,50,75,100 --key_seeds 0-4

# 情報理論的限界 N*_info の基準線（厳密ソルバーによる整合鍵数の数え上げ）
python experiments/info_limit.py --algorithm func_22 --n_shots 5,10,20,26,30,40,50 --key_seeds 0-4

# 評価結果の集計（summary_llm.md / summary_llm.csv の生成）
make summarize
```

- **出力構造**: `results/llm_eval/<モデル>/<アルゴリズム>/<タスク>/n<N>_stage<S>_k<K>/ks<鍵シード>_ds<データシード>/` に自動整理され，プロンプト実物・生レスポンス・`metrics.json` が保存されます．
- 設計変更の経緯と監査結果は [docs/refactor_notes.md](docs/refactor_notes.md) を参照してください．

### 従来の機械学習モデルの学習

```bash
python experiments/train_baseline.py       # 個別モデルの学習
python experiments/summarize_baseline.py   # 学習結果の集計
```

---

## ドキュメント・実行結果へのリンク

- [HCP LLM 実験実行ガイド (`experiment_guide.md`)](docs/experiment_guide.md)
- [研究計画書 (`plan.md`)](docs/plan.md)
- [研究ログ (`log.md`)](docs/log.md)
- [学習実験結果のサマリー (`summary.md`)](results/summary.md)
- [LLMベンチマーク結果のサマリー (`summary_llm.md`)](results/summary_llm.md)

---

### ファインチューニング（QLoRA）

torch 系依存は nix develop に含まれないため `.venv/bin/python` を使用します。paradigm `pot` は教師データに秘密鍵がリークするため廃止されました（`docs/refactor_notes.md` 参照）。

```bash
# 1. ファインチューニングの実行（学習済みアダプターは results/llm_finetune/ に保存）
.venv/bin/python experiments/train_finetuning.py --model Qwen/Qwen2.5-3B-Instruct \
    --algorithm func_22 --paradigm rationale --stage 2 --n_train 200

# 2. 共通スクリプトによる評価（学習時と同じ key_seed / stage を指定すること）
.venv/bin/python experiments/run_eval.py --provider lora \
    --model results/llm_finetune/qwen2.5_3b/func_22/run_XXXXXXXX_XXXXXX \
    --algorithm func_22 --stage 2 --key_seeds 0 --n_test 100
```
