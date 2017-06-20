import keras
import numpy as np
from keras import objectives
from keras.layers import Dense, LSTM
from keras.models import Sequential


class winRate_model(object):
    def __init__(self, x_trn, y_trn, x_val, y_val, time_step=1):
        # Suppose x = (id,date,[total,win,lose,draw]), the shape of x will be (id number, date range, 4)
        # Predict y as the next day's [total,win,lose,draw], which is a vector of (id number,4)
        self.x_trn = x_trn
        self.y_trn = y_trn
        self.x_val = x_val
        self.y_val = y_val
        self.x_shape = self.x_trn.shape
        self.y_shape = self.y_trn.shape
        self.batch_size = self.y_shape[1]
        self.epoch = 1000
        self.lr = 0.001
        self.lr_decay = 0.9
        self.lstm1_node = 500
        self.lstm2_node = 250
        self.Dense1_node = 125
        self.Dense2_node = 25
        self.init_thres = 0.1
        self.time_window = time_step
        self.loss = objectives.mae
        self.optimizer = keras.optimizers.adam(lr=self.lr)
        self.train_size = int(self.x_shape[0] * 0.8)
        # Initialize model
        self.model = self.construct_model()

        # Files directory
        self.model_dir = '/model_results/'
        self.model_postfix = '_AP_tw_' + str(time_step) + '_batch_' + str(self.batch_size)
        self.model_file = self.model_dir + 'activity model' + self.model_postfix + '.h5'
        self.model_weights = self.model_dir + 'activity model_weights' + self.model_postfix + '.h5'
        self.model_json = self.model_dir + 'activity model' + self.model_postfix + '.json'

    def construct_model(self):
        model = Sequential()
        # LSTM layers
        model.add(
            LSTM(self.lstm1_node, batch_input_shape=(self.batch_size, self.time_window, self.y_shape[1]),
                 init='glorot_normal', return_sequences=True,
                 stateful=True),
        )
        # self.model.add(MaxPooling1D(2))
        model.add(
            LSTM(self.lstm2_node, init='glorot_normal', stateful=True))
        # Dense layers
        model.add(Dense(self.Dense1_node, init='glorot_normal', activation='tanh'))
        model.add(Dense(self.Dense2_node, init='glorot_normal', activation='sigmoid'))
        model.add(Dense(self.y_shape[1], init='glorot_normal', activation='relu'))

        model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])

        return model

    def train_case(self, contd=False):
        if contd:
            self.model.load_weights(self.model_file)

        # split the train and validation set
        x_trn, y_trn, x_val, y_val = self.x_trn, self.y_trn, self.x_val, self.y_val
        for ep in range(self.epoch):
            init_score = [0, 0]
            # Manual learning rate decay
            if ep % 100 == 0 and ep > 0:
                self.lr *= self.lr_decay
                self.model.compile(loss=self.loss, optimizer=self.optimizer,
                                   metrics=['accuracy'])
            for index in range(self.train_size):

                self.model.fit(x=x_trn, y=y_trn,
                               batch_size=self.batch_size,
                               nb_epoch=1, shuffle=False, verbose=0)
                score = self.model.evaluate(x=x_val, y=y_val,
                                            batch_size=self.batch_size, verbose=0)
                init_score[0] += score[0]
                init_score[1] += score[1]

                self.model.reset_states()
                if np.isnan(score[0]):
                    print("Model training failed! Loss becomes NaN!")
                    break

            self.save_model()  # Save model after each epoch to avoid crash
            init_score[0] /= self.train_size
            init_score[1] /= self.train_size
            print("Epoch %s/%s: average loss - %.4f average acc - %.4f%% learning rate - %.8f" %
                  (ep, self.epoch, init_score[0], init_score[1] * 100,
                   keras.backend.get_value(self.optimizer.lr)))
            if (ep == 0) and (init_score[1] * 100 < self.init_thres):
                print("Reinitialization...")
                self.construct_model()
                self.train_case()
                break
            if init_score[1] * 100 > self.init_thres:
                print(
                    "Activity prediction finished! Final average loss - %.4f acc - %.4f%%" % (
                        init_score[0], init_score[1] * 100))
                break

    def predict_case(self, x):
        winRate_prediction = []
        # Check shape, abandon predict if test & train shapes are different
        shape = np.asarray(x).shape
        assert shape[1] == self.x_shape[1] and shape[2] == self.x_shape[2]
        for index in range(len(x)):
            print("Testing trace: " + str(index))
            prediction = self.model.predict(x=x, batch_size=self.batch_size, verbose=0)
            self.model.reset_states()
            winRate_prediction.append(prediction)

        return winRate_prediction

    def save_model(self):
        self.model.save(self.model_file)
        model_json = self.model.to_json()
        with open(self.model_json, "w") as json_file:
            json_file.write(model_json)
        self.model.save_weights(self.model_weights)


if __name__ == "__main__":
    print("winRate prediction main")
