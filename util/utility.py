import datetime
import socket

import ipgetter
import math

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


def max_hundred(x):
    return int(x / 100) * 100


def lca(x, y):
    negate = False
    if (x > 0 and y < 0) or (x < 0 and y > 0):
        negate = True
    x = abs(x)
    y = abs(y)
    if x == 0 or y == 0:
        return 0
    if x == y:
        return x
    if x > y:
        if x % y == 0:
            r = y
        else:
            r = lca(x - y, y)
    else:
        if y % x == 0:
            r = x
        else:
            r = lca(y - x, x)
    if negate:
        r = -r
    return r


def factor(x, y, limit=1000):
    f = lca(x, y)
    factor = 1
    for i in range(1, min(int(math.sqrt(f)), limit) + 1):
        if f % i == 0:
            factor = i
    return factor


if __name__ == "__main__":
    x = lca(288, 108)
    print(x)
    print(factors)
    getcurrent_date()
