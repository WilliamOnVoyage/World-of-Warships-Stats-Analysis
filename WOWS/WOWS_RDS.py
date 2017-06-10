import pymysql as sql
import json
from util import read_config
from util.ansi_code import ANSI_escode as tf


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
                tf.BLUE, dbname, tf.ENDC, tf.BLUE, hostname, tf.ENDC, tf.BLUE, port, tf.ENDC))

    def get_IDlist(self, overwrite=True):
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

    def write_ID(self, data_list):
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
            tf.GREEN if fail_count == 0 else tf.RED, fail_count, tf.ENDC))

    def write_detail(self, data_list):
        cursor = self.db.cursor()
        update_sql = """
        INSERT INTO `wowstats`.`wows_stats` (`Date`,`accountID`,`nickname`,`public`,`total`,`win`,`defeat`,`draw`)
        VALUES %s ON DUPLICATE KEY UPDATE `total` = %s,`win` =%s,`defeat` = %s,`draw` = %s
        """
        fail_count = 0
        for record in data_list:
            try:
                # execute sql in database
                cursor.execute(query=update_sql,
                               args=[record, record[4], record[5], record[6], record[7]])
                self.db.commit()
                # print("%s written." % (record,))
            except sql.MySQLError:
                # roll back if error
                self.db.rollback()
                fail_count += 1
                print("%s%s%s write failed!" % (tf.RED, record, tf.RED))
        print("********************Detail write finished, %s%d%s cases failed********************" % (
            tf.GREEN if fail_count == 0 else tf.RED, fail_count, tf.ENDC))

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
            print(tf.RED + query + " Execution failed!!!")
            raise sql.MySQLError

    def close_db(self):
        # disconnect
        self.db.close()


if __name__ == '__main__':
    try:
        db = wows_database()
        db.write_detail(data_list=[('1018170999', 'Luizclv', '0', '0', '0', '0')])
        db.close_db()
    except sql.MySQLError:
        print(tf.RED + "Database connection failed!")
