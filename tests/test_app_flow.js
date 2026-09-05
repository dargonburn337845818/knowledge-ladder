/* Node VM 小脚本：验证移动端主流程无 baseline、概率选择、方向点拨。 */
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const code = fs.readFileSync("mobile/www/app.js", "utf8");

// 静态断言：主流程无 baseline、无三层递进，且存在概率选择/动态点拨，无卡点自查/看别的
assert(!/baseline|renderBaseline|先写暴力|基线/.test(code), "mobile app.js still contains baseline flow");
assert(code.includes('mode: "question"'), "initial state is not question");
assert(code.includes("renderQuestion();"), "initial call is not renderQuestion");
assert(code.includes("direction-choice"), "missing probability choice implementation");
assert(!/卡点自查|看别的/.test(code), "card self-check or see-other still present");
assert(!/layerUnlocked|layerCondition|layerAction|layerSelfQuestion|nextLayerBtn|prevLayerBtn/.test(code), "mobile app.js still contains three-layer UI");
assert(!code.includes("三层点拨"), "mobile app.js still contains three-layer title");
assert(code.includes("nudge-text"), "missing one-line nudge rendering");
assert(code.includes("DYNAMIC_INSIGHTS"), "missing dynamic insights loader");
assert(code.includes("insight-text"), "missing dynamic insight rendering");
assert(code.includes("深入点拨"), "missing deep direction insight rendering");

// --- 最小 DOM / 引擎桩 ---
function fakeEl() {
  return {
    innerHTML: "",
    style: {},
    textContent: "",
    addEventListener(type, fn) {
      this["on" + type] = fn;
    },
    click() {
      if (this.onclick) this.onclick();
    },
  };
}

const directionChoices = ["编码压缩", "传播松弛", "剪枝决策", "变换域映射"].map((title) => ({
  dataset: { dir: title },
  addEventListener(type, fn) {
    this.onclick = fn;
  },
  click() {
    if (this.onclick) this.onclick();
  },
}));

const elements = {};
function getEl(id) {
  if (!elements[id]) elements[id] = fakeEl();
  return elements[id];
}

const stage = fakeEl();
stage.querySelectorAll = function (selector) {
  if (selector === ".direction-choice") return directionChoices;
  return [];
};
elements.stage = stage;

const document = {
  getElementById(id) {
    if (id === "stage") return stage;
    return getEl(id);
  },
};

const engine = {
  initialWeights() {
    return [];
  },
  shouldStop() {
    return { stop: true }; // 直接进入最终页
  },
  chooseNext() {
    return { id: "f1" };
  },
  features: [],
  params: {},
  directionProbs() {
    return { 编码压缩: 1, 传播松弛: 0.5, 剪枝决策: 0.2, 变换域映射: 0.1 };
  },
  entropy() {
    return 0;
  },
};

const fourDirs = [
  {
    title: "编码压缩",
    value: "重复信息只算一次，把慢查询变成快查询。",
    nudge: "重复的信息只算一次；先问：哪个量会被反复查？",
    triggers: ["触发1", "触发2"],
    card_triggers: ["安全触发1", "安全触发2"],
    layers: { condition: "条件1", action: "动作1", self_question: "自问1" },
  },
  {
    title: "传播松弛",
    value: "沿依赖一层层推。",
    triggers: ["触发1", "触发2"],
    card_triggers: ["安全触发1", "安全触发2"],
    layers: { condition: "条件2", action: "动作2", self_question: "自问2" },
  },
  {
    title: "剪枝决策",
    value: "证明候选不可能赢。",
    triggers: ["触发1", "触发2"],
    card_triggers: ["安全触发1", "安全触发2"],
    layers: { condition: "条件3", action: "动作3", self_question: "自问3" },
  },
  {
    title: "变换域映射",
    value: "换个表示或坐标。",
    triggers: ["触发1", "触发2"],
    card_triggers: ["安全触发1", "安全触发2"],
    layers: { condition: "条件4", action: "动作4", self_question: "自问4" },
  },
];

const context = {
  window: {
    ENTROPY_DATA: {
      heuristics: { directions: [], card_points: [] },
      direction_content: { directions: fourDirs },
      dynamic_insights: {
        features: {},
        directions: { 编码压缩: "编码压缩的本质是把被反复消费的信息只算一次；边界是数据静态且查询关心可压缩性质。" },
      },
    },
    EntropyEngine: {
      create() {
        return engine;
      },
    },
  },
  document,
  console,
};

vm.createContext(context);
vm.runInContext(code, context);

// 最终页：概率排序选择
assert(elements.stage.innerHTML.includes("选一个方向"), "finish page title missing");
for (const title of ["编码压缩", "传播松弛", "剪枝决策", "变换域映射"]) {
  assert(elements.stage.innerHTML.includes(`data-dir="${title}"`), `missing direction choice ${title}`);
}
assert(elements.stage.innerHTML.includes("%"), "probability percent not shown");

// 点击第一个选择进入详情
directionChoices[0].click();
let html = elements.stage.innerHTML;
assert(!html.includes("三层点拨"), "three-layer title still shown");
assert(!html.includes("第 1/3 层"), "layer progress still shown");
assert(!html.includes("nextLayerBtn"), "next layer button still shown");
assert(!html.includes("prevLayerBtn"), "prev layer button still shown");
assert(html.includes("常见信号"), "common signal keywords not shown");
assert(html.includes("一句话点拨"), "one-line nudge not shown");
assert(html.includes("深入点拨"), "deep direction insight not shown");
assert(!/算法理解|信息论视角|经典模式|关键观察/.test(html), "mobile should stay lean without desktop deep understanding");

console.log("APP_FLOW NODE TEST OK");
