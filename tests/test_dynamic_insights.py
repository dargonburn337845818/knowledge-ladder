"""动态点拨语料测试：20 个特征 × 3 种回答都有非空、差异化、可追溯的深层提示。"""

import json
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(REPO, "expert_content", "dynamic_insights.json")
FEATURE_IDS = [
    "shape_linear", "shape_graph", "shape_algebra", "dynamic",
    "metric_sum", "metric_xor", "metric_count", "metric_bool",
    "metric_geom", "metric_num", "scale_tiny", "scale_small",
    "scale_large", "monotonic", "dependency", "multi_query",
    "preprocess", "optimization", "range_ops", "graph_path",
]


@unittest.skipUnless(os.path.exists(PATH), "dynamic_insights.json not generated yet")
class DynamicInsightsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PATH, encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_meta_and_sources(self):
        self.assertTrue(self.data["meta"]["version"])
        self.assertGreaterEqual(len(self.data["meta"]["source_ledger"]), 5)
        for s in self.data["meta"]["source_ledger"]:
            self.assertTrue(s.get("url"))
            self.assertTrue(s.get("title"))
            self.assertTrue(s.get("claim"))

    def test_all_features_have_three_answers(self):
        features = self.data["features"]
        self.assertEqual(set(features.keys()), set(FEATURE_IDS))
        for fid in FEATURE_IDS:
            answers = features[fid]
            self.assertEqual(set(answers.keys()), {"yes", "no", "uncertain"}, fid)
            for ans, text in answers.items():
                self.assertIsInstance(text, str)
                self.assertGreaterEqual(len(text), 25, f"{fid}.{ans} too short")

    def test_answers_are_not_boilerplate_repeats(self):
        features = self.data["features"]
        all_texts = [t for answers in features.values() for t in answers.values()]
        self.assertEqual(len(all_texts), len(set(all_texts)), "duplicate answer texts detected")

    def test_direction_insights_present(self):
        dirs = self.data["directions"]
        self.assertEqual(set(dirs.keys()), {"编码压缩", "传播松弛", "剪枝决策", "变换域映射"})
        for name, text in dirs.items():
            self.assertGreaterEqual(len(text), 40, name)


if __name__ == "__main__":
    unittest.main()
