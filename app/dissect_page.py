"""桌面端动态熵减拆题页：基线暴力 → 单一问题流 → 四方向引导。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from entropy_engine import EntropyEngine


class DissectPage(QWidget):
    """桌面端动态熵减拆题页：基线暴力 -> 单一问题流 -> 四方向引导。"""

    VAGUE_TEXT = {
        "编码压缩": "重复信息提前存好；把状态压缩成更小表示；用预处理换取更快查询。",
        "传播松弛": "沿着依赖关系一层层推；状态从前驱传递过来；让信息按顺序走到终点。",
        "剪枝决策": "排除大批不可能候选；利用单调性一次砍掉一半；先判可行再找最优。",
        "变换域映射": "换一个坐标系；做端点变化、对偶、重表述；把纠缠结构转成熟悉模型。",
    }

    def __init__(self, on_back=None, parent=None, store=None):
        super().__init__(parent)
        self.on_back = on_back
        self.store = store
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
        self._add_title("先写暴力")
        self._add_body("写一个最直接的暴力/模拟方案")
        self._add_button("写好了", lambda: self._baseline_answer(True))
        self._add_button("还没写", lambda: self._baseline_answer(False))
        self._baseline_warning = QLabel("先写，再继续。")
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
        self.step_label.setText("拆题")
        self._add_title("这个问题符合吗？")
        self._add_body(feature["question"] if feature else fid)
        self._add_button("是", lambda: self._handle_answer("yes"))
        self._add_button("否", lambda: self._handle_answer("no"))
        self._add_button("不确定", lambda: self._handle_answer("uncertain"))
        self._add_button("不像？再想想", self._handle_detector, "opPill")
        self._detector_hint = QLabel("")
        self._detector_hint.setObjectName("dissectHint")
        self._detector_hint.setWordWrap(True)
        self._detector_hint.hide()
        self.content_layout.addWidget(self._detector_hint)
        if self.anomaly_flag:
            note = QLabel("刚才有点反常。")
            note.setObjectName("dissectHint")
            note.setWordWrap(True)
            self.content_layout.addWidget(note)
        if self.history:
            self._add_button("‹ 上一步", self._go_back, "dissectBack")
        self._add_button("重新开始", self._reset, "dissectRestart")
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
            self._detector_hint.setText("先回答一两个，再想。")
            self._detector_hint.show()

    # ---------- Finish ----------
    def _render_finish(self):
        self.mode = "finished"
        self.step_label.setText("")
        probs = self.engine.direction_probs(self.weights)
        top = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        if not top:
            self._add_body("暂时没有收敛方向，重新开始。")
            self._add_button("重新开始", self._reset, "dissectRestart")
            return
        # 机器根据熵/方向概率自动给出最可能方向，不再让用户“选”。
        self._current_direction = top[0][0]
        self._render_direction()

    def _toggle_debug(self):
        if not hasattr(self, "_debug_label"):
            return
        if self._debug_label.isVisible():
            self._debug_label.hide()
        else:
            lines = [
                f"当前熵：{self.engine.entropy(self.weights):.3f}",
                f"已问问题数：{len(self.asked)}",
                f"候选数：{len(self.weights)}",
            ]
            self._debug_label.setText("\n".join(lines))
            self._debug_label.show()

    def _open_direction(self, direction):
        self.mode = "direction"
        self._current_direction = direction
        self._render()

    # ---------- 卡点自查 ----------
    def _card_points(self):
        return self.engine.heuristics.get("card_points", []) or []

    def _card_name(self, card_id):
        for cp in self._card_points():
            if cp.get("id") == card_id:
                return cp.get("name", card_id)
        return card_id

    def _on_card_clicked(self, card_id):
        card = next((c for c in self._card_points() if c.get("id") == card_id), None)
        if card and hasattr(self, "_card_hint_label"):
            self._card_hint_label.setText(card.get("hint", ""))
            self._card_hint_label.show()
        if self.store is not None:
            self.store.add_card_record(card_id)
            self._refresh_card_summary()

    def _refresh_card_summary(self):
        if not hasattr(self, "_card_summary_label"):
            return
        if self.store is None:
            self._card_summary_label.setText("最近：暂无")
            return
        counts = self.store.card_record_counts(10)
        parts = [f"{self._card_name(c)}×{n}" for c, n in counts.items()]
        self._card_summary_label.setText("最近：" + " ".join(parts) if parts else "最近：暂无")

    # ---------- Direction ----------
    def _render_direction(self):
        direction = getattr(self, "_current_direction", "编码压缩")
        self.step_label.setText("")
        self._add_title(f"最可能：{direction}")
        self._add_hint("先做一句")
        h = self.engine.heuristic_direction(direction)
        if h:
            actions = h.get("next_actions", [])
            if actions:
                self._add_body(f"先做：{actions[0]}")
            else:
                self._add_body(self.VAGUE_TEXT.get(direction, ""))
        else:
            self._add_body(self.VAGUE_TEXT.get(direction, ""))

        card_points = self._card_points()
        if card_points:
            self._add_title("卡点自查")
            for cp in card_points:
                self._add_button(
                    cp.get("name", cp["id"]),
                    lambda c=cp["id"]: self._on_card_clicked(c),
                    "dissectBack",
                )
            self._card_hint_label = QLabel("")
            self._card_hint_label.setObjectName("dissectThinkCard")
            self._card_hint_label.setWordWrap(True)
            self._card_hint_label.hide()
            self.content_layout.addWidget(self._card_hint_label)
            self._card_summary_label = QLabel("")
            self._card_summary_label.setObjectName("dissectHint")
            self._card_summary_label.setWordWrap(True)
            self.content_layout.addWidget(self._card_summary_label)
            self._refresh_card_summary()

        probs = self.engine.direction_probs(self.weights)
        others = [name for name, _ in sorted(probs.items(), key=lambda kv: kv[1], reverse=True) if name != direction][:2]
        for other in others:
            btn = QPushButton(f"看别的：{other}")
            btn.setObjectName("dissectBack")
            btn.clicked.connect(lambda checked=False, o=other: self._open_direction(o))
            self.content_layout.addWidget(btn)

        self._add_button("状态", self._toggle_debug, "dissectBack")
        self._debug_label = QLabel("")
        self._debug_label.setObjectName("dissectHint")
        self._debug_label.setWordWrap(True)
        self._debug_label.hide()
        self.content_layout.addWidget(self._debug_label)
        self._add_button("重新开始", self._reset, "dissectRestart")
        self.content_layout.addStretch(1)
