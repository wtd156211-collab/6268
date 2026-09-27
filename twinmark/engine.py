"""判定引擎：注册判定（screen）、比对判定（compare）、归一化记录。"""

import unicodedata

from .textnorm import normalize

INVISIBLE_RULE = "invisible.zero-width"


def _cp(ch):
    return f"U+{ord(ch):04X}"


def scan_evidence(text, side, cmap):
    """逐码位扫原始输入取证：同形命中映射表，Cf 不可见字符目标为空。"""
    pairs = []
    for index, ch in enumerate(text):
        hit = cmap.lookup(ch)
        if hit is not None:
            target, rule = hit
            pairs.append({
                "side": side,
                "index": index,
                "cp": _cp(ch),
                "char": ch,
                "target": target,
                "target_cp": _cp(target),
                "rule": rule,
            })
        elif unicodedata.category(ch) == "Cf":
            pairs.append({
                "side": side,
                "index": index,
                "cp": _cp(ch),
                "char": ch,
                "target": None,
                "target_cp": None,
                "rule": INVISIBLE_RULE,
            })
    return pairs


def _rules(pairs):
    return sorted({pair["rule"] for pair in pairs})


def screen(name, cmap):
    """注册判定：reject 当且仅当有同形证据且归一化结果含 ASCII 字母，或有不可见证据。"""
    normalized = normalize(name)
    pairs = scan_evidence(name, "input", cmap)
    has_homoglyph = any(pair["rule"] != INVISIBLE_RULE for pair in pairs)
    has_invisible = any(pair["rule"] == INVISIBLE_RULE for pair in pairs)
    has_ascii = any("a" <= ch <= "z" for ch in normalized)
    decision = "reject" if (has_invisible or (has_homoglyph and has_ascii)) else "allow"
    return {
        "normalized": normalized,
        "decision": decision,
        "pairs": pairs,
        "rules": _rules(pairs),
    }


def compare(left, right, cmap):
    """比对判定：equivalent 看 fold 后是否一致，identical 看归一化结果是否逐码位相同。"""
    norm_left = normalize(left)
    norm_right = normalize(right)
    pairs = scan_evidence(left, "left", cmap) + scan_evidence(right, "right", cmap)
    return {
        "normalized_left": norm_left,
        "normalized_right": norm_right,
        "equivalent": cmap.fold(norm_left) == cmap.fold(norm_right),
        "identical": norm_left == norm_right,
        "pairs": pairs,
        "rules": _rules(pairs),
    }


def evaluate_record(case, cmap):
    """把一条用例变成一行结果记录。"""
    kind = case["kind"]
    record = {"id": case["id"], "kind": kind}
    if kind == "normalize":
        record["normalized"] = normalize(case["text"])
    elif kind == "screen":
        record.update(screen(case["name"], cmap))
    elif kind == "compare":
        record.update(compare(case["left"], case["right"], cmap))
    else:
        raise ValueError(f"未知 kind: {kind!r}")
    return record
