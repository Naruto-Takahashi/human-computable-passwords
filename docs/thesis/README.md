# 卒論の章立てと素材の所在

> 卒論の章立てと，各章の素材の所在。**本文は書かない**
>
> 📚 [ドキュメント索引](../README.md) ／ 関連: [第1章 貢献の主張](ch1_contribution.md) ・ [実験の一覧](../experiment_index.md) ・ [研究計画](../plan.md)

**本文はまだ書かない．** ここに置くのは，章立てと「各章に何を書くか・その根拠は
どこにあるか・まだ足りないものは何か」だけである。

理由は2つ。(1) 卒論は「捨てる」文書だが，リポジトリの価値は失敗が残っていることにある。
ドキュメント＝下書きにすると，論文に要らないものを消したくなる圧力がかかる。
(2) 運用文書（`make status` の説明など）と論文は読者も目的も違う。

したがってこのファイルの役目は**下書きではなく，逆算して残タスクを洗い出すこと**である。
提出締切は 2027-02-09（火）15:00，試問は 2027-02-16（火）。本文の執筆は12月から
（[../plan.md](../plan.md) §5）。

## 章立て

研究室の卒論（R6 池田・R7 小川）で一致している7章構成に従う。
2026-10-30 に経路C主軸（[../plan.md](../plan.md) v3）へ組み替えた。

| 章 | 中身 | いま書けるか |
|---|---|---|
| 1 緒論 | 背景・系譜・問題の所在・貢献 | 主張は決まった（[ch1_contribution.md](ch1_contribution.md)）。Murata ら待ち |
| 2 背景知識 | 認証・機械学習（Transformer） | 一部空白 |
| 3 既存研究 | HCP・学習による評価の系譜・古典的な攻撃 | **ほぼ書ける** |
| 4 研究手法 | 経路Cの構成・離陸率・基準線・鍵の信号 | **書ける** |
| 5 結果 | 鍵が決める → 介入 → 同じ鍵の CNN → 古典的な攻撃との比較 | C1〜C3 は書ける。C5〜C7・G1 待ち |
| 6 考察 | 理論との対応・弱い鍵の割合・対策と代償・限界 | 一部書ける |
| 7 結論 | | 結果待ち |

---

## 第1章 緒論

**書くこと**: 研究背景（パスワード認証 → HCP）／学習による評価の系譜／問題の所在／本研究の貢献

**素材**: [ch1_contribution.md](ch1_contribution.md)（中心主張・貢献の表・言わないこと・結果による分岐），
[../authentication_background.md](../authentication_background.md)

**足りないもの**
- Murata ら（WISA 2022）の本文。R4 の卒論との差分を確かめないと，新規性の段落が書けない

## 第2章 背景知識

**書くこと**: 2.1 認証（パスワード認証・チャレンジレスポンス認証）／2.2 機械学習（Transformer・勾配学習）

**素材**
- 2.1 → [../authentication_background.md](../authentication_background.md)
- 2.2 → [../llm_training_basics.md](../llm_training_basics.md)（LLM 寄りで過剰。Transformer エンコーダと self-attention に絞る）

**足りないもの**
- 2.1 は**出典が未確定**なので執筆時に一次資料へ当たる（同ファイルの「要確認」節に一覧がある）
- 2.2 の Transformer の説明は経路C用に書き起こす必要がある

## 第3章 既存研究

**書くこと**: 3.1 人間計算可能なパスワード（定義・関数族・$`s(f)`$・$`r(f)`$）／3.2 学習による安全性評価の系譜／
3.3 古典的な攻撃（CSP ソルバー・ガウス消去・スペクトル法）／3.4 勾配学習の理論（短く）

**素材**
- 3.1 → [../hcp_background.md](../hcp_background.md)，
  [../literature/related_work_survey.md](../literature/related_work_survey.md) §2
- 3.2 → [../literature/lab_theses.md](../literature/lab_theses.md)
- 3.3 → [../literature/related_work_survey.md](../literature/related_work_survey.md) §2・§5
- 3.4 → [../literature/related_work_survey.md](../literature/related_work_survey.md) §6
- 各論文の事実（手法・条件・数値）は非公開の論文ノートにある

**足りないもの**
- 加地ら(2025)の代数的な表現を 3.1 に入れるか 3.2 に入れるかは未決

## 第4章 研究手法

**書くこと**: 4.1 脅威モデル（関数は既知・鍵は未知。Transformer は $`f`$ を使わない攻撃者）／
4.2 経路Cの構成／4.3 測り方（離陸率・鍵ごとの基準線・鍵と初期値の分離）／
4.4 鍵の信号（$`I_1`$ と，学習せずに計算できること）

**素材**
- 構成 → [../experiment_index.md](../experiment_index.md) の実験C1・C2，[../cli_reference.md](../cli_reference.md)
- 測り方 → [../experiment_index.md](../experiment_index.md) の方法論上の規則8項目，
  [../measurement_audit.md](../measurement_audit.md)
- 鍵の信号 → [../experiment_index.md](../experiment_index.md) の実験C3「1変数信号 $`I_1`$」，
  `experiments/signal_strength.py`

**足りないもの**
- 規則8項目は経路Bで得たもの。経路Bを本文に出さずに，規則の根拠をどこまで書くか（付録に回すか）を決める

## 第5章 結果

**書くこと（案）**
- 5.1 Transformer は $`j`$ 項を解く。ただし離陸は鍵で決まる（C1・C2）
- 5.2 鍵の偏りが離陸を予測する（C2.1・R1）
- 5.3 介入: 双子の鍵（C3）・数字をそろえた鍵（C5）・付け替え（C6）
- 5.4 同じ鍵での CNN（C7）
- 5.5 古典的な攻撃との比較（標本数の位置づけ・G1）

**素材**: [../experiment_index.md](../experiment_index.md)，[../log.md](../log.md)

**足りないもの**: C5・C6・C7・G1・R1（[../plan.md](../plan.md) §3）

## 第6章 考察 / 第7章 結論

考察で扱う論点（一部はいま書ける）。

- 原論文の $`r(f)=k_2+1`$ と，ランダムな鍵で崩れる分が学習の足がかりになること
- SGD の学習可能性の理論（leap・merged-staircase）との対応と，前提のずれ
  （[../literature/related_work_survey.md](../literature/related_work_survey.md) §6）
- 弱い鍵の割合が $`N`$ とともにどう減るか（C3 の $`I_1`$ の表）
- 対策（数字をそろえた鍵）と代償（鍵の空間），ガウス消去には効かないこと
- $`N`$ の効果が関数によって残る理由（C3 の $`f_{1,3}`$，未特定）
- 限界: 学習器は1種類，予算の範囲，$`N`$ は小さい

---

## いま進めるべきこと

1. Murata ら（WISA 2022）の本文の入手（大学のネットワーク）
2. C5 の実装と実行（設計は [../experiment_index.md](../experiment_index.md)）
3. 第3章・第4章は素材がそろったので，12月の執筆を待たずに骨組みを作ってよい
4. 2.1 の出典の確定（「要確認」5項目）

---

## 次に読む

| | |
|---|---|
| [第1章 貢献の主張](ch1_contribution.md) | 何を主張するか |
| [研究計画](../plan.md) | 問い・実験計画・スケジュール |
| [実験の一覧](../experiment_index.md) | 第5章の素材 |

📚 [ドキュメント索引](../README.md) へ戻る
