#!/usr/bin/env python3
# =============================================================================
# batch_benchmark.py
# =============================================================================
# 複数のジェネレータに対して一括で LLM ベンチマークを実行するスクリプト．
# =============================================================================

import subprocess
import os
import sys

# src/ をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from llm import list_available_generators

def run_batch():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--parallel", type=int, default=12, help="並列リクエスト数")
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="使用するモデル名")
    parser.add_argument("--n_shot", type=int, default=10, help="Few-shot 例題数")
    parser.add_argument("--n_test", type=int, default=50, help="テスト問題数")
    parser.add_argument("--rationale", action="store_true", help="計算過程の解説を含める")
    args = parser.parse_args()

    generators = list_available_generators()
    provider = "ollama"
    model = args.model
    n_shot = args.n_shot
    n_test = args.n_test
    sleep_sec = 0.0

    print(f"Batch Benchmark Start: model={model}, generators={generators}, parallel={args.parallel}, rationale={args.rationale}")

    # 実行スクリプトのパス
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runner.py")

    for gen in generators:
        print(f"\n>>> Running benchmark for generator: {gen}")
        cmd = [
            "python3", script_path,
            "--provider", provider,
            "--model", model,
            "--generator", gen,
            "--n_shot", str(n_shot),
            "--n_test", str(n_test),
            "--sleep_sec", str(sleep_sec),
            "--parallel", str(args.parallel)
        ]
        if args.rationale:
            cmd.append("--rationale")
        if args.use_code:
            cmd.append("--use_code")
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running benchmark for {gen}: {e}")

    print("\nBatch Benchmark Completed.")

if __name__ == "__main__":
    run_batch()
Benchmark Completed.")

if __name__ == "__main__":
    run_batch()
