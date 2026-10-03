"""归一化、折叠与判定逻辑（README 第二节）。"""

import unicodedata

__all__ = [
    "NormalizeError",
    "normalize",
    "fold",
    "scan_evidence",
    "screen",
    "compare",
    "format_cp",
]

ZERO_WIDTH_RULE = "invisible.zero-width"
MAX_ROUNDS = 4


class NormalizeError(ValueError):
    """归一化四轮不收敛，输入不可用。"""


def _round(text):
    text = text.casefold()
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    text = unicodedata.normalize("NFC", text)
    return text


def normalize(text):
    """四步一轮（大小写、全半角、零宽、组合字符），迭代到不动点，最多 4 轮。"""
    previous = text
    for _ in range(MAX_ROUNDS):
        current = _round(previous)
        if current == previous:
            return current
        previous = current
    raise NormalizeError("normalization did not converge within %d rounds" % MAX_ROUNDS)


def fold(text, index):
    """逐码位查表替换为目标字符，只替换一次、不级联。"""
    parts = []
    for ch in text:
        hit = index.get(ord(ch))
        parts.append(chr(hit[0]) if hit is not None else ch)
    return "".join(parts)


def format_cp(code):
    return "U+%04X" % code


def scan_evidence(text, side, index):
    """逐码位扫原始输入取证：同形命中映射表，Cf 记不可见证据。"""
    pairs = []
    get = index.get
    for pos, ch in enumerate(text):
        code = ord(ch)
        hit = get(code)
        if hit is not None:
            target, rule = hit
            pairs.append(
                {
                    "side": side,
                    "index": pos,
                    "cp": format_cp(code),
                    "char": ch,
                    "target": chr(target),
                    "target_cp": format_cp(target),
                    "rule": rule,
                }
            )
        elif unicodedata.category(ch) == "Cf":
            pairs.append(
                {
                    "side": side,
                    "index": pos,
                    "cp": format_cp(code),
                    "char": ch,
                    "target": None,
                    "target_cp": None,
                    "rule": ZERO_WIDTH_RULE,
                }
            )
    return pairs


def _rules_of(pairs):
    return sorted({pair["rule"] for pair in pairs})


def screen(name, index):
    """注册判定：reject / allow，附归一结果、证据与规则。"""
    normalized = normalize(name)
    pairs = scan_evidence(name, "input", index)
    has_homoglyph = False
    has_invisible = False
    for pair in pairs:
        if pair["target"] is None:
            has_invisible = True
        else:
            has_homoglyph = True
    has_ascii_letter = any("a" <= ch <= "z" for ch in normalized)
    decision = (
        "reject" if (has_invisible or (has_homoglyph and has_ascii_letter)) else "allow"
    )
    return {
        "kind": "screen",
        "normalized": normalized,
        "decision": decision,
        "pairs": pairs,
        "rules": _rules_of(pairs),
    }


def compare(left, right, index):
    """比对判定：equivalent / identical，附归一结果、证据与规则。"""
    normalized_left = normalize(left)
    normalized_right = normalize(right)
    equivalent = fold(normalized_left, index) == fold(normalized_right, index)
    identical = normalized_left == normalized_right
    pairs = scan_evidence(left, "left", index) + scan_evidence(right, "right", index)
    return {
        "kind": "compare",
        "normalized_left": normalized_left,
        "normalized_right": normalized_right,
        "equivalent": equivalent,
        "identical": identical,
        "pairs": pairs,
        "rules": _rules_of(pairs),
    }
