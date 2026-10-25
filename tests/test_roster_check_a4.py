"""roster-check.py (release A4, 13.1): the reviewer's family is compared with the builder that built the
change, read from the launcher's run log, not only with the profile's own builder."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "roster-check.py")

ROSTER = {
    "other_pool": "exhausted",
    "reset_day": 16,
    "review_a": "claude-opus-4-8",
    "profiles": [
        {"name": "full", "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"},
        {"name": "native", "builder": "composer-2.5", "review_b": "grok-4.7-high"},
    ],
}


def run(cwd, roster_path, *args):
    p = subprocess.run([sys.executable, PROG, str(roster_path), "--no-probe"] + list(args), capture_output=True, text=True, cwd=str(cwd))
    return p.returncode, p.stdout + p.stderr


def test_the_reviewer_is_never_of_the_family_that_built_the_change(tmp_path):
    """Since 2026.10.25a the profile resolves with a REBUILD order instead of failing: its builder
    rebuilds the change in flight, and the launcher refuses Review B until it has."""
    subprocess.run(["git", "init", "-q", "-b", "task-1", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "c"], check=True, capture_output=True)
    roster = tmp_path / "ROSTER.json"
    roster.write_text(json.dumps(ROSTER, indent=2), encoding="utf-8")
    (tmp_path / "run" / "launcher").mkdir(parents=True)
    rc, out = run(tmp_path, roster)
    assert rc == 0 and "RESOLVED profile 'native'" in out, "without a run log the native profile resolves (the other pool is exhausted): " + out
    log = tmp_path / "run" / "launcher" / "runs.jsonl"
    log.write_text(json.dumps({"id": "a1", "kind": "review", "head": "cursor-agent", "model": "gpt-5.6-sol-high", "branch": "task-1", "limit": 3600, "seconds": 10, "exit": 0, "healthy": True}) + "\n"
                   + json.dumps({"id": "b1", "kind": "builder", "head": "cursor-agent", "model": "grok-4.7-high", "branch": "task-1", "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}) + "\n", encoding="utf-8")
    rc, out = run(tmp_path, roster)
    resolved = json.loads((tmp_path / "ROSTER.resolved.json").read_text(encoding="utf-8"))
    assert rc == 0 and "REBUILD" in out and resolved.get("rebuild") == {"built_by": "grok-4.7-high", "rebuild_with": "composer-2.5"}, \
        "review_b grok-4.7-high may not review a change grok-4.7-high built (13.1): the native builder rebuilds it: " + out
    log.write_text(json.dumps({"id": "b2", "kind": "builder", "head": "cursor-agent", "model": "composer-2.5", "branch": "task-1", "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}) + "\n", encoding="utf-8")
    rc, out = run(tmp_path, roster)
    resolved = json.loads((tmp_path / "ROSTER.resolved.json").read_text(encoding="utf-8"))
    assert rc == 0 and "REBUILD" not in out and "rebuild" not in resolved, out
