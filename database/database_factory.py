import database.mongo_db, database.mysql_db


def database_factory(db_type):
    if 'mongo' in db_type:
        return database.mongo_db.MongoDB()
    else:
        return database.mysql_db.MySQLDB()
