from api.mysqldb import MySQLDB

from database.mongo_db import MongoDB

SQL_TRY_NUMBER = 3


class DatabaseConnector(object):
    def __init__(self, database_type='mysql'):
        try:
            if database_type == 'mysql':
                self.db = MySQLDB()
            else:
                self.db = MongoDB()
        except NotImplementedError as e:
            print(e)

    def write_accountid(self, id_list):
        self.db.connect_db()
        self.db.write_accountid(id_list=id_list)
        self.db.close_db()

    def write_detail(self, detail_dict_list):
        self.db.connect_db()
        self.db.write_detail(detail_dict_list=detail_dict_list)
        self.db.close_db()

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        self.db.connect_db()
        self.db.update_winrate(start=start, end=end)
        self.db.close_db()

    def write_by_query(self, query, args=None):
        self.db.connect_db()
        self.db.write_by_query(query=query, args=args)
        self.db.close_db()

    def get_idlist(self, get_entire_idlist=True):
        self.db.connect_db()
        idlist = self.db.get_idlist(get_entire_idlist=get_entire_idlist)
        self.db.close_db()
        return idlist

    def get_stats_by_date(self, args=None):
        self.db.connect_db()
        result = self.db.get_stats_by_date(args=args)
        self.db.close_db()
        return result

    def get_by_query(self, query, args=None):
        self.db.connect_db()
        result = self.db.get_by_query(query=query, args=args)
        self.db.close_db()
        return result


if __name__ == '__main__':
    DatabaseConnector(database_type='mongo').write_accountid(id_list=[{"account_id": "1", "nickname": "test"}])
    # DatabaseConnector().write_detail(detail_dict_list=[
    #     {'account_id': '1018170999', 'nickname': 'Luizclv', 'battles': '0', 'losses': '0', 'draws': '0',
    #      'frags': '0'}])
    # result = DatabaseConnector().get_idlist()
