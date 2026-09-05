/* Node VM 小脚本：验证 mobile/www/card_store.js 的 localStorage 封装。 */
const fs = require("fs");
const vm = require("vm");

const code = fs.readFileSync("mobile/www/card_store.js", "utf8");

function makeStorage(initial) {
  let data = initial || {};
  return {
    getItem(k) {
      return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null;
    },
    setItem(k, v) {
      data[k] = String(v);
    },
  };
}

function loadStore(storage) {
  const ctx = {
    window: {},
    localStorage: storage,
    Date,
    JSON,
    console,
  };
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return ctx.window.KL_CARD_STORE;
}

let storage = makeStorage();
let store = loadStore(storage);
if (JSON.stringify(store.load()) !== "[]") throw new Error("missing load fail");

storage = makeStorage({ kl_card_records: "{bad" });
store = loadStore(storage);
if (JSON.stringify(store.load()) !== "[]") throw new Error("corrupt load fail");

storage = makeStorage();
store = loadStore(storage);
store.add("reading");
store.add("modeling");
store.add("reading");
store.add("proof");
if (JSON.stringify(store.summary(10)) !== JSON.stringify({ reading: 2, modeling: 1, proof: 1 })) {
  throw new Error("summary(10) fail");
}
if (JSON.stringify(store.summary(2)) !== JSON.stringify({ reading: 1, proof: 1 })) {
  throw new Error("summary(2) fail");
}
if (JSON.stringify(store.summary(0)) !== "{}") throw new Error("summary(0) fail");

// 模拟刷新：同一 storage 重新加载脚本
store = loadStore(storage);
if (store.load().length !== 4) throw new Error("persist fail");

console.log("CARD_STORE NODE TEST OK");
