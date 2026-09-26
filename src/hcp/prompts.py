# =============================================================================
# prompts.py — プロンプト構築
# =============================================================================
# 3種類のタスクに対応する:
#   - predict (paradigm=pure) : テストチャレンジ1件の Z を JSON で回答させる
#   - predict (paradigm=pot)  : Z を計算する Python 関数を書かせ，ローカルで実行する
#   - recover_key             : 観察データ全体から秘密鍵テーブルを丸ごと逆推定させ，
#                               JSON で出力させる（鍵復元率の直接測定．1回の推論で済む）
#
# Stage（情報開示レベル）:
#   0: ペアデータのみ / 1: 鍵開示・ルール非開示 / 2: ルール開示・鍵非開示 /
#   3: ルール開示・鍵先頭 K 要素開示
#
# ルール説明文は Algorithm.rule_text（単一情報源）から取得する．
# =============================================================================

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd

from .algorithms import Algorithm
from .dataset import extract_challenge_and_response

# recover_key 用の冒頭。**predict 用の文面を使い回してはいけない。**
# 2026-09-26 まで「新しい入力に対する出力を予測する専門家です」と書いたまま
# 鍵の復元をさせていた。冒頭で別の仕事を宣言してから末尾で復元を求める形になる。
RECOVER_SYSTEM_INSTRUCTION = (
    "あなたは入出力ペアを観察し，その背後にある秘密のテーブルを逆推定する専門家です．\n"
    "計算のルール自体は与えられます．あなたの仕事は，ルールに現れる秘密のテーブルの\n"
    "中身を，観察データと矛盾しないように決定することです．\n"
    "注意深く推論し，思考過程を述べた後，必ず最後に回答を提示してください．\n\n"
)

SYSTEM_INSTRUCTION = (
    "あなたは入出力ペアを観察し，隠れたルールを特定して新しい入力に対する出力を予測する専門家です．\n"
    "提示されるデータには，シンプルかつ論理的な算術ルールが存在します．\n"
    "入力は14個の整数（C[0]〜C[13]），出力は0から9の整数1桁（Z）です．\n"
    "注意深く観察し，思考過程を述べた後，必ず最後に回答を提示してください．\n\n"
)

# 重み格納型（CNN類比）の学習・評価用: Few-shot例なし（n_shot=0）のときに使う最小指示．
# 「例からの読み取り」ではなく X→Z の直接写像だけを要求し，CNN と情報条件を揃える．
MINIMAL_INSTRUCTION = (
    "入力は14個の整数（C[0]〜C[13]），出力は0から9の整数1桁（Z）です．\n"
    "与えられた Input に対する Z を回答してください．\n\n"
)

_MINIMAL_ANSWER_INSTRUCTION = (
    "Input: {challenge}\n"
    "必ず以下のJSON形式でのみ回答を出力してください：\n"
    "{{\n"
    "  \"answer\": <0〜9の整数1桁>\n"
    "}}\n"
)

_ANSWER_INSTRUCTION = (
    "Input: {challenge}\n"
    "思考過程を記述した後，必ず最後に以下のJSON形式でのみ回答を出力してください：\n"
    "{{\n"
    "  \"answer\": <0〜9の整数1桁>\n"
    "}}\n"
)

_CODE_INSTRUCTION = (
    "Input: {challenge}\n"
    "この入出力データの法則に従い，新しい Input に対する Z を計算する Python 関数"
    " `predict_z(X)` を作成してください．\n"
    "X は 14 個の整数のリストです．\n"
    "思考過程を述べた後，必ず最後に ```python ... ``` ブロックで関数を定義してください．\n"
)

_RECOVER_KEY_INSTRUCTION = (
    "上記の観察データ（と与えられた情報）に整合する秘密の鍵テーブル SGM_TABLE を逆推定してください．\n"
    "SGM_TABLE は長さ {key_size} の整数リストで，各要素は 0〜9 です．\n"
    "思考過程を記述した後，必ず最後に以下のJSON形式でのみ回答を出力してください：\n"
    "{{\n"
    "  \"sgm_table\": [<0〜9の整数を{key_size}個>]\n"
    "}}\n"
    "確信が持てない要素についても，最も整合的と考えられる値を必ず埋めてください．\n"
)


def _rule_section(algorithm: Algorithm) -> str:
    return "【アルゴリズムの計算ルール】\n" + algorithm.rule_text + "\n"


