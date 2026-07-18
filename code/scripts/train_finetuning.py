#!/usr/bin/env python3
# =============================================================================
# train_finetuning.py — QLoRA ファインチューニング（hcp パッケージ版）
# =============================================================================
# 旧版からの研究上重要な変更:
#   1. paradigm "pot" を削除．教師コードに秘密鍵 sgm がリテラルとして埋め込まれ，
#      「鍵推論」ではなく丸暗記に帰着していたため（weekly_report_20260705.md）．
#      残る教師形式は pure（JSON回答のみ）と rationale（鍵値に触れない構造説明+JSON）．
#   2. 学習データのシード空間を評価用と分離．旧版は評価スクリプトと同一シードから
#      同一のデータ列を生成していたため，評価テスト問題が学習データに含まれていた
#      （ホールドアウト評価になっていなかった）．
#      本版では学習サンプルのチャレンジは data_seed + TRAIN_SEED_OFFSET から生成し，
#      評価（run_eval.py --provider lora）は素の data_seed を使うため互いに素になる．
#   3. アルゴリズム定義・プロンプト・rationale は hcp パッケージ（単一情報源）から取得．
#
# 実行には torch 系依存が必要（nix develop には無いため .venv/bin/python を使用）:
#   .venv/bin/python code/scripts/train_finetuning.py --model Qwen/Qwen2.5-3B-Instruct \
#       --algorithm func_22 --paradigm rationale --stage 2 --n_train 200
# 評価:
#   python code/scripts/run_eval.py --provider lora --model results/finetuned_models/... \
#       --algorithm func_22 --stage 2 --key_seeds 0
# =============================================================================

import torch

# Initialize CUDA context first to avoid conflict with tensorflow imports
if torch.cuda.is_available():
    torch.cuda.init()

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hcp import algorithm_names, get_algorithm
from hcp.dataset import extract_challenge_and_response, generate_dataset
from hcp.prompts import build_prompt

# 学習用チャレンジのシード空間を評価用（素の data_seed）から分離するためのオフセット
TRAIN_SEED_OFFSET = 1_000_000


