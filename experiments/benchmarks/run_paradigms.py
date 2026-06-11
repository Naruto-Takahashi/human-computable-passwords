#!/usr/bin/env python3
# =============================================================================
# run_paradigms.py
# =============================================================================
# 特定のアルゴリズムに対し，全4つの実験手法（パラダイム）を連続実行するスクリプト．
# =============================================================================

import subprocess
import os
import argparse

def run_all_paradigms():
    parser = argparse.ArgumentParser(description="特定のアルゴリズムで全パラダイムを比較実行する")
    parser.add_argument("--model", type=str, default="gemma2:9b", help="使用するモデル名")
    parser.add_argument("--generator", type=str, default="simple_add", help="対象のアルゴリズム")
    parser.add_argument("--n_test", type=int, default=20, help="各テストの件数")
    parser.add_argument("--parallel", type=int, default=2, help="並列度")
    parser.add_argument("--n_shot", type=int, default=10, help="Few-shot数")
    args = parser.parse_args()

    # 4つのパラダイム設定
    paradigms = [
        ("Pure Few-shot", []),
        ("Rationalized Few-shot", ["--rationale"]),
        ("Program-of-Thought", ["--use_code"]),
        ("Rationalized PoT", ["--rationale", "--use_code"])
    ]

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runner.py")

    print(f"=== Paradigm Comparison Start ===")
    print(f"Model: {args.model}")
    print(f"Generator: {args.generator}")
    print(f"Tests per paradigm: {args.n_test}")
    print("===================================\n")

    for name, flags in paradigms:
        print(f"\n>>> Running Paradigm: {name}")
        cmd = [
            "python3", script_path,
            "--provider", "ollama",
            "--model", args.model,
            "--generator", args.generator,
            "--n_test", str(args.n_test),
            "--n_shot", str(args.n_shot),
            "--parallel", str(args.parallel)
        ] + flags
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during {name}: {e}")

    print("\n=== All Paradigms Completed ===")

if __name__ == "__main__":
    run_all_paradigms()
