import random
from datetime import timedelta

import numpy as np
from pandas import DataFrame, Panel
from pymysql import MySQLError as mysqlErr

from wows_stats import util as ut
from wows_stats.database.database_factory import database_factory


def get_from_db(last_day, timewindow=8, id_column=1, stat_columns=np.array([4, 5, 6, 7])):
    try:
        day_dict = {}
        day_str = "date "
        day_columns = ['battles', 'wins', 'losses', 'draws']
        db = database_factory(db_type='mongodb')
        # Convert the cases from database into tuple like [case,[total,win,loss,draw]],
        # erase date, nickname and public information
        i = 0
        count = timewindow
        while count > 0:
            data = np.asarray(
                db.get_stats_by_date_as_array(args=[last_day - timedelta(i), '100']))  # filter total>100, ~300k per day
            if data.any():
                ids = data[:, id_column]
                stats = data[:, stat_columns]
                single_frame = DataFrame(data=stats, index=ids, columns=day_columns)
                for d in day_columns:
                    if d != day_columns[0]:
                        single_frame[d] /= single_frame[
                                               day_columns[0]] + 0.001  # plus 0.001 to avoid all 0s from database
                single_frame[day_columns[0]] = 1
                day_dict[day_str + str(count + 1)] = single_frame
                count -= 1
            i += 1
        result = Panel(day_dict)
        return result
    except mysqlErr:
        print("Get ID list connection failed!")
        return None


# This function requires the items in data be consistent (same major index values)
def split_train_validation(data, y_column=1, train_ratio=0.8, shuffle=False):
    last_day = data.shape[0] - y_column

    max_subsize = ut.max_hundred(data.shape[1])
    discard_index = np.asarray(random.sample(range(data.shape[1]), data.shape[1] - max_subsize))
    filter_dict = {}
    for d in data.keys():
        labels = data[d].axes[0][discard_index]
        filter_dict[d] = data[d].drop(labels)
    data = Panel(filter_dict)

    # Sample by major index (ids)
    rd_index = np.asarray(random.sample(range(data.shape[1]), int(train_ratio * data.shape[1])))
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
