from apidatabase.wows_db import DatabaseConnector


class rds(object):
    def __init__(self):
        self.db = DatabaseConnector()

    def __del__(self):
        self.db.close_db()

    def update_winRate(self):
        sql = """UPDATE `wows_stats`
        SET `winRate` = `win` / `total`
        WHERE (`accountID` <> 0 AND `total` IS NOT NULL)"""
        self.db.fetch_by_query(query=sql)

    def get_detail(self, total_thres=100):
        sql = """SELECT * FROM wowstats.wows_stats
        WHERE (`total` > %d AND `winRate` is not null)""" % total_thres
        detail = self.db.fetch_by_query(query=sql)
        print(detail)
