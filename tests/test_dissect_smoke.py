"""桌面拆题页 offscreen 冒烟：无算法名/权重，卡点点击显示提示并写记录。"""

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.dissect_page import DissectPage
    from app.state import ProgressStore

    PYSIDE_OK = True
except ImportError:  # pragma: no cover - CI 无 PySide6 时跳过
    QApplication = QLabel = QPushButton = None
    DissectPage = None
    ProgressStore = None
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

    def test_direction_page_no_algorithm_names_and_card_click(self):
        with tempfile.TemporaryDirectory() as d:
            store = ProgressStore(base_dir=d)
            page = DissectPage(store=store)
            page.mode = "direction"
            page._current_direction = "编码压缩"
            page._render()

            texts = [b.text() for b in page.findChildren(QPushButton)]
            self.assertIn("读题卡", texts)
            self.assertIn("建模卡", texts)
            self.assertIn("复杂度卡", texts)
            self.assertIn("实现卡", texts)
            self.assertIn("证明卡", texts)

            all_text = "\n".join(
                [label.text() for label in page.findChildren(QLabel)]
                + [b.text() for b in page.findChildren(QPushButton)]
            )
            self.assertNotIn("%", all_text)
            for token in FORBIDDEN:
                self.assertNotIn(token, all_text)

            # 点击真实按钮
            reading_btn = next(b for b in page.findChildren(QPushButton) if b.text() == "读题卡")
            reading_btn.click()
            self.assertTrue(page._card_hint_label.text())
            self.assertIn("读题卡", page._card_summary_label.text())
            self.assertEqual(store.card_record_counts(), {"reading": 1})


if __name__ == "__main__":
    unittest.main()
