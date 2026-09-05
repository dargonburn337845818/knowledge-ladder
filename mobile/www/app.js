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
      .replace(/\{top1\}/g, names[0] || "目前更像")
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
        <div class="card-title">先写暴力</div>
        <div style="font-size:18px;margin-bottom:18px;">写一个最直接的暴力/模拟方案</div>
        <div class="options">
          <button class="option" data-answer="yes">写好了</button>
          <button class="option" data-answer="no">还没写</button>
        </div>
        <div id="baselineWarn" class="warn-text" style="display:none;margin-top:14px;">
          先写，再继续。
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
          先回答一两个，再想。
        </div>
        ${state.anomalyFlag ? '<div class="muted-text" style="margin-top:10px;">刚才有点反常。</div>' : ""}
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
    if (dirs.length) {
      renderDirection(dirs[0]);
      return;
    }
    const algos = engine.topAlgorithms(state.weights);
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">最可能的方向</div>
        <div class="card-hint">选一个最像的方向</div>
        <div class="options">
          ${dirs.map(d => `
            <button class="option direction-option" data-dir="${d}">
              ${d}
            </button>
          `).join("")}
        </div>
        <div style="display:flex;gap:8px;margin-top:8px;">
          ${state.history.length ? '<button class="think-back" id="backBtn" style="flex:1;">‹ 上一步</button>' : ""}
          <button class="think-back" id="debugBtn" style="flex:1;">诊断</button>
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
        <div id="debugPanel" class="debug-text" style="display:none;margin-top:12px;">
          当前熵：${entropy().toFixed(3)}<br>
          已问问题：${state.asked.length}<br>
          候选数：${state.weights.length}
          <br>
          ${algos.length ? `<div style="margin-top:6px;">更像哪类解法（仅诊断）</div>` + algos.map(a => `<div>${a.algorithm_name} ${(a.weight * 100).toFixed(1)}%</div>`).join("") : ""}
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
    const firstAction = h && h.next_actions && h.next_actions[0] ? h.next_actions[0] : "";
    const dirThemes = teacherThemesForDirection(dir);
    const signal = dirThemes.length && dirThemes[0]
      ? `如果 ${dirThemes[0].trigger || ""}，就试 ${dirThemes[0].action || ""}`
      : "";
    const probs = engine.directionProbs(state.weights);
    const others = Object.keys(probs).sort((a, b) => probs[b] - probs[a]).filter(x => x !== dir).slice(0, 2);
    stage.innerHTML = `
      <div class="card">
        <div class="card-title">最可能：${dir}</div>
        <div class="card-hint">先做一句</div>
        ${firstAction ? `<div class="direction-body">${firstAction}</div>` : ""}
        ${signal ? `<div class="muted-text" style="margin-top:12px;">${signal}</div>` : ""}
        <div style="display:flex;gap:8px;margin-top:16px;">
          ${others.map(o => `<button class="think-back" id="other-${o}" style="flex:1;">看别的：${o}</button>`).join("")}
          <button class="restart-btn" id="restartBtn" style="flex:1;margin-top:0;">重新开始</button>
        </div>
      </div>
    `;
    others.forEach(o => {
      const btn = document.getElementById("other-" + o);
      if (btn) btn.addEventListener("click", () => renderDirection(o));
    });
    document.getElementById("restartBtn").addEventListener("click", restart);
  }



  function render() {
    if (!engine) return showError("未加载熵减引擎");
    if (state.mode === "baseline") renderBaseline();
    else if (state.mode === "question") renderQuestion();
    else if (state.mode === "finished") renderFinish();
    else if (state.mode === "direction") renderDirection("编码压缩");
  }

  renderBaseline();
})();
