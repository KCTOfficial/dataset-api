"""Hand-verified golden answers.

Generators and the validator share `lib/`, so a bug there could make both
agree on a wrong answer. These cases are checked by hand (not computed) and
`validate.py` refuses to run if any of them fails.
"""

import os
import sys
import unicodedata
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import compare, equation, expr, javanese, roman, sequence, terbilang  # noqa: E402


class GoldenTerbilang(unittest.TestCase):
    CASES = {
        0: "nol", 1: "satu", 7: "tujuh", 10: "sepuluh", 11: "sebelas", 12: "dua belas",
        15: "lima belas", 19: "sembilan belas", 20: "dua puluh", 21: "dua puluh satu",
        99: "sembilan puluh sembilan", 100: "seratus", 101: "seratus satu", 111: "seratus sebelas",
        200: "dua ratus", 1000: "seribu", 1001: "seribu satu", 1100: "seribu seratus",
        2020: "dua ribu dua puluh", 2026: "dua ribu dua puluh enam", 10000: "sepuluh ribu",
        11000: "sebelas ribu", 100000: "seratus ribu", 1000000: "satu juta",
        1001000: "satu juta seribu", 1250000: "satu juta dua ratus lima puluh ribu",
        1000000000: "satu miliar", 1000000000000: "satu triliun",
        999000000000000: "sembilan ratus sembilan puluh sembilan triliun",
    }

    def test_words(self):
        for n, words in self.CASES.items():
            self.assertEqual(terbilang.words_int(n), words, n)
            self.assertEqual(terbilang.parse_words(words), n, words)

    def test_decimal(self):
        self.assertEqual(terbilang.words_decimal(3, "25"), "tiga koma dua lima")
        self.assertEqual(terbilang.words_decimal(0, "05"), "nol koma nol lima")

    def test_non_canonical_rejected(self):
        for bad in ["satu ribu", "satu ratus", "dua dua", "milyar", "Dua", "dua  puluh", "satu puluh"]:
            self.assertIsNone(terbilang.parse_words(bad), bad)

    def test_display(self):
        self.assertEqual(terbilang.format_int(2020), "2020")
        self.assertEqual(terbilang.format_int(10000), "10.000")
        self.assertEqual(terbilang.format_int(1250000), "1.250.000")
        self.assertEqual(terbilang.format_decimal(3, "25"), "3,25")
        self.assertIsNone(terbilang.parse_display("2.020"))
        self.assertEqual(terbilang.parse_display("1.250.000"), (1250000, None))


class GoldenArithmetic(unittest.TestCase):
    CASES = {
        "7 + 5": 12, "2 + 4 × 5": 22, "(2 + 4) × 5": 30, "20 − 8 ÷ 2": 16, "(−3) × 4 + 2²": -8,
        "(−3)²": 9, "−3²": -9, "√49 + 3": 10, "∛27 × 2": 6, "²log 32": 5, "log 1000": 3,
        "³log 81 − ²log 8": 1, "2³ × 2²": 32, "(2²)³": 64,
    }

    def test_values(self):
        for text, value in self.CASES.items():
            self.assertEqual(expr.evaluate_text(text), value, text)

    def test_exact_division(self):
        with self.assertRaises(expr.ExprError):
            expr.evaluate_text("7 ÷ 2", exact_division=True)
        self.assertEqual(expr.evaluate_text("7 ÷ 2"), Fraction(7, 2))

    def test_rejects_code(self):
        for bad in ["__import__('os')", "1;2", "2 + abc", "1 + ", "()", "2 ** 3 @ 4"]:
            with self.assertRaises(expr.ExprError, msg=bad):
                expr.evaluate_text(bad)


class GoldenRoman(unittest.TestCase):
    def test_values(self):
        for text, n in {"I": 1, "IV": 4, "IX": 9, "XIV": 14, "XL": 40, "XC": 90, "CD": 400,
                        "CM": 900, "MCMXLV": 1945, "MMXXVI": 2026, "MMMCMXCIX": 3999}.items():
            self.assertEqual(roman.from_roman(text), n, text)
            self.assertEqual(roman.to_roman(n), text, n)

    def test_non_standard_rejected(self):
        for bad in ["IIII", "VV", "IC", "XM", "MMMM", "", "iv"]:
            self.assertIsNone(roman.from_roman(bad), bad)


