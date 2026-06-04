# 人間計算可能なパスワード生成器からデータを取得し，各種モデルで学習を行うメインスクリプト
from computable_password_generator import ComputablePasswordGenerator
from utils import Utils
from models import Models

# 定義されたすべての機械学習モデルに対してループ
for model in Models.list_models():
  print("Runnning model: {}".format(model.name))
  
  # すべてのパスワードジェネレータに対してループ
  for generator in ComputablePasswordGenerator.list_generators():
    try:
      print("Testing: generator: {}, model: {}".format(generator.name, model.name))
      print("Figure name: {}".format(generator.name + "_" + model.name))
      
      # 指定されたサイズで模擬パスワードデータを生成
      generated_passwords = generator.generator(model.required_data_size)
      
      # 訓練データと検証データに分割
      x_train, x_test, y_train, y_test = Utils.split_to_train_and_valid(generated_passwords)
      
      # モデルの入力形式に合わせてデータをリシェイプ
      x_train = model.resharper(x_train)
      print(x_train.shape)
      x_test = model.resharper(x_test)
      
      # 学習中の詳細な損失履歴を記録するコールバックを設定 (必要に応じてメンバ変数 losses を参照可能)
      history_callback = Utils.LossHistory()
      
      # モデルの学習実行
      model.model.fit(
        x_train, y_train,
        batch_size=model.batch_size,
        epochs=model.epochs,
        verbose=1,
        validation_data=(x_test, y_test),
        callbacks=[history_callback]
      )
      
      # 学習完了後，エポックごとの履歴辞書を渡してグラフ保存
      Utils.plot_history(model.model.history.history, generator.name + "_" + model.name)
      
    except Exception as e:
      print("Error: generator: {}, model: {}".format(generator.name, model.name))
      print(e)
      continue
