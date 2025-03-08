import re
import html
import unicodedata

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