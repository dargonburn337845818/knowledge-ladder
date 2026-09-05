"""数据完整性测试：矩阵、先验、知识树与启发式数据保持一致。"""

import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from knowledge_data import ALGORITHMS


class DataIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(REPO_ROOT, "algorithm_prior.json"), encoding="utf-8") as f:
            cls.prior = json.load(f)
        with open(os.path.join(REPO_ROOT, "feature_algorithm_matrix.json"), encoding="utf-8") as f:
            cls.matrix = json.load(f)
        with open(os.path.join(REPO_ROOT, "heuristics.json"), encoding="utf-8") as f:
            cls.heuristics = json.load(f)
        with open(os.path.join(REPO_ROOT, "teacher_consensus.json"), encoding="utf-8") as f:
            cls.teacher = json.load(f)

    def test_algorithm_names_unique_in_matrix(self):
        names = [a["algorithm_name"] for a in self.matrix["algorithms"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 120)

    def test_knowledge_data_and_matrix_share_algorithms(self):
        matrix_names = {a["algorithm_name"] for a in self.matrix["algorithms"]}
        python_names = {a["name"] for a in ALGORITHMS}
        self.assertEqual(matrix_names, python_names)

    def test_every_algorithm_has_all_profiles_and_direction_weights(self):
        feature_ids = [f["id"] for f in self.matrix["features"]]
        directions = self.matrix["directions"]
        for alg in self.matrix["algorithms"]:
            for fid in feature_ids:
                self.assertIn(fid, alg.get("profile", {}), f"{alg['algorithm_name']} missing {fid}")
                self.assertIsInstance(alg["profile"][fid], (int, float))
            for d in directions:
                self.assertIn(d, alg.get("direction_weights", {}), f"{alg['algorithm_name']} missing {d}")

    def test_heuristics_directions_match_matrix(self):
        matrix_dirs = set(self.matrix["directions"])
        heur_ids = {h["id"] for h in self.heuristics["directions"]}
        self.assertEqual(matrix_dirs, heur_ids)

    def test_no_uncalibrated_teacher_features_in_matrix(self):
        # 教师共识不拍脑袋进概率矩阵；只在方向末页作为未校准线索展示。
        teacher_features = [f for f in self.matrix["features"] if f.get("kind") == "teacher"]
        self.assertEqual(teacher_features, [])

    def test_teacher_consensus_shape(self):
        themes = self.teacher["themes"]
        self.assertEqual(len(themes), 24)
        self.assertEqual(len({t["id"] for t in themes}), len(themes))
        for t in themes:
            self.assertTrue(t.get("name"))
            self.assertTrue(t.get("trigger"))
            self.assertTrue(t.get("action"))
            self.assertIn(t.get("layer"), ("consensus", "style", "warning", "common-lore"))
            self.assertIsInstance(t.get("confidence", 0), (int, float))

    def test_card_points_shape(self):
        card_points = self.heuristics.get("card_points", [])
        self.assertEqual(len(card_points), 5)
        self.assertEqual(len({c["id"] for c in card_points}), len(card_points))
        for c in card_points:
            self.assertTrue(c.get("name"))
            self.assertTrue(c.get("hint"))
            self.assertTrue(c.get("question"))


if __name__ == "__main__":
    unittest.main()
