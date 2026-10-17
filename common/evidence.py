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


def quote_found(quote: str, source: str, min_words: int = 3, max_gap: int = 200) -> bool:
    """True if the quote (ignoring case, punctuation and spacing) appears in the source, as whole words.

    A quote shorter than min_words is too easy to match by accident, so it doesn't count as evidence.
    An ellipsis splits the quote into pieces: each piece must appear, in order, with no more than max_gap
    characters between one piece and the next, so a quote can't be stitched together from scattered words.
    """
    pieces = [normalize(p) for p in re.split(r"\.\.\.|…", quote)]
    pieces = [p for p in pieces if p]
    if not pieces or len(" ".join(pieces).split()) < min_words:
        return False
    if len(pieces) > 1 and min(len(p.split()) for p in pieces) < 2:
        return False  # "the part ... is ... in" is a few common words, not a quote
    haystack = normalize(source)

    def from_(start: int, rest: list[str]) -> bool:
        if not rest:
            return True
        for m in re.finditer(rf"(?<!\w){re.escape(rest[0])}(?!\w)", haystack[start:]):
            at = start + m.start()
            if start and at - start > max_gap:
                return False
            if from_(at + len(rest[0]), rest[1:]):
                return True
        return False

    return from_(0, pieces)


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


NUMBER = re.compile(
    r"(?<![\w.])[-+−]?\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s?(?:k|K|M|million|billion|thousand)\b)?%?"
)
SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "billion": 1e9}


def numbers_in(text: str) -> list[str]:
    return [m.group() for m in NUMBER.finditer(text)]


def to_float(token: str) -> float:
    """The value of a number as written: "$5k" is 5000, "-$1,200" is -1200, "−3.5%" is -3.5."""
    t = token.replace("−", "-").replace("$", "").replace(",", "").replace("%", "").replace("+", "").strip()
    m = re.match(r"(-?[\d.]+)\s?([A-Za-z]+)?$", t)
    if not m:
        return float(t)
    value = float(m.group(1))
    return value * SCALE.get((m.group(2) or "").lower(), 1)


def unsupported_numbers(text: str, allowed: list[float], tolerance: float = 0.005, ignore_small: int = 10) -> list[str]:
    """Numbers in the text that don't match an allowed value (within a relative tolerance, for rounding).

    Small whole numbers (counts like "3 jobs", list numbering) are ignored up to ignore_small, and so are
    four-digit years, but never a number written as money ($) or a percent, or with a scale ("$5k", "3M"):
    those are always checked. Signs count: -2% isn't 2%.
    """
    bad = []
    for token in numbers_in(text):
        value = to_float(token)
        money_like = "$" in token or "%" in token or re.search(r"[A-Za-z]", token)
        if not money_like and value.is_integer():
            if abs(value) <= ignore_small or (1900 <= value <= 2100 and "," not in token):
                continue
        if not any(abs(value - a) <= max(abs(a) * tolerance, 0.051) for a in allowed):
            bad.append(token)
    return bad
