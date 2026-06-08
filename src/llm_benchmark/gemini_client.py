# =============================================================================
# gemini_client.py
# =============================================================================
# Google Gemini API を呼び出し，HCPテスト問題の予測結果を取得するモジュール．
#
# 使用SDK: google-genai (最新SDK，google-generativeai の後継)
#   インストール: pip install google-genai
#   参考: https://github.com/googleapis/python-genai
#
# 無料枠のレートリミット対応:
#   Gemini 2.0 Flash の無料枠は 15 RPM（リクエスト/分）．
#   デフォルトで 4 秒/リクエスト のスリープを挟み，安全に動作させる．
# =============================================================================

import os
import re
import time
import logging
from typing import Optional

from google import genai
from google.genai import types


# =============================================================================
# ログ設定
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# GeminiClient クラス
# =============================================================================

class GeminiClient:
    """
    Gemini API への接続・リクエスト・レスポンスパース処理をカプセル化するクライアントクラス．

    設計方針:
        - APIキーを環境変数（GEMINI_API_KEY）から取得し，初期化時に認証する．
        - レートリミット超過を防ぐため，各リクエスト後に sleep_sec 秒の待機を実施する．
        - レスポンスから数字1桁を抽出するパース処理を内包する．
        - 将来的にマルチモーダル（画像入力）への拡張も容易な構造にする．
    """

    def __init__(
        self,
        model_name : str   = "gemini-2.5-flash",
        sleep_sec  : float = 4.0,
        api_key    : Optional[str] = None,
    ):
        """
        GeminiClient を初期化する．

        Args:
            model_name : 使用する Gemini モデルの名前（例: "gemini-2.0-flash"）．
            sleep_sec  : 各 API リクエスト後に挟む待機時間（秒）．
                         無料枠の 15 RPM 制限では 4 秒以上を推奨する．
            api_key    : Gemini API キー．None の場合，環境変数 GEMINI_API_KEY から取得する．

        Raises:
            EnvironmentError: APIキーが環境変数にも引数にも指定されていない場合．
        """
        # ---- API キーの取得と認証 ----
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "Gemini API キーが見つかりません．\n"
                "環境変数 GEMINI_API_KEY を設定するか，api_key 引数に渡してください．\n"
                "例: export GEMINI_API_KEY='AIza...'\n"
                "APIキーの取得: https://aistudio.google.com/app/apikey"
            )

        # ---- google-genai クライアントの初期化 ----
        self.client     = genai.Client(api_key=resolved_key)
        self.model_name = model_name
        self.sleep_sec  = sleep_sec

        # ---- 生成設定: 出力の多様性を抑え，決定論的な回答を促す ----
        # max_output_tokens: gemini-2.5-flash は思考型モデルのため，
        # Chain-of-Thoughtの推論過程を書き終えてから最後に答えを出力する．
        # 2048 では推論途中で打ち切られ「Answer: X」に到達しないため，
        # 8192 に設定して十分な余裕を確保する．
        self._generation_config = types.GenerateContentConfig(
            temperature       = 0.0,   # 出力をできるだけ決定論的にする
            top_p             = 1.0,
            max_output_tokens = 8192,  # 思考型モデル対応: 推論の書き切りを保証
            thinking_config   = types.ThinkingConfig(thinking_budget=1024), # 思考量を制限して途切れを防ぐ
        )

        logger.info(f"GeminiClient 初期化完了: model={self.model_name}, sleep={self.sleep_sec}s")

    def predict(self, prompt: str) -> tuple[str, Optional[int]]:
        """
        テキストプロンプトを Gemini API に送信し，予測値（0〜9の整数）を返す．

        処理フロー:
            1. Gemini API にプロンプトを送信
            2. レートリミット（429）や一時エラー（503）が発生した場合は指示された秒数待機してリトライ
            3. レスポンステキストから「Answer: <数字>」を正規表現で抽出
            4. パースに失敗した場合は None を返す
            5. 正常終了後、レートリミット予防のために sleep_sec 秒待機する

        Args:
            prompt : Gemini API に送信するテキストプロンプト．

        Returns:
            raw_response : API から返ってきた生のテキスト．
            parsed_digit : パースした予測値（0〜9の整数）．パース失敗時は None．
        """
        raw_response: str = ""
        parsed_digit: Optional[int] = None
        max_retries = 10
        base_delay = 5.0

        for attempt in range(max_retries):
            try:
                logger.debug(f"Gemini API にリクエスト送信中... (試行 {attempt + 1}/{max_retries})")
                response = self.client.models.generate_content(
                    model    = self.model_name,
                    contents = prompt,
                    config   = self._generation_config,
                )
                raw_response = response.text
                logger.debug(f"レスポンス受信: {raw_response[:100]}...")

                # パース処理
                parsed_digit = self._parse_digit_from_response(raw_response)
                
                # 正常終了時は標準スリープを挟んでループを抜ける
                time.sleep(self.sleep_sec)
                break

            except Exception as e:
                err_msg = str(e)
                logger.warning(f"API呼び出しエラー (試行 {attempt + 1}/{max_retries}): {err_msg}")
                
                if attempt == max_retries - 1:
                    logger.error("最大リトライ回数に達しました。")
                    raw_response = f"ERROR: {err_msg}"
                    break

                # 待機秒数の解析 (例: Please retry in 47.991206402s のようなパターン)
                wait_match = re.search(r"[Pp]lease retry in ([0-9.]+)\s*s", err_msg)
                if wait_match:
                    sleep_time = float(wait_match.group(1)) + 1.0 # 余裕を持って+1秒
                    logger.info(f"APIからの指示に基づき，{sleep_time:.2f}秒待機して再試行します...")
                else:
                    # 指数バックオフ
                    sleep_time = base_delay * (2 ** attempt)
                    logger.info(f"指数バックオフに基づき，{sleep_time:.2f}秒待機して再試行します...")

                time.sleep(sleep_time)

        return raw_response, parsed_digit

    # -------------------------------------------------------------------------
    # 内部メソッド: レスポンスパース処理
    # -------------------------------------------------------------------------

    def _parse_digit_from_response(self, text: str) -> Optional[int]:
        """
        API レスポンステキストから予測値（0〜9の1桁整数）を抽出する．

        パース優先度（上から順に試みる）:
            1. "Answer: <digit>"  形式（プロンプトで指定した形式）
            2. "答え: <digit>" / "答え：<digit>"  形式（日本語応答）
            3. "Z = <digit>" / "Z=<digit>"  形式（数式表記）
            4. レスポンスの最終行に含まれる唯一の1桁数字
            5. レスポンス全体の末尾に最も近い1桁数字（最終フォールバック）
            ※ 上記すべてに失敗した場合は None を返す

        Args:
            text : Gemini API のレスポンステキスト．

        Returns:
            抽出した 0〜9 の整数，または None（パース失敗時）．
        """
        # Markdown の強調記号（** __ * _）を除去してパースしやすくする
        cleaned = re.sub(r"[*_`]", "", text)

        # ---- パターン 1: "Answer: <digit>" (大文字小文字・空白・コロン全角半角を許容) ----
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
        # 空行を除いた最後の行を取得し，そこに数字が1つだけあれば採用する
        non_empty_lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        if non_empty_lines:
            last_line = non_empty_lines[-1]
            digits_in_last = re.findall(r"[0-9]", last_line)
            if len(digits_in_last) == 1:
                digit = int(digits_in_last[0])
                logger.debug(f"パース成功（最終行単一数字パターン）: {digit}")
                return digit

        # ---- パターン 5: テキスト末尾に最も近い1桁数字（最終フォールバック） ----
        all_digits = re.findall(r"[0-9]", cleaned)
        if all_digits:
            digit = int(all_digits[-1])
            logger.debug(f"パース成功（末尾数字フォールバック）: {digit}")
            return digit

        # ---- パース完全失敗 ----
        logger.warning(f"レスポンスから予測値を抽出できませんでした．Raw: {text[:200]}")
        return None
