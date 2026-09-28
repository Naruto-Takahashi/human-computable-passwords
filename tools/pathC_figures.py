#!/usr/bin/env python3
"""実験C1 の図を作る（docs/reports/figures/*.svg）．

    python3 tools/pathC_figures.py

配色は dataviz スキルの検証済みパレット（light）から取り，validate_palette.js で
検証済み（カテゴリ4色: 青・橙・翠・紫。隣接対の CVD ΔE 9.2 / 通常視 27.6）。
翠は明地での контраст が 3:1 を下回るため，直接ラベルを必ず添える（relief 規則）。
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs/reports/figures")
THRESHOLD = 0.5

BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8880"
GRID = "#e3e2dd"

plt.rcParams.update({
    # Typst(resvg) は可変フォントを扱えず，SVG 内のフォント名解決も環境依存になる．
    # 文字をパスに落として埋め込む（svg.fonttype="path"）ので，字形は確実に出る．
    "font.family": ["Noto Sans CJK JP", "sans-serif"],
    "font.size": 9, "axes.edgecolor": INK3, "axes.linewidth": 0.6,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "svg.fonttype": "path", "figure.facecolor": "white", "axes.facecolor": "white",
})

LABEL = {"func_pow": "$h$（統制・$j$項なし）", "func_22": "$f_{2,2}$  $s$=1.5",
         "func_13_k26": "$f_{1,3}$  $s$=2.0", "func_31": "$f_{3,1}$  $s$=1.0"}
LABEL50 = {"func_pow_k50": LABEL["func_pow"], "func_22_k50": LABEL["func_22"],
           "func_13_k50": LABEL["func_13_k26"], "func_31_k50": LABEL["func_31"]}
K26 = ["func_pow", "func_22", "func_13_k26", "func_31"]
K50 = ["func_pow_k50", "func_22_k50", "func_13_k50", "func_31_k50"]


def load(exp="C1"):
    rows = []
    for f in glob.glob(os.path.join(REPO, f"results/path_c/{exp}/runs_*.jsonl")):
        for line in open(f):
            rows.append(json.loads(line))
    return rows


def wilson(k, n, z=1.959963985):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def sel(rows, algo, datasize):
    return [r for r in rows if r["algorithm"] == algo and r["datasize"] == datasize]


def tidy(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=3, width=0.6)


# ---------------------------------------------------------------- 図1 離陸率
def fig_takeoff(rows):
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.5), sharex=True)
    for ax, algos, N in zip(axes, (K26, K50), (26, 50)):
        ys = np.arange(len(algos))[::-1]
        for y, a in zip(ys, algos):
            rs = sel(rows, a, 50000)
            k = sum(1 for r in rs if r["val_accuracy_max"] > THRESHOLD)
            n = len(rs)
            lo, hi = wilson(k, n)
            color = VIOLET if "pow" in a else BLUE
            ax.plot([lo, hi], [y, y], color=color, lw=2, solid_capstyle="round",
                    alpha=0.35, zorder=2)
            ax.plot([k / n], [y], "o", ms=8, color=color, zorder=3,
                    markeredgecolor="white", markeredgewidth=1.2)
            ax.text(hi + 0.035, y, f"{k}/{n}", va="center", ha="left",
                    fontsize=8.5, color=INK)
        ax.set_yticks(ys)
        ax.set_yticklabels([(LABEL if N == 26 else LABEL50)[a] for a in algos])
        ax.set_xlim(-0.04, 1.30)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(["0", "25", "50", "75", "100%"])
        ax.xaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_title(f"鍵サイズ $N$={N}", fontsize=9.5, color=INK, pad=6)
        tidy(ax)
    axes[0].set_xlabel("離陸率（20 run 中，95% Wilson 区間）", color=INK2)
    axes[1].set_xlabel("離陸率（20 run 中，95% Wilson 区間）", color=INK2)
    fig.tight_layout()
    fig.savefig(f"{OUT}/c1_takeoff_rate.svg", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------- 図2 run ごとの分布（二峰性）
def fig_runs(rows):
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.7), sharey=True)
    rng = np.random.default_rng(7)
    for ax, algos, N in zip(axes, (K26, K50), (26, 50)):
        for i, a in enumerate(algos):
            v = np.array([r["val_accuracy_max"] for r in sel(rows, a, 50000)])
            x = i + rng.uniform(-0.17, 0.17, len(v))
            color = VIOLET if "pow" in a else BLUE
            ax.scatter(x, v, s=26, color=color, alpha=0.75, linewidths=0.8,
                       edgecolors="white", zorder=3)
            ax.plot([i - 0.34, i + 0.34], [v.mean()] * 2, color=ORANGE, lw=2,
                    zorder=4, solid_capstyle="butt")
            # 平均の数値は本文の表にあるので図には書かない（点の塊と必ず重なる）
        ax.axhline(THRESHOLD, color=INK3, lw=0.8, ls=(0, (4, 3)), zorder=1)
        ax.set_xticks(range(len(algos)))
        ax.set_xticklabels(["$h$", "$f_{2,2}$", "$f_{1,3}$", "$f_{3,1}$"])
        ax.set_ylim(-0.02, 1.12)
        ax.set_xlim(-0.6, len(algos) - 0.4)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_title(f"鍵サイズ $N$={N}", fontsize=9.5, color=INK, pad=6)
        tidy(ax)
    axes[0].set_ylabel("検証正解率", color=INK2)
    axes[1].text(len(K50) - 0.45, THRESHOLD + 0.02, "離陸の判定線 0.5",
                 fontsize=7.6, color=INK3, ha="right")
    fig.tight_layout()
    fig.savefig(f"{OUT}/c1_run_distribution.svg", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------- 図3 鍵×初期値のヒートマップ
def fig_keyinit(rows):
    fig, axes = plt.subplots(1, 4, figsize=(7.1, 2.1))
    for ax, a in zip(axes, K26):
        rs = sel(rows, a, 50000)
        keys = sorted({r["key_seed"] for r in rs})
        inits = sorted({r["init_seed"] for r in rs})
        m = np.full((len(keys), len(inits)), np.nan)
        for r in rs:
            m[keys.index(r["key_seed"]), inits.index(r["init_seed"])] = r["val_accuracy_max"]
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq", SEQ)
        ax.imshow(m, vmin=0, vmax=1, cmap=cmap, aspect="auto")
        for i in range(len(keys)):
            for j in range(len(inits)):
                v = m[i, j]
                txt = "1.0" if v >= 0.995 else f"{v:.2f}"[1:]
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=6.6, color="white" if v > 0.6 else INK)
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                       edgecolor="white", lw=1.2))
        ax.set_xticks(range(len(inits)))
        ax.set_xticklabels([f"{i+1}" for i in range(len(inits))])
        ax.set_yticks(range(len(keys)))
        ax.set_yticklabels([f"鍵{i+1}" for i in range(len(keys))] if a == K26[0] else [""] * len(keys))
        ax.set_xlabel("初期値", color=INK2, fontsize=8)
        ax.set_title(LABEL[a].split("  ")[0], fontsize=9.5, color=INK, pad=5)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/c1_key_init.svg", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------ 図4 学習曲線（相転移）
def fig_curve(rows):
    rs = [r for r in sel(rows, "func_22", 50000)]
    best = max(rs, key=lambda r: r["val_accuracy_max"])
    flat = min(rs, key=lambda r: r["val_accuracy_max"])
    fig, ax = plt.subplots(figsize=(7.1, 2.4))
    for r, style in ((best, "-"), (flat, (0, (5, 3)))):
        ep = np.arange(len(r["history"]["val_accuracy"]))
        ax.plot(ep, r["history"]["accuracy"], ls=style, color=ORANGE, lw=1.6,
                label="訓練" if style == "-" else None)
        ax.plot(ep, r["history"]["val_accuracy"], ls=style, color=BLUE, lw=1.6,
                label="検証" if style == "-" else None)
    ax.axhline(0.5, color=INK3, lw=0.8, ls=(0, (2, 3)), zorder=1)
    n_ep = len(best["history"]["val_accuracy"])
    ax.text(n_ep - 2, 1.02, "離陸した run（実線）", fontsize=8, color=INK,
            ha="right", va="bottom")
    ax.text(n_ep - 2, flat["history"]["accuracy"][-1] + 0.04,
            "離陸しなかった run（破線）", fontsize=8, color=INK, ha="right", va="bottom")
    ax.text(2, 0.52, "離陸の判定線 0.5", fontsize=7.6, color=INK3, va="bottom")
    leg = ax.legend(loc="center right", frameon=False, fontsize=8,
                    bbox_to_anchor=(1.0, 0.56), handlelength=1.6)
    for t in leg.get_texts():
        t.set_color(INK2)
    ax.set_xlabel("エポック", color=INK2)
    ax.set_ylabel("正解率", color=INK2)
    ax.set_ylim(0, 1.18)
    ax.set_xlim(0, len(best["history"]["val_accuracy"]) - 1)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    tidy(ax)
    fig.tight_layout()
    fig.savefig(f"{OUT}/c1_learning_curve.svg", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------- 図5 データ量の閾値
def fig_datasize(rows):
    sizes = [1000, 5000, 10000, 50000]
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.5), sharey=True)
    colors = {0: VIOLET, 1: BLUE, 2: ORANGE, 3: AQUA}
    for ax, algos, N in zip(axes, (K26, K50), (26, 50)):
        ends = []
        for i, a in enumerate(algos):
            ys = []
            for d in sizes:
                rs = sel(rows, a, d)
                ys.append(sum(1 for r in rs if r["val_accuracy_max"] > THRESHOLD) / len(rs))
            ax.plot(range(len(sizes)), ys, "-o", color=colors[i], lw=1.8, ms=6,
                    markeredgecolor="white", markeredgewidth=1.0, zorder=3)
            ends.append((ys[-1], i))
        # 直接ラベルは終点に置くが，終点が近いと重なるので上から順に間隔を空ける
        ends.sort(reverse=True)
        placed = []
        for y, i in ends:
            pos = y + 0.045
            while placed and pos > min(placed) - 0.085:
                pos = min(placed) - 0.085
            placed.append(pos)
            ax.text(len(sizes) - 0.85, pos,
                    ["$h$", "$f_{2,2}$", "$f_{1,3}$", "$f_{3,1}$"][i],
                    color=colors[i], fontsize=9, ha="left", va="center")
        ax.set_xticks(range(len(sizes)))
        ax.set_xticklabels(["1千", "5千", "1万", "5万"])
        ax.set_xlabel("学習データ量（件）", color=INK2)
        ax.set_ylim(-0.22, 1.12)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_title(f"鍵サイズ $N$={N}", fontsize=9.5, color=INK, pad=6)
        tidy(ax)
    axes[0].set_ylabel("離陸率", color=INK2)
    axes[0].set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    axes[0].set_yticklabels(["0", "25", "50", "75", "100%"])
    fig.tight_layout()
    fig.savefig(f"{OUT}/c1_datasize.svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    rows = load()
    fig_takeoff(rows); fig_runs(rows); fig_keyinit(rows)
    fig_curve(rows); fig_datasize(rows)
    for f in sorted(glob.glob(f"{OUT}/c1_*.svg")):
        print(f"  {os.path.basename(f)}  {os.path.getsize(f)//1024} KB")
