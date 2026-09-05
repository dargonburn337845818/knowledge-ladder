/* 动态熵减拆题引导：纯本地状态机 + 是/否/不确定 + 人类探测器 */
(function () {
  const engine = window.EntropyEngine ? window.EntropyEngine.create(window.ENTROPY_DATA || {}) : null;
  let state = {
    weights: engine ? engine.initialWeights() : [],
    asked: [],
    history: [],
    mode: "question",
    currentQuestion: null,
    lastSurprise: 1,
    anomalyFlag: false,
    lastInsight: null,
    lastAnswered: null
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
  const DIRECTION_CONTENT = (window.ENTROPY_DATA && window.ENTROPY_DATA.direction_content) || { directions: [] };
  const DYNAMIC_INSIGHTS = (window.ENTROPY_DATA && window.ENTROPY_DATA.dynamic_insights) || { features: {}, directions: {} };

  function directionContentByName(name) {
    return DIRECTION_CONTENT.directions.find(d => d.title === name) || null;
  }

  function heuristicObj(name) {
    return HEURISTICS.directions.find(h => h.id === name) || null;
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
      mode: "question",
      currentQuestion: null,
      lastSurprise: 1,
      anomalyFlag: false,
      lastInsight: null,
      lastAnswered: null
    };
    renderQuestion();
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
    stepCount.textContent = "拆题";

    const hasBack = state.history.length > 0;
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">这个问题符合吗？</div>
        <div class="question-text">${questionText(next.id)}</div>
        <div class="options">
          <button class="option" data-answer="yes">是</button>
          <button class="option" data-answer="no">否</button>
          <button class="option" data-answer="uncertain">不确定</button>
        </div>
        <button class="action-btn" id="detectorBtn" style="width:100%;margin-top:4px;">不像？再想想</button>
        <div id="detectorHint" class="warn-text" style="display:none;margin-top:10px;">
          卡住很正常，先挑一个能确定的信号回答；没把握就选“不确定”。
        </div>
        ${state.asked.length ? `<div class="muted-text" style="margin-top:8px;">已确认 ${state.asked.length} 个信号。</div>` : ""}
        ${state.anomalyFlag ? '<div class="muted-text" style="margin-top:10px;">刚才有点反常。</div>' : ""}
        ${state.lastInsight ? `<div class="insight-text" style="margin-top:10px;">点拨：${state.lastInsight}</div>` : ""}
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
    const insightEntry = (DYNAMIC_INSIGHTS.features || {})[fid] || {};
    state.lastAnswered = fid;
    state.lastInsight = insightEntry[answer] || "";
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
    if (!dirs.length) {
      stage.innerHTML = `
        <div class="card">
          <div class="card-title">暂无方向</div>
          <div class="card-hint">暂时没有收敛方向，重新开始。</div>
          <button class="restart-btn" id="restartBtn" style="margin-top:12px;">重新开始</button>
        </div>
      `;
      document.getElementById("restartBtn").addEventListener("click", restart);
      return;
    }
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">选一个方向</div>
        <div class="card-hint">按当前信息的最可能程度排序；点进去看方向点拨。</div>
        ${state.lastInsight ? `<div class="insight-text" style="margin-bottom:12px;">点拨：${state.lastInsight}</div>` : ""}
        <div class="options">
          ${dirs.map(d => `
            <button class="option direction-choice" data-dir="${d}">
              ${d}　${Math.round(probs[d] * 100)}%
            </button>
          `).join("")}
        </div>
        <div style="display:flex;gap:8px;margin-top:8px;">
          ${state.history.length ? '<button class="think-back" id="backBtn" style="flex:1;">‹ 上一步</button>' : ""}
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
      </div>
    `;
    stage.querySelectorAll(".direction-choice").forEach(btn => {
      btn.addEventListener("click", () => renderDirection(btn.dataset.dir));
    });
    document.getElementById("restartBtn").addEventListener("click", restart);
    const backBtn = document.getElementById("backBtn");
    if (backBtn) backBtn.addEventListener("click", goBack);
  }

  function renderDirection(dir) {
    state.mode = "direction";
    stepCount.style.display = "none";
    const d = directionContentByName(dir);
    if (d) {
      stage.innerHTML = `
        <div class="card">
          <div class="card-title">你选择：${dir}</div>
          <div class="card-hint">${d.value}</div>
          ${d.nudge ? `<div class="nudge-text">一句话点拨：${d.nudge}</div>` : ""}
          ${(DYNAMIC_INSIGHTS.directions || {})[dir] ? `<div class="insight-text" style="margin-top:10px;">深入点拨：${(DYNAMIC_INSIGHTS.directions || {})[dir]}</div>` : ""}
          <div class="card-hint">常见信号：${(d.signal_keywords || []).slice(0, 3).join("、")}</div>
          <div style="display:flex;gap:8px;margin-top:16px;">
            <button class="think-back" id="backBtn" style="flex:1;">‹ 返回选择</button>
            <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
          </div>
        </div>
      `;
      document.getElementById("backBtn").addEventListener("click", goBack);
      document.getElementById("restartBtn").addEventListener("click", restart);
      return;
    }
    // 兜底：旧启发式详情
    const h = heuristicObj(dir);
    const firstAction = h && h.next_actions && h.next_actions[0] ? h.next_actions[0] : "";
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">你选择：${dir}</div>
        <div class="card-hint">先做一句</div>
        ${firstAction ? `<div class="direction-body">${firstAction}</div>` : ""}
        <div style="display:flex;gap:8px;margin-top:16px;">
          <button class="think-back" id="backBtn" style="flex:1;">‹ 返回选择</button>
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
      </div>
    `;
    document.getElementById("backBtn").addEventListener("click", goBack);
    document.getElementById("restartBtn").addEventListener("click", restart);
  }

  function render() {
    if (!engine) return showError("未加载熵减引擎");
    else if (state.mode === "question") renderQuestion();
    else if (state.mode === "finished") renderFinish();
    else if (state.mode === "direction") renderDirection("编码压缩");
  }

  renderQuestion();
})();
