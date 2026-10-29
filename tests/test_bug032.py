"""BUG-032: stage B5's review, round 2 (docs/HARDENING.md, "Stage B5's review, round 2"): the reproduction tests the
supervisor wrote before the fix brief, each failing on main at BUG-031's squash (41ead62) and naming the finding it
reproduces."""
import json

from test_mutation_run_supervisor import CALC, _fixture, _git, _mutants, _run, _write
from test_task032_supervisor_launcher import (Lab, _guard_ready, assert_ran, assert_refused, build, guard_snapshot,
                                              launch, write_brief)

SLOT_NOT_FREE = {"kind": "builder", "head": "cursor-agent", "model": "composer-2.5", "seconds": 0, "exit": 123,
                 "waited": 1500, "slot": "not free"}


def _rows(folder, rows):
    path = folder / "run" / "launcher" / "runs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_bug032_a_conftest_importing_what_the_increment_adds_lists_its_tests_not_run(tmp_path):
    """Stage B5's review, round 2, tests-mutation-pace Blocking: BUG-030 copies the working tree's conftest.py files
    on the way to each new test into the checkpoint copy; one that imports a module the increment adds cannot load
    on the checkpoint's code, so pytest ends at startup (exit 4) and the resolution check refused the whole run
    (exit 2, `resolution check failed`), where before BUG-030 the run went on. A conftest that imports the code
    under test is ordinary; the tests it guards cannot be run against the checkpoint, so they are listed `not run`
    with the reason, as a collection error is, and the run is not refused.
    enforces: R-041 (the new tests run once against the checkpoint's code); handoff/TASK-031.md Requirement 8
    (every listed test reported passing, failing or `not run`); docs/INVENTORY.md, Decisions, the by-class line
    (a refusal of ordinary work on an ordinary layout is a false result and blocks)"""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "demo/newmod.py", "def triple(x):\n    return 3 * x\n")
    _write(ws, "tests/conftest.py", "import pytest\n\nfrom demo.newmod import triple\n\n\n@pytest.fixture\n"
           "def six():\n    return triple(2)\n")
    _write(ws, "tests/test_six.py", "def test_six(six):\n    assert six == 6\n")
    _git(ws, "add", "-A")
    mf = _mutants(ws, "ckimp", {"mutants": [], "new_tests": ["tests/test_six.py"]})
    p = _run(ws, mf, "--checkpoint", sha)
    out = p.stdout + p.stderr
    assert "resolution check failed" not in out, out
    assert p.returncode != 2, out
    assert "tests/test_six.py" in p.stdout and "not run" in p.stdout, out


def test_bug032_a_launch_that_never_got_the_slot_opens_no_builder_window(program, tmp_path, monkeypatch):
    """Stage B5's review, round 2 (tests-guard C2, tests-launcher C5, launcher C1; convergent): a builder launch that
    waited for the heavy slot and gave up (exit 123, `"slot": "not free"`) started no builder, as BUG-030 made
    roster-check's built_by and the launcher's class line read it; scope-check's builder windows read it as a run of
    `waited` + 120 seconds, so a `supervisor:` test commit made while no builder ran was reported as drift. Such a
    row opens no window; a row of a run that started still does (the precondition).
    enforces: R-040 (a launch refused the slot runs nothing); hotfix 2026.10.25a C6 (the `supervisor:` test commits);
    handoff/BUG-030.md (a `slot: not free` row is no builder run)"""
    sc = program("scope-check")
    ws = _fixture(tmp_path, CALC)
    monkeypatch.chdir(ws)
    started = dict(SLOT_NOT_FREE, id="2026-01-01T00:00:00Z", exit=0, seconds=600)
    started.pop("slot")
    _rows(ws, [started])
    assert len(sc.builder_windows()) == 1, "the precondition: a run that started opens its window"
    _rows(ws, [dict(SLOT_NOT_FREE, id="2026-01-01T00:00:00Z")])
    assert sc.builder_windows() == [], sc.builder_windows()


