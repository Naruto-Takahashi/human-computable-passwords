#!/usr/bin/env python3
# =============================================================================
# benchmark_runner.py
# =============================================================================
# 人間計算可能なパスワード（HCP）を題材とした LLM アルゴリズム推論ベンチマークの
# 実行エントリーポイント．
# =============================================================================

import argparse
import logging
import os
import sys
import re
from typing import Optional

# パッケージのルートディレクトリ（src/）をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

# llm パッケージからインポート
from llm_agent import (
    generate_dataset, extract_challenge_and_response, list_available_generators,
    get_prompt_builder, GeminiClient, OllamaClient, MockClient, BenchmarkRecord, Evaluator, make_output_dir, CodeExecutor
)


# =============================================================================
# ログ設定
# =============================================================================

def setup_logging(verbose: bool = False):
    """
    ロギングの設定を行う．
    verbose=True の場合は DEBUG レベル，それ以外は INFO レベル．
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level  = level,
        format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt= "%Y-%m-%d %H:%M:%S",
    )


# =============================================================================
# コマンドライン引数の定義
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="HCP LLM ベンチマーク実行スクリプト",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ---- 実験設定 ----
    parser.add_argument(
        "--generator",
        type    = str,
        default = "func_31",
        choices = list_available_generators(),
        help    = "使用する HCP アルゴリズム名",
    )
    parser.add_argument(
        "--n_shot",
        type    = int,
        default = 10,
        help    = "Few-shot 用の正解例数",
    )
    parser.add_argument(
        "--n_test",
        type    = int,
        default = 50,
        help    = "評価を行うテスト問題数",
    )
    parser.add_argument(
        "--seed",
        type    = int,
        default = 42,
        help    = "データ生成に使用する乱数シード",
    )

    # ---- モデル設定 ----
    parser.add_argument(
        "--provider",
        type    = str,
        default = "gemini",
        choices = ["gemini", "ollama", "mock", "lora"],
        help    = "LLM プロバイダ",
    )
    parser.add_argument(
        "--model",
        type    = str,
        default = "gemini-2.0-flash",
        help    = "使用するモデル名（Gemini: gemini-2.0-flash, Ollama: qwen2.5:7b 等）",
    )
    parser.add_argument(
        "--sleep_sec",
        type    = float,
        default = 4.0,
        help    = "リクエスト間の待機時間（Gemini の API レートリミット回避用）",
    )
    parser.add_argument(
        "--api_key",
        type    = str,
        default = None,
        help    = "Gemini API キー（未指定の場合は環境変数 GEMINI_API_KEY を参照）",
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
        default = 32,
        help    = "並列リクエスト数（Ollama/ローカル実行時のみ推奨。デフォルト: 32）",
    )
    parser.add_argument(
        "--stage",
        type    = int,
        default = 1,
        choices = [0, 1, 2, 3],
        help    = "実験の開示段階（Stage 0: 鍵・ルール無し, Stage 1: 鍵あり・ルール無し, Stage 2: 鍵無し・ルールあり, Stage 3: 鍵部分公開・ルールあり）",
    )
    parser.add_argument(
        "--k_disclosed",
        type    = int,
        default = 5,
        help    = "Stage 3 で公開する秘密鍵の要素数 K",
    )
    parser.add_argument(
        "--paradigm",
        type    = str,
        default = "pure",
        choices = ["pure", "rationale", "pot", "rationale_pot"],
        help    = "実験手法の選択（pure, rationale, pot, rationale_pot）",
    )


    # ---- プロンプト設定 ----
    parser.add_argument(
        "--prompt_mode",
        type    = str,
        default = "text",
        choices = ["text"],
        help    = "プロンプトの構成モード",
    )

    # ---- 出力設定 ----
    parser.add_argument(
        "--output_base_dir",
        type    = str,
        default = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "benchmarks"
        ),
        help    = "結果ファイルを保存するベースディレクトリ",
    )
    parser.add_argument(
        "--verbose",
        action  = "store_true",
        help    = "デバッグログと詳細な推論過程を表示する",
    )

    return parser.parse_args()


# =============================================================================
# メイン実行ロジック
# =============================================================================

def run_benchmark(args):
    """
    ベンチマーク実験を一通り実行し，結果を保存する．
    """
    # paradigm 設定から rationale と use_code の真偽値を決定する
    rationale = args.paradigm in ["rationale", "rationale_pot"]
    use_code = args.paradigm in ["pot", "rationale_pot"]

    print("=" * 60)
    print("【ベンチマーク設定】")
    print(f"  プロバイダ   : {args.provider}")
    print(f"  モデル       : {args.model}")
    print(f"  ジェネレータ : {args.generator}")
    print(f"  Few-shot 数  : {args.n_shot} 件")
    print(f"  テスト件数   : {args.n_test} 件")
    print(f"  API 待機時間 : {args.sleep_sec} 秒 / リクエスト")
    print(f"  乱数シード   : {args.seed}")
    print(f"  PoT方式      : {'ON' if use_code else 'OFF'}")
    print(f"  実験ステージ : Stage {args.stage}")
    if args.stage == 3:
        print(f"  鍵公開数 (K) : {args.k_disclosed}")
    print("=" * 60)

    # =========================================================================
    # Step 1: データセットの準備
    # =========================================================================
    print("\nデータセットを生成中...")
    shot_df, test_df, sgm = generate_dataset(
        generator_name = args.generator,
        n_shot         = args.n_shot,
        n_test         = args.n_test,
        seed           = args.seed,
    )
    print(f"  Few-shot 例題: {len(shot_df)} 件")
    print(f"  テスト問題  : {len(test_df)} 件")
    if sgm:
        print(f"  秘密のテーブル(sgm)をロードしました（サイズ: {len(sgm)}）")

    # =========================================================================
    # Step 2: クライアントとビルダーの初期化
    # =========================================================================
    print("\nモジュールを初期化中...")

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
    elif args.provider == "mock":
        client = MockClient(
            model_name = args.model,
            sleep_sec  = 0.05,
        )
    elif args.provider == "lora":
        from llm_agent import LoraClient
        client = LoraClient(run_dir=args.model)

    prompt_builder = get_prompt_builder(mode=args.prompt_mode)
    
    # paradigm フォルダ名にステージ情報を付加して管理する
    paradigm = f"stage{args.stage}_{args.paradigm}"

    # lora プロバイダの場合はモデル名をパスから安全に抽出
    model_dir_name = args.model
    if args.provider == "lora":
        parts = [p for p in args.model.split(os.sep) if p]
        if len(parts) >= 4:
            model_dir_name = parts[-4] + "_finetuned"
        else:
            model_dir_name = os.path.basename(args.model.rstrip(os.sep)) + "_finetuned"

    output_dir = make_output_dir(
        base_dir       = args.output_base_dir,
        generator_name = args.generator,
        model_name     = model_dir_name,
        paradigm       = paradigm,
    )
    evaluator = Evaluator(output_dir=output_dir)

    print(f"  初期化完了．出力先: {output_dir}")

    # =========================================================================
    # Step 3: テスト問題ループ
    # =========================================================================
    print(f"\nベンチマークを開始します（並列数: {args.parallel}）...\n")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_item(i, row):
        print(f"  [{i + 1:3d}/{args.n_test}] 推論開始...")
        
        challenge, correct_ans = extract_challenge_and_response(row)

        prompt = prompt_builder.build_fewshot_prompt(
            shot_df           = shot_df,
            test_challenge    = challenge,
            generator_name    = args.generator,
            include_rationale = rationale,
            use_code          = use_code,
            sgm               = sgm,
            stage             = args.stage,
            k_disclosed       = args.k_disclosed
        )

        raw_response, predicted = client.predict(prompt)

        # コード実行が有効な場合，コードを抽出して実行
        if use_code:
            code_match = re.search(r"```python\s+(.*?)\s+```", raw_response, re.DOTALL)
            if code_match:
                code_str = code_match.group(1)
                code_result = CodeExecutor.execute_llm_code(code_str, challenge)
                if code_result is not None:
                    predicted = code_result

        record = BenchmarkRecord(
            challenge    = challenge,
            correct_ans  = correct_ans,
            predicted    = predicted,
            raw_response = raw_response,
        )
        return i, record

    results = [None] * len(test_df)

    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(process_item, i, row): i for i, row in test_df.iterrows()}
        
        for future in as_completed(futures):
            idx, record = future.result()
            results[idx] = record
            evaluator.add_record(record)
            
            status_icon = "✓" if record.is_correct else ("?" if record.predicted is None else "✗")
            print(
                f"\n  [{idx + 1:3d}/{args.n_test}] {status_icon} "
                f"正解={record.correct_ans}, 予測={record.predicted if record.predicted is not None else 'ERR'}"
            )
            
            if args.verbose:
                clean_content = re.sub(r"<(think|思考過程)>.*?</(think|思考过程|思考過程)>", "[THINKING...]", record.raw_response, flags=re.DOTALL | re.IGNORECASE)
                tail = clean_content[-100:].replace("\n", " ") if len(clean_content) > 100 else clean_content.replace("\n", " ")
                print(f"      [Result Tail]: ...{tail}")
            elif record.predicted is None:
                print(f"      [Parse Error Context]: {record.raw_response[-100:].replace('\\n', ' ')}")

    metadata = {
        "provider"       : args.provider,
        "generator_name" : args.generator,
        "n_shot"         : args.n_shot,
        "n_test"         : args.n_test,
        "seed"           : args.seed,
        "model_name"     : args.model,
        "sleep_sec"      : args.sleep_sec,
        "prompt_mode"    : args.prompt_mode,
        "rationale"      : rationale,
        "use_code"       : use_code,
        "paradigm"       : args.paradigm,
        "stage"          : args.stage,
        "k_disclosed"    : args.k_disclosed,
        "output_dir"     : output_dir,
    }

    evaluator.save_results(metadata=metadata)


if __name__ == "__main__":
    args = parse_args()
    setup_logging(verbose=args.verbose)
    run_benchmark(args)
