import datetime

import bson.json_util
import numpy as np
import pymongo as mg
from bson.json_util import dumps

from src.database.abstract_db import AbstractDB
from src.util.ansi_code import AnsiEscapeCode as ansi
from src.util.config import ConfigFileReader


class MongoDB(AbstractDB):
    def __init__(self, date=datetime.date.today()):
        super().__init__()
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
            self.connect_db()
            # Set ordered  = False to ignore the duplicate key error and keeps adding all data
            for id_item in id_list_json:
                id_dict = bson.json_util.loads(id_item)
                account_id = id_dict[0]
                account_info = id_dict[1]
                if account_info:
                    self._collection.update_many(filter={'_id': int(account_id)},
                                                 update={'$set': account_info}, upsert=True)
            self.close_db()
        except mg.errors.BulkWriteError:
            print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                ansi.RED, ansi.ENDC))

    def write_detail(self, detail_list_json):
        self.connect_db()
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
                            self._collection.update_one(filter={'_id': object_id},
                                                        update={'$setOnInsert': detail_info['pvp'][date]}, upsert=True)
                            # add object id to account_id doc
                            self._collection.update_one(filter={'_id': int(account_id)},
                                                        update={'$addToSet': {'daily_stats': object_id}}, upsert=True)
                    elif 'nickname' in detail_info and not detail_info['hidden_profile']:
                        self._collection.update_one(filter={'_id': int(account_id)},
                                                    update={'$set': detail_info}, upsert=True)
                except mg.errors.BulkWriteError:
                    print("%sDuplicate key error!!! Other documents have been inserted!%s" % (
                        ansi.RED, ansi.ENDC))
        self.close_db()

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        pass

    def get_id_list(self, get_all_ids=True):
        self.connect_db()
        if get_all_ids:
            id_list = self._collection.distinct(key='account_id')
        else:
            id_list = self._collection.distinct(key='account_id', query={'statistics.battles': {'$gte': 100}})
        self.close_db()
        return id_list

    def get_stats_by_date_as_array(self, args=None):

        pass

    def get_database_info(self, battles_threshold=10):
        self.connect_db()
        active_player_number = np.nan
        try:
            filter = {'statistics.battles': {'$gte': battles_threshold}}
            player_list = self._collection.distinct(key='account_id', filter=filter)
            active_player_number = len(player_list)
        except mg.errors.OperationFailure as e:
            print(e)
        self.close_db()
        return active_player_number

    def get_top_players(self, battles_threshold=1000):
        self.connect_db()
        top_player_list = list()
        projection = ['statistics.pvp.battles', 'statistics.pvp.wins', 'statistics.pvp.losses', 'nickname']
        try:
            doc_filter = {'_id': {'$type': 'int'}, 'statistics.battles': {'$gte': battles_threshold}}
            top_player_list = list(
                self._collection.find(filter=doc_filter, projection=projection).sort('statistics.battles',
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

    def _print_database_error(self):
        print('%sDatabase connection failed!!!%s' % (ansi.RED, ansi.ENDC))


if __name__ == '__main__':
    prefix = '000000'
    id = 1000000005
    id1 = bson.objectid.ObjectId(prefix + '20170808' + str(id))
    id2 = bson.objectid.ObjectId(prefix + '20170807' + str(id))
    id3 = bson.objectid.ObjectId(prefix + '20170806' + str(id))

    print(id1)
    print(id2)
    print(id3)

    json_data = {"1008331251": {
        "last_battle_time": 1500140223,
        "account_id": 1008331251,
        "leveling_tier": 15,
        "created_at": 1435322987,
        "leveling_points": 8612323,
        "updated_at": 1500053592,
        "private": None,
        "hidden_profile": False,
        "logout_at": 1500053581,
        "karma": None,
        "statistics": {
            "distance": 117155,
            "battles": 3143,
            "pvp": {
                "max_xp": 4913,
                "damage_to_buildings": 509380,
                "main_battery": {
                    "max_frags_battle": 7,
                    "frags": 2697,
                    "hits": 163178,
                    "max_frags_ship_id": 4292818736,
                    "shots": 501631
                },
                "max_ships_spotted_ship_id": 4285511376,
                "max_damage_scouting": 143913,
                "art_agro": 1681724500,
                "max_xp_ship_id": 4276041424,
                "ships_spotted": 1670,
                "second_battery": {
                    "max_frags_battle": 2,
                    "frags": 125,
                    "hits": 28123,
                    "max_frags_ship_id": 3763287856,
                    "shots": 154801
                },
                "max_frags_ship_id": 3763287856,
                "xp": 3925692,
                "survived_battles": 1357,
                "dropped_capture_points": 3629,
                "max_damage_dealt_to_buildings": 128650,
                "torpedo_agro": 224350304,
                "draws": 23,
                "control_captured_points": 24296,
                "max_total_agro_ship_id": 4276041424,
                "planes_killed": 5550,
                "battles": 2884,
                "max_ships_spotted": 11,
                "max_suppressions_ship_id": 4292818736,
                "survived_wins": 1160,
                "frags": 3613,
                "damage_scouting": 36181164,
                "max_total_agro": 5084868,
                "max_frags_battle": 7,
                "capture_points": 399,
                "ramming": {
                    "max_frags_battle": 1,
                    "frags": 15,
                    "max_frags_ship_id": 4276041424
                },
                "suppressions_count": 1,
                "max_suppressions_count": 1,
                "torpedoes": {
                    "max_frags_battle": 5,
                    "frags": 403,
                    "hits": 1763,
                    "max_frags_ship_id": 4274927600,
                    "shots": 25036
                },
                "max_planes_killed_ship_id": 4276041424,
                "aircraft": {
                    "max_frags_battle": 3,
                    "frags": 54,
                    "max_frags_ship_id": 4288657104
                },
                "team_capture_points": 211599,
                "control_dropped_points": 17979,
                "max_damage_dealt": 281538,
                "max_damage_dealt_to_buildings_ship_id": 4292818736,
                "max_damage_dealt_ship_id": 4276041424,
                "wins": 1744,
                "losses": 1117,
                "damage_dealt": 213232024,
                "max_planes_killed": 49,
                "max_scouting_damage_ship_id": 4181669680,
                "team_dropped_capture_points": 108490,
                "battles_since_512": 1443
            }
        },
        "nickname": "zmlzeze",
        "stats_updated_at": 1500140964
    }}
    previous_json_data = {"1008331251": {
        "pvp": {
            "20170714": {
                "capture_points": 399,
                "account_id": 1008331251,
                "max_xp": 4913,
                "wins": 1742,
                "planes_killed": 5550,
                "battles": 2882,
                "damage_dealt": 213130514,
                "battle_type": "pvp",
                "date": "20170714",
                "xp": 3923528,
                "frags": 3612,
                "survived_battles": 1356,
                "dropped_capture_points": 3629
            }
        }
    }
    }

    MgDB = MongoDB(stats_filter=STATS_DICT)
    MgDB.write_detail(detail_list_json=[dumps(json_data)])
    MgDB.write_detail(detail_list_json=[dumps(previous_json_data)])
    id_list = MgDB.get_id_list()
    print(id_list)
