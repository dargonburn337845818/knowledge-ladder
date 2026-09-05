"""视觉主题层：常量、QSS 加载与壁纸模式。

这个模块不依赖具体业务数据，只负责“长什么样”。
"""

import os
import sys

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink  # noqa: F401
    from PySide6.QtMultimediaWidgets import QGraphicsVideoItem  # noqa: F401
    HAS_MEDIA = True
except ImportError:
    HAS_MEDIA = False

APP_NAME = "KnowledgeLadder"
ORG_NAME = "ACMWorkflow"
WINDOW_TITLE = "Codeforces 难度阶梯"

STYLE_DARK = "dark"
STYLE_LIGHT = "light"
STYLE_NAMES = {STYLE_DARK: "深色现代", STYLE_LIGHT: "浅色现代"}

ANIM_OFF = "off"
ANIM_LIGHT = "light"
ANIM_SMOOTH = "smooth"
ANIM_NAMES = {ANIM_OFF: "关闭", ANIM_LIGHT: "轻量", ANIM_SMOOTH: "流畅"}

# 与 ACM Workflow 的壁纸模式一致：
# 没有壁纸时是默认亚克力；有壁纸时面板只保留一层薄雾，透出下方视频/图片壁纸。
WALLPAPER_QSS = """
/* ===== 壁纸模式：轻薄亚克力，让壁纸透出来 ===== */
QWidget#appBody, QWidget#rightContainer {
    background: transparent;
}

QFrame#titleBar {
    background: rgba(0, 0, 0, 0.30);
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

QWidget#sidebar {
    background: rgba(0, 0, 0, 0.28);
    border-right: 1px solid rgba(255,255,255,0.05);
}

QPushButton {
    background: rgba(0, 0, 0, 0.34);
    border: 1px solid rgba(255,255,255,0.10);
    color: rgba(255,255,255,0.94);
}

QPushButton#dissectNext,
QPushButton#dissectRestart,
QPushButton#next {
    background: rgba(228, 184, 99, 0.16);
    border: 1px solid rgba(228, 184, 99, 0.38);
    color: #F3DCA8;
}

QListWidget#tierList::item {
    background: rgba(0, 0, 0, 0.30);
    border: 1px solid rgba(255,255,255,0.06);
}

QListWidget#tierList::item:selected {
    background: rgba(228, 184, 99, 0.18);
    border-color: rgba(228, 184, 99, 0.45);
    color: #F3DCA8;
}

QFrame#tagRow,
QLabel#dissectNode,
QLabel#dissectThinkCard {
    background: rgba(0, 0, 0, 0.30);
    border: 1px solid rgba(255,255,255,0.06);
}

QFrame#dissectAcrylic {
    background: rgba(0, 0, 0, 0.30);
    border: 1px solid rgba(255,255,255,0.06);
}

QFrame#diagramNode,
QPushButton#diagramNodeButton {
    background: rgba(0, 0, 0, 0.30);
    border: 1px solid rgba(255,255,255,0.06);
}

QWidget#dissectContent {
    background: transparent;
}

QDialog {
    background: rgba(12, 14, 18, 0.92);
}
"""


def load_qss(path: str) -> str:
    """加载 QSS；PyInstaller 打包时从 _MEIPASS 兼容读取。"""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base = getattr(sys, "_MEIPASS", repo_root)
        with open(os.path.join(base, "style.qss"), encoding="utf-8") as f:
            return f.read()
