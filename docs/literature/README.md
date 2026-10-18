# 文献要約

> 先行研究の資料一覧（実体は Google Drive）
>
> 📚 [ドキュメント索引](../README.md) ／ 関連: [研究室の卒論4本](lab_theses.md) ・ [HCP の前提知識](../hcp_background.md)

論文の読解メモ。PDF実体は `literature/`（Google Drive管理）を参照。

## 収録

| ファイル | 論文 | 位置づけ |
|---|---|---|
| [blocki2017_towards_human_computable_passwords.md](blocki2017_towards_human_computable_passwords.md) | Blocki, Blum, Datta, Vempala, "Towards Human Computable Passwords", ITCS 2017 | **原論文**。HCP方式・関数族 $`f_{k_1,k_2}`$・安全性パラメータ $s(f)$・UF-RCAゲームを定義 |
| [ogawa2025_learning_hcp_neural_models.md](ogawa2025_learning_hcp_neural_models.md) | Ogawa, Ikeda, Sakurai, "Learning Human-Computable Passwords: What Makes Them Hard (or Easy) for Neural Models?" | **直接の先行研究**。CNN/Bi-LSTM/MLPによる学習ベース攻撃。経路Bとほぼ同一の結論を先に取得 |
| [kachi2025_lagrange_interpolation_hcp.md](kachi2025_lagrange_interpolation_hcp.md) | Kachi, Viglietta, Sakurai, "Applying Lagrange Interpolation to Polynomial Expressions of Human-Computable Functions", SCIS 2025 | **理論的裏付け**。$f$ を $`\mathbb{F}_{11}`$ 上の多項式として明示的に表現 |
| [related_work_survey.md](related_work_survey.md) | 関連研究の調査（2026-10-18） | **被引用・派生方式・攻撃理論の洗い出し**。Murata ら（WISA 2022）が学習ベース評価の査読付き先行研究であること，$`f_{k_1,k_2}`$ に代わる関数族は無いことを確認 |

## 文献調査の台帳（2026-10-18〜）

| ファイル | 役割 | 誰が書くか |
|---|---|---|
| [search_log.md](search_log.md) | **検索の記録**。いつ・どこを・何で検索し，何件見つけたか | スクリプトが自動で1行足す。手で検索したら手で足す |
| [candidates.csv](candidates.csv) | **候補論文の一覧**。1論文1行 | スクリプトが「未読」で追記する。状態・関連度・メモは人が付ける |
| `<引用キー>.md` | 精読した論文のメモ | 人 |

書誌情報と PDF の正本は Zotero に置く（PDF はリポジトリに入れない）。台帳は
「何を調べ，何を読み，どう判断したか」の正本である。

**状態**: 未読 → 要旨（要旨と書誌だけ確認）→ 本文（本文を読んだ），または 除外（理由をメモに書く）

**関連度**:

| | 意味 |
|---|---|
| A | 論文の位置づけに直結する。必ず精読して引用する |
| B | 関連研究の節で触れる |
| C | 周辺。引用するかは任意 |

**検索**（`tools/lit_search.py`。使い方はファイル冒頭）:

```
python3 tools/lit_search.py cites  <DOI>        # 被引用（前向き）
python3 tools/lit_search.py refs   <DOI>        # 参考文献（後ろ向き）
python3 tools/lit_search.py search "<語句>"     # 語句検索（OpenAlex・DBLP・arXiv）
python3 tools/lit_search.py add    <DOI>        # 1本だけ足す
```

> [!WARNING]
> どのデータベースも被引用・参考文献の網羅率は低い（Murata ら の参考文献は10件しか
> 取れなかった）。**Google Scholar の「引用元」と，本文の参考文献リストで必ず補う。**

## 3本の関係

```
        Blocki et al. 2017（原論文）
        ├─ 関数族 f_{k1,k2} を提案，s(f) = min{(k2+1)/2, k1+1}
        ├─ 攻撃者モデル: 関数 f は既知，秘密写像 σ のみ未知（＝本研究のStage 2）
        └─ 「f 自体の数学的性質は将来の研究者に委ねる」と明言
             │
             ├──▶ 加地ら 2025（理論方向）
             │     f 単体を F11 上の多項式として明示表現
             │     → j項があることで f が非自明に絡み合った代数構造を持つことを示す
             │     （σ は扱わない）
             │
             └──▶ 小川ら 2025（実証方向）
                   f∘σ を学習ベース攻撃で評価（CNN/Bi-LSTM/MLP）
                   → no-j ablation で「j項こそが学習耐性の主因」を実証
                   → 将来課題として Transformer / self-attention を名指し
                        │
                        └──▶ 本研究
                              経路B（FT）: 小川らの知見をLLM微調整で再現（収束的証拠）
                              経路A（in-context）: 小川らが残した空白を埋める
```

## 本研究にとっての要点3行

1. **Stage 2（規則開示・鍵非開示）は恣意的な設定ではない** — 原論文のPassword Unforgeabilityゲーム（"The adversary is given the function f"）と厳密に一致する。
2. **経路Bの結論は新発見ではなく追試** — 小川ら(2025)がCNN/LSTMで既に同一の結論（j項＝動的参照だけが崩壊の原因）を得ている。新規性は経路A以降に置く。
3. **$`k_2`$（最後の加算項）が安全性を担う** — $s(f)$ の式がそれを示しており，これは2026年8月に発見した「足し算のない関数では鍵の偏りがレスポンス分布に漏れる」現象の理論的裏付けになる。

---

## 次に読む

| | |
|---|---|
| [研究室の卒論4本](lab_theses.md) | 直接の系譜 |
| [関連研究の調査](related_work_survey.md) | 研究室の外の HCP 研究と攻撃の理論 |

📚 [ドキュメント索引](README.md) へ戻る
