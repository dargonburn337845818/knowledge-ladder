/* Node VM：验证每次回答后出现与“问题+回答”对应的动态点拨，而不是重复话术。 */
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const code = fs.readFileSync("mobile/www/app.js", "utf8");

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

const yesBtn = fakeEl();
yesBtn.dataset = { answer: "yes" };
const noBtn = fakeEl();
noBtn.dataset = { answer: "no" };
const uncertainBtn = fakeEl();
uncertainBtn.dataset = { answer: "uncertain" };

const stage = fakeEl();
stage.querySelectorAll = function (selector) {
  if (selector === ".option") return [yesBtn, noBtn, uncertainBtn];
  return [];
};

const elements = {};
function getEl(id) {
  if (!elements[id]) elements[id] = fakeEl();
  return elements[id];
}
elements.stage = stage;

const document = {
  getElementById(id) {
    if (id === "stage") return stage;
    return getEl(id);
  },
};

const engine = {
  asked: [],
  initialWeights() { return []; },
  shouldStop(weights, asked) {
    return { stop: asked.length >= 2 };
  },
  chooseNext(weights, asked) {
    return { id: asked.length === 0 ? "f1" : "f2" };
  },
  answerProbability() { return 0.5; },
  posterior(w) { return w; },
  directionProbs() { return { 编码压缩: 1 }; },
  entropy() { return 1; },
  features: [
    { id: "f1", question: "数据主体是线性序列吗？" },
    { id: "f2", question: "答案有单调性吗？" },
  ],
  params: {},
};

const context = {
  window: {
    ENTROPY_DATA: {
      heuristics: { directions: [] },
      direction_content: { directions: [] },
      dynamic_insights: {
        features: {
          f1: {
            yes: "你确认了线性结构：顺序、区间、下标关系成为主要资源。",
            no: "你排除了线性结构：要换成树、集合或代数对象的读法。",
            uncertain: "线性结构仍不确定：先保留两种读法，等下一特征收窄。",
          },
          f2: {
            yes: "你确认了单调性：候选答案空间可被一次比较切成两半。",
            no: "你排除了单调性：不要强行一次比较减半。",
            uncertain: "单调性存疑：先在小样例上验证是否连续。",
          },
        },
        directions: {},
      },
    },
    EntropyEngine: { create: () => engine },
  },
  document,
  console,
};

vm.createContext(context);
vm.runInContext(code, context);

// 第一题：还没有铺垫，不应显示点拨
let html = stage.innerHTML;
assert(html.includes("数据主体是线性序列吗"), "first question not shown");
assert(!html.includes("点拨："), "insight should not appear before first answer");

// 回答“是”
yesBtn.click();

// 第二题：应显示前面回答对应的动态点拨，且不是重复文案
html = stage.innerHTML;
assert(html.includes("数据主体是线性序列吗") || html.includes("答案有单调性吗"), "second question not rendered");
assert(html.includes("点拨：你确认了线性结构"), "dynamic insight after answer not shown");
assert(!html.includes("点拨：你排除了线性结构"), "wrong insight shown");

// 再答一题后直接收敛：最后一次点拨也要保留在方向选择页
yesBtn.click();
html = stage.innerHTML;
assert(html.includes("选一个方向"), "finish page not rendered");
assert(html.includes("点拨：你确认了单调性"), "last insight should persist on finish page");

console.log("DYNAMIC_INSIGHT_FLOW NODE TEST OK");
