"""R-110: a brief's `Satisfies` ids are read one way by every program (TASK-088; C29, T96).

The supervisor's acceptance tests, written before the builder's run. The launcher is started on a scratch Workspace
with the stand-in for cursor-agent the other brief-rule tests use (tests/test_task032_supervisor_launcher.py), so no
builder runs; plan-check runs on the scratch plan of tests/test_plan_check.py; the review guard on the scratch
repository of tests/test_header_plan.py.

The one reader is `bridge_env.brief_satisfies_ids(body)`, which returns `(ids, none_carries_ids)`: the R-ids on the
brief's `Satisfies:` line and on the bullet lines directly beneath it, up to the first line that is neither a bullet
nor blank, each id once in first-seen order; and True where the line reads `none` and an id follows on the line or
beneath it.

enforces: docs/DESIGN.md, "Change: the improvements release", C29 and its table of seven rows; docs/BUILD_PLAN.md,
TASK-088's Done when; R-110.
"""
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

import test_task032_supervisor_launcher as t32  # noqa: E402  (the launcher's lab, reused as it stands)
import test_plan_check as tpc  # noqa: E402  (the scratch plan and plan-check's runner)
import test_header_plan as thp  # noqa: E402  (the review guard's scratch repository)

DISAGREES_SATISFIES = "bridge-run: refused - header: disagrees satisfies"
SAME_ROWS = "the header and the prose name the same rows"
NONE_REMEDY = "a brief that satisfies no row reads exactly"


def _q(s):
    return '"%s"' % s


def _flow(items):
    return "[" + ", ".join(_q(x) for x in items) + "]"


def header(satisfies, scope=("a.py",)):
    out = ["---", "record: brief", "header: 1", "id: TASK-001", "round: 1", "satisfies: " + _flow(satisfies),
           "scope: " + _flow(scope), "merge_unit: null", "blocking_class: null", "---"]
    return "\n".join(out) + "\n"


def body(satisfies_lines):
    """The prose of the fixture brief: the given Satisfies lines under the title, Scope a.py."""
    return "# TASK-001\n\n%s\n## Objective\nFixture brief.\n\n## Scope\n- a.py\n" % satisfies_lines


def reader():
    fn = getattr(bridge_env, "brief_satisfies_ids", None)
    assert fn is not None, "bridge_env.brief_satisfies_ids is missing (TASK-088)"
    return fn


def launch(tmp_path, text):
    lab = t32.Lab(tmp_path)
    (lab.root / "handoff" / "TASK-001.md").write_bytes(text.encode("utf-8"))
    return t32.launch(lab, t32.build("TASK-001"))


# ---------------------------------------------------------------- the one reader

def test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath():
    ids, flag = reader()(body("Satisfies:\n- R-077\n* R-078\n\n- R-079\nA sentence.\n- R-080\n"))
    assert list(ids) == ["R-077", "R-078", "R-079"] and flag is False, (ids, flag)


def test_task088_the_reader_names_each_id_once_in_first_seen_order():
    ids, flag = reader()(body("Satisfies: R-078, R-077, R-078\n- R-077\n- R-079\n"))
    assert list(ids) == ["R-078", "R-077", "R-079"] and flag is False, (ids, flag)


@pytest.mark.parametrize("lines,flag", [
    ("Satisfies: none\n", False),
    ("Satisfies: none (R-105 is TASK-084's)\n", True),
    ("Satisfies: none\n- R-105\n", True),
], ids=["none", "none-carries-an-id-on-the-line", "none-carries-an-id-beneath"])
def test_task088_the_reader_flags_a_none_that_carries_ids(lines, flag):
    got = reader()(body(lines))
    assert got[1] is flag, got
    if not flag:
        assert list(got[0]) == [], got


def test_task088_the_briefs_two_readers_call_the_one_reader(monkeypatch):
    """`brief_satisfies` and the header's fallback reading both answer what the one reader answers: no second copy."""
    reader()
    monkeypatch.setattr(bridge_env, "brief_satisfies_ids", lambda text: (["R-999"], False))
    text = header(["R-077"]) + body("Satisfies: R-077\n")
    assert list(bridge_env.brief_satisfies(text)) == ["R-999"]
    rec = bridge_env.read_brief_record(text, "TASK-001")
    assert list(rec.fallback["satisfies"]) == ["R-999"], rec.fallback
    assert list(bridge_env.brief_satisfies(body("Satisfies: R-077\n"))) == ["R-999"]


