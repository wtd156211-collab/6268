"""混淆映射表：加载、逐行校验、按需查表（不展开等价类）。"""

import re

from .textnorm import normalize

CP_RE = re.compile(r"^U\+[0-9A-F]{4,6}$")
RULE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*(\.[a-z0-9]+(-[a-z0-9]+)*)*$")


class MapError(Exception):
    """映射表输入不可用。"""


class ConfusableMap:
    """索引 {可疑字符: (目标字符, 规则 ID)}，fold 只替换一次、不级联。"""

    __slots__ = ("index", "_translate", "size")

    def __init__(self, index):
        self.index = index
        self._translate = {ord(ch): target for ch, (target, _rule) in index.items()}
        self.size = len(index)

    def fold(self, text):
        return text.translate(self._translate)

    def lookup(self, ch):
        return self.index.get(ch)


def _parse_cp(field, where):
    if not CP_RE.match(field):
        raise MapError(f"{where}: 码位格式不合法: {field!r}")
    value = int(field[2:], 16)
    if value > 0x10FFFF:
        raise MapError(f"{where}: 码位超出范围: {field!r}")
    return value


def _load_file(path, index):
    try:
        fh = open(path, "r", encoding="utf-8", newline="")
    except OSError as exc:
        raise MapError(f"无法读取映射表 {path}: {exc}") from exc
    with fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            where = f"{path}:{lineno}"
            parts = line.split("\t")
            if len(parts) != 4:
                raise MapError(f"{where}: 应为四列 TSV")
            src_field, dst_field, rule, _desc = parts
            src = _parse_cp(src_field, where)
            dst = _parse_cp(dst_field, where)
            if not RULE_RE.match(rule):
                raise MapError(f"{where}: 规则 ID 不合法: {rule!r}")
            if not (0x21 <= dst <= 0x7E):
                raise MapError(f"{where}: 目标不是 ASCII 可打印字符: {dst_field!r}")
            dst_ch = chr(dst)
            if normalize(dst_ch) != dst_ch:
                raise MapError(f"{where}: 目标过 normalize 会变化: {dst_field!r}")
            src_ch = chr(src)
            if normalize(src_ch) != src_ch:
                raise MapError(f"{where}: 可疑码位过 normalize 会变化: {src_field!r}")
            if src_ch in index:
                raise MapError(f"{where}: 可疑码位重复: {src_field!r}")
            index[src_ch] = (dst_ch, rule)


def load_maps(paths):
    """按序合并多份映射表；同一可疑码位出现两次判输入不可用。"""
    index = {}
    for path in paths:
        _load_file(path, index)
    return ConfusableMap(index)
