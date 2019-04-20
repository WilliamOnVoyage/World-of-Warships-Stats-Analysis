import unittest

from wows_stats.api import wows_api
from wows_stats.util import aux_functions as ut


class APITestCase(unittest.TestCase):
    def test_api(self):
        ut.check_ip()
        ut.check_date()
        wows = wows_api.WowsAPIRequest()
        id_list = wows.generate_id_list_by_range(account_ID=1000000000)
        self.assertIsNotNone(id_list)
        wows.update_database_winrate()
