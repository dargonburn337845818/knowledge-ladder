"""本地进度存储：使用系统 AppData 目录。"""

import json
import logging
import os
import tempfile
import time

from PySide6.QtCore import QStandardPaths

from .theme import ANIM_LIGHT, ANIM_OFF, ANIM_SMOOTH, STYLE_DARK, STYLE_LIGHT

logger = logging.getLogger(__name__)


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
        # 非静默错误面：UI 可读取，日志也会输出
        self.load_error: str | None = None
        self.save_error: str | None = None
        self.load()

    def _reset_defaults(self):
        self.mastered = {}
        self.style_mode = STYLE_DARK
        self.animation_level = ANIM_LIGHT
        self.wallpaper = ""
        self.card_records = []

    def _note_load_error(self, message: str):
        logger.warning("ProgressStore load problem: %s", message)
        if self.load_error is None:
            self.load_error = message
        else:
            self.load_error = f"{self.load_error}; {message}"

    def _clean_records(self, raw) -> list[dict]:
        if not isinstance(raw, list):
            return []
        out = []
        for r in raw:
            if isinstance(r, dict) and isinstance(r.get("card"), str) and "ts" in r:
                out.append({"ts": r.get("ts"), "card": r["card"]})
        return out

    def load(self):
        self.load_error = None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            # 首次运行尚无进度文件：这是正常初始状态，不算加载失败。
            self._reset_defaults()
            return
        except (OSError, ValueError) as exc:
            self._reset_defaults()
            self.load_error = f"无法读取进度文件：{exc}"
            logger.warning("Failed to load progress from %s: %s", self.path, exc)
            return

        if not isinstance(data, dict):
            self._reset_defaults()
            self.load_error = "进度文件不是 JSON 对象"
            logger.warning("Progress file %s is not a JSON object", self.path)
            return

        # mastered：必须是 dict[str, bool]
        raw_mastered = data.get("mastered", {})
        if not isinstance(raw_mastered, dict):
            self.mastered = {}
            self._note_load_error("mastered 字段不是 dict，已重置")
        else:
            self.mastered = {
                str(k): bool(v) for k, v in raw_mastered.items() if isinstance(k, str)
            }
            if len(self.mastered) != len(raw_mastered):
                self._note_load_error(
                    f"mastered 中有 {len(raw_mastered) - len(self.mastered)} 个非字符串键，已丢弃"
                )

        # style_mode：兼容旧版 hard/mac，非法值回退 dark
        style = data.get("style_mode", STYLE_DARK)
        if not isinstance(style, str):
            self.style_mode = STYLE_DARK
            self._note_load_error("style_mode 不是字符串，已回退 dark")
        else:
            if style == "hard":
                style = STYLE_DARK
            elif style == "mac":
                style = STYLE_LIGHT
            if style == STYLE_LIGHT:
                # 桌面端当前实际只有深色亚克力，light 与 mac 统一落回 dark
                self.style_mode = STYLE_DARK
            elif style in (STYLE_DARK, STYLE_LIGHT):
                self.style_mode = style
            else:
                self.style_mode = STYLE_DARK
                self._note_load_error(f"style_mode 值 {style!r} 非法，已回退 dark")

        # animation_level：合法值白名单
        raw_anim = data.get("animation_level", ANIM_LIGHT)
        if raw_anim in (ANIM_OFF, ANIM_LIGHT, ANIM_SMOOTH):
            self.animation_level = raw_anim
        else:
            self.animation_level = ANIM_LIGHT

        # wallpaper：字符串路径
        raw_wallpaper = data.get("wallpaper", "")
        if isinstance(raw_wallpaper, str):
            self.wallpaper = raw_wallpaper
        else:
            self.wallpaper = ""
            self._note_load_error("wallpaper 不是字符串，已清空")

        # card_records：必须是 list，条目形状由 _clean_records 过滤
        raw_records = data.get("card_records", [])
        if not isinstance(raw_records, list):
            self.card_records = []
            self._note_load_error("card_records 不是 list，已重置")
        else:
            self.card_records = self._clean_records(raw_records)
            if len(self.card_records) != len(raw_records):
                self._note_load_error(
                    f"card_records 中有 {len(raw_records) - len(self.card_records)} 条记录形状非法，已丢弃"
                )

    def save(self):
        data = {
            "mastered": self.mastered,
            "style_mode": self.style_mode,
            "animation_level": self.animation_level,
            "wallpaper": self.wallpaper,
            "card_records": self.card_records,
            "updatedAt": "",
        }
        self.save_error = None
        directory = os.path.dirname(self.path) or "."
        try:
            fd, tmp_path = tempfile.mkstemp(prefix=".progress-", suffix=".tmp", dir=directory)
        except OSError as exc:
            self.save_error = f"无法创建临时文件：{exc}"
            logger.exception("Failed to create temp file for progress save: %s", exc)
            return

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
            # 原子替换已保证不会出现半写文件；去掉每次 fsync，勾选进度时手感更跟手。
            os.replace(tmp_path, self.path)
        except Exception as exc:  # noqa: BLE001 - 持久化失败必须可见，不能静默吞掉
            self.save_error = f"保存失败：{exc}"
            logger.exception("Failed to save progress to %s: %s", self.path, exc)
            try:
                os.unlink(tmp_path)
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
