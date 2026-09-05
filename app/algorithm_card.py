"""算法卡数据层：加载 PC 阶梯的“是什么 / 怎么写 / 复杂度 / C++ 代码”。

数据文件：``expert_content/algorithm_cards.json``（随 expert_content 资产打包）。
对外接口：
- ``load_cards() -> dict``：全部卡片，进程内缓存。
- ``cards_for_algorithms(algorithms: list[str]) -> list[tuple[str, dict]]``：按名称取卡片。
"""

from __future__ import annotations

import json

from resource_paths import find_data

DEFAULT_PATH = find_data("expert_content", "algorithm_cards.json")

_cache: dict | None = None


def load_cards() -> dict:
    """加载算法卡（进程内缓存）；文件缺失/损坏时返回空字典，不崩溃。"""
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(DEFAULT_PATH, encoding="utf-8") as f:
            data = json.load(f)
        cards = data.get("cards") if isinstance(data, dict) else None
        _cache = cards if isinstance(cards, dict) else {}
    except (OSError, ValueError):
        _cache = {}
    return _cache


def clear_cache() -> None:
    """清空缓存（测试用）。"""
    global _cache
    _cache = None


def cards_for_algorithms(algorithms: list[str]) -> list[tuple[str, dict]]:
    """返回 [ (算法名, 卡片), ... ]，保持传入顺序；无卡片则跳过。"""
    cards = load_cards()
    out: list[tuple[str, dict]] = []
    for name in algorithms:
        card = cards.get(name)
        if isinstance(card, dict):
            out.append((name, card))
    return out
