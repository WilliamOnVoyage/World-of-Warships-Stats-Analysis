class AbstractDB(object):
    def __init__(self):
        pass

    def connect_db(self):
        pass

    def write_accountid(self, id_list):
        pass

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

    def fetch_by_query(self, query, args=None):
        pass

    def close_db(self):
        pass
