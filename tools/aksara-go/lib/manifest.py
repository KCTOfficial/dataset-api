"""Build `aksara-go/manifest.json` from the files on disk (never edited by hand)."""

import os
import re

from lib import catalog, jsonio

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_VERSION = "1.0.0"


def game_folders(root):
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))


def segment_files(game_dir):
    """Segment ids that have a `<segment>.json` file, in canonical segment order."""
    present = {name[:-5] for name in os.listdir(game_dir) if name.endswith(".json") and name != "meta.json"}
    return [s for s in catalog.SEGMENT_ORDER if s in present]


def file_status(meta, segment, digest, valid):
    """Procedural: reviewed when valid. Curated: reviewed only if the reviewed checksum still matches."""
    if meta.get("contentKind") == "procedural":
        return "reviewed" if valid else "draft"
    review = (meta.get("review") or {}).get(segment)
    return "reviewed" if valid and isinstance(review, dict) and review.get("sha256") == digest else "draft"


def build(root, invalid_paths=frozenset(), version=None):
    """Return the manifest object. `invalid_paths` are relative file paths that failed validation."""
    games = []
    for game_id in game_folders(root):
        game_dir = os.path.join(root, game_id)
        meta_path = os.path.join(game_dir, "meta.json")
        try:
            meta_raw = jsonio.read_bytes(meta_path)
            meta = jsonio.loads(meta_raw)
        except (OSError, ValueError):
            meta_raw, meta = b"", {}
        files = []
        for segment in segment_files(game_dir):
            rel = f"{game_id}/{segment}.json"
            raw = jsonio.read_bytes(os.path.join(root, rel))
            try:
                count = len(jsonio.loads(raw).get("questions", []))
            except (ValueError, AttributeError):
                count = 0
            digest = jsonio.sha256(raw)
            files.append({
                "path": rel,
                "gameId": game_id,
                "segment": segment,
                "jenjang": catalog.SEGMENTS[segment],
                "questionCount": count,
                "sha256": digest,
                "status": file_status(meta, segment, digest, rel not in invalid_paths),
            })
        games.append({
            "gameId": game_id,
            "meta": f"{game_id}/meta.json",
            "metaSha256": jsonio.sha256(meta_raw),
            "files": files,
        })
    return {
        "schemaVersion": catalog.SCHEMA_VERSION,
        "datasetVersion": version or DEFAULT_VERSION,
        "games": games,
    }


def existing_version(root):
    try:
        version = jsonio.read(os.path.join(root, "manifest.json")).get("datasetVersion")
    except (OSError, ValueError, AttributeError):
        return None
    return version if isinstance(version, str) and SEMVER.match(version) else None
