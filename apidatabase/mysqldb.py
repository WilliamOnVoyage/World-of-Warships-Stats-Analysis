import json

import pymysql as sql

from apidatabase.abstract_db import AbstractDB
from util.ansi_code import AnsiEscapeCode as ansi
from util.read_config import ConfigFileReader

SQL_TRY_NUMBER = 3


class MySQLDB(AbstractDB):
    def __init__(self):
        super().__init__()
        try:
            # Read database config file
            _config_data = json.loads(ConfigFileReader().read_config())
            self._db_params = _config_data['mysql']
            self.connect_db()
            self.close_db()
        except:
            print("%sMySQL initialization failed!!!%s" % (ansi.RED, ansi.ENDC))

    def connect_db(self):
        self.db = sql.connect(host=self._db_params["hostname"], port=self._db_params['port'],
                              user=self._db_params['usr'],
                              password=self._db_params['pw'], database=self._db_params['dbname'])
        print(
            "MySQL %s%s%s connected at host %s%s%s port %s%d%s!" % (
                ansi.BLUE, self._db_params['dbname'], ansi.ENDC, ansi.BLUE, self._db_params["hostname"], ansi.ENDC,
                ansi.BLUE, self._db_params['port'], ansi.ENDC))

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
            getid_sql = """SELECT `account_id` FROM wowstats.`wows_idlist`"""
        else:
            getid_sql = """SELECT DISTINCT `account_id` FROM wowstats.`wows_stats` WHERE `battles` is not null"""
        return self.get_by_query(query=getid_sql)

    def get_stats_by_date(self, args=None):
        getid_sql = """SELECT * FROM wowstats.`wows_stats` WHERE `date` = %s AND `battles` > %s"""
        return self.get_by_query(query=getid_sql, args=args)

    def get_by_query(self, query, args=None):
        cursor = self.db.cursor()
        result = []
        try:
            cursor.execute(query=query, args=args)
            self.db.commit()
            result = cursor.fetchall()
        except sql.MySQLError:
            self.db.rollback()
            print("%s%s Execution failed!!!%s" % (ansi.RED, query, ansi.ENDC))
        return result

    def close_db(self):
        self.db.close()
