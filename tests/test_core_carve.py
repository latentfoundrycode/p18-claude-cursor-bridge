"""TASK-010: the core and its phase modules (R-003, R-032).

enforces: docs/REQUIREMENTS.md R-003 (the core holds the roles and division of labour, the founding rules, the loop's
shape, escalation and reporting, project state and the standing rules; each phase's procedure is a module) and R-032
(each module is read whole: within 1,500 lines and 60,000 characters); docs/BUILD_PLAN.md TASK-010's Done when (the
core's section set, no phase procedure left in it, the modules exist, workflow/** installs from the regenerated
manifest)."""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
REGISTRY = os.path.join(BRIDGE, "cursor-bridge", "workflow", "extension-points.md")
INSTALL = os.path.join(BRIDGE, "cursor-bridge", "bridge-install.py")

# each module and the heading it opens with: the phase's own heading from the core, kept (project end has its own,
# and the interface module names the phase since TASK-012 made its mockups one of four variants)
MODULES = {
    "intake": "## Phase 1 — Intake",
    "design": "## Phase 2 — Design",
    "interface": "## Phase 3 — Interface",
    "planning": "## Phase 4 — Build plan",
    "run-parameters": "## Run parameters — asked once, after the plan is approved, before configuration",
    "configuration": "## Phase 5 — Configure the Cursor build environment",
    "delegation-loop": "## Phase 6 — The delegation loop",
    "change-cycle": "## The change cycle — a request on a finished project",
    "reflection": "## Reflection points — stage close, phase gates, project end",
    "project-end": "## Project end",
}
CORE_SECTIONS = [
    "The core, in brief", "Founding rules", "The division of labour", "Main and conditional workflows",
    "The project layout", "The phase modules", "Objections — bottom-up escalation", "Escalate to the user when",
    "Reporting to the user", "Project state", "Standing rules",
]


