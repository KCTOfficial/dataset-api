"""Game-specific content rules and answer recomputation (specs/question-bank-content).

`QUESTION_CHECKS[gameId](question, segment)` returns error messages for one
question; `FILE_CHECKS[gameId](questions, segment)` returns (id, message)
pairs for rules that span a whole file.
"""

import re
from fractions import Fraction

from lib import equation, expr, javanese, roman, sequence, terbilang
from lib.rules import is_int, is_text

NUMBER_LIMITS = {"sd-a": 100, "sd-b": 10_000, "sd-c": 1_000_000, "smp": 999_999_999_999,
                 "sma": 999_999_999_999_999}
ROMAN_LIMITS = {"sd-b": 50, "sd-c": 1000, "smp": 3999}
WORD_PATTERN = re.compile(r"^[A-Z]+$")


def _is_sd(segment):
    return segment.startswith("sd-")


def _evaluate(text, **kwargs):
    """(value, intermediates, info) or raises ExprError."""
    node = expr.parse(text, allow_vars=kwargs.pop("allow_vars", False))
    values = []
    value = expr.evaluate(node, intermediates=values, **kwargs)
    return value, values, expr.info(node)


# --- numerasi -----------------------------------------------------------------------------

def check_hitung_cepat(q, segment):
    text = q["prompt"]["text"]
    errors = expr.display_errors(text)
    try:
        value, values, info = _evaluate(text, exact_division=True)
    except expr.ExprError as exc:
        return errors + [f"cannot evaluate prompt: {exc}"]
    if value.denominator != 1:
        return errors + ["recomputed result is not an integer"]
    if q["answer"] != value:
        errors.append(f"answer {q['answer']} does not match recomputed {value}")
    ops = info["ops"]
    literals = [int(v) for v in info["literals"] if v.denominator == 1]
    if _is_sd(segment):
        if any(v < 0 for v in values):
            errors.append("SD questions must not produce negative values")
        if info["power"] or info["root"] or info["log"] or info["percent"] or info["neg"]:
            errors.append("SD questions use only + − × ÷ and parentheses")
    if segment == "sd-a":
        if len(ops) != 1 or ops[0] not in "+-":
            errors.append("sd-a uses exactly one operator, + or −")
        if any(v > 20 for v in literals) or not 0 <= value <= 20:
            errors.append("sd-a operands and result must be within 0-20")
    elif segment == "sd-b":
        if len(ops) != 1:
            errors.append("sd-b uses exactly one operator (mixed operators start in sd-c)")
        elif ops[0] in "+-":
            if any(v > 1000 for v in literals) or value > 1000:
                errors.append("sd-b + and − stay within 0-1000")
        elif ops[0] == "*":
            if any(not 1 <= v <= 10 for v in literals):
                errors.append("sd-b × stays within the 1-10 multiplication table")
        elif len(literals) != 2 or not (1 <= literals[1] <= 10 and 1 <= value <= 10):
            errors.append("sd-b ÷ stays within the 1-10 multiplication table")
    elif segment == "sd-c":
        if not 1 <= len(ops) <= 2:
            errors.append("sd-c uses two or three operands")
        elif len(ops) == 2 and not info["parens"] and not (set(ops) & set("+-") and set(ops) & set("*/")):
            errors.append("sd-c three-operand questions must mix +/− with ×/÷ so precedence matters")
        if info["parens"] and q["difficulty"] < 4:
            errors.append("sd-c uses parentheses only at difficulty 4-5")
        if not 0 <= value <= 10_000:
            errors.append("sd-c results stay within 0-10.000")
    elif segment == "smp":
        if info["log"]:
            errors.append("logarithms start in sma")
    elif segment == "sma":
        if not (info["power"] or info["root"] or info["log"]):
            errors.append("sma questions use exponents, roots or logarithms")
    return errors


def _number_from_display(text):
    parsed = terbilang.parse_display(text)
    if parsed is None:
        return None, None
    return parsed


