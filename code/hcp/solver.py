# =============================================================================
# solver.py — 厳密ソルバー（制約充足による鍵の逆推定）と整合鍵数の数え上げ
# =============================================================================
# 研究上の役割（plan_v2 の3本の基準線のうち2本を担う）:
#   1. 情報理論的限界 N*_info の特定:
#      観察データ N 件に整合する鍵候補の個数を厳密に数え上げ，
#      候補が1個に絞られる N（一意特定の臨界点）を求める．
#   2. 計算機的可解性の実証:
#      「ルール既知なら古典的探索で鍵は復元できる」ことを示す統制条件．
#      LLM の失敗が情報不足でも計算不能性でもなく推論の失敗であることを保証する．
#
# 実装: 動的変数順序つき深さ優先探索．
#   - Algorithm.fn は必要な鍵セルしか参照せず，未知セルに触れると KeyUnknown を
#     送出する．これを利用して各観測の「いまブロックしているセル（first-unknown）」
#     を追跡し，最も多くの観測をブロックしているセルから割り当てる．
#     これにより観測が最短手数で評価可能になり，矛盾枝が浅い段階で刈られる．
#   - 全観測が満たされた時点で未割当のセルは（この分枝では）どの値でも整合する
#     ため，解数には 10^(未割当セル数) を加算する．
#   - 解の個数（solution_cap）・探索ノード数（node_budget）に上限を設け，
#     情報不足で解が爆発する領域では下限値として報告する．
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Union

from .algorithms import Algorithm, KeyUnknown, PartialKey

Observation = tuple[Sequence[int], int]  # (challenge, Z)


@dataclass
class SolverResult:
    """数え上げ／探索の結果．"""

    solution_count: int          # 見つかった整合鍵の個数（capped の場合は下限値）
    capped: bool                 # 解数またはノード数の上限に達したか
    nodes_expanded: int          # 展開した探索ノード数
    solutions: list[list[int]]   # 整合鍵の実例（最大 max_solutions_kept 件．
                                 #   探索中に制約されなかったセルは 0 で埋める）


