#!/usr/bin/env python3
"""
既存の評価結果を，現在の正しいディレクトリ構造へ移す．

移動先は各 metrics.json に記録されている実験条件から `hcp.evaluation.make_run_dir`
で計算する．ディレクトリ名を正規表現で解釈しないので，過去のどの構造から来ても
（そして今後また構造を変えても）同じ手順で移行できる．

これまでの変更:
  2026-09-12(1) 条件に評価件数を追加      n{N}_stage{S}_k{K} → n{N}_t{T}_stage{S}_k{K}
                件数の違う結果が同じ場所に書かれ，50件と500件を見分けられなかった．
  2026-09-12(2) アルゴリズムを先頭へ      {model}/{algo}/... → {algo}/.../{model}
                モデル名が学習 run ごとに変わるため，同じアルゴリズムの結果が
                60個のディレクトリに散っていた．

    python3 tools/migrate_eval_paths.py            # 変更内容の確認のみ（既定）
    python3 tools/migrate_eval_paths.py --apply    # 実際に移動する
"""
import argparse
import json
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from hcp.evaluation import make_run_dir  # noqa: E402

EVALS_DIR = os.path.join(REPO_ROOT, "results", "llm_eval")


def display_model_name(cfg: dict) -> str:
    """ディレクトリ名に使われる短いモデル名を復元する．

    metrics.json の config["model"] にはアダプタ**ディレクトリのパス**が入っており，
    実際にディレクトリ名として使われる LoraClient.model_name（例
    `qwen2.5_3b_ft_20260729_023201`）とは別物である。LoraClient と同じ手順で
    組み立て直す（src/hcp/clients.py の LoraClient.__init__ と揃えること）。
    """
    model = cfg.get("model", "unknown")
    if cfg.get("provider") != "lora":
        return model
    meta = os.path.join(model, "train_metadata.json")
    if not os.path.exists(meta):
        return model
    with open(meta, encoding="utf-8") as f:
        base = json.load(f)["args"]["model"]
    base_short = re.sub(
        r"-?instruct", "", base.split("/")[-1], flags=re.IGNORECASE
    ).strip("-").replace("-", "_").lower()
    run_stamp = os.path.basename(model.rstrip(os.sep)).removeprefix("run_")
    return f"{base_short}_ft_{run_stamp}"


def canonical_dir(metrics_path: str) -> str | None:
    with open(metrics_path, encoding="utf-8") as f:
        data = json.load(f)
    cfg = data.get("config")
    if not cfg:
        return None  # 旧形式（config を持たない）は対象外
    n_test = data.get("n_test", cfg.get("n_test"))
    if n_test is None:
        return None
    task = data.get("task", cfg.get("task", "predict"))
    label = cfg.get("task_label") or (
        f"predict_{cfg.get('paradigm', 'pure')}" if task == "predict" else "recover_key")
    return make_run_dir(
        base_dir=EVALS_DIR,
        model=display_model_name(cfg),
        algorithm=cfg.get("algorithm", "unknown"),
        task_label=label,
        stage=cfg.get("stage", 2),
        k_disclosed=cfg.get("k_disclosed", 0),
        n_shot=cfg.get("n_shot", 0),
        key_seed=cfg.get("key_seed", 0),
        data_seed=cfg.get("data_seed", 0),
        n_test=n_test,
    )


def plan_moves() -> tuple[list[tuple[str, str]], list[str]]:
    moves, skipped = [], []
    for dirpath, _dirnames, filenames in os.walk(EVALS_DIR):
        if "metrics.json" not in filenames:
            continue
        dst = canonical_dir(os.path.join(dirpath, "metrics.json"))
        if dst is None:
            skipped.append(dirpath)
        elif os.path.normpath(dst) != os.path.normpath(dirpath):
            moves.append((dirpath, dst))
    return moves, skipped


def prune_empty() -> int:
    """空になったディレクトリを消す．

    os.walk は走査前のディレクトリ一覧を保持するので，子を消しても同じ走査の中では
    親が空だと分からない．変化がなくなるまで繰り返す．
    """
    removed = 0
    while True:
        gone = 0
        for dirpath, dirnames, filenames in os.walk(EVALS_DIR, topdown=False):
            if dirpath != EVALS_DIR and not dirnames and not filenames:
                os.rmdir(dirpath)
                gone += 1
        removed += gone
        if gone == 0:
            return removed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="実際に移動する（既定は確認のみ）")
    args = ap.parse_args()

    moves, skipped = plan_moves()
    if skipped:
        print(f"[情報] 条件を復元できないため据え置く結果が {len(skipped)} 件あります。")
    if not moves:
        print("移行対象はありません（すべて正しい場所にあります）。")
        return

    print(f"移行対象 {len(moves)} 件\n")
    for src, dst in moves[:5]:
        print(f"  {os.path.relpath(src, REPO_ROOT)}\n    -> {os.path.relpath(dst, REPO_ROOT)}")
    if len(moves) > 5:
        print(f"  ... 他 {len(moves) - 5} 件")

    conflicts = [d for _s, d in moves if os.path.exists(d)]
    if conflicts:
        print(f"\n[中止] 移動先がすでに存在します（{len(conflicts)} 件）。手で確認してください。",
              file=sys.stderr)
        for d in conflicts[:5]:
            print(f"  {os.path.relpath(d, REPO_ROOT)}", file=sys.stderr)
        sys.exit(1)

    if not args.apply:
        print("\n確認のみです。実行するには --apply を付けてください。")
        return

    for src, dst in moves:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
    pruned = prune_empty()
    print(f"\n完了: {len(moves)} 件を移動し，空になった {pruned} 個のディレクトリを削除しました。")


if __name__ == "__main__":
    main()
