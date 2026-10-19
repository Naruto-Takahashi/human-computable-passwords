# literature — 原本の置き場

> 先行研究の PDF・スライドの実体を置く場所。**読解メモは
> [docs/literature/](../docs/literature/) にある**
>
> 📚 [ドキュメント索引](../docs/README.md) ／ 関連:
> [研究室の先行研究](../docs/literature/lab_theses.md) ・
> [関連研究の調査](../docs/literature/related_work_survey.md)

> [!IMPORTANT]
> **GitHub 上では，このディレクトリはこの README しか見えない。**
> `.gitignore` に `/literature/*` があり，**実体は追跡対象外**だからである。
> 空に見えても手元のファイルは消さないこと（先輩方の卒論など，再入手に手間がかかる）。

論文・卒論・スライドの実体はGoogle Driveで管理しています(個人名を含む資料が多いため、publicリポジトリにバイナリを直接置かない運用)。

Google Driveフォルダ: https://drive.google.com/drive/folders/1iBuo0FqA4w1V-3j4lFrm8SkHq0Xh7yJv

## 収録資料

**論文の PDF の正本は Zotero に移した**（PDF は Google Drive の `Zotero/` フォルダ。Zotero から
リンクしている）。卒論4本・原論文・小川さんの英語論文・加地先生の論文はすべてそこにある。
Google Drive の `卒業研究/03_参考資料/` には，論文以外の資料（卒論のスライド・櫻井先生の学会スライド）を置く。
同じフォルダに残っている論文の PDF は，Zotero 側と重複している。

各論文に書いてある事実は，研究に依らない個人の論文ノート（非公開）にある。
この研究にとっての位置づけは [docs/literature/](../docs/literature/README.md) にある。

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
