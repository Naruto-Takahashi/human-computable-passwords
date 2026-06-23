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
    parser.add_argument("--provider", type=str, default="ollama", choices=["ollama", "gemini", "mock"], help="LLMプロバイダ")
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="使用するモデル名")
    parser.add_argument("--generator", type=str, default="func_31", help="対象のアルゴリズム")
    parser.add_argument("--n_test", type=int, default=20, help="各テストの件数")
    parser.add_argument("--parallel", type=int, default=1, help="並列度")
    parser.add_argument("--n_shot", type=int, default=10, help="Few-shot数")
    parser.add_argument("--stage", type=int, default=1, choices=[0, 1, 2, 3], help="実験ステージ（0〜3）")
    parser.add_argument("--k_disclosed", type=int, default=5, help="Stage 3 で公開する秘密鍵の要素数 K")
    args = parser.parse_args()

    # 4つのパラダイム設定
    paradigms = ["pure", "rationale", "pot", "rationale_pot"]

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_benchmark.py")

    print(f"=== Paradigm Comparison Start ===")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model}")
    print(f"Generator: {args.generator}")
    print(f"Stage: Stage {args.stage}")
    if args.stage == 3:
        print(f"K Disclosed: {args.k_disclosed}")
    print(f"Tests per paradigm: {args.n_test}")
    print("===================================\n")

    for paradigm in paradigms:
        print(f"\n>>> Running Paradigm: {paradigm}")
        cmd = [
            "python3", script_path,
            "--provider", args.provider,
            "--model", args.model,
            "--generator", args.generator,
            "--n_test", str(args.n_test),
            "--n_shot", str(args.n_shot),
            "--parallel", str(args.parallel),
            "--stage", str(args.stage),
            "--k_disclosed", str(args.k_disclosed),
            "--paradigm", paradigm
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during paradigm {paradigm}: {e}")

    print("\n=== All Paradigms Completed ===")

if __name__ == "__main__":
    run_all_paradigms()
