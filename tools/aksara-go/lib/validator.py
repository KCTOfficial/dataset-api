"""Whole-dataset validation: layout, formatting, envelope, content rules, ids, catalog, manifest.

Dataset files are treated strictly as data: nothing read from them is executed.
"""

import datetime
import json
import os
import re

from lib import catalog, games, jsonio, manifest, rules

ROOT_FILES = {"manifest.json", "README.md"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REVIEW_KEYS = {"sha256", "date", "role"}


class Report:
    def __init__(self):
        self.violations = []  # (path, question_id or None, message)
        self.counts = {}      # gameId -> {segment: count}

    def add(self, path, qid, message):
        self.violations.append((path, qid, message))

    @property
    def ok(self):
        return not self.violations

    def lines(self):
        return [f"{path}{'#' + qid if qid else ''}: {message}" for path, qid, message in self.violations]


def _format_errors(raw, obj, canonical):
    errors = []
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("file starts with a UTF-8 BOM")
    if b"\r" in raw:
        errors.append("file must use LF line endings, not CRLF")
    if not errors and raw != jsonio.dumps(canonical(obj)):
        errors.append("file is not canonically formatted (2-space indent, fixed key order, trailing newline)")
    return errors


def _load(path, rel, report, canonical):
    try:
        raw = jsonio.read_bytes(path)
        obj = jsonio.loads(raw)
    except (OSError, ValueError) as exc:
        report.add(rel, None, f"cannot read JSON: {exc}")
        return None
    for message in _format_errors(raw, obj, canonical):
        report.add(rel, None, message)
    return obj


def _check_meta(meta, game_id, files_present, report, rel, check_catalog):
    if not isinstance(meta, dict):
        report.add(rel, None, "meta.json must be a JSON object")
        return {}
    extra = set(meta) - set(jsonio.META_KEYS)
    if extra:
        report.add(rel, None, f"unknown meta keys {sorted(extra)}")
    if meta.get("gameId") != game_id:
        report.add(rel, None, f"gameId {meta.get('gameId')!r} does not match folder {game_id!r}")
    for key in ("title", "description", "instruction", "emoji"):
        if not rules.is_text(meta.get(key)):
            report.add(rel, None, f"meta.{key} must be a non-empty string")
    for key, allowed in (("category", catalog.CATEGORIES), ("contentKind", catalog.CONTENT_KINDS),
                         ("interaction", catalog.INTERACTIONS), ("colorToken", catalog.COLOR_TOKENS)):
        if meta.get(key) not in allowed:
            report.add(rel, None, f"meta.{key} {meta.get(key)!r} is not one of {sorted(allowed)}")
    segments = meta.get("segments")
    if not isinstance(segments, list) or any(s not in catalog.SEGMENTS for s in segments):
        report.add(rel, None, "meta.segments must list known segment ids")
    elif segments != [s for s in catalog.SEGMENT_ORDER if s in segments] or len(set(segments)) != len(segments):
        report.add(rel, None, "meta.segments must be unique and in order sd-a, sd-b, sd-c, smp, sma")
    else:
        missing = [s for s in segments if s not in files_present]
        unlisted = [s for s in files_present if s not in segments]
        if missing:
            report.add(rel, None, f"meta.segments lists {missing} but those files are missing")
        if unlisted:
            report.add(rel, None, f"segment files {unlisted} exist but are not listed in meta.segments")
    review = meta.get("review")
    if review is not None:
        if meta.get("contentKind") != "curated":
            report.add(rel, None, "only curated games carry review records")
        elif not isinstance(review, dict):
            report.add(rel, None, "meta.review must be an object keyed by segment")
        else:
            for segment, entry in review.items():
                if segment not in (segments or []):
                    report.add(rel, None, f"review entry for unlisted segment {segment!r}")
                if not isinstance(entry, dict) or set(entry) != REVIEW_KEYS:
                    report.add(rel, None, f"review[{segment}] must have exactly {sorted(REVIEW_KEYS)}")
                    continue
                if not isinstance(entry["sha256"], str) or not HEX64.match(entry["sha256"]):
                    report.add(rel, None, f"review[{segment}].sha256 must be a lowercase hex SHA-256")
                try:
                    datetime.date.fromisoformat(entry["date"])
                    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry["date"]):
                        raise ValueError
                except (TypeError, ValueError):
                    report.add(rel, None, f"review[{segment}].date must be YYYY-MM-DD")
                if not rules.is_text(entry["role"]):
                    report.add(rel, None, f"review[{segment}].role must describe the reviewer's role")
    if check_catalog and game_id in catalog.CATALOG:
        spec = catalog.CATALOG[game_id]
        for key in ("category", "contentKind", "interaction", "segments"):
            if meta.get(key) != spec[key]:
                report.add(rel, None, f"meta.{key} {meta.get(key)!r} differs from the catalog ({spec[key]!r})")
    return meta


