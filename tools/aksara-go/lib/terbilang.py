"""Indonesian number words (terbilang) and Indonesian number display formatting.

Canonical form: lowercase, single spaces, `se-` forms for 10/11/100/1000
(sepuluh, sebelas, seratus, seribu), `satu` before juta/miliar/triliun,
decimals as `koma` followed by each digit read individually.
"""

import re

UNITS = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
SCALES = [(10**12, "triliun"), (10**9, "miliar"), (10**6, "juta"), (10**3, "ribu")]
MAX_INT = 10**15 - 1  # up to 999 triliun

VOCABULARY = set(UNITS) | {"sepuluh", "sebelas", "seratus", "seribu", "belas", "puluh", "ratus", "koma"} | {
    name for _, name in SCALES
}

MINUS = "−"


def _below_thousand(n):
    words = []
    hundreds, rest = divmod(n, 100)
    if hundreds == 1:
        words.append("seratus")
    elif hundreds > 1:
        words += [UNITS[hundreds], "ratus"]
    if rest >= 20:
        tens, unit = divmod(rest, 10)
        words += [UNITS[tens], "puluh"]
        if unit:
            words.append(UNITS[unit])
    elif rest >= 12:
        words += [UNITS[rest - 10], "belas"]
    elif rest == 11:
        words.append("sebelas")
    elif rest == 10:
        words.append("sepuluh")
    elif rest > 0:
        words.append(UNITS[rest])
    return words


def words_int(n):
    """Canonical terbilang of a non-negative integer up to 999 triliun."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0 or n > MAX_INT:
        raise ValueError(f"unsupported number: {n!r}")
    if n == 0:
        return "nol"
    words = []
    for scale, name in SCALES:
        count, n = divmod(n, scale)
        if count == 0:
            continue
        if scale == 1000 and count == 1:
            words.append("seribu")
        else:
            words += _below_thousand(count) + [name]
    words += _below_thousand(n)
    return " ".join(words)


def words_decimal(int_part, frac_digits):
    """Terbilang of a decimal, e.g. (3, "25") becomes "tiga koma dua lima"."""
    if not frac_digits or not frac_digits.isdigit():
        raise ValueError(f"invalid decimal digits: {frac_digits!r}")
    return words_int(int_part) + " koma " + " ".join(UNITS[int(d)] for d in frac_digits)


_UNIT_VALUE = {w: i for i, w in enumerate(UNITS) if i > 0}
_SCALE_VALUE = {name: scale for scale, name in SCALES}


def parse_words(text):
    """Words to integer (integers only). Returns None unless `text` is exactly canonical terbilang."""
    if not isinstance(text, str) or not text:
        return None
    if text == "nol":
        return 0
    total = 0
    group = 0      # value accumulated for the current < 1000 group
    pending = None  # last unit word not yet consumed by belas/puluh/ratus
    try:
        for tok in text.split(" "):
            if tok in _UNIT_VALUE:
                if pending is not None:
                    return None
                pending = _UNIT_VALUE[tok]
            elif tok in ("belas", "puluh", "ratus"):
                if pending is None:
                    return None
                group += {"belas": pending + 10, "puluh": pending * 10, "ratus": pending * 100}[tok]
                pending = None
            elif tok in ("sepuluh", "sebelas", "seratus"):
                group += {"sepuluh": 10, "sebelas": 11, "seratus": 100}[tok]
            elif tok == "seribu":
                if group or pending is not None:
                    return None
                total += 1000
            elif tok in _SCALE_VALUE:
                group += pending or 0
                pending = None
                if group == 0:
                    return None
                total += group * _SCALE_VALUE[tok]
                group = 0
            else:
                return None
        total += group + (pending or 0)
    except (KeyError, TypeError):
        return None
    # Round-trip guarantees the text was canonical (rejects "dua dua", "satu ribu", ...).
    try:
        return total if words_int(total) == text else None
    except ValueError:
        return None


def format_int(n):
    """Indonesian display: '.' thousands separator only from 10.000 upward; U+2212 for negatives."""
    if n < 0:
        return MINUS + format_int(-n)
    if n < 10000:
        return str(n)
    return f"{n:,}".replace(",", ".")


def format_decimal(int_part, frac_digits):
    return f"{format_int(int_part)},{frac_digits}"


_DISPLAY = re.compile(r"^(\d{1,3}(?:\.\d{3})+|\d{1,4})(?:,(\d+))?$")


def parse_display(text):
    """Parse an Indonesian display number. Returns (int_part, frac_digits or None) or None if not canonical."""
    if not isinstance(text, str):
        return None
    m = _DISPLAY.match(text)
    if not m:
        return None
    int_part = int(m.group(1).replace(".", ""))
    frac = m.group(2)
    canonical = format_int(int_part) if frac is None else format_decimal(int_part, frac)
    return (int_part, frac) if canonical == text else None
