# 関連研究の調査（2026-10-18）

> 原論文を引用する研究・HCP の派生方式・攻撃の理論を洗い出し，論文化の際の位置づけを決めるための調査記録
>
> 📚 [ドキュメント索引](../README.md) ／ 関連: [文献要約](README.md) ・ [研究室の卒論4本](lab_theses.md) ・ [標本数の位置づけ](../experiment_index.md#標本数の位置づけ-transformer-は何件の観測を要しそれは理論ソルバーと比べてどうか1017gpu不要)

## 調べ方と限界

- 原論文（Blocki ら, ITCS 2017 / arXiv 1404.0024）の**被引用**を Semantic Scholar（約30件）と
  OpenAlex（12件）で取得し，題名で HCP に関わるものを拾った。会場は Crossref で DOI から確かめた
- 語句検索: OpenAlex（"human computable password(s)"），CiNii（日本語），英語の Web 検索
- **Google Scholar は使えていない**（API が無い）。どちらのデータベースも被引用の網羅率は低い。
  本文まで読んだのは原論文と Trenchcoat だけで，他は要旨と書誌のみ

> [!IMPORTANT]
> 2026-10-18 の会話で「Trenchcoat は arXiv のプレプリントのみで査読の記録は無い」と述べたが，
> **誤りだった。** CANS 2020（Cryptology and Network Security，LNCS）に掲載されている。

## 1. 研究室の系譜（最重要）

| 文献 | 会場 | 本研究との関係 |
|---|---|---|
| **Murata, He, Gu, Sakurai, "Towards Evaluating the Security of Human Computable Passwords Using Neural Networks"** | **WISA 2022（LNCS, 2023刊）** | R4 村田の卒論の査読付き版。**ニューラルネットで HCP の安全性を評価する研究は，すでに査読付きで出ている** |
| 櫻井「人間計算可能なパスワード認証の現状と課題：AI複雑性の観点から」 | CSS 2022 | 研究室の問題設定を述べた位置づけの論文 |
| Ogawa, Ikeda, Sakurai（2025） | 未確認（Web では見つからず） | CNN/Bi-LSTM/MLP。§5.4 で Transformer を将来課題に挙げる |
| Kachi, Viglietta, Sakurai | SCIS 2025 | $`f`$ の $`\mathbb{F}_{11}`$ 上の多項式表現 |

**含意**: 「HCP を機械学習で評価した初めての研究」とは言えない。新規性は
(1) Transformer で $`j`$ 項が解けること，(2) 離陸を決めるのが鍵の分布であることを設計で特定したこと，
(3) 古典的な攻撃との標本数の比較，に置く。Murata ら（WISA 2022）は必ず引用し，手法と結論の差分を明示する。

## 2. 原論文の系統（Blocki・Blum・Datta・Vempala ほか）

| 文献 | 会場 | 内容 |
|---|---|---|
| Blocki, Blum, Datta, "Naturally Rehearsing Passwords" | Asiacrypt 2013 | 前身の方式と公開チャレンジ |
| **Blocki ら, "Towards Human Computable Passwords"** | ITCS 2017 | 原論文。$`f_{k_1,k_2}`$・$`s(f)`$・CSP ソルバー攻撃（付録C）・統計的攻撃（付録G.1）・ガウス消去攻撃（付録G.2） |
| Blum, Vempala, "Publishable Humanly Usable Secure Password Creation Schemas" | HCOMP 2015 | サイト名からパスワードを作る方式（Cue-Pin-Select の原型） |
| Samadi, Vempala, Kalai, "Usability of Humanly Computable Passwords" | HCOMP 2018 | 利用者調査 |
| Rosenfeld, Vempala, Blum, "Human-Usable Password Schemas: Beyond Information-Theoretic Security" | arXiv 2019 | 計算量を制限した攻撃者に対する評価。いくつかの方式は，漏れた組から情報理論上の上限まで計算機で引き出せると示す |
| Blum, Vempala, "The complexity of human computation via a concrete model with an application to passwords" | PNAS 2020 | 人間の計算の複雑さのモデル |

**$`f_{k_1,k_2}`$ に代わる新しい関数族の提案は見つからなかった。** この系統の後続は
「サイト名からパスワードを作る」別の問題設定に移っている。公開チャレンジ（賞金つき）が
解かれたという報告も見つからなかった。

## 3. 派生した方式と，その攻撃

| 文献 | 会場 | 内容 |
|---|---|---|
| Rooparaghunath, Harikrishnan, Gupta, "Trenchcoat" | CANS 2020 | 人間が計算する「ハッシュ関数」（Memory Palace など）。安全性はエントロピー・LSTM での予測しやすさ・利用者調査で評価。$`f_{k_1,k_2}`$ の代替ではない |
| Blanchard ら, "Cue-Pin-Select" | COMPSAC 2020 | Blum・Vempala の方式の改良 |
| HIPHCP（"Secure Human Identification Protocol with Human-Computable Passwords"） | ISPEC 2022 | HCP を使った本人確認プロトコル |
| Grześkowiak, Krzywiecki, Niczyj, "Cryptanalysis of Human Identification Protocol with Human-Computable Passwords" | ISPEC 2023 | HIPHCP は能動・受動の攻撃で鍵の大部分が漏れる |
| "LWO vs. LWE Lattice Problems in Human-Computable Passwords Protocol" | Procedia CS 2023 | 格子問題に基づく人間計算 OTP（Matelski らの系統） |
| Ayeswarya, John Singh | ICETITE 2024 | チャレンジ応答型の HCP プロトコルの提案 |
| Kofoed, "Human Computable Passwords - Design and Analysis" | 修士論文 2015（ノルウェー） | 実装と設計の分析。本文は未確認 |

## 4. 人間による本人確認プロトコルの古典（HCP の祖先）

HCP は「人間が頭の中で計算する本人確認プロトコル」の系譜の上にある。査読者がこの分野から来る可能性が高い。

| 文献 | 内容 |
|---|---|
| Matsumoto, Imai（1991）・Matsumoto（CCS 1996）・Matsumoto, Mizutani（IEICE 1995） | 人間が計算する本人確認方式と，その安全性評価の最初期 |
| Hopper, Blum（Asiacrypt 2001） | HB プロトコル（LPN 問題に基づく） |
| Coskun, Herley（2008） | **疎なチャレンジ**（1回に秘密の一部しか使わない方式）に対する攻撃。少ない観測から秘密を絞り込む |
| Asghar, Kaafar, "When are identification protocols with sparse challenges safe?"（J. Math. Cryptology 2017） | Coskun–Herley 攻撃の必要観測数と計算量を解析的に見積もる |

原論文は Hopper–Blum 方式に対する中間一致攻撃（$`O(n^{\ell/2})`$ 時間）に触れ，HCP はチャレンジを
短い節（14記号）にする点で違うと述べている。一方で，1回のチャレンジが14個の記号しか使わない HCP は
**疎なチャレンジの方式そのもの**でもある。Coskun–Herley 攻撃が HCP に効くかを Asghar らの見積もりで
確かめることは，原論文が明示的には扱っていない論点であり，標本数の比較表に加える候補になる。

## 5. 攻撃の理論（解が埋め込まれたランダム CSP）

| 文献 | 内容 |
|---|---|
| Feldman, Perkins, Vempala（STOC 2015） | 統計的アルゴリズムの下限 $`\tilde{\Omega}(n^{r/2})`$。原論文の $`s(f)`$ の土台 |
| Feldman, Perkins, Vempala, "Subsampled Power Iteration"（arXiv 1407.2774） | $`O(n^{r/2} \log n)`$ 個の制約で埋め込まれた解を復元するスペクトル法。原論文の付録G.1 の攻撃の元 |
| Basu, Hsieh, Lin, Manohar（ICALP 2026） | 二乗和緩和で $`n^{k/2}`$ 未満の制約から解く，時間と標本の兼ね合い |
| Goldreich の一方向関数・局所的な擬似乱数生成器の解析 | HCP は「$`\mathbb{Z}_{10}`$ 上の特定の述語による局所的な CSP」と見なせ，この分野の攻撃が使える可能性がある（本研究の解釈） |

## 論文化への含意

1. **新規性の置き場所が変わる。** 「学習ベースの HCP 評価」は Murata ら（WISA 2022）・小川ら（2025）が
   先行する。本研究の差分は，Transformer での $`j`$ 項の学習，鍵の分布という仕組みの特定，
   古典的な攻撃との比較である
2. **$`f_{k_1,k_2}`$ は今も最新の関数族であり，独立した攻撃論文は見つからない。** 対象として古びてはいない
3. **比較相手の攻撃は4系統ある**: ガウス消去（付録G.2）・スペクトル法（付録G.1）・CSP ソルバー（付録C）・
   疎なチャレンジへの中間一致攻撃（Coskun–Herley）
4. 投稿先の候補として，研究室が実績を持つ WISA・ISPEC・SCIS/CSS（国内）が並ぶ。HCP の派生方式の論文も
   ISPEC に集まっている

## 残っている調査

- Google Scholar で原論文と Murata ら（WISA 2022）の被引用を確認する（このメモの被引用リストは不完全）
- Murata ら（WISA 2022）の本文を入手し，R4 の卒論との差分（追加実験の有無）を確認する
- Coskun–Herley 攻撃を HCP に当てた場合の必要観測数を，Asghar らの式で見積もる

---

## 次に読む

| | |
|---|---|
| [文献要約](README.md) | 原論文・小川ら・加地らの読解メモ |
| [研究室の卒論4本](lab_theses.md) | 直接の系譜 |

📚 [ドキュメント索引](../README.md) へ戻る