def read(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


def headings(text, level):
    """The headings of one level outside fenced blocks, in order."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
            continue
        if fence is None:
            h = re.match(r"^ {0,3}(#{1,6}) (.*)$", line)
            if h and len(h.group(1)) == level:
                out.append(h.group(2).strip())
    return out


def test_r003_the_core_holds_exactly_its_sections():
    assert headings(read(CORE), 2) == CORE_SECTIONS


def test_r003_no_phase_procedure_remains_in_the_core():
    core = read(CORE)
    for heading in MODULES.values():
        assert heading not in core.split("\n"), heading
    for step in ("### 1. Checkpoint", "### 8. Merge (the verified gate)", "### Step 0 — Prior-project lessons (ask before drafting)",
                 "### The design-tooling flow", "### Issues — what counts, and where it is written"):
        assert step not in core.split("\n"), step
    assert "**Project end is a defined trigger, not a judgement.**" not in core
    assert "**At project end**, additionally:" not in core


def test_r003_the_modules_are_the_registrys_and_each_opens_with_its_heading():
    registry = read(REGISTRY)
    table = registry.split("\n## Phase modules\n", 1)[1].split("\n## ", 1)[0]
    keys = [row.split("|")[1].strip() for row in table.split("\n") if row.startswith("| ") and not row.startswith("| Module")]
    assert keys == list(MODULES), keys
    assert sorted(f for f in os.listdir(PHASES) if f.endswith(".md")) == sorted(k + ".md" for k in MODULES)
    for key, heading in MODULES.items():
        assert read(os.path.join(PHASES, key + ".md")).split("\n", 1)[0] == heading, key


def test_r003_the_core_names_every_module():
    core = read(CORE)
    section = core.split("\n## The phase modules\n", 1)[1].split("\n## ", 1)[0]
    for key in MODULES:
        assert "`~/.claude/cursor-bridge/workflow/phases/%s.md`" % key in section, key


def test_r003_project_end_is_carved_out_of_the_reflection_points():
    reflection = read(os.path.join(PHASES, "reflection.md"))
    project_end = read(os.path.join(PHASES, "project-end.md"))
    assert "**Project end is a defined trigger, not a judgement.**" in project_end
    assert "**At project end**, additionally:" in project_end and "- **Run the promotion pass.**" in project_end
    assert "**Project end is a defined trigger" not in reflection and "**At project end**" not in reflection
    assert "`~/.claude/cursor-bridge/workflow/phases/project-end.md`" in reflection
    assert "### Issues — what counts, and where it is written" in reflection.split("\n")


def test_r003_a_module_read_outside_its_own_phase_is_named_with_when():
    """PR #52's gate (Review A, the carve's part, blocking): before the carve every procedure was in the one file read
    whole; after it a reader reads the current phase's modules and "never a phase you are not in". The procedures that
    run outside their own Phase: value (reflection points at every phase gate, an issue in any phase, project end, the
    change cycle's scaled Phases 1 to 4) are named in the core with when they are read."""
    core = read(CORE)
    section = core.split("\n## The phase modules\n", 1)[1].split("\n## ", 1)[0]
    rule = section.split("**Modules read outside their own phase.**", 1)[1]
    assert "`reflection.md` is read whole at every reflection point: a stage close, each approved phase gate, and project end;" in rule
    assert "its section \"Issues — what counts, and where it is written\" is read whenever an issue is detected, in any phase;" in rule
    assert "`project-end.md` is read whole at the close of the plan's last stage;" in rule
    assert ("reads that phase's module whole for that step: the change cycle runs Phases 1 to 4, scaled; the design "
            "critique's failed launch follows the delegation loop's step 3b, and its review launch follows step 8.") in rule
    assert ("You never read a phase you are not in or a conditional workflow that does not apply, except a module "
            "\"The phase modules\" says is read outside its own phase.") in core
    layering = core.split("\n## Main and conditional workflows\n", 1)[1].split("\n## ", 1)[0]
    assert ("on entering the phase and at every calibration; a module read outside its own phase when \"The phase "
            "modules\" says |") in layering


# the traceability check's result on this tree, every excuse it uses named (PR #52's gate, Review A, the carve's part:
# a reword entry excuses a whole section, so a later drop there would show only as a NOTE with RESULT: OK)
# (TASK-012: three passages move from traced to excused: the design gate's sentence, "the UI mockups" -> "the
# interface phase"; the mockup paragraph's "Saving these concludes the planning stage", now the mockups and the phase;
# rule 13's pointer to the approved-mockup rule, excused by the earlier Standing rules entry and so labelled TASK-015;
# the other mockup passages traced in their new home, workflow/phases/interface/mockups.md)
TRACED = "TRACED: 424 passages of baseline 0a186da; 156 in supervisor.md, 261 under workflow/, 0 dropped, 7 excused"
NOTES = [
    "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - | Layer | Holds | Read when | |---|---|---| | **The main wor",
    "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - Until the phases are moved into files of their own, each pha",
    "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - **The order additions apply in.** Additions from several con",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - **Gate:** present the design to the user. Do not proceed to ",
    "NOTE (reword TASK-012) bridge/commands/supervisor.md: The design-tooling flow - Save the mockup files under `docs/mockups/` (one file per sc",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 13. Design correctness \\u2014 accessibility and interface MUSTs, ",
    "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 28. The installed bridge is the governing text, and its vers",
]


def test_r003_the_carve_traces_with_exactly_its_excuses():
    """The traceability check (R-029) on the repository: every passage of the baseline traced, none dropped, and the
    excused ones exactly the seven passages of the five rewords the carve and TASK-012 declare, so an increment that excuses anything more changes this
    test. It needs the baseline commit, which CI's depth-1 checkout lacks (INVENTORY Decisions): skipped there, run in
    the supervisor's checkout."""
    repo = os.path.abspath(os.path.join(HERE, os.pardir))
    have = subprocess.run(["git", "cat-file", "-e", "0a186da^{commit}"], cwd=repo, capture_output=True)
    if have.returncode != 0:
        import pytest
        pytest.skip("the baseline commit is not in this clone (a shallow checkout)")
    p = subprocess.run([sys.executable, os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")], cwd=repo,
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
    lines = p.stdout.strip().split("\n")
    assert lines == NOTES + [TRACED, "RESULT: OK"], p.stdout


def test_r032_each_module_is_read_whole():
    for key in MODULES:
        text = read(os.path.join(PHASES, key + ".md"))
        assert text.count("\n") <= 1500 and len(text) <= 60000, (key, text.count("\n"), len(text))


def test_r003_the_modules_install_from_the_manifest(tmp_path):
    """The proof that workflow/** installs with no change to bridge-install.py: the regenerated manifest lists every
    module, and an install into an empty target writes each one as it is in the source."""
    manifest = json.load(open(os.path.join(BRIDGE, "cursor-bridge", "MANIFEST.json"), encoding="utf-8"))
    listed = json.dumps(manifest)
    for key in MODULES:
        assert "cursor-bridge/workflow/phases/%s.md" % key in listed, key
    target = tmp_path / ".claude"
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    p = subprocess.run([sys.executable, INSTALL, "--target", str(target), "--anyway"], capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    for key in MODULES:
        installed = target / "cursor-bridge" / "workflow" / "phases" / (key + ".md")
        assert installed.is_file(), key
        assert read(str(installed)) == read(os.path.join(PHASES, key + ".md")), key
