"""Number-sequence rules for deret-angka. Each rule regenerates its terms exactly."""

RULE_PARAMS = {
    "arithmetic": {"start", "step"},
    "geometric": {"start", "ratio"},
    "square": {"start"},
    "cube": {"start"},
    "fibonacci": {"first", "second"},
    "alternating": {"start", "steps"},
    "second-difference": {"start", "step", "increment"},
}


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def rule_error(rule):
    """Return a message if `rule` is malformed, else None."""
    if not isinstance(rule, dict) or rule.get("type") not in RULE_PARAMS:
        return f"unknown sequence rule {rule!r}"
    expected = RULE_PARAMS[rule["type"]]
    if set(rule) - {"type"} != expected:
        return f"rule '{rule['type']}' needs exactly {sorted(expected)}"
    for key in expected:
        value = rule[key]
        if key == "steps":
            if not (isinstance(value, list) and len(value) == 2 and all(_is_int(s) for s in value)):
                return "alternating 'steps' must be two integers"
        elif not _is_int(value):
            return f"rule parameter '{key}' must be an integer"
    if rule["type"] == "geometric" and rule["ratio"] in (0, 1):
        return "geometric ratio must not be 0 or 1"
    if rule["type"] == "arithmetic" and rule["step"] == 0:
        return "arithmetic step must not be 0"
    return None


def terms(rule, count):
    error = rule_error(rule)
    if error:
        raise ValueError(error)
    kind = rule["type"]
    if kind == "arithmetic":
        return [rule["start"] + i * rule["step"] for i in range(count)]
    if kind == "geometric":
        return [rule["start"] * rule["ratio"] ** i for i in range(count)]
    if kind == "square":
        return [(rule["start"] + i) ** 2 for i in range(count)]
    if kind == "cube":
        return [(rule["start"] + i) ** 3 for i in range(count)]
    if kind == "fibonacci":
        out = [rule["first"], rule["second"]]
        while len(out) < count:
            out.append(out[-1] + out[-2])
        return out[:count]
    if kind == "alternating":
        out = [rule["start"]]
        while len(out) < count:
            out.append(out[-1] + rule["steps"][(len(out) - 1) % 2])
        return out
    # second-difference: differences step, step+inc, step+2inc, ...
    out = [rule["start"]]
    diff = rule["step"]
    while len(out) < count:
        out.append(out[-1] + diff)
        diff += rule["increment"]
    return out