def test_bug032_the_pace_report_reads_a_launch_refused_the_slot_as_no_launch(program, tmp_path):
    """Stage B5's review, round 2 (tests-launcher C5, launcher C3, briefs-ceiling C2; convergent): BUG-030 ruled that a
    launch that never got the slot spends no class line and is no builder run; the pace report still took such a
    row's `lift` as its round's lift and its time as the increment's start. A round whose only launch with the class
    line never got the slot, relaunched without it, reads `none`; the start is the first launch that started.
    enforces: R-044 (the pace report's started cell and lift column); handoff/BUG-030.md (a `slot: not free` row
    spends no class line); docs/INVENTORY.md, Decisions, TASK-033's settled points (an increment's start is its first
    builder launch)"""
    pr = program("pace-report")
    ws = tmp_path / "ws"
    common = tmp_path / "common"
    common.mkdir()
    refused = dict(SLOT_NOT_FREE, id="2026-01-01T00:00:00Z", brief="TASK-007", round=1, lift="class",
                   brief_name="TASK-007")
    ran = dict(SLOT_NOT_FREE, id="2026-01-02T00:00:00Z", brief="TASK-007", round=1, lift=None, brief_name="TASK-007",
               exit=0, seconds=600, waited=0)
    ran.pop("slot")
    _rows(ws, [ran])
    alone = pr._start_times(str(ws), str(common), "TASK-007")
    assert alone is not None and pr._lift_map(str(ws), str(common), "TASK-007") == {1: "none"}, "the precondition"
    _rows(ws, [refused, ran])
    assert pr._lift_map(str(ws), str(common), "TASK-007") == {1: "none"}
    assert pr._start_times(str(ws), str(common), "TASK-007") == alone


def test_bug032_a_refactoring_branch_takes_every_candidates_brief(tmp_path):
    """Stage B5's review, round 2, modules Blocking: the stage-close refactoring pass cuts one branch
    `refactor/<stage>` and delegates one brief `handoff/REFAC-<nnn>.md` per candidate (refactoring-pass.md step 4;
    step 6's pull-request title names them all); the launcher's branch rule (TASK-032) counted the IDs of the
    branch's first brief, so the second candidate's brief was refused on its own branch, and a `Merge unit:` line
    admits only the plan's increment IDs. On a `refactor/` branch every REFAC brief is of the branch's set; a brief
    under any other ID is refused there as before, and on another branch the rule is unchanged (the preconditions).
    enforces: bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md steps 4 and 6; R-042 (the
    branch rule refuses a brief under an ID outside the branch's set)"""
    lab = Lab(tmp_path, branch="refactor/B5")
    for name in ("REFAC-003", "REFAC-004", "TASK-005"):
        write_brief(lab.root, name)
    assert_ran(launch(lab, build("REFAC-003")))
    assert_ran(launch(lab, build("REFAC-004")))
    assert "REFAC-00" in assert_refused(launch(lab, build("TASK-005")))
    other = Lab(tmp_path / "other", branch="task-003")
    for name in ("REFAC-003", "REFAC-004"):
        write_brief(other.root, name)
    assert_ran(launch(other, build("REFAC-003")))
    assert "REFAC-003" in assert_refused(launch(other, build("REFAC-004")))


def test_bug032_the_refactoring_pass_snapshot_is_taken_on_its_branch(tmp_path):
    """Stage B5's review, round 2, modules Blocking, the guard's half: the pass's one gate pass takes one snapshot of
    the whole branch, named by the stage (`REFAC-<stage>`, as refactoring-pass.md step 6 names it), on a branch whose
    builder launches were REFAC briefs; the guard's branch rule, the launcher's, refused it as an ID outside the
    branch's set. A snapshot of a TASK ID there is still refused (the precondition).
    enforces: bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md step 6; R-042 (the guard
    refuses a snapshot under an ID outside the branch's set)"""
    lab = Lab(tmp_path, branch="refactor/B5")
    for name in ("REFAC-003", "REFAC-004"):
        write_brief(lab.root, name)
        assert_ran(launch(lab, build(name)))
    _guard_ready(lab)
    rc, out = guard_snapshot(lab.root, "TASK-005")
    assert rc != 0 and "branch rule" in out, out
    rc, out = guard_snapshot(lab.root, "REFAC-B5")
    assert rc == 0, out


