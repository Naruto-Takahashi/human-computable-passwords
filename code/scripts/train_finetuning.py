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

from core.generator import ComputablePasswordGenerator
from llm_agent.data_generator import generate_dataset, extract_challenge_and_response, list_available_generators
from llm_agent.prompt import TextPromptBuilder

def parse_args():
    parser = argparse.ArgumentParser(description="HCP LLM Fine-tuning via QLoRA")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Hugging Face model identifier")
    parser.add_argument("--generator", type=str, default="func_31", choices=list_available_generators(), help="HCP algorithm generator name")
    parser.add_argument("--stage", type=int, default=1, choices=[0, 1, 2, 3], help="Stage of data disclosure")
    parser.add_argument("--k_disclosed", type=int, default=0, help="Number of disclosed elements in stage 3")
    parser.add_argument("--n_shot", type=int, default=5, help="Number of few-shot examples embedded in each prompt")
    parser.add_argument("--n_train", type=int, default=500, help="Number of training samples")
    parser.add_argument("--n_val", type=int, default=100, help="Number of validation samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    # Training Hyperparameters
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size per GPU")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_len", type=int, default=2048, help="Max sequence length")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA R")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA Alpha")
    parser.add_argument("--include_rationale", action="store_true", help="Include reasoning chain in training completions")
    parser.add_argument("--include_fewshot_rationale", action="store_true", help="Include reasoning chain in few-shot prompts")
    
    return parser.parse_args()

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
        f"stage{args.stage}",
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
    
    def process_df(df):
        records = []
        for _, row in df.iterrows():
            challenge, response = extract_challenge_and_response(row)
            prompt = builder.build_fewshot_prompt(
                shot_df=few_shot_df,
                test_challenge=challenge,
                generator_name=args.generator,
                include_rationale=args.include_fewshot_rationale,
                use_code=False,
                sgm=sgm,
                stage=args.stage,
                k_disclosed=args.k_disclosed
            )
            
            if args.include_rationale:
                visible_sgm = sgm if args.stage in [1, 3] else None
                rationale = ComputablePasswordGenerator.explain_logic(args.generator, row, sgm=visible_sgm)
                completion = f"思考過程：\n{rationale}\n\n{{\n  \"answer\": {response}\n}}"
            else:
                completion = f"{{\n  \"answer\": {response}\n}}"
                
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion}
            ]
            
            formatted_chat = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            records.append({"text": formatted_chat})
        return Dataset.from_list(records)
        
    train_dataset = process_df(train_df)
    val_dataset = process_df(val_df) if len(val_df) > 0 else None
    
    print("Formatting complete. Example training text:")
    print(train_dataset[0]["text"][:1000] + "\n...")
    
    # QLoRA configuration
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    )
    
    print("Loading base model in 4-bit...")
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
        dataset_text_field="text",
        max_length=args.max_len,
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
        "stage": args.stage,
        "model": args.model,
        "elapsed_time_seconds": elapsed_time,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
    }
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(ft_summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
