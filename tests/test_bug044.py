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

import importlib.util

BRIEF_WITH_MERGE_UNIT = """# TASK-008: merge unit held (R-062)

## Objective
Hold merge unit.

Satisfies: R-008

Merge unit: TASK-008 TASK-009

## Scope
- src/a.py

## Out of scope
- secrets/
"""

F2_STAGE_SATISFIES = """# Build plan {d} stage line

## Stage A1 {d} the stage
Demonstration: none.
Satisfies: R-050

### TASK-001 {d} one
Depends on: none
Parallel: no
Scope: a.py
Satisfies: R-004
""".format(d=DASH)

F2_H4_SATISFIES = """# Build plan {d} h4 line

## Stage A1 {d} the stage
Demonstration: none.

### TASK-001 {d} one
Depends on: none
Parallel: no
Scope: a.py
Satisfies: R-004
#### Note
Satisfies: R-051
""".format(d=DASH)

F2_DOUBLE_SATISFIES = """# Build plan {d} two lines

## Stage A1 {d} the stage
Demonstration: none.

### TASK-001 {d} one
Depends on: none
Parallel: no
Scope: a.py
Satisfies: R-004
Satisfies: R-099
""".format(d=DASH)


def load_migrate():
    spec = importlib.util.spec_from_file_location("records_migrate_bug044", PROGRAM)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def call_main(mod, argv):
    return mod.main(list(argv))


def no_temps_under(root, subdir):
    folder = os.path.join(str(root), *subdir.split("/"))
    return not any(n.startswith(".records-migrate-") for n in os.listdir(folder))


def test_bug044_r062_f3_outside_stage_read_back_fails_with_f1_patched(tmp_path, monkeypatch):
    """BUG-044 F3: with F1's pre-compose refusal patched away, a headed plan the readers refuse still fails read-back."""
    root = project(tmp_path, [(PLAN_REL, OUTSIDE_STAGE_PLAN)])
    before = read(root, PLAN_REL)
    mod = load_migrate()
    monkeypatch.setattr(mod, "_plan_outside_stage_refusal", lambda _text: None)
    monkeypatch.setattr(mod, "_plan_satisfies_coverage_refusal", lambda _text, _header: None)
    monkeypatch.chdir(str(root))
    code = call_main(mod, [])
    assert code == 3
    assert read(root, PLAN_REL) == before
    assert no_temps_under(root, "docs")


def test_bug044_r062_f3_bold_satisfies_read_back_fails_with_f2_patched(tmp_path, monkeypatch):
    """BUG-044 F3: with F2's pre-write refusal patched away, satisfies coverage still fails read-back."""
    root = project(tmp_path, [(PLAN_REL, BOLD_SATISFIES_PLAN)])
    before = read(root, PLAN_REL)
    mod = load_migrate()
    monkeypatch.setattr(mod, "_plan_satisfies_coverage_refusal", lambda _text, _header: None)
    monkeypatch.chdir(str(root))
    code = call_main(mod, [])
    assert code == 3
    assert read(root, PLAN_REL) == before
    assert no_temps_under(root, "docs")


def test_bug044_r062_f3_outside_stage_in_memory_check_fails_under_check(tmp_path, monkeypatch):
    """BUG-044 F3: the in-memory check under --check also runs the readers' rules."""
    root = project(tmp_path, [(PLAN_REL, OUTSIDE_STAGE_PLAN)])
    mod = load_migrate()
    monkeypatch.setattr(mod, "_plan_outside_stage_refusal", lambda _text: None)
    monkeypatch.setattr(mod, "_plan_satisfies_coverage_refusal", lambda _text, _header: None)
    monkeypatch.chdir(str(root))
    code = call_main(mod, ["--check"])
    assert code == 3


