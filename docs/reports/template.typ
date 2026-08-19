// =============================================================================
// 週次報告の体裁（pandoc --pdf-engine=typst 用テンプレート）
//
// 中身は Typst Universe の "js" パッケージに任せている。
//   https://typst.app/universe/package/js/
//   奥村晴彦氏による，LaTeX の jsarticle / jsbook 相当のテンプレート。
// 日本の学術文書で見慣れた体裁で，独自の装飾は入っていない。
// このファイルは js と pandoc の橋渡しだけを行い，体裁そのものは持たない。
//
// フォントについて：
//   js の既定は原ノ味（Harano Aji）だが nixpkgs に無いため，その元となった
//   Source Han を指定している（同一設計）。システムの Noto CJK は可変フォントで
//   Typst が太字を出せないので使わない（docs/reports/README.md 参照）。
// =============================================================================

#import "@preview/js:0.1.3": *

#show: js.with(
  lang: "ja",
  seriffont: "New Computer Modern",
  seriffont-cjk: "Source Han Serif",
  sansfont: "Source Han Sans",
  sansfont-cjk: "Source Han Sans",
  paper: "$if(papersize)$$papersize$$else$a4$endif$",
  fontsize: $if(fontsize)$$fontsize$$else$10pt$endif$,
  cols: $if(columns)$$columns$$else$1$endif$,
)

// ---------------------------------------------------------------------------
// js の既定からの変更点。増やすときは理由をここに書くこと。
// ---------------------------------------------------------------------------

// (0) 章・節の採番は frontmatter の section-numbering がある時だけ行う。
//     js は常に採番するが，見出しに番号を手打ちしている古い報告書
//     （2026-08-18 以前）が「1 1 …」と二重になってしまうため。
#set heading(numbering: $if(section-numbering)$"$section-numbering$"$else$none$endif$)

// (1) js の見出しは weight 450（ゴシック体だが太くはない）。節の切れ目を追い
//     やすくするため太字にする。
#show heading: set text(weight: "bold")

// (2) 表を三本線（booktabs 相当）にする。js の既定は全格子の細罫で，行数の多い
//     数表だと見出し行と本体の区別がつかず読みにくいため。縦罫を落とし，
//     上下と見出し下だけを太くして，行間は薄い罫で区切る。
#set table(
  inset: (x: 0.6em, y: 0.45em),
  stroke: (x, y) => (
    top: if y == 0 { 0.08em } else if y == 1 { 0.05em } else { 0.02em + luma(160) },
    bottom: 0.08em,
  ),
)
#show table.cell.where(y: 0): strong

#set smartquote(enabled: false)

#let horizontalrule = line(start: (25%, 0%), end: (75%, 0%))

$for(header-includes)$
$header-includes$

$endfor$
$if(title)$
// (3) 標題は js の #maketitle を使わず，ここで組んでいる。maketitle には
//     副題（対象）とリポジトリの置き場が無く，項目ごとの間隔も広いため，
//     5行が散らばって目次が1ページに収まらなかった。字面は js のまま，
//     関連する項目をまとめて行間だけ詰めている。
#place(top + center, scope: "parent", float: true, block(width: 100%)[
  #set align(center)
  #set par(first-line-indent: 0em, justify: false)
  #v(0.6em)
  #text(1.7em)[$title$]
$if(subtitle)$
  #v(0.7em, weak: true)
  #text(0.95em)[$subtitle$]
$endif$
  #v(1.1em, weak: true)
  $for(author)$$author$$sep$，$endfor$$if(date)$#h(1.2em)$date$$endif$
$if(repo)$
  #v(0.35em, weak: true)
  #text(0.85em)[$repo$]
$endif$
$if(abstract)$
  #v(1.2em, weak: true)
  #block(width: 90%)[
    #set text(0.9em)
    _概要_
    #align(left)[$abstract$]
  ]
$endif$
  #v(1.2em)
])
$endif$

$for(include-before)$
$include-before$

$endfor$
$if(toc)$
#outline(depth: $if(toc-depth)$$toc-depth$$else$2$endif$)
#v(1em)

$endif$
$body$

$for(include-after)$

$include-after$
$endfor$
