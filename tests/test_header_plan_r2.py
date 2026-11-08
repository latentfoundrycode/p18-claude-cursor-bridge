"""TASK-048 round 2, the supervisor's reproduction tests (R-059; D-002): the defects the round-1 audit and Review A
reproduced on the builder's round 1, each a case that fails on that round and must pass on the next.

enforces: docs/DESIGN.md, "Change: release B2", "Header first; fallback; malformed" ("a `record:` kind the program
did not expect" is malformed; "never silently falling back"), "The fallback readers, one copy each" ("the one piece
of code that reads prose is the one that ... checks it"), and the brief's security context ("a gate program must
refuse rather than guess between two readings"; "No exception is swallowed"); docs/BUILD_PLAN.md, TASK-048's Done
when; R-059. The fixtures and helpers are tests/test_header_plan.py's, reused as they stand.

What each case pins:
- the Scope scope-check enforces is the Scope the header was compared with: the prose body's, never a `## Scope`
  line found in the header block (the audit's B1);
- a brief's blocking class is read from its prose line only: a class with no `Blocking class:` line carrying a
  finding never lifts the review ceiling, and a second front-matter block in the body is prose, never a header
  (the audit's B2);
- a header of the wrong `record:` kind, or none, or an empty block, is malformed in each of the five programs,
  never read as no header (Review A, 1);
- a headed plan whose unmerged `Scope:` carries an unbalanced parenthesis gets the SHAPE line, no traceback, and a
  merged one is read as today (Review A, 2); under `--no-git` the rule gives a note naming the increment, never
  silence and never a failure (Review A, 7; the supervisor's ruling as revised at round 3);
- scope-check's ellipsis refusal quotes its entry as before, and a leading `./` on a Scope bullet is stripped as
  before (Review A, 3 and 4);
- the historic exemption covers the shape rules and nothing else: a historic child's Parent is still checked and
  still counts as its group's child (Review A, 6);
- an unreadable first brief stops the guard, and a malformed brief header is a finding in plan-check's brief
  comparison, never a silent fallback (Review A, 8);
- plan-check reads a plan's increments from its body: a `###` comment inside the header is no increment (audit);
- the field reading is linear on a long run of spaces (audit);
- the launcher's plan reading refuses a malformed plan header and a header whose increments disagree with the
  headings, never falling back to the whole text or trusting the header alone (audit);
- completion-check walks no plan of its own (Review A, 9).
"""
import ast
import os
import time

import pytest

import test_header_plan as hp
import test_task032_supervisor_launcher as t32
from test_header_plan import scope_repo  # noqa: F401  (the fixture, reused)

be = hp.bridge_env
run = hp.run
DASH = hp.DASH


# ---------------------------------------------------------------- the audit's B1: one Scope, the body's

def _trick(text):
    """A `## Scope` comment as the header's last line and a `- **` line straight after its closing `---`."""
    head, sep, body = text.partition("\n---\n")
    head = head + "\n## Scope"
    return head + sep + "- **\n" + body


def test_r059_r2_scope_check_enforces_the_scope_the_header_was_checked_against(scope_repo):  # noqa: F811
    control = hp.checkpoint(scope_repo, "TASK-001.md", hp.brief_header() + hp.brief_prose())
    (scope_repo / "bridge").mkdir()
    (scope_repo / "bridge" / "evil.py").write_text("x = 1\n", encoding="utf-8")
    rc, out = run(hp.SCOPE_CHECK, scope_repo, control)
    assert rc == 1 and "bridge/evil.py" in out, out             # precondition: the file is drift under the agreed Scope
    text = _trick(hp.brief_header() + hp.brief_prose())
    assert be.read_header(text)[0] is not None                 # precondition: the header still reads
    (scope_repo / "handoff" / "TASK-001.md").write_text(text, encoding="utf-8", newline="")
    rc, out = run(hp.SCOPE_CHECK, scope_repo, control)
    assert rc != 0 and "VERDICT: SCOPE CLEAN" not in out, out


# ---------------------------------------------------------------- the audit's B2: the class from the prose only

def _class_brief(blocks, rnd=4):
    h = hp.brief_header(rnd=rnd, satisfies=(), scope=("a.py",), blocking_class="security")
    return h * blocks + "# TASK-001\n\n## Objective\nFixture brief.\n\n## Scope\n- a.py\n"


@pytest.mark.parametrize("blocks", [1, 2], ids=["one-header", "two-headers"])
def test_r059_r2_a_class_with_no_prose_line_never_reads_as_a_lift(blocks):
    got = be.read_blocking_class_line(_class_brief(blocks))
    assert got is None or (str(got[1]).strip() and str(got[2]).strip()), got


