"""TASK-048 round 3, the supervisor's reproduction tests (R-059; D-002): the defects the round-2 security audit and
Review A reproduced on the builder's round 2 (7dacef3), each a case that fails there and must pass on the next round.

enforces: docs/DESIGN.md, "Change: release B2", "The fallback readers, one copy each" ("the one piece of code that
reads prose is the one that ... checks it"), "Header first; fallback; malformed"; the round-1 brief's Requirement 5
("For a merged increment, the Scope is read as today and no failure is printed") and Requirement 8 (plan-check's brief
comparison reads the brief's Scope, header first); the round-2 brief's RA-9 (one plan body walker) and its security
context (a gate refuses rather than guess between two readings; no exception swallowed); R-059. The fixtures and
helpers are tests/test_header_plan.py's and tests/test_header_plan_r2.py's, reused as they stand.

What each case pins:
- plan-check's brief comparison runs on a brief with an agreeing header exactly as on a header-less one: a Scope
  path outside the increment's Scope, or an R-id the brief does not name, is a BRIEF finding (the audit's first
  blocking finding: the agreeing case returned nothing);
- a `###` increment heading outside any stage of a headed plan is a failure naming its ID in plan-check and a
  refusal in the launcher's plan reading, never READY and never a merge-unit ID the header does not declare (the
  audit and Review A: RA-9's walkers still diverge);
- a merged increment whose Scope line carries an unbalanced parenthesis can agree with a header: the headed plan
  gives the header-less plan's answer (Review A: the fallback stored a marker no header can equal; this repository's
  plan has fifteen such merged increments);
- the launcher reads a brief's lines as the other programs do, so a brief with bare carriage returns is refused like
  any other disagreeing brief (the audit);
- the launcher refuses a plan file it cannot read, never skipping it (the audit and Review A);
- no reader takes a blocking class or a merge unit from inside a malformed header block (Review A: the brief readers
  fell back to the whole text on a malformed header);
- plan-check and completion-check walk no plan themselves: no heading or field pattern of bridge_env's is used in
  either program (RA-9).
"""
import ast

import pytest

import test_header_plan as hp
import test_task032_supervisor_launcher as t32

be = hp.bridge_env
run = hp.run
DASH = hp.DASH


# ---------------------------------------------------------------- the brief comparison with an agreeing header

def _brief(header, scope, satisfies):
    text = "# TASK-003\n\n"
    if satisfies:
        text += "Satisfies: %s\n\n" % ", ".join(satisfies)
    text += "## Scope\n" + "".join("- %s\n" % p for p in scope)
    if header:
        text = hp.brief_header(id_="TASK-003", satisfies=satisfies, scope=scope) + text
    return text


BRIEF_CASES = [
    ("scope-outside", ("src/export.py", "src/evil/x.py"), ("R-004",), "src/evil/x.py"),
    ("satisfies-unnamed", ("src/export.py",), (), "R-004"),
]


@pytest.mark.parametrize("scope,satisfies,named", [c[1:] for c in BRIEF_CASES], ids=[c[0] for c in BRIEF_CASES])
def test_r059_r3_plan_check_compares_a_brief_with_an_agreeing_header(tmp_path, scope, satisfies, named):
    for header, name in ((False, "bare"), (True, "headed")):
        repo = hp.plan_repo(tmp_path, hp.plan_text(header=False), name=name)
        (repo / "handoff" / "TASK-003.md").write_text(_brief(header, scope, satisfies), encoding="utf-8", newline="")
        rc, out = hp.plan_check(repo)
        hits = [l for l in hp.lines_starting(out, "BRIEF: handoff/TASK-003.md") if named in l]
        assert rc == 1 and hits, (name, out)                  # the header-less run is the precondition


# ---------------------------------------------------------------- one walker: a heading outside any stage

ORPHAN = "### TASK-009 %s orphan\nKind: increment\nScope: src/z.py\n\n" % DASH


def _with_orphan(prose):
    return prose.replace("# Plan\n\n", "# Plan\n\n" + ORPHAN, 1)


def test_r059_r3_a_heading_outside_any_stage_of_a_headed_plan_is_a_failure(tmp_path):
    text = hp.plan_header(hp.STAGES) + _with_orphan(hp.plan_prose(hp.STAGES))
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, text))
    named = [l for l in out.splitlines() if "TASK-009" in l and l.startswith(("SHAPE: ", "HEADER DISAGREES: "))]
    assert rc == 1 and named and not hp.lines_starting(out, "READY: TASK-009"), out


