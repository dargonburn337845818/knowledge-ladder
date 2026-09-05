"""动态熵减决策引擎（纯本地 Python 实现）。

数据来源：
- algorithm_prior.json：初始先验 + 可调 params
- feature_algorithm_matrix.json：29 个特征问题（20 基础 + 9 教师共识）+ 120 算法 profile + 四方向权重

只使用 math.log2、加减乘除、归一化，不调用任何模型或外部 API。

性能设计：
- 构造函数把 profile / direction_weights 预计算成矩阵，避免每次更新都反复查 dict。
- feature_by_id 使用索引字典。
"""

import json
import math
import os

from resource_paths import find_data

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PRIOR = find_data("algorithm_prior.json")
DEFAULT_MATRIX = find_data("feature_algorithm_matrix.json")
DEFAULT_HEURISTICS = find_data("heuristics.json")


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

        # ---- 预计算矩阵：让每次更新只做乘法，不做 dict 查找 ----
        self._feature_index = {f["id"]: i for i, f in enumerate(self.features)}
        self._feature_ids = [f["id"] for f in self.features]
        # 列优先存储：每个特征一列 P(feature | algorithm)，
        # 避免遍历“算法 × 特征”时反复跨行访问。
        self._profile_columns = [
            [float(alg.get("profile", {}).get(fid, 0.5)) for alg in self.algorithms]
            for fid in self._feature_ids
        ]
        self._direction_columns = {
            d: [float(alg.get("direction_weights", {}).get(d, 0.0)) for alg in self.algorithms]
            for d in self.directions
        }

    # ---------- 基础工具 ----------
    def initial_weights(self):
        return _norm([max(0.0, a.get("prior_probability", 0)) for a in self.algorithms])

    def feature_by_id(self, fid):
        idx = self._feature_index.get(fid)
        if idx is None:
            return None
        return self.features[idx]

    def feature_index(self, fid):
        return self._feature_index.get(fid)

    def profile(self, alg_index, fid):
        """保留原接口：按特征 id 取 P(feature | algorithm)。"""
        idx = self._feature_index.get(fid)
        if idx is None:
            return 0.5
        return self._profile_columns[idx][alg_index]

    def entropy(self, weights):
        return _entropy(_norm(weights))

    def normalize(self, weights):
        return _norm(weights)

    def _py(self, fid_idx, w):
        """P(yes | feature) 对已归一化权重求和。"""
        column = self._profile_columns[fid_idx]
        total = 0.0
        for i, wi in enumerate(w):
            total += wi * column[i]
        return total

    def answer_probability(self, weights, fid, answer):
        if answer == "uncertain":
            # uncertain 的“惊讶度”按参数化弱证据混合期望
            decay = self.params.get("uncertain_decay", 0.5)
            py = self.answer_probability(weights, fid, "yes")
            pn = self.answer_probability(weights, fid, "no")
            return decay * py + (1.0 - decay) * pn
        w = self.normalize(weights)
        fid_idx = self._feature_index.get(fid)
        if fid_idx is None:
            return 1.0
        if answer == "yes":
            return self._py(fid_idx, w)
        return 1.0 - self._py(fid_idx, w)

    def _posterior_from_normalized(self, w, fid_idx, answer):
        if answer == "uncertain":
            decay = self.params.get("uncertain_decay", 0.5)
            wy = self._posterior_from_normalized(w, fid_idx, "yes")
            wn = self._posterior_from_normalized(w, fid_idx, "no")
            return self.normalize([decay * a + (1.0 - decay) * b for a, b in zip(wy, wn, strict=False)])
        column = self._profile_columns[fid_idx]
        out = []
        if answer == "yes":
            for i, wi in enumerate(w):
                out.append(wi * column[i])
        else:
            for i, wi in enumerate(w):
                out.append(wi * (1.0 - column[i]))
        return self.normalize(out)

    def posterior(self, weights, fid, answer):
        fid_idx = self._feature_index.get(fid)
        if fid_idx is None:
            return self.normalize(weights)
        w = self.normalize(weights)
        return self._posterior_from_normalized(w, fid_idx, answer)

    def information_gain(self, weights, fid):
        fid_idx = self._feature_index.get(fid)
        if fid_idx is None:
            return 0.0
        w = self.normalize(weights)
        py = self._py(fid_idx, w)
        pn = 1.0 - py
        if py <= 0 or pn <= 0:
            return 0.0
        hy = _entropy(self._posterior_from_normalized(w, fid_idx, "yes"))
        hn = _entropy(self._posterior_from_normalized(w, fid_idx, "no"))
        expected = py * hy + pn * hn
        return _entropy(w) - expected

    def choose_next(self, weights, asked):
        best_id = None
        best_ig = -1.0
        w = self.normalize(weights)
        w_entropy = _entropy(w)
        for fid_idx, fid in enumerate(self._feature_ids):
            if fid in asked:
                continue
            py = self._py(fid_idx, w)
            pn = 1.0 - py
            if py <= 0 or pn <= 0:
                continue
            hy = _entropy(self._posterior_from_normalized(w, fid_idx, "yes"))
            hn = _entropy(self._posterior_from_normalized(w, fid_idx, "no"))
            ig = w_entropy - (py * hy + pn * hn)
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
        for d, column in self._direction_columns.items():
            total = 0.0
            for i, wi in enumerate(w):
                total += wi * column[i]
            out[d] = total
        # 归一化，方便展示
        s = sum(out.values()) or 1.0
        return {d: v / s for d, v in out.items()}

    def top_directions(self, weights, top=4):
        probs = self.direction_probs(weights)
        return sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:top]
