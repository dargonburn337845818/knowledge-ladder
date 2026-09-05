"""双端内容一致性测试：移动端生成物必须与桌面/源数据完全一致。"""

import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from scripts.check_data_schema import parse_generated_js, project_mobile_direction_content


def load(name):
    with open(os.path.join(REPO_ROOT, name), encoding="utf-8") as f:
        return json.load(f)


class CrossEndConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.heuristics = load("heuristics.json")
        cls.content = load("expert_content/direction_cards_v1.json")
        cls.dynamic_insights = load("expert_content/dynamic_insights.json")
        cls.generated = parse_generated_js(
            os.path.join(REPO_ROOT, "mobile", "www", "entropy_data.js")
        )
        cls.mobile_projection = project_mobile_direction_content(cls.content)

    def test_generated_heuristics_matches_source(self):
        self.assertEqual(self.generated["heuristics"], self.heuristics)

    def test_generated_direction_content_matches_mobile_subset(self):
        self.assertEqual(self.generated["direction_content"], self.mobile_projection)

    def test_generated_dynamic_insights_matches_source(self):
        self.assertEqual(self.generated["dynamic_insights"], self.dynamic_insights)

    def test_direction_fields_are_identical(self):
        src_dirs = self.mobile_projection["directions"]
        gen_dirs = self.generated["direction_content"]["directions"]
        self.assertEqual(len(src_dirs), 4)
        self.assertEqual(len(gen_dirs), 4)
        for src, gen in zip(src_dirs, gen_dirs, strict=True):
            self.assertEqual(src["id"], gen["id"])
            self.assertEqual(src["title"], gen["title"])
            self.assertEqual(src["value"], gen["value"])
            self.assertEqual(src["triggers"], gen["triggers"])
            self.assertEqual(src["layers"], gen["layers"])
            self.assertEqual(src["edge_cases"], gen["edge_cases"])


if __name__ == "__main__":
    unittest.main()
