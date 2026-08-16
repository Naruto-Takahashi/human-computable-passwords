# =============================================================================
# algorithms.py — HCP アルゴリズム定義の単一情報源 (Single Source of Truth)
# =============================================================================
# 旧実装ではアルゴリズムの定義が以下の4箇所に重複しており，PoT教師データへの
# 鍵リーク（weekly_report_20260705.md 参照）のような齟齬の温床になっていた:
#   1. core/generator.py            … 計算本体
#   2. core/generator.explain_logic … 値つき解説
#   3. llm_agent/prompt.py          … ルール説明文（Stage 2/3）
#   4. scripts/train_finetuning.py  … 教師コード・rationale
# 本モジュールは各アルゴリズムを1つの Algorithm インスタンスに集約する．
# compute と reference_code の整合性は verify_all() で機械的に検証できる．
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence


class KeyUnknown(Exception):
    """部分鍵の未知セルにアクセスした際に送出される（ソルバーの部分評価用）．"""

    def __init__(self, index: int):
        super().__init__(f"key cell {index} is unknown")
        self.index = index


class PartialKey:
    """
    一部のセルが未知（None）の鍵テーブル．
    未知セルへのアクセスは KeyUnknown を送出する．
    Algorithm.compute に渡すことで「この観測は現在の部分割当で評価可能か」を
    判定できる（ソルバー・情報限界推定の中核）．
    """

    def __init__(self, values: list[Optional[int]]):
        # 参照を保持する（コピーしない）．ソルバーは元のリストを直接更新しながら
        # 同じ PartialKey で部分評価を繰り返すため，コピーすると更新が見えなくなる．
        self.values = values

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, index: int) -> int:
        v = self.values[index]
        if v is None:
            raise KeyUnknown(index)
        return v


@dataclass(frozen=True)
class Algorithm:
    """
    HCP アルゴリズム1つ分の完全な定義．

    Attributes:
        name           : 識別子（CLI の --algorithm に使用）
        level          : 難易度（1=直接演算, 2=間接参照, 3=非線形）
        key_size       : 秘密鍵テーブルの長さ（0 = 鍵なし）
        challenge_len  : チャレンジの長さ（固定14）
        fn             : (challenge, key) -> Z．key は添字アクセス可能であればよく，
                         PartialKey を渡すと未知セル参照時に KeyUnknown が飛ぶ．
                         必要なセルしか参照しない実装であること（部分評価のため）．
        rule_text      : Stage 2/3 プロンプトに埋め込むルール説明（鍵の値は含まない）
        rationale_text : 鍵の値に触れない構造のみの思考過程テンプレート（FT rationale 用）
        code_body      : 参照実装コードの関数本体（"{key}" プレースホルダに鍵リテラルが入る）．
                         鍵リテラルを埋め込むため，これをLLMの学習ターゲットにしてはならない．
        explain        : (challenge, key, Z) -> 値つき解説文（鍵の値を含む．Stage 1/3 の
                         rationale としてのみ使用可）
    """

    name: str
    level: int
    key_size: int
    fn: Callable[[Sequence[int], Sequence[int]], int]
    rule_text: str
    rationale_text: str
    code_body: str
    explain: Callable[[Sequence[int], Sequence[int], int], str]
    challenge_len: int = 14
    domain: Optional[int] = None  # チャレンジ各要素の値域の明示指定（省略時は key_size か 10）

    # ---- 計算 ----

    def compute(self, challenge: Sequence[int], key: Optional[Sequence[int]] = None) -> int:
        """チャレンジに対する正解レスポンス Z を計算する．"""
        if self.key_size and key is None:
            raise ValueError(f"{self.name} requires a key of size {self.key_size}")
        return self.fn(challenge, key) % 10

    def challenge_domain(self) -> int:
        """チャレンジ各要素の値域（0 〜 domain-1）．"""
        if self.domain is not None:
            return self.domain
        return self.key_size if self.key_size else 10

    # ---- 参照コード ----

    def reference_code(self, key: Optional[Sequence[int]] = None) -> str:
        """
        鍵リテラルを埋め込んだ検証用 Python 実装を返す．
        注意: 鍵を含むため LLM の学習ターゲット・プロンプトに含めてはならない
        （旧 PoT 学習の鍵リーク問題の原因）．採点・自己検証専用．
        """
        key_literal = list(key) if key is not None else None
        return f"def predict_z(X):\n{self.code_body.format(key=key_literal)}"


# =============================================================================
# 各アルゴリズムの定義（1アルゴリズム = 1ブロック）
# =============================================================================

