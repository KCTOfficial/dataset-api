"""hitung-cepat: integer arithmetic per segment. Answers are computed here with plain Python
integers; the validator recomputes them independently by parsing the display text."""

from generators.common import MINUS, fmt, neg_paren, numeric_options, sup

GAME_ID = "hitung-cepat"
TARGETS = {"sd-a": 120, "sd-b": 120, "sd-c": 120, "smp": 120, "sma": 120}


def _q(difficulty, text, answer, rng, nonneg, slips=()):
    return {"difficulty": difficulty, "prompt": {"text": text}, "answer": answer,
            "payload": {"options": numeric_options(rng, answer, slips, nonneg)}}


def _add_or_sub(rng, d, a_range, b_range, op):
    a, b = rng.randint(*a_range), rng.randint(*b_range)
    if op == "-":
        a, b = max(a, b), min(a, b)
        return f"{fmt(a)} {MINUS} {fmt(b)}", a - b
    return f"{fmt(a)} + {fmt(b)}", a + b


def sd_a(rng, d):
    if d == 1:
        text, ans = _add_or_sub(rng, d, (0, 5), (0, 5), "+")
    elif d == 2:
        if rng.random() < 0.5:
            a = rng.randint(1, 9)
            text, ans = f"{a} + {rng.randint(0, 10 - a)}", None
        else:
            text, ans = _add_or_sub(rng, d, (1, 10), (0, 10), "-")
    elif d == 3:
        a, b = rng.randint(2, 10), rng.randint(2, 10)
        if a + b <= 10:
            return None
        text, ans = f"{a} + {b}", a + b
    elif d == 4:
        a = rng.randint(11, 20)
        b = rng.randint(1, a)
        text, ans = f"{a} {MINUS} {b}", a - b
    else:
        if rng.random() < 0.5:
            a = rng.randint(10, 18)
            b = rng.randint(1, 20 - a)
            text, ans = f"{a} + {b}", a + b
        else:
            a = rng.randint(12, 20)
            b = rng.randint(5, a)
            text, ans = f"{a} {MINUS} {b}", a - b
    if ans is None:
        a, b = map(int, text.split(" + "))
        ans = a + b
    return _q(d, text, ans, rng, nonneg=True)


def _table_div(rng, low, high):
    b, q = rng.randint(low, high), rng.randint(low, high)
    return f"{b * q} ÷ {b}", q


def sd_b(rng, d):
    if d == 1:
        a, b = rng.randint(10, 60), rng.randint(10, 40)
        text, ans = f"{a} + {b}", a + b
    elif d == 2:
        if rng.random() < 0.5:
            text, ans = _add_or_sub(rng, d, (20, 99), (10, 99), "-")
        else:
            a, b = rng.randint(1, 5), rng.randint(1, 5)
            text, ans = f"{a} × {b}", a * b
    elif d == 3:
        if rng.random() < 0.5:
            a, b = rng.randint(100, 600), rng.randint(50, 400)
            text, ans = f"{a} + {b}", a + b
        else:
            a, b = rng.randint(2, 10), rng.randint(2, 10)
            text, ans = f"{a} × {b}", a * b
    elif d == 4:
        if rng.random() < 0.5:
            text, ans = _add_or_sub(rng, d, (300, 1000), (100, 999), "-")
        else:
            text, ans = _table_div(rng, 2, 10)
    else:
        kind = rng.randrange(3)
        if kind == 0:
            a = rng.randint(500, 900)
            text, ans = f"{a} + {rng.randint(50, 1000 - a)}", None
            ans = sum(int(p) for p in text.split(" + "))
        elif kind == 1:
            a, b = rng.randint(6, 10), rng.randint(6, 10)
            text, ans = f"{a} × {b}", a * b
        else:
            text, ans = _table_div(rng, 6, 10)
    return _q(d, text, ans, rng, nonneg=True)


