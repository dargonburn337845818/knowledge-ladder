"""内容 schema 完整性校验测试：先红后绿，确保校验不是摆设。"""

import copy
import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from scripts.check_data_schema import check_direction_content, check_mobile_sync


def load(name):
    with open(os.path.join(REPO_ROOT, name), encoding="utf-8") as f:
        return json.load(f)


class ContentSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load("expert_content/schema.json")
        cls.content = load("expert_content/direction_cards_v1.json")
        cls.heuristics = load("heuristics.json")

    def test_green_on_real_content(self):
        errors = []
        check_direction_content(self.schema, self.content, self.heuristics, errors)
        self.assertEqual(errors, [])

    def test_red_on_missing_card_triggers(self):
        content = copy.deepcopy(self.content)
        del content["directions"][0]["card_triggers"]
        errors = []
        check_direction_content(self.schema, content, self.heuristics, errors)
        self.assertTrue(any("card_triggers" in e for e in errors), errors)

    def test_red_on_missing_three_layer_field(self):
        content = copy.deepcopy(self.content)
        del content["directions"][0]["layers"]["condition"]
        errors = []
        check_direction_content(self.schema, content, self.heuristics, errors)
        self.assertTrue(any("condition" in e for e in errors), errors)

    def test_red_on_missing_edge_cases(self):
        content = copy.deepcopy(self.content)
        del content["directions"][0]["edge_cases"]
        errors = []
        check_direction_content(self.schema, content, self.heuristics, errors)
        self.assertTrue(any("edge_cases" in e for e in errors), errors)

    def test_red_on_empty_edge_cases(self):
        content = copy.deepcopy(self.content)
        content["directions"][0]["edge_cases"] = []
        errors = []
        check_direction_content(self.schema, content, self.heuristics, errors)
        self.assertTrue(any("at least 1" in e for e in errors), errors)

    def test_red_on_mobile_sync_mismatch(self):
        generated = {
            "heuristics": self.heuristics,
            "direction_content": None,
        }
        errors = []
        check_mobile_sync(generated, self.content, self.heuristics, errors)
        self.assertTrue(any("direction_content" in e for e in errors), errors)

    def test_green_on_mobile_sync_match(self):
        generated = {
            "heuristics": self.heuristics,
            "direction_content": self.content,
        }
        errors = []
        check_mobile_sync(generated, self.content, self.heuristics, errors)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
