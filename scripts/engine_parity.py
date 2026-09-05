"""Python 端与移动端 JS 熵减引擎的黄金输出一致性检查。

在 CI 中运行：python scripts/engine_parity.py
依赖：python3 + node（仓库根目录执行）。
"""

import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from entropy_engine import EntropyEngine

TOLERANCE = 1e-6


def close(a, b):
    return abs(float(a) - float(b)) <= TOLERANCE


def close_list(a, b):
    return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b, strict=False))


def close_dict(a, b):
    return set(a) == set(b) and all(close(a[k], b[k]) for k in a)


def js_snapshot():
    js = r"""
    global.window = {};
    require(process.cwd() + '/mobile/www/entropy_data.js');
    require(process.cwd() + '/mobile/www/entropy_engine.js');
    const engine = window.EntropyEngine.create(window.ENTROPY_DATA);
    const w = engine.initialWeights();
    const first = engine.chooseNext(w, []);
    function answer(a) {
      return {
        posterior: engine.posterior(w, first.id, a),
        surprise: engine.answerProbability(w, first.id, a)
      };
    }
    const out = {
      first: first,
      answers: {
        yes: answer('yes'),
        no: answer('no'),
        uncertain: answer('uncertain')
      },
      dirs: engine.directionProbs(w),
      top: engine.topAlgorithms(w),
      realtime: engine.realtimeTop(w),
      stop: engine.shouldStop(w, [])
    };
    console.log(JSON.stringify(out));
    """
    proc = subprocess.run(
        ["node", "-e", js],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"node parity script failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def py_snapshot():
    engine = EntropyEngine()
    w = engine.initial_weights()
    first_id, first_ig = engine.choose_next(w, [])
    answers = {}
    for answer in ("yes", "no", "uncertain"):
        answers[answer] = {
            "posterior": engine.posterior(w, first_id, answer),
            "surprise": engine.answer_probability(w, first_id, answer),
        }
    stop, _reason = engine.should_stop(w, [])
    return {
        "first": {"id": first_id, "ig": first_ig},
        "answers": answers,
        "dirs": engine.direction_probs(w),
        "top": engine.top_algorithms(w),
        "realtime": engine.realtime_top(w),
        "stop": {"stop": stop},
    }


def main():
    js = js_snapshot()
    py = py_snapshot()
    failures = []

    if js["first"]["id"] != py["first"]["id"]:
        failures.append(f"first id: js={js['first']['id']} py={py['first']['id']}")
    if not close(js["first"]["ig"], py["first"]["ig"]):
        failures.append(f"first ig: js={js['first']['ig']} py={py['first']['ig']}")

    for answer in ("yes", "no", "uncertain"):
        jp = js["answers"][answer]["posterior"]
        pp = py["answers"][answer]["posterior"]
        if not close_list(jp, pp):
            failures.append(f"posterior[{answer}] differs")
        if not close(js["answers"][answer]["surprise"], py["answers"][answer]["surprise"]):
            failures.append(f"surprise[{answer}] differs")

    if not close_dict(js["dirs"], py["dirs"]):
        failures.append("direction_probs differ")

    for key in ("top", "realtime"):
        jr = js[key]
        pr = py[key]
        if [x["algorithm_name"] for x in jr] != [x["algorithm_name"] for x in pr]:
            failures.append(f"{key} ordering/names differ")
        elif not all(close(x["weight"], y["weight"]) for x, y in zip(jr, pr, strict=False)):
            failures.append(f"{key} weights differ")

    if js["stop"]["stop"] != py["stop"]["stop"]:
        failures.append(f"should_stop differs: js={js['stop']['stop']} py={py['stop']['stop']}")

    if failures:
        print("ENGINE PARITY FAILED")
        for f in failures:
            print(" -", f)
        return 1
    print("ENGINE PARITY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
