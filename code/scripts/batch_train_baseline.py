# TensorBoard と EarlyStopping を用いて，バッチサイズやエポック数を管理しつつ学習を実行するスクリプト
import os
import sys
import traceback

from tensorflow.keras.callbacks import EarlyStopping, TensorBoard

# src/ をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

from core import Models, Utils
from core.generator import ComputablePasswordGenerator

iter = 0
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
base_output_dir = os.path.join(base_dir, "results", "baselines", str(iter))
base_log_dir = os.path.join(base_output_dir, "logs")  # TensorBoardのログ保存先ベースディレクトリ

# 出力用ディレクトリの作成
os.makedirs(base_output_dir, exist_ok=True)

# すべての機械学習モデルに対してループ
for model in Models.list_models():
    print("Runnning model: {}".format(model.name))

    # すべてのパスワードジェネレータに対してループ
    for generator in ComputablePasswordGenerator.list_generators():
        # 早期終了 (EarlyStopping) の設定: 検証データの損失が50エポック改善しない場合に打ち切り
        early_stopping = EarlyStopping(monitor="val_loss", patience=50)

        # TensorBoard用のログディレクトリ設定
        log_dir = os.path.join(
            base_log_dir, str(iter), f"{generator.name}_{model.name}"
        )
        os.makedirs(log_dir, exist_ok=True)
        tensorboard = TensorBoard(log_dir=log_dir, histogram_freq=1)

        try:
            print(
                "Testing: generator: {}, model: {}".format(generator.name, model.name)
            )
            print("Figure name: {}".format(generator.name + "_" + model.name))

            # データの自動生成と分割
            generated_passwords = generator.generator(model.required_data_size)
            x_train, x_test, y_train, y_test = Utils.split_to_train_and_valid(
                generated_passwords
            )

            # モデル入力に合わせたリシェイプ
            x_train = model.reshaper(x_train)
            x_test = model.reshaper(x_test)

            # 学習実行 (TensorBoard コールバックを適用)
            model.model.fit(
                x_train,
                y_train,
                batch_size=model.batch_size,
                epochs=model.epochs,
                verbose=1,
                validation_data=(x_test, y_test),
                callbacks=[tensorboard],
            )

            # 学習履歴の取得とグラフ保存
            history = model.model.history.history
            plot_dir = os.path.join(base_output_dir, f"{generator.name}_{model.name}")
            os.makedirs(plot_dir, exist_ok=True)
            Utils.plot_history(history, plot_dir)

        except Exception as e:
            print("Error: generator: {}, model: {}".format(generator.name, model.name))
            print(e)
            traceback.print_exc()
            continue
