"""壁纸层深模块：本地图片 / GIF / 视频壁纸的加载、布局与选择。

对外接口只暴露一个 WallpaperManager：
- apply()          按 ProgressStore 中保存的壁纸路径加载并叠加壁纸 QSS
- clear()          清除所有壁纸层与残留内联样式
- layout()         主窗口 resize 时同步壁纸层几何
- raise_ui()       把主界面控件抬到壁纸层上方
- choose()         打开壁纸选择对话框（本地文件 / Wallpaper Engine）

这个模块不关心业务逻辑；主窗口只负责在 resize / 初始化 / 用户操作时调用。
"""

import os

from PySide6.QtCore import QSizeF, Qt, QUrl
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QInputDialog,
    QLabel,
    QMessageBox,
)

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
    HAS_MEDIA = True
except Exception:
    HAS_MEDIA = False


class WallpaperManager:
    """管理器：所有属性存放在本对象上，不污染主窗口命名空间。"""

    _LAYER_ATTRS = (
        "_video_player",
        "_video_widget",
        "_video_sink",
        "_video_label",
        "_video_item",
        "_video_scene",
        "_video_view",
        "_gif_movie",
        "_gif_label",
        "_image_label",
    )

    def __init__(self, window):
        self.window = window
        self.store = window.store
        for attr in self._LAYER_ATTRS:
            setattr(self, attr, None)

    # ---------- 通用 ----------
    def layout(self):
        rect = self.window.centralWidget().rect()
        for attr in ("_video_view", "_video_label", "_gif_label", "_image_label"):
            layer = getattr(self, attr, None)
            if layer is not None:
                layer.setGeometry(rect)
        item = self._video_item
        if item is not None:
            item.setSize(QSizeF(rect.width(), rect.height()))
            scene = self._video_scene
            if scene is not None:
                scene.setSceneRect(0, 0, rect.width(), rect.height())

    def raise_ui(self):
        """确保主界面控件永远在壁纸层上方。"""
        if hasattr(self.window, "body"):
            self.window.body.raise_()
        if hasattr(self.window, "title_bar"):
            self.window.title_bar.raise_()

    def apply(self):
        path = (self.store.wallpaper or "").strip()
        lower = path.lower()
        self.clear()
        if path and lower.endswith(".gif"):
            self._setup_gif_wallpaper(path)
        elif path and HAS_MEDIA and lower.endswith((".mp4", ".webm", ".mov", ".m4v")):
            self._setup_video_wallpaper(path)
        elif path:
            self._setup_image_wallpaper(path)
        # 重新应用样式：有壁纸时叠加“壁纸模式”亚克力，没壁纸时恢复默认亚克力
        self.window._apply_style(self.store.style_mode)

    def clear(self):
        for attr in self._LAYER_ATTRS:
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
        self.window.centralWidget().setStyleSheet("")

    # ---------- 图片 / GIF / 视频 ----------
    def _setup_image_wallpaper(self, path: str):
        self.clear()
        pm = QPixmap(path)
        if pm.isNull():
            # 图片加载失败时回退到 QSS 背景，避免无背景
            style = (
                '#appShell { background-image: url("'
                + path.replace("\\", "/")
                + '"); background-repeat: no-repeat; background-position: center; background-color: transparent; }'
            )
            self.window.centralWidget().setStyleSheet(style)
            return
        label = QLabel(self.window.centralWidget())
        label.setObjectName("wallpaperImage")
        label.setScaledContents(True)
        label.setGeometry(self.window.centralWidget().rect())
        label.setPixmap(pm)
        label.lower()
        label.show()
        self._image_label = label
        self.raise_ui()

    def _setup_gif_wallpaper(self, path: str):
        self.clear()
        from PySide6.QtGui import QMovie

        label = QLabel(self.window.centralWidget())
        label.setObjectName("wallpaperGif")
        label.setScaledContents(True)
        label.setGeometry(self.window.centralWidget().rect())
        movie = QMovie(path)
        movie.setCacheMode(QMovie.CacheMode.CacheAll)
        label.setMovie(movie)
        label.lower()
        movie.start()
        self._gif_label = label
        self._gif_movie = movie
        self.raise_ui()

    def _setup_video_wallpaper(self, path: str):
        self.clear()
        if not HAS_MEDIA:
            return
        # 使用 QGraphicsVideoItem + QGraphicsView：
        # 1) 是普通 Qt 控件，可稳定放在主界面下层；
        # 2) 由 QtMultimedia 内部渲染视频，不在 Python 里逐帧转 QImage，
        #    性能远好于 QVideoSink+QLabel。
        scene = QGraphicsScene(self.window)
        item = QGraphicsVideoItem()
        try:
            item.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        except Exception:
            pass
        scene.addItem(item)

        view = QGraphicsView(scene, self.window.centralWidget())
        view.setObjectName("wallpaperVideoView")
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setStyleSheet("QGraphicsView { background: transparent; border: none; }")
        view.setGeometry(self.window.centralWidget().rect())
        view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        view.lower()
        view.show()
        if view.width() > 0 and view.height() > 0:
            item.setSize(QSizeF(view.width(), view.height()))
            scene.setSceneRect(0, 0, view.width(), view.height())
        self.raise_ui()

        media = QMediaPlayer(self.window)
        audio = QAudioOutput(self.window)
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

    # ---------- 选择 ----------
    def choose(self):

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

        window = self.window
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
            choice, ok = QInputDialog.getItem(
                window,
                "选择壁纸",
                "壁纸（支持 mp4 / webm / mov / m4v / gif / 图片）：",
                labels,
                default_index,
                False,
            )
            if not ok:
                return

            if choice == CLEAR_LABEL:
                self.store.set_wallpaper("")
                self.apply()
                return

            if choice == LOCAL_LABEL:
                path, _ = QFileDialog.getOpenFileName(
                    window,
                    "选择壁纸文件",
                    "",
                    "壁纸 (*.mp4 *.webm *.mov *.m4v *.gif *.jpg *.jpeg *.png *.webp *.bmp);;"
                    "视频 (*.mp4 *.webm *.mov *.m4v);;图片 (*.jpg *.jpeg *.png *.webp *.bmp);;GIF (*.gif)",
                )
                if path:
                    self.store.set_wallpaper(path)
                    self.apply()
                return

            if choice == WEDIR_LABEL:
                root = QFileDialog.getExistingDirectory(
                    window,
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
                    self.apply()
                    QMessageBox.information(
                        window,
                        "壁纸已设置",
                        f"已使用壁纸：\n{choice}\n\n动态视频壁纸会在桌面端播放；静态图作为玻璃背景显示。",
                    )
                    return
