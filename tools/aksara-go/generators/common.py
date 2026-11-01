"""Helpers shared by the procedural generators."""

from lib import terbilang

MINUS = "−"
_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def fmt(n):
    return terbilang.format_int(n)


def sup(n):
    """Superscript digits for exponents and logarithm bases (e.g. 3 -> ³)."""
    return str(n).translate(_SUP)


def neg_paren(n):
    """Display a value inside an expression: negatives in parentheses, e.g. (−3)."""
    return f"({MINUS}{fmt(-n)})" if n < 0 else fmt(n)


def numeric_options(rng, answer, extra=(), nonneg=False):
    """4 distinct integers including the answer: plausible slips first, then small offsets."""
    pool = [v for v in extra if v != answer]
    pool += [answer + d for d in (1, -1, 2, -2, 10, -10, 5, -5, 3, -3)]
    seen, candidates = set(), []
    for v in pool:
        if v != answer and v not in seen and (not nonneg or v >= 0):
            seen.add(v)
            candidates.append(v)
    preferred = [v for v in extra if v in seen][:2]
    rest = [v for v in candidates if v not in preferred]
    picks = preferred + rng.sample(rest, 3 - len(preferred))
    options = picks + [answer]
    rng.shuffle(options)
    return options


def pick_distinct(rng, items, count):
    items = sorted(set(items), key=str)
    return rng.sample(items, min(count, len(items)))
