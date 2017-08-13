import flask

from database.db_connector import DatabaseConnector

app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template("hello.html")


@app.route('/overallstats')
# Access database, get the recent stats and return in JSON format?
def get_overall_stats():
    battle_threshold = flask.request.args.get('battles', 0, type=int)
    active_player_number = request_id_list_from_database(battle_threshold=battle_threshold)
    return_value = flask.jsonify(active_player_number=active_player_number)
    return return_value


def request_id_list_from_database(battle_threshold=10):
    _db = DatabaseConnector(database_type='mongo')
    return _db.get_database_info(threshold=battle_threshold)


if __name__ == '__main__':
    app.run(debug=False)
