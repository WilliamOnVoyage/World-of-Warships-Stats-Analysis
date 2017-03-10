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



def check_ip():
    external_ip = ipgetter.myip()
    print("External ip:%s " % external_ip)
    local_ip = socket.gethostbyname(socket.gethostname())
    print("Local ip:%s " % local_ip)


def request_player():
    # Request API url
    # player_url = 'https://api.worldofwarships.com/wows/account/list/'
    account_url = 'https://api.worldofwarships.com/wows/account/info/'
    # Request params
    application_id = 'bc7a1942582313fd553a85240bd491c8'
    account_ID = 1001220200
    result_list = []
    size_per_write = 100

    while account_ID < 2000000000:
        idlist, account_ID = create_idlist(account_ID)
        parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist}, True)

        url = account_url + '?' + parameter

        try:
            result = request.urlopen(url).read().decode("utf-8")
            # print(result)
            data = json.loads(result)
            if data["status"] == "ok":
                for acc_id in data["data"]:
                    if data["data"][acc_id] is not None:
                        nickname = data["data"][acc_id]["nickname"]
                        record = (str(acc_id), str(nickname))
                        result_list.append(record)
            else:
                print(data["error"])  # print error message
        except error.URLError:  # API url request failed
            print("API request failed!")
            continue
        if len(result_list) == 10:  # write when data has 100 records
            write_database(result_list)
            result_list = []

    return "Request finished!"


def write_database(data_list):
    try:
        db = mysql()
        db.write_db(data_list)
        db.close_db()
    except ConnectionError:
        print("Database connection failed!")


def create_idlist(account_ID):
    id = []
    Length = 100
    for i in range(Length):
        id.append(account_ID + i)
    return id, account_ID + Length


if __name__ == '__main__':
    check_ip()
    result = request_player()
    print(result)
