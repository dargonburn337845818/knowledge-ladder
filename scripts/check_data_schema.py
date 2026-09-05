"""数据 schema / 版本完整性检查。

校验四个核心 JSON 的 meta.version 是否存在、矩阵规模是否与代码约定一致。
CI 在生成移动端数据前运行，避免“数据文件损坏但测试恰好通过”。
"""

import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILES = [
    "algorithm_prior.json",
    "feature_algorithm_matrix.json",
    "heuristics.json",
    "teacher_consensus.json",
]


def load(name):
    with open(os.path.join(REPO_ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    errors = []
    versions = {}
    for name in DATA_FILES:
        data = load(name)
        meta = data.get("meta", {})
        if not isinstance(meta, dict) or not meta.get("version"):
            errors.append(f"{name}: missing meta.version")
        else:
            versions[name] = meta["version"]

    matrix = load("feature_algorithm_matrix.json")
    prior = load("algorithm_prior.json")
    heuristics = load("heuristics.json")

    if len(matrix.get("algorithms", [])) != 120:
        errors.append("feature_algorithm_matrix algorithms != 120")
    if len(matrix.get("features", [])) != 20:
        errors.append("feature_algorithm_matrix features != 20")
    if len(prior.get("algorithms", [])) != 120:
        errors.append("algorithm_prior algorithms != 120")

    matrix_dirs = set(matrix.get("directions", []))
    heur_dirs = {h.get("id") for h in heuristics.get("directions", [])}
    if matrix_dirs != heur_dirs:
        errors.append("heuristics directions do not match matrix directions")

    if errors:
        print("DATA SCHEMA CHECK FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("DATA SCHEMA OK", versions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
