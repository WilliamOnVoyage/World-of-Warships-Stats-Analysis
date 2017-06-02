import WOWS.WOWS_API as wows
import util.read_config as config
import pymysql as sql
from WOWS.WOWS_RDS import wows_database


def test_WOWS_API():
    try:
        wows.check_ip()
        wows.check_date()
        idlist = wows.create_idlist(account_ID=1000000000)
        wows.convertlisttopara(idlist)
        wows.request_main(days=1)
    except:
        print("WOWS API test failed!")


def test_WOWS_RDS():
    try:
        db = wows_database()
        db.write_detail(data_list=[('1018170999', 'Luizclv', '0', '0', '0', '0')])
        id_list = db.get_IDlist()
        print(id_list)
        db.write_ID(data_list=['1000000000', 'xxxxxxx'])
        db.close_db()
    except sql.MySQLError:
        print("WOWS RDS test failed!")


def test_config():
    try:
        cg = config.config()
        json_data = cg.read_config(config_file="sample_config.json")
        print(json_data)
    except:
        print("read_config test failed!")


if __name__ == "__main__":
    test_WOWS_API()
    test_WOWS_RDS()
    test_config()
