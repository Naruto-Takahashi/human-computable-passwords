# =============================================================================
# plotting.py — 学習曲線などの可視化（人間のレビュー用）
# =============================================================================
# 学習実行ごとに以下を run ディレクトリへ保存する:
#   - history.csv          : trainer.state.log_history のフラットなCSV（一次データ）
#   - training_curves.png  : 損失（対数軸）と token_accuracy の推移（train / eval）
#
# 配色は CVD セーフ検証済み: train=#3B6EC5, eval=#EE6677．
# 損失と精度はスケールが異なるため二軸にせず，上下2パネルに分ける．
# =============================================================================

from __future__ import annotations

import csv
import os
from typing import Optional

COLOR_TRAIN = "#3B6EC5"
COLOR_EVAL = "#EE6677"
COLOR_INK = "#404040"
COLOR_MUTED = "#767676"
COLOR_GRID = "#e4e4e0"


def save_history_csv(log_history: list[dict], run_dir: str) -> str:
    """log_history（学習ステップ/評価の記録）を history.csv に保存する．"""
    fields: list[str] = []
    for entry in log_history:
        for k in entry:
            if k not in fields:
                fields.append(k)
    path = os.path.join(run_dir, "history.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(log_history)
    return path


def _series(log_history: list[dict], y_key: str) -> tuple[list[float], list[float]]:
    xs, ys = [], []
    for e in log_history:
        if y_key in e and "epoch" in e:
            xs.append(float(e["epoch"]))
            ys.append(float(e[y_key]))
    return xs, ys


def plot_training_curves(
    log_history: list[dict], run_dir: str, title: Optional[str] = None
) -> Optional[str]:
    """損失と token_accuracy の推移を training_curves.png に保存する．"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    # 日本語ラベル用フォント（matplotlib が実際に読み込めるものを優先的に使う）
    available = {f.name for f in font_manager.fontManager.ttflist}
    for jp_font in (
        "Noto Sans CJK JP", "IPAexGothic", "TakaoGothic",
        "HackGen Console NF", "HackGen35 Console NF",
    ):
        if jp_font in available:
            plt.rcParams["font.family"] = [jp_font, "DejaVu Sans"]
            break

    panels = [
        ("損失 (log scale)", [("loss", "train", COLOR_TRAIN), ("eval_loss", "eval", COLOR_EVAL)], "log"),
        ("token accuracy", [("mean_token_accuracy", "train", COLOR_TRAIN),
                            ("eval_mean_token_accuracy", "eval", COLOR_EVAL)], "linear"),
    ]

    fig, axes = plt.subplots(2, 1, figsize=(8, 6.4), sharex=True)
    fig.patch.set_facecolor("white")

    plotted_any = False
    for ax, (label, series_spec, yscale) in zip(axes, panels):
        for y_key, name, color in series_spec:
            xs, ys = _series(log_history, y_key)
            if not xs:
                continue
            plotted_any = True
            ax.plot(xs, ys, color=color, linewidth=2, label=name,
                    marker="o" if len(xs) <= 40 else None, markersize=4)
        ax.set_yscale(yscale)
        ax.set_ylabel(label, color=COLOR_INK, fontsize=10)
        ax.grid(True, color=COLOR_GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(COLOR_MUTED)
        ax.tick_params(colors=COLOR_MUTED, labelsize=9)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(frameon=False, fontsize=9, labelcolor=COLOR_INK)

    if not plotted_any:
        plt.close(fig)
        return None

    axes[1].set_xlabel("epoch", color=COLOR_INK, fontsize=10)
    if title:
        fig.suptitle(title, color=COLOR_INK, fontsize=11)
    fig.tight_layout()
    path = os.path.join(run_dir, "training_curves.png")
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)
    return path


def save_training_artifacts(
    log_history: list[dict], run_dir: str, title: Optional[str] = None
) -> None:
    """history.csv と training_curves.png をまとめて保存する（学習スクリプトから呼ぶ）．"""
    if not log_history:
        return
    csv_path = save_history_csv(log_history, run_dir)
    png_path = plot_training_curves(log_history, run_dir, title=title)
    print(f"学習履歴を保存: {csv_path}")
    if png_path:
        print(f"学習曲線を保存: {png_path}")
