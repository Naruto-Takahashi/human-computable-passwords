import os
import re
import time
import logging
from typing import Optional
import requests

try:
    from google import genai
    from google.genai import types
except ImportError:
    # google-genai may not be installed in all environments
    genai = None
    types = None

logger = logging.getLogger(__name__)

class BaseLLMClient:
    """
    LLM クライアントの基底クラス．
    共通のパース処理などを提供する．
    """
    def _parse_digit_from_response(self, text: str) -> Optional[int]:
        """
        API レスポンステキストから予測値（0〜9の1桁整数）を抽出する．
        """
        # Markdown の強調記号（** __ * _）を除去してパースしやすくする
        cleaned = re.sub(r"[*_`]", "", text)

        # ---- パターン 1: "Answer: <digit>" ----
        match = re.search(r"Answer\s*[：:]\s*([0-9])", cleaned, re.IGNORECASE)
        if match:
            digit = int(match.group(1))
            logger.debug(f"パース成功（Answer:パターン）: {digit}")
            return digit

        # ---- パターン 2: "答え: <digit>" / "答え：<digit>" (日本語応答) ----
        match = re.search(r"答え\s*[：:]\s*([0-9])", cleaned)
        if match:
            digit = int(match.group(1))
            logger.debug(f"パース成功（答え:パターン）: {digit}")
            return digit

        # ---- パターン 3: "Z = <digit>" / "Z=<digit>" (数式表記) ----
        match = re.search(r"\bZ\s*=\s*([0-9])\b", cleaned)
        if match:
            digit = int(match.group(1))
            logger.debug(f"パース成功（Z=パターン）: {digit}")
            return digit

        # ---- パターン 4: 最終行に含まれる唯一の1桁数字 ----
        non_empty_lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        if non_empty_lines:
            last_line = non_empty_lines[-1]
            digits_in_last = re.findall(r"[0-9]", last_line)
            if len(digits_in_last) == 1:
                digit = int(digits_in_last[0])
                logger.debug(f"パース成功（最終行単一数字パターン）: {digit}")
                return digit

        # ---- パターン 5: テキスト末尾に最も近い1桁数字 ----
        all_digits = re.findall(r"[0-9]", cleaned)
        if all_digits:
            digit = int(all_digits[-1])
            logger.debug(f"パース成功（末尾数字フォールバック）: {digit}")
            return digit

        return None

class GeminiClient(BaseLLMClient):
    """
    Gemini API クライアント．
    """
    def __init__(
        self,
        model_name : str   = "gemini-2.5-flash",
        sleep_sec  : float = 4.0,
        api_key    : Optional[str] = None,
    ):
        if genai is None:
            raise ImportError("google-genai package is not installed.")

        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "Gemini API キーが見つかりません．環境変数 GEMINI_API_KEY を設定してください．"
            )

        self.client     = genai.Client(api_key=resolved_key)
        self.model_name = model_name
        self.sleep_sec  = sleep_sec

        self._generation_config = types.GenerateContentConfig(
            temperature       = 0.0,
            top_p             = 1.0,
            max_output_tokens = 8192,
            thinking_config   = types.ThinkingConfig(thinking_budget=1024),
        )

        logger.info(f"GeminiClient 初期化完了: model={self.model_name}, sleep={self.sleep_sec}s")

    def predict(self, prompt: str) -> tuple[str, Optional[int]]:
        raw_response: str = ""
        parsed_digit: Optional[int] = None
        max_retries = 10
        base_delay = 5.0

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model    = self.model_name,
                    contents = prompt,
                    config   = self._generation_config,
                )
                raw_response = response.text
                parsed_digit = self._parse_digit_from_response(raw_response)
                time.sleep(self.sleep_sec)
                break
            except Exception as e:
                err_msg = str(e)
                if attempt == max_retries - 1:
                    raw_response = f"ERROR: {err_msg}"
                    break
                wait_match = re.search(r"[Pp]lease retry in ([0-9.]+)\s*s", err_msg)
                sleep_time = float(wait_match.group(1)) + 1.0 if wait_match else base_delay * (2 ** attempt)
                time.sleep(sleep_time)

        return raw_response, parsed_digit

class OllamaClient(BaseLLMClient):
    """
    Ollama API クライアント．
    """
    def __init__(
        self,
        model_name : str = "qwen2.5:3b",
        api_url    : str = "http://localhost:11434/api/generate",
    ):
        self.model_name = model_name
        self.api_url    = api_url
        self._options = {
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 42,
            "num_predict": 256,
        }
        logger.info(f"OllamaClient 初期化完了: model={self.model_name}, endpoint={self.api_url}")

    def predict(self, prompt: str, options_override: Optional[dict] = None) -> tuple[str, Optional[int]]:
        raw_response: str = ""
        parsed_digit: Optional[int] = None
        max_retries = 3

        options = self._options.copy()
        if options_override:
            options.update(options_override)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, json=payload, timeout=600)
                response.raise_for_status()
                result_json = response.json()
                raw_response = result_json.get("response", "")
                parsed_digit = self._parse_digit_from_response(raw_response)
                break
            except Exception as e:
                raw_response = f"ERROR: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(1)

        return raw_response, parsed_digit
