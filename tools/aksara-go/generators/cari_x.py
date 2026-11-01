"""cari-x: one-unknown equations built from a chosen integer solution (so a solution exists by
construction); the validator checks the solution and its uniqueness independently."""

from generators.common import MINUS, fmt, numeric_options, sup

GAME_ID = "cari-x"
TARGETS = {"sd-b": 120, "sd-c": 120, "smp": 120, "sma": 120}


def _signed(n):
    """' + 3' / ' − 3' suffix for a constant term."""
    return f" + {fmt(n)}" if n >= 0 else f" {MINUS} {fmt(-n)}"


def _num(n):
    return fmt(n)


def _coef(a):
    return "x" if a == 1 else f"{a}x"


def _q(difficulty, text, x, rng, nonneg):
    return {"difficulty": difficulty, "prompt": {"text": text}, "answer": x,
            "payload": {"options": numeric_options(rng, x, [], nonneg)}}


def sd_b(rng, d):
    x = rng.randint(0, 50)
    a = rng.randint(1, 50)
    if d == 1:
        text = f"? + {a} = {x + a}"
    elif d == 2:
        text = f"{a} + ? = {a + x}"
    elif d == 3:
        x += a  # ? − a = x − a, so the answer stays non-negative
        text = f"? {MINUS} {a} = {x - a}"
    elif d == 4:
        total = x + a
        text = f"{total} {MINUS} ? = {a}"
    else:
        x, a = rng.randint(1, 10), rng.randint(1, 10)
        text = f"? × {a} = {x * a}" if rng.random() < 0.5 else f"{x * a} ÷ ? = {a}"
    return _q(d, text, x, rng, nonneg=True)


def sd_c(rng, d):
    x = rng.randint(1, 50)
    a, b = rng.randint(2, 12), rng.randint(1, 30)
    if d == 1:
        text = f"? × {a} = {x * a}"
    elif d == 2:
        text = f"? × {a} + {b} = {x * a + b}"
    elif d == 3:
        if x * a <= b:
            return None
        text = f"{a} × ? {MINUS} {b} = {x * a - b}"
    elif d == 4:
        text = f"(? + {b}) × {a} = {(x + b) * a}"
    else:
        a, q = rng.randint(1, 20), rng.randint(2, 15)
        x = a + q * rng.randint(2, 9)  # (x − a) divisible by q
        text = f"(? {MINUS} {a}) ÷ {q} = {(x - a) // q}"
    return _q(d, text, x, rng, nonneg=True)


def smp(rng, d):
    x = rng.randint(-20, 30)
    a, b = rng.randint(2, 9), rng.randint(-30, 30)
    if d == 1:
        text = f"x{_signed(b)} = {_num(x + b)}"
    elif d == 2:
        text = f"{_coef(a)}{_signed(b)} = {_num(a * x + b)}"
    elif d == 3:
        c = rng.randint(1, 8)
        if c == a:
            return None
        dconst = a * x + b - c * x
        text = f"{_coef(a)}{_signed(b)} = {_coef(c)}{_signed(dconst)}"
    elif d == 4:
        k = rng.randint(1, 15)
        text = f"{a}(x {MINUS} {k}) = {_num(a * (x - k))}"
    else:
        q = rng.randint(2, 6)
        x = q * rng.randint(-8, 10)
        text = f"x ÷ {q}{_signed(b)} = {_num(x // q + b)}"
    return _q(d, text, x, rng, nonneg=False)


def sma(rng, d):
    if d == 1:
        x = rng.randint(-15, 20)
        a, b, c = rng.randint(2, 6), rng.randint(2, 5), rng.randint(1, 9)
        dd = rng.randint(1, 9)
        if a * b == dd:
            return None
        e = a * (b * x - c) - dd * x
        text = f"{a}({b}x {MINUS} {c}) = {_coef(dd)}{_signed(e)}"
    elif d == 2:
        base = rng.choice([2, 3, 4, 5])
        x = rng.randint(1, {2: 10, 3: 6, 4: 5, 5: 4}[base])
        text = f"{base}ˣ = {fmt(base ** x)}"
    elif d == 3:
        base, k = rng.choice([2, 3]), rng.randint(1, 4)
        x = rng.randint(1, 6)
        if base ** (x + k) > 10 ** 6:
            return None
        text = f"{base}ˣ × {base}{sup(k)} = {fmt(base ** (x + k))}"
    elif d == 4:
        base = rng.choice([2, 3])
        k = rng.randint(1, {2: 9, 3: 6}[base])
        x = base ** k
        if x > 1000:
            return None
        text = f"{sup(base)}log x = {k}"
    else:
        if rng.random() < 0.4:
            k = rng.randint(1, 3)
            x = 10 ** k
            text = f"log x = {k}"
        else:
            x = rng.randint(-12, 12)
            a, b = rng.randint(2, 5), rng.randint(2, 5)
            c, e = rng.randint(1, 6), rng.randint(1, 6)
            if a == b:
                return None
            text = f"{a}(x + {c}) = {b}(x{_signed(e)}){_signed(a * (x + c) - b * (x + e))}"
    return _q(d, text, x, rng, nonneg=False)


GENERATORS = {"sd-b": sd_b, "sd-c": sd_c, "smp": smp, "sma": sma}


def generate(rng, segment, difficulty):
    return GENERATORS[segment](rng, difficulty)
