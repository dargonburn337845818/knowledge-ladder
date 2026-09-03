# -*- coding: utf-8 -*-
"""纯数据工具：标签聚合、去重排序、总量常量。"""

from info_framework import (
    DYN_DYNAMIC,
    DYN_STATIC,
    INFO_OPS,
    TOPOLOGIES,
    get_alg_info,
)
from knowledge_data import ALGORITHM_BY_NAME
from tiers_data import TIERS

TOTAL_TAGS = sum(len(tier["tags"]) for tier in TIERS)


def _unique_in_order(values, order=None):
    """去重并尽量按 order 排序，保持界面标签稳定。"""
    seen = set()
    result = []
    for v in values:
        if v is None or v in seen:
            continue
        seen.add(v)
        result.append(v)
    if order:
        oi = {v: i for i, v in enumerate(order)}
        result.sort(key=lambda x: oi.get(x, len(order) + 1))
    return result


def aggregate_tag_info(tag):
    """聚合一个标签下所有算法的信息论视角，用于行内徽章和过滤。"""
    infos = []
    for name in tag.get("algorithms", []):
        alg = ALGORITHM_BY_NAME.get(name)
        if alg is not None:
            infos.append(alg.get("info", get_alg_info(name)))
    ops, topologies, dynamics, metrics = [], [], [], []
    for info in infos:
        ops.extend(info.get("ops", []))
        if info.get("topology"):
            topologies.append(info["topology"])
        if info.get("dynamic"):
            dynamics.append(info["dynamic"])
        if info.get("metric"):
            metrics.append(info["metric"])
    return {
        "ops": _unique_in_order(ops, INFO_OPS),
        "topologies": _unique_in_order(topologies, TOPOLOGIES),
        "dynamics": _unique_in_order(dynamics, [DYN_STATIC, DYN_DYNAMIC]),
        "metrics": _unique_in_order(metrics),
    }
