# =============================================================================
# prompts.py — プロンプト構築
# =============================================================================
# 3種類のタスクに対応する:
#   - predict (paradigm=pure) : テストチャレンジ1件の Z を JSON で回答させる
#   - predict (paradigm=pot)  : Z を計算する Python 関数を書かせ，ローカルで実行する
#   - recover_key             : 観察データ全体から秘密鍵テーブルを丸ごと逆推定させ，
#                               JSON で出力させる（鍵復元率の直接測定．1回の推論で済む）
#
# Stage（情報開示レベル）:
#   0: ペアデータのみ / 1: 鍵開示・ルール非開示 / 2: ルール開示・鍵非開示 /
#   3: ルール開示・鍵先頭 K 要素開示
#
# ルール説明文は Algorithm.rule_text（単一情報源）から取得する．
# =============================================================================

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd

from .algorithms import Algorithm
from .dataset import extract_challenge_and_response

SYSTEM_INSTRUCTION = (
    "あなたは入出力ペアを観察し，隠れたルールを特定して新しい入力に対する出力を予測する専門家です．\n"
    "提示されるデータには，シンプルかつ論理的な算術ルールが存在します．\n"
    "入力は14個の整数（X0〜X13），出力は0から9の整数1桁（Z）です．\n"
    "注意深く観察し，思考過程を述べた後，必ず最後に回答を提示してください．\n\n"
)

# 重み格納型（CNN類比）の学習・評価用: Few-shot例なし（n_shot=0）のときに使う最小指示．
# 「例からの読み取り」ではなく X→Z の直接写像だけを要求し，CNN と情報条件を揃える．
MINIMAL_INSTRUCTION = (
    "入力は14個の整数（X0〜X13），出力は0から9の整数1桁（Z）です．\n"
    "与えられた Input に対する Z を回答してください．\n\n"
)

_MINIMAL_ANSWER_INSTRUCTION = (
    "Input: {challenge}\n"
    "必ず以下のJSON形式でのみ回答を出力してください：\n"
    "{{\n"
    "  \"answer\": <0〜9の整数1桁>\n"
    "}}\n"
)

_ANSWER_INSTRUCTION = (
    "Input: {challenge}\n"
    "思考過程を記述した後，必ず最後に以下のJSON形式でのみ回答を出力してください：\n"
    "{{\n"
    "  \"answer\": <0〜9の整数1桁>\n"
    "}}\n"
)

_CODE_INSTRUCTION = (
    "Input: {challenge}\n"
    "この入出力データの法則に従い，新しい Input に対する Z を計算する Python 関数"
    " `predict_z(X)` を作成してください．\n"
    "X は 14 個の整数のリストです．\n"
    "思考過程を述べた後，必ず最後に ```python ... ``` ブロックで関数を定義してください．\n"
)

_RECOVER_KEY_INSTRUCTION = (
    "上記の観察データ（と与えられた情報）に整合する秘密の鍵テーブル SGM_TABLE を逆推定してください．\n"
    "SGM_TABLE は長さ {key_size} の整数リストで，各要素は 0〜9 です．\n"
    "思考過程を記述した後，必ず最後に以下のJSON形式でのみ回答を出力してください：\n"
    "{{\n"
    "  \"sgm_table\": [<0〜9の整数を{key_size}個>]\n"
    "}}\n"
    "確信が持てない要素についても，最も整合的と考えられる値を必ず埋めてください．\n"
)


def _rule_section(algorithm: Algorithm) -> str:
    return "【アルゴリズムの計算ルール】\n" + algorithm.rule_text + "\n"


