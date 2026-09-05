"""桌面拆题页 offscreen 冒烟：三层点拨、无算法名/权重、无卡点自查/看别的。"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.dissect_page import DissectPage

    PYSIDE_OK = True
except ImportError:  # pragma: no cover - CI 无 PySide6 时跳过
    QApplication = QLabel = QPushButton = None
    DissectPage = None
    PYSIDE_OK = False

FORBIDDEN = [
    "前缀和", "线段树", "字符串哈希", "随机哈希", "二分", "三分", "差分",
    "DAG", "MST", "DP", "2-SAT", "矩阵幂", "自动机", "KMP", "Dijkstra",
    "单调栈", "单调队列", "凸包", "FFT", "AC自动机", "SAM", "背包",
    "莫队", "Tarjan", "LCA", "BIT", "Treap",
]


@unittest.skipUnless(PYSIDE_OK, "PySide6 not installed")
class DissectSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_direction_page_three_layers_no_card_points_no_algorithms(self):
        page = DissectPage()
        page.mode = "direction"
        page._current_direction = "编码压缩"
        page._layer_unlocked = 1
        page._render()

        self.assertEqual(len(page._layer_labels), 3)
        self.assertFalse(page._layer_labels[0].isHidden())
        self.assertTrue(page._layer_labels[1].isHidden())
        self.assertTrue(page._layer_labels[2].isHidden())

        all_text = "\n".join(
            [label.text() for label in page.findChildren(QLabel) if not label.objectName().startswith("deep")]
            + [b.text() for b in page.findChildren(QPushButton)]
        )
        self.assertNotIn("%", all_text)
        self.assertNotIn("卡点自查", all_text)
        self.assertNotIn("看别的", all_text)
        self.assertIn("常见信号", all_text)
        self.assertIn("算法理解", all_text)
        deep_text = "\n".join(
            label.text() for label in page.findChildren(QLabel) if label.objectName().startswith("deep")
        )
        self.assertIn("常见误区", all_text)
        for token in ("信息论视角", "经典模式", "关键观察", "证明思路"):
            self.assertIn(token, deep_text)
        for token in FORBIDDEN:
            self.assertNotIn(token, all_text)

        self.assertTrue(any(b.text() == "下一步" for b in page.findChildren(QPushButton)))


if __name__ == "__main__":
    unittest.main()
