import os
import traceback
from computable_password_generator import ComputablePasswordGenerator
from models import Models
from tensorflow.keras.callbacks import EarlyStopping, TensorBoard
from utils import Utils

iter = 0
base_log_dir = r""  # 保存先ディレクトリ

try:
  os.mkdir("outputs/{}".format(iter))

except:
  pass

for model in Models.list_models():
  print("Runnning model: {}".format(model.name))

  for generator in ComputablePasswordGenerator.list_generators():
    early_stopping = EarlyStopping(monitor='val_loss', patience=50)
    log_dir = os.path.join(base_log_dir, str(iter), f"{generator.name}_{model.name}")
    os.makedirs(log_dir, exist_ok=True)
    tensorboard = TensorBoard(log_dir=log_dir, histogram_freq=1)

    try:
      print("Testing: generator: {}, model: {}".format(generator.name, model.name))
      print("Figure name: {}".format(generator.name + "_" + model.name))
      generated_passwords = generator.generator(model.required_data_size)
      x_train, x_test, y_train, y_test = Utils.split_to_train_and_valid(generated_passwords)
      x_train = model.resharper(x_train)
      x_test = model.resharper(x_test)
      model.model.fit(x_train,y_train,batch_size=model.batch_size, epochs=model.epochs, verbose=1, validation_data=(x_test, y_test), callbacks=[tensorboard])
      history = model.model.history.history
      Utils.plot_history(history, "{}/".format(iter) + generator.name + "_" + model.name)

    except Exception as e:
      print("Error: generator: {}, model: {}".format(generator.name, model.name))
      print(e)
      traceback.print_exc()
      continue
