"""TASK-089 (R-111, C30): a plan heading's increment id takes the prefixes TASK, BUG, DEP, CONFIG and FIX.

The supervisor's acceptance tests, written before the brief and red on the checkpoint where they say so.
One tuple of prefixes in bridge_env.py; PLAN_ID_PATTERN composed of it; the walker, the plan check, the
completion check's reading of Satisfies, records-migrate's header and the launcher's merge-unit rule all
read a `### BUG-001` heading as an increment; `### REFAC-001`, `### DEV-001`, `### TEST-001` and
`### R-027` stay no increments; records-check.py keeps its own list (TASK, BUG, FIX), so a merged DEP or
CONFIG subject needs no docs/CHANGES.md line, as on the checkpoint.

enforces: docs/DESIGN.md, Change: the improvements release, C30; docs/BUILD_PLAN.md TASK-089's Done when; R-111.
"""
import ast
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bridge_env  # noqa: E402
import test_header_plan as hp  # noqa: E402  (the plan and completion labs, reused as they stand)
import test_task032_supervisor_launcher as t32  # noqa: E402  (the launcher's lab, reused as it stands)
from test_header_currency import code_tree as _tree  # noqa: E402

DASH = chr(0x2014)
PREFIXES = ("TASK", "BUG", "DEP", "CONFIG", "FIX")
OTHERS = ("BUG", "DEP", "CONFIG", "FIX")
NOT_INCREMENTS = ("REFAC-001", "DEV-001", "TEST-001", "R-027")
RECORDS_CHECK = os.path.join(BRIDGE, "records-check.py")
RECORDS_MIGRATE = os.path.join(BRIDGE, "records-migrate.py")


# ---------------------------------------------------------------- the one tuple and the pattern composed of it

def test_task089_one_tuple_of_prefixes_in_bridge_env():
    got = getattr(bridge_env, "PLAN_ID_PREFIXES", None)
    assert isinstance(got, tuple) and got == PREFIXES, got


def test_task089_the_plan_id_pattern_is_the_explicit_alternation_of_the_tuple():
    assert bridge_env.PLAN_ID_PATTERN == r"(?:TASK|BUG|DEP|CONFIG|FIX)-\d{3,}[a-z]?", bridge_env.PLAN_ID_PATTERN


ACCEPTED = ["TASK-001", "TASK-087d", "BUG-001", "DEP-002", "CONFIG-003", "FIX-004", "FIX-1234b"]
REFUSED = ["REFAC-001", "DEV-001", "TEST-001", "R-027", "HOTFIX-004", "BUG-01", "BUG-001ab", "BUG-001A", "bug-001",
           "Task-001", "TASKBUG-001", "BUG001"]


@pytest.mark.parametrize("pid", ACCEPTED)
def test_task089_the_pattern_accepts_each_prefix(pid):
    assert re.fullmatch(bridge_env.PLAN_ID_PATTERN, pid), pid


@pytest.mark.parametrize("pid", REFUSED)
def test_task089_the_pattern_refuses_the_other_forms(pid):
    assert not re.fullmatch(bridge_env.PLAN_ID_PATTERN, pid), pid


def test_task089_the_pattern_composes_inside_a_larger_pattern():
    """The pattern is embedded in the heading, subject and trailer patterns: its alternation is grouped."""
    rx = re.compile(r"^x(%s)y$" % bridge_env.PLAN_ID_PATTERN)
    assert rx.match("xBUG-001y").group(1) == "BUG-001"
    assert not rx.match("xTASKy") and not rx.match("xBUG-001")


@pytest.mark.parametrize("prefix", PREFIXES)
def test_task089_a_heading_of_each_prefix_is_read(prefix):
    m = bridge_env.HEAD_RX.match("### %s-007 %s the title" % (prefix, DASH))
    assert m and m.group(1) == "%s-007" % prefix and m.group(2) == "the title", m


@pytest.mark.parametrize("pid", NOT_INCREMENTS)
def test_task089_the_other_headings_are_no_increment_headings(pid):
    assert bridge_env.HEAD_RX.match("### %s %s the title" % (pid, DASH)) is None


# ---------------------------------------------------------------- no other pattern of a plan id

SCANNED = ["bridge_env.py", "plan-check.py", "bridge-run.py", "records-migrate.py"]
TASK_ONLY = re.compile(r"(?i)task-(?:\\d|\*|\[)|\(\?:task\|")


