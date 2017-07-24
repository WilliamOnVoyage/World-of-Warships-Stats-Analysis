import json

import pymysql as sql

from util.ansi_code import AnsiEscapeCode as ansi
from util.read_config import ConfigFileReader

SQL_TRY_NUMBER = 3


class DatabaseConnector(object):
    def __init__(self):
        try:
            self.connect_db()
            print("Database connected!")
        except:
            print("%sConnection failed!!!%s" % (ansi.RED, ansi.ENDC))
            raise sql.MySQLError

    def connect_db(self, database='mysql'):
        # Read database config file
        cg = ConfigFileReader()
        config_data = json.loads(cg.read_config())
        param_dict = config_data[database]
        self.db = sql.connect(host=param_dict["hostname"], port=param_dict['port'], user=param_dict['usr'],
                              password=param_dict['pw'], database=param_dict['dbname'])
        print(
            "Database %s%s%s connected at host %s%s%s port %s%d%s!" % (
                ansi.BLUE, param_dict['dbname'], ansi.ENDC, ansi.BLUE, param_dict["hostname"], ansi.ENDC,
                ansi.BLUE, param_dict['port'], ansi.ENDC))

    def write_accountid(self, id_list):
        sql_query = """
        INSERT INTO `wowstats`.`wows_idlist` (`accountID`, `nickname`) VALUES %s
        ON DUPLICATE KEY UPDATE `nickname` = %s
        """
        fail_count = 0
        for id_nicknames in id_list:
            if not self.write_by_query(query=sql_query, args=[id_nicknames, id_nicknames[1]]):
                fail_count += 1
        print("********************ID list write finished, %s%d%s cases failed********************" % (
            ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    def write_detail(self, detail_dict_list):
        sql_query = """
        INSERT IGNORE INTO `wowstats`.`wows_stats` (%s) VALUES (%s)
        """
        query_spliter = ", "
        fail_count = 0
        for detail_dict in detail_dict_list:
            value_placeholders = query_spliter.join(['%s'] * len(detail_dict))
            key_names = query_spliter.join(detail_dict.keys())
            query = sql_query % (key_names, value_placeholders)
            if not self.write_by_query(query=query, args=list(detail_dict.values())):
                fail_count += 1
        print("********************Detail write finished, %s%d%s cases failed********************" % (
            ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        sql_query = """
            update wowstats.wows_stats set `winRate` = round(`wins`/`battles`,4) where `date`>=%s and `date`<=%s and `account_id`<>0 and `battles` is not null;
            """
        success = self.write_by_query(query=sql_query, args=[str(start), str(end)])
        print("%s%s to %s winRate update %s%s" % (
            ansi.GREEN if success else ansi.RED, str(start), str(end), "finished!" if success else "failed!!!",
            ansi.ENDC))

    def write_by_query(self, query, args=None):
        cursor = self.db.cursor()
        ntry = SQL_TRY_NUMBER
        while ntry > 0:
            try:
                cursor.execute(query=query, args=args)
                self.db.commit()
                return True
            except sql.MySQLError:
                ntry -= 1
                self.db.rollback()
        print("%s%s %% %swrite failed!%s" % (ansi.RED, query, args, ansi.ENDC))
        return False

    def get_idlist(self, get_entire_idlist=True):
        if get_entire_idlist:
            getid_sql = """SELECT `accountID` FROM wowstats.`wows_idlist`"""
        else:
            getid_sql = """SELECT DISTINCT `accountID` FROM wowstats.`wows_stats` WHERE `total` IS NULL"""
        return self.fetch_by_query(query=getid_sql)

    def get_stats_by_date(self, args='2017-01-01'):
        getid_sql = """SELECT * FROM wowstats.`wows_stats` WHERE `Date` = %s"""
        return self.fetch_by_query(query=getid_sql, args=args)

    def fetch_by_query(self, query, args=None):
        cursor = self.db.cursor()
        try:
            cursor.execute(query=query, args=[args])
            self.db.commit()
        except sql.MySQLError:
            self.db.rollback()
            print("%s%s Execution failed!!!%s" % (ansi.RED, query, ansi.ENDC))
        return cursor.fetchall()

    def close_db(self):
        self.db.close()


def test_wows_db():
    try:
        db = DatabaseConnector()
        db.write_detail(detail_dict_list=[
            {'account_id': '1018170999', 'nickname': 'Luizclv', 'battles': '0', 'losses': '0', 'draws': '0',
             'frags': '0'}])
        db.close_db()
    except sql.MySQLError:
        print("%sDatabase test failed!%s" % (ansi.RED, ansi.ENDC))


if __name__ == '__main__':
    test_wows_db()
