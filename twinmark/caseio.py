"""用例文件读取与校验（README 第三节与 4.2）。"""

import json
import unicodedata

__all__ = ["CaseError", "iter_cases"]

_KIND_FIELDS = {
    "normalize": ("text",),
    "screen": ("name",),
    "compare": ("left", "right"),
}


class CaseError(ValueError):
    """用例输入不可用。"""


def _check_no_cc(text, where):
    for ch in text:
        if unicodedata.category(ch) == "Cc":
            raise CaseError("%s: control character U+%04X not allowed" % (where, ord(ch)))


def parse_case(line, where, seen_ids):
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise CaseError("%s: invalid JSON: %s" % (where, exc)) from exc
    if not isinstance(obj, dict):
        raise CaseError("%s: case must be a JSON object" % where)
    case_id = obj.get("id")
    if not isinstance(case_id, str) or not case_id:
        raise CaseError("%s: missing or invalid id" % where)
    kind = obj.get("kind")
    if kind not in _KIND_FIELDS:
        raise CaseError("%s: missing or unknown kind %r" % (where, kind))
    if case_id in seen_ids:
        raise CaseError("%s: duplicate id %r" % (where, case_id))
    _check_no_cc(case_id, where)
    for field in _KIND_FIELDS[kind]:
        value = obj.get(field)
        if not isinstance(value, str):
            raise CaseError("%s: missing or invalid field %r" % (where, field))
        _check_no_cc(value, where)
    seen_ids.add(case_id)
    return obj


def iter_cases(paths):
    """按序产出 (path, lineno, case)；校验失败抛 CaseError。"""
    seen_ids = set()
    for path in paths:
        try:
            stream = open(path, "r", encoding="utf-8", newline="")
        except OSError as exc:
            raise CaseError("cannot open cases %s: %s" % (path, exc)) from exc
        with stream:
            for lineno, line in enumerate(stream, 1):
                where = "%s:%d" % (path, lineno)
                line = line.rstrip("\n")
                if not line:
                    continue
                yield path, lineno, parse_case(line, where, seen_ids)
