import keras
import numpy as np
from keras import objectives
from keras.layers import Dense, LSTM
from keras.models import Sequential


class winRate_model(object):
    def __init__(self, x, y, time_step):
        # Suppose x = (id,date,[total,win,lose,draw]), the shape of x will be (id number, date range, 4)
        # Predict y as the next day's [total,win,lose,draw], which is a vector of (id number,4)
        self.X = x
        self.Y = y
        self.y_shape = np.asarray(self.Y).shape
        self.batch_size = self.y_shape[1]
        self.lr = 0.001
        self.lr_decay = 0.9
        self.lstm1_node = 500
        self.lstm2_node = 250
        self.Dense1_node = 125
        self.Dense2_node = 25
        self.time_window = time_step
        self.loss = objectives.mae
        self.model = self.construct_model()

        # Files directory
        self.model_dir = 'model_results/'
        self.model_postfix = '_AP_tw_' + str(time_step) + '_batch_' + str(self.batch_size)
        self.model_file = self.model_dir + 'activity model' + self.model_postfix + '.h5'
        self.model_weights = self.model_dir + 'activity model_weights' + self.model_postfix + '.h5'
        self.model_json = self.model_dir + 'activity model' + self.model_postfix + '.json'

    def construct_model(self):
        model = Sequential()
        # LSTM layers
        model.add(
            LSTM(self.lstm1_node, batch_input_shape=(self.batch_size, self.time_window, self.y_shape[1]),
                 init='glorot_normal',
                 stateful=True),
        )
        # self.model.add(MaxPooling1D(2))
        model.add(
            LSTM(self.lstm2_node, init='glorot_normal', stateful=True))
        # Dense layers
        model.add(Dense(self.Dense1_node, init='glorot_normal', activation='tanh'))
        model.add(Dense(self.Dense2_node, init='glorot_normal', activation='sigmoid'))
        model.add(Dense(self.y_shape[1], init='glorot_normal', activation='softmax'))  # output value 0~1
        # Decision making layer
        # self.model.add(
        #     decisionLayer(self.label_row, init='uniform'))  # add this layer if output is vector
        # Optimization
        optimizer_ = keras.optimizers.adam(lr=self.lr)
        model.compile(loss=self.loss, optimizer=optimizer_, metrics=['accuracy'])

        return model

    def train_case(self, contd=False):
        if contd:
            self.model.load_weights(self.model_file)

        for ep in range(epoch):
            init_score = [0, 0]
            if ep % 100 == 0 and ep > 0:
                self.ac_optimizer_.lr *= self.lr_decay
                self.ac_model.compile(loss=self.ac_loss, optimizer=self.ac_optimizer_,
                                      metrics=['accuracy'])
            for index in range(self.train_size):
                x_train, y_train = util.data_io.subsampling_activity(X=self.X[index], Y=self.Y[index],
                                                                     x_time_w=self.time_window, y_time_w=1)

                predictions = self.phase_model.predict(x=x_train, batch_size=self.batch_size)
                predictions = self.extendPrediction(predictions, 1)
                x_train = np.concatenate((predictions, x_train.astype(np.float)), axis=2)
                x_train = [x_train] * self.phase_label_dim
                self.ac_model.fit(x=x_train, y=y_train,
                                  batch_size=self.batch_size,
                                  nb_epoch=1, shuffle=False, verbose=0)
                score = self.ac_model.evaluate(x=x_train, y=y_train,
                                               batch_size=self.batch_size, verbose=0)
                init_score[0] += score[0]
                init_score[1] += score[1]

                self.ac_model.reset_states()
                self.phase_model.reset_states()
                if (np.isnan(score[0])):
                    print('Model training failed! Loss becomes NaN!')
                    break

            self.save_acModel()  # Save model after each epoch to avoid crash
            init_score[0] /= self.train_size
            init_score[1] /= self.train_size
            print('Epoch %s/%s: average loss - %.4f average acc - %.4f%% learning rate - %.8f' %
                  (ep, epoch, init_score[0], init_score[1] * 100, keras.backend.get_value(self.phase_optimizer_.lr)))
            if (ep == 0) and (init_score[1] * 100 < activity_init_thres):
                print('Reinitialization...')
                self.construct_ac_model()
                self.train_case()
                break
            if init_score[1] * 100 > activity_final_thres:
                print(
                    "Activity prediction finished! Final average loss - %.4f acc - %.4f%%" % (
                        init_score[0], init_score[1] * 100))
                break
