import json
import os
import unittest

from tests.helpers import (
    CASE_STEMS,
    CASES_DIR,
    CORE_MAP,
    EXPECTED_DIR,
    LARGE_MAP,
    read_jsonl,
)
from twinmark import load_maps, run_evaluate, run_report


def evaluate_to_text(map_paths, case_paths):
    index = load_maps(map_paths)
    chunks = []
    run_evaluate(case_paths, index, chunks.append)
    return "".join(chunks)


def report_to_text(map_paths, case_paths):
    index = load_maps(map_paths)
    chunks = []
    run_report(case_paths, index, chunks.append)
    return "".join(chunks)


class EvaluateMatchesExpectedTest(unittest.TestCase):
    def test_each_cases_file_byte_identical(self):
        for stem in CASE_STEMS:
            with self.subTest(stem=stem):
                got = evaluate_to_text(
                    [LARGE_MAP], [os.path.join(CASES_DIR, stem + ".jsonl")]
                )
                with open(
                    os.path.join(EXPECTED_DIR, stem + ".jsonl"),
                    "r",
                    encoding="utf-8",
                    newline="",
                ) as stream:
                    want = stream.read()
                self.assertEqual(got, want)

    def test_core_and_large_maps_agree(self):
        for stem in CASE_STEMS:
            with self.subTest(stem=stem):
                case_path = os.path.join(CASES_DIR, stem + ".jsonl")
                self.assertEqual(
                    evaluate_to_text([CORE_MAP], [case_path]),
                    evaluate_to_text([LARGE_MAP], [case_path]),
                )

    def test_deterministic_across_runs(self):
        case_path = os.path.join(CASES_DIR, "b-01-batch.jsonl")
        first = evaluate_to_text([LARGE_MAP], [case_path])
        second = evaluate_to_text([LARGE_MAP], [case_path])
        self.assertEqual(first, second)

    def test_report_byte_identical(self):
        got = report_to_text([LARGE_MAP], [os.path.join(CASES_DIR, "w-01-web.jsonl")])
        with open(
            os.path.join(EXPECTED_DIR, "w-01-web.report.json"),
            "r",
            encoding="utf-8",
            newline="",
        ) as stream:
            want = stream.read()
        self.assertEqual(got, want)


class EvidenceTest(unittest.TestCase):
    """判定必须带依据：reject 都有非空 pairs，证据键齐全。"""

    PAIR_KEYS = {"side", "index", "cp", "char", "target", "target_cp", "rule"}

    def test_reject_always_has_pairs(self):
        for stem in CASE_STEMS:
            for result in read_jsonl(os.path.join(EXPECTED_DIR, stem + ".jsonl")):
                if result.get("decision") == "reject":
                    with self.subTest(id=result["id"]):
                        self.assertTrue(result["pairs"])

    def test_pair_shape(self):
        for stem in CASE_STEMS:
            for result in read_jsonl(os.path.join(EXPECTED_DIR, stem + ".jsonl")):
                for pair in result.get("pairs", []):
                    with self.subTest(id=result["id"]):
                        self.assertEqual(set(pair), self.PAIR_KEYS)
                        if pair["rule"] == "invisible.zero-width":
                            self.assertIsNone(pair["target"])
                            self.assertIsNone(pair["target_cp"])
                        else:
                            self.assertIsNotNone(pair["target"])
                            self.assertIsNotNone(pair["target_cp"])

    def test_pairs_sorted_left_then_right_by_index(self):
        order = {"input": 0, "left": 0, "right": 1}
        for stem in CASE_STEMS:
            for result in read_jsonl(os.path.join(EXPECTED_DIR, stem + ".jsonl")):
                pairs = result.get("pairs", [])
                keys = [(order[p["side"]], p["index"]) for p in pairs]
                with self.subTest(id=result["id"]):
                    self.assertEqual(keys, sorted(keys))


class ReportStatsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(EXPECTED_DIR, "w-01-web.report.json"),
            "r",
            encoding="utf-8",
        ) as stream:
            cls.report = json.load(stream)

    def test_stats_keys(self):
        self.assertEqual(
            set(self.report["stats"]),
            {
                "total", "normalize", "screen", "compare", "reject", "allow",
                "equivalent", "confusable", "different", "pairs", "flagged",
            },
        )

    def test_stats_consistent_with_items(self):
        items = self.report["items"]
        stats = self.report["stats"]
        self.assertEqual(stats["total"], len(items))
        for kind in ("normalize", "screen", "compare"):
            self.assertEqual(stats[kind], sum(1 for i in items if i["kind"] == kind))
        self.assertEqual(
            stats["reject"],
            sum(1 for i in items if i.get("decision") == "reject"),
        )
        self.assertEqual(
            stats["allow"],
            sum(1 for i in items if i.get("decision") == "allow"),
        )
        self.assertEqual(
            stats["equivalent"],
            sum(1 for i in items if i.get("equivalent") is True),
        )
        self.assertEqual(
            stats["different"],
            sum(1 for i in items if i.get("equivalent") is False),
        )
        self.assertEqual(
            stats["confusable"],
            sum(
                1
                for i in items
                if i.get("equivalent") is True and i.get("identical") is False
            ),
        )
        self.assertEqual(
            stats["pairs"], sum(len(i.get("pairs", [])) for i in items)
        )
        flagged = [
            i
            for i in items
            if i.get("pairs")
            and (
                (i["kind"] == "screen" and i["decision"] == "reject")
                or (i["kind"] == "compare" and i["equivalent"])
            )
        ]
        self.assertEqual(stats["flagged"], len(flagged))


if __name__ == "__main__":
    unittest.main()