def _normalized_key(q):
    text = q.get("prompt", {}).get("text", "") if isinstance(q.get("prompt"), dict) else ""
    return " ".join(str(text).casefold().split()), json.dumps(q.get("answer"), ensure_ascii=False)


def _check_questions(data, game_id, segment, rel, report):
    file_interaction = data.get("interaction")
    questions = data.get("questions") if isinstance(data.get("questions"), list) else []
    check = games.QUESTION_CHECKS.get(game_id)
    seen = {}
    difficulties = []
    for q in questions:
        qid = q.get("id") if isinstance(q, dict) else None
        errors = rules.check_question_envelope(q, game_id, segment, file_interaction)
        if not errors and check:
            errors = check(q, segment)
        for message in errors:
            report.add(rel, qid, message)
        if not isinstance(q, dict):
            continue
        if rules.is_int(q.get("difficulty")):
            difficulties.append(q["difficulty"])
        key = _normalized_key(q)
        if key in seen:
            report.add(rel, qid, f"duplicate of {seen[key]} (same prompt and answer)")
        else:
            seen[key] = qid
    if difficulties:
        if len(set(difficulties)) < catalog.MIN_DISTINCT_DIFFICULTIES:
            report.add(rel, None, f"needs at least {catalog.MIN_DISTINCT_DIFFICULTIES} distinct difficulty "
                                  f"values, has {sorted(set(difficulties))}")
        if difficulties != sorted(difficulties):
            report.add(rel, None, "questions must be listed in non-decreasing difficulty order")
    file_check = games.FILE_CHECKS.get(game_id)
    if file_check:
        for qid, message in file_check(questions, segment):
            report.add(rel, qid, message)
    return questions


def _check_counts(root_counts, metas, report):
    for game_id, per_segment in root_counts.items():
        kind = metas.get(game_id, {}).get("contentKind")
        if kind == "procedural":
            for segment, count in per_segment.items():
                if count < catalog.PROCEDURAL_MIN_PER_FILE:
                    report.add(f"{game_id}/{segment}.json", None,
                               f"has {count} questions; procedural files need at least {catalog.PROCEDURAL_MIN_PER_FILE}")
        elif kind == "curated":
            total = sum(per_segment.values())
            if total < catalog.CURATED_MIN_PER_GAME:
                report.add(f"{game_id}/", None,
                           f"has {total} questions in total; curated games need at least {catalog.CURATED_MIN_PER_GAME}")
            for segment, count in per_segment.items():
                if count < catalog.CURATED_MIN_PER_FILE:
                    report.add(f"{game_id}/{segment}.json", None,
                               f"has {count} questions; curated files need at least {catalog.CURATED_MIN_PER_FILE}")


