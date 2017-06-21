# World of Warships API request and database

[![Build Status](https://travis-ci.org/WilliamOnVoyage/World-of-Warships-Stats-Analysis.svg?branch=master)](https://travis-ci.org/WilliamOnVoyage/World-of-Warships-Stats-Analysis) [![Pythonversion](https://img.shields.io/badge/python-3.5-blue.svg)](https://sourceforge.net/projects/winpython/files/WinPython_3.5/3.5.2.3/) [![database](https://img.shields.io/badge/mysql-5.5-orange.svg)](https://dev.mysql.com/downloads/windows/installer/5.5.html) [![Test Coverage](https://codeclimate.com/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/badges/coverage.svg)](https://codeclimate.com/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/coverage) [![Code Health](https://landscape.io/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/master/landscape.svg?style=flat)](https://landscape.io/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/master)

## API Request
This python based script handles [World of Warships API request](https://developers.wargaming.net/) for statistical data and store them in local MySQL database. The World of Warships API needs an application_id for credential connection with the API server, the application_id should be registered on [Wargaming.net](https://developers.wargaming.net/applications/) and stored in a local configuration file named as "[config.json](#local-configuration-file-format)". Also the ip address of the terminal running this script (provided by package [ipgetter](https://pypi.python.org/pypi/ipgetter/0.6)) should be added in your application launched on [developer room of Wargaming.net](https://developers.wargaming.net/applications/).

There are several limitations, as well as specific JSON format regarding different types of the API request (refer to [Wargaming.net API reference](https://developers.wargaming.net/reference/all/wot/account/list/?application_id=bc7a1942582313fd553a85240bd491c8&r_realm=ru)), please check based on your need.

## Database

The script connects relational database (MySQL, AWS RDS, etc.) for storing extracted data. The players' id list is stored in an individual table `wows_idlist`, which is essential for efficient API request since the complete id list is not officially provided, and the account number is sparsely distributed in a large range ([WOWS account number range](#account-id-range)). Some statistics like the number of battles are stored in `wows_stats`, and you can customize your own database as well.

The players' statistical data can then be retrieved through SQL and analyzed for your own purpose.
## Analysis
### Data Preprocessing
When retrieving players' data from database, we use `pandas` Panel to construct the 3D DataFrame as:

|ID\day|1|2|3|...|
|:----:|:----:|:----:|:----:|:----:|
|10001|[t,w,l,d]|[t,w,l,d]|[t,w,l,d]|...|
|10002|[t,w,l,d]|[t,w,l,d]|[t,w,l,d]|...|
|10003|[t,w,l,d]|[t,w,l,d]|[t,w,l,d]|...|

The `[t,w,l,d]` is the vector of one day's stats of `[total,win,loss,draw]`.

### LSTM Model
We use LSTM without attention model to predict the players' performance based on previous days' stats. The prediction is within certain time window and the objective is to minimize the distance between the ground truth and predicted stats vectors:

----
### Local configuration file format
```
{
  "wows_api": {
    "application_id": "XXX",
    "player_url": "https://api.worldofwarships.com/wows/account/list/",
    "account_url": "https://api.worldofwarships.com/wows/account/info/"
  },
  "mysql": {
    "dbname": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XXX",
    "port": 0000
  },
  "AWS_RDS": {
    "dbname": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XXX",
    "port": 0000
  }
}
```
### Account id range
* [0, 500000000) : 'RU';
* [500000000, 1000000000) : 'EU';
* [1000000000, 2000000000) : 'NA';
* [2000000000, 3000000000) : 'ASIA';
* [3000000000, ) : 'KR';

---
More projects on [my private repository summary](https://williamonvoyage.github.io/Private-Repository-Summary/)
