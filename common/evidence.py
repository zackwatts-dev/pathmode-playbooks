"""Checks that run in code on what the model said, so a confident wrong answer gets caught.

The model is asked to quote its source. These functions check that the quote is really there, and that the
numbers in its prose are numbers we gave it.
"""

from __future__ import annotations

import re


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[^\w$%.' -]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def quote_found(quote: str, source: str, min_words: int = 3) -> bool:
    """True if the quote (ignoring case, punctuation and spacing) appears in the source.

    A quote shorter than min_words is too easy to match by accident, so it doesn't count as evidence.
    An ellipsis splits the quote into pieces, and each piece must appear.
    """
    pieces = [normalize(p) for p in re.split(r"\.\.\.|…", quote)]
    pieces = [p for p in pieces if p]
    if not pieces or len(" ".join(pieces).split()) < min_words:
        return False
    haystack = normalize(source)
    return all(re.search(rf"(?<!\w){re.escape(p)}(?!\w)", haystack) for p in pieces)


def value_in_quote(value: object, quote: str) -> bool:
    """True if a value the model extracted (a serial, a tag, a quantity) appears, as whole words, in the quote it
    gave as evidence. A real quote proves nothing about a value that isn't in it.

    Spaces, dashes, slashes and dots between letters and digits don't count, so "RTU-2" matches "rtu 2" and
    "4417-631" matches "4417 631". A value written differently (a date reformatted, "three" for "3") doesn't
    match, and should be checked another way or go to a person.
    """
    want = re.sub(r"[^a-z0-9]", "", str(value).lower())
    if not want:
        return False
    tokens = re.findall(r"[a-z0-9]+", str(quote).lower())
    for i in range(len(tokens)):
        joined = ""
        for t in tokens[i:]:
            joined += t
            if joined == want:
                return True
            if len(joined) >= len(want):
                break
    return False


NUMBER = re.compile(r"(?<![\w.])[-+]?\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")


def numbers_in(text: str) -> list[str]:
    return [m.group() for m in NUMBER.finditer(text)]


def to_float(token: str) -> float:
    return float(token.replace("$", "").replace(",", "").replace("%", "").replace("+", ""))


def unsupported_numbers(text: str, allowed: list[float], tolerance: float = 0.005, ignore_small: int = 10) -> list[str]:
    """Numbers in the text that don't match an allowed value (within a relative tolerance, for rounding).

    Small whole numbers (counts like "3 jobs", list numbering) are ignored up to ignore_small, and so are
    four-digit years.
    """
    bad = []
    for token in numbers_in(text):
        value = to_float(token)
        if value.is_integer() and (abs(value) <= ignore_small or (1900 <= value <= 2100 and "," not in token)):
            continue
        if not any(abs(value - a) <= max(abs(a) * tolerance, 0.051) for a in allowed):
            bad.append(token)
    return bad
