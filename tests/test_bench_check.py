"""bench-check.py (release A4, R17): the direction of a metric comes from its budget (max, min or
direction) or from a unit the metric names whole, never from its last letter; a throughput named
`requests` is not read as lower-is-better. Scratch files."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bench-check.py")


def run(tmp_path, budgets, baseline, latest):
    for name, doc in (("budgets.json", budgets), ("baseline.json", baseline), ("latest.json", latest)):
        (tmp_path / name).write_text(json.dumps(doc), encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, str(tmp_path / "budgets.json"), str(tmp_path / "baseline.json"), str(tmp_path / "latest.json")],
                       capture_output=True, text=True, cwd=str(tmp_path))
    return p.returncode, p.stdout


def results(**kv):
    return {"results": [{"benchmark": "api", "metric": k, "value": v} for k, v in kv.items()]}


def test_a_throughput_drop_is_a_regression_not_an_improvement(tmp_path):
    budgets = {"budgets": [{"id": "B1", "benchmark": "api", "metric": "requests", "direction": "higher", "tolerance_pct": 10},
                           {"id": "B2", "benchmark": "api", "metric": "requests_per_s", "tolerance_pct": 10}]}
    rc, out = run(tmp_path, budgets, results(requests=100, requests_per_s=100), results(requests=50, requests_per_s=50))
    assert rc == 1 and out.count("REGRESSION") == 2 and "IMPROVED" not in out, "a throughput drop read as an improvement (R17): " + out


def test_an_unknown_direction_is_refused_for_a_budget_and_noted_for_a_baseline(tmp_path):
    budgets = {"budgets": [{"id": "B1", "benchmark": "api", "metric": "requests", "tolerance_pct": 10}]}
    rc, out = run(tmp_path, budgets, results(requests=100, widgets=100), results(requests=50, widgets=50))
    assert rc == 1 and "DIRECTION UNKNOWN" in out and "B1" in out.split("DIRECTION UNKNOWN")[0].rsplit("\n", 1)[-1], out
    assert "widgets" in out and "not judged" in out and "IMPROVED" not in out, "a baseline-only metric of unknown direction is noted, never judged: " + out


def test_units_still_decide_when_named_whole(tmp_path):
    budgets = {"budgets": [{"id": "L", "benchmark": "api", "metric": "latency_ms", "tolerance_pct": 10}, {"id": "M", "benchmark": "api", "metric": "peak_mb", "max": 500}]}
    rc, out = run(tmp_path, budgets, results(latency_ms=100, peak_mb=100), results(latency_ms=50, peak_mb=120))
    assert rc == 1 and "IMPROVED" in out.split("latency_ms")[1].split("\n")[0] and "REGRESSION" in out.split("peak_mb")[1].split("\n")[0], out