def _key_section(key: Sequence[int], stage: int, k_disclosed: int) -> str:
    if stage == 1:
        return (
            "【秘密の鍵テーブル】\n"
            f"SGM_TABLE = {list(key)}\n"
            "このテーブルは，入力の各値（インデックス）を実際の計算用数値に変換するために使用されます．\n"
            "例: 入力が 5 の場合，実際の計算には SGM_TABLE[5] の値を使用してください．\n\n"
        )
    if stage == 3:
        # Python の repr だと '?' とクォートが付いて文字列リテラルに見えるため
        # 手で組み立てる（2026-09-26）。説明文の引用符とも表記を揃える。
        masked = ", ".join([str(v) for v in key[:k_disclosed]]
                           + ["?"] * (len(key) - k_disclosed))
        return (
            "【秘密の鍵テーブル（部分公開）】\n"
            f"SGM_TABLE = [{masked}]\n"
            f"テーブルの最初の {k_disclosed} 要素のみが公開されています。"
            "残りの要素は ? で表されており、未知です。\n"
            "公開されているインデックスに対しては SGM_TABLE[idx] の値を使用して計算できますが、"
            "未知のインデックスについては入出力関係から逆推定する必要があります。\n\n"
        )
    return ""


# 記法の曖昧さを実例で潰すためのダミー鍵（円周率の数字を並べたもの）。
# 本物の鍵と一致しないことを呼び出し側で必ず確認する。
_EXAMPLE_KEY_DIGITS = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3,
                       2, 3, 8, 4, 6, 2, 6, 4, 3, 3]


def _notation_example_section(
    algorithm: Algorithm, key: Optional[Sequence[int]]
) -> str:
    """ルール文の記法を，実装から生成した実例1つで確定させる（recover_key 専用）．

    **なぜ必要か（2026-09-26）**: ルール文の記法が関数間で逆になっている。

    | 関数 | 書き方 | `X0` / `X[i]` の意味 |
    |---|---|---|
    | `table_add3` | `Z = (SGM_TABLE[X0] + ...) mod 10` | 入力の値そのもの（表の添字） |
    | `narrowptr` / `func_*` | `X[i] = SGM_TABLE[入力のi番目の値]` | 変換後の値 |

    さらに `narrowptr` の第1項は「SGM_TABLE のインデックスに**対応する値**です
    （X[i] = SGM_TABLE[入力のi番目の値]）」と，散文と括弧内で意味が食い違う。
    qwen3.5:9b は出力の大半をこの解釈に費やし「この記述は矛盾しています」と述べた。

    ルール文そのものは `algorithms.py` にあり，過去82件の学習結果と紐づくため
    変更できない（CLAUDE.md）。そこで**文章で言い換えるのではなく**，
    `fn` / `explain` から生成した計算例を1つ添える。実装から作るので定義上正しい。

    鍵は本物とは別のダミーなので，観測を1件増やすことにはならない。
    """
    n = algorithm.key_size
    if n == 0:
        return ""
    dummy = [_EXAMPLE_KEY_DIGITS[i % len(_EXAMPLE_KEY_DIGITS)] for i in range(n)]
    if key is not None and list(key) == dummy:
        # 万一一致したら例が本物の観測になってしまうので崩す
        dummy = [(v + 1) % 10 for v in dummy]
    domain = algorithm.challenge_domain()
    challenge = [(i * 3 + 1) % domain for i in range(algorithm.challenge_len)]
    z = algorithm.fn(challenge, dummy)
    return (
        "\n【記法の確認（ここだけの練習用の例です．この鍵は本物ではありません）】\n"
        f"練習用に SGM_TABLE = {dummy} だとしてみます（**本物の鍵とは無関係です**）．\n"
        f"入力 C = {challenge} のとき，上のルールは次のように適用され Z = {z} になります．\n"
        f"{algorithm.explain(challenge, dummy, z)}\n"
        # 実例はルールの直後・鍵の公開より前に置くので，「以下の観察データ」と
        # 書いてはいけない（次に来るのは鍵の公開である）。
        "この対応関係と同じ読み方をしてください．観察データの Input が C にあたります．\n"
        "**練習用の鍵はここで忘れてください。以降の SGM_TABLE は本物です．**\n\n"
    )


# 解き方の指示を段階的に与える水準（2026-09-26 追加）。
#
# **プロンプトは明示的な独立変数として扱う。**調整して成績が上がるまで直すと，
# 測っているのはモデルではなくプロンプトの書き手になる（経路Bで学習予算が
# 隠れた変数だったのと同型）。水準を先に決めて全部報告する。
#
# 水準 A は現行と**バイト単位で同一**に保つこと（過去との比較のため）。
#
# 水準 B の狙い: 2026-09-26 の試走で，モデルは16件中2件だけ検算して
# 「すべてのデータに整合する唯一の解」と述べ，実際の整合率は 4/16 だった。
# 失敗は「探索を早く止めた」ではなく「確認せずに確信した」である。
# 効いたかどうかは shot_consistency で直接測れる。
#
# 水準 C の狙い: 鍵空間は 10^n（n=10 で100億）なので総当りは不可能だが，
# 各観測は mod 10 の一次方程式（ポインタ系は j で場合分け）なので
# 系統的に解ける。ソルバーは数千ノードでやっている。
PROMPT_LEVELS = ("A", "B", "C")

