"""内容有效性校验：检查拆题问题是否结构化、是否可执行、是否避免算法名/标签黑话。

运行：python scripts/validate_content.py
"""

import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANNED_PATTERNS = [
    r"是不是.*(算法|题|标签)",
    r"是否属于",
    r"是不是.*类题",
    r"\b(DP|Dp|BFS|DFS|KMP|SAM|Treap|BIT)\b",
    r"\b(dp|dfs|bfs|kmp|sam|treap|bit)\b",
]


def load(name):
    with open(os.path.join(REPO_ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def check_question(q):
    errors = []
    text = q.get("question", "")
    if len(text) < 8:
        errors.append("question too short")
    if len(text) > 60:
        errors.append(f"question too long: {text}")
    for pat in BANNED_PATTERNS:
        if re.search(pat, text):
            errors.append(f"question may leak algorithm/tag language: {text}")
    return errors


def main():
    errors = []
    matrix = load("feature_algorithm_matrix.json")
    heuristics = load("heuristics.json")

    for f in matrix.get("features", []):
        errors.extend(f"feature {f['id']}: {e}" for e in check_question(f))

    for d in heuristics.get("directions", []):
        for field in ("next_actions", "self_questions"):
            values = d.get(field, [])
            if not isinstance(values, list) or not values:
                errors.append(f"direction {d.get('id')} missing {field}")
            for item in values:
                if len(item) < 4:
                    errors.append(f"direction {d.get('id')} {field} item too short: {item}")

    teacher = load("teacher_consensus.json")
    for t in teacher.get("themes", []):
        if not t.get("trigger") or not t.get("action"):
            errors.append(f"teacher theme {t.get('id')} missing trigger/action")

    if errors:
        print("CONTENT VALIDATION FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("CONTENT VALIDATION OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