def sd_c(rng, d):
    slips = []
    if d == 1:
        if rng.random() < 0.5:
            a, b = rng.randint(11, 99), rng.randint(2, 9)
            text, ans = f"{a} × {b}", a * b
        else:
            q, b = rng.randint(11, 50), rng.randint(2, 9)
            text, ans = f"{q * b} ÷ {b}", q
    elif d == 2:
        a, b, c = rng.randint(1, 50), rng.randint(2, 10), rng.randint(2, 10)
        if rng.random() < 0.5:
            text, ans, slips = f"{a} + {b} × {c}", a + b * c, [(a + b) * c]
        else:
            a = rng.randint(b * c, b * c + 60)
            text, ans, slips = f"{a} {MINUS} {b} × {c}", a - b * c, [(a - b) * c]
    elif d == 3:
        kind = rng.randrange(3)
        if kind == 0:
            a, b = rng.randint(2, 12), rng.randint(2, 12)
            c = rng.randint(1, a * b)
            text, ans, slips = f"{a} × {b} {MINUS} {c}", a * b - c, [a * (b - c)] if b >= c else []
        elif kind == 1:
            b, q, c = rng.randint(2, 9), rng.randint(2, 15), rng.randint(1, 40)
            text, ans = f"{b * q} ÷ {b} + {c}", q + c
        else:
            b, q = rng.randint(2, 9), rng.randint(2, 12)
            a = rng.randint(q, q + 80)
            text, ans, slips = f"{a} {MINUS} {b * q} ÷ {b}", a - q, []
    elif d == 4:
        kind = rng.randrange(3)
        a, b, c = rng.randint(2, 40), rng.randint(2, 40), rng.randint(2, 9)
        if kind == 0:
            text, ans, slips = f"({a} + {b}) × {c}", (a + b) * c, [a + b * c]
        elif kind == 1:
            a, b = max(a, b) + 1, min(a, b)
            text, ans, slips = f"({a} {MINUS} {b}) × {c}", (a - b) * c, [a - b * c] if a >= b * c else []
        else:
            q = rng.randint(2, 20)
            total = q * c
            a = rng.randint(1, total - 1)
            text, ans = f"({a} + {total - a}) ÷ {c}", q
    else:
        kind = rng.randrange(3)
        if kind == 0:
            a, b, c = rng.randint(2, 30), rng.randint(5, 60), rng.randint(1, 4)
            text, ans, slips = f"{a} × ({b} {MINUS} {c})", a * (b - c), [a * b - c]
        elif kind == 1:
            c, q = rng.randint(2, 12), rng.randint(5, 40)
            total = c * q
            a = rng.randint(total + 1, total + 200)
            text, ans = f"({a} {MINUS} {a - total}) ÷ {c}", q
        else:
            q, b = rng.randint(2, 30), rng.randint(3, 12)
            c = rng.randint(1, b - 1)
            text, ans = f"{q * (b - c) * 10} ÷ ({b} {MINUS} {c})", q * 10
        if ans > 10_000:
            return None
    if not 0 <= ans <= 10_000:
        return None
    return _q(d, text, ans, rng, nonneg=True, slips=[s for s in slips if s >= 0])


