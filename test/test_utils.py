import os
import unittest

from pandas import DataFrame, Panel
from wows_stats.util.config import ConfigFileReader


class TestUtilsCase(unittest.TestCase):
    def setUp(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        project_root_path = os.path.dirname(current_path)
        self.config_path = os.path.join(project_root_path, 'config')

    def test_config_file_reader(self):
        json_data = ConfigFileReader().read_config(file_dir=self.config_path, file_name="sample_config.json")
        self.assertIsNotNone(json_data)
        self.assertIsNotNone(json_data['mongo'])
        self.assertIsNotNone(ConfigFileReader().read_api_config(config_file="sample_config.json"))
        self.assertIsNotNone(ConfigFileReader().read_mongo_config(config_file="sample_config.json"))

    def test_win_rate_prediction(self):
        try:
            from wows_stats.model.winrate_model import WinrateModel
            df1 = DataFrame(columns=['t', 'w', 'l', 'd'])
            df2 = DataFrame(columns=['t', 'w', 'l', 'd'])
            df1.loc[1000, ['t', 'w', 'l', 'd']] = [1, 0, 1, 0]
            df1.loc[1001, ['t', 'w', 'l', 'd']] = [1, 1, 0, 0]
            df1.loc[1002, ['t', 'w', 'l', 'd']] = [2, 1, 1, 0]
            for i in range(1, len(df1.columns)):
                df1.iloc[:, i] = df1.iloc[:, i] / df1.iloc[:, 0]
            df1.iloc[:, 0] += 0.001

            df2.loc[1000, ['t', 'w', 'l', 'd']] = [13, 4, 5, 4]
            df2.loc[1001, ['t', 'w', 'l', 'd']] = [4, 1, 1, 2]
            df2.loc[1002, ['t', 'w', 'l', 'd']] = [5, 3, 2, 0]
            for i in range(1, len(df2.columns)):
                df2.iloc[:, i] = df2.iloc[:, i] / df2.iloc[:, 0]
            df2.iloc[:, 0] += 0.001
            df = {'d1': df1, 'd2': df2}
            pd = Panel(df)
            model = WinrateModel(data=pd, time_window=1)
            model.training()
            model.save_model()
            self.assertIsNotNone(model)
        except ModuleNotFoundError, ImportError as me:
            print("tensorflow test unavailable due to: {}".format(me))