def check_tebak_angka(q, segment):
    prompt = q["prompt"]
    int_part, frac = _number_from_display(prompt["text"])
    if int_part is None:
        return [f"prompt.text {prompt['text']!r} is not a canonical Indonesian number"]
    errors = []
    if frac is not None:
        if segment != "sma":
            errors.append("decimals appear only in sma")
        if len(frac) > 2 or frac.endswith("0"):
            errors.append("decimals have 1-2 digits without a trailing zero")
        expected = terbilang.words_decimal(int_part, frac)
        value = Fraction(int_part) + Fraction(int(frac), 10 ** len(frac))
    else:
        expected = terbilang.words_int(int_part)
        value = int_part
    if q["answer"] != expected:
        errors.append(f"answer {q['answer']!r} is not the canonical terbilang {expected!r}")
    if not 0 < value <= NUMBER_LIMITS[segment]:
        errors.append(f"number {prompt['text']} is outside the {segment} range 1-{NUMBER_LIMITS[segment]}")
    if "number" in prompt and (frac is not None or prompt["number"] != int_part):
        errors.append("prompt.number must equal the displayed integer")
    for word in q.get("payload", {}).get("distractors", []):
        if word not in terbilang.VOCABULARY:
            errors.append(f"distractor {word!r} is not a number word")
    return errors


def check_kata_ke_angka(q, segment):
    answer = q["answer"]
    errors = []
    if not is_int(answer):
        return ["answer must be an integer"]
    try:
        expected_text = terbilang.words_int(answer)
    except ValueError:
        return [f"answer {answer} cannot be written as terbilang"]
    if q["prompt"]["text"] != expected_text:
        errors.append(f"prompt.text is not the canonical terbilang of {answer} ({expected_text!r})")
    if not 1 <= answer <= NUMBER_LIMITS[segment]:
        errors.append(f"answer {answer} is outside the {segment} range")
    if "options" not in q.get("payload", {}):
        errors.append("kata-ke-angka needs 4 numeric payload.options")
    return errors


def check_deret_angka(q, segment):
    prompt = q["prompt"]
    seq = prompt.get("sequence")
    rule = q.get("payload", {}).get("rule")
    if not (isinstance(seq, list) and 4 <= len(seq) <= 7 and seq.count(None) == 1
            and all(t is None or is_int(t) for t in seq)):
        return ["prompt.sequence must hold 4-7 integers with exactly one null gap"]
    rule_error = sequence.rule_error(rule)
    if rule_error:
        return [f"payload.rule: {rule_error}"]
    terms = sequence.terms(rule, len(seq))
    errors = []
    for i, (shown, expected) in enumerate(zip(seq, terms)):
        if shown is not None and shown != expected:
            errors.append(f"term {i + 1} is {shown} but the rule gives {expected}")
    gap = seq.index(None)
    if q["answer"] != terms[gap]:
        errors.append(f"answer {q['answer']} does not match the rule's term {terms[gap]}")
    expected_text = ", ".join("?" if t is None else terbilang.format_int(t) for t in seq)
    if prompt["text"] != expected_text:
        errors.append(f"prompt.text must be {expected_text!r}")
    if _is_sd(segment):
        allowed = rule["type"] == "arithmetic" or (
            segment != "sd-a" and rule["type"] == "geometric" and rule["ratio"] == 2)
        if not allowed:
            errors.append("SD sequences use arithmetic rules (and doubling from sd-b)")
        if any(t < 0 for t in terms):
            errors.append("SD sequences must not contain negative numbers")
    return errors


def check_banding_angka(q, segment):
    prompt = q["prompt"]
    left, right = prompt["left"], prompt["right"]
    errors = expr.display_errors(left, allow_slash=True) + expr.display_errors(right, allow_slash=True)
    if prompt["text"] != f"{left} ? {right}":
        errors.append(f"prompt.text must be {left + ' ? ' + right!r}")
    try:
        sides = [_evaluate(side) for side in (left, right)]
    except expr.ExprError as exc:
        return errors + [f"cannot evaluate a side: {exc}"]
    a, b = sides[0][0], sides[1][0]
    expected = "<" if a < b else ">" if a > b else "="
    if q["answer"] != expected:
        errors.append(f"answer {q['answer']!r} but the exact comparison gives {expected!r}")
    if _is_sd(segment):
        for value, values, info in sides:
            if any(v < 0 for v in values) or info["power"] or info["root"] or info["log"]:
                errors.append("SD comparisons use non-negative values without powers, roots or logs")
                break
    if segment == "sd-a":
        for (value, _, info), side in zip(sides, (left, right)):
            if len(info["ops"]) > 1 or set(info["ops"]) - set("+-") or value > 100 or value.denominator != 1:
                errors.append(f"sd-a side {side!r} must be a whole number up to 100 or one + / − step")
    return errors


