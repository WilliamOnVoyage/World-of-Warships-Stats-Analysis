import WOWS.WOWS_API as wows
import util.read_config as config
import coverage


def test_WOWS_API():
    wows.check_ip()
    wows.check_date()


if __name__ == "__main__":
    test_WOWS_API()
    cg = config.config()
    json_data = cg.read_config(config_file="sample_config.json")
    print(json_data)
