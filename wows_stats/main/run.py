import wows_stats.model.winrate_model as winR_model

from src import api as wows


def database_update():
    wows.WowsAPIRequest().request_historical_stats_all_accounts_last_month(start_date='2017-09-18')


def model_update():
    winR_model.build_winrate_model()


def systemRun():
    database_update()
    model_update()
    return "Main function finished!"


if __name__ == '__main__':
    systemRun()
