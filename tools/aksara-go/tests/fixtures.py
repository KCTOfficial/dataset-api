"""Build small fixture datasets in a temporary directory for validator tests."""

import os
import tempfile

from lib import catalog, ids, jsonio


def meta_for(game_id, segments=None, **overrides):
    spec = catalog.CATALOG[game_id]
    meta = {
        "gameId": game_id,
        "title": spec["title"],
        "description": spec["description"],
        "category": spec["category"],
        "contentKind": spec["contentKind"],
        "interaction": spec["interaction"],
        "instruction": spec["instruction"],
        "emoji": spec["emoji"],
        "colorToken": spec["colorToken"],
        "segments": segments if segments is not None else spec["segments"],
    }
    meta.update(overrides)
    return meta


def question(game_id, segment, seq, prompt, answer, difficulty=1, **extra):
    q = {"id": ids.make_id(game_id, segment, seq), "difficulty": difficulty, "prompt": prompt, "answer": answer}
    q.update(extra)
    return q


def file_for(game_id, segment, questions, interaction=None):
    return {
        "schemaVersion": 1,
        "gameId": game_id,
        "segment": segment,
        "jenjang": catalog.SEGMENTS[segment],
        "interaction": interaction or catalog.CATALOG[game_id]["interaction"],
        "questions": questions,
    }


class Dataset:
    """Context manager: `with Dataset() as ds: ds.add(...); report = ds.validate()`."""

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        return self

    def __exit__(self, *exc):
        self._tmp.cleanup()

    def path(self, rel):
        return os.path.join(self.root, rel)

    def add(self, game_id, files, meta=None):
        """`files`: {segment: [questions] or full file dict}."""
        segments = [s for s in catalog.SEGMENT_ORDER if s in files]
        jsonio.write(self.path(f"{game_id}/meta.json"),
                     jsonio.canonical_meta(meta or meta_for(game_id, segments)))
        for segment, content in files.items():
            data = content if isinstance(content, dict) else file_for(game_id, segment, content)
            jsonio.write(self.path(f"{game_id}/{segment}.json"), jsonio.canonical_file(data))

    def write_raw(self, rel, raw):
        with open(self.path(rel), "wb") as fh:
            fh.write(raw)

    def validate(self, **flags):
        from lib import validator
        options = {"check_catalog": False, "check_manifest": False, "check_counts": False}
        options.update(flags)
        return validator.validate(self.root, **options)


def messages(report, qid=None):
    return [m for _, q, m in report.violations if qid is None or q == qid]


def has(report, fragment, qid=None):
    return any(fragment in m for m in messages(report, qid))
