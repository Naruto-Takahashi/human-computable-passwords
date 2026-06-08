# =============================================================================
# ollama_client.py
# =============================================================================
# ローカルで実行中の Ollama API を呼び出し，HCPテスト問題の予測結果を取得するモジュール．
#
# 既存の gemini_client.py を汚さず，同じインターフェースを持つ独立したクライアントとして定義する．
# ローカル実行であるため，APIキーやインターネット接続は不要．またレートリミット（429）の
# リトライ処理も基本的には不要だが，接続エラー時の再試行を念のため備える．
# =============================================================================

import re
import time
import logging
from typing import Optional
import requests

# ログ設定
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    ローカル Ollama API への接続・リクエスト・レスポンスパース処理をカプセル化するクライアントクラス．

    設計方針:
        - GeminiClient と同一の `predict` メソッドを提供し，runnerからシームレスに差し替え可能にする．
        - ローカルホストの Ollama エンドポイント（デフォルト: http://localhost:11434）を叩く．
        - 安定した再現性を得るため，生成パラメータ（temperature=0.0）を設定する．
    """

    def __init__(
        self,
        model_name : str = "qwen2.5:3b",
        api_url    : str = "http://localhost:11434/api/generate",
    ):
        """
        OllamaClient を初期化する．

        Args:
            model_name : 使用する Ollama モデルの名前（例: "qwen2.5:3b", "gemma2:2b"）．
            api_url    : Ollama の generate API エンドポイント URL．
        """
        self.model_name = model_name
        self.api_url    = api_url

        # 生成設定: 決定論的で再現性の高い回答を得るためのオプション
        self._options = {
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 42,
        }

        logger.info(f"OllamaClient 初期化完了: model={self.model_name}, endpoint={self.api_url}")

    def predict(self, prompt: str) -> tuple[str, Optional[int]]:
        """
        テキストプロンプトを Ollama API に送信し，予測値（0〜9の整数）を返す．

        Args:
            prompt : Ollama に送信するテキストプロンプト．

        Returns:
            raw_response : モデルから返ってきた生のテキスト．
            parsed_digit : パースした予測値（0〜9の整数）．パース失敗時は None．
        """
        raw_response: str = ""
        parsed_digit: Optional[int] = None
        max_retries = 3

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": self._options,
        }

        for attempt in range(max_retries):
            try:
                logger.debug(f"Ollama API にリクエスト送信中... (モデル: {self.model_name})")
                response = requests.post(self.api_url, json=payload, timeout=300)
                response.raise_for_status()
                
                result_json = response.json()
                raw_response = result_json.get("response", "")
                
                # レスポンスのパース
                parsed_digit = self._parse_digit_from_response(raw_response)
                break

            except Exception as e:
                logger.warning(f"Ollama API 呼び出しエラー (試行 {attempt + 1}/{max_retries}): {e}")
                raw_response = f"ERROR: {str(e)}"
                if attempt < max_retries - 1:
                    time.sleep(1)

        return raw_response, parsed_digit

    def _parse_digit_from_response(self, text: str) -> Optional[int]:
        """
        GeminiClient と同等のロジックで，テキストから予測値をパースする．
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
