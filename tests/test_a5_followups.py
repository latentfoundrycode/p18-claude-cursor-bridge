"""Release 2026.10.11d (the A5 follow-up text release, the report cycle's text items of
2026-10-11 and the owner's decision D1): the texts say what the changelog says, and the two
program lines for the builder's report file hold."""
import os
import re
import subprocess
import sys

from instructions import instructions

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
BRIDGE = os.path.join(ROOT, "bridge")
PLAN_CHECK = os.path.join(BRIDGE, "cursor-bridge", "plan-check.py")
SCOPE_CHECK = os.path.join(BRIDGE, "cursor-bridge", "scope-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def text(*parts):
    return open(os.path.join(BRIDGE, *parts), encoding="utf-8").read()


SV = instructions()   # the core and its phase modules (TASK-010)
SP = text("agents", "spec-packager.md")
DR = text("agents", "diff-reviewer.md")


def section(src, start, end):
    return src[src.index(start):src.index(end)]


# --- the texts ---------------------------------------------------------------------------

def test_the_quiet_rule_names_the_writing_subagents():
    """Entry 2 (reAngle ISS-014): a brief written during a Review B run flagged GATE-INTEGRITY."""
    step8 = section(SV, "### 8. Merge (the verified gate)", "### 9. Refactoring")
    quiet = step8[step8.index("**While it runs, nothing of yours writes to the checkout**"):]
    quiet = quiet[:quiet.index("**Afterwards**")]
    for name in ("`spec-packager`", "`diagram-specialist`", "`cursor-configurator`", "status-file edits"):
        assert name in quiet, name


def test_the_builders_report_is_a_file_in_every_brief_variant():
    """Entry D2: the report is written as the builder goes; the last message is its summary."""
    scope = section(SP, "## Scope", "## Out of scope")
    assert "- handoff/TASK-<nnn>-r<N>-report.md\n" in scope, "the Scope names the report file beside the notes file"
    done = section(SP, "## Done", "The report file and the `Assumed, not verified` section")
    assert "handoff/TASK-<nnn>-r<N>-report.md" in done and "write as you go" in done
    assert "Your last message is the summary and the report file's path" in done
    assert "`Assumed, not verified`" in done, "the assumptions section stays in the Done section"
    variants = [line for line in SP.split("\n") if line.startswith("- **Scope** names")]
    assert len(variants) == 2 and all("report file" in line for line in variants), variants
    assert "REFAC-<nnn>-r<N>-report.md" in SP, "the refactoring variant's report file is named"
    step4 = section(SV, "### 4. Inspect", "### 5. Scan")
    assert "`handoff/TASK-<nnn>-r<N>-report.md` it writes as it runs" in step4
    assert "a hint, never evidence" in step4
    assert "It stands in the builder's report file" in step4, "the assumptions list is read from the report file"
    step8 = section(SV, "### 8. Merge (the verified gate)", "### 9. Refactoring")
    assert "builder's report `handoff/TASK-<nnn>-r<N>-report.md`" in step8, "the SCOPE file lists the report as expected"
    assert "Never treat the builder's own report as evidence" in DR
    assert "builder's report file under `handoff/`" in text("cursor-bridge", "Merge-Verification-Policy.md")


def test_mutation_drivers_belong_to_the_supervisors_side():
    """Entry D3 (reAngle TASK-010c): five mutants that did not model their names cost three rounds."""
    step4 = section(SV, "### 4. Inspect", "### 5. Scan")
    assert "written here too, on your side, after the builder's run and never by the builder" in step4
    assert "a fix brief after a driver run asks for the code fix only" in step4
    assert "`bridge-stop.py` (KP-056)" in step4
    constraints = section(SP, "## Constraints", "## Done")
    assert "is the supervisor's side's, written after your run with the criterion" in constraints
    assert "asks you to list each mutation with" in constraints, "the brief's mutation list (A5) stays"
    assert "**A mutation driver is read like a test.**" in DR
    kp = text("cursor-bridge", "Known-Pitfalls.md")
    assert "never by the builder (2026.10.11d)" in section(kp, "### KP-056", "### KP-057")


def test_a_maintainers_request_is_recorded_and_answered():
    """Decision D1 of 2026-10-11: the owner relays nothing and asks nothing."""
    rule57 = section(SV, "57. **A message from the maintainer session", "58. **A material change")
    assert "`Maintainer requests:` line" in rule57 and "`FB-nnn` entry" in rule57 and "one FYI line" in rule57
    assert "Maintainer requests: <none | <what> — asked <date> — open | answered FB-nnn>\n" in SV
    assert "issue placeholders and the answer to a maintainer's request, rule 57, aside" in SV
    assert "The answer to a maintainer's request (rule 57) is one line of it." in section(SV, "## Reporting to the user", "## Project state")


def test_a_stage_review_runs_in_parts_of_at_most_25_test_files():
    stage = section(SV, "**At a stage close, after the refactoring pass has merged", "**Then the stage's demonstration runs live:**")
    assert "the test files' part at most 25 files" in stage
    assert "run/review/STAGE-<name>-r<N>-<part>.diff" in stage
    assert "run again on what it had not reached (rule 43)" in stage


def test_a_suite_over_ten_minutes_runs_through_the_launcher():
    step4 = section(SV, "### 4. Inspect", "### 5. Scan")
    assert "600 seconds, KP-061" in step4 and "--kind test" in step4
    tr = text("agents", "test-runner.md")
    assert "ten minutes is not yours to run" in tr and "KP-061" in tr
    kp = text("cursor-bridge", "Known-Pitfalls.md")
    assert "### KP-061 — A test suite over ten minutes ended inside a subagent's foreground call" in kp
    assert kp.count("### KP-061") == 1


def test_the_ci_watch_that_returns_at_once_confirms_the_head():
    step8 = section(SV, "### 8. Merge (the verified gate)", "### 9. Refactoring")
    assert "wait for the first check to appear" in step8
    assert "statusCheckRollup,headRefOid" in step8 and "(KP-051)" in step8


def test_the_changelog_entry_exists_and_the_digest_is_unchanged_in_size():
    cl = text("cursor-bridge", "CHANGELOG.md")
    assert cl.index("## 2026.10.11d") < cl.index("## 2026.10.11c")
    entry = section(cl, "## 2026.10.11d", "## 2026.10.11c")
    for part in ("**What changed**", "**Running projects must**", "**If rolled back**", "**Field acceptance on the trial project.**"):
        assert part in entry, part
    assert "Maintainer requests:" in entry
    a, b = SV.index("<!-- digest:start -->"), SV.index("<!-- digest:end -->")
    assert len(SV[a:b]) <= 9500, "a text release adds nothing to the digest"


# --- the two program lines --------------------------------------------------------------

def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


PLAN = """# Build plan

## Stage: one
Demonstration: start it

### TASK-001 — the parser
Satisfies: R-001
Scope: src/parse.py
Depends on: none
Parent: none
Parallel: no
"""


def test_a_builders_report_file_is_not_read_as_a_brief(tmp_path):
    """plan-check.py globs handoff/TASK-*.md; the report beside the brief has no Scope and would be a BRIEF finding."""
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "docs" / "BUILD_PLAN.md").write_text(PLAN, encoding="utf-8")
    (r / "handoff" / "TASK-001.md").write_text("# TASK-001\nSatisfies: R-001\n\n## Scope\n- src/parse.py\n- docs/BUILDER_NOTES.md\n- handoff/TASK-001-r1-report.md\n\n## Constraints\n- none\n", encoding="utf-8")
    (r / "handoff" / "TASK-001-r1-report.md").write_text("# Report\nChanged src/parse.py.\n\nAssumed, not verified: none\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    p = subprocess.run([sys.executable, PLAN_CHECK, "--base", "main"], cwd=str(r), capture_output=True, text=True, env=ENV)
    out = p.stdout + p.stderr
    assert p.returncode == 0 and "BRIEF" not in out, "the report file was read as a brief: " + out
    assert "READY: TASK-001" in out, out


def test_a_builders_report_file_is_bookkeeping_for_the_scope_check(tmp_path):
    r = tmp_path / "ws"
    (r / "src").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "docs").mkdir()
    (r / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (r / "handoff" / "TASK-001.md").write_text("# TASK-001\n\n## Scope\n- src/a.py\n- docs/BUILDER_NOTES.md\n\n## Constraints\n- none\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "checkpoint TASK-001")
    (r / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    (r / "handoff" / "TASK-001-r1-report.md").write_text("# Report\n", encoding="utf-8")
    (r / "handoff" / "TASK-001-notes.md").write_text("# not a report\n", encoding="utf-8")
    p = subprocess.run([sys.executable, SCOPE_CHECK, "handoff/TASK-001.md"], cwd=str(r), capture_output=True, text=True, env=ENV)
    out = p.stdout + p.stderr
    assert "BOOKKEEPING (1), never drift: handoff/TASK-001-r1-report.md" in out, out
    assert p.returncode == 1 and "handoff/TASK-001-notes.md" in out.split("SCOPE DRIFT (")[-1], "a handoff file that is not the report is still drift: " + out


def test_the_report_pattern_in_both_scripts():
    import importlib.util
    for name, path in (("scope_check", SCOPE_CHECK), ("plan_check", PLAN_CHECK)):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rx = mod.REPORT_RX
        for good in ("handoff/TASK-012-r1-report.md", "handoff/REFAC-003-r2-report.md", "handoff/TASK-010c-r3-report.md", "handoff/BUG-004-r1-report.md"):
            assert rx.match(good), (name, good)
        for bad in ("handoff/TASK-012-r2.md", "handoff/TASK-012.md", "handoff/sub/TASK-012-r1-report.md", "handoff/TASK-012-r1-report.md.bak", "docs/TASK-012-r1-report.md"):
            assert not rx.match(bad), (name, bad)
