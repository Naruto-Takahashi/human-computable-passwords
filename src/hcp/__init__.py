# =============================================================================
# hcp — Human-Computable Passwords ベンチマークの中核パッケージ
# =============================================================================
# モジュール構成:
#   algorithms  : HCP アルゴリズム定義の単一情報源（計算・ルール文・参照コード・解説）
#   dataset     : 鍵/データシード分離のデータセット生成
#   prompts     : predict / recover_key プロンプト構築（Stage 0〜3）
#   clients     : LLM プロバイダ（Gemini / Ollama / Mock / LoRA）
#   executor    : LLM 出力のパースと生成コードの実行
#   evaluation  : 実験の実行・採点・記録（応答精度・鍵復元率）
#   solver      : 厳密ソルバー（整合鍵の数え上げ = 情報限界，鍵復元 = 計算可解性）
# =============================================================================

from .algorithms import ALGORITHMS, Algorithm, algorithm_names, get_algorithm, verify_all
from .dataset import HCPDataset, extract_challenge_and_response, generate_dataset

__all__ = [
    "ALGORITHMS",
    "Algorithm",
    "algorithm_names",
    "get_algorithm",
    "verify_all",
    "HCPDataset",
    "extract_challenge_and_response",
    "generate_dataset",
]
