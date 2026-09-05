"""统计页测试：分词函数 + 离屏冒烟，确保量化页可读、可刷新。"""

import os
import tempfile
import unittest
from datetime import date, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from app.reflection import ReflectionStore
    from app.state import ProgressStore
    from app.stats_page import StatsPage, _split_topics

    PYSIDE_OK = True
except ImportError:  # pragma: no cover - CI 无 PySide6 时跳过
    QApplication = ReflectionStore = ProgressStore = StatsPage = _split_topics = None
    PYSIDE_OK = False


class SplitTopicsTest(unittest.TestCase):
    def test_counts_chinese_separators(self):
        self.assertEqual(_split_topics(""), 0)
        self.assertEqual(_split_topics("DP"), 1)
        self.assertEqual(_split_topics("区间DP,树上差分"), 2)
        self.assertEqual(_split_topics("区间DP，树上差分、图论"), 3)
        self.assertEqual(_split_topics("  "), 0)


@unittest.skipUnless(PYSIDE_OK, "PySide6 not installed")
class StatsPageSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_stats_page_renders_with_sample_data(self):
        with tempfile.TemporaryDirectory() as d:
            rs = ReflectionStore(base_dir=d)
            ps = ProgressStore(base_dir=d)
            today = date.today()
            for i in range(3):
                day = today - timedelta(days=i)
                rs.write_reflection(day, f"# {day} 复盘")
                rs.write_metrics(
                    day,
                    {"attempts": 5 + i, "ac": 3 + i, "minutes": 60 + i * 10, "no_idea": "DP,图论" if i < 2 else ""},
                )
            page = StatsPage(rs, ps)
            self.assertIn("近7天", page.summary_label.text())
            self.assertIn("AC", page.summary_label.text())
            self.assertEqual(len(page.tier_bars), 8)
            self.assertIn("30 分钟无思路", page.no_idea_chart.title)


if __name__ == "__main__":
    unittest.main()
