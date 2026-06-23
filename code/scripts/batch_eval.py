#!/usr/bin/env python3
# =============================================================================
# batch_eval.py
# =============================================================================
# 複数のジェネレータに対して一括で LLM ベンチマークを実行するスクリプト．
# =============================================================================

import subprocess
import os
import sys

# core をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

from llm_agent import list_available_generators

def run_batch():
    import argparse
    parser = argparse.ArgumentParser(description="全アルゴリズムに対して一括評価を実行する")
    parser.add_argument("--provider", type=str, default="ollama", choices=["ollama", "gemini", "mock"], help="LLMプロバイダ")
    parser.add_argument("--parallel", type=int, default=1, help="並列リクエスト数")
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="使用するモデル名")
    parser.add_argument("--n_shot", type=int, default=10, help="Few-shot 例題数")
    parser.add_argument("--n_test", type=int, default=50, help="テスト問題数")
    parser.add_argument("--stage", type=int, default=1, choices=[0, 1, 2, 3], help="実験ステージ（0〜3）")
    parser.add_argument("--k_disclosed", type=int, default=5, help="Stage 3 で公開する秘密鍵の要素数 K")
    parser.add_argument("--paradigm", type=str, default="pure", choices=["pure", "rationale", "pot", "rationale_pot"], help="実験手法の選択")
    args = parser.parse_args()

    generators = list_available_generators()
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_benchmark.py")

    print(f"=== Batch Evaluation Start ===")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model}")
    print(f"Stage: Stage {args.stage}")
    if args.stage == 3:
        print(f"K Disclosed: {args.k_disclosed}")
    print(f"Paradigm: {args.paradigm}")
    print(f"Generators: {generators}")
    print(f"Parallel: {args.parallel}")
    print(f"Tests per generator: {args.n_test}")
    print("===============================\n")

    for gen in generators:
        print(f"\n>>> Running benchmark for generator: {gen}")
        cmd = [
            "python3", script_path,
            "--provider", args.provider,
            "--model", args.model,
            "--generator", gen,
            "--n_shot", str(args.n_shot),
            "--n_test", str(args.n_test),
            "--parallel", str(args.parallel),
            "--stage", str(args.stage),
            "--k_disclosed", str(args.k_disclosed),
            "--paradigm", args.paradigm
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running benchmark for {gen}: {e}")

    print("\nBatch Evaluation Completed.")

if __name__ == "__main__":
    run_batch()
