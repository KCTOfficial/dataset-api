"""Envelope and per-interaction rules (specs/question-dataset)."""

import math

from lib import catalog, ids, jsonio

ALLOWED_QUESTION_KEYS = set(jsonio.QUESTION_KEYS)
ALLOWED_PROMPT_KEYS = set(jsonio.PROMPT_KEYS)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def is_text(v):
    return isinstance(v, str) and v.strip() != ""


def effective_interaction(question, file_interaction):
    return question.get("interaction", file_interaction)


def check_file_envelope(data, game_id, segment):
    """File-level envelope errors as (question_id_or_None, message)."""
    errors = []
    if not isinstance(data, dict):
        return [(None, "file must be a JSON object")]
    if data.get("schemaVersion") != catalog.SCHEMA_VERSION:
        errors.append((None, f"schemaVersion must be {catalog.SCHEMA_VERSION}"))
    if data.get("gameId") != game_id:
        errors.append((None, f"gameId {data.get('gameId')!r} does not match folder {game_id!r}"))
    if data.get("segment") != segment:
        errors.append((None, f"segment {data.get('segment')!r} does not match file name {segment!r}"))
    expected_jenjang = catalog.SEGMENTS.get(segment)
    if data.get("jenjang") != expected_jenjang:
        errors.append((None, f"jenjang {data.get('jenjang')!r} inconsistent with segment {segment!r} "
                             f"(expected {expected_jenjang!r})"))
    if data.get("interaction") not in catalog.INTERACTIONS:
        errors.append((None, f"unknown interaction {data.get('interaction')!r}"))
    extra = set(data) - set(jsonio.FILE_KEYS)
    if extra:
        errors.append((None, f"unknown file keys {sorted(extra)}"))
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append((None, "questions must be a non-empty array"))
    return errors


def check_question_envelope(q, game_id, segment, file_interaction):
    """Envelope errors for one question (messages only)."""
    if not isinstance(q, dict):
        return ["question must be a JSON object"]
    errors = []
    extra = set(q) - ALLOWED_QUESTION_KEYS
    if extra:
        errors.append(f"unknown question keys {sorted(extra)}")
    parsed = ids.parse_id(q.get("id"))
    if parsed is None:
        errors.append(f"malformed id {q.get('id')!r} (expected <gameId>.<segment>.<NNNN>)")
    elif parsed[:2] != (game_id, segment):
        errors.append(f"id prefix does not match file {game_id}/{segment}.json")
    difficulty = q.get("difficulty")
    if not is_int(difficulty) or not 1 <= difficulty <= 5:
        errors.append(f"difficulty must be an integer 1-5, got {difficulty!r}")
    prompt = q.get("prompt")
    if not isinstance(prompt, dict) or not is_text(prompt.get("text")):
        errors.append("prompt must be an object with a non-empty 'text'")
    elif set(prompt) - ALLOWED_PROMPT_KEYS:
        errors.append(f"unknown prompt keys {sorted(set(prompt) - ALLOWED_PROMPT_KEYS)}")
    if "answer" not in q:
        errors.append("missing answer")
    elif not (is_int(q["answer"]) or is_text(q["answer"])):
        errors.append("answer must be a non-empty string or an integer")
    if "interaction" in q and q["interaction"] not in catalog.INTERACTIONS:
        errors.append(f"unknown interaction override {q['interaction']!r}")
    if "payload" in q and not isinstance(q["payload"], dict):
        errors.append("payload must be an object")
    if "explanation" in q and not is_text(q["explanation"]):
        errors.append("explanation must be a non-empty string")
    if not errors:
        interaction = effective_interaction(q, file_interaction)
        if interaction in catalog.INTERACTIONS:
            errors += check_interaction(q, interaction)
    return errors


def _distinct_options(options, size, kind):
    if not isinstance(options, list) or not (size[0] <= len(options) <= size[1]):
        n = size[0] if size[0] == size[1] else f"{size[0]}-{size[1]}"
        return f"payload.options must hold {n} values"
    if not all(kind(o) for o in options):
        return "payload.options has a value of the wrong type"
    if len(set(map(repr, options))) != len(options):
        return "payload.options values must be distinct"
    return None


def check_interaction(q, interaction):
    answer = q["answer"]
    prompt = q["prompt"]
    payload = q.get("payload", {})
    errors = []
    if interaction == "NUMPAD":
        if not is_int(answer):
            errors.append("NUMPAD answer must be an integer")
        elif "options" in payload:
            err = _distinct_options(payload["options"], (4, 4), is_int)
            if err:
                errors.append(err)
            elif answer not in payload["options"]:
                errors.append("payload.options must include the answer")
    elif interaction == "TILE_BANK":
        if not is_text(answer):
            errors.append("TILE_BANK answer must be a non-empty string")
            return errors
        distractors = payload.get("distractors")
        if not isinstance(distractors, list) or not all(is_text(d) for d in distractors):
            errors.append("TILE_BANK needs payload.distractors as an array of non-empty strings")
        elif answer in (" ".join(distractors), "".join(distractors)):
            errors.append("payload.distractors must not by themselves spell the answer")
        letters = prompt.get("letters")
        if letters is not None:
            if not (isinstance(letters, list) and all(isinstance(c, str) and len(c) == 1 for c in letters)):
                errors.append("prompt.letters must be an array of single characters")
            elif sorted(letters) != sorted(answer):
                errors.append("prompt.letters must be a permutation of the answer's letters")
            elif "".join(letters) == answer:
                errors.append("prompt.letters must differ from the answer")
    elif interaction == "FILL_GAP":
        text = prompt["text"]
        if not is_text(answer) or "_" in answer:
            errors.append("FILL_GAP answer must be a word without '_'")
        elif len(text) != len(answer):
            errors.append("FILL_GAP prompt.text must have the same length as the answer")
        else:
            gaps = text.count("_")
            mismatch = [i for i, (m, a) in enumerate(zip(text, answer)) if m != "_" and m != a]
            if mismatch:
                errors.append(f"FILL_GAP visible letter at position {mismatch[0] + 1} does not match the answer")
            if gaps < 1 or gaps > math.ceil(len(answer) / 2):
                errors.append(f"FILL_GAP must hide 1-{math.ceil(len(answer) / 2)} letters, hides {gaps}")
    elif interaction == "MULTI_CHOICE":
        err = _distinct_options(payload.get("options"), (2, 4), lambda o: is_int(o) or is_text(o))
        if err:
            errors.append(err)
        elif answer not in payload["options"]:
            errors.append("answer must equal exactly one of payload.options")
    elif interaction == "MATCH_PAIRS":
        if not is_text(answer):
            errors.append("MATCH_PAIRS answer must be a non-empty string")
        if not is_text(payload.get("relation")):
            errors.append("MATCH_PAIRS needs payload.relation")
        err = _distinct_options(payload.get("options"), (4, 4), is_text)
        if err:
            errors.append(err)
        elif answer not in payload["options"]:
            errors.append("payload.options must include the answer")
        if answer == prompt["text"]:
            errors.append("MATCH_PAIRS answer must differ from the prompt word")
    elif interaction == "COMPARE":
        if not (is_text(prompt.get("left")) and is_text(prompt.get("right"))):
            errors.append("COMPARE needs non-empty prompt.left and prompt.right")
        if answer not in ("<", ">", "="):
            errors.append("COMPARE answer must be one of '<', '>', '='")
    return errors
