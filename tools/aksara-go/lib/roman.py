"""Roman numerals, standard subtractive notation only, 1-3999."""

import re

_VALUES = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
           (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
_CANONICAL = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
LETTERS = ["I", "V", "X", "L", "C", "D", "M"]


def to_roman(n):
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 3999:
        raise ValueError(f"unsupported number: {n!r}")
    out = []
    for value, symbol in _VALUES:
        count, n = divmod(n, value)
        out.append(symbol * count)
    return "".join(out)


def from_roman(text):
    """Integer value of a canonical Roman numeral, or None (rejects IIII, VV, IC, ...)."""
    if not isinstance(text, str) or not text or not _CANONICAL.match(text):
        return None
    total, i = 0, 0
    for value, symbol in _VALUES:
        while text.startswith(symbol, i):
            total += value
            i += len(symbol)
    return total if i == len(text) and to_roman(total) == text else None
