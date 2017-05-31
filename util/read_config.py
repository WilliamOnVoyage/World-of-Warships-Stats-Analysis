import json
import os


class config(object):
    def read_config(self):
        path = os.path.abspath('..')
        print(path)
        file = os.path.join(path,"config.json")
        json_data = open(file).read()
        print(json_data)
        return json_data


if __name__ == '__main__':
    cg = config()
    cg.read_config()
