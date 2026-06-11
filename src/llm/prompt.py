# =============================================================================
# prompt_builder.py
# =============================================================================
# Gemini API に渡すテキストプロンプトを構築するモジュール．
#
# 設計方針:
#   - PromptBuilder 基底クラスを定義し，テキスト/画像など異なる入力モードへの
#     拡張を容易にするポリモーフィックな設計を採用する．
#   - 現在は TextPromptBuilder（テキストのみ）を実装する．
#   - 将来的に ImagePromptBuilder（マルチモーダル入力）を同じ基底クラスから派生させることができる．
# =============================================================================

from abc import ABC, abstractmethod
import pandas as pd


# =============================================================================
# 基底クラス: PromptBuilder
# =============================================================================

class PromptBuilder(ABC):
    """
    プロンプト構築の基底クラス．
    テキスト入力・画像入力など，入力モードの違いを吸収するための抽象インターフェース．
    サブクラスで build_fewshot_prompt() と build_test_query() を実装すること．
    """

    @abstractmethod
    def build_fewshot_prompt(
        self,
        shot_df        : pd.DataFrame,
        test_challenge : list[int],
    ) -> str | list:
        """
        Few-shot 例題とテスト問題を組み合わせたプロンプトを構築する．

        Args:
            shot_df        : Few-shot例題のDataFrame（カラム: X0〜X13, Z）．
            test_challenge : テスト問題のチャレンジ（14個の整数リスト）．

        Returns:
            Gemini API に渡す入力（テキストプロンプト文字列 or コンテンツリスト）．
        """
        pass


# =============================================================================
# テキスト入力モード: TextPromptBuilder
# =============================================================================

class TextPromptBuilder(PromptBuilder):
    """
    テキストのみを使用してプロンプトを構築するクラス．
    LLMに対し，「入力と出力のペアを観察して，変換ルールを自分で推論し，
    新しい入力に対する出力を予測する」というFew-shot推論タスクを課す．
    """

    # -------------------------------------------------------------------------
    # プロンプトのテンプレート文字列（クラス定数として定義）
    # -------------------------------------------------------------------------

    # タスク説明部分: LLMへの役割・目標の指示
    _SYSTEM_INSTRUCTION: str = (
        "あなたは入出力ペアを観察し，隠れたルールを特定して新しい入力に対する出力を予測する専門家です．\n"
        "提示されるデータには，シンプルかつ論理的な算術ルールが存在します．\n"
        "入力は14個の整数（X0〜X13），出力は0から9の整数1桁（Z）です．\n"
        "注意深く観察し，思考過程を述べた後，必ず最後に回答を提示してください．\n\n"
    )

    # Few-shot 例題セクションのヘッダー
    _EXAMPLES_HEADER: str = "【観察データ】\n"

    # テスト問題セクション
    _QUESTION_HEADER: str = "\n【予測課題】\n"
    _ANSWER_INSTRUCTION: str = (
        "Input: {challenge}\n"
        "思考過程を記述した後，必ず最後に以下のJSON形式でのみ回答を出力してください：\n"
        "{{\n"
        "  \"answer\": <0〜9の整数1桁>\n"
        "}}\n"
    )

    # コード出力指示セクション
    _CODE_INSTRUCTION: str = (
        "Input: {challenge}\n"
        "この入出力データの法則に従い，新しい Input に対する Z を計算する Python 関数 `predict_z(X)` を作成してください．\n"
        "X は 14 個の整数のリストです．\n"
        "思考過程を述べた後，必ず最後に ```python ... ``` ブロックで関数を定義してください．\n"
    )

    def build_fewshot_prompt(
        self,
        shot_df        : pd.DataFrame,
        test_challenge : list[int],
        generator_name : str = "unknown",
        include_rationale: bool = False,
        use_code       : bool = False
    ) -> str:
        """
        Few-shot 例題とテスト問題を組み合わせたテキストプロンプトを構築する．
        """
        from hcp.generator import ComputablePasswordGenerator

        # ---- (1) タスク説明 ----
        prompt_parts = [self._SYSTEM_INSTRUCTION]

        # ---- (2) 観察データ（Few-shot 例題）の列挙 ----
        prompt_parts.append(self._EXAMPLES_HEADER)
        for _, row in shot_df.iterrows():
            challenge_vals = [int(row[f"X{i}"]) for i in range(14)]
            response_val   = int(row["Z"])
            # 少し構造的な形式で記述
            prompt_parts.append(f"Input: {challenge_vals} | Output: Z = {response_val}\n")
            
            if include_rationale and generator_name != "unknown":
                rationale = ComputablePasswordGenerator.explain_logic(generator_name, row)
                prompt_parts.append(f"Reasoning:\n{rationale}\n\n")

        # ---- (3) テスト問題 ----
        prompt_parts.append(self._QUESTION_HEADER)
        if use_code:
            prompt_parts.append(
                self._CODE_INSTRUCTION.format(challenge=test_challenge)
            )
        else:
            prompt_parts.append(
                self._ANSWER_INSTRUCTION.format(challenge=test_challenge)
            )

        return "".join(prompt_parts)


# =============================================================================
# ファクトリ関数: get_prompt_builder()
# =============================================================================

def get_prompt_builder(mode: str = "text") -> PromptBuilder:
    """
    指定されたモードに対応する PromptBuilder インスタンスを返すファクトリ関数．
    新しい入力モード（例: "image"）を追加する際はこの関数にケースを追加する．

    Args:
        mode : 入力モードを示す文字列．現在は "text" のみ対応．

    Returns:
        PromptBuilder のサブクラスインスタンス．

    Raises:
        ValueError: 未知のモードが指定された場合．
    """
    if mode == "text":
        return TextPromptBuilder()
    # 将来の拡張ポイント:
    # elif mode == "image":
    #     return ImagePromptBuilder()
    else:
        raise ValueError(
            f"未知のプロンプトモードです: '{mode}'．"
            f"使用可能な選択肢: ['text']"
        )
