# 研究開発ログ（Research & Development Log）

本ファイルは，「人間計算可能なパスワード（HCP）」をベースとした推論特化型AI向けベンチマーク構築の研究における，日々の活動，実験結果，エラーログ，および考察を記録する日誌です．

---

## 1. 運用ルール
- 新しいログは**最上部（日付の新しい順）**に追加していきます．
- 各ログには以下の項目を含めます：
  - **日付と作業内容のサマリー**
  - **実施したことの詳細**
  - **得られた知見・結果・エラー**
  - **次にやること（Next Actions）**

---

## 2. 活動記録

### 2026/06/05: GitコミットID自動記録および実験結果集計の自動化
- **実施したこと**:
  - `metadata.json` 内に，実行時のGitコミットハッシュ（短縮ID）を自動的に記録する機能を実装した．（`git rev-parse --short HEAD` をプログラム内部で実行）．
  - 依存ライブラリを必要としない，純粋なPythonのみによる実験結果自動集計スクリプト [`src/summarize_results.py`](file:///home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/src/summarize_results.py) を新規に作成した．
  - 同スクリプトにより，`outputs/` 下のメタデータを自動で読み込み，Markdownテーブルとして整形されたレポート [`outputs/summary.md`](file:///home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/outputs/summary.md) を自動更新・作成できるようにした．
- **得られた知見**:
  - コミットIDが紐づくことで，過去の任意の実験データを生み出したソースコードの状態へ Git で一発で戻れるようになり，再現性が大幅に向上した．
  - 集計スクリプトによって，実験が増えた場合でも一括で進捗やモデル精度を一覧化できるようになり，報告書の作成が非常に楽になった．
- **次にやること（Next Actions）**:
  - LLM（推論特化型AI）のFew-shotプロンプティングに適した，プロンプトへ注入可能な形式のデータセット（JSON等）を生成するジェネレータの整備．

### 2026/06/05: 実験の再現性確保およびメタデータ自動記録機構の導入
- **実施したこと**:
  - 実験の再現性を高めるため，Pythonの `random`，`numpy`，および `tensorflow` の乱数シードを固定する `Utils.fix_seed()` を追加した．
  - 訓練・検証データの分割に `random_state` 引数を渡し，常に同じデータ分割が再現されるようにした．
  - 実験のメタデータ（パラメータ，学習時間，最終評価精度など）を一意なタイムスタンプ付きディレクトリ `outputs/run_YYYYMMDD_HHMMSS_{generator}_{model}/` に `metadata.json` として自動保存する機能を実装した．
  - テスト実行（`python src/main.py`）を行い，プロット画像とメタデータが正常に保存されることを確認した．
- **得られた知見**:
  - 実験を繰り返し行う際，学習時間や最終精度がメタデータとして構造化データ（JSON）で残るため，後から結果の集計や比較プロットの自動生成が非常に容易になった．
- **次にやること（Next Actions）**:
  - LLM（推論特化型AI）のFew-shotプロンプティングに適した，プロンプトへ注入可能な形式のデータセット（JSON等）を生成するジェネレータの整備．

### 2026/06/05: 研究テーマの再定義および研究計画書の策定
- **実施したこと**:
  - 卒論テーマである「人間計算可能なパスワードの安全性評価」の方向性を議論し，「実用化」から「推論特化型AIの論理・記号推論ベンチマークとしての再定義」へシフトすることを決定した．
  - [研究計画書 (plan.md)](file:///home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/research/plan.md) を作成した．
  - 本研究開発ログファイル（[log.md](file:///home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords/research/log.md)）のセットアップを行った．
- **得られた知見**:
  - HCPは暗算可能（＝短い計算ステップ，限られたメモリ）という人間の特性を満たしつつ，間接参照や剰余演算といった非線形な論理構造を持つため，LLMのコンテキスト内推論（Few-shot）の限界を測るベンチマークとして非常に親和性が高いことを整理した．
- **次にやること（Next Actions）**:
  - 第1期（6月〜7月）の目標に向け，既存の `src/computable_password_generator.py` を用いて，LLMのプロンプトに流し込める形式（JSONやCSV等）の評価用データセットを生成するスクリプトの設計を開始する．
