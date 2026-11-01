"""One-unknown equations for cari-x (`? + 3 = 7`, `2x − 5 = 9`, `2ˣ = 32`, `²log x = 5`)."""

from lib import expr

SEARCH_RANGE = range(-1000, 1001)


def parse(text):
    if not isinstance(text, str) or text.count("=") != 1:
        raise expr.ExprError("equation must contain exactly one '='")
    left, right = text.split("=")
    return expr.parse(left, allow_vars=True), expr.parse(right, allow_vars=True)


def holds(parsed, x):
    left, right = parsed
    try:
        return expr.evaluate(left, {"x": x}) == expr.evaluate(right, {"x": x})
    except expr.ExprError:
        return False  # e.g. log of a non-positive number: not a solution


def solutions(text, search=SEARCH_RANGE):
    """All integer solutions in the checked range."""
    parsed = parse(text)
    return [x for x in search if holds(parsed, x)]
