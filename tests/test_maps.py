"""映射表加载与校验。"""

import os
import tempfile
import unittest

from twinmark import MapError, load_maps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "samples", "maps", "confusables-core.tsv")
LARGE = os.path.join(ROOT, "samples", "maps", "confusables-large.tsv")


def _write(tmp, text):
    path = os.path.join(tmp, "m.tsv")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


class LoadTest(unittest.TestCase):
    def test_core_map_size(self):
        cmap = load_maps([CORE])
        self.assertEqual(cmap.size, 42)

    def test_large_map_size_and_lookup(self):
        cmap = load_maps([LARGE])
        self.assertEqual(cmap.size, 12042)
        self.assertEqual(cmap.lookup("а"), ("a", "homoglyph.cyrillic"))
        self.assertIsNone(cmap.lookup("a"))

    def test_fold_replaces_once_no_cascade(self):
        cmap = load_maps([CORE])
        self.assertEqual(cmap.fold("раураl"), "paypal")
        self.assertEqual(cmap.fold("abc"), "abc")

    def test_merge_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            extra = _write(tmp, "U+4E00\tU+007A\ttest.synthetic\t甲 like z\n")
            cmap = load_maps([CORE, extra])
            self.assertEqual(cmap.size, 43)
            self.assertEqual(cmap.lookup("一"), ("z", "test.synthetic"))


class ValidationTest(unittest.TestCase):
    def _expect_error(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MapError):
                load_maps([_write(tmp, text)])

    def test_duplicate_codepoint_rejected(self):
        self._expect_error(
            "U+0430\tU+0061\thomoglyph.cyrillic\tx\n"
            "U+0430\tU+0061\thomoglyph.cyrillic\tx\n")

    def test_duplicate_across_files_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            extra = _write(tmp, "U+0430\tU+0061\thomoglyph.cyrillic\tx\n")
            with self.assertRaises(MapError):
                load_maps([CORE, extra])

    def test_bad_codepoint_format(self):
        self._expect_error("u+0430\tU+0061\thomoglyph.cyrillic\tx\n")
        self._expect_error("U+430\tU+0061\thomoglyph.cyrillic\tx\n")

    def test_target_must_be_printable_ascii(self):
        self._expect_error("U+4E01\tU+000A\ttest.bad\tx\n")
        self._expect_error("U+4E01\tU+00E9\ttest.bad\tx\n")

    def test_target_must_be_normalize_stable(self):
        self._expect_error("U+4E01\tU+0041\ttest.bad\tx\n")  # 'A' casefold 后会变

    def test_source_must_be_normalize_stable(self):
        self._expect_error("U+FF21\tU+0061\ttest.bad\tx\n")  # 全角Ａ归一化后是 a

    def test_bad_rule_id(self):
        self._expect_error("U+4E01\tU+0061\tBadRule\tx\n")

    def test_wrong_column_count(self):
        self._expect_error("U+4E01\tU+0061\ttest.ok\n")

    def test_missing_file(self):
        with self.assertRaises(MapError):
            load_maps(["no-such-file.tsv"])


if __name__ == "__main__":
    unittest.main()
