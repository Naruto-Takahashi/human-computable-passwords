from computable_password_generator import ComputablePasswordGenerator
from utils import Utils
from models import Models

for model in Models.list_models():
  print("Runnning model: {}".format(model.name))
  for generator in ComputablePasswordGenerator.list_generators():
    try:
      print("Testing: generator: {}, model: {}".format(generator.name, model.name))
      print("Figure name: {}".format(generator.name + "_" + model.name))
      generated_passwords = generator.generator(model.required_data_size)
      x_train, x_test, y_train, y_test = Utils.split_to_train_and_valid(generated_passwords)
      x_train = model.resharper(x_train)
      print(x_train.shape)
      x_test = model.resharper(x_test)
      history = LossHistory()
      model.model.fit(x_train,y_train,batch_size=model.batch_size, epochs=model.epochs, verbose=1, validation_data=(x_test, y_test), callbacks=[history])
      Utils.plot_history(history, generator.name + "_" + model.name)
    except Exception as e:
      print("Error: generator: {}, model: {}".format(generator.name, model.name))
      print(e)
      continue