def _fn_simple_add(ch, key):
    return (ch[0] + ch[1] + ch[2]) % 10


def _explain_simple_add(ch, key, z):
    s = ch[0] + ch[1] + ch[2]
    return (
        f"1. 最初の3つの数字を取得: X0={ch[0]}, X1={ch[1]}, X2={ch[2]}\n"
        f"2. 和を計算: {ch[0]} + {ch[1]} + {ch[2]} = {s}\n"
        f"3. 10で割った余りを算出: {s} mod 10 = {z}"
    )


_SIMPLE_ADD = Algorithm(
    name="simple_add",
    level=1,
    key_size=0,
    fn=_fn_simple_add,
    rule_text=(
        "ルール：Z = (X0 + X1 + X2) mod 10\n"
        "（入力リスト X の最初の3つの要素を合計し、10で割った余りを求めます）\n"
    ),
    rationale_text=(
        "考え方:\n"
        "1. 入力 X の X[0], X[1], X[2] を合計する．\n"
        "2. その合計を 10 で割った余りが答えです．\n"
    ),
    code_body="    return (X[0] + X[1] + X[2]) % 10\n",
    explain=_explain_simple_add,
)


# --- secret_add: 学習可能性切り分け用の最小タスク（指導教員レビュー 0707 優先度3） ---
# 鍵はスカラー1個のみ．Z = (X0 + 秘密値) mod 10．
# 「鍵1マスすら教師あり学習で重みに書き込めないのか」を検証する統制条件．

def _fn_secret_add(ch, key):
    return (ch[0] + key[0]) % 10


def _explain_secret_add(ch, key, z):
    return (
        f"1. 最初の数字を取得: X0={ch[0]}\n"
        f"2. 秘密の値を加算: {ch[0]} + {key[0]} = {ch[0] + key[0]}\n"
        f"3. 10で割った余りを算出: {ch[0] + key[0]} mod 10 = {z}"
    )


_SECRET_ADD = Algorithm(
    name="secret_add",
    level=1,
    key_size=1,
    domain=10,
    fn=_fn_secret_add,
    rule_text=(
        "ルール：Z = (X0 + SGM_TABLE[0]) mod 10\n"
        "（入力リスト X の最初の要素に秘密の値 SGM_TABLE[0]（0〜9の整数1個）を加え、"
        "10で割った余りを求めます。X1〜X13 は使用しません）\n"
    ),
    rationale_text=(
        "考え方:\n"
        "1. 入力 X の X[0] に秘密の値を加算する．\n"
        "2. その合計を 10 で割った余りが答えです．\n"
    ),
    code_body=(
        "    sgm = {key}\n"
        "    return (X[0] + sgm[0]) % 10\n"
    ),
    explain=_explain_secret_add,
)


_KEYED_RULE_PREFIX = (
    "1. 入力リストの各値 X[i] (0 <= i <= 13) は、SGM_TABLE のインデックスに対応する値です"
    "（X[i] = SGM_TABLE[入力のi番目の値]）。\n"
)
_KEYED_RATIONALE_PREFIX = (
    "1. 入力 X の各値は秘密の鍵テーブルのインデックスに対応しており，"
    "鍵テーブルを介して実際の計算用の値に変換される．\n"
)
_KEYED_CODE_PREFIX = (
    "    sgm = {key}\n"
    "    X_val = [sgm[i] for i in X]\n"
)


def _fn_func_13(ch, key):
    def x(i):
        return key[ch[i]]
    j = x(10) % 10
    return (x(j) + x(11) + x(12) + x(13)) % 10


def _explain_func_13(ch, key, z):
    X = [key[i] for i in ch]
    j = X[10] % 10
    return (
        f"1. インデックスに対応するテーブル値を参照: X10=sgm[{ch[10]}]={X[10]}\n"
        f"2. ポインタ j = X10 mod 10 = {X[10]} mod 10 = {j} を計算\n"
        f"3. インデックス {j} の値をテーブルから取得: X{j}=sgm[{ch[j]}]={X[j]}\n"
        f"4. Z = (X{j} + X11 + X12 + X13) mod 10 = "
        f"({X[j]} + {X[11]} + {X[12]} + {X[13]}) mod 10 = {z}"
    )


