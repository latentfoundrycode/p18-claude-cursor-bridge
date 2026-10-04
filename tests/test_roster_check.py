"""roster-check.py: the four defects of KP-034 and the behaviours around them.
Runs on temporary copies of a roster; never calls cursor-agent (--no-probe, --record-* only)."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, ".claude", "cursor-bridge", "roster-check.py")

ROSTER = {
    "other_pool": "available",
    "reset_day": 16,
    "review_a": "claude-opus-4-8",
    "profiles": [
        {"name": "full", "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"},
        {"name": "native", "builder": "composer-2.5", "review_b": "grok-4.7-high"},
    ],
}


def run(roster_path, *args, now=None):
    env = dict(os.environ)
    if now:
        env["ROSTER_NOW"] = now
    p = subprocess.run([sys.executable, PROG, roster_path] + list(args), capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


@pytest.fixture
def roster(tmp_path):
    path = tmp_path / "ROSTER.json"
    path.write_text(json.dumps(ROSTER, indent=2), encoding="utf-8")
    return str(path)


def write_err(tmp_path, text):
    f = tmp_path / "call.err"
    f.write_text(text, encoding="utf-8")
    return str(f)


def test_wrong_model_argument_changes_nothing(roster, tmp_path):
    """reAngle 2026-09-29: a file path was recorded as the model id and exhausted the pool."""
    before = open(roster, encoding="utf-8").read()
    rc, out = run(roster, "--record-failure", "run/review/REVIEW-FIX.err", "--stderr-file", write_err(tmp_path, "boom"))
    assert rc == 2 and "CANNOT RECORD" in out
    assert open(roster, encoding="utf-8").read() == before


def test_connection_error_is_transient_and_not_counted(roster, tmp_path):
    err = write_err(tmp_path, "Connection lost. Reconnecting...")
    for _ in range(3):
        rc, out = run(roster, "--record-failure", "grok-4.7-high", "--stderr-file", err)
        assert rc == 4 and "connection error" in out
    data = json.load(open(roster, encoding="utf-8"))
    assert data.get("other_pool") == "available" and "unavailable" not in data and not data.get("failures")


def test_rate_limit_is_transient_not_usage_limit(roster, tmp_path):
    rc, out = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", write_err(tmp_path, "Error: rate limit exceeded, retry later"))
    assert rc == 4
    assert json.load(open(roster, encoding="utf-8")).get("other_pool") == "available"


def test_usage_limit_message_exhausts_the_pool(roster, tmp_path):
    rc, out = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", write_err(tmp_path, "You have reached your usage limit for this billing period"))
    assert rc == 3
    assert json.load(open(roster, encoding="utf-8")).get("other_pool") == "exhausted"


def test_two_failures_within_the_window_count_but_days_apart_do_not(roster, tmp_path):
    err = write_err(tmp_path, "Error: the model returned an empty response")
    rc, _ = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", err, now="2026-10-04T10:00")
    assert rc == 4
    rc, _ = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", err, now="2026-10-06T10:00")
    assert rc == 4, "a failure two days later is a first failure again"
    rc, out = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", err, now="2026-10-06T10:30")
    assert rc == 3 and "consecutive" in out
    assert json.load(open(roster, encoding="utf-8")).get("other_pool") == "exhausted"


def test_record_success_clears_the_count(roster, tmp_path):
    err = write_err(tmp_path, "Error: empty response")
    run(roster, "--record-failure", "composer-2.5", "--stderr-file", err)
    rc, out = run(roster, "--record-success", "composer-2.5")
    assert rc == 0 and "cleared" in out
    rc, _ = run(roster, "--record-failure", "composer-2.5", "--stderr-file", err)
    assert rc == 4, "after a success the next failure is a first failure"


def test_unavailable_mark_expires(roster, tmp_path):
    err = write_err(tmp_path, "Error: empty response")
    run(roster, "--record-failure", "composer-2.5", "--stderr-file", err, now="2026-10-04T10:00")
    rc, out = run(roster, "--record-failure", "composer-2.5", "--stderr-file", err, now="2026-10-04T10:10")
    assert rc == 3 and "UNAVAILABLE" in out
    rc, out = run(roster, "--no-probe", now="2026-10-04T12:00")
    assert "composer-2.5" in json.load(open(roster, encoding="utf-8")).get("unavailable", {})
    rc, out = run(roster, "--no-probe", now="2026-10-04T17:00")
    assert rc == 0 and "expired" in out
    assert "unavailable" not in json.load(open(roster, encoding="utf-8"))


def test_resolve_without_probe_picks_the_full_profile(roster):
    rc, out = run(roster, "--no-probe")
    assert rc == 0 and "RESOLVED profile 'full'" in out
