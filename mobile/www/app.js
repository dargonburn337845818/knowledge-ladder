/* 拆题 + 进度：快速拆题，也能勾选掌握、看简洁算法信息 */
(function () {
  const D = window.KNOWLEDGE_DATA;
  const algMap = {};
  (D.algorithms || []).forEach(a => { algMap[a.name] = a; });

  const STORAGE_KEY = "kl_mobile_mastered_v1";
  let mastered = {};
  try {
    mastered = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch (e) {
    mastered = {};
  }

  const OP_DESC = {
    "编码压缩": "减少冗余",
    "传播松弛": "扩散信息",
    "剪枝决策": "缩小搜索",
    "变换域映射": "换个角度",
    "基线/暴力": "没有明显压缩"
  };

  let currentView = "dissect";
  let openTiers = {};

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function saveMastered() { localStorage.setItem(STORAGE_KEY, JSON.stringify(mastered)); }
  function isMastered(id) { return !!mastered[id]; }
  function setMastered(id, value) { mastered[id] = value; saveMastered(); }

  function unique(arr) {
    const seen = new Set(), out = [];
    for (const x of arr) if (x && !seen.has(x)) { seen.add(x); out.push(x); }
    return out;
  }

  function aggregateTagInfo(tag) {
    const ops = [];
    (tag.algorithms || []).forEach(name => {
      const a = algMap[name];
      if (a && a.info) ops.push(...(a.info.ops || []));
    });
    return { ops: unique(ops) };
  }

  function totalTags() {
    return (D.tiers || []).reduce((sum, t) => sum + (t.tags || []).length, 0);
  }

  function masteredCount() {
    let c = 0;
    (D.tiers || []).forEach(t => (t.tags || []).forEach(tag => { if (isMastered(tag.id)) c++; }));
    return c;
  }

  function opCoverage() {
    const counts = {};
    (D.infoOps || []).forEach(op => counts[op] = 0);
    (D.tiers || []).forEach(t => (t.tags || []).forEach(tag => {
      if (!isMastered(tag.id)) return;
      aggregateTagInfo(tag).ops.forEach(op => { if (counts[op] !== undefined) counts[op]++; });
    }));
    return counts;
  }

  // ---------- 拆题页 ----------
  function renderTop() {
    const el = document.getElementById("homeProgress");
    if (el) {
      const total = totalTags(), done = masteredCount();
      el.textContent = `总进度：${done} / ${total}`;
    }
    const box = document.getElementById("opOverview");
    if (box) {
      const counts = {};
      (D.infoOps || []).forEach(op => counts[op] = 0);
      (D.algorithms || []).forEach(a => {
        (a.info && a.info.ops || []).forEach(op => { if (counts[op] !== undefined) counts[op]++; });
      });
      const learned = opCoverage();
      box.innerHTML = (D.infoOps || []).map(op => `
        <div class="op-card">
          <div class="op-name" style="color:${(D.infoOpColors || {})[op] || "#6c8cff"}">${esc(op)}</div>
          <div class="op-desc">${esc(OP_DESC[op] || "")}</div>
          <div class="op-count">已掌握 ${learned[op] || 0}</div>
        </div>
      `).join("");
    }
  }

  const DISSECT_STEPS = [
    {
      key: "shape", title: "1. 数据形状", hint: "数据长在什么结构上？",
      options: [
        { value: "linear", label: "线性", desc: "数组、字符串、区间" },
        { value: "graph", label: "树 / 图", desc: "树、图、网络、依赖" },
        { value: "algebra", label: "数学对象", desc: "数字、集合、异或、多项式" }
      ]
    },
    {
      key: "dynamic", title: "2. 数据是否变化", hint: "运行过程中会修改吗？",
      options: [
        { value: "static", label: "静态", desc: "只读，可预处理" },
        { value: "dynamic", label: "动态", desc: "要实时维护" }
      ]
    },
    {
      key: "metric", title: "3. 运算规则", hint: "合并信息用什么规则？",
      options: [
        { value: "sum", label: "加法 / 最值", desc: "路径、区间和" },
        { value: "xor", label: "异或", desc: "线性基" },
        { value: "conv", label: "卷积 / 计数", desc: "FFT、组合" },
        { value: "bool", label: "可行性", desc: "连通、匹配、2-SAT" },
        { value: "number", label: "数论 / 模", desc: "gcd、同余" },
        { value: "geom", label: "几何", desc: "凸包、距离" }
      ]
    },
    {
      key: "scale", title: "4. 数据规模", hint: "n 大概多大？",
      options: [
        { value: "n20", label: "≤ 20", desc: "状压 / 枚举" },
        { value: "n100", label: "≤ 100", desc: "O(n³) / 区间DP" },
        { value: "n5000", label: "≤ 5000", desc: "O(n²) / 简单DP" },
        { value: "n1e5", label: "≤ 1e5", desc: "O(n log n) / 数据结构" },
        { value: "n1e9", label: "≤ 1e9", desc: "公式 / 矩阵" }
      ]
    }
  ];

  const N_SCALE = [
    ["≤ 20", "状压 / 枚举", "状态少，直接 2^n 级暴力。"],
    ["≤ 100", "O(n³)", "区间 DP、Floyd、矩阵乘法。"],
    ["≤ 5000", "O(n²)", "两层 DP，再看单调性剪枝。"],
    ["≤ 1e5", "O(n log n)", "排序、二分、堆、线段树、分治。"],
    ["≤ 1e9", "对数 / 公式", "公式、矩阵快速幂、找循环节。"]
  ];

  let ans = {};

  function renderDissect() {
    renderTop();

    const wizard = document.getElementById("dissectWizard");
    wizard.innerHTML = DISSECT_STEPS.map(step => `
      <div class="wizard-step">
        <div class="wizard-step-title">${esc(step.title)}</div>
        <div class="wizard-step-hint">${esc(step.hint)}</div>
        <div class="wizard-options">
          ${step.options.map(opt => `
            <button class="option-chip ${ans[step.key] === opt.value ? "active" : ""}"
              data-step="${step.key}" data-value="${opt.value}">
              ${esc(opt.label)} ${esc(opt.desc)}
            </button>
          `).join("")}
        </div>
      </div>
    `).join("");

    wizard.querySelectorAll(".option-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        ans[btn.dataset.step] = btn.dataset.value;
        renderDissect();
      });
    });

    const nbox = document.getElementById("nScaleCard");
    nbox.innerHTML = N_SCALE.map(row => `
      <div class="nscale-row">
        <div class="nscale-label">${esc(row[0])}</div>
        <div class="nscale-text"><b>${esc(row[1])}</b>：${esc(row[2])}</div>
      </div>
    `).join("");

    updateResult();
  }

  function recommendOps() {
    const ops = new Set();
    if (ans.metric === "conv") ops.add("变换域映射");
    if (ans.metric === "xor") { ops.add("编码压缩"); ops.add("变换域映射"); }
    if (ans.metric === "number") ops.add("变换域映射");
    if (ans.scale === "n20") { ops.add("编码压缩"); ops.add("基线/暴力"); }
    if (ans.scale === "n100") ops.add("传播松弛");
    if (ans.scale === "n5000") { ops.add("传播松弛"); ops.add("剪枝决策"); }
    if (ans.scale === "n1e5") { ops.add("剪枝决策"); ops.add("编码压缩"); }
    if (ans.scale === "n1e9") ops.add("变换域映射");
    if (ans.shape === "graph") { ops.add("传播松弛"); ops.add("剪枝决策"); }
    if (ans.shape === "linear") ops.add("编码压缩");
    if (ans.dynamic === "dynamic") ops.add("传播松弛");
    if (ans.dynamic === "static") ops.add("编码压缩");
    if (!ops.size) ops.add("剪枝决策");
    return (D.infoOps || []).filter(op => ops.has(op));
  }

  function nextHints() {
    const map = {
      shape_linear: "序列题先想双指针、前缀和、区间 DP。",
      shape_graph: "图/树题先想连通性、最短路、树形 DP。",
      shape_algebra: "代数题先想线性基、同余、生成函数。",
      dynamic_dynamic: "实时修改：线段树、树状数组、平衡树。",
      dynamic_static: "可离线：前缀和、ST 表、莫队。",
      metric_sum: "加法/最值通常走 DP 或最短路。",
      metric_xor: "异或题优先线性基。",
      metric_conv: "卷积/计数优先 FFT / NTT。",
      metric_bool: "可行性优先并查集、二分图、2-SAT。",
      metric_number: "数论先看 gcd、逆元、同余、质因子。",
      metric_geom: "几何先看凸包、叉积、极角排序。",
      scale_n20: "优先状压、搜索、暴力。",
      scale_n100: "O(n³) 或区间 DP 可行。",
      scale_n5000: "O(n²) DP，再找单调性剪枝。",
      scale_n1e5: "必须 O(n log n)：排序/二分/线段树/分治。",
      scale_n1e9: "不要循环：公式、矩阵快速幂、找循环节。"
    };
    const hints = [];
    Object.keys(ans).forEach(k => {
      const key = k + "_" + ans[k];
      if (map[key]) hints.push(map[key]);
    });
    return hints;
  }

  function updateResult() {
    const box = document.getElementById("dissectResult");
    const done = DISSECT_STEPS.every(s => ans[s.key]);
    if (!done) { box.classList.add("hidden"); box.innerHTML = ""; return; }
    const ops = recommendOps();
    box.innerHTML = `
      <div class="result-title">建议方向</div>
      <div class="result-ops">
        ${ops.map(op => {
          const c = (D.infoOpColors || {})[op] || "#6c8cff";
          return `<span class="badge" style="color:${c};border-color:${c}55;background:${c}18;">${esc(op)}</span>`;
        }).join("")}
      </div>
      ${nextHints().map(h => `<div class="result-line">· ${esc(h)}</div>`).join("")}
    `;
    box.classList.remove("hidden");
  }

  // ---------- 进度页 ----------
  function renderTiers() {
    const list = document.getElementById("tierList");
    if (!list) return;
    list.innerHTML = (D.tiers || []).map(tier => {
      const tags = tier.tags || [];
      const total = tags.length;
      const done = tags.filter(t => isMastered(t.id)).length;
      const open = openTiers[tier.id];
      return `
        <div class="tier-card ${open ? "open" : ""}">
          <button class="tier-head" data-tier="${tier.id}">
            <span class="tier-dot" style="background:${tier.color || "#6c8cff"}"></span>
            <span class="tier-head-text">
              <span class="tier-name">${esc(tier.name)}</span>
              <div class="tier-range">${esc(tier.range || "")} · ${esc(tier.phase_name || "")}</div>
            </span>
            <span class="tier-arrow">▶</span>
          </button>
          <div class="tier-progress"><div style="width:${total ? Math.round(done*100/total) : 0}%"></div></div>
          <div class="tier-body" style="display:${open ? "block" : "none"}">
            ${tags.map(tagRowHtml).join("")}
          </div>
        </div>
      `;
    }).join("");
    bindTierEvents();
  }

  function tagRowHtml(tag) {
    const agg = aggregateTagInfo(tag);
    const badges = agg.ops.map(op => {
      const c = (D.infoOpColors || {})[op] || "#6c8cff";
      return `<span class="badge" style="color:${c};border-color:${c}55;background:${c}18;">${esc(op)}</span>`;
    }).join("");
    const hasAlgs = (tag.algorithms || []).length > 0;
    return `
      <div class="tag-row ${isMastered(tag.id) ? "mastered" : ""}">
        <div class="tag-top">
          <input type="checkbox" class="tag-check" ${isMastered(tag.id) ? "checked" : ""} data-tag-id="${esc(tag.id)}">
          <div style="min-width:0;flex:1;">
            <div class="tag-name">${esc(tag.name)}</div>
            <div class="tag-desc">${esc(tag.desc || "")}</div>
          </div>
        </div>
        ${badges ? `<div class="tag-badges">${badges}</div>` : ""}
        ${hasAlgs ? `<div class="tag-actions"><button class="tag-btn" data-info="${esc(tag.id)}">信息</button></div>` : ""}
      </div>
    `;
  }

  function bindTierEvents() {
    document.querySelectorAll(".tier-head").forEach(btn => {
      btn.addEventListener("click", () => {
        openTiers[Number(btn.dataset.tier)] = !openTiers[Number(btn.dataset.tier)];
        renderTiers();
      });
    });
    document.querySelectorAll(".tag-check").forEach(cb => {
      cb.addEventListener("change", () => {
        setMastered(cb.dataset.tagId, cb.checked);
        const row = cb.closest(".tag-row");
        if (row) row.classList.toggle("mastered", cb.checked);
        renderTop();
        renderTiers();
      });
    });
    document.querySelectorAll("[data-info]").forEach(btn => {
      btn.addEventListener("click", () => {
        const tag = findTagById(btn.dataset.info);
        if (tag) showTagInfo(tag);
      });
    });
  }

  function findTagById(id) {
    for (const t of D.tiers || []) {
      for (const tag of t.tags || []) {
        if (tag.id === id) return tag;
      }
    }
    return null;
  }

  // ---------- 简洁信息弹窗（无 C++ 模板） ----------
  const modal = document.getElementById("modal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");

  function showModal(title, html) {
    modalTitle.textContent = title;
    modalBody.innerHTML = html;
    modal.classList.remove("hidden");
  }

  function hideModal() {
    modal.classList.add("hidden");
    modalBody.innerHTML = "";
  }

  function showTagInfo(tag) {
    const names = tag.algorithms || [];
    if (!names.length) return;
    const html = names.map(name => {
      const a = algMap[name];
      if (!a) return "";
      const info = a.info || {};
      return `
        <div style="border:1px solid var(--border);border-radius:12px;padding:10px;margin-bottom:10px;">
          <div style="font-weight:700;">${esc(a.name)}</div>
          <div class="info-line">${esc((info.ops || []).join(" / "))} · ${esc(info.topology || "")} · ${esc(info.dynamic || "")}</div>
          <div class="why-line">${esc(info.why || "")}</div>
          <p style="font-size:12px;color:var(--text-dim);margin-top:4px;">${esc(a.intro || "")}</p>
          <p style="font-size:12px;color:var(--text-dim);">复杂度：${esc(a.complexity || "")}</p>
        </div>
      `;
    }).join("");
    showModal(tag.name, html);
  }

  // ---------- tabs ----------
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentView = btn.dataset.view;
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === currentView + "-view"));
      if (currentView === "dissect") renderDissect();
      if (currentView === "tiers") renderTiers();
    });
  });

  document.getElementById("modalClose").addEventListener("click", hideModal);
  document.getElementById("modalMask").addEventListener("click", hideModal);

  // ---------- PWA ----------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    });
  }

  // ---------- init ----------
  renderDissect();
  renderTiers();
})();
