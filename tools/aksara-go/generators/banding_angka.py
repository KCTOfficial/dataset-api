"""banding-angka: compare two values. Each side is built together with its exact Fraction value
here; the validator re-derives both values independently by parsing the display text."""

from fractions import Fraction

from generators.common import MINUS, fmt, sup

GAME_ID = "banding-angka"
TARGETS = {"sd-a": 120, "sd-b": 120, "sd-c": 120, "smp": 120, "sma": 120}


def _int(n):
    return fmt(n), Fraction(n)


def _frac(a, b):
    return f"{a}/{b}", Fraction(a, b)


def _dec(value_hundredths):
    whole, rest = divmod(value_hundredths, 100)
    digits = f"{rest:02d}".rstrip("0")
    return (f"{whole},{digits}" if digits else str(whole)), Fraction(value_hundredths, 100)


def _neg(side):
    text, value = side
    return MINUS + text, -value


def _side(rng, segment, d):
    if segment == "sd-a":
        if d == 1:
            return _int(rng.randint(0, 20))
        if d == 2:
            return _int(rng.randint(0, 50))
        if d == 3:
            return _int(rng.randint(10, 99))
        a, b = rng.randint(0, 10), rng.randint(0, 10)
        if d == 5 and rng.random() < 0.5 and a >= b:
            return f"{a} {MINUS} {b}", Fraction(a - b)
        return (f"{a} + {b}", Fraction(a + b)) if rng.random() < 0.6 else _int(rng.randint(0, 20))
    if segment == "sd-b":
        if d == 1:
            return _int(rng.randint(100, 999))
        if d == 2:
            return _int(rng.randint(1000, 10_000))
        if d == 3:
            a, b = rng.randint(2, 10), rng.randint(2, 10)
            return (f"{a} × {b}", Fraction(a * b)) if rng.random() < 0.6 else _int(rng.randint(4, 100))
        if d == 4:
            return _frac(rng.randint(1, 11), 12 if rng.random() < 0.5 else 8)
        a, b = rng.randint(2, 10), rng.randint(2, 10)
        return (f"{a * b} ÷ {b}", Fraction(a)) if rng.random() < 0.5 else (f"{a} × {b}", Fraction(a * b))
    if segment == "sd-c":
        if d == 1:
            b = rng.choice([2, 3, 4, 5, 6, 8, 10])
            return _frac(rng.randint(1, b - 1), b)
        if d == 2:
            return _dec(rng.randint(1, 99))
        if d == 3:
            return _frac(rng.randint(1, 4), 5) if rng.random() < 0.5 else _dec(rng.choice(range(5, 100, 5)))
        if d == 4:
            pct = rng.choice(range(5, 100, 5))
            return (f"{pct}%", Fraction(pct, 100)) if rng.random() < 0.5 else _frac(rng.randint(1, 3), 4)
        return _frac(rng.randint(1, 7), 8) if rng.random() < 0.5 else _dec(rng.randint(10, 95))
    if segment == "smp":
        if d == 1:
            return _neg(_int(rng.randint(1, 30))) if rng.random() < 0.7 else _int(rng.randint(0, 10))
        if d == 2:
            return _frac(rng.randint(1, 9), 10) if rng.random() < 0.5 else _dec(rng.randint(5, 99))
        if d == 3:
            pct = rng.choice([10, 20, 25, 40, 50, 60, 75, 80])
            return (f"{pct}%", Fraction(pct, 100)) if rng.random() < 0.5 else _frac(rng.randint(1, 4), 5)
        if d == 4:
            kind = rng.randrange(3)
            if kind == 0:
                r = rng.randint(2, 12)
                return f"√{r * r}", Fraction(r)
            a, e = rng.randint(2, 6), rng.randint(2, 3)
            return (f"{a}{sup(e)}", Fraction(a ** e)) if kind == 1 else _int(rng.randint(4, 60))
        return _neg(_frac(rng.randint(1, 4), 5)) if rng.random() < 0.5 else _neg(_dec(rng.randint(10, 95)))
    # sma
    if d == 1:
        a, e = rng.choice([2, 3, 5, 10]), rng.randint(2, 10)
        if a ** e > 10 ** 7:
            return None
        return f"{a}{sup(e)}", Fraction(a ** e)
    if d == 2:
        if rng.random() < 0.5:
            r = rng.randint(2, 20)
            return f"√{r * r}", Fraction(r)
        s = rng.randint(2, 10)
        return f"∛{fmt(s ** 3)}", Fraction(s)
    if d == 3:
        base = rng.choice([2, 3, 5])
        k = rng.randint(1, 6)
        return f"{sup(base)}log {fmt(base ** k)}", Fraction(k)
    if d == 4:
        a, e = rng.randint(2, 9), rng.randint(2, 5)
        return f"{a}{sup(e)}", Fraction(a ** e)
    kind = rng.randrange(3)
    if kind == 0:
        k = rng.randint(1, 8)
        return f"{sup(2)}log {fmt(2 ** k)}", Fraction(k)
    if kind == 1:
        r = rng.randint(1, 9)
        return f"√{r * r}", Fraction(r)
    k = rng.randint(1, 6)
    return f"log {fmt(10 ** k)}", Fraction(k)


