import datetime
import json

import pymysql as sql

from src.database.abstract_db import AbstractDB
from src.util.ansi_code import AnsiEscapeCode as ansi
from src.util.config import ConfigFileReader

SQL_TRY_NUMBER = 3


class MySQLDB(AbstractDB):
    def __init__(self, date=datetime.date.today()):
        super().__init__()
        self._db_params = ConfigFileReader().read_mysql_config()
        self._date = date
        self.connect_db()
        self.close_db()

    def connect_db(self):
        try:
            self._db = sql.connect(host=self._db_params['hostname'], port=self._db_params['port'],
                                   user=self._db_params['usr'],
                                   password=self._db_params['pw'], database=self._db_params['dbname'])
            print(
                'MySQL %s%s%s connected at host %s%s%s port %s%d%s!' % (
                    ansi.BLUE, self._db_params['dbname'], ansi.ENDC, ansi.BLUE, self._db_params['hostname'], ansi.ENDC,
                    ansi.BLUE, self._db_params['port'], ansi.ENDC))
        except:
            print('%sMySQL initialization failed!!!%s' % (ansi.RED, ansi.ENDC))

    def write_account_id(self, id_list_json):
        sql_query = '''
        INSERT INTO `wowstats`.`wows_idlist` (`accountID`, `nickname`) VALUES %s
        ON DUPLICATE KEY UPDATE `nickname` = %s
        '''
        fail_count = 0
        id_list = self._id_list_json_to_dict(id_list_json=id_list_json)
        for id_nicknames in id_list:
            if not self._write_by_query(query=sql_query, args=[id_nicknames, id_nicknames[1]]):
                fail_count += 1
        print('********************ID list write finished, %s%d%s cases failed********************' % (
            ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    def write_detail(self, detail_list_json):
        sql_query = '''
        INSERT IGNORE INTO `wowstats`.`wows_stats` (%s) VALUES (%s)
        '''
        query_spliter = ', '
        fail_count = 0
        detail_list = self._detail_list_json_to_dict(detail_list_json)
        for detail_dict in detail_list:
            value_placeholders = query_spliter.join(['%s'] * len(detail_dict))
            key_names = query_spliter.join(detail_dict.keys())
            query = sql_query % (key_names, value_placeholders)
            if not self._write_by_query(query=query, args=list(detail_dict.values())):
                fail_count += 1
        print('********************Detail write finished, %s%d%s cases failed********************' % (
            ansi.GREEN if fail_count == 0 else ansi.RED, fail_count, ansi.ENDC))

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        sql_query = '''
            update wowstats.wows_stats set `winRate` = round(`wins`/`battles`,4) where `date`>=%s and `date`<=%s and `account_id`<>0 and `battles` is not null;
            '''
        success = self._write_by_query(query=sql_query, args=[str(start), str(end)])
        print('%s%s to %s winRate update %s%s' % (
            ansi.GREEN if success else ansi.RED, str(start), str(end), 'finished!' if success else 'failed!!!',
            ansi.ENDC))

    def get_id_list(self, get_all_ids=True):
        if get_all_ids:
            getid_sql = '''SELECT `account_id` FROM wowstats.`wows_idlist`'''
        else:
            getid_sql = '''SELECT DISTINCT `account_id` FROM wowstats.`wows_stats` WHERE `battles` is not null'''
        raw_list = self._get_by_query(query=getid_sql)
        id_list = list()
        for item in raw_list:
            id_list.append(item[0])
        return id_list

    def get_stats_by_date_as_array(self, args=None):
        getid_sql = '''SELECT * FROM wowstats.`wows_stats` WHERE `date` = %s AND `battles` > %s'''
        return self._get_by_query(query=getid_sql, args=args)

    def get_database_info(self):
        pass

    def close_db(self):
        self._db.close()

    def _write_by_query(self, query, args=None):
        self.close_db()
        cursor = self._db.cursor()
        ntry = SQL_TRY_NUMBER
        while ntry > 0:
            try:
                cursor.execute(query=query, args=args)
                self._db.commit()
                return True
            except sql.MySQLError:
                ntry -= 1
                self._db.rollback()
        print('%s%s %% %swrite failed!%s' % (ansi.RED, query, args, ansi.ENDC))
        self.close_db()
        return False

    def _get_by_query(self, query, args=None):
        self.connect_db()
        cursor = self._db.cursor()
        result = []
        try:
            cursor.execute(query=query, args=args)
            self._db.commit()
            result = cursor.fetchall()
        except sql.MySQLError:
            self._db.rollback()
            print('%s%s Execution failed!!!%s' % (ansi.RED, query, ansi.ENDC))
        self.close_db()
        return result

    def _id_list_json_to_dict(self, id_list_json):
        id_list = list()
        for id_json in id_list_json:
            id_info = json.loads(id_json)
            for account_id in id_info:
                nickname = id_info[account_id]['nickname']
                record = (str(account_id), str(nickname))
                id_list.append(record)
        return id_list

    def _detail_list_json_to_dict(self, detail_list_json):
        detail_list = list()
        for detail_json in detail_list_json:
            # TODO: Check! here the json loads return list???
            detail_info = json.loads(detail_json)
            account_id = detail_info[0]
            info = detail_info[1]
            if 'pvp' in info:
                detail_list = detail_list + self._dict_list_from_json_history(acc_id=account_id, info=info['pvp'])
            elif 'nickname' in info and not info['hidden_profile']:
                detail_list.append(self._dict_from_json_new(acc_id=account_id, info=info))
        return detail_list

    def _dict_list_from_json_history(self, acc_id, info):
        stats_list = list()
        for date in info:
            stats = info[date]
            stats_dict = {'account_id': acc_id, 'date': str(date)}
            for item in self._stats_dictionary:
                stats_dict[item] = str(stats[item])
            if stats_dict['battles'] != '0':
                stats_list.append(stats_dict)
        return stats_list

    def _dict_from_json_new(self, acc_id, info):
        nickname = info['nickname']
        pvp = info['statistics']['pvp']
        stats_dict = {'date': str(self._date), 'account_id': str(acc_id), 'nickname': str(nickname)}
        for item in self._stats_dictionary:
            stats_dict[item] = str(pvp[item])
        if stats_dict['battles'] == '0':
            stats_dict = dict()
        return stats_dict
