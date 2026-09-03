# -*- coding: utf-8 -*-
"""主窗口层：自定义标题栏、缩放手柄、主窗口与壁纸集成。

对上层暴露的接口很薄：创建 MainWindow 后 show() 即可；
所有页面/弹窗/进度状态都封装在 app 深模块与 app.state 中。
"""

import os
import sys

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, QSizeF, Qt, QStandardPaths, QUrl
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
try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
    from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
    HAS_MEDIA = True
except ImportError:
    HAS_MEDIA = False

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

from .theme import (
    APP_NAME,
    ANIM_LIGHT,
    ANIM_NAMES,
    ANIM_OFF,
    ANIM_SMOOTH,
    HAS_MEDIA as THEME_HAS_MEDIA,
    ORG_NAME,
    STYLE_DARK,
    STYLE_LIGHT,
    STYLE_NAMES,
    WALLPAPER_QSS,
    WINDOW_TITLE,
    load_qss,
)
from .state import ProgressStore
from .utils import TOTAL_TAGS
from .dialogs import CodeDialog, InfoGuideDialog, InfoMiniDialog
from .dissect_page import DissectPage
from .flow import FlowDiagram
from .tier_page import TagRow, TierPage, make_tier_icon, tier_item_text

HAS_MEDIA = THEME_HAS_MEDIA

class ResizeHandle(QFrame):
    """无边框窗口的边缘/角落调整手柄。"""

    def __init__(self, parent, directions):
        super().__init__(parent)
        self.directions = set(directions)
        self._press_global = None
        self._start_geo = None
        self.setMouseTracking(True)
        self.setCursor(self._cursor())

    def _cursor(self):
        d = self.directions
        if "left" in d and "top" in d:
            return Qt.CursorShape.SizeFDiagCursor
        if "right" in d and "bottom" in d:
            return Qt.CursorShape.SizeFDiagCursor
        if "right" in d and "top" in d:
            return Qt.CursorShape.SizeBDiagCursor
        if "left" in d and "bottom" in d:
            return Qt.CursorShape.SizeBDiagCursor
        if "left" in d or "right" in d:
            return Qt.CursorShape.SizeHorCursor
        return Qt.CursorShape.SizeVerCursor

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._start_geo = self.window().geometry()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._press_global is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_global
            g = self._start_geo
            x, y, w, h = g.x(), g.y(), g.width(), g.height()
            d = self.directions
            if "left" in d:
                x += delta.x()
                w -= delta.x()
            if "right" in d:
                w += delta.x()
            if "top" in d:
                y += delta.y()
                h -= delta.y()
            if "bottom" in d:
                h += delta.y()
            min_w = self.window().minimumWidth()
            min_h = self.window().minimumHeight()
            if w < min_w:
                if "left" in d:
                    x -= min_w - w
                w = min_w
            if h < min_h:
                if "top" in d:
                    y -= min_h - h
                h = min_h
            self.window().setGeometry(x, y, w, h)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._press_global = None


