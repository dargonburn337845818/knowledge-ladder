"""复盘记事本存储测试：验证 D 盘/临时目录下的文件读写与状态机。"""

import os
import tempfile
import unittest
from datetime import date

try:
    from app.reflection import ReflectionStore

    PYSIDE_OK = True
except ImportError:  # pragma: no cover - CI 无 PySide6 时跳过
    ReflectionStore = None
    PYSIDE_OK = False


@unittest.skipUnless(PYSIDE_OK, "PySide6 not installed")
class ReflectionStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = ReflectionStore(base_dir=self.tmp.name)
        self.today = date(2026, 9, 5)

    def test_write_reflection_creates_files_and_pending(self):
        text = "# 今日复盘\n\n有感悟。"
        self.store.write_reflection(self.today, text)

        reflection_path = self.store.reflection_path(self.today)
        review_path = self.store.review_path(self.today)
        self.assertTrue(os.path.exists(reflection_path))
        self.assertFalse(os.path.exists(review_path))
        self.assertEqual(self.store.read_reflection(self.today), text.rstrip() + "\n")
        self.assertEqual(self.store.status(), "pending_review")

        index = self.store.load_index()
        self.assertEqual(index["current_date"], "2026-09-05")
        self.assertEqual(index["storage_root"], self.tmp.name)

    def test_read_missing_returns_none(self):
        self.assertIsNone(self.store.read_reflection(self.today))
        self.assertIsNone(self.store.read_review(self.today))

    def test_write_review_marks_reviewed(self):
        self.store.write_reflection(self.today, "感悟")
        review = "# 专家点评\n\n优点：...\n不足：...\n追问：...\n行动：..."
        self.store.write_review(self.today, review)

        self.assertEqual(self.store.read_review(self.today), review.rstrip() + "\n")
        self.assertEqual(self.store.status(), "reviewed")
        index = self.store.load_index()
        self.assertEqual(index["last_reviewed"], "2026-09-05")

    def test_set_status_persists(self):
        self.store.set_status("leave", self.today)
        reloaded = ReflectionStore(base_dir=self.tmp.name)
        self.assertEqual(reloaded.status(), "leave")
        self.assertEqual(reloaded.load_index()["current_date"], "2026-09-05")

    def test_corrupt_index_recovers(self):
        with open(self.store.index_path(), "w", encoding="utf-8") as f:
            f.write("{ bad json")
        self.assertEqual(self.store.load_index(), {})
        self.store.write_reflection(self.today, "ok")
        self.assertEqual(self.store.status(), "pending_review")

    def test_write_and_read_metrics(self):
        self.store.write_metrics(
            self.today,
            {"attempts": 6, "ac": 4, "minutes": 90, "no_idea": "区间DP,树上差分"},
        )
        metrics = self.store.read_metrics(self.today)
        self.assertEqual(metrics["attempts"], 6)
        self.assertEqual(metrics["ac"], 4)
        self.assertEqual(metrics["minutes"], 90)
        self.assertEqual(metrics["no_idea"], "区间DP,树上差分")

    def test_write_metrics_filters_invalid_fields(self):
        clean = self.store.write_metrics(
            self.today,
            {"attempts": "3", "ac": "bad", "unknown": 1, "no_idea": "构造"},
        )
        self.assertEqual(clean, {"attempts": 3, "no_idea": "构造"})
        reloaded = self.store.read_metrics(self.today)
        self.assertEqual(reloaded["attempts"], 3)
        self.assertEqual(reloaded["no_idea"], "构造")

    def test_list_dates_sorted_and_all_metrics(self):
        d1 = date(2026, 9, 3)
        d2 = date(2026, 9, 5)
        self.store.write_metrics(d1, {"ac": 2})
        self.store.write_reflection(d2, "# 复盘")
        self.store.write_metrics(d2, {"ac": 4, "no_idea": "图论"})

        self.assertEqual(self.store.list_dates(), [d1, d2])
        all_metrics = self.store.all_metrics()
        self.assertEqual(all_metrics["2026-09-03"], {"ac": 2})
        self.assertEqual(all_metrics["2026-09-05"]["no_idea"], "图论")


if __name__ == "__main__":
    unittest.main()
