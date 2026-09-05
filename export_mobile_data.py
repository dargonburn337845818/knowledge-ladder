"""导出移动端熵减数据：只导出运行所需的最小字段 + 教师共识。"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "mobile", "www")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(ROOT, "algorithm_prior.json"), encoding="utf-8") as f:
    prior = json.load(f)
with open(os.path.join(ROOT, "feature_algorithm_matrix.json"), encoding="utf-8") as f:
    matrix = json.load(f)
with open(os.path.join(ROOT, "heuristics.json"), encoding="utf-8") as f:
    heuristics = json.load(f)
with open(os.path.join(ROOT, "teacher_consensus.json"), encoding="utf-8") as f:
    teacher_consensus = json.load(f)

entropy = {
    "params": prior.get("params", {}),
    "features": matrix.get("features", []),
    "directions": matrix.get("directions", []),
    "heuristics": heuristics,
    "teacher_consensus": teacher_consensus,
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
versions = {
    "prior": prior.get("meta", {}).get("version", "?"),
    "matrix": matrix.get("meta", {}).get("version", "?"),
    "heuristics": heuristics.get("meta", {}).get("version", "?"),
    "teacher": teacher_consensus.get("meta", {}).get("version", "?"),
}
with open(entropy_path, "w", encoding="utf-8") as f:
    f.write("// 由 export_mobile_data.py 自动生成，请勿手改。\n")
    f.write("// data versions: " + ", ".join(f"{k}={v}" for k, v in versions.items()) + "\n")
    f.write("window.ENTROPY_DATA = ")
    json.dump(entropy, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print(f"Written: {entropy_path}")
