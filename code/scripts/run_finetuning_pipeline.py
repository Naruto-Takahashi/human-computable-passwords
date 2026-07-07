#!/usr/bin/env python3
"""
ファインチューニング → 評価テスト の一連のパイプラインを実行するラッパースクリプト．
（Google Drive 同期は train_finetuning.py / run_prompting.py の内部で自動実行される）

train_finetuning.py を子プロセスとして実行し，標準出力から保存先ディレクトリを検出したうえで，
そのアダプターに対して run_prompting.py --provider lora による評価を続けて実行する．
"""
import argparse
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRAIN_SCRIPT = os.path.join(REPO_ROOT, "code", "scripts", "train_finetuning.py")
EVAL_SCRIPT = os.path.join(REPO_ROOT, "code", "scripts", "run_prompting.py")

RESULTS_DIR_PATTERN = re.compile(r"^Results will be saved to: (.+)$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="HCP LLM ファインチューニング + 評価テスト パイプライン",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ---- 学習・評価で共有する実験条件 ----
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-3B-Instruct", help="Hugging Face モデル識別子")
    parser.add_argument("--generator", type=str, default="func_31", help="HCP アルゴリズム名")
    parser.add_argument("--paradigm", type=str, default="pot", choices=["pure", "pot", "rationale"], help="学習の出力形式（評価時は rationale も pure として評価される）")
    parser.add_argument("--stage", type=int, default=0, choices=[0, 1, 2, 3], help="評価時の情報開示ステージ（学習は常に stage=0 を想定）")
    parser.add_argument("--k_disclosed", type=int, default=0, help="Stage 3 で事前開示する秘密鍵の要素数")
    parser.add_argument("--n_shot", type=int, default=10, help="Few-shot 例題数")
    parser.add_argument("--seed", type=int, default=42, help="乱数シード")

    # ---- 学習固有のパラメータ ----
    parser.add_argument("--n_train", type=int, default=500, help="学習サンプル数")
    parser.add_argument("--n_val", type=int, default=-1, help="検証サンプル数（未指定時は n_train // 5）")
    parser.add_argument("--epochs", type=int, default=3, help="学習エポック数")
    parser.add_argument("--batch_size", type=int, default=2, help="1GPUあたりのバッチサイズ")
    parser.add_argument("--grad_accum", type=int, default=4, help="勾配蓄積ステップ数")
    parser.add_argument("--lr", type=float, default=2e-4, help="学習率")
    parser.add_argument("--max_len", type=int, default=2048, help="最大シーケンス長")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA ランク")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA アルファ")
    parser.add_argument("--quant", type=str, default="4bit", choices=["4bit", "8bit"], help="ベースモデルの量子化方式")

    # ---- 評価固有のパラメータ ----
    parser.add_argument("--n_test", type=int, default=50, help="評価テスト問題数")

    # ---- パイプライン制御 ----
    parser.add_argument("--skip_train", type=str, default=None, help="学習をスキップし，指定した run ディレクトリを直接評価する")
    parser.add_argument("--python", type=str, default=sys.executable, help="学習・評価に使用する python 実行ファイル")

    return parser.parse_args()


def run_streamed(cmd: list[str]) -> str:
    """
    子プロセスを実行し，標準出力をリアルタイムに表示しつつ全文を返す．
    非ゼロ終了コードの場合は例外を送出する．
    """
    print(f"[pipeline] 実行: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    lines = []
    for line in proc.stdout:
        print(line, end="")
        lines.append(line)
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"コマンドが失敗しました（終了コード {proc.returncode}）: {' '.join(cmd)}")
    return "".join(lines)


def find_run_dir(train_output: str) -> str:
    for line in train_output.splitlines():
        m = RESULTS_DIR_PATTERN.match(line.strip())
        if m:
            return m.group(1).strip()
    raise RuntimeError("学習ログから保存先ディレクトリを検出できませんでした（'Results will be saved to:' が見つかりません）")


def main():
    args = parse_args()

    if args.skip_train:
        run_dir = args.skip_train
        print(f"[pipeline] --skip_train が指定されたため学習をスキップします: {run_dir}")
    else:
        train_cmd = [
            args.python, TRAIN_SCRIPT,
            "--model", args.model,
            "--generator", args.generator,
            "--paradigm", args.paradigm,
            "--n_shot", str(args.n_shot),
            "--n_train", str(args.n_train),
            "--n_val", str(args.n_val),
            "--seed", str(args.seed),
            "--stage", str(args.stage),
            "--k_disclosed", str(args.k_disclosed),
            "--epochs", str(args.epochs),
            "--batch_size", str(args.batch_size),
            "--grad_accum", str(args.grad_accum),
            "--lr", str(args.lr),
            "--max_len", str(args.max_len),
            "--lora_r", str(args.lora_r),
            "--lora_alpha", str(args.lora_alpha),
            "--quant", args.quant,
        ]
        train_output = run_streamed(train_cmd)
        run_dir = find_run_dir(train_output)
        print(f"[pipeline] 学習完了．アダプター保存先: {run_dir}")

    # run_prompting.py は "rationale" パラダイムを持たない（JSON抽出パーサーが
    # 前置きの思考テキストを無視して {"answer": ...} を拾えるため，pure として評価する）
    eval_paradigm = "pure" if args.paradigm == "rationale" else args.paradigm

    eval_cmd = [
        args.python, EVAL_SCRIPT,
        "--provider", "lora",
        "--model", run_dir,
        "--generator", args.generator,
        "--paradigm", eval_paradigm,
        "--stage", str(args.stage),
        "--k_disclosed", str(args.k_disclosed),
        "--n_shot", str(args.n_shot),
        "--n_test", str(args.n_test),
        "--seed", str(args.seed),
    ]
    run_streamed(eval_cmd)

    print("[pipeline] 学習・評価パイプラインが完了しました．")
    print(f"[pipeline]   学習済みアダプター: {run_dir}")
    print("[pipeline]   評価結果は上記ログの '結果保存先' を参照してください．")
    print("[pipeline]   Google Drive 同期は学習・評価それぞれの実行スクリプト内でバックグラウンド実行されています．")


if __name__ == "__main__":
    main()
