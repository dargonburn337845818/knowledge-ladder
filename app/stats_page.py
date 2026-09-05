"""成长统计页：知识面覆盖 + 量化趋势 + 复盘状态。

读两个本地数据源：
- ProgressStore.mastered：知识节点勾选。
- ReflectionStore：D 盘记忆本中的 reflection.md / metrics.json / review.md。

保持离线：全部本地计算，不调用网络/LLM。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tiers_data import TIERS

from .reflection import ReflectionStore
from .state import ProgressStore


def _split_topics(text: str) -> int:
    """返回 30 分钟无思路的“类数”（逗号/顿号分隔，空串为 0）。"""
    if not text:
        return 0
    parts = [p.strip() for p in text.replace("，", ",").replace("、", ",").split(",")]
    return sum(1 for p in parts if p)


class MiniBarChart(QWidget):
    """极简竖向柱状图：用于趋势展示，不引入第三方绘图库。"""

    def __init__(self, title: str, labels: list[str], values: list[int], parent=None):
        super().__init__(parent)
        self.title = title
        self.labels = labels
        self.values = values
        self.setMinimumHeight(180)
        self.setObjectName("statsChart")

    def set_data(self, labels: list[str], values: list[int]):
        self.labels = labels
        self.values = values
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt 命名
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        painter.setPen(QColor(255, 255, 255, 200))
        painter.setFont(QFont("Sans", 11))
        painter.drawText(rect.left(), rect.top() + 16, self.title)

        plot = rect.adjusted(0, 28, 0, -22)
        max_v = max(self.values) if self.values else 1
        max_v = max(max_v, 1)
        n = len(self.values)
        if n == 0:
            painter.setPen(QColor(255, 255, 255, 90))
            painter.drawText(plot, Qt.AlignmentFlag.AlignCenter, "暂无数据")
            return

        slot = plot.width() / n
        bar_w = max(4.0, slot * 0.55)
        for i, v in enumerate(self.values):
            h = (v / max_v) * plot.height()
            x = plot.left() + i * slot + (slot - bar_w) / 2
            painter.fillRect(
                int(x),
                int(plot.bottom() - h),
                int(bar_w),
                max(1, int(h)),
                QColor(228, 184, 99, 220),
            )
            if n <= 14:
                painter.setPen(QColor(255, 255, 255, 130))
                painter.setFont(QFont("Sans", 8))
                label = self.labels[i] if i < len(self.labels) else ""
                painter.drawText(
                    int(x - 2),
                    int(plot.bottom() + 14),
                    int(bar_w + 4),
                    16,
                    Qt.AlignmentFlag.AlignCenter,
                    label,
                )


class StatsPage(QWidget):
    """成长统计页：知识面进度条 + 本周汇总 + 趋势图。"""

    def __init__(
        self,
        reflection_store: ReflectionStore,
        progress_store: ProgressStore,
        on_back=None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.reflection_store = reflection_store
        self.progress_store = progress_store
        self.on_back = on_back
        self._build()
        self._refresh()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        card = QFrame(self)
        card.setObjectName("dissectAcrylic")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 26)
        card_layout.setSpacing(10)

        head = QHBoxLayout()
        if self.on_back is not None:
            back_btn = QPushButton("‹ 返回")
            back_btn.setObjectName("dissectBack")
            back_btn.clicked.connect(self.on_back)
            head.addWidget(back_btn)
        title = QLabel("成长统计")
        title.setObjectName("dissectTitle")
        head.addWidget(title, 1)
        card_layout.addLayout(head)

        hint = QLabel("数据来自：知识面勾选 + 复盘页每日量化 + D 盘记忆本")
        hint.setObjectName("dissectHint")
        card_layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setObjectName("dissectScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("dissectContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # 知识面覆盖
        section = QLabel("知识面覆盖")
        section.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(section)

        self.tier_bars: list[tuple[QProgressBar, QLabel]] = []
        for tier in TIERS:
            tags = cast(list[dict[str, Any]], tier["tags"])
            row = QHBoxLayout()
            name = QLabel(f"{tier['name']} {tier['range']}")
            name.setObjectName("dissectHint")
            name.setMinimumWidth(150)
            row.addWidget(name)
            bar = QProgressBar()
            bar.setObjectName("statsTierBar")
            bar.setTextVisible(False)
            bar.setRange(0, len(tags))
            row.addWidget(bar, 1)
            label = QLabel("0/0")
            label.setObjectName("dissectStep")
            label.setMinimumWidth(50)
            row.addWidget(label)
            content_layout.addLayout(row)
            self.tier_bars.append((bar, label))

        # 本周量化汇总
        summary_title = QLabel("本周量化汇总")
        summary_title.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(summary_title)

        self.summary_label = QLabel("")
        self.summary_label.setObjectName("dissectThinkCard")
        self.summary_label.setWordWrap(True)
        content_layout.addWidget(self.summary_label)

        # 趋势
        trend_title = QLabel("近 14 天：30 分钟无思路类数")
        trend_title.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(trend_title)
        self.no_idea_chart = MiniBarChart("30 分钟无思路（类/天）", [], [])
        content_layout.addWidget(self.no_idea_chart)

        ac_title = QLabel("近 14 天：AC 数")
        ac_title.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(ac_title)
        self.ac_chart = MiniBarChart("AC（题/天）", [], [])
        content_layout.addWidget(self.ac_chart)

        # 复盘状态
        state_title = QLabel("复盘与点评状态")
        state_title.setObjectName("dissectThinkingTitle")
        content_layout.addWidget(state_title)
        self.state_label = QLabel("")
        self.state_label.setObjectName("dissectThinkCard")
        self.state_label.setWordWrap(True)
        content_layout.addWidget(self.state_label)

        scroll.setWidget(content)
        card_layout.addWidget(scroll, 1)
        outer.addWidget(card, 1)

    def _refresh(self) -> None:
        # 知识面覆盖
        for i, tier in enumerate(TIERS):
            tags = cast(list[dict[str, Any]], tier["tags"])
            bar, label = self.tier_bars[i]
            done = sum(1 for t in tags if self.progress_store.is_mastered(t["id"]))
            total = len(tags)
            bar.setValue(done)
            label.setText(f"{done}/{total}")

        # 量化汇总（近 7 天）
        all_metrics = self.reflection_store.all_metrics()
        dates = self.reflection_store.list_dates()
        today = date.today()
        week_start = today - timedelta(days=6)
        week_dates = [d for d in dates if week_start <= d <= today]
        attempts = ac = minutes = 0
        no_idea_days = 0
        cards_days = 0
        cards_total = 0
        for d in week_dates:
            m = all_metrics.get(d.isoformat(), {})
            attempts += int(m.get("attempts", 0))
            ac += int(m.get("ac", 0))
            minutes += int(m.get("minutes", 0))
            if _split_topics(str(m.get("no_idea", ""))) > 0:
                no_idea_days += 1
            card_text = str(m.get("cards", ""))
            if card_text.strip():
                cards_days += 1
                cards_total += _split_topics(card_text)
        reflection_days = sum(1 for d in week_dates if self.reflection_store.read_reflection(d))
        reviewed = sum(1 for d in week_dates if self.reflection_store.read_review(d))
        self.summary_label.setText(
            f"近7天：尝试 {attempts} 题 / AC {ac} 题 / 训练 {minutes} 分钟\n"
            f"复盘 {reflection_days} 天 / 有30分钟无思路 {no_idea_days} 天 / 已点评 {reviewed} 天\n"
            f"算法卡摄入 {cards_total} 个（{cards_days} 天）"
        )

        # 近 14 天趋势
        labels: list[str] = []
        no_idea_values: list[int] = []
        ac_values: list[int] = []
        start = today - timedelta(days=13)
        for i in range(14):
            d = start + timedelta(days=i)
            labels.append(d.strftime("%m-%d")[-5:])
            m = all_metrics.get(d.isoformat(), {})
            no_idea_values.append(_split_topics(str(m.get("no_idea", ""))))
            ac_values.append(int(m.get("ac", 0)))
        self.no_idea_chart.set_data(labels, no_idea_values)
        self.ac_chart.set_data(labels, ac_values)

        # 复盘状态
        pending = reviewed_total = 0
        for d in dates:
            if self.reflection_store.read_review(d):
                reviewed_total += 1
            elif self.reflection_store.read_reflection(d):
                pending += 1
        status = self.reflection_store.status()
        self.state_label.setText(
            f"当前状态：{status} ｜ 历史复盘 {len(dates)} 天 ｜ 已点评 {reviewed_total} 天 ｜ 待点评 {pending} 天"
        )
