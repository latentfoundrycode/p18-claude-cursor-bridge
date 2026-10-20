"""TASK-013: the run-parameters, configuration and delegation-loop modules enriched (R-004, R-006, R-032).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring), R-032 (each module read whole: the
delegation-loop module, at 94% of the bound's characters before this increment, is split, its step 9 in a sub-file under
workflow/phases/delegation-loop/ that the module's own `Sub-files:` line names and the session-start hook follows);
docs/BUILD_PLAN.md TASK-013's Done when, and the pointer sweep for the split (the core's module table)."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
REGISTRY = os.path.join(CB, "workflow", "extension-points.md")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
HOOK = os.path.join(CB, "session-start.py")

SUB = "delegation-loop/refactoring-pass.md"
STEP9 = "9. Refactoring and optimization pass (at stage close)"


def read(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


def module(rel):
    return read(os.path.join(PHASES, rel if rel.endswith(".md") else rel + ".md"))


def flat(text):
    return re.sub(r"\s+", " ", text)


def headings(text):
    """(level, title) of every heading outside fenced blocks, in order."""
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
            h = re.match(r"^(#{1,6}) (.*)$", line)
            if h:
                out.append((len(h.group(1)), h.group(2).strip()))
    return out


def section(text, title, level):
    """The body of the heading `title` at `level`, to the next heading of that level or higher."""
    lines = text.split("\n")
    start = lines.index("#" * level + " " + title) + 1
    end = len(lines)
    for i in range(start, len(lines)):
        h = re.match(r"^(#{1,6}) ", lines[i])
        if h and len(h.group(1)) <= level:
            end = i
            break
    return "\n".join(lines[start:end])


LOOP_STEPS = ["1. Checkpoint", "2. Package the brief", "3. Delegate to Cursor",
              "3b. A model fails mid-step — switch automatically, restart the step, never wait", "4. Inspect", "5. Scan",
              "5b. Dependency-admission gate", "6. Benchmarks and observability", "7. Decide (accept the increment)",
              "8. Merge (the verified gate)"]

STRUCTURE = {
    "run-parameters": [(2, "Run parameters — asked once, after the plan is approved, before configuration"),
                       (3, "What must survive a compaction"), (3, "The procedure"), (3, "Writing the answers down"),
                       (2, "Extension points")],
    "configuration": [(2, "Phase 5 — Configure the Cursor build environment"), (3, "What must survive a compaction"),
                      (3, "The procedure"), (3, "Keeping the position"), (2, "Extension points")],
    "delegation-loop": [(2, "Phase 6 — The delegation loop"), (3, "What must survive a compaction"), (3, "The procedure")]
                       + [(3, s) for s in LOOP_STEPS] + [(2, "Extension points")],
}

INTRO = {
    "run-parameters": "After a compaction or a resume in this step, read these before your next action:",
    "configuration": "After a compaction or a resume in this phase, read these before your next action:",
    "delegation-loop": "After a compaction or a resume in this phase, read these before your next action:",
}

SURVIVAL = {
    "run-parameters": [
        "this module, whole;",
        "`docs/RUN_PARAMETERS.md` as written so far, whole: each answer is written there as the owner gives it "
        "(\"Writing the answers down\"), so the questions still to ask are the parameters it does not yet hold;",
        "`docs/BUILD_PLAN.md`, the approved plan, whole: a refactoring answer may name its stages, and parallel "
        "increments apply only where the plan marks increments `Parallel: yes`;",
        "`docs/PROJECT_STATUS.md`, whole: its `Workflows:` line names each part's conditional workflows, which add "
        "parameters at `run-parameters.parameters` and show whether a part is installable, as installer verification "
        "needs, and its `Awaiting user on:` line names the question that waits for the owner.",
    ],
    "configuration": [
        "this module, whole, with `~/.claude/cursor-bridge/Cursor-Project-Configuration.md` and "
        "`~/.claude/cursor-bridge/Known-Pitfalls.md`, each whole (the session-start hook names both for this phase);",
        "the approved design and plan: `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md` and "
        "`docs/RUN_PARAMETERS.md`, whole: only the items that are load-bearing for this project are applied;",
        "`docs/INVENTORY.md`, whole: its Resources rows record each pinned tool and version, each mode in force and each "
        "spending limit as the items are configured;",
        "`docs/PROJECT_STATUS.md`, whole: its `In flight:` line names the items configured so far and the one in hand "
        "(\"Keeping the position\"), its `Awaiting user on:` line an escalation that waits for the owner, and its "
        "`Workflows:` line the conditional workflows that add items at `configuration.items`.",
    ],
    "delegation-loop": [
        "this module and its sub-file, each whole (the session-start hook names both), with "
        "`~/.claude/cursor-bridge/Merge-Verification-Policy.md` and `~/.claude/cursor-bridge/Known-Pitfalls.md`, each "
        "whole;",
        "`docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41), and the last entries of "
        "`run/supervisor/in-flight.md` where it exists: the increment in hand, its branch and its checkpoint, the "
        "background runs that will wake you and what waits for the owner; while Review B runs the status file is not "
        "written and the position is kept in `in-flight.md` (step 8);",
        "the increment's entry in `docs/BUILD_PLAN.md`, its brief `handoff/TASK-<nnn>.md` with every revision of it, and "
        "each builder report `handoff/TASK-<nnn>-r<N>-report.md`, whole: the brief bounds the increment, and the report "
        "holds the `Assumed, not verified` list whose every item takes a disposition (rule 42);",
        "`docs/RUN_PARAMETERS.md` and `docs/ROSTER.resolved.json`: who completes a merge, whether the refactoring pass "
        "runs and whether increments run in parallel, and the models the delegate command and Review B name;",
        "the runs' files: `run/agent/TASK-<nnn>.err`, which step 3b reads after a failed call, and, while a gate is "
        "open, its files under `run/review/` (`REVIEW-<nnn>.diff`, `SCOPE-<nnn>.md`, `ASSUMPTIONS-<nnn>.md`, and "
        "`REVIEW-<nnn>.err`, whose first line is the launch time `pr-activity-check.py` needs), whole.",
    ],
}

KEYS = ["run-parameters", "configuration", "delegation-loop"]


@pytest.mark.parametrize("key", KEYS)
def test_r004_the_module_opens_with_its_compaction_survival_list(key):
    """R-004: the module's first section, straight after its heading, is the compaction-survival list, and the list is
    exactly what a resumed session in that phase reads before its next action."""
    text = module(key)
    assert headings(text) == STRUCTURE[key], headings(text)
    lines = text.split("\n")
    assert lines[1] == "" and lines[2] == "### What must survive a compaction", lines[:3]
    body = section(text, "What must survive a compaction", 3).strip().split("\n")
    assert body[0] == INTRO[key]
    assert all(l.startswith("- ") for l in body[1:] if l), body
    assert [l[2:] for l in body[1:] if l] == SURVIVAL[key]


def registry_points(module_key):
    text = read(REGISTRY)
    table = text.split("\n## Extension points\n", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in table.split("\n") if l.startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    out = []
    for row in rows[2:]:
        cells = dict(zip(header, [c.strip() for c in row.strip("|").split("|")]))
        if cells["Declared by"] == module_key:
            out.append(cells["Key"])
    return out


@pytest.mark.parametrize("key", KEYS)
def test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order(key):
    """R-006 and the registry's "How a phase module declares its points": a `## Extension points` section, one line
    per point giving its key, exactly the points the registry names this module as declaring, in the table's order."""
    body = section(module(key), "Extension points", 2).strip().split("\n")
    lines = [l for l in body if l.startswith("- ")]
    keys = [re.match(r"^- `([a-z0-9.-]+)` — \S", l).group(1) for l in lines]
    want = registry_points(key)
    assert want and keys == want, (keys, want)
    prose = flat(" ".join(l for l in body if l and not l.startswith("- ")))
    assert prose == ("This module offers the points below, each by its key in the extension-point registry "
                     "(`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each "
                     "accepts and whether it applies per part or per project. A conditional workflow's additions at a "
                     "point are made where the point's line places them, in the order the core states in \"Main and "
                     "conditional workflows\".")
    assert "may set" not in "\n".join(body)


