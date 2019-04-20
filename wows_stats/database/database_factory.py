from wows_stats.database.mongo_db import MongoDB


def database_factory(db_type, config_file="config.json"):
    if 'mongo' in db_type:
        return MongoDB(config_file)
    else:
        raise NotImplementedError("Database {} is not supported!".format(db_type))
