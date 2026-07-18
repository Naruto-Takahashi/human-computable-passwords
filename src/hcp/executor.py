# =============================================================================
# executor.py — LLM 出力のパースと生成コードの実行
# =============================================================================
# 旧 llm_agent/code_executor.py + clients.py 内のパース処理を統合．
# パース（回答抽出）は「モデルが明示的に出した回答」だけを拾い，
# 迷い書きの数字を拾わない方針（研究ノイズ防止）を維持する．
# =============================================================================

from __future__ import annotations

import json
import logging
import re
import traceback
from typing import Optional

logger = logging.getLogger(__name__)

_REFUSAL_KEYWORDS = ["unknown", "cannot determine", "不明", "分かりません", "わからない"]

_THINK_RE = re.compile(
    r"<(think|思考過程)>.*?</(think|思考过程|思考過程)>", re.DOTALL | re.IGNORECASE
)


def strip_thinking(text: str) -> str:
    """<think> ブロックを除去する．"""
    return _THINK_RE.sub("", text)


def _find_json_objects(text: str) -> list[dict]:
    """テキスト中の JSON オブジェクトを（コードブロック内も含め）すべて抽出する．"""
    candidates = []
    # ブレース対応で {...} を走査（正規表現の貪欲マッチによる取りこぼしを回避）
    starts = [m.start() for m in re.finditer(r"\{", text)]
    for s in starts:
        depth = 0
        for e in range(s, len(text)):
            if text[e] == "{":
                depth += 1
            elif text[e] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        candidates.append(json.loads(text[s : e + 1]))
                    except (json.JSONDecodeError, ValueError):
                        pass
                    break
    return candidates


def parse_answer_digit(text: str) -> Optional[int]:
    """
    レスポンステキストから予測値（0〜9）を抽出する．
    優先順: JSON {"answer": n} → "Answer:"/"答え:"/"Z =" の明示回答．
    回答拒否ワードがある場合や見つからない場合は None．
    """
    lower = text.lower()
    if any(kw in lower for kw in _REFUSAL_KEYWORDS):
        return None

    for obj in reversed(_find_json_objects(text)):
        if "answer" in obj:
            val = obj["answer"]
            if isinstance(val, (int, float)):
                return int(val) % 10
            if isinstance(val, str) and val.isdigit():
                return int(val) % 10

    main = strip_thinking(text)
    main = re.sub(r"[*_`]", "", main)
    for pattern in (
        r"Answer\s*[：:]\s*.*?([0-9])",
        r"答え\s*[：:]\s*.*?([0-9])",
        r"\bZ\s*=\s*([0-9])\b",
    ):
        match = re.search(pattern, main, re.IGNORECASE | re.DOTALL)
        if match:
            return int(match.group(1))
    return None


def parse_key_table(text: str, key_size: int) -> Optional[list[int]]:
    """
    レスポンステキストから鍵テーブル（長さ key_size の 0〜9 整数リスト）を抽出する．
    優先順: JSON {"sgm_table": [...]} → Python コード内の sgm/SGM_TABLE リテラル．
    """
    def _validate(values) -> Optional[list[int]]:
        try:
            table = [int(v) for v in values]
        except (TypeError, ValueError):
            return None
        if len(table) != key_size or not all(0 <= v <= 9 for v in table):
            return None
        return table

    for obj in reversed(_find_json_objects(text)):
        for field in ("sgm_table", "SGM_TABLE", "key", "table"):
            if field in obj:
                table = _validate(obj[field])
                if table is not None:
                    return table

    # フォールバック: sgm = [ ... ] 形式のリテラル
    for match in reversed(
        list(re.finditer(r"(?:sgm|SGM_TABLE)\s*=\s*(\[[^\]]*\])", text, re.IGNORECASE))
    ):
        try:
            table = _validate(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
        if table is not None:
            return table
    return None


def extract_python_block(text: str) -> Optional[str]:
    """最後の ```python ...``` ブロックを抽出する．"""
    matches = re.findall(r"```python\s+(.*?)\s+```", text, re.DOTALL)
    return matches[-1] if matches else None


def execute_predict_code(code_str: str, input_x: list[int]) -> Optional[int]:
    """
    LLM が生成した predict_z(X)（または solve(X)）を実行して結果を得る．
    実行エラー・関数未定義の場合は None．
    """
    try:
        local_vars: dict = {}
        exec(code_str, {"__builtins__": __builtins__}, local_vars)  # noqa: S102
        func = local_vars.get("predict_z") or local_vars.get("solve")
        if callable(func):
            result = func(input_x)
            if result is not None:
                return int(result) % 10
        logger.warning("実行可能な関数 (predict_z or solve) が見つかりませんでした．")
    except Exception as e:
        logger.error(f"コードの実行中にエラーが発生しました: {e}")
        logger.debug(traceback.format_exc())
    return None
