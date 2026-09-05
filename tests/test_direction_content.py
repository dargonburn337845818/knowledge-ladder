"""四方向内容数据层公开接口测试。"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from app.direction_content import (
    direction_by_id,
    direction_by_title,
    directions,
    legacy_direction_by_title,
    legacy_view,
    load,
)


class DirectionContentTest(unittest.TestCase):
    def test_load_has_four_directions(self):
        data = load()
        self.assertEqual(len(data["directions"]), 4)
        self.assertTrue(data["meta"]["version"])

    def test_directions_are_ordered_and_complete(self):
        rows = directions()
        self.assertEqual([d["id"] for d in rows], [
            "coding_compression",
            "propagation_relaxation",
            "pruning_decision",
            "transform_domain_mapping",
        ])
        for d in rows:
            self.assertTrue(d["value"])
            self.assertGreaterEqual(len(d["triggers"]), 3)
            self.assertIn("condition", d["layers"])
            self.assertIn("action", d["layers"])
            self.assertIn("self_question", d["layers"])
            self.assertGreaterEqual(len(d["edge_cases"]), 1)

    def test_card_triggers_are_safe_and_present(self):
        FORBIDDEN = [
            "前缀和", "线段树", "字符串哈希", "随机哈希", "二分", "三分", "差分",
            "DAG", "MST", "DP", "2-SAT", "矩阵幂", "自动机", "KMP", "Dijkstra",
            "单调栈", "单调队列", "凸包", "FFT", "AC自动机", "SAM", "背包",
            "莫队", "Tarjan", "LCA", "BIT", "Treap",
        ]
        for d in directions():
            self.assertGreaterEqual(len(d.get("card_triggers", [])), 1)
            for t in d["card_triggers"]:
                for word in FORBIDDEN:
                    self.assertNotIn(word, t)

    def test_lookup_by_id_and_title(self):
        by_id = direction_by_id("coding_compression")
        self.assertIsNotNone(by_id)
        self.assertEqual(by_id["title"], "编码压缩")
        by_title = direction_by_title("变换域映射")
        self.assertIsNotNone(by_title)
        self.assertEqual(by_title["id"], "transform_domain_mapping")

    def test_legacy_bridge(self):
        d = direction_by_id("pruning_decision")
        legacy = legacy_view(d)
        self.assertEqual(legacy["summary"], d["value"])
        self.assertEqual(legacy["signals"], d["triggers"])
        self.assertEqual(legacy["next_actions"], [d["layers"]["action"]])
        self.assertEqual(legacy["self_questions"], [d["layers"]["self_question"]])

        old = legacy_direction_by_title("编码压缩")
        self.assertIsNotNone(old)
        for field in ("summary", "signals", "next_actions", "self_questions"):
            self.assertIn(field, old)


if __name__ == "__main__":
    unittest.main()
