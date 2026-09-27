"""JSON 输出：键按字典序、紧凑分隔符、非 ASCII 不转义、Cc/Cf 写成 \\uXXXX 大写。"""

import json

# Unicode 中类别为 Cf 的码位区间。Cc 由 json.dumps 自行转义，不在此处理，
# 否则会误伤 indent=2 报告里的结构换行。
_ESCAPE_RANGES = (
    (0x00AD, 0x00AD),
    (0x0600, 0x0605),
    (0x061C, 0x061C),
    (0x06DD, 0x06DD),
    (0x070F, 0x070F),
    (0x0890, 0x0891),
    (0x08E2, 0x08E2),
    (0x180E, 0x180E),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x2064),
    (0x2066, 0x206F),
    (0xFEFF, 0xFEFF),
    (0xFFF9, 0xFFFB),
    (0x110BD, 0x110BD),
    (0x110CD, 0x110CD),
    (0x13430, 0x1343F),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0001, 0xE0001),
    (0xE0020, 0xE007F),
)


def _escape(cp):
    if cp <= 0xFFFF:
        return "\\u%04X" % cp
    cp -= 0x10000
    return "\\u%04X\\u%04X" % (0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF))


_TRANSLATE = {cp: _escape(cp) for lo, hi in _ESCAPE_RANGES for cp in range(lo, hi + 1)}


def _escape_invisible(text):
    return text.translate(_TRANSLATE)


def dumps_line(obj):
    """单行 JSONL：紧凑分隔符，键按字典序。"""
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _escape_invisible(text)


def dumps_report(obj):
    """报告：indent=2，键按字典序，末行换行。"""
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    return _escape_invisible(text) + "\n"
