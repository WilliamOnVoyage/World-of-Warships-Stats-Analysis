import random
from datetime import timedelta

import numpy as np
from pandas import DataFrame, Panel
from pymysql import MySQLError as mysqlErr

import apidatabase.wows_db as wows_db
import util.utility as ut


def db_retrieve(last_day, timewindow=8, id_column=1, date_column=0, nickname=2, public=3,
                stat_columns=np.array([4, 5, 6, 7])):
    try:
        day_dict = {}
        day_str = "day "
        day_columns = ['total', 'win', 'loss', 'draw']

        data_frames = []
        db = wows_db.wows_database()
        # Convert the cases from database into tuple like [case,[total,win,loss,draw]], erase date, nickname and public information
        i = 0
        count = timewindow
        while count > 0:
            data = np.asarray(
                db.get_statsbyDate(para=[last_day - timedelta(i), 100]))  # filter total>100, ~300k per day
            if data.any():
                ids = data[:, id_column]
                stats = data[:, stat_columns]
                single_frame = DataFrame(data=stats, index=ids, columns=day_columns)
                for d in day_columns:
                    if d != day_columns[0]:
                        single_frame[d] = single_frame[d] / (
                            single_frame[day_columns[0]] + 0.001)  # plus 0.001 to avoid all 0s from database
                single_frame[day_columns[0]] = 1
                day_dict[day_str + str(count + 1)] = single_frame
                count -= 1
            i += 1
        db.close_db()
        result = Panel(day_dict)
        return result
    except mysqlErr:
        print("Get ID list connection failed!")
        return None


# This function requires the items in data be consistent (same major index values)
def convert_train_vali(data, y_column=1, r=0.8, shuffle=False):
    last_day = data.shape[0] - y_column

    max_subsize = ut.max_hundred(data.shape[1])
    discard_index = np.asarray(random.sample(range(data.shape[1]), data.shape[1] - max_subsize))
    filter_dict = {}
    for d in data.keys():
        labels = data[d].axes[0][discard_index]
        filter_dict[d] = data[d].drop(labels)
    data = Panel(filter_dict)

    # Sample by major index (ids)
    rd_index = np.asarray(random.sample(range(data.shape[1]), int(r * data.shape[1])))
    trn_dict = {}
    val_dict = {}

    for d in data.keys():
        labels = data[d].axes[0][rd_index]
        trn_dict[d] = data[d].loc[labels, :]
        val_dict[d] = data[d].drop(labels)

    data_trn = Panel(trn_dict)
    data_val = Panel(val_dict)
    # Select items
    x_trn = data_trn[0:last_day].swapaxes(0, 1)
    x_val = data_val[0:last_day].swapaxes(0, 1)
    y_trn = data_trn[last_day:data.shape[0]].swapaxes(0, 1)
    y_val = data_val[last_day:data.shape[0]].swapaxes(0, 1)
    return x_trn, y_trn, x_val, y_val


def test():
    data = DataFrame(columns=['t', 'w', 'l', 'd'])
    print(data)

    columns = {'d1': data, 'd2': data, 'd3': data, 'd4': data}
    pd = Panel(columns)
    pd['d2'].loc[1000, ['t', 'w', 'l', 'd']] = [3, 3, 3, 3]
    pd['d2'].loc[1001, 't'] = 3.5
    pd['d2'].loc[1002, 't'] = 4

    print(pd)
    droped = pd['d2'].drop(1001)
    print(droped)


if __name__ == "__main__":
    test()
    # date = date.today()
    # data = db_retrieve(last_day=date)
    # # x, y = convert_train_vali(data)
    # print(data)