@pytest.mark.parametrize("blocks", [1, 2], ids=["one-header", "two-headers"])
def test_r059_r2_a_header_class_with_no_prose_line_is_refused(blocks):
    got = be.brief_header_refusal(_class_brief(blocks), "handoff/TASK-001-r4.md")
    assert isinstance(got, str) and got.startswith("header: "), got


def test_r059_r2_the_launcher_never_lifts_the_ceiling_on_a_second_header(tmp_path):
    lab = t32.Lab(tmp_path)
    t32.three_completed(lab)
    (lab.root / "handoff" / "TASK-001-r4.md").write_bytes(_class_brief(2).encode("ascii"))
    t32.assert_refused(t32.launch(lab, t32.build("TASK-001-r4")), "bridge-run: refused - ")


# ---------------------------------------------------------------- Review A 1: the wrong record kind is malformed

def _wrong_kind(text, how):
    if how == "typo":
        return text.replace("record: brief", "record: breif", 1).replace("record: build-plan", "record: buildplan", 1)
    if how == "missing":
        return text.replace("record: brief\n", "", 1).replace("record: build-plan\n", "", 1)
    head, sep, body = text.partition("\n---\n")
    return "---\n---\n" + body


KINDS = ["typo", "missing", "empty"]


@pytest.mark.parametrize("how", KINDS, ids=KINDS)
def test_r059_r2_a_brief_header_of_the_wrong_kind_is_refused(how):
    text = _wrong_kind(hp.brief_header(scope=("src/core/b.py", "docs/BUILDER_NOTES.md")) + hp.brief_prose(), how)
    got = be.brief_header_refusal(text, "handoff/TASK-001.md")
    assert isinstance(got, str) and got.startswith("header: "), got


@pytest.mark.parametrize("how", KINDS, ids=KINDS)
def test_r059_r2_scope_check_refuses_a_header_of_the_wrong_kind(scope_repo, how):  # noqa: F811
    text = _wrong_kind(hp.brief_header(scope=("src/zzz.py",)) + hp.brief_prose(), how)
    b = hp.checkpoint(scope_repo, "TASK-001.md", text)
    rc, out = run(hp.SCOPE_CHECK, scope_repo, b)
    assert rc == 2 and hp.lines_starting(out, "HEADER MALFORMED: handoff/TASK-001.md:"), out


def test_r059_r2_the_launcher_refuses_a_header_of_the_wrong_kind(tmp_path):
    lab = t32.Lab(tmp_path)
    hp.lab_brief(lab, "TASK-001", _wrong_kind(hp.brief_header(satisfies=(), scope=("b.py",)), "typo"))
    t32.assert_refused(t32.launch(lab, t32.build("TASK-001")), "bridge-run: refused - header: ")


def test_r059_r2_the_guard_refuses_a_first_brief_of_the_wrong_kind(tmp_path):
    text = _wrong_kind(hp.brief_header(merge_unit=("TASK-001",)) + hp.brief_prose(extra=hp.UNIT), "typo")
    rc, out = run(hp.GUARD, hp.guard_repo(tmp_path, text), "snapshot", "TASK-001")
    assert rc == 125 and out.startswith("review-guard: refused - header: "), out


@pytest.mark.parametrize("prog", ["plan-check", "completion-check"], ids=["plan-check", "completion-check"])
def test_r059_r2_a_plan_header_of_the_wrong_kind_is_malformed(tmp_path, prog):
    if prog == "plan-check":
        rc, out = hp.plan_check(hp.plan_repo(tmp_path, _wrong_kind(hp.plan_text(), "typo")))
    else:
        plan = _wrong_kind(hp.plan_header(hp.C_STAGES) + hp.plan_prose(hp.C_STAGES), "typo")
        rc, out = run(hp.COMPLETION_CHECK, hp.completion_repo(tmp_path, plan), "--mode", "plan")
    assert rc == 2 and hp.lines_starting(out, "HEADER MALFORMED: docs/BUILD_PLAN.md:"), out


# ---------------------------------------------------------------- Review A 2 and 7: the parenthesis rule

def test_r059_r2_a_headed_plan_with_an_unbalanced_unmerged_scope_gets_the_shape_line(tmp_path):
    prose = hp._variant(lambda s: s[1]["incs"][0]["lines"].__setitem__(3, hp.UNBALANCED))
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_header(hp.STAGES) + hp.plan_prose(prose)))
    assert "Traceback" not in out and hp.lines_starting(out, "RESULT: "), out
    hits = [l for l in hp.lines_starting(out, "SHAPE: TASK-003") if "parenthes" in l]
    assert rc == 1 and hits, out


