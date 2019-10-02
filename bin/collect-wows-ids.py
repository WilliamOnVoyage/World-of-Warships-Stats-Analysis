import argparse
from wows_stats.api.wows_api import WowsAPIRequest


def create_parser():
    parser = argparse.ArgumentParser(description="Input args for collect WOWS IDs command")
    parser.add_argument("-c", "--config", help="Configuration file path for starting the data collection",
                        dest="config", required=True)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    WowsAPIRequest(args.config).request_all_ids()


if __name__ == "__main__":
    main()
