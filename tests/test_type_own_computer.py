"""TASK-020: the type workflow software on your own computer and its sub-workflow local service (R-024), new text
throughout.

enforces: docs/BUILD_PLAN.md TASK-020 (its Done when: the type names its GUI, CLI, pipeline and local-service sub-types;
local service adds the contract design interface variant and, where the part also has administrative commands (the
TDP), the command design variant too, variants added per interface kind, not set as one value; every section new text
under a `new` entry; both rows written; `workflow-check.py` passing and classifying the TDP, performance budgets held
per §6.3 until its code map carries one, without pausing); bridge/cursor-bridge/workflow/open-list.md, "Default traits"
(the open list is the one source of a type's and a sub-type's default traits); extension-points.md, `interface.variants`
(add only, per part); phases/interface.md, "The variants" (every variant is an addition). Supervisor-written; no builder
run."""
import importlib.util
import os
import re
import subprocess
import sys

import pytest

from phase_modules import BRIDGE, read, section

REPO = os.path.dirname(BRIDGE)

WORKFLOW = os.path.join(BRIDGE, "cursor-bridge", "workflow")
TYPES = os.path.join(WORKFLOW, "types")
TRAITS = os.path.join(WORKFLOW, "traits")
PHASES = os.path.join(WORKFLOW, "phases")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
EXCEPTIONS = os.path.join(WORKFLOW, "trace-exceptions.md")
OPEN_LIST = os.path.join(WORKFLOW, "open-list.md")
REGISTRY = os.path.join(WORKFLOW, "extension-points.md")
TRACE_CHECK = os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")
WORKFLOW_CHECK = os.path.join(BRIDGE, "cursor-bridge", "workflow-check.py")
FIXTURES = os.path.join(REPO, "tests", "fixtures", "workflows")

# Each file's path under workflow/types/, its title and its change headings, in its order (BUILD_PLAN TASK-020).
FILES = {
    "own-computer": ("own-computer.md", "Software on your own computer", ["Add at intake.questions"]),
    "local-service": ("own-computer/local-service.md", "Local service", ["Add at interface.variants"]),
}
SUB_TYPES = {"gui": "GUI", "cli": "CLI", "pipeline": "pipeline", "local-service": "local service"}


def text(key):
    return read(os.path.join(TYPES, FILES[key][0]))


def flat(t):
    return re.sub(r"\s+", " ", t).strip()


def body(key, heading):
    return section(text(key), heading, 2)