_FUNC_13 = Algorithm(
    name="func_13",
    level=2,
    key_size=100,
    fn=_fn_func_13,
    rule_text=(
        "ルール：\n" + _KEYED_RULE_PREFIX +
        "2. j = X[10] mod 10 を計算します。\n"
        "3. Z = (X[j] + X[11] + X[12] + X[13]) mod 10 を計算します。\n"
    ),
    rationale_text=(
        "考え方:\n" + _KEYED_RATIONALE_PREFIX +
        "2. 変換後の位置10の値を10で割った余りを j とする．\n"
        "3. 変換後の位置 j, 11, 12, 13 の値を合計し，10で割った余りが答えです．\n"
    ),
    code_body=(
        _KEYED_CODE_PREFIX +
        "    j = X_val[10] % 10\n"
        "    return (X_val[j] + X_val[11] + X_val[12] + X_val[13]) % 10\n"
    ),
    explain=_explain_func_13,
)


# key_size=26 版（RQ4: s(f) 軸の比較用）．
# 原論文のデモ例に合わせた既定の func_13（key_size=100）は，func_22/func_31（ともに
# key_size=26）と鍵サイズが揃っておらず，N*_info の差が s(f) 由来か鍵サイズ由来か
# 分離できない．func_22/func_31 と鍵サイズを揃えた比較用にこちらを用いる．
_FUNC_13_K26 = Algorithm(
    name="func_13_k26",
    level=2,
    key_size=26,
    fn=_fn_func_13,
    rule_text=(
        "ルール：\n" + _KEYED_RULE_PREFIX +
        "2. j = X[10] mod 10 を計算します。\n"
        "3. Z = (X[j] + X[11] + X[12] + X[13]) mod 10 を計算します。\n"
    ),
    rationale_text=(
        "考え方:\n" + _KEYED_RATIONALE_PREFIX +
        "2. 変換後の位置10の値を10で割った余りを j とする。\n"
        "3. 変換後の位置 j, 11, 12, 13 の値を合計し，10で割った余りが答えです。\n"
    ),
    code_body=(
        _KEYED_CODE_PREFIX +
        "    j = X_val[10] % 10\n"
        "    return (X_val[j] + X_val[11] + X_val[12] + X_val[13]) % 10\n"
    ),
    explain=_explain_func_13,
)


def _fn_func_22(ch, key):
    def x(i):
        return key[ch[i]]
    j = (x(10) + x(11)) % 10
    return (x(j) + x(12) + x(13)) % 10


def _explain_func_22(ch, key, z):
    X = [key[i] for i in ch]
    j = (X[10] + X[11]) % 10
    return (
        f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X[10]}, X11=sgm[{ch[11]}]={X[11]}\n"
        f"2. ポインタ j = (X10 + X11) mod 10 = ({X[10]} + {X[11]}) mod 10 = {j} を計算\n"
        f"3. インデックス {j} の値を参照: X{j}=sgm[{ch[j]}]={X[j]}\n"
        f"4. Z = (X{j} + X12 + X13) mod 10 = ({X[j]} + {X[12]} + {X[13]}) mod 10 = {z}"
    )


_FUNC_22 = Algorithm(
    name="func_22",
    level=2,
    key_size=26,
    fn=_fn_func_22,
    rule_text=(
        "ルール：\n" + _KEYED_RULE_PREFIX +
        "2. j = (X[10] + X[11]) mod 10 を計算します。\n"
        "3. Z = (X[j] + X[12] + X[13]) mod 10 を計算します。\n"
    ),
    rationale_text=(
        "考え方:\n" + _KEYED_RATIONALE_PREFIX +
        "2. 変換後の位置10と位置11の値の和を10で割った余りを j とする．\n"
        "3. 変換後の位置 j, 12, 13 の値を合計し，10で割った余りが答えです．\n"
    ),
    code_body=(
        _KEYED_CODE_PREFIX +
        "    j = (X_val[10] + X_val[11]) % 10\n"
        "    return (X_val[j] + X_val[12] + X_val[13]) % 10\n"
    ),
    explain=_explain_func_22,
)


def _fn_func_31(ch, key):
    def x(i):
        return key[ch[i]]
    j = (x(10) + x(11) + x(12)) % 10
    return (x(j) + x(13)) % 10


def _explain_func_31(ch, key, z):
    X = [key[i] for i in ch]
    j = (X[10] + X[11] + X[12]) % 10
    return (
        f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X[10]}, X11=sgm[{ch[11]}]={X[11]}, "
        f"X12=sgm[{ch[12]}]={X[12]}\n"
        f"2. ポインタ j = (X10 + X11 + X12) mod 10 = "
        f"({X[10]} + {X[11]} + {X[12]}) mod 10 = {j} を計算\n"
        f"3. インデックス {j} の値を参照: X{j}=sgm[{ch[j]}]={X[j]}\n"
        f"4. Z = (X{j} + X13) mod 10 = ({X[j]} + {X[13]}) mod 10 = {z}"
    )


