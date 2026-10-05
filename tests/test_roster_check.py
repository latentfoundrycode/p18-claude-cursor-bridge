"""roster-check.py: the four defects of KP-034 and the behaviours around them.
Runs on temporary copies of a roster; never calls cursor-agent (--no-probe, --record-* only)."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "roster-check.py")

ROSTER = {
    "other_pool": "available",
    "reset_day": 16,
    "review_a": "claude-opus-4-8",
    "profiles": [
        {"name": "full", "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"},
        {"name": "native", "builder": "composer-2.5", "review_b": "grok-4.7-high"},
    ],
}


def pathlib_write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


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


def state(roster_path):
    """The untracked state file beside a roster outside git: run/roster-state.json."""
    sp = os.path.join(os.path.dirname(roster_path), "run", "roster-state.json")
    return json.load(open(sp, encoding="utf-8")) if os.path.isfile(sp) else {}


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


def test_connection_errors_are_retried_twice_then_escalated_never_switched(roster, tmp_path):
    err = write_err(tmp_path, "Connection lost. Reconnecting...")
    for i in range(2):
        rc, out = run(roster, "--record-failure", "grok-4.7-high", "--stderr-file", err)
        assert rc == 4 and "connection error" in out, (i, out)
    rc, out = run(roster, "--record-failure", "grok-4.7-high", "--stderr-file", err)
    assert rc == 5 and "ESCALATE" in out
    st = state(roster)
    assert st.get("other_pool", "available") == "available" and "unavailable" not in st and not st.get("failures")


def test_a_hit_run_limit_counts_as_a_connection_failure(roster, tmp_path):
    err = write_err(tmp_path, "bridge-run: LIMIT 7200s reached after 7200s; terminating the whole process tree")
    rc, out = run(roster, "--record-failure", "grok-4.7-high", "--stderr-file", err)
    assert rc == 4 and "time-out" in out
    assert state(roster).get("other_pool", "available") == "available"


def test_state_survives_a_reset_of_the_working_tree(tmp_path):
    """Release 0a review F1: the exhaustion mark used to live in the tracked roster and a
    reset erased it. It now lives under .git/bridge/."""
    repo = tmp_path / "Workspace"
    (repo / "docs").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    rpath = repo / "docs" / "ROSTER.json"
    rpath.write_text(json.dumps(ROSTER, indent=2), encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "checkpoint"], check=True)
    rc, out = run(str(rpath), "--record-failure", "gpt-5.6-sol-high", "--stderr-file", write_err(tmp_path, "usage limit reached for this billing period"))
    assert rc == 3
    subprocess.run(["git", "-C", str(repo), "reset", "--hard", "-q", "HEAD"], check=True)
    subprocess.run(["git", "-C", str(repo), "clean", "-fdq"], check=True)
    rc, out = run(str(rpath), "--no-probe")
    assert rc == 0 and "RESOLVED profile 'native'" in out, out
    assert (repo / ".git" / "bridge" / "roster-state.json").is_file()
    assert "roster-state" not in subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout


def test_a_legacy_roster_seeds_the_state_once_and_integer_counts_are_expired(roster, tmp_path):
    legacy = dict(ROSTER, other_pool="exhausted", exhausted_at="2026-09-29T19:31 UTC", failures={"grok-4.7-high": 1})
    pathlib_write(roster, legacy)
    rc, out = run(roster, "--no-probe", now="2026-10-04T10:00")
    assert "migrated" in out and "RESOLVED profile 'native'" in out
    err = write_err(tmp_path, "Error: empty response")
    rc, out = run(roster, "--record-failure", "grok-4.7-high", "--stderr-file", err, now="2026-10-04T10:05")
    assert rc == 4, "an old integer count is expired, not a prior failure: " + out


def test_rate_limit_is_transient_not_usage_limit(roster, tmp_path):
    rc, out = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", write_err(tmp_path, "Error: rate limit exceeded, retry later"))
    assert rc == 4
    assert state(roster).get("other_pool", "available") == "available"


def test_usage_limit_message_exhausts_the_pool(roster, tmp_path):
    rc, out = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", write_err(tmp_path, "You have reached your usage limit for this billing period"))
    assert rc == 3
    assert state(roster).get("other_pool") == "exhausted"
    assert json.load(open(roster, encoding="utf-8")).get("other_pool") == "available", "the tracked roster is never written"


def test_two_failures_within_the_window_count_but_days_apart_do_not(roster, tmp_path):
    err = write_err(tmp_path, "Error: the model returned an empty response")
    rc, _ = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", err, now="2026-10-04T10:00")
    assert rc == 4
    rc, _ = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", err, now="2026-10-06T10:00")
    assert rc == 4, "a failure two days later is a first failure again"
    rc, out = run(roster, "--record-failure", "gpt-5.6-sol-high", "--stderr-file", err, now="2026-10-06T10:30")
    assert rc == 3 and "consecutive" in out
    assert state(roster).get("other_pool") == "exhausted"


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
    assert "composer-2.5" in state(roster).get("unavailable", {})
    rc, out = run(roster, "--no-probe", now="2026-10-04T17:00")
    assert rc == 0 and "expired" in out
    assert "unavailable" not in state(roster)


def test_resolve_without_probe_picks_the_full_profile(roster):
    rc, out = run(roster, "--no-probe")
    assert rc == 0 and "RESOLVED profile 'full'" in out
