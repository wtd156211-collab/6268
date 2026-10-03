import json
import os
import re
import unittest

from tests.helpers import EXPECTED_DIR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")


def _flagged_items():
    with open(
        os.path.join(EXPECTED_DIR, "w-01-web.report.json"), encoding="utf-8"
    ) as stream:
        report = json.load(stream)

    def flagged(item):
        if not item.get("pairs"):
            return False
        if item["kind"] == "screen":
            return item["decision"] == "reject"
        if item["kind"] == "compare":
            return item["equivalent"] is True
        return False

    return report, [item for item in report["items"] if flagged(item)]


class WebAssetsTest(unittest.TestCase):
    def test_required_elements_present(self):
        with open(os.path.join(WEB_DIR, "index.html"), encoding="utf-8") as stream:
            html = stream.read()
        self.assertIn('id="stats"', html)
        self.assertIn('id="list"', html)
        self.assertIn('id="detail"', html)
        self.assertIn('type="module"', html)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

    def test_app_reads_report_json_only(self):
        with open(os.path.join(WEB_DIR, "app.js"), encoding="utf-8") as stream:
            js = stream.read()
        self.assertIn("../var/report.json", js)
        # 位置与依据只能取自 JSON：必须使用 pairs / data-cp / data-target / data-rule
        for token in ("pairs", "data-cp", "data-target", "data-rule", 'dataset.id', "mark"):
            self.assertIn(token, js)

    def test_flagged_list_count_matches_stats(self):
        # 左栏条目数 = stats.flagged
        report, flagged = _flagged_items()
        self.assertEqual(len(flagged), report["stats"]["flagged"])
        ids = [item["id"] for item in flagged]
        self.assertEqual(ids, sorted(ids))

    def test_every_highlight_is_backed_by_engine_output(self):
        # 页面按 pairs 的 index 包 mark：每个标记都能在引擎输出里对上位置/目标/规则
        _, flagged = _flagged_items()
        for item in flagged:
            seen_sides = {pair["side"] for pair in item["pairs"]}
            for pair in item["pairs"]:
                side = pair["side"]
                if side == "input":
                    source = item["name"]
                elif side == "left":
                    source = item["left"]
                else:
                    source = item["right"]
                chars = list(source)
                self.assertEqual(chars[pair["index"]], pair["char"])
                self.assertRegex(pair["cp"], r"^U\+[0-9A-F]{4,6}$")
                self.assertIn(side, seen_sides)


if __name__ == "__main__":
    unittest.main()
