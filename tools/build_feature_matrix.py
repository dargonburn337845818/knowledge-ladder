# -*- coding: utf-8 -*-
"""阶段二：构建特征-算法条件概率矩阵 feature_algorithm_matrix.json。

数据源：
- 仓库 info_framework.py：每种算法的信息论视角（ops/topology/metric/dynamic/phase）
- algorithm_prior.json：120 个算法的多源先验
- 人工规则：规模/单调/前驱依赖/多次查询/离线预处理等排查维度

输出：
- feature_algorithm_matrix.json
- 设计文档《docs/system-design.md》中对矩阵结构的说明
"""

import json
import os
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PRIOR = os.path.join(REPO_ROOT, "algorithm_prior.json")
OUT = os.path.join(REPO_ROOT, "feature_algorithm_matrix.json")

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from info_framework import (  # noqa: E402
    ALGORITHM_INFO,
    OP_BASELINE,
    OP_ENCODE,
    OP_PROPAGATE,
    OP_PRUNE,
    OP_TRANSFORM,
)

FEATURES = [
    {"id": "shape_linear", "dimension": "形状", "question": "数据主体是线性/序列/区间结构吗？", "kind": "base"},
    {"id": "shape_graph", "dimension": "形状", "question": "数据主体是树/图/依赖结构吗？", "kind": "base"},
    {"id": "shape_algebra", "dimension": "形状", "question": "数据主体是抽象数学对象/集合/值域吗？", "kind": "base"},
    {"id": "dynamic", "dimension": "变化", "question": "运行过程中数据会修改、需要实时维护吗？", "kind": "base"},
    {"id": "metric_sum", "dimension": "规则", "question": "合并规则是加法/最值/路径权值吗？", "kind": "base"},
    {"id": "metric_xor", "dimension": "规则", "question": "核心涉及异或/线性独立/异或空间吗？", "kind": "base"},
    {"id": "metric_count", "dimension": "规则", "question": "需要计数/组合/卷积/方案数吗？", "kind": "base"},
    {"id": "metric_bool", "dimension": "规则", "question": "问题只问可行性/判定（布尔）吗？", "kind": "base"},
    {"id": "metric_geom", "dimension": "规则", "question": "核心是几何/向量/距离/凸性吗？", "kind": "base"},
    {"id": "metric_num", "dimension": "规则", "question": "核心是数论/模运算/整除/质数吗？", "kind": "base"},
    {"id": "scale_tiny", "dimension": "规模", "question": "n ≤ 20，可以状压/指数级枚举吗？", "kind": "base"},
    {"id": "scale_small", "dimension": "规模", "question": "n ≤ 5000，可以接受 O(n²)/O(n³) 吗？", "kind": "base"},
    {"id": "scale_large", "dimension": "规模", "question": "n ≥ 1e5，需要 O(n log n) 或更好吗？", "kind": "base"},
    {"id": "monotonic", "dimension": "排查", "question": "答案或可行性判定具有单调性，可以二分吗？", "kind": "extra"},
    {"id": "dependency", "dimension": "排查", "question": "当前状态依赖前驱/递推关系，需要按顺序传递吗？", "kind": "extra"},
    {"id": "multi_query", "dimension": "排查", "question": "有大量/多次查询，需要批量或数据结构维护吗？", "kind": "extra"},
    {"id": "preprocess", "dimension": "排查", "question": "允许离线/预处理来换取查询更快吗？", "kind": "extra"},
    {"id": "optimization", "dimension": "排查", "question": "求的是最优值/最值，而不只是可行性吗？", "kind": "extra"},
    {"id": "range_ops", "dimension": "排查", "question": "核心在线性序列的区间操作/区间查询上吗？", "kind": "extra"},
    {"id": "graph_path", "dimension": "排查", "question": "核心在树/图的路径、连通、最短路或流上吗？", "kind": "extra"},
]

DIRECTIONS = ["编码压缩", "传播松弛", "剪枝决策", "变换域映射"]

MONOTONIC_NAMES = {
    "二分查找", "二分答案", "双指针（滑动窗口）", "单调栈", "单调队列（滑动窗口）",
    "斜率优化（CHT）", "四边形不等式优化", "分治 DP", "最近点对（分治）",
    "Andrew 单调链凸包", "旋转卡壳", "半平面交", "最小圆覆盖",
}

