# =============================================================================
# clients.py — LLM プロバイダクライアント
# =============================================================================
# 旧 llm_agent/clients.py からの主な変更:
#   - predict() は生テキストのみ返す（パースは executor.py に分離．
#     タスクごとに抽出対象が異なるため，クライアントはパースに関与しない）
#   - Ollama の num_ctx をプロンプト長から自動計算（固定4096では n_shot を増やした
#     相転移スイープでプロンプトが黙って切り捨てられ，実験が無効になる）
#   - MockClient は「パイプライン疎通確認専用」と明確化（正解は知らないため，
#     predict の期待正解率は約10%．形式的に正しい応答を返すことだけを保証する）
# =============================================================================

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)


class BaseLLMClient:
    model_name: str = "unknown"

    def predict(self, prompt: str) -> str:
        """プロンプトを送信し，生のレスポンステキストを返す．"""
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    """Gemini API クライアント．"""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        sleep_sec: float = 4.0,
        api_key: Optional[str] = None,
        thinking_budget: int = 1024,
        max_output_tokens: int = 8192,
    ):
        from google import genai
        from google.genai import types

        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "Gemini API キーが見つかりません．環境変数 GEMINI_API_KEY を設定してください．"
            )

        self.client = genai.Client(api_key=resolved_key)
        self.model_name = model_name
        self.sleep_sec = sleep_sec
        self._generation_config = types.GenerateContentConfig(
            temperature=0.0,
            top_p=1.0,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
        )
        logger.info(f"GeminiClient 初期化完了: model={self.model_name}, sleep={self.sleep_sec}s")

    def predict(self, prompt: str) -> str:
        max_retries = 10
        base_delay = 5.0
        qualified = self.model_name
        if not qualified.startswith("models/"):
            qualified = f"models/{qualified}"

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=qualified, contents=prompt, config=self._generation_config
                )
                time.sleep(self.sleep_sec)
                return response.text or ""
            except Exception as e:
                err_msg = str(e)
                if attempt == max_retries - 1:
                    return f"ERROR: {err_msg}"
                wait_match = re.search(r"[Pp]lease retry in ([0-9.]+)\s*s", err_msg)
                sleep_time = (
                    float(wait_match.group(1)) + 1.0 if wait_match else base_delay * (2**attempt)
                )
                time.sleep(sleep_time)
        return "ERROR: unreachable"


class OllamaClient(BaseLLMClient):
    """Ollama API クライアント．"""

    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        api_url: str = "http://localhost:11434/api/generate",
        num_predict: int = 4096,
        num_ctx: Optional[int] = None,
    ):
        self.model_name = model_name
        self.api_url = api_url
        self.num_predict = num_predict
        self.num_ctx_override = num_ctx
        logger.info(f"OllamaClient 初期化完了: model={self.model_name}, endpoint={self.api_url}")

    def _auto_num_ctx(self, prompt: str) -> int:
        """
        プロンプトが確実にコンテキストへ収まるサイズを見積もる．
        日本語混じりテキストの控えめな見積もりとして 1文字≈1トークンとし，
        生成分（num_predict）を加えて 2 の冪へ切り上げる（下限 4096）．
        """
        needed = len(prompt) + self.num_predict
        ctx = 4096
        while ctx < needed:
            ctx *= 2
        return ctx

    def predict(self, prompt: str) -> str:
        import requests

        options = {
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 42,
            "num_predict": self.num_predict,
            "num_ctx": self.num_ctx_override or self._auto_num_ctx(prompt),
            "num_batch": 512,
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": options,
        }

        max_retries = 3
        for attempt in range(max_retries):
            full_text: list[str] = []
            try:
                response = requests.post(self.api_url, json=payload, timeout=1800, stream=True)
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("response") or chunk.get("message", {}).get("content")
                    if delta:
                        full_text.append(delta)
                    if chunk.get("done"):
                        break
                return "".join(full_text)
            except Exception as e:
                if full_text:
                    logger.warning(f"推論の途中で接続エラーが発生（受信済み内容で継続）: {e}")
                    return "".join(full_text)
                if attempt == max_retries - 1:
                    return f"ERROR: {e}"
                time.sleep(1)
        return "ERROR: unreachable"


