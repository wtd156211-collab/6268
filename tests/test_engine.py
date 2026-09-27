"""判定口径：screen / compare / 证据。"""

import os
import unittest

from twinmark import compare, load_maps, normalize, screen
from twinmark.textnorm import NonConvergenceError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "samples", "maps", "confusables-core.tsv")

cmap = load_maps([CORE])


class ScreenTest(unittest.TestCase):
    def test_homoglyph_with_ascii_rejected(self):
        result = screen("pаypal-support", cmap)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(len(result["pairs"]), 1)
        pair = result["pairs"][0]
        self.assertEqual((pair["index"], pair["cp"], pair["target"], pair["rule"]),
                         (1, "U+0430", "a", "homoglyph.cyrillic"))

    def test_pure_foreign_allowed_but_keeps_evidence(self):
        result = screen("привет", cmap)
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(len(result["pairs"]), 4)

    def test_invisible_always_rejected(self):
        for name in ("paypal​", "﻿support", "sup⁠port", "a­b"):
            with self.subTest(name=name):
                result = screen(name, cmap)
                self.assertEqual(result["decision"], "reject")
                self.assertEqual(result["rules"], ["invisible.zero-width"])
                self.assertIsNone(result["pairs"][0]["target"])
                self.assertIsNone(result["pairs"][0]["target_cp"])

    def test_clean_name_allowed(self):
        result = screen("PayPal-Support", cmap)
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["pairs"], [])
        self.assertEqual(result["normalized"], "paypal-support")

    def test_fullwidth_not_evidence(self):
        result = screen("ｐａｙｐａｌ", cmap)
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["pairs"], [])


class CompareTest(unittest.TestCase):
    def test_confusable_equivalent_not_identical(self):
        result = compare("paypal", "pаypal", cmap)
        self.assertTrue(result["equivalent"])
        self.assertFalse(result["identical"])
        self.assertEqual(result["pairs"][0]["side"], "right")

    def test_zero_width_identical_with_evidence(self):
        result = compare("pay​pal", "paypal", cmap)
        self.assertTrue(result["equivalent"])
        self.assertTrue(result["identical"])
        self.assertEqual(result["pairs"][0]["rule"], "invisible.zero-width")

    def test_unrelated_not_equivalent(self):
        result = compare("paypal", "netflix", cmap)
        self.assertFalse(result["equivalent"])
        self.assertFalse(result["identical"])

    def test_equivalent_false_can_carry_evidence(self):
        result = compare("kefu-01", "kefu-о1", cmap)
        self.assertFalse(result["equivalent"])
        self.assertEqual(len(result["pairs"]), 1)
        self.assertEqual(result["pairs"][0]["side"], "right")

    def test_evidence_sorted_left_then_right(self):
        result = compare("Привет", "привет", cmap)
        sides = [pair["side"] for pair in result["pairs"]]
        self.assertEqual(sides, sorted(sides, key=lambda s: 0 if s == "left" else 1))
        left_idx = [p["index"] for p in result["pairs"] if p["side"] == "left"]
        self.assertEqual(left_idx, sorted(left_idx))


class NormalizeTest(unittest.TestCase):
    def test_four_step_order(self):
        self.assertEqual(normalize("㎒"), "mhz")  # 兼容字符折出大写，需第二轮
        self.assertEqual(normalize("Ⅷ"), "viii")
        self.assertEqual(normalize("Ω"), "ω")
        self.assertEqual(normalize("  paypal  "), "  paypal  ")  # 空白不动


if __name__ == "__main__":
    unittest.main()