def test_task088_brief_satisfies_reads_the_bullets():
    assert list(bridge_env.brief_satisfies(body("Satisfies:\n- R-077\n- R-078\n"))) == ["R-077", "R-078"]


# ---------------------------------------------------------------- the design's seven rows, one test each, at the launcher

def test_task088_row1_a_line_of_two_ids_beside_the_same_header_is_launched(tmp_path):
    t32.assert_ran(launch(tmp_path, header(["R-077", "R-078"]) + body("Satisfies: R-077, R-078\n")))


def test_task088_row2_bullets_beneath_the_line_are_launched(tmp_path):
    t32.assert_ran(launch(tmp_path, header(["R-077", "R-078"]) + body("Satisfies:\n- R-077\n- R-078\n")))


def test_task088_row3_a_repeated_id_is_launched(tmp_path):
    t32.assert_ran(launch(tmp_path, header(["R-077"]) + body("Satisfies: R-077, R-077\n")))


def test_task088_row4_the_same_set_in_another_order_is_launched(tmp_path):
    t32.assert_ran(launch(tmp_path, header(["R-077", "R-078"]) + body("Satisfies: R-078, R-077\n")))


def test_task088_row5_none_beside_an_empty_header_is_launched(tmp_path):
    t32.assert_ran(launch(tmp_path, header([]) + body("Satisfies: none\n")))


def test_task088_row6_a_none_that_carries_ids_is_refused_with_the_remedy(tmp_path):
    line = t32.assert_refused(launch(tmp_path, header([]) + body("Satisfies: none (R-105 is TASK-084's)\n")),
                              "bridge-run: refused - ")
    assert NONE_REMEDY in line and "Satisfies: none" in line, line


def test_task088_row7_a_disagreeing_list_is_refused_with_both_lists(tmp_path):
    line = t32.assert_refused(launch(tmp_path, header(["R-077"]) + body("Satisfies: R-078\n")), DISAGREES_SATISFIES)
    assert "R-077" in line and "R-078" in line and SAME_ROWS in line, line


# ---------------------------------------------------------------- the refusals' ASCII path and the header-less brief

def test_task088_a_none_with_a_non_ascii_line_is_refused_in_ascii(tmp_path):
    line = t32.assert_refused(launch(tmp_path, header([]) + body("Satisfies: none — R-105 is TASK-084's\n")),
                              "bridge-run: refused - ")
    assert NONE_REMEDY in line, line
    assert all(ord(c) < 128 for c in line), repr(line)


def test_task088_a_brief_with_no_header_keeps_its_reading_and_no_check_at_launch(tmp_path):
    """As on the checkpoint: a header-less brief is launched, whatever its Satisfies line says."""
    t32.assert_ran(launch(tmp_path, body("Satisfies: none (R-105 is TASK-084's)\n")))


# ---------------------------------------------------------------- plan-check's BRIEF lines

def _plan_brief(header_sat, sat_lines):
    out = ["---", "record: brief", "header: 1", "id: TASK-003", "round: 1", "satisfies: " + _flow(header_sat),
           "scope: " + _flow(["src/graph/draw.py", "docs/BUILDER_NOTES.md"]), "merge_unit: null",
           "blocking_class: null", "---"]
    return ("\n".join(out) + "\n# TASK-003\n%s\n## Scope\n- src/graph/draw.py\n- docs/BUILDER_NOTES.md\n\n"
            "## Constraints\n- none\n" % sat_lines)


def _brief_lines(out):
    return [l for l in out.splitlines() if "BRIEF: handoff/TASK-003.md" in l]


def test_task088_plan_check_names_an_unmerged_brief_whose_header_disagrees(tmp_path):
    r = tpc.make(tmp_path)
    (r / "handoff" / "TASK-003.md").write_text(_plan_brief(["R-003"], "Satisfies: R-003, R-004\n"), encoding="utf-8")
    rc, out = tpc.run(r)
    lines = _brief_lines(out)
    assert rc == 1 and lines and any("satisfies" in l.lower() for l in lines), out


def test_task088_plan_check_names_an_unmerged_brief_whose_none_carries_ids(tmp_path):
    r = tpc.make(tmp_path)
    (r / "handoff" / "TASK-003.md").write_text(_plan_brief([], "Satisfies: none (R-003, R-004)\n"), encoding="utf-8")
    rc, out = tpc.run(r)
    lines = _brief_lines(out)
    assert rc == 1 and any("Satisfies: none" in l for l in lines), out


def test_task088_plan_check_passes_an_agreeing_brief_with_bullets(tmp_path):
    r = tpc.make(tmp_path)
    (r / "handoff" / "TASK-003.md").write_text(_plan_brief(["R-003", "R-004"], "Satisfies:\n- R-004\n- R-003\n"),
                                               encoding="utf-8")
    rc, out = tpc.run(r)
    assert rc == 0 and not _brief_lines(out), out


# ---------------------------------------------------------------- what stands: the review guard and the plan's own line

def test_task088_the_review_guard_answers_as_on_the_checkpoint(tmp_path):
    """The guard's call of the same refusal reads merge_unit, id and round: a satisfies disagreement, a list in
    bullets or a none that carries ids is no refusal of its."""
    unit = "Merge unit: TASK-001 TASK-002\n"
    for name, extra, sat in (("disagree", unit, ("R-001", "R-002")), ("bullets", unit + "- R-002\n", ("R-001", "R-002")),
                             ("none-carries-ids", unit, ())):
        text = thp.brief_header(merge_unit=("TASK-001", "TASK-002"), satisfies=sat)
        if name == "disagree":
            prose = thp.brief_prose(extra=extra)
        elif name == "bullets":
            prose = thp.brief_prose(extra="").replace(
                "Satisfies: R-001 - parse the file\n", "Satisfies:\n- R-001\n- R-002\n" + unit)
        else:
            prose = thp.brief_prose(extra=extra).replace(
                "Satisfies: R-001 - parse the file\n", "Satisfies: none (R-001 is TASK-002's)\n")
        (tmp_path / name).mkdir()
        repo = thp.guard_repo(tmp_path / name, text + prose)
        rc, out = thp.run(thp.GUARD, repo, "snapshot", "TASK-001")
        assert rc == 0, (name, out)


def test_task088_a_plans_satisfies_line_is_read_as_on_the_checkpoint():
    """This repository's plan: each increment's own one `Satisfies:` line, its R-ids, as the checkpoint read them."""
    text = bridge_env.read_record_text(os.path.join(ROOT, "docs", "BUILD_PLAN.md"))
    body_text = bridge_env.plan_body(text)
    expect = set()
    for line in body_text.splitlines():
        m = re.match(r"^Satisfies:\s*(.*)$", line)
        if m:
            expect.update(re.findall(r"\bR-\d{3,}\b", m.group(1)))
    assert bridge_env.plan_collect_satisfies_ids(body_text) == expect


# ---------------------------------------------------------------- round 2: text quoted from a brief, and a field as a bullet

CONTROL_LINE = "Satisfies: none \x1b]52;c;SGVsbG8=\x07 \x1b[2K\x08\x08 R-105\n"


def _no_control(line):
    return not any(ord(c) < 0x20 or ord(c) == 0x7f for c in line)


def test_task088_r2_a_control_byte_in_a_none_line_is_escaped_at_the_launcher(tmp_path):
    """The security audit, round 1 (blocking, security): ESC, BEL and backspace from the brief reached the refusal raw."""
    line = t32.assert_refused(launch(tmp_path, header([]) + body(CONTROL_LINE)), "bridge-run: refused - ")
    assert NONE_REMEDY in line, repr(line)
    assert _no_control(line) and all(ord(c) < 128 for c in line), repr(line)


def test_task088_r2_a_control_byte_in_a_none_line_is_escaped_by_plan_check(tmp_path):
    r = tpc.make(tmp_path)
    sat = "Satisfies: none \x1b[2K\x07 (R-003, R-004)\n"
    (r / "handoff" / "TASK-003.md").write_text(_plan_brief([], sat), encoding="utf-8")
    rc, out = tpc.run(r)
    lines = [l for l in _brief_lines(out) if "Satisfies: none" in l]
    assert rc == 1 and lines, repr(out)
    assert all(_no_control(l) and all(ord(c) < 128 for c in l) for l in lines), repr(lines)


