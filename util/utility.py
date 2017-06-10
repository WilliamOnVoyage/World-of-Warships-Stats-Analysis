import datetime
from util.ansi_code import ANSI_escode as tf


def getcurrent_date():
    time = datetime.datetime.now().date()
    print(tf.DARKGREEN + str(time) + tf.ENDC)


if __name__ == "__main__":
    getcurrent_date()
