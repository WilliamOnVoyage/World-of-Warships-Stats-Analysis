from abc import ABCMeta, abstractmethod

STATS_DICT = {'battles', 'wins', 'losses', 'draws', 'damage_dealt', 'frags', 'planes_killed', 'xp',
              'capture_points', 'dropped_capture_points', 'survived_battles'}


class AbstractDB(object, metaclass=ABCMeta):
    def __init__(self):
        self.name = 'Database'
        self.stats_dictionary = STATS_DICT

    @abstractmethod
    def connect_db(self):
        pass

    @abstractmethod
    def write_account_id(self, id_list_json):
        pass

    @abstractmethod
    def write_detail(self, detail_list_json):
        pass

    @abstractmethod
    def update_win_rate(self, start='2017-01-01', end='2017-01-01'):
        pass

    @abstractmethod
    def get_id_list(self, get_all_ids=True):
        pass

    @abstractmethod
    def get_stats_by_date_as_array(self, args=None):
        pass

    @abstractmethod
    def get_database_info(self):
        print("Not implemented error!!!")

    @abstractmethod
    def get_top_players(self):
        print("Not implemented error!!!")

    @abstractmethod
    def get_top_players_in_week(self):
        print("Not implemented error!!!")

    @abstractmethod
    def get_top_players_in_month(self):
        print("Not implemented error!!!")

    @abstractmethod
    def close_db(self):
        pass
