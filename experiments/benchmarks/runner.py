#!/usr/bin/env python3
# =============================================================================
# benchmark_runner.py
# =============================================================================
# 人間計算可能なパスワード（HCP）を題材とした LLM ベンチマークのメインスクリプト．
#
# 機能概要:
#   1. コマンドライン引数でベンチマーク設定を受け取る
#   2. HCP データセットを生成し，Few-shot 用とテスト用に分割する
#   3. テスト問題ごとにプロンプトを構築し，Gemini API に送信する
#   4. 予測結果を正解と照合し，結果を CSV / JSON に保存する
#
# 使い方:
#   cd src/
#   python llm_benchmark/benchmark_runner.py \
#     --generator func_31 \
#     --n_shot 10 \
#     --n_test 50 \
#     --model gemini-2.0-flash \
#     --sleep_sec 4.0 \
#     --seed 42
#
# 必要な環境変数:
#   GEMINI_API_KEY : Google AI Studio から取得した API キー
# =============================================================================

import argparse
import logging
import os
import sys
from typing import Optional

# パッケージのルートディレクトリ（src/）をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

# llm パッケージからインポート
from llm import (
    generate_dataset, extract_challenge_and_response, list_available_generators,
    get_prompt_builder, GeminiClient, OllamaClient, BenchmarkRecord, Evaluator, make_output_dir
)


# =============================================================================
# ログ設定
# =============================================================================

