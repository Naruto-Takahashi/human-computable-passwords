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


# 観察データ（プロンプトに出すチャレンジ）を引くときに data_seed へ足すオフセット。
#
# NumPy の SeedSequence は末尾のゼロを落とすため，`default_rng([d, 0])` が
# `default_rng(d)` と同じ系列になる。鍵は `default_rng(key_seed)` で引いているので，
# **key_seed = data_seed = 0 のとき，先頭のチャレンジが鍵そのものと一致する**。
# 2026-09-23 に経路A の最初の疎通テストで発覚した（観察データの1行目に鍵が
# 平文で並んでいた）。学習側には TRAIN_SEED_OFFSET という同じ対策が既にあり，
# 観察側にだけ無かった。
#
# 過去の評価 74 件はすべて n_shot=0（観察データを出していない）ため，
# オフセットを「観察を出すときだけ」掛ければ，過去の結果はビット単位で不変である。
OBSERVATION_SEED_OFFSET = 2_000_000


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

    n_shot > 0 のときは data_seed に OBSERVATION_SEED_OFFSET を足す
    （理由は同定数のコメント）．n_shot = 0 のときは従来どおりで，
    過去の評価結果との互換性を保つ．
    """
    key = generate_key(algorithm, key_seed)
    effective_data_seed = data_seed + (OBSERVATION_SEED_OFFSET if n_shot > 0 else 0)
    rng = np.random.default_rng([effective_data_seed, key_seed])
    challenges = _draw_unique_challenges(algorithm, n_shot + n_test, rng)
    shot_df = challenges_to_df(algorithm, challenges[:n_shot], key)
    test_df = challenges_to_df(algorithm, challenges[n_shot:], key)
    if key is not None and n_shot > 0:
        _assert_key_not_leaked(key, challenges[:n_shot])
    return HCPDataset(
        algorithm=algorithm,
        key=key,
        shot_df=shot_df,
        test_df=test_df,
        key_seed=key_seed,
        data_seed=data_seed,
    )


def _assert_key_not_leaked(key: list[int], shots: list[tuple[int, ...]]) -> None:
    """観察データのどこかに鍵が平文で並んでいないかを点検する．

    2026-09-23 の事故（OBSERVATION_SEED_OFFSET のコメント参照）を二度と
    起こさないための歯止め．チャレンジは長さ14，鍵は長さ n なので，
    チャレンジ内の連続する n 要素が鍵と一致していないかを見る．
    """
    n = len(key)
    for shot in shots:
        for i in range(len(shot) - n + 1):
            if list(shot[i:i + n]) == key:
                raise AssertionError(
                    "観察データに鍵が平文で現れています（生成器のシードが衝突しています）。"
                    f"鍵={key} が観察 {list(shot)} の位置 {i} に一致しました。"
                )


def extract_challenge_and_response(row: pd.Series) -> tuple[list[int], int]:
    """DataFrame の1行からチャレンジ（14整数）とレスポンス Z を取り出す．"""
    challenge = [int(row[col]) for col in CHALLENGE_COLUMNS]
    return challenge, int(row["Z"])


def observations_from_df(df: pd.DataFrame) -> list[tuple[list[int], int]]:
    """ソルバー・情報限界推定用に (challenge, Z) のリストへ変換する．"""
    return [extract_challenge_and_response(row) for _, row in df.iterrows()]
