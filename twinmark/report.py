"""报告：结果行加原始串与统计。"""

_STAT_KEYS = (
    "total", "normalize", "screen", "compare", "reject", "allow",
    "equivalent", "confusable", "different", "pairs", "flagged",
)


def attach_raw(record, case):
    """结果行带上原始串：normalize 用 input，screen 用 name，compare 用 left/right。"""
    item = dict(record)
    kind = case["kind"]
    if kind == "normalize":
        item["input"] = case["text"]
    elif kind == "screen":
        item["name"] = case["name"]
    elif kind == "compare":
        item["left"] = case["left"]
        item["right"] = case["right"]
    return item


def is_flagged(item):
    """有证据且可疑：screen 判 reject 或 compare 判 equivalent。"""
    if not item.get("pairs"):
        return False
    if item["kind"] == "screen":
        return item["decision"] == "reject"
    if item["kind"] == "compare":
        return item["equivalent"]
    return False


def build_report(items):
    stats = {key: 0 for key in _STAT_KEYS}
    for item in items:
        stats["total"] += 1
        kind = item["kind"]
        stats[kind] += 1
        if kind == "screen":
            stats[item["decision"]] += 1
        elif kind == "compare":
            if item["equivalent"]:
                stats["equivalent"] += 1
                if not item["identical"]:
                    stats["confusable"] += 1
            else:
                stats["different"] += 1
        stats["pairs"] += len(item.get("pairs", ()))
        if is_flagged(item):
            stats["flagged"] += 1
    return {"items": items, "stats": stats}