def _key_section(key: Sequence[int], stage: int, k_disclosed: int) -> str:
    if stage == 1:
        return (
            "【秘密の鍵テーブル】\n"
            f"SGM_TABLE = {list(key)}\n"
            "このテーブルは，入力の各値（インデックス）を実際の計算用数値に変換するために使用されます．\n"
            "例: 入力が 5 の場合，実際の計算には SGM_TABLE[5] の値を使用してください．\n\n"
        )
    if stage == 3:
        masked = list(key[:k_disclosed]) + ["?"] * (len(key) - k_disclosed)
        return (
            "【秘密の鍵テーブル（部分公開）】\n"
            f"SGM_TABLE = {masked}\n"
            f"テーブルの最初の {k_disclosed} 要素のみが公開されています。"
            "残りの要素は \"?\" で表されており、未知です。\n"
            "公開されているインデックスに対しては SGM_TABLE[idx] の値を使用して計算できますが、"
            "未知のインデックスについては入出力関係から逆推定する必要があります。\n\n"
        )
    return ""


def _observation_section(
    algorithm: Algorithm,
    shot_df: pd.DataFrame,
    include_rationale: bool,
    key: Optional[Sequence[int]],
    stage: int,
) -> str:
    # CNN同条件比較（Few-shot例なし・入出力の直接対応のみを学習させる条件）では
    # 観察データセクション自体を省略する
    if len(shot_df) == 0:
        return ""
    section = "【観察データ】\n"
    for _, row in shot_df.iterrows():
        challenge, z = extract_challenge_and_response(row)
        section += f"Input: {challenge} | Output: Z = {z}\n"
        if include_rationale:
            # 値つき解説は鍵の値を含むため，鍵が開示されている Stage 1 でのみ許可する．
            # （Stage 3 でも未知セルの値を含み得るためリークになる — 旧実装のバグ）
            if algorithm.key_size == 0:
                section += f"Reasoning:\n{algorithm.explain(challenge, key, z)}\n\n"
            elif stage == 1 and key is not None:
                section += f"Reasoning:\n{algorithm.explain(challenge, key, z)}\n\n"
    return section


def build_prompt(
    algorithm: Algorithm,
    shot_df: pd.DataFrame,
    task: str,
    stage: int,
    k_disclosed: int = 0,
    key: Optional[Sequence[int]] = None,
    test_challenge: Optional[list[int]] = None,
    paradigm: str = "pure",
    include_rationale: bool = False,
) -> str:
    """
    プロンプトを構築する．

    Args:
        task           : "predict"（1問予測）または "recover_key"（鍵テーブル復元）
        stage          : 0〜3 の情報開示レベル
        paradigm       : predict タスクの回答形式（"pure" = JSON / "pot" = Pythonコード）
        test_challenge : predict タスクのテスト問題（recover_key では不要）
    """
    if task == "recover_key":
        if algorithm.key_size == 0:
            raise ValueError(f"{algorithm.name} は鍵を持たないため recover_key は定義できません")
        if stage not in (2, 3):
            raise ValueError("recover_key はルールが既知の Stage 2/3 でのみ意味を持ちます")
    if task == "predict" and test_challenge is None:
        raise ValueError("predict タスクには test_challenge が必要です")
    if stage == 3 and not (0 <= k_disclosed <= algorithm.key_size):
        raise ValueError(f"k_disclosed は 0〜{algorithm.key_size} の範囲で指定してください")

    # n_shot=0（重み格納型・CNN類比条件）では観察・思考を促さない最小プロンプトにする
    minimal = len(shot_df) == 0 and task == "predict" and paradigm == "pure"

    prompt = MINIMAL_INSTRUCTION if minimal else SYSTEM_INSTRUCTION
    if stage in (2, 3):
        prompt += _rule_section(algorithm)
    if key is not None:
        prompt += _key_section(key, stage, k_disclosed)
    prompt += _observation_section(algorithm, shot_df, include_rationale, key, stage)

    prompt += "\n【予測課題】\n" if task == "predict" else "\n【復元課題】\n"
    if task == "predict":
        if minimal:
            template = _MINIMAL_ANSWER_INSTRUCTION
        else:
            template = _CODE_INSTRUCTION if paradigm == "pot" else _ANSWER_INSTRUCTION
        prompt += template.format(challenge=test_challenge)
    else:
        prompt += _RECOVER_KEY_INSTRUCTION.format(key_size=algorithm.key_size)

    return prompt
