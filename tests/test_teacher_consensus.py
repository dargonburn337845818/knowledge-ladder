# -*- coding: utf-8 -*-
"""教师共识数据层测试：方向过滤、Top 主题排序、元纪律。"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from app.teacher_consensus import (
    load,
    meta_disciplines,
    themes,
    themes_for_direction,
    top_themes,
)


class TeacherConsensusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()

    def test_themes_loaded(self):
        self.assertEqual(len(themes()), 24)

    def test_direction_filter(self):
        trans = themes_for_direction("变换域映射")
        self.assertTrue(trans)
        self.assertTrue(all(t["direction"] == "变换域映射" for t in trans))
        self.assertEqual(trans, sorted(trans, key=lambda t: t["confidence"], reverse=True))

    def test_top_themes_respects_probabilities(self):
        probs = {"变换域映射": 0.8, "剪枝决策": 0.1}
        top = top_themes(probs, n=3)
        self.assertLessEqual(len(top), 3)
        self.assertTrue(all(t["direction"] in probs for t in top))

    def test_meta_disciplines(self):
        names = [m["id"] for m in meta_disciplines()]
        self.assertIn("human-takeover", names)
        self.assertIn("judge-then-construct", names)


if __name__ == "__main__":
    unittest.main()
