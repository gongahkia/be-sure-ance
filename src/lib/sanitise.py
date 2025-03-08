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
    inp = re.sub(r"\n+", "\n", inp)
    inp = re.sub(r"[ \t\u200b]+", " ", inp)
    return inp.strip()

def remove_unicode(inp):

    def is_printable(char):
        return char.isprintable() and not unicodedata.category(char).startswith("C")

    inp2 = "".join(char for char in inp if is_printable(char))
    return inp2

def remove_html_entities(inp):
    inp2 = html.unescape(inp)
    replacements = {
        "\xa0": " ",       # Non-breaking space
        "\u200b": "",      # Zero-width space
        "\u2013": "-",     # En dash
        "\u2014": "--",    # Em dash
        "\u2026": "...",   # Ellipsis
        "\u2018": "'",     # Left single quote
        "\u2019": "'",     # Right single quote
        "\u201c": '"',     # Left double quote
        "\u201d": '"',     # Right double quote
        "\u00ab": '"',     # Left guillemet
        "\u00bb": '"',     # Right guillemet
        "\u02c6": "^",     # Circumflex
        "\u2039": "<",     # Single left angle quote
        "\u203a": ">",     # Single right angle quote
        "\u02dc": "~",     # Small tilde
        "\u00a9": "(c)",   # Copyright symbol
        "\u00ae": "(R)",   # Registered trademark symbol
        "\u2122": "(TM)",  # Trademark symbol
        "\u00b0": "°",     # Degree symbol
        "\u00b7": "*",     # Middle dot
        "\u00b1": "+/-",   # Plus-minus symbol
        "\u00bc": "1/4",   # One-quarter fraction
        "\u00bd": "1/2",   # One-half fraction
        "\u00be": "3/4",   # Three-quarters fraction
        "&lt;": "<",       # Less-than sign (HTML entity)
        "&gt;": ">",       # Greater-than sign (HTML entity)
        "&amp;": "&",      # Ampersand (HTML entity)
        "&quot;": '"',     # Quotation mark (HTML entity)
        "&apos;": "'",     # Apostrophe (HTML entity)
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