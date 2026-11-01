"""Deterministic JSON reading/writing for the AksaraGo dataset.

Every dataset file is written through `dumps`, so identical content always
produces identical bytes (and therefore identical SHA-256 in the manifest).
"""

import hashlib
import json
import os

FILE_KEYS = ["schemaVersion", "gameId", "segment", "jenjang", "interaction", "questions"]
QUESTION_KEYS = ["id", "difficulty", "interaction", "prompt", "answer", "payload", "explanation"]
PROMPT_KEYS = ["text", "hint", "emoji", "number", "letters", "sequence", "left", "right"]
META_KEYS = [
    "gameId", "title", "description", "category", "contentKind", "interaction",
    "instruction", "emoji", "colorToken", "segments", "review",
]


class DuplicateKeyError(ValueError):
    pass


def _ordered(obj, keys):
    """Return a copy of `obj` with `keys` first (in order), then any other keys sorted."""
    out = {k: obj[k] for k in keys if k in obj}
    for k in sorted(set(obj) - set(keys)):
        out[k] = obj[k]
    return out


def _sorted_dict(value):
    if isinstance(value, dict):
        return {k: _sorted_dict(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_sorted_dict(v) for v in value]
    return value


def canonical_question(q):
    q = _ordered(q, QUESTION_KEYS)
    if isinstance(q.get("prompt"), dict):
        q["prompt"] = _ordered(q["prompt"], PROMPT_KEYS)
    if isinstance(q.get("payload"), dict):
        q["payload"] = _sorted_dict(q["payload"])
    return q


def canonical_file(data):
    data = _ordered(data, FILE_KEYS)
    if isinstance(data.get("questions"), list):
        data["questions"] = [canonical_question(q) if isinstance(q, dict) else q for q in data["questions"]]
    return data


def canonical_meta(meta):
    meta = _ordered(meta, META_KEYS)
    if isinstance(meta.get("review"), dict):
        meta["review"] = _sorted_dict(meta["review"])
    return meta


def dumps(obj):
    """Serialize to canonical bytes: UTF-8 (no BOM), 2-space indent, LF, trailing newline."""
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = dumps(obj)
    # Binary mode: no platform newline translation.
    with open(path, "wb") as fh:
        fh.write(data)
    return data


def _reject_duplicates(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise DuplicateKeyError(f"duplicate key '{k}'")
        seen[k] = v
    return seen


def loads(raw):
    """Parse bytes strictly: rejects a BOM, invalid UTF-8, and duplicate object keys."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("file starts with a UTF-8 BOM")
    text = raw.decode("utf-8")
    return json.loads(text, object_pairs_hook=_reject_duplicates)


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read(path):
    return loads(read_bytes(path))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()