def trace_units(t):
    spec = importlib.util.spec_from_file_location("trace_check_type_own_computer", TRACE_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [u["normal"] for u in mod.parse_units(t)[0]]


def rows(table_heading):
    """The open list's rows in the table under `table_heading`, each a dict of its columns, keyed by the first."""
    lines = section(read(OPEN_LIST), table_heading, 2).split("\n")
    table = [l for l in lines if l.startswith("|")]
    header = [c.strip() for c in table[0].strip("|").split("|")]
    out = {}
    for l in table[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        out[cells[0]] = dict(zip(header, cells))
    return out


def traits_of(cell):
    return set(t.strip() for t in cell.split(","))


def run_check(*args):
    return subprocess.run([sys.executable, WORKFLOW_CHECK] + list(args), capture_output=True, text=True,
                          encoding="utf-8")


@pytest.mark.parametrize("key", sorted(FILES))
def test_r024_each_file_is_a_title_and_its_change_sections_only(key):
    """BUILD_PLAN TASK-020: one `#` title, then the change headings named above, in that order, and nothing else, so
    each file changes the main workflow at those points and no other: the type adds at intake, the sub-workflow adds
    at `interface.variants`, and neither sets a value or replaces a module."""
    lines = text(key).split("\n")
    heads = [l for l in lines if re.match(r"^ {0,3}#", l)]
    assert heads == ["# " + FILES[key][1]] + ["## " + h for h in FILES[key][2]], heads
    assert lines[0] == "# " + FILES[key][1], lines[0]


def test_r024_the_type_names_its_four_sub_types_by_what_the_user_meets():
    """BUILD_PLAN TASK-020: the type names its GUI, CLI, pipeline and local-service sub-types, each by the surface its
    open-list definition turns on (a window, a terminal, nothing, other software through a protocol); every sub-type
    the open list gives the type is named and none other; a part met through several takes the sub-type of the surface
    it exists for, and one that exists for two equally pauses as intake's classification says (phases/intake.md)."""
    t = flat(body("own-computer", "Add at intake.questions"))
    subs = {k: r for k, r in rows("Sub-types").items() if r["Of type"] == "own-computer"}
    assert sorted(subs) == sorted(SUB_TYPES), sorted(subs)
    assert "has four sub-types, told apart by what its user meets it through" in t
    for phrase in ["a window (GUI)", "a terminal (CLI)",
                   "nothing, the part running jobs unattended with files or records as its output (pipeline)",
                   "other software on the same computer calling it through a protocol (local service)"]:
        assert phrase in t, phrase
    for key, definition in [("gui", "Met through a window"), ("cli", "Met through a terminal"),
                            ("pipeline", "Met through nothing: it runs jobs unattended and its output is files or records"),
                            ("local-service", "Other software on the same computer calls it through a protocol")]:
        assert subs[key]["Definition"].startswith(definition), (key, subs[key]["Definition"])
    assert "Ask which, where the owner's description leaves it open." in t
    assert ("A part met through several, such as a local service with administrative commands, takes the sub-type of "
            "the surface it exists for, and the interface phase runs a variant for each of its other kinds of interface") in t
    assert "a part that exists for two equally fits two sub-types equally, which pauses the project as the classification at intake says" in t
    intake = flat(read(os.path.join(PHASES, "intake.md")))
    assert "fits two sub-types of its type equally" in intake and "the project stops before design" in intake


def test_r024_local_service_adds_the_contract_design_and_for_commands_the_command_design():
    """BUILD_PLAN TASK-020: local service adds the contract design variant and, where the part also has administrative
    commands (the TDP), the command design variant too, each added for its own kind of interface and never set as one
    value (extension-points.md: `interface.variants` accepts add only; interface.md: every variant is an addition);
    both variant files exist where the text points."""
    t = flat(body("local-service", "Add at interface.variants"))
    assert ("runs the interface phase's contract design variant for the protocol other software calls it through, "
            "`~/.claude/cursor-bridge/workflow/phases/interface/contract-design.md`: the variant this sub-workflow "
            "activates, an addition and never a replacement") in t
    assert ("Where the part also has administrative commands a person types, as the TDP has, it runs the command design "
            "variant for them too, `~/.claude/cursor-bridge/workflow/phases/interface/command-design.md`") in t
    assert "Each variant is added for its own kind of interface, so a part with both runs both, never one in place of the other." in t
    assert t.index("contract-design.md") < t.index("command-design.md")
    for name in ("contract-design.md", "command-design.md"):
        assert os.path.isfile(os.path.join(PHASES, "interface", name)), name
    line = [l for l in read(REGISTRY).split("\n") if l.startswith("| interface.variants |")]
    assert len(line) == 1 and line[0].rstrip().endswith("| interface | add | part |"), line
    assert "Every variant is an addition, never a replacement of another" in flat(read(os.path.join(PHASES, "interface.md")))


@pytest.mark.parametrize("key", sorted(FILES))
def test_r024_every_section_has_its_own_new_entry_and_no_other_entry_names_the_file(key):
    """BUILD_PLAN TASK-020: every section of the two files is new text under a `new` entry naming the file and that
    heading (the trace check counts the type files as modules); no `reword` entry, and none on the title."""
    rel = "bridge/cursor-bridge/workflow/types/" + FILES[key][0]
    got = []
    for line in read(EXCEPTIONS).split("\n"):
        m = re.match(r"^- (new|reword) (\S+) (\S+\.md) (.+)$", line)
        if m and m.group(3) == rel:
            got.append((m.group(1), m.group(2), m.group(4).strip()))
    assert got == [("new", "TASK-020", h) for h in FILES[key][2]], got


@pytest.mark.parametrize("key", sorted(FILES))
def test_r024_the_text_is_new_and_copies_no_passage_of_the_main_workflow(key):
    """BUILD_PLAN TASK-020: the files are new text throughout; no unit of one, as trace-check.py reads units, is a unit
    of the core, of a phase module, of the plan critic, of a trait file, of another type file or of the other file."""
    main = set(trace_units(read(CORE))) | set(trace_units(read(os.path.join(BRIDGE, "agents", "plan-critic.md"))))
    for root in (PHASES, TRAITS, TYPES):
        for here, _dirs, names in os.walk(root):
            for f in names:
                path = os.path.join(here, f)
                if f.endswith(".md") and os.path.normcase(path) != os.path.normcase(os.path.join(TYPES, FILES[key][0])):
                    main |= set(trace_units(read(path)))
    assert len(main) > 300, len(main)
    for unit in trace_units(text(key)):
        assert unit not in main, unit[:80]


def test_r024_both_rows_are_written_and_the_other_sub_types_are_not():
    """BUILD_PLAN TASK-020: the type's and local service's rows flip to written in the same change as their files;
    GUI, CLI and pipeline stay unwritten, so a part of one of them still pauses at intake (open-list.md, "When each is
    written": when the first project of that type arrives)."""
    types = rows("Product types")
    subs = rows("Sub-types")
    assert types["own-computer"]["Written"] == "yes" and subs["local-service"]["Written"] == "yes"
    for key in ("gui", "cli", "pipeline"):
        assert subs[key]["Written"] == "no", key
    assert types["own-computer"]["Workflow name"] == "Own-Computer Software Development"
    assert subs["local-service"]["Sub-workflow name"] == "Local Service Software"


def test_r024_the_default_traits_stay_in_the_open_list():
    """BUILD_PLAN TASK-020 and §6.3: the type's default trait is installable; local service's complete set adds
    long-running process. The open list is the one source of both sets, so neither type file states them (open-list.md,
    the opening paragraph and "Default traits"; INVENTORY, Decisions, TASK-019)."""
    assert traits_of(rows("Product types")["own-computer"]["Default traits"]) == {"installable"}
    assert traits_of(rows("Sub-types")["local-service"]["Default traits"]) == {"installable", "long-running-process"}
    for key in FILES:
        assert "Default traits" not in text(key) and "long-running" not in text(key).lower(), key


def test_r024_workflow_check_passes_over_the_workflow_folder():
    """BUILD_PLAN TASK-020: `workflow-check.py` passes over `workflow/` with the two files written."""
    r = run_check(WORKFLOW)
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr


def test_r024_the_tdp_is_classified_without_pausing():
    """BUILD_PLAN TASK-020: the committed fixture, shaped as the TDP's `Workflows:` line (§6.3's classification:
    software on your own computer → local service, with installable, external services, spends money, long-running
    process and AI models in the open list's order; performance budgets held until its code map carries one), passes
    `workflow-check.py --status` with no FAIL (a part whose type or sub-type is not written pauses) and no FLAG (every
    trait named is written)."""
    path = os.path.join(FIXTURES, "tdp.status.md")
    lines = read(path).replace("\r\n", "\n").split("\n")
    wf = [l for l in lines if l.startswith("Workflows: ")]
    assert wf == ["Workflows: Own-Computer Software Development → Local Service Software; traits: Installable, "
                  "External services, Spends money, Long-running process, AI models"], wf
    assert "Performance budgets" not in wf[0]
    r = run_check("--status", path)
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr
