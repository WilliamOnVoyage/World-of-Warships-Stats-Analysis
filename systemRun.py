import datetime
import json
import time

import api_database.wows_api as wows_api
import model.winRate_dataprocess as winR_data
import util.read_config as read_config
from model.winRate_prediction import winRate_model as winR_model
from util.ansi_code import ANSI_escode as ansi


def database_update(date):
    # Request params from config file
    cg = read_config.config()
    config_data = json.loads(cg.read_config())
    application_id = config_data['wows_api']['application_id']
    account_url = config_data['wows_api']['account_url']
    player_url = config_data['wows_api']['player_url']
    wows_api.check_ip()

    wows_api.request_statsbyID(account_url, application_id, date, overwrite=True)
    wows_api.update_winRate(date)


def model_update(date):
    timewindow = 7
    x, y = winR_data.db_retrieve(date)
    model = winR_model(x=x, y=y, time_step=timewindow)


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
                ansi.BLUE, last_date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, db_time, ansi.ENDC))

            start = datetime.datetime.now()
            model_update(date=last_date)
            end = datetime.datetime.now()
            model_time = end - start
            print("\n%s%s%s model update finished, time usage: %s%s%s\n" % (
                ansi.BLUE, last_date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, model_time, ansi.ENDC))

            print("\n%s%s%s function finished, total time usage: %s%s%s\n" % (
                ansi.BLUE, last_date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, db_time + model_time, ansi.ENDC))
            day_count -= 1
        else:
            time.sleep(1800)  # wait 30 mins for next check
    return "Main function finished!"


if __name__ == '__main__':
    result = main()
    print(result)
