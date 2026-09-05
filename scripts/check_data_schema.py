"""数据 schema / 版本完整性检查。

校验核心 JSON 的 meta.version、矩阵规模、方向一致性，以及
`expert_content/direction_cards_v1.json` 是否符合 `expert_content/schema.json`
定义的四方向内容 schema，并核对旧 heuristics 字段的兼容映射。
同时校验 `mobile/www/entropy_data.js` 内嵌的 heuristics / direction_content
是否与源 JSON 一致（移动端生成物同步门禁）。
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
    "expert_content/direction_cards_v1.json",
    "expert_content/algorithm_cards.json",
    "expert_content/dynamic_insights.json",
]

SCHEMA_PATH = "expert_content/schema.json"
MOBILE_DATA_PATH = "mobile/www/entropy_data.js"


def load(name):
    with open(os.path.join(REPO_ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def _type_ok(value, expected):
    if expected == "string":
        return isinstance(value, str)
    if expected == "object":
        return isinstance(value, dict)
    if expected.startswith("array<"):
        inner = expected[len("array<"):-1]
        return isinstance(value, list) and all(_type_ok(v, inner) for v in value)
    return False


def _check_object(obj, spec, path, errors):
    if not isinstance(obj, dict):
        errors.append(f"{path}: expected object")
        return
    for field in spec.get("required_fields", []):
        if field not in obj:
            errors.append(f"{path}: missing required field {field}")
    for field, typ in spec.get("field_types", {}).items():
        if field in obj and not _type_ok(obj[field], typ):
            errors.append(f"{path}.{field}: expected {typ}, got {type(obj[field]).__name__}")


def check_direction_content(schema, content, heuristics, errors):
    direction_spec = schema["direction"]
    anchor_spec = schema["anchor"]
    layers_spec = schema["layers"]
    edge_spec = schema["edge_case"]
    expert_spec = schema["expert_mark"]
    deep_dive_spec = schema.get("deep_dive", {})

    directions = content.get("directions", [])
    required_count = schema.get("required_direction_count", 4)
    if len(directions) != required_count:
        errors.append(f"expert_content directions != {required_count}")

    ids = [d.get("id") for d in directions]
    if len(ids) != len(set(ids)):
        errors.append("expert_content direction ids not unique")

    heur_by_title = {h.get("title"): h for h in heuristics.get("directions", [])}

    for d in directions:
        did = d.get("id", "?")
        _check_object(d, direction_spec, f"direction[{did}]", errors)
        if "deep_dive" in d:
            _check_object(d["deep_dive"], deep_dive_spec, f"direction[{did}].deep_dive", errors)
            refs = d["deep_dive"].get("source_refs", [])
            if len(refs) < 3:
                errors.append(f"direction[{did}].deep_dive.source_refs: expected at least 3 items")
            for i, ref in enumerate(refs):
                if not isinstance(ref, dict) or not ref.get("url") or not ref.get("title") or not ref.get("claim"):
                    errors.append(f"direction[{did}].deep_dive.source_refs[{i}]: missing url/title/claim")
        if len(d.get("triggers", [])) < 3:
            errors.append(f"direction[{did}].triggers: expected at least 3 items")
        if len(d.get("edge_cases", [])) < 1:
            errors.append(f"direction[{did}].edge_cases: expected at least 1 item")
        if len(d.get("source_refs", [])) < 1:
            errors.append(f"direction[{did}].source_refs: expected at least 1 item")
        anchor = d.get("anchor", {})
        _check_object(anchor, anchor_spec, f"direction[{did}].anchor", errors)
        layers = d.get("layers", {})
        _check_object(layers, layers_spec, f"direction[{did}].layers", errors)
        for i, edge in enumerate(d.get("edge_cases", [])):
            _check_object(edge, edge_spec, f"direction[{did}].edge_cases[{i}]", errors)
        for i, mark in enumerate(d.get("expert_marks", [])):
            _check_object(mark, expert_spec, f"direction[{did}].expert_marks[{i}]", errors)
        for i, mark in enumerate(layers.get("expert_marks", [])):
            _check_object(mark, expert_spec, f"direction[{did}].layers.expert_marks[{i}]", errors)
        for edge in d.get("edge_cases", []):
            for i, mark in enumerate(edge.get("expert_marks", [])):
                _check_object(mark, expert_spec, f"direction[{did}].edge.expert_marks[{i}]", errors)

        # 旧字段兼容映射：每个新方向必须能在 heuristics.json 找到同名旧方向及旧字段
        legacy = heur_by_title.get(d.get("title"))
        if legacy is None:
            errors.append(f"direction[{did}]: no legacy heuristics direction for title {d.get('title')}")
        else:
            for field in ("summary", "signals", "next_actions", "self_questions"):
                if field not in legacy:
                    errors.append(f"direction[{did}]: legacy heuristics missing {field}")


def parse_generated_js(path):
    """从 entropy_data.js 提取 window.ENTROPY_DATA JSON 对象。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    prefix = "window.ENTROPY_DATA = "
    suffix = ";\n"
    idx = text.find(prefix)
    if idx < 0 or not text.endswith(suffix):
        raise ValueError("generated entropy_data.js has unexpected shape")
    body = text[idx + len(prefix):-len(suffix)]
    return json.loads(body)


def project_mobile_direction_content(content):
    """移动端载荷子集：剔除 PC 端 deep_dive。"""
    return {
        "meta": content.get("meta", {}),
        "directions": [
            {k: v for k, v in d.items() if k != "deep_dive"}
            for d in content.get("directions", [])
        ],
    }


def check_mobile_sync(generated, content, heuristics, errors, dynamic_insights=None):
    """移动端生成物同步门禁：内嵌 heuristics / direction_content / dynamic_insights 必须等于源 JSON。"""
    if generated.get("heuristics") != heuristics:
        errors.append("mobile entropy_data.js heuristics does not match heuristics.json")
    projected = project_mobile_direction_content(content)
    if generated.get("direction_content") != projected:
        errors.append("mobile entropy_data.js direction_content does not match mobile subset of expert_content/direction_cards_v1.json")
    if dynamic_insights is not None and generated.get("dynamic_insights") != dynamic_insights:
        errors.append("mobile entropy_data.js dynamic_insights does not match expert_content/dynamic_insights.json")


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
    content_schema = load(SCHEMA_PATH)
    content = load("expert_content/direction_cards_v1.json")
    dynamic_insights = load("expert_content/dynamic_insights.json")

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

    check_direction_content(content_schema, content, heuristics, errors)

    try:
        generated = parse_generated_js(os.path.join(REPO_ROOT, MOBILE_DATA_PATH))
        check_mobile_sync(generated, content, heuristics, errors, dynamic_insights)
    except (OSError, ValueError) as exc:
        errors.append(f"mobile sync check failed: {exc}")

    if errors:
        print("DATA SCHEMA CHECK FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("DATA SCHEMA OK", versions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