def smp(rng, d):
    slips = []
    if d == 1:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        kind = rng.randrange(3)
        if kind == 0:
            text, ans, slips = f"{neg_paren(-a)} + {b}", -a + b, [a + b]
        elif kind == 1:
            text, ans, slips = f"{a} {MINUS} {neg_paren(-b)}", a + b, [a - b]
        else:
            text, ans, slips = f"{neg_paren(-a)} {MINUS} {b}", -a - b, [b - a]
    elif d == 2:
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        kind = rng.randrange(3)
        if kind == 0:
            text, ans, slips = f"{neg_paren(-a)} × {b}", -a * b, [a * b]
        elif kind == 1:
            text, ans, slips = f"{neg_paren(-a)} × {neg_paren(-b)}", a * b, [-a * b]
        else:
            text, ans, slips = f"{neg_paren(-a * b)} ÷ {b}", -a, [a]
    elif d == 3:
        a, b = rng.randint(2, 15), rng.randint(1, 15)
        kind = rng.randrange(3)
        if kind == 0:
            text, ans, slips = f"{a}{sup(2)} + {b}", a * a + b, [2 * a + b]
        elif kind == 1:
            text, ans = f"{a}{sup(2)} {MINUS} {b}{sup(2)}", a * a - b * b
        else:
            a = rng.randint(2, 6)
            text, ans, slips = f"{a}{sup(3)} {MINUS} {b}", a ** 3 - b, [3 * a - b]
    elif d == 4:
        r, b = rng.randint(2, 20), rng.randint(2, 9)
        kind = rng.randrange(3)
        if kind == 0:
            text, ans = f"√{r * r} + {b}{sup(2)}", r + b * b
        elif kind == 1:
            text, ans = f"√{r * r} × {b}", r * b
        else:
            text, ans, slips = f"√{r * r} {MINUS} {b}{sup(2)}", r - b * b, [b * b - r]
    else:
        kind = rng.randrange(3)
        if kind == 0:
            c = rng.randint(2, 6)
            k = rng.randint(1, 4)
            a = rng.randint(c * k + 1, c * k + 20)
            text, ans = f"({a} {MINUS} {a - c * k}){sup(2)} ÷ {c}", (c * k) ** 2 // c
        elif kind == 1:
            a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
            text, ans, slips = f"{neg_paren(-a)}{sup(2)} {MINUS} {b} × {c}", a * a - b * c, [-a * a - b * c]
        else:
            a, b, c = rng.randint(1, 9), rng.randint(1, 9), rng.randint(1, 12)
            text, ans = f"({a} + {b}){sup(2)} {MINUS} {c}{sup(2)}", (a + b) ** 2 - c * c
    return _q(d, text, ans, rng, nonneg=False, slips=slips)


def sma(rng, d):
    slips = []
    if d == 1:
        a, m, n = rng.randint(2, 5), rng.randint(2, 4), rng.randint(2, 4)
        if a ** (m + n) > 100_000:
            return None
        text, ans, slips = f"{a}{sup(m)} × {a}{sup(n)}", a ** (m + n), [a ** (m * n)]
    elif d == 2:
        a = rng.randint(2, 5)
        if rng.random() < 0.5:
            m, n = rng.randint(4, 7), rng.randint(2, 3)
            if m <= n:
                return None
            text, ans, slips = f"{a}{sup(m)} ÷ {a}{sup(n)}", a ** (m - n), [a ** (m // n) if m % n == 0 else a]
        else:
            m, n = rng.randint(2, 3), rng.randint(2, 3)
            if a ** (m * n) > 100_000:
                return None
            text, ans, slips = f"({a}{sup(m)}){sup(n)}", a ** (m * n), [a ** (m + n)]
    elif d == 3:
        base = rng.choice([2, 3, 10])
        k = rng.randint(1, {2: 10, 3: 6, 10: 6}[base])
        prefix = "" if base == 10 else sup(base)
        text, ans = f"{prefix}log {fmt(base ** k)}", k
    elif d == 4:
        r, s = rng.randint(2, 15), rng.randint(2, 6)
        kind = rng.randrange(3)
        if kind == 0:
            text, ans = f"∛{s ** 3} + √{r * r}", s + r
        elif kind == 1:
            text, ans = f"√{r * r} × ∛{s ** 3}", r * s
        else:
            if r % s:
                return None
            text, ans = f"√{r * r} ÷ ∛{s ** 3}", r // s
    else:
        kind = rng.randrange(3)
        a, b = rng.randint(1, 8), rng.randint(1, 5)
        if kind == 0:
            text, ans = f"{sup(2)}log {fmt(2 ** a)} + {sup(3)}log {fmt(3 ** b)}", a + b
        elif kind == 1:
            c = rng.randint(1, 4)
            text, ans = f"log {fmt(10 ** c)} × {sup(2)}log {fmt(2 ** a)}", c * a
        else:
            m = rng.randint(3, 8)
            text, ans = f"2{sup(m)} {MINUS} {sup(2)}log {fmt(2 ** a)}", 2 ** m - a
    return _q(d, text, ans, rng, nonneg=False, slips=slips)


GENERATORS = {"sd-a": sd_a, "sd-b": sd_b, "sd-c": sd_c, "smp": smp, "sma": sma}


def generate(rng, segment, difficulty):
    return GENERATORS[segment](rng, difficulty)