_FUNC_31 = Algorithm(
    name="func_31",
    level=2,
    key_size=26,
    fn=_fn_func_31,
    rule_text=(
        "ルール：\n" + _KEYED_RULE_PREFIX +
        "2. j = (X[10] + X[11] + X[12]) mod 10 を計算します。\n"
        "3. Z = (X[j] + X[13]) mod 10 を計算します。\n"
    ),
    rationale_text=(
        "考え方:\n" + _KEYED_RATIONALE_PREFIX +
        "2. 変換後の位置10, 11, 12の値の和を10で割った余りを j とする．\n"
        "3. 変換後の位置 j, 13 の値を合計し，10で割った余りが答えです．\n"
    ),
    code_body=(
        _KEYED_CODE_PREFIX +
        "    j = (X_val[10] + X_val[11] + X_val[12]) % 10\n"
        "    return (X_val[j] + X_val[13]) % 10\n"
    ),
    explain=_explain_func_31,
)


def _fn_func_pow(ch, key):
    def x(i):
        return key[ch[i]]
    return (1 * x(10) ** 4 + 2 * x(11) ** 3 + 3 * x(12) ** 2 + 4 * x(13)) % 10


def _explain_func_pow(ch, key, z):
    X = [key[i] for i in ch]
    v10, v11, v12, v13 = X[10] ** 4, X[11] ** 3, X[12] ** 2, X[13]
    total = 1 * v10 + 2 * v11 + 3 * v12 + 4 * v13
    return (
        f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X[10]}, X11=sgm[{ch[11]}]={X[11]}, "
        f"X12=sgm[{ch[12]}]={X[12]}, X13=sgm[{ch[13]}]={X[13]}\n"
        f"2. 各項を計算: 1*X10^4={v10}, 2*X11^3={2*v11}, 3*X12^2={3*v12}, 4*X13^1={4*v13}\n"
        f"3. 10で割った余りを算出: {total} mod 10 = {z}"
    )


_FUNC_POW = Algorithm(
    name="func_pow",
    level=3,
    key_size=26,
    fn=_fn_func_pow,
    rule_text=(
        "ルール：\n" + _KEYED_RULE_PREFIX +
        "2. Z = (1 * X[10]^4 + 2 * X[11]^3 + 3 * X[12]^2 + 4 * X[13]^1) mod 10 を計算します。\n"
    ),
    rationale_text=(
        "考え方:\n" + _KEYED_RATIONALE_PREFIX +
        "2. 変換後の位置10, 11, 12, 13の値をそれぞれ4乗, 3乗, 2乗, 1乗し，"
        "係数1, 2, 3, 4を掛けて合計する．\n"
        "3. その合計を10で割った余りが答えです．\n"
    ),
    code_body=(
        _KEYED_CODE_PREFIX +
        "    return (1 * pow(X_val[10], 4) + 2 * pow(X_val[11], 3)"
        " + 3 * pow(X_val[12], 2) + 4 * pow(X_val[13], 1)) % 10\n"
    ),
    explain=_explain_func_pow,
)


# =============================================================================
# 難易度ラダー（段階3: 重み格納型学習の境界探索用の診断アルゴリズム）
# =============================================================================
# func_22 が同時に含む3つの困難（①鍵テーブルの記憶量，②参照値の算術合成，
# ③ポインタ間接参照）を1段ずつ分離する:
#   L1 lookup_k{k}    : Z = SGM_TABLE[X0]                    …… ①のみ（鍵サイズ k を振る）
#   L2 table_add_k{k} : Z = (SGM_TABLE[X0]+SGM_TABLE[X1])%10 …… ①+②
#   L3 func_22        : （既存）                              …… ①+②+③
# これらは認証方式としての HCP ではなく，学習可能性の統制条件（診断用）である．

