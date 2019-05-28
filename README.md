# World of Warships Stats Analysis and Web Application

[![Build Status](https://travis-ci.org/WilliamOnVoyage/World-of-Warships-Stats-Analysis.svg?branch=master)](https://travis-ci.org/WilliamOnVoyage/World-of-Warships-Stats-Analysis) ![AWS CodeBuild](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiVSthN0QzYzd5RnFqN1lpNkdGVjBXMncvRlREandzYVRWWng4anh1dlFOSGlhWnh6VmhCSXpzUXE3MU5wMWttNlpzMXl6THFkR1pKbFJZeThwTjIxQ2RNPSIsIml2UGFyYW1ldGVyU3BlYyI6Ii8wN20zYTVqbWthaHJOTlgiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master) [![Test Coverage](https://codeclimate.com/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/badges/coverage.svg)](https://codeclimate.com/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/coverage) [![Maintainability](https://api.codeclimate.com/v1/badges/60dd12c25dd6fa7e97b4/maintainability)](https://codeclimate.com/github/WilliamOnVoyage/World-of-Warships-Stats-Analysis/maintainability)
[![Pythonversion](https://img.shields.io/badge/python-3.5-blue.svg)](https://sourceforge.net/projects/winpython/files/WinPython_3.5/3.5.2.3/) [![MongoDB](https://img.shields.io/badge/mongo-3.4-blue.svg)](https://docs.mongodb.com/manual/release-notes/3.4/?_ga=2.148716407.1370168894.1503081314-630273995.1503081314) [![Tensorflow](https://img.shields.io/badge/tensorflow-1.0.1-blue.svg)](https://github.com/tensorflow/tensorflow/tree/r1.0) 
## System Design
![Architecture diagram](WOWS_Architecture.png)

_Created using [Gliffy](www.gliffy.com)_
### Major classes

|Class|Description|functions|attributes|
|:----|:----|:----|:----|
|**wows_api**|...|...|...|
|**abstract_db**|...|...|...|
|**prediction_model**|...|...|...|
|**web_connector**|...|...|...|

## API
This python based script handles [World of Warships API request](https://developers.wargaming.net/) for statistical data and store them in local MySQL database. The World of Warships API needs an application_id for credential connection with the API server, the application_id should be registered on [Wargaming.net](https://developers.wargaming.net/applications/) and stored in a local configuration file named as "[config.json](#local-configuration-file-format)". Also the ip address of the terminal running this script (provided by package [ipgetter](https://pypi.python.org/pypi/ipgetter/0.6)) should be added in your application launched on [developer room of Wargaming.net](https://developers.wargaming.net/applications/).

There are several limitations, as well as specific JSON format regarding different types of the API request (refer to [Wargaming.net API reference](https://developers.wargaming.net/reference/all/wot/account/list/?application_id=bc7a1942582313fd553a85240bd491c8&r_realm=ru)), please check based on your need.

## Database
### MongoDB
Since the API request returns JSON format data, it is natural to use MongoDB (BSON) for data storing. The newest and historical stats of a player differ a little. To be consistent with the data, we store the newest stats and historical stats differently.

### ~~MySQL [Deprecated]~~
The script connects relational database (MySQL, AWS RDS, etc.) for storing extracted data. The players' id list is stored in an individual table `wows_idlist`, which is essential for efficient API request since the complete id list is not officially provided, and the account number is sparsely distributed in a large range ([WOWS account number range](#account-id-range)). Some statistics like the number of battles are stored in `wows_stats`, and you can customize your own database as well.
The players' statistical data can then be retrieved through SQL and analyzed for your own purpose.

***We replaced the ~~MySQL~~ with MongoDB due to the performance limitation.***

#### Newest stats:
```
{
      "_id":1008331251,
      "daily_stats":{
            ObjectId('000000201701011008331251'),
            ...
      },
      "account_id": 1008331251,
      "nickname": "zmlzeze",
      "last_battle_time": 1500140223,
      "leveling_tier": 15,
      "created_at": 1435322987,
      "leveling_points": 8612323,
      "updated_at": 1500053592,
      "private": null,
      "hidden_profile": false,
      "logout_at": 1500053581,
      "karma": null,
      "statistics": {
        "distance": 117155,
        "battles": 3143,
        "pvp": {
        ...
        }
      },
      "stats_updated_at": 1500140964
    }
```
#### Historical stats:
```
{
      "_id":ObjectId('000000201701011008331251'),
      "capture_points": 399,
      "account_id": 1008331251,
      "max_xp": 4913,
      "wins": 1742,
      "planes_killed": 5550,
      "battles": 2882,
      "damage_dealt": 213130514,
      "battle_type": "pvp",
      "date": "20170101",
      "xp": 3923528,
      "frags": 3612,
      "survived_battles": 1356,
      "dropped_capture_points": 3629
}
```
The database provides stats for modeling and web application, thus the performance is crucial. For NA server, the player number is about 1.6 million, and about 30% play at least 100 battles (considered as **valid players**). Since each player has daily update, the total number of historical stats will keep increasing with time. Based on estimation, the newest stats for **1.6 million** players take up to **2 GB** memory, while the historical stats of valid players over **a year** take about **50 GB** memory on disk. 

## Analysis
### Data Preprocessing
When retrieving players' data from database, we use `pandas` Panel to construct the 3D DataFrame as:

|ID\day|1|2|3|...|
|:----:|:----:|:----:|:----:|:----:|
|10001|[t,w,l,d]|[t,w,l,d]|[t,w,l,d]|...|
|10002|[t,w,l,d]|[t,w,l,d]|[t,w,l,d]|...|
|10003|[t,w,l,d]|[t,w,l,d]|[t,w,l,d]|...|
|...|...|...|...|...|

The `[t,w,l,d]` is the vector of one day's stats of `[battles,wins,losses,draws]`.

### LSTM Model
We use the LSTM without attention model to predict the players' performance based on previous days' stats. The prediction is within certain time window and the objective is to minimize the distance between the ground truth and predicted stats vectors:

### Local configuration file format
```
{
  "wows_api": {
    "application_id": "XXX",
    "player_url": "https://api.worldofwarships.com/wows/account/list/",
    "account_url": "https://api.worldofwarships.com/wows/account/info/",
    "stats_by_date_url": "https://api.worldofwarships.com/wows/account/statsbydate/",
    "DB_TYPE": "mongo",
    "DATE_FORMAT": "%Y-%m-%d",
    "NA_ACCOUNT_LIMIT_LO": 1000000000,
    "NA_ACCOUNT_LIMIT_HI": 2000000000,
    "ID_STEP": 100,
    "SIZE_PER_WRITE": 10000,
    "URL_REQ_DELAY": 0,
    "URL_REQ_TIMEOUT": 45,
    "URL_REQ_TRYNUM": 3
  },
  "mysql": {
    "dbname": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XX.XX.XX.XX",
    "port": 123
  },
  "mongo": {
    "dbname": "XXX",
    "collection": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XX.XX.XX.XX",
    "port": 123
  },
  "AWS_RDS": {
    "dbname": "XXX",
    "usr": "XXX",
    "pw": "XXX",
    "hostname": "XX.XX.XX.XX",
    "port": 123
  }
}
```
#### Account id range:
* [0, 500000000) : 'RU';
* [500000000, 1000000000) : 'EU';
* [1000000000, 2000000000) : 'NA';
* [2000000000, 3000000000) : 'ASIA';
* [3000000000, ) : 'KR';

## Web Application
We use the [Flask](http://flask.pocoo.org/) framework to develop the front-end web application with Python back-end.
### HTML/JavaScript front-end

### Python back-end
---
More projects on [my private repository summary](https://williamonvoyage.github.io/Private-Repository-Summary/)
