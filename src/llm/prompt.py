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
        "あなたは入出力ペアを観察し，ルールを推論して新しい入力に対する出力を予測する専門家です．\n"
        "入力は14個の整数（X0〜X13），出力は0から9の整数1桁（Z）です．\n"
        "指示に従い，簡潔な思考過程の後に回答を提示してください．\n\n"
    )

    # Few-shot 例題セクションのヘッダー
    _EXAMPLES_HEADER: str = "【観察データ】\n"

    # テスト問題セクション
    _QUESTION_HEADER: str = "\n【予測課題】\n"
    _ANSWER_INSTRUCTION: str = (
        "入力: {challenge}\n"
        "思考過程を詳しく述べた後，必ず最後に次の形式で回答してください：\n"
        "Answer: <0〜9の整数1桁>\n"
        "Z = "
    )

    def build_fewshot_prompt(
        self,
        shot_df        : pd.DataFrame,
        test_challenge : list[int],
    ) -> str:
        """
        Few-shot 例題とテスト問題を組み合わせたテキストプロンプトを構築する．

        プロンプトの構造:
            1. タスク説明（LLMへの役割・目標の指示）
            2. 観察データ（Few-shot 例題ペアの一覧）
            3. 予測課題（テスト問題のチャレンジ）

        Args:
            shot_df        : Few-shot 例題の DataFrame．
            test_challenge : テスト問題のチャレンジ（14個の整数のリスト）．

        Returns:
            構築されたプロンプト文字列．
        """
        # ---- (1) タスク説明 ----
        prompt_parts = [self._SYSTEM_INSTRUCTION]

        # ---- (2) 観察データ（Few-shot 例題）の列挙 ----
        prompt_parts.append(self._EXAMPLES_HEADER)
        for idx, row in shot_df.iterrows():
            challenge_vals = [int(row[f"X{i}"]) for i in range(14)]
            response_val   = int(row["Z"])
            # 各例題を「入力: [x0, x1, ..., x13] → 出力: Z」形式で表記
            example_line = (
                f"例{idx + 1:03d}: 入力={challenge_vals} → Z={response_val}\n"
            )
            prompt_parts.append(example_line)

        # ---- (3) テスト問題 ----
        prompt_parts.append(self._QUESTION_HEADER)
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
