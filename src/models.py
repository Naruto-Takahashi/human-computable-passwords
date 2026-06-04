import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Dense, Dropout, LSTM, Flatten, Bidirectional, Concatenate, Input, Embedding, Reshape, Conv1D, Layer, Lambda
from tensorflow.keras.models import Sequential, Model

class SqueezeLayer(Layer):
  # テンソルからサイズが1の次元を削除するカスタムレイヤー (最後の次元を削除)
  def call(self, inputs):
    return tf.squeeze(inputs, axis=-1)

class Models:
  class ModelWithMetadata:
    # Kerasモデルとそのトレーニングパラメータ (名前，バッチサイズ，エポック数，必要データ数) を保持するコンテナ
    def __init__(self, model, name :str, batch_size :int, epochs :int, required_data_size :int):
      self.model = model
      self.name = name
      self.batch_size = batch_size
      self.epochs = epochs
      self.required_data_size = required_data_size

    # LSTMモデル向けに入力データの形状を (サンプル数, タイムステップ数, 特徴量数) に変形する
    def resharper(self, df :pd.DataFrame) -> (np.ndarray):
      if self.name.find("lstm") != -1:
        return df.to_numpy().reshape(df.shape[0], df.shape[1], 1)
      return df

  @staticmethod
  # 実験で使用する機械学習モデルを選択・取得する関数
  def list_models() -> list:
    models = []
    # models.append(Models.ModelWithMetadata(Models.embed_mlp(), "mlp_with_embedding", 25, 1024, 50000))
    # models.append(Models.ModelWithMetadata(Models.embed_lstm(), "lstm_with_embedding", 25, 200, 50000))
    models.append(Models.ModelWithMetadata(Models.embed_cnn(), "cnn_with_embedding", 25, 50, 1000))
    # models.append(Models.ModelWithMetadata(Models.deep_bidirectional_sequential_lstm_with_dropout(), "deep_bidirectional_lstm_with_dropout_online", 1, 1024, 50000))
    # models.append(Models.ModelWithMetadata(Models.bidirectional_sequential_lstm_with_dropout_stateful(), "bidirectional_sequential_lstm_with_dropout_stateful", 100, 4096, 50000))
    # models.append(Models.ModelWithMetadata(Models.deep_bidirectional_sequential_lstm_with_dropout(), "deep_bidirectional_lstm_with_dropout", 32, 4096, 50000))
    # models.append(Models.ModelWithMetadata(Models.deep_bidirectional_sequential_lstm_32_1(), "deep_bidirectional_lstm_32_1", 64, 300, 50000))
    # models.append(Models.ModelWithMetadata(Models.deep_bidirectional_sequential_lstm_32_2(), "deep_bidirectional_lstm_32_2", 64, 300, 50000))
    # models.append(Models.ModelWithMetadata(Models.deep_bidirectional_sequential_lstm_32_4(), "deep_bidirectional_lstm_32_4", 64, 300, 50000))
    # models.append(Models.ModelWithMetadata(Models.deep_lstm_with_dropout(), "deep_lstm_with_dropout", 32, 4096, 50000))
    # models.append(Models.ModelWithMetadata(Models.bidirectional_sequential_lstm(), "bidirectional_lstm", 32, 4096, 50000))
    # models.append(Models.ModelWithMetadata(Models.mlp_model(), "mlp", 16, 1024, 10000))
    # models.append(Models.ModelWithMetadata(Models.simple_lstm_with_AMSGrad(), "simple_lstm", 32, 1024, 50000))
    # models.append(Models.ModelWithMetadata(Models.simple_lstm_with_adam(), "lstm_with_adam", 32, 1024, 50000))
    return models

  @staticmethod
  # 埋め込み層 (Embedding) と全結合層 (MLP) を組み合わせたモデル
  def embed_mlp() -> Model:
    inputs = Input(shape=(14, 1))
    inputs_reshaped = Flatten()(inputs)
    embedding = Embedding(14, 1)(inputs)
    embedding = Flatten()(embedding)
    concat = Concatenate(axis = 1)([inputs_reshaped, embedding])
    dense = Dense(128)(concat)
    dense = Dense(64)(dense)
    dense = Dense(32)(dense)
    outputs = Dense(10, activation="softmax")(dense)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    model.summary()
    return model
  
  @staticmethod
  # 埋め込み層 (Embedding) と双方向LSTM (Bi-LSTM) を組み合わせた再帰的ニューラルネットワークモデル
  def embed_lstm() -> Model:
    inputs = Input(shape=(14, 1))
    inputs_reshaped = Flatten()(inputs)
    embedding = Embedding(14, 1)(inputs)
    embedding = Flatten()(embedding)
    embedding = SqueezeLayer()(embedding)
    lstm = Bidirectional(LSTM(56), return_sequences=True)(embedding)
    lstm = Bidirectional(LSTM(56), return_sequences=True)(lstm)
    lstm = Bidirectional(LSTM(56), return_sequences=True)(lstm)
    dense = Dense(50)(lstm)
    dense = Dense(50)(lstm)
    dense = Dense(50)(lstm)
    outputs = Dense(10, activation="softmax")(dense)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    model.summary()
    return model

  @staticmethod
  # 埋め込み層 (Embedding) と 1次元畳み込み層 (Conv1D) を組み合わせたCNNモデル
  def embed_cnn() -> Model:
    N = 26 # ユーザーの記憶情報 (画像数)
    inputs = Input(shape=(14, ))
    embedding = Embedding(input_dim=N, output_dim=3)(inputs)
    conv = Conv1D(filters=32, kernel_size=3, activation="relu")(embedding)
    conv = Conv1D(filters=64, kernel_size=3, activation="relu")(conv)
    conv = Flatten()(conv)
    dense = Dense(30, activation="relu")(conv)
    dense = Dense(30, activation="relu")(dense)
    dense = Dense(30, activation="relu")(dense)
    outputs = Dense(10, activation="softmax")(dense)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(loss="categorical_crossentropy", optimizer="Adam", metrics=["accuracy"])
    model.summary()
    return model