def file_check_banding_angka(questions, segment):
    total = len(questions)
    errors = []
    for symbol in ("<", ">", "="):
        share = sum(1 for q in questions if q.get("answer") == symbol)
        if total and share * 5 < total:
            errors.append((None, f"answer {symbol!r} appears in {share}/{total} questions (needs at least 20%)"))
    return errors


def check_angka_romawi(q, segment):
    answer = q["answer"]
    text = q["prompt"]["text"]
    limit = ROMAN_LIMITS[segment]
    if is_int(answer):
        value = roman.from_roman(text)
        if value is None:
            return [f"prompt.text {text!r} is not a standard Roman numeral"]
        errors = [] if value == answer else [f"answer {answer} but {text} is {value}"]
    else:
        if not text.isdigit() or text != str(int(text)):
            return ["prompt.text must be a whole number for Arabic-to-Roman questions"]
        value = int(text)
        if not 1 <= value <= 3999:
            return [f"{value} cannot be written as a Roman numeral"]
        expected = roman.to_roman(value)
        errors = [] if answer == expected else [f"answer {answer!r} but {value} is {expected}"]
        if q.get("interaction") != "TILE_BANK":
            errors.append("Arabic-to-Roman questions use the TILE_BANK interaction override")
        for letter in q.get("payload", {}).get("distractors", []):
            if letter not in roman.LETTERS:
                errors.append(f"distractor {letter!r} is not a Roman letter")
    if not 1 <= value <= limit:
        errors.append(f"{value} is outside the {segment} range 1-{limit}")
    return errors


def check_cari_x(q, segment):
    text = q["prompt"]["text"]
    sd = _is_sd(segment)
    errors = expr.display_errors(text, allow_x=not sd)
    if sd and ("?" not in text or "x" in text):
        errors.append("SD equations write the unknown as '?'")
    if not sd and ("x" not in text and "ˣ" not in text or "?" in text):
        errors.append("SMP/SMA equations write the unknown as 'x'")
    try:
        solutions = equation.solutions(text)
    except expr.ExprError as exc:
        return errors + [f"cannot parse equation: {exc}"]
    answer = q["answer"]
    if answer not in solutions:
        errors.append(f"answer {answer} does not satisfy the equation")
    elif len(solutions) > 1:
        errors.append(f"equation is not uniquely solvable (also {[s for s in solutions if s != answer][:3]})")
    if sd and is_int(answer) and answer < 0:
        errors.append("SD answers must not be negative")
    return errors


# --- budaya ---------------------------------------------------------------------------------

def check_aksara_nusantara(q, segment):
    text = q["prompt"]["text"]
    options = q.get("payload", {}).get("options", [])
    errors = []
    if javanese.is_script(text):
        latin = javanese.to_latin(text)
        if latin is None:
            return ["prompt.text uses Javanese characters outside the supported open syllables"]
        if q["answer"] != latin:
            errors.append(f"answer {q['answer']!r} but the script reads {latin!r}")
        if not all(isinstance(o, str) and javanese.to_script(o) for o in options):
            errors.append("options for a script prompt must be romanized open syllables")
    else:
        script = javanese.to_script(text)
        if script is None:
            return [f"prompt.text {text!r} is neither Javanese script nor romanized open syllables"]
        latin = text
        if q["answer"] != script:
            errors.append(f"answer is not the Javanese script for {text!r}")
        if not all(isinstance(o, str) and javanese.is_script(o) and javanese.to_latin(o) for o in options):
            errors.append("options for a Latin prompt must be Javanese script")
    syllables = sum(1 for ch in (text if javanese.is_script(text) else javanese.to_script(text) or "")
                    if ch in {s for _, s in javanese.NGLEGENA})
    if segment in ("sd-b", "sd-c") and syllables != 1:
        errors.append(f"{segment} questions use a single syllable")
    if segment == "smp" and syllables < 2:
        errors.append("smp questions use words of two or more syllables")
    return errors


# --- literasi (structural checks; language quality is human-reviewed) ----------------------

