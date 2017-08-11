import datetime

import bson.objectid

from database.mongo_db import MongoDB
from database.mysql_db import MySQLDB
from util.ansi_code import AnsiEscapeCode as ansi

SQL_TRY_NUMBER = 3
STATS_DICT = {'battles', 'wins', 'losses', 'draws', 'damage_dealt', 'frags', 'planes_killed', 'xp',
              'capture_points', 'dropped_capture_points', 'survived_battles'}


class DatabaseConnector(object):
    def __init__(self, database_type='mysql', date=datetime.date.today()):
        self._stats_dictionary = STATS_DICT
        try:
            if database_type == 'mysql':
                self._db = MySQLDB(stats_filter=STATS_DICT, date=date)
            else:
                self._db = MongoDB(stats_filter=STATS_DICT, date=date)
        except NotImplementedError as e:
            print(e)

    def write_accountid(self, id_list):
        self._db.connect_db()
        self._db.write_account_id(id_list=id_list)
        self._db.close_db()

    def write_detail(self, detail_list):
        self._db.connect_db()
        self._db.write_detail(detail_list_json=detail_list)
        self._db.close_db()

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        self._db.connect_db()
        self._db.update_winrate(start=start, end=end)
        self._db.close_db()

    def get_idlist(self, get_entire_idlist=True):
        self._db.connect_db()
        idlist = self._db.get_id_list(get_entire_idlist=get_entire_idlist)
        self._db.close_db()
        return idlist

    def get_stats_by_date(self, args=None):
        self._db.connect_db()
        result = self._db.get_stats_by_date(args=args)
        self._db.close_db()
        return result

    def print_database_error(self):
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
    DatabaseConnector(database_type='mongo').write_accountid(
        id_list=[{'_id': id, 'nickname': 'Flamu',
                  'daily_stats': [id1, id2, id3],
                  'last_battle_time': 1500140223,
                  'leveling_tier': 15,
                  'created_at': 1435322987,
                  'leveling_points': 8612323,
                  'updated_at': 1500053592,
                  'logout_at': 1500053581,
                  'karma': 0,
                  'statistics': {
                      'distance': 117155,
                      'battles': 3143,
                      'pvp': {
                          'max_xp': 4913,
                          'damage_to_buildings': 509380,
                          'main_battery': {
                              'max_frags_battle': 7,
                              'frags': 2697,
                              'hits': 163178,
                              'max_frags_ship_id': 4292818736,
                              'shots': 501631
                          },
                          'max_ships_spotted_ship_id': 4285511376,
                          'max_damage_scouting': 143913,
                          'art_agro': 1681724500,
                          'max_xp_ship_id': 4276041424,
                          'ships_spotted': 1670,
                          'second_battery': {
                              'max_frags_battle': 2,
                              'frags': 125,
                              'hits': 28123,
                              'max_frags_ship_id': 3763287856,
                              'shots': 154801
                          },
                          'max_frags_ship_id': 3763287856,
                          'xp': 3925692,
                          'survived_battles': 1357,
                          'dropped_capture_points': 3629,
                          'max_damage_dealt_to_buildings': 128650,
                          'torpedo_agro': 224350304,
                          'draws': 23,
                          'control_captured_points': 24296,
                          'max_total_agro_ship_id': 4276041424,
                          'planes_killed': 5550,
                          'battles': 2884,
                          'max_ships_spotted': 11,
                          'max_suppressions_ship_id': 4292818736,
                          'survived_wins': 1160,
                          'frags': 3613,
                          'damage_scouting': 36181164,
                          'max_total_agro': 5084868,
                          'max_frags_battle': 7,
                          'capture_points': 399,
                          'ramming': {
                              'max_frags_battle': 1,
                              'frags': 15,
                              'max_frags_ship_id': 4276041424
                          },
                          'suppressions_count': 1,
                          'max_suppressions_count': 1,
                          'torpedoes': {
                              'max_frags_battle': 5,
                              'frags': 403,
                              'hits': 1763,
                              'max_frags_ship_id': 4274927600,
                              'shots': 25036
                          },
                          'max_planes_killed_ship_id': 4276041424,
                          'aircraft': {
                              'max_frags_battle': 3,
                              'frags': 54,
                              'max_frags_ship_id': 4288657104
                          },
                          'team_capture_points': 211599,
                          'control_dropped_points': 17979,
                          'max_damage_dealt': 281538,
                          'max_damage_dealt_to_buildings_ship_id': 4292818736,
                          'max_damage_dealt_ship_id': 4276041424,
                          'wins': 1744,
                          'losses': 1117,
                          'damage_dealt': 213232024,
                          'max_planes_killed': 49,
                          'max_scouting_damage_ship_id': 4181669680,
                          'team_dropped_capture_points': 108490,
                          'battles_since_512': 1443
                      }
                  },
                  'stats_updated_at': 1500140964
                  },
                 {'_id': id1,
                  'capture_points': 399,
                  'wins': 1742,
                  'planes_killed': 5550,
                  'battles': 2882,
                  'damage_dealt': 213130514,
                  'xp': 3923528,
                  'frags': 3612,
                  'survived_battles': 1356,
                  'dropped_capture_points': 3629},
                 {'_id': id2,
                  'capture_points': 399,
                  'wins': 1742,
                  'planes_killed': 5550,
                  'battles': 2882,
                  'damage_dealt': 213130514,
                  'xp': 3923528,
                  'frags': 3612,
                  'survived_battles': 1356,
                  'dropped_capture_points': 3629},
                 {'_id': id3,
                  'capture_points': 399,
                  'wins': 1742,
                  'planes_killed': 5550,
                  'battles': 2882,
                  'damage_dealt': 213130514,
                  'xp': 3923528,
                  'frags': 3612,
                  'survived_battles': 1356,
                  'dropped_capture_points': 3629}])
    # DatabaseConnector().write_detail(detail_dict_list=[
    #     {'account_id': '1018170999', 'nickname': 'Luizclv', 'battles': '0', 'losses': '0', 'draws': '0',
    #      'frags': '0'}])
    # result = DatabaseConnector().get_id_list()
