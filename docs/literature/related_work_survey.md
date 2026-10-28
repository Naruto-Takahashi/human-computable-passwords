# 関連研究の調査（2026-10-18）

> 原論文を引用する研究・HCP の派生方式・攻撃の理論を洗い出し，論文化の際の位置づけを決めるための調査記録
>
> 📚 [ドキュメント索引](../README.md) ／ 関連: [文献の管理](README.md) ・ [研究室の先行研究](lab_theses.md) ・ [標本数の位置づけ](../experiment_index.md#標本数の位置づけ-transformer-は何件の観測を要しそれは理論ソルバーと比べてどうか1017gpu不要)

## 目次

- [調べ方と限界](#調べ方と限界)
- [1. 研究室の系譜（最重要）](#1-研究室の系譜最重要)
- [2. 原論文の系統](#2-原論文の系統blockiblumdattavempala-ほか)
- [3. 派生した方式と，その攻撃](#3-派生した方式とその攻撃)
- [4. 人間による本人確認プロトコルの古典](#4-人間による本人確認プロトコルの古典hcp-の祖先)
- [5. 攻撃の理論](#5-攻撃の理論解が埋め込まれたランダム-csp)
- [6. 機械学習の理論](#6-機械学習の理論勾配学習で疎な関数が学べるか)
- [論文化への含意](#論文化への含意)
- [残っている調査](#残っている調査)

## 調べ方と限界

- 原論文（Blocki ら, ITCS 2017 / arXiv 1404.0024）の**被引用**を Semantic Scholar（約30件）と
  OpenAlex（12件）で取得し，題名で HCP に関わるものを拾った。会場は Crossref で DOI から確かめた
- 語句検索: OpenAlex（"human computable password(s)"），CiNii（日本語），英語の Web 検索
- 2026-10-19 に Google Scholar の被引用（28件）と突き合わせた。21件は既出，新規7件は博士論文・前の版・
  無関係の文献で，研究室の外で $`f_{k_1,k_2}`$ を攻撃・改良した論文は無かった
- 検索の記録・候補の選別台帳・各論文の事実（論文ノート）は，研究に依らない個人の保管庫（非公開）にある。
  このファイルには**本研究にとっての位置づけ**だけを書く

> [!IMPORTANT]
> 2026-10-18 の会話で「Trenchcoat は arXiv のプレプリントのみで査読の記録は無い」と述べたが，
> **誤りだった。** CANS 2020（Cryptology and Network Security，LNCS）に掲載されている。

## 1. 研究室の系譜（最重要）

| 文献 | 会場 | 本研究との関係 |
|---|---|---|
| **Murata, He, Gu, Sakurai, "Towards Evaluating the Security of Human Computable Passwords Using Neural Networks"** | **WISA 2022（LNCS, 2023刊）** | R4 村田の卒論の査読付き版。**ニューラルネットで HCP の安全性を評価する研究は，すでに査読付きで出ている** |
| 櫻井「人間計算可能なパスワード認証の現状と課題：AI複雑性の観点から」 | CSS 2022 | 研究室の問題設定を述べた位置づけの論文 |
| Ogawa, Ikeda, Sakurai | 未公開の原稿（2026年5月版。査読を受けたあとの改訂版） | CNN/Bi-LSTM/MLP。§5.4 で Transformer を将来課題に挙げる。公開の扱いは未確認 |
| Kachi, Viglietta, Sakurai | SCIS 2025 | $`f`$ の $`\mathbb{F}_{11}`$ 上の多項式表現 |

**含意**: 「HCP を機械学習で評価した初めての研究」とは言えない。新規性は
(1) Transformer で $`j`$ 項が解けること，(2) 離陸を決めるのが鍵の分布であることを設計で特定したこと，
(3) 古典的な攻撃との標本数の比較，に置く。Murata ら（WISA 2022）は必ず引用し，手法と結論の差分を明示する。
研究室の系譜との対応は [lab_theses.md](lab_theses.md) にある。

**小川ら（英語論文）と本研究**: 経路Bの主結論（記憶・合成は学習できるが，動的参照だけがデータ量を
増やしても崩壊する）は，小川らの「$`j`$ 項を除くと学習できる」とアーキテクチャが違うだけで同じ知見であり，
収束的証拠として位置づける。経路Cは小川ら §5.4 の将来課題（attention・Transformer 系で試す）に当たり，
$`N=26`$ では $`j`$ 項を解く。経路A（in-context 推論）は学習パラダイム（重みを更新しない）と目標
（$`\sigma`$ そのものの復元）の両方で小川らの枠組みの外にある。小川らの脅威モデルは $`\sigma`$ の復元を
厳密ソルバーの担当として別に置いているので，「先行研究の未実施課題を実行する」ではなく
「関数近似から逆問題への再定式化」として主張する（2026-08-18 に原文で確認）。

**加地らと本研究**: 加地らは HCP の秘密写像を含まない $`f`$ 単体を $`\mathbb{F}_{11}`$ 上の多項式として表し，
$`j`$ 項が $`f`$ 全体を絡み合った構造にすることを示した。$`f \circ \sigma`$ を学習で扱う本研究とは相補的である。
加地らが提案する準単項式 $`x_{f(x_k)}`$（自己写像を挟んだ添字化）は，本研究の `pointer_chain` と同じ族に属する。
引用の注意: 加地らの論文の $`\sigma`$ は添字化の関数（$`x`$ と $`t`$ から $`x_t`$ を取り出す）で，HCP の秘密写像とは別物である。
また主定理（Theorem 1.5）と Corollary 2.7 の2つ目の因子は印刷では $`\sum_k k^{i} M_k`$ と読めるが，
証明と数値計算（2026-10-19，ランダムな入力30点）からは $`k^{j}`$ が正しく，誤植の可能性が高い。

## 2. 原論文の系統（Blocki・Blum・Datta・Vempala ほか）

| 文献 | 会場 | 内容 |
|---|---|---|
| Blocki, Blum, Datta, "Naturally Rehearsing Passwords" | Asiacrypt 2013 | 前身の方式と公開チャレンジ |
| **Blocki ら, "Towards Human Computable Passwords"** | ITCS 2017 | 原論文。$`f_{k_1,k_2}`$・$`s(f)`$・CSP ソルバー攻撃（付録C）・統計的攻撃（付録G.1）・ガウス消去攻撃（付録G.2） |
| Blum, Vempala, "Publishable Humanly Usable Secure Password Creation Schemas" | HCOMP 2015 | サイト名からパスワードを作る方式（Cue-Pin-Select の原型） |
| Samadi, Vempala, Kalai, "Usability of Humanly Computable Passwords" | HCOMP 2018 | 利用者調査 |
| Rosenfeld, Vempala, Blum, "Human-Usable Password Schemas: Beyond Information-Theoretic Security" | arXiv 2019 | 計算量を制限した攻撃者に対する評価。いくつかの方式は，漏れた組から情報理論上の上限まで計算機で引き出せると示す |
| Blum, Vempala, "The complexity of human computation via a concrete model with an application to passwords" | PNAS 2020 | 人間の計算の複雑さのモデル |

**原論文と本研究の対応**:

- **攻撃者モデル**: 原論文の攻撃ゲーム（§2.3）は関数 $`f`$ を攻撃者に与え，$`\sigma`$ だけを隠す。
  本研究の Stage 2（規則を開示し鍵を隠す）と経路Cの設定はこれに一致する（ケルクホフスの原理）。
- **関数族**: `func_13`・`func_22`・`func_31` は $`f_{1,3}`$・$`f_{2,2}`$・$`f_{3,1}`$ に対応する。
- **$`k_2`$ の役割**: $`r(f) = k_2+1`$（$`k_2`$ 個の変数を固定しても出力は一様）は，足し算を省いた関数
  （`pointer_k` など，$`k_2=0`$）で鍵の数字の偏りが応答の分布に漏れる理由であり，経路Cで鍵の偏りが
  学習の足がかりになる理由（1変数信号 $`I_1`$）でもある。
- **$`n=26`$ の扱い**: 原論文は $`n=26`$ を安全でないと注意している。本研究の $`N=26`$ は安全な設定の再現ではなく，
  学習可能性を測るための難易度の設定である。$`N=26`$ という値自体は，原論文の例示
  （アルファベット26文字から数字への写像）に由来する。
- **古典的な攻撃**: 付録C の CSP ソルバー，付録G のガウス消去・スペクトル法を，標本数の比較表の基準にする
  （[../experiment_index.md](../experiment_index.md) の「標本数の位置づけ」）。原論文は，計算量に制限の無い攻撃者なら
  $`O(n)`$ 組で破れる（安全性は情報理論的ではない，脚注2）と書いており，実験13 の「鍵が一意に決まるのは約 $`1.1n`$ 組」と合う。
- **中国剰余定理による分解**: 原論文は付録G（arXiv 版 p.42〜43）で，$`\sigma`$ を mod 2 と mod 5 の部分に分け，
  一方が易しくても他方の復元に多くの観測が要る関数がある，と論じている。C1-N100 で正解率が 0.1・0.2・0.5・1.0 の
  4段に分かれたこと（mod 2 だけ・mod 5 だけ解けた）の読み方の裏付けとして引用できる。
- **小さい $`n`$ での指標**: 原論文は $`n \le 100`$ では $`10^{\sqrt{n}}`$ 程度の時間をかける攻撃が現実的になりうるとし，
  $`s(f)`$ ではなく $`\min\lbrace r(f)/2, 1+g(f)/2 \rbrace`$ を最大にする方がよいかもしれない，と書く（Remark 4・付録B）。
  小さい $`n`$ で難しさが $`s(f)`$ の順に並ばない（C1・小川ら）ことと向きが合う。
- **下限の仕組み**: 統計的アルゴリズムの下限（Theorem 3）は，$`r(f)`$ より低い次数のフーリエ係数が0になることから来る。
  経路Cの「1変数の相関（$`I_1`$）が無いと離陸しない」は，この構造の最も低い次数の場合にあたる。
  ニューラルネットの勾配学習との対応は §6 にある。
- **公開チャレンジ**: 解かれたのは $`f_{2,2}`$・$`n=30`$・$`m=300`$ の1件だけ（原論文の CSP ソルバー自身，付録B 表3）。

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

## 6. 機械学習の理論（勾配学習で疎な関数が学べるか）

§5 は「どんな攻撃でも何組要るか」の理論である。経路Cが問うのは「**勾配学習**が離陸するか」で，
こちらは少数の変数に依存する関数（疎な関数）を SGD で学ぶ理論が扱う。2026-10-28 に4本を全ページ読んだ。

| 文献 | 会場 | 示したこと |
|---|---|---|
| Barak, Edelman, Goel, Kakade, Malach, Zhang, "Hidden Progress in Deep Learning: SGD Learns Parities Near the Computational Limit" | NeurIPS 2022 | $`n`$ ビット中 $`k`$ ビットのパリティを，SGD は統計的な下限に近い $`n^{O(k)}`$ 反復で学ぶ。損失が平らな間も内部では進んでいる（hidden progress） |
| Abbe, Boix-Adsera, Misiakiewicz, "The merged-staircase property: a necessary and nearly sufficient condition for SGD learning of sparse functions on two-layer neural networks" | COLT 2022 | 2層ネットが $`O(d)`$ 標本で学べるのは，低い次数の項から1変数ずつ足していける「階段」を持つ関数に（ほぼ）限る |
| Abbe, Boix-Adsera, Misiakiewicz, "SGD learning on neural networks: leap complexity and saddle-to-saddle dynamics" | COLT 2023 | 一度に新しく足す変数の数の最大値（leap）で，必要な反復数が $`\tilde{\Theta}(d^{\max(\mathrm{Leap}-1,1)})`$ と決まる。学習は停滞と急な降下を繰り返す |
| Saxena, Alfarano, Charton, Allen-Zhu, Wenger, Lauter, "Making Hard Problems Easier with Custom Data Distributions and Loss Regularization: A Case Study in Modular Arithmetic" | arXiv 2024 | 訓練データに疎な入力（0の多い易しい例）を混ぜると，一様な入力では学べない $`N`$ 項の和 $`\bmod q`$ を $`N=128`$ まで学べる |

**本研究との対応**:

- **鍵の偏りは，学習の最初の一段を作る（Abbe ら 2022・2023 の枠で読んだ本研究の解釈）。**
  偏りの無い鍵では $`f \circ \sigma`$ は $`r(f)=k_2+1`$ 個未満の変数と無相関で（原論文 Theorem 3），
  学習の最初の一歩から $`k_2+1`$ 個の変数を同時に捉える必要がある。leap が大きい状態である。
  鍵の数字が偏ると1変数の相関 $`I_1`$ が生まれ，これが階段の最初の段になる。
  実験C3 の「$`I_1`$ が離陸率と相関する」（[../experiment_index.md](../experiment_index.md)）はこの絵と向きが合う。
- **C1-N100 の4段の正解率は，停滞と降下の繰り返し（saddle-to-saddle）として読める。**
  mod 2 だけ・mod 5 だけ解けた段で止まるのは，一部の成分を学んだ鞍点で予算が尽きた状態にあたる。
  実験7 の教訓（測っていたのは予算の中で離陸が起きたか）も，停滞の長さが問題の大きさで伸びるという理論と整合する。
- **離陸を決めるものが，理論の典型的な設定と違う。** Barak らは入力を一様に固定し，離陸は初期値の運でばらつく。
  本研究では鍵5本 × 初期値4通りの分解で，鍵が分散の85〜100%を説明した。理論の言葉では，
  入力の分布でも初期値でもなく**学ぶ関数そのもの**が鍵で変わる場合にあたる。
- **Saxena らとは「分布を変えると学べる」点が似るが，変えている側が違う。** Saxena らは入力の分布を変え，
  学ぶ関数は同じままである。本研究で離陸を決める鍵の偏りは，関数そのものを易しくする。
  「最も近い先行例」として引くときは，この違いを明記する。
- **攻撃の候補（未実施）**: HCP の攻撃者は観測を選べない（受動的）ので，疎な問題を本物の鍵に答えさせることはできない。
  一方，自作の鍵なら易しい問題を混ぜて事前学習でき，そのあと本物の観測で微調整する攻撃は設計できる。
- **GPU 不要の次の分析の候補**: 鍵ごとに $`f \circ \sigma`$ の $`\mathbb{Z}_{10}`$ 上のフーリエ係数を次数ごとに計算し，
  $`I_1`$（1次）で説明しきれない離陸のばらつき（C2.1再測の $`f_{3,1}`$ など）を2次以上の重みが説明するかを確かめる。

> [!IMPORTANT]
> **理論をそのまま当てはめて数値を予言することはできない。** 4本の理論は，ブール値かガウスの入力，
> 2層ネット（Saxena らを除く），次元 $`d`$ に対して固定された少数の変数，を前提にする。
> HCP の入力は $`N`$ 個の記号から14個を選ぶチャレンジで，次元 $`d`$ との対応が素直でない。
> $`j`$ 項は入力によって参照先が変わるため，固定の変数集合に依存する関数でもない。
> 言えるのは「低い次数の成分があるほど易しい」という**向き**までで，$`N \approx 100`$ の壁の位置は予言できない。

引用の注意: Saxena らの訓練分布の式 `f_inv_sqrt` は，印刷どおりに読むと本文の説明と逆向きの偏りになる。
公開実装と表3の KL の値からは「非0の個数 $`n`$ に対して $`1/\sqrt{N-n+1}`$ に比例」が正しい。

## 論文化への含意

1. **新規性の置き場所が変わる。** 「学習ベースの HCP 評価」は Murata ら（WISA 2022）・小川ら（2025）が
   先行する。本研究の差分は，Transformer での $`j`$ 項の学習，鍵の分布という仕組みの特定，
   古典的な攻撃との比較である
2. **$`f_{k_1,k_2}`$ は今も最新の関数族であり，独立した攻撃論文は見つからない。** 対象として古びてはいない
3. **比較相手の攻撃は4系統ある**: ガウス消去（付録G.2）・スペクトル法（付録G.1）・CSP ソルバー（付録C）・
   疎なチャレンジへの中間一致攻撃（Coskun–Herley）
4. **経路Cの結果は，機械学習の理論の側からも位置づけられる。** 鍵の偏りが低い次数の成分（階段の最初の段）を作る，
   という読みは Abbe らの枠と向きが合う。ただし理論の前提と HCP の設定はずれるので，主張は向きに留める（§6）
5. 投稿先の候補として，研究室が実績を持つ WISA・ISPEC・SCIS/CSS（国内）が並ぶ。HCP の派生方式の論文も
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
| [研究室の先行研究と本研究の位置づけ](lab_theses.md) | 直接の系譜 |

📚 [ドキュメント索引](../README.md) へ戻る
