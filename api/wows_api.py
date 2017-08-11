import datetime
import json
import time
from socket import timeout as timeoutError
from urllib import request, parse, error

import numpy as np

from database.db_connector import DatabaseConnector
from util import aux_functions
from util.ansi_code import AnsiEscapeCode as ansi
from util.config import ConfigFileReader

# account ID range
# if ($id <  500000000) return 'RU';
# elseif ($id < 1000000000) return 'EU';
# elseif ($id < 2000000000) return 'NA';
# elseif ($id < 3000000000) return 'ASIA';
# elseif ($id >= 3000000000) return 'KR';

DB_TYPE = 'DB_TYPE'
DATE_FORMAT = 'DATE_FORMAT'
NA_ACCOUNT_LIMIT_LO = 'NA_ACCOUNT_LIMIT_LO'
NA_ACCOUNT_LIMIT_HI = 'NA_ACCOUNT_LIMIT_HI'
ID_STEP = 'ID_STEP'
SIZE_PER_WRITE = 'SIZE_PER_WRITE'
URL_REQ_DELAY = 'URL_REQ_DELAY'
URL_REQ_TIMEOUT = 'URL_REQ_TIMEOUT'
URL_REQ_TRYNUM = 'URL_REQ_TRYNUM'

APPLICATION_ID = 'application_id'
ACCOUNT_URL = 'account_url'
STATS_BY_DATE_URL = 'stats_by_date_url'


