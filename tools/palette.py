"""図の配色（機械可読版）．

**正本は docs/palette.md。**値を変えるときは両方を合わせ，`dataviz` スキルの
検証器を通し直すこと:

    node scripts/validate_palette.js "#7096F8,#D2A400,#41C2A8,#A98CE0" --mode light
    node scripts/validate_palette.js "#5580FC,#B08A00,#35A98A,#9179DC" --mode dark

デジタル庁デザインシステムの配色を採用している。系列色は正本のチャート色だけでは
2つしか作れないため（灰は彩度0で系列に使えず，Yellow 400 は明るすぎる），
翠と紫を拡張した。経緯と検証結果は docs/palette.md にある。
"""

# ---- 正本のトークン -------------------------------------------------------
TEXT_BLACK = "#000000"
TEXT_WHITE = "#FFFFFF"
LABEL = "#626264"
LINK = "#0017C1"

BG_STANDARD = "#F8F8FB"
BG_HIGHLIGHT = "#0017C1"
BG_CONTROL = "#F1F1F4"

BLUE = {1200: "#000060", 900: "#0017C1", 600: "#3460FB",
        400: "#7096F8", 200: "#C5D7FB", 50: "#E8F1FE"}
YELLOW = {800: "#A58000", 600: "#D2A400", 400: "#FFC700"}
GRAY = {800: "#333333", 600: "#666666", 400: "#999999", 200: "#CCCCCC"}

RED = {600: "#FE3939", 200: "#FFBBBB", 50: "#FDEEEE"}
SUCCESS = "#197A4B"
ERROR = "#CE0000"

# ---- 役割への割り当て -----------------------------------------------------
#: 系列色（明地）。順に割り当て，系列が減っても詰めない
LIGHT = [BLUE[400], YELLOW[600], "#41C2A8", "#A98CE0"]
#: 系列色（暗地）。明地の機械的な反転ではなく，暗地で検証し直した別の段
DARK = ["#5580FC", "#B08A00", "#35A98A", "#9179DC"]

#: 連続値のランプ（単一色相・明→暗）。紙面では 1〜4段目だけ使うと落ち着く
SEQ_BLUE = [BLUE[50], BLUE[200], BLUE[400], BLUE[600], BLUE[900], BLUE[1200]]

#: 図の地・線・文字
SURFACE = TEXT_WHITE      # 紙面。画面向けは BG_STANDARD
INK = GRAY[800]           # 図中の文字（主）
INK2 = LABEL              # 図中の文字（副）
AXIS = GRAY[400]          # 軸・補助線
GRID = GRAY[200]          # 目盛り線


def matplotlib_rc() -> dict:
    """matplotlib の rcParams へそのまま渡せる辞書．

    和文はパスに落とす（Typst の SVG 描画が可変フォントを扱えないため）。
    """
    return {
        "font.family": ["Noto Sans CJK JP", "sans-serif"],
        "font.size": 9,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.6,
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": INK2, "ytick.color": INK2,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "svg.fonttype": "path",
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    }