@pytest.mark.parametrize("program", SCANNED)
def test_task089_no_task_only_pattern_stands_in_the_program(program):
    """Docstrings out (KP-073): no string constant is a TASK-only pattern (`TASK-\\d`, `TASK-*`, `task-[`) or the
    bare `TASK-` a candidate id is built from; every reader takes the prefixes from bridge_env.PLAN_ID_PREFIXES."""
    own = []
    for node in ast.walk(_tree(program)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if TASK_ONLY.search(node.value) or node.value.lower() == "task-":
                own.append(node.value)
    assert not own, "%s holds a TASK-only pattern: %r" % (program, own)


@pytest.mark.parametrize("program", ["plan-check.py", "bridge-run.py", "records-migrate.py"])
def test_task089_the_programs_compile_no_plan_id_pattern_of_their_own(program):
    """A program that needs the plan id reads bridge_env.PLAN_ID_PATTERN (or HEAD_RX); none spells the prefixes."""
    spelled = []
    for node in ast.walk(_tree(program)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if re.search(r"\b(?:BUG|DEP|CONFIG|FIX)\|", node.value) or re.search(r"\|(?:BUG|DEP|CONFIG|FIX)\b", node.value):
                spelled.append(node.value)
    assert not spelled, "%s spells the prefixes itself: %r" % (program, spelled)


def test_task089_records_check_keeps_its_own_list():
    """records-check.py is not edited: its own list stays TASK, BUG and FIX (C30)."""
    with open(RECORDS_CHECK, encoding="utf-8") as f:
        text = f.read()
    assert 'ID = r"(?:TASK|BUG|FIX)-\\d{3,}[a-z]?"' in text
    assert "bridge_env" not in text


# ---------------------------------------------------------------- the walker and the plan's id reader

WALK_PLAN = """# Plan

## Stage 1 %(d)s fixes
Demonstration: the fixes run.

### TASK-001 %(d)s base
Scope: src/a.py
Satisfies: R-001

### BUG-001 %(d)s a bug
Depends on: TASK-001
Scope: src/b.py
Satisfies: R-002

### DEP-002 %(d)s a dependency
Depends on: BUG-001
Scope: requirements.txt

### CONFIG-003 %(d)s a setting
Scope: config/c.toml

### FIX-004 %(d)s a fix
Depends on: DEP-002, CONFIG-003
Scope: src/d.py

### REFAC-001 %(d)s no increment
Scope: src/e.py

### DEV-001 %(d)s no increment
Scope: src/f.py

### TEST-001 %(d)s no increment
Scope: src/g.py

### R-027 %(d)s no increment
Scope: src/h.py
""" % {"d": DASH}
WALK_IDS = ["TASK-001", "BUG-001", "DEP-002", "CONFIG-003", "FIX-004"]


def test_task089_the_walker_reads_each_prefix_and_no_other_heading():
    walk = bridge_env.walk_plan_prose_body(WALK_PLAN)
    incs = walk["stages"][0]["increments"]
    assert [i["id"] for i in incs] == WALK_IDS, [i["id"] for i in incs]
    by_id = {i["id"]: i for i in incs}
    assert by_id["BUG-001"]["fields"].get("satisfies") == "R-002"
    assert by_id["BUG-001"]["fields"].get("depends on") == "TASK-001"
    assert by_id["FIX-004"]["fields"].get("scope") == "src/d.py", "a field under REFAC-001 was read into FIX-004"


def test_task089_plan_increment_ids_reads_each_prefix(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "BUILD_PLAN.md").write_text(WALK_PLAN, encoding="utf-8")
    assert set(bridge_env.plan_increment_ids(str(tmp_path))) == set(WALK_IDS)


# ---------------------------------------------------------------- the plan check

def walk_repo(tmp_path, subjects, plan=WALK_PLAN, briefs=None):
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "docs" / "BUILD_PLAN.md").write_text(plan, encoding="utf-8", newline="")
    for name, text in (briefs or {}).items():
        (r / "handoff" / name).write_text(text, encoding="utf-8", newline="")
    hp.git(r, "init", "-q", "-b", "main")
    hp.git(r, "add", "-A")
    hp.git(r, "commit", "-q", "-m", "scratch")
    for subject in subjects:
        hp.git(r, "commit", "-q", "--allow-empty", "-m", subject)
    return r


def ready_ids(out):
    return [l.split()[1] for l in out.splitlines() if l.startswith("READY: ")]


def test_task089_plan_check_reads_each_prefix_as_an_increment(tmp_path):
    """TASK-001 and BUG-001 merged (a squash subject each); DEP-002 and CONFIG-003 ready; FIX-004 waits for both."""
    repo = walk_repo(tmp_path, ["TASK-001: base (#1)", "BUG-001: a bug (#2)"])
    rc, out = hp.plan_check(repo)
    assert rc == 0, out
    assert "note: 5 increments in 1 file(s); 2 merged, 0 deferred" in out.splitlines(), out
    assert ready_ids(out) == ["DEP-002", "CONFIG-003"], out
    assert not [l for l in hp.answer(out) if not l.startswith(("READY", "TOGETHER", "RESULT"))], out


def test_task089_a_subject_counts_as_merged_only_where_the_plan_holds_its_heading(tmp_path):
    """FIX-009 and REFAC-001 merged on the base: neither is a merged increment, FIX-009 having no heading and REFAC-001
    being no increment; the count of merged increments is the plan's own."""
    repo = walk_repo(tmp_path, ["TASK-001: base (#1)", "FIX-009: elsewhere (#2)", "REFAC-001: a pass (#3)"])
    rc, out = hp.plan_check(repo)
    assert rc == 0, out
    assert "note: 5 increments in 1 file(s); 1 merged, 0 deferred" in out.splitlines(), out
    assert ready_ids(out) == ["BUG-001", "CONFIG-003"], out


@pytest.mark.parametrize("subject", [
    "Merge pull request #7 from someone/bug-001",
    "Merge branch 'bug-001'",
    "fix(walker): a bug (BUG-001) (#7)",
    "a bug\n\nMerges: BUG-001",
], ids=["merge-pull-request", "merge-branch", "closing-parenthesis", "trailer"])
def test_task089_each_merged_form_names_a_bug_increment(tmp_path, subject):
    repo = walk_repo(tmp_path, ["TASK-001: base (#1)", subject])
    rc, out = hp.plan_check(repo)
    assert rc == 0, out
    assert "note: 5 increments in 1 file(s); 2 merged, 0 deferred" in out.splitlines(), out
    assert ready_ids(out) == ["DEP-002", "CONFIG-003"], out


def test_task089_a_headed_plan_with_a_bug_increment_agrees(tmp_path):
    """The header names BUG-001 and DEP-002 and their depends_on; the prose's headings and lines agree: no
    HEADER line, the answer as for TASK ids."""
    stages = [{"name": "Stage 1 %s fixes" % DASH, "demo": "the fixes run.", "incs": [
        {"id": "TASK-001", "title": "base", "lines": ["Depends on: none", "Satisfies: R-001", "Scope: src/a.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/a.py"], "satisfies": ["R-001"], "historic": False}},
        {"id": "BUG-001", "title": "a bug", "lines": ["Depends on: TASK-001", "Satisfies: R-002", "Scope: src/b.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": ["TASK-001"], "parallel": False, "diagrams": [],
               "scope": ["src/b.py"], "satisfies": ["R-002"], "historic": False}},
        {"id": "DEP-002", "title": "a dependency", "lines": ["Depends on: BUG-001", "Scope: requirements.txt"],
         "h": {"kind": "increment", "parent": None, "depends_on": ["BUG-001"], "parallel": False, "diagrams": [],
               "scope": ["requirements.txt"], "satisfies": [], "historic": False}},
    ]}]
    repo = hp.plan_repo(tmp_path, hp.plan_text(stages), merged=("TASK-001",))
    rc, out = hp.plan_check(repo)
    assert rc == 0 and "HEADER" not in out, out
    assert ready_ids(out) == ["BUG-001"], out


