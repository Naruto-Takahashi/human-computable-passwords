import numpy as np
import pandas as pd
from matplotlib import pyplot
from sklearn.model_selection import train_test_split
from tensorflow import keras

class Utils:
  # グラフのプロットを行う関数
  # keras.model.fit.historyおよび画像の保存名を引数として取る
  @staticmethod
  def plot_history(history :str, name :str) -> None:
    # 学習時の訓練データおよび検証データに対する正解率を表示する
    pyplot.clf()
    pyplot.plot(history['accuracy'])
    pyplot.plot(history['val_accuracy'])
    pyplot.title('model accuracy')
    pyplot.xlabel('epoch')
    pyplot.ylabel('accuracy')
    pyplot.legend(['acc', 'val_acc'], loc='lower right')
    pyplot.savefig("outputs/" + name + '_accuracy.png')

    # 学習時の訓練データおよび検証データに対する損失関数の値を表示する
    pyplot.clf()
    pyplot.plot(history['loss'])
    pyplot.plot(history['val_loss'])
    pyplot.title('model loss')
    pyplot.xlabel('epoch')
    pyplot.ylabel('loss')
    pyplot.legend(['loss', 'val_loss'], loc='lower right')
    pyplot.savefig("outputs/" + name + '_loss.png')
    return None

  @staticmethod
  def split_to_train_and_valid(generated_passwords :pd.DataFrame) -> (np.ndarray, np.ndarray, np.ndarray, np.ndarray):
    generated_passwords = generated_passwords.sample(frac=1).reset_index(drop=True)
    x = generated_passwords.drop(labels = ["Z"],axis = 1)
    y = generated_passwords["Z"]

    # 説明変数・目的変数をそれぞれ訓練データ・検証データに分割
    x_train,x_test,y_train,y_test = train_test_split(x, y, test_size=0.2)

    y_train = keras.utils.to_categorical(y_train, 10)
    y_test = keras.utils.to_categorical(y_test, 10)

    return x_train, x_test, y_train, y_test

  class LossHistory(keras.callbacks.Callback):
    def on_train_begin(self, logs={}):
      self.losses = []

    def on_batch_end(self, batch, logs={}):
      self.losses.append(logs.get('loss'))
