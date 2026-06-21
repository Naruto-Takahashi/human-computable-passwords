# 人間計算可能なパスワード生成器からデータを取得し，各種モデルで学習を行うメインスクリプト
import os
import time
import sys
from datetime import datetime

# src/ をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'code'))

from core import Models, Utils, LossHistory
from core.generator import ComputablePasswordGenerator

# 実験の再現性のためのシード値固定
SEED = 42
Utils.fix_seed(SEED)

# 定義されたすべての機械学習モデルに対してループ
for model in Models.list_models():
    print("Runnning model: {}".format(model.name))

    # すべてのパスワードジェネレータに対してループ
    for generator in ComputablePasswordGenerator.list_generators():
        try:
            print(
                "Testing: generator: {}, model: {}".format(generator.name, model.name)
            )
            print("Figure name: {}".format(generator.name + "_" + model.name))

            # 今回の実験結果を保存する一意なディレクトリを作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"run_{timestamp}_{generator.name}_{model.name}"
            
            # プロジェクトルートの results/baselines/ に保存
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(base_dir, "results", "baselines", run_name)
            os.makedirs(output_dir, exist_ok=True)

            # 指定されたサイズで模擬パスワードデータを生成
            generated_passwords = generator.generator(model.required_data_size)

            # 訓練データと検証データに分割（シードを指定）
            x_train, x_test, y_train, y_test = Utils.split_to_train_and_valid(
                generated_passwords, seed=SEED
            )

            # モデルの入力形式に合わせてデータをリシェイプ
            x_train = model.reshaper(x_train)
            print(x_train.shape)
            x_test = model.reshaper(x_test)

            # 学習中の詳細な損失履歴を記録するコールバックを設定
            history_callback = LossHistory()

            # 学習完了時間を測定
            start_time = time.time()

            # モデルの学習実行
            model.model.fit(
                x_train,
                y_train,
                batch_size=model.batch_size,
                epochs=model.epochs,
                verbose=1,
                validation_data=(x_test, y_test),
                callbacks=[history_callback],
            )

            elapsed_time = time.time() - start_time

            # 学習完了後，エポックごとの履歴辞書を渡してグラフ保存
            Utils.plot_history(model.model.history.history, output_dir)

            # 実験メタデータ（設定や最終精度）を整理してJSON保存
            final_epoch_metrics = {
                metric: values[-1]
                for metric, values in model.model.history.history.items()
            }
            metadata = {
                "timestamp": timestamp,
                "git_commit": Utils.get_git_commit_hash(),
                "seed": SEED,
                "model_name": model.name,
                "generator_name": generator.name,
                "batch_size": model.batch_size,
                "epochs": model.epochs,
                "required_data_size": model.required_data_size,
                "elapsed_time_seconds": elapsed_time,
                "final_metrics": final_epoch_metrics,
            }
            Utils.save_metadata(metadata, output_dir)
            print(f"Saved results and metadata to {output_dir}")

        except Exception as e:
            print("Error: generator: {}, model: {}".format(generator.name, model.name))
            print(e)
            continue