class MockClient(BaseLLMClient):
    """
    パイプライン疎通確認専用のモッククライアント（正解を知らない）．
    - predict/pure     : ランダムな数字の JSON 回答（期待正解率 ≈ 10%）
    - predict/pot      : ランダム定数を返す predict_z のコードブロック
    - recover_key      : ランダムな鍵テーブルの JSON 回答
    形式的に正しい応答を返すことだけを保証する．精度の検証には使えない．
    """

    def __init__(self, model_name: str = "mock-model", sleep_sec: float = 0.02, seed: int = 0):
        import random

        self.model_name = model_name
        self.sleep_sec = sleep_sec
        self.random = random.Random(seed)

    def predict(self, prompt: str) -> str:
        time.sleep(self.sleep_sec)
        thinking = "<think>\nThis is a mocked thinking process for pipeline testing.\n</think>\n"

        if "sgm_table" in prompt:
            size_match = re.search(r"長さ (\d+) の整数リスト", prompt)
            size = int(size_match.group(1)) if size_match else 26
            table = [self.random.randint(0, 9) for _ in range(size)]
            return f"{thinking}{{\"sgm_table\": {table}}}"

        if "```python" in prompt:
            digit = self.random.randint(0, 9)
            return (
                f"{thinking}法則を推定しました。\n"
                f"```python\ndef predict_z(X):\n    return {digit}\n```"
            )

        digit = self.random.randint(0, 9)
        return f"{thinking}{{\n  \"answer\": {digit}\n}}"


class LoraClient(BaseLLMClient):
    """ローカルのファインチューニング済み LoRA モデル用クライアント．"""

    def __init__(self, run_dir: str, max_new_tokens: int = 512):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        self.run_dir = run_dir
        self.max_new_tokens = max_new_tokens
        meta_path = os.path.join(run_dir, "train_metadata.json")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        with open(meta_path, "r", encoding="utf-8") as f:
            train_meta = json.load(f)

        self.base_model_name = train_meta["args"]["model"]
        # 評価結果ディレクトリ名に使われる識別子．ベースモデル名 + _ft + 学習run日時
        # （例: qwen2.5_3b_ft_20260716_125310）で，どのアダプターの評価か一目で分かるようにする
        base_short = re.sub(
            r"-?instruct", "", self.base_model_name.split("/")[-1], flags=re.IGNORECASE
        ).strip("-").replace("-", "_").lower()
        run_stamp = os.path.basename(run_dir.rstrip(os.sep)).removeprefix("run_")
        self.model_name = f"{base_short}_ft_{run_stamp}"
        adapter_path = os.path.join(run_dir, "adapter")

        logger.info(f"LoraClient: Loading base model {self.base_model_name}")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=(
                torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            ),
        )
        self.tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        logger.info(f"LoraClient: Loading LoRA adapter from {adapter_path}")
        self.model = PeftModel.from_pretrained(base_model, adapter_path)
        self.model.eval()

    def predict(self, prompt: str) -> str:
        import torch

        messages = [{"role": "user", "content": prompt}]
        formatted = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(formatted, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = outputs[0][inputs.input_ids.shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True)


def create_client(provider: str, model: str, **kwargs) -> BaseLLMClient:
    """プロバイダ名からクライアントを生成するファクトリ．"""
    if provider == "gemini":
        return GeminiClient(model_name=model, **kwargs)
    if provider == "ollama":
        return OllamaClient(model_name=model, **kwargs)
    if provider == "mock":
        return MockClient(model_name=model)
    if provider == "lora":
        return LoraClient(run_dir=model)
    raise ValueError(f"未知のプロバイダです: '{provider}'")
