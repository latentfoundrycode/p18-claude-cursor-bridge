"""plan-check.py (release A4, R17 and 13.1): a commit marks an increment merged only when its subject
starts with the ID (or a merge commit's branch does); a dependency the parser cannot read fails
instead of vanishing; each brief is compared with its increment; a dated addendum is read with the
plan. Scratch repositories."""
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "plan-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")

PLAN = """# Plan

## Stage 1
Demonstration: the parser runs.

### TASK-001 — parser
Satisfies: R-001
Scope: src/parse.py

### TASK-002 — writer
Depends on: TASK-001
Satisfies: R-002
Scope: src/write.py

### TASK-003 — graph
Depends on: TASK-002
Satisfies: R-003, R-004
Scope: src/graph/

### TASK-004 — export
Depends on: TASK-003
Satisfies: R-005
Scope: src/export.py

### TASK-006a — lettered one
Satisfies: R-010
Scope: src/l1.py

### TASK-006b — lettered two
Satisfies: R-011
Scope: src/l2.py

### TASK-007 — exporter, merged under the TDP's subject form
Depends on: TASK-006a, TASK-006b (TASK-006b added 2026-10-03: the pair ships together; see the note)
Satisfies: R-009
Scope: src/exp/

### TASK-008 — merged by a records commit's Merges: trailer
Satisfies: R-012
Scope: src/rec.py
"""


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV, timeout=120)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def make(tmp_path, plan=PLAN):
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "docs" / "BUILD_PLAN.md").write_text(plan, encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    git(r, "commit", "-q", "--allow-empty", "-m", "TASK-001: the parser")
    git(r, "commit", "-q", "--allow-empty", "-m", "Merge pull request #5 from owner/task-002-writer")
    git(r, "commit", "-q", "--allow-empty", "-m", "docs: plan split TASK-003 out of TASK-004")
    git(r, "commit", "-q", "--allow-empty", "-m", "TASK-006a TASK-006b: the lettered pair (#7)")
    git(r, "commit", "-q", "--allow-empty", "-m", "feat(export): the exporter (TASK-007, R-009) - v0.2.0 (#8)")
    git(r, "commit", "-q", "--allow-empty", "-m", "records: the stage close\n\nMerges: TASK-008")
    return r


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG, "--base", "main"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV, timeout=120)
    return p.returncode, p.stdout + p.stderr


def test_a_commit_that_mentions_two_increments_merges_neither(tmp_path):
    r = make(tmp_path)
    rc, out = run(r)
    assert rc == 0 and "6 merged" in out and "READY: TASK-003" in out and "READY: TASK-004" not in out, "the docs commit marked TASK-003 and TASK-004 merged (R17): " + out
    for tid in ("TASK-006a", "TASK-006b", "TASK-007", "TASK-008"):
        assert "READY: %s" % tid not in out, "%s is merged: a lettered ID keeps its case, several IDs at the start all count, the IDs in parentheses at the end count, a Merges: trailer counts (first pass, F1 and F4): %s" % (tid, out)
    assert "DEPENDS" not in out, "a dated note in parentheses on a Depends on line is not an ID (first pass, F3): " + out


def test_an_unreadable_dependency_fails_instead_of_vanishing(tmp_path):
    r = make(tmp_path, PLAN.replace("Depends on: TASK-002", "Depends on: TASK-02"))
    rc, out = run(r)
    assert rc == 1 and "DEPENDS: TASK-003" in out and "TASK-02" in out, "`Depends on: TASK-02` was silently dropped (R17): " + out


def test_each_brief_is_compared_with_its_increment(tmp_path):
    r = make(tmp_path)
    (r / "handoff" / "TASK-003.md").write_text("# TASK-003\nSatisfies: R-003 graph\n\n## Scope\n- src/graph/draw.py\n- src/export.py\n- docs/BUILDER_NOTES.md\n\n## Constraints\n- none\n", encoding="utf-8")
    rc, out = run(r)
    assert rc == 1 and "BRIEF: handoff/TASK-003.md" in out and "src/export.py" in out and "R-004" in out, "a brief that drops a requirement and reaches outside its increment (13.1): " + out
    (r / "handoff" / "TASK-003.md").write_text("# TASK-003\nSatisfies: R-003, R-004\n\n## Scope\n- src/graph/draw.py\n- docs/BUILDER_NOTES.md\n\n## Constraints\n- none\n", encoding="utf-8")
    rc, out = run(r)
    assert rc == 0, "the bookkeeping file every brief names is not a BRIEF finding (first pass, F2): " + out


def test_a_dated_addendum_is_read_with_the_plan(tmp_path):
    r = make(tmp_path)
    (r / "docs" / "BUILD_PLAN-2026-10-11-addendum.md").write_text("# Addendum 2026-10-11\n\n## Change cycle: colours\nDemonstration: the graph in colour.\n\n### TASK-005 — colours\nDepends on: TASK-002\nSatisfies: R-006\nScope: src/colour.py\n", encoding="utf-8")
    rc, out = run(r)
    assert rc == 0 and "READY: TASK-005" in out and "addendum" in out.lower(), out