def _make_lookup(k: int) -> Algorithm:
    def fn(ch, key):
        return key[ch[0]] % 10

    def explain(ch, key, z):
        return f"1. X0={ch[0]} をインデックスとしてテーブル値を参照: sgm[{ch[0]}]={key[ch[0]]}\n2. Z = {z}"

    return Algorithm(
        name=f"lookup_k{k}",
        level=1,
        key_size=k,
        fn=fn,
        rule_text=(
            f"ルール：Z = SGM_TABLE[X0]\n"
            f"（X0 は 0〜{k - 1} の整数で、秘密のテーブル SGM_TABLE（長さ{k}、各要素0〜9）の"
            "インデックスです。X1〜X13 は使用しません）\n"
        ),
        rationale_text=(
            "考え方:\n1. X[0] をインデックスとして秘密のテーブルの値を参照する．その値が答えです．\n"
        ),
        code_body=(
            "    sgm = {key}\n"
            "    return sgm[X[0]] % 10\n"
        ),
        explain=explain,
    )


def _make_table_add(k: int) -> Algorithm:
    def fn(ch, key):
        return (key[ch[0]] + key[ch[1]]) % 10

    def explain(ch, key, z):
        a, b = key[ch[0]], key[ch[1]]
        return (
            f"1. テーブル値を参照: sgm[{ch[0]}]={a}, sgm[{ch[1]}]={b}\n"
            f"2. Z = ({a} + {b}) mod 10 = {z}"
        )

    return Algorithm(
        name=f"table_add_k{k}",
        level=1,
        key_size=k,
        fn=fn,
        rule_text=(
            f"ルール：Z = (SGM_TABLE[X0] + SGM_TABLE[X1]) mod 10\n"
            f"（X0, X1 は 0〜{k - 1} の整数で、秘密のテーブル SGM_TABLE（長さ{k}、各要素0〜9）の"
            "インデックスです。X2〜X13 は使用しません）\n"
        ),
        rationale_text=(
            "考え方:\n1. X[0], X[1] をインデックスとして秘密のテーブルの値を2つ参照する．\n"
            "2. その和を10で割った余りが答えです．\n"
        ),
        code_body=(
            "    sgm = {key}\n"
            "    return (sgm[X[0]] + sgm[X[1]]) % 10\n"
        ),
        explain=explain,
    )


def _make_pointer(k: int) -> Algorithm:
    """
    動的参照だけを単独で測る診断用アルゴリズム．
    Z = X[j] （j = (X10+X11) mod 10）．func_22 から「+X12+X13」の合成を除いたもの．
    table_add_k{k} と表サイズを揃えることで，「静的な2箇所参照+足し算」と
    「動的な参照先決定+単純な読み出し」を，同じ表サイズ・同じデータ量で直接比較できる．
    """

    def fn(ch, key):
        def x(i):
            return key[ch[i]]
        j = (x(10) + x(11)) % 10
        return x(j) % 10

    def explain(ch, key, z):
        X10, X11 = key[ch[10]], key[ch[11]]
        j = (X10 + X11) % 10
        Xj = key[ch[j]]
        return (
            f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X10}, X11=sgm[{ch[11]}]={X11}\n"
            f"2. ポインタ j = (X10 + X11) mod 10 = ({X10} + {X11}) mod 10 = {j} を計算\n"
            f"3. インデックス {j} の値を参照: X{j}=sgm[{ch[j]}]={Xj}\n"
            f"4. Z = X{j} = {z}（加算はありません）"
        )

    return Algorithm(
        name=f"pointer_k{k}",
        level=2,
        key_size=k,
        fn=fn,
        rule_text=(
            "ルール：\n" + _KEYED_RULE_PREFIX +
            "2. j = (X[10] + X[11]) mod 10 を計算します。\n"
            "3. Z = X[j] とします（そのまま出力します。加算はありません）。\n"
        ),
        rationale_text=(
            "考え方:\n" + _KEYED_RATIONALE_PREFIX +
            "2. 変換後の位置10と位置11の値の和を10で割った余りを j とする．\n"
            "3. 変換後の位置 j の値がそのまま答えです．\n"
        ),
        code_body=(
            _KEYED_CODE_PREFIX +
            "    j = (X_val[10] + X_val[11]) % 10\n"
            "    return X_val[j] % 10\n"
        ),
        explain=explain,
    )


