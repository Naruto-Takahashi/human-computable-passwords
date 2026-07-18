# =============================================================================
# dataset.py — HCP データセット生成
# =============================================================================
# 旧実装（llm_agent/data_generator.py）からの主な改善:
#   - np.random.seed() によるグローバル乱数汚染を廃止し，np.random.default_rng を使用
#   - 鍵シード（key_seed）とデータシード（data_seed）を分離．
#     「同じ鍵で異なるチャレンジ集合」「異なる鍵」を独立に制御でき，
#     成功『率』の測定（複数鍵での反復）が正しく行える．
#   - shot と test の間でチャレンジが重複しないことを保証（リーク防止）
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .algorithms import Algorithm

CHALLENGE_COLUMNS = [f"X{i}" for i in range(14)]
COLUMNS = CHALLENGE_COLUMNS + ["Z"]


@dataclass
class HCPDataset:
    """1回の実験で使うデータ一式（鍵・Few-shot例・テスト問題）．"""

    algorithm: Algorithm
    key: Optional[list[int]]
    shot_df: pd.DataFrame
    test_df: pd.DataFrame
    key_seed: int
    data_seed: int


def generate_key(algorithm: Algorithm, key_seed: int) -> Optional[list[int]]:
    """鍵テーブルを生成する（鍵なしアルゴリズムでは None）．"""
    if algorithm.key_size == 0:
        return None
    rng = np.random.default_rng(key_seed)
    return rng.integers(0, 10, algorithm.key_size).tolist()


def _draw_unique_challenges(
    algorithm: Algorithm, n: int, rng: np.random.Generator
) -> list[tuple[int, ...]]:
    """重複しないチャレンジを n 件生成する．"""
    seen: set[tuple[int, ...]] = set()
    out: list[tuple[int, ...]] = []
    domain = algorithm.challenge_domain()
    while len(out) < n:
        ch = tuple(int(v) for v in rng.integers(0, domain, algorithm.challenge_len))
        if ch in seen:
            continue
        seen.add(ch)
        out.append(ch)
    return out


def challenges_to_df(
    algorithm: Algorithm,
    challenges: list[tuple[int, ...]],
    key: Optional[list[int]],
) -> pd.DataFrame:
    rows = [list(ch) + [algorithm.compute(ch, key)] for ch in challenges]
    return pd.DataFrame(rows, columns=COLUMNS)


def generate_dataset(
    algorithm: Algorithm,
    n_shot: int,
    n_test: int,
    key_seed: int = 0,
    data_seed: int = 0,
) -> HCPDataset:
    """
    Few-shot 用（観察データ）とテスト用（採点データ）を生成する．
    両者のチャレンジは互いに素であることを保証する．
    """
    key = generate_key(algorithm, key_seed)
    rng = np.random.default_rng([data_seed, key_seed])
    challenges = _draw_unique_challenges(algorithm, n_shot + n_test, rng)
    shot_df = challenges_to_df(algorithm, challenges[:n_shot], key)
    test_df = challenges_to_df(algorithm, challenges[n_shot:], key)
    return HCPDataset(
        algorithm=algorithm,
        key=key,
        shot_df=shot_df,
        test_df=test_df,
        key_seed=key_seed,
        data_seed=data_seed,
    )


def extract_challenge_and_response(row: pd.Series) -> tuple[list[int], int]:
    """DataFrame の1行からチャレンジ（14整数）とレスポンス Z を取り出す．"""
    challenge = [int(row[col]) for col in CHALLENGE_COLUMNS]
    return challenge, int(row["Z"])


def observations_from_df(df: pd.DataFrame) -> list[tuple[list[int], int]]:
    """ソルバー・情報限界推定用に (challenge, Z) のリストへ変換する．"""
    return [extract_challenge_and_response(row) for _, row in df.iterrows()]