def _equal_pair(rng, segment, d):
    """Constructively equal sides (random pairs rarely tie)."""
    if segment == "sd-a":
        if d <= 3:
            n = rng.randint(0, 50 if d > 1 else 20)
            return _int(n), _int(n)
        a, b = rng.randint(0, 10), rng.randint(0, 10)
        return (f"{a} + {b}", Fraction(a + b)), (f"{b} + {a}", Fraction(a + b)) if d == 5 else _int(a + b)
    if segment == "sd-b":
        if d <= 2:
            n = rng.randint(100, 999) if d == 1 else rng.randint(1000, 10_000)
            return _int(n), _int(n)
        if d == 4:
            a, b = rng.randint(1, 5), rng.choice([2, 3, 4])
            return _frac(a, 6), _frac(a * 2, 12) if b else None
        a, b = rng.randint(2, 10), rng.randint(2, 10)
        return (f"{a} × {b}", Fraction(a * b)), (f"{b} × {a}", Fraction(a * b)) if d == 5 else _int(a * b)
    if segment == "sd-c":
        b, k = rng.choice([2, 3, 4, 5]), rng.randint(2, 4)
        a = rng.randint(1, b - 1)
        if d == 1:
            return _frac(a, b), _frac(a * k, b * k)
        if d == 2:
            n = rng.randint(1, 9) * 10
            return _dec(n), _dec(n)
        if d == 3:
            n = rng.choice([1, 2, 3, 4])
            return _frac(n, 5), _dec(n * 20)
        if d == 4:
            n = rng.choice([1, 2, 3])
            return (f"{n * 25}%", Fraction(n, 4)), _frac(n, 4)
        n = rng.choice([1, 3])
        return _frac(n, 4), _dec(n * 25)
    if segment == "smp":
        if d == 1:
            n = rng.randint(1, 30)
            return _neg(_int(n)), (f"{MINUS}{n * 2} ÷ 2", Fraction(-n))
        if d == 2:
            n = rng.randint(1, 9)
            return _frac(n, 10), _dec(n * 10)
        if d == 3:
            n = rng.choice([1, 2, 3, 4])
            return (f"{n * 20}%", Fraction(n, 5)), _frac(n, 5)
        if d == 4:
            r = rng.randint(2, 12)
            return (f"√{r * r}", Fraction(r)), _int(r)
        n = rng.choice([1, 2, 3, 4])
        return _neg(_frac(n, 5)), _neg(_dec(n * 20))
    if d in (1, 4):
        pairs = [((2, 6), (4, 3)), ((2, 6), (8, 2)), ((3, 4), (9, 2)), ((2, 4), (4, 2)), ((2, 9), (8, 3)),
                 ((5, 2), (25, 1)), ((2, 10), (4, 5)), ((3, 6), (9, 3)), ((2, 8), (4, 4)), ((2, 8), (16, 2))]
        (a, e), (b, f) = rng.choice(pairs)
        right = f"{b}{sup(f)}" if f > 1 else fmt(b)
        return (f"{a}{sup(e)}", Fraction(a ** e)), (right, Fraction(b ** f))
    if d == 2:
        s = rng.randint(2, 10)
        return (f"∛{fmt(s ** 3)}", Fraction(s)), (f"√{s * s}", Fraction(s))
    k = rng.randint(1, 5)
    return (f"{sup(2)}log {fmt(2 ** k)}", Fraction(k)), (f"{sup(3)}log {fmt(3 ** k)}", Fraction(k))


OUTCOMES = ["<", ">", "="]


def make(segment):
    """Stateful generator for one file: the wanted outcome rotates so <, >, = stay balanced."""
    calls = [0]

    def generate_balanced(rng, seg, difficulty):
        want = OUTCOMES[(calls[0] // 5) % 3]  # each outcome gets a full round of difficulties 1-5
        calls[0] += 1
        return generate(rng, seg, difficulty, want)

    return generate_balanced


def generate(rng, segment, difficulty, want=None):
    want = want or rng.choice(OUTCOMES)
    if want == "=":
        pair = _equal_pair(rng, segment, difficulty)
        if not pair or pair[1] is None:
            return None
        (lt, lv), (rt, rv) = pair
        if rng.random() < 0.5:
            (lt, lv), (rt, rv) = (rt, rv), (lt, lv)
    else:
        for _ in range(50):
            left, right = _side(rng, segment, difficulty), _side(rng, segment, difficulty)
            if left is None or right is None or left[1] is None or right[1] is None:
                continue
            (lt, lv), (rt, rv) = left, right
            if (lv < rv and want == "<") or (lv > rv and want == ">"):
                break
        else:
            return None
    if lt == rt and want != "=":
        return None
    answer = "<" if lv < rv else ">" if lv > rv else "="
    return {"difficulty": difficulty, "prompt": {"text": f"{lt} ? {rt}", "left": lt, "right": rt}, "answer": answer}