def _make_table_add3(k: int) -> Algorithm:
    """
    統制実験用アルゴリズム（指導教員レビュー対応）．
    Z = (X0 + X1 + X2) mod 10．pointer_k{k} と「中間結果を保持して次の計算に使う」
    という多段階性・表サイズ・データ量は揃えつつ，中間結果を添字（動的参照）としては
    使わない点だけが異なる．pointer_k{k} と対にして比較することで，失敗の原因が
    「動的参照（間接参照）」なのか「多段階推論・中間結果の保持」なのかを切り分ける．
    """

    def fn(ch, key):
        return (key[ch[0]] + key[ch[1]] + key[ch[2]]) % 10

    def explain(ch, key, z):
        a, b, c = key[ch[0]], key[ch[1]], key[ch[2]]
        return (
            f"1. テーブル値を参照: sgm[{ch[0]}]={a}, sgm[{ch[1]}]={b}, sgm[{ch[2]}]={c}\n"
            f"2. Z = ({a} + {b} + {c}) mod 10 = {z}"
        )

    return Algorithm(
        name=f"table_add3_k{k}",
        level=1,
        key_size=k,
        fn=fn,
        rule_text=(
            f"ルール：Z = (SGM_TABLE[X0] + SGM_TABLE[X1] + SGM_TABLE[X2]) mod 10\n"
            f"（X0, X1, X2 は 0〜{k - 1} の整数で、秘密のテーブル SGM_TABLE（長さ{k}、各要素0〜9）の"
            "インデックスです。X3〜X13 は使用しません）\n"
        ),
        rationale_text=(
            "考え方:\n1. X[0], X[1], X[2] をインデックスとして秘密のテーブルの値を3つ参照する．\n"
            "2. その和を10で割った余りが答えです．\n"
        ),
        code_body=(
            "    sgm = {key}\n"
            "    return (sgm[X[0]] + sgm[X[1]] + sgm[X[2]]) % 10\n"
        ),
        explain=explain,
    )


def _make_pointer_chain(k: int, depth: int) -> Algorithm:
    """
    動的参照の「深さ」を振る診断用アルゴリズム（指導教員指示: #pointer chasing）．
    j = (X10+X11) mod 10 から出発し，(depth-1) 回 j = X[j] mod 10 を繰り返して
    ポインタを追跡してから，最後に X[j] を返す．depth=1 は既存 pointer_k と一致する
    （後方互換の健全性チェックに使える）．
    表サイズ k を固定して depth のみを振ることで，「組み合わせ爆発」（k を増やす場合の
    交絡，table_add 系で確認済み）と切り離して「参照の深さ」単体の効果を測る．
    """

    def fn(ch, key):
        def x(i):
            return key[ch[i]]
        j = (x(10) + x(11)) % 10
        for _ in range(depth - 1):
            j = x(j) % 10
        return x(j) % 10

    def explain(ch, key, z):
        def x(i):
            return key[ch[i]]
        X10, X11 = x(10), x(11)
        j = (X10 + X11) % 10
        lines = [
            f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X10}, X11=sgm[{ch[11]}]={X11}",
            f"2. ポインタ j = (X10 + X11) mod 10 = ({X10} + {X11}) mod 10 = {j} を計算",
        ]
        step = 3
        for _ in range(depth - 1):
            xj = x(j)
            new_j = xj % 10
            lines.append(
                f"{step}. 位置 {j} の値を参照して次のポインタにする: "
                f"X{j}=sgm[{ch[j]}]={xj} → j = {xj} mod 10 = {new_j}"
            )
            j = new_j
            step += 1
        final = x(j)
        lines.append(f"{step}. 最終的な位置 {j} の値を参照: X{j}=sgm[{ch[j]}]={final}")
        lines.append(f"{step + 1}. Z = X{j} = {z}（加算はありません）")
        return "\n".join(lines)

    if depth == 1:
        chase_rule = "3. Z = X[j] とします（そのまま出力します。加算はありません）。\n"
        chase_rationale = "3. 変換後の位置 j の値がそのまま答えです．\n"
        chase_code = ""
    else:
        chase_rule = (
            f"3. 次の手順を {depth - 1} 回繰り返します： j = X[j] mod 10（参照した値を次の"
            "ポインタにする）。\n"
            "4. 最後に Z = X[j] とします（そのまま出力します。加算はありません）。\n"
        )
        chase_rationale = (
            f"3. 参照して得た値を次のポインタとして使う操作を {depth - 1} 回繰り返します"
            "（ポインタ追跡）．\n"
            "4. 最終的に到達した位置の値がそのまま答えです．\n"
        )
        chase_code = f"    for _ in range({depth - 1}):\n        j = X_val[j] % 10\n"

    return Algorithm(
        name=f"pointer_chain_k{k}_d{depth}",
        level=2,
        key_size=k,
        fn=fn,
        rule_text=(
            "ルール：\n" + _KEYED_RULE_PREFIX +
            "2. j = (X[10] + X[11]) mod 10 を計算します。\n"
            + chase_rule
        ),
        rationale_text=(
            "考え方:\n" + _KEYED_RATIONALE_PREFIX +
            "2. 変換後の位置10と位置11の値の和を10で割った余りを j とする．\n"
            + chase_rationale
        ),
        code_body=(
            _KEYED_CODE_PREFIX +
            "    j = (X_val[10] + X_val[11]) % 10\n"
            + chase_code +
            "    return X_val[j] % 10\n"
        ),
        explain=explain,
    )