# Round 2 (handoff/BUG-032-r2.md): the blocking findings of Review A and the security audit on round 1's change.

NEWMOD = "def triple(x):\n    return 3 * x\n"
IMPORTING_CONFTEST = ("import pytest\n\nfrom demo.newmod import triple\n\n\n@pytest.fixture\n"
                      "def six():\n    return triple(2)\n")
USES_SIX = "def test_six(six):\n    assert six == 6\n"
PASSES_ON_OLD = "from demo.calc import add\n\n\ndef test_old():\n    assert add(1, 2) == 3\n"


def test_bug032_r2_two_failing_conftests_block_their_tests_and_the_rest_are_judged(tmp_path):
    """BUG-032 round 2 (Review A Blocking 1 = security Blocking; convergent): pytest stops at the first conftest.py
    that fails to load, so one run reports one; round 1 excused the first, then threw away the second check's
    answer, so the tests behind the second conftest printed a bare `not run` (a whole-file item nothing) and the
    tests behind neither were run with no resolution check. Each copied conftest that fails to load is found and
    named on the `not run` line of every listed test behind it, whole-file items included, and a test behind
    neither is judged as today: one passing on the old code gives exit 4.
    enforces: handoff/BUG-032.md Requirement 1 ("a whole-file item behind such a conftest prints its `not run` line
    too"; "the other listed new tests are judged as today, the resolution check's refusals included"); R-041"""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "demo/newmod.py", NEWMOD)
    for sub in ("a", "b"):
        _write(ws, "tests/%s/conftest.py" % sub, IMPORTING_CONFTEST)
        _write(ws, "tests/%s/test_%s.py" % (sub, sub), USES_SIX)
    _write(ws, "tests/c/test_c.py", PASSES_ON_OLD)
    _git(ws, "add", "-A")
    mf = _mutants(ws, "cktwo", {"mutants": [], "new_tests": ["tests/a/test_a.py", "tests/b/test_b.py",
                                                            "tests/c/test_c.py"]})
    p = _run(ws, mf, "--checkpoint", sha)
    out = p.stdout + p.stderr
    lines = p.stdout.splitlines()
    for sub in ("a", "b"):
        assert any(l.startswith("tests/%s/test_%s.py: not run" % (sub, sub)) and "tests/%s/conftest.py" % sub in l
                   for l in lines), out
    assert "tests/c/test_c.py::test_old: passing on old code" in p.stdout, out
    assert p.returncode == 4, out


def test_bug032_r2_a_conftest_unchanged_since_the_checkpoint_still_refuses(tmp_path):
    """BUG-032 round 2 (Review A Should fix = security advisory; convergent): BUG-030's copy records every working-tree
    conftest.py on the way, one byte-identical to the checkpoint's included, so round 1 excused a conftest the
    increment did not change, whose failure to load is the checkpoint's own (here it imports a module the
    checkpoint lacks), and printed `not run` with exit 0. Only a copied conftest absent at the commit or differing
    from its blob there is excused; an unchanged one that fails to load refuses the run as before BUG-032.
    enforces: handoff/BUG-032.md Requirement 1 ("a conftest that came from the checkpoint's own archive and fails to
    load still refuses as today")"""
    files = dict(CALC)
    files["tests/conftest.py"] = IMPORTING_CONFTEST
    ws = _fixture(tmp_path, files)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "demo/newmod.py", NEWMOD)
    _write(ws, "tests/test_six.py", USES_SIX)
    _git(ws, "add", "-A")
    mf = _mutants(ws, "cksame", {"mutants": [], "new_tests": ["tests/test_six.py"]})
    p = _run(ws, mf, "--checkpoint", sha)
    out = p.stdout + p.stderr
    assert p.returncode == 2 and "resolution check failed" in out, out


