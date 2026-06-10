import os
import re
import time
import json
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
        JSON 形式での回答を優先的に処理し，フォールバックとして従来の正規表現パースも行う．
        """
        # ---- 1. JSON パースを試行 ----
        try:
            # Markdown のコードブロック ```json ... ``` がある場合は中身を抽出
            json_text = text
            md_match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
            if md_match:
                json_text = md_match.group(1)

            # テキスト内から JSON っぽい部分を探す（{...}）
            json_match = re.search(r"(\{.*\})", json_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                if "answer" in data:
                    val = data["answer"]
                    # 数字が文字列として入っている場合も考慮
                    if isinstance(val, (int, float)):
                        return int(val)
                    if isinstance(val, str) and val.isdigit():
                        return int(val)
        except Exception:
            pass

        # ---- 2. 思考プロセス（thinkタグ）を削除して最終回答セクションのみを対象にする ----
        # <think>...</think> または <思考過程>...</思考過程> を除去
        cleaned = re.sub(r"<(think|思考過程)>.*?</(think|思考过程|思考過程)>", "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Markdown の強調記号（** __ * _）を除去
        cleaned = re.sub(r"[*_`]", "", cleaned)

        # パースを試行する関数（DRY原則のため）
        def find_digit(src: str) -> Optional[int]:
            # パターン 1: "Answer: <digit>"
            match = re.search(r"Answer\s*[：:]\s*.*?([0-9])", src, re.IGNORECASE | re.DOTALL)
            if match: return int(match.group(1))
            # パターン 2: "答え: <digit>"
            match = re.search(r"答え\s*[：:]\s*.*?([0-9])", src)
            if match: return int(match.group(1))
            # パターン 3: "Z = <digit>"
            match = re.search(r"\bZ\s*=\s*([0-9])\b", src)
            if match: return int(match.group(1))
            return None

        # ---- 1. 回答セクション（thinkタグの外）から探す ----
        digit = find_digit(cleaned)
        if digit is not None:
            logger.debug(f"パース成功（回答セクション）: {digit}")
            return digit

        # ---- 2. 思考プロセス（thinkタグの中）の末尾から探す (フォールバック) ----
        think_match = re.search(r"<(think|思考過程)>(.*?)</(think|思考过程|思考過程)>", text, flags=re.DOTALL | re.IGNORECASE)
        if think_match:
            think_content = think_match.group(2)
            # 思考プロセスの最後の200文字程度から答えを探す
            tail_think = think_content[-200:]
            digit = find_digit(tail_think)
            if digit is not None:
                logger.debug(f"パース成功（思考内フォールバック）: {digit}")
                return digit

        # ---- 3. 最終行に含まれる唯一の1桁数字 ----
        non_empty_lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        if non_empty_lines:
            last_line = non_empty_lines[-1]
            # 行の中に1つだけ数字があるか確認
            digits_in_last = re.findall(r"[0-9]", last_line)
            if len(digits_in_last) == 1:
                digit = int(digits_in_last[0])
                logger.debug(f"パース成功（最終行単一数字パターン）: {digit}")
                return digit

        # ---- 4. テキスト末尾に最も近い1桁数字 ----
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
            "num_predict": 4096,  # 長い思考を許容
            "num_ctx": 8192,      # 思考ログを保存するためのコンテキスト確保
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
            "stream": True,  # ストリーミングを有効にして安定性を向上
            "options": options,
        }

        for attempt in range(max_retries):
            full_text = []
            try:
                # タイムアウトを 1800 秒（30分）に設定
                response = requests.post(self.api_url, json=payload, timeout=1800, stream=True)
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                            if "response" in chunk:
                                full_text.append(chunk["response"])
                            if chunk.get("done"):
                                break
                        except Exception as e:
                            logger.warning(f"チャンクのパースに失敗しました: {e}")
                            continue
                
                raw_response = "".join(full_text)
                parsed_digit = self._parse_digit_from_response(raw_response)
                break
            except Exception as e:
                # 途中まで受信できていれば、それを結果として返す（救済措置）
                if full_text:
                    raw_response = "".join(full_text)
                    parsed_digit = self._parse_digit_from_response(raw_response)
                    logger.warning(f"推論の途中で接続エラーが発生しましたが，受信済みの内容で継続します: {e}")
                    break

                raw_response = f"ERROR: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(1)

        return raw_response, parsed_digit