def test_task089_plan_check_reads_a_bug_increments_brief(tmp_path):
    """handoff/BUG-001.md is the brief of BUG-001: its Scope outside the increment's is a BRIEF line; a REFAC brief
    and a BUG report file are not read."""
    brief = "# BUG-001\n\nSatisfies: R-002\n\n## Scope\n- src/zzz.py\n"
    repo = walk_repo(tmp_path, ["TASK-001: base (#1)"], briefs={
        "BUG-001.md": brief, "REFAC-001.md": brief.replace("BUG-001", "REFAC-001"),
        "BUG-001-r1-report.md": "# report\n\n## Scope\n- src/yyy.py\n"})
    rc, out = hp.plan_check(repo)
    lines = [l for l in out.splitlines() if l.startswith("BRIEF: ")]
    assert lines == ["BRIEF: handoff/BUG-001.md names src/zzz.py in its Scope, outside BUG-001's Scope (src/b.py)"], out
    assert rc == 1, out


# ---------------------------------------------------------------- the completion check's reading of Satisfies

C_REGISTER = """| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | parse the file | owner | built | tests/test_parse.py |
| R-002 | fix the bug | owner | planned | - |
"""


def completion_plan(heading):
    return ("# Plan\n\n## Stage 1\nDemonstration: the parser runs.\n\n"
            "### TASK-001 %(d)s parser\nSatisfies: R-001\nScope: src/parse.py\n\n"
            "### %(h)s %(d)s the second\nSatisfies: R-002\nScope: src/fix.py\n" % {"d": DASH, "h": heading})