def test_bug032_r2_a_conftest_that_writes_the_load_failure_line_names_itself(tmp_path):
    """BUG-032 round 2 (the security audit, Blocking route and advisory): the excuse took the first `ImportError while
    loading conftest '<path>'` anywhere in stdout and stderr, so a conftest.py the increment adds can write that
    line naming another conftest before it fails to load (pytest passes what a conftest writes at startup through,
    ahead of its own line; seen with pytest 8 on 2026-10-29), and the tests behind the named one, which load and
    would be judged, are listed `not run` instead. pytest's own line is the last line of its standard error that
    is exactly that text (the traceback after it is indented or prefixed); the conftest it names is the one that
    failed. Here the failing conftest's test is `not run` and the other's, passing on the old code, gives exit 4.
    enforces: handoff/BUG-032.md Requirement 1 ("the other listed new tests are judged as today"); the brief's
    Context, the working tree as untrusted input"""
    ws = _fixture(tmp_path, CALC)
    sha = _git(ws, "rev-parse", "HEAD")
    _write(ws, "tests/a/conftest.py", "import pytest\n\n\n@pytest.fixture\ndef one():\n    return 1\n")
    _write(ws, "tests/a/test_a.py", PASSES_ON_OLD)
    _write(ws, "tests/b/conftest.py",
           "import os\nimport sys\n\nsys.stderr.write(\"ImportError while loading conftest '%s'.\\n\" % os.path.join("
           "os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'a', 'conftest.py'))\n"
           "raise ImportError('no such thing')\n")
    _write(ws, "tests/b/test_b.py", USES_SIX)
    _git(ws, "add", "-A")
    mf = _mutants(ws, "ckspoof", {"mutants": [], "new_tests": ["tests/a/test_a.py", "tests/b/test_b.py"]})
    p = _run(ws, mf, "--checkpoint", sha)
    out = p.stdout + p.stderr
    lines = p.stdout.splitlines()
    assert any(l.startswith("tests/b/test_b.py: not run") and "tests/b/conftest.py" in l for l in lines), out
    assert "tests/a/test_a.py::test_old: passing on old code" in p.stdout, out
    assert p.returncode == 4, out


def test_bug032_r2_a_refactoring_branch_admits_numbered_briefs_and_its_own_snapshot_only(tmp_path):
    """BUG-032 round 2 (the security audit's advisory = Review A's design note; convergent): round 1 admitted any REFAC
    ID on a `refactor/` branch whose IDs are all REFAC, so the pass's one snapshot could be taken again under any
    other REFAC name with fresh guard rounds, escaping the ceiling the guard holds per ID. Beyond the branch's
    declared IDs, a `refactor/<stage>` branch admits a candidate's brief `REFAC-<digits>` and one snapshot name,
    `REFAC-<stage>`; another REFAC name is refused there.
    enforces: R-042 (the guard's ceiling per ID; the branch rule refusing an ID outside the branch's set);
    bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md steps 4 and 6"""
    lab = Lab(tmp_path, branch="refactor/B5")
    for name in ("REFAC-003", "REFAC-B5x"):
        write_brief(lab.root, name)
    assert_ran(launch(lab, build("REFAC-003")))
    assert "REFAC-003" in assert_refused(launch(lab, build("REFAC-B5x")))
    _guard_ready(lab)
    rc, out = guard_snapshot(lab.root, "REFAC-B6")
    assert rc != 0 and "branch rule" in out, out
    rc, out = guard_snapshot(lab.root, "REFAC-B5")
    assert rc == 0, out
