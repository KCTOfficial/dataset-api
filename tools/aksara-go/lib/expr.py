"""Safe arithmetic expression parsing and exact evaluation.

A closed grammar (no eval/exec): integers and decimals (Indonesian `,`),
`+ − × ÷ / ^`, superscript exponents (`2³`, `2ˣ`), parentheses, `√`, `∛`,
logarithms in Indonesian notation (`²log 8`, `log 1000`), postfix `%`, and
the unknowns `x` / `?` when variables are enabled. Evaluation uses
`fractions.Fraction`, so results are exact.

ASCII `-`, `*` and `/` are accepted by the parser (for tests and fractions);
display-text rules are enforced separately by `display_errors`.
"""

import re
from fractions import Fraction

MINUS = "−"
SUPERSCRIPTS = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "ˣ": "x"}
MAX_EXPONENT = 1100
_NUMBER = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")


class ExprError(ValueError):
    pass


def _number_value(text):
    int_text, _, frac_text = text.replace(".", "").partition(",")
    value = Fraction(int(int_text))
    if frac_text:
        value += Fraction(int(frac_text), 10 ** len(frac_text))
    return value


def tokenize(text, allow_vars=False):
    if not isinstance(text, str) or not text.strip():
        raise ExprError("empty expression")
    tokens = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        m = _NUMBER.match(text, i)
        if m and ch.isdigit():
            tokens.append(("num", _number_value(m.group(0))))
            i = m.end()
            continue
        if ch in SUPERSCRIPTS:
            j = i
            while j < n and text[j] in SUPERSCRIPTS:
                j += 1
            sup = "".join(SUPERSCRIPTS[c] for c in text[i:j])
            k = j
            while k < n and text[k] == " ":
                k += 1
            if text.startswith("log", k):
                if not sup.isdigit() or int(sup) < 2:
                    raise ExprError(f"invalid logarithm base {sup!r}")
                tokens.append(("log", int(sup)))
                i = k + 3
            else:
                if sup != "x" and not sup.isdigit():
                    raise ExprError(f"invalid superscript {text[i:j]!r}")
                if sup == "x" and not allow_vars:
                    raise ExprError("variables are not allowed here")
                tokens.append(("sup", sup))
                i = j
            continue
        if text.startswith("log", i):
            i += 3
            base = 10
            if i < n and text[i] == "_":
                m = re.compile(r"_(\d+)").match(text, i)
                if not m or int(m.group(1)) < 2:
                    raise ExprError("invalid logarithm base")
                base = int(m.group(1))
                i = m.end()
            tokens.append(("log", base))
            continue
        if ch in "x?":
            if not allow_vars:
                raise ExprError(f"unexpected symbol {ch!r}")
            tokens.append(("var", "x"))
            i += 1
            continue
        op = {"+": "+", "-": "-", MINUS: "-", "×": "*", "*": "*", "÷": "/", "/": "/", "^": "^",
              "(": "(", ")": ")", "%": "%", "√": "sqrt", "∛": "cbrt"}.get(ch)
        if op is None:
            raise ExprError(f"unexpected symbol {ch!r}")
        tokens.append(("op", op))
        i += 1
    return tokens


