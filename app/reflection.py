"""复盘记事本：本地文件存储 + 专家点评展示。

对外接口很薄：
- ``ReflectionStore``：负责 D 盘/指定目录下的 ``YYYY-MM-DD/reflection.md``、
  ``review.md`` 与 ``index.json`` 的读写与状态机。
- ``ReflectionPage``：桌面端“复盘”页，自由文本 + 保存标记待点评 + 展示专家点评。

设计方向（见 workspace ``algorithm-coaching/DESIGN-reflection-notebook.md``）：
- 软件只负责“写复盘”，真正的 AI 专家点评由 DSH 会话读记忆本后写回 review.md。
- 保持离线承诺：本模块不调用任何网络/LLM。
"""

from __future__ import annotations

import json
import os
import platform
from datetime import date
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def default_storage_root() -> str:
    """返回默认记忆本目录：Windows 优先 D 盘链接，否则落到 WSL 真实记忆目录。

    可通过环境变量 ``KNOWLEDGE_LADDER_COACHING_ROOT`` 覆盖（测试/便携场景）。
    """
    env = os.environ.get("KNOWLEDGE_LADDER_COACHING_ROOT")
    if env:
        return env
    if platform.system() == "Windows":
        d_path = r"D:\algorithm-coaching"
        try:
            if os.path.isdir(d_path):
                return d_path
        except OSError:
            pass
        return r"\\wsl.localhost\Ubuntu\home\ru\work\algorithm-coaching"
    return str(Path.home() / ".knowledge-ladder-coaching")


