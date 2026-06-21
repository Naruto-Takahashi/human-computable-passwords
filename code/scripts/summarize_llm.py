# LLM ベンチマーク結果 自動集計スクリプト
import glob
import json
import os
import unicodedata
from datetime import datetime

def get_display_width(text):
    """全角文字を2、半角文字を1として文字列の表示幅を計算する"""
    width = 0
    for char in str(text):
        if unicodedata.east_asian_width(char) in ('W', 'F', 'A'):
            width += 2
        else:
            width += 1
    return width

def pad_text(text, width):
    """表示幅を考慮したパディングを行う"""
    text_str = str(text)
    curr_width = get_display_width(text_str)
    padding = max(0, width - curr_width)
    return text_str + (" " * padding)

def generate_markdown_table(headers, rows):
    if not rows:
        return "データがありません。"

    # 各カラムの最大表示幅を計算
    col_widths = [get_display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], get_display_width(cell))

    # ヘッダー行
    header_line = "| " + " | ".join(pad_text(h, col_widths[i]) for i, h in enumerate(headers)) + " |"
    # セパレータ
    separator_line = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"
    
    data_lines = []
    for row in rows:
        line = "| " + " | ".join(pad_text(cell, col_widths[i]) for i, cell in enumerate(row)) + " |"
        data_lines.append(line)

    return "\n".join([header_line, separator_line] + data_lines)

def summarize_llm_results():
    # experiments/benchmarks/summarize.py から見たプロジェクトルート
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    output_dir = os.path.join(base_dir, "results", "benchmarks")
    # 階層化されたディレクトリから全ての metadata.json を再帰的に検索
    metadata_files = glob.glob(os.path.join(output_dir, "**", "metadata.json"), recursive=True)

    if not metadata_files:
        print("No LLM benchmark metadata files found.")
        return

    headers = [
        "実行日時",
        "モデル名",
        "アルゴリズム",
        "手法",
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

            # ディレクトリ構造から情報を取得 (model/generator/paradigm/run_timestamp)
            parts = os.path.relpath(os.path.dirname(filepath), output_dir).split(os.sep)
            if len(parts) >= 4:
                model_name = parts[0]
                gen_name = parts[1]
                paradigm = parts[2]
                run_dir = parts[3]
                timestamp = run_dir.replace("run_", "")
            else:
                # 以前の構造へのフォールバック
                model_name = data.get("model_name", "unknown")
                gen_name = data.get("generator_name", "unknown")
                timestamp = os.path.basename(os.path.dirname(filepath)).replace("run_", "")
                # メタデータから手法を判定
                is_rationale = data.get("rationale", False)
                is_use_code = data.get("use_code", False)
                if is_rationale and is_use_code: paradigm = "rationale_pot"
                elif is_rationale: paradigm = "rationale"
                elif is_use_code: paradigm = "pot"
                else: paradigm = "pure"

            row = [
                timestamp,
                model_name,
                gen_name,
                paradigm,
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

このファイルは `code/scripts/summarize_llm.py` によって自動生成されました．
最終更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 実験結果一覧

{markdown_table}
"""

    summary_filepath = os.path.join(base_dir, "results", "summary_llm.md")
    with open(summary_filepath, "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"Successfully generated summary at {summary_filepath}")
    print("\n--- LLM Experiment Summary ---")
    print(markdown_table)

if __name__ == "__main__":
    summarize_llm_results()
