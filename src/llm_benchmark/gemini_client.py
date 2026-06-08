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
        self._generation_config = types.GenerateContentConfig(
            temperature       = 0.0,   # 出力をできるだけ決定論的にする
            top_p             = 1.0,
            max_output_tokens = 2048,  # 推論ステップを含めるため余裕を持たせる
        )

        logger.info(f"GeminiClient 初期化完了: model={self.model_name}, sleep={self.sleep_sec}s")

    def predict(self, prompt: str) -> tuple[str, Optional[int]]:
        """
        テキストプロンプトを Gemini API に送信し，予測値（0〜9の整数）を返す．

        処理フロー:
            1. Gemini API にプロンプトを送信
            2. レスポンステキストから「Answer: <数字>」を正規表現で抽出
            3. パースに失敗した場合は None を返す
            4. レートリミット対応のために sleep_sec 秒待機する

        Args:
            prompt : Gemini API に送信するテキストプロンプト．

        Returns:
            raw_response : API から返ってきた生のテキスト．
            parsed_digit : パースした予測値（0〜9の整数）．パース失敗時は None．
        """
        raw_response: str = ""
        parsed_digit: Optional[int] = None

        try:
            # ---- API 呼び出し ----
            logger.debug("Gemini API にリクエスト送信中...")
            response = self.client.models.generate_content(
                model    = self.model_name,
                contents = prompt,
                config   = self._generation_config,
            )
            raw_response = response.text
            logger.debug(f"レスポンス受信: {raw_response[:100]}...")

            # ---- レスポンスのパース ----
            parsed_digit = self._parse_digit_from_response(raw_response)

        except Exception as e:
            # API エラー（レートリミット超過，ネットワークエラー等）をログに記録
            logger.error(f"Gemini API 呼び出しエラー: {e}")
            raw_response = f"ERROR: {str(e)}"

        finally:
            # ---- レートリミット対応: 必ず待機する ----
            logger.debug(f"レートリミット対応: {self.sleep_sec}秒待機...")
            time.sleep(self.sleep_sec)

        return raw_response, parsed_digit

    # -------------------------------------------------------------------------
    # 内部メソッド: レスポンスパース処理
    # -------------------------------------------------------------------------

    def _parse_digit_from_response(self, text: str) -> Optional[int]:
        """
        API レスポンステキストから「Answer: <数字>」形式の予測値を抽出する．

        パース優先度:
            1. 「Answer: <0〜9>」形式（プロンプトで指定した形式）
            2. 「Z = <0〜9>」形式（数式表記のフォールバック）
            3. 上記いずれも見つからない場合は None を返す

        Args:
            text : Gemini API のレスポンステキスト．

        Returns:
            抽出した 0〜9 の整数，または None（パース失敗時）．
        """
        # ---- パターン 1: "Answer: <digit>" ----
        match = re.search(r"Answer\s*:\s*([0-9])", text, re.IGNORECASE)
        if match:
            digit = int(match.group(1))
            logger.debug(f"パース成功（Answer:パターン）: {digit}")
            return digit

        # ---- パターン 2: "Z = <digit>" または "Z=<digit>"（行末） ----
        match = re.search(r"Z\s*=\s*([0-9])\s*$", text, re.MULTILINE)
        if match:
            digit = int(match.group(1))
            logger.debug(f"パース成功（Z=パターン）: {digit}")
            return digit

        # ---- パース失敗 ----
        logger.warning(f"レスポンスから予測値を抽出できませんでした．Raw: {text[:200]}")
        return None