class ReflectionStore:
    """复盘记事本文件存储（深模块：接口简单，实现处理路径/状态/容错）。"""

    def __init__(self, base_dir: str | None = None):
        self.root = base_dir or default_storage_root()
        os.makedirs(self.root, exist_ok=True)

    # ---------- 路径 ----------
    def day_dir(self, d: date) -> str:
        return os.path.join(self.root, d.isoformat())

    def reflection_path(self, d: date) -> str:
        return os.path.join(self.day_dir(d), "reflection.md")

    def review_path(self, d: date) -> str:
        return os.path.join(self.day_dir(d), "review.md")

    def metrics_path(self, d: date) -> str:
        return os.path.join(self.day_dir(d), "metrics.json")

    def index_path(self) -> str:
        return os.path.join(self.root, "index.json")

    # ---------- index ----------
    def load_index(self) -> dict:
        try:
            with open(self.index_path(), encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            pass
        return {}

    def save_index(self, data: dict) -> None:
        path = self.index_path()
        tmp = path + ".tmp"
        os.makedirs(self.root, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def set_status(self, status: str, d: date | None = None) -> None:
        index = self.load_index()
        index["storage_root"] = self.root
        index["status"] = status
        if d is not None:
            index["current_date"] = d.isoformat()
        self.save_index(index)

    def status(self) -> str:
        return self.load_index().get("status", "writing")

    # ---------- reflection ----------
    def read_reflection(self, d: date) -> str | None:
        try:
            with open(self.reflection_path(d), encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def write_reflection(self, d: date, text: str) -> str:
        """保存复盘内容，并把状态置为 pending_review（等待专家点评）。"""
        day = self.day_dir(d)
        os.makedirs(day, exist_ok=True)
        content = text.rstrip() + "\n"
        with open(self.reflection_path(d), "w", encoding="utf-8") as f:
            f.write(content)
        index = self.load_index()
        index["storage_root"] = self.root
        index["current_date"] = d.isoformat()
        index["status"] = "pending_review"
        self.save_index(index)
        return content

    # ---------- review ----------
    def read_review(self, d: date) -> str | None:
        try:
            with open(self.review_path(d), encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def write_review(self, d: date, text: str) -> str:
        """写入专家点评，并把状态置为 reviewed。"""
        day = self.day_dir(d)
        os.makedirs(day, exist_ok=True)
        content = text.rstrip() + "\n"
        with open(self.review_path(d), "w", encoding="utf-8") as f:
            f.write(content)
        index = self.load_index()
        index["storage_root"] = self.root
        index["current_date"] = d.isoformat()
        index["status"] = "reviewed"
        index["last_reviewed"] = d.isoformat()
        self.save_index(index)
        return content

    # ---------- metrics ----------
    def read_metrics(self, d: date) -> dict:
        try:
            with open(self.metrics_path(d), encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            pass
        return {}

    def write_metrics(self, d: date, metrics: dict) -> dict:
        """保存当天量化指标（只保留合法字段），并确保当天目录存在。"""
        day = self.day_dir(d)
        os.makedirs(day, exist_ok=True)
        allowed = {"attempts", "ac", "minutes", "no_idea", "cards"}
        clean: dict = {}
        for k, v in metrics.items():
            if k not in allowed:
                continue
            if k in ("no_idea", "cards"):
                clean[k] = str(v)
            else:
                try:
                    clean[k] = int(v)
                except (TypeError, ValueError):
                    continue
        with open(self.metrics_path(d), "w", encoding="utf-8") as f:
            json.dump(clean, f, ensure_ascii=False, indent=2)
        return clean

    def list_dates(self) -> list[date]:
        """返回有 reflection.md 或 metrics.json 的日期，升序。"""
        result: list[date] = []
        try:
            names = os.listdir(self.root)
        except OSError:
            return result
        for name in names:
            try:
                d = date.fromisoformat(name)
            except ValueError:
                continue
            if os.path.exists(self.reflection_path(d)) or os.path.exists(self.metrics_path(d)):
                result.append(d)
        return sorted(result)

    def all_metrics(self) -> dict[str, dict]:
        """返回全部日期的量化指标：{date_str: metrics}，按日期升序。"""
        out: dict[str, dict] = {}
        for d in self.list_dates():
            out[d.isoformat()] = self.read_metrics(d)
        return out

    def open_dir(self) -> None:
        """在系统文件管理器中打开记忆本目录。"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.root))


class ReflectionPage(QWidget):
    """桌面端复盘页：自由文本 + 保存待点评 + 展示专家点评。"""

    def __init__(self, store: ReflectionStore, on_back=None, parent: QWidget | None = None):
        super().__init__(parent)
        self.store = store
        self.on_back = on_back
        self.today = date.today()
        self._build()
        self._load()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        card = QFrame(self)
        card.setObjectName("dissectAcrylic")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 26)
        card_layout.setSpacing(12)

        head = QHBoxLayout()
        if self.on_back is not None:
            back_btn = QPushButton("‹ 返回")
            back_btn.setObjectName("dissectBack")
            back_btn.clicked.connect(self.on_back)
            head.addWidget(back_btn)
        title = QLabel("复盘记事本")
        title.setObjectName("dissectTitle")
        head.addWidget(title, 1)
        root_label = QLabel(self.store.root)
        root_label.setObjectName("dissectHint")
        root_label.setToolTip("复盘与点评保存在此目录")
        head.addWidget(root_label)
        card_layout.addLayout(head)

        date_label = QLabel(self.today.isoformat())
        date_label.setObjectName("dissectStep")
        card_layout.addWidget(date_label)

        hint = QLabel("写题后自然写：今天哪道题让我有感悟？哪里没讲清？想给专家一个问题？\n不用每道题都写，有真实感悟和事实即可。")
        hint.setObjectName("dissectHint")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setObjectName("dissectScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("dissectContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        self.editor = QTextEdit()
        self.editor.setObjectName("reflectionEditor")
        self.editor.setPlaceholderText(
            "# 今日复盘\n\n"
            "## 今天有感悟的题\n"
            "- 题号/难度：\n"
            "- 能讲清：\n"
            "- 还没讲清：\n"
            "- 想问专家：\n\n"
            "## 今日感悟\n"
            "（自然写）"
        )
        content_layout.addWidget(self.editor, 3)

        metric_title = QLabel("今日量化（可选，用于统计页与专家量化小评）")
        metric_title.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(metric_title)

        metric_row = QHBoxLayout()
        metric_row.setSpacing(10)

        self.attempts_spin = QSpinBox()
        self.attempts_spin.setRange(0, 10000)
        self.attempts_spin.setPrefix("尝试 ")
        metric_row.addWidget(self.attempts_spin)

        self.ac_spin = QSpinBox()
        self.ac_spin.setRange(0, 10000)
        self.ac_spin.setPrefix("AC ")
        metric_row.addWidget(self.ac_spin)

        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 1440)
        self.minutes_spin.setPrefix("时长(分钟) ")
        metric_row.addWidget(self.minutes_spin)

        self.no_idea_edit = QLineEdit()
        self.no_idea_edit.setPlaceholderText("30分钟无思路题型（逗号分隔，如：区间DP,树上差分）")
        self.no_idea_edit.setObjectName("reflectionMetricInput")
        metric_row.addWidget(self.no_idea_edit, 1)

        content_layout.addLayout(metric_row)

        self.cards_edit = QLineEdit()
        self.cards_edit.setPlaceholderText("今天看的算法卡（逗号分隔，如：二分答案,线段树）")
        self.cards_edit.setObjectName("reflectionMetricInput")
        content_layout.addWidget(self.cards_edit)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("保存并标记待点评")
        self.save_btn.setObjectName("dissectNext")
        self.save_btn.clicked.connect(self._save)
        self.open_btn = QPushButton("打开记忆本目录")
        self.open_btn.setObjectName("dissectOption")
        self.open_btn.clicked.connect(self._open_dir)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.open_btn)
        buttons.addStretch(1)
        content_layout.addLayout(buttons)

        review_title = QLabel("专家点评")
        review_title.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(review_title)

        self.review_editor = QTextEdit()
        self.review_editor.setObjectName("reflectionReview")
        self.review_editor.setReadOnly(True)
        self.review_editor.setPlaceholderText(
            "暂无点评。\n\n"
            "保存复盘后，在 DSH 会话说一声“看复盘”，专家团会读取今天这份记录，"
            "把【优点 / 真实不足 / 待验证问题 / 最小行动】写回这里。"
        )
        content_layout.addWidget(self.review_editor, 2)

        self.status_label = QLabel("状态：writing")
        self.status_label.setObjectName("dissectHint")
        content_layout.addWidget(self.status_label)

        scroll.setWidget(content)
        card_layout.addWidget(scroll, 1)

        outer.addWidget(card, 1)

    def _load(self) -> None:
        reflection = self.store.read_reflection(self.today)
        if reflection:
            self.editor.setPlainText(reflection)
        review = self.store.read_review(self.today)
        if review:
            self.review_editor.setPlainText(review)
        metrics = self.store.read_metrics(self.today)
        if metrics:
            self.attempts_spin.setValue(int(metrics.get("attempts", 0)))
            self.ac_spin.setValue(int(metrics.get("ac", 0)))
            self.minutes_spin.setValue(int(metrics.get("minutes", 0)))
            self.no_idea_edit.setText(str(metrics.get("no_idea", "")))
            self.cards_edit.setText(str(metrics.get("cards", "")))
        self._refresh_status()

    def _save(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text:
            self.status_label.setText("状态：未保存（内容为空）")
            return
        self.store.write_reflection(self.today, text)
        self.store.write_metrics(
            self.today,
            {
                "attempts": self.attempts_spin.value(),
                "ac": self.ac_spin.value(),
                "minutes": self.minutes_spin.value(),
                "no_idea": self.no_idea_edit.text().strip(),
                "cards": self.cards_edit.text().strip(),
            },
        )
        self._refresh_status()
        self.status_label.setText("已保存并标记待点评 ✓")

    def _open_dir(self) -> None:
        self.store.open_dir()

    def _refresh_status(self) -> None:
        status = self.store.status()
        labels = {
            "writing": "状态：writing（还没保存今天复盘）",
            "pending_review": "状态：pending_review（待专家点评）",
            "reviewed": "状态：reviewed（专家已点评）",
        }
        self.status_label.setText(labels.get(status, f"状态：{status}"))
