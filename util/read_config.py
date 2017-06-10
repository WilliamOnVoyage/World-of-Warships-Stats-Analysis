import json
import os


class config(object):
    def __init__(self):
        self.path = os.path.split(os.path.realpath(__file__))[0]

    def read_config(self, config_file="config.json"):
        path = os.path.dirname(self.path)
        file_name = os.path.join(path, config_file)
        json_data = open(file_name).read()
        return json_data


if __name__ == '__main__':
    cg = config()
    json_data = cg.read_config(config_file="sample_config.json")
    json_str = json.loads(json_data)
    print(json_str['mysql']['usr'])