def test_task088_r2_plan_checks_disagreement_line_prints_the_lists_in_ascii(tmp_path):
    """The security audit, round 1 (advisory): the header's list was printed by repr, printable non-ASCII kept."""
    r = tpc.make(tmp_path)
    (r / "handoff" / "TASK-003.md").write_text(_plan_brief(["R-003é"], "Satisfies: R-003, R-004\n"),
                                               encoding="utf-8")
    rc, out = tpc.run(r)
    lines = [l for l in _brief_lines(out) if "satisfies" in l.lower()]
    assert rc == 1 and lines, repr(out)
    assert all(all(ord(c) < 128 for c in l) for l in lines), repr(lines)


@pytest.mark.parametrize("lines,ids,flag", [
    ("- Satisfies: R-077\n- Depends on: TASK-003 (R-080)\n", ["R-077"], False),
    ("- Satisfies: none\n- Depends on: TASK-003 (R-080)\n", [], False),
], ids=["ids-then-a-field-bullet", "none-then-a-field-bullet"])
def test_task088_r2_a_field_written_as_a_bullet_ends_the_bullets(lines, ids, flag):
    """The security audit, round 1 (advisory): a bullet that is another field of the brief is no row of its Satisfies."""
    got = reader()(body(lines))
    assert list(got[0]) == ids and got[1] is flag, got


@pytest.mark.parametrize("lines", [
    "Satisfies: none.\n- R-105\n",
    "Satisfies: none, R-105\n",
    "Satisfies: none; R-105\n",
    "Satisfies: none(R-105)\n",
    "Satisfies: **none** (R-105)\n",
    "Satisfies: NONE R-1234\n",
], ids=["full-stop-then-a-bullet", "comma", "semicolon", "parenthesis", "bold", "upper-case"])
def test_task088_r2_none_is_matched_as_a_word(lines):
    """Review A, round 1 (blocking, behaviour): `Satisfies: none.` (handoff/BUG-038.md's form) with an id was read as rows."""
    got = reader()(body(lines))
    assert got[1] is True, got


@pytest.mark.parametrize("lines", ["Satisfies: nonetheless R-105\n", "Satisfies: R-105 none\n"],
                         ids=["a-longer-word", "none-not-first"])
def test_task088_r2_none_inside_another_word_or_later_is_no_none(lines):
    got = reader()(body(lines))
    assert got[1] is False and list(got[0]) == ["R-105"], got


def test_task088_r2_the_ids_beside_a_none_are_returned():
    """Requirement 1 as written: `ids` are the R-ids on the line and the bullets, a none or not (the supervisor's ruling on
    Review A's round-1 should-fix); a header-less brief keeps the checkpoint's reading."""
    got = reader()(body("Satisfies: none (R-105 is TASK-084's)\n- R-106\n"))
    assert list(got[0]) == ["R-105", "R-106"] and got[1] is True, got
    assert list(bridge_env.brief_satisfies(body("Satisfies: none (R-105 is TASK-084's)\n"))) == ["R-105"]


def test_task088_r2_one_locator_finds_the_line_for_the_reader_and_the_refusal(monkeypatch):
    """Review A, round 1 (blocking): a second loop found the line for the refusal's text. `brief_satisfies_line(body)`
    returns None or `(index, line, value)`; the reader and the refusal both take the line from it."""
    loc = getattr(bridge_env, "brief_satisfies_line", None)
    assert loc is not None, "bridge_env.brief_satisfies_line is missing (TASK-088, round 2)"
    assert loc(body("Satisfies: R-077\n"))[1:] == ("Satisfies: R-077", "R-077")
    assert loc("# no line\n") is None
    monkeypatch.setattr(bridge_env, "brief_satisfies_line", lambda b: (0, "Satisfies: none R-777", "none R-777"))
    assert reader()("") == (["R-777"], True)
    line = bridge_env.brief_header_refusal(header([]) + body("Satisfies: R-001\n"), "handoff/TASK-001.md")
    assert line is not None and "R-777" in line, line


def test_task088_r2_a_wrong_id_is_told_before_a_none_that_carries_ids(tmp_path):
    """Review A, round 1 (should-fix): the none refusal stands where satisfies stands in the order of the keys."""
    text = header([]).replace("id: TASK-001", "id: TASK-002") + body("Satisfies: none (R-105 is TASK-084's)\n")
    line = t32.assert_refused(launch(tmp_path, text), "bridge-run: refused - ")
    assert line.startswith("bridge-run: refused - header: disagrees id"), line
