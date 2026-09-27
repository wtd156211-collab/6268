"""对照 samples/expected 逐字节验收，外加幂等与可重复性。"""

import json
import os
import tempfile
import unittest

from twinmark import iter_cases, load_maps, normalize
from twinmark.cli import main
from twinmark.engine import evaluate_record
from twinmark.jsonio import dumps_line, dumps_report
from twinmark.report import attach_raw, build_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(ROOT, "samples", "maps")
CASES = os.path.join(ROOT, "samples", "cases")
EXPECTED = os.path.join(ROOT, "samples", "expected")

CASE_FILES = [
    "n-01-normalize.jsonl",
    "s-01-screen.jsonl",
    "x-01-compare.jsonl",
    "w-01-web.jsonl",
    "b-01-batch.jsonl",
]


def _load_cmap(name="confusables-large.tsv"):
    return load_maps([os.path.join(MAPS, name)])


class EvaluateMatchesExpectedTest(unittest.TestCase):
    def test_each_case_file_byte_identical(self):
        cmap = _load_cmap()
        for name in CASE_FILES:
            with self.subTest(cases=name):
                produced = []
                for case in iter_cases([os.path.join(CASES, name)]):
                    produced.append(dumps_line(evaluate_record(case, cmap)))
                actual = ("\n".join(produced) + "\n").encode("utf-8")
                with open(os.path.join(EXPECTED, name), "rb") as fh:
                    self.assertEqual(actual, fh.read())

    def test_core_map_gives_same_results(self):
        large = _load_cmap("confusables-large.tsv")
        core = _load_cmap("confusables-core.tsv")
        for name in CASE_FILES:
            for case in iter_cases([os.path.join(CASES, name)]):
                self.assertEqual(
                    dumps_line(evaluate_record(case, core)),
                    dumps_line(evaluate_record(case, large)),
                )

    def test_report_byte_identical(self):
        cmap = _load_cmap()
        items = []
        for case in iter_cases([os.path.join(CASES, "w-01-web.jsonl")]):
            items.append(attach_raw(evaluate_record(case, cmap), case))
        actual = dumps_report(build_report(items)).encode("utf-8")
        with open(os.path.join(EXPECTED, "w-01-web.report.json"), "rb") as fh:
            self.assertEqual(actual, fh.read())


class IdempotenceTest(unittest.TestCase):
    def test_normalize_is_idempotent_on_all_sample_strings(self):
        strings = set()
        for name in CASE_FILES:
            for case in iter_cases([os.path.join(CASES, name)]):
                for field in ("text", "name", "left", "right"):
                    if field in case:
                        strings.add(case[field])
        for text in strings:
            with self.subTest(text=text):
                self.assertEqual(normalize(normalize(text)), normalize(text))

    def test_normalize_fixpoint_roundtrip(self):
        for raw, want in [
            ("PAYPAL-SUPPORT", "paypal-support"),
            ("STRAẞE", "strasse"),
            ("㎒", "mhz"),
            ("ｐａｙｐａｌ", "paypal"),
            ("pay​pal", "paypal"),
            ("café", "café"),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize(raw), want)
                self.assertEqual(normalize(want), want)


class DeterminismTest(unittest.TestCase):
    def test_same_input_same_output_twice(self):
        cmap = _load_cmap()
        path = os.path.join(CASES, "s-01-screen.jsonl")
        first = [dumps_line(evaluate_record(c, cmap)) for c in iter_cases([path])]
        second = [dumps_line(evaluate_record(c, cmap)) for c in iter_cases([path])]
        self.assertEqual(first, second)


class CliTest(unittest.TestCase):
    def test_evaluate_to_file_and_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "var", "results.jsonl")
            rc = main(["evaluate", "--map", os.path.join(MAPS, "confusables-core.tsv"),
                       "--cases", os.path.join(CASES, "s-01-screen.jsonl"), "--out", out])
            self.assertEqual(rc, 0)
            with open(out, "rb") as fh:
                actual = fh.read()
            with open(os.path.join(EXPECTED, "s-01-screen.jsonl"), "rb") as fh:
                self.assertEqual(actual, fh.read())

    def test_report_default_out(self):
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                rc = main(["report", "--map", os.path.join(MAPS, "confusables-core.tsv"),
                           "--cases", os.path.join(CASES, "w-01-web.jsonl")])
                self.assertEqual(rc, 0)
                with open(os.path.join(tmp, "var", "report.json"), "rb") as fh:
                    actual = fh.read()
            finally:
                os.chdir(cwd)
        with open(os.path.join(EXPECTED, "w-01-web.report.json"), "rb") as fh:
            self.assertEqual(actual, fh.read())

    def test_missing_file_exit_1_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.jsonl")
            rc = main(["evaluate", "--map", os.path.join(MAPS, "confusables-core.tsv"),
                       "--cases", os.path.join(tmp, "nope.jsonl"), "--out", out])
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(out))

    def test_bad_cases_exit_1_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.jsonl")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write('{"id":"t-01-00001","kind":"screen","name":"a"}\n')
                fh.write('{"id":"t-01-00001","kind":"screen","name":"b"}\n')
            out = os.path.join(tmp, "out.jsonl")
            rc = main(["evaluate", "--map", os.path.join(MAPS, "confusables-core.tsv"),
                       "--cases", bad, "--out", out])
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(out))

    def test_usage_error_exit_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["evaluate"])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