# 以下のコメントアウトされたコードブロックは，必要に応じて有効化可能な代替モデル群です
"""
  # 人間計算可能なパスワードの予測に使うための機械学習モデル群
  # これらの関数を呼び出すと、指定したSequentialモデルがreturnされる
  @staticmethod
  def mlp_model() -> Sequential:
    model = Sequential()
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(10, activation='softmax'))
    model.compile(optimizer='sgd', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

  @staticmethod
  def simple_lstm_with_AMSGrad() -> Sequential:
    model = Sequential()
    model.add(LSTM(32, input_shape = (14, 1)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="RMSprop", metrics=["accuracy"])
    return model

  @staticmethod
  def simple_lstm_with_adam() -> Sequential:
    model = Sequential()
    model.add(LSTM(32, input_shape = (14, 1)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model
  
  @staticmethod
  def deep_lstm_with_dropout() -> Sequential:
    model = Sequential()
    model.add(LSTM(32, input_shape = (14, 1), return_sequences=True, dropout=0.2))
    model.add(LSTM(32, return_sequences=True, dropout=0.2))
    model.add(LSTM(32, dropout=0.2))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model

  @staticmethod
  def bidirectional_sequential_lstm() -> Sequential:
    model = Sequential()
    model.add(Bidirectional(LSTM(32, return_sequences=True), input_shape = (14, 1),))
    model.add(Bidirectional(LSTM(32)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model
  
  @staticmethod
  def deep_bidirectional_sequential_lstm_32_4() -> Sequential:
    model = Sequential()
    model.add(Bidirectional(LSTM(32, return_sequences=True), input_shape = (14, 1), ))
    model.add(Bidirectional(LSTM(32, return_sequences=True)))
    model.add(Bidirectional(LSTM(32, return_sequences=True)))
    model.add(Bidirectional(LSTM(32)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model

  @staticmethod
  def deep_bidirectional_sequential_lstm_32_2() -> Sequential:
    model = Sequential()
    model.add(Bidirectional(LSTM(32, return_sequences=True), input_shape = (14, 1), ))
    model.add(Bidirectional(LSTM(32)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model
  
  @staticmethod
  def deep_bidirectional_sequential_lstm_32_1() -> Sequential:
    model = Sequential()
    model.add(Bidirectional(LSTM(32), input_shape = (14, 1), ))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model
  
  @staticmethod
  def deep_bidirectional_sequential_lstm_with_dropout() -> Sequential:
    model = Sequential()
    model.add(Bidirectional(LSTM(32, return_sequences=True, dropout=0.2), input_shape = (14, 1)))
    model.add(Bidirectional(LSTM(32, return_sequences=True, dropout=0.2)))
    model.add(Bidirectional(LSTM(32, return_sequences=True, dropout=0.2)))
    model.add(Bidirectional(LSTM(32, dropout=0.2)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model
  
  @staticmethod
  def bidirectional_sequential_lstm_with_dropout_stateful() -> Sequential:
    model = Sequential()
    model.add(Bidirectional(LSTM(32, stateful = True, dropout=0.2), batch_input_shape = (100, 14, 1)))
    model.add(Bidirectional(LSTM(32, stateful = True, dropout=0.2)))
    model.add(Dense(10, activation="softmax"))
    model.compile(loss="mean_squared_error", optimizer="Adam", metrics=["accuracy"])
    return model
"""
