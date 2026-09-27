import numpy as np
import pandas as pd
import keras
from keras import ops
from keras.layers import (
    LSTM,
    Add,
    Bidirectional,
    Concatenate,
    Conv1D,
    Dense,
    Dropout,
    Embedding,
    Flatten,
    GlobalAveragePooling1D,
    Input,
    Layer,
    LayerNormalization,
    MultiHeadAttention,
)
from keras.models import Model, Sequential
from keras.optimizers import Adam


class PositionalEmbedding(Layer):
    """位置埋め込み（学習可能）．

    self-attention は順序を持たないので，位置情報を足さないと
    「10番目の値」「12番目の値」を区別できない。HCP は位置が本質的
    （$j$ は位置10, 11 から作り，位置12, 13 を足す）なので必須である。
    """

    def __init__(self, length: int, dim: int, **kwargs):
        super().__init__(**kwargs)
        self.pos = Embedding(input_dim=length, output_dim=dim)
        self.length = length

    def call(self, x):
        positions = ops.arange(self.length)
        return x + self.pos(positions)


class PrependClsToken(Layer):
    """系列の先頭に学習可能な1トークンを挿入する（`readout="cls"` 用）．

    平均プーリングは位置をまたいで潰すので，「位置 $j$ の値」を読み出しにくい。
    CLS トークンなら，どの位置を見るかを attention 自身に決めさせられる。
    """

    def __init__(self, dim: int, **kwargs):
        super().__init__(**kwargs)
        self.dim = dim

    def build(self, input_shape):
        self.cls = self.add_weight(
            name="cls", shape=(1, 1, self.dim), initializer="random_normal"
        )
        super().build(input_shape)

    def call(self, x):
        batch = ops.shape(x)[0]
        return ops.concatenate([ops.tile(self.cls, [batch, 1, 1]), x], axis=1)


class SliceFirstToken(Layer):
    """CLS トークン（先頭位置）の出力だけを取り出す．"""

    def call(self, x):
        return x[:, 0, :]


class SqueezeLayer(Layer):
    # テンソルからサイズが1の次元を削除するカスタムレイヤー (最後の次元を削除)
    def call(self, inputs):
        return ops.squeeze(inputs, axis=-1)


