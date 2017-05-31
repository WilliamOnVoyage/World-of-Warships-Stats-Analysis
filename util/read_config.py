import json
import os


class config(object):
    def read_config(self):
        path = os.path.abspath('..')
        file = os.path.join(path, "config.json")
        json_data = open(file).read()
        return json_data


if __name__ == '__main__':
    cg = config()
    json_data = cg.read_config()
    json_str = json.loads(json_data)
    print(json_str['mysql']['usr'])
