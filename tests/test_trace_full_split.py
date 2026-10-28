"""TASK-025: the traceability check green over the finished split (R-029).

enforces: docs/REQUIREMENTS.md R-029 and docs/BUILD_PLAN.md TASK-025's Done when ("`test_trace_full_split.py` asserts
`trace-check` green over the finished split (nothing dropped across all modules and traits, no passage in two
homes)"). The finished split is the core, the phase modules with their sub-files and variants, the type workflows and
the trait files, as release B leaves them; trace-check.py's `--map` names each baseline passage's current home or homes
(`-` for one a `reword` entry excuses). The trait files that hold moved passages are TASK-017's four (BUILD_PLAN TASK-017:
the phase modules' conditional passages moved there); TASK-018's three traits and the type workflows are new text
throughout (TASK-018 to TASK-021). The check needs the baseline commit, which CI's depth-1 checkout lacks (INVENTORY,
Decisions): these tests are skipped there and run in the supervisor's checkout, as tests/test_core_carve.py's trace test
is. Supervisor-written; no builder run."""
import os
import re
import subprocess
import sys

import pytest

from phase_modules import BRIDGE, read, section
from test_core_carve import NOTES
from workflow_files import REGISTRY

REPO = os.path.dirname(BRIDGE)
TRACE = os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")
CORE = "bridge/commands/supervisor.md"
WF = "bridge/cursor-bridge/workflow/"
MOVED_TRAITS = {WF + "traits/%s.md" % t for t in ("has-screens", "installable", "performance-budgets",
                                                  "external-services")}
TRACED = re.compile(r"^TRACED: (\d+) passages of baseline ([0-9a-f]+); (\d+) in supervisor\.md, (\d+) under workflow/, "
                    r"(\d+) dropped, (\d+) excused$")


def baseline():
    return read(os.path.join(BRIDGE, "cursor-bridge", "workflow", "trace-baseline.txt")).strip().split()[0]


@pytest.fixture(scope="module")
def run():
    have = subprocess.run(["git", "cat-file", "-e", baseline() + "^{commit}"], cwd=REPO, capture_output=True)
    if have.returncode != 0:
        pytest.skip("the baseline commit is not in this clone (a shallow checkout)")
    p = subprocess.run([sys.executable, TRACE, "--map"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    lines = p.stdout.strip().split("\n")
    traced = [TRACED.match(l) for l in lines if l.startswith("TRACED: ")]
    assert len(traced) == 1 and traced[0], p.stdout
    maps = [re.match(r"^MAP (.+?): ", l).group(1) for l in lines if l.startswith("MAP ")]
    return p, lines, traced[0], maps


def test_r029_the_check_is_green_with_nothing_dropped(run):
    """trace-check exits 0 with RESULT: OK and no FAIL line of any kind (dropped, copy, new, ref, cite), over the
    baseline the repository pins, and reports 0 dropped."""
    p, lines, traced, _maps = run
    assert p.returncode == 0 and lines[-1] == "RESULT: OK", p.stdout + p.stderr
    assert not [l for l in lines if l.startswith("FAIL")], p.stdout
    assert baseline().startswith(traced.group(2)) and traced.group(5) == "0", traced.group(0)


def test_r029_every_passage_has_one_home_or_its_reword(run):
    """Each of the baseline's passages is mapped once, to exactly one current home or to `-`; the core's count, the
    workflow's count and the excused count add up to all passages, and each excused passage is a `reword` NOTE."""
    _p, lines, traced, maps = run
    passages, in_core, in_wf, excused = (int(traced.group(i)) for i in (1, 3, 4, 6))
    assert len(maps) == passages, (len(maps), passages)
    assert not [m for m in maps if ", " in m], "a passage in two homes"
    assert maps.count("-") == excused == len([l for l in lines if l.startswith("NOTE (reword ")])
    assert maps.count(CORE) == in_core and len([m for m in maps if m.startswith(WF)]) == in_wf
    assert in_core + in_wf + excused == passages


def test_r029_the_excused_passages_are_exactly_the_recorded_rewords(run):
    """A `reword` entry excuses every passage under its section, so a passage dropped there is reported excused, not
    dropped (the trace check's section-wide entries, docs/INVENTORY.md, Decisions); "nothing dropped" holds only
    because the excused passages are exactly the ones each increment recorded with its reword, the list
    tests/test_core_carve.py pins. A passage dropped under a reworded section adds a NOTE line and fails here."""
    lines = run[1]
    assert [l for l in lines if l.startswith("NOTE ")] == NOTES, "an excused passage that no increment recorded"


def test_r029_the_homes_are_the_core_the_modules_and_the_moved_traits(run):
    """Every home is the core, a phase module (its file, a sub-file or a variant), or one of the four trait files
    TASK-017 moved passages into; every module of the registry holds moved passages, and so does each of those four;
    no type workflow, no other trait and no table (the open list, the registry) is a home."""
    homes = {m for m in run[3] if m != "-"}
    modules = [l.split("|")[1].strip() for l in section(read(REGISTRY), "Phase modules", 2).split("\n")
               if l.startswith("| ") and not l.startswith("| Module") and not l.startswith("|---")]
    assert len(modules) == 10, modules

    def module_of(home):
        for m in modules:
            if home == WF + "phases/%s.md" % m or home.startswith(WF + "phases/%s/" % m):
                return m
        return None

    others = {h for h in homes if h != CORE and module_of(h) is None}
    assert others == MOVED_TRAITS, sorted(others ^ MOVED_TRAITS)
    assert {module_of(h) for h in homes} - {None} == set(modules), sorted(set(modules) - {module_of(h) for h in homes})
