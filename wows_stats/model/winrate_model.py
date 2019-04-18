import datetime

import keras
import numpy as np
from keras import objectives
from keras.layers import Dense, LSTM
from keras.models import Sequential

from src import model as data_prep, util as ut
from wows_stats.util.ansi_code import AnsiEscapeCode as ansi


class WinrateModel(object):
    def __init__(self, data, time_window=1):
        # Suppose x = (id,date,[total,win,lose,draw]), the shape of x will be (id number, date range, 4)
        # Predict y as the next day's [total,win,lose,draw], which is a vector of (id number,4)
        self._init_params(data=data, time_window=time_window)
        self._init_model()

    def _init_params(self, data, time_window):
        x_trn, y_trn, x_val, y_val = data_prep.split_train_validation(data=data)
        self.x_trn = x_trn.values
        self.x_val = x_val.values
        self.x_shape = x_trn.shape
        self.y_shape = y_trn.shape
        self.y_trn = np.squeeze(y_trn.values, axis=1)
        self.y_val = np.squeeze(y_val.values, axis=1)
        self.batch_size = ut.least_common_factor_with_limit(x_trn.shape[0], x_val.shape[0], limit=1000)
        self.time_window = time_window

        # Files directory
        self._model_dir = 'models/'
        self._model_postfix = '_AP_tw_' + str(self.time_window) + '_batch_' + str(self.batch_size)
        self._model_file = self._model_dir + 'activity model' + self._model_postfix + '.h5'
        self._model_weights = self._model_dir + 'activity _model_weights' + self._model_postfix + '.h5'
        self._model_json = self._model_dir + 'activity model' + self._model_postfix + '.json'

    def _init_model(self):
        self.epoch = 1000
        self.lr = 0.01
        self.lr_decay = 0.9
        self.lstm1_node = 64
        self.lstm2_node = 16
        self.Dense1_node = 125
        self.Dense2_node = 25
        self.init_threshold = 0
        self.acc_threshold = 90
        self.loss = objectives.mse
        self.optimizer = keras.optimizers.adam(lr=self.lr)
        self.model = self._construct_model()

    def _construct_model(self):
        model = Sequential()
        model.add(
            LSTM(units=self.lstm1_node, batch_input_shape=(self.batch_size, self.time_window, self.y_shape[2]))
        )
        model.add(Dense(units=self.y_shape[2], activation='sigmoid'))
        model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
        return model

    def training(self, contd=False):
        if contd:
            self.model.load_weights(self._model_file)
        init_score = np.zeros(2)
        for ep in range(self.epoch):
            score = self._train_each_epoch(ep=ep)
            if np.isnan(score[0]):
                print("Model training failed! Loss becomes %sNaN%s!" % (ansi.RED, ansi.ENDC))
                break
            init_score += score
            init_score /= len(self.x_trn)
            avg_loss = init_score[0]
            avg_acc = init_score[1] * 100

            print("Epoch %s/%s: average loss - %.4f average acc - %.4f%% learning rate - %.8f" %
                  (ep, self.epoch, avg_loss, avg_acc,
                   keras.backend.get_value(self.optimizer.lr)))
            if (ep == 0) and (avg_acc < self.init_threshold):
                print("Reinitialization...")
                self._construct_model()
                self.training()
                break
            self.save_model()
            if avg_acc > self.acc_threshold:
                print(
                    "Activity prediction finished! Final average loss - %.4f acc - %.4f%%" % (
                        avg_loss, avg_acc))
                break

    def _train_each_epoch(self, ep):
        if ep % 100 == 0 and ep > 0:
            self._manual_lr_decay()
        self.model.fit(x=self.x_trn, y=self.y_trn, batch_size=self.batch_size,
                       epochs=1, shuffle=False, verbose=1)
        return self.model.evaluate(x=self.x_val, y=self.y_val, batch_size=self.batch_size, verbose=1)

    def _manual_lr_decay(self):
        self.lr *= self.lr_decay
        self.model.compile(loss=self.loss, optimizer=self.optimizer,
                           metrics=['accuracy'])

    def predict(self, test_data):
        prediction_list = list()
        # Check shape, abandon predict if test & train shapes are different
        shape = np.asarray(test_data).shape
        assert shape[1] == self.x_shape[1] and shape[2] == self.x_shape[2]
        for index in range(len(test_data)):
            print("Testing trace: " + str(index))
            prediction_case = self.model.predict(x=test_data[index], batch_size=self.batch_size, verbose=0)
            self.model.reset_states()
            prediction_list.append(prediction_case)
        return prediction_list

    def save_model(self):
        try:
            self.model.save(self._model_file)
            model_json = self.model.to_json()
            with open(self._model_json, "w") as json_file:
                json_file.write(model_json)
            self.model.save_weights(self._model_weights)
        except OSError:
            print(ansi.RED + self._model_file + " save failed!!!" + ansi.ENDC)
            print(OSError)


def build_winrate_model():
    start_timer = datetime.datetime.now()
    date = start_timer.date()
    time_window = 8

    data = data_prep.get_from_db(last_day=date, timewindow=time_window)
    model = WinrateModel(data=data, time_window=time_window - 1)
    model.training(contd=False)

    end_timer = datetime.datetime.now()
    duration = end_timer - start_timer
    print("\n%s%s%s model update finished, time usage: %s%s%s\n" % (
        ansi.BLUE, date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, duration, ansi.ENDC))


if __name__ == "__main__":
    build_winrate_model()