POINTS = {
    "run-parameters.parameters": "parameters a conditional workflow adds to the five above, each asked as a question of "
                                 "its own in the same form with its default named first, and written as a line of its "
                                 "own in `docs/RUN_PARAMETERS.md`; made once for the whole project.",
    "configuration.items": "configuration items, tools and checks a conditional workflow adds to those above, each "
                           "worked as they are: written by **cursor-configurator** on your instruction, each tool's "
                           "pinned version recorded in `docs/INVENTORY.md` (Resources), and committed with the "
                           "configuration's checkpoint; made once for the whole project.",
    "delegation-loop.inspect-checks": "checks run at step 4 on every diff of the part, beside the scope and "
                                      "design-conformance checks and before the first reviewer; a failing one goes back "
                                      "to the builder with a corrected brief (step 7), never to the owner.",
    "delegation-loop.test-checks": "tests and checks run with the part's tests before the first reviewer (step 4), such "
                                   "as the observability tests of a part with screens (step 6); a failing one is a "
                                   "correctness-class block, re-delegated like any defect (step 7).",
    "delegation-loop.brief-constraints": "constraints every brief for the part carries beside spec-packager's template, "
                                         "such as a frozen rule the builder must follow, written into the brief at step "
                                         "2 and checked by `diff-reviewer` with the rest of the brief.",
}


