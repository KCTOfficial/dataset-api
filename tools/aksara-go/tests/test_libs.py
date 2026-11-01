import random
import unittest

from lib import equation, expr, javanese, roman, sequence, terbilang

SEGMENT_RANGES = [(1, 100), (1, 10_000), (1, 1_000_000), (1, 999_999_999_999), (1, 999_999_999_999_999)]


class TerbilangRoundTrip(unittest.TestCase):
    def test_round_trip_per_segment_range(self):
        rng = random.Random(2020)
        for low, high in SEGMENT_RANGES:
            for _ in range(10_000):
                n = rng.randint(low, high)
                self.assertEqual(terbilang.parse_words(terbilang.words_int(n)), n)
                self.assertEqual(terbilang.parse_display(terbilang.format_int(n)), (n, None))

    def test_out_of_range(self):
        for bad in [-1, 10**15, 1.5, True]:
            with self.assertRaises(ValueError):
                terbilang.words_int(bad)


class ExprTest(unittest.TestCase):
    def test_info(self):
        info = expr.info(expr.parse("2 + 4 × 5"))
        self.assertEqual(info["ops"], ["+", "*"])
        self.assertFalse(info["parens"])
        self.assertTrue(expr.info(expr.parse("(2 + 4) × 5"))["parens"])

    def test_intermediates(self):
        values = []
        expr.evaluate(expr.parse("3 − 5 + 4"), intermediates=values)
        self.assertIn(-2, values)

    def test_variables_only_when_allowed(self):
        with self.assertRaises(expr.ExprError):
            expr.parse("2x + 1")
        self.assertEqual(expr.evaluate(expr.parse("2x + 1", allow_vars=True), {"x": 3}), 7)
        self.assertEqual(expr.evaluate(expr.parse("3(x + 2)", allow_vars=True), {"x": 1}), 9)

    def test_non_exact_root_and_log(self):
        for bad in ["√50", "²log 10", "√(−4)"]:
            with self.assertRaises(expr.ExprError, msg=bad):
                expr.evaluate_text(bad)

    def test_display_errors(self):
        self.assertEqual(expr.display_errors("2 + 4 × 5"), [])
        self.assertTrue(expr.display_errors("2 + 4 * 5"))
        self.assertTrue(expr.display_errors("2 x 5"))
        self.assertTrue(expr.display_errors("5 - 2"))
        self.assertEqual(expr.display_errors("2x − 5 = 9", allow_x=True), [])


class RomanTest(unittest.TestCase):
    def test_round_trip(self):
        for n in range(1, 4000):
            self.assertEqual(roman.from_roman(roman.to_roman(n)), n)


class SequenceTest(unittest.TestCase):
    def test_spec_case_rejected(self):
        # Spec: [2, 4, 7, null] with arithmetic step 2 is inconsistent (third term is 6).
        self.assertEqual(sequence.terms({"type": "arithmetic", "start": 2, "step": 2}, 4)[2], 6)

    def test_rules(self):
        self.assertEqual(sequence.terms({"type": "cube", "start": 1}, 4), [1, 8, 27, 64])
        self.assertEqual(sequence.terms({"type": "alternating", "start": 1, "steps": [3, -1]}, 5), [1, 4, 3, 6, 5])
        self.assertEqual(sequence.terms({"type": "geometric", "start": 3, "ratio": -2}, 4), [3, -6, 12, -24])

    def test_malformed_rules(self):
        self.assertIsNotNone(sequence.rule_error({"type": "arithmetic", "start": 1}))
        self.assertIsNotNone(sequence.rule_error({"type": "magic"}))
        self.assertIsNotNone(sequence.rule_error({"type": "geometric", "start": 1, "ratio": 1}))


class EquationTest(unittest.TestCase):
    def test_unique_linear(self):
        self.assertEqual(equation.solutions("3x + 4 = 2x + 9"), [5])
        self.assertEqual(equation.solutions("4(x − 2) = 20"), [7])

    def test_identity_has_many_solutions(self):
        self.assertGreater(len(equation.solutions("x + 1 = 1 + x")), 1)


class JavaneseTest(unittest.TestCase):
    def test_every_syllable_round_trips(self):
        for consonant, _ in javanese.NGLEGENA:
            for vowel in javanese.VOWELS:
                latin = consonant + vowel
                self.assertEqual(javanese.to_latin(javanese.to_script(latin)), latin)

    def test_rejects_non_open_syllables(self):
        self.assertIsNone(javanese.to_script("buk"))
        self.assertIsNone(javanese.to_latin("abc"))


if __name__ == "__main__":
    unittest.main()
