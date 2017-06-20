import datetime
import socket

import ipgetter

from util.ansi_code import ANSI_escode as tf


def check_ip():
    external_ip = ipgetter.myip()
    print("External ip:%s " % external_ip)
    local_ip = socket.gethostbyname(socket.gethostname())
    print("Local ip:%s " % local_ip)


def check_date():
    d = datetime.datetime.now().date()
    return d


def getcurrent_date():
    time = datetime.datetime.now().date()
    print(tf.DARKGREEN + str(time) + tf.ENDC)


if __name__ == "__main__":
    getcurrent_date()
