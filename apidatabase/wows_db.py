import json

import pymysql as sql

from util import read_config
from util.ansi_code import ANSI_escode as ansi

SQL_TRY_NUMBER = 3


class wows_database(object):
    def __init__(self):
        try:
            self.connect_db()
            # print("Database connected!")
        except:
            print("Connection failed!")
            raise sql.MySQLError

    def connect_db(self, database='mysql'):
        # Read database config file
        cg = read_config.config()
        config_data = json.loads(cg.read_config())
        hostname = config_data[database]["hostname"]
        port = config_data[database]['port']
        usr = config_data[database]['usr']
        pw = config_data[database]['pw']
        dbname = config_data[database]['dbname']
        self.db = sql.connect(host=hostname, port=port, user=usr, password=pw, database=dbname)
        print(
            "Database %s%s%s connected at host %s%s%s port %s%d%s!" % (
                ansi.BLUE, dbname, ansi.ENDC, ansi.BLUE, hostname, ansi.ENDC, ansi.BLUE, port, ansi.ENDC))

    def get_idlist(self, overwrite=True):
        cursor = self.db.cursor()
        # Get all ids from ID_table whether id has valid stats
        if overwrite:
            getid_sql = """SELECT `accountID` FROM wowstats.`wows_idlist`"""
        # Get the ids only have valid stats in the day
        else:
            getid_sql = """SELECT DISTINCT `accountID` FROM wowstats.`wows_stats` WHERE `total` IS NULL"""
        try:
            # execute sql in database
            cursor.execute(query=getid_sql)
            return cursor.fetchall()
        except sql.MySQLError:
            # roll back if error
            self.db.rollback()
            print("Fetch failed!!!")

    def write_idlist(self, data_list):
        cursor = self.db.cursor()
        insert_sql = """
        INSERT INTO `wowstats`.`wows_idlist` (`accountID`, `nickname`) VALUES %s
        ON DUPLICATE KEY UPDATE `nickname` = %s
        """
        fail_count = 0
        for record in data_list:
            try:
                # execute sql in database
                cursor.execute(query=insert_sql, args=[record, record[1]])
                self.db.commit()
                # print("%s written." % (record,))
            except sql.MySQLError:
                # roll back if error
                self.db.rollback()
                fail_count += 1
                # print("%s write failed!" % (record,))
        print("********************ID list write finished, %s%d%s cases failed********************" % (
            ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    # def write_detail(self, data_list):
    #     cursor = self.db.cursor()
    #     update_sql = """
    #     INSERT IGNORE INTO `wowstats`.`wows_stats` (`Date`,`accountID`,`nickname`,`public`,`total`,`win`,`defeat`,`draw`)
    #     VALUES %s
    #     """
    #     fail_count = 0
    #     for record in data_list:
    #         ntry = SQL_TRY_NUMBER
    #         while ntry > 0:
    #             try:
    #                 # execute sql in database
    #                 cursor.execute(query=update_sql,
    #                                args=[record])
    #                 self.db.commit()
    #                 # print("%s written." % (record,))
    #                 break
    #             except sql.MySQLError:
    #                 # roll back if error
    #                 ntry -= 1
    #                 self.db.rollback()
    #                 print("%s%s%s write failed!%s" % (ansi.RED, record, ansi.RED, ansi.ENDC))
    #         if ntry == 0:
    #             fail_count += 1
    #     print("********************Detail write finished, %s%d%s cases failed********************" % (
    #         ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    def write_detailbydict(self, dict_list):
        cursor = self.db.cursor()
        sql_query = """
        INSERT IGNORE INTO `wowstats`.`wows_stats` (%s) VALUES (%s)
        """
        spliter = ", "
        fail_count = 0
        for dict in dict_list:
            ntry = SQL_TRY_NUMBER
            while ntry > 0:
                try:
                    placeholders = spliter.join(['%s'] * len(dict))
                    columns = spliter.join(dict.keys())
                    query = sql_query % (columns, placeholders)
                    # execute sql in database
                    cursor.execute(query=query, args=list(dict.values()))
                    self.db.commit()
                    # print("%s written." % (record,))
                    break
                except sql.MySQLError:
                    # roll back if error
                    ntry -= 1
                    self.db.rollback()
                    print("%s%s%s write failed!%s" % (ansi.RED, dict, ansi.RED, ansi.ENDC))
            if ntry == 0:
                fail_count += 1
        print("********************Detail write finished, %s%d%s cases failed********************" % (
            ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    def execute_single(self, query, arg=None):
        cursor = self.db.cursor()
        try:
            # execute sql in database
            cursor.execute(query=query, args=[arg])
            self.db.commit()
            return cursor.fetchall()
            # print("%s written." % (record,))
        except sql.MySQLError:
            # roll back if error
            self.db.rollback()
            print(ansi.RED + query + " Execution failed!!!")
            raise sql.MySQLError

    def get_statsbyDate(self, para):
        cursor = self.db.cursor()
        getid_sql = """SELECT * FROM wowstats.`wows_stats` WHERE `Date` = %s AND `total`>%s"""
        try:
            # execute sql in database
            cursor.execute(query=getid_sql, args=para)
            return cursor.fetchall()
        except sql.MySQLError:
            # roll back if error
            self.db.rollback()
            print("Fetch failed!!!")

    def close_db(self):
        # disconnect
        self.db.close()


if __name__ == '__main__':
    try:
        db = wows_database()
        db.write_detail(data_list=[('1018170999', 'Luizclv', '0', '0', '0', '0')])
        db.close_db()
    except sql.MySQLError:
        print(ansi.RED + "Database connection failed!")
