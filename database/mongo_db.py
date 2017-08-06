import json

import pymongo as mg

from database.abstract_db import AbstractDB
from util.ansi_code import AnsiEscapeCode as ansi
from util.config import ConfigFileReader


class MongoDB(AbstractDB):
    def __init__(self):
        super().__init__()
        try:
            _config_data = json.loads(ConfigFileReader().read_config())
            self._db_params = _config_data['mongo']
            self.connect_db()
            self.close_db()
        except:
            print("%sMongoDB initialization failed!!!%s" % (ansi.RED, ansi.ENDC))

    def connect_db(self):
        self._connect = mg.MongoClient(host=self._db_params['hostname'], port=self._db_params['port'])
        self._db = self._connect[self._db_params['dbname']]
        self._collection = self._db[self._db_params['collection']]
        print(
            "MongoDB %s%s%s connected at host %s%s%s port %s%d%s!" % (
                ansi.BLUE, self._db_params['dbname'], ansi.ENDC, ansi.BLUE, self._db_params["hostname"], ansi.ENDC,
                ansi.BLUE, self._db_params['port'], ansi.ENDC))


    def write_accountid(self, id_list):
        self.insert_list(data_list=id_list)

    def write_detail(self, detail_dict_list):
        pass

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        pass

    def write_by_query(self, query, args=None):
        pass

    def get_idlist(self, get_entire_idlist=True):
        pass

    def get_stats_by_date(self, args=None):
        pass

    def get_by_query(self, query, args=None):
        pass

    def insert_list(self, data_list):
        self._collection.insert_many(data_list)

    def update_list(self, data_list):
        self._collection.find_one_and_update()

    def close_db(self):
        self._connect.close()
