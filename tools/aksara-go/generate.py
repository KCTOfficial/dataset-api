"""Generate or extend procedural game files, append-only.

Existing questions (and their ids) are never changed or removed. The candidate
stream is seeded from gameId+segment and replayed from the start on every run,
so a run reproduces the questions a previous run accepted and only appends new
ones once the existing count is passed. Files are kept sorted by
(difficulty, id sequence); ids never change, only positions.
"""

import argparse
import hashlib
import itertools
import os
import random
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from generators import REGISTRY  # noqa: E402
from lib import catalog, ids, jsonio  # noqa: E402
from lib.validator import _normalized_key  # noqa: E402

DEFAULT_ROOT = os.path.normpath(os.path.join(TOOLS_DIR, "..", "..", "aksara-go"))
MAX_CONSECUTIVE_MISSES = 3000


class GenerationError(RuntimeError):
    pass


def seed_for(game_id, segment):
    return int.from_bytes(hashlib.sha256(f"{game_id}:{segment}".encode()).digest()[:8], "big")


def candidate_stream(game, segment):
    """Deterministic stream: featured candidates first, then difficulty round-robin."""
    rng = random.Random(seed_for(game.GAME_ID, segment))
    featured = getattr(game, "featured", None)
    for candidate in (featured(rng, segment) if featured else []):
        if candidate is not None:
            yield candidate
    produce = game.make(segment) if hasattr(game, "make") else game.generate
    misses = {d: 0 for d in range(1, 6)}
    for d in itertools.cycle(range(1, 6)):
        if all(m >= MAX_CONSECUTIVE_MISSES for m in misses.values()):
            return
        if misses[d] >= MAX_CONSECUTIVE_MISSES:
            continue
        candidate = produce(rng, segment, d)
        accepted = yield candidate
        misses[d] = 0 if accepted else misses[d] + 1


def _run(game, segment, wanted):
    """First `wanted` distinct candidates of the stream (exactly what a fresh run would accept)."""
    accepted, keys = [], set()
    stream = candidate_stream(game, segment)
    reply = None
    while len(accepted) < wanted:
        try:
            candidate = stream.send(reply) if reply is not None else next(stream)
        except StopIteration:
            break
        reply = False
        if candidate is None:
            continue
        key = _normalized_key(candidate)
        if key not in keys:
            keys.add(key)
            accepted.append(candidate)
            reply = True
    return accepted


def meta_for(game_id, existing=None):
    spec = catalog.CATALOG[game_id]
    meta = {"gameId": game_id}
    for key in ("title", "description", "category", "contentKind", "interaction", "instruction",
                "emoji", "colorToken", "segments"):
        meta[key] = spec[key]
    if existing and "review" in existing:
        meta["review"] = existing["review"]
    return jsonio.canonical_meta(meta)


def write_if_changed(path, obj):
    data = jsonio.dumps(obj)
    if os.path.exists(path) and jsonio.read_bytes(path) == data:
        return False
    jsonio.write(path, obj)
    return True


def generate_file(root, game, segment, target):
    """Returns the number of appended questions."""
    game_id = game.GAME_ID
    path = os.path.join(root, game_id, f"{segment}.json")
    existing = jsonio.read(path)["questions"] if os.path.exists(path) else []
    if len(existing) >= target:
        return 0
    existing_keys = {_normalized_key(q) for q in existing}
    candidates = _run(game, segment, target + len(existing))
    new = [c for c in candidates if _normalized_key(c) not in existing_keys][: target - len(existing)]
    if len(existing) + len(new) < target:
        raise GenerationError(f"{game_id}/{segment}: only {len(existing) + len(new)} distinct questions "
                              f"available, target is {target}")
    seq = ids.next_seq(existing)
    for offset, q in enumerate(new):
        q["id"] = ids.make_id(game_id, segment, seq + offset)
    questions = sorted(existing + new, key=lambda q: (q["difficulty"], ids.parse_id(q["id"])[2]))
    data = {
        "schemaVersion": catalog.SCHEMA_VERSION,
        "gameId": game_id,
        "segment": segment,
        "jenjang": catalog.SEGMENTS[segment],
        "interaction": catalog.CATALOG[game_id]["interaction"],
        "questions": questions,
    }
    jsonio.write(path, jsonio.canonical_file(data))
    return len(new)


def generate_game(root, game_id, segments=None, target=None):
    game = REGISTRY[game_id]
    meta_path = os.path.join(root, game_id, "meta.json")
    existing_meta = jsonio.read(meta_path) if os.path.exists(meta_path) else None
    write_if_changed(meta_path, meta_for(game_id, existing_meta))
    results = {}
    for segment in segments or list(game.TARGETS):
        if segment not in game.TARGETS:
            raise GenerationError(f"{game_id} has no generator for segment {segment}")
        results[segment] = generate_file(root, game, segment, target or game.TARGETS[segment])
    return results


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generate or extend procedural question files (append-only).")
    parser.add_argument("games", nargs="*", help=f"game ids (default: all): {', '.join(sorted(REGISTRY))}")
    parser.add_argument("--segment", action="append", help="limit to a segment (repeatable)")
    parser.add_argument("--target", type=int, help="minimum question count per file (default: per-game target)")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="dataset root (default: aksara-go/)")
    args = parser.parse_args(argv)
    unknown = [g for g in args.games if g not in REGISTRY]
    if unknown:
        parser.error(f"no generator for {unknown}")
    try:
        for game_id in args.games or sorted(REGISTRY):
            results = generate_game(args.root, game_id, args.segment, args.target)
            print(f"{game_id}: " + ", ".join(f"{s} +{n}" for s, n in results.items()))
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
