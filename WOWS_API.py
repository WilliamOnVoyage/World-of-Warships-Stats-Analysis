from urllib import request, parse
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
    account_ID = 1000002000

    while account_ID < 2000000000:
        idlist, account_ID = create_idlist(account_ID)
        parameter = parse.urlencode({'application_id': application_id, 'account_id': idlist}, True)

        url = account_url + '?' + parameter

        result = request.urlopen(url).read().decode("utf-8")
        # print(result)
        data = json.loads(result)

        if (data["status"] == "ok"):
            try:
                db = mysql()
                db.write_db(data)
                db.close_db()
            except ConnectionError:
                print("Database connection failed!")
    return "Request finished!"


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
