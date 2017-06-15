import datetime

from pymysql import MySQLError as mysqlErr

import api_database.wows_DB as wows_db


def db_retrieve(date):
    try:
        db = wows_db.wows_database()
        stats = db.get_statsbyDate(date=date)
        db.close_db()
        return stats
    except mysqlErr:
        print("Get ID list connection failed!")
        return None


def convert_train(data, time_window=1):
    x = []
    y = []
    return x, y


def convert_test(data):
    x = []
    return x


if __name__ == "__main__":
    data = db_retrieve(datetime.datetime.now().date())
    print(data)