def test_r059_r3_the_launchers_plan_reading_refuses_a_heading_outside_any_stage():
    text = hp.plan_header(hp.STAGES) + _with_orphan(hp.plan_prose(hp.STAGES))
    got = be.plan_header_refusal(text, "docs/BUILD_PLAN.md")
    assert isinstance(got, str) and got, got


def test_r059_r3_the_launcher_accepts_no_merge_unit_id_outside_any_stage(tmp_path):
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, "TASK-010")
    stages = [{"name": "Stage 9", "demo": "it runs.", "incs": [
        {"id": "TASK-015", "title": "two", "lines": ["Kind: increment", "Scope: src/two.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/two.py"], "satisfies": [], "historic": False}}]}]
    (lab.root / "docs" / "BUILD_PLAN-2026-11-04.md").write_bytes(
        (hp.plan_header(stages) + _with_orphan(hp.plan_prose(stages))).encode("utf-8"))
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-009\n")
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-010")), "bridge-run: refused - header: ")
    assert "outside any stage" in line, line                   # the plan's refusal, not the ID reading's


# ---------------------------------------------------------------- a merged Scope with an unbalanced parenthesis

def test_r059_r3_a_merged_unbalanced_scope_can_agree_with_its_header(tmp_path):
    def mutate(s):
        s[0]["incs"][0]["lines"][5] = "Scope: src/parse.py (the reader; its tests)"
        s[0]["incs"][0]["h"]["scope"] = ["src/parse.py (the reader", "its tests)"]
    stages = hp._variant(mutate)
    rc_p, out_p = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_prose(stages), name="bare"))
    assert rc_p == 0, out_p                                   # precondition: merged, read as today, no failure
    rc_h, out_h = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_header(stages) + hp.plan_prose(stages), name="headed"))
    assert rc_h == 0 and hp.answer(out_h) == hp.answer(out_p) and not hp.lines_starting(out_h, "HEADER"), out_h


# ---------------------------------------------------------------- the launcher reads lines as the others do

def test_r059_r3_the_launcher_refuses_a_disagreeing_brief_with_bare_carriage_returns(tmp_path):
    lab = t32.Lab(tmp_path)
    text = hp.brief_header(satisfies=(), scope=("b.py",)) + "# TASK-001\n\n## Objective\nFixture brief.\n\n## Scope\n- a.py\n"
    (lab.root / "handoff" / "TASK-001.md").write_bytes(text.replace("\n", "\r").encode("ascii"))
    t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")


def test_r059_r3_the_launcher_refuses_a_plan_file_it_cannot_read(tmp_path):
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, "TASK-010", "TASK-011")
    (lab.root / "docs" / "BUILD_PLAN-2026-11-04.md").mkdir()     # matched by the plan glob, and opening it fails
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-011\n")
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-010")), "bridge-run: refused - ")
    assert "BUILD_PLAN-2026-11-04.md" in line, line


# ---------------------------------------------------------------- nothing read from inside a malformed header

MALFORMED = ("---\nrecord: brief\nheader: 1\nround:\t1\nBlocking class: security - in the header block\n"
             "Merge unit: TASK-001 TASK-002\n---\n# TASK-001\n\n## Scope\n- a.py\n")


def test_r059_r3_no_class_is_read_from_inside_a_malformed_header():
    with pytest.raises(be.HeaderError):                        # precondition: the block is malformed
        be.read_header(MALFORMED)
    assert be.read_blocking_class_line(MALFORMED) is None


def test_r059_r3_no_merge_unit_is_read_from_inside_a_malformed_header():
    assert be.merge_unit_ids(MALFORMED) is None and not be.merge_unit_line_present(MALFORMED)


# ---------------------------------------------------------------- RA-9: the programs walk no plan themselves

@pytest.mark.parametrize("prog", ["plan-check.py", "completion-check.py"], ids=["plan-check", "completion-check"])
def test_r059_r3_the_program_walks_no_plan_itself(prog):
    used = sorted({n.attr for n in ast.walk(hp._tree(prog)) if isinstance(n, ast.Attribute)
                   and n.attr in ("HEAD_RX", "FIELD_RX", "DEMO_RX", "STAGE_RX")})
    assert not used, "%s walks the plan itself with bridge_env's %s" % (prog, ", ".join(used))


# ---------------------------------------------------------------- builder's cases below this line
