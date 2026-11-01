import os
import tempfile
import unittest

from lib import ids, jsonio


class JsonIoTest(unittest.TestCase):
    def test_write_is_byte_identical_lf_no_bom(self):
        obj = jsonio.canonical_file({
            "questions": [{"answer": 12, "prompt": {"text": "7 + 5"}, "id": "x.sd-a.0001", "difficulty": 1}],
            "gameId": "x", "schemaVersion": 1, "segment": "sd-a", "jenjang": "SD", "interaction": "NUMPAD",
        })
        with tempfile.TemporaryDirectory() as tmp:
            p1, p2 = os.path.join(tmp, "a.json"), os.path.join(tmp, "b.json")
            jsonio.write(p1, obj)
            jsonio.write(p2, jsonio.canonical_file(jsonio.read(p1)))
            raw1, raw2 = jsonio.read_bytes(p1), jsonio.read_bytes(p2)
        self.assertEqual(raw1, raw2)
        self.assertFalse(raw1.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", raw1)
        self.assertTrue(raw1.endswith(b"}\n"))
        self.assertTrue(raw1.startswith(b'{\n  "schemaVersion": 1,\n  "gameId": "x"'))

    def test_unicode_kept_literal(self):
        self.assertIn("×".encode("utf-8"), jsonio.dumps({"t": "2 × 3"}))

    def test_rejects_bom_and_duplicate_keys(self):
        with self.assertRaises(ValueError):
            jsonio.loads(b"\xef\xbb\xbf{}")
        with self.assertRaises(jsonio.DuplicateKeyError):
            jsonio.loads(b'{"a": 1, "a": 2}')


class IdsTest(unittest.TestCase):
    def test_make_and_parse(self):
        qid = ids.make_id("lengkapi-kata", "sd-a", 42)
        self.assertEqual(qid, "lengkapi-kata.sd-a.0042")
        self.assertEqual(ids.parse_id(qid), ("lengkapi-kata", "sd-a", 42))

    def test_malformed(self):
        for bad in ["lengkapi-kata.sd-a.42", "Lengkapi.sd-a.0001", "x.sd-d.0001", None, 5]:
            self.assertIsNone(ids.parse_id(bad))

    def test_next_seq_skips_retired(self):
        qs = [{"id": "x.sd-a.0001"}, {"id": "x.sd-a.0007"}]
        self.assertEqual(ids.next_seq(qs), 8)


if __name__ == "__main__":
    unittest.main()