def completion_repo(tmp_path, plan):
    r = tmp_path / "ws"
    for d in ("docs", "tests", "src"):
        (r / d).mkdir(parents=True)
    (r / "docs" / "REQUIREMENTS.md").write_text(C_REGISTER, encoding="utf-8")
    (r / "docs" / "BUILD_PLAN.md").write_text(plan, encoding="utf-8", newline="")
    (r / "tests" / "test_parse.py").write_text("def test_it():  # R-001\n    assert True\n", encoding="utf-8")
    hp.git(r, "init", "-q", "-b", "main")
    hp.git(r, "add", "-A")
    hp.git(r, "commit", "-q", "-m", "scratch")
    return r


@pytest.mark.parametrize("prefix", OTHERS)
def test_task089_the_completion_check_reads_satisfies_under_each_prefix(tmp_path, prefix):
    rc, out = hp.run(hp.COMPLETION_CHECK, completion_repo(tmp_path, completion_plan("%s-002" % prefix)), "--mode", "plan")
    assert "UNPLANNED: R-002" not in out, out
    assert "UNPLANNED: R-001" not in out, out


@pytest.mark.parametrize("pid", ["REFAC-002", "DEV-002", "TEST-002"])
def test_task089_satisfies_under_another_heading_plans_nothing(tmp_path, pid):
    rc, out = hp.run(hp.COMPLETION_CHECK, completion_repo(tmp_path, completion_plan(pid)), "--mode", "plan")
    assert rc == 1 and "UNPLANNED: R-002" in out, out


# ---------------------------------------------------------------- records-migrate's plan header

MIGRATE_PLAN = """# Plan

## Stage 1 %(d)s fixes
Demonstration: the fix runs.

### BUG-003 %(d)s something

### CONFIG-004 %(d)s next
Kind: increment
Scope: src/a.py
Satisfies: R-002

### REFAC-005 %(d)s no increment
Scope: src/b.py
""" % {"d": DASH}


def test_task089_records_migrate_writes_a_bug_increment_into_the_header(tmp_path):
    """BUG-003, merged on the base, is a historic increment of the written header; CONFIG-004 an increment;
    REFAC-005 none."""
    repo = tmp_path / "proj"
    (repo / "docs").mkdir(parents=True)
    hp.git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    hp.git(repo, "add", "README.md")
    hp.git(repo, "commit", "-q", "-m", "initial")
    hp.git(repo, "commit", "-q", "--allow-empty", "-m", "BUG-003: something (#12)")
    (repo / "docs" / "BUILD_PLAN.md").write_text(MIGRATE_PLAN, encoding="utf-8", newline="")
    rc, out = hp.run(RECORDS_MIGRATE, repo, "--base", "main")
    assert rc == 0, out
    header, _body = bridge_env.read_header((repo / "docs" / "BUILD_PLAN.md").read_text(encoding="utf-8"))
    assert header is not None, out
    incs = header["stages"][0]["increments"]
    assert [i["id"] for i in incs] == ["BUG-003", "CONFIG-004"], incs
    assert incs[0]["historic"] is True and incs[1]["historic"] is False, incs
    assert incs[1]["satisfies"] == ["R-002"] and incs[1]["scope"] == ["src/a.py"], incs


# ---------------------------------------------------------------- the launcher's merge-unit rule

