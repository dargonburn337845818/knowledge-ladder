/* 动态熵减决策引擎（纯本地 JS）。
 * 输入 window.ENTROPY_DATA，不调用任何网络/模型。
 */
(function (global) {
  function normalize(weights) {
    var total = 0;
    for (var i = 0; i < weights.length; i++) total += weights[i];
    if (total <= 0) {
      var out = new Array(weights.length);
      for (var j = 0; j < weights.length; j++) out[j] = 1 / weights.length;
      return out;
    }
    // 与 Python _norm 对齐：返回新数组，绝不原地修改调用方传入的权重。
    var result = new Array(weights.length);
    for (var k = 0; k < weights.length; k++) result[k] = weights[k] / total;
    return result;
  }

  function entropy(weights) {
    // 与 Python EntropyEngine.entropy 对齐：先归一化再计算熵。
    var normalized = normalize(weights);
    var h = 0;
    for (var i = 0; i < normalized.length; i++) {
      var w = normalized[i];
      if (w > 0) h -= w * Math.log2(w);
    }
    return h;
  }

  function makeEngine(data) {
    var features = data.features || [];
    var algorithms = data.algorithms || [];
    var params = data.params || {};
    var directions = data.directions || [];

    var featureIds = features.map(function (f) { return f.id; });
    var featureIndex = {};
    for (var fi = 0; fi < featureIds.length; fi++) featureIndex[featureIds[fi]] = fi;

    // 列优先预计算：避免每次回答都在 120×20 个对象上做属性查找。
    var profileColumns = [];
    for (var fIdx = 0; fIdx < featureIds.length; fIdx++) {
      var fid = featureIds[fIdx];
      var col = [];
      for (var aIdx = 0; aIdx < algorithms.length; aIdx++) {
        var p = (algorithms[aIdx].profile || {})[fid];
        col.push(typeof p === "number" ? p : 0.5);
      }
      profileColumns.push(col);
    }

    var directionColumns = {};
    for (var dIdx = 0; dIdx < directions.length; dIdx++) {
      var dName = directions[dIdx];
      var dCol = [];
      for (var a2 = 0; a2 < algorithms.length; a2++) {
        dCol.push((algorithms[a2].direction_weights || {})[dName] || 0);
      }
      directionColumns[dName] = dCol;
    }

    function profile(algIndex, fid) {
      var idx = featureIndex[fid];
      if (idx == null) return 0.5;
      return profileColumns[idx][algIndex];
    }

    function answerProbabilityNorm(w, fidIdx, answer) {
      if (answer === "uncertain") {
        var decay = params.uncertain_decay == null ? 0.5 : params.uncertain_decay;
        return decay * answerProbabilityNorm(w, fidIdx, "yes")
          + (1 - decay) * answerProbabilityNorm(w, fidIdx, "no");
      }
      var s = 0;
      var col = profileColumns[fidIdx];
      if (answer === "yes") {
        for (var i = 0; i < w.length; i++) s += w[i] * col[i];
      } else {
        for (var j = 0; j < w.length; j++) s += w[j] * (1 - col[j]);
      }
      return s;
    }

    function posteriorNorm(w, fidIdx, answer) {
      if (answer === "uncertain") {
        var decay = params.uncertain_decay == null ? 0.5 : params.uncertain_decay;
        var wy = posteriorNorm(w, fidIdx, "yes");
        var wn = posteriorNorm(w, fidIdx, "no");
        var mix = [];
        for (var m = 0; m < wy.length; m++) mix.push(decay * wy[m] + (1 - decay) * wn[m]);
        return normalize(mix);
      }
      var col = profileColumns[fidIdx];
      var out = [];
      for (var i = 0; i < w.length; i++) {
        var p = answer === "yes" ? col[i] : (1 - col[i]);
        out.push(w[i] * p);
      }
      return normalize(out);
    }

    function answerProbability(weights, fid, answer) {
      var idx = featureIndex[fid];
      if (idx == null) return 1;
      return answerProbabilityNorm(normalize(weights.slice()), idx, answer);
    }

    function posterior(weights, fid, answer) {
      var idx = featureIndex[fid];
      if (idx == null) return normalize(weights.slice());
      return posteriorNorm(normalize(weights.slice()), idx, answer);
    }

    function informationGain(weights, fid) {
      var idx = featureIndex[fid];
      if (idx == null) return 0;
      var w = normalize(weights.slice());
      var py = answerProbabilityNorm(w, idx, "yes");
      var pn = 1 - py;
      if (py <= 0 || pn <= 0) return 0;
      var hy = entropy(posteriorNorm(w, idx, "yes"));
      var hn = entropy(posteriorNorm(w, idx, "no"));
      return entropy(w) - (py * hy + pn * hn);
    }

    function chooseNext(weights, asked) {
      var bestId = null;
      var bestIg = -1;
      var w = normalize(weights.slice());
      var wEntropy = entropy(w);
      for (var i = 0; i < featureIds.length; i++) {
        var fid = featureIds[i];
        if (asked.indexOf(fid) >= 0) continue;
        var py = answerProbabilityNorm(w, i, "yes");
        var pn = 1 - py;
        if (py <= 0 || pn <= 0) continue;
        var hy = entropy(posteriorNorm(w, i, "yes"));
        var hn = entropy(posteriorNorm(w, i, "no"));
        var ig = wEntropy - (py * hy + pn * hn);
        if (ig > bestIg) {
          bestIg = ig;
          bestId = fid;
        }
      }
      return { id: bestId, ig: bestIg };
    }

    function shouldStop(weights, asked) {
      var h = entropy(normalize(weights.slice()));
      var paramsStop = params.entropy_stop_threshold == null ? 0.45 : params.entropy_stop_threshold;
      if (h < paramsStop) return { stop: true, reason: "entropy" };
      var maxQ = params.max_questions == null ? 12 : params.max_questions;
      if (asked.length >= maxQ) return { stop: true, reason: "max" };
      var next = chooseNext(weights, asked);
      if (!next.id) return { stop: true, reason: "exhausted" };
      var igStop = params.ig_stop_threshold == null ? 0.03 : params.ig_stop_threshold;
      if (next.ig < igStop) return { stop: true, reason: "ig" };
      return { stop: false, reason: next.id, ig: next.ig };
    }

    function directionProbs(weights) {
      var w = normalize(weights.slice());
      var out = {};
      var total = 0;
      for (var d = 0; d < directions.length; d++) {
        var name = directions[d];
        var column = directionColumns[name];
        var s = 0;
        for (var i = 0; i < w.length; i++) s += w[i] * column[i];
        out[name] = s;
        total += s;
      }
      if (total <= 0) total = 1;
      for (var key in out) out[key] = out[key] / total;
      return out;
    }

    function topAlgorithms(weights, threshold, limit) {
      if (threshold == null) threshold = params.algorithm_weight_threshold == null ? 0.02 : params.algorithm_weight_threshold;
      if (limit == null) limit = params.max_algorithm_list == null ? 12 : params.max_algorithm_list;
      var w = normalize(weights.slice());
      var rows = [];
      for (var i = 0; i < w.length; i++) {
        if (w[i] >= threshold) {
          rows.push({ algorithm_name: algorithms[i].algorithm_name, weight: w[i] });
        }
      }
      rows.sort(function (a, b) { return b.weight - a.weight; });
      return rows.slice(0, limit);
    }

    function realtimeTop(weights, n) {
      if (n == null) n = params.realtime_top_n == null ? 3 : params.realtime_top_n;
      var w = normalize(weights.slice());
      var rows = [];
      for (var i = 0; i < w.length; i++) rows.push({ algorithm_name: algorithms[i].algorithm_name, weight: w[i] });
      rows.sort(function (a, b) { return b.weight - a.weight; });
      return rows.slice(0, n);
    }

    return {
      features: features,
      algorithms: algorithms,
      params: params,
      normalize: normalize,
      entropy: entropy,
      answerProbability: answerProbability,
      posterior: posterior,
      informationGain: informationGain,
      chooseNext: chooseNext,
      shouldStop: shouldStop,
      directionProbs: directionProbs,
      topAlgorithms: topAlgorithms,
      realtimeTop: realtimeTop,
      initialWeights: function () {
        // 与 Python initial_weights 对齐：先取非负先验，再做归一化。
        return normalize(algorithms.map(function (a) {
          return Math.max(0, a.prior_probability || 0);
        }));
      }
    };
  }

  global.EntropyEngine = { create: makeEngine };
})(window);
