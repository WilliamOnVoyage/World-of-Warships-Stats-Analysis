import json
import os

CONFIG_FOLDER_NAME = "config"


class ConfigFileReader(object):
    def __init__(self):
        pass

    def read_api_config(self, config_file="config.json"):
        config_params = self.read_config_in_default_folder(config_file)
        return config_params['wows_api']

    def read_mongo_config(self, config_file="config.json"):
        config_params = self.read_config_in_default_folder(config_file)
        return config_params['mongo']

    def read_config_in_default_folder(self, config_file):
        config_file_path = self._get_config_folder_path()
        return self.read_config(file_dir=config_file_path, file_name=config_file)

    @classmethod
    def read_config(cls, file_dir, file_name):
        file_path = os.path.join(file_dir, file_name)
        with open(file_path) as config_data:
            database_config_json = json.load(config_data)
        return database_config_json

    @staticmethod
    def _get_config_folder_path():
        current_path = os.path.dirname(os.path.realpath(__file__))
        project_root_path = os.path.dirname(os.path.dirname(current_path))
        return os.path.join(project_root_path, CONFIG_FOLDER_NAME)
