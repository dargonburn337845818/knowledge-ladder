"""算法卡数据测试：120 张卡片完整、字段齐全、能按名称取用。"""

import json
import os
import unittest

from knowledge_data import ALGORITHM_NAMES

try:
    from app.algorithm_card import cards_for_algorithms, load_cards

    CARDS_OK = True
except ImportError:
    load_cards = None
    cards_for_algorithms = None
    CARDS_OK = False

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD_PATH = os.path.join(REPO, "expert_content", "algorithm_cards.json")


@unittest.skipUnless(os.path.exists(CARD_PATH), "algorithm_cards.json not generated yet")
class AlgorithmCardDataTest(unittest.TestCase):
    def test_cards_cover_all_algorithm_names(self):
        with open(CARD_PATH, encoding="utf-8") as f:
            data = json.load(f)
        cards = data["cards"]
        missing = [name for name in ALGORITHM_NAMES if name not in cards]
        self.assertEqual(missing, [], f"missing cards: {missing[:10]}")
        self.assertEqual(len(cards), len(ALGORITHM_NAMES))

    def test_card_fields_exist(self):
        with open(CARD_PATH, encoding="utf-8") as f:
            data = json.load(f)
        for name, card in data["cards"].items():
            for field in ("what", "how", "complexity", "code", "advanced"):
                self.assertIn(field, card, f"{name} missing {field}")
                self.assertTrue(str(card[field]).strip(), f"{name}.{field} empty")

    def test_cards_for_algorithms_returns_in_order(self):
        result = cards_for_algorithms(["暴力枚举", "二分答案", "不存在算法"])
        names = [r[0] for r in result]
        self.assertEqual(names, ["暴力枚举", "二分答案"])
        self.assertTrue(all(len(r[1]["code"]) > 0 for r in result))


@unittest.skipUnless(CARDS_OK, "PySide6 not installed")
class AlgorithmCardLoaderTest(unittest.TestCase):
    def test_loader_returns_dict(self):
        cards = load_cards()
        if not cards:
            self.skipTest("algorithm_cards.json not available")
        self.assertIsInstance(cards, dict)
        self.assertIn("暴力枚举", cards)


if __name__ == "__main__":
    unittest.main()
