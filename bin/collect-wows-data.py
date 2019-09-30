import argparse
import datetime
from wows_stats.api.wows_api import WowsAPIRequest


def create_parser():
    parser = argparse.ArgumentParser(description="Input args for collect WOWS data command")
    parser.add_argument("-d", "--date", help="The starting date of players' data to collect, YYYY-mm-dd format",
                        dest="date",
                        default=datetime.datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("-c", "--config", help="Configuration file path for starting the data collection",
                        dest="config", required=True)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    WowsAPIRequest(args.config).request_historical_stats_all_accounts_last_month(args.date)


if __name__ == "__main__":
    main()
