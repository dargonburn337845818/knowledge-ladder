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
        self.assertIn("_render_direction_cards", src)
        self.assertIn("directionCard", src)
        self.assertIn("_direction_content_directions", src)
        self.assertIn("_open_direction", src)

    def test_source_has_three_layer_unlock(self):
        path = os.path.join(REPO_ROOT, "app", "dissect_page.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("_layer_unlocked", src)
        self.assertIn("_next_layer", src)
        self.assertIn("_prev_layer", src)
        self.assertIn("layerCondition", src)
        self.assertIn("layerAction", src)
        self.assertIn("layerSelfQuestion", src)
        self.assertIn("下一步", src)


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

    def test_finish_renders_four_cards_and_click_opens_detail(self):
        page = DissectPage()
        page.mode = "finished"
        page._render()
        cards = [b for b in page.findChildren(QPushButton) if b.objectName() == "directionCard"]
        self.assertEqual(len(cards), 4)
        first = cards[0]
        first.click()
        self.assertEqual(page.mode, "direction")
        self.assertIn(page._current_direction, {"编码压缩", "传播松弛", "剪枝决策", "变换域映射"})

    def test_three_layer_progressive_unlock(self):
        page = DissectPage()
        page.mode = "direction"
        page._current_direction = "编码压缩"
        page._layer_unlocked = 1
        page._render()
        # 用最近一次渲染的 _layer_labels，避免 deleteLater 旧控件干扰
        cond, action, question = page._layer_labels
        self.assertFalse(cond.isHidden())
        self.assertTrue(action.isHidden())
        self.assertTrue(question.isHidden())
        progress = next(label for label in page.findChildren(QLabel) if label.objectName() == "layerProgress")
        self.assertIn("第 1/3 层", progress.text())

        next_btn = next(b for b in page.findChildren(QPushButton) if b.text() == "下一步")
        next_btn.click()
        QApplication.processEvents()
        _, action, question = page._layer_labels
        self.assertFalse(action.isHidden())
        self.assertTrue(question.isHidden())
        progress = next(label for label in page.findChildren(QLabel) if label.objectName() == "layerProgress")
        self.assertIn("第 2/3 层", progress.text())

        next_btn = next(b for b in page.findChildren(QPushButton) if b.text() == "下一步")
        next_btn.click()
        QApplication.processEvents()
        _, _, question = page._layer_labels
        self.assertFalse(question.isHidden())
        self.assertFalse(any(b.text() == "下一步" for b in page.findChildren(QPushButton)))

        prev_btn = next(b for b in page.findChildren(QPushButton) if b.text() == "‹ 上一层")
        prev_btn.click()
        QApplication.processEvents()
        _, _, question = page._layer_labels
        self.assertTrue(question.isHidden())


if __name__ == "__main__":
    unittest.main()
