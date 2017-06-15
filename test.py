import datetime

import pymysql as sql

import api_database.wows_api as wows
import util.read_config as config
from api_database.wows_DB import wows_database


def test_wows_api():
    try:
        wows.check_ip()
        wows.check_date()
        idlist = wows.create_idlist(account_ID=1000000000)
        wows.convertlisttopara(idlist)
        wows.update_winRate(date=datetime.datetime.now().date())
        wows.request_main(days=1)
    except:
        print("api_database API test failed!")


def test_wows_rds():
    try:
        db = wows_database()
        db.write_detail(data_list=[('1018170999', 'Luizclv', '0', '0', '0', '0')])
        id_list = db.get_IDlist()
        print(id_list)
        db.write_ID(data_list=['1000000000', 'xxxxxxx'])
        db.close_db()
    except sql.MySQLError:
        print("api_database RDS test failed!")


def test_config():
    try:
        cg = config.config()
        json_data = cg.read_config(config_file="sample_config.json")
        print(json_data)
    except:
        print("read config test failed!")


if __name__ == "__main__":
    test_wows_api()
    test_wows_rds()
    test_config()