def _make_dualptr(k: int) -> Algorithm:
    """
    独立な動的参照を2つ持つ診断用アルゴリズム（指導教員候補②）．
    j1, j2 は互いに独立に計算され（依存関係がない），それぞれの参照結果を足す。
    recptr（依存あり）との対比により，「参照の独立な多重化」と「参照の連鎖的依存」の
    どちらがより深刻な壁になるかを切り分ける。
    """

    def fn(ch, key):
        def x(i):
            return key[ch[i]]
        j1 = (x(10) + x(11)) % 10
        j2 = (x(12) + x(13)) % 10
        return (x(j1) + x(j2)) % 10

    def explain(ch, key, z):
        def x(i):
            return key[ch[i]]
        X10, X11, X12, X13 = x(10), x(11), x(12), x(13)
        j1 = (X10 + X11) % 10
        j2 = (X12 + X13) % 10
        Xj1, Xj2 = x(j1), x(j2)
        return (
            f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X10}, X11=sgm[{ch[11]}]={X11}, "
            f"X12=sgm[{ch[12]}]={X12}, X13=sgm[{ch[13]}]={X13}\n"
            f"2. ポインタ j1 = (X10+X11) mod 10 = {j1}, "
            f"j2 = (X12+X13) mod 10 = {j2} を独立に計算\n"
            f"3. それぞれの位置を参照: X{j1}=sgm[{ch[j1]}]={Xj1}, X{j2}=sgm[{ch[j2]}]={Xj2}\n"
            f"4. Z = (X{j1} + X{j2}) mod 10 = ({Xj1} + {Xj2}) mod 10 = {z}"
        )

    return Algorithm(
        name=f"dualptr_k{k}",
        level=2,
        key_size=k,
        fn=fn,
        rule_text=(
            "ルール：\n" + _KEYED_RULE_PREFIX +
            "2. j1 = (X[10] + X[11]) mod 10 と j2 = (X[12] + X[13]) mod 10 を，"
            "互いに独立に計算します。\n"
            "3. Z = (X[j1] + X[j2]) mod 10 を計算します。\n"
        ),
        rationale_text=(
            "考え方:\n" + _KEYED_RATIONALE_PREFIX +
            "2. 位置10・11の和からポインタ j1，位置12・13の和からポインタ j2 を，"
            "互いに独立に求める．\n"
            "3. 変換後の位置 j1, j2 の値を合計し，10で割った余りが答えです．\n"
        ),
        code_body=(
            _KEYED_CODE_PREFIX +
            "    j1 = (X_val[10] + X_val[11]) % 10\n"
            "    j2 = (X_val[12] + X_val[13]) % 10\n"
            "    return (X_val[j1] + X_val[j2]) % 10\n"
        ),
        explain=explain,
    )


