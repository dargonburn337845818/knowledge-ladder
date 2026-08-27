/* 知识阶梯移动端 PWA 逻辑 */
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
    "编码压缩": "减少冗余：哈希 / 前缀和 / 线性基 / SAM / 可持久化",
    "传播松弛": "扩散信息：BFS / DP / Dijkstra / 线段树 / 树形 DP",
    "剪枝决策": "缩小搜索：二分 / 双指针 / 单调栈 / 凸包 / 斜率优化 / 最小割",
    "变换域映射": "解耦纠缠：FFT / 矩阵幂 / 差分 / 对偶 / 生成函数 / LCT",
    "基线/暴力": "没有信息破缺：暴力 / 模拟 / 几何原子 / 构造"
  };

  let currentView = "home";
  let currentOp = "";
  let searchTerm = "";
  let openTiers = {};
  const allTierIds = (D.tiers || []).map(t => t.id);

  // ---------- helpers ----------
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function saveMastered() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mastered));
  }

  function isMastered(id) {
    return !!mastered[id];
  }

  function setMastered(id, value) {
    mastered[id] = value;
    saveMastered();
  }

  function unique(arr) {
    const seen = new Set();
    const out = [];
    for (const x of arr) {
      if (x && !seen.has(x)) { seen.add(x); out.push(x); }
    }
    return out;
  }

  function aggregateTagInfo(tag) {
    const ops = [], topos = [], dyns = [], metrics = [];
    (tag.algorithms || []).forEach(name => {
      const info = algMap[name] && algMap[name].info;
      if (!info) return;
      (info.ops || []).forEach(op => ops.push(op));
      if (info.topology) topos.push(info.topology);
      if (info.dynamic) dyns.push(info.dynamic);
      if (info.metric) metrics.push(info.metric);
    });
    return {
      ops: unique(ops),
      topologies: unique(topos),
      dynamics: unique(dyns),
      metrics: unique(metrics)
    };
  }

  function totalTags() {
    return (D.tiers || []).reduce((sum, t) => sum + (t.tags || []).length, 0);
  }

  function masteredCount() {
    let c = 0;
    (D.tiers || []).forEach(t => (t.tags || []).forEach(tag => {
      if (isMastered(tag.id)) c++;
    }));
    return c;
  }

  function opCoverage() {
    const counts = {};
    (D.infoOps || []).forEach(op => counts[op] = 0);
    (D.tiers || []).forEach(t => (t.tags || []).forEach(tag => {
      if (!isMastered(tag.id)) return;
      const agg = aggregateTagInfo(tag);
      agg.ops.forEach(op => { if (counts[op] !== undefined) counts[op]++; });
    }));
    return counts;
  }

  // ---------- render home ----------
  function renderHome() {
    const total = totalTags();
    const done = masteredCount();
    document.getElementById("homeProgress").textContent =
      `总进度：${done} / ${total}（${Math.round(done * 100 / Math.max(1, total))}%）`;

    const counts = {};
    (D.infoOps || []).forEach(op => counts[op] = 0);
    (D.algorithms || []).forEach(a => {
      (a.info && a.info.ops || []).forEach(op => {
        if (counts[op] !== undefined) counts[op]++;
      });
    });
    const masteredCounts = opCoverage();

    document.getElementById("opOverview").innerHTML = (D.infoOps || []).map(op => `
      <div class="op-card">
        <div class="op-name" style="color:${(D.infoOpColors || {})[op] || "#6c8cff"}">${esc(op)}</div>
        <div class="op-desc">${esc(OP_DESC[op] || "")}</div>
        <div class="op-count">覆盖 ${counts[op]} 个算法 · 已掌握 ${masteredCounts[op] || 0} 个标签</div>
      </div>
    `).join("");

    const phases = D.phases || {};
    document.getElementById("phaseList").innerHTML = Object.keys(phases).sort((a,b)=>a-b).map(k => {
      const p = phases[k];
      return `
        <div class="phase-card">
          <div class="phase-name">${esc(p.name)}</div>
          <div class="phase-meta">${esc(p.range || "")} · ${esc(p.slogan || "")}</div>
          <div class="phase-desc">${esc(p.description || "")}</div>
        </div>
      `;
    }).join("");

    document.getElementById("anatomyList").innerHTML = (D.anatomySteps || []).map(s => `
      <div class="anatomy-card">
        <div class="anatomy-step">${esc(s.step)}</div>
        <div class="anatomy-question">${esc(s.question)} <b>${esc(s.choices)}</b></div>
        <div style="font-size:12px;color:var(--text-dim);margin-top:4px;">${esc(s.output)}</div>
      </div>
    `).join("");
  }

  // ---------- render tier list ----------
  function tagMatches(tag) {
    if (currentOp) {
      const agg = aggregateTagInfo(tag);
      if (!agg.ops.includes(currentOp)) return false;
    }
    if (searchTerm) {
      const agg = aggregateTagInfo(tag);
      const hay = [
        tag.name || "", tag.desc || "", tag.detail || "", tag.group || "",
        (tag.algorithms || []).join(" "),
        agg.ops.join(" "), agg.topologies.join(" "), agg.metrics.join(" ")
      ].join(" ").toLowerCase();
      if (!hay.includes(searchTerm.toLowerCase())) return false;
    }
    return true;
  }

  function renderTiers() {
    document.getElementById("opFilter").innerHTML = ["", ...(D.infoOps || [])].map(op => `
      <button class="chip ${(currentOp || "") === (op || "") ? "active" : ""}" data-op="${esc(op)}">${esc(op || "全部")}</button>
    `).join("");

    const list = document.getElementById("tierList");
    list.innerHTML = (D.tiers || []).map(tier => {
      const tags = tier.tags || [];
      const total = tags.length;
      const done = tags.filter(t => isMastered(t.id)).length;
      const open = openTiers[tier.id];
      const filtering = !!(currentOp || searchTerm);
      const showBody = open || filtering;
      const visibleTags = tags.filter(tagMatches);
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
          <div class="tier-body" style="display:${showBody ? "block" : "none"}">
            ${visibleTags.length ? visibleTags.map(tagRowHtml).join("") : '<div class="empty-tip">没有匹配的知识点</div>'}
          </div>
        </div>
      `;
    }).join("");
    bindTierEvents();
  }

  function tagRowHtml(tag) {
    const agg = aggregateTagInfo(tag);
    const badges = [
      ...agg.ops.map(op => {
        const c = (D.infoOpColors || {})[op] || "#6c8cff";
        return `<span class="badge" style="color:${c};border-color:${c}55;background:${c}18;">${esc(op)}</span>`;
      }),
      ...agg.topologies.map(t => `<span class="badge topo">${esc(t)}</span>`),
      ...agg.dynamics.map(d => `<span class="badge dyn">${esc(d)}</span>`)
    ].join("");
    const hasAlgs = (tag.algorithms || []).length > 0;
    const hasDetail = !!tag.detail;
    return `
      <div class="tag-row ${isMastered(tag.id) ? "mastered" : ""}" data-tag="${esc(tag.id)}">
        <div class="tag-top">
          <input type="checkbox" class="tag-check" ${isMastered(tag.id) ? "checked" : ""} data-tag-id="${esc(tag.id)}">
          <div style="min-width:0;flex:1;">
            <div class="tag-name">${esc(tag.name)}</div>
            <div class="tag-desc">${esc(tag.desc || "")}</div>
          </div>
        </div>
        ${badges ? `<div class="tag-badges">${badges}</div>` : ""}
        <div class="tag-actions">
          ${hasAlgs ? `<button class="tag-btn" data-info="${esc(tag.id)}">信息</button>` : ""}
          ${hasDetail ? `<button class="tag-btn" data-detail="${esc(tag.id)}">详情</button>` : ""}
        </div>
      </div>
    `;
  }

  function bindTierEvents() {
    document.querySelectorAll(".tier-head").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.tier);
        openTiers[id] = !openTiers[id];
        renderTiers();
      });
    });
    document.querySelectorAll(".tag-check").forEach(cb => {
      cb.addEventListener("change", () => {
        const id = cb.dataset.tagId;
        setMastered(id, cb.checked);
        const row = cb.closest(".tag-row");
        if (row) row.classList.toggle("mastered", cb.checked);
        renderHome();
        renderTiers();
      });
    });
    document.querySelectorAll("[data-info]").forEach(btn => {
      btn.addEventListener("click", () => {
        const tag = findTagById(btn.dataset.info);
        if (tag) showTagInfo(tag);
      });
    });
    document.querySelectorAll("[data-detail]").forEach(btn => {
      btn.addEventListener("click", () => {
        const tag = findTagById(btn.dataset.detail);
        if (tag) showTagDetail(tag);
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

  // ---------- 拆题引导 ----------
  const DISSECT_STEPS = [
    {
      key: "shape", title: "1. 数据形状", hint: "先看数据长在什么结构上？",
      options: [
        { value: "linear", label: "线性", desc: "数组、字符串、区间、序列" },
        { value: "graph", label: "树 / 图", desc: "树、图、网络、依赖关系" },
        { value: "algebra", label: "数学对象", desc: "数字、集合、异或、多项式、组合" }
      ]
    },
    {
      key: "dynamic", title: "2. 数据是否变化", hint: "程序运行过程中数据会改吗？",
      options: [
        { value: "static", label: "静态", desc: "只读，可预处理 / 离线" },
        { value: "dynamic", label: "动态", desc: "有修改，需要实时数据结构" }
      ]
    },
    {
      key: "metric", title: "3. 运算规则", hint: "合并信息时用什么规则？",
      options: [
        { value: "sum", label: "加法 / 最值", desc: "路径、区间和、最大最小" },
        { value: "xor", label: "异或", desc: "不进位、线性基" },
        { value: "conv", label: "卷积 / 计数", desc: "多项式、组合计数" },
        { value: "bool", label: "可行性", desc: "连通、匹配、2-SAT" },
        { value: "number", label: "数论 / 模", desc: "gcd、逆元、同余、整除" },
        { value: "geom", label: "几何", desc: "点、线、凸包、距离" }
      ]
    },
    {
      key: "scale", title: "4. 数据规模", hint: "n 大概有多大？这是最快排除法。",
      options: [
        { value: "n20", label: "≤ 20", desc: "状压 / 小范围枚举" },
        { value: "n100", label: "≤ 100", desc: "O(n³) / 区间 DP" },
        { value: "n5000", label: "≤ 5000", desc: "O(n²) / 简单 DP" },
        { value: "n1e5", label: "≤ 1e5", desc: "O(n log n) / 数据结构" },
        { value: "n1e9", label: "≤ 1e9", desc: "公式 / 矩阵 / 找规律" }
      ]
    }
  ];

  const N_SCALE = [
    ["≤ 20", "状压 / 枚举", "状态少就可以直接考虑 2^n 级别的暴力或状压。"],
    ["≤ 100", "O(n³)", "区间 DP、Floyd、矩阵乘法都能接受。"],
    ["≤ 5000", "O(n²)", "两层 DP 可行；再看看有没有单调性可以剪枝。"],
    ["≤ 1e5", "O(n log n)", "主要靠排序、二分、堆、线段树、分治。"],
    ["≤ 1e9", "对数 / 公式", "不能循环枚举，找数学公式、矩阵快速幂、循环节。"]
  ];

  let dissectAnswers = {};

  function renderDissect() {
    const wizard = document.getElementById("dissectWizard");
    if (!wizard) return;
    wizard.innerHTML = DISSECT_STEPS.map(step => `
      <div class="wizard-step">
        <div class="wizard-step-title">${esc(step.title)}</div>
        <div class="wizard-step-hint">${esc(step.hint)}</div>
        <div class="wizard-options">
          ${step.options.map(opt => `
            <button class="option-chip ${dissectAnswers[step.key] === opt.value ? "active" : ""}"
              data-step="${step.key}" data-value="${opt.value}">
              ${esc(opt.label)} ${esc(opt.desc)}
            </button>
          `).join("")}
        </div>
      </div>
    `).join("");

    wizard.querySelectorAll(".option-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        dissectAnswers[btn.dataset.step] = btn.dataset.value;
        renderDissect();
      });
    });

    updateDissectResult();
    renderNScale();
  }

  function renderNScale() {
    const box = document.getElementById("nScaleCard");
    if (!box) return;
    box.innerHTML = N_SCALE.map(row => `
      <div class="nscale-row">
        <div class="nscale-label">${esc(row[0])}</div>
        <div class="nscale-text"><b>${esc(row[1])}</b>：${esc(row[2])}</div>
      </div>
    `).join("");
  }

  function recommendOps(ans) {
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

  function nextHints(ans) {
    const hints = [];
    const map = {
      shape_linear: "序列题先想双指针、前缀和、区间 DP。",
      shape_graph: "图/树题先想连通性、最短路、树形 DP。",
      shape_algebra: "代数题先想线性基、同余、生成函数、矩阵。",
      dynamic_dynamic: "要支持实时修改：线段树、树状数组、平衡树。",
      dynamic_static: "可以离线预处理：前缀和、ST 表、莫队。",
      metric_sum: "加法/最值通常走 DP 或最短路。",
      metric_xor: "异或题优先线性基。",
      metric_conv: "卷积/计数题优先 FFT / NTT。",
      metric_bool: "可行性题优先并查集、二分图、2-SAT。",
      metric_number: "数论题先看 gcd、逆元、同余、质因子分解。",
      metric_geom: "几何题先看凸包、叉积、极角排序。",
      scale_n20: "n 很小：优先想状压、搜索、暴力枚举。",
      scale_n100: "n≤100：O(n³) 或区间 DP 可行。",
      scale_n5000: "n≤5000：考虑 O(n²) DP，再找单调性剪枝。",
      scale_n1e5: "n≤1e5：必须 O(n log n)，排序/二分/线段树/分治。",
      scale_n1e9: "n≤1e9：不要循环，找公式、矩阵快速幂、循环节。"
    };
    (Object.keys(ans)).forEach(k => {
      const key = k + "_" + ans[k];
      if (map[key]) hints.push(map[key]);
    });
    return hints;
  }

  function updateDissectResult() {
    const box = document.getElementById("dissectResult");
    if (!box) return;
    const done = DISSECT_STEPS.every(s => dissectAnswers[s.key]);
    if (!done) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    const ans = dissectAnswers;
    const ops = recommendOps(ans);
    const hints = nextHints(ans);
    box.innerHTML = `
      <div class="result-title">建议方向</div>
      <div class="result-ops">
        ${ops.map(op => {
          const c = (D.infoOpColors || {})[op] || "#6c8cff";
          return `<span class="badge" style="color:${c};border-color:${c}55;background:${c}18;">${esc(op)}</span>`;
        }).join("")}
      </div>
      ${hints.map(h => `<div class="result-line">· ${esc(h)}</div>`).join("")}
      <p style="font-size:12px;color:var(--text-dim);margin-top:6px;">这只是粗筛，具体还要继续看题目里的特殊条件。</p>
    `;
    box.classList.remove("hidden");
  }

  // ---------- modal ----------
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

  function showGuide() {
    const phases = D.phases || {};
    const phaseHtml = Object.keys(phases).sort((a,b)=>a-b).map(k => {
      const p = phases[k];
      return `<p><b>${esc(p.name)}</b>（${esc(p.range)}）<br>${esc(p.description)}</p>`;
    }).join("");
    const anatomyHtml = (D.anatomySteps || []).map(s => `
      <p><b>${esc(s.step)}</b>：${esc(s.question)}<br>${esc(s.choices)}<br>${esc(s.output)}</p>
    `).join("");
    showModal("信息论导论", `
      <h3>四种信息操作</h3>
      ${(D.infoOps || []).map(op => `<p><b>${esc(op)}</b>：${esc(OP_DESC[op] || "")}</p>`).join("")}
      <h3>四阶段地图</h3>
      ${phaseHtml}
      <h3>拆题四步</h3>
      ${anatomyHtml}
      <p style="font-size:12px;">四种操作是记忆坐标系，不是严格分类；一个算法可以属于多个操作。</p>
    `);
  }

  function showTagInfo(tag) {
    const names = tag.algorithms || [];
    if (!names.length) return;
    const html = names.map(n => {
      const a = algMap[n];
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

  function showTagDetail(tag) {
    showModal(tag.name, `
      <p>${esc(tag.desc || "")}</p>
      ${(tag.detail || "").split(/\n\n+/).map(p => `<p>${esc(p)}</p>`).join("")}
    `);
  }

  // ---------- bind views / filters ----------
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentView = btn.dataset.view;
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === currentView + "-view"));
      if (currentView === "home") renderHome();
      if (currentView === "dissect") renderDissect();
      if (currentView === "tiers") renderTiers();
    });
  });

  document.getElementById("guideBtn").addEventListener("click", showGuide);
  document.getElementById("modalClose").addEventListener("click", hideModal);
  document.getElementById("modalMask").addEventListener("click", hideModal);

  document.getElementById("opFilter").addEventListener("click", e => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    currentOp = btn.dataset.op || "";
    renderTiers();
  });

  document.getElementById("searchInput").addEventListener("input", e => {
    searchTerm = e.target.value.trim();
    renderTiers();
  });

  // ---------- PWA service worker ----------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    });
  }

  // ---------- init ----------
  renderHome();
  renderDissect();
  renderTiers();
})();