def _check_manifest(root, invalid_paths, report):
    rel = "manifest.json"
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        report.add(rel, None, "manifest.json is missing (run build_manifest.py)")
        return
    actual = _load(path, rel, report, lambda obj: obj)
    if actual is None:
        return
    version = actual.get("datasetVersion") if isinstance(actual, dict) else None
    if not isinstance(version, str) or not manifest.SEMVER.match(version):
        report.add(rel, None, "datasetVersion must be a semantic version like 1.0.0")
    expected = manifest.build(root, invalid_paths, version=version)
    if actual == expected:
        return
    actual_files = {f.get("path"): f for g in actual.get("games", []) for f in g.get("files", [])
                    if isinstance(f, dict)} if isinstance(actual, dict) else {}
    expected_files = {f["path"]: f for g in expected["games"] for f in g["files"]}
    for p in sorted(set(expected_files) - set(actual_files)):
        report.add(rel, None, f"{p} is not listed in the manifest")
    for p in sorted(set(actual_files) - set(expected_files)):
        report.add(rel, None, f"manifest lists {p}, which does not exist")
    for p in sorted(set(actual_files) & set(expected_files)):
        for key in ("questionCount", "sha256", "status", "segment", "jenjang", "gameId"):
            if actual_files[p].get(key) != expected_files[p][key]:
                label = "SHA-256" if key == "sha256" else key
                report.add(rel, None, f"{p}: {label} in manifest ({actual_files[p].get(key)}) no longer matches "
                                      f"the file ({expected_files[p][key]}); rebuild the manifest")
    if not any(m[0] == rel for m in report.violations):
        report.add(rel, None, "manifest differs from the files on disk; rebuild the manifest")


def validate(root, check_catalog=True, check_manifest=True, check_counts=True):
    report = Report()
    if not os.path.isdir(root):
        report.add(root, None, "dataset root does not exist")
        return report
    for name in sorted(os.listdir(root)):
        if os.path.isfile(os.path.join(root, name)) and name not in ROOT_FILES:
            report.add(name, None, "unexpected file at the dataset root")
    game_ids = manifest.game_folders(root)
    metas = {}
    all_ids = {}
    lengkapi, susun = [], []
    for game_id in game_ids:
        game_dir = os.path.join(root, game_id)
        for name in sorted(os.listdir(game_dir)):
            is_segment = name.endswith(".json") and name[:-5] in catalog.SEGMENTS
            if name != "meta.json" and not is_segment and not name.endswith(".md"):
                report.add(f"{game_id}/{name}", None, "unexpected file in a game folder")
        present = manifest.segment_files(game_dir)
        meta_rel = f"{game_id}/meta.json"
        if not os.path.exists(os.path.join(game_dir, "meta.json")):
            report.add(meta_rel, None, "meta.json is missing")
            meta = {}
        else:
            meta = _load(os.path.join(game_dir, "meta.json"), meta_rel, report, jsonio.canonical_meta)
            meta = _check_meta(meta, game_id, present, report, meta_rel, check_catalog) if meta is not None else {}
        metas[game_id] = meta
        report.counts[game_id] = {}
        for segment in present:
            rel = f"{game_id}/{segment}.json"
            data = _load(os.path.join(root, rel), rel, report, jsonio.canonical_file)
            if data is None:
                continue
            for qid, message in rules.check_file_envelope(data, game_id, segment):
                report.add(rel, qid, message)
            if meta.get("interaction") and data.get("interaction") != meta.get("interaction"):
                report.add(rel, None, f"file interaction {data.get('interaction')!r} differs from meta.json")
            questions = _check_questions(data, game_id, segment, rel, report)
            report.counts[game_id][segment] = len(questions)
            for q in questions:
                if not isinstance(q, dict) or not isinstance(q.get("id"), str):
                    continue
                if q["id"] in all_ids:
                    report.add(rel, q["id"], f"duplicate id (also in {all_ids[q['id']]})")
                else:
                    all_ids[q["id"]] = rel
                if game_id == "lengkapi-kata" and isinstance(q.get("prompt"), dict):
                    lengkapi.append((rel, q))
                elif game_id == "susun-huruf":
                    susun.append((rel, q))
    if check_catalog:
        for game_id in sorted(set(catalog.CATALOG) - set(game_ids)):
            report.add(f"{game_id}/", None, "catalog game is missing from the dataset")
        for game_id in sorted(set(game_ids) - set(catalog.CATALOG)):
            report.add(f"{game_id}/", None, "game folder is not in the catalog")
    if check_counts:
        _check_counts(report.counts, metas, report)
    for path, qid, message in games.ambiguity_errors(lengkapi, susun):
        report.add(path, qid, message)
    if check_manifest:
        invalid = {path for path, _, _ in report.violations}
        _check_manifest(root, invalid, report)
    return report
