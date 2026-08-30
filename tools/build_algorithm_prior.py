# -*- coding: utf-8 -*-
"""阶段一：汇总可信公开数据源，构建先验熵词典 algorithm_prior.json。

数据源（全部为公开 API / 公开数据集，运行时不做模型推理，只做本地统计）：
- Codeforces 官方 API：problemset.problems（标签 + rating + solvedCount）
- DMOJ 公开 API v2：算法类型（21 类）+ points
- AtCoder Problems（kenkoooo）公开数据集：题目难度模型

输出：
- algorithm_prior.json（静态先验熵词典）
- reports/stage1_cleaning_report.md（清洗报告）
"""

import json
import os
import statistics
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(REPO_ROOT, "algorithm_prior.json")
OUT_REPORT = os.path.join(REPO_ROOT, "reports", "stage1_cleaning_report.md")

CF_API = "https://codeforces.com/api/problemset.problems"
DMOJ_API = "https://dmoj.ca/api/v2/problems?page={}"
ATCODER_PROBLEMS = "https://kenkoooo.com/atcoder/resources/problems.json"
ATCODER_MODELS = "https://kenkoooo.com/atcoder/resources/problem-models.json"

# 本地 120 算法映射：来自 tiers_data 的 cf_tag 关联；缺少的 3 个前缀和/差分手工补上。
MANUAL_CF_TAGS = {
    "一维前缀和": ["data structures"],
    "二维前缀和": ["data structures"],
    "差分数组": ["data structures"],
}

# DMOJ 类型 -> 本地算法的粗粒度映射（按 category/sub 自动归类，允许手工微调）。
# 这里只用于“多源先验估算”，最终界面仍以中文四大方向 + 本地 120 算法为准。
DMOJ_TYPE_BY_CATEGORY = {
    "数据结构": ["Data Structures"],
    "图论": ["Graph Theory"],
    "树": ["Graph Theory"],
    "动态规划": ["Dynamic Programming"],
    "字符串": ["String Algorithms"],
    "计算几何": ["Geometry"],
    "网络流": ["Graph Theory"],
    "矩阵": ["Advanced Math"],
    "数学": ["Advanced Math"],
    "数论": ["Advanced Math"],
    "其他": ["Ad Hoc"],
    "基础算法": [],
}

DMOJ_TYPE_BY_SUB = {
    "枚举": ["Brute Force"],
    "模拟": ["Simulation"],
    "贪心": ["Greedy Algorithms"],
    "构造": ["Constructive"],
    "分治": ["Divide and Conquer"],
    "位运算": ["Ad Hoc"],
    "排序": ["Implementation"],
    "二分": ["Implementation"],
    "双指针": ["Implementation"],
    "前缀和与差分": ["Data Structures"],
    "博弈论": ["Game Theory"],
    "概率期望": ["Ad Hoc"],
    "莫队": ["Data Structures"],
    "主席树": ["Data Structures"],
    "动态树": ["Data Structures"],
    "树链剖分": ["Data Structures"],
    "可持久化": ["Data Structures"],
    "后缀结构": ["String Algorithms"],
    "模式匹配": ["String Algorithms"],
    "多模式匹配": ["String Algorithms"],
    "哈希与字典树": ["String Algorithms"],
    "多项式": ["Advanced Math"],
    "组合计数": ["Advanced Math"],
    "反演": ["Advanced Math"],
    "线性基进阶": ["Advanced Math"],
    "凸包": ["Geometry"],
    "最近点对": ["Geometry"],
    "线段相交": ["Geometry"],
    "向量基础": ["Geometry"],
    "圆": ["Geometry"],
    "三维": ["Geometry"],
    "半平面交": ["Geometry"],
    "网络流": ["Graph Theory"],
    "上下界网络流": ["Graph Theory"],
    "费用流": ["Graph Theory"],
    "最短路": ["Graph Theory"],
    "最小生成树": ["Graph Theory"],
    "强连通分量": ["Graph Theory"],
    "拓扑序": ["Graph Theory"],
    "DFS / BFS": ["Graph Theory"],
    "进阶图论": ["Graph Theory"],
    "树形 DP": ["Dynamic Programming"],
    "区间 DP": ["Dynamic Programming"],
    "状压 DP": ["Dynamic Programming"],
    "数位 DP": ["Dynamic Programming"],
    "DP 优化": ["Dynamic Programming"],
    "轮廓线 DP": ["Dynamic Programming"],
    "插头 DP": ["Dynamic Programming"],
    "DP 套 DP": ["Dynamic Programming"],
    "分治 DP": ["Dynamic Programming"],
    "树上基础": ["Graph Theory"],
    "进阶树论": ["Graph Theory"],
    "树分治": ["Graph Theory", "Divide and Conquer"],
    "离线动态图": ["Graph Theory"],
    "支配树": ["Graph Theory"],
}


