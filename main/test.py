import api.wows_api as wows_api
from model.winrate_model import WinrateModel
from pandas import DataFrame, Panel
from model import preprocessor as data_preprocess
from util import aux_functions as ut
from util import config as config


def test_api():
    try:
        ut.check_ip()
        ut.check_date()
        wows = wows_api.WowsAPIRequest()
        idlist = wows.generate_id_list_by_range(account_ID=1000000000)
        wows.list_to_url_params(idlist)
        wows.update_database_winrate()
        wows.request_historical_stats_all_accounts_last_month(days=0)
    except:
        print("api API test failed!")


def test_database():
    try:
        db = wows_db.DatabaseConnector(database_type='mysql')
        dict_list = [{'date': '2017-01-01', 'accound_id': '1000000000', 'nickname': 'xxxxxxx', 'battles': '1',
                      'wins': '0', 'losses': '0', 'draws': '0', 'dmg': '0'}]
        db.write_detail(
            detail_list=dict_list)
        id_list = db.get_id_list()
        print(id_list)
        db.write_accountid(id_list=['1000000000', 'xxxxxxx'])
    except sql.MySQLError:
        print("api RDS test failed!")


def test_winrateprediction():
    try:
        print("tensorflow test unavailable")
        df1 = DataFrame(columns=['t', 'w', 'l', 'd'])
        df2 = DataFrame(columns=['t', 'w', 'l', 'd'])
        df1.loc[1000, ['t', 'w', 'l', 'd']] = [1, 0, 1, 0]
        df1.loc[1001, ['t', 'w', 'l', 'd']] = [1, 1, 0, 0]
        df1.loc[1002, ['t', 'w', 'l', 'd']] = [2, 1, 1, 0]
        for i in range(1, len(df1.columns)):
            df1.iloc[:, i] = df1.iloc[:, i] / df1.iloc[:, 0]
        df1.iloc[:, 0] += 0.001

        df2.loc[1000, ['t', 'w', 'l', 'd']] = [13, 4, 5, 4]
        df2.loc[1001, ['t', 'w', 'l', 'd']] = [4, 1, 1, 2]
        df2.loc[1002, ['t', 'w', 'l', 'd']] = [5, 3, 2, 0]
        for i in range(1, len(df2.columns)):
            df2.iloc[:, i] = df2.iloc[:, i] / df2.iloc[:, 0]
        df2.iloc[:, 0] += 0.001
        df = {'d1': df1, 'd2': df2}
        pd = Panel(df)

        print(pd['d1'])
        print(pd['d2'])

        model = WinrateModel(data=pd, time_window=1)
        model.training()
        model.save_model()
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
        json_data = cg._read_all_config(file_name="sample_config.json")
        print(json_data)
    except:
        print("read config test failed!")


def test_util():
    print("Testing check date: %s" % ut.check_date())
    print("Testing check ip: %s" % ut.check_ip())
    print("Testing factor of %d and %d %d" % (36, 120, ut.least_common_factor_with_limit(36, 120)))
    print("Testing max hundered of %d: %d" % (12345679, ut.max_hundred(12345679)))

if __name__ == '__main__':
    test_api()
    test_database()
    test_winrateprediction()
    test_dataprocess()
    test_config()
    test_util()
