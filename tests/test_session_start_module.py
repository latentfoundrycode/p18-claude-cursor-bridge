"""TASK-015: after a compaction, a resume or a fork, the session-start hook names the current phase's module or
modules, the conditional workflows (type, sub-type, trait) that touch that phase, and the further files the phase
re-reads (R-005).

enforces: docs/REQUIREMENTS.md R-005 and docs/BUILD_PLAN.md TASK-015's Done when (handoff/TASK-015.md, its
Requirements); the order of conditional files is the core's "The order additions apply in" (R-034). The hook reads an
installed bridge: each test copies the repository's bridge/ into a temporary home, as bridge-install.py would."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
PROG = os.path.join(BRIDGE, "cursor-bridge", "session-start.py")
CORE = open(os.path.join(BRIDGE, "commands", "supervisor.md"), encoding="utf-8").read()
TEMPLATE_PHASES = [p.strip() for p in re.search(r"^Phase: <([^>]+)>", CORE, re.M).group(1).split("|")]
W = "~/.claude/cursor-bridge/workflow/"
P = W + "phases/"
MERGE, PITFALLS = "~/.claude/cursor-bridge/Merge-Verification-Policy.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"
DIAGRAMS, GLOSSARY = "~/.claude/cursor-bridge/Diagram-Planning-Conventions.md", "~/.claude/cursor-bridge/Glossary.md"
CONFIG = "~/.claude/cursor-bridge/Cursor-Project-Configuration.md"

# the shared Phase -> module table (BUILD_PLAN TASK-015), every template value, and the conventions each re-reads
EXPECTED = {
    "intake": (["intake"], []),
    "design": (["design"], [DIAGRAMS, GLOSSARY]),
    "mockups": (["interface"], []),
    "planning": (["planning", "run-parameters"], []),
    "configuration": (["configuration"], [CONFIG, PITFALLS]),
    "building": (["delegation-loop", "reflection", "project-end"], [MERGE, PITFALLS]),
    "done": (["change-cycle"], []),
    "changing": (["change-cycle", "delegation-loop", "reflection", "project-end"], [MERGE, PITFALLS]),
}


@pytest.fixture
def home(tmp_path):
    """An installed bridge in a temporary home: the repository's bridge/ copied as bridge-install.py lays it out."""
    h = tmp_path / "home"
    shutil.copytree(os.path.join(BRIDGE, "commands"), str(h / ".claude" / "commands"))
    shutil.copytree(os.path.join(BRIDGE, "cursor-bridge"), str(h / ".claude" / "cursor-bridge"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    return h


def write(home, rel, text):
    path = home / ".claude" / "cursor-bridge" / "workflow" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(tmp_path, *status_lines):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True, exist_ok=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\n" + "\n".join(status_lines) + "\nAwaiting user on: nothing\nBridge version: 2026.10.18a\n", encoding="utf-8")
    return root / "Workspace"


def pointers(cwd, home, source="compact"):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = {"cwd": str(cwd), "hook_event_name": "SessionStart", "source": source}
    p = subprocess.run([sys.executable, PROG, "--part", "pointers"], input=json.dumps(data), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    assert p.returncode == 0 and p.stderr == "", p.stderr
    return p.stdout


def named(out):
    """The workflow files the pointers name, in order, each path without any note after it."""
    return [re.match(r"  - (\S+)", line).group(1) for line in out.split("\n") if line.startswith("  - " + W)]


def conventions(out):
    return [m.group(1) for m in re.finditer(r"^  - and (\S+), whole$", out, re.M)]


def test_r005_the_table_maps_every_template_phase_value():
    assert sorted(TEMPLATE_PHASES) == sorted(EXPECTED), TEMPLATE_PHASES


@pytest.mark.parametrize("phase", sorted(EXPECTED))
def test_r005_each_phase_names_its_modules_in_order_and_its_conventions(tmp_path, home, phase):
    modules, convs = EXPECTED[phase]
    out = pointers(project(tmp_path, "Phase: %s (Stage 2)" % phase, "Workflows: not yet classified"), home)
    assert "BEFORE YOUR NEXT ACTION, re-read these files whole with the Read tool:" in out, out
    assert named(out) == [P + m + ".md" for m in modules], out
    assert conventions(out) == convs, out
    assert "lines " not in out, "no line ranges: a module is read whole"
    assert "Then read docs/PROJECT_STATUS.md and docs/INVENTORY.md whole (rule 41)." in out


@pytest.mark.parametrize("phase", ["building", "changing"])
def test_r005_project_end_is_named_for_the_last_stage_close(tmp_path, home, phase):
    out = pointers(project(tmp_path, "Phase: " + phase, "Workflows: not yet classified"), home)
    line = [l for l in out.split("\n") if l.startswith("  - " + P + "project-end.md")]
    assert len(line) == 1 and "last stage" in line[0], out


def test_r005_a_phase_outside_the_table_points_at_the_cores_table(tmp_path, home):
    out = pointers(project(tmp_path, "Phase: reviewing", "Workflows: not yet classified"), home)
    assert named(out) == [] and "not in the hook's map" in out and "The phase modules" in out, out


def test_r005_no_conditional_file_without_a_classified_line(tmp_path, home):
    write(home, "types/host-extension.md", "# Host extension\n\n## Add at intake.questions\n\nWhich host?\n")
    for lines in (["Phase: intake", "Workflows: not yet classified"], ["Phase: intake"]):
        out = pointers(project(tmp_path, *lines), home)
        assert named(out) == [P + "intake.md"], out


def conditionals(home):
    write(home, "types/host-extension.md", "# Host extension\n\n## Add at intake.questions\n\nWhich host?\n\n"
                                           "```\n## Add at delegation-loop.inspect-checks\n```\n")
    write(home, "types/host-extension/claude-code-extension.md",
          "# Claude Code extension\n\n## Add at interface.variants\n\nCommand design.\n")
    write(home, "traits/installable.md", "# Installable\n\n## Add at project-end.delivery for installer\n\nThe installer.\n\n"
                                         "## Add at interface.variants\n\nThe install screen.\n")
    write(home, "traits/external-services.md", "# External services\n\n## Add at interface.variants\n\nA contract.\n\n"
                                               "## Add at delegation-loop.test-checks\n\nRecorded replies.\n")


LINE = "Workflows: Host Extension Development → Claude Code Extension; traits: Installable, External services"


def test_r005_the_conditional_files_that_touch_the_phase_are_named_after_its_modules(tmp_path, home):
    conditionals(home)
    out = pointers(project(tmp_path, "Phase: intake", LINE), home)
    assert named(out) == [P + "intake.md", W + "types/host-extension.md"], out
    out = pointers(project(tmp_path, "Phase: building", LINE), home)
    # a heading inside a fenced block changes nothing: the type does not touch the delegation loop
    assert named(out) == [P + "delegation-loop.md", P + "reflection.md", P + "project-end.md",
                          W + "traits/installable.md", W + "traits/external-services.md"], out


def test_r034_the_conditional_files_follow_the_order_additions_apply_in(tmp_path, home):
    """Type, then sub-type, then the traits in the open list's order (installable before external services, which
    is not their alphabetical order)."""
    conditionals(home)
    out = pointers(project(tmp_path, "Phase: mockups", LINE), home)
    assert named(out) == [P + "interface.md", W + "types/host-extension/claude-code-extension.md",
                          W + "traits/installable.md", W + "traits/external-services.md"], out


def test_r005_a_file_two_parts_share_is_named_once_in_the_first_parts_place(tmp_path, home):
    conditionals(home)
    out = pointers(project(tmp_path, "Phase: building",
                           "Workflows: app: Host Extension Development; traits: External services",
                           "Workflows: tool: Host Extension Development → Claude Code Extension; traits: Installable, External services"), home)
    assert named(out) == [P + "delegation-loop.md", P + "reflection.md", P + "project-end.md",
                          W + "traits/external-services.md", W + "traits/installable.md"], out


def test_r005_a_named_workflow_that_is_not_written_is_not_named(tmp_path, home):
    out = pointers(project(tmp_path, "Phase: intake", "Workflows: Host Extension Development; traits: Installable"), home)
    assert named(out) == [P + "intake.md"], out


def test_r005_a_split_modules_sub_files_and_a_phases_variants_follow_their_module(tmp_path, home):
    """A module names its sub-files on a `Sub-files:` line and its variant files on a `Variants:` line, each path
    relative to workflow/phases/, separated by `; ` (handoff/TASK-015.md); the hook lists them after the module, in
    the order written; a line inside a fenced block names nothing."""
    loop = (home / ".claude" / "cursor-bridge" / "workflow" / "phases" / "delegation-loop.md")
    loop.write_text(loop.read_text(encoding="utf-8") + "\nSub-files: delegation-loop/merge.md; delegation-loop/inspect.md\n\n"
                    "```\nSub-files: delegation-loop/not-this.md\n```\n", encoding="utf-8")
    write(home, "phases/delegation-loop/merge.md", "## Merge\n")
    write(home, "phases/delegation-loop/inspect.md", "## Inspect\n")
    interface = (home / ".claude" / "cursor-bridge" / "workflow" / "phases" / "interface.md")
    interface.write_text(interface.read_text(encoding="utf-8") + "\nVariants: interface/mockups.md; interface/command-design.md\n",
                         encoding="utf-8")
    write(home, "phases/interface/mockups.md", "## Mockups\n")
    write(home, "phases/interface/command-design.md", "## Command design\n")
    out = pointers(project(tmp_path, "Phase: building", "Workflows: not yet classified"), home)
    assert named(out) == [P + "delegation-loop.md", P + "delegation-loop/merge.md", P + "delegation-loop/inspect.md",
                          P + "reflection.md", P + "project-end.md"], out
    out = pointers(project(tmp_path, "Phase: mockups", "Workflows: not yet classified"), home)
    assert named(out) == [P + "interface.md", P + "interface/mockups.md", P + "interface/command-design.md"], out


def test_r005_a_pointer_line_names_no_file_outside_its_module_folder(tmp_path, home):
    loop = (home / ".claude" / "cursor-bridge" / "workflow" / "phases" / "delegation-loop.md")
    loop.write_text(loop.read_text(encoding="utf-8") + "\nSub-files: ../../Known-Pitfalls.md; delegation-loop/ok.md; C:/x.md\n",
                    encoding="utf-8")
    write(home, "phases/delegation-loop/ok.md", "## Ok\n")
    out = pointers(project(tmp_path, "Phase: building", "Workflows: not yet classified"), home)
    assert named(out) == [P + "delegation-loop.md", P + "delegation-loop/ok.md", P + "reflection.md", P + "project-end.md"], out


def test_r005_both_parts_stay_under_the_cap_with_many_conditionals(tmp_path, home):
    conditionals(home)
    parts = ["Workflows: part%d: Host Extension Development → Claude Code Extension; traits: Installable, External services" % i
             for i in range(12)]
    cwd = project(tmp_path, "Phase: changing", *parts)
    out = pointers(cwd, home)
    assert len(out) < 10000 and "cut at" not in out, len(out)
    assert named(out)[-2:] == [W + "traits/installable.md", W + "traits/external-services.md"], out
