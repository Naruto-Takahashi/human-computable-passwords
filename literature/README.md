# literature — 原本の置き場

> 先行研究の PDF・スライドの実体を置く場所。**読解メモは
> [docs/literature/](../docs/literature/) にある**
>
> 📚 [ドキュメント索引](../docs/README.md) ／ 関連:
> [研究室の卒業研究](../docs/literature/lab_theses.md) ・
> [小川ら英語論文](../docs/literature/ogawa2025_learning_hcp_neural_models.md)

> [!IMPORTANT]
> **GitHub 上では，このディレクトリはこの README しか見えない。**
> `.gitignore` に `/literature/*` があり，**実体は追跡対象外**だからである。
> 空に見えても手元のファイルは消さないこと（先輩方の卒論など，再入手に手間がかかる）。

論文・卒論・スライドの実体はGoogle Driveで管理しています(個人名を含む資料が多いため、publicリポジトリにバイナリを直接置かない運用)。

Google Driveフォルダ: https://drive.google.com/drive/folders/1iBuo0FqA4w1V-3j4lFrm8SkHq0Xh7yJv

## 収録資料

- R4_村田.pdf / R4_村田_卒論スライド.pptx
- R5_丸野.pdf
- R6_池田.pdf / R6_池田_卒論スライド.pptx
- R7_小川.pdf / R7_小川_卒論スライド.pptx
- Towards Human Computable Passwords.pdf
- 櫻井_学会スライド.pptx
- 小川さん_英語論文.pdf … **手元に未取得**（2026-09-20 時点）
- 加地先生.pdf … **手元に未取得**（2026-09-20 時点）

**この一覧は Google Drive の中身**であり，手元にあるとは限らない。
上の2件は未取得である。小川さんの英語論文は週次報告で数値を引用している
（$f_{2,2}$ で平均 0.2872 ± 0.1651，最大 68.58%）ので，原文にあたる必要が
生じたら Drive から取得すること。要約は
[docs/literature/ogawa2025_learning_hcp_neural_models.md](../docs/literature/ogawa2025_learning_hcp_neural_models.md)
にある。

新しい資料を追加する場合は、上記Google Driveフォルダにアップロードし、このリストを更新してください。

## 読み方

R4・R5 の PDF は ToUnicode CMap を持たないため，普通に開くと文字が化ける。
専用の読み取りツールを使うこと。

```
python3 tools/read_pdf.py literature/R4_村田.pdf --toc
```

## 次に読む

- [研究室の卒業研究（R4〜R7）の要約](../docs/literature/lab_theses.md) — 各卒論の章立て・手法・結果
- [先行研究の見取り図](../docs/literature/README.md) — どの論文がどうつながるか
