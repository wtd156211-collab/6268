import unittest

from tests.helpers import read_jsonl, sample_strings, CASES_DIR, EXPECTED_DIR
import os

from twinmark import normalize


class NormalizeSamplesTest(unittest.TestCase):
    def test_expected_results(self):
        cases = read_jsonl(os.path.join(CASES_DIR, "n-01-normalize.jsonl"))
        expected = read_jsonl(os.path.join(EXPECTED_DIR, "n-01-normalize.jsonl"))
        self.assertEqual(len(cases), len(expected))
        for case, want in zip(cases, expected):
            with self.subTest(id=case["id"]):
                self.assertEqual(normalize(case["text"]), want["normalized"])

    def test_idempotent_on_all_sample_strings(self):
        for text in sample_strings():
            with self.subTest(text=text):
                self.assertEqual(normalize(normalize(text)), normalize(text))

    def test_multi_round_convergence(self):
        # ㎒ 第 1 轮得 MHz、第 2 轮才得 mhz
        self.assertEqual(normalize("㎒"), "mhz")

    def test_step_order_casefold_before_nfkc(self):
        # İ casefold 出 i + 组合点，NFKC/NFC 不再变
        self.assertEqual(normalize("İ"), "i̇")

    def test_zero_width_removed(self):
        self.assertEqual(normalize("pay​pal"), "paypal")
        self.assertEqual(normalize("﻿admin"), "admin")
        self.assertEqual(normalize("a­b"), "ab")

    def test_whitespace_untouched(self):
        self.assertEqual(normalize("  paypal  "), "  paypal  ")


if __name__ == "__main__":
    unittest.main()
