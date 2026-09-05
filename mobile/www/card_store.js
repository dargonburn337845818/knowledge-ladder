/* 卡点本地记录：localStorage 封装，纯本地、无网络、无依赖。 */
(function () {
  var KEY = "kl_card_records";

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) {
        return [];
      }
      var data = JSON.parse(raw);
      if (!Array.isArray(data)) {
        return [];
      }
      return data.filter(function (r) {
        return r && typeof r === "object" && typeof r.card === "string" && "ts" in r;
      });
    } catch (e) {
      return [];
    }
  }

  function add(card) {
    var records = load();
    records.push({ ts: Date.now(), card: String(card) });
    try {
      localStorage.setItem(KEY, JSON.stringify(records));
    } catch (e) {
      // 存储配额/禁用时静默失败，不影响主流程。
    }
  }

  function summary(limit) {
    var records = load();
    if (limit > 0) {
      records = records.slice(-limit);
    } else {
      records = [];
    }
    var counts = {};
    records.forEach(function (r) {
      counts[r.card] = (counts[r.card] || 0) + 1;
    });
    return counts;
  }

  window.KL_CARD_STORE = { load: load, add: add, summary: summary };
})();
