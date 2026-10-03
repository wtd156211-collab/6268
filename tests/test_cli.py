import json
import os
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import CASES_DIR, EXPECTED_DIR, LARGE_MAP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "twinmark", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class CliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)

    def out_path(self, name):
        return os.path.join(self.tmp.name, name)

    def test_evaluate_success_matches_expected(self):
        out = self.out_path("out-%s.jsonl" % self._testMethodName)
        result = run_cli(
            "evaluate", "--map", LARGE_MAP,
            "--cases", os.path.join(CASES_DIR, "x-01-compare.jsonl"),
            "--out", out,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(out, encoding="utf-8", newline="") as stream:
            got = stream.read()
        with open(
            os.path.join(EXPECTED_DIR, "x-01-compare.jsonl"),
            encoding="utf-8", newline="",
        ) as stream:
            want = stream.read()
        self.assertEqual(got, want)

    def test_stdout_when_out_omitted(self):
        result = run_cli(
            "evaluate", "--map", LARGE_MAP,
            "--cases", os.path.join(CASES_DIR, "n-01-normalize.jsonl"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("\n"))
        lines = [line for line in result.stdout.splitlines() if line]
        self.assertEqual(len(lines), 24)

    def test_missing_map_file_exit_1(self):
        out = self.out_path("x-%s.jsonl" % self._testMethodName)
        result = run_cli(
            "evaluate", "--map", os.path.join(self.tmp.name, "nope.tsv"),
            "--cases", os.path.join(CASES_DIR, "x-01-compare.jsonl"),
            "--out", out,
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(os.path.exists(out))

    def test_missing_cases_file_exit_1(self):
        out = self.out_path("x-%s.jsonl" % self._testMethodName)
        result = run_cli(
            "evaluate", "--map", LARGE_MAP,
            "--cases", os.path.join(self.tmp.name, "nope.jsonl"),
            "--out", out,
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(os.path.exists(out))

    def test_duplicate_id_exit_1_and_no_output(self):
        cases = self.out_path("dup.jsonl")
        with open(cases, "w", encoding="utf-8", newline="") as stream:
            stream.write('{"id":"d-01","kind":"normalize","text":"a"}\n')
            stream.write('{"id":"d-01","kind":"normalize","text":"b"}\n')
        out = self.out_path("out-%s.jsonl" % self._testMethodName)
        result = run_cli(
            "evaluate", "--map", LARGE_MAP, "--cases", cases, "--out", out
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(os.path.exists(out))

    def test_missing_field_exit_1(self):
        cases = self.out_path("bad.jsonl")
        with open(cases, "w", encoding="utf-8", newline="") as stream:
            stream.write('{"id":"d-02","kind":"screen"}\n')
        out = self.out_path("out-%s.jsonl" % self._testMethodName)
        result = run_cli(
            "evaluate", "--map", LARGE_MAP, "--cases", cases, "--out", out
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(os.path.exists(out))

    def test_control_character_exit_1(self):
        cases = self.out_path("cc.jsonl")
        with open(cases, "w", encoding="utf-8", newline="") as stream:
            stream.write('{"id":"d-03","kind":"normalize","text":"a\\u0000b"}\n')
        result = run_cli(
            "evaluate", "--map", LARGE_MAP, "--cases", cases,
            "--out", self.out_path("out-cc.jsonl"),
        )
        self.assertEqual(result.returncode, 1)

    def test_usage_error_exit_2(self):
        result = run_cli("evaluate", "--map", LARGE_MAP)
        self.assertEqual(result.returncode, 2)
        result = run_cli()
        self.assertEqual(result.returncode, 2)

    def test_multiple_case_files_processed_in_order(self):
        out = self.out_path("multi.jsonl")
        result = run_cli(
            "evaluate", "--map", LARGE_MAP,
            "--cases", os.path.join(CASES_DIR, "n-01-normalize.jsonl"),
            "--cases", os.path.join(CASES_DIR, "s-01-screen.jsonl"),
            "--out", out,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(out, encoding="utf-8") as stream:
            ids = [json.loads(line)["id"] for line in stream if line.strip()]
        self.assertEqual(ids[0], "n-01-00001")
        self.assertEqual(ids[-1], "s-01-00026")
        self.assertEqual(len(ids), 50)


if __name__ == "__main__":
    unittest.main()
