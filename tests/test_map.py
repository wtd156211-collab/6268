import os
import tempfile
import unittest

from twinmark import load_maps
from twinmark.mapio import MapError


def write_tmp(text):
    fd, path = tempfile.mkstemp(suffix=".tsv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.write(text)
    return path


class MapLoadingTest(unittest.TestCase):
    def test_valid_file(self):
        path = write_tmp(
            "# comment\n"
            "\n"
            "U+0430\tU+0061\thomoglyph.cyrillic\tа\n"
        )
        try:
            index = load_maps([path])
            self.assertEqual(index[0x0430], (0x0061, "homoglyph.cyrillic"))
        finally:
            os.unlink(path)

    def test_bad_code_point_format(self):
        for bad in ("u+0430", "U+430", "U+1234567", "0x0430"):
            path = write_tmp("%s\tU+0061\thomoglyph.x\tnote\n" % bad)
            with self.subTest(bad=bad):
                try:
                    with self.assertRaises(MapError):
                        load_maps([path])
                finally:
                    os.unlink(path)

    def test_target_must_be_printable_ascii(self):
        path = write_tmp("U+0430\tU+0061\thomoglyph.x\tnote\n")
        try:
            load_maps([path])
        finally:
            os.unlink(path)
        # 目标 U+0041 'A' 归一化后变小写，不稳定，拒收
        path = write_tmp("U+0430\tU+0041\thomoglyph.x\tnote\n")
        try:
            with self.assertRaises(MapError):
                load_maps([path])
        finally:
            os.unlink(path)
        path = write_tmp("U+0430\tU+00C0\thomoglyph.x\tnote\n")
        try:
            with self.assertRaises(MapError):
                load_maps([path])
        finally:
            os.unlink(path)
        path = write_tmp("U+0430\tU+0020\thomoglyph.x\tnote\n")
        try:
            with self.assertRaises(MapError):
                load_maps([path])
        finally:
            os.unlink(path)

    def test_bad_rule_id(self):
        for rule in ("Homoglyph", "homoglyph_", "a..b", ".a", "a."):
            path = write_tmp("U+0430\tU+0061\t%s\tnote\n" % rule)
            with self.subTest(rule=rule):
                try:
                    with self.assertRaises(MapError):
                        load_maps([path])
                finally:
                    os.unlink(path)

    def test_suspicious_cp_must_be_normalize_stable(self):
        # U+00AD SOFT HYPHEN 是 Cf，归一化会被删掉，不允许当可疑码位
        path = write_tmp("U+00AD\tU+0061\thomoglyph.x\tnote\n")
        try:
            with self.assertRaises(MapError):
                load_maps([path])
        finally:
            os.unlink(path)

    def test_duplicate_suspicious_cp_rejected_even_same_value(self):
        path = write_tmp(
            "U+0430\tU+0061\thomoglyph.cyrillic\ta\n"
            "U+0430\tU+0061\thomoglyph.cyrillic\ta again\n"
        )
        try:
            with self.assertRaises(MapError):
                load_maps([path])
        finally:
            os.unlink(path)

    def test_duplicate_across_files_rejected(self):
        first = write_tmp("U+0430\tU+0061\thomoglyph.cyrillic\ta\n")
        second = write_tmp("U+0430\tU+0061\thomoglyph.cyrillic\ta copy\n")
        try:
            with self.assertRaises(MapError):
                load_maps([first, second])
        finally:
            os.unlink(first)
            os.unlink(second)

    def test_duplicate_target_is_allowed_equivalence_by_target(self):
        # 不同可疑码位指向同一目标是允许的（按目标归并，不展开等价类）
        path = write_tmp(
            "U+0430\tU+0061\thomoglyph.cyrillic\ta\n"
            "U+03B1\tU+0061\thomoglyph.greek\ta again\n"
        )
        try:
            index = load_maps([path])
            self.assertEqual(index[0x0430][0], 0x0061)
            self.assertEqual(index[0x03B1][0], 0x0061)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
