import json
import os


class ConfigFileReader(object):
    def __init__(self):
        self.config_filepath = os.path.split(os.path.realpath(__file__))[0]

    def _read_all_config(self, file_name="config.json"):
        path = os.path.dirname(self.config_filepath)
        file_name = os.path.join(path, file_name)
        database_config_json = open(file_name).read()
        return database_config_json

    def read_api_config(self):
        _api_config = json.loads(self._read_all_config())
        return _api_config['wows_api']

    def read_mongo_config(self):
        _mongo_config = json.loads(ConfigFileReader()._read_all_config())
        return _mongo_config['mongo']

    def read_mysql_config(self):
        _mysql_config = json.loads(ConfigFileReader()._read_all_config())
        return _mysql_config['mysql']


def test_config_file_reader():
    cg = ConfigFileReader()
    json_data = cg._read_all_config(file_name="sample_config.json")
    json_str = json.loads(json_data)
    print(json_str['mysql']['usr'])


if __name__ == '__main__':
    test_config_file_reader()
