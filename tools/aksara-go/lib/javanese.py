"""Aksara Jawa: the 20 basic letters (nglegena) with vowel signs (sandhangan swara).

Covers open syllables only (consonant + vowel), which is what aksara-nusantara
uses. Latin romanization: taling = `é`, pepet = `e`, taling tarung = `o`.
"""

# Order of the hanacaraka: ha na ca ra ka / da ta sa wa la / pa dha ja ya nya / ma ga ba tha nga
NGLEGENA = [
    ("h", "ꦲ"), ("n", "ꦤ"), ("c", "ꦕ"), ("r", "ꦫ"), ("k", "ꦏ"),
    ("d", "ꦢ"), ("t", "ꦠ"), ("s", "ꦱ"), ("w", "ꦮ"), ("l", "ꦭ"),
    ("p", "ꦥ"), ("dh", "ꦝ"), ("j", "ꦗ"), ("y", "ꦪ"), ("ny", "ꦚ"),
    ("m", "ꦩ"), ("g", "ꦒ"), ("b", "ꦧ"), ("th", "ꦛ"), ("ng", "ꦔ"),
]

WULU = "ꦶ"    # i
SUKU = "ꦸ"    # u
TALING = "ꦺ"  # é (with TARUNG after the consonant: o)
TARUNG = "ꦴ"
PEPET = "ꦼ"   # e (schwa)

VOWEL_SIGNS = {"a": "", "i": WULU, "u": SUKU, "é": TALING, "o": TALING + TARUNG, "e": PEPET}
VOWELS = list(VOWEL_SIGNS)

_LETTER_TO_LATIN = {script: latin for latin, script in NGLEGENA}
_LATIN_TO_LETTER = {latin: script for latin, script in NGLEGENA}
# Longest consonant first so "nya"/"nga"/"dha"/"tha" are not split.
_CONSONANTS = sorted(_LATIN_TO_LETTER, key=len, reverse=True)


def syllable(consonant, vowel):
    return _LATIN_TO_LETTER[consonant] + VOWEL_SIGNS[vowel]


def to_latin(text):
    """Romanize a string of open syllables, or return None if it contains anything else."""
    if not isinstance(text, str) or not text:
        return None
    out, i = [], 0
    while i < len(text):
        latin = _LETTER_TO_LATIN.get(text[i])
        if latin is None:
            return None
        i += 1
        vowel = "a"
        if text.startswith(TALING + TARUNG, i):
            vowel, i = "o", i + 2
        elif i < len(text) and text[i] in (WULU, SUKU, TALING, PEPET):
            vowel = {WULU: "i", SUKU: "u", TALING: "é", PEPET: "e"}[text[i]]
            i += 1
        out.append(latin + vowel)
    return "".join(out)


def to_script(text):
    """Write a Latin string of open syllables in Aksara Jawa, or return None if impossible."""
    if not isinstance(text, str) or not text:
        return None
    out, i = [], 0
    while i < len(text):
        consonant = next((c for c in _CONSONANTS if text.startswith(c, i)), None)
        if consonant is None:
            return None
        i += len(consonant)
        if i >= len(text) or text[i] not in VOWEL_SIGNS:
            return None
        out.append(syllable(consonant, text[i]))
        i += 1
    script = "".join(out)
    return script if to_latin(script) == text else None


def is_script(text):
    return isinstance(text, str) and bool(text) and all("ꦀ" <= ch <= "꧟" for ch in text)
