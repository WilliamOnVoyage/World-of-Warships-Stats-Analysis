import flask
import pandas.io.json as pd_json

import database.mongo_db

DB_TYPE = 'mongo'
DB = database.mongo_db.MongoDB()

app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template("WOWS_Stats.html")


@app.route('/databaseinfo')
def get_database_info():
    battle_threshold = flask.request.args.get('battles', 0, type=int)
    active_player_number = DB.get_database_info(battles_threshold=battle_threshold)
    return flask.jsonify(active_player_number=active_player_number)


@app.route('/overallstats')
def get_overall_stats():
    battle_threshold = flask.request.args.get('battles', 0, type=int)
    player_list = DB.get_top_players_by_battles(battles_threshold=battle_threshold)
    flattened_player_list = list()
    for player in player_list:
        flattened_player_list.append(pd_json.json_normalize(player).to_json(orient='records'))
    return flask.jsonify(player_list=flattened_player_list)


if __name__ == '__main__':
    app.run(debug=False)
