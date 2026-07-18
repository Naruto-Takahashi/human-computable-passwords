# =============================================================================
# evaluation.py — 実験の実行・採点・記録
# =============================================================================
# 旧 llm_agent/evaluator.py からの主な変更:
#   - タスクを predict（応答予測）と recover_key（鍵復元）の2種類に拡張．
#     鍵復元率（Key Recovery Rate）は plan.md の主要評価指標だが旧実装には存在しなかった．
#   - プロンプトを必ずファイルに保存する（先週の stage 強制リセットバグのような
#     「学習条件と評価条件の食い違い」をログから即座に検出できるようにする）
#   - 出力ディレクトリを実験条件から決定的に構成し，スイープのレジューム
#     （完了済み条件のスキップ）を可能にする
# =============================================================================

from __future__ import annotations

import csv
import json
import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

from . import executor
from .clients import BaseLLMClient
from .dataset import HCPDataset, extract_challenge_and_response

logger = logging.getLogger(__name__)

METRICS_FILENAME = "metrics.json"


def git_commit_hash() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("ascii")
            .strip()
        )
    except Exception:
        return "unknown"


def safe_model_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def make_run_dir(
    base_dir: str,
    model: str,
    algorithm: str,
    task_label: str,
    stage: int,
    k_disclosed: int,
    n_shot: int,
    key_seed: int,
    data_seed: int,
) -> str:
    """
    実験条件から決定的な出力ディレクトリを構成する．
    構造: {base}/{model}/{algorithm}/{task}/n{N}_stage{S}_k{K}/ks{key_seed}_ds{data_seed}
    """
    condition = f"n{n_shot}_stage{stage}_k{k_disclosed}"
    seeds = f"ks{key_seed}_ds{data_seed}"
    return os.path.join(
        base_dir, safe_model_name(model), algorithm, task_label, condition, seeds
    )


def is_run_completed(run_dir: str) -> bool:
    return os.path.exists(os.path.join(run_dir, METRICS_FILENAME))


