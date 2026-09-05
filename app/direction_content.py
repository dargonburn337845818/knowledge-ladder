"""四方向专家内容数据层：加载方向卡片/反例边界/专家深挖内容。

用途：
- 桌面端统一从 `expert_content/direction_cards_v1.json` 读取方向内容，避免硬编码漂移。
- 提供旧 `heuristics.json` 字段（summary/signals/next_actions/self_questions）的兼容视图与迁移桥。
- 不修改 EntropyEngine 公开接口；本模块只做内容读取与轻量映射。

对外接口：
- load() -> dict                     加载完整内容资产（进程缓存）
- directions() -> list[dict]         四个方向列表
- direction_by_id(direction_id) -> dict | None
- direction_by_title(title) -> dict | None
- legacy_heuristics() -> dict        加载旧 heuristics.json（兼容）
- legacy_direction_by_title(title) -> dict | None
- legacy_view(direction) -> dict     将新方向映射为旧字段形状
"""

import json

from resource_paths import find_data

DEFAULT_PATH = find_data("expert_content", "direction_cards_v1.json")
LEGACY_PATH = find_data("heuristics.json")

_cache = None
_legacy_cache = None


def load(path: str | None = None) -> dict:
    """加载方向内容资产，进程内缓存。"""
    global _cache
    if _cache is not None:
        return _cache
    path = path or DEFAULT_PATH
    with open(path, encoding="utf-8") as f:
        _cache = json.load(f)
    return _cache


def clear_cache() -> None:
    """清空缓存（测试用）。"""
    global _cache, _legacy_cache
    _cache = None
    _legacy_cache = None


def directions() -> list:
    return load().get("directions", [])


def direction_by_id(direction_id: str):
    for d in directions():
        if d.get("id") == direction_id:
            return d
    return None


def direction_by_title(title: str):
    for d in directions():
        if d.get("title") == title:
            return d
    return None


def legacy_heuristics() -> dict:
    """加载旧 heuristics.json；仅用于兼容读取，不参与新主流程。"""
    global _legacy_cache
    if _legacy_cache is not None:
        return _legacy_cache
    with open(LEGACY_PATH, encoding="utf-8") as f:
        _legacy_cache = json.load(f)
    return _legacy_cache


def legacy_direction_by_title(title: str):
    for d in legacy_heuristics().get("directions", []):
        if d.get("title") == title or d.get("id") == title:
            return d
    return None


def legacy_view(direction: dict) -> dict:
    """把新方向内容映射为旧 heuristics 方向字段形状。

    旧字段 → 新字段：
    - summary            → value
    - signals            → triggers
    - next_actions       → layers.action
    - self_questions     → layers.self_question
    - dynamic_template   → 保留在 heuristics.json，不迁移
    """
    layers = direction.get("layers", {})
    return {
        "id": direction.get("title", ""),
        "title": direction.get("title", ""),
        "summary": direction.get("value", ""),
        "signals": list(direction.get("triggers", [])),
        "next_actions": [layers["action"]] if layers.get("action") else [],
        "self_questions": [layers["self_question"]] if layers.get("self_question") else [],
    }
