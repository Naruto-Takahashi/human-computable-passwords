import numpy as np
import pandas as pd

class ComputablePasswordGenerator:
  # 人間計算可能なパスワードの流出データを模したデータを自動生成する関数群
  # このクラスの関数を実行すると、人間計算可能なパスワードを模したデータが生成され、csvファイルとして保存される
  # 外部のプログラムから呼び出すときは、from computable_password_generator import ComputablePasswordGenerator としてimportを行う

  # 生成される DataFrame の共通カラム定義
  COLUMNS = [f"X{i}" for i in range(14)] + ["Z"]

  # この関数群の呼び出しには int: データ数 を引数として与える
  # この関数群はpandas.DataFrameをreturnする
  
  class Utils:
    @staticmethod
    # 0〜9のランダムな整数からなる配列 (長さ n) を生成するユーティリティ関数
    def sgm(n :int) -> np.ndarray:
      sgm = np.random.randint(0,10,n)
      return sgm

  class GeneratorWithMetadata:
    # ジェネレータ関数本体と，そのメタデータ（識別名）を保持するクラス
    def __init__(self, generator, name :str):
      self.generator = generator
      self.name = name

  @staticmethod
  # 使用するジェネレータ（パスワード生成アルゴリズム）の選択リストを取得
  def list_generators() -> list:
    generators = []
    # generators.append(ComputablePasswordGenerator.GeneratorWithMetadata(ComputablePasswordGenerator.password_simple_add, "simple_add"))
    # generators.append(ComputablePasswordGenerator.GeneratorWithMetadata(ComputablePasswordGenerator.password_with_middle, "middle"))
    # generators.append(ComputablePasswordGenerator.GeneratorWithMetadata(ComputablePasswordGenerator.s_x, "s_x"))
    # generators.append( ComputablePasswordGenerator.GeneratorWithMetadata( ComputablePasswordGenerator.func_13, "func_13" ) )
    generators.append( ComputablePasswordGenerator.GeneratorWithMetadata( ComputablePasswordGenerator.func_31, "func_31" ) )
    # generators.append( ComputablePasswordGenerator.GeneratorWithMetadata( ComputablePasswordGenerator.func_pow, "func_pow" ) )
    return generators

  @staticmethod
  # 単純加算アルゴリズム: 最初の3つの数字の合計を10で割った余りを Z (パスワード) とし，X に Z を付加して返す
  def password_simple_add(datasize :int) -> np.ndarray:
    result = []
    for row in range(datasize):
      X = ComputablePasswordGenerator.Utils.sgm(14)
      Z = (X[0] + X[1] + X[2]) % 10
      row = np.append(X, Z)
      result.append(row)
    table_array = np.array(result)
    return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS)

  @staticmethod
  # 中間変数を用いた暗号化アルゴリズム: 各チャレンジを変換して中間変数を求め，特定のインデックスを参照して最終的な Z を生成する
  def password_with_middle(datasize :int) -> np.ndarray:
    result = []
    sgm = ComputablePasswordGenerator.Utils.sgm(14)
    for row in range(datasize):
      X = ComputablePasswordGenerator.Utils.sgm(14)
      S_X = np.zeros(14)
      for k in range(14):
        S_X[k] = sgm[X[k]]
      mid = (S_X[10] + S_X[11]) % 10
      Z = (S_X[int(mid)] + S_X[12]) % 10
      row = np.append(X, Z)
      result.append(row)
    table_array = np.array(result)
    return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS)

  @staticmethod
  # s_x アルゴリズム: N=100の記憶情報をもとに，ランダムチャレンジから得られた記憶配列 (S_X) のインデックスから Z を算出する (k1,k2) = (2,2)
  def s_x(datasize :int) -> np.ndarray:
    N = 100 # the number of images
    result = []
    sgm = ComputablePasswordGenerator.Utils.sgm(N)
    for row in range( datasize ):
      X = np.random.randint(0,N,14)
      S_X = np.zeros(14,dtype=int)
      for k in range(14):
        S_X[k] = sgm[X[k]]
      mid = ( S_X[10] + S_X[11] ) % 10
      Z = ( S_X[12] + S_X[13] + S_X[int(mid)] ) % 10
      row = np.append(X, Z)
      result.append(row)
    table_array = np.array(result)
    return pd.DataFrame(table_array, columns=ComputablePasswordGenerator.COLUMNS)
  
  @staticmethod
  # func_13: 記憶数 N=100 に対して (k1,k2) = (1,3) の構成．X[10] をポインタとして用いる
  def func_13( datasize: int ) -> np.ndarray:
    N_user_memory = 100 # the number of images
    result = []
    sgm = ComputablePasswordGenerator.Utils.sgm( N_user_memory )
    for row in range( datasize ):
      challenge_idx = np.random.randint( 0, N_user_memory, 14 )
      X = np.zeros( 14, dtype = int )
      for k in range( 14 ):
        X[k] = sgm[challenge_idx[k]]
      j = X[10] % 10
      Z = ( X[int(j)] + X[11] + X[12] + X[13] ) % 10
      row = np.append( challenge_idx, Z )
      result.append( row )
    table_array = np.array( result )
    return pd.DataFrame( table_array, columns=ComputablePasswordGenerator.COLUMNS )
  
  @staticmethod
  # func_31: 記憶数 N=26 に対して (k1,k2) = (3,1) の構成．X[10], X[11], X[12] の和をポインタとして用いる
  def func_31( datasize: int ) -> np.ndarray:
    N_user_memory = 26 # the number of images
    result = []
    sgm = ComputablePasswordGenerator.Utils.sgm( N_user_memory )
    for row in range( datasize ):
      challenge_idx = np.random.randint( 0, N_user_memory, 14 )
      X = np.zeros( 14, dtype = int )
      for k in range( 14 ):
        X[k] = sgm[challenge_idx[k]]
      j = ( X[10] + X[11] + X[12] ) % 10
      Z = ( X[int(j)] + X[13] ) % 10
      row = np.append( challenge_idx, Z )
      result.append( row )
    table_array = np.array( result )
    return pd.DataFrame( table_array, columns=ComputablePasswordGenerator.COLUMNS )

  @staticmethod
  # func_pow: 各チャレンジ値の多項式累乗 (4乗, 3乗, 2乗, 1乗) を計算し，10で割った余りを Z とする
  def func_pow( datasize: int ) -> np.ndarray:
    N_user_memory = 26 # the number of images
    result = []
    sgm = ComputablePasswordGenerator.Utils.sgm( N_user_memory )
    for row in range( datasize ):
      challenge_idx = np.random.randint( 0, N_user_memory, 14 )
      X = np.zeros( 14, dtype = int )
      for k in range( 14 ):
        X[k] = sgm[challenge_idx[k]]
      Z = ( 1*pow(X[10],4) + 2*pow(X[11],3) + 3*pow(X[12],2) + 4*pow(X[13],1) ) % 10
      row = np.append( challenge_idx, Z )
      result.append( row )
    table_array = np.array( result )
    return pd.DataFrame( table_array, columns=ComputablePasswordGenerator.COLUMNS )