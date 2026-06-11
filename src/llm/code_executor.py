import logging
import traceback
from typing import Optional, List

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    LLM が生成した Python コードを抽出し，実行して結果を得るクラス．
    """

    @staticmethod
    def execute_llm_code(code_str: str, input_x: List[int]) -> Optional[int]:
        """
        文字列としての Python コードを実行し，特定の関数を呼び出す．
        
        期待される関数のシグネチャ:
            def predict_z(X: List[int]) -> int:
        """
        try:
            # 実行用のローカル環境を構築
            local_vars = {}
            # exec は慎重に扱う必要があるが，研究用途のローカル環境であることを前提とする
            exec(code_str, {"__builtins__": __builtins__}, local_vars)

            # predict_z または solve という名前の関数を探す
            func = local_vars.get("predict_z") or local_vars.get("solve")
            
            if func and callable(func):
                result = func(input_x)
                # 整数であることを確認し，1桁（mod 10）に収める
                if result is not None:
                    return int(result) % 10
            else:
                logger.warning("実行可能な関数 (predict_z or solve) が見つかりませんでした．")
                
        except Exception as e:
            logger.error(f"コードの実行中にエラーが発生しました: {e}")
            logger.debug(traceback.format_exc())
            
        return None
