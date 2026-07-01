import numpy as np
import pandas as pd


class ComputablePasswordGenerator:
    # 生成される DataFrame の共通カラム定義
    COLUMNS = [f"X{i}" for i in range(14)] + ["Z"]

    class Utils:
        @staticmethod
        # 0〜9のランダムな整数からなる配列 (長さ n) を生成するユーティリティ関数
        def sgm(n: int) -> np.ndarray:
            sgm = np.random.randint(0, 10, n)
            return sgm

    @staticmethod
    def list_generators() -> list:
        # 従来のコードとの互換性のため残す
        return []

    @staticmethod
    def password_simple_add(datasize: int) -> tuple[pd.DataFrame, None]:
        result = []
        for row in range(datasize):
            X = ComputablePasswordGenerator.Utils.sgm(14)
            Z = (X[0] + X[1] + X[2]) % 10
            row = np.append(X, Z)
            result.append(row)
        table_array = np.array(result)
        return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS), None

    @staticmethod
    def func_13(datasize: int) -> tuple[pd.DataFrame, list[int]]:
        N_user_memory = 100
        result = []
        sgm = ComputablePasswordGenerator.Utils.sgm(N_user_memory).tolist()
        for row in range(datasize):
            challenge_idx = np.random.randint(0, N_user_memory, 14)
            X = np.zeros(14, dtype=int)
            for k in range(14):
                X[k] = sgm[challenge_idx[k]]
            j = X[10] % 10
            Z = (X[int(j)] + X[11] + X[12] + X[13]) % 10
            row = np.append(challenge_idx, Z)
            result.append(row)
        table_array = np.array(result)
        return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS), sgm

    @staticmethod
    def func_31(datasize: int) -> tuple[pd.DataFrame, list[int]]:
        N_user_memory = 26
        result = []
        sgm = ComputablePasswordGenerator.Utils.sgm(N_user_memory).tolist()
        for row in range(datasize):
            challenge_idx = np.random.randint(0, N_user_memory, 14)
            X = np.zeros(14, dtype=int)
            for k in range(14):
                X[k] = sgm[challenge_idx[k]]
            j = (X[10] + X[11] + X[12]) % 10
            Z = (X[int(j)] + X[13]) % 10
            row = np.append(challenge_idx, Z)
            result.append(row)
        table_array = np.array(result)
        return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS), sgm

    @staticmethod
    def func_22(datasize: int) -> tuple[pd.DataFrame, list[int]]:
        N_user_memory = 26
        result = []
        sgm = ComputablePasswordGenerator.Utils.sgm(N_user_memory).tolist()
        for row in range(datasize):
            challenge_idx = np.random.randint(0, N_user_memory, 14)
            X = np.zeros(14, dtype=int)
            for k in range(14):
                X[k] = sgm[challenge_idx[k]]
            j = (X[10] + X[11]) % 10
            Z = (X[int(j)] + X[12] + X[13]) % 10
            row = np.append(challenge_idx, Z)
            result.append(row)
        table_array = np.array(result)
        return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS), sgm

    @staticmethod
    def func_pow(datasize: int) -> tuple[pd.DataFrame, list[int]]:
        N_user_memory = 26
        result = []
        sgm = ComputablePasswordGenerator.Utils.sgm(N_user_memory).tolist()
        for row in range(datasize):
            challenge_idx = np.random.randint(0, N_user_memory, 14)
            X = np.zeros(14, dtype=int)
            for k in range(14):
                X[k] = sgm[challenge_idx[k]]
            Z = (
                1 * pow(X[10], 4)
                + 2 * pow(X[11], 3)
                + 3 * pow(X[12], 2)
                + 4 * pow(X[13], 1)
            ) % 10
            row = np.append(challenge_idx, Z)
            result.append(row)
        table_array = np.array(result)
        return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS), sgm

    @staticmethod
    def explain_logic(generator_name: str, row: pd.Series, sgm: list[int] = None) -> str:
        """
        特定のアルゴリズムとデータ行に対して，正解に至る論理ステップを解説文として生成する．
        """
        # プロンプトに渡されている X は実は challenge_idx (sgmのインデックス)
        idx = [int(row[f"X{i}"]) for i in range(14)]
        Z = int(row["Z"])
        
        if generator_name == "simple_add":
            return (
                f"1. 最初の3つの数字を取得: X0={idx[0]}, X1={idx[1]}, X2={idx[2]}\n"
                f"2. 和を計算: {idx[0]} + {idx[1]} + {idx[2]} = {idx[0]+idx[1]+idx[2]}\n"
                f"3. 10で割った余りを算出: {idx[0]+idx[1]+idx[2]} mod 10 = {Z}"
            )
        
        # sgm を使ったアルゴリズムの場合の解説
        if sgm is None:
            return "解説の生成に秘密のテーブル(sgm)が必要です．"

        if generator_name == "func_13":
            # 実際の計算に使われる値 X
            X = [sgm[i] for i in idx]
            j = X[10] % 10
            return (
                f"1. インデックスに対応するテーブル値を参照: X10=sgm[{idx[10]}]={X[10]}\n"
                f"2. ポインタ j = X10 mod 10 = {X[10]} mod 10 = {j} を計算\n"
                f"3. インデックス {j} の値をテーブルから取得: X{j}=sgm[{idx[j]}]={X[j]}\n"
                f"4. Z = (X{j} + X11 + X12 + X13) mod 10 = ({X[j]} + {X[11]} + {X[12]} + {X[13]}) mod 10 = {Z}"
            )

        elif generator_name == "func_31":
            X = [sgm[i] for i in idx]
            j = (X[10] + X[11] + X[12]) % 10
            return (
                f"1. テーブル値を参照: X10=sgm[{idx[10]}]={X[10]}, X11=sgm[{idx[11]}]={X[11]}, X12=sgm[{idx[12]}]={X[12]}\n"
                f"2. ポインタ j = (X10 + X11 + X12) mod 10 = ({X[10]} + {X[11]} + {X[12]}) mod 10 = {j} を計算\n"
                f"3. インデックス {j} の値を参照: X{j}=sgm[{idx[j]}]={X[j]}\n"
                f"4. Z = (X{j} + X13) mod 10 = ({X[j]} + {X[13]}) mod 10 = {Z}"
            )

        elif generator_name == "func_22":
            X = [sgm[i] for i in idx]
            j = (X[10] + X[11]) % 10
            return (
                f"1. テーブル値を参照: X10=sgm[{idx[10]}]={X[10]}, X11=sgm[{idx[11]}]={X[11]}\n"
                f"2. ポインタ j = (X10 + X11) mod 10 = ({X[10]} + {X[11]}) mod 10 = {j} を計算\n"
                f"3. インデックス {j} の値を参照: X{j}=sgm[{idx[j]}]={X[j]}\n"
                f"4. Z = (X{j} + X12 + X13) mod 10 = ({X[j]} + {X[12]} + {X[13]}) mod 10 = {Z}"
            )

        elif generator_name == "func_pow":
            X = [sgm[i] for i in idx]
            v10, v11, v12, v13 = pow(X[10],4), pow(X[11],3), pow(X[12],2), pow(X[13],1)
            total = (1*v10 + 2*v11 + 3*v12 + 4*v13)
            return (
                f"1. テーブル値を参照: X10=sgm[{idx[10]}]={X[10]}, X11=sgm[{idx[11]}]={X[11]}, X12=sgm[{idx[12]}]={X[12]}, X13=sgm[{idx[13]}]={X[13]}\n"
                f"2. 各項を計算: 1*X10^4={v10}, 2*X11^3={2*v11}, 3*X12^2={3*v12}, 4*X13^1={4*v13}\n"
                f"3. 10で割った余りを算出: {total} mod 10 = {Z}"
            )
            
        return "解説が定義されていないアルゴリズムです．"