def count_consistent_keys(
    algorithm: Algorithm,
    observations: list[Observation],
    known_cells: Optional[dict[int, int]] = None,
    solution_cap: int = 1_000_000,
    node_budget: int = 20_000_000,
    max_solutions_kept: int = 5,
) -> SolverResult:
    """
    観察データに整合する鍵テーブルを数え上げる．

    Args:
        known_cells  : 事前開示されたセル {index: value}（Stage 3 の K 開示に対応）
        solution_cap : この解数に達したら打ち切る（情報不足領域での爆発対策）
        node_budget  : 展開ノード数の上限
    """
    if algorithm.key_size == 0:
        raise ValueError(f"{algorithm.name} は鍵を持たないためソルバーの対象外です")

    known_cells = known_cells or {}
    values: list[Optional[int]] = [None] * algorithm.key_size
    for idx, val in known_cells.items():
        values[idx] = val
    key = PartialKey(values)

    result = SolverResult(solution_count=0, capped=False, nodes_expanded=0, solutions=[])

    def probe(oi: int) -> tuple[str, Union[bool, int]]:
        """観測 oi を現在の部分割当で評価する．
        ("done", 整合か) または ("blocked", ブロックしているセル) を返す．"""
        challenge, z = observations[oi]
        try:
            return "done", algorithm.compute(challenge, key) == z
        except KeyUnknown as e:
            return "blocked", e.index

    # 初期状態: 開示セルのみで評価可能な観測を先に処理する
    pending: set[int] = set()
    first_unknown: dict[int, int] = {}
    for oi in range(len(observations)):
        state, val = probe(oi)
        if state == "done":
            if not val:
                return result  # 開示情報だけで矛盾 → 整合鍵は存在しない
        else:
            pending.add(oi)
            first_unknown[oi] = val

    def record_solution() -> bool:
        """解を記録し，探索を続行するなら True を返す．"""
        free_cells = sum(1 for v in values if v is None)
        result.solution_count += 10 ** free_cells
        if len(result.solutions) < max_solutions_kept:
            result.solutions.append([v if v is not None else 0 for v in values])
        if result.solution_count >= solution_cap:
            result.capped = True
            return False
        return True

    class _CountingKey:
        """未知セルに 0 を仮埋めして評価を最後まで走らせ，参照された未知セルを数える．
        MRV ヒューリスティック（残り未知セル最少の観測から完成させる）のための概算．"""

        def __init__(self):
            self.unknown: set[int] = set()

        def __getitem__(self, i: int) -> int:
            v = values[i]
            if v is None:
                self.unknown.add(i)
                return 0
            return v

    def rem_of(oi: int) -> int:
        ck = _CountingKey()
        algorithm.compute(observations[oi][0], ck)
        return len(ck.unknown)

    def viable_values(oi: int) -> list[int]:
        """
        rem=1 の観測 oi について，残り未知セル（= first_unknown[oi]）に入り得る値を返す．
        値を入れた結果さらに別の未知セルが現れる場合（ポインタセル）は棄却できないため
        viable に含める．
        """
        cell = first_unknown[oi]
        viable = []
        for w in range(10):
            values[cell] = w
            state, res = probe(oi)
            if state == "blocked" or res:
                viable.append(w)
        values[cell] = None
        return viable

    class _Trail:
        """1分岐分の変更記録（巻き戻し用）．"""

        __slots__ = ("cells", "satisfied", "fu_changes")

        def __init__(self):
            self.cells: list[int] = []
            self.satisfied: list[int] = []
            self.fu_changes: list[tuple[int, int]] = []

        def undo(self):
            for oi, old in reversed(self.fu_changes):
                first_unknown[oi] = old
            pending.update(self.satisfied)
            for c in self.cells:
                values[c] = None

    def try_assign(cell: int, v: int, trail: _Trail) -> bool:
        """
        values[cell] = v とし，影響を受ける観測の再評価と rem=1 連鎖の強制割当
        （単位伝播）を行う．変更はすべて trail に記録する．矛盾なら False．
        """
        queue: list[tuple[int, int]] = [(cell, v)]
        while queue:
            c, val = queue.pop()
            if values[c] is not None:
                if values[c] != val:
                    return False
                continue
            values[c] = val
            trail.cells.append(c)
            affected = [oi for oi in pending if first_unknown[oi] == c]
            for oi in affected:
                state, res = probe(oi)
                if state == "done":
                    if not res:
                        return False
                    pending.discard(oi)
                    trail.satisfied.append(oi)
                    continue
                trail.fu_changes.append((oi, first_unknown[oi]))
                first_unknown[oi] = res
                # 残り未知セルが1つなら値の候補を数え，1つに定まれば強制割当
                if rem_of(oi) == 1:
                    viable = viable_values(oi)
                    if not viable:
                        return False
                    if len(viable) == 1:
                        queue.append((first_unknown[oi], viable[0]))
        return True

    def choose_branch() -> tuple[int, list[int]]:
        """
        分岐点: 完成に最も近い pending 観測を選び，
        （先頭ブロッカーのセル, 試すべき値のリスト）を返す．
        """
        best_oi = -1
        best_rem = 10**9
        for oi in pending:
            rem = rem_of(oi)
            if rem < best_rem:
                best_rem = rem
                best_oi = oi
                if rem <= 1:
                    break
        if best_rem == 1:
            return first_unknown[best_oi], viable_values(best_oi)
        return first_unknown[best_oi], list(range(10))

    def dfs() -> bool:
        """探索継続なら True，上限到達で全体打ち切りなら False を返す．"""
        result.nodes_expanded += 1
        if result.nodes_expanded > node_budget:
            result.capped = True
            return False

        if not pending:
            return record_solution()

        cell, candidates = choose_branch()
        keep_going = True
        for v in candidates:
            trail = _Trail()
            ok = try_assign(cell, v, trail)
            if ok:
                keep_going = dfs()
            trail.undo()
            if not keep_going:
                return False
        return True

    dfs()
    return result


def solve_key(
    algorithm: Algorithm,
    observations: list[Observation],
    known_cells: Optional[dict[int, int]] = None,
    node_budget: int = 20_000_000,
) -> Optional[list[int]]:
    """
    整合する鍵を1つ復元して返す（ソルバー基準線の「解答」）．
    見つからない／予算超過の場合は None．
    観測に現れないセルは制約されないため 0 で埋められる点に注意．
    """
    result = count_consistent_keys(
        algorithm,
        observations,
        known_cells=known_cells,
        solution_cap=1,
        node_budget=node_budget,
        max_solutions_kept=1,
    )
    return result.solutions[0] if result.solutions else None
