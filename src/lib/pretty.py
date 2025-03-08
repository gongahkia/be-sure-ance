import json


def pretty_print_json(json_object):
    print(json.dumps(json_object, indent=4))


def pretty_print_red(text):
    RED = "\033[91m"
    RESET = "\033[0m"
    print(f"{RED}{text}{RESET}")


def pretty_print_green(text):
    GREEN = "\033[92m"
    RESET = "\033[0m"
    print(f"{GREEN}{text}{RESET}")


def pretty_print_yellow(text):
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    print(f"{YELLOW}{text}{RESET}")


def pretty_print_blue(text):
    BLUE = "\033[94m"
    RESET = "\033[0m"
    print(f"{BLUE}{text}{RESET}")


def pretty_print_magenta(text):
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    print(f"{MAGENTA}{text}{RESET}")


def pretty_print_cyan(text):
    CYAN = "\033[96m"
    RESET = "\033[0m"
    print(f"{CYAN}{text}{RESET}")