def setup_logging(verbose: bool = False) -> None:
    """
    ロギングレベルと出力フォーマットを設定する．

    Args:
        verbose : True の場合は DEBUG レベルで詳細ログを出力する．
                  False の場合は INFO レベルで通常ログを出力する．
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level   = level,
        format  = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )


# =============================================================================
# コマンドライン引数のパース
# =============================================================================

def parse_args() -> argparse.Namespace:
    """
    コマンドライン引数をパースして返す．

    Returns:
        解析済みの引数を保持する Namespace オブジェクト．
    """
    parser = argparse.ArgumentParser(
        description=(
            "人間計算可能なパスワード（HCP）を題材とした LLM Few-shot 推論ベンチマーク．\n"
            "Gemini API を使用して，隠れたアルゴリズムルールを推論させる実験を自動実行します．"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ---- データセット設定 ----
    parser.add_argument(
        "--generator",
        type    = str,
        default = "func_31",
        choices = list_available_generators(),
        help    = f"使用するパスワードジェネレータ名（デフォルト: func_31）",
    )
    parser.add_argument(
        "--n_shot",
        type    = int,
        default = 10,
        help    = "Few-shot プロンプトに含める例題数（デフォルト: 10）",
    )
    parser.add_argument(
        "--n_test",
        type    = int,
        default = 50,
        help    = "テスト問題数（デフォルト: 50）",
    )
    parser.add_argument(
        "--seed",
        type    = int,
        default = 42,
        help    = "乱数シード（デフォルト: 42）",
    )

    # ---- API・プロバイダ設定 ----
    parser.add_argument(
        "--provider",
        type    = str,
        default = "gemini",
        choices = ["gemini", "ollama"],
        help    = "LLMプロバイダ名（gemini: Google API, ollama: ローカルOllama）（デフォルト: gemini）",
    )
    parser.add_argument(
        "--model",
        type    = str,
        default = "gemini-2.5-flash",
        help    = "使用するモデル名（Gemini時デフォルト: gemini-2.5-flash、Ollama時推奨: qwen2.5:3b）",
    )
    parser.add_argument(
        "--sleep_sec",
        type    = float,
        default = 4.0,
        help    = (
            "API リクエスト間の待機時間（秒）．"
            "無料枠（15 RPM）では 4.0 秒以上を推奨（デフォルト: 4.0、Ollama時は 0.0 推奨）"
        ),
    )
    parser.add_argument(
        "--api_key",
        type    = str,
        default = None,
        help    = (
            "Gemini API キー（省略時は環境変数 GEMINI_API_KEY を使用）"
        ),
    )
    parser.add_argument(
        "--ollama_url",
        type    = str,
        default = "http://localhost:11434/api/generate",
        help    = "OllamaのAPIエンドポイントURL（デフォルト: http://localhost:11434/api/generate）",
    )
    parser.add_argument(
        "--parallel",
        type    = int,
        default = 1,
        help    = "並列リクエスト数（Ollama/ローカル実行時のみ推奨。デフォルト: 1）",
    )

    # ---- プロンプト設定 ----
    parser.add_argument(
        "--prompt_mode",
        type    = str,
        default = "text",
        choices = ["text"],   # 将来: ["text", "image"]
        help    = "プロンプトのモード（デフォルト: text）",
    )

    # ---- 出力設定 ----
    parser.add_argument(
        "--output_base_dir",
        type    = str,
        default = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "outputs", "benchmarks"
        ),
        help    = "結果ファイルを保存するベースディレクトリ",
    )
    parser.add_argument(
        "--verbose",
        action  = "store_true",
        help    = "詳細なデバッグログを出力する",
    )

    return parser.parse_args()


# =============================================================================
# メイン処理
# =============================================================================

def run_benchmark(args: argparse.Namespace) -> None:
    """
    ベンチマークのメイン処理を実行する．

    処理フロー:
        1. データセット生成（Few-shot 用 + テスト用）
        2. 各モジュール（クライアント，プロンプトビルダー，評価器）の初期化
        3. テスト問題ループ:
            a. プロンプトの構築
            b. API / ローカルLLM への送信
            c. 結果の記録
            d. 進捗の表示
        4. 結果の保存（CSV + JSON）

    Args:
        args : parse_args() で得た引数オブジェクト．
    """
    logger = logging.getLogger(__name__)

    # =========================================================================
    # Step 1: データセット生成
    # =========================================================================
    print(f"\n{'=' * 60}")
    print(f"【ベンチマーク設定】")
    print(f"  プロバイダ   : {args.provider}")
    print(f"  モデル       : {args.model}")
    print(f"  ジェネレータ : {args.generator}")
    print(f"  Few-shot 数  : {args.n_shot} 件")
    print(f"  テスト件数   : {args.n_test} 件")
    print(f"  API 待機時間 : {args.sleep_sec} 秒 / リクエスト")
    print(f"  乱数シード   : {args.seed}")
    print(f"{'=' * 60}\n")

    print("データセットを生成中...")
    shot_df, test_df = generate_dataset(
        generator_name = args.generator,
        n_shot         = args.n_shot,
        n_test         = args.n_test,
        seed           = args.seed,
    )
    print(f"  Few-shot 例題: {len(shot_df)} 件")
    print(f"  テスト問題  : {len(test_df)} 件")

    # =========================================================================
    # Step 2: モジュールの初期化
    # =========================================================================
    print("\nモジュールを初期化中...")

    # クライアントの差し替え分岐
    if args.provider == "gemini":
        client = GeminiClient(
            model_name = args.model,
            sleep_sec  = args.sleep_sec,
            api_key    = args.api_key,
        )
    elif args.provider == "ollama":
        client = OllamaClient(
            model_name = args.model,
            api_url    = args.ollama_url,
        )
        # ローカル推論向けに、タイムアウト対策でスリープ値を考慮
        # (OllamaClient側で既にリクエスト後待機処理はないため、追加の sleep_sec が適用される)
    else:
        raise ValueError(f"未知のプロバイダ: {args.provider}")

    # プロンプトビルダー（テキストモード）
    prompt_builder = get_prompt_builder(mode=args.prompt_mode)

    # 評価器（出力ディレクトリを自動生成）
    output_dir = make_output_dir(
        base_dir       = args.output_base_dir,
        generator_name = args.generator,
        model_name     = f"{args.provider}_{args.model.replace(':', '_')}",
    )
    evaluator = Evaluator(output_dir=output_dir)

    print(f"  初期化完了．出力先: {output_dir}")

    # =========================================================================
    # Step 3: テスト問題ループ
    # =========================================================================
    print(f"\nベンチマークを開始します（並列数: {args.parallel}）...\n")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_item(i, row):
        # ---- チャレンジとレスポンスの取り出し ----
        challenge, correct_ans = extract_challenge_and_response(row)

        # ---- プロンプトの構築 ----
        prompt = prompt_builder.build_fewshot_prompt(
            shot_df        = shot_df,
            test_challenge = challenge,
        )

        # ---- API / ローカルLLM 呼び出し ----
        raw_response, predicted = client.predict(prompt)

        # ---- 評価記録の構築 ----
        record = BenchmarkRecord(
            challenge    = challenge,
            correct_ans  = correct_ans,
            predicted    = predicted,
            raw_response = raw_response,
        )
        return i, record

    # 結果を順番通りに格納するためのリスト
    results = [None] * len(test_df)

    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(process_item, i, row): i for i, row in test_df.iterrows()}
        
        for future in as_completed(futures):
            idx, record = future.result()
            results[idx] = record
            evaluator.add_record(record)
            
            # ---- 進捗表示 ----
            status_icon = "✓" if record.is_correct else ("?" if record.predicted is None else "✗")
            print(
                f"  [{idx + 1:3d}/{args.n_test}] {status_icon} "
                f"正解={record.correct_ans}, 予測={record.predicted if record.predicted is not None else 'ERR'} "
                f"| 現在の正解率: {evaluator.accuracy():.2%}"
            )
            if args.verbose or idx < 5:
                # 応答の最後の方を表示して Answer: があるか確認
                tail_response = record.raw_response[-150:] if len(record.raw_response) > 150 else record.raw_response
                print(f"      [Raw Response Tail ({idx+1})]: ...{tail_response.replace('\\n', ' ')}")


    # =========================================================================
    # Step 4: 結果の保存
    # =========================================================================

    # 実験メタデータの構築
    metadata = {
        "provider"       : args.provider,
        "generator_name" : args.generator,
        "n_shot"         : args.n_shot,
        "n_test"         : args.n_test,
        "seed"           : args.seed,
        "model_name"     : args.model,
        "sleep_sec"      : args.sleep_sec,
        "prompt_mode"    : args.prompt_mode,
        "output_dir"     : output_dir,
    }

    evaluator.save_results(metadata=metadata)


# =============================================================================
# エントリーポイント
# =============================================================================

if __name__ == "__main__":
    args = parse_args()
    setup_logging(verbose=args.verbose)
    run_benchmark(args)
