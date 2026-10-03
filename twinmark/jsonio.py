"""JSON 序列化：键按字典序、非 ASCII 不转义、Cc/Cf 写成 \\uXXXX（大写）。"""

import unicodedata

__all__ = ["dumps", "dump_line"]


def _escape(text):
    parts = []
    for ch in text:
        if ch == '"':
            parts.append('\\"')
        elif ch == "\\":
            parts.append("\\\\")
        elif unicodedata.category(ch) in ("Cc", "Cf"):
            code = ord(ch)
            if code <= 0xFFFF:
                parts.append("\\u%04X" % code)
            else:
                code -= 0x10000
                parts.append(
                    "\\u%04X\\u%04X" % (0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF))
                )
        else:
            parts.append(ch)
    return "".join(parts)


def _dump_compact(obj, out):
    if obj is None:
        out.append("null")
    elif obj is True:
        out.append("true")
    elif obj is False:
        out.append("false")
    elif isinstance(obj, str):
        out.append('"')
        out.append(_escape(obj))
        out.append('"')
    elif isinstance(obj, (int, float)):
        out.append(repr(obj))
    elif isinstance(obj, dict):
        out.append("{")
        for pos, key in enumerate(sorted(obj)):
            if pos:
                out.append(",")
            out.append('"')
            out.append(_escape(key))
            out.append('":')
            _dump_compact(obj[key], out)
        out.append("}")
    elif isinstance(obj, (list, tuple)):
        out.append("[")
        for pos, item in enumerate(obj):
            if pos:
                out.append(",")
            _dump_compact(item, out)
        out.append("]")
    else:
        raise TypeError("unsupported type: %r" % type(obj))


def _dump_pretty(obj, out, level):
    pad = "  " * level
    inner = "  " * (level + 1)
    if isinstance(obj, dict):
        if not obj:
            out.append("{}")
            return
        out.append("{\n")
        keys = sorted(obj)
        for pos, key in enumerate(keys):
            out.append(inner)
            out.append('"')
            out.append(_escape(key))
            out.append('": ')
            _dump_pretty(obj[key], out, level + 1)
            if pos < len(keys) - 1:
                out.append(",")
            out.append("\n")
        out.append(pad)
        out.append("}")
    elif isinstance(obj, (list, tuple)):
        if not obj:
            out.append("[]")
            return
        out.append("[\n")
        for pos, item in enumerate(obj):
            out.append(inner)
            _dump_pretty(item, out, level + 1)
            if pos < len(obj) - 1:
                out.append(",")
            out.append("\n")
        out.append(pad)
        out.append("]")
    else:
        _dump_compact(obj, out)


def dumps(obj, indent=None):
    """序列化为 README 第四节规定的 JSON 文本（不含末尾换行）。"""
    out = []
    if indent is None:
        _dump_compact(obj, out)
    else:
        if indent != 2:
            raise ValueError("only indent=2 is supported")
        _dump_pretty(obj, out, 0)
    return "".join(out)


def dump_line(obj):
    """单行 JSONL 序列化，带末尾换行。"""
    return dumps(obj) + "\n"