def load_tier_mapping():
    """从 tiers_data 中提取 算法名 -> CF 标签集合 的映射。"""
    sys.path.insert(0, REPO_ROOT)
    from tiers_data import TIERS

    mapping = defaultdict(set)
    for tier in TIERS:
        for tag in tier["tags"]:
            cf = tag.get("cf_tag")
            if not cf:
                continue
            for alg in tag.get("algorithms", []):
                mapping[alg].add(cf)
    for alg, tags in MANUAL_CF_TAGS.items():
        mapping[alg].update(tags)
    return mapping


def fetch_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "knowledge-ladder/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_codeforces():
    print("Fetching Codeforces problemset.problems ...")
    data = fetch_json(CF_API)
    if data.get("status") != "OK":
        raise RuntimeError(f"CF API status: {data.get('status')}")
    return data["result"]


def fetch_dmoj():
    print("Fetching DMOJ API (all pages) ...")
    objects = []
    page = 1
    while True:
        data = fetch_json(DMOJ_API.format(page))
        info = data.get("data", {})
        objects.extend(info.get("objects", []))
        total_pages = info.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1
    return objects


def fetch_atcoder():
    print("Fetching AtCoder Problems datasets ...")
    problems = fetch_json(ATCODER_PROBLEMS)
    models = fetch_json(ATCODER_MODELS)
    return problems, models


def combine_cf(result):
    stats = {(s["contestId"], s["index"]): s.get("solvedCount", 0) for s in result.get("problemStatistics", [])}
    problems = []
    for p in result.get("problems", []):
        key = (p.get("contestId"), p.get("index"))
        problems.append({
            "contestId": p.get("contestId"),
            "index": p.get("index"),
            "name": p.get("name"),
            "rating": p.get("rating"),
            "tags": list(p.get("tags", [])),
            "solvedCount": stats.get(key, 0),
        })
    return problems


def agg_diff(values):
    if not values:
        return None
    vs = sorted(values)
    return {
        "min": vs[0],
        "max": vs[-1],
        "median": round(statistics.median(vs), 1),
        "q1": round(statistics.quantiles(vs, n=4)[0], 1) if len(vs) >= 4 else vs[0],
        "q3": round(statistics.quantiles(vs, n=4)[2], 1) if len(vs) >= 4 else vs[-1],
        "sample_count": len(vs),
    }


def dmoj_types_for_algorithm(name, category, sub):
    types = set(DMOJ_TYPE_BY_CATEGORY.get(category, []))
    types.update(DMOJ_TYPE_BY_SUB.get(sub, []))
    # 少量精确补丁
    if name in ("并查集 (DSU)", "带权并查集", "可撤销并查集"):
        types.add("Data Structures")
    if name in ("二分查找", "二分答案"):
        types.add("Divide and Conquer")
    if name in ("状态压缩 + BFS", "TSP（状压）", "位掩码子集枚举"):
        types.add("Brute Force")
    if name in ("AC 自动机 + 矩阵快速幂", "矩阵快速幂优化递推", "FFT", "NTT"):
        types.add("Advanced Math")
    if name in ("最小费用最大流", "Dinic 最大流", "上下界网络流"):
        types.add("Graph Theory")
    return sorted(types)