@pytest.mark.parametrize("key", KEYS)
def test_r006_each_point_says_where_its_additions_are_made(key):
    """R-006 and the registry's "How a phase module declares its points": each point's line places the additions a
    conditional workflow makes there, as the point's Applies cell states (per part or for the whole project)."""
    body = section(module(key), "Extension points", 2).strip().split("\n")
    for line in [l for l in body if l.startswith("- ")]:
        k = re.match(r"^- `([a-z0-9.-]+)` — ", line).group(1)
        assert line == "- `%s` — %s" % (k, POINTS[k]), line


def pointer_lines(text):
    return [l for l in text.split("\n") if l.startswith("Sub-files: ") or l.startswith("Variants: ")]


def test_r032_the_delegation_loop_names_its_sub_file_on_its_pointer_line():
    """R-032: the delegation-loop module names its one sub-file on a `Sub-files:` line, in the grammar session-start.py
    reads (a line at column 0, paths relative to workflow/phases/ separated by `; `), in its procedure; every file under
    workflow/phases/delegation-loop/ is named there, so no sub-file goes unread."""
    text = module("delegation-loop")
    assert pointer_lines(text) == ["Sub-files: " + SUB], pointer_lines(text)
    proc = section(text, "The procedure", 3)
    assert "\nSub-files: " + SUB + "\n" in proc
    assert flat(proc).strip() == ("Steps 1 to 8 below run for every increment; step 9, the refactoring and optimization "
                                  "pass at a stage's close, is in a sub-file of this module, read whole with it wherever "
                                  "the module is read: Sub-files: " + SUB + " For each increment, in order:")
    folder = os.path.join(PHASES, "delegation-loop")
    assert sorted(os.listdir(folder)) == [os.path.basename(SUB)]


def test_r032_step_9_is_in_the_sub_file_whole_and_nowhere_else():
    """R-032: the sub-file opens with its own heading and a paragraph that says it is part of the module and when its
    step runs; it holds step 9 under its heading as the core had it, and no other file under workflow/phases/ holds
    the step's heading or its passages."""
    sub = module(SUB)
    assert headings(sub) == [(2, "The refactoring pass (Phase 6, step 9)"), (3, STEP9)], headings(sub)
    assert flat(sub.split("\n\n")[1]) == (
        "This file is a sub-file of the delegation-loop module (`delegation-loop.md`, \"The procedure\"), read whole "
        "with it. It holds the loop's step 9, which runs at a stage's close, before the stage's reflection point "
        "(`reflection.md`), when `docs/RUN_PARAMETERS.md` turns the refactoring pass on for the stage.")
    fs = flat(sub)
    passages = (
        "When the last increment of a stage has merged and `docs/RUN_PARAMETERS.md` says **Refactoring pass: on** for "
        "that stage, run one refactoring pass **before** the stage's reflection point.",
        "**Scout.** Delegate to **refactor-scout** with the stage base commit",
        "**Purity check — deterministic, before any reviewer:**",
        "python ~/.claude/cursor-bridge/refactor-check.py main --max-lines 400",
        "**Beyond budget** candidates go to `docs/HARDENING.md` under the stage name",
        "At **project end** run one final pass over the whole tree before the User Manual is written.",
    )
    for p in passages:
        assert p in fs, p
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/")
            if rel == SUB:
                continue
            text = read(os.path.join(root, f))
            assert "### " + STEP9 not in text.split("\n"), rel
            for p in passages:
                assert p not in flat(text), (rel, p)


