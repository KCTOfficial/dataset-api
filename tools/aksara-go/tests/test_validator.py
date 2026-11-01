"""Fixture tests: one per spec scenario (specs/question-dataset, specs/question-bank-content)."""

import contextlib
import io
import unittest

from lib import jsonio
from tests.fixtures import Dataset, file_for, has, messages, meta_for, question as Q

HC = "hitung-cepat"


def hc(seq, text, answer, difficulty=1, segment="sd-a", **extra):
    return Q(HC, segment, seq, {"text": text}, answer, difficulty, **extra)


def clean_hc():
    return [hc(1, "7 + 5", 12, 1), hc(2, "9 − 4", 5, 2), hc(3, "8 + 8", 16, 3)]


class EnvelopeScenarios(unittest.TestCase):
    def test_minimal_valid_question(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()})
            report = ds.validate()
        self.assertEqual(report.lines(), [])

    def test_missing_answer_rejected(self):
        bad = hc(4, "3 + 3", 6, 3)
        del bad["answer"]
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc() + [bad]})
            report = ds.validate()
        self.assertTrue(has(report, "missing answer", "hitung-cepat.sd-a.0004"))
        self.assertTrue(any(p == "hitung-cepat/sd-a.json" for p, _, _ in report.violations))

    def test_difficulty_out_of_range_rejected(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc() + [hc(4, "1 + 1", 2, 0), hc(5, "2 + 1", 3, 6)]})
            report = ds.validate()
        self.assertTrue(has(report, "difficulty must be an integer 1-5", "hitung-cepat.sd-a.0004"))
        self.assertTrue(has(report, "difficulty must be an integer 1-5", "hitung-cepat.sd-a.0005"))

    def test_segment_and_jenjang_agree(self):
        data = file_for(HC, "sd-b", [hc(1, "12 + 30", 42, 1, "sd-b"), hc(2, "3 × 4", 12, 2, "sd-b"),
                                     hc(3, "50 − 8", 42, 3, "sd-b")])
        data["jenjang"] = "SMP"
        with Dataset() as ds:
            ds.add(HC, {"sd-b": data})
            report = ds.validate()
        self.assertTrue(has(report, "inconsistent with segment 'sd-b'"))


class InteractionScenarios(unittest.TestCase):
    def test_multiple_choice_answer_not_among_options(self):
        q = Q("kata-baku", "smp", 1, {"text": "Mana yang baku?"}, "apoteker",
              payload={"options": ["apotek", "apotik"]}, explanation="Bentuk baku: apotek.")
        with Dataset() as ds:
            ds.add("kata-baku", {"smp": [q]})
            report = ds.validate()
        self.assertTrue(has(report, "answer must equal exactly one of payload.options", "kata-baku.smp.0001"))

    def test_fill_gap_mask_consistent_passes(self):
        q = Q("lengkapi-kata", "sd-a", 1, {"text": "H_RI_A_", "hint": "Hewan buas bergaris"}, "HARIMAU")
        with Dataset() as ds:
            ds.add("lengkapi-kata", {"sd-a": [q]})
            report = ds.validate()
        self.assertEqual(messages(report, "lengkapi-kata.sd-a.0001"), [])

    def test_fill_gap_mask_contradicting_answer_rejected(self):
        q = Q("lengkapi-kata", "sd-a", 1, {"text": "H_RO_A_", "hint": "Hewan buas bergaris"}, "HARIMAU")
        with Dataset() as ds:
            ds.add("lengkapi-kata", {"sd-a": [q]})
            report = ds.validate()
        self.assertTrue(has(report, "does not match the answer", "lengkapi-kata.sd-a.0001"))

    def test_per_question_interaction_override(self):
        roman_to = Q("angka-romawi", "sd-b", 1, {"text": "14"}, "XIV", 1,
                     interaction="TILE_BANK", payload={"distractors": ["L", "I"]})
        bad_override = Q("angka-romawi", "sd-b", 2, {"text": "15"}, "XV", 2, interaction="TILE_BANK")
        roman_from = Q("angka-romawi", "sd-b", 3, {"text": "XIV"}, 14, 3)
        with Dataset() as ds:
            ds.add("angka-romawi", {"sd-b": [roman_to, bad_override, roman_from]})
            report = ds.validate()
        self.assertEqual(messages(report, "angka-romawi.sd-b.0001"), [])
        self.assertTrue(has(report, "TILE_BANK needs payload.distractors", "angka-romawi.sd-b.0002"))
        self.assertEqual(messages(report, "angka-romawi.sd-b.0003"), [])

    def test_multiplication_symbol(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-c": [hc(1, "2 + 4 * 5", 22, 1, "sd-c"), hc(2, "2 + 4 × 5", 22, 2, "sd-c"),
                                 hc(3, "3 + 2 × 5", 13, 3, "sd-c")]})
            report = ds.validate()
        self.assertTrue(has(report, "use '×' instead of '*'", "hitung-cepat.sd-c.0001"))
        self.assertEqual(messages(report, "hitung-cepat.sd-c.0002"), [])

    def test_rendering_mode_not_in_data(self):
        q = Q("tebak-angka", "sd-b", 1, {"text": "2020", "number": 2020}, "dua ribu dua puluh",
              payload={"distractors": ["ratus", "tiga"]}, presentation="letters")
        with Dataset() as ds:
            ds.add("tebak-angka", {"sd-b": [q]})
            report = ds.validate()
        self.assertTrue(has(report, "unknown question keys ['presentation']", "tebak-angka.sd-b.0001"))


