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
        use_code       : bool = False,
        sgm            : list[int] = None,
        stage          : int = 1,
        k_disclosed    : int = 0
    ) -> str:
        """
        Few-shot 例題とテスト問題を組み合わせたテキストプロンプトを構築する．
        """
        from core.generator import ComputablePasswordGenerator

        # ---- (1) タスク説明 ----
        prompt = self._SYSTEM_INSTRUCTION
        
        # アルゴリズムルールの説明 (Stage 2, Stage 3)
        if stage in [2, 3]:
            prompt += "【アルゴリズムの計算ルール】\n"
            if generator_name == "simple_add":
                prompt += "ルール：Z = (X0 + X1 + X2) mod 10\n"
                prompt += "（入力リスト X の最初の3つの要素を合計し、10で割った余りを求めます）\n\n"
            elif generator_name == "func_13":
                prompt += "ルール：\n"
                prompt += "1. 入力リストの各値 X[i] (0 <= i <= 13) は、SGM_TABLE のインデックスに対応する値です（X[i] = SGM_TABLE[入力のi番目の値]）。\n"
                prompt += "2. j = X[10] mod 10 を計算します。\n"
                prompt += "3. Z = (X[j] + X[11] + X[12] + X[13]) mod 10 を計算します。\n\n"
            elif generator_name == "func_31":
                prompt += "ルール：\n"
                prompt += "1. 入力リストの各値 X[i] (0 <= i <= 13) は、SGM_TABLE のインデックスに対応する値です（X[i] = SGM_TABLE[入力のi番目の値]）。\n"
                prompt += "2. j = (X[10] + X[11] + X[12]) mod 10 を計算します。\n"
                prompt += "3. Z = (X[j] + X[13]) mod 10 を計算します。\n\n"
            elif generator_name == "func_pow":
                prompt += "ルール：\n"
                prompt += "1. 入力リストの各値 X[i] (0 <= i <= 13) は、SGM_TABLE のインデックスに対応する値です（X[i] = SGM_TABLE[入力のi番目の値]）。\n"
                prompt += "2. Z = (1 * X[10]^4 + 2 * X[11]^3 + 3 * X[12]^2 + 4 * X[13]^1) mod 10 を計算します。\n\n"
            else:
                prompt += "（このアルゴリズムのルール説明は定義されていません）\n\n"

        # 秘密の鍵テーブル（sgm）の公開制御
        if sgm is not None:
            if stage == 1:
                # Stage 1: 完全公開
                prompt += "【秘密の鍵テーブル】\n"
                prompt += f"SGM_TABLE = {sgm}\n"
                prompt += "このテーブルは，入力の各値（インデックス）を実際の計算用数値に変換するために使用されます．\n"
                prompt += "例: 入力が 5 の場合，実際の計算には SGM_TABLE[5] の値を使用してください．\n\n"
            elif stage == 3:
                # Stage 3: 部分公開
                disclosed = sgm[:k_disclosed]
                masked = disclosed + ["?"] * (len(sgm) - k_disclosed)
                prompt += "【秘密の鍵テーブル（部分公開）】\n"
                prompt += f"SGM_TABLE = {masked}\n"
                prompt += f"テーブルの最初の {k_disclosed} 要素のみが公開されています。残りの要素は \"?\" で表されており、未知です。\n"
                prompt += "公開されているインデックスに対しては SGM_TABLE[idx] の値を使用して計算できますが、未知のインデックスについては入出力関係から逆推定する必要があります。\n\n"
            # Stage 0, 2 の場合は秘密鍵テーブルをプロンプトに含めない

        # ---- (2) 観察データ（Few-shot 例題）の列挙 ----
        prompt += self._EXAMPLES_HEADER
        for _, row in shot_df.iterrows():
            challenge_vals = [int(row[f"X{i}"]) for i in range(14)]
            response_val   = int(row["Z"])
            prompt += f"Input: {challenge_vals} | Output: Z = {response_val}\n"
            
            if include_rationale and generator_name != "unknown":
                visible_sgm = sgm if stage in [1, 3] else None
                if generator_name == "simple_add" or visible_sgm is not None:
                    rationale = ComputablePasswordGenerator.explain_logic(generator_name, row, sgm=visible_sgm)
                    prompt += f"Reasoning:\n{rationale}\n\n"

        # ---- (3) テスト問題 ----
        prompt += self._QUESTION_HEADER
        if use_code:
            prompt += self._CODE_INSTRUCTION.format(challenge=test_challenge)
        else:
            prompt += self._ANSWER_INSTRUCTION.format(challenge=test_challenge)

        return prompt


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
