import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "samples")
CASES_DIR = os.path.join(SAMPLES, "cases")
EXPECTED_DIR = os.path.join(SAMPLES, "expected")
MAPS_DIR = os.path.join(SAMPLES, "maps")
CORE_MAP = os.path.join(MAPS_DIR, "confusables-core.tsv")
LARGE_MAP = os.path.join(MAPS_DIR, "confusables-large.tsv")

CASE_STEMS = [
    "n-01-normalize",
    "s-01-screen",
    "x-01-compare",
    "w-01-web",
    "b-01-batch",
]


def read_jsonl(path):
    with open(path, "r", encoding="utf-8", newline="") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sample_strings():
    """样例里出现过的所有输入串与归一结果。"""
    texts = []
    for stem in CASE_STEMS:
        for case in read_jsonl(os.path.join(CASES_DIR, stem + ".jsonl")):
            for key in ("text", "name", "left", "right"):
                if key in case:
                    texts.append(case[key])
    for stem in CASE_STEMS:
        for result in read_jsonl(os.path.join(EXPECTED_DIR, stem + ".jsonl")):
            for key in ("normalized", "normalized_left", "normalized_right"):
                if key in result:
                    texts.append(result[key])
    return texts
