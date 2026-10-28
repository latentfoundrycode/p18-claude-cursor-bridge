"""BUG-030: stage B5's review, round 1 — the supervisor's reproduction tests of two findings taken there that have no
test file of their own: a report file named `<ID>-report.md` read as a brief (Review B, S1), and the review guard's
input list taking another ID's files (the tests-guard part, S2). The other findings' reproductions stand beside the
tests of the program they concern (scope-check, roster-check, bridge-run, mutation-run)."""
import pytest


@pytest.mark.parametrize("name, brief", [("BUG-029-report.md", "BUG-029"), ("TASK-031-r8-report.md", "TASK-031-r8"),
                                         ("TASK-002-r2b-report.md", "TASK-002-r2")])
def test_bug030_a_report_file_is_never_a_brief_to_the_launcher(program, name, brief):
    """BUG-030 (Review B, S1): handoff/BUG-029-report.md, a report on main, is a report, not the brief
    `BUG-029-report`: a builder launch naming it beside its brief names one brief, and a launch naming it alone
    names none. The round report forms (`-r<N>-report.md`, `-r<N><letter>-report.md`) are reports too.
    enforces: docs/BUILD_PLAN.md TASK-032 clause (e) (every builder launch names exactly one brief
    `handoff/<ID>[-r<N>].md`); handoff/TASK-032.md (report names are not briefs)"""
    be = program("bridge_env")
    assert be.handoff_brief_tokens(["Read handoff/%s" % name]) == []
    assert be.handoff_brief_tokens(["Read handoff/%s.md and handoff/%s" % (brief, name)]) == [brief]


def test_bug030_the_pace_report_takes_no_report_file_for_an_increment(program):
    """BUG-030 (Review B, S1): the pace report's list of IDs with a tracked brief never holds a report's name read
    as an ID (`BUG-029-report`), so no increment with an unknown start is invented from it.
    enforces: R-044 (an increment is an ID with a tracked brief, handoff/TASK-033.md)"""
    pr = program("pace-report")
    listed = "handoff/BUG-029.md\nhandoff/BUG-029-report.md\nhandoff/TASK-031-r8-report.md\nhandoff/TASK-031-r8.md\n"
    assert pr._ids_with_brief(listed) == {"BUG-029", "TASK-031"}


def _inputs(program, tmp_path, nnn, names):
    folder = tmp_path / "run" / "review"
    folder.mkdir(parents=True)
    for n in names:
        (folder / n).write_bytes(b"x\n")
    return [n for n, _ in program("review-guard").review_inputs(str(tmp_path), nnn)]


def test_bug030_the_review_inputs_are_the_ids_own_files(program, tmp_path):
    """BUG-030 (the tests-guard part, S2): the review guard lists as a snapshot's inputs, and refuses empty, only
    the files named for that ID: the ID ends where the name ends, at a `.`, or at a `-` that does not start
    another round's `-r<N>`; so TASK-001's inputs never hold TASK-001b's, TASK-001-r2's or XTASK-001's files, while
    TASK-001-r2's hold its own and a stage's parts are its own.
    enforces: docs/BUILD_PLAN.md TASK-034 (a round's review inputs take its snapshot's name; the guard refuses an
    empty one, KP-067)"""
    names = ["REVIEW-TASK-001.diff", "ASSUMPTIONS-TASK-001.md", "SCOPE-TASK-001.md", "REVIEW-TASK-001b.diff",
             "REVIEW-TASK-001-r2.diff", "ASSUMPTIONS-TASK-001-r2.md", "REVIEW-XTASK-001.diff", "REVIEW-TASK-001.err",
             "STAGE-B5-r2.diff", "STAGE-B5-r2-core.diff", "STAGE-B5-core.diff", "STAGE-B55.diff"]
    got = _inputs(program, tmp_path, "TASK-001", names)
    assert got == ["ASSUMPTIONS-TASK-001.md", "REVIEW-TASK-001.diff", "SCOPE-TASK-001.md"], got
    got = [n for n, _ in program("review-guard").review_inputs(str(tmp_path), "TASK-001-r2")]
    assert got == ["ASSUMPTIONS-TASK-001-r2.md", "REVIEW-TASK-001-r2.diff"], got
    got = [n for n, _ in program("review-guard").review_inputs(str(tmp_path), "STAGE-B5-r2")]
    assert got == ["STAGE-B5-r2-core.diff", "STAGE-B5-r2.diff"], got
    got = [n for n, _ in program("review-guard").review_inputs(str(tmp_path), "STAGE-B5")]
    assert got == ["STAGE-B5-core.diff"], got
