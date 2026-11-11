"""BUG-044, the supervisor's reproduction tests (R-062): stage H2's review (STAGE-H2-r1) found that records-migrate.py
writes a plan header the headed plan's own readers then refuse, so a project following calibrate-bridge.md's
migration item comes out of a records-only checkpoint with a red gate:

- a `### <ID>` heading standing before the plan's first `## ` stage heading is left out of the header, and once the
  plan has a header plan-check.py reports `SHAPE: <ID> has a ### heading but stands outside any stage` and the
  launcher's `plan_header_refusal` refuses (Review A, STAGE-H2-r1, the bridge part);
- a bold `Satisfies` line (`**Satisfies:** R-099`, `**Satisfies**: R-011`), which the prose fallback's field pattern
  does not read and completion-check.py's outside-header scan does, is left out of the header's `satisfies`, and
  completion-check.py --mode plan then fails `HEADER DISAGREES: satisfies` (Review B, STAGE-H2-r1).

The confirmed cause of both: the migration's read-back checks `header_agrees` against the same fallback that composed
the header, never what the headed plan's readers check. The ruling: such a plan is not written; the migration lists it
as `cannot read <path>: <reason>`, the reason naming the increment and what the prose must become, and writes nothing;
and the read-back of a plan also runs the readers' checks, so a header they would refuse is never written.

With them, three findings of the same review ride: the plans enumerated under a root whose path holds a glob character
(`[`), and a brief with no `Merge unit:` line written `merge_unit: null` as spec-packager.md's template shows it.

enforces: docs/BUILD_PLAN.md, TASK-051's Done when (every `docs/BUILD_PLAN*.md`; the read-back); R-062 ("append-only,
reopening no gate"); bridge/commands/calibrate-bridge.md, step 4's migration item; bridge/agents/spec-packager.md,
the brief header (`null` where the brief has no such line).
"""
import os
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

PROGRAM = os.path.join(BRIDGE, "records-migrate.py")
DASH = chr(0x2014)
PLAN_REL = "docs/BUILD_PLAN.md"


def git_env():
    return dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
                GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def run(cwd, program, *args):
    p = subprocess.run([sys.executable, program] + [str(a) for a in args], cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=git_env(), timeout=120)
    return p.returncode, p.stdout + p.stderr


def migrate(cwd, *args):
    return run(cwd, PROGRAM, *args)