class TitleBar(QFrame):
    """自定义标题栏：支持拖动窗口，左侧 macOS 风格按钮。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(36)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        self.close_btn = QPushButton()
        self.close_btn.setObjectName("winClose")
        self.close_btn.setFixedSize(14, 14)
        self.close_btn.setToolTip("关闭")
        self.close_btn.setStyleSheet("QPushButton { background: #ff5f57; border: none; border-radius: 7px; } QPushButton:hover { background: #ff7b74; }")
        self.close_btn.clicked.connect(self.window().close)

        self.min_btn = QPushButton()
        self.min_btn.setObjectName("winMin")
        self.min_btn.setFixedSize(14, 14)
        self.min_btn.setToolTip("最小化")
        self.min_btn.setStyleSheet("QPushButton { background: #febc2e; border: none; border-radius: 7px; } QPushButton:hover { background: #ffce5c; }")
        self.min_btn.clicked.connect(self.window().showMinimized)

        self.max_btn = QPushButton()
        self.max_btn.setObjectName("winMax")
        self.max_btn.setFixedSize(14, 14)
        self.max_btn.setToolTip("最大化 / 还原")
        self.max_btn.setStyleSheet("QPushButton { background: #28c840; border: none; border-radius: 7px; } QPushButton:hover { background: #4cdb62; }")
        self.max_btn.clicked.connect(self._toggle_max)

        title = QLabel("")
        title.setObjectName("winTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, 1)

        layout.addSpacing(8)
        layout.addWidget(self.close_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)

    def _toggle_max(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()
        if hasattr(win, "_update_maximized_mode"):
            win._update_maximized_mode()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(make_tier_icon("#C79A6B"))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(1080, 720)
        self.setMinimumSize(860, 560)

        self.store = ProgressStore()

        central = QWidget()
        central.setObjectName("appShell")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.root_layout = root

        self.title_bar = TitleBar(self)
        root.addWidget(self.title_bar)

        body = QWidget()
        body.setObjectName("appBody")
        self.body = body
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        root.addWidget(body, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        body_layout.addWidget(splitter)

        # 左侧档位列表：极简导航，只留颜色 + 数字；宽度可拖动缩放
        left = QWidget()
        left.setObjectName("sidebar")
        left.setMinimumWidth(120)
        left.setMaximumWidth(280)
        left.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)

        app_title = QLabel("CF 难度阶梯", left)
        app_title.setObjectName("appTitle")
        app_title.setVisible(False)

        self.global_progress = QLabel(left)
        self.global_progress.setObjectName("globalProgress")
        self.global_progress.setVisible(False)

        self.tier_list = QListWidget()
        self.tier_list.setObjectName("tierList")
        self.tier_list.setUniformItemSizes(True)
        self.tier_list.setIconSize(QSize(18, 18))
        self.tier_list.currentRowChanged.connect(self._on_tier_changed)

        # 拆题主入口：桌面端也以“拆题引导”为主
        self.dissect_btn = QPushButton("拆题", left)
        self.dissect_btn.setObjectName("dissectBtn")
        self.dissect_btn.setToolTip("打开拆题引导：四步拆解 + 引导式思考")
        self.dissect_btn.clicked.connect(self._show_dissect)
        left_layout.addWidget(self.dissect_btn)

        # 算法模板导航：从拆题主界面进入，查看算法信息/C++模板
        self.template_btn = QPushButton("算法模板", left)
        self.template_btn.setObjectName("templateBtn")
        self.template_btn.setToolTip("查看算法信息与 C++ 模板")
        self.template_btn.clicked.connect(self._show_templates)
        left_layout.addWidget(self.template_btn)

        # 壁纸：桌面端玻璃拟态可链接本地 wallpaper 图片
        self.wallpaper_btn = QPushButton("壁纸", left)
        self.wallpaper_btn.setObjectName("wallpaperBtn")
        self.wallpaper_btn.setToolTip("选择壁纸：支持 mp4 / webm / mov / m4v 视频、GIF 与图片；有壁纸时透出背景，清除后恢复默认亚克力")
        self.wallpaper_btn.clicked.connect(self._choose_wallpaper)
        left_layout.addWidget(self.wallpaper_btn)

        # 信息论导论入口：常驻一个小按钮，不占太多空间
        self.info_btn = QPushButton("导论", left)
        self.info_btn.setObjectName("infoBtn")
        self.info_btn.setToolTip("打开信息论总纲：四操作 / 四阶段 / 拆题四步")
        self.info_btn.clicked.connect(self._show_guide)
        left_layout.addWidget(self.info_btn)

        # 导航按钮放在左上，和预览保持一致；8 档列表保持紧凑，不撑满左侧
        self.tier_list.setMaximumHeight(320)
        left_layout.addWidget(self.tier_list)
        left_layout.addStretch(1)

        # 简约模式：隐藏风格/动画/重置等次要控制，避免挤压左侧 8 档列表
        self.style_btn = QPushButton(left)
        self.style_btn.setObjectName("styleBtn")
        self.style_btn.clicked.connect(self._toggle_style)
        self.style_btn.setVisible(False)

        anim_label = QLabel("动画强度", left)
        anim_label.setObjectName("animLabel")
        anim_label.setVisible(False)

        self.anim_combo = QComboBox(left)
        self.anim_combo.setObjectName("animCombo")
        for level in (ANIM_OFF, ANIM_LIGHT, ANIM_SMOOTH):
            self.anim_combo.addItem(ANIM_NAMES[level], level)
        idx = self.anim_combo.findData(self.store.animation_level)
        self.anim_combo.setCurrentIndex(idx if idx >= 0 else 1)
        self.anim_combo.currentIndexChanged.connect(self._change_animation_level)
        self.anim_combo.setVisible(False)

        reset_btn = QPushButton("重置进度", left)
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self._reset_progress)
        reset_btn.setVisible(False)

        splitter.addWidget(left)

        # 右侧内容
        self.right_container = QWidget()
        self.right_container.setObjectName("rightContainer")
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        splitter.addWidget(self.right_container)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([190, 890])

        self._install_resize_handles()
        self._update_window_effect()

        self._populate_tier_list()
        self._update_global_progress()
        self._apply_style(self.store.style_mode)
        self._apply_wallpaper()
        self._update_maximized_mode()
        self._show_dissect()

    def _install_resize_handles(self):
        central = self.centralWidget()
        self._resize_handles = []
        specs = [
            ("left", ["left"]),
            ("right", ["right"]),
            ("top", ["top"]),
            ("bottom", ["bottom"]),
            ("topleft", ["left", "top"]),
            ("topright", ["right", "top"]),
            ("bottomleft", ["left", "bottom"]),
            ("bottomright", ["right", "bottom"]),
        ]
        for name, dirs in specs:
            handle = ResizeHandle(central, dirs)
            handle.setObjectName(f"resizeHandle{name}")
            handle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self._resize_handles.append(handle)
        self._layout_resize_handles()

    def _layout_resize_handles(self):
        central = self.centralWidget()
        w = central.width()
        h = central.height()
        m = 0
        t = 6
        positions = {
            "left": (0, m, t, h - 2 * m),
            "right": (w - t, m, t, h - 2 * m),
            "top": (m, 0, w - 2 * m, t),
            "bottom": (m, h - t, w - 2 * m, t),
            "topleft": (0, 0, 14, 14),
            "topright": (w - 14, 0, 14, 14),
            "bottomleft": (0, h - 14, 14, 14),
            "bottomright": (w - 14, h - 14, 14, 14),
        }
        for handle in self._resize_handles:
            name = handle.objectName().replace("resizeHandle", "")
            x, y, rw, rh = positions[name]
            handle.setGeometry(x, y, rw, rh)
            handle.raise_()

    def _update_maximized_mode(self):
        """最大化时去掉外圈留白、圆角和阴影，让界面真正填满屏幕。"""
        if not hasattr(self, "root_layout") or not hasattr(self, "title_bar"):
            return
        maximized = self.isMaximized()

        shell = self.centralWidget()
        shell.setProperty("maximized", maximized)
        shell.style().unpolish(shell)
        shell.style().polish(shell)

        self.title_bar.setProperty("maximized", maximized)
        self.title_bar.style().unpolish(self.title_bar)
        self.title_bar.style().polish(self.title_bar)

        # 扁平化：任何状态下都不保留四周留白
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        if hasattr(self, "_resize_handles"):
            for handle in self._resize_handles:
                handle.setVisible(not maximized)

        self._update_window_effect()
        self.root_layout.invalidate()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_resize_handles"):
            self._layout_resize_handles()
        self._layout_wallpaper_layer()
        if hasattr(self, "root_layout") and hasattr(self, "title_bar"):
            self._update_maximized_mode()

    def _layout_wallpaper_layer(self):
        if not hasattr(self, "centralWidget"):
            return
        rect = self.centralWidget().rect()
        for attr in ("_video_widget", "_video_view", "_video_label", "_gif_label", "_image_label"):
            layer = getattr(self, attr, None)
            if layer is not None:
                layer.setGeometry(rect)
        item = getattr(self, "_video_item", None)
        if item is not None:
            item.setSize(QSizeF(rect.width(), rect.height()))
            scene = getattr(self, "_video_scene", None)
            if scene is not None:
                scene.setSceneRect(0, 0, rect.width(), rect.height())

    def _raise_ui_above_wallpaper(self):
        """确保主界面控件永远在壁纸层上方。"""
        if hasattr(self, "body"):
            self.body.raise_()
        if hasattr(self, "title_bar"):
            self.title_bar.raise_()

    def _update_window_effect(self):
        # 扁平简约：不使用窗口阴影，避免四边出现多余暗角
        self.centralWidget().setGraphicsEffect(None)

    def _populate_tier_list(self):
        for tier in TIERS:
            item = QListWidgetItem()
            item.setText(tier_item_text(tier, self.store))
            item.setIcon(make_tier_icon(tier["color"]))
            item.setData(Qt.ItemDataRole.UserRole, tier["id"])
            item.setSizeHint(QSize(120, 42))
            total = len(tier["tags"])
            done = sum(1 for t in tier["tags"] if self.store.is_mastered(t["id"]))
            phase_line = tier.get("phase_name", "")
            item.setToolTip(f"{tier['name']}  {tier['range']}\n{phase_line}\n已掌握 {done}/{total}")
            self.tier_list.addItem(item)

    def _refresh_tier_list(self):
        for i, tier in enumerate(TIERS):
            item = self.tier_list.item(i)
            if item:
                item.setText(tier_item_text(tier, self.store))
                total = len(tier["tags"])
                done = sum(1 for t in tier["tags"] if self.store.is_mastered(t["id"]))
                phase_line = tier.get("phase_name", "")
                item.setToolTip(f"{tier['name']}  {tier['range']}\n{phase_line}\n已掌握 {done}/{total}")

    def _on_tier_changed(self, row: int):
        if row < 0 or row >= len(TIERS):
            return
        tier = TIERS[row]
        self._clear_right()
        page = TierPage(tier, self.store, self._update_global_progress)
        self.right_layout.addWidget(page, 1)

    def _show_dissect(self):
        self.tier_list.setVisible(False)
        self._clear_right()
        page = DissectPage(on_back=self._show_templates, parent=self)
        self.right_layout.addWidget(page, 1)

    def _show_templates(self):
        self.tier_list.setVisible(True)
        if self.tier_list.currentRow() < 0:
            self.tier_list.setCurrentRow(0)
        else:
            self._on_tier_changed(self.tier_list.currentRow())

    def _clear_right(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _update_global_progress(self):
        total = TOTAL_TAGS
        done = self.store.mastered_count()
        self.global_progress.setText(f"总进度：{done} / {total}")
        self._refresh_tier_list()
        # 刷新当前页进度条
        for i in range(self.right_layout.count()):
            w = self.right_layout.itemAt(i).widget()
            if isinstance(w, TierPage):
                w.update_progress()

    def _reset_progress(self):
        ret = QMessageBox.question(
            self,
            "确认重置",
            "确定要清空所有已掌握进度吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.store.reset()
            self._update_global_progress()
            row = self.tier_list.currentRow()
            if row >= 0:
                self._on_tier_changed(row)

    def _apply_style(self, mode: str):
        # 桌面端没有真正的浅色主题（两个 QSS 相同），隐藏入口并强制深色亚克力。
        if mode == STYLE_LIGHT:
            mode = STYLE_DARK
            self.store.style_mode = STYLE_DARK
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(repo_root, "style.qss")
        qss = load_qss(qss_path)
        if self.store.wallpaper:
            qss += "\n" + WALLPAPER_QSS
        QApplication.instance().setStyleSheet(qss)
        self.style_btn.setText(f"风格：{STYLE_NAMES[mode]}")
        self.style_btn.setToolTip("点击切换 深色现代 / 浅色现代 风格")

    def _show_guide(self):
        dlg = InfoMiniDialog(self)
        dlg.exec()

    def _apply_wallpaper(self):
        path = (self.store.wallpaper or "").strip()
        lower = path.lower()
        self._clear_video_wallpaper()
        if path and lower.endswith(".gif"):
            self._setup_gif_wallpaper(path)
        elif path and HAS_MEDIA and lower.endswith((".mp4", ".webm", ".mov", ".m4v")):
            self._setup_video_wallpaper(path)
        elif path:
            self._setup_image_wallpaper(path)
        # 重新应用样式：有壁纸时叠加“壁纸模式”亚克力，没壁纸时恢复默认亚克力
        self._apply_style(self.store.style_mode)

    def _setup_image_wallpaper(self, path: str):
        self._clear_video_wallpaper()
        pm = QPixmap(path)
        if pm.isNull():
            # 图片加载失败时回退到 QSS 背景，避免无背景
            style = (
                '#appShell { background-image: url("'
                + path.replace("\\", "/")
                + '"); background-repeat: no-repeat; background-position: center; background-color: transparent; }'
            )
            self.centralWidget().setStyleSheet(style)
            return
        label = QLabel(self.centralWidget())
        label.setObjectName("wallpaperImage")
        label.setScaledContents(True)
        label.setGeometry(self.centralWidget().rect())
        label.setPixmap(pm)
        label.lower()
        label.show()
        self._image_label = label
        self._raise_ui_above_wallpaper()

    def _setup_gif_wallpaper(self, path: str):
        self._clear_video_wallpaper()
        label = QLabel(self.centralWidget())
        label.setObjectName("wallpaperGif")
        label.setScaledContents(True)
        label.setGeometry(self.centralWidget().rect())
        movie = QMovie(path)
        movie.setCacheMode(QMovie.CacheMode.CacheAll)
        label.setMovie(movie)
        label.lower()
        movie.start()
        self._gif_label = label
        self._gif_movie = movie
        self._raise_ui_above_wallpaper()

    def _setup_video_wallpaper(self, path: str):
        self._clear_video_wallpaper()
        if not HAS_MEDIA:
            return
        # 使用 QGraphicsVideoItem + QGraphicsView：
        # 1) 是普通 Qt 控件，可稳定放在主界面下层；
        # 2) 由 QtMultimedia 内部渲染视频，不在 Python 里逐帧转 QImage，
        #    性能远好于 QVideoSink+QLabel。
        scene = QGraphicsScene(self)
        item = QGraphicsVideoItem()
        try:
            item.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        except Exception:
            pass
        scene.addItem(item)

        view = QGraphicsView(scene, self.centralWidget())
        view.setObjectName("wallpaperVideoView")
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setStyleSheet("QGraphicsView { background: transparent; border: none; }")
        view.setGeometry(self.centralWidget().rect())
        view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        view.lower()
        view.show()
        if view.width() > 0 and view.height() > 0:
            item.setSize(QSizeF(view.width(), view.height()))
            scene.setSceneRect(0, 0, view.width(), view.height())
        self._raise_ui_above_wallpaper()

        media = QMediaPlayer(self)
        audio = QAudioOutput(self)
        audio.setVolume(0)
        media.setAudioOutput(audio)
        media.setVideoOutput(item)
        media.setSource(QUrl.fromLocalFile(path))
        def replay(status):
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                media.setPosition(0)
                media.play()
        media.mediaStatusChanged.connect(replay)
        media.play()
        self._video_player = media
        self._video_item = item
        self._video_scene = scene
        self._video_view = view

    def _clear_video_wallpaper(self):
        for attr in ("_video_player", "_video_widget", "_video_sink", "_video_label", "_video_item", "_video_scene", "_video_view", "_gif_movie", "_gif_label", "_image_label"):
            obj = getattr(self, attr, None)
            if obj is not None:
                try:
                    if attr == "_video_player":
                        obj.stop()
                    if attr == "_gif_movie":
                        obj.stop()
                    obj.deleteLater()
                except Exception:
                    pass
                setattr(self, attr, None)
        # 清除之前可能残留的内联背景样式，交回默认 QSS 亚克力
        self.centralWidget().setStyleSheet("")

    def _choose_wallpaper(self):
        from PySide6.QtWidgets import QFileDialog

        LOCAL_TAG = "__local__"
        WEDIR_TAG = "__wedir__"
        CLEAR_TAG = "__clear__"
        LOCAL_LABEL = "📁 选择本地视频 / 图片 / GIF…"
        WEDIR_LABEL = "📂 选择 Wallpaper Engine 壁纸目录…"
        CLEAR_LABEL = "✕ 清除壁纸（恢复默认亚克力）"

        # 自动找 Steam Wallpaper Engine 本地壁纸库
        def detect_we_roots():
            candidates = []
            pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
            pf64 = os.environ.get("ProgramFiles", r"C:\Program Files")
            candidates.append(os.path.join(pf86, "Steam", "steamapps", "workshop", "content", "431960"))
            candidates.append(os.path.join(pf64, "Steam", "steamapps", "workshop", "content", "431960"))
            candidates.append(os.path.expandvars(r"%LOCALAPPDATA%\Steam\steamapps\workshop\content\431960"))
            return [p for p in candidates if os.path.isdir(p)]

        def scan_wallpapers(roots):
            out = []
            for root in roots:
                try:
                    for name in os.listdir(root):
                        d = os.path.join(root, name)
                        if not os.path.isdir(d):
                            continue
                        candidate = None
                        for fn in ("preview.gif", "preview.jpg", "preview.png", "preview.webp"):
                            p2 = os.path.join(d, fn)
                            if os.path.isfile(p2):
                                candidate = p2
                                break
                        if not candidate:
                            for ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"):
                                try:
                                    matches = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(ext)]
                                except OSError:
                                    matches = []
                                if matches:
                                    candidate = matches[0]
                                    break
                        if not candidate:
                            for ext in (".mp4", ".webm", ".mov", ".m4v"):
                                try:
                                    matches = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(ext)]
                                except OSError:
                                    matches = []
                                if matches:
                                    candidate = matches[0]
                                    break
                        if candidate:
                            lower = candidate.lower()
                            is_video = lower.endswith((".mp4", ".webm", ".mov", ".m4v"))
                            is_gif = lower.endswith(".gif")
                            kind = "动态视频" if is_video else ("动态预览GIF" if is_gif else "预览/静态图")
                            label = f"{name}  ({kind}: {os.path.basename(candidate)})"
                            out.append((label, candidate))
                except OSError:
                    continue
            return out

        roots = detect_we_roots()
        while True:
            items = [(LOCAL_LABEL, LOCAL_TAG)]
            if self.store.wallpaper:
                items.insert(0, (CLEAR_LABEL, CLEAR_TAG))
            items.extend(scan_wallpapers(roots))
            if not roots:
                items.append((WEDIR_LABEL, WEDIR_TAG))

            labels = [x[0] for x in items]
            default_index = 1 if self.store.wallpaper else 0
            choice, ok = QInputDialog.getItem(self, "选择壁纸", "壁纸（支持 mp4 / webm / mov / m4v / gif / 图片）：", labels, default_index, False)
            if not ok:
                return

            if choice == CLEAR_LABEL:
                self.store.set_wallpaper("")
                self._apply_wallpaper()
                return

            if choice == LOCAL_LABEL:
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "选择壁纸文件",
                    "",
                    "壁纸 (*.mp4 *.webm *.mov *.m4v *.gif *.jpg *.jpeg *.png *.webp *.bmp);;"
                    "视频 (*.mp4 *.webm *.mov *.m4v);;图片 (*.jpg *.jpeg *.png *.webp *.bmp);;GIF (*.gif)",
                )
                if path:
                    self.store.set_wallpaper(path)
                    self._apply_wallpaper()
                return

            if choice == WEDIR_LABEL:
                root = QFileDialog.getExistingDirectory(
                    self,
                    "选择 Wallpaper Engine 壁纸目录",
                    "",
                )
                if not root:
                    continue
                roots = [root]
                continue

            for label, path in items:
                if label == choice:
                    self.store.set_wallpaper(path)
                    self._apply_wallpaper()
                    QMessageBox.information(
                        self,
                        "壁纸已设置",
                        f"已使用壁纸：\n{choice}\n\n动态视频壁纸会在桌面端播放；静态图作为玻璃背景显示。",
                    )
                    return

    def _toggle_style(self):
        new_mode = STYLE_LIGHT if self.store.style_mode == STYLE_DARK else STYLE_DARK
        self.store.set_style_mode(new_mode)
        self._apply_style(new_mode)

    def _change_animation_level(self, index: int):
        level = self.anim_combo.itemData(index)
        self.store.set_animation_level(level)
        self._update_window_effect()
        # 立即刷新当前页进度条，关闭动画时直接跳到最终值
        for i in range(self.right_layout.count()):
            w = self.right_layout.itemAt(i).widget()
            if isinstance(w, TierPage):
                w.update_progress()
