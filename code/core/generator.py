# =============================================================================
# generator.py — 従来ML（CNN 等）ベースライン用のデータ生成アダプタ
# =============================================================================
# アルゴリズムの定義本体は hcp/algorithms.py（単一情報源）へ移動した．
# 本モジュールは train_baseline.py が期待するインターフェース
# （list_generators() → .name / .generator(datasize) を持つオブジェクト列）を
# hcp パッケージへ委譲する薄いアダプタである．
#
# 注意: 旧実装では list_generators() が空リストを返しており，
# train_baseline.py のループは一度も実行されない死にコードになっていた．
# 本アダプタで全アルゴリズムが列挙されるようになった．
# =============================================================================

import os
import sys
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hcp.algorithms import ALGORITHMS, Algorithm
from hcp.dataset import COLUMNS


@dataclass
class GeneratorEntry:
    name: str
    generator: Callable[[int], pd.DataFrame]


def _make_generator(algorithm: Algorithm) -> Callable[[int], pd.DataFrame]:
    def generate(datasize: int, seed: int = 42) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        key = (
            rng.integers(0, 10, algorithm.key_size).tolist()
            if algorithm.key_size
            else None
        )
        challenges = rng.integers(
            0, algorithm.challenge_domain(), (datasize, algorithm.challenge_len)
        )
        rows = [
            list(ch) + [algorithm.compute([int(v) for v in ch], key)] for ch in challenges
        ]
        return pd.DataFrame(rows, columns=COLUMNS)

    return generate


class ComputablePasswordGenerator:
    """後方互換のための名前空間（実体は hcp.algorithms）．"""

    COLUMNS = COLUMNS

    @staticmethod
    def list_generators() -> list[GeneratorEntry]:
        return [
            GeneratorEntry(name=a.name, generator=_make_generator(a))
            for a in ALGORITHMS.values()
        ]
