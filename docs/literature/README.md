# 文献要約

論文の読解メモ。PDF実体は `literature/`（Google Drive管理）を参照。

## 収録

| ファイル | 論文 | 位置づけ |
|---|---|---|
| [blocki2017_towards_human_computable_passwords.md](blocki2017_towards_human_computable_passwords.md) | Blocki, Blum, Datta, Vempala, "Towards Human Computable Passwords", ITCS 2017 | **原論文**。HCP方式・関数族 $f_{k_1,k_2}$・安全性パラメータ $s(f)$・UF-RCAゲームを定義 |
| [ogawa2025_learning_hcp_neural_models.md](ogawa2025_learning_hcp_neural_models.md) | Ogawa, Ikeda, Sakurai, "Learning Human-Computable Passwords: What Makes Them Hard (or Easy) for Neural Models?" | **直接の先行研究**。CNN/Bi-LSTM/MLPによる学習ベース攻撃。経路Bとほぼ同一の結論を先に取得 |
| [kachi2025_lagrange_interpolation_hcp.md](kachi2025_lagrange_interpolation_hcp.md) | Kachi, Viglietta, Sakurai, "Applying Lagrange Interpolation to Polynomial Expressions of Human-Computable Functions", SCIS 2025 | **理論的裏付け**。$f$ を $\mathbb{F}_{11}$ 上の多項式として明示的に表現 |

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
3. **$k_2$（最後の加算項）が安全性を担う** — $s(f)$ の式がそれを示しており，これは2026年8月に発見した「足し算のない関数では鍵の偏りがレスポンス分布に漏れる」現象の理論的裏付けになる。
