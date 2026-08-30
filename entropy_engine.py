# -*- coding: utf-8 -*-
"""动态熵减决策引擎（纯本地 Python 实现）。

数据来源：
- algorithm_prior.json：初始先验 + 可调 params
- feature_algorithm_matrix.json：20 个特征问题 + 120 算法 profile + 四方向权重

只使用 math.log2、加减乘除、归一化，不调用任何模型或外部 API。
"""

import json
import math
import os

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PRIOR = os.path.join(REPO_ROOT, "algorithm_prior.json")
DEFAULT_MATRIX = os.path.join(REPO_ROOT, "feature_algorithm_matrix.json")
DEFAULT_HEURISTICS = os.path.join(REPO_ROOT, "heuristics.json")


def _norm(weights):
    total = sum(weights)
    if total <= 0:
        n = len(weights)
        return [1.0 / n] * n if n else []
    return [w / total for w in weights]


def _entropy(weights):
    h = 0.0
    for w in weights:
        if w > 0:
            h -= w * math.log2(w)
    return h


class EntropyEngine:
    def __init__(self, prior_path=None, matrix_path=None, heuristics_path=None):
        prior_path = prior_path or DEFAULT_PRIOR
        matrix_path = matrix_path or DEFAULT_MATRIX
        heuristics_path = heuristics_path or DEFAULT_HEURISTICS
        with open(prior_path, encoding="utf-8") as f:
            self.prior = json.load(f)
        with open(matrix_path, encoding="utf-8") as f:
            self.matrix = json.load(f)
        with open(heuristics_path, encoding="utf-8") as f:
            self.heuristics = json.load(f)

        self.params = self.prior.get("params", {})
        self.features = self.matrix.get("features", [])
        self.directions = self.matrix.get("directions", [])
        self.algorithms = self.matrix.get("algorithms", [])

        priors = {a["algorithm_name"]: a.get("prior_probability", 0) for a in self.prior.get("algorithms", [])}
        for alg in self.algorithms:
            alg.setdefault("prior_probability", priors.get(alg["algorithm_name"], 0))

        self._weights_cache = None

    # ---------- 基础工具 ----------
    def initial_weights(self):
        return [max(0.0, a.get("prior_probability", 0)) for a in self.algorithms]

    def feature_by_id(self, fid):
        for f in self.features:
            if f["id"] == fid:
                return f
        return None

    def profile(self, alg_index, fid):
        return float(self.algorithms[alg_index].get("profile", {}).get(fid, 0.5))

    def entropy(self, weights):
        return _entropy(_norm(weights))

    def normalize(self, weights):
        return _norm(weights)

    def answer_probability(self, weights, fid, answer):
        w = self.normalize(weights)
        if answer == "yes":
            return sum(wi * self.profile(i, fid) for i, wi in enumerate(w))
        if answer == "no":
            return sum(wi * (1.0 - self.profile(i, fid)) for i, wi in enumerate(w))
        # uncertain 的“惊讶度”按参数化弱证据混合期望
        decay = self.params.get("uncertain_decay", 0.5)
        py = self.answer_probability(weights, fid, "yes")
        pn = self.answer_probability(weights, fid, "no")
        return decay * py + (1.0 - decay) * pn

    def posterior(self, weights, fid, answer):
        w = self.normalize(weights)
        if answer == "yes":
            out = [wi * self.profile(i, fid) for i, wi in enumerate(w)]
        elif answer == "no":
            out = [wi * (1.0 - self.profile(i, fid)) for i, wi in enumerate(w)]
        else:  # uncertain
            decay = self.params.get("uncertain_decay", 0.5)
            wy = self.posterior(weights, fid, "yes")
            wn = self.posterior(weights, fid, "no")
            out = [decay * a + (1.0 - decay) * b for a, b in zip(wy, wn)]
        return self.normalize(out)

    def information_gain(self, weights, fid):
        w = self.normalize(weights)
        py = self.answer_probability(w, fid, "yes")
        pn = 1.0 - py
        if py <= 0 or pn <= 0:
            return 0.0
        hy = self.entropy(self.posterior(w, fid, "yes"))
        hn = self.entropy(self.posterior(w, fid, "no"))
        expected = py * hy + pn * hn
        return self.entropy(w) - expected

    def choose_next(self, weights, asked):
        best_id = None
        best_ig = -1.0
        for f in self.features:
            fid = f["id"]
            if fid in asked:
                continue
            ig = self.information_gain(weights, fid)
            if ig > best_ig:
                best_ig = ig
                best_id = fid
        return best_id, best_ig

    def should_stop(self, weights, asked):
        h = self.entropy(weights)
        if h < self.params.get("entropy_stop_threshold", 0.45):
            return True, "entropy"
        if len(asked) >= self.params.get("max_questions", 12):
            return True, "max_questions"
        best_id, best_ig = self.choose_next(weights, asked)
        if best_id is None:
            return True, "exhausted"
        if best_ig < self.params.get("ig_stop_threshold", 0.03):
            return True, "ig"
        return False, best_id

    def answer(self, weights, asked, fid, answer):
        new_weights = self.posterior(weights, fid, answer)
        surprise = self.answer_probability(weights, fid, answer)
        new_asked = list(asked) + [fid]
        return new_weights, new_asked, surprise


    def heuristic_direction(self, name):
        for h in self.heuristics.get("directions", []):
            if h.get("id") == name:
                return h
        return None

    def top_algorithms(self, weights, threshold=None, limit=None):
        """返回后验权重 >= threshold 的候选算法（按权重降序），threshold 默认取 params。"""
        if threshold is None:
            threshold = self.params.get("algorithm_weight_threshold", 0.02)
        if limit is None:
            limit = self.params.get("max_algorithm_list", 12)
        w = self.normalize(weights)
        rows = []
        for i, wi in enumerate(w):
            if wi >= threshold:
                rows.append({
                    "algorithm_name": self.algorithms[i]["algorithm_name"],
                    "weight": wi,
                })
        rows.sort(key=lambda r: r["weight"], reverse=True)
        return rows[:limit]

    def realtime_top(self, weights, n=None):
        """问题流实时展示用的 Top N 候选算法。"""
        if n is None:
            n = self.params.get("realtime_top_n", 3)
        w = self.normalize(weights)
        rows = sorted(
            ({"algorithm_name": self.algorithms[i]["algorithm_name"], "weight": wi}
             for i, wi in enumerate(w)),
            key=lambda r: r["weight"], reverse=True,
        )
        return rows[:n]

    def direction_probs(self, weights):
        w = self.normalize(weights)
        out = {}
        for d in self.directions:
            total = 0.0
            for i, wi in enumerate(w):
                total += wi * float(self.algorithms[i].get("direction_weights", {}).get(d, 0.0))
            out[d] = total
        # 归一化，方便展示
        s = sum(out.values()) or 1.0
        return {d: v / s for d, v in out.items()}

    def top_directions(self, weights, top=4):
        probs = self.direction_probs(weights)
        return sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:top]
