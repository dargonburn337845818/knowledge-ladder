"""ProgressStore 卡点记录测试：临时目录隔离，验证持久化与旧文件兼容。"""

import json
import os
import tempfile
import unittest

try:
    from app.state import ProgressStore

    PYSIDE_OK = True
except ImportError:  # pragma: no cover - CI 无 PySide6 时跳过
    ProgressStore = None
    PYSIDE_OK = False


@unittest.skipUnless(PYSIDE_OK, "PySide6 not installed")
class ProgressStoreTest(unittest.TestCase):
    def test_card_records_persist_and_count(self):
        with tempfile.TemporaryDirectory() as d:
            store = ProgressStore(base_dir=d)
            store.add_card_record("reading")
            store.add_card_record("modeling")
            store.add_card_record("reading")

            reloaded = ProgressStore(base_dir=d)
            self.assertEqual(len(reloaded.card_records), 3)
            self.assertEqual(reloaded.card_record_counts(10), {"reading": 2, "modeling": 1})
            self.assertEqual(reloaded.card_record_counts(2), {"reading": 1, "modeling": 1})
            self.assertEqual(reloaded.card_record_counts(0), {})

    def test_old_progress_compat(self):
        with tempfile.TemporaryDirectory() as d:
            old = {
                "mastered": {"tag-a": True},
                "style_mode": "dark",
                "animation_level": "light",
                "wallpaper": "sample.png",
                "updatedAt": "",
            }
            with open(os.path.join(d, "progress.json"), "w", encoding="utf-8") as f:
                json.dump(old, f, ensure_ascii=False, indent=2)

            store = ProgressStore(base_dir=d)
            self.assertEqual(store.card_records, [])
            self.assertEqual(store.mastered, {"tag-a": True})
            self.assertEqual(store.style_mode, "dark")
            self.assertEqual(store.wallpaper, "sample.png")

            store.add_card_record("proof")
            reloaded = ProgressStore(base_dir=d)
            self.assertEqual(reloaded.mastered, {"tag-a": True})
            self.assertEqual(reloaded.wallpaper, "sample.png")
            self.assertEqual(reloaded.card_records[0]["card"], "proof")


if __name__ == "__main__":
    unittest.main()
