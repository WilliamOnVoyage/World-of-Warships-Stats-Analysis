import pymysql as sql

import api.wows_api as wows_api
import database.db_connector as wows_db
from model import data_preprocess as data_preprocess
from util import aux_functions as ut
from util import config as config


def test_api():
    try:
        ut.check_ip()
        ut.check_date()
        wows = wows_api.WowsAPIRequest()
        idlist = wows.generate_id_list_by_range(account_ID=1000000000)
        wows.list_to_url_params(idlist)
        wows.update_winrate()
        wows.main_request(days=0)
    except:
        print("api API test failed!")


def test_database():
    try:
        db = wows_db.DatabaseConnector(database_type='mysql')
        dict_list = [{'date': '2017-01-01', 'accound_id': '1000000000', 'nickname': 'xxxxxxx', 'battles': '1',
                      'wins': '0', 'losses': '0', 'draws': '0', 'dmg': '0'}]
        db.write_detail(
            detail_dict_list=dict_list)
        id_list = db.get_idlist()
        print(id_list)
        db.write_accountid(id_list=['1000000000', 'xxxxxxx'])
    except sql.MySQLError:
        print("api RDS test failed!")


def test_winrateprediction():
    try:
        print("tensorflow test unavailable")
        # winRate_prediction.test()
    except OSError:
        print("win Rate prediction test failed!")


def test_dataprocess():
    try:
        data_preprocess.test()
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
    print("Testing factor of %d and %d %d" % (36, 120, ut.least_common_factor_with_limit(36, 120)))
    print("Testing max hundered of %d: %d" % (12345679, ut.max_hundred(12345679)))


test_api()
test_database()
test_winrateprediction()
test_dataprocess()
test_config()
test_util()
