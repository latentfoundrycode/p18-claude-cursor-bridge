"""session-start.py (KP-035): the digest survives at the head of supervisor.md; the hook
re-injects it in two parts, each under Claude Code's 10,000-character cap, on a realistic
status file for every phase the template allows; it is silent outside a bridge project and
in a session that never invoked /supervisor (0b review, findings 1, 3 and 7)."""
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
TEMPLATE_PHASES = re.search(r"^Phase: <([^>]+)>", TEXT, re.M).group(1).split("|")
TEMPLATE_PHASES = [p.strip() for p in TEMPLATE_PHASES]
CAP = 10000


def test_digest_is_at_the_head_and_within_what_a_compaction_keeps():
    a, b = TEXT.find("<!-- digest:start -->"), TEXT.find("<!-- digest:end -->")
    assert 0 < a < b
    assert b < 20000, "the digest must end inside the first 20,000 characters, the part a compaction keeps"
    assert len(TEXT[a:b]) <= 9500, "the digest part (digest + its header line) must stay under the hook's cap with margin"


def test_digest_names_every_standing_rule_and_founding_rule():
    a, b = TEXT.find("<!-- digest:start -->"), TEXT.find("<!-- digest:end -->")
    digest = TEXT[a:b]
    rules = re.findall(r"^(\d+)\. ", TEXT[TEXT.find("## Standing rules"):], re.M)
    assert len(rules) >= 47
    for n in rules:
        assert re.search(r"(?:^|[ .(])%s [A-Z`]" % n, digest), "rule %s is missing from the digest" % n
    for n in range(1, 10):
        assert ("N%d " % n) in digest, "founding rule N%d is missing from the digest" % n


def test_digest_carries_the_literal_commands_and_the_merge_authority_check():
    """0b review, finding 4: a supervisor working from the digest alone must not have to
    compose the constant delegate command, and must not merge under `Merge authority: owner`."""
    a, b = TEXT.find("<!-- digest:start -->"), TEXT.find("<!-- digest:end -->")
    digest = TEXT[a:b]
    assert "Read handoff/TASK-<nnn>.md and implement exactly what it specifies." in digest
    assert "2> run/review/REVIEW-<nnn>.err" in digest
    assert "review-guard.py snapshot <nnn>" in digest and "review-guard.py verify <nnn>" in digest and "review-guard.py premerge <nnn>" in digest
    assert "Merge authority: owner" in digest and "READY TO MERGE" in digest


