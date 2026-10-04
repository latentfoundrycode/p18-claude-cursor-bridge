"""session-start.py (KP-035): the digest survives at the head of supervisor.md, the hook
re-injects it with the phase's sections, stays under the output cap, and is silent outside
a bridge project."""
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.abspath(os.path.join(HERE, os.pardir, ".claude"))
PROG = os.path.join(CLAUDE, "cursor-bridge", "session-start.py")
SV = os.path.join(CLAUDE, "commands", "supervisor.md")
TEXT = open(SV, encoding="utf-8").read()


def test_digest_is_at_the_head_and_within_what_a_compaction_keeps():
    a, b = TEXT.find("<!-- digest:start -->"), TEXT.find("<!-- digest:end -->")
    assert 0 < a < b
    assert b < 20000, "the digest must end inside the first 20,000 characters, the part a compaction keeps"
    assert len(TEXT[a:b]) <= 9000, "the digest plus the hook's pointers must stay under the hook's 10,000-character output"


def test_digest_names_every_standing_rule_and_founding_rule():
    a, b = TEXT.find("<!-- digest:start -->"), TEXT.find("<!-- digest:end -->")
    digest = TEXT[a:b]
    rules = re.findall(r"^(\d+)\. ", TEXT[TEXT.find("## Standing rules"):], re.M)
    assert len(rules) >= 47
    for n in rules:
        assert re.search(r"(?:^|[ .(])%s [A-Z`]" % n, digest), "rule %s is missing from the digest" % n
    for n in range(1, 10):
        assert ("N%d " % n) in digest, "founding rule N%d is missing from the digest" % n


def run_hook(cwd, home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    p = subprocess.run([sys.executable, PROG], input=json.dumps({"cwd": str(cwd), "hook_event_name": "SessionStart"}),
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return p.returncode, p.stdout


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    (h / ".claude" / "commands").mkdir(parents=True)
    (h / ".claude" / "commands" / "supervisor.md").write_text(TEXT, encoding="utf-8")
    return h


def test_silent_outside_a_bridge_project(tmp_path, home):
    rc, out = run_hook(tmp_path / "elsewhere", home)
    assert rc == 0 and out == ""


def test_reinjects_the_digest_and_the_phase_sections(tmp_path, home):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nBridge version: 2026.10.04c\nPhase: building (Stage 2)\nAwaiting user on: nothing\n", encoding="utf-8")
    for cwd in (root / "Workspace", root):
        rc, out = run_hook(cwd, home)
        assert rc == 0
        assert "CLAUDE-CURSOR BRIDGE" in out and "bridge 2026.10.04c" in out
        assert "**Founding rules.**" in out and "43 Never end a turn" in out
        assert "Phase: building (Stage 2)" in out
        assert re.search(r"'Phase 6 — The delegation loop': lines \d+-\d+", out)
        assert "Merge-Verification-Policy.md, whole" in out
        assert len(out) < 10000 and "truncated" not in out


def test_design_phase_points_at_the_design_section_and_conventions(tmp_path, home):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text("**Phase:** design\n", encoding="utf-8")
    rc, out = run_hook(root / "Workspace", home)
    assert re.search(r"'Phase 2 — Design': lines \d+-\d+", out) and "Diagram-Planning-Conventions.md" in out


def test_never_blocks_on_bad_input(home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    p = subprocess.run([sys.executable, PROG], input="not json", capture_output=True, text=True, env=env)
    assert p.returncode == 0
