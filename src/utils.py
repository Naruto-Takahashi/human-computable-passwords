import numpy as np
import pandas as pd
import os
import json
import random
import subprocess
from matplotlib import pyplot
from sklearn.model_selection import train_test_split
from tensorflow import keras

class LossHistory(keras.callbacks.Callback):
  # Kerasの各バッチ終了時に損失 (loss) を記録するためのカスタムコールバック
  def on_train_begin(self, logs=None):
    if logs is None:
      logs = {}
    self.losses = []

  def on_batch_end(self, batch, logs=None):
    if logs is None:
      logs = {}
    self.losses.append(logs.get('loss'))


class Utils:
  # 現在のGitのコミットハッシュを取得する関数
  @staticmethod
  def get_git_commit_hash() -> str:
    try:
      commit_hash = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'],
        stderr=subprocess.DEVNULL
      ).decode('ascii').strip()
      return commit_hash
    except Exception:
      return "unknown"

  # 乱数シードを固定して再現性を確保する関数
  @staticmethod
  def fix_seed(seed :int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import tensorflow as tf
    tf.random.set_seed(seed)
    os.environ['TF_DETERMINISTIC_OPS'] = '1'

  # グラフのプロットを行う関数
  @staticmethod
  def plot_history(history :dict, output_dir :str) -> None:
    # 学習時の訓練データおよび検証データに対する正解率を表示する
    pyplot.clf()
    pyplot.plot(history['accuracy'])
    pyplot.plot(history['val_accuracy'])
    pyplot.title('model accuracy')
    pyplot.xlabel('epoch')
    pyplot.ylabel('accuracy')
    pyplot.legend(['acc', 'val_acc'], loc='lower right')
    pyplot.savefig(os.path.join(output_dir, 'accuracy.png'))

    # 学習時の訓練データおよび検証データに対する損失関数の値を表示する
    pyplot.clf()
    pyplot.plot(history['loss'])
    pyplot.plot(history['val_loss'])
    pyplot.title('model loss')
    pyplot.xlabel('epoch')
    pyplot.ylabel('loss')
    pyplot.legend(['loss', 'val_loss'], loc='lower right')
    pyplot.savefig(os.path.join(output_dir, 'loss.png'))
    return None

  # 実験メタデータと最終精度をJSONとして保存する関数
  @staticmethod
  def save_metadata(metadata :dict, output_dir :str) -> None:
    filepath = os.path.join(output_dir, 'metadata.json')
    with open(filepath, 'w', encoding='utf-8') as f:
      json.dump(metadata, f, indent=2, ensure_ascii=False)

  # 生成されたパスワードデータを訓練データと検証データに分割する関数
  @staticmethod
  def split_to_train_and_valid(generated_passwords :pd.DataFrame, seed :int = 42) -> (np.ndarray, np.ndarray, np.ndarray, np.ndarray):
    # 行全体をランダムシャッフル
    generated_passwords = generated_passwords.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # 特徴量 X とラベル Z に分割
    x = generated_passwords.drop(labels = ["Z"],axis = 1)
    y = generated_passwords["Z"]

    # 説明変数・目的変数をそれぞれ訓練データ・検証データに分割 (8:2)
    x_train,x_test,y_train,y_test = train_test_split(x, y, test_size=0.2, random_state=seed)

    # 目的変数を One-hot ベクトル形式 (10クラス) に変換
    y_train = keras.utils.to_categorical(y_train, 10)
    y_test = keras.utils.to_categorical(y_test, 10)

    return x_train, x_test, y_train, y_test
