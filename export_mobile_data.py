"""导出移动端熵减数据：只导出运行所需的最小字段 + 教师共识 + 移动端拆题子集。"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "mobile", "www")


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mobile_direction_subset(content):
    """移动端只保留拆题所需字段，剔除 PC 端算法理解深挖（deep_dive）。"""
    return {
        "meta": content.get("meta", {}),
        "directions": [
            {k: v for k, v in d.items() if k != "deep_dive"}
            for d in content.get("directions", [])
        ],
    }


def _parse_generated(path):
    text = open(path, encoding="utf-8").read()
    prefix = "window.ENTROPY_DATA = "
    suffix = ";\n"
    idx = text.find(prefix)
    if idx < 0 or not text.endswith(suffix):
        raise SystemExit("generated entropy_data.js has unexpected shape")
    body = text[idx + len(prefix):-len(suffix)]
    return json.loads(body)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    prior = _read_json(os.path.join(ROOT, "algorithm_prior.json"))
    matrix = _read_json(os.path.join(ROOT, "feature_algorithm_matrix.json"))
    heuristics = _read_json(os.path.join(ROOT, "heuristics.json"))
    teacher_consensus = _read_json(os.path.join(ROOT, "teacher_consensus.json"))
    direction_content = _read_json(
        os.path.join(ROOT, "expert_content", "direction_cards_v1.json")
    )

    mobile_direction_content = mobile_direction_subset(direction_content)

    entropy = {
        "params": prior.get("params", {}),
        "features": matrix.get("features", []),
        "directions": matrix.get("directions", []),
        "heuristics": heuristics,
        "direction_content": mobile_direction_content,
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
        "direction_content": direction_content.get("meta", {}).get("version", "?"),
    }
    with open(entropy_path, "w", encoding="utf-8") as f:
        f.write("// 由 export_mobile_data.py 自动生成，请勿手改。\n")
        f.write("// data versions: " + ", ".join(f"{k}={v}" for k, v in versions.items()) + "\n")
        f.write("window.ENTROPY_DATA = ")
        json.dump(entropy, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # 自动一致性比较：生成文件中的 heuristics 与移动端拆题子集必须等于源
    generated = _parse_generated(entropy_path)
    if generated.get("heuristics") != heuristics:
        raise SystemExit("MOBILE SYNC FAILED: heuristics mismatch")
    if generated.get("direction_content") != mobile_direction_content:
        raise SystemExit("MOBILE SYNC FAILED: direction_content mismatch")

    print(f"Written: {entropy_path}")
    print(f"MOBILE DATA SYNC OK: heuristics={heuristics.get('meta', {}).get('version')}, "
          f"direction_content={direction_content.get('meta', {}).get('version')} (mobile subset)")


if __name__ == "__main__":
    main()