def test_every_template_phase_value_is_mapped():
    sys.path.insert(0, os.path.dirname(PROG))
    import importlib.util
    spec = importlib.util.spec_from_file_location("session_start", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for phase in TEMPLATE_PHASES:
        assert phase in mod.PHASE_SECTIONS, "template phase %r has no section pointers" % phase
    digest, sections = mod.digest_and_sections(SV)
    for wanted in set(sum(mod.PHASE_SECTIONS.values(), [])):
        assert wanted in sections, "mapped heading %r is not a section of supervisor.md" % wanted
    # a section ends at the next real heading, never at a template line inside a code block
    design = sections["## Phase 2 — Design"]
    mock = sections["## Phase 3 — UI mockups"]
    assert design[1] == mock[0] - 1, "the design section must run up to the mockup heading (code-fenced '# Requirements' is not a heading)"
    lines = TEXT.split("\n")
    for h, (first, last) in sections.items():
        assert lines[first - 1].strip() == h


def run_hook(cwd, home, part=None, source="compact", transcript=None):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    args = [sys.executable, PROG] + (["--part", part] if part else [])
    data = {"cwd": str(cwd), "hook_event_name": "SessionStart", "source": source}
    if transcript:
        data["transcript_path"] = str(transcript)
    p = subprocess.run(args, input=json.dumps(data), capture_output=True, text=True, encoding="utf-8", env=env)
    return p.returncode, p.stdout


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    (h / ".claude" / "commands").mkdir(parents=True)
    (h / ".claude" / "commands" / "supervisor.md").write_text(TEXT, encoding="utf-8")
    return h


def realistic_status(phase, awaiting="nothing"):
    """A status file at the template's limits: 12,000 characters, a 4,000-character
    Awaiting line (the video factory's today), every field present."""
    filler = ("Next: TASK-120 — the settings store; the session needs the following context " * 40)[:3000]
    lines = ["# Project Status", "Last updated: 2026-10-04T10:00:00Z", "Phase: %s (Stage 3 of 5)" % phase,
             "Change cycle: none", "Increment: TASK-119 — grant subsystem", "Last accepted: TASK-118 at commit abc1234",
             "Awaiting user on: " + awaiting, filler, "Deviations accepted: none",
             "Terms fixed: " + "; ".join("term%d — sense %d — Established" % (i, i) for i in range(60)),
             "Software name: Thing", "Layout: Workspace=E:/x/Workspace  Documents=E:/x/Documents", "Worktrees: none",
             "In flight: none", "Remote sync: in sync at 2026-10-04", "Stage: Stage 3 — Last reflection: stage close 2026-10-03",
             "Open issues: " + ", ".join("ISS-%03d" % i for i in range(1, 80)), "Bridge version: 2026.10.04c"]
    text = "\n".join(lines) + "\n"
    while len(text) < 12000:
        text += "Note: " + "x" * 90 + "\n"
    return text


@pytest.mark.parametrize("phase", TEMPLATE_PHASES)
def test_both_parts_fit_under_the_cap_for_every_phase_on_a_realistic_status_file(tmp_path, home, phase):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text(realistic_status(phase, "the owner must decide " + "y" * 4000), encoding="utf-8")
    rc, pointers = run_hook(root, home, "pointers")
    rc2, digest = run_hook(root / "Workspace", home, "digest")
    assert rc == 0 and rc2 == 0
    for out in (pointers, digest):
        assert len(out) < CAP and "cut at" not in out and "truncated" not in out
    assert "PROJECT STATE: Phase: %s" % phase in pointers
    assert "BEFORE YOUR NEXT ACTION" in pointers and re.search(r"': lines \d+-\d+", pointers)
    assert "Then read docs/PROJECT_STATUS.md and docs/INVENTORY.md whole (rule 41)." in pointers
    assert "WAITING FOR THE OWNER" in pointers and "(read it whole in docs/PROJECT_STATUS.md)" in pointers
    assert "**Founding rules.**" in digest and "43 Never end a turn" in digest and "bridge 2026.10.04c" in digest


def test_pointers_name_the_phase_sections_and_conventions(tmp_path, home):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nBridge version: 2026.10.04c\nPhase: building (Stage 2)\nAwaiting user on: nothing\n", encoding="utf-8")
    for cwd in (root / "Workspace", root):
        rc, out = run_hook(cwd, home)                     # both parts
        assert rc == 0
        assert re.search(r"'Phase 6 — The delegation loop': lines \d+-\d+", out)
        assert "Merge-Verification-Policy.md, whole" in out
        assert "Continue from where the status file says the work is." in out and "WAITING" not in out
        assert "**Founding rules.**" in out
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text("**Phase:** design\n", encoding="utf-8")
    rc, out = run_hook(root / "Workspace", home, "pointers")
    assert re.search(r"'Phase 2 — Design': lines \d+-\d+", out) and "Diagram-Planning-Conventions.md" in out
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text("Phase: configuration\n", encoding="utf-8")
    rc, out = run_hook(root / "Workspace", home, "pointers")
    assert re.search(r"'Phase 5 — Configure the Cursor build environment': lines \d+-\d+", out) and "Cursor-Project-Configuration.md" in out


def test_fork_source_is_named(tmp_path, home):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\n", encoding="utf-8")
    rc, out = run_hook(root, home, "pointers", source="fork")
    assert "forked from another session" in out


def test_silent_outside_a_bridge_project(tmp_path, home):
    rc, out = run_hook(tmp_path / "elsewhere", home)
    assert rc == 0 and out == ""


def test_silent_in_a_session_that_never_invoked_supervisor(tmp_path, home):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\n", encoding="utf-8")
    other = tmp_path / "review-session.jsonl"
    other.write_text('{"type":"user","message":{"content":"<command-name>/calibrate-bridge</command-name>"}}\n', encoding="utf-8")
    rc, out = run_hook(root / "Documents", home, transcript=other)
    assert rc == 0 and out == ""
    sup = tmp_path / "supervisor-session.jsonl"
    sup.write_text('{"type":"user","message":{"content":"<command-name>/supervisor</command-name>"}}\n', encoding="utf-8")
    rc, out = run_hook(root, home, "pointers", transcript=sup)
    assert "CLAUDE-CURSOR BRIDGE" in out
    rc, out = run_hook(root, home, "pointers", transcript=tmp_path / "missing.jsonl")   # no transcript to consult: fail open
    assert "CLAUDE-CURSOR BRIDGE" in out


def test_never_blocks_on_bad_input(home):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    p = subprocess.run([sys.executable, PROG], input="not json", capture_output=True, text=True, env=env)
    assert p.returncode == 0
