import datetime
import time

import apidatabase.wows_api as wows
import model.data_preprocess as winR_data
from model.winrate_prediction import WinrateModel as winR_model
from util.ansi_code import AnsiEscapeCode as ansi


def database_update(date):
    # Request params from config file
    timing = wows.WowsAPIRequest().single_day_request(date=date)
    return timing


def model_update(date):
    start = datetime.datetime.now()
    last_date = start.date()
    timewindow = 8
    # retrieve 8 days data, last day is the y_trn and previous 7 days are the x_trn
    # Data in pandas.Panel format
    data = winR_data.db_retrieve(last_day=date, timewindow=timewindow)
    x_trn, y_trn, x_val, y_val = winR_data.convert_train_vali(data=data)
    # initialize model
    model = winR_model(x_trn=x_trn, y_trn=y_trn, x_val=x_val, y_val=y_val, time_step=timewindow - 1)
    model.train_case(contd=False)
    end = datetime.datetime.now()
    model_time = end - start
    print("\n%s%s%s model update finished, time usage: %s%s%s\n" % (
        ansi.BLUE, date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, model_time, ansi.ENDC))
    return model_time


def systemRun(days=7):
    day_count = days
    last_date = None
    while day_count != 0:
        start = datetime.datetime.now()
        if start.date() != last_date:
            db_time = datetime.timedelta(0)
            model_time = datetime.timedelta(0)
            last_date = start.date()
            db_time = database_update(date=last_date)
            # model_time = model_update(date=last_date)
            print("\n%s%s%s function finished, total time usage: %s%s%s\n" % (
                ansi.BLUE, last_date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, db_time + model_time,
                ansi.ENDC))
            day_count -= 1
        else:
            time.sleep(1800)  # wait 30 mins for next check
    return "Main function finished!"


if __name__ == '__main__':
    systemRun()
    # lastday = datetime.date.today()
    # database_update(date=lastday)
    # model_update(date=lastday)
