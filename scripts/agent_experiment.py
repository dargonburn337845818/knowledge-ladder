"""真实 Codeforces 题目的“代理 agent 引导实验”。

思路：
- 用真实 CF 题目的 tags 作为 ground truth 算法集合。
- 模拟一个“知道真实算法、但按结构性问题诚实回答”的代理 agent。
- 比较：
  * 无引导：随机从 120 个算法中猜，期望猜测次数 = 120 / 真算法数。
  * 有引导：按熵减引擎回答问题后，只看 Top-N 候选/方向。

这不是真人实验，但用于验证“引擎在真实题目上是否能把候选池收窄、方向是否对得上”。
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from entropy_engine import EntropyEngine

CASES = [
    ("1A", "Theatre Square", ["math"]),
    ("339A", "Helpful Maths", ["greedy", "implementation", "sortings", "strings"]),
    ("363B", "Fence", ["brute force", "dp"]),
    ("455A", "Boredom", ["dp"]),
    ("466C", "Number of Ways", ["binary search", "brute force", "data structures", "dp", "two pointers"]),
    ("489C", "Given Length and Sum of Digits", ["dp", "greedy", "implementation"]),
    ("580A", "Kefa and First Steps", ["brute force", "dp", "implementation"]),
    ("580C", "Kefa and Park", ["dfs and similar", "graphs", "trees"]),
    ("545C", "Woodcutters", ["dp", "greedy"]),
    ("913C", "Party Lemonade", ["bitmasks", "dp", "greedy"]),
    ("777C", "Alyona and Spreadsheet", ["binary search", "data structures", "dp", "greedy", "implementation", "two pointers"]),
]

TOP_LIMIT = 10
THRESHOLD = 0.01


def load_prior():
    with open(os.path.join(REPO_ROOT, "algorithm_prior.json"), encoding="utf-8") as f:
        return json.load(f)


def load_matrix():
    with open(os.path.join(REPO_ROOT, "feature_algorithm_matrix.json"), encoding="utf-8") as f:
        return json.load(f)


def main():
    prior = load_prior()
    matrix = load_matrix()
    matrix_by_name = {a["algorithm_name"]: a for a in matrix.get("algorithms", [])}
    engine = EntropyEngine()
    algorithms = prior.get("algorithms", [])
    total = len(algorithms)

    rows = []
    for cid, name, tags in CASES:
        true_algs = [
            a for a in algorithms
            if set(a.get("cf_tags", [])) & set(tags)
        ]
        if not true_algs:
            rows.append((cid, name, tags, "NO_MATCH", 0, 0, False, False, 0))
            continue
        # 选一个代表性真实算法：先验最高的
        rep = max(true_algs, key=lambda a: a.get("prior_probability", 0))
        rep_idx = next(i for i, a in enumerate(algorithms) if a["algorithm_name"] == rep["algorithm_name"])
        rep_matrix = matrix_by_name.get(rep["algorithm_name"], {})
        rep_direction = max(
            rep_matrix.get("direction_weights", {}).items(),
            key=lambda kv: kv[1],
        )[0] if rep_matrix.get("direction_weights") else None

        weights = engine.initial_weights()
        asked = []
        # 允许最多问 12 个问题；用真实算法的 profile 回答
        for _ in range(engine.params.get("max_questions", 12)):
            stop, _reason = engine.should_stop(weights, asked)
            if stop:
                break
            fid, _ig = engine.choose_next(weights, asked)
            if fid is None:
                break
            ans = "yes" if engine.profile(rep_idx, fid) >= 0.5 else "no"
            weights = engine.posterior(weights, fid, ans)
            asked.append(fid)

        top = engine.top_algorithms(weights, threshold=THRESHOLD, limit=TOP_LIMIT)
        top_names = [a["algorithm_name"] for a in top]
        hit = rep["algorithm_name"] in top_names
        dirs = engine.direction_probs(weights)
        top1_dir = max(dirs.items(), key=lambda kv: kv[1])[0] if dirs else None
        dir_hit = top1_dir == rep_direction

        blind_expected = total / max(1, len(true_algs))
        guided_candidates = len(top) if hit else TOP_LIMIT
        rows.append((cid, name, tags, rep["algorithm_name"], len(asked), blind_expected, guided_candidates, hit, dir_hit, top1_dir, rep_direction))

    # 汇总
    hits = [r for r in rows if r[0] != "NO_MATCH"]
    hit_rate = sum(1 for r in hits if r[7]) / len(hits) if hits else 0
    dir_rate = sum(1 for r in hits if r[8]) / len(hits) if hits else 0
    avg_blind = sum(r[5] for r in hits) / len(hits) if hits else 0
    avg_guided = sum(r[6] for r in hits) / len(hits) if hits else 0
    avg_q = sum(r[4] for r in hits) / len(hits) if hits else 0

    print("=== Agent Guidance Proxy Experiment ===")
    print(f"cases: {len(hits)} / {len(CASES)} with ground-truth algorithm")
    print(f"avg blind random guesses expected: {avg_blind:.1f}")
    print(f"avg guided candidates after questions: {avg_guided:.1f}")
    print(f"avg questions used: {avg_q:.1f}")
    print(f"true algorithm in top-{TOP_LIMIT}: {hit_rate:.0%}")
    print(f"top direction matches true direction: {dir_rate:.0%}")
    print()
    for cid, name, _tags, _rep, q, blind, guided, hit, dir_hit, t1, _rd in rows:
        if cid == "NO_MATCH":
            continue
        print(f"{cid:>5} {name[:34]:<34} q={q:>2} blind={blind:>6.1f} guided={guided:>3} hit={hit!s:>5} dir={dir_hit!s:>5} top1={t1}")

    # 有效性门槛（启发式）：真实算法应基本能进 Top10，方向也应基本对得上
    if hit_rate < 0.8 or dir_rate < 0.6:
        print("AGENT GUIDANCE EXPERIMENT: BELOW THRESHOLD")
        return 1
    print("AGENT GUIDANCE EXPERIMENT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
