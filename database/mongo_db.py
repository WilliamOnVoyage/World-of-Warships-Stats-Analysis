import json

import pymongo as mg

from database.abstract_db import AbstractDB
from util.ansi_code import AnsiEscapeCode as ansi
from util.config import ConfigFileReader


class MongoDB(AbstractDB):
    def __init__(self):
        super().__init__()
        self._connect = None
        self._db = None
        self._collection = None
        self._index = 'account_id'
        try:
            _config_data = json.loads(ConfigFileReader().read_config())
            self._db_params = _config_data['mongo']
            # self._ensure_index()
        except:
            print("%sMongoDB initialization failed!!!%s" % (ansi.RED, ansi.ENDC))

    def connect_db(self, verbose=True):
        self._connect = mg.MongoClient(host=self._db_params['hostname'], port=self._db_params['port'])
        self._db = self._connect[self._db_params['dbname']]
        self._collection = self._db[self._db_params['collection']]
        if verbose:
            print(
                "MongoDB %s%s%s connected at host %s%s%s port %s%d%s!" % (
                    ansi.BLUE, self._db_params['dbname'], ansi.ENDC, ansi.BLUE, self._db_params["hostname"], ansi.ENDC,
                    ansi.BLUE, self._db_params['port'], ansi.ENDC))

    def _ensure_index(self):
        self.connect_db(verbose=False)
        self._collection.create_index([(self._index, mg.ASCENDING)], unique=True)
        self.close_db()

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
        try:
            # Set ordered  = False to ignore the duplicate key error and keeps adding all data
            self._collection.insert_many(data_list, ordered=False)
        except mg.errors.BulkWriteError:
            print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                ansi.RED, ansi.ENDC))

    def update_list(self, data_list):
        self._collection.find_one_and_update()

    def close_db(self):
        self._connect.close()
