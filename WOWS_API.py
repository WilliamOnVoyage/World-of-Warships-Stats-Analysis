from urllib import request, parse, error
import json
import socket
import ipgetter
from Connect_mysql import mysql


# account ID range
# if ($id <  500000000) return 'RU';
# elseif ($id < 1000000000) return 'EU';
# elseif ($id < 2000000000) return 'NA';
# elseif ($id < 3000000000) return 'ASIA';
# elseif ($id >= 3000000000) return 'KR';

size_per_write = 1000

def check_ip():
    external_ip = ipgetter.myip()
    print("External ip:%s " % external_ip)
    local_ip = socket.gethostbyname(socket.gethostname())
    print("Local ip:%s " % local_ip)


def get_idlistfromsql():
    try:
        db = mysql()
        idlist = db.get_IDlist()
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
    return id, account_ID + Length


def convertlisttopara(list):
    s = ""
    for i in list:
        if (s != ""):
            s += ","
        s += str(i)
    return s


def request_statsbyID(account_url, application_id):
    result_list = []
    idlist = get_idlistfromsql()
    sublist = []
    for id in idlist:
        sublist.append(id[0])
        if len(sublist) == 100:
            sublist = convertlisttopara(sublist)
            parameter = parse.urlencode({'application_id': application_id, 'account_id': sublist})
            url = account_url + '?' + parameter
            try:
                result = request.urlopen(url).read().decode("utf-8")
                # print(result)
                data = json.loads(result)
                # result_list = record_ID(data, result_list)
                result_list = record_detail(data, result_list)
                sublist = []
            except error.URLError:  # API url request failed
                print("API request failed!")


def request_allID(account_url, application_id):
    account_ID = 1000000000
    result_list = []

    while account_ID < 2000000000:
        idlist, account_ID = create_idlist(account_ID)
        idlist = convertlisttopara(idlist)
        parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist})
        url = account_url + '?' + parameter
        try:
            result = request.urlopen(url).read().decode("utf-8")
            # print(result)
            data = json.loads(result)
            result_list = record_ID(data, result_list)
        except error.URLError:  # API url request failed
            print("API request failed!")


def record_ID(data, result_list):

    if data["status"] == "ok":
        for acc_id in data["data"]:
            if data["data"][acc_id] is not None:
                nickname = data["data"][acc_id]["nickname"]
                record = (str(acc_id), str(nickname))
                result_list.append(record)
    else:
        print(data["error"])  # print error message
    if len(result_list) >= size_per_write:  # write when data has 100 records
        try:
            db = mysql()
            db.write_ID(result_list)
            db.close_db()
        except ConnectionError:
            print("Database connection failed!")
        result_list = []
    return result_list


def record_detail(data, result_list):
    if data["status"] == "ok":
        for acc_id in data["data"]:
            case = data["data"][acc_id]
            if case is not None and not case["hidden_profile"]:
                nickname = case["nickname"]
                pvp = case["statistics"]["pvp"]
                total = pvp["battles"]
                win = pvp["wins"]
                defeat = pvp["losses"]
                draw = pvp["draws"]
                record = (str(acc_id), str(nickname), str(total), str(win), str(defeat), str(draw))
                result_list.append(record)
            else:
                print("User data private or null")
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


def request_API():
    # Request API url
    # player_url = 'https://api.worldofwarships.com/wows/account/list/'
    account_url = 'https://api.worldofwarships.com/wows/account/info/'
    # Request params
    application_id = 'bc7a1942582313fd553a85240bd491c8'
    request_allID(account_url, application_id)
    request_statsbyID(account_url, application_id)
    return "Request finished!"


if __name__ == '__main__':
    check_ip()
    result = request_API()
    print(result)
