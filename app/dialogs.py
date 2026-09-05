"""桌面端信息论微缩模块对话框。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
)

from info_framework import INFO_OPS, PHASES

from .teacher_consensus import meta_disciplines, themes


class InfoMiniDialog(QDialog):
    """信息论微缩模块：四操作、四阶段、数据规模、教师共识。"""

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