def test_r059_r2_a_headed_plan_with_an_unbalanced_merged_scope_is_read_as_today(tmp_path):
    prose = hp._variant(lambda s: s[0]["incs"][0]["lines"].__setitem__(5, "Scope: src/parse.py (the reader; its tests)"))
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_header(hp.STAGES) + hp.plan_prose(prose)))
    assert "Traceback" not in out and hp.lines_starting(out, "RESULT: "), out
    assert not [l for l in hp.lines_starting(out, "SHAPE: TASK-001") if "parenthes" in l], out


def test_r059_r2_under_no_git_an_unbalanced_scope_is_a_note(tmp_path):
    # The supervisor's ruling, revised at round 3: with no merged set (--no-git or an unreadable log) the rule
    # cannot tell history from new work, so an unbalanced parenthesis is a note naming the increment, never a
    # failure; a SHAPE failure would fail every merged increment of a plan's history (this repository's plan has
    # fifteen). Silence, as on round 1, is not allowed either.
    prose = hp._variant(lambda s: s[1]["incs"][0]["lines"].__setitem__(3, hp.UNBALANCED))
    rc, out = run(hp.PLAN_CHECK, hp.plan_repo(tmp_path, hp.plan_prose(prose)), "--no-git")
    assert rc == 0 and not [l for l in hp.lines_starting(out, "SHAPE: TASK-003") if "parenthes" in l], out
    assert [l for l in hp.lines_starting(out, "note:") if "TASK-003" in l and "parenthes" in l], out


# ---------------------------------------------------------------- Review A 3 and 4: scope-check as before

def test_r059_r2_the_ellipsis_refusal_quotes_its_entry(scope_repo):  # noqa: F811
    text = hp.brief_prose().replace("- src/core/a.py\n", "- src/core/a.py, src/core/b.py, ...\n")
    b = hp.checkpoint(scope_repo, "TASK-001.md", text)
    rc, out = run(hp.SCOPE_CHECK, scope_repo, b)
    want = "CANNOT VERIFY: a Scope entry carries an ellipsis (src/core/a.py, src/core/b.py, ...); name every path or a glob."
    assert rc == 2 and want in out.splitlines(), out


def test_r059_r2_a_leading_dot_slash_on_a_scope_bullet_is_stripped(scope_repo):  # noqa: F811
    b = hp.checkpoint(scope_repo, "TASK-001.md", hp.brief_prose().replace("- src/core/a.py\n", "- ./src/core/a.py\n"))
    rc, out = run(hp.SCOPE_CHECK, scope_repo, b)
    assert rc == 0 and "VERDICT: SCOPE CLEAN" in out, out


# ---------------------------------------------------------------- Review A 6: the historic exemption, shape rules only

def _inc(id_, title, lines, kind="increment", parent=None, scope=(), satisfies=(), historic=False):
    return {"id": id_, "title": title, "lines": list(lines),
            "h": {"kind": kind, "parent": parent, "depends_on": [], "parallel": False, "diagrams": [],
                  "scope": list(scope), "satisfies": list(satisfies), "historic": historic}}


def _grouped(child_parent, with_new=True):
    incs = [_inc("TASK-010", "the group", ["Kind: group"], kind="group"),
            _inc("TASK-011", "the old child", ["Parent: %s" % child_parent], parent=child_parent, historic=True)]
    if with_new:
        incs.append(_inc("TASK-012", "the new child", ["Kind: increment", "Parent: TASK-010", "Satisfies: R-001",
                                                        "Scope: src/g/b.py"], parent="TASK-010", scope=["src/g/b.py"],
                         satisfies=["R-001"]))
    return [{"name": "Stage 1", "demo": "it runs.", "incs": incs}]


def test_r059_r2_a_historic_childs_parent_is_still_checked(tmp_path):
    stages = _grouped("TASK-099")
    want = "PARENT: TASK-011 names parent TASK-099, which does not exist"
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_prose(stages), merged=("TASK-011",), name="bare"))
    assert want in out.splitlines(), out                        # precondition: the header-less plan reports it
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_header(stages) + hp.plan_prose(stages),
                                         merged=("TASK-011",), name="marked"))
    assert rc == 1 and want in out.splitlines(), out


def test_r059_r2_a_historic_child_still_counts_as_its_groups_child(tmp_path):
    stages = _grouped("TASK-010", with_new=False)
    shape = "SHAPE: group TASK-010 has no child increments"
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_prose(stages), merged=("TASK-011",), name="bare"))
    assert shape not in out.splitlines(), out                   # precondition: header-less, the child counts
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, hp.plan_header(stages) + hp.plan_prose(stages),
                                         merged=("TASK-011",), name="marked"))
    assert shape not in out.splitlines(), out


# ---------------------------------------------------------------- Review A 8: nothing swallowed

