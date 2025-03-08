import os
import re
import html
import json
import unicodedata

def delete_json(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        pretty_print_green(f"JSON file has been deleted at filepath: {file_path}")
    else:
        pretty_print_red(f"No JSON file was found at filepath: {file_path}")
    return

def all_JSON_fields(json_object):
    fin = []
    for field_name in json_object:
        fin.append(field_name)
    return fin

def unique_JSON_fields(file_path):
    attributes_list = []
    all_attributes = set()
    with open(file_path, "r") as fhand:
        for line in fhand:
            entry = json.loads(line)
            attributes = set(entry.keys())
            all_attributes.update(attributes)
            attributes_list.append(attributes)
    return attributes_list

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

def enforce_snake_case(inp):
    inp2 = re.sub(r"(?<!^)(?=[A-Z])", "_", inp)
    return inp2.lower()

def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(
            f"Input must be type <string> but was type <{type(inp).__name__}>"
        )
    inp2 = re.sub(r"\n+", "\n", inp)
    return inp2.strip()


def remove_unicode(inp):

    def is_printable(char):
        return char.isprintable() and not unicodedata.category(char).startswith("C")

    inp2 = "".join(char for char in inp if is_printable(char))
    return inp2


def remove_html_entities(inp):
    inp2 = html.unescape(inp)
    replacements = {
        "\xa0": " ",
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00ab": '"',
        "\u00bb": '"',
        "\u02c6": "^",
        "\u2039": "<",
        "\u203a": ">",
        "\u02dc": "~",
        "\u00a9": "(c)",
        "\u00ae": "(R)",
        "\u2122": "(TM)",
        "\u00b0": "°",
        "\u00b7": "*",
        "\u00b1": "+/-",
        "\u00bc": "1/4",
        "\u00bd": "1/2",
        "\u00be": "3/4",
    }
    for old_char, new_char in replacements.items():
        inp2 = inp2.replace(old_char, new_char)
    return inp2


def remove_html_xml_tags(inp):
    tag_pattern = re.compile(r"</?[^>]+>")
    tags = tag_pattern.findall(inp)
    clean_text = tag_pattern.sub("", inp)
    return clean_text, tags


def remove_excess_whitespace(inp):
    cleaned_text = re.sub(r"\s+", " ", inp)
    return cleaned_text.strip()