class _Parser:
    def __init__(self, tokens, allow_vars):
        self.tokens = tokens
        self.pos = 0
        self.allow_vars = allow_vars

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def take(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def expect_op(self, op):
        tok = self.take()
        if tok != ("op", op):
            raise ExprError(f"expected {op!r}")

    def parse(self):
        node = self.expr()
        if self.pos != len(self.tokens):
            raise ExprError("unexpected trailing input")
        return node

    def expr(self):
        node = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            node = ("bin", op, node, self.term())
        return node

    def _starts_implicit(self):
        kind, value = self.peek()
        return self.allow_vars and (kind == "var" or (kind, value) == ("op", "("))

    def term(self):
        node = self.factor()
        while True:
            if self.peek() in (("op", "*"), ("op", "/")):
                op = self.take()[1]
                node = ("bin", op, node, self.factor())
            elif self._starts_implicit():
                node = ("bin", "*", node, self.factor())
            else:
                return node

    def factor(self):
        if self.peek() == ("op", "-"):
            self.take()
            return ("neg", self.factor())
        return self.power()

    def power(self):
        node = self.postfix()
        kind, value = self.peek()
        if (kind, value) == ("op", "^"):
            self.take()
            return ("pow", node, self.factor())
        if kind == "sup":
            self.take()
            exponent = ("var", "x") if value == "x" else ("num", Fraction(int(value)))
            return ("pow", node, exponent)
        return node

    def postfix(self):
        node = self.primary()
        if self.peek() == ("op", "%"):
            self.take()
            node = ("pct", node)
        return node

    def primary(self):
        kind, value = self.take()
        if kind == "num":
            return ("num", value)
        if kind == "var":
            return ("var", value)
        if kind == "log":
            return ("log", value, self.postfix())
        if (kind, value) == ("op", "("):
            node = self.expr()
            self.expect_op(")")
            return ("paren", node)
        if (kind, value) == ("op", "sqrt"):
            return ("root", 2, self.postfix())
        if (kind, value) == ("op", "cbrt"):
            return ("root", 3, self.postfix())
        raise ExprError("expected a number or '('")


def parse(text, allow_vars=False):
    return _Parser(tokenize(text, allow_vars), allow_vars).parse()


def _int_root(value, degree):
    if value < 0:
        if degree % 2 == 0:
            raise ExprError("square root of a negative number")
        return -_int_root(-value, degree)
    guess = round(value ** (1.0 / degree))
    for candidate in (guess - 1, guess, guess + 1):
        if candidate >= 0 and candidate ** degree == value:
            return candidate
    raise ExprError("root is not exact")


def _exact_log(base, value):
    if value <= 0:
        raise ExprError("logarithm of a non-positive number")
    for k in range(-64, 65):
        if Fraction(base) ** k == value:
            return Fraction(k)
    raise ExprError("logarithm is not an exact integer")


def evaluate(node, env=None, exact_division=False, intermediates=None):
    """Exactly evaluate a parsed expression. `intermediates`, if a list, collects every node value."""

    def ev(n):
        kind = n[0]
        if kind == "num":
            v = n[1]
        elif kind == "var":
            if env is None or n[1] not in env:
                raise ExprError("unbound variable")
            v = Fraction(env[n[1]])
        elif kind == "paren":
            v = ev(n[1])
        elif kind == "neg":
            v = -ev(n[1])
        elif kind == "pct":
            v = ev(n[1]) / 100
        elif kind == "bin":
            left, right = ev(n[2]), ev(n[3])
            op = n[1]
            if op == "+":
                v = left + right
            elif op == "-":
                v = left - right
            elif op == "*":
                v = left * right
            else:
                if right == 0:
                    raise ExprError("division by zero")
                v = left / right
                if exact_division and (left.denominator != 1 or right.denominator != 1 or v.denominator != 1):
                    raise ExprError("division is not exact")
        elif kind == "pow":
            base, exponent = ev(n[1]), ev(n[2])
            if exponent.denominator != 1 or abs(exponent) > MAX_EXPONENT:
                raise ExprError("unsupported exponent")
            if base == 0 and exponent < 0:
                raise ExprError("division by zero")
            v = base ** int(exponent)
        elif kind == "root":
            inner = ev(n[2])
            v = Fraction(_int_root(inner.numerator, n[1]), _int_root(inner.denominator, n[1]))
        elif kind == "log":
            v = _exact_log(n[1], ev(n[2]))
        else:  # pragma: no cover - parser never builds other nodes
            raise ExprError(f"unknown node {kind}")
        if intermediates is not None:
            intermediates.append(v)
        return v

    return ev(node)


def evaluate_text(text, env=None, allow_vars=False, exact_division=False):
    return evaluate(parse(text, allow_vars), env, exact_division)


def info(node):
    """Structural summary: binary operators in order, and which features are used."""
    out = {"ops": [], "parens": False, "power": False, "root": False, "log": False,
           "percent": False, "neg": False, "literals": []}

    def walk(n):
        kind = n[0]
        if kind == "num":
            out["literals"].append(n[1])
        elif kind == "bin":
            walk(n[2])
            out["ops"].append(n[1])
            walk(n[3])
        elif kind == "paren":
            out["parens"] = True
            walk(n[1])
        elif kind == "neg":
            out["neg"] = True
            walk(n[1])
        elif kind == "pct":
            out["percent"] = True
            walk(n[1])
        elif kind == "pow":
            out["power"] = True
            walk(n[1])
            walk(n[2])
        elif kind == "root":
            out["root"] = True
            walk(n[2])
        elif kind == "log":
            out["log"] = True
            walk(n[2])

    walk(node)
    return out


def display_errors(text, allow_slash=False, allow_x=False):
    """Display-symbol rules for numeric prompts: ×, ÷ and U+2212 only."""
    errors = []
    if "*" in text:
        errors.append("use '×' instead of '*' in display text")
    if "-" in text:
        errors.append("use '−' (U+2212) instead of ASCII '-' in display text")
    if "^" in text:
        errors.append("use superscript exponents instead of '^' in display text")
    if "/" in text and not allow_slash:
        errors.append("use '÷' instead of '/' in display text")
    if "X" in text or ("x" in text and not allow_x):
        errors.append("use '×' for multiplication; 'x' is reserved for the unknown")
    return errors