def check_lengkapi_kata(q, segment):
    errors = []
    if not isinstance(q["answer"], str) or not WORD_PATTERN.match(q["answer"]):
        errors.append("answer must be an uppercase word A-Z")
    if not is_text(q["prompt"].get("hint")):
        errors.append("lengkapi-kata questions need a prompt.hint")
    return errors


def check_susun_huruf(q, segment):
    errors = []
    answer = q["answer"]
    if not isinstance(answer, str) or not WORD_PATTERN.match(answer):
        errors.append("answer must be an uppercase word A-Z")
    letters = q["prompt"].get("letters")
    if not isinstance(letters, list):
        errors.append("susun-huruf questions need prompt.letters")
    elif q["prompt"]["text"] != " ".join(letters):
        errors.append("prompt.text must be the scrambled letters separated by spaces")
    return errors


def check_kata_baku(q, segment):
    return [] if is_text(q.get("explanation")) else ["kata-baku questions need an explanation naming the baku form"]


def check_sinonim_antonim(q, segment):
    relation = q.get("payload", {}).get("relation")
    return [] if relation in ("sinonim", "antonim") else ["payload.relation must be 'sinonim' or 'antonim'"]


def check_imbuhan(q, segment):
    return [] if "+" in q["prompt"]["text"] else ["prompt.text must show the affix and base word joined by '+'"]


def check_peribahasa(q, segment):
    errors = []
    if "…" not in q["prompt"]["text"]:
        errors.append("prompt.text must mark the missing part with '…'")
    if not is_text(q.get("explanation")):
        errors.append("peribahasa questions need the proverb's meaning as explanation")
    return errors


def check_susun_kalimat(q, segment):
    answer = q["answer"]
    words = answer.split(" ") if isinstance(answer, str) else []
    errors = []
    if len(words) < 3 or any(not w for w in words):
        errors.append("answer must be a sentence of at least 3 words separated by single spaces")
    overlap = set(q.get("payload", {}).get("distractors", [])) & set(words)
    if overlap:
        errors.append(f"distractors must not repeat words of the answer: {sorted(overlap)}")
    return errors


QUESTION_CHECKS = {
    "hitung-cepat": check_hitung_cepat,
    "tebak-angka": check_tebak_angka,
    "kata-ke-angka": check_kata_ke_angka,
    "deret-angka": check_deret_angka,
    "banding-angka": check_banding_angka,
    "angka-romawi": check_angka_romawi,
    "cari-x": check_cari_x,
    "aksara-nusantara": check_aksara_nusantara,
    "lengkapi-kata": check_lengkapi_kata,
    "susun-huruf": check_susun_huruf,
    "kata-baku": check_kata_baku,
    "sinonim-antonim": check_sinonim_antonim,
    "imbuhan": check_imbuhan,
    "peribahasa": check_peribahasa,
    "susun-kalimat": check_susun_kalimat,
}

FILE_CHECKS = {
    "banding-angka": file_check_banding_angka,
}


def ambiguity_errors(lengkapi, susun):
    """Dataset-level ambiguity checks against the combined lengkapi-kata + susun-huruf word list.

    `lengkapi` / `susun` are lists of (path, question). Returns (path, id, message).
    """
    words = {q["answer"] for _, q in lengkapi + susun if isinstance(q.get("answer"), str)}
    by_letters = {}
    for w in words:
        by_letters.setdefault("".join(sorted(w)), set()).add(w)
    errors = []
    for path, q in lengkapi:
        mask, answer = q["prompt"].get("text", ""), q.get("answer")
        if not isinstance(answer, str):
            continue
        pattern = re.compile("^" + "".join("." if c == "_" else re.escape(c) for c in mask) + "$")
        others = sorted(w for w in words if w != answer and pattern.match(w))
        if others:
            errors.append((path, q.get("id"), f"ambiguous: {mask} also fits {', '.join(others[:3])}"))
    for path, q in susun:
        answer = q.get("answer")
        if not isinstance(answer, str):
            continue
        others = sorted(by_letters.get("".join(sorted(answer)), set()) - {answer})
        if others:
            errors.append((path, q.get("id"), f"ambiguous anagram: letters also spell {', '.join(others[:3])}"))
    return errors
