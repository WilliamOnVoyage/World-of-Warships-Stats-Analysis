import json
import socket
import datetime
import time
import ipgetter
from WOWS.WOWS_RDS import mysql
from urllib import request, parse, error

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
        db = mysql()
        idlist = db.get_IDlist(overwrite=overwrite)
        db.close_db()
        return idlist
    except ConnectionError:
        print("Get ID list connection failed!")


def create_idlist(account_ID):
    id = []
    Length = 100
    # account_ID /= 100
    for i in range(Length):
        id.append(int(account_ID + i))
    return id, Length


def convertlisttopara(list):
    s = ""
    for i in list:
        if s != "":
            s += ","
        s += str(i)
    return s


def update_winRate(date):
    try:
        db = mysql()
        sql = """update wowstats.wows_stats set `winRate` = `win`/`total` where `Date`=%s and `accountID`<>0 and `total` is not null;"""
        db.execute_single(sql=sql, arg=[date])
        db.close_db()
    except ConnectionError:
        print("Database connection failed!")


def request_statsbyID(account_url, application_id, date, overwrite=True):
    result_list = []
    idlist = get_idlistfromsql(overwrite=overwrite)
    sublist = []
    for id in idlist:
        sublist.append(id[0])
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
            db = mysql()
            db.write_ID(result_list)
            db.close_db()
            print("Last account id: ", result_list[size_per_write - 1][0])
        except ConnectionError:
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
            db = mysql()
            db.write_detail(result_list)
            db.close_db()
        except ConnectionError:
            print("Database connection failed!")
        result_list = []
    return result_list


def request_API(days=7):
    # Request API url
    # player_url = 'https://api.worldofwarships.com/wows/account/list/'
    account_url = 'https://api.worldofwarships.com/wows/account/info/'
    # Request params
    application_id = 'bc7a1942582313fd553a85240bd491c8'
    check_ip()
    # request_allID(account_url, application_id)
    iter = days
    last_date = None
    while iter != 0:
        start = datetime.datetime.now()
        if start.date() != last_date:
            last_date = start.date()
            request_statsbyID(account_url, application_id, last_date, overwrite=True)
            update_winRate(last_date)
            # date = datetime.datetime.now().date()
            end = datetime.datetime.now()
            iter -= 1
            print("%s data update finished, time usage: %s" % (start.date().strftime("%Y-%m-%d"), end - start))
        else:
            time.sleep(1800)  # wait 30 mins for next check
    return "Main request finished!"


if __name__ == '__main__':
    result = request_API()
    print(result)
