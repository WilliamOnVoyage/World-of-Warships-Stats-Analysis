import flask
import pandas.io.json as pd_json
import os
from enum import Enum
from wows_stats.database.mongo_db import MongoDB

DB_TYPE = 'mongo'
CONFIG_FILE = os.path.join("config", "config.json")
DB = MongoDB(CONFIG_FILE)
app = flask.Flask(__name__)


class StatsType(Enum):
    Overall = 0
    Weekly = 1
    Monthly = 2


@app.route('/')
def index():
    return flask.render_template("WOWS_Stats.html")


@app.route('/databaseinfo')
def get_database_info():
    battle_threshold = flask.request.args.get('battles', 0, type=int)
    active_player_number = DB.get_database_info(battles_threshold=battle_threshold)
    return flask.jsonify(active_player_number=active_player_number)


@app.route('/overallstats')
@app.route('/weeklystats')
@app.route('/monthlystats')
def get_stats():
    battle_threshold = flask.request.args.get('battles', 0, type=int)
    stats_type = flask.request.args.get('statsType', 0, type=int)
    stats_functions = {StatsType.Overall: DB.get_top_players(battles_threshold=battle_threshold),
                       StatsType.Weekly: DB.get_top_players_in_week(battles_threshold=battle_threshold),
                       StatsType.Monthly: DB.get_top_players_in_month(battles_threshold=battle_threshold)}
    player_list = stats_functions[stats_type]
    return flatten_json(json_list=player_list)


def flatten_json(json_list):
    flattened_list = list()
    for json_item in json_list:
        flattened_list.append(pd_json.json_normalize(json_item).to_json(orient='records'))
    return flask.jsonify(player_list=flattened_list)


if __name__ == '__main__':
    app.run(debug=False)