def test_the_run_parameters_are_written_as_each_answer_is_given():
    """R-004: the survival list names docs/RUN_PARAMETERS.md as written so far, so the procedure writes each answer as
    it arrives (as intake writes its notes, TASK-011)."""
    s = flat(section(module("run-parameters"), "Writing the answers down", 3))
    assert s.strip() == ("Write each answer into `docs/RUN_PARAMETERS.md` as the owner gives it, in the form above, the "
                         "`Set:` line with the first: a compaction between two questions then loses no answer, and a "
                         "resume asks only the parameters the file does not yet hold. A parameter a conditional workflow "
                         "adds at `run-parameters.parameters` is asked and written the same way.")


def test_the_configurations_position_is_kept_on_in_flight():
    """R-004: the survival list names the status file's In flight: line, so the procedure keeps it while the phase
    runs."""
    s = flat(section(module("configuration"), "Keeping the position", 3))
    assert s.strip() == ("While the phase runs, keep the status file's `In flight:` line naming the items configured so "
                         "far and the one in hand, rewritten as each is finished, so that a resume after a compaction "
                         "neither redoes an item nor skips one; once the configuration's checkpoint is committed, the "
                         "line gives way to the record of what was configured.")


@pytest.mark.parametrize("rel", ["run-parameters.md", "configuration.md", "delegation-loop.md", SUB])
def test_r032_the_module_and_its_sub_file_are_read_whole(rel):
    """R-032: each enriched module and the sub-file stay within the bound a module is read whole by."""
    text = module(rel)
    assert text.count("\n") <= 1500 and len(text) <= 60000, (rel, text.count("\n"), len(text))


def test_r005_the_hook_names_the_delegation_loop_and_its_sub_file(tmp_path):
    """R-005 with R-032, the first real Sub-files: line: for `Phase: building` the installed hook names
    delegation-loop.md, then its sub-file, then the reflection and project-end modules."""
    home = tmp_path / "home"
    shutil.copytree(os.path.join(BRIDGE, "commands"), str(home / ".claude" / "commands"))
    shutil.copytree(CB, str(home / ".claude" / "cursor-bridge"), ignore=shutil.ignore_patterns("__pycache__"))
    ws = tmp_path / "proj" / "Workspace"
    (ws / "docs").mkdir(parents=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nPhase: building\nWorkflows: not yet classified\nAwaiting user on: nothing\n", encoding="utf-8")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    p = subprocess.run([sys.executable, HOOK, "--part", "pointers"], input=json.dumps(data), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    assert p.returncode == 0 and p.stderr == "", p.stderr
    w = "~/.claude/cursor-bridge/workflow/phases/"
    named = [re.match(r"  - (\S+)", l).group(1) for l in p.stdout.split("\n") if l.startswith("  - " + w)]
    assert named == [w + "delegation-loop.md", w + SUB, w + "reflection.md", w + "project-end.md"], p.stdout


def test_the_core_names_the_delegation_loops_sub_file():
    """The pointer sweep for the split: the core's module table names the delegation loop's sub-file folder, and the
    sentence under the table says where a split module's step keeps its heading."""
    core = flat(read(CORE))
    assert ("| The delegation loop (Phase 6) | `~/.claude/cursor-bridge/workflow/phases/delegation-loop.md` and its "
            "sub-file under `~/.claude/cursor-bridge/workflow/phases/delegation-loop/` |") in core
    assert ("A step a module keeps in a sub-file keeps its heading there: the delegation loop's step 9 is in "
            "`delegation-loop/refactoring-pass.md`.") in core
