class AnsiEscapeCode:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    DARKGREEN = '\033[32m'


def test_ansi_code():
    print(AnsiEscapeCode.RED + "This is to test" + AnsiEscapeCode.ENDC)


if __name__ == "__main__":
    test_ansi_code()