class Models:
    class ModelWithMetadata:
        # Kerasモデルとそのトレーニングパラメータ (名前，バッチサイズ，エポック数，必要データ数) を保持するコンテナ
        def __init__(
            self,
            model,
            name: str,
            batch_size: int,
            epochs: int,
            required_data_size: int,
        ):
            self.model = model
            self.name = name
            self.batch_size = batch_size
            self.epochs = epochs
            self.required_data_size = required_data_size

        # LSTMモデル向けに入力データの形状を (サンプル数, タイムステップ数, 特徴量数) に変形する
        def reshaper(self, df: pd.DataFrame) -> np.ndarray:
            if self.name.find("lstm") != -1:
                return df.to_numpy().reshape(df.shape[0], df.shape[1], 1)
            return df

    @staticmethod
    # 実験で使用する機械学習モデルを選択・取得する関数
    def list_models() -> list:
        models = []
        # models.append(Models.ModelWithMetadata(Models.embed_mlp(), "mlp_with_embedding", 25, 1024, 50000))
        # models.append(Models.ModelWithMetadata(Models.embed_lstm(), "lstm_with_embedding", 25, 200, 50000))
        models.append(
            Models.ModelWithMetadata(
                Models.embed_cnn(), "cnn_with_embedding", 25, 50, 1000
            )
        )
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
        concat = Concatenate(axis=1)([inputs_reshaped, embedding])
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
        N = 26  # ユーザーの記憶情報 (画像数)
        inputs = Input(shape=(14,))
        embedding = Embedding(input_dim=N, output_dim=3)(inputs)
        conv = Conv1D(filters=32, kernel_size=3, activation="relu")(embedding)
        conv = Conv1D(filters=64, kernel_size=3, activation="relu")(conv)
        conv = Flatten()(conv)
        dense = Dense(30, activation="relu")(conv)
        dense = Dense(30, activation="relu")(dense)
        dense = Dense(30, activation="relu")(dense)
        outputs = Dense(10, activation="softmax")(dense)
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(
            loss="categorical_crossentropy", optimizer="Adam", metrics=["accuracy"]
        )
        model.summary()
        return model

    @staticmethod
    # 埋め込み層と Transformer エンコーダを組み合わせたモデル（2026-09-27 追加）
    def embed_transformer(
        n_images: int = 26,
        d_model: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        ff_dim: int = 128,
        readout: str = "mean",
        learning_rate: float = 1e-3,
    ) -> Model:
        """**小川ら(2025) §5.4 の第一の将来課題に対応するモデル。**

        原文: "A particularly important next step is to evaluate attention-based
        and Transformer-style models. **Self-attention is naturally suited to
        content-dependent selection**, and therefore provides a direct way to test
        whether a model can learn to attend to the input-dependent referenced position."

        $`j`$ 項はまさに「内容依存の参照位置の選択」であり，self-attention は
        その機構そのものである。したがって本モデルは著者らの予想を直接検証する。

        **既存の LLM 実験（経路A・経路B）との違い**: あちらは事前学習済みモデルを
        使うので，self-attention の効果と事前学習の効果が分離できない。
        ゼロから学習する本モデルは**アーキテクチャの効果だけ**を取り出す。

        | 道 | self-attention | 事前学習 | 重み更新 |
        |---|---|---|---|
        | 本モデル | ○ | **✗** | ○ |
        | 経路B（LLM追加学習） | ○ | ○ | ○ |
        | 経路A（LLM in-context） | ○ | ○ | **✗** |

        > [!WARNING]
        > **規模は小川らの CNN と揃っていない。**既定値（d_model=64, 4ヘッド,
        > 2層, ff=128）では 74,314 パラメータで，CNN の 28,006 の約2.7倍である。
        > 「揃えた」とは書けない。容量で負けていない方が
        > 「Transformer でも解けない」の主張には安全だが，**既定値は根拠なく
        > 選んだ値であり，実験C1 の予備実験4 で決める**。

        ## `readout` — 14位置をどう1つのベクトルに畳むか

        **ここは結果を左右する。実測で確かめた（2026-09-27，`table_add3_k26`，
        10,000件，30エポック）。**

        | 値 | 畳み方 | 統制の検証最大 | パラメータ |
        |---|---|---|---|
        | `mean` | 14位置の平均（既定） | **1.0000** | 75,850 |
        | `cls` | 先頭に学習可能な1トークンを足しその出力だけ使う | **1.0000** | 75,978 |
        | `flatten` | 14×d_model を連結（小川らの CNN と同じ） | **0.1210**（床） | 129,098 |

        > [!WARNING]
        > **`flatten` は統制すら学習できない。**「平均は位置情報を潰すから
        > `Flatten` の方が公平だろう」と考えて既定にしたが，実測は逆だった。
        > パラメータは最多（129,098）なので容量の問題ではない。
        > 位置ごとに `LayerNormalization` を通したあと 896 次元を一度に
        > 全結合へ渡す形が最適化を壊していると見られる。
        >
        > したがって既定は `mean` に戻した。**この軸は実験C1 の予備実験4 で
        > 3値すべてを回す**（読み出しを変えるとパラメータ数も動くので，
        > 規模の軸と合わせて読む）。
        """
        if readout not in ("flatten", "mean", "cls"):
            raise ValueError(f"readout は flatten / mean / cls のいずれか: {readout}")

        inputs = Input(shape=(14,))
        x = Embedding(input_dim=n_images, output_dim=d_model)(inputs)
        length = 14
        if readout == "cls":
            x = PrependClsToken(d_model)(x)
            length = 15
        x = PositionalEmbedding(length, d_model)(x)

        for _ in range(num_layers):
            # self-attention ブロック（残差 ＋ 層正規化）
            attn = MultiHeadAttention(num_heads=num_heads, key_dim=d_model // num_heads)(
                x, x
            )
            x = LayerNormalization(epsilon=1e-6)(Add()([x, attn]))
            # 位置ごとの全結合ブロック
            ff = Dense(ff_dim, activation="relu")(x)
            ff = Dense(d_model)(ff)
            x = LayerNormalization(epsilon=1e-6)(Add()([x, ff]))

        if readout == "mean":
            x = GlobalAveragePooling1D()(x)
        elif readout == "flatten":
            x = Flatten()(x)
        else:  # cls
            x = SliceFirstToken()(x)

        x = Dense(64, activation="relu")(x)
        outputs = Dense(10, activation="softmax")(x)
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(
            loss="categorical_crossentropy",
            optimizer=Adam(learning_rate=learning_rate),
            metrics=["accuracy"],
        )
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
