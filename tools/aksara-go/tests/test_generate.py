import os
import tempfile
import unittest

import generate
from generators import REGISTRY
from lib import jsonio, validator

FLAGS = {"check_catalog": False, "check_manifest": False, "check_counts": False}


class AppendOnlyGeneration(unittest.TestCase):
    def test_rerun_is_byte_identical_and_raising_target_only_appends(self):
        with tempfile.TemporaryDirectory() as root:
            generate.generate_game(root, "hitung-cepat", ["sd-a"], target=30)
            path = os.path.join(root, "hitung-cepat", "sd-a.json")
            first = jsonio.read_bytes(path)
            generate.generate_game(root, "hitung-cepat", ["sd-a"], target=30)
            self.assertEqual(jsonio.read_bytes(path), first)

            before = {q["id"]: q for q in jsonio.loads(first)["questions"]}
            generate.generate_game(root, "hitung-cepat", ["sd-a"], target=40)
            after = {q["id"]: q for q in jsonio.read(path)["questions"]}
            self.assertEqual(len(after), 40)
            for qid, q in before.items():
                self.assertEqual(after[qid], q)
            # Same questions as a fresh run straight to 40.
            with tempfile.TemporaryDirectory() as fresh:
                generate.generate_game(fresh, "hitung-cepat", ["sd-a"], target=40)
                self.assertEqual(jsonio.read_bytes(os.path.join(fresh, "hitung-cepat", "sd-a.json")),
                                 jsonio.read_bytes(path))

    def test_existing_questions_survive_generator_changes(self):
        with tempfile.TemporaryDirectory() as root:
            generate.generate_game(root, "hitung-cepat", ["sd-a"], target=20)
            path = os.path.join(root, "hitung-cepat", "sd-a.json")
            data = jsonio.read(path)
            data["questions"][0]["explanation"] = "Disunting manual."
            jsonio.write(path, data)
            generate.generate_game(root, "hitung-cepat", ["sd-a"], target=25)
            kept = jsonio.read(path)["questions"]
            self.assertIn("Disunting manual.", [q.get("explanation") for q in kept])
            self.assertEqual(len({q["id"] for q in kept}), 25)

    def test_every_generator_produces_valid_questions(self):
        with tempfile.TemporaryDirectory() as root:
            for game_id, game in REGISTRY.items():
                generate.generate_game(root, game_id, list(game.TARGETS), target=25)
            report = validator.validate(root, **FLAGS)
            problems = [line for line in report.lines() if "meta.segments lists" not in line]
            self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
