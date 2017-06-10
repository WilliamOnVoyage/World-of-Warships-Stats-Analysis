import json
import socket
import datetime
import time
import ipgetter

from util import read_config
from WOWS.WOWS_RDS import wows_database
from urllib import request, parse, error
from pymysql import MySQLError as mysqlErr
from util.ansi_code import ANSI_escode as ansi

# account ID range
# if ($id <  500000000) return 'RU';
# elseif ($id < 1000000000) return 'EU';
# elseif ($id < 2000000000) return 'NA';
# elseif ($id < 3000000000) return 'ASIA';
# elseif ($id >= 3000000000) return 'KR';

size_per_write = 10000


def check_ip():
    external_ip = ipgetter.myip()
    print("External ip:%s " % external_ip)
    local_ip = socket.gethostbyname(socket.gethostname())
    print("Local ip:%s " % local_ip)


def check_date():
    d = datetime.datetime.now().date()
    return d


def get_idlistfromsql(overwrite=True):
    try:
        db = wows_database()
        idlist = db.get_IDlist(overwrite=overwrite)
        db.close_db()
        return idlist
    except mysqlErr:
        print("Get ID list connection failed!")


def create_idlist(account_ID):
    ids = []
    l = 100
    # account_ID /= 100
    for i in range(l):
        ids.append(int(account_ID + i))
    return ids, l


def convertlisttopara(list_ids):
    s = ""
    for i in list_ids:
        if s != "":
            s += ","
        s += str(i)
    return s


def update_winRate(date):
    try:
        db = wows_database()
        sql = """update wowstats.wows_stats set `winRate` = round(`win`/`total`,4) where `Date`=%s and `accountID`<>0 and `total` is not null;"""
        db.execute_single(query=sql, arg=str(date))
        print("%s%s%s winRate update %sfinished!" % (ansi.BLUE, str(date), ansi.ENDC, ansi.DARKGREEN))
        db.close_db()
    except mysqlErr:
        print("%s%s%s winRate update %sfailed!" % (ansi.BLUE, str(date), ansi.ENDC, ansi.RED))


def request_statsbyID(account_url, application_id, date, overwrite=True):
    result_list = []
    idlist = get_idlistfromsql(overwrite=overwrite)
    sublist = []
    for ids in idlist:
        sublist.append(ids[0])
        if len(sublist) == 100:
            idlist = convertlisttopara(sublist)
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
                    result_list = record_detail(date, data, result_list)
                    sublist = []
                except error.URLError:  # API url request failed
                    print("API request failed!")
                    print(error.URLError)
                    continue
                break


def request_allID(account_url, application_id):
    account_ID = 1000000000
    result_list = []

    while account_ID < 2000000000:
        idlist, increment = create_idlist(account_ID)
        idlist = convertlisttopara(idlist)
        parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist})
        url = account_url + '?' + parameter
        try:
            result = request.urlopen(url).read().decode("utf-8")
            # print(result)
            data = json.loads(result)
            if data["status"] == "ok":
                result_list = record_ID(data, result_list)
                account_ID += increment
            else:
                print(data["error"])  # print error message
        except error.URLError:  # API url request failed
            print("API request failed!")
            print(error.URLError)
            continue


def record_ID(data, result_list):
    for acc_id in data["data"]:
        if data["data"][acc_id] is not None:
            nickname = data["data"][acc_id]["nickname"]
            record = (str(acc_id), str(nickname))
            result_list.append(record)
    if len(result_list) >= size_per_write:  # write when data has certain size
        try:
            db = wows_database()
            db.write_ID(result_list)
            db.close_db()
            print("Last account id: ", result_list[size_per_write - 1][0])
        except mysqlErr:
            print("Database connection failed!")
        result_list = []
    return result_list


def record_detail(date, data, result_list):
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
                    record = (
                        str(date), str(acc_id), str(nickname), str(public), str(total), str(win), str(defeat),
                        str(draw))
                    result_list.append(record)
                    # else:
                    # print("User %s data private" % acc_id)
    else:
        print(data["error"])  # print error message
    if len(result_list) >= size_per_write:  # write when data has 100 records
        try:
            db = wows_database()
            db.write_detail(result_list)
            db.close_db()
        except mysqlErr:
            print("Database connection failed!")
        result_list = []
    return result_list


def request_main(days=7):
    # Request params from config file
    cg = read_config.config()
    config_data = json.loads(cg.read_config())
    application_id = config_data['wows_api']['application_id']
    account_url = config_data['wows_api']['account_url']
    player_url = config_data['wows_api']['player_url']
    check_ip()

    # request_allID(account_url, application_id)
    day_count = days
    last_date = None
    while day_count != 0:
        start = datetime.datetime.now()
        if start.date() != last_date:
            last_date = start.date()
            request_statsbyID(account_url, application_id, last_date, overwrite=True)
            update_winRate(last_date)
            # date = datetime.datetime.now().date()
            end = datetime.datetime.now()
            day_count -= 1
            print("%s%s%s data update finished, time usage: %s%s%s" % (
                ansi.BLUE, start.date().strftime("%Y-%m-%d"), ansi.ENDC, ansi.DARKGREEN, end - start, ansi.ENDC))
        else:
            time.sleep(1800)  # wait 30 mins for next check
    return "Main request finished!"


if __name__ == '__main__':
    result = request_main()
    print(result)
