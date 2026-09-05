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

from .teacher_consensus import themes_for_direction, top_themes


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
        self._add_title("先想暴力方案")
        self._add_hint("先写一个最直接的暴力/模拟方案，再继续。")
        self._add_body("你已经想好最直接的暴力做法了吗？")
        self._add_button("是（已经想了）", lambda: self._baseline_answer(True))
        self._add_button("否（还没想）", lambda: self._baseline_answer(False))
        self._add_button("不确定", lambda: self._baseline_answer(False))
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
        self._add_title("下一步")
        self._add_hint("这个问题符合你的题吗？")
        self._add_body(feature["question"] if feature else fid)
        top3 = self.engine.realtime_top(self.weights)
        if top3:
            rt = QLabel("目前更像： " + "   ".join(f"{a['algorithm_name']} {a['weight']*100:.1f}%" for a in top3))
            rt.setObjectName("dissectHint")
            rt.setWordWrap(True)
            self.content_layout.addWidget(rt)
        self._add_button("是", lambda: self._handle_answer("yes"))
        self._add_button("否", lambda: self._handle_answer("no"))
        self._add_button("不确定", lambda: self._handle_answer("uncertain"))
        self._add_button("我感觉不对劲", self._handle_detector, "opPill")
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
            self._detector_hint.setText("先再回答 1–2 个问题，让范围收小；如果仍然觉得不对，再点“我感觉不对劲”。")
            self._detector_hint.show()

    # ---------- Finish ----------
    def _render_finish(self):
        self.mode = "finished"
        self.step_label.setText("")
        self._add_title("最可能的方向")
        self._add_hint("选一个最像的方向")
        probs = self.engine.direction_probs(self.weights)
        top = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        for name, prob in top:
            btn = QPushButton(f"{name}    {prob * 100:.0f}%")
            btn.setObjectName("opPill")
            btn.clicked.connect(lambda checked=False, d=name: self._open_direction(d))
            self.content_layout.addWidget(btn)
        algos = self.engine.top_algorithms(self.weights)
        if algos:
            algo_label = QLabel("更像哪类解法\n" + "\n".join(f"{a['algorithm_name']}  {a['weight']*100:.1f}%" for a in algos))
            algo_label.setObjectName("dissectFinal")
            algo_label.setWordWrap(True)
            self.content_layout.addWidget(algo_label)
        self._add_top_teacher_themes()
        self._add_button("重新开始", self._reset, "dissectRestart")
        if self.history:
            self._add_button("‹ 上一步", self._go_back, "dissectBack")
        self._add_button("诊断", self._toggle_debug, "dissectBack")
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
                f"候选数：{len(self.weights)}"
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
        return (tpl.replace("{top1}", names[0] if names else "更像这类")
                    .replace("{top2}", names[1] if len(names) > 1 else "后续候选")
                    .replace("{top3}", names[2] if len(names) > 2 else "另一个候选"))

    def _add_top_teacher_themes(self):
        """在最终页追加跨方向评分最高的这类题常想的点。"""
        themes = top_themes(self.engine.direction_probs(self.weights), n=2)
        if not themes:
            return
        title = QLabel("这类题常想的点")
        title.setObjectName("dissectTitle")
        self.content_layout.addWidget(title)
        for theme in themes:
            lines = [theme.get("name", "")]
            if theme.get("trigger"):
                lines.append(f"触发：{theme['trigger']}")
            if theme.get("action"):
                lines.append(f"动作：{theme['action']}")
            if theme.get("counterexample"):
                lines.append(f"失效：{theme['counterexample']}")
            card = QLabel("\n".join(lines))
            card.setObjectName("dissectThinkCard")
            card.setWordWrap(True)
            self.content_layout.addWidget(card)

    def _add_teacher_themes(self, direction):
        """在方向页追加这类题常想的点：只展示触发条件、动作与失效边界。"""
        themes = themes_for_direction(direction)
        if not themes:
            return
        title = QLabel("这类题常想的点")
        title.setObjectName("dissectTitle")
        self.content_layout.addWidget(title)
        for theme in themes[:3]:
            lines = [theme.get("name", "")]
            if theme.get("trigger"):
                lines.append(f"触发：{theme['trigger']}")
            if theme.get("action"):
                lines.append(f"动作：{theme['action']}")
            if theme.get("counterexample"):
                lines.append(f"失效：{theme['counterexample']}")
            card = QLabel("\n".join(lines))
            card.setObjectName("dissectThinkCard")
            card.setWordWrap(True)
            self.content_layout.addWidget(card)

    def _render_direction(self):
        direction = getattr(self, "_current_direction", "编码压缩")
        self.step_label.setText("")
        self._add_title(direction)
        self._add_hint("按这个方向想，先不背名字")
        h = self.engine.heuristic_direction(direction)
        top = self.engine.realtime_top(self.weights)
        if h:
            dynamic = self._fill_template(h.get("dynamic_template", ""), top)
            text = h.get("heuristic", "") + "\n\n" + dynamic
            self._add_body(text)
            questions = h.get("self_questions", [])
            if questions:
                q_label = QLabel("问自己：\n" + "\n".join(f"· {q}" for q in questions))
                q_label.setObjectName("dissectHint")
                q_label.setWordWrap(True)
                self.content_layout.addWidget(q_label)
        else:
            self._add_body(self.VAGUE_TEXT.get(direction, ""))
        self._add_teacher_themes(direction)
        self._add_button("‹ 返回方向", self._go_back, "dissectBack")
        self._add_button("重新开始", self._reset, "dissectRestart")
        self.content_layout.addStretch(1)