@pytest.mark.parametrize("prefix", OTHERS)
def test_task089_a_merge_unit_may_name_an_increment_of_each_prefix(tmp_path, prefix):
    lab = t32.Lab(tmp_path, branch="task-010")
    other = "%s-011" % prefix
    t32.write_plan(lab, "TASK-010", other)
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 %s\n" % other)
    row = t32.assert_ran(t32.launch(lab, t32.build("TASK-010")))
    assert sorted(row.get("merge_ids") or []) == sorted(["TASK-010", other]), row


@pytest.mark.parametrize("pid", ["REFAC-011", "DEV-011", "TEST-011"])
def test_task089_a_merge_unit_naming_another_heading_is_refused(tmp_path, pid):
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, "TASK-010", pid)
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 %s\n" % pid)
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-010")), "bridge-run: refused - brief rule: ")
    assert pid in line, line


def test_task089_a_bug_brief_naming_its_unit_runs_on_its_branch(tmp_path):
    """BUG-011's own brief declares the unit BUG-011 TASK-012, both headings of the plan."""
    lab = t32.Lab(tmp_path, branch="bug-011")
    t32.write_plan(lab, "BUG-011", "TASK-012")
    t32.write_brief(lab.root, "BUG-011", "\nMerge unit: BUG-011 TASK-012\n")
    row = t32.assert_ran(t32.launch(lab, t32.build("BUG-011")))
    assert sorted(row.get("merge_ids") or []) == ["BUG-011", "TASK-012"], row


# ---------------------------------------------------------------- records-check keeps its own list

def changes_repo(tmp_path, subjects):
    r = tmp_path / "rc"
    (r / "docs").mkdir(parents=True)
    (r / "docs" / "CHANGES.md").write_text("# Changes\n\n- TASK-001: the base\n", encoding="utf-8")
    hp.git(r, "init", "-q", "-b", "main")
    hp.git(r, "add", "-A")
    hp.git(r, "commit", "-q", "-m", "scratch")
    since = hp.git(r, "rev-parse", "HEAD")
    for subject in subjects:
        hp.git(r, "commit", "-q", "--allow-empty", "-m", subject)
    return r, since


def test_task089_a_merged_dep_or_config_subject_needs_no_changes_line(tmp_path):
    repo, since = changes_repo(tmp_path, ["TASK-001: the base (#1)", "DEP-002: a dependency (#2)",
                                          "CONFIG-003: a setting (#3)"])
    rc, out = hp.run(RECORDS_CHECK, repo, "--since", since, "--ref", "main")
    assert rc == 0 and "MISSING" not in out, out


def test_task089_a_merged_bug_subject_still_needs_its_changes_line(tmp_path):
    repo, since = changes_repo(tmp_path, ["BUG-004: a bug (#4)"])
    rc, out = hp.run(RECORDS_CHECK, repo, "--since", since, "--ref", "main")
    assert rc == 1 and "BUG-004" in out, out


# ================================================================ round 2

# ---------------------------------------------------------------- an id inside a longer word is no plan id

WORD_PLAN = """# Plan

## Stage 1 %(d)s words
Demonstration: the plan reads.

### TASK-001 %(d)s base
Scope: src/a.py

### TASK-002 %(d)s after a hotfix
Depends on: HOTFIX-004
Scope: src/b.py

### TASK-003 %(d)s under a debug group
Parent: DEBUG-001
Scope: src/c.py

### TASK-004 %(d)s after a subtask
Depends on: SUBTASK-001
Scope: src/d.py
""" % {"d": DASH}


def test_task089_r2_an_id_inside_a_longer_word_is_read_whole_by_plan_check(tmp_path):
    """`HOTFIX-004`, `DEBUG-001` and `SUBTASK-001` name no plan id: each value is unreadable as written, and no line
    names FIX-004, BUG-001 or TASK-001 as a dependency or a parent (round 1 read the id out of the longer word)."""
    repo = walk_repo(tmp_path, ["TASK-001: base (#1)"], plan=WORD_PLAN)
    rc, out = hp.plan_check(repo)
    lines = out.splitlines()
    assert rc == 1, out
    assert not [l for l in lines if "depends on FIX-004" in l or "names parent BUG-001" in l
                or "depends on TASK-001" in l and "TASK-004" in l], out
    for tid, key, value in (("TASK-002", "Depends On", "HOTFIX-004"), ("TASK-003", "Parent", "DEBUG-001"),
                            ("TASK-004", "Depends On", "SUBTASK-001")):
        want = "DEPENDS: %s has an unreadable %s value '%s'" % (tid, key, value)
        assert [l for l in lines if l.startswith(want)], (want, out)


