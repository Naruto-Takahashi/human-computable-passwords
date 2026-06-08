# 実験結果をスキャンし，outputs/summary.md に自動集計表を出力するスクリプト
import glob
import json
import os


def generate_markdown_table(headers, rows):
    # ライブラリ依存（tabulate等）なしでMarkdownテーブル文字列を生成するヘルパー
    if not rows:
        return ""

    # カラムごとの最大幅を計算
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # ヘッダー行とセパレータ
    header_line = (
        "| "
        + " | ".join(f"{str(h):<{col_widths[i]}}" for i, h in enumerate(headers))
        + " |"
    )
    separator_line = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"

    # データ行
    data_lines = []
    for row in rows:
        line = (
            "| "
            + " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row))
            + " |"
        )
        data_lines.append(line)

    return "\n".join([header_line, separator_line] + data_lines)


def summarize_results():
    output_dir = "outputs"
    metadata_files = glob.glob(os.path.join(output_dir, "run_*", "metadata.json"))

    if not metadata_files:
        print("No experiment metadata files found.")
        return

    headers = [
        "日時",
        "モデル名",
        "アルゴリズム",
        "データ数",
        "エポック数",
        "シード値",
        "学習時間(秒)",
        "Gitコミット",
        "Accuracy (Train)",
        "Accuracy (Val)",
        "Loss (Train)",
        "Loss (Val)",
    ]

    records = []
    for filepath in metadata_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            final_metrics = data.get("final_metrics", {})

            row = [
                data.get("timestamp", ""),
                data.get("model_name", ""),
                data.get("generator_name", ""),
                str(data.get("required_data_size", "")),
                str(data.get("epochs", "")),
                str(data.get("seed", "")),
                f"{data.get('elapsed_time_seconds', 0):.2f}",
                data.get("git_commit", "unknown"),
                f"{final_metrics.get('accuracy', 0):.4f}",
                f"{final_metrics.get('val_accuracy', 0):.4f}",
                f"{final_metrics.get('loss', 0):.4f}",
                f"{final_metrics.get('val_loss', 0):.4f}",
            ]
            records.append(row)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    # 日時（最初の列）の降順でソート
    records.sort(key=lambda x: x[0], reverse=True)

    # Markdownテーブル生成
    markdown_table = generate_markdown_table(headers, records)

    summary_content = f"""# 実験結果 自動集計表

このファイルは，`src/summarize_results.py` によって自動生成された実験結果の集計ログです．

## 実行結果一覧

{markdown_table}
"""

    # outputs/summary.md へ保存
    summary_filepath = os.path.join(output_dir, "summary.md")
    with open(summary_filepath, "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"Successfully generated summary at {summary_filepath}")
    print("\n--- Current Experiment Summary ---")
    print(markdown_table)


if __name__ == "__main__":
    summarize_results()