_VERIFY_INSTRUCTION = (
    "候補となる SGM_TABLE を作ったら，**提示された観察データすべて**に当てはめて\n"
    "確認してください．1件でも合わなければ，その候補を捨てて考え直してください．\n"
)

_METHOD_INSTRUCTION = (
    "総当りで列挙しようとしないでください（鍵の候補は膨大です）．\n"
    "各観察データは SGM_TABLE の要素についての mod 10 の一次方程式とみなせます．\n"
    "未知の要素が1つに絞れる式から順に確定させ，確定した値を他の式へ代入して\n"
    "いく，という手順で系統的に解いてください．\n"
)


def recover_key_instruction(key_size: int, level: str = "A") -> str:
    """復元課題の指示文を水準つきで組み立てる．"""
    if level not in PROMPT_LEVELS:
        raise ValueError(f"prompt_level は {PROMPT_LEVELS} のいずれかです: {level}")
    text = _RECOVER_KEY_INSTRUCTION.format(key_size=key_size)
    if level in ("B", "C"):
        text += _VERIFY_INSTRUCTION
    if level == "C":
        text += _METHOD_INSTRUCTION
    return text


def _observation_section(
    algorithm: Algorithm,
    shot_df: pd.DataFrame,
    include_rationale: bool,
    key: Optional[Sequence[int]],
    stage: int,
) -> str:
    # CNN同条件比較（Few-shot例なし・入出力の直接対応のみを学習させる条件）では
    # 観察データセクション自体を省略する
    if len(shot_df) == 0:
        return ""
    section = "【観察データ】\n"
    for _, row in shot_df.iterrows():
        challenge, z = extract_challenge_and_response(row)
        section += f"Input: {challenge} | Output: Z = {z}\n"
        if include_rationale:
            # 値つき解説は鍵の値を含むため，鍵が開示されている Stage 1 でのみ許可する．
            # （Stage 3 でも未知セルの値を含み得るためリークになる — 旧実装のバグ）
            if algorithm.key_size == 0:
                section += f"Reasoning:\n{algorithm.explain(challenge, key, z)}\n\n"
            elif stage == 1 and key is not None:
                section += f"Reasoning:\n{algorithm.explain(challenge, key, z)}\n\n"
    return section


def build_prompt(
    algorithm: Algorithm,
    shot_df: pd.DataFrame,
    task: str,
    stage: int,
    k_disclosed: int = 0,
    key: Optional[Sequence[int]] = None,
    test_challenge: Optional[list[int]] = None,
    paradigm: str = "pure",
    include_rationale: bool = False,
    prompt_level: str = "A",
) -> str:
    """
    プロンプトを構築する．

    Args:
        task           : "predict"（1問予測）または "recover_key"（鍵テーブル復元）
        stage          : 0〜3 の情報開示レベル
        paradigm       : predict タスクの回答形式（"pure" = JSON / "pot" = Pythonコード）
        test_challenge : predict タスクのテスト問題（recover_key では不要）
    """
    if task == "recover_key":
        if algorithm.key_size == 0:
            raise ValueError(f"{algorithm.name} は鍵を持たないため recover_key は定義できません")
        if stage not in (2, 3):
            raise ValueError("recover_key はルールが既知の Stage 2/3 でのみ意味を持ちます")
    if task == "predict" and test_challenge is None:
        raise ValueError("predict タスクには test_challenge が必要です")
    if stage == 3 and not (0 <= k_disclosed <= algorithm.key_size):
        raise ValueError(f"k_disclosed は 0〜{algorithm.key_size} の範囲で指定してください")

    # n_shot=0（重み格納型・CNN類比条件）では観察・思考を促さない最小プロンプトにする
    minimal = len(shot_df) == 0 and task == "predict" and paradigm == "pure"

    if minimal:
        prompt = MINIMAL_INSTRUCTION
    elif task == "recover_key":
        prompt = RECOVER_SYSTEM_INSTRUCTION
    else:
        prompt = SYSTEM_INSTRUCTION
    if stage in (2, 3):
        prompt += _rule_section(algorithm)
    if task == "recover_key":
        # **記法の実例は，本物の鍵の公開より前に置くこと。**
        # 逆にすると「本物の部分公開鍵 → 同じ長さのダミー鍵」と並び，
        # モデルがダミーを本物の続きと取り違える危険がある（2026-09-26）。
        prompt += _notation_example_section(algorithm, key)
    if key is not None:
        prompt += _key_section(key, stage, k_disclosed)
    prompt += _observation_section(algorithm, shot_df, include_rationale, key, stage)

    prompt += "\n【予測課題】\n" if task == "predict" else "\n【復元課題】\n"
    if task == "predict":
        if minimal:
            template = _MINIMAL_ANSWER_INSTRUCTION
        else:
            template = _CODE_INSTRUCTION if paradigm == "pot" else _ANSWER_INSTRUCTION
        prompt += template.format(challenge=test_challenge)
    else:
        prompt += recover_key_instruction(algorithm.key_size, prompt_level)

    return prompt