class GoldenSequenceCompareEquation(unittest.TestCase):
    def test_sequences(self):
        self.assertEqual(sequence.terms({"type": "arithmetic", "start": 2, "step": 2}, 4), [2, 4, 6, 8])
        self.assertEqual(sequence.terms({"type": "geometric", "start": 1, "ratio": 2}, 5), [1, 2, 4, 8, 16])
        self.assertEqual(sequence.terms({"type": "square", "start": 1}, 4), [1, 4, 9, 16])
        self.assertEqual(sequence.terms({"type": "fibonacci", "first": 1, "second": 1}, 6), [1, 1, 2, 3, 5, 8])
        self.assertEqual(sequence.terms({"type": "second-difference", "start": 1, "step": 1, "increment": 1}, 5),
                         [1, 2, 4, 7, 11])

    def test_compare(self):
        self.assertEqual(compare.compare("1/2", "0,5"), "=")
        self.assertEqual(compare.compare("3/4", "0,7"), ">")
        self.assertEqual(compare.compare("25%", "1/4"), "=")
        self.assertEqual(compare.compare("2¹⁰", "10³"), ">")
        self.assertEqual(compare.compare("15", "51"), "<")

    def test_equations(self):
        self.assertEqual(equation.solutions("2x − 5 = 9"), [7])
        self.assertEqual(equation.solutions("? + 3 = 7"), [4])
        self.assertEqual(equation.solutions("2ˣ = 32"), [5])
        self.assertEqual(equation.solutions("²log x = 5"), [32])
        self.assertEqual(equation.solutions("x² = 49"), [-7, 7])


class GoldenJavanese(unittest.TestCase):
    def test_letter_names(self):
        names = {"h": "HA", "n": "NA", "c": "CA", "r": "RA", "k": "KA", "d": "DA", "t": "TA", "s": "SA",
                 "w": "WA", "l": "LA", "p": "PA", "dh": "DDA", "j": "JA", "y": "YA", "ny": "NYA", "m": "MA",
                 "g": "GA", "b": "BA", "th": "TTA", "ng": "NGA"}
        for latin, script in javanese.NGLEGENA:
            self.assertEqual(unicodedata.name(script), "JAVANESE LETTER " + names[latin])
        self.assertEqual(unicodedata.name(javanese.WULU), "JAVANESE VOWEL SIGN WULU")
        self.assertEqual(unicodedata.name(javanese.SUKU), "JAVANESE VOWEL SIGN SUKU")
        self.assertEqual(unicodedata.name(javanese.TALING), "JAVANESE VOWEL SIGN TALING")
        self.assertEqual(unicodedata.name(javanese.TARUNG), "JAVANESE VOWEL SIGN TARUNG")
        self.assertEqual(unicodedata.name(javanese.PEPET), "JAVANESE VOWEL SIGN PEPET")

    def test_syllables(self):
        ka = "ꦏ"
        self.assertEqual(javanese.to_latin(ka), "ka")
        self.assertEqual(javanese.to_latin(ka + "ꦶ"), "ki")
        self.assertEqual(javanese.to_latin(ka + "ꦸ"), "ku")
        self.assertEqual(javanese.to_latin(ka + "ꦺ"), "ké")
        self.assertEqual(javanese.to_latin(ka + "ꦺꦴ"), "ko")
        self.assertEqual(javanese.to_latin(ka + "ꦼ"), "ke")
        self.assertEqual(javanese.to_latin("ꦧꦸꦏꦸ"), "buku")
        self.assertEqual(javanese.to_script("buku"), "ꦧꦸꦏꦸ")


def run_golden(verbosity=0):
    """Run all golden tests; True if every case passes."""
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stderr).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(0 if run_golden(verbosity=2) else 1)
