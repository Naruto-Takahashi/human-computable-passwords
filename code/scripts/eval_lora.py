#!/usr/bin/env python3
import torch
# Initialize CUDA context first to avoid conflict with tensorflow imports
if torch.cuda.is_available():
    torch.cuda.init()

import argparse
import os
import sys
import json
import re
import numpy as np
import pandas as pd

# Add code/ to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

from core.generator import ComputablePasswordGenerator
from llm_agent.data_generator import extract_challenge_and_response
from llm_agent.prompt import TextPromptBuilder

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Fine-tuned HCP LoRA Model")
    parser.add_argument("--run_dir", type=str, required=True, help="Path to the fine-tuning run directory (containing adapter/ and train_metadata.json)")
    parser.add_argument("--n_test", type=int, default=100, help="Number of test samples to evaluate")
    parser.add_argument("--seed", type=int, default=999, help="Random seed for test data generation (different from train)")
    return parser.parse_args()

def extract_json_answer(text: str) -> int:
    """
    Extract answer from model output, looking for {"answer": X} JSON format.
    """
    try:
        # Search for JSON block
        match = re.search(r'\{\s*"answer"\s*:\s*(\d)\s*\}', text)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    
    # Fallback to finding any single digit
    digits = re.findall(r'\b\d\b', text)
    if digits:
        return int(digits[-1])
        
    return -1

def main():
    args = parse_args()
    
    # Load training metadata
    meta_path = os.path.join(args.run_dir, "train_metadata.json")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        train_meta = json.load(f)
        
    train_args = train_meta["args"]
    sgm = train_meta["sgm"]
    few_shot_records = train_meta["few_shot_data"]
    few_shot_df = pd.DataFrame(few_shot_records)
    
    # Import HF libraries
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    
    adapter_path = os.path.join(args.run_dir, "adapter")
    base_model_name = train_args["model"]
    
    print(f"Loading base model: {base_model_name}")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    )
    
    tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    print(f"Loading LoRA adapter from: {adapter_path}")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()
    
    # Generate test data using the same generator function & key table
    from llm_agent.data_generator import AVAILABLE_GENERATORS
    generator_func = AVAILABLE_GENERATORS[train_args["generator"]]
    
    # Generate test data (ensure it's distinct from train data by using a different seed / offset)
    # To keep it completely independent, generate size = n_test + 1000 and take slice
    np.random.seed(args.seed)
    test_raw_df, _ = generator_func(args.n_test + 50)
    # Ensure it's not overlapping with fewshot
    # Check simple exclusion
    test_df = test_raw_df.iloc[:args.n_test].reset_index(drop=True)
    
    from llm_agent import BenchmarkRecord, Evaluator

    print(f"Test data size: {len(test_df)}")
    
    builder = TextPromptBuilder()
    evaluator = Evaluator(output_dir=args.run_dir)
    
    # Evaluation loop
    with torch.no_grad():
        for i, row in test_df.iterrows():
            challenge, response = extract_challenge_and_response(row)
            prompt = builder.build_fewshot_prompt(
                shot_df=few_shot_df,
                test_challenge=challenge,
                generator_name=train_args["generator"],
                include_rationale=train_args["include_fewshot_rationale"],
                use_code=False,
                sgm=sgm,
                stage=train_args["stage"],
                k_disclosed=train_args["k_disclosed"]
            )
            
            # Format using tokenizer chat template
            messages = [{"role": "user", "content": prompt}]
            formatted_chat = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            inputs = tokenizer(formatted_chat, return_tensors="pt").to("cuda")
            
            # Generate response
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            
            # Extract new generated tokens
            input_len = inputs.input_ids.shape[1]
            generated_tokens = outputs[0][input_len:]
            response_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            predicted_z = extract_json_answer(response_text)
            is_correct = (predicted_z == response)
            
            record = BenchmarkRecord(
                challenge=challenge,
                correct_ans=response,
                predicted=predicted_z if predicted_z != -1 else None,
                raw_response=response_text
            )
            evaluator.add_record(record)
            
            print(f"Sample {i+1}/{args.n_test} | True Z: {response} | Pred Z: {predicted_z} | Correct: {is_correct}")
            
    accuracy = evaluator.accuracy()
    correct_count = sum(1 for r in evaluator.records if r.is_correct)
    print(f"\nFinal Test Accuracy: {accuracy * 100:.2f}% ({correct_count}/{args.n_test})")
    
    # Save evaluation report via standard Evaluator
    eval_report = {
        "generator": train_args["generator"],
        "stage": train_args["stage"],
        "model": train_args["model"],
        "n_test": args.n_test,
        "accuracy": accuracy,
        "correct_count": correct_count,
    }
    evaluator.save_results(metadata=eval_report)
    
    # Also save eval_report.json for compatibility
    eval_report["details"] = [r.to_dict() for r in evaluator.records]
    output_path = os.path.join(args.run_dir, "eval_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, ensure_ascii=False, indent=2)
    print(f"Evaluation report saved to: {output_path}")

if __name__ == "__main__":
    main()
