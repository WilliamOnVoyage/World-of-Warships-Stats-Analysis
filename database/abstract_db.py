class AbstractDB(object):
    def __init__(self):
        self._name = 'Database'

    def connect_db(self):
        pass

    def write_account_id(self, id_list_json):
        pass

    def write_detail(self, detail_list_json):
        pass

    def update_winrate(self, start='2017-01-01', end='2017-01-01'):
        pass

    def get_id_list(self, get_all_ids=True):
        pass

    def get_stats_by_date(self, args=None):
        pass

    def close_db(self):
        pass