class DatasetScenarios(unittest.TestCase):
    def test_duplicate_id_rejected(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc() + [hc(1, "1 + 2", 3, 3)]})
            report = ds.validate()
        self.assertTrue(has(report, "duplicate id", "hitung-cepat.sd-a.0001"))

    def test_id_prefix_mismatch_rejected(self):
        q = Q("kata-baku", "smp", 3, {"text": "Mana yang baku?"}, "apotek",
              payload={"options": ["apotek", "apotik"]}, explanation="Bentuk baku: apotek.")
        with Dataset() as ds:
            ds.add("kata-baku", {"sma": [q]})
            report = ds.validate()
        self.assertTrue(has(report, "id prefix does not match file kata-baku/sma.json", "kata-baku.smp.0003"))

    def test_meta_lists_exactly_the_files_present(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()}, meta=meta_for(HC, ["sd-a", "sd-b"]))
            report = ds.validate()
        self.assertTrue(has(report, "lists ['sd-b'] but those files are missing"))

    def test_unsupported_segment_has_no_file(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()})
            ds.write_raw("hitung-cepat/notes.txt", b"x")
            report = ds.validate()
        self.assertTrue(has(report, "unexpected file in a game folder"))

    def test_catalog_completeness(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()})
            report = ds.validate(check_catalog=True)
        self.assertTrue(has(report, "catalog game is missing from the dataset"))
        self.assertTrue(has(report, "meta.segments ['sd-a'] differs from the catalog"))

    def test_procedural_segment_below_minimum(self):
        questions = [hc(i, f"{i % 10} + {i // 10}", i % 10 + i // 10, 1 + (i - 1) // 33) for i in range(1, 100)]
        with Dataset() as ds:
            ds.add(HC, {"sd-a": questions})
            report = ds.validate(check_counts=True)
        self.assertTrue(has(report, "has 99 questions; procedural files need at least 100"))

    def test_curated_game_meets_total_but_one_segment_is_thin(self):
        def proverb_file(segment, count):
            return [Q("peribahasa", segment, i, {"text": f"Peribahasa {i} …"}, f"jawaban {i}", 1 + i % 3,
                      payload={"options": [f"jawaban {i}", "salah"]}, explanation="Makna.")
                    for i in range(1, count + 1)]
        with Dataset() as ds:
            smp = sorted(proverb_file("smp", 95), key=lambda q: q["difficulty"])
            sd_c = sorted(proverb_file("sd-c", 15), key=lambda q: q["difficulty"])
            ds.add("peribahasa", {"sd-c": sd_c, "smp": smp})
            report = ds.validate(check_counts=True)
        self.assertTrue(has(report, "has 15 questions; curated files need at least 20"))
        self.assertFalse(has(report, "curated games need at least 100"))

    def test_duplicate_question_rejected(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc() + [hc(4, "7 + 5", 12, 3)]})
            report = ds.validate()
        self.assertTrue(has(report, "duplicate of hitung-cepat.sd-a.0001", "hitung-cepat.sd-a.0004"))

    def test_flat_difficulty_rejected(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": [hc(1, "1 + 1", 2, 2), hc(2, "1 + 2", 3, 2), hc(3, "1 + 3", 4, 2)]})
            report = ds.validate()
        self.assertTrue(has(report, "needs at least 3 distinct difficulty values"))


class ProceduralScenarios(unittest.TestCase):
    def check(self, game, segment, questions):
        with Dataset() as ds:
            ds.add(game, {segment: questions})
            return ds.validate()

    def test_wrong_arithmetic_answer_caught(self):
        report = self.check(HC, "sd-c", [hc(1, "2 + 4 × 5", 30, 1, "sd-c")])
        self.assertTrue(has(report, "answer 30 does not match recomputed 22"))

    def test_wrong_terbilang_caught(self):
        q = Q("tebak-angka", "sd-b", 1, {"text": "2020", "number": 2020}, "dua ribu dua puluh enam",
              payload={"distractors": ["ratus"]})
        report = self.check("tebak-angka", "sd-b", [q])
        self.assertTrue(has(report, "is not the canonical terbilang 'dua ribu dua puluh'"))

    def test_mixed_operators_only_from_sd_fase_c(self):
        report = self.check(HC, "sd-b", [hc(1, "2 + 4 × 5", 22, 1, "sd-b")])
        self.assertTrue(has(report, "sd-b uses exactly one operator"))

    def test_non_exact_division_rejected(self):
        report = self.check(HC, "sd-b", [hc(1, "7 ÷ 2", 3, 1, "sd-b")])
        self.assertTrue(has(report, "division is not exact"))

    def test_out_of_range_number_rejected(self):
        q = Q("tebak-angka", "sd-a", 1, {"text": "250", "number": 250}, "dua ratus lima puluh",
              payload={"distractors": ["tiga"]})
        report = self.check("tebak-angka", "sd-a", [q])
        self.assertTrue(has(report, "outside the sd-a range"))

    def test_irregular_forms(self):
        cases = [(11, "sebelas"), (100, "seratus"), (1000, "seribu"), (1_000_000, "satu juta")]
        questions = [Q("tebak-angka", "sd-c", i + 1, {"text": f"{n:,}".replace(",", ".") if n >= 10000 else str(n),
                                                       "number": n}, words, 1 + i % 3,
                       payload={"distractors": ["dua"]}) for i, (n, words) in enumerate(cases)]
        report = self.check("tebak-angka", "sd-c", sorted(questions, key=lambda q: q["difficulty"]))
        self.assertEqual([m for m in messages(report) if "difficulty" not in m], [])

    def test_sequence_term_inconsistent_with_rule(self):
        q = Q("deret-angka", "sd-a", 1, {"text": "2, 4, 7, ?", "sequence": [2, 4, 7, None]}, 8,
              payload={"rule": {"type": "arithmetic", "start": 2, "step": 2}})
        report = self.check("deret-angka", "sd-a", [q])
        self.assertTrue(has(report, "term 3 is 7 but the rule gives 6"))

    def test_non_standard_roman_rejected(self):
        report = self.check("angka-romawi", "sd-b", [Q("angka-romawi", "sd-b", 1, {"text": "IIII"}, 4)])
        self.assertTrue(has(report, "is not a standard Roman numeral"))

    def test_syllable_mapping_verified(self):
        ki = "ꦏꦶ"
        q = Q("aksara-nusantara", "sd-b", 1, {"text": ki}, "ki", payload={"options": ["ki", "ku", "ka", "ke"]})
        report = self.check("aksara-nusantara", "sd-b", [q])
        self.assertEqual(messages(report, "aksara-nusantara.sd-b.0001"), [])

    def test_mismatched_syllable_rejected(self):
        ku = "ꦏꦸ"
        q = Q("aksara-nusantara", "sd-b", 1, {"text": ku}, "ki", payload={"options": ["ki", "ku", "ka", "ke"]})
        report = self.check("aksara-nusantara", "sd-b", [q])
        self.assertTrue(has(report, "the script reads 'ku'"))

    def test_malicious_expression_is_not_executed(self):
        report = self.check(HC, "sd-a", [hc(1, "__import__('os')", 0, 1)])
        self.assertTrue(has(report, "cannot evaluate prompt"))

    def test_cari_x_uniqueness(self):
        q = Q("cari-x", "sma", 1, {"text": "x² = 49"}, 7)
        report = self.check("cari-x", "sma", [q])
        self.assertTrue(has(report, "not uniquely solvable"))

    def test_banding_distribution(self):
        qs = [Q("banding-angka", "sd-a", i, {"text": f"{i} ? 50", "left": str(i), "right": "50"}, "<", 1 + i % 3)
              for i in range(1, 6)]
        report = self.check("banding-angka", "sd-a", sorted(qs, key=lambda q: q["difficulty"]))
        self.assertTrue(has(report, "needs at least 20%"))


class CuratedScenarios(unittest.TestCase):
    def test_ambiguous_fill_gap_rejected(self):
        buku = Q("lengkapi-kata", "sd-a", 1, {"text": "B_KU", "hint": "Dibaca di sekolah"}, "BUKU")
        baku = Q("susun-huruf", "sd-a", 1, {"text": "K U A B", "letters": ["K", "U", "A", "B"]}, "BAKU",
                 payload={"distractors": []})
        with Dataset() as ds:
            ds.add("lengkapi-kata", {"sd-a": [buku]})
            ds.add("susun-huruf", {"sd-a": [baku]})
            report = ds.validate()
        self.assertTrue(has(report, "ambiguous: B_KU also fits BAKU", "lengkapi-kata.sd-a.0001"))

    def test_hint_required(self):
        q = Q("lengkapi-kata", "sd-a", 1, {"text": "H_RI_A_"}, "HARIMAU")
        with Dataset() as ds:
            ds.add("lengkapi-kata", {"sd-a": [q]})
            report = ds.validate()
        self.assertTrue(has(report, "need a prompt.hint"))

    def test_ambiguous_anagram_rejected(self):
        kata = Q("susun-huruf", "sd-a", 1, {"text": "T A K A", "letters": ["T", "A", "K", "A"]}, "KATA",
                 payload={"distractors": []})
        taka = Q("lengkapi-kata", "sd-a", 1, {"text": "T_KA", "hint": "contoh"}, "TAKA")
        with Dataset() as ds:
            ds.add("susun-huruf", {"sd-a": [kata]})
            ds.add("lengkapi-kata", {"sd-a": [taka]})
            report = ds.validate()
        self.assertTrue(has(report, "ambiguous anagram: letters also spell TAKA", "susun-huruf.sd-a.0001"))

    def test_susun_kalimat_distractors(self):
        q = Q("susun-kalimat", "sd-a", 1, {"text": "Kegiatan Ibu"}, "Ibu pergi ke pasar.",
              payload={"distractors": ["ke", "sekolah"]})
        with Dataset() as ds:
            ds.add("susun-kalimat", {"sd-a": [q]})
            report = ds.validate()
        self.assertTrue(has(report, "must not repeat words of the answer: ['ke']"))


class FormattingAndGate(unittest.TestCase):
    def test_crlf_and_bom_rejected(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()})
            raw = jsonio.read_bytes(ds.path("hitung-cepat/sd-a.json"))
            ds.write_raw("hitung-cepat/sd-a.json", b"\xef\xbb\xbf" + raw.replace(b"\n", b"\r\n"))
            report = ds.validate()
        self.assertTrue(has(report, "cannot read JSON") or has(report, "BOM"))

    def test_crlf_rejected(self):
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()})
            raw = jsonio.read_bytes(ds.path("hitung-cepat/sd-a.json"))
            ds.write_raw("hitung-cepat/sd-a.json", raw.replace(b"\n", b"\r\n"))
            report = ds.validate()
        self.assertTrue(has(report, "LF line endings"))

    def test_clean_dataset_and_injected_error_exit_codes(self):
        import build_manifest
        import validate
        from lib import validator
        flags = {"check_catalog": False, "check_counts": False}
        with Dataset() as ds:
            ds.add(HC, {"sd-a": clean_hc()})
            build_manifest.build_and_write(ds.root, **flags)
            self.assertEqual(validator.validate(ds.root, **flags).lines(), [])
            ds.add(HC, {"sd-a": clean_hc() + [hc(4, "1 + 1", 3, 3)]})
            report = validator.validate(ds.root, **flags)
            self.assertTrue(has(report, "answer 3 does not match recomputed 2", "hitung-cepat.sd-a.0004"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = validate.main(["--root", ds.root])
            self.assertEqual(code, 1)
            self.assertIn("hitung-cepat/sd-a.json#hitung-cepat.sd-a.0004: answer 3 does not match", out.getvalue())

if __name__ == "__main__":
    unittest.main()
