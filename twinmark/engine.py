"""逐条判定与批量流程（README 第三节）。"""

from .caseio import iter_cases
from .core import compare, normalize, screen
from .jsonio import dump_line, dumps

__all__ = ["evaluate_case", "run_evaluate", "run_report", "STATS_KEYS"]

STATS_KEYS = (
    "total",
    "normalize",
    "screen",
    "compare",
    "reject",
    "allow",
    "equivalent",
    "confusable",
    "different",
    "pairs",
    "flagged",
)


def evaluate_case(case, index):
    """对一条用例给出结果记录（带 id、kind，字段见 README 第三节）。"""
    kind = case["kind"]
    if kind == "normalize":
        return {"id": case["id"], "kind": kind, "normalized": normalize(case["text"])}
    if kind == "screen":
        result = screen(case["name"], index)
    else:
        result = compare(case["left"], case["right"], index)
    result["id"] = case["id"]
    return result


def run_evaluate(case_paths, index, write):
    """逐条判定并按序写结果行。"""
    for _path, _lineno, case in iter_cases(case_paths):
        write(dump_line(evaluate_case(case, index)))


def run_report(case_paths, index, write):
    """在结果上加统计与原串，输出报告文档。"""
    items = []
    stats = {key: 0 for key in STATS_KEYS}
    for _path, _lineno, case in iter_cases(case_paths):
        result = evaluate_case(case, index)
        kind = case["kind"]
        pairs = result.get("pairs") or []
        stats["total"] += 1
        stats[kind] += 1
        stats["pairs"] += len(pairs)
        if kind == "normalize":
            result["input"] = case["text"]
        elif kind == "screen":
            result["name"] = case["name"]
            stats[result["decision"]] += 1
            if result["decision"] == "reject" and pairs:
                stats["flagged"] += 1
        else:
            result["left"] = case["left"]
            result["right"] = case["right"]
            if result["equivalent"]:
                stats["equivalent"] += 1
                if not result["identical"]:
                    stats["confusable"] += 1
                if pairs:
                    stats["flagged"] += 1
            else:
                stats["different"] += 1
        items.append(result)
    write(dumps({"items": items, "stats": stats}, indent=2) + "\n")
