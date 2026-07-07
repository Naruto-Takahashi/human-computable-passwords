#!/usr/bin/env python3
import torch
# Initialize CUDA context first to avoid conflict with tensorflow imports
if torch.cuda.is_available():
    torch.cuda.init()

import argparse
import os
import re
import sys
import time
from datetime import datetime
import json
import numpy as np
import pandas as pd

# Add code/ to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

from llm_agent.data_generator import generate_dataset, extract_challenge_and_response, list_available_generators
from llm_agent.prompt import TextPromptBuilder

def parse_args():
    parser = argparse.ArgumentParser(description="HCP LLM Fine-tuning via QLoRA")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Hugging Face model identifier")
    parser.add_argument("--generator", type=str, default="func_31", choices=list_available_generators(), help="HCP algorithm generator name")
    parser.add_argument("--n_shot", type=int, default=10, help="Number of few-shot examples embedded in each prompt (default: 10)")
    parser.add_argument("--n_train", type=int, default=500, help="Number of training samples")
    parser.add_argument("--n_val", type=int, default=-1, help="Number of validation samples (default: n_train // 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--stage", type=int, default=0, choices=[0, 1, 2, 3],
                        help="Disclosure stage for the training prompt. 0=no rule/no key (default), "
                             "1=key disclosed, 2=rule disclosed/key hidden, 3=rule disclosed/key partially disclosed")
    parser.add_argument("--k_disclosed", type=int, default=0, help="Number of secret key elements to disclose for stage=3")

    # Paradigm: controls completion format (matches run_prompting.py --paradigm)
    parser.add_argument("--paradigm", type=str, default="pot", choices=["pure", "pot", "rationale"],
                        help="Training target format: 'pure'=JSON answer only, 'pot'=Python code block, "
                             "'rationale'=structure-only reasoning (no secret key values) + JSON answer (default: pot)")

    # Training Hyperparameters
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size per GPU")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_len", type=int, default=2048, help="Max sequence length")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA R")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA Alpha")
    parser.add_argument("--quant", type=str, default="4bit", choices=["4bit", "8bit"], help="Base model quantization (量子化ノイズの影響を検証するための切替)")

    args = parser.parse_args()

    # n_val のデフォルトは n_train // 5 に比例させる
    if args.n_val == -1:
        args.n_val = max(1, args.n_train // 5)
        print(f"[INFO] --n_val が未指定のため n_train // 5 = {args.n_val} を使用します")

    return args

def main():
    args = parse_args()
    
    # Set seed
    np.random.seed(args.seed)
    
    # Check GPU availability
    import torch
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    
    # Prepare Output Directories
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # org 名（例: "Qwen/"）を除き、-Instruct を除去してアンダースコア区切り・小文字の短い名前を使用
    # 例: Qwen/Qwen2.5-0.5B-Instruct -> qwen2.5_0.5b
    _base = args.model.split("/")[-1]  # e.g. "Qwen2.5-0.5B-Instruct"
    _base = re.sub(r"-?instruct", "", _base, flags=re.IGNORECASE)  # remove -Instruct
    _base = _base.strip("-")  # strip trailing dash
    model_name_safe = _base.replace("-", "_").lower()  # e.g. "qwen2.5_0.5b"
    output_dir = os.path.join(
        base_dir,
        "results",
        "finetuned_models",
        model_name_safe,
        args.generator,
        f"run_{timestamp}"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Results will be saved to: {output_dir}")
    
    # Generate Datasets
    # We pool data for fewshot examples and training/validation targets
    from llm_agent.data_generator import AVAILABLE_GENERATORS
    generator_func = AVAILABLE_GENERATORS[args.generator]
    total_size = args.n_shot + args.n_train + args.n_val
    
    all_df, sgm = generator_func(total_size)
    all_df = all_df.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    
    few_shot_df = all_df.iloc[:args.n_shot].reset_index(drop=True)
    train_df = all_df.iloc[args.n_shot : args.n_shot + args.n_train].reset_index(drop=True)
    val_df = all_df.iloc[args.n_shot + args.n_train :].reset_index(drop=True)
    
    print(f"Datasets generated. Train size: {len(train_df)}, Val size: {len(val_df)}, Few-shot pool: {len(few_shot_df)}")
    
    # Save datasets/sgm table metadata
    metadata = {
        "args": vars(args),
        "sgm": sgm,
        "few_shot_data": few_shot_df.to_dict(orient="records"),
    }
    with open(os.path.join(output_dir, "train_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print("Debug: Writing train_metadata.json done. Now importing HF libraries...")
    # Import HF libraries
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig
    print("Debug: HF imports done. Now loading tokenizer...")
    
    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    print("Debug: Tokenizer loaded. Checking pad token...")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print("Debug: Tokenizer setup done. Now building datasets...")
        
    # Build HF Datasets
    builder = TextPromptBuilder()
    
    def generate_target_code(generator_name: str, challenge: list[int], sgm: list[int] = None) -> str:
        code = "```python\n"
        code += "def predict_z(X):\n"
        if generator_name == "simple_add":
            code += "    return (X[0] + X[1] + X[2]) % 10\n"
        elif generator_name == "func_13":
            code += f"    sgm = {sgm}\n"
            code += "    X_val = [sgm[i] for i in X]\n"
            code += "    j = X_val[10] % 10\n"
            code += "    return (X_val[j] + X_val[11] + X_val[12] + X_val[13]) % 10\n"
        elif generator_name == "func_22":
            code += f"    sgm = {sgm}\n"
            code += "    X_val = [sgm[i] for i in X]\n"
            code += "    j = (X_val[10] + X_val[11]) % 10\n"
            code += "    return (X_val[j] + X_val[12] + X_val[13]) % 10\n"
        elif generator_name == "func_31":
            code += f"    sgm = {sgm}\n"
            code += "    X_val = [sgm[i] for i in X]\n"
            code += "    j = (X_val[10] + X_val[11] + X_val[12]) % 10\n"
            code += "    return (X_val[j] + X_val[13]) % 10\n"
        elif generator_name == "func_pow":
            code += f"    sgm = {sgm}\n"
            code += "    X_val = [sgm[i] for i in X]\n"
            code += "    return (1 * pow(X_val[10], 4) + 2 * pow(X_val[11], 3) + 3 * pow(X_val[12], 2) + 4 * pow(X_val[13], 1)) % 10\n"
        code += "```"
        return code

    def generate_rationale(generator_name: str, response: int) -> str:
        """
        秘密鍵の値には一切触れず，計算の「構造」だけを自然言語で説明した思考過程を生成する．
        （Stage 0 / PoT の前提：アルゴリズム構造は既知，鍵の値のみ非公開）
        中間の推論トークンにも損失をかけることで，勾配信号を増やす狙い．
        """
        if generator_name == "simple_add":
            reasoning = (
                "考え方:\n"
                "1. 入力 X の X[0], X[1], X[2] を合計する．\n"
                "2. その合計を 10 で割った余りが答えです．\n"
            )
        elif generator_name == "func_13":
            reasoning = (
                "考え方:\n"
                "1. 入力 X の各値は秘密の鍵テーブルのインデックスに対応しており，鍵テーブルを介して実際の計算用の値に変換される．\n"
                "2. 変換後の位置10の値を10で割った余りを j とする．\n"
                "3. 変換後の位置 j, 11, 12, 13 の値を合計し，10で割った余りが答えです．\n"
            )
        elif generator_name == "func_22":
            reasoning = (
                "考え方:\n"
                "1. 入力 X の各値は秘密の鍵テーブルのインデックスに対応しており，鍵テーブルを介して実際の計算用の値に変換される．\n"
                "2. 変換後の位置10と位置11の値の和を10で割った余りを j とする．\n"
                "3. 変換後の位置 j, 12, 13 の値を合計し，10で割った余りが答えです．\n"
            )
        elif generator_name == "func_31":
            reasoning = (
                "考え方:\n"
                "1. 入力 X の各値は秘密の鍵テーブルのインデックスに対応しており，鍵テーブルを介して実際の計算用の値に変換される．\n"
                "2. 変換後の位置10, 11, 12の値の和を10で割った余りを j とする．\n"
                "3. 変換後の位置 j, 13 の値を合計し，10で割った余りが答えです．\n"
            )
        elif generator_name == "func_pow":
            reasoning = (
                "考え方:\n"
                "1. 入力 X の各値は秘密の鍵テーブルのインデックスに対応しており，鍵テーブルを介して実際の計算用の値に変換される．\n"
                "2. 変換後の位置10, 11, 12, 13の値をそれぞれ4乗, 3乗, 2乗, 1乗し，係数1, 2, 3, 4を掛けて合計する．\n"
                "3. その合計を10で割った余りが答えです．\n"
            )
        else:
            reasoning = "考え方:\n1. 与えられた入出力データの法則性から答えを推定する．\n"

        return f"{reasoning}\n{{\n  \"answer\": {response}\n}}"

    def process_df(df):
        records = []
        for _, row in df.iterrows():
            challenge, response = extract_challenge_and_response(row)
            prompt = builder.build_fewshot_prompt(
                shot_df=few_shot_df,
                test_challenge=challenge,
                generator_name=args.generator,
                include_rationale=False,
                use_code=(args.paradigm == "pot"),
                sgm=sgm,
                stage=args.stage,
                k_disclosed=args.k_disclosed
            )

            if args.paradigm == "pot":
                completion = generate_target_code(args.generator, challenge, sgm)
            elif args.paradigm == "rationale":
                completion = generate_rationale(args.generator, response)
            else:  # pure: JSON answer only
                completion = f"{{\n  \"answer\": {response}\n}}"

            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion}
            ]

            records.append({"messages": messages})
        return Dataset.from_list(records)

    train_dataset = process_df(train_df)
    val_dataset = process_df(val_df) if len(val_df) > 0 else None

    print("Formatting complete. Example training messages:")
    print(train_dataset[0]["messages"])
    
    # QLoRA configuration
    if args.quant == "8bit":
        bnb_config = BitsAndBytesConfig(load_in_8bit=True)
    else:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        )

    print(f"Loading base model in {args.quant}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    model = prepare_model_for_kbit_training(model)
    
    # Target modules for LoRA
    # Detect target modules dynamically or fallback to common ones
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=target_modules,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # Training Arguments
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
    
    # Save adapter
    adapter_path = os.path.join(output_dir, "adapter")
    trainer.model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"Adapter saved to {adapter_path}")
    
    # Log fine-tuning metadata
    ft_summary = {
        "generator": args.generator,
        "model": args.model,
        "elapsed_time_seconds": elapsed_time,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
    }
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(ft_summary, f, ensure_ascii=False, indent=2)

    # Google Drive 同期をバックグラウンドで開始
    import subprocess
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results_dir = os.path.join(base_dir, "results")
    if os.path.exists(results_dir):
        try:
            rclone_path = "/home/nalt/.nix-profile/bin/rclone"
            if not os.path.exists(rclone_path):
                rclone_path = "rclone"
            subprocess.Popen(
                [rclone_path, "sync", results_dir, "gdrive:human-computable-passwords-results"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("Google Drive 同期タスクをバックグラウンドで開始しました。")
        except Exception as e:
            print(f"Google Drive 同期のトリガーに失敗しました: {e}")

if __name__ == "__main__":
    main()
