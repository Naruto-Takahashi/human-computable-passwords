# =============================================================================
# data_generator.py
# =============================================================================
# 人間計算可能なパスワード（HCP）の（チャレンジ, レスポンス）ペアを生成し，
# Few-shot用サンプルとテスト用データに分割するモジュール．
#
# 依存: computable_password_generator.ComputablePasswordGenerator
# =============================================================================

import os
import sys
from typing import Tuple, Optional

import numpy as np
import pandas as pd

# src/ をパスに追加し，hcp パッケージをインポートできるようにする
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

from core.generator import ComputablePasswordGenerator

# =============================================================================
# ジェネレータ名 → ジェネレータ関数のマッピング
# 新たなジェネレータを追加する際は，このdictにエントリーを追加するだけでよい
# =============================================================================
AVAILABLE_GENERATORS: dict = {
    "simple_add": ComputablePasswordGenerator.password_simple_add,
    "func_13": ComputablePasswordGenerator.func_13,
    "func_31": ComputablePasswordGenerator.func_31,
    "func_pow": ComputablePasswordGenerator.func_pow,
}


def list_available_generators() -> list[str]:
    """
    利用可能なジェネレータ名の一覧を返す．
    コマンドラインの --generator 引数の選択肢として使用される．
    """
    return list(AVAILABLE_GENERATORS.keys())


def generate_dataset(
    generator_name: str,
    n_shot: int,
    n_test: int,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[list[int]]]:
    """
    指定したジェネレータを使用して，Few-shot用データとテスト用データを生成する．
    """
    # ジェネレータ名のバリデーション
    if generator_name not in AVAILABLE_GENERATORS:
        raise ValueError(
            f"未知のジェネレータです: '{generator_name}'．"
            f"使用可能な選択肢: {list_available_generators()}"
        )

    # 乱数シードを固定して再現性を確保する
    np.random.seed(seed)

    generator_func = AVAILABLE_GENERATORS[generator_name]
    total_size = n_shot + n_test

    # 指定サイズのデータを一括生成し，Few-shot用とテスト用に分割する
    all_df, sgm = generator_func(total_size)

    # 行をシャッフルして偏りを排除する
    all_df = all_df.sample(frac=1, random_state=seed).reset_index(drop=True)

    shot_df = all_df.iloc[:n_shot].reset_index(drop=True)
    test_df = all_df.iloc[n_shot:].reset_index(drop=True)

    return shot_df, test_df, sgm


def extract_challenge_and_response(row: pd.Series) -> Tuple[list[int], int]:
    """
    DataFrame の1行から，チャレンジ（14個の整数リスト）とレスポンス（1桁の整数）を抽出する．

    Args:
        row : DataFrame の1行（pd.Series，カラム X0〜X13 と Z を含む）．

    Returns:
        challenge : 14個の整数からなるリスト．
        response  : 1桁の整数（正解ラベル Z）．
    """
    challenge_cols = [f"X{i}" for i in range(14)]
    challenge = [int(row[col]) for col in challenge_cols]
    response = int(row["Z"])
    return challenge, response
