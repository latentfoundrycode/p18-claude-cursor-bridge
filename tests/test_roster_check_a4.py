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
    roster = tmp_path / "ROSTER.json"
    roster.write_text(json.dumps(ROSTER, indent=2), encoding="utf-8")
    (tmp_path / "run" / "launcher").mkdir(parents=True)
    rc, out = run(tmp_path, roster)
    assert rc == 0 and "RESOLVED profile 'native'" in out, "without a run log the native profile resolves (the other pool is exhausted): " + out
    log = tmp_path / "run" / "launcher" / "runs.jsonl"
    log.write_text(json.dumps({"id": "a1", "kind": "review", "head": "cursor-agent", "model": "gpt-5.6-sol-high", "limit": 3600, "seconds": 10, "exit": 0, "healthy": True}) + "\n"
                   + json.dumps({"id": "b1", "kind": "builder", "head": "cursor-agent", "model": "grok-4.7-high", "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}) + "\n", encoding="utf-8")
    rc, out = run(tmp_path, roster)
    assert rc == 1 and "built this change" in out and "grok" in out, "review_b grok-4.7-high reviews a change grok-4.7-high built (13.1): " + out
    log.write_text(json.dumps({"id": "b2", "kind": "builder", "head": "cursor-agent", "model": "composer-2.5", "limit": 7200, "seconds": 100, "exit": 0, "healthy": True}) + "\n", encoding="utf-8")
    rc, out = run(tmp_path, roster)
    assert rc == 0, out
