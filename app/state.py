"""本地进度存储：使用系统 AppData 目录。"""

import json
import os
import time

from PySide6.QtCore import QStandardPaths

from .theme import ANIM_LIGHT, ANIM_OFF, ANIM_SMOOTH, STYLE_DARK, STYLE_LIGHT


class ProgressStore:
    """本地进度存储：使用系统 AppData 目录，Windows 上通常为 %APPDATA%。"""

    def __init__(self, base_dir: str | None = None):
        if base_dir:
            base = base_dir
        else:
            base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)  # type: ignore[attr-defined]
            if not base:
                base = os.path.join(os.path.expanduser("~"), ".knowledge-ladder")
        os.makedirs(base, exist_ok=True)
        self.path = os.path.join(base, "progress.json")
        self.mastered: dict[str, bool] = {}
        self.style_mode = STYLE_DARK
        self.animation_level = ANIM_LIGHT
        self.wallpaper = ""
        self.card_records: list[dict] = []
        self.load()

    def _clean_records(self, raw) -> list[dict]:
        if not isinstance(raw, list):
            return []
        out = []
        for r in raw:
            if isinstance(r, dict) and isinstance(r.get("card"), str) and "ts" in r:
                out.append({"ts": r.get("ts"), "card": r["card"]})
        return out

    def load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self.mastered = data.get("mastered", {})
            style = data.get("style_mode", STYLE_DARK)
            # 兼容旧版 hard/mac
            if style == "hard":
                style = STYLE_DARK
            elif style == "mac":
                style = STYLE_LIGHT
            self.style_mode = STYLE_DARK if style == STYLE_LIGHT else (style if style in (STYLE_DARK, STYLE_LIGHT) else STYLE_DARK)
            self.animation_level = data.get("animation_level", ANIM_LIGHT)
            if self.animation_level not in (ANIM_OFF, ANIM_LIGHT, ANIM_SMOOTH):
                self.animation_level = ANIM_LIGHT
            self.wallpaper = data.get("wallpaper", "")
            self.card_records = self._clean_records(data.get("card_records", []))
        except (OSError, ValueError):
            self.mastered = {}
            self.style_mode = STYLE_DARK
            self.animation_level = ANIM_LIGHT
            self.wallpaper = ""
            self.card_records = []

    def save(self):
        data = {
            "mastered": self.mastered,
            "style_mode": self.style_mode,
            "animation_level": self.animation_level,
            "wallpaper": self.wallpaper,
            "card_records": self.card_records,
            "updatedAt": "",
        }
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def set_style_mode(self, mode: str):
        self.style_mode = mode
        self.save()

    def set_animation_level(self, level: str):
        self.animation_level = level
        self.save()

    def set_wallpaper(self, path: str):
        self.wallpaper = path
        self.save()

    def add_card_record(self, card: str):
        """记录一次卡点点击；card 为卡点 id，记录格式 {ts, card}。"""
        self.card_records.append({"ts": time.time(), "card": card})
        self.save()

    def card_record_counts(self, limit: int = 10) -> dict[str, int]:
        """返回最近 limit 条记录中按卡点 id 的计数；空记录返回空 dict。"""
        recent = self.card_records[-limit:] if limit > 0 else []
        counts: dict[str, int] = {}
        for r in recent:
            card = r.get("card")
            if isinstance(card, str):
                counts[card] = counts.get(card, 0) + 1
        return counts

    def is_mastered(self, tag_id: str) -> bool:
        return bool(self.mastered.get(tag_id, False))

    def set_mastered(self, tag_id: str, value: bool):
        self.mastered[tag_id] = value
        self.save()

    def reset(self):
        self.mastered = {}
        self.save()

    def mastered_count(self) -> int:
        return sum(1 for v in self.mastered.values() if v)
