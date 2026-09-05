"""本地进度存储：使用系统 AppData 目录。"""

import json
import os

from PySide6.QtCore import QStandardPaths

from .theme import ANIM_LIGHT, ANIM_OFF, ANIM_SMOOTH, STYLE_DARK, STYLE_LIGHT


class ProgressStore:
    """本地进度存储：使用系统 AppData 目录，Windows 上通常为 %APPDATA%。"""

    def __init__(self):
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not base:
            base = os.path.join(os.path.expanduser("~"), ".knowledge-ladder")
        os.makedirs(base, exist_ok=True)
        self.path = os.path.join(base, "progress.json")
        self.mastered: dict[str, bool] = {}
        self.style_mode = STYLE_DARK
        self.animation_level = ANIM_LIGHT
        self.wallpaper = ""
        self.load()

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
        except (OSError, ValueError):
            self.mastered = {}
            self.style_mode = STYLE_DARK
            self.animation_level = ANIM_LIGHT

    def save(self):
        data = {
            "mastered": self.mastered,
            "style_mode": self.style_mode,
            "animation_level": self.animation_level,
            "wallpaper": self.wallpaper,
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