MULTI_QUERY_NAMES = {
    "线段树（区间和 + 懒标记）", "树状数组 (BIT)", "树状数组求逆序对", "ST 表（静态区间最值）",
    "主席树（区间第 k 小）", "可持久化数据结构（主席树进阶）", "莫队（区间不同数）",
    "一维前缀和", "二维前缀和", "差分数组", "LCA（倍增）", "树链剖分 (HLD)", "线段树合并/分裂",
}

PREPROCESS_NAMES = {
    "一维前缀和", "二维前缀和", "差分数组", "ST 表（静态区间最值）", "后缀数组 (SA)",
    "AC 自动机", "Trie（字典树）", "字符串哈希（Rolling Hash）", "LCA（倍增）",
    "Manacher", "Z-function", "KMP", "莫队（区间不同数）", "结构体排序（重载运算符）",
    "归并排序求逆序对", "树上差分", "树链剖分 (HLD)",
}

RANGE_NAMES = {
    "一维前缀和", "二维前缀和", "差分数组", "线段树（区间和 + 懒标记）", "树状数组 (BIT)",
    "树状数组求逆序对", "ST 表（静态区间最值）", "主席树（区间第 k 小）",
    "可持久化数据结构（主席树进阶）", "莫队（区间不同数）", "LIS（最长上升子序列）",
    "LCS（最长公共子序列）", "石子合并", "双指针（滑动窗口）", "单调栈", "单调队列（滑动窗口）",
    "KMP", "字符串哈希（Rolling Hash）", "后缀数组 (SA)", "Manacher", "Z-function",
}

# 手动补丁：某些算法在“剪枝/松弛”上同时起作用（如单调队列优化 DP 时既剪枝又传递前驱最优值）
MANUAL_DEPENDENCY_NAMES = {
    "单调队列（滑动窗口）",
}

DIRECTION_PATCHES = {
    "单调队列（滑动窗口）": {"剪枝决策": 1.0, "传播松弛": 0.8},
    "LIS（最长上升子序列）": {"传播松弛": 1.0, "剪枝决策": 0.8},
    "分治 DP": {"剪枝决策": 1.0, "传播松弛": 0.8},
    "四边形不等式优化": {"剪枝决策": 1.0, "传播松弛": 0.8},
}


def p_yes_from_metric(metric: str, keywords) -> float:
    if not metric:
        return 0.2
    if any(k in metric for k in keywords):
        return 0.9
    return 0.1


def scale_tiny(name: str, sub: str) -> float:
    keys = ("状压", "TSP", "位掩码", "插头", "轮廓线", "Nim", "子集")
    if any(k in name or k in sub for k in keys):
        return 0.85
    return 0.1


def scale_small(name: str, sub: str) -> float:
    small_subs = {
        "区间 DP", "DP 优化", "线性 DP", "数位 DP", "轮廓线 DP", "插头 DP", "DP 套 DP",
        "矩阵快速幂", "组合数学", "快速幂与逆元", "GCD / LCM", "素数筛", "博弈论",
    }
    if sub in small_subs or any(k in name for k in ("Floyd", "KM", "高斯消元", "中国剩余定理", "Lucas", "背包", "LIS", "LCS")):
        return 0.75
    return 0.25


def scale_large(name: str, sub: str) -> float:
    large_subs = {
        "线段树", "树状数组", "高级数据结构", "可持久化", "后缀结构", "模式匹配", "多模式匹配",
        "哈希与字典树", "最短路", "最小生成树", "网络流", "树上基础", "进阶树论", "树分治",
        "离线动态图", "支配树", "多项式", "组合计数", "反演", "凸包", "最近点对", "半平面交",
        "二分", "双指针", "排序", "莫队", "主席树", "字符串", "动态树", "树链剖分",
        "栈", "队列", "堆",
    }
    if sub in large_subs or any(k in name for k in ("FFT", "NTT", "线段树", "树状数组", "后缀", "SAM", "AC 自动机", "莫队", "LCA", "Dijkstra", "Tarjan", "Dinic", "点分治", "二分")):
        return 0.8
    return 0.2


