import datetime
import json
import time
from socket import timeout as timeoutError
from urllib import request, parse, error

import numpy as np
from pymysql import MySQLError

from apidatabase.db_connector import DatabaseConnector
from util import aux_functions
from util.ansi_code import AnsiEscapeCode as ansi
from util.read_config import ConfigFileReader

# account ID range
# if ($id <  500000000) return 'RU';
# elseif ($id < 1000000000) return 'EU';
# elseif ($id < 2000000000) return 'NA';
# elseif ($id < 3000000000) return 'ASIA';
# elseif ($id >= 3000000000) return 'KR';

DB_TYPE = 'mysql'
NA_ACCOUNT_LIMIT_LO = 1000000000
NA_ACCOUNT_LIMIT_HI = 2000000000
IDLIST_LIMIT = 100
SIZE_PER_WRITE = 100000
URL_REQ_DELAY = 10
URL_REQ_TIMEOUT = 45
URL_REQ_TRYNUM = 10
DATE_FORMAT = "%Y-%m-%d"
STATS_DICT = {"battles", "wins", "losses", "draws", "damage_dealt", "frags", "planes_killed", "xp",
              "capture_points", "dropped_capture_points", "survived_battles"}


class WowsAPIRequest(object):
    def __init__(self):
        # *************CRUCIAL PARAMETERS**************
        self._size_per_write = SIZE_PER_WRITE
        self._stats_dictionary = STATS_DICT
        self._request_delay = URL_REQ_DELAY
        self._account_id_upperbound = NA_ACCOUNT_LIMIT_HI
        self._account_id_lowerbound = NA_ACCOUNT_LIMIT_LO
        self._account_id_step = IDLIST_LIMIT
        self._date_format = DATE_FORMAT
        self._date = '2017-01-01'
        self._application_id, self._account_url, self._stats_by_date_url = ConfigFileReader().read_api_config()
        self._url_req_trynumber = URL_REQ_TRYNUM
        self._db_type = DB_TYPE
        self._db = DatabaseConnector(database_type=self._db_type)

        print("API initialized!")

    def request_all_ids(self, account_url, application_id):
        account_id = self._account_id_lowerbound
        requested_id_list = []
        while account_id < self._account_id_upperbound:
            id_list = self.list_to_url_params(self.generate_id_list_by_range(account_id))
            params = parse.urlencode({'application_id': application_id, 'account_id': id_list})
            url = account_url + '?' + params
            try:
                json_returned = json.loads(request.urlopen(url).read().decode("utf-8"))
                if json_returned["status"] == "ok":
                    requested_id_list = self.append_id_list(json_returned, requested_id_list)
                    account_id += self._account_id_step
                else:
                    print(json_returned["error"])
            except error.URLError:
                print("%sAPI request failed!!!%s" % (ansi.RED, ansi.ENDC))
                print("URL: %s, Error type: %s%s%s" % (url, ansi.RED, error.URLError, ansi.ENDC))
            if self.write_database(data_list=requested_id_list, type_detail=False):
                requested_id_list = []

    def request_stats_by_id(self, date):
        total_id_list = self.get_idlist(get_entire_list=True)
        total_count = len(total_id_list)
        count = 0
        sub_id_list = []
        result_list = []
        print("Task: Total request number to be executed: %s%d%s" % (
            ansi.BLUE, int(np.ceil(total_count / IDLIST_LIMIT)), ansi.ENDC))

        for ids in total_id_list:
            sub_id_list.append(ids[0])
            if len(sub_id_list) == IDLIST_LIMIT or total_count - count < IDLIST_LIMIT:
                result_list = self.request_and_store_stats(result_list=result_list, id_list=sub_id_list)
                sub_id_list = []
                count += IDLIST_LIMIT
                time.sleep(self._request_delay)
        print("Stats by id request finished!")

    def request_stats_by_date(self, date_list):
        total_idlist = self.get_idlist(get_entire_list=False)
        print("Task: Total request number to be executed: %s%d%s" % (
            ansi.BLUE, len(total_idlist), ansi.ENDC))

        result_list = []
        for id in total_idlist:
            result_list = self.request_and_store_stats(result_list=result_list, id_list=list(id), date_list=date_list)
            time.sleep(self._request_delay)
        print("Stats by date request finished!")

    def request_and_store_stats(self, result_list=list(), id_list=list(), date_list=list(),
                                url_timeout=URL_REQ_TIMEOUT):
        if not date_list:
            idlist = self.list_to_url_params(id_list)
            parameter = parse.urlencode({'application_id': self._application_id, 'account_id': idlist})
            main_url = self._account_url
        else:
            date_para = self.list_to_url_params(date_list)
            parameter = parse.urlencode(
                {'application_id': self._application_id, 'account_id': id_list[0], 'date_list': date_para})
            main_url = self._stats_by_date_url

        url = main_url + '?' + parameter
        numberOfTry = self._url_req_trynumber
        while numberOfTry > 0:
            try:
                json_returned = json.loads(request.urlopen(url, timeout=url_timeout).read().decode("utf-8"))
                while json_returned["status"] != "ok":
                    print("%s API error message: %s%s" % (ansi.RED, json_returned["error"], ansi.ENDC))
                    json_returned = json.loads(request.urlopen(url, timeout=url_timeout).read().decode("utf-8"))

                result_list = self.json_to_details(json_returned, result_list,
                                                   history=True if date_list else False)
                break
            except (error.URLError, timeoutError, ConnectionResetError) as e:  # API url request failed
                print("%sAPI request failed!%s %s" % (ansi.RED, e, ansi.ENDC))
                if e is timeoutError:
                    time.sleep(self._request_delay)
                numberOfTry -= 1
        if self.write_database(data_list=result_list):
            result_list = []
        return result_list

    def json_to_details(self, data, result_list, history=False):
        if data is not None and data["status"] == "ok":
            for acc_id in data["data"]:
                case = data["data"][acc_id]
                stats_dict = []
                if case is not None and history:
                    stats_dict = self.generate_dict_from_json_history(acc_id=acc_id, case=case)
                elif case is not None and not case["hidden_profile"]:
                    stats_dict = self.generate_dict_from_json_now(acc_id=acc_id, case=case)

                if stats_dict and stats_dict["battles"] != "0":  # Discard info of players who played no pvp game
                    result_list.append(stats_dict)
        elif data is not None and data["status"] != "ok":
            print("%s API error message: %s%s" % (ansi.RED, data["error"], ansi.ENDC))
        else:
            print("%sCannot convert JSON to detail!%s" % (ansi.RED, ansi.ENDC))  # print error message
        return result_list

    def generate_dict_from_json_history(self, acc_id, case):
        stats_dict = []
        if case["pvp"] is not None:
            pvp = case["pvp"]
            for date in pvp:
                stats = pvp[date]
                stats_dict = {'account_id': acc_id, 'date': date, "date": str(date)}
                for item in self._stats_dictionary:
                    stats_dict[item] = str(stats[item])
        return stats_dict

    def generate_dict_from_json_now(self, acc_id, case):
        nickname = case["nickname"]
        pvp = case["statistics"]["pvp"]
        stats_dict = {"date": str(self._date), "account_id": str(acc_id), "nickname": str(nickname)}
        for item in self._stats_dictionary:
            stats_dict[item] = str(pvp[item])
        return stats_dict

    def append_id_list(self, data, id_list):
        for account_id in data["data"]:
            if data["data"][account_id] is not None:
                nickname = data["data"][account_id]["nickname"]
                record = (str(account_id), str(nickname))
                id_list.append(record)
        return id_list

    def write_database(self, data_list, type_detail=True):
        success = False
        msg = "Start recording details..." if type_detail else "Start recording ids..."
        if len(data_list) >= self._size_per_write:
            try:
                print(msg)
                if type_detail:
                    self._db.write_detail(data_list)
                else:
                    self._db.write_accountid(data_list)
                success = True
            except MySQLError:
                self.print_database_error()

        return success

    def update_winrate(self, start=datetime.date.today(), end=datetime.date.today()):
        try:
            self._db.update_winrate(start=start, end=end)
        except MySQLError:
            self.print_database_error()

    def get_idlist(self, get_entire_list=True):
        idlist = list()
        try:
            print("Reading ID list...")
            idlist = self._db.get_idlist(get_entire_idlist=get_entire_list)
            print("%sID list read finished%s" % (ansi.GREEN, ansi.ENDC))
        except MySQLError:
            self.print_database_error()
        return idlist

    def generate_id_list_by_range(self, account_ID):
        ids = []
        for i in range(IDLIST_LIMIT):
            ids.append(int(account_ID + i))
        return ids

    def list_to_url_params(self, list):
        return ",".join(str(item) for item in list)

    def print_database_error(self):
        print("%sDatabase connection failed!!!%s" % (ansi.RED, ansi.ENDC))

    def single_day_request(self, date):
        timer_start = datetime.datetime.now()
        aux_functions.check_ip()
        self._date = date

        self.request_stats_by_id(date=date)
        # self.request_stats_by_date(date_list=list('2017-07-24'))
        self.update_winrate(start=date, end=date)

        time_usage = datetime.datetime.now() - timer_start
        print("\n%s%s%s data update finished, time usage: %s%s%s\n" % (
            ansi.BLUE, date.strftime(self._date_format), ansi.ENDC, ansi.DARKGREEN, time_usage,
            ansi.ENDC))
        return time_usage

    def main_request(self, start_date=None, days=7):
        # request all IDs, only need to execute once per (month, year) ?
        # request_all_ids(account_url, application_id)
        last_date = None
        start = datetime.date.today()
        if start_date is not None:
            d = datetime.datetime.strptime(start_date, self._date_format)
            start.replace(year=d.year, month=d.month, day=d.day)

        while days > 0:
            if start != last_date:
                last_date = start
                self.single_day_request(date=last_date)
                days -= 1
            else:
                time.sleep(1800)
            start = datetime.date.today()
        return "Main request finished!"


if __name__ == '__main__':
    result = WowsAPIRequest().main_request(start_date='2017-07-25')
    print(result)
