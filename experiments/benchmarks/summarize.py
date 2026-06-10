# LLM ベンチマーク結果 自動集計スクリプト
import glob
import json
import os
from datetime import datetime

def generate_markdown_table(headers, rows):
    if not rows:
        return "データがありません。"

    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    header_line = "| " + " | ".join(f"{str(h):<{col_widths[i]}}" for i, h in enumerate(headers)) + " |"
    separator_line = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"
    
    data_lines = []
    for row in rows:
        line = "| " + " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row)) + " |"
        data_lines.append(line)

    return "\n".join([header_line, separator_line] + data_lines)

def summarize_llm_results():
    # experiments/benchmarks/summarize.py から見たプロジェクトルート
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    output_dir = os.path.join(base_dir, "outputs", "benchmarks")
    metadata_files = glob.glob(os.path.join(output_dir, "run_*", "metadata.json"))

    if not metadata_files:
        print("No LLM benchmark metadata files found.")
        return

    headers = [
        "実行日時",
        "モデル名",
        "アルゴリズム",
        "Few-shot",
        "テスト数",
        "Accuracy",
        "パースエラー"
    ]

    records = []
    for filepath in metadata_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # フォルダ名からタイムスタンプを抽出 (run_YYYYMMDD_HHMMSS_...)
            folder_name = os.path.basename(os.path.dirname(filepath))
            timestamp = folder_name.split("_")[1] + "_" + folder_name.split("_")[2]

            row = [
                timestamp,
                data.get("model_name", ""),
                data.get("generator_name", ""),
                str(data.get("n_shot", "")),
                str(data.get("n_test", "")),
                f"{data.get('accuracy', 0):.2%}",
                str(data.get("parse_error_count", 0))
            ]
            records.append(row)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    # 実行日時の降順でソート
    records.sort(key=lambda x: x[0], reverse=True)

    markdown_table = generate_markdown_table(headers, records)

    summary_content = f"""# LLM ベンチマーク実験結果 サマリー

このファイルは `src/llm_benchmark/summarize_llm_results.py` によって自動生成されました。
最終更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 実験結果一覧

{markdown_table}
"""

    summary_filepath = os.path.join(base_dir, "outputs", "summary_llm.md")
    with open(summary_filepath, "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"Successfully generated summary at {summary_filepath}")
    print("\n--- LLM Experiment Summary ---")
    print(markdown_table)

if __name__ == "__main__":
    summarize_llm_results()
