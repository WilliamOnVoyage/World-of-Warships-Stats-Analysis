from wows_stats.database.mongo_db import MongoDB


def database_factory(db_type):
    if 'mongo' in db_type:
        return MongoDB()
    else:
        raise NotImplementedError("Database {} is not supported!".format(db_type))
