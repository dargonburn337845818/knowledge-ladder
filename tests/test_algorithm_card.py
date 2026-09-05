"""算法卡数据测试：120 张基础 + 7 张补充卡完整、字段齐全、能按名称取用。"""

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
        self.assertGreaterEqual(len(cards), len(ALGORITHM_NAMES))

    def test_card_fields_exist(self):
        with open(CARD_PATH, encoding="utf-8") as f:
            data = json.load(f)
        for name, card in data["cards"].items():
            for field in ("what", "how", "complexity", "code", "advanced", "priority", "signals", "key_insight", "template_quality"):
                self.assertIn(field, card, f"{name} missing {field}")
                self.assertTrue(str(card[field]).strip(), f"{name}.{field} empty" if field != "signals" else f"{name}.{field} not list")
            self.assertIn(card["priority"], ("core", "common", "aware"))
            self.assertIn(card["template_quality"], ("template", "skeleton"))
            self.assertIsInstance(card["signals"], list)

    def test_cards_for_algorithms_returns_in_order(self):
        result = cards_for_algorithms(["暴力枚举", "二分答案", "不存在算法"])
        names = [r[0] for r in result]
        self.assertEqual(names, ["暴力枚举", "二分答案"])
        self.assertTrue(all(len(r[1]["code"]) > 0 for r in result))

    def test_supplement_cards_present_with_priority(self):
        supplement = ["坐标离散化", "扫描线", "差分约束", "树形背包", "树上启发式合并 (DSU on tree)", "整体二分", "CDQ 分治"]
        with open(CARD_PATH, encoding="utf-8") as f:
            cards = json.load(f)["cards"]
        for name in supplement:
            self.assertIn(name, cards, f"missing supplement card {name}")
            self.assertIn(cards[name]["priority"], ("core", "common", "aware"))
            self.assertIsInstance(cards[name]["signals"], list)
            self.assertTrue(cards[name]["signals"])


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
