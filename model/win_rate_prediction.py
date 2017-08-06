import datetime

import keras
import numpy as np
from keras import objectives
from keras.layers import Dense, LSTM
from keras.models import Sequential
from pandas import DataFrame, Panel

import model.data_preprocess as data_pro
import util.aux_functions as ut
from util.ansi_code import AnsiEscapeCode as ansi


class WinrateModel(object):
    def __init__(self, x_trn, y_trn, x_val, y_val, time_step=1):
        # Suppose x = (id,date,[total,win,lose,draw]), the shape of x will be (id number, date range, 4)
        # Predict y as the next day's [total,win,lose,draw], which is a vector of (id number,4)
        self.x_trn = x_trn.values
        self.x_val = x_val.values
        self.x_shape = x_trn.shape
        self.y_shape = y_trn.shape
        self.y_trn = np.squeeze(y_trn.values, axis=1)
        self.y_val = np.squeeze(y_val.values, axis=1)
        self.batch_size = ut.least_common_factor_with_limit(x_trn.shape[0], x_val.shape[0], limit=1000)
        self.epoch = 1000
        self.lr = 0.01
        self.lr_decay = 0.9
        self.lstm1_node = 64
        self.lstm2_node = 16
        self.Dense1_node = 125
        self.Dense2_node = 25
        self.init_threshold = 0
        self.final_threshold = 90
        self.time_window = time_step
        self.loss = objectives.mse
        self.optimizer = keras.optimizers.adam(lr=self.lr)

        # Files directory
        self._model_dir = 'models/'
        self._model_postfix = '_AP_tw_' + str(time_step) + '_batch_' + str(self.batch_size)
        self._model_file = self._model_dir + 'activity model' + self._model_postfix + '.h5'
        self._model_weights = self._model_dir + 'activity _model_weights' + self._model_postfix + '.h5'
        self._model_json = self._model_dir + 'activity model' + self._model_postfix + '.json'

        self.model = self.construct_model()

    def construct_model(self):
        model = Sequential()
        model.add(
            LSTM(units=self.lstm1_node, batch_input_shape=(self.batch_size, self.time_window, self.y_shape[2]))
        )
        model.add(Dense(units=self.y_shape[2], activation='sigmoid'))
        model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
        return model

    def train_case(self, contd=False):
        if contd:
            self.model.load_weights(self._model_file)
        # split the train and validation set
        x_trn, y_trn, x_val, y_val = self.x_trn, self.y_trn, self.x_val, self.y_val
        for ep in range(self.epoch):
            init_score = [0, 0]
            # Manual learning rate decay
            if ep % 100 == 0 and ep > 0:
                self.lr *= self.lr_decay
                self.model.compile(loss=self.loss, optimizer=self.optimizer,
                                   metrics=['accuracy'])

            self.model.fit(x=x_trn, y=y_trn,
                           batch_size=self.batch_size,
                           epochs=1, shuffle=False, verbose=1)

            score = self.model.evaluate(x=x_val, y=y_val, batch_size=self.batch_size, verbose=1)
            init_score[0] += score[0]
            init_score[1] += score[1]

            if np.isnan(score[0]):
                print("Model training failed! Loss becomes %sNaN%s!" % (ansi.RED, ansi.ENDC))
                break

            self.save_model()  # Save model after each epoch to avoid crash
            init_score[0] /= len(x_trn)
            init_score[1] /= len(x_trn)
            print("Epoch %s/%s: average loss - %.4f average acc - %.4f%% learning rate - %.8f" %
                  (ep, self.epoch, init_score[0], init_score[1] * 100,
                   keras.backend.get_value(self.optimizer.lr)))
            if (ep == 0) and (init_score[1] * 100 < self.init_threshold):
                print("Reinitialization...")
                self.construct_model()
                self.train_case()
                break
            if init_score[1] * 100 > self.final_threshold:
                print(
                    "Activity prediction finished! Final average loss - %.4f acc - %.4f%%" % (
                        init_score[0], init_score[1] * 100))
                break

    def predict_case(self, x):
        prediction_all = []
        # Check shape, abandon predict if test & train shapes are different
        shape = np.asarray(x).shape
        assert shape[1] == self.x_shape[1] and shape[2] == self.x_shape[2]
        for index in range(len(x)):
            print("Testing trace: " + str(index))
            prediction_case = self.model.predict(x=x[index], batch_size=self.batch_size, verbose=0)
            self.model.reset_states()
            prediction_all.append(prediction_case)

        return prediction_all

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


def test():
    df1 = DataFrame(columns=['t', 'w', 'l', 'd'])
    df2 = DataFrame(columns=['t', 'w', 'l', 'd'])
    df1.loc[1000, ['t', 'w', 'l', 'd']] = [1, 0, 1, 0]
    df1.loc[1001, ['t', 'w', 'l', 'd']] = [1, 1, 0, 0]
    df1.loc[1002, ['t', 'w', 'l', 'd']] = [2, 1, 1, 0]
    for i in range(1, len(df1.columns)):
        df1.iloc[:, i] = df1.iloc[:, i] / df1.iloc[:, 0]
    df1.iloc[:, 0] += 0.001

    df2.loc[1000, ['t', 'w', 'l', 'd']] = [13, 4, 5, 4]
    df2.loc[1001, ['t', 'w', 'l', 'd']] = [4, 1, 1, 2]
    df2.loc[1002, ['t', 'w', 'l', 'd']] = [5, 3, 2, 0]
    for i in range(1, len(df2.columns)):
        df2.iloc[:, i] = df2.iloc[:, i] / df2.iloc[:, 0]
    df2.iloc[:, 0] += 0.001
    df = {'d1': df1, 'd2': df2}
    pd = Panel(df)

    print(pd['d1'])
    print(pd['d2'])

    # x_trn, y_trn, x_val, y_val = data_preprocess.convert_train_vali(data=pd)
    # model = winRate_model(x_trn=x_trn.values, y_trn=y_trn.values, x_val=x_val.values, y_val=y_val.values,
    #                       time_step=1)
    # model.train_case()
    # model.save_model()


if __name__ == "__main__":
    date = datetime.date.today()
    start = datetime.datetime.now()
    last_date = start.date()
    timewindow = 8

    data = data_pro.db_retrieve(last_day=date, timewindow=timewindow)
    x_trn, y_trn, x_val, y_val = data_pro.convert_train_vali(data=data)
    model = WinrateModel(x_trn=x_trn, y_trn=y_trn, x_val=x_val, y_val=y_val, time_step=timewindow - 1)
    model.train_case(contd=False)

    end = datetime.datetime.now()
    model_time = end - start
    print("\n%s%s%s model update finished, time usage: %s%s%s\n" % (
        ansi.BLUE, date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, model_time, ansi.ENDC))