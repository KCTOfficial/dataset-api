"""Question id format: `<gameId>.<segment>.<NNNN>`."""

import re

ID_PATTERN = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)\.(sd-a|sd-b|sd-c|smp|sma)\.(\d{4})$")


def make_id(game_id, segment, seq):
    if not 1 <= seq <= 9999:
        raise ValueError(f"sequence {seq} outside 1..9999")
    return f"{game_id}.{segment}.{seq:04d}"


def parse_id(question_id):
    """Return (gameId, segment, seq) or None if the id is malformed."""
    m = ID_PATTERN.match(question_id) if isinstance(question_id, str) else None
    if not m:
        return None
    return m.group(1), m.group(2), int(m.group(3))


def next_seq(questions):
    """Next free sequence number after the highest one already used (ids are never reused)."""
    highest = 0
    for q in questions:
        parsed = parse_id(q.get("id"))
        if parsed:
            highest = max(highest, parsed[2])
    return highest + 1
