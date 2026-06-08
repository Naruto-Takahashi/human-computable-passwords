#!/usr/bin/env python3
# =============================================================================
# dry_run_test.py
# =============================================================================
# API キーなしで llm_benchmark パッケージの動作を検証するドライランスクリプト．
#
# 以下の内容を検証する:
#   1. computable_password_generator からのデータ生成
#   2. Few-shot 用とテスト用への分割
#   3. プロンプト構築（実際のプロンプト文字列を表示）
#   4. 評価器の記録・集計ロジック（ダミー予測値を使用）
# =============================================================================

import sys
import os

# src/ をパスに追加
# このスクリプトは src/llm_benchmark/ 内に配置されているため，
# 親の src/ ディレクトリをパスに追加する
_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _src_dir)

from llm_benchmark.data_generator import generate_dataset, extract_challenge_and_response
from llm_benchmark.prompt_builder import get_prompt_builder
from llm_benchmark.evaluator      import BenchmarkRecord, Evaluator, make_output_dir


def main():
    print("=" * 60)
    print("LLM ベンチマーク ドライランテスト（API なし）")
    print("=" * 60)

    # ---- Step 1: データ生成 ----
    print("\n[Step 1] データセット生成...")
    shot_df, test_df = generate_dataset(
        generator_name = "func_31",
        n_shot         = 5,    # テスト用に少量
        n_test         = 10,
        seed           = 42,
    )
    print(f"  Few-shot 例題: {len(shot_df)} 件")
    print(f"  テスト問題  : {len(test_df)} 件")
    print(f"\n  shot_df の先頭:\n{shot_df.head(3).to_string()}")

    # ---- Step 2: プロンプト構築 ----
    print("\n[Step 2] プロンプト構築...")
    builder = get_prompt_builder("text")
    first_row = test_df.iloc[0]
    challenge, correct_ans = extract_challenge_and_response(first_row)
    prompt = builder.build_fewshot_prompt(shot_df, challenge)
    print(f"\n--- 生成プロンプト（先頭 800 文字） ---\n{prompt[:800]}\n...\n---")

    # ---- Step 3: 評価器テスト（ダミー予測値を使用） ----
    print("\n[Step 3] 評価器テスト（ダミー予測値を使用）...")
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "outputs", "llm_benchmark", "dry_run_test"
    )
    evaluator = Evaluator(output_dir=output_dir)

    for _, row in test_df.iterrows():
        chal, ans = extract_challenge_and_response(row)
        # ダミー予測: 正解の 30% 相当をシミュレート
        dummy_pred = ans if (_ % 3 == 0) else ((ans + 1) % 10)
        record = BenchmarkRecord(
            challenge    = chal,
            correct_ans  = ans,
            predicted    = dummy_pred,
            raw_response = f"(dry_run) Answer: {dummy_pred}",
        )
        evaluator.add_record(record)

    evaluator.save_results(metadata={
        "mode"          : "dry_run",
        "generator_name": "func_31",
        "n_shot"        : 5,
        "n_test"        : 10,
    })

    print("\n[完了] ドライランテストが正常に終了しました．")


if __name__ == "__main__":
    main()
