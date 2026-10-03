"""混淆映射表加载与校验（README 2.2 与 4.1）。

索引只存 {可疑码位: (目标码位, 规则 ID)}，等价关系按目标归并，
不展开成两两组合，内存随表条数线性增长。
"""

import re

from .core import normalize

__all__ = ["MapError", "load_maps"]

_CP_RE = re.compile(r"^U\+[0-9A-F]{4,6}$")
_RULE_RE = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*$")
_TARGET_MIN = 0x21
_TARGET_MAX = 0x7E


class MapError(ValueError):
    """映射表输入不可用。"""


def _parse_cp(text, where):
    if not _CP_RE.match(text):
        raise MapError("%s: bad code point %r" % (where, text))
    code = int(text[2:], 16)
    if code > 0x10FFFF:
        raise MapError("%s: code point out of range %r" % (where, text))
    return code


def load_maps(paths):
    """按序合并多份映射表，返回 {可疑码位: (目标码位, 规则 ID)}。"""
    index = {}
    for path in paths:
        try:
            stream = open(path, "r", encoding="utf-8", newline="")
        except OSError as exc:
            raise MapError("cannot open map %s: %s" % (path, exc)) from exc
        with stream:
            for lineno, line in enumerate(stream, 1):
                where = "%s:%d" % (path, lineno)
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                cols = line.split("\t")
                if len(cols) != 4:
                    raise MapError("%s: expected 4 tab-separated columns" % where)
                src = _parse_cp(cols[0], where)
                dst = _parse_cp(cols[1], where)
                rule = cols[2]
                if not _RULE_RE.match(rule):
                    raise MapError("%s: bad rule id %r" % (where, rule))
                if not (_TARGET_MIN <= dst <= _TARGET_MAX):
                    raise MapError("%s: target not printable ASCII" % where)
                src_ch = chr(src)
                if normalize(src_ch) != src_ch:
                    raise MapError("%s: suspicious code point not normalize-stable" % where)
                if normalize(chr(dst)) != chr(dst):
                    raise MapError("%s: target not normalize-stable" % where)
                if src in index:
                    raise MapError("%s: duplicate suspicious code point U+%04X" % (where, src))
                index[src] = (dst, rule)
    return index
