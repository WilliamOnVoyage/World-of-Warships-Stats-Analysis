import datetime

import bson.json_util
import numpy as np
import pymongo as mg

from database.abstract_db import AbstractDB
from util.ansi_code import AnsiEscapeCode as ansi
from util.config import ConfigFileReader


class MongoDB(AbstractDB):
    def __init__(self, stats_filter, date=datetime.date.today()):
        super().__init__()
        self._stats_dictionary = stats_filter
        self._date = date
        self._connect = None
        self._db = None
        self._collection = None
        self._index = 'account_id'
        self._id_prefix = '000000'
        self._db_params = ConfigFileReader().read_mongo_config()
        # comment the following when running/debuging
        self._connect = mg.MongoClient(host=self._db_params['hostname'], port=self._db_params['port'])
        self._db = self._connect.get_database(name=self._db_params['dbname'])
        self._collection = self._db.get_collection(name=self._db_params['collection'])
        self._connect.close()

    def connect_db(self, verbose=True):
        try:
            self._connect = mg.MongoClient(host=self._db_params['hostname'], port=self._db_params['port'])
            self._db = self._connect.get_database(name=self._db_params['dbname'])
            self._collection = self._db.get_collection(name=self._db_params['collection'])
            if verbose:
                print(
                    "MongoDB %s%s%s connected at host %s%s%s port %s%d%s!" % (
                        ansi.BLUE, self._db_params['dbname'], ansi.ENDC, ansi.BLUE, self._db_params["hostname"],
                        ansi.ENDC,
                        ansi.BLUE, self._db_params['port'], ansi.ENDC))
        except BaseException as e:
            print("%sMongoDB initialization failed!!! %s%s" % (ansi.RED, e, ansi.ENDC))

    def _ensure_index(self):
        try:
            self.connect_db(verbose=False)
            self._collection.create_index([(self._index, mg.ASCENDING)], unique=True)
            self.close_db()
        except:
            print("%s Ensuring MongoDB index failed!!!%s" % (ansi.RED, ansi.ENDC))

    def write_account_id(self, id_list_json):
        try:
            # Set ordered  = False to ignore the duplicate key error and keeps adding all data
            for id_item in id_list_json:
                id_dict = bson.json_util.loads(id_item)
                account_id = id_dict[0]
                account_info = id_dict[1]
                if account_info:
                    self._collection.update_many(filter={'_id': int(account_id)},
                                                 update={'$set': account_info}, upsert=True)
        except mg.errors.BulkWriteError:
            print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                ansi.RED, ansi.ENDC))

    def write_detail(self, detail_list_json):
        for detail_item in detail_list_json:
            detail_dict = bson.json_util.loads(detail_item)
            account_id = detail_dict[0]
            detail_info = detail_dict[1]
            if detail_info:
                try:
                    if 'pvp' in detail_info:
                        for date in detail_info['pvp']:
                            date_key = date
                            if len(date_key) < 8:
                                date_key = '0' * (8 - len(date_key)) + date_key
                            object_id = bson.objectid.ObjectId(self._id_prefix + str(date_key) + str(account_id))
                            # add new doc with object id
                            self._collection.update_many(filter={'_id': object_id},
                                                         update={'$set': detail_info['pvp'][date]}, upsert=True)
                            # add object id to account_id doc
                            self._collection.update_many(filter={'_id': int(account_id)},
                                                         update={'$addToSet': {'daily_stats': object_id}}, upsert=True)
                    elif 'nickname' in detail_info and not detail_info['hidden_profile']:
                        self._collection.update_many(filter={'_id': int(account_id)},
                                                     update={'$set': detail_info}, upsert=True)
                except mg.errors.BulkWriteError:
                    print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                        ansi.RED, ansi.ENDC))

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        pass

    def get_id_list(self, get_all_ids=True):
        if get_all_ids:
            id_list = self._collection.distinct(key='account_id')
        else:
            id_list = self._collection.distinct(key='account_id', query={'statistics.battles': {'$gte': 100}})
        return id_list

    def get_stats_by_date(self, args=None):
        pass

    def get_database_info(self, battles_threshold=10):
        active_player_number = np.nan
        try:
            filter = {'statistics.battles': {'$gte': battles_threshold}}
            active_player_number = len(self._collection.distinct(key='account_id', filter=filter))
        except mg.errors.OperationFailure as e:
            print(e)
        return active_player_number

    def get_top_players_by_battles(self, battles_threshold=1000):
        top_player_list = list()
        try:
            filter = {'_id': {'$type': 'int'}, 'statistics.battles': {'$gte': battles_threshold}}
            top_player_list = self._collection.find(filter).sort('statistics.battles', mg.DESCENDING)
        except mg.errors.OperationFailure as e:
            print(e)
        return top_player_list

    def close_db(self):
        self._connect.close()
