# -*- coding: utf-8 -*-
"""可复用 UI 组件：对话框、标签行、档位页、拆题页等。

保持“简单接口”：主窗口只实例化这些组件并接信号；
具体渲染、过滤、展开、拆题逻辑都封装在组件内部。
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, QSizeF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QMovie, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from info_framework import (
    ANATOMY_STEPS,
    DYN_DYNAMIC,
    DYN_STATIC,
    INFO_OPS,
    INFO_OP_COLORS,
    OP_BASELINE,
    OP_ENCODE,
    OP_PROPAGATE,
    OP_PRUNE,
    OP_TRANSFORM,
    PHASES,
    TOPOLOGIES,
    get_alg_info,
)
from knowledge_data import ALGORITHMS, ALGORITHM_BY_NAME
from tiers_data import TIERS
from entropy_engine import EntropyEngine

from .theme import ANIM_LIGHT, ANIM_NAMES, ANIM_OFF, ANIM_SMOOTH, STYLE_DARK, STYLE_LIGHT, STYLE_NAMES, WALLPAPER_QSS
from .utils import TOTAL_TAGS, aggregate_tag_info, _unique_in_order

class CodeDialog(QDialog):
    """算法模板详情对话框。"""

    def __init__(self, parent, algorithms, animation_level=ANIM_LIGHT):
        super().__init__(parent)
        self.animation_level = animation_level
        self._fade_started = False
        self.setWindowTitle("知识点详情 / C++ 模板")
        self.resize(760, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        tabs = QTabWidget(self)
        for alg in algorithms:
            tab = QWidget()
            v = QVBoxLayout(tab)
            v.setContentsMargins(12, 12, 12, 12)
            v.setSpacing(8)

            quality = alg.get("quality", "complete")
            quality_text = {"complete": "完整", "skeleton": "骨架", "todo": "待补"}.get(quality, "完整")
            quality_label = QLabel(f"质量：{quality_text}")
            quality_label.setObjectName("qualityLabel")
            quality_label.setProperty("quality", quality)
            quality_label.style().unpolish(quality_label)
            quality_label.style().polish(quality_label)
            v.addWidget(quality_label, alignment=Qt.AlignmentFlag.AlignLeft)

            path_label = QLabel(f"{alg['category']} / {alg['sub']}")
            path_label.setObjectName("pathLabel")
            v.addWidget(path_label)

            info = alg.get("info", get_alg_info(alg["name"]))
            if info:
                info_parts = []
                if info.get("ops"):
                    info_parts.append(" / ".join(info["ops"]))
                if info.get("topology"):
                    info_parts.append(f"拓扑：{info['topology']}")
                if info.get("dynamic"):
                    info_parts.append(info["dynamic"])
                if info.get("metric"):
                    info_parts.append(f"度量：{info['metric']}")
                info_label = QLabel("信息论：" + " · ".join(info_parts))
                info_label.setObjectName("infoText")
                info_label.setWordWrap(True)
                v.addWidget(info_label)
                if info.get("why"):
                    why_label = QLabel("为什么：" + info["why"])
                    why_label.setObjectName("infoWhy")
                    why_label.setWordWrap(True)
                    v.addWidget(why_label)

            name_label = QLabel(alg["name"])
            name_label.setObjectName("algName")
            v.addWidget(name_label)

            intro_label = QLabel(alg["intro"])
            intro_label.setWordWrap(True)
            intro_label.setObjectName("introLabel")
            v.addWidget(intro_label)

            cplx_label = QLabel(f"复杂度：{alg['complexity']}")
            cplx_label.setObjectName("complexityLabel")
            v.addWidget(cplx_label)

            copy_btn = QPushButton("复制模板")
            copy_btn.setObjectName("copyBtn")
            copy_btn.clicked.connect(lambda checked=False, a=alg: self.copy_code(a["cpp"]))
            v.addWidget(copy_btn, alignment=Qt.AlignmentFlag.AlignLeft)

            code = QPlainTextEdit()
            code.setPlainText(alg["cpp"])
            code.setReadOnly(True)
            code.setObjectName("codeView")
            code.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            code.setFont(QFont("Consolas", 11))
            v.addWidget(code, 1)

            tabs.addTab(tab, alg["name"])

        layout.addWidget(tabs, 1)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def showEvent(self, event):
        super().showEvent(event)
        if self.animation_level == ANIM_SMOOTH and not self._fade_started:
            self._fade_started = True
            self.setWindowOpacity(0.0)
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setDuration(300)
            self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._fade_anim.start()

    def copy_code(self, code: str):
        QGuiApplication.clipboard().setText(code)
        QMessageBox.information(self, "已复制", "C++ 模板已复制到剪贴板。")
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
class InfoGuideDialog(QDialog):
    """信息论导论：四操作、四阶段、拆题四步、数据规模速查。"""

    def __init__(self, parent=None, store=None):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("信息论导论 / 拆题四步")
        self.resize(860, 680)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        browser = QTextBrowser(self)
        browser.setObjectName("guideBrowser")
        browser.setOpenExternalLinks(False)
        browser.setHtml(self._build_html())
        layout.addWidget(browser, 1)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _build_html(self) -> str:
        op_counts = {op: 0 for op in INFO_OPS}
        for alg in ALGORITHMS:
            for op in alg.get("info", {}).get("ops", []):
                if op in op_counts:
                    op_counts[op] += 1

        mastered_counts = None
        if self.store is not None:
            mastered_counts = {op: 0 for op in INFO_OPS}
            for tier in TIERS:
                for tag in tier["tags"]:
                    if not self.store.is_mastered(tag.get("id", "")):
                        continue
                    agg = aggregate_tag_info(tag)
                    for op in agg["ops"]:
                        if op in mastered_counts:
                            mastered_counts[op] += 1

        op_items = []
        for op in INFO_OPS:
            color = INFO_OP_COLORS.get(op, "#9AA1B0")
            desc = {
                OP_ENCODE: "减少冗余：哈希 / 前缀和 / 线性基 / SAM / 可持久化",
                OP_PROPAGATE: "扩散信息：BFS / DP / Dijkstra / 线段树 pushup / 树形 DP",
                OP_PRUNE: "缩小搜索：二分 / 双指针 / 单调栈 / 凸包 / 斜率优化 / 最小割",
                OP_TRANSFORM: "解耦纠缠：FFT / 矩阵幂 / 差分 / 对偶 / 生成函数 / LCT",
                OP_BASELINE: "没有信息破缺：暴力 / 模拟 / 几何原子 / 构造",
            }.get(op, "")
            mastered_cell = ""
            if mastered_counts is not None:
                mastered_cell = f'<td style="text-align:center;">{mastered_counts.get(op, 0)}</td>'
            op_items.append(
                f'<tr><td style="color:{color};font-weight:600;white-space:nowrap;">{op}</td>'
                f'<td>{desc}</td><td style="text-align:center;">{op_counts.get(op, 0)}</td>'
                f'{mastered_cell}</tr>'
            )

        phase_rows = []
        for pid in sorted(PHASES):
            ph = PHASES[pid]
            phase_rows.append(
                f"<tr><td style='font-weight:600;white-space:nowrap;'>{ph['name']}</td>"
                f"<td>{ph['range']}</td><td>{ph['slogan']}</td>"
                f"<td>{ph['description']}</td></tr>"
            )

        anatomy_rows = []
        for s in ANATOMY_STEPS:
            anatomy_rows.append(
                f"<tr><td style='font-weight:600;white-space:nowrap;'>{s['step']}</td>"
                f"<td>{s['question']}</td><td>{s['choices']}</td><td>{s['output']}</td></tr>"
            )

        return f"""