def main():
    # ---------- 拉取 ----------
    cf_result = fetch_codeforces()
    cf_problems = combine_cf(cf_result)
    dmoj_objects = fetch_dmoj()
    atcoder_problems, atcoder_models = fetch_atcoder()

    # ---------- CF 统计 ----------
    total_cf = len(cf_problems)
    cf_tagged = [p for p in cf_problems if p["tags"]]
    cf_rated = [p for p in cf_problems if p.get("rating")]
    total_tag_occurrences = sum(len(p["tags"]) for p in cf_tagged)

    tag_count = Counter()
    tag_rated = defaultdict(list)
    tag_solved = Counter()
    for p in cf_tagged:
        for t in p["tags"]:
            tag_count[t] += 1
            tag_rated[t].append(p["rating"])
            tag_solved[t] += p.get("solvedCount", 0)

    tags = []
    for t, freq in tag_count.most_common():
        ratings = [r for r in tag_rated[t] if r]
        tags.append({
            "tag": t,
            "frequency": freq,
            "probability_per_problem": round(freq / len(cf_tagged), 6) if cf_tagged else 0,
            "probability_per_tag_occurrence": round(freq / total_tag_occurrences, 6) if total_tag_occurrences else 0,
            "difficulty_range": agg_diff(ratings),
            "solved_count_sum": tag_solved[t],
        })

    pair_count = Counter()
    triple_count = Counter()
    for p in cf_tagged:
        ts = sorted(set(p["tags"]))
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                pair_count[(ts[i], ts[j])] += 1
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                for k in range(j + 1, len(ts)):
                    triple_count[(ts[i], ts[j], ts[k])] += 1

    freq_by_tag = dict(tag_count)
    pairs = []
    for (a, b), freq in pair_count.most_common():
        pairs.append({
            "pair": [a, b],
            "frequency": freq,
            "probability": round(freq / len(cf_tagged), 6) if cf_tagged else 0,
            "cond_a_given_b": round(freq / freq_by_tag[b], 6) if freq_by_tag.get(b) else 0,
            "cond_b_given_a": round(freq / freq_by_tag[a], 6) if freq_by_tag.get(a) else 0,
        })
    triples = []
    for (a, b, c), freq in triple_count.most_common(200):
        triples.append({"triple": [a, b, c], "frequency": freq,
                        "probability": round(freq / len(cf_tagged), 6) if cf_tagged else 0})

    # ---------- DMOJ 统计 ----------
    total_dmoj = len(dmoj_objects)
    dmoj_type_count = Counter()
    dmoj_type_points = defaultdict(list)
    for obj in dmoj_objects:
        types = obj.get("types", [])
        if not types:
            continue
        for t in types:
            dmoj_type_count[t] += 1
            dmoj_type_points[t].append(obj.get("points"))

    dmoj_types = []
    for t, freq in dmoj_type_count.most_common():
        pts = [p for p in dmoj_type_points[t] if p is not None]
        dmoj_types.append({
            "type": t,
            "frequency": freq,
            "probability_per_problem": round(freq / total_dmoj, 6) if total_dmoj else 0,
            "points_range": agg_diff(pts),
        })

    # ---------- AtCoder 统计 ----------
    atcoder_with_diff = []
    for pid, model in atcoder_models.items():
        if isinstance(model, dict) and model.get("difficulty") is not None:
            atcoder_with_diff.append(model["difficulty"])
    atcoder_summary = {
        "problem_count": len(atcoder_problems),
        "model_count": len(atcoder_models),
        "difficulty_model_count": len(atcoder_with_diff),
        "difficulty_range": agg_diff(atcoder_with_diff) if atcoder_with_diff else None,
    }

    # ---------- 本地 120 算法多源先验 ----------
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from knowledge_data import ALGORITHMS
    tier_mapping = load_tier_mapping()

    algorithms = []
    for alg in ALGORITHMS:
        name = alg["name"]
        category = alg.get("category", "")
        sub = alg.get("sub", "")
        cf_tags = sorted(tier_mapping.get(name, []))
        dmoj_ts = dmoj_types_for_algorithm(name, category, sub)

        cf_freqs = [tag_count[t] for t in cf_tags if t in tag_count]
        cf_freq = round(sum(cf_freqs) / len(cf_freqs), 2) if cf_freqs else 0
        dmoj_freqs = [dmoj_type_count[t] for t in dmoj_ts if t in dmoj_type_count]
        dmoj_freq = round(sum(dmoj_freqs) / len(dmoj_freqs), 2) if dmoj_freqs else 0

        cf_ratings = []
        for t in cf_tags:
            cf_ratings.extend([r for r in tag_rated[t] if r])
        dmoj_pts = []
        for t in dmoj_ts:
            dmoj_pts.extend([p for p in dmoj_type_points[t] if p is not None])

        algorithms.append({
            "algorithm_name": name,
            "category": category,
            "sub": sub,
            "cf_tags": cf_tags,
            "dmoj_types": dmoj_ts,
            "cf_frequency": cf_freq,
            "dmoj_frequency": dmoj_freq,
            "frequency": round((cf_freq + dmoj_freq) / 2, 2),
            "difficulty_range_cf": agg_diff(cf_ratings),
            "difficulty_range_dmoj": agg_diff(dmoj_pts),
            "mapping_source": "tiers_data + manual" if name in MANUAL_CF_TAGS else "tiers_data",
        })

    # 三种先验：CF 归一化 / DMOJ 归一化 / 综合（各 50%）
    sum_cf = sum(a["cf_frequency"] for a in algorithms) or 1.0
    sum_dmoj = sum(a["dmoj_frequency"] for a in algorithms) or 1.0
    for a in algorithms:
        a["prior_cf"] = round(a["cf_frequency"] / sum_cf, 6)
        a["prior_dmoj"] = round(a["dmoj_frequency"] / sum_dmoj, 6)
    sum_mix = sum((a["prior_cf"] + a["prior_dmoj"]) / 2 for a in algorithms) or 1.0
    for a in algorithms:
        a["prior_probability"] = round(((a["prior_cf"] + a["prior_dmoj"]) / 2) / sum_mix, 6)

    params = {
        "entropy_stop_threshold": 0.45,
        "ig_stop_threshold": 0.03,
        "detector_entropy_threshold": 0.30,
        "anomaly_surprise_threshold": 0.85,
        "uncertain_decay": 0.5,
        "max_questions": 12,
        "baseline_required": True,
        "algorithm_weight_threshold": 0.02,
        "realtime_top_n": 3,
        "max_algorithm_list": 12,
    }

    data = {
        "meta": {
            "version": "0.2.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "codeforces": {
                    "endpoint": CF_API,
                    "problem_count": total_cf,
                    "tagged_problem_count": len(cf_tagged),
                    "rated_problem_count": len(cf_rated),
                    "tag_occurrence_count": total_tag_occurrences,
                },
                "dmoj": {
                    "endpoint": "https://dmoj.ca/api/v2/problems",
                    "problem_count": total_dmoj,
                    "type_count": len(dmoj_types),
                },
                "atcoder_problems": {
                    "endpoint": ATCODER_PROBLEMS,
                    "problem_count": len(atcoder_problems),
                    "model_count": len(atcoder_models),
                },
                "luogu": {
                    "status": "not_included",
                    "note": "按用户确认不接入洛谷。",
                },
            },
            "cleaning": [
                "Codeforces problemset.problems 与 problemStatistics 按 (contestId,index) 合并",
                "仅保留带标签的 CF 题目参与标签/组合统计",
                "CF 难度统计只使用有 rating 的题目",
                "DMOJ 仅统计带 types 的题目，points 作为难度代理",
                "AtCoder 仅使用有 difficulty 的 model，不参与标签分类",
                "本地算法先验 = CF 标签频率映射 + DMOJ 类型频率映射的 50/50 综合",
                "洛谷不接入",
            ],
        },
        "params": params,
        "tags": tags,
        "pairs": pairs,
        "triples": triples,
        "dmoj_types": dmoj_types,
        "atcoder": atcoder_summary,
        "algorithms": algorithms,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- 报告 ----------
    os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
    lines = []
    lines.append("# 阶段一清洗报告：多源先验熵词典")
    lines.append("")
    lines.append(f"- 生成时间：{data['meta']['generated_at']}")
    lines.append("- 数据源：Codeforces 官方 API、DMOJ 公开 API v2、AtCoder Problems（kenkoooo）")
    lines.append("- 洛谷：按用户确认不接入。")
    lines.append("")
    lines.append("## 规模")
    lines.append("")
    lines.append(f"- CF 题目总数：{total_cf}；带标签：{len(cf_tagged)}；有 rating：{len(cf_rated)}")
    lines.append(f"- CF 标签种数：{len(tags)}；两两组合：{len(pairs)}")
    lines.append(f"- DMOJ 题目：{total_dmoj}；类型种数：{len(dmoj_types)}")
    lines.append(f"- AtCoder Problems 题目：{len(atcoder_problems)}；有 difficulty model：{len(atcoder_with_diff)}")
    lines.append(f"- 本地算法数：{len(algorithms)}")
    lines.append("")
    lines.append("## 清洗规则")
    lines.append("")
    for rule in data["meta"]["cleaning"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("## Top 30 CF 标签")
    lines.append("")
    lines.append("| 标签 | 频率 | P(题含此标签) | 难度中位 |")
    lines.append("|---|---|---|---|")
    for t in tags[:30]:
        d = t.get("difficulty_range") or {}
        lines.append(f"| {t['tag']} | {t['frequency']} | {t['probability_per_problem']} | {d.get('median', '-')} |")
    lines.append("")
    lines.append("## Top 20 DMOJ 类型")
    lines.append("")
    lines.append("| 类型 | 频率 | P(题含此类型) | 题分中位 |")
    lines.append("|---|---|---|---|")
    for t in dmoj_types[:20]:
        d = t.get("points_range") or {}
        lines.append(f"| {t['type']} | {t['frequency']} | {t['probability_per_problem']} | {d.get('median', '-')} |")
    lines.append("")
    lines.append("## Top 30 缝合怪两两组合（CF）")
    lines.append("")
    lines.append("| 组合 | 频率 | P(题含此组合) |")
    lines.append("|---|---|---|")
    for c in pairs[:30]:
        lines.append(f"| {' + '.join(c['pair'])} | {c['frequency']} | {c['probability']} |")
    lines.append("")
    lines.append("## AtCoder 难度摘要")
    lines.append("")
    d = atcoder_summary.get("difficulty_range") or {}
    lines.append(f"- 难度模型数：{atcoder_summary['difficulty_model_count']}")
    lines.append(f"- 范围：{d.get('min')} ~ {d.get('max')}；中位：{d.get('median')}")
    lines.append("")
    lines.append("## 本地 120 算法映射覆盖率")
    lines.append("")
    cf_mapped = sum(1 for a in algorithms if a["cf_tags"])
    dmoj_mapped = sum(1 for a in algorithms if a["dmoj_types"])
    lines.append(f"- CF 标签映射：{cf_mapped}/{len(algorithms)}")
    lines.append(f"- DMOJ 类型映射：{dmoj_mapped}/{len(algorithms)}")
    lines.append("")
    lines.append("## 已知近似/局限")
    lines.append("")
    lines.append("- CF 标签是英文粗粒度，本地 120 算法频率为映射后的估算值。")
    lines.append("- DMOJ 类型只有 21 类，points 只作难度代理，不是严格 rating。")
    lines.append("- AtCoder 只有难度曲线，没有算法标签，因此不作为算法分类依据，只用于交叉验证难度。")
    lines.append("- 组合统计来自 CF 官方标签；中文“线段树+贪心”这类组合会在阶段二映射展开。")
    lines.append("")
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {OUT_JSON} ({os.path.getsize(OUT_JSON)} bytes)")
    print(f"Wrote {OUT_REPORT} ({os.path.getsize(OUT_REPORT)} bytes)")
    print(f"cf_tags={len(tags)} cf_pairs={len(pairs)} dmoj_types={len(dmoj_types)} algorithms={len(algorithms)}")


if __name__ == "__main__":
    main()
