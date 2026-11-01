"""aksara-nusantara syllable files (sd-b, sd-c): nglegena letters x sandhangan swara, both directions.
The smp word file is curated (authored by hand), so it has no generator target here."""

from lib import javanese

GAME_ID = "aksara-nusantara"
TARGETS = {"sd-b": 80, "sd-c": 100}

CONSONANTS = [c for c, _ in javanese.NGLEGENA]
SIGN_NAMES = {"i": "wulu", "u": "suku", "é": "taling", "o": "taling tarung", "e": "pepet"}

# (segment, difficulty) -> (consonant pool, vowel pool, direction)
PLAN = {
    "sd-b": {1: (CONSONANTS[:10], ["a"], "read"), 2: (CONSONANTS[10:], ["a"], "read"),
             3: (CONSONANTS, ["a"], "write"), 4: (CONSONANTS, ["i"], "read"), 5: (CONSONANTS, ["u"], "read")},
    "sd-c": {1: (CONSONANTS, ["é"], "read"), 2: (CONSONANTS, ["o"], "read"), 3: (CONSONANTS, ["e"], "read"),
             4: (CONSONANTS, ["i", "u"], "write"), 5: (CONSONANTS, ["é", "o", "e"], "write")},
}


def _confusables(rng, consonant, vowel, vowels_in_play):
    """3 other syllables: same consonant with another vowel, or another consonant with the same vowel."""
    same_consonant = [consonant + v for v in javanese.VOWELS if v != vowel and v in vowels_in_play]
    same_vowel = [c + vowel for c in CONSONANTS if c != consonant]
    picks = rng.sample(same_consonant, min(1, len(same_consonant)))
    picks += rng.sample(same_vowel, 3 - len(picks))
    return picks


def generate(rng, segment, difficulty):
    consonants, vowels, direction = PLAN[segment][difficulty]
    consonant, vowel = rng.choice(consonants), rng.choice(vowels)
    latin = consonant + vowel
    script = javanese.to_script(latin)
    in_play = {"sd-b": ["a", "i", "u"], "sd-c": javanese.VOWELS}[segment]
    others = _confusables(rng, consonant, vowel, in_play)
    if direction == "read":
        prompt, answer, options = script, latin, others + [latin]
    else:
        prompt, answer, options = latin, script, [javanese.to_script(o) for o in others] + [script]
    rng.shuffle(options)
    q = {"difficulty": difficulty, "prompt": {"text": prompt}, "answer": answer, "payload": {"options": options}}
    if vowel != "a":
        base = javanese.to_script(consonant + "a")
        q["explanation"] = f"{base} ({consonant}a) diberi sandhangan {SIGN_NAMES[vowel]} dibaca {latin}."
    return q
