# -*- coding: utf-8 -*-
"""熵减引擎的公开接口测试：初始化、更新、信息增益、停止条件。"""

import math
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from entropy_engine import EntropyEngine


class EntropyEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = EntropyEngine()

    def test_initial_weights_normalize_to_one(self):
        w = self.engine.initial_weights()
        self.assertAlmostEqual(sum(w), 1.0, places=6)
        self.assertEqual(len(w), len(self.engine.algorithms))
        self.assertTrue(all(x >= 0 for x in w))

    def test_posterior_is_normalized(self):
        w = self.engine.initial_weights()
        fid, _ = self.engine.choose_next(w, [])
        for answer in ("yes", "no", "uncertain"):
            out = self.engine.posterior(w, fid, answer)
            self.assertAlmostEqual(sum(out), 1.0, places=9)
            self.assertGreaterEqual(min(out), 0.0)

    def test_information_gain_non_negative(self):
        w = self.engine.initial_weights()
        for f in self.engine.features[:5]:
            self.assertGreaterEqual(self.engine.information_gain(w, f["id"]), -1e-12)

    def test_choose_next_ignores_asked(self):
        w = self.engine.initial_weights()
        all_first, _ = self.engine.choose_next(w, [])
        self.assertIsNotNone(all_first)
        # 一旦问过，不应再次选中
        second, _ = self.engine.choose_next(w, [all_first])
        self.assertIsNotNone(second)
        self.assertNotEqual(second, all_first)

    def test_should_stop_after_exhaustion(self):
        # 问满后必须停止
        w = self.engine.initial_weights()
        max_q = self.engine.params.get("max_questions", 12)
        asked = [f["id"] for f in self.engine.features[:max_q]]
        stop, reason = self.engine.should_stop(w, asked)
        self.assertTrue(stop)
        self.assertIn(reason, ("max_questions", "entropy", "ig", "exhausted"))

    def test_direction_probs_sum_to_one(self):
        w = self.engine.initial_weights()
        probs = self.engine.direction_probs(w)
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=9)
        self.assertEqual(set(probs), set(self.engine.directions))

    def test_uncertain_is_weak_evidence_not_no(self):
        w = self.engine.initial_weights()
        fid, _ = self.engine.choose_next(w, [])
        no_w = self.engine.posterior(w, fid, "no")
        un_w = self.engine.posterior(w, fid, "uncertain")
        # 不确定是“是/否各一半”的弱证据，不能与“否”完全相同
        self.assertNotEqual(un_w, no_w)
        self.assertAlmostEqual(sum(un_w), 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