def write(root, rel, text):
    path = os.path.join(str(root), *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(text.encode("utf-8"))
    return path


def read(root, rel):
    with open(os.path.join(str(root), *rel.split("/")), "rb") as f:
        return f.read()


def lines_naming(out, prefix, rel):
    """The rest of every `<prefix><path>...` line whose path names rel (shown relative, as given or absolute)."""
    hits = []
    for line in out.splitlines():
        if not line.startswith(prefix):
            continue
        rest = line[len(prefix):]
        path = rest.split(": ", 1)[0].strip().replace("\\", "/")
        if path == rel or path.endswith("/" + rel):
            hits.append(rest)
    return hits


# ---------------------------------------------------------------- the plans

OUTSIDE_STAGE_PLAN = """# Build plan {d} an early project

### TASK-001 {d} the reader
Depends on: none
Parallel: no
Scope: src/reader.py
Satisfies: R-001

## Stage S2 {d} the writer
Demonstration: it writes.

### TASK-002 {d} the writer
Depends on: TASK-001
Parallel: no
Scope: src/writer.py
Satisfies: R-002
""".format(d=DASH)

BOLD_SATISFIES_PLAN = """# Build plan {d} Example

## Stage A1 {d} the parser
Demonstration: the parser reads a file.

### TASK-001 {d} the reader
Depends on: none
Parallel: no
Scope: src/reader.py
Satisfies: R-004
**Satisfies:** R-099

### TASK-002 {d} the writer
Depends on: TASK-001
Parallel: no
Scope: src/writer.py
**Satisfies**: R-011
""".format(d=DASH)

PLAIN_PLAN = """# Build plan {d} Example

## Stage A1 {d} the parser
Demonstration: the parser reads a file.

### TASK-001 {d} the reader
Depends on: none
Parallel: no
Scope: src/reader.py
Satisfies: R-004, R-099

### TASK-002 {d} the writer
Depends on: TASK-001
Parallel: no
Scope: src/writer.py
Satisfies: R-011
""".format(d=DASH)

BRIEF_NO_MERGE_UNIT = """# TASK-007: the writer (R-007)

## Objective
Build the writer.

Satisfies: R-007 - the writer writes each record.

## Scope
Files you may modify:
- src/writer.py
- tests/test_writer.py

## Out of scope
- .env and anything under secrets/
"""


def project(tmp_path, files, name="proj"):
    root = tmp_path / name
    root.mkdir()
    for rel, text in files:
        write(root, rel, text)
    return root


# ---------------------------------------------------------------- the two blocking findings

def test_bug044_a_plan_heading_outside_any_stage_is_listed_cannot_read_and_not_written(tmp_path):
    """Review A, STAGE-H2-r1: TASK-001 stands before the first `## ` heading. Without a header the plan is valid (the
    readers keep it); with the header the migration composed it would be refused. The migration writes nothing and
    lists the plan `cannot read`, the reason naming TASK-001 and `outside any stage`."""
    root = project(tmp_path, [(PLAN_REL, OUTSIDE_STAGE_PLAN)])
    before = read(root, PLAN_REL)
    code, out = migrate(root, "--check")
    assert not lines_naming(out, "would write ", PLAN_REL), out
    hits = lines_naming(out, "cannot read ", PLAN_REL)
    assert len(hits) == 1, out
    assert "TASK-001" in hits[0] and "outside any stage" in hits[0], hits
    assert code == 0, out
    code, out = migrate(root)
    assert read(root, PLAN_REL) == before, out
    assert len(lines_naming(out, "cannot read ", PLAN_REL)) == 1, out
    assert code == 0, out
    assert sorted(os.listdir(os.path.join(str(root), "docs"))) == ["BUILD_PLAN.md"]


def test_bug044_a_bold_satisfies_line_is_listed_cannot_read_and_not_written(tmp_path):
    """Review B, STAGE-H2-r1: a bold Satisfies line the prose fallback does not read and completion-check.py's
    outside-header scan does. The migration writes nothing and lists the plan `cannot read`, the reason naming an R-id
    on such a line and the plain `Satisfies:` form the prose must take."""
    root = project(tmp_path, [(PLAN_REL, BOLD_SATISFIES_PLAN)])
    before = read(root, PLAN_REL)
    code, out = migrate(root, "--check")
    assert not lines_naming(out, "would write ", PLAN_REL), out
    hits = lines_naming(out, "cannot read ", PLAN_REL)
    assert len(hits) == 1, out
    assert ("R-099" in hits[0] or "R-011" in hits[0]) and "Satisfies" in hits[0], hits
    assert code == 0, out
    code, out = migrate(root)
    assert read(root, PLAN_REL) == before, out
    assert code == 0, out


def test_bug044_the_plain_form_of_the_same_plan_migrates_and_its_readers_accept_the_header(tmp_path):
    """The repair the reason names: the same IDs on plain `Satisfies:` lines. The plan is written, and the headed plan
    passes what its readers check: plan_header_refusal is None, plan_header_findings has no line, and every R-id
    completion-check.py's outside-header scan reads is in the header's satisfies."""
    root = project(tmp_path, [(PLAN_REL, PLAIN_PLAN)])
    code, out = migrate(root)
    assert code == 0, out
    text = bridge_env.decode_record_bytes(read(root, PLAN_REL))
    header, _body = bridge_env.read_header(text)
    assert header is not None, text[:200]
    assert bridge_env.plan_header_refusal(text, PLAN_REL) is None
    fatal, disagree, _h = bridge_env.plan_header_findings(PLAN_REL, text, None)
    assert fatal == [] and disagree == [], (fatal, disagree)
    in_header = {rid for st in header["stages"] for inc in st["increments"] for rid in inc.get("satisfies") or []}
    assert set(bridge_env.plan_r_ids_outside_headers(text)) <= in_header, in_header


def requirements_for(ids):
    rows = "".join("| %s | requirement %s | owner | planned | |\n" % (rid, rid) for rid in ids)
    return "# Requirements\n\n| ID | Requirement | Source | Status | Evidence |\n|---|---|---|---|---|\n" + rows


GATE_CASES = {
    "outside-stage": (OUTSIDE_STAGE_PLAN, ["R-001", "R-002"]),
    "bold-satisfies": (BOLD_SATISFIES_PLAN, ["R-004"]),
    "plain": (PLAIN_PLAN, ["R-004", "R-011", "R-099"]),
}


@pytest.mark.parametrize("case", sorted(GATE_CASES))
def test_bug044_after_the_migration_plan_check_and_completion_check_answer_as_before(tmp_path, case):
    """The gate a running project meets after calibrate-bridge.md's records-only checkpoint, which reopens no gate:
    plan-check.py --no-git and completion-check.py --mode plan pass before the migration on each plan, and pass after
    it, whether the migration wrote the plan (plain) or listed it `cannot read` (the two the readers would refuse)."""
    plan, ids = GATE_CASES[case]
    root = project(tmp_path, [(PLAN_REL, plan), ("docs/REQUIREMENTS.md", requirements_for(ids))])
    plan_check = os.path.join(BRIDGE, "plan-check.py")
    completion = os.path.join(BRIDGE, "completion-check.py")
    pc_before = run(root, plan_check, "--no-git")
    cc_before = run(root, completion, "--mode", "plan")
    assert pc_before[0] == 0 and cc_before[0] == 0, (pc_before, cc_before)
    code, out = migrate(root, PLAN_REL)
    assert code == 0, out
    pc_after = run(root, plan_check, "--no-git")
    cc_after = run(root, completion, "--mode", "plan")
    assert pc_after[0] == 0, pc_after
    assert cc_after[0] == 0, cc_after


# ---------------------------------------------------------------- the findings that ride

def test_bug044_a_glob_character_in_the_root_s_path_still_finds_the_plans(tmp_path):
    """Review A, STAGE-H2-r1 (the briefs part): a root whose folder name holds `[1]` lists its plan as a root without
    one does (`would write`, exit 1), never silently nothing."""
    root = project(tmp_path, [(PLAN_REL, PLAIN_PLAN)], name="proj[1]")
    code, out = migrate(root, "--check")
    assert len(lines_naming(out, "would write ", PLAN_REL)) == 1, out
    assert code == 1, out


def test_bug044_a_brief_with_no_merge_unit_line_is_written_merge_unit_null(tmp_path):
    """Review B (TASK-052-r2 and STAGE-H2-r1) and Review A (STAGE-H2-r1, the tests part), convergent: spec-packager.md
    gives each brief key as `null` where the brief has no such line, and its template shows `merge_unit: null`; the
    migration writes the same, and the header still passes check_header and agrees with the prose."""
    rel = "handoff/TASK-007.md"
    root = project(tmp_path, [(rel, BRIEF_NO_MERGE_UNIT)])
    code, out = migrate(root)
    assert code == 0, out
    text = bridge_env.decode_record_bytes(read(root, rel))
    block = text.split("\n---", 1)[0]
    assert "\nmerge_unit: null" in block, block
    header, _body = bridge_env.read_header(text)
    assert header["merge_unit"] is None
    assert yaml.safe_load(block[len("---"):])["merge_unit"] is None
    assert bridge_env.check_header("brief", header) == []
    fb = bridge_env.brief_prose_fallback(bridge_env.decode_record_bytes(BRIEF_NO_MERGE_UNIT.encode("utf-8")),
                                         "TASK-007")
    assert bridge_env.header_agrees("brief", header, fb) == []


# ---------------------------------------------------------------- the builder adds its cases below this line and edits nothing above it
