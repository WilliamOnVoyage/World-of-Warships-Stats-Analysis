from src.database.mongo_db import MongoDB
from src.database.mysql_db import MySQLDB


def database_factory(db_type):
    if 'mongo' in db_type:
        return MongoDB()
    else:
        return MySQLDB()
