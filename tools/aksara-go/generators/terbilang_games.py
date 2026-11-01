"""tebak-angka (number to words) and kata-ke-angka (words to number)."""

from generators.common import fmt, numeric_options
from lib import terbilang

T, J, M = 1_000, 1_000_000, 1_000_000_000
TR = 1_000_000_000_000

# (segment, difficulty) -> function(rng) -> int. Pools favor irregular forms (se-, belas, round numbers).
POOLS = {
    "sd-a": {1: lambda r: r.randint(1, 10), 2: lambda r: r.randint(11, 20), 3: lambda r: r.randint(21, 50),
             4: lambda r: r.randint(51, 80), 5: lambda r: r.randint(81, 100)},
    "sd-b": {1: lambda r: r.randint(100, 199), 2: lambda r: r.randint(200, 999),
             3: lambda r: r.randint(1000, 1999), 4: lambda r: r.randint(2000, 9999),
             5: lambda r: r.choice([r.randint(1, 9) * T + r.randint(0, 9) * 10 + r.randint(0, 9),
                                    r.randint(1, 9) * T + r.randint(1, 9) * 100 + r.randint(10, 19), 10_000])},
    "sd-c": {1: lambda r: r.randint(10, 99) * T, 2: lambda r: r.randint(11_000, 19_999),
             3: lambda r: r.randint(100, 999) * T, 4: lambda r: r.randint(10_000, 999_999),
             5: lambda r: r.choice([100_000 + r.randint(1, 999), 101_000 + r.randint(0, 99) * 10,
                                    110_000 + r.randint(10, 19), r.randint(1, 9) * 100_000 + r.randint(1, 9) * 1000,
                                    J])},
    "smp": {1: lambda r: r.randint(2, 999) * J, 2: lambda r: r.randint(J, 999_999_999),
            3: lambda r: J + r.choice([1000, 1001, 1011, 100_000, 110_011]) + r.randint(0, 9) * 10 * T,
            4: lambda r: r.choice([r.randint(1, 999) * M, r.randint(1, 999) * M + r.randint(1, 999) * J]),
            5: lambda r: r.randint(M, 999_999_999_999)},
}

FEATURED = {
    # The request's own example (2020 is "dua ribu dua puluh") plus the se- forms.
    "sd-b": [(3, 1000), (3, 1001), (3, 1100), (3, 1011), (4, 2020), (4, 2026), (5, 10_000)],
    "sd-c": [(2, 11_000), (3, 100_000), (5, J)],
    "smp": [(2, J), (3, 1_001_000), (4, M)],
    "sma": [(2, TR)],
}

SCALE_WORDS = ["ratus", "ribu", "juta", "miliar", "triliun"]


def _sma_value(rng, d):
    """sma: (int_part, frac_digits or None)."""
    if d == 1:
        return rng.randint(M, 999_999_999_999), None
    if d == 2:
        return rng.randint(1, 999) * TR, None
    if d == 3:
        return rng.randint(TR, 999_999_999_999_999), None
    frac = str(rng.randint(1, 99)) if rng.random() < 0.6 else str(rng.randint(1, 9))
    if len(frac) == 2 and frac.endswith("0"):
        frac = frac[0]
    if rng.random() < 0.25 and len(frac) == 1:
        frac = "0" + frac  # e.g. 3,05
    if d == 4:
        return rng.randint(0, 99), frac
    return rng.randint(100, 99_999), frac


def _distractors(rng, words, max_scale):
    present = set(words)
    candidates = []
    for w in words:
        if w in terbilang.UNITS[1:]:
            i = terbilang.UNITS.index(w)
            candidates += [terbilang.UNITS[j] for j in (i - 1, i + 1) if 1 <= j <= 9]
    if "belas" in present and "puluh" not in present:
        candidates.append("puluh")
    if "puluh" in present and "belas" not in present:
        candidates.append("belas")
    if "sebelas" in present:
        candidates.append("satu")
    if "seratus" in present or "seribu" in present:
        candidates.append("satu")
    candidates += [s for s in SCALE_WORDS[:max_scale] if s not in present]
    candidates = sorted(set(candidates) - present) or ["puluh", "belas"]
    return rng.sample(candidates, min(3, len(candidates)))


def _max_scale(segment):
    return {"sd-a": 2, "sd-b": 2, "sd-c": 3, "smp": 4, "sma": 5}[segment]


def tebak_question(rng, segment, difficulty, number=None):
    if segment == "sma" and number is None:
        int_part, frac = _sma_value(rng, difficulty)
    else:
        int_part = number if number is not None else POOLS[segment][difficulty](rng)
        frac = None
    if frac is None:
        text, answer = fmt(int_part), terbilang.words_int(int_part)
        prompt = {"text": text, "number": int_part}
    else:
        text = terbilang.format_decimal(int_part, frac)
        answer = terbilang.words_decimal(int_part, frac)
        prompt = {"text": text}
    if not 0 < (int_part or (frac and int(frac))):
        return None
    return {"difficulty": difficulty, "prompt": prompt, "answer": answer,
            "payload": {"distractors": _distractors(rng, answer.split(" "), _max_scale(segment))}}


def _near_misses(n):
    digits = str(n)
    slips = []
    for i in range(len(digits) - 1):
        if digits[i] != digits[i + 1]:
            swapped = digits[:i] + digits[i + 1] + digits[i] + digits[i + 2:]
            if swapped[0] != "0":
                slips.append(int(swapped))
            break
    place = 10 ** max(0, len(digits) - 2)
    slips += [n + place, n - place, n * 10]
    if n % 10 == 0:
        slips.append(n // 10)
    return [s for s in slips if s > 0]


def kata_question(rng, segment, difficulty, number=None):
    n = number if number is not None else POOLS[segment][difficulty](rng)
    return {"difficulty": difficulty, "prompt": {"text": terbilang.words_int(n)}, "answer": n,
            "payload": {"options": numeric_options(rng, n, _near_misses(n), nonneg=True)}}


class _Game:
    def __init__(self, game_id, targets, builder):
        self.GAME_ID = game_id
        self.TARGETS = targets
        self._builder = builder

    def featured(self, rng, segment):
        return [self._builder(rng, segment, d, number=n) for d, n in FEATURED.get(segment, [])
                if self.GAME_ID == "tebak-angka" or segment != "sma"]

    def generate(self, rng, segment, difficulty):
        return self._builder(rng, segment, difficulty)


TEBAK_ANGKA = _Game("tebak-angka", {"sd-a": 100, "sd-b": 120, "sd-c": 120, "smp": 120, "sma": 120},
                    tebak_question)
KATA_KE_ANGKA = _Game("kata-ke-angka", {"sd-a": 100, "sd-b": 120, "sd-c": 120, "smp": 120}, kata_question)
