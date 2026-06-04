import numpy as np
import pandas as pd

class ComputablePasswordGenerator:
  # 人間計算可能なパスワードの流出データを模したデータを自動生成する関数群
  # このクラスの関数を実行すると、人間計算可能なパスワードを模したデータが生成され、csvファイルとして保存される
  # 外部のプログラムから呼び出すときは、from computable_password_generator import ComputablePasswordGenerator としてimportを行う

  # この関数群の呼び出しには int: データ数 を引数として与える
  # この関数群はpandas.DataFrameをreturnする
  class Utils:
    @staticmethod
    def sgm(n :int) -> np.ndarray:
      sgm = np.random.randint(0,10,n)
      return sgm

  class GeneratorWithMetadata:
    def __init__(self, generator, name :str):
      self.generator = generator
      self.name = name

  @staticmethod
  # 関数の選択
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
  def password_simple_add(datasize :int) -> np.ndarray:
    result = []
    for row in range(datasize):
      X = ComputablePasswordGenerator.Utils.sgm(14)
      Z = (X[0] + X[1] + X[2]) % 10
      row = np.append(X, Z)
      result.append(row)
    table_array = np.array(result)
    return pd.DataFrame(table_array, columns=["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7",
      "X8", "X9", "X10", "X11", "X12","X13", "Z"])

  @staticmethod
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
    return pd.DataFrame(table_array, columns=["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7",
      "X8", "X9", "X10", "X11", "X12","X13", "Z"])

  @staticmethod
  # (k1,k2) = (2,2)
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
    return pd.DataFrame(table_array, columns=["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7",
      "X8", "X9", "X10", "X11", "X12","X13", "Z"])
  
  @staticmethod
  # (k1,k2) = (1,3)
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
    return pd.DataFrame( table_array, columns = ["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11", "X12", "X13", "Z"] )
  
  @staticmethod
  # (k1,k2) = (3,1)
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
    return pd.DataFrame( table_array, columns = ["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11", "X12", "X13", "Z"] )

  @staticmethod
  # power
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
    return pd.DataFrame( table_array, columns = ["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11", "X12", "X13", "Z"] )