@pytest.mark.parametrize("plan,rel,needle", [
    (OUTSIDE_STAGE_PLAN, "docs/BUILD_PLAN.md", "outside any stage"),
    (BOLD_SATISFIES_PLAN, "docs/BUILD_PLAN.md", "Satisfies line"),
    (OUTSIDE_STAGE_PLAN, "docs/BUILD_PLAN-b.md", "outside any stage"),
    (BOLD_SATISFIES_PLAN, "docs/BUILD_PLAN-b.md", "Satisfies line"),
], ids=["f1-main", "f2-main", "f1-addendum", "f2-addendum"])
def test_bug044_f1_f2_cannot_read_on_crlf_and_addendum(tmp_path, plan, rel, needle):
    """BUG-044 F1/F2: refusal on CRLF plans and on enumerated addendum files."""
    crlf = plan.replace("\n", "\r\n")
    files = [(rel, crlf)]
    if rel.endswith("BUILD_PLAN-b.md"):
        files.insert(0, (PLAN_REL, PLAIN_PLAN))
    root = project(tmp_path, files)
    path = os.path.join(str(root), *rel.split("/"))
    before = read(root, rel)
    code, out = migrate(root)
    assert read(root, rel) == before
    hits = lines_naming(out, "cannot read ", rel)
    assert len(hits) == 1 and needle in hits[0], hits
    assert code == 0
    with open(path, "rb") as f:
        assert b"\r\n" in f.read()


@pytest.mark.parametrize("plan,rid", [
    (F2_STAGE_SATISFIES, "R-050"),
    (F2_H4_SATISFIES, "R-051"),
    (F2_DOUBLE_SATISFIES, "R-004"),
], ids=["stage-before-heading", "below-h4", "second-plain-line"])
def test_bug044_f2_other_satisfies_shapes_listed_cannot_read(tmp_path, plan, rid):
    """BUG-044 F2: every Satisfies shape plan_r_ids_outside_headers reads is covered before write."""
    root = project(tmp_path, [(PLAN_REL, plan)])
    before = read(root, PLAN_REL)
    code, out = migrate(root)
    assert read(root, PLAN_REL) == before
    hits = lines_naming(out, "cannot read ", PLAN_REL)
    assert len(hits) == 1 and rid in hits[0], hits
    assert code == 0


def test_bug044_f5_brief_with_merge_unit_line_keeps_list_not_null(tmp_path):
    """BUG-044 F5: a brief that has Merge unit: still writes the list, not null."""
    rel = "handoff/TASK-008.md"
    root = project(tmp_path, [(rel, BRIEF_WITH_MERGE_UNIT)])
    code, out = migrate(root)
    assert code == 0, out
    text = bridge_env.decode_record_bytes(read(root, rel))
    header, _body = bridge_env.read_header(text)
    assert header["merge_unit"] == ["TASK-008", "TASK-009"]
    block = text.split("\n---", 1)[0]
    assert "merge_unit: [TASK-008, TASK-009]" in block
    assert "merge_unit: null" not in block
    brief_name = "TASK-008"
    fb = bridge_env.brief_prose_fallback(bridge_env.decode_record_bytes(BRIEF_WITH_MERGE_UNIT.encode("utf-8")),
                                         brief_name)
    assert bridge_env.check_header("brief", header) == []
    assert bridge_env.header_agrees("brief", header, fb) == []


# ---------------------------------------------------------------- the supervisor's case after the builder's run

OUTSIDE_STAGE_NO_SATISFIES_PLAN = OUTSIDE_STAGE_PLAN.replace("Satisfies: R-001\n", "")


