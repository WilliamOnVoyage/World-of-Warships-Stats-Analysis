import json
import os


class ConfigFileReader(object):
    def __init__(self):
        self.config_filepath = os.path.split(os.path.realpath(__file__))[0]

    def read_config(self, file_name="config.json"):
        path = os.path.dirname(self.config_filepath)
        file_name = os.path.join(path, file_name)
        json_data = open(file_name).read()
        return json_data

    def read_api_config(self):
        api_config = json.loads(self.read_config())
        application_id = api_config['wows_api']['application_id']
        account_url = api_config['wows_api']['account_url']
        return application_id, account_url


def test_config_file_reader():
    cg = ConfigFileReader()
    json_data = cg.read_config(file_name="sample_config.json")
    json_str = json.loads(json_data)
    print(json_str['mysql']['usr'])


if __name__ == '__main__':
    test_config_file_reader()