<html>
<body style="font-family:'Microsoft YaHei',sans-serif;font-size:13px;color:#eef0f4;background:#1d1f26;">
<h2 style="color:#82a0ff;">信息论视角：把 120 个算法压缩成一条认知轴</h2>
<p>算法不需要背标签。先问自己：<b>数据长在哪、变不变、按什么规则合并、n 有多大？</b></p>

<h3 style="color:#82a0ff;">一、四种信息操作 + 基线/暴力（算法世界的基本力）</h3>
<table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%;">
<tr><th>操作</th><th>代表算法</th><th>覆盖数</th>{("<th>已掌握</th>" if mastered_counts is not None else "")}</tr>
{''.join(op_items)}
</table>

<h3 style="color:#82a0ff;">二、四阶段难度地图</h3>
<table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%;">
<tr><th>阶段</th><th>约对应档位</th><th>一句话</th><th>核心战术</th></tr>
{''.join(phase_rows)}
</table>

<h3 style="color:#82a0ff;">三、拆题四步</h3>
<table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%;">
<tr><th>步骤</th><th>问题</th><th>选项</th><th>产出</th></tr>
{''.join(anatomy_rows)}
</table>

<h3 style="color:#82a0ff;">四、数据规模速查</h3>
<table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%;">
<tr><th>n</th><th>允许复杂度</th><th>常走的路</th></tr>
<tr><td>≤20</td><td>指数 / 状压</td><td>直接枚举子集、TSP、位运算</td></tr>
<tr><td>≤100</td><td>O(n³)</td><td>Floyd、区间 DP、矩阵乘法</td></tr>
<tr><td>≤5000</td><td>O(n²)</td><td>简单 DP、N² 枚举、局部剪枝</td></tr>
<tr><td>≤1e5</td><td>O(n log n)</td><td>排序 / 二分 / 堆 / 线段树 / 分治</td></tr>
<tr><td>≤1e9</td><td>对数 / 公式</td><td>数学公式、矩阵快速幂、找循环节</td></tr>
</table>

