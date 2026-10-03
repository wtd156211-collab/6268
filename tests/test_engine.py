import unittest

from twinmark import compare, load_maps, normalize, screen
from tests.helpers import CORE_MAP


class ScreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = load_maps([CORE_MAP])

    def test_homoglyph_with_ascii_is_reject_with_evidence(self):
        result = screen("pаypal", self.index)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["normalized"], "pаypal")
        pair = result["pairs"][0]
        self.assertEqual(pair["side"], "input")
        self.assertEqual(pair["index"], 1)
        self.assertEqual(pair["cp"], "U+0430")
        self.assertEqual(pair["char"], "а")
        self.assertEqual(pair["target"], "a")
        self.assertEqual(pair["target_cp"], "U+0061")
        self.assertEqual(pair["rule"], "homoglyph.cyrillic")
        self.assertEqual(result["rules"], ["homoglyph.cyrillic"])

    def test_pure_foreign_name_allowed_but_keeps_evidence(self):
        result = screen("привет", self.index)
        self.assertEqual(result["decision"], "allow")
        self.assertTrue(result["pairs"])
        self.assertIn("homoglyph.cyrillic", result["rules"])

    def test_zero_width_always_reject(self):
        result = screen("support​", self.index)
        self.assertEqual(result["decision"], "reject")
        pair = result["pairs"][0]
        self.assertEqual(pair["rule"], "invisible.zero-width")
        self.assertIsNone(pair["target"])
        self.assertIsNone(pair["target_cp"])

    def test_bom_evidence_index_zero(self):
        result = screen("﻿support", self.index)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["pairs"][0]["index"], 0)
        self.assertEqual(result["pairs"][0]["cp"], "U+FEFF")

    def test_plain_name_allowed_no_pairs(self):
        result = screen("paypal-support", self.index)
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["pairs"], [])
        self.assertEqual(result["rules"], [])

    def test_punct_homoglyph_reject_when_ascii_letters_present(self):
        result = screen("‐admin", self.index)
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["pairs"][0]["rule"], "homoglyph.punct")


class CompareTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = load_maps([CORE_MAP])

    def test_homoglyph_equivalent_not_identical(self):
        result = compare("paypal", "pаypal", self.index)
        self.assertTrue(result["equivalent"])
        self.assertFalse(result["identical"])
        pair = result["pairs"][0]
        self.assertEqual(pair["side"], "right")
        self.assertEqual(pair["index"], 1)

    def test_case_only_difference_identical(self):
        result = compare("PAYPAL", "paypal", self.index)
        self.assertTrue(result["equivalent"])
        self.assertTrue(result["identical"])
        self.assertEqual(result["pairs"], [])

    def test_zero_width_only_difference_identical_with_evidence(self):
        result = compare("pay​pal", "paypal", self.index)
        self.assertTrue(result["equivalent"])
        self.assertTrue(result["identical"])
        self.assertEqual(result["pairs"][0]["side"], "left")
        self.assertEqual(result["pairs"][0]["rule"], "invisible.zero-width")

    def test_different_names_equivalent_false_but_may_have_pairs(self):
        result = compare("kefu-01", "kefu-о1", self.index)
        self.assertFalse(result["equivalent"])
        self.assertFalse(result["identical"])
        self.assertTrue(result["pairs"])

    def test_trailing_space_not_equivalent(self):
        result = compare("paypal", "paypal ", self.index)
        self.assertFalse(result["equivalent"])

    def test_compatibility_char_two_rounds(self):
        result = compare("mhz", "㎒", self.index)
        self.assertTrue(result["equivalent"])
        self.assertTrue(result["identical"])

    def test_evidence_order_left_then_right(self):
        result = compare("Привет", "привет", self.index)
        sides = [(p["side"], p["index"]) for p in result["pairs"]]
        self.assertEqual(sides, sorted(sides, key=lambda x: (0 if x[0] == "left" else 1, x[1])))
        self.assertTrue(all(p["side"] == "left" for p in result["pairs"][:4]))

    def test_rules_unique_sorted(self):
        result = compare("κеfu", "kefu", self.index)
        self.assertEqual(result["rules"], ["homoglyph.cyrillic", "homoglyph.greek"])


class FoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = load_maps([CORE_MAP])

    def test_fold_single_pass_no_cascade(self):
        from twinmark import fold
        self.assertEqual(fold("аdmin", self.index), "admin")
        # 目标是 ASCII，表里不会再有映射；即使有也不级联
        self.assertEqual(fold("xyz", self.index), "xyz")


if __name__ == "__main__":
    unittest.main()
