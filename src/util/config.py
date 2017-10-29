import json
import os


class ConfigFileReader(object):
    def __init__(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        project_root_path = os.path.dirname(os.path.dirname(current_path))
        config_file_path = os.path.join(project_root_path, 'config/')
        self._config_params = self._read_all_config(file_path=config_file_path)

    @staticmethod
    def _read_all_config(file_path="", file_name="config.json"):
        path = os.path.dirname(file_path)
        file_name = os.path.join(path, file_name)
        with open(file_name) as config_data:
            database_config_json = json.load(config_data)
        return database_config_json

    def read_api_config(self):
        return self._config_params['wows_api']

    def read_mongo_config(self):
        return self._config_params['mongo']

    def read_mysql_config(self):
        return self._config_params['mysql']


def test_config_file_reader():
    cg = ConfigFileReader()
    json_data = cg._read_all_config(file_name="sample_config.json")
    json_str = json.loads(json_data)
    print(json_str['mysql']['usr'])


if __name__ == '__main__':
    test_config_file_reader()