class WowsAPIRequest(object):
    def __init__(self):
        # *************CRUCIAL PARAMETERS**************
        _api_params = ConfigFileReader().read_api_config()
        self._size_per_write = _api_params[SIZE_PER_WRITE]
        self._request_delay = _api_params[URL_REQ_DELAY]
        self._account_id_upperbound = _api_params[NA_ACCOUNT_LIMIT_HI]
        self._account_id_lowerbound = _api_params[NA_ACCOUNT_LIMIT_LO]
        self._account_id_step = _api_params[ID_STEP]
        self._date_format = _api_params[DATE_FORMAT]
        self._application_id = _api_params[APPLICATION_ID]
        self._account_url = _api_params[ACCOUNT_URL]
        self._stats_by_date_url = _api_params[STATS_BY_DATE_URL]
        self._url_req_trynumber = _api_params[URL_REQ_TRYNUM]
        self._url_req_timeout = _api_params[URL_REQ_TIMEOUT]
        self._db_type = _api_params[DB_TYPE]
        self._date = '2017-01-01'
        self._db = DatabaseConnector(database_type=self._db_type)
        self._failed_urls = list()
        print('API initialized!')

    def request_all_ids(self):
        account_id = self._account_id_lowerbound
        requested_id_list = list()
        print('Task: Requesting all IDs...')
        while account_id < self._account_id_upperbound:
            id_list = self.list_to_url_params(self.generate_id_list_by_range(account_id))
            params = parse.urlencode({'application_id': self._application_id, 'account_id': id_list})
            url = self._account_url + '?' + params
            requested_id_list = requested_id_list + self.get_json_from_url(url=url)
            requested_id_list = self.write_database(data_list=requested_id_list, type_detail=False)
            time.sleep(self._request_delay)

    def request_stats_by_id(self):
        self._failed_urls = list()
        id_list = self.get_id_list(get_entire_list=True)
        total_count = len(id_list)
        count = 0
        sub_id_list = list()
        result_list = list()
        print('Task: Total request number to be executed: %s%d%s' % (
            ansi.BLUE, int(np.ceil(total_count / self._account_id_step)), ansi.ENDC))
        for account_id in id_list:
            sub_id_list.append(account_id)
            if len(sub_id_list) == self._account_id_step or total_count - count < self._account_id_step:
                result_list = self.get_stats_from_api(result_list=result_list, id_list=sub_id_list)
                sub_id_list = list()
                count += self._account_id_step
        while self._failed_urls:
            self.get_stats_from_failed_api()
        print('Stats by id request finished!')

    def request_stats_by_date(self, date_list):
        self._failed_urls = list()
        id_list = self.get_id_list(get_entire_list=False)
        print('Task: Total request number to be executed: %s%d%s' % (
            ansi.BLUE, len(id_list), ansi.ENDC))
        result_list = list()
        for account_id in id_list:
            result_list = self.get_stats_from_api(result_list=result_list, id_list=list(account_id),
                                                  date_list=date_list)
        while self._failed_urls:
            self.get_stats_from_failed_api()
        print('Stats by date request finished!')

    def get_stats_from_api(self, result_list=list(), id_list=list(), date_list=list()):
        if not date_list:
            id_list = self.list_to_url_params(id_list)
            parameter = parse.urlencode({'application_id': self._application_id, 'account_id': id_list})
            main_url = self._account_url
        else:
            date_para = self.list_to_url_params(date_list)
            parameter = parse.urlencode(
                {'application_id': self._application_id, 'account_id': id_list[0], 'date_list': date_para})
            main_url = self._stats_by_date_url

        url = main_url + '?' + parameter
        result_list = result_list + self.get_json_from_url(url=url)
        time.sleep(self._request_delay)
        return self.write_database(data_list=result_list)

    def get_stats_from_failed_api(self, result_list=list()):
        failed_url_list = self._failed_urls
        self._failed_urls = list()
        for url in failed_url_list:
            result_list = result_list + self.get_json_from_url(url=url)
        self.write_database(data_list=result_list, force_write=True)

    def get_json_from_url(self, url):
        numberOfTry = self._url_req_trynumber
        json_returned = {'status': 'ini', 'data': {}}
        while numberOfTry > 0:
            try:
                while json_returned['status'] != 'ok':
                    if json_returned['status'] is not 'ini':
                        print('%s API error message: %s%s' % (ansi.RED, json_returned['error'], ansi.ENDC))
                    json_returned = json.loads(
                        request.urlopen(url, timeout=self._url_req_timeout).read().decode('utf-8'))
                break
            except (error.URLError, timeoutError, ConnectionResetError) as e:  # API url request failed
                print('%sAPI request failed!%s %s' % (ansi.RED, e, ansi.ENDC))
                self._failed_urls.append(url)
                if e is timeoutError:
                    time.sleep(self._request_delay)
                numberOfTry -= 1
        json_list = list()
        for account_id_item in json_returned['data'].items():
            json_list.append(json.dumps(account_id_item))
        return json_list

    def write_database(self, data_list, type_detail=True, force_write=False):
        msg = 'Start recording details...' if type_detail else 'Start recording ids...'
        if len(data_list) >= self._size_per_write or force_write:
            print(msg)
            if type_detail:
                self._db.write_detail(data_list)
            else:
                self._db.write_accountid(data_list)
            data_list = list()
        return data_list

    def update_database_winrate(self, start=datetime.date.today(), end=datetime.date.today()):
        self._db.update_winrate(start=start, end=end)

    def get_id_list(self, get_entire_list=True):
        print('Reading ID list...')
        idlist = self._db.get_id_list(get_entire_idlist=get_entire_list)
        print('%sID list read finished%s' % (ansi.GREEN, ansi.ENDC))
        return idlist

    def generate_id_list_by_range(self, account_ID):
        ids = []
        for i in range(self._account_id_step):
            ids.append(int(account_ID + i))
        return ids

    def list_to_url_params(self, list):
        return ','.join(str(item) for item in list)

    def single_day_request(self, date):
        timer_start = datetime.datetime.now()
        aux_functions.check_ip()
        self._date = date
        self.request_all_ids()
        self.request_stats_by_id()
        self.update_database_winrate(start=date, end=date)

        time_usage = datetime.datetime.now() - timer_start
        print('\n%s%s%s data update finished, time usage: %s%s%s\n' % (
            ansi.BLUE, date.strftime(self._date_format), ansi.ENDC, ansi.DARKGREEN, time_usage,
            ansi.ENDC))
        return time_usage

    def main_request(self, start_date=None, days=7):
        # request all IDs, only need to execute once per (month, year) ?
        # request_all_ids(account_url, application_id)
        last_date = None
        start = datetime.date.today()
        if start_date is not None:
            d = datetime.datetime.strptime(start_date, self._date_format)
            start.replace(year=d.year, month=d.month, day=d.day)

        while days > 0:
            if start != last_date:
                last_date = start
                self.single_day_request(date=last_date)
                days -= 1
            else:
                time.sleep(1800)
            start = datetime.date.today()
        return 'Main request finished!'


if __name__ == '__main__':
    result = WowsAPIRequest().main_request(start_date='2017-07-25')
    print(result)