def _write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_response_log(
    run_dir: str, index: int, status: str, body: str, header: dict
) -> None:
    log_dir = os.path.join(run_dir, "responses")
    os.makedirs(log_dir, exist_ok=True)
    lines = [f"# Case {index:03d}", f"- **Result**: {status}"]
    lines += [f"- **{k}**: `{v}`" for k, v in header.items()]
    lines += ["\n---", "\n## Raw LLM Response\n", body]
    with open(os.path.join(log_dir, f"{index:03d}_{status}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _base_metrics(config: dict) -> dict:
    return {
        "config": config,
        "git_commit": git_commit_hash(),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }


# =============================================================================
# タスク 1: predict — テストチャレンジごとの応答予測
# =============================================================================

def run_predict(
    client: BaseLLMClient,
    ds: HCPDataset,
    stage: int,
    k_disclosed: int,
    paradigm: str,
    run_dir: str,
    config: dict,
    parallel: int = 1,
    verbose: bool = False,
) -> dict:
    """
    テスト問題を1問ずつ LLM に予測させ，正解率を測定する．
    paradigm="pot" の場合は生成コードをローカル実行して答えを得る．
    """
    from .prompts import build_prompt

    os.makedirs(run_dir, exist_ok=True)
    test_items = list(ds.test_df.iterrows())
    n_test = len(test_items)

    def process(i: int, row) -> dict:
        challenge, correct = extract_challenge_and_response(row)
        prompt = build_prompt(
            algorithm=ds.algorithm,
            shot_df=ds.shot_df,
            task="predict",
            stage=stage,
            k_disclosed=k_disclosed,
            key=ds.key,
            test_challenge=challenge,
            paradigm=paradigm,
        )
        if i == 0:  # プロンプトの実物を保存（監査・再現用．テスト問題行のみ i で異なる）
            with open(os.path.join(run_dir, "prompt_example.txt"), "w", encoding="utf-8") as f:
                f.write(prompt)

        raw = client.predict(prompt)
        if paradigm == "pot":
            predicted = None
            code = executor.extract_python_block(raw)
            if code is not None:
                predicted = executor.execute_predict_code(code, challenge)
        else:
            predicted = executor.parse_answer_digit(raw)

        return {
            "index": i,
            "challenge": challenge,
            "correct_ans": correct,
            "predicted": predicted,
            "is_correct": predicted is not None and predicted == correct,
            "raw_response": raw,
        }

    results: list[Optional[dict]] = [None] * n_test
    with ThreadPoolExecutor(max_workers=max(parallel, 1)) as pool:
        futures = {pool.submit(process, i, row): i for i, row in test_items}
        done = 0
        for future in as_completed(futures):
            rec = future.result()
            results[rec["index"]] = rec
            done += 1
            icon = "✓" if rec["is_correct"] else ("?" if rec["predicted"] is None else "✗")
            print(
                f"  [{done:3d}/{n_test}] case{rec['index']:03d} {icon} "
                f"正解={rec['correct_ans']}, "
                f"予測={rec['predicted'] if rec['predicted'] is not None else 'ERR'}"
            )
            if verbose and rec["predicted"] is None:
                tail = rec["raw_response"][-120:].replace("\n", " ")
                print(f"      [Parse Error Context]: ...{tail}")

    # ---- 記録 ----
    for rec in results:
        status = (
            "CORRECT"
            if rec["is_correct"]
            else ("PARSE_ERROR" if rec["predicted"] is None else "WRONG")
        )
        _save_response_log(
            run_dir,
            rec["index"],
            status,
            rec["raw_response"],
            {
                "Challenge": rec["challenge"],
                "Correct": rec["correct_ans"],
                "Predicted": rec["predicted"],
            },
        )

    csv_path = os.path.join(run_dir, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["index", "challenge", "correct_ans", "predicted", "is_correct"]
        )
        writer.writeheader()
        for rec in results:
            writer.writerow({k: rec[k] for k in writer.fieldnames})

    correct_count = sum(1 for r in results if r["is_correct"])
    parse_errors = sum(1 for r in results if r["predicted"] is None)
    metrics = {
        **_base_metrics(config),
        "task": "predict",
        "n_test": n_test,
        "correct_count": correct_count,
        "parse_error_count": parse_errors,
        "accuracy": round(correct_count / n_test, 4) if n_test else 0.0,
    }
    _write_json(os.path.join(run_dir, METRICS_FILENAME), metrics)
    return metrics


# =============================================================================
# タスク 2: recover_key — 鍵テーブルの丸ごと逆推定（1回の推論）
# =============================================================================

def run_recover_key(
    client: BaseLLMClient,
    ds: HCPDataset,
    stage: int,
    k_disclosed: int,
    run_dir: str,
    config: dict,
) -> dict:
    """
    観察データから秘密鍵テーブルを逆推定させ，以下を測定する:
      - key_cell_accuracy          : 全セルの一致率
      - undisclosed_cell_accuracy  : 非開示セルのみの一致率（Stage 3 で開示分を除く）
      - key_exact_match            : 完全一致か
      - heldout_accuracy           : 復元鍵を正解アルゴリズムに代入して held-out テスト
                                     問題を解いた場合の正解率（機能的正しさ）
    """
    from .prompts import build_prompt

    os.makedirs(run_dir, exist_ok=True)
    prompt = build_prompt(
        algorithm=ds.algorithm,
        shot_df=ds.shot_df,
        task="recover_key",
        stage=stage,
        k_disclosed=k_disclosed,
        key=ds.key,
    )
    with open(os.path.join(run_dir, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt)

    raw = client.predict(prompt)
    recovered = executor.parse_key_table(raw, ds.algorithm.key_size)

    true_key = ds.key
    metrics = {
        **_base_metrics(config),
        "task": "recover_key",
        "parse_error": recovered is None,
        "recovered_key": recovered,
        "true_key": true_key,
    }

    if recovered is not None:
        matches = [int(r == t) for r, t in zip(recovered, true_key)]
        undisclosed = matches[k_disclosed:] if stage == 3 else matches
        heldout_correct = 0
        n_heldout = len(ds.test_df)
        for _, row in ds.test_df.iterrows():
            challenge, correct = extract_challenge_and_response(row)
            if ds.algorithm.compute(challenge, recovered) == correct:
                heldout_correct += 1
        metrics.update(
            key_cell_accuracy=round(sum(matches) / len(matches), 4),
            undisclosed_cell_accuracy=(
                round(sum(undisclosed) / len(undisclosed), 4) if undisclosed else None
            ),
            key_exact_match=all(matches),
            heldout_accuracy=round(heldout_correct / n_heldout, 4) if n_heldout else None,
            n_heldout=n_heldout,
        )
        status = "EXACT" if all(matches) else "PARTIAL"
    else:
        status = "PARSE_ERROR"

    _save_response_log(
        run_dir, 0, status, raw,
        {"TrueKey": true_key, "Recovered": recovered},
    )
    _write_json(os.path.join(run_dir, METRICS_FILENAME), metrics)

    print(f"  recover_key: {status}")
    if recovered is not None:
        print(
            f"    セル一致率={metrics['key_cell_accuracy']:.2%}, "
            f"held-out精度={metrics['heldout_accuracy']:.2%}"
        )
    return metrics
