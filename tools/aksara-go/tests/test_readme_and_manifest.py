import json
import os
import re
import unittest

import build_manifest
from lib import ids, jsonio, manifest, validator
from tests.fixtures import Dataset, has, meta_for, question as Q

README = os.path.join(os.path.dirname(__file__), "..", "..", "..", "aksara-go", "README.md")
FLAGS = {"check_catalog": False, "check_counts": False}


class ReadmeExamples(unittest.TestCase):
    def test_every_question_example_passes(self):
        with open(README, encoding="utf-8") as fh:
            blocks = re.findall(r"```json\n(.*?)\n```", fh.read(), re.S)
        examples = [json.loads(b) for b in blocks if b.startswith('{"id"')]
        self.assertEqual(len(examples), 6)  # one per interaction
        for q in examples:
            game_id, segment, _ = ids.parse_id(q["id"])
            with Dataset() as ds:
                ds.add(game_id, {segment: [q]})
                report = ds.validate()
            per_question = [m for _, qid, m in report.violations if qid == q["id"]]
            self.assertEqual(per_question, [], q["id"])


def curated_file():
    return [Q("kata-baku", "smp", i, {"text": f"Mana yang baku? ({i})"}, "apotek", 1 + i % 3,
              payload={"options": ["apotek", "apotik"]}, explanation="Bentuk baku: apotek.")
            for i in (3, 1, 2)]


class ManifestScenarios(unittest.TestCase):
    def build(self, ds):
        data, _ = build_manifest.build_and_write(ds.root, **FLAGS)
        return {f["path"]: f for g in data["games"] for f in g["files"]}

    def test_checksum_drift_detected(self):
        with Dataset() as ds:
            ds.add("hitung-cepat", {"sd-a": [Q("hitung-cepat", "sd-a", i, {"text": f"{i} + 1"}, i + 1, i)
                                             for i in (1, 2, 3)]})
            self.build(ds)
            self.assertEqual(validator.validate(ds.root, **FLAGS).lines(), [])
            raw = jsonio.read_bytes(ds.path("hitung-cepat/sd-a.json"))
            ds.write_raw("hitung-cepat/sd-a.json", raw.replace(b'"3 + 1"', b'"3 + 0"').replace(b"4\n", b"3\n"))
            report = validator.validate(ds.root, **FLAGS)
            self.assertTrue(has(report, "SHA-256 in manifest"))
            self.build(ds)
            self.assertEqual(validator.validate(ds.root, **FLAGS).lines(), [])

    def test_new_curated_file_starts_as_draft(self):
        with Dataset() as ds:
            ds.add("kata-baku", {"smp": sorted(curated_file(), key=lambda q: q["difficulty"])})
            self.assertEqual(self.build(ds)["kata-baku/smp.json"]["status"], "draft")

    def test_review_status_derived_not_hand_set(self):
        with Dataset() as ds:
            ds.add("kata-baku", {"smp": sorted(curated_file(), key=lambda q: q["difficulty"])})
            digest = jsonio.sha256(jsonio.read_bytes(ds.path("kata-baku/smp.json")))
            review = {"smp": {"sha256": digest, "date": "2026-11-01", "role": "guru Bahasa Indonesia"}}
            jsonio.write(ds.path("kata-baku/meta.json"),
                         jsonio.canonical_meta(meta_for("kata-baku", ["smp"], review=review)))
            self.assertEqual(self.build(ds)["kata-baku/smp.json"]["status"], "reviewed")
            # Editing the reviewed file drops it back to draft automatically.
            data = jsonio.read(ds.path("kata-baku/smp.json"))
            data["questions"][0]["explanation"] = "Bentuk baku menurut KBBI: apotek."
            jsonio.write(ds.path("kata-baku/smp.json"), data)
            self.assertEqual(self.build(ds)["kata-baku/smp.json"]["status"], "draft")

    def test_procedural_files_are_reviewed_by_construction(self):
        with Dataset() as ds:
            ds.add("hitung-cepat", {"sd-a": [Q("hitung-cepat", "sd-a", i, {"text": f"{i} + 1"}, i + 1, i)
                                             for i in (1, 2, 3)]})
            self.assertEqual(self.build(ds)["hitung-cepat/sd-a.json"]["status"], "reviewed")
            ds.add("hitung-cepat", {"sd-a": [Q("hitung-cepat", "sd-a", i, {"text": f"{i} + 1"}, i, i)
                                             for i in (1, 2, 3)]})
            self.assertEqual(self.build(ds)["hitung-cepat/sd-a.json"]["status"], "draft")

    def test_consumer_can_skip_unchanged_files(self):
        with Dataset() as ds:
            ds.add("hitung-cepat", {"sd-a": [Q("hitung-cepat", "sd-a", i, {"text": f"{i} + 1"}, i + 1, i)
                                             for i in (1, 2, 3)]})
            entry = self.build(ds)["hitung-cepat/sd-a.json"]
            cached = jsonio.read_bytes(ds.path("hitung-cepat/sd-a.json"))
            self.assertEqual(jsonio.sha256(cached), entry["sha256"])
            self.assertEqual(self.build(ds)["hitung-cepat/sd-a.json"]["sha256"], entry["sha256"])

    def test_missing_manifest_reported(self):
        with Dataset() as ds:
            ds.add("hitung-cepat", {"sd-a": [Q("hitung-cepat", "sd-a", i, {"text": f"{i} + 1"}, i + 1, i)
                                             for i in (1, 2, 3)]})
            self.assertTrue(has(validator.validate(ds.root, **FLAGS), "manifest.json is missing"))

    def test_version_kept_across_rebuilds(self):
        with Dataset() as ds:
            ds.add("hitung-cepat", {"sd-a": [Q("hitung-cepat", "sd-a", i, {"text": f"{i} + 1"}, i + 1, i)
                                             for i in (1, 2, 3)]})
            build_manifest.build_and_write(ds.root, version="1.2.0", **FLAGS)
            build_manifest.build_and_write(ds.root, **FLAGS)
            self.assertEqual(manifest.existing_version(ds.root), "1.2.0")


if __name__ == "__main__":
    unittest.main()
