# -*- coding: utf-8 -*-
"""拆题流程图：不依赖 QSS 的 QPainter 纵向节点图。"""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

class FlowDiagram(QWidget):
    """用 QPainter 直接绘制拆题流程图：不依赖 QSS / 富文本引擎，保证一定显示。"""

    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.setMinimumHeight(260)
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def sizeHint(self):
        return QSize(420, max(260, 40 + len(self.items) * 86))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        margin = 16
        node_h = 58
        gap = 26
        y = margin

        for i, (label, value) in enumerate(self.items):
            node = QRectF(margin, y, w - margin * 2, node_h)
            p.setPen(QColor(255, 255, 255, 60))
            p.setBrush(QColor(42, 45, 51))
            p.drawRoundedRect(node, 10, 10)

            p.setPen(QColor(228, 184, 99))
            p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            p.drawText(
                QRectF(node.left() + 14, node.top() + 8, node.width() - 28, 16),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

            p.setPen(QColor(245, 246, 248))
            p.setFont(QFont("Georgia", 15, QFont.Weight.Bold))
            p.drawText(
                QRectF(node.left() + 14, node.top() + 28, node.width() - 28, 22),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                value,
            )

            if i < len(self.items) - 1:
                p.setPen(QColor(255, 255, 255, 130))
                p.setFont(QFont("Segoe UI", 13))
                p.drawText(
                    QRectF(margin, node.bottom() + 2, w - margin * 2, 20),
                    Qt.AlignmentFlag.AlignCenter,
                    "↓",
                )
            y += node_h + gap