def build_profile(name: str, info: dict, sub: str = "") -> dict:
    ops = set(info.get("ops", []))
    topology = info.get("topology", "")
    metric = info.get("metric", "")
    dynamic = info.get("dynamic", "")

    profile = {}
    # 形状
    profile["shape_linear"] = 0.9 if topology == "线性" else 0.05
    profile["shape_graph"] = 0.9 if topology == "树图" else 0.05
    profile["shape_algebra"] = 0.9 if topology == "抽象代数" else 0.05
    # 动静
    profile["dynamic"] = 0.9 if dynamic == "动态" else 0.1
    # 度量
    profile["metric_sum"] = p_yes_from_metric(metric, ("加法", "最值", "路径", "费用", "容量"))
    profile["metric_xor"] = p_yes_from_metric(metric, ("异或", "线性基", "线性无关"))
    profile["metric_count"] = p_yes_from_metric(metric, ("计数", "长度", "方案", "组合"))
    profile["metric_bool"] = p_yes_from_metric(metric, ("布尔", "可行", "连通", "匹配", "判定"))
    profile["metric_geom"] = p_yes_from_metric(metric, ("几何", "距离", "凸", "向量"))
    profile["metric_num"] = p_yes_from_metric(metric, ("数论", "模", "同余", "质", "整除", "素数"))
    # 规模
    profile["scale_tiny"] = scale_tiny(name, sub)
    profile["scale_small"] = scale_small(name, sub)
    profile["scale_large"] = scale_large(name, sub)
    # 排查维度
    profile["monotonic"] = 0.85 if name in MONOTONIC_NAMES else 0.15
    profile["dependency"] = 0.85 if name in MANUAL_DEPENDENCY_NAMES or OP_PROPAGATE in ops else 0.15
    profile["multi_query"] = 0.85 if name in MULTI_QUERY_NAMES else 0.15
    profile["preprocess"] = 0.85 if name in PREPROCESS_NAMES else 0.15
    profile["optimization"] = 0.9 if ("布尔" not in metric and "可行" not in metric) else 0.2
    profile["range_ops"] = 0.85 if name in RANGE_NAMES or "区间" in name else 0.15
    profile["graph_path"] = 0.85 if topology == "树图" else 0.1

    # 四方向权重（由信息论 ops 生成，供最终/异常卡片使用）
    weights = {d: 0.05 for d in DIRECTIONS}
    if OP_ENCODE in ops:
        weights["编码压缩"] = 1.0
    if OP_PROPAGATE in ops:
        weights["传播松弛"] = 1.0
    if OP_PRUNE in ops:
        weights["剪枝决策"] = 1.0
    if OP_TRANSFORM in ops:
        weights["变换域映射"] = 1.0
    if OP_BASELINE in ops and not any(op in ops for op in (OP_ENCODE, OP_PROPAGATE, OP_PRUNE, OP_TRANSFORM)):
        # 纯暴力给四个方向都留一点，避免最终无卡片；仍以“基线/暴力”为最低权重
        for d in DIRECTIONS:
            weights[d] = 0.35
    if name in DIRECTION_PATCHES:
        weights.update(DIRECTION_PATCHES[name])
    return {"profile": profile, "direction_weights": weights}


def main():
    with open(SRC_PRIOR, encoding="utf-8") as f:
        prior = json.load(f)

    prior_by_name = {a["algorithm_name"]: a for a in prior["algorithms"]}

    algorithms = []
    for a in prior["algorithms"]:
        name = a["algorithm_name"]
        info = ALGORITHM_INFO.get(name, {})
        built = build_profile(name, info, a.get("sub", ""))
        algorithms.append({
            "algorithm_name": name,
            "category": a.get("category", ""),
            "sub": a.get("sub", ""),
            "cf_tags": a.get("cf_tags", []),
            "dmoj_types": a.get("dmoj_types", []),
            "prior_probability": a.get("prior_probability", 0),
            **built,
        })

    data = {
        "meta": {
            "version": "0.1.0",
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "description": "条件概率矩阵 P(feature|algorithm)。在熵减更新中以贝叶斯方式使用：P(algorithm|answer) ∝ P(algorithm) * P(feature|algorithm)。",
            "source": ["info_framework.py", "algorithm_prior.json", "人工排查规则"],
        },
        "features": FEATURES,
        "directions": DIRECTIONS,
        "algorithms": algorithms,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")
    print(f"features={len(FEATURES)} algorithms={len(algorithms)} direction={len(DIRECTIONS)}")


if __name__ == "__main__":
    main()