def _make_recptr(k: int) -> Algorithm:
    """
    再帰的（依存あり）な二重動的参照（指導教員候補③，func_22 の依存強化版）．
    j2 の計算に j1 の参照結果 X[j1] が使われる点が dualptr（j1, j2 が独立）との違い。
    """

    def fn(ch, key):
        def x(i):
            return key[ch[i]]
        j1 = (x(10) + x(11)) % 10
        j2 = (x(j1) + x(12)) % 10
        return (x(j2) + x(13)) % 10

    def explain(ch, key, z):
        def x(i):
            return key[ch[i]]
        X10, X11, X12, X13 = x(10), x(11), x(12), x(13)
        j1 = (X10 + X11) % 10
        Xj1 = x(j1)
        j2 = (Xj1 + X12) % 10
        Xj2 = x(j2)
        return (
            f"1. テーブル値を参照: X10=sgm[{ch[10]}]={X10}, X11=sgm[{ch[11]}]={X11}\n"
            f"2. ポインタ j1 = (X10+X11) mod 10 = {j1} を計算\n"
            f"3. 位置 j1 を参照: X{j1}=sgm[{ch[j1]}]={Xj1}\n"
            f"4. X12=sgm[{ch[12]}]={X12} を使い，j2 = (X{j1}+X12) mod 10 = {j2} を計算"
            f"（★j1の参照結果がj2の計算に影響する＝依存あり）\n"
            f"5. 位置 j2 を参照: X{j2}=sgm[{ch[j2]}]={Xj2}\n"
            f"6. X13=sgm[{ch[13]}]={X13} を足す: Z = (X{j2} + X13) mod 10 = "
            f"({Xj2} + {X13}) mod 10 = {z}"
        )

    return Algorithm(
        name=f"recptr_k{k}",
        level=2,
        key_size=k,
        fn=fn,
        rule_text=(
            "ルール：\n" + _KEYED_RULE_PREFIX +
            "2. j1 = (X[10] + X[11]) mod 10 を計算します。\n"
            "3. j2 = (X[j1] + X[12]) mod 10 を計算します"
            "（j1 の参照結果を使う点に注意）。\n"
            "4. Z = (X[j2] + X[13]) mod 10 を計算します。\n"
        ),
        rationale_text=(
            "考え方:\n" + _KEYED_RATIONALE_PREFIX +
            "2. 位置10・11の和からポインタ j1 を求める．\n"
            "3. 位置 j1 の値と位置12の値の和から，さらにポインタ j2 を求める"
            "（j1 の参照結果に依存する）．\n"
            "4. 変換後の位置 j2 と位置13の値を合計し，10で割った余りが答えです．\n"
        ),
        code_body=(
            _KEYED_CODE_PREFIX +
            "    j1 = (X_val[10] + X_val[11]) % 10\n"
            "    j2 = (X_val[j1] + X_val[12]) % 10\n"
            "    return (X_val[j2] + X_val[13]) % 10\n"
        ),
        explain=explain,
    )


_LADDER = [_make_lookup(4), _make_lookup(10), _make_lookup(26),
           _make_table_add(10), _make_table_add(13), _make_table_add(16),
           _make_table_add(20), _make_table_add(26),
           _make_pointer(10), _make_pointer(26),
           _make_table_add3(10), _make_table_add3(26)]

# 動的参照の「深さ」ラダー（2026-07: 教員指示 #pointer chasing）。
# k=10 を主戦場とする（k=26 は table_add 系で組み合わせ爆発と交絡することが判明済み
# のため参考条件に留める）。depth=1 は既存 pointer_k と等価（後方互換チェック用）。
_DEPTH_LADDER = [
    _make_pointer_chain(10, 1), _make_pointer_chain(10, 2), _make_pointer_chain(10, 3),
    _make_pointer_chain(26, 1), _make_pointer_chain(26, 2), _make_pointer_chain(26, 3),
    _make_dualptr(10), _make_dualptr(26),
    _make_recptr(10), _make_recptr(26),
]


# =============================================================================
# レジストリ
# =============================================================================

ALGORITHMS: dict[str, Algorithm] = {
    a.name: a
    for a in [_SIMPLE_ADD, _SECRET_ADD, *_LADDER, *_DEPTH_LADDER,
              _FUNC_13, _FUNC_13_K26, _FUNC_22, _FUNC_31, _FUNC_POW]
}


def get_algorithm(name: str) -> Algorithm:
    if name not in ALGORITHMS:
        raise ValueError(f"未知のアルゴリズムです: '{name}'．選択肢: {list(ALGORITHMS)}")
    return ALGORITHMS[name]


def algorithm_names() -> list[str]:
    return list(ALGORITHMS.keys())


# =============================================================================
# 自己検証: fn と reference_code の整合性チェック
# =============================================================================

def verify_all(n_samples: int = 200, seed: int = 0) -> None:
    """
    全アルゴリズムについて，fn（計算本体）と reference_code（コード表現）が
    同一の出力を返すことをランダムサンプルで検証する．不一致なら AssertionError．
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    for algo in ALGORITHMS.values():
        key = rng.integers(0, 10, algo.key_size).tolist() if algo.key_size else None
        namespace: dict = {}
        exec(algo.reference_code(key), {}, namespace)  # noqa: S102 — 自己生成コードの検証
        predict_z = namespace["predict_z"]
        for _ in range(n_samples):
            ch = rng.integers(0, algo.challenge_domain(), algo.challenge_len).tolist()
            expected = algo.compute(ch, key)
            actual = predict_z(ch) % 10
            assert expected == actual, (
                f"{algo.name}: fn と reference_code の結果が不一致 "
                f"(challenge={ch}, fn={expected}, code={actual})"
            )
    print(f"verify_all: {len(ALGORITHMS)} アルゴリズム × {n_samples} サンプル OK")


if __name__ == "__main__":
    verify_all()
