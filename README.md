# World of Warships API request and database

[![Build Status](https://travis-ci.com/WilliamOnVoyage/WOWS_stats.svg?token=mAvX7VnJxpyB9MUv3mSv&branch=master)](https://travis-ci.com/WilliamOnVoyage/WOWS_stats) [![Pythonversion](https://img.shields.io/badge/winpython-3.5.2-blue.svg)](https://sourceforge.net/projects/winpython/files/WinPython_3.5/3.5.2.3/) [![database](https://img.shields.io/badge/mysql-5.5-orange.svg)](https://dev.mysql.com/downloads/windows/installer/5.5.html) [![Code Health](https://landscape.io/github/WilliamOnVoyage/WOWS_stats/master/landscape.svg?style=flat&badge_auth_token=d93c6fcebdf2479295bb05dc33fe44c3)](https://landscape.io/github/WilliamOnVoyage/WOWS_stats/master)

## API Request
This python based script handles API request for World of Warships statistical data and store them in local MySQL database. The World of Warships API needs an application_id for credential connection with the API server, the application_id should be registered on [developer room of Wargaming.net](https://developers.wargaming.net/applications/) and stored in a local configuration file named as "[config.json](#Local-configuration-file-format)". Also the ip address of the terminal running this script (provided by package [ipgetter](https://pypi.python.org/pypi/ipgetter/0.6)) should be added in your application launched on [developer room of Wargaming.net](https://developers.wargaming.net/applications/).

There are several limitations, as well as specific JSON format regarding different types of the API request (refer to [Wargaming.net API reference](https://developers.wargaming.net/reference/all/wot/account/list/?application_id=bc7a1942582313fd553a85240bd491c8&r_realm=ru)), please check for your own purpose.

## Database

The script connects relational database (MySQL, AWS RDS, etc.) for storing extracted data. The players' id list is stored in an individual table `wows_idlist`, which is essential for efficient API request since the complete id list is not officially provided, and the account number is sparsely distributed in a large range ([WOWS account number range](#Account-id-range)). Some statistics like number of battles are stored in `wows_stats`, and you can customize the database for your own purpose.

----
### Local configuration file format

{
    "wows_api": {
    "application_id": "XXXX",
    "player_url": "https://api.worldofwarships.com/wows/account/list/",
    "account_url": "https://api.worldofwarships.com/wows/account/info/",
    ...
  },
  "mysql": {
    "dbname": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XXX",
    "port": XXXX
  },
  "AWS_RDS": {
    "dbname": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XXX",
    "port": XXXX
  }
  ...
}
---
### Account id range
[0,500000000) : 'RU';
[500000000,1000000000) : 'EU';
[1000000000,2000000000) : 'NA';
[2000000000,3000000000) : 'ASIA';
[3000000000, no limit) : 'KR';