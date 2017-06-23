import datetime
import json
import time
from urllib import request, parse, error

from pymysql import MySQLError as mysqlErr

from apidatabase.wows_db import wows_database
from util import read_config, utility
from util.ansi_code import ANSI_escode as ansi


# account ID range
# if ($id <  500000000) return 'RU';
# elseif ($id < 1000000000) return 'EU';
# elseif ($id < 2000000000) return 'NA';
# elseif ($id < 3000000000) return 'ASIA';
# elseif ($id >= 3000000000) return 'KR';




class wows_api_req(object):
    def __init__(self):
        self.size_per_write = 10000
        print("API initialized")

    def get_idlistfromsql(self, overwrite=True):
        try:
            db = wows_database()
            idlist = db.get_IDlist(overwrite=overwrite)
            db.close_db()
            return idlist
        except mysqlErr:
            print("Get ID list connection failed!")

    def create_idlist(self, account_ID):
        ids = []
        l = 100
        # account_ID /= 100
        for i in range(l):
            ids.append(int(account_ID + i))
        return ids, l

    def convertlisttopara(self, list_ids):
        s = ""
        for i in list_ids:
            if s != "":
                s += ","
            s += str(i)
        return s

    def update_winRate(self, date):
        try:
            db = wows_database()
            sql = """update wowstats.wows_stats set `winRate` = round(`win`/`total`,4) where `Date`=%s and `accountID`<>0 and `total` is not null;"""
            db.execute_single(query=sql, arg=str(date))
            print("%s%s%s winRate update %sfinished!%s" % (ansi.BLUE, str(date), ansi.ENDC, ansi.DARKGREEN, ansi.ENDC))
            db.close_db()
        except mysqlErr:
            print("%s%s%s winRate update %sfailed!%s" % (ansi.BLUE, str(date), ansi.ENDC, ansi.RED, ansi.ENDC))

    def request_statsbyID(self, account_url, application_id, date, overwrite=True):
        result_list = []
        total_idlist = self.get_idlistfromsql(overwrite=overwrite)
        total_count = len(total_idlist)
        count = 0
        sublist = []
        for ids in total_idlist:
            sublist.append(ids[0])
            if len(sublist) == 100 or total_count - count < 100:
                idlist = self.convertlisttopara(sublist)
                parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist})
                url = account_url + '?' + parameter
                n_try = 10
                while n_try > 0:
                    try:
                        result = request.urlopen(url).read().decode("utf-8")
                        data = json.loads(result)
                        while data["status"] != "ok":  # keep requesting until get ok
                            result = request.urlopen(url).read().decode("utf-8")
                            data = json.loads(result)
                        result_list = self.record_detail(date, data, result_list)
                        sublist = []
                        count += 100
                    except error.URLError:  # API url request failed
                        print("%sAPI request failed!%s" % (ansi.RED, ansi.ENDC))
                        print("URL: %s, Error type: %s%s%s" % (url, ansi.RED, error.URLError, ansi.ENDC))
                        continue
                    break

    def request_allID(self, account_url, application_id):
        account_ID = 1000000000
        result_list = []

        while account_ID < 2000000000:
            idlist, increment = self.create_idlist(account_ID)
            idlist = self.convertlisttopara(idlist)
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
                print("Last account id: ", result_list[self.size_per_write - 1][0])
            except mysqlErr:
                print("%sDatabase connection failed!%s" % (ansi.RED, ansi.ENDC))
            result_list = []
        return result_list

    def record_detail(self, date, data, result_list):
        if data["status"] == "ok":
            for acc_id in data["data"]:
                case = data["data"][acc_id]
                if case is not None:
                    if not case["hidden_profile"]:
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
                            # else:
                            # print("User %s data private" % acc_id)
        else:
            print(data["error"])  # print error message
        if len(result_list) >= self.size_per_write:  # write when data has 100 records
            try:
                db = wows_database()
                db.write_detail(result_list)
                db.close_db()
            except mysqlErr:
                print("Database connection failed!")
            result_list = []
        return result_list

    def api_main(self, days=7):
        # Request params from config file
        cg = read_config.config()
        config_data = json.loads(cg.read_config())
        application_id = config_data['wows_api']['application_id']
        account_url = config_data['wows_api']['account_url']
        player_url = config_data['wows_api']['player_url']
        utility.check_ip()

        # request_allID(account_url, application_id)
        day_count = days
        last_date = None
        while day_count != 0:
            start = datetime.datetime.now()
            if start.date() != last_date:
                last_date = start.date()
                self.request_statsbyID(account_url=account_url, application_id=application_id, date=last_date,
                                       overwrite=True)
                self.update_winRate(date=last_date)
                # date = datetime.datetime.now().date()
                end = datetime.datetime.now()
                day_count -= 1
                print("\n%s%s%s data update finished, time usage: %s%s%s\n" % (
                    ansi.BLUE, start.date().strftime("%y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, end - start,
                    ansi.ENDC))
            else:
                time.sleep(1800)  # wait 30 mins for next check
        return "Main request finished!"


if __name__ == '__main__':
    result = wows_api_req().api_main()
    print(result)
