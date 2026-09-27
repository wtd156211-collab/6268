"""用例读取与校验：id 唯一、字段齐全、无 Cc。"""

import json
import re
import unicodedata

ID_RE = re.compile(r"^[a-z0-9]+-[0-9]{2}-[0-9]{5}$")

_KIND_FIELDS = {
    "normalize": ("text",),
    "screen": ("name",),
    "compare": ("left", "right"),
}


class CaseError(Exception):
    """用例输入不可用。"""


def _check_no_cc(value, where):
    for ch in value:
        if unicodedata.category(ch) == "Cc":
            raise CaseError(f"{where}: 含 Cc 控制字符 U+{ord(ch):04X}")


def validate_case(obj, where, seen_ids):
    if not isinstance(obj, dict):
        raise CaseError(f"{where}: 用例不是 JSON 对象")
    case_id = obj.get("id")
    if not isinstance(case_id, str) or not ID_RE.match(case_id):
        raise CaseError(f"{where}: id 缺失或格式不合法")
    if case_id in seen_ids:
        raise CaseError(f"{where}: id 重复: {case_id}")
    seen_ids.add(case_id)
    kind = obj.get("kind")
    if kind not in _KIND_FIELDS:
        raise CaseError(f"{where}: kind 缺失或不合法: {kind!r}")
    for field in _KIND_FIELDS[kind]:
        value = obj.get(field)
        if not isinstance(value, str):
            raise CaseError(f"{where}: 字段缺失或不是字符串: {field}")
        _check_no_cc(value, f"{where} 字段 {field}")
    return obj


def iter_cases(paths):
    """按序逐行产出校验过的用例；id 全局唯一。"""
    seen_ids = set()
    for path in paths:
        try:
            fh = open(path, "r", encoding="utf-8", newline="")
        except OSError as exc:
            raise CaseError(f"无法读取用例文件 {path}: {exc}") from exc
        with fh:
            for lineno, line in enumerate(fh, 1):
                line = line.rstrip("\n")
                if not line:
                    continue
                where = f"{path}:{lineno}"
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CaseError(f"{where}: JSON 不合法: {exc}") from exc
                yield validate_case(obj, where, seen_ids)
