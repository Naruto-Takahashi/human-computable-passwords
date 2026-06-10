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
    args = parser.parse_args()

    generators = list_available_generators()
    provider = "ollama"
    model = args.model
    n_shot = 10
    n_test = 50
    sleep_sec = 0.0

    print(f"Batch Benchmark Start: model={model}, generators={generators}, parallel={args.parallel}")

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
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running benchmark for {gen}: {e}")

    print("\nBatch Benchmark Completed.")

if __name__ == "__main__":
    run_batch()
