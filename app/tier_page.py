# -*- coding: utf-8 -*-
"""档位知识树页面：掌握勾选、信息论徽章、操作过滤与分组展开。"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from info_framework import INFO_OPS, INFO_OP_COLORS
from knowledge_data import ALGORITHM_BY_NAME

from .dialogs import CodeDialog
from .theme import ANIM_OFF, ANIM_LIGHT
from .utils import aggregate_tag_info

class TagRow(QFrame):
    """单个知识点行：勾选 + 名称 + 描述 + 模板/详情按钮。

    带 ``detail`` 的条目会显示“展开/收起”，把详情原地展开；
    没有关联算法的条目不再显示无效的“模板”按钮。
    """

    def __init__(self, tag, store, on_change):
        super().__init__()
        self.tag = tag
        self.store = store
        self.on_change = on_change
        self.setObjectName("tagRow")
        self._detail_open = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(6)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(store.is_mastered(tag["id"]))
        self.checkbox.stateChanged.connect(self._changed)
        layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignTop)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        name_label = QLabel(tag["name"])
        name_label.setObjectName("tagName")
        text_box.addWidget(name_label)
        desc_label = QLabel(tag["desc"])
        desc_label.setObjectName("tagDesc")
        desc_label.setWordWrap(True)
        text_box.addWidget(desc_label)

        # 信息论徽章：操作 / 拓扑 / 动静
        self.tag_info = aggregate_tag_info(tag)
        self.info_ops = list(self.tag_info["ops"])
        if self.tag_info["ops"] or self.tag_info["topologies"] or self.tag_info["dynamics"]:
            info_row = QHBoxLayout()
            info_row.setSpacing(4)
            for op in self.tag_info["ops"]:
                badge = QLabel(op)
                badge.setObjectName("infoBadge")
                badge.setProperty("op", op)
                badge.setToolTip(f"信息操作：{op}\n{INFO_OP_COLORS.get(op, '')}")
                info_row.addWidget(badge)
            if self.tag_info["topologies"]:
                topo_badge = QLabel(" · ".join(self.tag_info["topologies"]))
                topo_badge.setObjectName("infoBadgeTopo")
                topo_badge.setToolTip("拓扑空间")
                info_row.addWidget(topo_badge)
            if self.tag_info["dynamics"]:
                dyn_badge = QLabel(" · ".join(self.tag_info["dynamics"]))
                dyn_badge.setObjectName("infoBadgeDyn")
                dyn_badge.setToolTip("静态 / 动态")
                info_row.addWidget(dyn_badge)
            info_row.addStretch(1)
            text_box.addLayout(info_row)

        layout.addLayout(text_box, 1)

        if tag.get("cf_tag"):
            cf_label = QLabel(tag["cf_tag"])
            cf_label.setObjectName("cfTag")
            layout.addWidget(cf_label, alignment=Qt.AlignmentFlag.AlignTop)

        # 无算法但有详情的思维模式：显示“展开”而不是无效的“模板”
        self.detail_btn = None
        if tag.get("detail"):
            self.detail_btn = QPushButton("展开")
            self.detail_btn.setObjectName("detailBtn")
            self.detail_btn.setFixedWidth(56)
            self.detail_btn.clicked.connect(self._toggle_detail)
            layout.addWidget(self.detail_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # 有算法模板的条目：显示“模板”
        if tag.get("algorithms"):
            template_btn = QPushButton("模板")
            template_btn.setObjectName("detailBtn")
            template_btn.setFixedWidth(56)
            template_btn.clicked.connect(self._show_template)
            layout.addWidget(template_btn, alignment=Qt.AlignmentFlag.AlignTop)

        outer.addLayout(layout)

        # 可展开详情
        self.detail_box = None
        if tag.get("detail"):
            self.detail_box = QFrame()
            self.detail_box.setObjectName("tagDetail")
            detail_layout = QVBoxLayout(self.detail_box)
            detail_layout.setContentsMargins(10, 8, 10, 8)
            detail_layout.setSpacing(4)
            detail_text = QLabel(tag["detail"])
            detail_text.setObjectName("tagDetailText")
            detail_text.setTextFormat(Qt.TextFormat.PlainText)
            detail_text.setWordWrap(True)
            detail_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            detail_layout.addWidget(detail_text)
            self.detail_box.setVisible(False)
            outer.addWidget(self.detail_box)

        if self.checkbox.isChecked():
            self._apply_checked(True)

    def _changed(self, state):
        checked = state == Qt.CheckState.Checked.value
        self.store.set_mastered(self.tag["id"], checked)
        self._apply_checked(checked)
        self.on_change()

    def _apply_checked(self, checked: bool):
        self.setProperty("mastered", checked)
        self.style().unpolish(self)
        self.style().polish(self)

    def _toggle_detail(self):
        if self.detail_box is not None:
            self.set_detail_visible(not self._detail_open)

    def set_detail_visible(self, visible: bool):
        """统一控制详情展开/收起，并同步按钮文字。"""
        if self.detail_box is None:
            return
        self._detail_open = bool(visible)
        self.detail_box.setVisible(self._detail_open)
        if self.detail_btn is not None:
            self.detail_btn.setText("收起" if self._detail_open else "展开")

    def matches(self, text: str) -> bool:
        """搜索过滤：名称、描述、分组、详情正文、信息论标签均可匹配。"""
        if not text:
            return True
        haystack = " ".join([
            self.tag.get("name", ""),
            self.tag.get("desc", ""),
            self.tag.get("group", ""),
            self.tag.get("detail", ""),
            " ".join(self.tag.get("algorithms", [])),
            " ".join(self.tag_info.get("ops", [])),
            " ".join(self.tag_info.get("topologies", [])),
            " ".join(self.tag_info.get("dynamics", [])),
            " ".join(self.tag_info.get("metrics", [])),
        ]).lower()
        return text.lower() in haystack

    def matches_op(self, op: str) -> bool:
        """按信息操作过滤：不传 op 时全部通过。"""
        if not op:
            return True
        return op in self.info_ops

    def _show_template(self):
        names = self.tag.get("algorithms", [])
        algs = [ALGORITHM_BY_NAME[n] for n in names if n in ALGORITHM_BY_NAME]
        if not algs:
            QMessageBox.information(self, "暂无模板", "该知识点暂未关联具体模板。")
            return
        dialog = CodeDialog(self, algs, self.store.animation_level)
        dialog.exec()

class TierPage(QWidget):
    """单个档位的详情页。"""

    def __init__(self, tier, store, on_change):
        super().__init__()
        self.tier = tier
        self.store = store
        self.on_change = on_change
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 极细进度条，尽量让内容区更大
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("tierProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        if self.tier.get("phase_name"):
            phase_label = QLabel(
                f"{self.tier['phase_name']} · {self.tier.get('range', '')} · {self.tier.get('goal', '')}"
            )
            phase_label.setObjectName("phaseLabel")
            phase_label.setWordWrap(True)
            layout.addWidget(phase_label)

        # 信息论操作过滤：跨档位看见同一把“刀”（仅有关联算法的档位显示）
        self.current_op_filter = ""
        self.op_filter_buttons = []
        if any(tag.get("algorithms") for tag in self.tier["tags"]):
            filter_layout = QHBoxLayout()
            filter_layout.setSpacing(4)
            all_btn = QPushButton("全部")
            all_btn.setObjectName("infoFilterBtn")
            all_btn.setCheckable(True)
            all_btn.setChecked(True)
            all_btn.clicked.connect(lambda checked=False: self._set_op_filter(""))
            filter_layout.addWidget(all_btn)
            self.op_filter_buttons.append(all_btn)
            for op in INFO_OPS:
                btn = QPushButton(op)
                btn.setObjectName("infoFilterBtn")
                btn.setProperty("op", op)
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked=False, o=op: self._set_op_filter(o))
                filter_layout.addWidget(btn)
                self.op_filter_buttons.append(btn)
            filter_layout.addStretch(1)
            layout.addLayout(filter_layout)

        # 已删除搜索框；仅在第 8 档保留批量展开/收起小按钮
        if self.tier["tags"] and any(t.get("detail") for t in self.tier["tags"]):
            toolbar = QHBoxLayout()
            toolbar.setSpacing(6)
            toolbar.addStretch(1)
            expand_btn = QPushButton("全部展开")
            expand_btn.setObjectName("toolBtn")
            expand_btn.clicked.connect(lambda: self._set_all_details(True))
            toolbar.addWidget(expand_btn)
            collapse_btn = QPushButton("全部收起")
            collapse_btn.setObjectName("toolBtn")
            collapse_btn.clicked.connect(lambda: self._set_all_details(False))
            toolbar.addWidget(collapse_btn)
            layout.addLayout(toolbar)

        # 标签列表（第 8 档带分组标题）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        self.tags_layout = QVBoxLayout(content)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(6)
        self.tag_rows = []
        self.group_headers = {}
        self.group_rows = {}
        self.group_expanded = {}
        self.ungrouped_rows = []
        for tag in self.tier["tags"]:
            group = tag.get("group")
            if group and group not in self.group_headers:
                header = QPushButton(group)
                header.setObjectName("groupHeader")
                header.setCursor(Qt.CursorShape.PointingHandCursor)
                header.setToolTip(f"点击展开 / 收起「{group}」")
                header.clicked.connect(lambda checked=False, g=group: self._toggle_group(g))
                self.tags_layout.addWidget(header)
                self.group_headers[group] = header
                self.group_rows[group] = []
                self.group_expanded[group] = False
            row = TagRow(tag, self.store, self.on_change)
            self.tag_rows.append(row)
            if group:
                self.group_rows[group].append(row)
                row.setVisible(False)  # 默认折叠分组，减少拥挤
            else:
                self.ungrouped_rows.append(row)
            self.tags_layout.addWidget(row)

        # 分组标题带数量与折叠箭头
        for group, header in self.group_headers.items():
            count = len(self.group_rows[group])
            header.setText(f"▸ {group}（{count}）")
        self.tags_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self.update_progress()

    def _filter_tags(self, text: str):
        text = (text or "").strip()
        op = self.current_op_filter

        def row_visible(row) -> bool:
            if op and not row.matches_op(op):
                return False
            if text and not row.matches(text):
                return False
            return True

        for row in self.ungrouped_rows:
            row.setVisible(row_visible(row))
        for group, rows in self.group_rows.items():
            header = self.group_headers.get(group)
            if text or op:
                matched = [row for row in rows if row_visible(row)]
                for row in rows:
                    row.setVisible(False)
                for row in matched:
                    row.setVisible(True)
                if header is not None:
                    header.setVisible(bool(matched))
            else:
                expanded = self.group_expanded.get(group, False)
                for row in rows:
                    row.setVisible(expanded)
                if header is not None:
                    header.setVisible(True)

    def _set_op_filter(self, op: str):
        self.current_op_filter = op or ""
        for btn in self.op_filter_buttons:
            if btn.text() == "全部":
                btn.setChecked(not self.current_op_filter)
            else:
                btn.setChecked(btn.text() == self.current_op_filter)
        self._filter_tags("")

    def _toggle_group(self, group: str):
        if group not in self.group_expanded:
            return
        self.group_expanded[group] = not self.group_expanded[group]
        self._refresh_group_header(group)
        self._filter_tags("")

    def _refresh_group_header(self, group: str):
        header = self.group_headers.get(group)
        if header is None:
            return
        count = len(self.group_rows.get(group, []))
        arrow = "▾" if self.group_expanded.get(group, False) else "▸"
        header.setText(f"{arrow} {group}（{count}）")

    def _set_all_details(self, visible: bool):
        # 全部展开/收起同时控制分组展开状态与详情，避免“展开了但看不到”
        for row in self.tag_rows:
            if hasattr(row, "set_detail_visible"):
                row.set_detail_visible(visible)
        for group in self.group_headers:
            self.group_expanded[group] = visible
            self._refresh_group_header(group)
        self._filter_tags("")

    def update_progress(self):
        total = len(self.tier["tags"])
        done = sum(1 for t in self.tier["tags"] if self.store.is_mastered(t["id"]))
        self.progress_bar.setRange(0, total)
        self.progress_bar.setFormat(f"已掌握 {done} / {total}")
        self.progress_bar.setToolTip(f"已掌握 {done} / {total}")
        if hasattr(self, "_progress_anim"):
            self._progress_anim.stop()
        level = self.store.animation_level
        if level in (ANIM_OFF, ANIM_LIGHT):
            self.progress_bar.setValue(done)
            return
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value", self)
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(done)
        self._progress_anim.setDuration(420)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._progress_anim.start()

def make_tier_icon(color_hex: str) -> QIcon:
    """生成一个 18x18 的档位色块图标。"""
    pm = QPixmap(18, 18)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color_hex))
    painter.drawRect(0, 0, 17, 17)
    painter.end()
    return QIcon(pm)
def tier_item_text(tier, store) -> str:
    # 极简侧栏：只保留档位数字，颜色即档位标识
    return str(tier["id"])
