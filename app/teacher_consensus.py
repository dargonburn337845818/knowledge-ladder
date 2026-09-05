"""教师共识数据层：加载 teacher-consensus-skill 蒸馏出的 24 条主题。

用途：
- 最终方向页展示“教师共识线索”，只给触发条件/动作/失效边界，不直接给算法名。
- 元纪律（人类接管、先判定再重构）独立于四大方向，作为引导入口。

对外接口：
- load() -> dict
- themes_for_direction(direction) -> list[dict]
- top_themes(probabilities, n=2) -> list[dict]
- meta_disciplines() -> list[dict]
"""

import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(REPO_ROOT, "teacher_consensus.json")

_cache = None


def load(path: str | None = None) -> dict:
    """加载教师共识 JSON，按进程缓存。"""
    global _cache
    if _cache is not None:
        return _cache
    path = path or DEFAULT_PATH
    with open(path, encoding="utf-8") as f:
        _cache = json.load(f)
    return _cache


def themes() -> list:
    return load().get("themes", [])


def meta_disciplines() -> list:
    return load().get("meta_disciplines", [])


def theme_by_id(theme_id: str):
    for t in themes():
        if t.get("id") == theme_id:
            return t
    return None


def themes_for_direction(direction: str) -> list:
    """返回指定方向下的教师共识主题，按置信度降序。"""
    rows = [t for t in themes() if t.get("direction") == direction]
    rows.sort(key=lambda t: t.get("confidence", 0.5), reverse=True)
    return rows


def top_themes(probabilities: dict, n: int = 2) -> list:
    """按方向概率加权从各方向取前 n 个主题。

    probabilities: {方向名: 0~1 概率}，通常来自 EntropyEngine.direction_probs()。
    返回的主题按权重降序，用于最终页的“教师共识线索”。
    """
    if not probabilities:
        return []
    scored = []
    for direction, prob in probabilities.items():
        for theme in themes_for_direction(direction):
            # 教师共识得分 = 方向概率 × 主题置信度；方向概率过低时不展示
            score = prob * theme.get("confidence", 0.5)
            scored.append((score, theme))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    seen = set()
    out = []
    for _score, theme in scored:
        if theme["id"] in seen:
            continue
        seen.add(theme["id"])
        out.append(theme)
        if len(out) >= n:
            break
    return out
