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
    for (var k = 0; k < weights.length; k++) weights[k] /= total;
    return weights;
  }

  function entropy(weights) {
    var h = 0;
    for (var i = 0; i < weights.length; i++) {
      var w = weights[i];
      if (w > 0) h -= w * Math.log2(w);
    }
    return h;
  }

  function makeEngine(data) {
    var features = data.features || [];
    var algorithms = data.algorithms || [];
    var params = data.params || {};

    function profile(algIndex, fid) {
      var p = (algorithms[algIndex].profile || {})[fid];
      return (typeof p === "number") ? p : 0.5;
    }

    function answerProbability(weights, fid, answer) {
      var w = normalize(weights.slice());
      var s = 0;
      if (answer === "yes") {
        for (var i = 0; i < w.length; i++) s += w[i] * profile(i, fid);
      } else if (answer === "no") {
        for (var j = 0; j < w.length; j++) s += w[j] * (1 - profile(j, fid));
      } else {
        var decay = params.uncertain_decay == null ? 0.5 : params.uncertain_decay;
        s = decay * answerProbability(w, fid, "yes") + (1 - decay) * answerProbability(w, fid, "no");
      }
      return s;
    }

    function posterior(weights, fid, answer) {
      var w = normalize(weights.slice());
      if (answer === "uncertain") {
        var decay = params.uncertain_decay == null ? 0.5 : params.uncertain_decay;
        var wy = posterior(w, fid, "yes");
        var wn = posterior(w, fid, "no");
        var mix = [];
        for (var m = 0; m < wy.length; m++) mix.push(decay * wy[m] + (1 - decay) * wn[m]);
        return normalize(mix);
      }
      var out = [];
      for (var i = 0; i < w.length; i++) {
        var p = answer === "yes" ? profile(i, fid) : (1 - profile(i, fid));
        out.push(w[i] * p);
      }
      return normalize(out);
    }

    function informationGain(weights, fid) {
      var w = normalize(weights.slice());
      var py = answerProbability(w, fid, "yes");
      var pn = 1 - py;
      if (py <= 0 || pn <= 0) return 0;
      var hy = entropy(posterior(w, fid, "yes"));
      var hn = entropy(posterior(w, fid, "no"));
      return entropy(w) - (py * hy + pn * hn);
    }

    function chooseNext(weights, asked) {
      var bestId = null;
      var bestIg = -1;
      for (var i = 0; i < features.length; i++) {
        var fid = features[i].id;
        if (asked.indexOf(fid) >= 0) continue;
        var ig = informationGain(weights, fid);
        if (ig > bestIg) {
          bestIg = ig;
          bestId = fid;
        }
      }
      return { id: bestId, ig: bestIg };
    }

    function shouldStop(weights, asked) {
      var h = entropy(weights);
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
      var dirs = data.directions || [];
      var out = {};
      var total = 0;
      for (var d = 0; d < dirs.length; d++) {
        var name = dirs[d];
        var s = 0;
        for (var i = 0; i < w.length; i++) {
          s += w[i] * ((algorithms[i].direction_weights || {})[name] || 0);
        }
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
        return algorithms.map(function (a) { return Math.max(0, a.prior_probability || 0); });
      }
    };
  }

  global.EntropyEngine = { create: makeEngine };
})(window);
