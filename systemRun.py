import datetime
import json
import time

import api_database.wows_api as wows
import model.winRate_dataprocess as winR_data
import util.read_config as read_config
from model.winRate_prediction import winRate_model as winR_model
from util import utility
from util.ansi_code import ANSI_escode as ansi


def database_update(date):
    # Request params from config file
    cg = read_config.config()
    config_data = json.loads(cg.read_config())
    application_id = config_data['wows_api']['application_id']
    account_url = config_data['wows_api']['account_url']
    player_url = config_data['wows_api']['player_url']
    utility.check_ip()
    wows_api = wows.wows_api()
    wows_api.request_statsbyID(account_url, application_id, date, overwrite=True)
    wows_api.update_winRate(date)


def model_update(date):
    timewindow = 2
    # retrieve 8 days data, last day is the y_trn and previous 7 days are the x_trn
    # Data in pandas.DataFrame format
    data = winR_data.db_retrieve(last_day=date, timewindow=timewindow)
    x_trn, y_trn, x_val, y_val = winR_data.convert_train_vali(data=data)
    # initialize model
    # x = [[1, 2, 3, 4]]
    # y = [[1, 2, 3, 4]]

    model = winR_model(x_trn=x_trn, y_trn=y_trn, x_val=x_val, y_val=y_val, time_step=timewindow)
    model.train_case(contd=False)


def main(days=7):
    day_count = days
    last_date = None
    while day_count != 0:
        start = datetime.datetime.now()
        if start.date() != last_date:
            last_date = start.date()
            database_update(date=last_date)
            end = datetime.datetime.now()

            db_time = end - start
            print("\n%s%s%s data update finished, time usage: %s%s%s\n" % (
                ansi.BLUE, last_date.strftime("%y_trn-%m-%d"), ansi.ENDC, ansi.DARKGREEN, db_time, ansi.ENDC))

            start = datetime.datetime.now()
            model_update(date=last_date)
            end = datetime.datetime.now()
            model_time = end - start
            print("\n%s%s%s model update finished, time usage: %s%s%s\n" % (
                ansi.BLUE, last_date.strftime("%y_trn-%m-%d"), ansi.ENDC, ansi.DARKGREEN, model_time, ansi.ENDC))

            print("\n%s%s%s function finished, total time usage: %s%s%s\n" % (
                ansi.BLUE, last_date.strftime("%y_trn-%m-%d"), ansi.ENDC, ansi.DARKGREEN, db_time + model_time,
                ansi.ENDC))
            day_count -= 1
        else:
            time.sleep(1800)  # wait 30 mins for next check
    return "Main function finished!"


if __name__ == '__main__':
    # result = main()
    # print(result)

    model_update(date=datetime.date.today())
