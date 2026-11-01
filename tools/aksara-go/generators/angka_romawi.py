"""angka-romawi: Roman to Arabic (NUMPAD) and Arabic to Roman (TILE_BANK override)."""

from generators.common import numeric_options
from lib import roman

GAME_ID = "angka-romawi"
TARGETS = {"sd-b": 100, "sd-c": 120, "smp": 120}

# (segment, difficulty) -> (low, high, direction) with direction "from", "to" or "both"
PLAN = {
    "sd-b": {1: (1, 10, "from"), 2: (1, 10, "to"), 3: (11, 30, "from"), 4: (11, 30, "to"), 5: (31, 50, "both")},
    "sd-c": {1: (1, 100, "from"), 2: (1, 100, "to"), 3: (101, 500, "both"), 4: (500, 1000, "from"),
             5: (100, 1000, "to")},
    "smp": {1: (1, 1000, "from"), 2: (1000, 2000, "from"), 3: (2000, 3999, "from"), 4: (1, 3999, "to"),
            5: (1500, 3999, "both")},
}

YEARS = {
    1928: "MCMXXVIII = 1928, tahun Sumpah Pemuda.",
    1945: "MCMXLV = 1945, tahun Proklamasi Kemerdekaan Indonesia.",
    1998: "MCMXCVIII = 1998, tahun dimulainya Reformasi.",
}


def _question(rng, difficulty, n, direction, explanation=None):
    numeral = roman.to_roman(n)
    if direction == "from":
        q = {"difficulty": difficulty, "prompt": {"text": numeral}, "answer": n,
             "payload": {"options": numeric_options(rng, n, [], nonneg=True)}}
    else:
        unused = [letter for letter in roman.LETTERS if letter not in numeral]
        q = {"difficulty": difficulty, "interaction": "TILE_BANK", "prompt": {"text": str(n)}, "answer": numeral,
             "payload": {"distractors": rng.sample(unused, min(2, len(unused)))}}
    if explanation:
        q["explanation"] = explanation
    return q


def featured(rng, segment):
    if segment != "smp":
        return []
    return [_question(rng, 5, year, "from", text) for year, text in YEARS.items()]


def generate(rng, segment, difficulty):
    low, high, direction = PLAN[segment][difficulty]
    if direction == "both":
        direction = rng.choice(["from", "to"])
    return _question(rng, difficulty, rng.randint(low, high), direction)
