"""Exact comparison of two display values for banding-angka."""

from lib import expr


def value(text):
    """Exact value of one side (integer, decimal, fraction, percent, power, root, log)."""
    return expr.evaluate_text(text)


def compare(left, right):
    a, b = value(left), value(right)
    return "<" if a < b else ">" if a > b else "="
