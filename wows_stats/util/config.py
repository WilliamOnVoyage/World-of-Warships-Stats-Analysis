import json
import os


class ConfigFileReader(object):
    def __init__(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        project_root_path = os.path.dirname(os.path.dirname(current_path))
        config_file_path = os.path.join(project_root_path, 'config')
        self._config_params = self.read_all_config(file_dir=config_file_path)

    @staticmethod
    def read_all_config(file_dir="", file_name="config.json"):
        file_path = os.path.join(file_dir, file_name)
        with open(file_path) as config_data:
            database_config_json = json.load(config_data)
        return database_config_json

    def read_api_config(self):
        return self._config_params['wows_api']

    def read_mongo_config(self):
        return self._config_params['mongo']

    def read_mysql_config(self):
        return self._config_params['mysql']