def parse_args():
    parser = argparse.ArgumentParser(description="HCP LLM Fine-tuning via QLoRA")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--algorithm", "--generator", dest="algorithm", type=str,
                        default="func_22", choices=algorithm_names())
    parser.add_argument("--n_shot", type=int, default=10,
                        help="各学習プロンプトに埋め込む Few-shot 例数")
    parser.add_argument("--n_train", type=int, default=500)
    parser.add_argument("--n_val", type=int, default=-1, help="デフォルトは n_train // 5")
    parser.add_argument("--key_seed", type=int, default=0, help="鍵シード（評価時と揃えること）")
    parser.add_argument("--data_seed", type=int, default=0,
                        help="データシード（学習チャレンジは +%d オフセットで生成）" % TRAIN_SEED_OFFSET)
    parser.add_argument("--stage", type=int, default=2, choices=[0, 1, 2, 3],
                        help="学習プロンプトの情報開示ステージ（評価時と揃えること）")
    parser.add_argument("--k_disclosed", type=int, default=0)
    parser.add_argument("--paradigm", type=str, default="rationale",
                        choices=["pure", "rationale"],
                        help="教師形式（pot は鍵リークのため廃止．docs/refactor_notes.md 参照）")
    # Training Hyperparameters
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--grad_accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max_len", type=int, default=2048)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--quant", type=str, default="4bit", choices=["4bit", "8bit"])

    args = parser.parse_args()
    if args.n_val == -1:
        args.n_val = max(1, args.n_train // 5)
        print(f"[INFO] --n_val 未指定のため n_train // 5 = {args.n_val} を使用します")
    return args


def main():
    args = parse_args()
    algorithm = get_algorithm(args.algorithm)

    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"VRAM Total: {vram:.2f} GB")

    # ---- 出力先 ----
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _base = args.model.split("/")[-1]
    _base = re.sub(r"-?instruct", "", _base, flags=re.IGNORECASE).strip("-")
    model_name_safe = _base.replace("-", "_").lower()
    output_dir = os.path.join(
        base_dir, "results", "finetuned_models", model_name_safe,
        args.algorithm, f"run_{timestamp}",
    )
    os.makedirs(output_dir, exist_ok=True)
    print(f"Results will be saved to: {output_dir}")

    # ---- データ生成 ----
    # 鍵は key_seed から決定的に生成（評価時に同じ key_seed を指定すれば同じ鍵になる）．
    # Few-shot 例と学習/検証チャレンジは学習専用のシード空間から生成し，
    # 評価用（素の data_seed）のチャレンジと重複しないようにする．
    train_ds = generate_dataset(
        algorithm,
        n_shot=args.n_shot,
        n_test=args.n_train + args.n_val,
        key_seed=args.key_seed,
        data_seed=args.data_seed + TRAIN_SEED_OFFSET,
    )
    key = train_ds.key
    few_shot_df = train_ds.shot_df
    train_df = train_ds.test_df.iloc[: args.n_train].reset_index(drop=True)
    val_df = train_ds.test_df.iloc[args.n_train :].reset_index(drop=True)
    print(f"Datasets generated. Train: {len(train_df)}, Val: {len(val_df)}, Few-shot: {len(few_shot_df)}")

    metadata = {
        "args": vars(args),
        "sgm": key,
        "few_shot_data": few_shot_df.to_dict(orient="records"),
        "train_seed_offset": TRAIN_SEED_OFFSET,
    }
    with open(os.path.join(output_dir, "train_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ---- HF ライブラリ ----
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def completion_for(response: int) -> str:
        answer_json = f"{{\n  \"answer\": {response}\n}}"
        if args.paradigm == "rationale":
            # 鍵の値に一切触れない構造のみの思考過程（単一情報源から取得）
            return f"{algorithm.rationale_text}\n{answer_json}"
        return answer_json

    def process_df(df) -> Dataset:
        records = []
        for _, row in df.iterrows():
            challenge, response = extract_challenge_and_response(row)
            prompt = build_prompt(
                algorithm=algorithm,
                shot_df=few_shot_df,
                task="predict",
                stage=args.stage,
                k_disclosed=args.k_disclosed,
                key=key,
                test_challenge=challenge,
                paradigm="pure",
            )
            records.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": completion_for(response)},
                ]
            })
        return Dataset.from_list(records)

    train_dataset = process_df(train_df)
    val_dataset = process_df(val_df) if len(val_df) > 0 else None

    print("Formatting complete. Example training messages:")
    print(train_dataset[0]["messages"])

    # ---- QLoRA ----
    if args.quant == "8bit":
        bnb_config = BitsAndBytesConfig(load_in_8bit=True)
    else:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=(
                torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            ),
        )

    print(f"Loading base model in {args.quant}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, quantization_config=bnb_config, device_map="auto", trust_remote_code=True
    )
    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    training_args = SFTConfig(
        output_dir=os.path.join(output_dir, "checkpoints"),
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        logging_steps=5,
        eval_strategy="epoch" if val_dataset else "no",
        save_strategy="epoch",
        save_total_limit=1,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        optim="adamw_8bit",
        report_to="none",
        remove_unused_columns=False,
        assistant_only_loss=True,
        max_length=args.max_len,
        dataloader_num_workers=4,
        dataloader_pin_memory=True,
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        args=training_args,
    )

    print("Starting training...")
    start_time = time.time()
    trainer.train()
    elapsed_time = time.time() - start_time
    print(f"Training completed in {elapsed_time:.2f} seconds.")

    # 学習履歴の保存と可視化（history.csv / training_curves.png）
    from hcp.plotting import save_training_artifacts

    save_training_artifacts(
        trainer.state.log_history,
        output_dir,
        title=f"{model_name_safe} / {args.algorithm} / stage{args.stage} / "
              f"{args.paradigm} / n_train={args.n_train}",
    )

    adapter_path = os.path.join(output_dir, "adapter")
    trainer.model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"Adapter saved to {adapter_path}")

    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "algorithm": args.algorithm,
                "model": args.model,
                "paradigm": args.paradigm,
                "stage": args.stage,
                "elapsed_time_seconds": elapsed_time,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
            },
            f, ensure_ascii=False, indent=2,
        )
    print("完了。評価: python code/scripts/run_eval.py --provider lora "
          f"--model {output_dir} --algorithm {args.algorithm} --stage {args.stage} "
          f"--key_seeds {args.key_seed} --data_seeds {args.data_seed}")


if __name__ == "__main__":
    main()