def test_r059_r2_the_guard_refuses_a_first_brief_it_cannot_read(tmp_path):
    repo = hp.guard_repo(tmp_path, hp.brief_header(merge_unit=("TASK-001",)) + hp.brief_prose())
    hp.git(repo, "rm", "-q", "handoff/TASK-001.md")
    (repo / "handoff" / "TASK-001.md").mkdir(parents=True)     # exists, and opening it fails
    (repo / "handoff" / "TASK-001.md" / "keep.txt").write_text("x\n", encoding="utf-8")
    hp.git(repo, "add", "-A")
    hp.git(repo, "commit", "-q", "-m", "the first brief made unreadable")
    rc, out = run(hp.GUARD, repo, "snapshot", "TASK-001")
    assert rc == 125 and out.startswith("review-guard: refused - "), out


def test_r059_r2_plan_check_reports_a_malformed_brief_header(tmp_path):
    repo = hp.plan_repo(tmp_path, hp.plan_text(header=False))
    text = hp.brief_header(id_="TASK-003", satisfies=("R-004",), scope=("src/export.py",)).replace(
        "round: 1", "round:\t1") + "# TASK-003\n\nSatisfies: R-004\n\n## Scope\n- src/export.py\n"
    (repo / "handoff" / "TASK-003.md").write_text(text, encoding="utf-8", newline="")
    rc, out = hp.plan_check(repo)
    named = [l for l in out.splitlines() if "TASK-003.md" in l and "header" in l.lower()]
    assert rc != 0 and named, out


# ---------------------------------------------------------------- the audit's advisories reproduced

def test_r059_r2_a_heading_comment_inside_a_plan_header_is_no_increment(tmp_path):
    text = hp.plan_header(hp.STAGES).replace("\n---\n", "\n### TASK-099 %s phantom\n---\n" % DASH, 1) + hp.plan_prose(
        hp.STAGES)
    assert be.read_header(text)[0] is not None                 # precondition: a comment line, the header reads
    rc, out = hp.plan_check(hp.plan_repo(tmp_path, text))
    assert rc == 0 and "TASK-099" not in out, out


def test_r059_r2_the_field_reading_is_linear_on_a_long_run_of_spaces():
    # A value, a long run of spaces, a word, another run: the lazy capture before `\s*$` retried every split
    # (40,000 spaces took 2.9 s on the round-1 reading, 20,000 took 0.7 s).
    pad = " " * 60000
    start = time.perf_counter()
    got = list(be.brief_satisfies("# T\n\nSatisfies: R-001" + pad + "x" + pad + "\n"))
    took = time.perf_counter() - start
    assert got == ["R-001"] and took < 1.5, (got, took)


def test_r059_r2_the_launcher_refuses_a_malformed_plan_header(tmp_path):
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, "TASK-010")
    (lab.root / "docs" / "BUILD_PLAN-2026-11-04.md").write_bytes(
        ("---\nrecord: build-plan\nheader:\t1\n---\n# Addendum\n\n### TASK-015 %s two\n\nKind: increment\n"
         % DASH).encode("utf-8"))
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015\n")
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-010")), "bridge-run: refused - ")
    assert "BUILD_PLAN-2026-11-04.md" in line, line


def test_r059_r2_the_launcher_refuses_a_plan_header_whose_increments_have_no_heading(tmp_path):
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, "TASK-010")
    stages = [{"name": "Stage 9", "demo": "it runs.", "incs": [
        _inc("TASK-015", "two", ["Kind: increment", "Scope: src/two.py"], scope=["src/two.py"])]}]
    prose = [{"name": "Stage 9", "demo": "it runs.", "incs": [
        _inc("TASK-016", "two", ["Kind: increment", "Scope: src/two.py"], scope=["src/two.py"])]}]
    (lab.root / "docs" / "BUILD_PLAN-2026-11-04.md").write_bytes(
        (hp.plan_header(stages) + hp.plan_prose(prose)).encode("utf-8"))
    # TASK-016 has a heading and no header entry: only the header comparison refuses it (the ID reading accepts it)
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-016\n")
    t32.assert_refused(t32.launch(lab, t32.build("TASK-010")), "bridge-run: refused - header: ")


def test_r059_r2_completion_check_walks_no_plan_of_its_own():
    used = sorted({n.attr for n in ast.walk(hp._tree("completion-check.py")) if isinstance(n, ast.Attribute)
                   and n.attr in ("HEAD_RX", "FIELD_RX", "DEMO_RX", "STAGE_RX")})
    assert not used, "completion-check.py walks the plan itself with bridge_env's %s" % ", ".join(used)


# ---------------------------------------------------------------- builder's cases below this line
