"""deret-angka: sequences generated from an explicit rule (stored in payload.rule)."""

from generators.common import fmt, numeric_options
from lib import sequence

GAME_ID = "deret-angka"
TARGETS = {"sd-a": 120, "sd-b": 120, "sd-c": 120, "smp": 120, "sma": 120}


def _arith(rng, start, step):
    return {"type": "arithmetic", "start": rng.randint(*start), "step": rng.choice(step)}


def _rule(rng, segment, d):
    """(rule, length, gap) where gap is 'last' or 'any'."""
    if segment == "sd-a":
        return {
            1: (_arith(rng, (0, 10), [1]), 4, "last"),
            2: (_arith(rng, (0, 10), [2]), 4, "last"),
            3: (_arith(rng, (0, 20), [1, 2, 3, 4, 5]), 5, "inner"),
            4: (_arith(rng, (20, 40), [-1, -2, -3, -4, -5]), 5, "any"),
            5: (_arith(rng, (0, 30), [5, 10]), rng.randint(5, 6), "any"),
        }[d]
    if segment == "sd-b":
        return {
            1: (_arith(rng, (0, 50), list(range(2, 11))), 5, "last"),
            2: (_arith(rng, (60, 120), list(range(-10, -1))), 5, "any"),
            3: (_arith(rng, (100, 500), [15, 20, 25, 50]), 5, "any"),
            4: ({"type": "geometric", "start": rng.randint(1, 10), "ratio": 2}, 5, "last"),
            5: (rng.choice([{"type": "geometric", "start": rng.randint(1, 12), "ratio": 2},
                            _arith(rng, (100, 900), [50, 100, -50, -100])]), 6, "any"),
        }[d]
    if segment == "sd-c":
        return {
            1: (_arith(rng, (10, 100), [10, 20, 25, 50]), 5, "any"),
            2: (_arith(rng, (100, 900), [25, 75, 125, -25, -75]), 5, "any"),
            3: ({"type": "geometric", "start": rng.randint(3, 25), "ratio": 2}, 5, "any"),
            4: (_arith(rng, (900, 2000), [-15, -35, -45, -120, -150]), 6, "any"),
            5: ({"type": "geometric", "start": rng.randint(3, 40), "ratio": 2}, 6, "any"),
        }[d]
    if segment == "smp":
        nonzero = [s for s in range(-7, 8) if s]
        return {
            1: (_arith(rng, (-20, 20), nonzero), 5, "any"),
            2: ({"type": "square", "start": rng.randint(1, 10)}, 5, "any"),
            3: ({"type": "second-difference", "start": rng.randint(1, 10), "step": rng.randint(1, 5),
                 "increment": rng.randint(1, 3)}, 5, "any"),
            4: ({"type": "fibonacci", "first": rng.randint(1, 5), "second": rng.randint(1, 8)}, 6, "any"),
            5: (rng.choice([{"type": "cube", "start": rng.randint(1, 5)},
                            {"type": "alternating", "start": rng.randint(1, 20),
                             "steps": [rng.randint(2, 9), -rng.randint(1, 5)]},
                            {"type": "geometric", "start": rng.randint(1, 5), "ratio": 3}]), 6, "any"),
        }[d]
    return {  # sma
        1: ({"type": "geometric", "start": rng.randint(1, 6), "ratio": rng.randint(3, 5)}, 5, "any"),
        2: ({"type": "geometric", "start": rng.randint(1, 6), "ratio": rng.choice([-2, -3])}, 5, "any"),
        3: ({"type": "second-difference", "start": rng.randint(-10, 10), "step": rng.randint(-5, 8),
             "increment": rng.randint(2, 5)}, 6, "any"),
        4: (rng.choice([{"type": "fibonacci", "first": rng.randint(2, 10), "second": rng.randint(3, 15)},
                        {"type": "alternating", "start": rng.randint(-10, 30),
                         "steps": [rng.randint(5, 15), -rng.randint(2, 9)]}]), 7, "any"),
        5: (rng.choice([{"type": "cube", "start": rng.randint(-3, 5)},
                        {"type": "second-difference", "start": rng.randint(1, 20), "step": rng.randint(10, 20),
                         "increment": -rng.randint(2, 6)},
                        {"type": "geometric", "start": rng.randint(2, 5), "ratio": 2}]), 7, "any"),
    }[d]


def generate(rng, segment, difficulty):
    rule, length, gap_kind = _rule(rng, segment, difficulty)
    if sequence.rule_error(rule):
        return None
    terms = sequence.terms(rule, length)
    if segment.startswith("sd-") and any(t < 0 for t in terms):
        return None
    gap = {"last": length - 1, "inner": rng.randint(1, length - 2), "any": rng.randrange(length)}[gap_kind]
    answer = terms[gap]
    shown = [None if i == gap else t for i, t in enumerate(terms)]
    text = ", ".join("?" if t is None else fmt(t) for t in shown)
    step_slip = terms[gap - 1] + (terms[gap - 1] - terms[gap - 2]) if gap >= 2 else answer + 1
    return {"difficulty": difficulty, "prompt": {"text": text, "sequence": shown}, "answer": answer,
            "payload": {"rule": rule,
                        "options": numeric_options(rng, answer, [step_slip], nonneg=segment.startswith("sd-"))}}