WORKSPACE = os.path.abspath(os.path.join(HERE, os.pardir))
CB = os.path.join(WORKSPACE, "bridge", "cursor-bridge")
F_ID = r"TASK-\d{3,}[a-z]?"
F_SUBJECT = re.compile(r"^\s*((?:%s[\s,:]*)+)" % F_ID)
F_TRAIL = re.compile(r"\(([^()]*%s[^()]*)\)\s*(?:[-\u2014\u2013]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$" % F_ID)
F_MERGE = re.compile(r"^\s*Merge (?:pull request #\d+ from \S+?/|branch ')(task-\d{3,}[a-z]?)\b", re.I)
F_ID_RX = re.compile(F_ID)


def _commit_subject_lines(repo, sha):
    detail = subprocess.run(
        ["git", "log", "-1", sha, "--format=%s%n%(trailers:key=Merges,valueonly)"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=ENV,
        timeout=120,
    )
    assert detail.returncode == 0
    return detail.stdout.splitlines()


def _former_merged_ids_per_commit(repo):
    revs = subprocess.run(
        ["git", "log", "main", "--format=%H"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=ENV,
        timeout=120,
    )
    assert revs.returncode == 0
    out = {}
    for sha in revs.stdout.splitlines():
        merged = set()
        for line in _commit_subject_lines(repo, sha):
            m = F_SUBJECT.match(line)
            if m:
                merged.update(F_ID_RX.findall(m.group(1)))
                continue
            m = F_MERGE.match(line)
            if m:
                merged.add("TASK-" + m.group(1)[5:])
                continue
            m = F_TRAIL.search(line)
            if m:
                merged.update(F_ID_RX.findall(m.group(1)))
                continue
            if re.match(r"^\s*(%s)(\s*,\s*%s)*\s*$" % (F_ID, F_ID), line):
                merged.update(F_ID_RX.findall(line))
        out[sha] = merged
    return out


def _new_merged_ids_per_commit(repo):
    import bridge_env

    revs = subprocess.run(
        ["git", "log", "main", "--format=%H"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=ENV,
        timeout=120,
    )
    assert revs.returncode == 0
    out = {}
    for sha in revs.stdout.splitlines():
        out[sha] = bridge_env.squash_merged_ids_from_lines(
            _commit_subject_lines(repo, sha), bridge_env.PLAN_ID_PATTERN, plan_style=True
        )
    return out


def _load_plan_check():
    import importlib.util
    spec = importlib.util.spec_from_file_location("plan_check_t", PROG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_r044_iss013_subject_merges_nothing_beside_bare_parenthesis(tmp_path, monkeypatch):
    """R-044. 9f6ace6's subject merges nothing; (TASK-100, R-027) merges TASK-100."""
    pc = _load_plan_check()
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(repo), env=ENV, check=True, timeout=120)
    iss = subprocess.run(
        ["git", "log", "-1", "--format=%s", "9f6ace6"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if iss.returncode != 0:
        pytest.skip("9f6ace6 not in this checkout")
    git(repo, "commit", "-q", "--allow-empty", "-m", "feat(x): ok (TASK-100, R-027) (#1)")
    git(repo, "commit", "-q", "--allow-empty", "-m", iss.stdout.strip())
    monkeypatch.chdir(str(repo))
    assert pc.merged_ids("main") == {"TASK-100"}


@pytest.mark.parametrize(
    "subject",
    [
        "docs: x (pointers, TASK-031's Scope, survival lists, records) (#61)",
        "(TASK-031's Scope)",
    ],
)
def test_r044_non_bare_parenthesis_merges_nothing(tmp_path, subject, monkeypatch):
    """R-044. Non-bare closing parenthesis merges nothing (ISS-013)."""
    pc = _load_plan_check()
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    monkeypatch.chdir(str(repo))
    assert pc.merged_ids("main") == set()


def test_r044_main_regression_minus_task031(monkeypatch):
    """R-044. Reader on Workspace main equals former rule minus {TASK-031} at 9f6ace6 only."""
    shallow = subprocess.run(
        ["git", "-C", WORKSPACE, "rev-parse", "--is-shallow-repository"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if shallow.returncode != 0 or shallow.stdout.strip() == "true":
        pytest.skip("shallow checkout")
    if (
        subprocess.run(
            ["git", "-C", WORKSPACE, "rev-parse", "--verify", "--quiet", "refs/heads/main"],
            capture_output=True,
            timeout=120,
        ).returncode
        != 0
    ):
        pytest.skip("no local main")
    monkeypatch.syspath_prepend(CB)
    monkeypatch.chdir(WORKSPACE)
    former = _former_merged_ids_per_commit(WORKSPACE)
    new = _new_merged_ids_per_commit(WORKSPACE)
    seen_9f6 = False
    for sha, fset in former.items():
        nset = new.get(sha, set())
        if sha.startswith("9f6ace6") or sha == "9f6ace6":
            seen_9f6 = True
            assert fset - nset == {"TASK-031"}, (sha, fset, nset)
            assert nset - fset == set(), (sha, fset, nset)
        else:
            assert nset == fset, (sha, fset, nset)
    assert seen_9f6
