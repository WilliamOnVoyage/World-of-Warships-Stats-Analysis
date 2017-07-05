import datetime
import json
import time
from socket import timeout as timeoutError
from urllib import request, parse, error

import numpy as np
from pymysql import MySQLError as mysqlErr

from apidatabase.wows_db import wows_database
from util import utility
from util.ansi_code import ANSI_escode as ansi
from util.read_config import config

# account ID range
# if ($id <  500000000) return 'RU';
# elseif ($id < 1000000000) return 'EU';
# elseif ($id < 2000000000) return 'NA';
# elseif ($id < 3000000000) return 'ASIA';
# elseif ($id >= 3000000000) return 'KR';
NA_lo = 1000000000
NA_hi = 2000000000
ACCOUNT_ID_LIMIT = 100
SIZE_PER_WRITE = 10000


class wows_api_req(object):
    def __init__(self):
        # *************CRUCIAL PARAMETERS**************
        self.size_per_write = SIZE_PER_WRITE
        self.request_delay = 10  # delay 10 seconds between requests
        print("API initialized")

    def request_allID(self, account_url, application_id):
        account_ID = NA_lo  # NA limit
        result_list = []
        while account_ID < NA_hi:  # NA limit
            idlist, increment = self.create_idlist(account_ID)
            idlist = self.list2param(idlist)
            parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist})
            url = account_url + '?' + parameter
            try:
                result = request.urlopen(url).read().decode("utf-8")
                # print(result)
                data = json.loads(result)
                if data["status"] == "ok":
                    result_list = self.record_ID(data, result_list)
                    account_ID += increment
                else:
                    print(data["error"])  # print error message
            except error.URLError:  # API url request failed
                print("%sAPI request failed!%s" % (ansi.RED, ansi.ENDC))
                print("URL: %s, Error type: %s%s%s" % (url, ansi.RED, error.URLError, ansi.ENDC))
                continue

    def request_statsbyID(self, account_url, application_id, date, overwrite=True):
        total_idlist = self.idlist_sql(overwrite=overwrite)
        total_count = len(total_idlist)
        count = 0
        sublist = []
        result_list = []
        url_timeout = 60
        print("Task: Total request number to be executed: %s%d%s" % (
            ansi.BLUE, int(np.ceil(total_count / ACCOUNT_ID_LIMIT)), ansi.ENDC))
        start_time = datetime.datetime.now()
        for ids in total_idlist:
            sublist.append(ids[0])
            if len(sublist) == ACCOUNT_ID_LIMIT or total_count - count < ACCOUNT_ID_LIMIT:
                idlist = self.list2param(sublist)
                parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist})
                url = account_url + '?' + parameter
                data = []
                n_try = 10
                while n_try > 0:
                    try:
                        print("Sending request %s%d%s... ETA: %s%s%s" % (
                            ansi.BLUE, count / ACCOUNT_ID_LIMIT + 1, ansi.ENDC, ansi.BLUE,
                            (datetime.datetime.now() - start_time) / (count / ACCOUNT_ID_LIMIT + 1) * (
                                int(np.ceil(total_count / ACCOUNT_ID_LIMIT)) - (count / ACCOUNT_ID_LIMIT + 1)),
                            ansi.ENDC))

                        api_back = request.urlopen(url, timeout=url_timeout).read().decode("utf-8")
                        # print(api_back)
                        data = json.loads(api_back)
                        # while data["status"] != "ok":  # keep requesting until get ok
                        #     api_back = request.urlopen(url, timeout=url_timeout).read().decode("utf-8")
                        #     data = json.loads(api_back)
                        # break
                    except (error.URLError, timeoutError) as e:  # API url request failed
                        print("%sAPI request failed!%s %s" % (ansi.RED, e, ansi.ENDC))
                        if e is timeoutError:  # Request limit exceeds, wait for 10s
                            time.sleep(self.request_delay)
                        n_try -= 1
                result_list = self.json2detail(date, data, result_list)
                # print("result_list length: %d" % (len(result_list)))
                if self.record_detail(result_list):
                    result_list = []
                sublist = []
                count += ACCOUNT_ID_LIMIT
                time.sleep(self.request_delay)
        print("Stats request finished!")

    def json2detail(self, date, data, result_list):
        if data is not None and data["status"] == "ok":
            for acc_id in data["data"]:
                case = data["data"][acc_id]
                if case is not None and not case["hidden_profile"]:
                    nickname = case["nickname"]
                    pvp = case["statistics"]["pvp"]
                    total = pvp["battles"]
                    win = pvp["wins"]
                    defeat = pvp["losses"]
                    draw = pvp["draws"]
                    public = 1
                    if total > 0:  # Discard info of players who played no pvp game
                        record = (
                            str(date), str(acc_id), str(nickname), str(public), str(total), str(win), str(defeat),
                            str(draw))
                        result_list.append(record)
        elif data is not None and data["status"] != "ok":
            print("%s API error message: %s%s" % (ansi.RED, data["error"], ansi.ENDC))
        else:
            print("%sCannot convert JSON to detail!%s" % (ansi.RED, ansi.ENDC))  # print error message
        return result_list

    def record_ID(self, data, result_list):
        for acc_id in data["data"]:
            if data["data"][acc_id] is not None:
                nickname = data["data"][acc_id]["nickname"]
                record = (str(acc_id), str(nickname))
                result_list.append(record)
        if len(result_list) >= self.size_per_write:  # write when data has certain size
            try:
                db = wows_database()
                db.write_ID(result_list)
                db.close_db()
                print("Last account id: ", result_list[len(result_list) - 1][0])
                result_list = []
            except mysqlErr:
                print("%sDatabase connection failed!%s" % (ansi.RED, ansi.ENDC))
        return result_list

    def record_detail(self, result_list):
        success = False
        if len(result_list) >= self.size_per_write:  # write data
            try:
                print("Start writing database")
                db = wows_database()
                db.write_detail(result_list)
                db.close_db()
                success = True
            except mysqlErr:
                print("%sDatabase connection failed!%s" % (ansi.RED, ansi.ENDC))
        return success

    def update_winrate(self, date):
        try:
            db = wows_database()
            sql = """update wowstats.wows_stats set `winRate` = round(`win`/`total`,4) where `Date`=%s and `accountID`<>0 and `total` is not null;"""
            db.execute_single(query=sql, arg=str(date))
            print("%s%s%s winRate update %sfinished!%s" % (ansi.BLUE, str(date), ansi.ENDC, ansi.DARKGREEN, ansi.ENDC))
            db.close_db()
        except mysqlErr:
            print("%s%s%s winRate update %sfailed!%s" % (ansi.BLUE, str(date), ansi.ENDC, ansi.RED, ansi.ENDC))

    def update_prevwinrate(self, start=datetime.date.today(), end=datetime.date.today()):
        try:
            db = wows_database()
            sql = """update wowstats.wows_stats set `winRate` = round(`win`/`total`,4) where `Date`>%s and `Date`<=%s and `accountID`<>0 and `total` is not null;"""
            db.execute_single(query=sql, arg=[str(start), str(end)])
            print("%s%s%s winRate update %sfinished!%s" % (ansi.BLUE, str(end), ansi.ENDC, ansi.DARKGREEN, ansi.ENDC))
            db.close_db()
        except mysqlErr:
            print("%s%s%s winRate update %sfailed!%s" % (ansi.BLUE, str(end), ansi.ENDC, ansi.RED, ansi.ENDC))

    def idlist_sql(self, overwrite=True):
        try:
            print("Reading ID list...")
            db = wows_database()
            idlist = db.get_IDlist(overwrite=overwrite)
            db.close_db()
            print("%sID list read finished%s" % (ansi.GREEN, ansi.ENDC))
            return idlist
        except mysqlErr:
            print("Get ID list connection failed!")

    def create_idlist(self, account_ID):
        ids = []
        l = ACCOUNT_ID_LIMIT
        # account_ID /= 100
        for i in range(l):
            ids.append(int(account_ID + i))
        return ids, l

    def list2param(self, list_ids):
        s = ""
        for i in list_ids:
            if s != "":
                s += ","
            s += str(i)
        return s

    # *****************MAJOR API FUNCTIONS****************
    def api_singleDay(self, date):
        timer_start = datetime.datetime.now()

        # Request params from config file
        config_data = json.loads(config().read_config())
        application_id = config_data['wows_api']['application_id']
        account_url = config_data['wows_api']['account_url']
        utility.check_ip()

        # main api request
        self.request_statsbyID(account_url=account_url, application_id=application_id, date=date,
                               overwrite=True)
        self.update_winrate(date=date)

        timing = datetime.datetime.now() - timer_start
        print("\n%s%s%s data update finished, time usage: %s%s%s\n" % (
            ansi.BLUE, date.strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, timing,
            ansi.ENDC))
        return timing

    def api_main(self, start_date=None, days=7):
        # request all IDs, only need to execute once per (month, year) ?
        # request_allID(account_url, application_id)
        # initialize date counter
        last_date = None
        start = datetime.date.today()
        if start_date is not None:
            d = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            start.replace(year=d.year, month=d.month, day=d.day)

        while days != 0:
            if start != last_date:
                # update
                last_date = start
                self.api_singleDay(date=last_date)
                days -= 1
            else:
                time.sleep(1800)  # wait 30 mins for next check
            start = datetime.date.today()
        return "Main request finished!"


if __name__ == '__main__':
    result = wows_api_req().api_main(start_date='2017-07-03')
    print(result)
