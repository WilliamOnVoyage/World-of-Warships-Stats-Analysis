import json
import os
import unittest

from src.util.config import ConfigFileReader


class TestUtilsCase(unittest.TestCase):
    def setUp(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        project_root_path = os.path.dirname(current_path)
        self.config_path = os.path.join(project_root_path, 'config')

    def test_config_file_reader(self):
        cg = ConfigFileReader()
        json_data = cg.read_all_config(file_name="sample_config.json")
        json_str = json.loads(json_data)
        self.assertIsNotNone(json_str['mysql'])
        self.assertIsNotNone(json_str['mongo'])
        self.assertIsNotNone(json_str['AWS_RDS'])
