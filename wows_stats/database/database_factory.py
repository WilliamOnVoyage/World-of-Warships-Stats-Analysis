from wows_stats.database.mongo_db import MongoDB
from wows_stats.database.mysql_db import MySQLDB


def database_factory(db_type):
    if 'mongo' in db_type:
        return MongoDB()
    else:
        return MySQLDB()
