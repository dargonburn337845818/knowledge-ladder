"""桌面主流程无基线回归测试。

静态断言在无 PySide6 环境也可运行；行为断言在 PySide6 存在时运行
（与现有 dissect_smoke 一致：CI 无 PySide6 时跳过）。
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

PYSIDE_OK = True
DissectPage = None
QLabel = None
QPushButton = None
try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.dissect_page import DissectPage
except ImportError:  # pragma: no cover - 无 PySide6 环境
    PYSIDE_OK = False


class DissectFlowStaticTest(unittest.TestCase):
    """不依赖 PySide6 的源码级门禁：主流程不存在 baseline。"""

    def test_source_has_no_baseline_state(self):
        path = os.path.join(REPO_ROOT, "app", "dissect_page.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("baseline", src)
        self.assertNotIn("_render_baseline", src)
        self.assertIn('self.mode = "question"', src)
        self.assertIn("_render_finish", src)

    def test_source_has_four_direction_cards(self):
        path = os.path.join(REPO_ROOT, "app", "dissect_page.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("_render_direction_choices", src)
        self.assertIn("directionChoice", src)
        self.assertNotIn("_render_direction_cards", src)
        self.assertNotIn("directionCard", src)
        self.assertIn("_open_direction", src)

    def test_source_has_no_three_layer_unlock(self):
        path = os.path.join(REPO_ROOT, "app", "dissect_page.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("_layer_unlocked", src)
        self.assertNotIn("_next_layer", src)
        self.assertNotIn("_prev_layer", src)
        self.assertNotIn("layerCondition", src)
        self.assertNotIn("layerAction", src)
        self.assertNotIn("layerSelfQuestion", src)
        self.assertNotIn("下一步", src)
        self.assertNotIn("三层点拨", src)


@unittest.skipUnless(PYSIDE_OK, "PySide6 not installed")
class DissectFlowBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_initial_mode_is_question(self):
        page = DissectPage()
        self.assertEqual(page.mode, "question")

    def test_reset_returns_to_question(self):
        page = DissectPage()
        page.mode = "finished"
        page._reset()
        self.assertEqual(page.mode, "question")

    def test_question_flow_can_reach_finished(self):
        page = DissectPage()
        for _ in range(30):
            if page.mode in ("finished", "direction"):
                break
            if page.current_question:
                page._handle_answer("yes")
            else:
                page._render_question()
        self.assertIn(page.mode, ("finished", "direction"))

    def test_finish_renders_probability_choices_and_click_opens_detail(self):
        page = DissectPage()
        page.mode = "finished"
        page._render()
        choices = [b for b in page.findChildren(QPushButton) if b.objectName() == "directionChoice"]
        self.assertEqual(len(choices), 4)
        self.assertTrue(all("%" in b.text() for b in choices))
        first = choices[0]
        first.click()
        self.assertEqual(page.mode, "direction")
        self.assertIn(page._current_direction, {"编码压缩", "传播松弛", "剪枝决策", "变换域映射"})
        self.assertFalse(any("看别的" in b.text() for b in page.findChildren(QPushButton)))
        self.assertFalse(any("卡点自查" == b.text() for b in page.findChildren(QPushButton)))

    def test_direction_detail_has_no_three_layer(self):
        page = DissectPage()
        page.mode = "direction"
        page._current_direction = "编码压缩"
        page._render()
        labels = page.findChildren(QLabel)
        self.assertFalse(any("三层点拨" in label.text() for label in labels))
        self.assertFalse(any("第 1/3 层" in label.text() for label in labels))
        buttons = page.findChildren(QPushButton)
        self.assertFalse(any(b.text() == "下一步" for b in buttons))
        self.assertFalse(any(b.text() == "‹ 上一层" for b in buttons))
        self.assertFalse(hasattr(page, "_layer_labels"))
        self.assertTrue(any("常见信号" in label.text() for label in labels))


if __name__ == "__main__":
    unittest.main()