<p style="margin-top:14px;color:#9aa1b0;">
提醒：四种操作是<b>方便联想的记忆坐标系</b>，不是严格数学分类；一个算法常有多个标签。
例如树链剖分 = 编码压缩 + 传播松弛，AC 自动机 = 编码压缩 + 剪枝决策。
「已掌握」列按知识点行统计，一个标签包含多个操作时会重复计入。
</p>
</body>
</html>
"""
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
class DissectPage(QWidget):
    """桌面端动态熵减拆题页：基线暴力 -> 单一问题流 -> 四方向引导。"""

    VAGUE_TEXT = {
        "编码压缩": "重复信息提前存好；把状态压缩成更小表示；用预处理换取更快查询。",
        "传播松弛": "沿着依赖关系一层层推；状态从前驱传递过来；让信息按顺序走到终点。",
        "剪枝决策": "排除大批不可能候选；利用单调性一次砍掉一半；先判可行再找最优。",
        "变换域映射": "换一个坐标系；做差分、对偶、重表述；把纠缠结构转成熟悉模型。",
    }

    def __init__(self, on_back=None, parent=None):
        super().__init__(parent)
        self.on_back = on_back
        self.engine = EntropyEngine()
        self.mode = "baseline"
        self.weights = self.engine.initial_weights()
        self.asked = []
        self.history = []
        self.current_question = None
        self.last_surprise = 1.0
        self.anomaly_flag = False
        self.setObjectName("dissectPage")
        self._build()

    # ---------- 基础 UI ----------
    def _build(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 24, 24, 24)
        self.root.setSpacing(12)

        self.card = QFrame(self)
        self.card.setObjectName("dissectAcrylic")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(28, 22, 28, 26)
        card_layout.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(12)
        self.back_btn = QPushButton("‹ 返回")
        self.back_btn.setObjectName("dissectBack")
        self.back_btn.clicked.connect(self._go_back)
        head.addWidget(self.back_btn)
        self.step_label = QLabel("")
        self.step_label.setObjectName("dissectStep")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        head.addWidget(self.step_label, 1)
        card_layout.addLayout(head)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("dissectScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content = QWidget()
        self.content.setObjectName("dissectContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 20, 0, 0)
        self.content_layout.setSpacing(14)
        self.scroll_area.setWidget(self.content)
        card_layout.addWidget(self.scroll_area, 1)

        self.root.addWidget(self.card, 1)
        self._render()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
                continue
            sub = item.layout()
            if sub is not None:
                self._clear_layout(sub)
                sub.deleteLater()

    def _clear_content(self):
        self._clear_layout(self.content_layout)

    def _add_title(self, text):
        label = QLabel(text)
        label.setObjectName("dissectTitle")
        self.content_layout.addWidget(label)

    def _add_hint(self, text):
        label = QLabel(text)
        label.setObjectName("dissectHint")
        self.content_layout.addWidget(label)

    def _add_body(self, text):
        label = QLabel(text)
        label.setObjectName("dissectThinkCard")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

    def _add_button(self, text, slot, extra_object="dissectOption"):
        btn = QPushButton(text)
        btn.setObjectName(extra_object)
        btn.clicked.connect(lambda checked=False, s=slot: s())
        self.content_layout.addWidget(btn)
        return btn

    # ---------- 渲染分发 ----------
    def _render(self):
        self._clear_content()
        if self.mode == "baseline":
            self._render_baseline()
        elif self.mode == "question":
            self._render_question()
        elif self.mode == "finished":
            self._render_finish()
        else:
            self._render_direction()

    # ---------- 状态操作 ----------
    def _save_snapshot(self):
        self.history.append({
            "weights": list(self.weights),
            "asked": list(self.asked),
            "current_question": self.current_question,
        })

    def _restore_snapshot(self, snap):
        self.weights = list(snap["weights"])
        self.asked = list(snap["asked"])
        self.current_question = snap["current_question"]
        self.mode = "question"

    def _reset(self):
        self.mode = "baseline"
        self.weights = self.engine.initial_weights()
        self.asked = []
        self.history = []
        self.current_question = None
        self.last_surprise = 1.0
        self.anomaly_flag = False
        self._render()

    def _go_back(self):
        if self.mode == "question" and self.history:
            self._restore_snapshot(self.history.pop())
            self._render()
        elif self.mode == "direction":
            self.mode = "finished"
            self._render()
        elif self.mode == "finished" and self.history:
            self._restore_snapshot(self.history.pop())
            self._render()
        elif self.mode == "baseline" and self.on_back:
            self.on_back()

    def _finish_reason(self):
        stop, reason = self.engine.should_stop(self.weights, self.asked)
        return stop, reason

    # ---------- Baseline ----------
    def _render_baseline(self):
        self.step_label.setText("基线")
        self._add_title("先确认基线暴力")
        self._add_hint("这一步不看方向，只看你现在的朴素方案")
        self._add_body("你已经先想了一个暴力/模拟方案吗？")
        yes = self._add_button("是（已经想了）", lambda: self._baseline_answer(True))
        no = self._add_button("否（还没想）", lambda: self._baseline_answer(False))
        un = self._add_button("不确定", lambda: self._baseline_answer(False))
        self._baseline_warning = QLabel("请先写一个最直接的暴力/模拟方案，再继续拆题。")
        self._baseline_warning.setObjectName("dissectHint")
        self._baseline_warning.setWordWrap(True)
        self._baseline_warning.hide()
        self.content_layout.addWidget(self._baseline_warning)
        self.content_layout.addStretch(1)

    def _baseline_answer(self, ok):
        if ok:
            self.mode = "question"
            self._render()
        else:
            if hasattr(self, "_baseline_warning"):
                self._baseline_warning.show()

    # ---------- Question ----------
    def _render_question(self):
        stop, _reason = self._finish_reason()
        if stop:
            self.mode = "finished"
            self._render()
            return
        fid, _ig = self.engine.choose_next(self.weights, self.asked)
        if fid is None:
            self.mode = "finished"
            self._render()
            return
        self.current_question = fid
        feature = self.engine.feature_by_id(fid)
        self.step_label.setText("熵减")
        self._add_title("动态拆题")
        self._add_hint("只回答一个问题，机器会选最值得问的")
        self._add_body(feature["question"] if feature else fid)
        top3 = self.engine.realtime_top(self.weights)
        if top3:
            rt = QLabel("当前候选： " + "   ".join(f"{a['algorithm_name']} {a['weight']*100:.1f}%" for a in top3))
            rt.setObjectName("dissectHint")
            rt.setWordWrap(True)
            self.content_layout.addWidget(rt)
        self._add_button("是", lambda: self._handle_answer("yes"))
        self._add_button("否", lambda: self._handle_answer("no"))
        self._add_button("不确定", lambda: self._handle_answer("uncertain"))
        detector = self._add_button("我感觉不对劲", self._handle_detector, "opPill")
        self._detector_hint = QLabel("")
        self._detector_hint.setObjectName("dissectHint")
        self._detector_hint.setWordWrap(True)
        self._detector_hint.hide()
        self.content_layout.addWidget(self._detector_hint)
        if self.anomaly_flag:
            note = QLabel("刚才的回答有点反直觉，你可以持续留意。")
            note.setObjectName("dissectHint")
            note.setWordWrap(True)
            self.content_layout.addWidget(note)
        if self.history:
            back = self._add_button("‹ 上一步", self._go_back, "dissectBack")
        restart = self._add_button("重新开始", self._reset, "dissectRestart")
        self.content_layout.addStretch(1)

    def _handle_answer(self, answer):
        fid = self.current_question
        if not fid:
            return
        self._save_snapshot()
        surprise = self.engine.answer_probability(self.weights, fid, answer)
        self.weights = self.engine.posterior(self.weights, fid, answer)
        self.asked = list(self.asked) + [fid]
        self.last_surprise = surprise
        if surprise < self.engine.params.get("anomaly_surprise_threshold", 0.85):
            self.anomaly_flag = True
        stop, _reason = self._finish_reason()
        if stop:
            self.mode = "finished"
        else:
            self.mode = "question"
        self._render()

    def _handle_detector(self):
        thr = self.engine.params.get("detector_entropy_threshold", 0.30)
        if self.engine.entropy(self.weights) < thr:
            self.mode = "finished"
            self._render()
            return
        if hasattr(self, "_detector_hint"):
            self._detector_hint.setText("先再回答 1–2 个问题，让范围收小；如果仍然觉得不对，再点“我感觉不对劲”。")
            self._detector_hint.show()

    # ---------- Finish ----------
    def _render_finish(self):
        self.mode = "finished"
        self.step_label.setText("")
        self._add_title("四个方向")
        self._add_hint("机器已收敛；选一个你直觉最强的方向")
        probs = self.engine.direction_probs(self.weights)
        top = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        for name, prob in top:
            btn = QPushButton(f"{name}    {prob * 100:.0f}%")
            btn.setObjectName("opPill")
            btn.clicked.connect(lambda checked=False, d=name: self._open_direction(d))
            self.content_layout.addWidget(btn)
        algos = self.engine.top_algorithms(self.weights)
        if algos:
            algo_label = QLabel("候选算法权重\n" + "\n".join(f"{a['algorithm_name']}  {a['weight']*100:.1f}%" for a in algos))
            algo_label.setObjectName("dissectFinal")
            algo_label.setWordWrap(True)
            self.content_layout.addWidget(algo_label)
        restart = self._add_button("重新开始", self._reset, "dissectRestart")
        if self.history:
            back = self._add_button("‹ 上一步", self._go_back, "dissectBack")
        debug_btn = self._add_button("调试信息", self._toggle_debug, "dissectBack")
        self._debug_label = QLabel("")
        self._debug_label.setObjectName("dissectHint")
        self._debug_label.setWordWrap(True)
        self._debug_label.hide()
        self.content_layout.addWidget(self._debug_label)
        self.content_layout.addStretch(1)

    def _toggle_debug(self):
        if not hasattr(self, "_debug_label"):
            return
        if self._debug_label.isVisible():
            self._debug_label.hide()
        else:
            self._debug_label.setText(
                f"当前熵：{self.engine.entropy(self.weights):.3f}\n"
                f"已问问题：{len(self.asked)}\n"
                f"候选算法：{len(self.weights)}"
            )
            self._debug_label.show()

    def _open_direction(self, direction):
        self.mode = "direction"
        self._current_direction = direction
        self._render()

    # ---------- Direction ----------
    def _fill_template(self, tpl, top):
        if not tpl:
            return ""
        names = [a["algorithm_name"] for a in top]
        return (tpl.replace("{top1}", names[0] if names else "当前候选")
                    .replace("{top2}", names[1] if len(names) > 1 else "后续候选")
                    .replace("{top3}", names[2] if len(names) > 2 else "另一个候选"))

    def _render_direction(self):
        direction = getattr(self, "_current_direction", "编码压缩")
        self.step_label.setText("")
        self._add_title(direction)
        self._add_hint("顺着这个方向想，但别急着背名字")
        h = self.engine.heuristic_direction(direction)
        top = self.engine.realtime_top(self.weights)
        if h:
            dynamic = self._fill_template(h.get("dynamic_template", ""), top)
            text = h.get("heuristic", "") + "\n\n" + dynamic
            self._add_body(text)
            questions = h.get("self_questions", [])
            if questions:
                q_label = QLabel("该问自己：\n" + "\n".join(f"· {q}" for q in questions))
                q_label.setObjectName("dissectHint")
                q_label.setWordWrap(True)
                self.content_layout.addWidget(q_label)
        else:
            self._add_body(self.VAGUE_TEXT.get(direction, ""))
        back = self._add_button("‹ 返回方向", self._go_back, "dissectBack")
        restart = self._add_button("重新开始", self._reset, "dissectRestart")
        self.content_layout.addStretch(1)
class InfoMiniDialog(QDialog):
    """信息论微缩模块：把桌面端精华压缩成四个页签。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("信息论 · 微缩模块")
        self.resize(680, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        tabs = QTabWidget(self)
        tabs.addTab(self._make_ops_tab(), "四种操作")
        tabs.addTab(self._make_phase_tab(), "四阶段")
        tabs.addTab(self._make_steps_tab(), "拆题四步")
        tabs.addTab(self._make_scale_tab(), "数据规模")
        layout.addWidget(tabs, 1)

        note = QLabel("四种操作是记忆坐标系，不是严格分类；一个算法可以有多个标签。")
        note.setObjectName("miniNote")
        note.setWordWrap(True)
        layout.addWidget(note)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _html_wrap(self, body: str) -> str:
        return f"""
        <html><body style="font-family:Georgia,serif;font-size:13px;color:#F5F6F8;background:#15171C;">
        {body}
        </body></html>
        """

    def _make_ops_tab(self):
        b = QTextBrowser()
        b.setObjectName("guideBrowser")
        rows = []
        for op in INFO_OPS:
            desc = {
                "编码压缩": "减少冗余：哈希/前缀和/线性基/SAM",
                "传播松弛": "扩散信息：BFS/DP/Dijkstra/线段树",
                "剪枝决策": "缩小搜索：二分/双指针/凸包/斜率优化",
                "变换域映射": "解耦纠缠：FFT/矩阵幂/差分/生成函数",
                "基线/暴力": "没有明显压缩：暴力/模拟/构造",
            }.get(op, "")
            rows.append(f"<tr><td style='color:#E4B863'>{op}</td><td>{desc}</td></tr>")
        b.setHtml(self._html_wrap(
            "<table cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;'>"
            "<tr><th>操作</th><th>代表方向</th></tr>" + "".join(rows) + "</table>"
        ))
        return b

    def _make_phase_tab(self):
        b = QTextBrowser()
        b.setObjectName("guideBrowser")
        rows = []
        for pid in sorted(PHASES):
            ph = PHASES[pid]
            rows.append(
                f"<p style='border-top:1px solid rgba(255,255,255,0.12);padding-top:8px;'>"
                f"<b>{ph['name']}</b><br><span style='color:#E4B863'>{ph['range']}</span><br>"
                f"{ph['slogan']}<br>{ph['description']}</p>"
            )
        b.setHtml(self._html_wrap("".join(rows)))
        return b

    def _make_steps_tab(self):
        b = QTextBrowser()
        b.setObjectName("guideBrowser")
        rows = []
        for s in ANATOMY_STEPS:
            rows.append(
                f"<p style='border-top:1px solid rgba(255,255,255,0.12);padding-top:8px;'>"
                f"<b>{s['step']}</b><br>{s['question']}<br>"
                f"<span style='color:#E4B863'>{s['choices']}</span><br>{s['output']}</p>"
            )
        b.setHtml(self._html_wrap("".join(rows)))
        return b

    def _make_scale_tab(self):
        b = QTextBrowser()
        b.setObjectName("guideBrowser")
        rows = [
            "<tr><th>n</th><th>允许复杂度</th><th>常走的路</th></tr>",
            "<tr><td>≤20</td><td>指数/状压</td><td>子集、TSP、位运算</td></tr>",
            "<tr><td>≤100</td><td>O(n³)</td><td>Floyd、区间DP</td></tr>",
            "<tr><td>≤5000</td><td>O(n²)</td><td>简单DP、N²枚举</td></tr>",
            "<tr><td>≤1e5</td><td>O(n log n)</td><td>排序/二分/堆/线段树</td></tr>",
            "<tr><td>≤1e9</td><td>对数/公式</td><td>数学公式、矩阵快速幂</td></tr>",
        ]
        b.setHtml(self._html_wrap(
            "<table cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;'>"
            + "".join(rows) + "</table>"
        ))
        return b
