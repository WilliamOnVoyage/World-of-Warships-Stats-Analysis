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


if __name__ == '__main__':
    cg = ConfigFileReader()
    json_data = cg.read_config(file_name="sample_config.json")
    json_str = json.loads(json_data)
    print(json_str['mysql']['usr'])