@pytest.mark.parametrize("key,value,want", [
    ("depends_on", "HOTFIX-004", []),
    ("depends_on", "TASK-001, HOTFIX-004", ["TASK-001"]),
    ("depends_on", "SUBTASK-001", []),
    ("depends_on", "BUG-001 (the fix), FIX-002", ["BUG-001", "FIX-002"]),
    ("parent", "DEBUG-001", "DEBUG-001"),
    ("parent", "BUG-001", "BUG-001"),
], ids=["hotfix", "task-and-hotfix", "subtask", "two-ids", "debug-parent", "bug-parent"])
def test_task089_r2_the_headers_field_reading_keeps_a_longer_word_whole(key, value, want):
    """The header's parent and depends_on reading (records-migrate's header and plan-check's agreement) reads an id
    only where it stands as a word of its own; a parent value naming no id is kept as written, as on the checkpoint."""
    assert bridge_env._plan_normalize_field(key, value) == (key, want)


# ---------------------------------------------------------------- the branch names of every prefix, both styles

GRAMMAR_MERGES = [
    ("Merge pull request #1 from someone/bug-001", {"BUG-001"}),
    ("Merge branch 'Bug-001a'", {"BUG-001a"}),
    ("Merge branch 'bug-001-x'", {"BUG-001"}),
    ("Merge branch 'config-003'", {"CONFIG-003"}),
    ("Merge branch 'dep-002'", {"DEP-002"}),
    ("Merge branch 'task-031-x'", {"TASK-031"}),
    ("Merge branch 'task-03x'", {"TASK-03x"}),
    ("Merge branch 'task-12-fix'", {"TASK-12-fix"}),
    ("Merge branch 'bug-12-fix'", {"BUG-12-fix"}),
    ("Merge branch 'hotfix-004'", {"HOTFIX-004"}),
]


@pytest.mark.parametrize("line,want", GRAMMAR_MERGES, ids=[l.split()[-1].strip("'") for l, _ in GRAMMAR_MERGES])
def test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task(line, want):
    """The launcher's reading (the grammar's pattern): a branch named for an id of any of the five prefixes maps as a
    `task-` branch did on the checkpoint, the prefix upper-cased, the digits and letter kept (a longer name giving the
    id it begins with), else the prefix upper-cased and the rest as written; a `task-` name whose rest begins with a
    digit answers as on the checkpoint, and a name of another prefix (`hotfix-004`) as before. A rest that begins with
    a letter (`task-cleanup`) keeps its case, where the checkpoint upper-cased it: the supervisor's ruling at round 2,
    not one of the five (the launcher's lapse ignores case), recorded in docs/HARDENING.md (TASK-089)."""
    got = bridge_env.squash_merged_ids_from_lines([line], bridge_env.grammar_id_rx(), plan_style=False)
    assert got == want, (line, got)


PLAN_MERGES = [
    ("Merge branch 'Bug-001'", {"BUG-001"}),
    ("Merge pull request #3 from someone/bug-001-x", {"BUG-001"}),
    ("Merge pull request #3 from someone/feat/fix-004", {"FIX-004"}),
    ("Merge branch 'bug-001ab'", set()),
    ("Merge branch 'hotfix-004'", set()),
    ("Merge branch 'debug-001'", set()),
]


@pytest.mark.parametrize("line,want", PLAN_MERGES, ids=[l.split()[-1].strip("'") for l, _ in PLAN_MERGES])
def test_task089_r2_the_plan_style_maps_a_branch_of_each_prefix(line, want):
    got = bridge_env.squash_merged_ids_from_lines([line], bridge_env.PLAN_ID_PATTERN)
    assert got == want, (line, got)


def test_task089_r2_a_leading_id_wins_over_the_closing_parenthesis():
    """The supervisor's ruling on Review A's note: one rule for every prefix, as for `TASK-119: x (TASK-120)` on the
    checkpoint: a subject whose start names ids merges those, and its closing parenthesis is not read."""
    got = bridge_env.squash_merged_ids_from_lines(["BUG-018: x (TASK-031, TASK-100) (#61)"], bridge_env.PLAN_ID_PATTERN)
    assert got == {"BUG-018"}, got
    got = bridge_env.squash_merged_ids_from_lines(["TASK-119: x (TASK-120) (#62)"], bridge_env.PLAN_ID_PATTERN)
    assert got == {"TASK-119"}, got
