import datetime
import bson.json_util
import numpy as np
import pymongo as mg

from wows_stats.database.abstract_db import AbstractDB
from wows_stats.util.ansi_code import AnsiEscapeCode as ansi
from wows_stats.util.config import ConfigFileReader


class MongoDB(AbstractDB):
    def __init__(self, config_file, date=datetime.date.today()):
        super(MongoDB, self).__init__()
        self._date = date
        self._index = 'account_id'
        self._id_prefix = '000000'
        self._db_params = ConfigFileReader().read_mongo_config(config_file)
        # comment the following when running/debuging
        self._connect = mg.MongoClient(host=self._db_params['hostname'], port=self._db_params['port'])
        self._db = self._connect.get_database(name=self._db_params['dbname'])
        self._collection = self._db.get_collection(name=self._db_params['collection'])
        self._connect.close()

    def connect_db(self, verbose=True):
        try:
            connection = mg.MongoClient(host=self._db_params['hostname'], port=self._db_params['port'])
            db = connection.get_database(name=self._db_params['dbname'])
            collection = db.get_collection(name=self._db_params['collection'])
            if verbose:
                print(
                    "MongoDB %s%s%s connected at host %s%s%s port %s%d%s!" % (
                        ansi.BLUE, self._db_params['dbname'], ansi.ENDC, ansi.BLUE, self._db_params["hostname"],
                        ansi.ENDC,
                        ansi.BLUE, self._db_params['port'], ansi.ENDC))
            return collection
        except Exception as e:
            print("%sMongoDB initialization failed!!! %s%s" % (ansi.RED, e, ansi.ENDC))

    def _ensure_index(self):
        try:
            collection = self.connect_db(verbose=False)
            collection.create_index([(self._index, mg.ASCENDING)], unique=True)
            self.close_db()
        except Exception as ex:
            print("{} Ensuring MongoDB index failed due to {}!!!{}".format(ansi.RED, ex, ansi.ENDC))

    def write_account_id(self, id_list_json):
        try:
            collection = self.connect_db()
            # Set ordered  = False to ignore the duplicate key error and keeps adding all data
            for id_item in id_list_json:
                id_dict = bson.json_util.loads(id_item)
                account_id = id_dict[0]
                account_info = id_dict[1]
                if account_info:
                    collection.update_many(filter={'_id': int(account_id)},
                                           update={'$set': account_info}, upsert=True)
            self.close_db()
        except mg.errors.BulkWriteError:
            print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                ansi.RED, ansi.ENDC))

    def write_detail(self, detail_list_json):
        collection = self.connect_db()
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
                            collection.update_one(filter={'_id': object_id},
                                                  update={'$setOnInsert': detail_info['pvp'][date]}, upsert=True)
                            # add object id to account_id doc
                            collection.update_one(filter={'_id': int(account_id)},
                                                  update={'$addToSet': {'daily_stats': object_id}}, upsert=True)
                    elif 'nickname' in detail_info and not detail_info['hidden_profile']:
                        collection.update_one(filter={'_id': int(account_id)},
                                              update={'$set': detail_info}, upsert=True)
                except mg.errors.BulkWriteError:
                    print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                        ansi.RED, ansi.ENDC))
        self.close_db()

    def update_win_rate(self, start='2017-01-01', end='2017-01-01'):
        pass

    def get_id_list(self, get_all_ids=True):
        collection = self.connect_db()
        if get_all_ids:
            id_list = collection.distinct(key='account_id')
        else:
            id_list = collection.distinct(key='account_id', query={'statistics.battles': {'$gte': 100}})
        self.close_db()
        return id_list

    def get_stats_by_date_as_array(self, args=None):
        pass

    def get_database_info(self, battles_threshold=10):
        collection = self.connect_db()
        active_player_number = np.nan
        try:
            filter = {'statistics.battles': {'$gte': battles_threshold}}
            player_list = collection.distinct(key='account_id', filter=filter)
            active_player_number = len(player_list)
        except mg.errors.OperationFailure as e:
            print(e)
        self.close_db()
        return active_player_number

    def get_top_players(self, battles_threshold=1000):
        collection = self.connect_db()
        top_player_list = list()
        projection = ['statistics.pvp.battles', 'statistics.pvp.wins', 'statistics.pvp.losses', 'nickname']
        try:
            doc_filter = {'_id': {'$type': 'int'}, 'statistics.battles': {'$gte': battles_threshold}}
            top_player_list = list(
                collection.find(filter=doc_filter, projection=projection).sort('statistics.battles',
                                                                               mg.DESCENDING).limit(10))
        except mg.errors.OperationFailure as e:
            print(e)
        self.close_db()
        return top_player_list

    def get_top_players_in_week(self, battles_threshold=1000):
        self.connect_db()
        self.close_db()

    def get_top_players_in_month(self, battles_threshold=1000):
        self.connect_db()
        self.close_db()

    def close_db(self):
        self._connect.close()

    @staticmethod
    def print_database_error():
        print('%sDatabase connection failed!!!%s' % (ansi.RED, ansi.ENDC))
