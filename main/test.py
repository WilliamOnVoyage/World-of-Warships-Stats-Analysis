import pymysql as sql

import apidatabase.wows_api as wows_api
import apidatabase.wows_db as wows_db
from model import data_preprocess as winRate_dataprocess
from util import read_config as config
from util import utility as ut


def test_wows_api():
    try:
        ut.check_ip()
        ut.check_date()
        wows = wows_api.WowsAPIRequest()
        idlist = wows.create_idlist(account_ID=1000000000)
        wows.list2param(idlist)
        wows.update_winrate()
        wows.main_request(days=0)
    except:
        print("apidatabase API test failed!")


def test_wows_rds():
    try:
        db = wows_db.DatabaseConnector()
        dict_list = [{'date': '2017-01-01', 'accound_id': '1000000000', 'nickname': 'xxxxxxx', 'battles': '1',
                      'wins': '0', 'losses': '0', 'draws': '0', 'dmg': '0'}]
        db.write_detail(
            detail_dict_list=dict_list)
        id_list = db.get_idlist()
        print(id_list)
        db.write_accountid(id_list=['1000000000', 'xxxxxxx'])
        db.close_db()
    except sql.MySQLError:
        print("apidatabase RDS test failed!")


def test_winrateprediction():
    try:
        print("tensorflow test unavailable")
        # winRate_prediction.test()
    except OSError:
        print("win Rate prediction test failed!")


def test_winR_datapro():
    try:
        winRate_dataprocess.test()
    except OSError:
        print("win Rate data process test failed!")


def test_config():
    try:
        cg = config.ConfigFileReader()
        json_data = cg.read_config(file_name="sample_config.json")
        print(json_data)
    except:
        print("read config test failed!")


def test_util():
    print("Testing check date: %s" % ut.check_date())
    print("Testing check ip: %s" % ut.check_ip())
    print("Testing check current date: %s" % ut.getcurrent_date())
    print("Testing factor of %d and %d %d" % (36, 120, ut.common_factorbylimit(36, 120)))
    print("Testing max hundered of %d: %d" % (12345679, ut.max_hundred(12345679)))


test_wows_api()
test_wows_rds()
test_winrateprediction()
test_winR_datapro()
test_config()
test_util()
