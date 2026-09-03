# -*- coding: utf-8 -*-
"""桌面端对话框：算法模板、信息论导论、信息论微缩模块。"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from info_framework import (
    ANATOMY_STEPS,
    INFO_OPS,
    INFO_OP_COLORS,
    OP_BASELINE,
    OP_ENCODE,
    OP_PROPAGATE,
    OP_PRUNE,
    OP_TRANSFORM,
    PHASES,
    get_alg_info,
)
from knowledge_data import ALGORITHMS
from tiers_data import TIERS

from .teacher_consensus import meta_disciplines, themes
from .theme import ANIM_LIGHT, ANIM_SMOOTH
from .utils import aggregate_tag_info

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

class InfoMiniDialog(QDialog):
    """信息论微缩模块：四操作、四阶段、拆题四步、数据规模、教师共识。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("信息论 · 微缩模块")
        self.resize(720, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        tabs = QTabWidget(self)
        tabs.addTab(self._make_ops_tab(), "四种操作")
        tabs.addTab(self._make_phase_tab(), "四阶段")
        tabs.addTab(self._make_steps_tab(), "拆题四步")
        tabs.addTab(self._make_scale_tab(), "数据规模")
        tabs.addTab(self._make_teacher_tab(), "教师共识")
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

    def _make_teacher_tab(self):
        b = QTextBrowser()
        b.setObjectName("guideBrowser")
        parts = ["<h3 style='color:#E4B863'>元纪律</h3>"]
        for md in meta_disciplines():
            parts.append(
                f"<p style='border-top:1px solid rgba(255,255,255,0.12);padding-top:8px;'>"
                f"<b>{md['name']}</b><br>{md['description']}</p>"
            )
        parts.append("<h3 style='color:#E4B863'>教师共识主题速览</h3>")
        for t in themes():
            parts.append(
                f"<p style='border-top:1px solid rgba(255,255,255,0.12);padding-top:8px;'>"
                f"<b>{t['name']}</b><br>"
                f"<span style='color:#E4B863'>{t['direction']}</span><br>"
                f"{t['trigger']}</p>"
            )
        b.setHtml(self._html_wrap("".join(parts)))
        return b
