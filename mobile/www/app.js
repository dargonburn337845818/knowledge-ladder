/* 动态熵减拆题引导：纯本地状态机 + 是/否/不确定 + 人类探测器 */
(function () {
  const DIRECTION_TEXT = {
    "编码压缩": "重复信息提前存好；把状态压缩成更小表示；用预处理换取更快查询。",
    "传播松弛": "沿着依赖关系一层层推；状态从前驱传递过来；让信息按顺序走到终点。",
    "剪枝决策": "排除大批不可能候选；利用单调性一次砍掉一半；先判可行再找最优。",
    "变换域映射": "换一个坐标系；做差分、对偶、重表述；把纠缠结构转成熟悉模型。"
  };

  const engine = window.EntropyEngine ? window.EntropyEngine.create(window.ENTROPY_DATA || {}) : null;
  let state = {
    weights: engine ? engine.initialWeights() : [],
    asked: [],
    history: [],
    mode: "baseline",
    currentQuestion: null,
    lastSurprise: 1,
    anomalyFlag: false
  };

  const stage = document.getElementById("stage");
  const stepCount = document.getElementById("stepCount");

  function showError(msg) {
    stage.innerHTML = `<div class="card"><div class="card-title">数据错误</div><div class="card-hint">${msg}</div></div>`;
  }

  function entropy() {
    return engine ? engine.entropy(state.weights) : 0;
  }

  const HEURISTICS = (window.ENTROPY_DATA && window.ENTROPY_DATA.heuristics) || { directions: [] };
  const TEACHER_CONSENSUS = (window.ENTROPY_DATA && window.ENTROPY_DATA.teacher_consensus) || { themes: [] };

  function heuristicObj(name) {
    return HEURISTICS.directions.find(h => h.id === name) || null;
  }

  function teacherThemesForDirection(dir) {
    return (TEACHER_CONSENSUS.themes || [])
      .filter(t => t.direction === dir)
      .sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
      .slice(0, 3);
  }

  function topTeacherThemes(n) {
    if (!engine) return [];
    const probs = engine.directionProbs(state.weights);
    const scored = (TEACHER_CONSENSUS.themes || [])
      .filter(t => probs[t.direction] != null)
      .map(t => ({ t, score: probs[t.direction] * (t.confidence || 0.5) }));
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, n).map(x => x.t);
  }

  function fillTemplate(tpl, top) {
    if (!tpl) return "";
    const names = top.map(t => t.algorithm_name);
    return tpl
      .replace(/\{top1\}/g, names[0] || "当前候选")
      .replace(/\{top2\}/g, names[1] || "后续候选")
      .replace(/\{top3\}/g, names[2] || "另一个候选");
  }

  function saveSnapshot() {
    state.history.push({
      weights: state.weights.slice(),
      asked: state.asked.slice(),
      mode: state.mode,
      currentQuestion: state.currentQuestion
    });
  }

  function goBack() {
    if (state.mode === "question" && state.history.length > 0) {
      const snap = state.history.pop();
      state.weights = snap.weights;
      state.asked = snap.asked;
      state.currentQuestion = snap.currentQuestion;
      state.mode = "question";
      renderQuestion();
      return;
    }
    if (state.mode === "direction") {
      state.mode = "finished";
      renderFinish();
      return;
    }
    if (state.mode === "finished" && state.history.length > 0) {
      const snap = state.history.pop();
      state.weights = snap.weights;
      state.asked = snap.asked;
      state.currentQuestion = snap.currentQuestion;
      state.mode = "question";
      renderQuestion();
      return;
    }
  }

  function restart() {
    state = {
      weights: engine ? engine.initialWeights() : [],
      asked: [],
      history: [],
      mode: "baseline",
      currentQuestion: null,
      lastSurprise: 1,
      anomalyFlag: false
    };
    renderBaseline();
  }

  function renderBaseline() {
    stepCount.style.display = "";
    stepCount.textContent = "基线";
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">先确认基线暴力</div>
        <div class="card-hint">这一步不看方向，只看你现在的朴素方案</div>
        <div style="font-size:18px;margin-bottom:18px;">你已经先想了一个暴力/模拟方案吗？</div>
        <div class="options">
          <button class="option" data-answer="yes">是 <small>我已经有最直接的做法</small></button>
          <button class="option" data-answer="no">否 <small>我还没写/想暴力方案</small></button>
          <button class="option" data-answer="uncertain">不确定 <small>介于两者之间</small></button>
        </div>
        <div id="baselineWarn" class="warn-text" style="display:none;margin-top:14px;">
          请先写一个最直接的暴力/模拟方案，再继续拆题。
        </div>
      </div>
    `;
    stage.querySelectorAll(".option").forEach(btn => {
      btn.addEventListener("click", () => {
        const a = btn.dataset.answer;
        if (a === "yes") {
          state.mode = "question";
          renderQuestion();
        } else {
          const warn = document.getElementById("baselineWarn");
          if (warn) warn.style.display = "block";
        }
      });
    });
  }

  function questionText(fid) {
    const f = engine.features.find(x => x.id === fid);
    return f ? f.question : "";
  }

  function renderQuestion() {
    if (!engine) return showError("未加载熵减引擎");
    const stop = engine.shouldStop(state.weights, state.asked);
    if (stop.stop) {
      renderFinish();
      return;
    }
    const next = engine.chooseNext(state.weights, state.asked);
    if (!next.id) {
      renderFinish();
      return;
    }
    state.currentQuestion = next.id;
    stepCount.style.display = "";
    stepCount.textContent = "熵减";

    const hasBack = state.history.length > 0;
    const top3 = engine.realtimeTop(state.weights);
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">动态拆题</div>
        <div class="card-hint">只回答一个问题，机器会选最值得问的</div>
        <div class="question-text">${questionText(next.id)}</div>
        <div class="realtime-algos">
          <div class="realtime-label">当前候选</div>
          ${top3.map(t => `<span class="algo-chip">${t.algorithm_name} <b>${(t.weight * 100).toFixed(1)}%</b></span>`).join("")}
        </div>
        <div class="options">
          <button class="option" data-answer="yes">是 <small>符合这个特征</small></button>
          <button class="option" data-answer="no">否 <small>不符合这个特征</small></button>
          <button class="option" data-answer="uncertain">不确定 <small>弱证据，各算一半</small></button>
        </div>
        <button class="action-btn" id="detectorBtn" style="width:100%;margin-top:4px;">我感觉不对劲</button>
        <div id="detectorHint" class="warn-text" style="display:none;margin-top:10px;">
          先再回答 1–2 个问题，让范围收小；如果仍然觉得不对，再点“我感觉不对劲”。
        </div>
        ${state.anomalyFlag ? '<div class="muted-text" style="margin-top:10px;">刚才的回答有点反直觉，你可以持续留意。</div>' : ""}
        <div style="display:flex;gap:8px;margin-top:16px;">
          ${hasBack ? '<button class="think-back" id="backBtn" style="flex:1;">‹ 上一步</button>' : ""}
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
      </div>
    `;

    stage.querySelectorAll(".option").forEach(btn => {
      btn.addEventListener("click", () => handleAnswer(btn.dataset.answer));
    });
    document.getElementById("detectorBtn").addEventListener("click", handleDetector);
    const backBtn = document.getElementById("backBtn");
    if (backBtn) backBtn.addEventListener("click", goBack);
    document.getElementById("restartBtn").addEventListener("click", restart);
  }

  function handleAnswer(answer) {
    const fid = state.currentQuestion;
    if (!fid) return;
    saveSnapshot();
    const surprise = engine.answerProbability(state.weights, fid, answer);
    state.weights = engine.posterior(state.weights, fid, answer);
    state.asked = state.asked.concat([fid]);
    state.lastSurprise = surprise;
    if (surprise < (engine.params.anomaly_surprise_threshold || 0.85)) {
      state.anomalyFlag = true;
    }
    const stop = engine.shouldStop(state.weights, state.asked);
    if (stop.stop) renderFinish();
    else renderQuestion();
  }

  function handleDetector() {
    const thr = engine.params.detector_entropy_threshold == null ? 0.3 : engine.params.detector_entropy_threshold;
    if (entropy() < thr) {
      renderFinish();
    } else {
      const hint = document.getElementById("detectorHint");
      if (hint) hint.style.display = "block";
    }
  }

  function renderFinish() {
    state.mode = "finished";
    stepCount.style.display = "none";
    const probs = engine.directionProbs(state.weights);
    const dirs = Object.keys(probs).sort((a, b) => probs[b] - probs[a]);
    const algos = engine.topAlgorithms(state.weights);
    const topThemes = topTeacherThemes(2);
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">四个方向</div>
        <div class="card-hint">机器已收敛；选一个你直觉最强的方向</div>
        <div class="options">
          ${dirs.map(d => `
            <button class="option direction-option" data-dir="${d}">
              ${d}
              <small>${(probs[d] * 100).toFixed(0)}% 方向权重</small>
            </button>
          `).join("")}
        </div>
        <div class="algo-list">
          <div class="algo-list-title">候选算法权重</div>
          ${algos.length ? algos.map(a => `
            <div class="algo-row"><span>${a.algorithm_name}</span><b>${(a.weight * 100).toFixed(1)}%</b></div>
          `).join("") : '<div class="muted-text">当前候选都低于阈值，请点击方向继续。</div>'}
        </div>
        ${topThemes.length ? `
          <div class="heuristic-block">
            <div class="algo-list-title">教师共识线索</div>
            ${topThemes.map(t => `
              <div style="margin-top:8px;border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">
                <div style="font-weight:600;">${t.name}</div>
                <div class="muted-text">触发：${t.trigger || ""}</div>
                <div class="muted-text">动作：${t.action || ""}</div>
                ${t.counterexample ? `<div class="muted-text">失效：${t.counterexample}</div>` : ""}
              </div>
            `).join("")}
          </div>
        ` : ""}
        <div style="display:flex;gap:8px;margin-top:8px;">
          ${state.history.length ? '<button class="think-back" id="backBtn" style="flex:1;">‹ 上一步</button>' : ""}
          <button class="think-back" id="debugBtn" style="flex:1;">调试信息</button>
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
        <div id="debugPanel" class="debug-text" style="display:none;margin-top:12px;">
          当前熵：${entropy().toFixed(3)}<br>
          已问问题：${state.asked.length}<br>
          候选算法：${state.weights.length}
        </div>
      </div>
    `;
    stage.querySelectorAll("[data-dir]").forEach(btn => {
      btn.addEventListener("click", () => renderDirection(btn.dataset.dir));
    });
    document.getElementById("restartBtn").addEventListener("click", restart);
    const backBtn = document.getElementById("backBtn");
    if (backBtn) backBtn.addEventListener("click", goBack);
    document.getElementById("debugBtn").addEventListener("click", () => {
      const panel = document.getElementById("debugPanel");
      if (panel) panel.style.display = panel.style.display === "none" ? "block" : "none";
    });
  }

  function renderDirection(dir) {
    state.mode = "direction";
    stepCount.style.display = "none";
    const h = heuristicObj(dir);
    const top = engine.realtimeTop(state.weights, 3);
    const dynamic = fillTemplate(h ? h.dynamic_template : "", top);
    const body = h ? `${h.heuristic}<br><br>${dynamic}` : (DIRECTION_TEXT[dir] || "");
    const questions = h ? h.self_questions || [] : [];
    const dirThemes = teacherThemesForDirection(dir);
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">${dir}</div>
        <div class="card-hint">顺着这个方向想，但别急着背名字</div>
        <div class="direction-body">${body}</div>
        ${questions.length ? `
          <div class="heuristic-block">
            <div class="algo-list-title">该问自己</div>
            ${questions.map(q => `<div class="muted-text" style="margin-top:4px;">· ${q}</div>`).join("")}
          </div>
        ` : ""}
        ${dirThemes.length ? `
          <div class="heuristic-block">
            <div class="algo-list-title">教师共识线索</div>
            ${dirThemes.map(t => `
              <div style="margin-top:8px;border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">
                <div style="font-weight:600;">${t.name}</div>
                <div class="muted-text">触发：${t.trigger || ""}</div>
                <div class="muted-text">动作：${t.action || ""}</div>
                ${t.counterexample ? `<div class="muted-text">失效：${t.counterexample}</div>` : ""}
              </div>
            `).join("")}
          </div>
        ` : ""}
        <div style="display:flex;gap:8px;margin-top:16px;">
          <button class="think-back" id="backBtn" style="flex:1;">‹ 返回方向</button>
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
      </div>
    `;
    document.getElementById("backBtn").addEventListener("click", goBack);
    document.getElementById("restartBtn").addEventListener("click", restart);
  }

  function render() {
    if (!engine) return showError("未加载熵减引擎");
    if (state.mode === "baseline") renderBaseline();
    else if (state.mode === "question") renderQuestion();
    else if (state.mode === "finished") renderFinish();
    else if (state.mode === "direction") renderDirection("编码压缩");
  }

  // ---------- 风格切换：保留原有 ----------
  const THEME_KEY = "kl_mobile_theme";
  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    if (localStorage.getItem(THEME_KEY) === "editorial") {
      document.body.classList.add("theme-editorial");
    }
    themeToggle.addEventListener("click", () => {
      const on = document.body.classList.toggle("theme-editorial");
      localStorage.setItem(THEME_KEY, on ? "editorial" : "glass");
    });
  }

  renderBaseline();
})();

/* ---------- parallax editorial rAF ---------- */
let peTicking = false;
function peOnScroll() {
  if (peTicking) return;
  peTicking = true;
  requestAnimationFrame(() => {
    const y = window.scrollY || 0;
    document.querySelectorAll("[data-parallax]").forEach(el => {
      const rate = parseFloat(el.dataset.parallax || "0");
      el.style.setProperty("--pe-y", `${-y * rate}px`);
    });
    peTicking = false;
  });
}
window.addEventListener("scroll", peOnScroll, { passive: true });
window.addEventListener("resize", peOnScroll);
peOnScroll();
