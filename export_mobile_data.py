# -*- coding: utf-8 -*-
"""导出移动端数据：把 Python 知识树转成前端可加载的 data.js。"""
import json
import os

from info_framework import ANATOMY_STEPS, INFO_OPS, INFO_OP_COLORS, PHASES, TOPOLOGIES
from knowledge_data import ALGORITHMS
from tiers_data import TIERS

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "mobile", "www")
os.makedirs(OUT_DIR, exist_ok=True)

# 移动端不需要 C++ 模板，去掉 cpp 让包更轻
MOBILE_ALGORITHMS = [
    {k: v for k, v in a.items() if k != "cpp"}
    for a in ALGORITHMS
]

data = {
    "tiers": TIERS,
    "algorithms": MOBILE_ALGORITHMS,
    "infoOps": INFO_OPS,
    "infoOpColors": INFO_OP_COLORS,
    "topologies": TOPOLOGIES,
    "phases": {str(k): v for k, v in PHASES.items()},
    "anatomySteps": ANATOMY_STEPS,
}

out_path = os.path.join(OUT_DIR, "data.js")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("// 由 export_mobile_data.py 自动生成，请勿手改。\n")
    f.write("window.KNOWLEDGE_DATA = ")
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write(";\n")

# ---- 动态熵减数据：只导出运行所需的最小字段 ----
with open(os.path.join(ROOT, "algorithm_prior.json"), encoding="utf-8") as f:
    prior = json.load(f)
with open(os.path.join(ROOT, "feature_algorithm_matrix.json"), encoding="utf-8") as f:
    matrix = json.load(f)
with open(os.path.join(ROOT, "heuristics.json"), encoding="utf-8") as f:
    heuristics = json.load(f)

entropy = {
    "params": prior.get("params", {}),
    "features": matrix.get("features", []),
    "directions": matrix.get("directions", []),
    "heuristics": heuristics,
    "algorithms": [
        {
            "algorithm_name": a["algorithm_name"],
            "prior_probability": a.get("prior_probability", 0),
            "profile": a.get("profile", {}),
            "direction_weights": a.get("direction_weights", {}),
        }
        for a in matrix.get("algorithms", [])
    ],
}

entropy_path = os.path.join(OUT_DIR, "entropy_data.js")
with open(entropy_path, "w", encoding="utf-8") as f:
    f.write("// 由 export_mobile_data.py 自动生成，请勿手改。\n")
    f.write("window.ENTROPY_DATA = ")
    json.dump(entropy, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print(f"Written: {out_path}")
print(f"Written: {entropy_path}")
