"""TASK-023: calibration aware of conditional workflows (R-027), the text half; TASK-024 is the program half.

enforces: docs/BUILD_PLAN.md TASK-023 (its Done when: calibrate-bridge.md applies a conditional workflow to a running
project of that type by phase, reopens no gate, states that the applied text takes effect from the next design phase or
change cycle, adds a running project's `Workflows:` line from its recorded classification and confirms it with the owner,
keeps the project's `Phase:` value as the hook's table maps it, and its re-read list names, beside the core read in parts
to its end, the current phase's modules with their sub-files and variant files as the hook's table gives them);
docs/REQUIREMENTS.md R-027; Restructuring Plan section 6.10, step 4. Supervisor-written; no builder run."""
import importlib.util
import os
import re

from phase_modules import read, section
from workflow_files import BRIDGE, flat

CALIBRATE = os.path.join(BRIDGE, "commands", "calibrate-bridge.md")
SESSION_START = os.path.join(BRIDGE, "cursor-bridge", "session-start.py")
REREAD = "2. Re-read the governing files — they supersede what you hold in context"
CONDITIONAL = "4b. Conditional workflows — by phase, reopening no gate"


def text():
    return read(CALIBRATE)


def hook_table():
    spec = importlib.util.spec_from_file_location("session_start_for_calibrate", SESSION_START)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PHASE_MODULES


def test_r027_the_core_is_read_in_parts_with_the_phase_modules_and_the_conditional_workflows():
    """R-027 (TASK-023): the re-read list's first item reads the core in parts to its last line (it is past one Read
    call, stage B3's review, round 3), then the current phase's modules whole with the files their pointer lines name, as
    the hook's table gives them, then the conditional workflows that touch the phase, in the hook's order; held whole."""
    got = [l for l in section(text(), REREAD, 2).split("\n") if l.startswith("1. ")]
    assert got == [(
        "1. `~/.claude/commands/supervisor.md`, the core: it is longer than one Read call returns, so read it "
        "in parts, each call starting where the last one ended, until its last line; then the current phase's "
        "modules under `~/.claude/cursor-bridge/workflow/phases/`, each whole (`project-end.md` only at the "
        "close of the plan's last stage, as the table notes), with the sub-files and variant files their "
        "`Sub-files:` and `Variants:` lines name, as the session-start hook's table below gives them for the "
        "status file's `Phase:` value; then the conditional workflows the project's `Workflows:` line names "
        "that touch the phase: the type's file, the sub-type's file, the trait files in the open list's order")], "R-027: the re-read list's first item"


def test_r027_the_re_read_table_is_the_hooks_table():
    """R-027 (TASK-023): the table step 2 gives is the session-start hook's PHASE_MODULES, every `Phase:` value with
    exactly its modules in the hook's order, so calibration and the hook name the same files for a phase; a module's
    "and its sub-file" or "and its variant files" stands exactly where the module has a `Sub-files:` or `Variants:`
    line (Review A, round 1)."""
    body = section(text(), REREAD, 2)
    rows = [l for l in body.split("\n") if l.startswith("| `")]
    got = {}
    for r in rows:
        phases_cell, modules_cell = [c.strip() for c in r.strip("|").split("|")]
        modules = [m[:-3] for m in re.findall(r"`([a-z-]+\.md)`", modules_cell)]
        for phase in re.findall(r"`([a-z-]+)`", phases_cell):
            assert phase not in got, phase
            got[phase] = modules
        for m in modules:
            lines = read(os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases", m + ".md")).split("\n")
            for mark, words in (("Sub-files:", "and its sub-file"), ("Variants:", "and its variant files")):
                has_line = any(l.startswith(mark) for l in lines)
                says = ("`%s.md` %s" % (m, words)) in modules_cell
                assert has_line == says, "R-027: the table's %r for %s matches its %s line" % (words, m, mark)
    assert got == hook_table(), "R-027: the table is the hook's"
    assert "(`PHASE_MODULES` in `session-start.py`)" in body, "R-027: the table names its source"


def test_r027_a_conditional_workflow_is_applied_by_phase_reopening_no_gate():
    """R-027 (TASK-023; Restructuring Plan 6.10 step 4): the conditional workflows' step, held whole: applied by phase as
    step 4 sorts, reopening no gate; the `Workflows:` line added from the recorded classification, checked and confirmed
    with the owner (the A2 precedent, project.json); the `Phase:` value kept; the text in effect from the next design
    phase or change cycle, never applied backwards."""
    assert flat(section(text(), CONDITIONAL, 2)) == (
        "A release that adds or changes a conditional workflow (a product type's, a sub-type's or a trait's "
        "file under `~/.claude/cursor-bridge/workflow/`) names it in its changelog, and calibration applies "
        "it to every running project whose `Workflows:` line names that type, sub-type or trait, by phase, as "
        "step 4 sorts any item, reopening no gate: - **The `Workflows:` line.** A running project whose "
        "status file has none gets it now, a record-keeping addition as `project.json` was at release A2: one "
        "line per part, right after `Phase:`, in the open list's grammar, written from the classification the "
        "project recorded (the inventory's Decisions row of each part's product type, sub-type and traits, as "
        "the owner decided it); then `python ~/.claude/cursor-bridge/workflow-check.py --status "
        "docs/PROJECT_STATUS.md` must pass. Once it passes, the conditional workflows the new line names that "
        "touch the current phase are read whole, as step 2's item 1 reads them, before step 4 sorts anything "
        "(step 4 opens by sending such a project here): step 2 read none, since the line was missing. The "
        "line is confirmed with the owner: the report's first line quotes it, every part's line together, and "
        "asks whether they are right, after the roster's note where the profile is not the preferred one and "
        "beside step 4's decision line where there is one; the loop continues meanwhile on the line as "
        "written, and a correction is written and checked the same way. A project that recorded no "
        "classification is classified against the open list as intake does, and its line is put to the owner "
        "the same way. A project past intake is never paused for its classification: where the check fails, "
        "or the classification falls to a type or sub-type the open list has not written, its line reads `not "
        "yet classified`, which the check accepts, the finding or the unwritten workflow (a request to the "
        "maintainer) is the report's single decision line, and the project runs on the main workflow alone "
        "until the line is written. - **The `Phase:` value is kept.** Calibration never renames a project's "
        "phase: the session-start hook's table (step 2) maps the value the status file holds to its modules. "
        "- **When the text takes effect.** A conditional workflow's text takes effect from the project's next "
        "design phase or change cycle, where its intake questions, design sections, mandatory diagrams and "
        "plan additions are asked and written into the design and the plan; until then the project runs on "
        "the design and the plan the owner approved. Its additions at the points of a phase already passed "
        "are never applied backwards, and nothing it adds re-presents an approved design or plan or reopens a "
        "gate; what the changelog marks for the current phase or a later one is applied as step 4 says, "
        "**Now** or **Later**. - The report names each conditional workflow applied, the parts it reaches and "
        "when it takes effect, one line each."), "R-027: the conditional workflows' step"


def test_r027_the_step_stands_between_the_delta_and_the_record():
    """R-027 (TASK-023): the step runs after step 4 sorts the delta and before step 5 records it."""
    heads = [l for l in text().split("\n") if l.startswith("## ")]
    i = heads.index("## " + CONDITIONAL)
    assert heads[i - 1].startswith("## 4. ") and heads[i + 1].startswith("## 5. "), "R-027: 4b between 4 and 5"