def test_bug044_f3_the_read_back_runs_the_readers_shape_rule_on_its_own(tmp_path, monkeypatch, capsys):
    """enforces: handoff/BUG-044.md, F3 (the read-back runs plan_header_refusal, not only the satisfies coverage). The
    outside-stage increment carries no Satisfies line, so the coverage alone passes; with F1's and F2's refusals
    patched away, only the readers' shape rule stops the write: exit 3, the read-back line naming the increment that
    stands outside any stage, the plan byte-identical and no temporary file left."""
    root = project(tmp_path, [(PLAN_REL, OUTSIDE_STAGE_NO_SATISFIES_PLAN)])
    before = read(root, PLAN_REL)
    mod = load_migrate()
    monkeypatch.setattr(mod, "_plan_outside_stage_refusal", lambda _text: None)
    monkeypatch.setattr(mod, "_plan_satisfies_coverage_refusal", lambda _text, _header: None)
    monkeypatch.chdir(str(root))
    code = call_main(mod, [])
    out = capsys.readouterr().out
    assert code == 3, out
    lines = [ln for ln in out.splitlines() if "read-back failed" in ln]
    assert len(lines) == 1 and "TASK-001" in lines[0] and "outside any stage" in lines[0], out
    assert read(root, PLAN_REL) == before
    assert no_temps_under(root, "docs")


def test_bug044_f4_a_sibling_folder_the_raw_pattern_matches_is_never_listed(tmp_path):
    """enforces: handoff/BUG-044.md, F4 (the plan glob escapes the root); the security audit's advisory of BUG-044
    round 1. Beside the root `proj[1]` stands a sibling `proj1` whose plan the unescaped pattern matches (shown first,
    the precondition); the migration lists the root's own plan once and names nothing of the sibling's."""
    import glob as glob_module
    root = project(tmp_path, [(PLAN_REL, PLAIN_PLAN)], name="proj[1]")
    project(tmp_path, [("docs/BUILD_PLAN_x.md", PLAIN_PLAN)], name="proj1")
    raw = glob_module.glob(os.path.join(str(root), "docs", "BUILD_PLAN*.md"))
    assert any(p.endswith("BUILD_PLAN_x.md") for p in raw), raw
    code, out = migrate(root, "--check")
    assert len(lines_naming(out, "would write ", PLAN_REL)) == 1, out
    assert "BUILD_PLAN_x" not in out, out
    assert code == 1, out


import re  # noqa: E402

SCHEMA_BREAK_BRIEF ="---\nrecord: brief\nheader: 1\n---\n" + BRIEF_NO_MERGE_UNIT


def test_bug044_the_calibration_s_malformed_stop_says_what_the_message_names(tmp_path):
    """enforces: bridge/commands/calibrate-bridge.md, step 4, the stop on HEADER MALFORMED (Review B, BUG-044 round 1):
    a header that breaks its schema stops the run with exit 2 and a message naming the keys, with no line number, so
    the text names the keys for that case and the line only for a header that cannot be read."""
    rel = "handoff/TASK-009.md"
    root = project(tmp_path, [(rel, SCHEMA_BREAK_BRIEF)])
    code, out = migrate(root, "--check")
    assert code == 2, out
    hits = [ln for ln in out.splitlines() if ln.startswith("HEADER MALFORMED: ") and rel in ln]
    assert len(hits) == 1 and "missing key id" in hits[0], out
    assert not re.search(r"\bline \d", hits[0]), out
    unreadable = "---\nrecord: brief\nheader: 1\nid:\tTASK-009\n---\n" + BRIEF_NO_MERGE_UNIT
    root2 = project(tmp_path, [(rel, unreadable)], name="proj2")
    code, out = migrate(root2, "--check")
    assert code == 2, out
    hits = [ln for ln in out.splitlines() if ln.startswith("HEADER MALFORMED: ") and rel in ln]
    assert len(hits) == 1 and re.search(r"HEADER MALFORMED: handoff/TASK-009\.md: line \d+: ", hits[0]), out
    with open(os.path.join(ROOT, "bridge", "commands", "calibrate-bridge.md"), encoding="utf-8") as fh:
        text = " ".join(fh.read().split())
    assert "a header that cannot be read, the message naming its line, or one that breaks its schema, the message " \
           "naming the keys" in text
