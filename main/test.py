import datetime

import pymysql as sql

import api_database.wows_api as wows_api
import api_database.wows_db as wows_db
from util import read_config as config
from util import utility as ut


def test_wows_api():
    try:
        ut.check_ip()
        ut.check_date()
        wows = wows_api.wows_api_req()
        idlist = wows.create_idlist(account_ID=1000000000)
        wows.convertlisttopara(idlist)
        wows.update_winRate(date=datetime.datetime.now().date())
        wows.api_main(days=0)
    except:
        print("api_database API test failed!")


def test_wows_rds():
    try:
        db = wows_db.wows_database()
        db.write_detail(data_list=[('2017-01-01', '1000000000', 'xxxxxxx', '1', '0', '0', '0', '0')])
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
